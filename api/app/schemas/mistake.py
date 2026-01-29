"""
错题本相关的 Pydantic 模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class MistakeFilter(BaseModel):
    """错题筛选条件"""
    chapter_number: Optional[int] = None
    competency_dimension: Optional[str] = None
    difficulty: Optional[int] = None
    is_mastered: Optional[bool] = None
    limit: int = Field(default=50, ge=1, le=100)


class MistakeResponse(BaseModel):
    """错题响应"""
    id: int
    question_id: int
    question_text: str
    user_answer: str
    correct_answer: str
    explanation: Optional[str] = None
    is_correct: bool
    competency_dimension: Optional[str] = None
    difficulty: int
    chapter_number: int
    chapter_title: Optional[str] = None
    is_mastered: bool
    attempts_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MistakeListResponse(BaseModel):
    """错题列表响应"""
    mistakes: List[MistakeResponse]
    total: int
    page: int
    page_size: int


class MarkMasteredRequest(BaseModel):
    """标记掌握请求"""
    is_mastered: bool = Field(..., description="是否掌握")


class MistakeAnalysis(BaseModel):
    """错题分析"""
    dimension: str
    dimension_name: str
    total_mistakes: int
    mastered_count: int
    mistake_rate: float
    priority: int  # 1-5，1最高优先级
    recommendations: List[str]


class MistakeAnalysisResponse(BaseModel):
    """错题分析响应"""
    total_mistakes: int
    mastered_mistakes: int
    analysis_by_dimension: List[MistakeAnalysis]
    weak_dimensions: List[str]
    suggested_review_plan: List[str]


class PracticeConfig(BaseModel):
    """专项练习配置"""
    dimension: Optional[str] = Field(None, description="针对性练习的维度")
    chapter_number: Optional[int] = Field(None, description="针对性练习的章节")
    difficulty: Optional[int] = Field(None, description="针对性练习的难度")
    count: int = Field(default=10, ge=1, le=20, description="练习题目数量")
    include_mastered: bool = Field(default=False, description="是否包含已掌握的题目")


class PracticeQuestion(BaseModel):
    """练习题目"""
    id: int
    question_text: str
    options: Optional[Dict[str, str]] = None
    correct_answer: str
    explanation: Optional[str] = None
    difficulty: int
    competency_dimension: Optional[str] = None
    is_mastered: bool
    mistake_count: int  # 答错次数


class PracticeSessionResponse(BaseModel):
    """专项练习响应"""
    session_id: str
    questions: List[PracticeQuestion]
    total_questions: int
    focus_area: str
