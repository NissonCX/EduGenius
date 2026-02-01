"""
AI 智能出题 API 端点

集成 Examiner Agent 实现真正的 AI 智能出题功能
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import json

from app.db.database import get_db
from app.models.document import User, Question, Document
from app.core.security import get_current_user_optional
from app.agents.nodes.examiner import ExaminerAgent
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/quiz", tags=["quiz"])


async def get_chapter_content(document_id: int, chapter_number: int, db: AsyncSession) -> str:
    """获取章节内容用于出题"""
    # 从 ConversationHistory 或 Document 中获取章节内容
    # 简化版：返回章节标题作为内容来源
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"文档 {document_id} 不存在"
        )

    # 返回章节标题作为内容基础
    # TODO: 实际应该从章节解析的内容中获取
    return f"第{chapter_number}章内容，来自文档：{doc.title}"


@router.post("/generate-ai-questions")
async def generate_ai_questions(
    document_id: int,
    chapter_number: int,
    count: int = 10,
    difficulty: int = 3,
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    AI 智能生成题目

    根据章节内容，使用 Examiner Agent 生成测试题目
    """
    logger.info(f"开始AI出题: document_id={document_id}, chapter={chapter_number}, count={count}")

    # 获取章节内容
    chapter_content = await get_chapter_content(document_id, chapter_number, db)

    # 创建 Examiner Agent
    examiner = ExaminerAgent(
        api_key=settings.DASHSCOPE_API_KEY,
        model=getattr(settings, 'MODEL_NAME', 'qwen-max')
    )

    try:
        # 调用 AI 生成题目
        logger.info("调用 Examiner Agent 生成题目...")
        questions_data = await examiner.generate_questions(
            state={
                "document_id": document_id,
                "current_chapter": chapter_number,
                "chapter_content": chapter_content,
                "learning_objectives": [],
                "wrong_questions": []
            },
            count=count,
            difficulty=difficulty,
            student_level=3
        )

        logger.info(f"AI生成成功，获得 {len(questions_data)} 道题目")

        # 验证并保存题目
        saved_count = 0
        for q_data in questions_data:
            # 检查是否重复
            existing = await db.execute(
                select(Question).where(
                    Question.question_text == q_data.get('question_text', '')
                )
            )
            if existing.scalar_one_or_none():
                logger.warning(f"跳过重复题目: {q_data.get('question_text', '')[:30]}...")
                continue

            # 创建新题目
            question = Question(
                document_id=document_id,
                chapter_number=chapter_number,
                question_type=q_data.get('question_type', 'choice'),
                question_text=q_data.get('question_text', ''),
                options=json.dumps(q_data.get('options', {})) if q_data.get('options') else None,
                correct_answer=q_data.get('correct_answer', ''),
                explanation=q_data.get('explanation', ''),
                difficulty=q_data.get('difficulty', 3),
                competency_dimension=q_data.get('competency_dimension', 'comprehension'),
                created_by='AI'
            )

            db.add(question)
            saved_count += 1

        await db.commit()
        logger.info(f"成功保存 {saved_count} 道新题目到数据库")

        return {
            "success": True,
            "generated": len(questions_data),
            "saved": saved_count,
            "skipped": len(questions_data) - saved_count,
            "message": f"成功生成并保存 {saved_count} 道题目"
        }

    except Exception as e:
        logger.error(f"AI生成题目失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"AI生成题目失败: {str(e)}"
        )


@router.get("/chapter/{document_id}/{chapter_number}/generate-status")
async def check_generation_status(
    document_id: int,
    chapter_number: int,
    db: AsyncSession = Depends(get_db)
):
    """检查某章节的题目数量和状态"""
    result = await db.execute(
        select(Question).where(
            Question.document_id == document_id,
            Question.chapter_number == chapter_number,
            Question.is_active == 1
        )
    )
    questions = result.scalars().all()

    return {
        "document_id": document_id,
        "chapter_number": chapter_number,
        "total_questions": len(questions),
        "ready_for_quiz": len(questions) >= 5,  # 至少5道题才能测试
        "question_breakdown": {
            "by_difficulty": {
                "1": sum(1 for q in questions if q.difficulty == 1),
                "2": sum(1 for q in questions if q.difficulty == 2),
                "3": sum(1 for q in questions if q.difficulty == 3),
                "4": sum(1 for q in questions if q.difficulty == 4),
                "5": sum(1 for q in questions if q.difficulty == 5),
            },
            "by_dimension": {}
        }
    }
