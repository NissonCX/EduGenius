"""
题目和答题相关的 Pydantic 模型
"""
from pydantic import BaseModel, Field, validator, field_validator
from typing import List, Optional, Dict
from datetime import datetime


class QuestionGenerate(BaseModel):
    """生成题目请求"""
    document_id: int = Field(..., gt=0, description="文档ID")
    chapter_number: int = Field(..., ge=1, le=100, description="章节编号")
    question_type: str = Field(..., description="题目类型: choice, fill_blank, essay")
    difficulty: int = Field(default=3, ge=1, le=5, description="难度等级 1-5")
    count: int = Field(default=1, ge=1, le=10, description="生成题目数量")

    @field_validator('question_type')
    @classmethod
    def validate_question_type(cls, v):
        allowed_types = ['choice', 'fill_blank', 'essay']
        if v not in allowed_types:
            raise ValueError(f'题目类型必须是以下之一: {", ".join(allowed_types)}')
        return v

    @field_validator('chapter_number')
    @classmethod
    def validate_chapter_number(cls, v):
        if v > 50:
            raise ValueError('章节编号不能超过50')
        return v


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
    user_id: int = Field(..., gt=0, description="用户ID")
    question_id: int = Field(..., gt=0, description="题目ID")
    user_answer: str = Field(..., min_length=1, max_length=1000, description="用户答案")
    time_spent_seconds: Optional[int] = Field(None, ge=0, le=3600, description="答题时间（秒）")

    @field_validator('user_answer')
    @classmethod
    def validate_user_answer(cls, v):
        if not v or not v.strip():
            raise ValueError('答案不能为空')
        return v.strip()


class QuizSubmitResponse(BaseModel):
    """提交答案响应"""
    is_correct: bool
    correct_answer: str
    explanation: Optional[str] = None
    feedback: str
    competency_dimension: Optional[str] = None


class ChapterTestRequest(BaseModel):
    """章节测试请求"""
    user_id: int = Field(..., gt=0, description="用户ID")
    document_id: int = Field(..., gt=0, description="文档ID")
    chapter_number: int = Field(..., ge=1, le=100, description="章节编号")
    question_count: int = Field(default=10, ge=5, le=20, description="题目数量")

    @field_validator('chapter_number')
    @classmethod
    def validate_chapter_number(cls, v):
        if v > 50:
            raise ValueError('章节编号不能超过50')
        return v


class ChapterTestResponse(BaseModel):
    """章节测试响应"""
    test_id: str
    questions: List[QuestionResponse]
    total_questions: int
    time_limit_minutes: Optional[int] = None


class ChapterTestSubmit(BaseModel):
    """提交章节测试"""
    user_id: int = Field(..., gt=0, description="用户ID")
    test_id: str = Field(..., min_length=1, description="测试ID")
    answers: List[Dict[str, int]] = Field(..., min_length=1, description="答案列表")

    @field_validator('answers')
    @classmethod
    def validate_answers(cls, v):
        if not v:
            raise ValueError('答案列表不能为空')
        for answer in v:
            if 'question_id' not in answer:
                raise ValueError('每个答案必须包含 question_id')
        return v


class ChapterTestResult(BaseModel):
    """章节测试结果"""
    score: float  # 百分比
    correct_count: int
    total_count: int
    competency_scores: Dict[str, float]
    passed: bool  # 是否通过（>=60%）
    recommendations: List[str]
