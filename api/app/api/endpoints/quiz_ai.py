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


async def get_chapter_content(document_id: int, chapter_number: int, db: AsyncSession) -> tuple[str, str]:
    """
    获取章节内容用于出题

    Returns:
        tuple: (chapter_title, chapter_content)
    """
    from app.models.document import ConversationHistory
    import json

    # 获取文档
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"文档 {document_id} 不存在"
        )

    default_title = f"第{chapter_number}章"
    default_content = f"第{chapter_number}章内容，来自文档：{doc.title}"

    # 优先从文档的章节JSON中获取内容
    if doc.chapters_json:
        try:
            chapters = json.loads(doc.chapters_json)
            for chapter in chapters:
                if chapter.get('chapter_number') == chapter_number:
                    title = chapter.get('title', default_title)
                    content = chapter.get('content', '')
                    subsections = chapter.get('subsections', [])

                    # 构建完整内容
                    chapter_text = f"第{chapter_number}章：{title}\n\n"
                    chapter_text += content[:3000]  # 限制内容长度，避免超过token限制

                    if subsections:
                        chapter_text += "\n\n小节目录：\n"
                        for sub in subsections[:5]:  # 最多5个小节
                            chapter_text += f"- {sub.get('title', '')}\n"

                    logger.info(f"从文档章节JSON中获取内容: {title}")
                    return title, chapter_text
        except Exception as e:
            logger.warning(f"解析章节JSON失败: {e}")

    # 备选方案：从对话历史中获取AI讲解内容
    history_result = await db.execute(
        select(ConversationHistory)
        .where(
            ConversationHistory.document_id == document_id,
            ConversationHistory.chapter_number == chapter_number,
            ConversationHistory.role == 'assistant'  # 只获取AI的回复
        )
        .order_by(ConversationHistory.created_at.desc())
        .limit(5)
    )
    conversations = history_result.scalars().all()

    if conversations:
        content_parts = []
        for conv in conversations:
            if conv.content:
                content_parts.append(conv.content)

        if content_parts:
            chapter_text = f"第{chapter_number}章 内容摘要（来自对话历史）\n\n"
            chapter_text += "\n\n".join(content_parts)
            logger.info(f"从对话历史中获取内容: {len(content_parts)} 条对话")
            return default_title, chapter_text[:4000]  # 限制长度

    # 最终降级方案：返回章节标题
    logger.warning(f"无法获取章节内容，使用降级方案: 第{chapter_number}章")
    return default_title, default_content


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
        # 调用 AI 生成题目（使用正确的参数名）
        logger.info("调用 Examiner Agent 生成题目...")

        # 构建符合 ExaminerAgent 要求的 state 结构
        teaching_state = {
            "student_level": 3,
            "chapter_title": chapter_title,
            "chapter_content": chapter_content,
            "learning_objectives": [],
            "wrong_questions": []
        }

        questions_data = await examiner.generate_questions(
            state=teaching_state,
            num_questions=count
        )

        logger.info(f"AI生成成功，获得 {len(questions_data)} 道题目")

        # 验证并保存题目
        saved_count = 0
        for q_data in questions_data:
            # 字段映射：Examiner Agent 返回的字段名 -> 数据库字段名
            question_text = q_data.get('question_text') or q_data.get('question', '')
            if not question_text:
                logger.warning(f"题目缺少 question_text 字段，跳过: {q_data}")
                continue

            # 检查是否重复
            existing = await db.execute(
                select(Question).where(
                    Question.question_text == question_text
                )
            )
            if existing.scalar_one_or_none():
                logger.warning(f"跳过重复题目: {question_text[:50]}...")
                continue

            # 处理选项：Examiner 返回数组格式 ["A. xxx", "B. xxx"]，需要转换为字典 {"A": "xxx", "B": "xxx"}
            options_raw = q_data.get('options', [])
            options_dict = None
            if options_raw:
                if isinstance(options_raw, list):
                    options_dict = {}
                    for opt in options_raw:
                        if isinstance(opt, str) and len(opt) > 2:
                            match = opt[0]  # 取第一个字符作为选项字母
                            content = opt[2:] if opt[1] in ('.', '、') else opt[3:] if opt[2] in ('.', '、') else opt
                            options_dict[match.upper()] = content.strip()
                        elif isinstance(opt, dict):
                            options_dict = opt
                            break
                elif isinstance(options_raw, dict):
                    options_dict = options_raw

            # 获取题目类型和难度
            question_type = q_data.get('question_type') or q_data.get('type') or 'choice'
            difficulty = q_data.get('difficulty') or q_data.get('difficulty_level') or difficulty

            # 创建新题目
            question = Question(
                document_id=document_id,
                chapter_number=chapter_number,
                question_type=question_type,
                question_text=question_text,
                options=json.dumps(options_dict) if options_dict else None,
                correct_answer=q_data.get('correct_answer', ''),
                explanation=q_data.get('explanation', ''),
                difficulty=difficulty,
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
