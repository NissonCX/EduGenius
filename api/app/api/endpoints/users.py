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
        now = datetime.now()
        progress = Progress(
            user_id=user_id,
            document_id=document_id,
            chapter_number=chapter_number,
            chapter_title=chapter_title,
            status="in_progress",
            completion_percentage=0.0,
            cognitive_level_assigned=None,
            time_spent_minutes=0,
            quiz_attempts=0,
            quiz_success_rate=0.0,
            started_at=now,
            last_accessed_at=now,
            created_at=now
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
    subsection_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户对话历史和当前状态

    - 返回对话记录
    - 返回用户当前等级
    - 返回能力雷达图数据
    - 支持按小节筛选对话
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

    # 🔧 调试日志
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"📊 查询历史对话 - user_id: {user_id}, chapter_number: {chapter_number}, subsection_id: '{subsection_id}' (type: {type(subsection_id).__name__})")

    # 只有当 subsection_id 存在且不为空字符串时才添加过滤条件
    if subsection_id and subsection_id.strip():
        query = query.where(ConversationHistory.subsection_id == subsection_id)
        logger.info(f"✅ 已添加 subsection_id 过滤条件: '{subsection_id}'")

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


# ============ 密码找回功能 ============
class PasswordResetRequest(BaseModel):
    """密码重置请求"""
    email: str


class VerifyTokenRequest(BaseModel):
    """验证令牌请求"""
    token: str


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    token: str
    new_password: str


@router.post("/password-reset/request")
async def request_password_reset(
    request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    请求密码重置

    1. 验证邮箱是否存在
    2. 生成重置令牌
    3. 保存到数据库
    4. 发送重置邮件
    """
    from app.models.password_reset import PasswordReset
    from app.core.email import get_email_service
    from datetime import datetime, timedelta
    from app.core.config import settings

    # 验证邮箱格式
    if not request.email or "@" not in request.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱格式不正确"
        )

    # 检查邮箱是否注册（不暴露用户是否存在）
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    user = result.scalar_one_or_none()

    if not user:
        # 为了安全，即使邮箱不存在也返回成功消息
        # 这样可以防止枚举攻击
        return {
            "message": "如果该邮箱已注册，您将收到密码重置邮件",
            "status": "success"
        }

    # 生成重置令牌
    from app.core.security import get_password_hash
    email_service = await get_email_service()
    reset_token = email_service.generate_reset_token()

    # 计算过期时间
    expires_at = datetime.utcnow() + timedelta(
        hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS
    )

    # 保存到数据库
    password_reset = PasswordReset(
        email=request.email,
        token=get_password_hash(reset_token),  # 哈希令牌存储
        expires_at=expires_at
    )
    db.add(password_reset)
    await db.commit()

    # 发送重置邮件
    email_sent = await email_service.send_password_reset_email(
        request.email,
        reset_token
    )

    if email_sent:
        return {
            "message": "密码重置邮件已发送，请检查您的邮箱",
            "status": "success",
            "expires_in_hours": settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS
        }
    else:
        # 邮件发送失败，但为了用户体验仍然返回成功
        # 实际场景中应该记录日志并通知管理员
        logger.warning(f"密码重置邮件发送失败: {request.email}")
        return {
            "message": "密码重置邮件已发送（如果邮箱存在）",
            "status": "success"
        }


@router.post("/password-reset/verify")
async def verify_reset_token(
    request: VerifyTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    验证重置令牌是否有效

    用于前端验证后显示密码重置表单
    """
    from app.models.password_reset import PasswordReset
    from app.core.security import get_password_hash
    from datetime import datetime

    if not request.token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="令牌不能为空"
        )

    # 哈希令牌进行查询
    token_hash = get_password_hash(request.token)

    result = await db.execute(
        select(PasswordReset).where(
            PasswordReset.token == token_hash
        )
    )
    reset_record = result.scalar_one_or_none()

    # 验证令牌
    if not reset_record:
        return {
            "valid": False,
            "message": "无效的令牌"
        }

    if reset_record.used:
        return {
            "valid": False,
            "message": "令牌已被使用"
        }

    if reset_record.expires_at < datetime.utcnow():
        return {
            "valid": False,
            "message": "令牌已过期"
        }

    # 令牌有效
    return {
        "valid": True,
        "message": "令牌有效",
        "email": reset_record.email
    }


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    确认密码重置

    验证令牌并更新用户密码
    """
    from app.models.password_reset import PasswordReset
    from app.core.security import get_password_hash, verify_password
    from app.core.constants import PASSWORD_REQUIREMENTS
    from datetime import datetime

    if not request.token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="令牌不能为空"
        )

    # 验证新密码
    is_valid, error_msg = validate_password(request.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # 查找重置记录
    token_hash = get_password_hash(request.token)
    result = await db.execute(
        select(PasswordReset).where(
            PasswordReset.token == token_hash
        )
    )
    reset_record = result.scalar_one_or_none()

    if not reset_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的令牌"
        )

    if reset_record.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="令牌已被使用"
        )

    if reset_record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="令牌已过期"
        )

    # 获取用户
    user_result = await db.execute(
        select(User).where(User.email == reset_record.email)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 更新密码
    user.password = get_password_hash(request.new_password)
    
    # 标记令牌已使用
    reset_record.used = 1

    await db.commit()

    logger.info(f"✅ 用户 {user.id} ({user.email}) 密码已重置")

    return {
        "message": "密码重置成功，请使用新密码登录",
        "status": "success"
    }


@router.get("/{user_id}/activities")
async def get_user_activities(
    user_id: int,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户最近的学习活动

    返回的学习活动包括：
    - 章节完成
    - 章节开始学习
    - 测验完成
    - 等级提升
    """
    from datetime import timedelta
    from app.models.document import Document

    # 获取用户信息
    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    activities = []

    # 1. 获取最近的进度记录（最近7天）
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    progress_result = await db.execute(
        select(Progress, Document)
        .join(Document, Progress.document_id == Document.id)
        .where(Progress.user_id == user_id)
        .where(Progress.last_accessed_at >= seven_days_ago)
        .order_by(Progress.last_accessed_at.desc())
        .limit(limit * 2)
    )
    progress_records = progress_result.all()

    for progress, document in progress_records:
        # 完成的章节
        if progress.status == 'completed' and progress.completed_at:
            activities.append({
                "id": f"progress_{progress.id}",
                "action": "完成了",
                "target": f"{progress.chapter_title}",
                "time": _format_time_ago(progress.completed_at),
                "timestamp": progress.completed_at.isoformat(),
                "status": "completed",
                "document_title": document.title
            })

        # 开始学习的章节
        if progress.status == 'in_progress' and progress.started_at:
            activities.append({
                "id": f"progress_start_{progress.id}",
                "action": "开始了学习",
                "target": f"{progress.chapter_title}",
                "time": _format_time_ago(progress.started_at),
                "timestamp": progress.started_at.isoformat(),
                "status": "progress",
                "document_title": document.title
            })

    # 2. 获取最近的测验记录
    quiz_result = await db.execute(
        select(QuizAttempt, Progress, Document)
        .join(Progress, QuizAttempt.progress_id == Progress.id)
        .join(Document, Progress.document_id == Document.id)
        .where(Progress.user_id == user_id)
        .where(QuizAttempt.created_at >= seven_days_ago)
        .order_by(QuizAttempt.created_at.desc())
        .limit(limit)
    )
    quiz_records = quiz_result.all()

    # 统计每个章节的测验结果
    chapter_quiz_stats = {}
    for quiz_attempt, progress, document in quiz_records:
        key = f"{progress.id}"
        if key not in chapter_quiz_stats:
            chapter_quiz_stats[key] = {
                "total": 0,
                "correct": 0,
                "chapter_title": progress.chapter_title,
                "document_title": document.title,
                "latest_attempt": quiz_attempt.created_at
            }
        chapter_quiz_stats[key]["total"] += 1
        if quiz_attempt.is_correct:
            chapter_quiz_stats[key]["correct"] += 1
        if quiz_attempt.created_at > chapter_quiz_stats[key]["latest_attempt"]:
            chapter_quiz_stats[key]["latest_attempt"] = quiz_attempt.created_at

    # 添加测验活动
    for key, stats in chapter_quiz_stats.items():
        score = int((stats["correct"] / stats["total"]) * 100)
        if score >= 60:
            activities.append({
                "id": f"quiz_{key}",
                "action": "通过了测试",
                "target": f"{stats['chapter_title']} (得分: {score}%)",
                "time": _format_time_ago(stats["latest_attempt"]),
                "timestamp": stats["latest_attempt"].isoformat(),
                "status": "success",
                "document_title": stats["document_title"]
            })

    # 3. 添加等级提升活动（如果有等级变化记录）
    # 这里简单地使用用户的当前等级作为示例
    if user.cognitive_level and user.cognitive_level > 1:
        # 假设等级是最近提升的（实际应用中应该有专门的等级变更历史表）
        activities.append({
            "id": f"level_{user.id}",
            "action": "升级到",
            "target": f"L{user.cognitive_level} 等级",
            "time": "最近",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "level-up"
        })

    # 按时间排序并限制数量
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    activities = activities[:limit]

    return {
        "activities": activities,
        "total_count": len(activities)
    }


def _format_time_ago(dt: datetime) -> str:
    """
    格式化时间为"多久之前"
    """
    if not dt:
        return "未知时间"

    now = datetime.utcnow()
    diff = now - dt

    seconds = diff.total_seconds()

    if seconds < 60:
        return "刚刚"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes}分钟前"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours}小时前"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days}天前"
    else:
        return dt.strftime("%Y-%m-%d")


@router.get("/{user_id}/study-calendar")
async def get_user_study_calendar(
    user_id: int,
    weeks: int = 12,
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户学习日历热力图数据

    返回过去 N 周每天的学习时长（分钟）
    """
    from datetime import timedelta

    # 获取用户信息
    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 计算时间范围
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(weeks=weeks)

    # 获取该时间范围内的所有进度记录
    progress_result = await db.execute(
        select(Progress)
        .where(Progress.user_id == user_id)
        .where(Progress.last_accessed_at >= datetime.combine(start_date, datetime.min.time()))
        .order_by(Progress.last_accessed_at)
    )

    progress_records = progress_result.scalars().all()

    # 按日期聚合学习时长
    daily_study_time = {}

    for progress in progress_records:
        if progress.time_spent_minutes and progress.last_accessed_at:
            date_key = progress.last_accessed_at.date().isoformat()
            daily_study_time[date_key] = daily_study_time.get(date_key, 0) + progress.time_spent_minutes

    # 生成完整日期范围的数据
    study_days = []
    current_date = start_date

    while current_date <= end_date:
        date_key = current_date.isoformat()
        study_days.append({
            "date": date_key,
            "count": daily_study_time.get(date_key, 0)
        })
        current_date += timedelta(days=1)

    return {
        "study_days": study_days,
        "weeks": weeks,
        "total_days": len(study_days),
        "total_study_time": sum(d["count"] for d in study_days)
    }


@router.get("/{user_id}/study-curve")
async def get_user_study_curve(
    user_id: int,
    days: int = 30,
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户学习曲线数据

    返回过去 N 天的学习进度趋势
    """
    from datetime import timedelta
    from sqlalchemy import func

    # 获取用户信息
    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 计算时间范围
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # 获取该时间范围内的所有进度记录
    progress_result = await db.execute(
        select(Progress)
        .where(Progress.user_id == user_id)
        .where(Progress.last_accessed_at >= start_date)
        .order_by(Progress.last_accessed_at)
    )

    progress_records = progress_result.scalars().all()

    # 按日期聚合数据
    daily_data = {}

    for progress in progress_records:
        if progress.last_accessed_at:
            date_key = progress.last_accessed_at.date().isoformat()

            if date_key not in daily_data:
                daily_data[date_key] = {
                    "date": date_key,
                    "time_spent": 0,
                    "progress": 0,
                    "quiz_count": 0,
                    "quiz_correct": 0
                }

            daily_data[date_key]["time_spent"] += progress.time_spent_minutes or 0
            daily_data[date_key]["progress"] = max(daily_data[date_key]["progress"], progress.completion_percentage or 0)
            daily_data[date_key]["quiz_count"] += progress.quiz_attempts or 0
            daily_data[date_key]["quiz_correct"] += int((progress.quiz_success_rate or 0) * (progress.quiz_attempts or 0))

    # 获取每天的测验分数
    for date_key in daily_data:
        if daily_data[date_key]["quiz_count"] > 0:
            daily_data[date_key]["avg_score"] = int((daily_data[date_key]["quiz_correct"] / daily_data[date_key]["quiz_count"]) * 100)
        else:
            daily_data[date_key]["avg_score"] = None

    # 生成完整日期范围的数据（包括没有学习的日期）
    data_points = []
    current_date = start_date.date()

    while current_date <= end_date.date():
        date_key = current_date.isoformat()

        if date_key in daily_data:
            data_points.append({
                "date": date_key,
                "progress": daily_data[date_key]["progress"],
                "timeSpent": daily_data[date_key]["time_spent"],
                "avgScore": daily_data[date_key]["avg_score"]
            })
        else:
            # 没有学习的日期
            data_points.append({
                "date": date_key,
                "progress": 0,
                "timeSpent": 0,
                "avgScore": None
            })

        current_date += timedelta(days=1)

    return {
        "data_points": data_points,
        "days": days,
        "total_study_days": len([d for d in data_points if d["timeSpent"] > 0])
    }


# ============ 活动日历 API ============
@router.get("/{user_id}/activity-calendar")
async def get_activity_calendar(
    user_id: int,
    year: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户的活动日历（GitHub contribution graph风格）

    返回12个月的数据，每个月包含每天的活动记录
    """
    from datetime import date, timedelta

    # 该年的1月1日
    start_date = datetime(year, 1, 1)
    # 该年的12月31日
    end_date = datetime(year, 12, 31)

    # 获取该年的所有进度记录
    progress_result = await db.execute(
        select(Progress).where(
            Progress.user_id == user_id,
            Progress.last_study_at >= start_date,
            Progress.last_study_at <= end_date
        ).order_by(Progress.last_study_at)
    )
    progress_records = progress_result.scalars().all()

    # 按月份组织数据
    months_data = {}

    for month_num in range(1, 13):  # 1-12月
        # 获取该月第一天和总天数
        first_day = date(year, month_num, 1)
        if month_num == 12:
            days_in_month = (date(year, 12, 31) - date(year, 12, 1)).days + 1
        else:
            days_in_month = (date(year, month_num + 1, 1) - date(year, month_num, 1)).days

        # 初始化该月的所有天（level 0 = 无活动）
        days = []
        for day_num in range(1, days_in_month + 1):
            current_date = date(year, month_num, day_num)
            days.append({
                "date": current_date.isoformat(),
                "count": 0,  # 学习次数
                "level": 0   # 活动强度 0-4
            })

        month_key = f"{year}-{month_num:02d}"
        months_data[month_key] = {
            "year": year,
            "month": month_num,
            "days": days
        }

    # 填充实际学习数据
    for progress in progress_records:
        if not progress.last_study_at:
            continue

        study_date = progress.last_study_at.date()
        study_year = study_date.year
        if study_year != year:
            continue

        study_month = study_date.month
        study_day = study_date.day

        month_key = f"{study_year}-{study_month:02d}"

        if month_key in months_data:
            # 找到对应的天并更新
            day_index = study_day - 1
            if day_index < len(months_data[month_key]["days"]):
                days = months_data[month_key]["days"]
                days[day_index]["count"] += 1

                # 计算活动强度 level (0-4)
                # 基于学习时长和完成度计算
                time_spent = progress.time_spent_minutes or 0
                completion = progress.completion_percentage or 0

                # Level 0: 无活动
                # Level 1: 轻度 (< 10分钟 或 完成度 < 10%)
                # Level 2: 中度 (10-30分钟，完成度 10-30%)
                # Level 3: 较强 (30-60分钟，完成度 30-60%)
                # Level 4: 强烈 (> 60分钟 或 完成度 > 60%)
                if time_spent < 10 and completion < 10:
                    days[day_index]["level"] = max(days[day_index]["level"], 1)
                elif time_spent < 30 or completion < 30:
                    days[day_index]["level"] = max(days[day_index]["level"], 2)
                elif time_spent < 60 or completion < 60:
                    days[day_index]["level"] = max(days[day_index]["level"], 3)
                else:
                    days[day_index]["level"] = 4

    # 将字典转为列表格式（按月份顺序）
    months_list = []
    for month_num in range(1, 13):
        month_key = f"{year}-{month_num:02d}"
        if month_key in months_data:
            months_list.append(months_data[month_key])

    return {
        "year": year,
        "months": months_list
    }
