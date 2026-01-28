"""
CRUD operations with MD5-based deduplication logic.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Tuple
import hashlib

from app.models.document import Document, User, Progress
from app.schemas.document import DocumentCreate, ProgressCreate


# ============== MD5 Hash Calculation ==============
def calculate_md5_hash(file_content: bytes) -> str:
    """
    Calculate MD5 hash of file content.

    Args:
        file_content: Raw bytes of the file

    Returns:
        32-character hexadecimal MD5 hash string
    """
    return hashlib.md5(file_content).hexdigest()


# ============== Document CRUD ==============
async def get_document_by_md5(
    db: AsyncSession,
    md5_hash: str
) -> Optional[Document]:
    """
    Check if document already exists by MD5 hash.

    Args:
        db: Database session
        md5_hash: 32-character MD5 hash

    Returns:
        Document if exists, None otherwise
    """
    result = await db.execute(
        select(Document).where(Document.md5_hash == md5_hash)
    )
    return result.scalar_one_or_none()


async def create_document(
    db: AsyncSession,
    document_data: DocumentCreate,
    user_id: int
) -> Document:
    """
    Create a new document entry in database.

    Args:
        db: Database session
        document_data: Document creation data
        user_id: ID of user uploading the document

    Returns:
        Created Document instance
    """
    db_document = Document(
        md5_hash=document_data.md5_hash,
        filename=document_data.filename,
        file_type=document_data.file_type,
        file_size=document_data.file_size,
        uploaded_by=user_id,
        processing_status="processing",
        chroma_collection_name=f"doc_{document_data.md5_hash}"
    )

    db.add(db_document)
    await db.commit()
    await db.refresh(db_document)

    return db_document


async def get_document_by_id(
    db: AsyncSession,
    document_id: int
) -> Optional[Document]:
    """
    Retrieve document by ID.

    Args:
        db: Database session
        document_id: Document ID

    Returns:
        Document if exists, None otherwise
    """
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    return result.scalar_one_or_none()


async def update_document_status(
    db: AsyncSession,
    document_id: int,
    status: str,
    total_pages: int = 0,
    total_chapters: int = 0,
    title: Optional[str] = None
) -> Optional[Document]:
    """
    Update document processing status.

    Args:
        db: Database session
        document_id: Document ID
        status: New processing status
        total_pages: Total pages in document
        total_chapters: Total chapters detected
        title: Document title

    Returns:
        Updated Document if exists, None otherwise
    """
    document = await get_document_by_id(db, document_id)
    if document:
        document.processing_status = status
        if total_pages:
            document.total_pages = total_pages
        if total_chapters:
            document.total_chapters = total_chapters
        if title:
            document.title = title

        await db.commit()
        await db.refresh(document)

    return document


# ============== User CRUD ==============
async def get_or_create_user(
    db: AsyncSession,
    email: str,
    username: str,
    default_cognitive_level: int = 1
) -> Tuple[User, bool]:
    """
    Get existing user or create new one.

    Args:
        db: Database session
        email: User email
        username: Username
        default_cognitive_level: Default L1-L5 level for new users

    Returns:
        Tuple of (User instance, is_new: bool)
    """
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    if user:
        return user, False

    # Create new user
    new_user = User(
        email=email,
        username=username,
        cognitive_level=default_cognitive_level
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user, True


async def update_user_cognitive_level(
    db: AsyncSession,
    user_id: int,
    new_level: int
) -> Optional[User]:
    """
    Update user's cognitive level.

    Args:
        db: Database session
        user_id: User ID
        new_level: New L1-L5 level

    Returns:
        Updated User if exists, None otherwise
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user:
        user.cognitive_level = new_level
        await db.commit()
        await db.refresh(user)

    return user


# ============== Progress CRUD ==============
async def create_progress(
    db: AsyncSession,
    progress_data: ProgressCreate
) -> Progress:
    """
    Create initial progress entry for a chapter.

    Args:
        db: Database session
        progress_data: Progress creation data

    Returns:
        Created Progress instance
    """
    db_progress = Progress(
        user_id=progress_data.user_id,
        document_id=progress_data.document_id,
        chapter_number=progress_data.chapter_number,
        chapter_title=progress_data.chapter_title,
        cognitive_level_assigned=progress_data.cognitive_level_assigned,
        status="not_started",
        completion_percentage=0.0
    )

    db.add(db_progress)
    await db.commit()
    await db.refresh(db_progress)

    return db_progress


async def get_user_progress_for_document(
    db: AsyncSession,
    user_id: int,
    document_id: int
) -> list[Progress]:
    """
    Get all progress entries for a user-document pair.

    Args:
        db: Database session
        user_id: User ID
        document_id: Document ID

    Returns:
        List of Progress entries ordered by chapter number
    """
    result = await db.execute(
        select(Progress)
        .where(Progress.user_id == user_id, Progress.document_id == document_id)
        .order_by(Progress.chapter_number)
    )
    return result.scalars().all()
