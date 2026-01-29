"""
错题本 API 端点
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from typing import List, Optional
import uuid

from app.db.database import get_db
from app.models.document import User, QuizAttempt, Question, Progress
from app.schemas.mistake import (
    MistakeFilter,
    MistakeResponse,
    MistakeListResponse,
    MarkMasteredRequest,
    MistakeAnalysisResponse,
    PracticeConfig,
    PracticeSessionResponse,
    PracticeQuestion
)
from app.core.security import get_current_user

router = APIRouter(prefix="/api/mistakes", tags=["mistakes"])


# ============ 辅助函数 ============

async def get_mistake_query(
    user_id: int,
    filters: Optional[MistakeFilter] = None,
    db: AsyncSession = None
):
    """
    构建错题查询

    Returns:
        查询对象
    """
    # 关联查询：获取答错的题目
    query = (
        select(
            QuizAttempt.id.label('attempt_id'),
            QuizAttempt.question_id,
            QuizAttempt.question_text,
            QuizAttempt.user_answer,
            QuizAttempt.correct_answer,
            QuizAttempt.is_correct,
            QuizAttempt.time_spent_seconds,
            QuizAttempt.attempts_count,
            QuizAttempt.created_at,
            Question.competency_dimension,
            Question.difficulty,
            Question.explanation,
            Question.options,
            Progress.chapter_number,
            Progress.chapter_title,
            Question.id.label('original_question_id')
        )
        .join(Question, QuizAttempt.question_id == Question.id)
        .join(Progress, QuizAttempt.progress_id == Progress.id)
        .where(QuizAttempt.user_id == user_id)
        .where(QuizAttempt.is_correct == 0)  # 只获取答错的题目
    )

    # 添加筛选条件
    if filters:
        if filters.chapter_number is not None:
            query = query.where(Progress.chapter_number == filters.chapter_number)

        if filters.competency_dimension is not None:
            query = query.where(Question.competency_dimension == filters.competency_dimension)

        if filters.difficulty is not None:
            query = query.where(Question.difficulty == filters.difficulty)

    return query


async def check_if_mastered(
    question_id: int,
    user_id: int,
    db: AsyncSession
) -> bool:
    """
    检查题目是否已掌握（最近3次都答对）
    """
    # 获取该题目最近的3次尝试
    result = await db.execute(
        select(QuizAttempt)
        .where(
            and_(
                QuizAttempt.question_id == question_id,
                QuizAttempt.user_id == user_id
            )
        )
        .order_by(QuizAttempt.created_at.desc())
        .limit(3)
    )
    attempts = result.scalars().all()

    if len(attempts) < 3:
        return False

    # 检查最近3次是否都正确
    return all(attempt.is_correct == 1 for attempt in attempts)


# ============ API 端点 ============

@router.get("", response_model=MistakeListResponse)
async def get_mistakes(
    page: int = 1,
    page_size: int = 20,
    filters: MistakeFilter = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取错题列表（支持分页和筛选）
    """
    # 构建查询
    query = await get_mistake_query(current_user.id, filters, db)

    # 获取总数
    count_result = await db.execute(select(func.count()).select_from(query.alias()))
    total = count_result.scalar() or 0

    # 分页查询
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    query = query.order_by(QuizAttempt.created_at.desc())

    result = await db.execute(query)
    rows = result.all()

    # 格式化响应
    mistakes = []
    for row in rows:
        # 检查是否已掌握
        is_mastered = await check_if_mastered(row.question_id, current_user.id, db)

        mistakes.append({
            "id": row.attempt_id,
            "question_id": row.question_id,
            "question_text": row.question_text,
            "user_answer": row.user_answer,
            "correct_answer": row.correct_answer,
            "explanation": row.explanation,
            "is_correct": bool(row.is_correct),
            "competency_dimension": row.competency_dimension,
            "difficulty": row.difficulty,
            "chapter_number": row.chapter_number,
            "chapter_title": row.chapter_title,
            "is_mastered": is_mastered,
            "attempts_count": row.attempts_count,
            "created_at": row.created_at
        })

    return MistakeListResponse(
        mistakes=mistakes,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/{mistake_id}/mark-mastered", response_model=dict)
async def mark_mistake_mastered(
    mistake_id: int,
    request: MarkMasteredRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    标记错题为已掌握/未掌握
    """
    # 获取错题记录
    result = await db.execute(
        select(QuizAttempt).where(
            and_(
                QuizAttempt.id == mistake_id,
                QuizAttempt.user_id == current_user.id
            )
        )
    )
    mistake = result.scalar_one_or_none()

    if not mistake:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="错题记录不存在"
        )

    # 注意：这里我们实际上不能直接修改 QuizAttempt
    # 因为"掌握"是一个动态状态，基于最近的答题情况
    # 所以我们返回提示信息，而不是修改数据库

    return {
        "message": "掌握状态基于最近答题记录动态计算",
        "question_id": mistake.question_id,
        "is_mastered": request.is_mastered,
        "note": "请在练习模式下重新答对该题目3次以标记为掌握"
    }


@router.get("/analysis", response_model=MistakeAnalysisResponse)
async def get_mistake_analysis(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取错题分析
    - 按能力维度分析
    - 识别薄弱环节
    - 提供改进建议
    """
    # 获取所有错题（包含题目信息）
    query = await get_mistake_query(current_user.id, None, db)
    result = await db.execute(query)
    all_mistakes = result.all()

    # 统计各维度错题数据
    dimension_stats = {}
    for row in all_mistakes:
        dimension = row.competency_dimension or 'comprehension'

        if dimension not in dimension_stats:
            dimension_stats[dimension] = {
                'dimension': dimension,
                'total_mistakes': 0,
                'mastered_count': 0,
                'mistake_details': []
            }

        dimension_stats[dimension]['total_mistakes'] += 1

        # 检查是否掌握
        is_mastered = await check_if_mastered(row.question_id, current_user.id, db)
        if is_mastered:
            dimension_stats[dimension]['mastered_count'] += 1

    # 分析每个维度
    dimension_names = {
        'comprehension': '理解力',
        'logic': '逻辑',
        'terminology': '术语',
        'memory': '记忆',
        'application': '应用',
        'stability': '稳定性'
    }

    analysis_by_dimension = []
    weak_dimensions = []

    for dimension, stats in dimension_stats.items():
        total = stats['total_mistakes']
        mastered = stats['mastered_count']
        mistake_rate = (total - mastered) / total if total > 0 else 0

        # 计算优先级（错题越多且掌握率越低，优先级越高）
        priority = 1
        if total >= 10:
            priority = 1
        elif total >= 5:
            priority = 2
        elif total >= 3:
            priority = 3
        else:
            priority = 4

        if mistake_rate > 0.5 and priority <= 3:
            weak_dimensions.append(dimension)

        # 生成建议
        recommendations = []
        if mistake_rate > 0.7:
            recommendations.append(f"该维度错误率较高（{mistake_rate*100:.0f}%），建议重点复习")
        elif mistake_rate > 0.5:
            recommendations.append("建议多做练习巩固")
        else:
            recommendations.append("继续保持")

        analysis_by_dimension.append(MistakeAnalysis(
            dimension=dimension,
            dimension_name=dimension_names.get(dimension, dimension),
            total_mistakes=total,
            mastered_count=mastered,
            mistake_rate=mistake_rate,
            priority=priority,
            recommendations=recommendations
        ))

    # 按优先级排序
    analysis_by_dimension.sort(key=lambda x: x.priority)

    # 生成复习计划建议
    suggested_review_plan = []
    if weak_dimensions:
        weak_names = [dimension_names.get(d, d) for d in weak_dimensions]
        suggested_review_plan.append(f"优先复习薄弱环节：{', '.join(weak_names)}")
        suggested_review_plan.append("建议每天花30分钟专项练习")
    else:
        suggested_review_plan.append("当前学习状态良好，继续保持")

    total_mistakes = sum(stats['total_mistakes'] for stats in dimension_stats.values())
    mastered_mistakes = sum(stats['mastered_count'] for stats in dimension_stats.values())

    return MistakeAnalysisResponse(
        total_mistakes=total_mistakes,
        mastered_mistakes=mastered_mistakes,
        analysis_by_dimension=analysis_by_dimension,
        weak_dimensions=[dimension_names.get(d, d) for d in weak_dimensions],
        suggested_review_plan=suggested_review_plan
    )


@router.post("/practice", response_model=PracticeSessionResponse)
async def create_practice_session(
    config: PracticeConfig,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建专项练习会话
    - 针对薄弱维度或章节
    - 随机抽取错题
    - 支持练习模式
    """
    # 构建查询
    query = await get_mistake_query(current_user.id, None, db)

    # 应用筛选条件
    if config.dimension:
        query = query.where(Question.competency_dimension == config.dimension)

    if config.chapter_number:
        query = query.where(Progress.chapter_number == config.chapter_number)

    if config.difficulty:
        query = query.where(Question.difficulty == config.difficulty)

    # 获取所有符合条件的错题
    result = await db.execute(query)
    all_mistakes = result.all()

    if len(all_mistakes) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="没有找到符合条件的错题，请先完成一些练习"
        )

    # 随机抽取题目（避免重复）
    import random
    selected_mistakes = random.sample(list(all_mistakes), min(config.count, len(all_mistakes)))

    # 去重（同一题目只取一次）
    seen_questions = set()
    unique_questions = []
    for mistake in selected_mistakes:
        if mistake.question_id not in seen_questions:
            seen_questions.add(mistake.question_id)
            unique_questions.append(mistake)

    # 获取完整题目信息
    question_ids = [q.question_id for q in unique_questions]
    questions_result = await db.execute(
        select(Question).where(Question.id.in_(question_ids))
    )
    questions_map = {q.id: q for q in questions_result.scalars().all()}

    # 统计每道题的答错次数
    mistake_counts = {}
    for mistake in all_mistakes:
        mistake_counts[mistake.question_id] = mistake_counts.get(mistake.question_id, 0) + 1

    # 格式化练习题目
    practice_questions = []
    for question_id in question_ids:
        question = questions_map.get(question_id)
        if question:
            is_mastered = await check_if_mastered(question_id, current_user.id, db)

            practice_questions.append(PracticeQuestion(
                id=question.id,
                question_text=question.question_text,
                options=eval(question.options) if question.options else None,
                correct_answer=question.correct_answer,
                explanation=question.explanation,
                difficulty=question.difficulty,
                competency_dimension=question.competency_dimension,
                is_mastered=is_mastered,
                mistake_count=mistake_counts.get(question_id, 0)
            ))

    # 确定练习重点
    focus_area = []
    if config.dimension:
        focus_area.append(f"{dimension_names.get(config.dimension, config.dimension)}专项练习")
    if config.chapter_number:
        focus_area.append(f"第{config.chapter_number}章专项")
    if config.difficulty:
        focus_area.append(f"难度{config.difficulty}专项")

    focus = ", ".join(focus_area) if focus_area else "综合练习"

    return PracticeSessionResponse(
        session_id=str(uuid.uuid4()),
        questions=practice_questions,
        total_questions=len(practice_questions),
        focus_area=focus
    )


@router.get("/stats", response_model=dict)
async def get_mistake_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取错题统计信息
    """
    # 获取所有错题
    query = await get_mistake_query(current_user.id, None, db)
    result = await db.execute(query)
    all_mistakes = result.all()

    # 统计各维度错题数
    dimension_counts = {}
    for mistake in all_mistakes:
        dimension = mistake.competency_dimension or 'comprehension'
        dimension_counts[dimension] = dimension_counts.get(dimension, 0) + 1

    # 统计掌握情况
    mastered_count = 0
    for mistake in all_mistakes:
        is_mastered = await check_if_mastered(mistake.question_id, current_user.id, db)
        if is_mastered:
            mastered_count += 1

    return {
        "total_mistakes": len(all_mistakes),
        "mastered_mistakes": mastered_count,
        "mistakes_by_dimension": dimension_counts,
        "mastery_rate": mastered_count / len(all_mistakes) if all_mistakes else 0
    }
