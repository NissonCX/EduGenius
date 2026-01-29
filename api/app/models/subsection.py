"""
Subsection model for storing section-level learning progress
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from datetime import datetime


class Subsection(object):
    """小节学习进度表 - 使用table定义而不是declarative_base"""
    
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
