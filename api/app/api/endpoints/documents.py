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
    # 保存到临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
        tmp_file.write(await file.read())
        tmp_file_path = tmp_file.name

    try:
        # 计算文档处理器
        processor = DocumentProcessor()
        md5_hash = processor.calculate_md5(tmp_file_path)

        # 检查是否已存在
        existing_document = await get_document_by_md5(db, md5_hash)

        if existing_document:
            # 文档已存在 - 返回已有记录
            return DocumentUploadResponse(
                message="✨ 已从记忆库加载（文档已存在）",
                is_duplicate=True,
                document_id=existing_document.id,
                md5_hash=md5_hash,
                processing_status=existing_document.processing_status
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
            total_chapters=1,  # 简化：暂时设为1章
            title=title or file.filename
        )

        # 创建初始进度记录
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
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)


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


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "EduGenius API"}
