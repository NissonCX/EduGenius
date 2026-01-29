"""
题目和答题相关的 Pydantic 模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class QuestionGenerate(BaseModel):
    """生成题目请求"""
    document_id: int = Field(..., description="文档ID")
    chapter_number: int = Field(..., description="章节编号")
    question_type: str = Field(..., description="题目类型: choice, fill_blank, essay")
    difficulty: int = Field(default=3, ge=1, le=5, description="难度等级 1-5")
    count: int = Field(default=1, ge=1, le=10, description="生成题目数量")


class QuestionOption(BaseModel):
    """选择题选项"""
    A: str
    B: str
    C: Optional[str] = None
    D: Optional[str] = None


class QuestionResponse(BaseModel):
    """题目响应"""
    id: int
    document_id: int
    chapter_number: int
    question_type: str
    question_text: str
    options: Optional[Dict[str, str]] = None
    correct_answer: str
    explanation: Optional[str] = None
    difficulty: int
    competency_dimension: Optional[str] = None

    class Config:
        from_attributes = True


class QuestionListResponse(BaseModel):
    """题目列表响应"""
    questions: List[QuestionResponse]
    total: int
    chapter_number: int


class QuizSubmit(BaseModel):
    """提交答案请求"""
    user_id: int
    question_id: int
    user_answer: str
    time_spent_seconds: Optional[int] = None


class QuizSubmitResponse(BaseModel):
    """提交答案响应"""
    is_correct: bool
    correct_answer: str
    explanation: Optional[str] = None
    feedback: str
    competency_dimension: Optional[str] = None


class ChapterTestRequest(BaseModel):
    """章节测试请求"""
    user_id: int
    document_id: int
    chapter_number: int
    question_count: int = Field(default=10, ge=5, le=20, description="题目数量")


class ChapterTestResponse(BaseModel):
    """章节测试响应"""
    test_id: str
    questions: List[QuestionResponse]
    total_questions: int
    time_limit_minutes: Optional[int] = None


class ChapterTestSubmit(BaseModel):
    """提交章节测试"""
    user_id: int
    test_id: str
    answers: List[Dict[str, int]]  # [{"question_id": 1, "answer": "A"}, ...]


class ChapterTestResult(BaseModel):
    """章节测试结果"""
    score: float  # 百分比
    correct_count: int
    total_count: int
    competency_scores: Dict[str, float]
    passed: bool  # 是否通过（>=60%）
    recommendations: List[str]
