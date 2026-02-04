"""
用户认证和历史记录 API 端点
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, EmailStr
import re

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
    create_refresh_token,
    verify_token,
    get_current_user_optional,
    Token
)
from app.core.constants import (
    LEVEL_THRESHOLDS,
    LEVEL_NAMES,
    COMPLETION_THRESHOLD,
    DEFAULT_COMPETENCY_SCORE,
    PASSWORD_REQUIREMENTS
)

router = APIRouter(prefix="/api/users", tags=["users"])


# ============ 密码验证函数 ============
def validate_password(password: str) -> tuple[bool, str]:
    """
    验证密码复杂度

    Args:
        password: 密码字符串

    Returns:
        tuple[bool, str]: (是否有效, 错误信息)
    """
    if len(password) < 8:
        return False, "密码长度至少8位"

    if not re.search(r"[A-Z]", password):
        return False, "密码必须包含至少一个大写字母"

    if not re.search(r"[a-z]", password):
        return False, "密码必须包含至少一个小写字母"

    if not re.search(r"\d", password):
        return False, "密码必须包含至少一个数字"

    # 可选：特殊字符
    # if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
    #     return False, "密码必须包含至少一个特殊字符"

    return True, ""


# ============ 能力评估辅助函数 ============
def classify_question_type(question_text: str) -> str:
    """
    根据题目文本判断题目类型

    Args:
        question_text: 题目文本

    Returns:
        str: 题目类型 (comprehension, logic, terminology, memory, application)
    """
    question_lower = question_text.lower()

    # 理解类题目关键词
    comprehension_keywords = ['理解', '解释', '说明', '描述', '阐述', '分析', '总结', '概括',
                             'understand', 'explain', 'describe', 'analyze', 'summarize']
    # 逻辑类题目关键词
    logic_keywords = ['推导', '证明', '为什么', '原因', '因此', '逻辑', '推理', '判断',
                      'derive', 'prove', 'why', 'reason', 'logic', 'deduce']
    # 术语类题目关键词
    terminology_keywords = ['定义', '什么是', '术语', '概念', '名称', '符号', '表示',
                            'define', 'what is', 'term', 'concept', 'definition']
    # 记忆类题目关键词
    memory_keywords = ['记住', '背诵', '列举', '写出', '公式', '定理', '定律',
                       'memorize', 'list', 'write', 'formula', 'theorem']
    # 应用类题目关键词
    application_keywords = ['计算', '求解', '应用', '使用', '实例', '例子', '实际',
                            'calculate', 'solve', 'apply', 'example', 'practice']

    # 统计各类型关键词出现次数
    scores = {
        'comprehension': sum(1 for kw in comprehension_keywords if kw in question_lower),
        'logic': sum(1 for kw in logic_keywords if kw in question_lower),
        'terminology': sum(1 for kw in terminology_keywords if kw in question_lower),
        'memory': sum(1 for kw in memory_keywords if kw in question_lower),
        'application': sum(1 for kw in application_keywords if kw in question_lower),
    }

    # 返回得分最高的类型，如果没有匹配则默认为理解类
    max_score = max(scores.values())
    if max_score == 0:
        return 'comprehension'  # 默认类型

    return max(scores, key=scores.get)


def calculate_competency_scores(quiz_attempts_with_questions) -> Dict[str, int]:
    """
    基于答题记录计算六维能力评分（使用Question表中的competency_dimension）

    Args:
        quiz_attempts_with_questions: (QuizAttempt, Question) 元组列表

    Returns:
        Dict[str, int]: 六维能力评分
    """
    # 初始化各维度的数据
    dimensions = {
        'comprehension': {'correct': 0, 'total': 0},
        'logic': {'correct': 0, 'total': 0},
        'terminology': {'correct': 0, 'total': 0},
        'memory': {'correct': 0, 'total': 0},
        'application': {'correct': 0, 'total': 0},
        'stability': {'first_attempts': [], 'repeats': 0}
    }

    for attempt, question in quiz_attempts_with_questions:
        # 使用 Question 表中的 competency_dimension
        dimension = question.competency_dimension or 'comprehension'

        if dimension in dimensions and dimension != 'stability':
            dimensions[dimension]['total'] += 1
            if attempt.is_correct:
                dimensions[dimension]['correct'] += 1

        # 用于计算稳定性（基于重复答题）
        question_key = f"{question.id}"
        if question_key not in dimensions['stability']:
            dimensions['stability']['first_attempts'].append(attempt.is_correct)
        dimensions['stability']['repeats'] += 1

    # 计算各维度得分
    scores = {}

    for dimension, data in dimensions.items():
        if dimension == 'stability':
            # 计算稳定性
            first_attempts = data['first_attempts']
            if first_attempts:
                stability_score = int((sum(first_attempts) / len(first_attempts)) * 100)
                scores[dimension] = stability_score
            else:
                scores[dimension] = 50
        else:
            if data['total'] == 0:
                scores[dimension] = 50
            else:
                # 正确率 * 100
                accuracy_rate = data['correct'] / data['total']
                base_score = accuracy_rate * 100

                # 数量加成：题目越多，分数越可信
                count_bonus = min(10, data['total'] * 2)

                # 最终分数
                final_score = min(100, max(0, int(base_score + count_bonus)))
                scores[dimension] = final_score

    return scores

# ============ 认证请求/响应模型 ============
class LoginRequest(BaseModel):
    """登录请求"""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    refresh_token: str
    token_type: str
    user_id: int
    email: str
    username: str
    teaching_style: int  # 导师风格偏好 (1-5)


class RefreshTokenRequest(BaseModel):
    """Refresh Token 请求"""
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Refresh Token 响应"""
    access_token: str
    refresh_token: str
    token_type: str


# ============ 请求/响应模型 ============

class UserRegister(BaseModel):
    """用户注册请求"""
    email: EmailStr
    username: str
    password: str  # 前端应该哈希，但这里先接受
    preferred_teaching_style: Optional[int] = 3  # 1-5，默认3（标准）


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


async def get_or_create_progress(
    user_id: int,
    document_id: int,
    chapter_number: int,
    chapter_title: str,
    db: AsyncSession
) -> Progress:
    """
    获取或创建进度记录

    Args:
        user_id: 用户 ID
        document_id: 文档 ID
        chapter_number: 章节编号
        chapter_title: 章节标题
        db: 数据库 session

    Returns:
        Progress: 进度记录对象
    """
    # 尝试获取现有进度
    result = await db.execute(
        select(Progress).where(
            Progress.user_id == user_id,
            Progress.document_id == document_id,
            Progress.chapter_number == chapter_number
        )
    )
    progress = result.scalar_one_or_none()

    if not progress:
        # 创建新进度记录
        progress = Progress(
            user_id=user_id,
            document_id=document_id,
            chapter_number=chapter_number,
            chapter_title=chapter_title,
            status="in_progress",
            completion_percentage=0.0,
            cognitive_level_assigned=None,  # 将从用户获取
            time_spent_minutes=0,
            quiz_attempts=0,
            quiz_success_rate=0.0
        )
        db.add(progress)
        await db.commit()
        await db.refresh(progress)
    else:
        # 如果已锁定，解锁它
        if progress.status == "locked":
            progress.status = "in_progress"
            await db.commit()

    return progress


async def update_progress_activity(
    progress_id: int,
    time_spent_add: int = 1,
    db: AsyncSession = None
) -> Progress:
    """
    更新进度活动（时间和最后访问时间）

    Args:
        progress_id: 进度 ID
        time_spent_add: 增加的时间（分钟）
        db: 数据库 session

    Returns:
        Progress: 更新后的进度对象
    """
    result = await db.execute(
        select(Progress).where(Progress.id == progress_id)
    )
    progress = result.scalar_one_or_none()

    if progress:
        from datetime import datetime
        progress.last_accessed_at = datetime.now()
        progress.time_spent_minutes = (progress.time_spent_minutes or 0) + time_spent_add
        await db.commit()
        await db.refresh(progress)

    return progress


# ============ 端点实现 ============

@router.post(
    "/register",
    response_model=LoginResponse,
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
    description="""
    创建新用户账户并自动登录。

    **教学风格说明:**
    - 1 (温柔): 耐心细致，用简单的例子和鼓励帮助学生理解
    - 2 (耐心): 循序渐进，提供详细的讲解和指导
    - 3 (标准): 平衡严谨，既讲清原理又注重应用
    - 4 (严格): 注重细节，要求深入理解每一步推理
    - 5 (严厉): 挑战思维，培养独立解决问题的能力

    **密码要求:**
    - 最少 8 个字符
    - 至少一个大写字母
    - 至少一个小写字母
    - 至少一个数字
    """,
    responses={
        201: {"description": "注册成功"},
        400: {"description": "请求参数错误（邮箱已存在、用户名已使用或密码不符合要求）"}
    }
)
async def register_user(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """
    用户注册（简化版）

    - 直接选择导师风格偏好（1-5）
    - 创建用户记录
    - 返回 token 自动登录
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

    # 验证密码复杂度
    is_valid, error_msg = validate_password(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # 创建新用户（密码哈希）
    hashed_password = get_password_hash(user_data.password)
    new_user = UserModel(
        email=user_data.email,
        username=user_data.username,
        password=hashed_password,
        cognitive_level=user_data.preferred_teaching_style
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # 生成 Access Token 和 Refresh Token
    access_token = create_token_for_user(new_user.id, new_user.email)
    refresh_token = create_refresh_token({"sub": new_user.email, "user_id": new_user.id})

    # 保存 refresh token 到数据库
    new_user.refresh_token = refresh_token
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": new_user.id,
        "email": new_user.email,
        "username": new_user.username,
        "teaching_style": new_user.cognitive_level
    }


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="用户登录",
    description="""
    使用邮箱和密码登录系统。

    **返回信息:**
    - access_token: JWT 访问令牌（有效期 2 小时）
    - refresh_token: 刷新令牌（有效期 30 天）
    - user_id: 用户 ID
    - email: 用户邮箱
    - username: 用户名
    - teaching_style: 教学风格偏好（1-5）

    **使用方式:**
    在请求头中添加: `Authorization: Bearer {access_token}`
    """,
    responses={
        200: {"description": "登录成功"},
        401: {"description": "邮箱或密码错误"}
    }
)
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

    # 生成 Access Token 和 Refresh Token
    access_token = create_token_for_user(user.id, user.email)
    refresh_token = create_refresh_token({"sub": user.email, "user_id": user.id})

    # 保存 refresh token 到数据库
    user.refresh_token = refresh_token
    await db.commit()

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        username=user.username,
        teaching_style=user.cognitive_level
    )


@router.post("/refresh-token", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    刷新 Access Token

    - 验证 Refresh Token
    - 生成新的 Access Token 和 Refresh Token
    - 返回新的 token 对
    """
    # 验证 refresh token
    token_data = verify_token(request.refresh_token, token_type="refresh")

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 refresh token"
        )

    # 查找用户
    result = await db.execute(
        select(User).where(User.id == token_data.user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )

    # 验证 refresh token 是否与数据库中的匹配
    if user.refresh_token != request.refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="refresh token 已失效"
        )

    # 生成新的 access token 和 refresh token
    new_access_token = create_token_for_user(user.id, user.email)
    new_refresh_token = create_refresh_token({"sub": user.email, "user_id": user.id})

    # 更新数据库中的 refresh token
    user.refresh_token = new_refresh_token
    await db.commit()

    return RefreshTokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
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
    recommended_level = 1
    level_name = LEVEL_NAMES[1]
    
    for level in sorted(LEVEL_THRESHOLDS.keys(), reverse=True):
        if avg_score >= LEVEL_THRESHOLDS[level]:
            recommended_level = level
            level_name = LEVEL_NAMES[level]
            break

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

    # 获取能力评估数据（从最近的题目尝试记录计算，关联Question表）
    from app.models.document import Question as QuestionModel

    competency_result = await db.execute(
        select(QuizAttempt, QuestionModel)
        .join(QuestionModel, QuizAttempt.question_id == QuestionModel.id)
        .where(QuizAttempt.user_id == user_id)
        .order_by(QuizAttempt.created_at.desc())
        .limit(50)
    )
    quiz_attempts_with_questions = competency_result.all()

    # 计算六个维度的能力评分（使用 Question 表中的 competency_dimension）
    competency_scores = calculate_competency_scores(quiz_attempts_with_questions)

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


@router.post("/{user_id}/update-chapter-progress")
async def update_chapter_progress(
    user_id: int,
    progress_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    在学习过程中更新进度

    - 记录学习时间
    - 更新最后访问时间
    - 可选地更新完成百分比
    """
    document_id = progress_data.get("document_id", 1)
    chapter_number = progress_data.get("chapter_number", 1)
    chapter_title = progress_data.get("chapter_title", f"第{chapter_number}章")
    time_spent_add = progress_data.get("time_spent_minutes", 1)

    try:
        # 获取或创建进度记录
        progress = await get_or_create_progress(
            user_id,
            document_id,
            chapter_number,
            chapter_title,
            db
        )

        # 更新活动
        progress = await update_progress_activity(
            progress.id,
            time_spent_add,
            db
        )

        # 如果提供了完成百分比，更新它
        if "completion_percentage" in progress_data:
            progress.completion_percentage = min(100, max(0, progress_data["completion_percentage"]))

            # 如果完成度达到 95%，标记为完成
            if progress.completion_percentage >= 95 and progress.status != "completed":
                progress.status = "completed"
                progress.completed_at = datetime.now()

        await db.commit()

        return {
            "status": "success",
            "progress_id": progress.id,
            "completion_percentage": progress.completion_percentage,
            "time_spent_minutes": progress.time_spent_minutes
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新进度失败: {str(e)}"
        )


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


@router.put("/{user_id}/teaching-style")
async def update_teaching_style(
    user_id: int,
    style_data: dict,
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    更新用户的教学风格偏好

    Args:
        user_id: 用户ID
        style_data: {"teaching_style": int} (1-5)
    """
    # 验证权限：只能更新自己的风格
    if current_user and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限修改其他用户的设置"
        )

    teaching_style = style_data.get("teaching_style")

    # 验证风格值
    if not teaching_style or not isinstance(teaching_style, int) or teaching_style < 1 or teaching_style > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="教学风格必须是 1-5 之间的整数"
        )

    # 获取用户
    from sqlalchemy import select

    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 更新教学风格
    user.cognitive_level = teaching_style
    await db.commit()

    print(f"✅ 用户 {user_id} 的教学风格已更新为 L{teaching_style}")

    return {
        "status": "success",
        "message": "教学风格已更新",
        "teaching_style": teaching_style
    }
