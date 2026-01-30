"""
Subsection model for storing section-level learning progress
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from datetime import datetime


# Subsection 表定义（手动定义 Table）
from sqlalchemy import Table, MetaData
from app.models.document import Base

# 定义 subsections 表
subsections_table = Table(
    'subsections',
    Base.metadata,
    Column('id', Integer, primary_key=True, index=True),
    Column('user_id', Integer, ForeignKey('users.id'), nullable=False),
    Column('document_id', Integer, ForeignKey('documents.id'), nullable=False),
    Column('chapter_number', Integer, nullable=False),
    Column('subsection_number', String(50), nullable=False),
    Column('subsection_title', String(255), nullable=False),
    Column('page_number', Integer, nullable=True),
    Column('cognitive_level_assigned', Integer, default=3),
    Column('completion_percentage', Float, default=0.0),
    Column('time_spent_minutes', Float, default=0.0),
    Column('content_summary', String(1000), nullable=True),
    Column('estimated_time_minutes', Integer, nullable=True),
    Column('created_at', DateTime, default=datetime.utcnow),
    UniqueConstraint('user_id', 'document_id', 'chapter_number', 'subsection_number', name='unique_subsection')
)

# 为了向后兼容，保留旧的类定义（但不再使用）
class Subsection:
    """小节学习进度表 - 向后兼容类"""

    __tablename__ = "subsections"

    # 这些字段会在SQLAlchemy中使用table定义
    def __init__(self, user_id, document_id, chapter_number, subsection_number,
                 subsection_title, page_number=None, cognitive_level_assigned=3,
                 completion_percentage=0.0, time_spent_minutes=0.0):
        self.user_id = user_id
        self.document_id = document_id
        self.chapter_number = chapter_number
        self.subsection_number = subsection_number
        self.subsection_title = subsection_title
        self.page_number = page_number
        self.cognitive_level_assigned = cognitive_level_assigned
        self.completion_percentage = completion_percentage
        self.time_spent_minutes = time_spent_minutes

    def __repr__(self):
        return f"<Subsection(ch={self.chapter_number}, sec={self.subsection_number}, title={self.subsection_title})>"
