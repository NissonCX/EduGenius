"""
用户相关的 Pydantic 模型
"""
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime


class UserRegister(BaseModel):
    """用户注册请求"""
    email: EmailStr
    username: str
    password: str
    cognitive_level: Optional[int] = 1


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    email: str
    username: str
    cognitive_level: int
    total_documents_studied: int
    total_chapters_completed: int
    overall_progress_percentage: float
    created_at: datetime

    class Config:
        from_attributes = True


class UserLevelAssessment(BaseModel):
    """能力测评请求"""
    email: EmailStr
    answers: List[int]


class LevelRecommendation(BaseModel):
    """等级推荐响应"""
    recommended_level: int
    level_name: str
    avg_score: float
    total_questions: int
    message: str


class ConversationResponse(BaseModel):
    """对话记录响应"""
    id: int
    role: str
    content: str
    created_at: datetime


class HistoryResponse(BaseModel):
    """历史记录响应"""
    conversations: List[ConversationResponse]
    user_level: int
    competency_scores: dict


class CompetencyData(BaseModel):
    """能力数据"""
    comprehension: Optional[int] = None
    logic: Optional[int] = None
    terminology: Optional[int] = None
    memory: Optional[int] = None
    application: Optional[int] = None
    stability: Optional[int] = None
