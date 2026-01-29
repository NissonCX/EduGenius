"""
FastAPI endpoints for document upload and processing with MD5 deduplication.
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import tempfile
import os

from app.db.database import get_db
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
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentResponse,
    ChapterResponse,
    ProgressCreate
)
from app.models.document import User

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
    """
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
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        # 计算文档处理器
        processor = DocumentProcessor()
        md5_hash = processor.calculate_md5(tmp_file_path)

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
            
            # 为新用户创建章节（从 ChromaDB 恢复文本）
            try:
                from app.services.chapter_divider import ChapterDivider
                from app.core.chroma import get_document_collection
                
                divider = ChapterDivider()
                
                # 从 ChromaDB 恢复文档文本
                collection = get_document_collection(md5_hash)
                if collection and collection.count() > 0:
                    results = collection.get()
                    if results and results['documents']:
                        document_text = "\n\n".join(results['documents'])
                        
                        chapters = await divider.divide_document_into_chapters(
                            document_id=new_document.id,
                            user_id=current_user.id,
                            document_text=document_text,
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

        # 解析文档、切分、向量化
        result = await process_uploaded_document(
            file_path=tmp_file_path,
            title=title or file.filename,
            user_email=current_user.email
        )

        # 创建数据库记录
        from app.schemas.document import DocumentCreate
        document_data = DocumentCreate(
            filename=file.filename,
            file_type=file_type,
            file_size=os.path.getsize(tmp_file_path),
            md5_hash=md5_hash
        )

        new_document = await create_document(db, document_data, current_user.id)

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

        # 🎯 核心：自动划分章节
        try:
            from app.services.chapter_divider import ChapterDivider

            divider = ChapterDivider()
            # 使用所有文本内容，而不是只用第一个
            document_text = "\n\n".join(result['texts']) if result['texts'] else ""

            if document_text:
                chapters = await divider.divide_document_into_chapters(
                    document_id=new_document.id,
                    user_id=current_user.id,
                    document_text=document_text,
                    db=db
                )

                print(f"✅ 文档处理完成，共划分 {len(chapters)} 个章节")
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
        # 清理临时文件
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
            "quiz_success_rate": progress.quiz_success_rate
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
    
    # 删除文档
    await db.execute(
        delete(Document).where(Document.id == document_id)
    )
    await db.commit()
    
    return {"message": "文档删除成功", "document_id": document_id}

