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


@router.get("/{document_id}/chapters", response_model=list[ChapterResponse])
async def get_document_chapters(
    document_id: int,
    user_email: str = DEFAULT_USER_EMAIL,
    db: AsyncSession = Depends(get_db)
):
    """
    Get chapter list with progress status for a document.
    """
    # Get user
    user, _ = await get_or_create_user(db, user_email, DEFAULT_USERNAME)

    # Get progress entries
    progress_entries = await get_user_progress_for_document(db, user.id, document_id)

    if not progress_entries:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到章节信息"
        )

    return [
        ChapterResponse(
            chapter_number=p.chapter_number,
            chapter_title=p.chapter_title,
            status=p.status,
            completion_percentage=p.completion_percentage
        )
        for p in progress_entries
    ]


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "EduGenius API"}
