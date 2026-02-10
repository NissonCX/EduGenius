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
    from app.models.document import Progress, ConversationHistory

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
    default_content = f"第{chapter_number}章内容"

    # 方法1：从 ChromaDB 获取章节内容
    try:
        import chromadb
        from app.core.config import settings

        chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        collection_name = doc.chroma_collection_name or f"doc_{doc.md5_hash}"

        try:
            collection = chroma_client.get_collection(collection_name)

            # 获取该章节的所有内容
            results = collection.get(
                where={"chapter": chapter_number},
                include=["documents", "metadatas"]
            )

            if results and results.get('documents'):
                # 合并所有文档片段
                content_parts = []
                for i, doc_text in enumerate(results['documents'][:20]):  # 最多取20个片段
                    if doc_text:
                        content_parts.append(doc_text)

                if content_parts:
                    chapter_content = "\n\n".join(content_parts)
                    # 从 Progress 获取章节标题
                    progress_result = await db.execute(
                        select(Progress).where(
                            Progress.document_id == document_id,
                            Progress.chapter_number == chapter_number
                        )
                    )
                    progress = progress_result.scalar_one_or_none()
                    title = progress.chapter_title if progress else default_title

                    logger.info(f"从 ChromaDB 获取到章节 {chapter_number} 内容，{len(chapter_content)} 字符")
                    return title, chapter_content[:5000]  # 限制长度

        except Exception as e:
            logger.debug(f"从 ChromaDB 获取内容失败: {e}")

    except ImportError:
        logger.debug("ChromaDB 未安装")
    except Exception as e:
        logger.warning(f"ChromaDB 查询异常: {e}")

    # 方法2：从对话历史中获取相关内容
    history_result = await db.execute(
        select(ConversationHistory)
        .where(
            ConversationHistory.document_id == document_id,
            ConversationHistory.chapter_number == chapter_number,
            ConversationHistory.role == 'assistant'
        )
        .order_by(ConversationHistory.created_at.desc())
        .limit(10)
    )
    conversations = history_result.scalars().all()

    if conversations:
        # 拼接最近的对话内容
        content_parts = [conv.content for conv in conversations if conv.content]
        if content_parts:
            logger.info(f"从对话历史获取到章节 {chapter_number} 内容，{len(content_parts)} 条对话")
            return default_title, "\n\n".join(content_parts[:5])

    # 方法3：从原始 PDF 文件提取内容
    try:
        import os
        from app.services.document_extractors import extract_text_from_file

        # 查找上传的文件
        upload_dir = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
        if os.path.exists(upload_dir):
            # 尝试匹配文件
            for filename in os.listdir(upload_dir):
                filepath = os.path.join(upload_dir, filename)
                if os.path.isfile(filepath) and doc.filename in filename:
                    try:
                        # 提取文本
                        text = extract_text_from_file(filepath)
                        if text and len(text) > 100:
                            logger.info(f"从 PDF 文件提取到 {len(text)} 字符")
                            # 返回全部文本，让 AI 基于章节号生成相关题目
                            return default_title, f"文档内容：\n\n{text[:10000]}"
                    except Exception as e:
                        logger.debug(f"提取文件内容失败: {e}")
    except ImportError:
        logger.debug("文档提取服务不可用")
    except Exception as e:
        logger.warning(f"从文件提取内容异常: {e}")

    # 方法4：从 Progress 获取章节标题
    progress_result = await db.execute(
        select(Progress).where(
            Progress.document_id == document_id,
            Progress.chapter_number == chapter_number
        )
    )
    progress = progress_result.scalar_one_or_none()

    title = progress.chapter_title if progress else default_title

    # 给出清晰的提示
    logger.warning(f"章节 {chapter_number} 无可用内容，建议用户先学习")

    # 返回提示性内容
    prompt = f"""
【提示】此章节暂时没有可直接用于生成题目的内容。

建议：
1. 先使用"学习"功能学习此章节
2. 学习后系统会记录内容，然后可以生成测试题

章节信息：
- 标题：{title}
- 文档：{doc.title or '未命名文档'}

请基于章节标题"{title}"，生成一些基础的测试题目。
    """.strip()

    return title, prompt


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
