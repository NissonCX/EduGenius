"""
FastAPI endpoints for document upload and processing with MD5 deduplication.
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional
import tempfile
import os

from app.db.database import get_db, async_session_maker
from app.crud.document import (
    calculate_md5_hash,
    get_document_by_md5,
    create_document,
    get_or_create_user,
    update_document_status,
    get_user_progress_for_document,
    create_progress
)
from app.services.document_processor import process_uploaded_document, DocumentProcessor
from app.core.chroma import create_document_collection, add_document_chunks
from app.core.security import get_current_user
from app.core.logging_config import get_logger
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentResponse,
    ChapterResponse,
    ProgressCreate
)
from app.models.document import User

logger = get_logger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])


# For demo: use a default user
DEFAULT_USER_EMAIL = "demo@edugenius.ai"
DEFAULT_USERNAME = "demo_user"


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload document with MD5-based deduplication and RAG processing.

    完整流程：
    1. 计算 MD5 哈希
    2. 检查是否已存在（去重）
    3. 解析 PDF/TXT
    4. 语义切分
    5. DashScope 向量化
    6. 存入 ChromaDB
    7. 创建数据库记录

    注意：大文件处理可能需要较长时间，请耐心等待
    """
    import asyncio
    from app.core.config import settings

    # 文件大小限制（50MB）
    MAX_FILE_SIZE = 50 * 1024 * 1024

    # 读取文件内容
    content = await file.read()

    # 检查文件大小
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"文件过大，最大支持 {MAX_FILE_SIZE // (1024*1024)}MB"
        )

    # 保存到临时文件
    tmp_file_path = None
    permanent_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            tmp_file.write(content)
            tmp_file.flush()  # 🔧 确保内容写入磁盘
            tmp_file_path = tmp_file.name

        print(f"📄 开始处理文档: {file.filename} ({len(content)} bytes)")

        # 计算文档处理器
        processor = DocumentProcessor()
        md5_hash = processor.calculate_md5(tmp_file_path)
        print(f"🔐 MD5: {md5_hash}")

        # 检查是否已存在
        existing_document = await get_document_by_md5(db, md5_hash)

        if existing_document:
            # 文档内容已存在，但为当前用户创建新的文档记录
            # 这样可以复用 ChromaDB 向量数据，但每个用户有独立的学习进度
            
            # 检查当前用户是否已经有这个文档
            from sqlalchemy import select, and_
            from app.models.document import Document as DocumentModel
            
            user_doc_result = await db.execute(
                select(DocumentModel).where(
                    and_(
                        DocumentModel.md5_hash == md5_hash,
                        DocumentModel.uploaded_by == current_user.id
                    )
                )
            )
            user_existing_doc = user_doc_result.scalar_one_or_none()
            
            if user_existing_doc:
                # 用户已经上传过这个文档
                return DocumentUploadResponse(
                    message="✨ 您已上传过此文档",
                    is_duplicate=True,
                    document_id=user_existing_doc.id,
                    md5_hash=md5_hash,
                    processing_status=user_existing_doc.processing_status
                )
            
            # 为当前用户创建新的文档记录（复用向量数据）
            from app.schemas.document import DocumentCreate
            document_data = DocumentCreate(
                filename=file.filename,
                file_type=file.filename.split(".")[-1].lower(),
                file_size=len(content),
                md5_hash=md5_hash
            )
            
            new_document = await create_document(db, document_data, current_user.id)
            
            # 更新文档状态
            await update_document_status(
                db,
                new_document.id,
                status="completed",
                total_pages=existing_document.total_pages,
                total_chapters=0,
                title=title or file.filename
            )
            
            # 为新用户创建章节（从原始文件提取目录）
            try:
                from app.services.chapter_divider_enhanced import EnhancedChapterDivider
                from app.services.document_processor_v2 import EnhancedDocumentProcessor
                from app.core.chroma import get_document_collection

                divider = EnhancedChapterDivider()
                toc_text = ""

                # 尝试从原始 PDF 文件提取目录
                if existing_document.file_type == "pdf":
                    try:
                        enhanced_processor = EnhancedDocumentProcessor()
                        # 使用原始文件路径
                        original_file = f"uploads/{current_user.id}_{existing_document.filename}"
                        if os.path.exists(original_file):
                            # 🔧 FIX: 增加到15页，确保包含完整目录
                            _, toc_text = enhanced_processor.extract_toc_pages(original_file, max_toc_pages=15)
                            print(f"📚 从现有 PDF 提取了目录: {len(toc_text)} 字符")
                    except Exception as e:
                        print(f"⚠️  从 PDF 提取目录失败: {e}")

                # 如果没有 TOC，尝试从 ChromaDB 获取前几个 chunks
                if not toc_text:
                    collection = get_document_collection(md5_hash)
                    if collection and collection.count() > 0:
                        results = collection.get()
                        if results and results['documents']:
                            # 只使用前几个 chunks 作为 TOC 的 fallback
                            toc_text = "\n\n".join(results['documents'][:3])

                if toc_text:
                    chapters = await divider.divide_document_into_chapters(
                        document_id=new_document.id,
                        user_id=current_user.id,
                        document_text=toc_text,
                        db=db
                    )

                    print(f"✅ 为新用户创建了 {len(chapters)} 个章节")
            except Exception as e:
                print(f"⚠️  章节划分失败: {str(e)}")
                import traceback
                traceback.print_exc()
            
            return DocumentUploadResponse(
                message=f"✨ 文档已存在，已为您创建学习记录",
                is_duplicate=True,
                document_id=new_document.id,
                md5_hash=md5_hash,
                processing_status="completed"
            )

        # 处理新文档
        file_type = file.filename.split(".")[-1].lower()
        if file_type not in ["pdf", "txt"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件类型: {file_type}。支持的格式: pdf, txt"
            )

        # 创建数据库记录（必须在处理之前创建，以便获取document_id）
        from app.schemas.document import DocumentCreate
        document_data = DocumentCreate(
            filename=file.filename,
            file_type=file_type,
            file_size=len(content),
            md5_hash=md5_hash
        )

        new_document = await create_document(db, document_data, current_user.id)

        # 🔧 创建永久文件目录并移动文件
        os.makedirs("uploads", exist_ok=True)
        permanent_file_path = f"uploads/{current_user.id}_{new_document.id}_{file.filename}"
        import shutil
        shutil.move(tmp_file_path, permanent_file_path)
        print(f"💾 文件已保存到: {permanent_file_path}")

        print(f"📖 开始解析 {file_type} 文档...")

        # 🔍 智能混合处理：使用 HybridDocumentProcessor
        if file_type == "pdf":
            logger.info("🎯 检测到PDF文件，将使用HybridDocumentProcessor处理")
            try:
                from app.services.hybrid_document_processor import HybridDocumentProcessor
                from app.utils.pdf_validator import validate_pdf_before_upload

                logger.info("✅ HybridDocumentProcessor导入成功")
                print(f"\n{'='*60}")
                print(f"🔬 智能混合处理模式")
                print(f"{'='*60}\n")

                # 预检测
                validation = validate_pdf_before_upload(permanent_file_path)

                print(f"📋 PDF 预检查结果:")
                print(f"   总页数: {validation['total_pages']}")
                print(f"   文本页: {validation['text_pages']}")
                print(f"   文本占比: {validation['text_ratio']:.1%}")
                print(f"   是否扫描版: {'⚠️  是' if validation['is_scan'] else '✅ 否'}")
                print(f"{'='*60}\n")

                # 如果是扫描版，给出提示但继续处理（不再拒绝）
                if validation['is_scan']:
                    print(f"💡 检测到扫描版PDF，将使用 PaddleOCR 进行文字识别")
                    print(f"   预计处理时间: {validation['total_pages'] * 2}-{validation['total_pages'] * 5} 秒\n")

                # 使用混合处理器处理文档
                processor = HybridDocumentProcessor()

                # 更新状态为处理中
                await db.execute(
                    text("UPDATE documents SET processing_status = :status WHERE id = :id"),
                    {"status": "pending", "id": new_document.id}
                )
                await db.commit()

                # 检查 OCR 并发限制
                if validation['is_scan']:
                    from app.core.ocr_semaphore import ocr_semaphore

                    task_id = f"doc_{new_document.id}"
                    acquired = await ocr_semaphore.acquire(task_id)

                    if not acquired:
                        # 槽位已满，排队处理
                        await db.execute(
                            text("UPDATE documents SET processing_status = :status WHERE id = :id"),
                            {"status": "queued", "id": new_document.id}
                        )
                        await db.commit()

                        return DocumentUploadResponse(
                            message="⏳ 服务器繁忙，您的文档已加入队列，请稍后刷新页面查看进度",
                            is_duplicate=False,
                            document_id=new_document.id,
                            md5_hash=md5_hash,
                            processing_status="queued"
                        )

                    logger.info(f"🔐 OCR 任务 {task_id} 获得处理权限")

                # 异步处理（使用 asyncio.create_task）
                async def process_document_async():
                    # 在异步任务中创建新的数据库 session
                    async with async_session_maker() as async_db:
                        try:
                            result = await processor.process_document(
                                file_path=permanent_file_path,
                                document_id=new_document.id,
                                user_id=current_user.id,
                                title=title or file.filename,
                                db=async_db
                            )

                            logger.info(
                                f"✅ 文档 {new_document.id} 处理完成: "
                                f"路径={result.get('path')}, "
                                f"耗时={result.get('processing_time', 0):.1f}秒, "
                                f"OCR置信度={result.get('ocr_confidence', 0):.1%}"
                            )

                        except Exception as e:
                            logger.error(f"❌ 文档 {new_document.id} 处理失败: {e}", exc_info=True)

                            # 更新状态为失败
                            await async_db.execute(
                                text("UPDATE documents SET processing_status = :status WHERE id = :id"),
                                {"status": "failed", "id": new_document.id}
                            )
                            await async_db.commit()

                # 启动异步处理
                asyncio.create_task(process_document_async())

                # 立即返回，让前端可以轮询进度
                return DocumentUploadResponse(
                    message=f"✅ 文档已上传，正在{'OCR识别' if validation['is_scan'] else '处理'}中...",
                    is_duplicate=False,
                    document_id=new_document.id,
                    md5_hash=md5_hash,
                    processing_status="pending" if validation['is_scan'] else "processing"
                )

            except HTTPException:
                raise  # 重新抛出 HTTPException
            except Exception as e:
                # PDF处理失败，记录错误并返回失败状态
                logger.error(f"❌ PDF 处理失败: {e}", exc_info=True)

                # 更新状态为失败
                await db.execute(
                    text("UPDATE documents SET processing_status = :status WHERE id = :id"),
                    {"status": "failed", "id": new_document.id}
                )
                await db.commit()

                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"文档处理失败: {str(e)}"
                )

        # TXT文件处理：解析文档、切分、向量化（添加超时保护）
        try:
            result = await asyncio.wait_for(
                process_uploaded_document(
                    file_path=permanent_file_path,
                    title=title or file.filename,
                    user_email=current_user.email
                ),
                timeout=300.0  # 5分钟超时
            )
            print(f"✅ 文档解析完成: {len(result.get('chunks', []))} 个 chunks")
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="文档处理超时（超过5分钟），请尝试上传较小的文件"
            )

        # 🎯 如果是 PDF，使用智能解析器提取目录（书签优先 + 启发式扫描）
        toc_text = ""
        if file_type == "pdf":
            try:
                from app.core.textbook_parser import TextbookParser
                parser = TextbookParser()

                parse_result = await parser.parse_textbook(permanent_file_path, db)
                toc_text = parse_result['toc_text']

                source = parse_result['source']  # 'bookmark' or 'scan'
                pages = parse_result['pages']
                need_ai = parse_result.get('need_ai_guess', False)

                print(f"📚 智能解析完成:")
                print(f"   来源: {source}")
                print(f"   页码: {pages}")
                print(f"   文本长度: {len(toc_text)} 字符")
                if need_ai:
                    print(f"   ⚠️  需要AI辅助识别")
            except Exception as e:
                logger.warning(f"⚠️  智能解析失败: {e}，使用fallback")
                toc_text = ""

        # 创建 ChromaDB collection（以 MD5 命名）
        create_document_collection(md5_hash)

        # 添加 chunks 到 ChromaDB
        chunks = result['chunks']
        embeddings = result['embeddings']

        # 准备 metadata
        chunk_metadata = []
        for chunk in chunks:
            meta = chunk.metadata.copy()
            chunk_metadata.append(meta)

        # 提取文本内容
        chunk_texts = [chunk.page_content for chunk in chunks]

        # 存入 ChromaDB
        add_document_chunks(
            md5_hash=md5_hash,
            chunks=chunk_texts,
            embeddings=embeddings,
            metadata=chunk_metadata
        )

        # 更新文档状态
        await update_document_status(
            db,
            new_document.id,
            status="completed",
            total_pages=result['stats'].get('total_pages', 0),
            total_chapters=0,  # 稍后由章节划分服务更新
            title=title or file.filename
        )

        # 🎯 核心：自动划分章节（使用增强版服务）
        try:
            # 使用增强版章节划分服务
            from app.services.chapter_divider_enhanced import EnhancedChapterDivider

            divider = EnhancedChapterDivider()

            # 使用增强版处理器提取的目录文本
            # 如果 toc_text 为空（比如 txt 文件），使用常规文本
            if not toc_text:
                # 对于非 PDF 或提取失败的情况，使用前几个 chunks
                toc_text = "\n\n".join([c.page_content for c in chunks[:3]])

            if toc_text:
                print(f"📚 发送目录文本给 LLM，长度: {len(toc_text)} 字符")

                chapters = await divider.divide_document_into_chapters(
                    document_id=new_document.id,
                    user_id=current_user.id,
                    document_text=toc_text,  # 只发送目录文本
                    db=db
                )

                print(f"✅ 文档处理完成，共划分 {len(chapters)} 个章节")

                # 更新文档的章节数
                await update_document_status(
                    db,
                    new_document.id,
                    status="completed",
                    total_chapters=len(chapters)
                )
            else:
                print("⚠️ 未能提取到目录文本")
                # 创建默认章节
                await create_progress(
                    db,
                    ProgressCreate(
                        user_id=current_user.id,
                        document_id=new_document.id,
                        chapter_number=1,
                        chapter_title=title or file.filename,
                        cognitive_level_assigned=current_user.cognitive_level
                    )
                )
        except Exception as e:
            print(f"⚠️  章节划分失败: {str(e)}")
            import traceback
            traceback.print_exc()
            # 即使章节划分失败，也创建一个默认章节
            await create_progress(
                db,
                ProgressCreate(
                    user_id=current_user.id,
                    document_id=new_document.id,
                    chapter_number=1,
                    chapter_title=title or file.filename,
                    cognitive_level_assigned=current_user.cognitive_level
                )
            )

        return DocumentUploadResponse(
            message=f"✅ 文档上传成功：{file.filename}",
            is_duplicate=False,
            document_id=new_document.id,
            md5_hash=md5_hash,
            processing_status="completed"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档处理失败: {str(e)}"
        )

    finally:
        # 清理临时文件（只删除临时文件，不删除永久文件）
        if tmp_file_path and os.path.exists(tmp_file_path):
            try:
                os.remove(tmp_file_path)
            except Exception as e:
                # 记录错误但不抛出异常
                print(f"⚠️  清理临时文件失败: {e}")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "EduGenius API"}


@router.get("/list")
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户上传的所有文档列表
    """
    from sqlalchemy import select
    from app.models.document import Document
    
    # 查询用户的所有文档
    result = await db.execute(
        select(Document).where(
            Document.uploaded_by == current_user.id
        ).order_by(Document.uploaded_at.desc())
    )
    documents = result.scalars().all()
    
    # 转换为字典列表
    document_list = []
    for doc in documents:
        document_list.append({
            "id": doc.id,
            "filename": doc.filename,
            "title": doc.title or doc.filename,
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "total_pages": doc.total_pages,
            "total_chapters": doc.total_chapters,
            "processing_status": doc.processing_status,
            "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
            "md5_hash": doc.md5_hash
        })
    
    return {
        "documents": document_list,
        "total": len(document_list)
    }


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get document details by ID.
    """
    document = await get_document_by_md5(db, str(document_id))
    if not document:
        # Try by ID
        from app.crud.document import get_document_by_id
        document = await get_document_by_id(db, document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )

    return document


@router.get("/{document_id}/chapters")
async def get_document_chapters(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get chapter list with progress and lock status for a document.

    解锁规则：
    - 第一章默认解锁
    - 后续章节需要满足前置条件：
      1. 前一章完成度 >= 70%
      2. 前一章测试分数 >= 60%（如果有测试记录）
      3. 前一章学习时间 >= 10 分钟
    """
    from sqlalchemy import select
    from app.models.document import Document, Progress

    # 验证文档存在
    doc_result = await db.execute(select(Document).where(Document.id == document_id))
    document = doc_result.scalar_one_or_none()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )

    # 获取所有进度记录
    progress_result = await db.execute(
        select(Progress).where(
            Progress.user_id == current_user.id,
            Progress.document_id == document_id
        ).order_by(Progress.chapter_number)
    )
    all_progress = progress_result.scalars().all()

    # 获取所有小节记录（使用原生SQL，避免ORM问题）
    from collections import defaultdict
    from sqlalchemy import text
    subsections_by_chapter = defaultdict(list)

    try:
        subsection_query = text("""
            SELECT chapter_number, subsection_number, subsection_title,
                   page_number, completion_percentage, time_spent_minutes
            FROM subsections
            WHERE user_id = :user_id AND document_id = :document_id
            ORDER BY chapter_number, subsection_number
        """)

        result = await db.execute(
            subsection_query,
            {"user_id": current_user.id, "document_id": document_id}
        )

        rows = result.fetchall()
        for row in rows:
            subsections_by_chapter[row[0]].append({
                "subsection_number": row[1],
                "subsection_title": row[2],
                "page_number": row[3],
                "completion_percentage": row[4],
                "time_spent_minutes": row[5]
            })
    except Exception as e:
        print(f"⚠️  无法加载小节数据: {e}")
        # 继续执行，只是不包含小节数据

    # 解锁阈值配置
    UNLOCK_CONFIG = {
        "completion_threshold": 0.7,  # 70% 完成度
        "quiz_score_threshold": 0.6,  # 60% 测试分数
        "min_time_minutes": 10  # 最少10分钟学习时间
    }

    chapters = []

    for progress in all_progress:
        # 判断章节状态
        is_locked = False
        lock_reason = None

        if progress.chapter_number > 1:
            # 查找前一章的进度
            prev_progress = next(
                (p for p in all_progress if p.chapter_number == progress.chapter_number - 1),
                None
            )

            if prev_progress:
                # 检查解锁条件
                conditions_met = []
                conditions_not_met = []

                # 检查完成度
                if prev_progress.completion_percentage >= UNLOCK_CONFIG["completion_threshold"] * 100:
                    conditions_met.append(f"完成度 {prev_progress.completion_percentage:.0f}%")
                else:
                    conditions_not_met.append(
                        f"前一章完成度需达到 {UNLOCK_CONFIG['completion_threshold'] * 100:.0f}%（当前 {prev_progress.completion_percentage:.0f}%）"
                    )

                # 检查学习时间
                if prev_progress.time_spent_minutes >= UNLOCK_CONFIG["min_time_minutes"]:
                    conditions_met.append(f"学习时间 {prev_progress.time_spent_minutes} 分钟")
                else:
                    conditions_not_met.append(
                        f"前一章学习时间需达到 {UNLOCK_CONFIG['min_time_minutes']} 分钟（当前 {prev_progress.time_spent_minutes} 分钟）"
                    )

                # 检查测试分数（如果有测试记录）
                if prev_progress.quiz_attempts > 0:
                    if prev_progress.quiz_success_rate >= UNLOCK_CONFIG["quiz_score_threshold"]:
                        conditions_met.append(f"测试分数 {prev_progress.quiz_success_rate * 100:.0f}%")
                    else:
                        conditions_not_met.append(
                            f"前一章测试分数需达到 {UNLOCK_CONFIG['quiz_score_threshold'] * 100:.0f}%（当前 {prev_progress.quiz_success_rate * 100:.0f}%）"
                        )

                # 如果所有条件都满足，则解锁
                is_locked = len(conditions_not_met) > 0

                if is_locked:
                    lock_reason = f"需完成前一章：{'; '.join(conditions_not_met)}"
            else:
                # 没有前一章记录，锁定
                is_locked = True
                lock_reason = "需先完成前一章"

        # 如果状态为 locked，强制锁定
        if progress.status == "locked":
            is_locked = True
            lock_reason = "此章节已被锁定"

        # 确定状态图标
        if is_locked:
            status_icon = "🔒"
            status_text = "未解锁"
        elif progress.status == "completed":
            status_icon = "✅"
            status_text = "已完成"
        elif progress.status == "in_progress":
            status_icon = "🔓"
            status_text = "学习中"
        else:
            status_icon = "🔓"
            status_text = "未开始"

        chapters.append({
            "chapter_number": progress.chapter_number,
            "chapter_title": progress.chapter_title or f"第 {progress.chapter_number} 章",
            "status": progress.status,
            "completion_percentage": progress.completion_percentage,
            "is_locked": is_locked,
            "lock_reason": lock_reason,
            "status_icon": status_icon,
            "status_text": status_text,
            "time_spent_minutes": progress.time_spent_minutes,
            "quiz_attempts": progress.quiz_attempts,
            "quiz_success_rate": progress.quiz_success_rate,
            "subsections": subsections_by_chapter.get(progress.chapter_number, []),
            "subsection_count": len(subsections_by_chapter.get(progress.chapter_number, []))
        })

    return {
        "document_id": document_id,
        "document_title": document.title or document.filename,
        "total_chapters": len(chapters),
        "chapters": chapters
    }


@router.post("/{document_id}/redivide-chapters")
async def redivide_chapters(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    重新划分文档章节
    使用 LLM 重新分析文档并划分章节
    """
    from sqlalchemy import select, delete
    from app.models.document import Document, Progress
    from app.services.chapter_divider import ChapterDivider
    from app.services.document_processor import DocumentProcessor

    # 验证文档存在
    doc_result = await db.execute(select(Document).where(Document.id == document_id))
    document = doc_result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )

    # 验证文档所有权
    if document.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限操作此文档"
        )

    try:
        # 删除旧的章节进度记录
        await db.execute(
            delete(Progress).where(
                Progress.user_id == current_user.id,
                Progress.document_id == document_id
            )
        )
        await db.commit()

        # 重新解析文档
        processor = DocumentProcessor()
        result = await processor.process_document(
            file_path=None,  # 这里需要修改，应该使用存储的文件
            metadata={'title': document.title}
        )

        # 获取文档文本
        document_text = result['texts'][0] if result['texts'] else ""

        if not document_text:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="无法提取文档内容"
            )

        # 重新划分章节
        divider = ChapterDivider()
        chapters = await divider.divide_document_into_chapters(
            document_id=document_id,
            user_id=current_user.id,
            document_text=document_text,
            db=db
        )

        return {
            "message": f"✅ 章节重新划分成功，共 {len(chapters)} 个章节",
            "document_id": document_id,
            "total_chapters": len(chapters),
            "chapters": chapters
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_SERVER_ERROR,
            detail=f"章节划分失败: {str(e)}"
        )


@router.get("/{document_id}/chapters/{chapter_number}/subsections")
async def get_chapter_subsections(
    document_id: int,
    chapter_number: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取章节的所有小节
    """
    from sqlalchemy import select
    from app.models.subsection import Subsection
    from app.models.document import Progress
    
    # 验证章节存在
    progress_result = await db.execute(
        select(Progress).where(
            Progress.user_id == current_user.id,
            Progress.document_id == document_id,
            Progress.chapter_number == chapter_number
        )
    )
    progress = progress_result.scalar_one_or_none()
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="章节不存在"
        )
    
    # 获取所有小节
    subsections_result = await db.execute(
        select(Subsection).where(
            Subsection.document_id == document_id,
            Subsection.chapter_number == chapter_number
        ).order_by(Subsection.subsection_number)
    )
    subsections = subsections_result.scalars().all()
    
    # 一次性获取所有小节的进度（优化 N+1 查询）
    subsection_numbers = [s.subsection_number for s in subsections]
    if subsection_numbers:
        progress_result = await db.execute(
            select(Progress).where(
                Progress.user_id == current_user.id,
                Progress.document_id == document_id,
                Progress.chapter_number == chapter_number,
                Progress.subsection_number.in_(subsection_numbers)
            )
        )
        progress_map = {p.subsection_number: p for p in progress_result.scalars().all()}
    else:
        progress_map = {}
    
    # 转换为响应格式
    subsection_list = []
    for subsection in subsections:
        # 从 map 中查找进度
        subsection_progress = progress_map.get(subsection.subsection_number)
        
        is_completed = False
        progress_percentage = 0.0
        
        if subsection_progress:
            is_completed = subsection_progress.status == "completed"
            progress_percentage = subsection_progress.subsection_progress or 0.0
        
        subsection_list.append({
            "subsection_number": subsection.subsection_number,
            "subsection_title": subsection.subsection_title,
            "content_summary": subsection.content_summary,
            "estimated_time_minutes": subsection.estimated_time_minutes,
            "is_completed": is_completed,
            "progress": progress_percentage
        })
    
    return {
        "document_id": document_id,
        "chapter_number": chapter_number,
        "chapter_title": progress.chapter_title,
        "total_subsections": len(subsection_list),
        "subsections": subsection_list
    }


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除文档
    """
    from sqlalchemy import select, delete
    from app.models.document import Document
    
    # 验证文档存在且属于当前用户
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )
    
    if document.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限删除此文档"
        )
    
    # 🔧 FIX: 级联删除相关数据
    print(f"\n{'='*60}")
    print(f"🗑️  开始删除文档 {document_id} ({document.filename})")
    print(f"{'='*60}\n")

    from sqlalchemy import text

    # 0. 先统计要删除的数据
    print("📊 统计要删除的数据:")
    stats_check = text("""
        SELECT
            (SELECT COUNT(*) FROM conversations WHERE document_id = :doc_id AND user_id = :user_id) as conversations,
            (SELECT COUNT(*) FROM progress WHERE document_id = :doc_id AND user_id = :user_id) as progress,
            (SELECT COUNT(*) FROM subsections WHERE document_id = :doc_id AND user_id = :user_id) as subsections
    """)
    stats = await db.execute(stats_check, {
        'doc_id': document_id,
        'user_id': current_user.id
    })
    row = stats.fetchone()
    print(f"   - 对话记录: {row[0]} 条")
    print(f"   - 学习进度: {row[1]} 条")
    print(f"   - 小节记录: {row[2]} 条")
    print()

    # 1. 删除对话记录 (conversations 表)
    print("🗑️  步骤 1/6: 删除对话记录...")
    conversation_delete = text("""
        DELETE FROM conversations
        WHERE document_id = :document_id AND user_id = :user_id
    """)
    result = await db.execute(conversation_delete, {
        'document_id': document_id,
        'user_id': current_user.id
    })
    conversation_count = result.rowcount
    print(f"   ✅ 删除了 {conversation_count} 条对话记录")

    # 2. 删除学习进度记录 (progress 表) - 先获取要删除的 progress_id
    progress_ids_query = text("""
        SELECT id FROM progress
        WHERE document_id = :document_id AND user_id = :user_id
    """)
    progress_result = await db.execute(progress_ids_query, {
        'document_id': document_id,
        'user_id': current_user.id
    })
    progress_ids = [row[0] for row in progress_result.fetchall()]

    # 3. 删除测试记录 (quiz_attempts 表) - 通过 progress_id
    quiz_count = 0
    if progress_ids:
        # 构建 IN 子句
        placeholders = ','.join([f':pid{i}' for i in range(len(progress_ids))])
        params = {f'pid{i}': pid for i, pid in enumerate(progress_ids)}
        quiz_delete = text(f"""
            DELETE FROM quiz_attempts
            WHERE progress_id IN ({placeholders})
        """)
        quiz_result = await db.execute(quiz_delete, params)
        quiz_count = quiz_result.rowcount
        print(f"   ✅ 删除了 {quiz_count} 条测试记录")

    # 现在删除进度记录
    progress_delete = text("""
        DELETE FROM progress
        WHERE document_id = :document_id AND user_id = :user_id
    """)
    result = await db.execute(progress_delete, {
        'document_id': document_id,
        'user_id': current_user.id
    })
    progress_count = result.rowcount
    print(f"   ✅ 删除了 {progress_count} 条学习进度记录")

    # 4. 删除小节记录 (subsections 表)
    subsection_delete = text("""
        DELETE FROM subsections
        WHERE document_id = :document_id AND user_id = :user_id
    """)
    result = await db.execute(subsection_delete, {
        'document_id': document_id,
        'user_id': current_user.id
    })
    subsection_count = result.rowcount
    print(f"   ✅ 删除了 {subsection_count} 条小节记录")

    # 5. 删除 ChromaDB 中的向量集合
    try:
        from app.core.chroma import delete_document_collection
        deleted = delete_document_collection(document.md5_hash)
        if deleted:
            print(f"   ✅ 删除了 ChromaDB 向量集合")
        else:
            print(f"   ⚠️  ChromaDB 集合不存在")
    except Exception as e:
        print(f"   ⚠️  删除 ChromaDB 数据失败: {e}")

    # 4. 删除文档记录
    await db.execute(
        delete(Document).where(Document.id == document_id)
    )
    await db.commit()

    print(f"\n{'='*60}")
    print(f"✅ 文档删除完成")
    print(f"   文档ID: {document_id}")
    print(f"   文件名: {document.filename}")
    print(f"   已删除:")
    print(f"      - 对话记录: {conversation_count} 条")
    print(f"      - 测试记录: {quiz_count} 条")
    print(f"      - 学习进度: {progress_count} 条")
    print(f"      - 小节记录: {subsection_count} 条")
    print(f"{'='*60}\n")

    return {
        "message": "文档删除成功",
        "document_id": document_id,
        "document_title": document.title,
        "deleted_records": {
            "conversations": conversation_count,
            "quiz_attempts": quiz_count,
            "progress": progress_count,
            "subsections": subsection_count
        }
    }


@router.get("/{document_id}/status")
async def get_document_status(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取文档处理状态和进度

    返回详细的处理进度，用于前端轮询更新
    """
    from sqlalchemy import select, text

    # 验证文档存在且属于当前用户
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )

    if document.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问此文档"
        )

    # 获取处理状态
    status_query = text("""
        SELECT
            id,
            filename,
            title,
            processing_status,
            has_text_layer,
            ocr_confidence,
            current_page,
            total_pages,
            total_chapters,
            uploaded_at
        FROM documents
        WHERE id = :document_id
    """)

    result = await db.execute(status_query, {'document_id': document_id})
    row = result.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档状态信息不存在"
        )

    # 解析状态
    status = row[3] or 'pending'
    has_text_layer = bool(row[4])
    ocr_confidence = row[5] or 0.0
    current_page = row[6] or 0
    total_pages = row[7] or 0
    total_chapters = row[8] or 0

    # 计算进度百分比
    progress_percentage = 0
    stage = ""
    stage_message = ""

    if status == 'pending':
        progress_percentage = 0
        stage = "等待处理"
        stage_message = "文档已上传，等待开始处理..."

    elif status == 'processing':
        progress_percentage = 25
        stage = "正在提取文本"
        stage_message = "正在从PDF中提取文本内容..."

    elif status == 'ocr_processing':
        if total_pages > 0:
            progress_percentage = min(90, int((current_page / total_pages) * 100))
        else:
            progress_percentage = 50
        stage = "正在OCR识别"
        stage_message = f"正在使用AI识别第 {current_page}/{total_pages} 页..."

    elif status == 'completed':
        progress_percentage = 100
        stage = "处理完成"
        stage_message = "文档已成功处理并可以使用"

    elif status == 'failed':
        progress_percentage = 0
        stage = "处理失败"
        stage_message = "文档处理失败，请尝试重新上传更清晰的文件"

    # 构建响应
    response = {
        "document_id": document_id,
        "filename": row[1],
        "title": row[2],
        "status": status,
        "stage": stage,
        "stage_message": stage_message,
        "progress_percentage": progress_percentage,
        "has_text_layer": has_text_layer,
        "ocr_confidence": ocr_confidence,
        "current_page": current_page,
        "total_pages": total_pages,
        "total_chapters": total_chapters,
        "is_scan": not has_text_layer,
        "uploaded_at": row[10].isoformat() if row[10] else None
    }

    # 添加提示信息
    if status == 'completed' and not has_text_layer:
        response['warning'] = "此文档通过OCR识别，建议核对专业术语和公式"
        response['ocr_notice'] = "扫描件识别准确率约85-95%，重要内容请手动核对"

    return response

