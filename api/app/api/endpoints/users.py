"""
用户认证和历史记录 API 端点
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr

from app.db.database import get_db
from app.models.document import User, ConversationHistory, QuizAttempt, Progress
from app.schemas.user import (
    UserRegister,
    UserResponse,
    UserLevelAssessment,
    ConversationResponse,
    HistoryResponse,
    CompetencyData
)
from app.core.security import (
    verify_password,
    get_password_hash,
    create_token_for_user,
    Token
)

router = APIRouter(prefix="/api/users", tags=["users"])


# ============ 认证请求/响应模型 ============
class LoginRequest(BaseModel):
    """登录请求"""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    token_type: str
    user_id: int
    email: str
    username: str
    cognitive_level: int


# ============ 请求/响应模型 ============

class UserRegister(BaseModel):
    """用户注册请求"""
    email: EmailStr
    username: str
    password: str  # 前端应该哈希，但这里先接受
    cognitive_level: Optional[int] = 1  # L1-L5，默认 L1


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    email: str
    username: str
    cognitive_level: int
    total_documents_studied: int
    total_chapters_completed: int
    overall_progress_percentage: float
    created_at: datetime


class UserLevelAssessment(BaseModel):
    """能力测评请求"""
    email: EmailStr
    answers: List[int]  # 测评答案


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
    competency_scores: Optional[dict] = None


class CompetencyData(BaseModel):
    """能力数据"""
    comprehension: Optional[int] = None
    logic: Optional[int] = None
    terminology: Optional[int] = None
    memory: Optional[int] = None
    application: Optional[int] = None
    stability: Optional[int] = None


# ============ 端点实现 ============

@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """
    用户注册（带能力测评）

    - 支持直接选择 L1-L5 等级
    - 创建用户记录
    - 初始化学习统计数据
    """
    # 检查邮箱是否已存在
    from sqlalchemy import select
    from app.models.document import User as UserModel

    result = await db.execute(
        select(UserModel).where(UserModel.email == user_data.email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )

    # 检查用户名是否已存在
    result = await db.execute(
        select(UserModel).where(UserModel.username == user_data.username)
    )
    existing_username = result.scalar_one_or_none()

    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已被使用"
        )

    # 创建新用户（密码哈希）
    hashed_password = get_password_hash(user_data.password)
    new_user = UserModel(
        email=user_data.email,
        username=user_data.username,
        password=hashed_password,  # 存储哈希密码
        cognitive_level=user_data.cognitive_level
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.post("/login", response_model=LoginResponse)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录

    - 验证邮箱和密码
    - 返回 JWT Token
    - 返回用户基本信息
    """
    from app.models.document import User as UserModel

    # 查找用户
    result = await db.execute(
        select(UserModel).where(UserModel.email == credentials.email)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误"
        )

    # 验证密码
    if not verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误"
        )

    # 生成 JWT Token
    access_token = create_token_for_user(user.id, user.email)

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        username=user.username,
        cognitive_level=user.cognitive_level
    )


@router.post("/assess-level", response_model=dict)
async def assess_user_level(
    assessment: UserLevelAssessment,
    db: AsyncSession = Depends(get_db)
):
    """
    能力测评：根据用户答案自动确定 L1-L5 等级

    - 分析用户答题情况
    - 计算综合得分
    - 返回推荐等级
    """
    answers = assessment.answers

    # 简化的测评逻辑（实际可更复杂）
    if not answers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="答案不能为空"
        )

    # 计算得分
    total_score = sum(answers)
    avg_score = total_score / len(answers) if answers else 0

    # 根据得分确定等级
    if avg_score >= 90:
        recommended_level = 5
        level_name = "专家 (Expert)"
    elif avg_score >= 75:
        recommended_level = 4
        level_name = "高级 (Advanced)"
    elif avg_score >= 60:
        recommended_level = 3
        level_name = "进阶 (Intermediate)"
    elif avg_score >= 40:
        recommended_level = 2
        level_name = "入门 (Beginner)"
    else:
        recommended_level = 1
        level_name = "基础 (Foundation)"

    return {
        "recommended_level": recommended_level,
        "level_name": level_name,
        "avg_score": avg_score,
        "total_questions": len(answers),
        "message": f"根据您的答题情况，推荐您从 **{level_name}** (L{recommended_level}) 开始学习"
    }


@router.get("/{user_id}/history", response_model=HistoryResponse)
async def get_user_history(
    user_id: int,
    document_id: Optional[int] = None,
    chapter_number: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户对话历史和当前状态

    - 返回对话记录
    - 返回用户当前等级
    - 返回能力雷达图数据
    """
    # 获取用户信息
    from app.models.document import User as UserModel

    result = await db.execute(
        select(UserModel).where(UserModel.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 构建查询条件
    query = select(ConversationHistory).where(
        ConversationHistory.user_id == user_id
    )

    if document_id:
        query = query.where(ConversationHistory.document_id == document_id)

    if chapter_number:
        query = query.where(ConversationHistory.chapter_number == chapter_number)

    query = query.order_by(ConversationHistory.created_at).limit(50)

    result = await db.execute(query)
    conversations = result.scalars().all()

    # 获取能力评估数据（从最近的题目尝试记录计算）
    competency_result = await db.execute(
        select(QuizAttempt).where(
            QuizAttempt.user_id == user_id
        ).order_by(QuizAttempt.created_at.desc()).limit(20)
    )
    quiz_attempts = competency_result.scalars().all()

    # 计算六个维度的能力评分
    competency_scores = {
        "comprehension": 70,  # 理解力
        "logic": 68,          # 逻辑
        "terminology": 75,     # 术语
        "memory": 82,         # 记忆
        "application": 60,     # 应用
        "stability": 72        # 稳定性
    }

    if quiz_attempts:
        # 根据题目正确率调整评分
        correct_count = sum(1 for attempt in quiz_attempts if attempt.is_correct)
        total_count = len(quiz_attempts)
        if total_count > 0:
            base_score = (correct_count / total_count) * 100
            # 所有维度都基于这个正确率，加一些随机差异
            import random
            for key in competency_scores:
                competency_scores[key] = min(100, max(0, int(
                    base_score + random.uniform(-10, 10)
                )))

    return HistoryResponse(
        conversations=[
            ConversationResponse(
                id=conv.id,
                role=conv.role,
                content=conv.content,
                created_at=conv.created_at
            )
            for conv in conversations
        ],
        user_level=user.cognitive_level,
        competency_scores=competency_scores
    )


@router.get("/{user_id}/progress", response_model=List[dict])
async def get_user_progress(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取用户所有学习进度"""
    result = await db.execute(
        select(Progress).where(Progress.user_id == user_id)
    )
    progress_records = result.scalars().all()

    return [
        {
            "id": p.id,
            "document_id": p.document_id,
            "chapter_number": p.chapter_number,
            "chapter_title": p.chapter_title,
            "status": p.status,
            "completion_percentage": p.completion_percentage,
            "quiz_attempts": p.quiz_attempts,
            "quiz_success_rate": p.quiz_success_rate,
            "time_spent_minutes": p.time_spent_minutes
        }
        for p in progress_records
    ]


@router.post("/{user_id}/update-progress")
async def update_progress(
    user_id: int,
    progress_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    实时更新学习进度

    - 完成章节
    - 做题记录
    - 更新统计
    """
    progress_id = progress_data.get("progress_id")
    action = progress_data.get("action")  # 'complete_chapter', 'submit_quiz', etc.

    if action == "submit_quiz":
        # 记录题目尝试
        quiz_attempt = QuizAttempt(
            user_id=user_id,
            progress_id=progress_id,
            question_text=progress_data.get("question_text"),
            user_answer=progress_data.get("user_answer"),
            correct_answer=progress_data.get("correct_answer"),
            is_correct=1 if progress_data.get("is_correct") else 0,
            time_spent_seconds=progress_data.get("time_spent_seconds", 0)
        )
        db.add(quiz_attempt)

        # 更新进度统计
        result = await db.execute(
            select(Progress).where(Progress.id == progress_id)
        )
        progress = result.scalar_one_or_none()

        if progress:
            # 重新计算正确率
            quiz_result = await db.execute(
                select(QuizAttempt).where(
                    QuizAttempt.progress_id == progress_id
                )
            )
            all_attempts = quiz_result.scalars().all()

            if all_attempts:
                correct_count = sum(1 for a in all_attempts if a.is_correct)
                progress.quiz_success_rate = correct_count / len(all_attempts)
                progress.quiz_attempts = len(all_attempts)

            await db.commit()

    elif action == "complete_chapter":
        # 完成章节
        result = await db.execute(
            select(Progress).where(Progress.id == progress_id)
        )
        progress = result.scalar_one_or_none()

        if progress:
            progress.status = "completed"
            progress.completion_percentage = 100.0
            progress.completed_at = datetime.now()

            # 更新用户总体进度
            user_result = await db.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            user = user_result.scalar_one_or_none()

            if user:
                user.total_chapters_completed += 1
                # 重新计算总体进度百分比
                total_progress_result = await db.execute(
                    select(Progress).where(Progress.user_id == user_id)
                )
                all_progress = total_progress_result.scalars().all()
                if all_progress:
                    completed = sum(1 for p in all_progress if p.status == "completed")
                    user.overall_progress_percentage = (completed / len(all_progress)) * 100

            await db.commit()

    return {
        "status": "success",
        "message": "进度已更新"
    }


@router.get("/{user_id}/stats")
async def get_user_stats(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取用户学习统计"""
    from app.models.document import User as UserModel

    result = await db.execute(
        select(UserModel).where(UserModel.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 获取详细进度
    progress_result = await db.execute(
        select(Progress).where(Progress.user_id == user_id)
    )
    progress_records = progress_result.scalars().all()

    # 统计各状态章节数
    status_counts = {
        "not_started": 0,
        "in_progress": 0,
        "completed": 0,
        "locked": 0
    }

    for p in progress_records:
        status_counts[p.status] = status_counts.get(p.status, 0) + 1

    return {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "cognitive_level": user.cognitive_level,
        "total_documents_studied": user.total_documents_studied,
        "total_chapters_completed": user.total_chapters_completed,
        "overall_progress_percentage": user.overall_progress_percentage,
        "chapter_counts": status_counts,
        "total_chapters": len(progress_records)
    }


@router.post("/{user_id}/save-conversation")
async def save_conversation(
    user_id: int,
    conversation_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    保存单条对话记录

    - 保存用户消息或 AI 回复
    - 自动关联到章节和文档
    """
    from app.models.document import User as UserModel

    # 验证用户存在
    result = await db.execute(
        select(UserModel).where(UserModel.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 创建对话记录
    conversation = ConversationHistory(
        user_id=user_id,
        document_id=conversation_data.get("document_id", 1),
        chapter_number=conversation_data.get("chapter_number", 1),
        role=conversation_data.get("role", "user"),
        content=conversation_data.get("content", ""),
        student_level_at_time=user.cognitive_level
    )

    db.add(conversation)
    await db.commit()

    return {
        "status": "success",
        "message": "对话已保存",
        "id": conversation.id
    }
