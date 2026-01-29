"""
Subsection 数据模型
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.db.database import Base


class Subsection(Base):
    """小节模型"""
    __tablename__ = "subsections"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    subsection_number = Column(Integer, nullable=False)
    subsection_title = Column(String(500))
    content_summary = Column(Text)
    estimated_time_minutes = Column(Integer, default=15)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
