"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime


# ============== User Schemas ==============
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    cognitive_level: int = Field(default=1, ge=1, le=5)


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    id: int
    total_documents_studied: int
    total_chapters_completed: int
    overall_progress_percentage: float
    created_at: datetime

    class Config:
        from_attributes = True


# ============== Document Schemas ==============
class DocumentBase(BaseModel):
    filename: str
    file_type: str = Field(..., pattern=r'^(pdf|txt|docx)$')


class DocumentCreate(DocumentBase):
    file_size: int
    md5_hash: str


class DocumentResponse(DocumentBase):
    id: int
    md5_hash: str
    file_size: int
    title: Optional[str] = None
    total_pages: int
    total_chapters: int
    processing_status: str
    chroma_collection_name: Optional[str] = None
    uploaded_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    """Response for document upload with MD5 deduplication."""
    message: str
    is_duplicate: bool  # True if document already exists
    document_id: Optional[int] = None
    md5_hash: str
    processing_status: str


# ============== Progress Schemas ==============
class ProgressBase(BaseModel):
    chapter_number: int
    chapter_title: Optional[str] = None


class ProgressCreate(ProgressBase):
    user_id: int
    document_id: int
    cognitive_level_assigned: int = Field(default=1, ge=1, le=5)


class ProgressUpdate(BaseModel):
    status: str = Field(..., pattern=r'^(not_started|in_progress|completed|locked)$')
    completion_percentage: float = Field(default=0.0, ge=0.0, le=100.0)


class ProgressResponse(ProgressBase):
    id: int
    user_id: int
    document_id: int
    status: str
    completion_percentage: float
    cognitive_level_assigned: int
    time_spent_minutes: int
    quiz_attempts: int
    quiz_success_rate: float
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============== Chapter Response ==============
class ChapterResponse(BaseModel):
    """Chapter information for navigation."""
    chapter_number: int
    chapter_title: Optional[str] = None
    status: str
    completion_percentage: float
