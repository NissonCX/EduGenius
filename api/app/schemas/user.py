"""
用户相关的 Pydantic 模型

教学风格说明 (Teaching Style):
- 1 (温柔): 耐心细致，用简单的例子和鼓励帮助学生理解
- 2 (耐心): 循序渐进，提供详细的讲解和指导
- 3 (标准): 平衡严谨，既讲清原理又注重应用
- 4 (严格): 注重细节，要求深入理解每一步推理
- 5 (严厉): 挑战思维，培养独立解决问题的能力
"""
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime


class UserRegister(BaseModel):
    """用户注册请求"""
    email: EmailStr
    username: str
    password: str
    # 教学风格偏好 (1-5)，默认为 3 (标准)
    preferred_teaching_style: Optional[int] = Field(
        default=3,
        ge=1,
        le=5,
        description="教学风格偏好: 1=温柔, 2=耐心, 3=标准, 4=严格, 5=严厉"
    )


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    email: str
    username: str
    # 使用 teaching_style 而非 cognitive_level (保持向后兼容)
    teaching_style: int = Field(alias="cognitive_level", description="教学风格偏好 (1-5)")
    total_documents_studied: int
    total_chapters_completed: int
    overall_progress_percentage: float
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True  # 允许字段别名


class UserLevelAssessment(BaseModel):
    """能力测评请求（已弃用，保留以兼容）"""
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
