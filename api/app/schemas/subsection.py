"""
Subsection Pydantic 模式
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SubsectionBase(BaseModel):
    """小节基础模式"""
    document_id: int
    chapter_number: int
    subsection_number: int
    subsection_title: str = Field(..., min_length=1, max_length=500)
    content_summary: Optional[str] = None
    estimated_time_minutes: int = Field(default=15, ge=1, le=180)


class SubsectionCreate(SubsectionBase):
    """创建小节"""
    pass


class SubsectionResponse(SubsectionBase):
    """小节响应"""
    id: int
    created_at: datetime
    is_completed: bool = False
    progress: float = 0.0

    class Config:
        from_attributes = True
