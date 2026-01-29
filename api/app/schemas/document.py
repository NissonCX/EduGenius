"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime


# ============== User Schemas ==============
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    cognitive_level: int = Field(default=1, ge=1, le=5)

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not v or not v.strip():
            raise ValueError('用户名不能为空')
        # 只允许字母、数字、下划线
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('用户名只能包含字母、数字和下划线')
        return v.strip()


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
    filename: str = Field(..., min_length=1, max_length=255)
    file_type: str = Field(..., pattern=r'^(pdf|txt|docx)$')

    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v):
        if not v or not v.strip():
            raise ValueError('文件名不能为空')
        # 检查文件名是否包含非法字符
        import re
        if re.search(r'[<>:"/\\|?*]', v):
            raise ValueError('文件名包含非法字符')
        return v.strip()


class DocumentCreate(DocumentBase):
    file_size: int = Field(..., gt=0, le=52428800)  # 最大 50MB
    md5_hash: str = Field(..., min_length=32, max_length=32)

    @field_validator('md5_hash')
    @classmethod
    def validate_md5_hash(cls, v):
        import re
        if not re.match(r'^[a-f0-9]{32}$', v.lower()):
            raise ValueError('无效的 MD5 哈希值')
        return v.lower()


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
    user_id: int = Field(..., gt=0)
    document_id: int = Field(..., gt=0)
    cognitive_level_assigned: int = Field(default=1, ge=1, le=5)

    @field_validator('chapter_number')
    @classmethod
    def validate_chapter_number(cls, v):
        if v < 1 or v > 100:
            raise ValueError('章节编号必须在 1-100 之间')
        return v


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
