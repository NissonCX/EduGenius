"""
题目生成和答题 API 端点
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
import json
import uuid
from datetime import datetime
from pydantic import BaseModel

from app.db.database import get_db
from app.models.document import User, Question, QuizAttempt, Progress, Document
from app.core.security import get_current_user_optional  # 添加导入
from app.schemas.quiz import (
    QuestionGenerate,
    QuestionResponse,
    QuestionListResponse,
    QuizSubmit,
    QuizSubmitResponse,
    ChapterTestRequest,
    ChapterTestResponse,
    ChapterTestSubmit,
    ChapterTestResult
)
from app.core.security import get_current_user
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/quiz", tags=["quiz"])


# ============ Session 管理 ============
# 内存中存储测试 session（生产环境应使用 Redis）
quiz_sessions: dict = {}

# Session TTL 配置（秒）
SESSION_TTL_SECONDS = 3600  # 1小时后过期
MAX_SESSIONS = 1000  # 最大 session 数量，防止内存泄漏


class QuizSession:
    """测试会话数据结构"""
    def __init__(
        self,
        session_id: str,
        user_id: int,
        document_id: int,
        chapter_number: int,
        questions: List[dict],
        mode: str = "practice"
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.document_id = document_id
        self.chapter_number = chapter_number
        self.questions = questions  # 题目列表
        self.mode = mode  # practice 或 test
        self.answers = {}  # {question_id: answer}
        self.results = {}  # {question_id: is_correct}
        self.current_question_index = 0
        self.started_at = datetime.now()
        self.completed_at = None

    def is_expired(self) -> bool:
        """检查 session 是否已过期"""
        if self.completed_at:
            # 已完成的 session，30分钟后过期
            expiry_time = self.completed_at.timestamp() + 1800
        else:
            # 未完成的 session，按 TTL 过期
            expiry_time = self.started_at.timestamp() + SESSION_TTL_SECONDS
        return datetime.now().timestamp() > expiry_time


def cleanup_expired_sessions() -> int:
    """
    清理过期的 session

    Returns:
        int: 清理的 session 数量
    """
    global quiz_sessions

    expired_keys = [
        session_id for session_id, session in quiz_sessions.items()
        if session.is_expired()
    ]

    for key in expired_keys:
        del quiz_sessions[key]

    if expired_keys:
        logger.info(f"🧹 清理了 {len(expired_keys)} 个过期的 quiz session")

    return len(expired_keys)


def prune_sessions_if_needed() -> None:
    """
    如果 session 数量超过限制，删除最旧的 session
    """
    global quiz_sessions

    if len(quiz_sessions) > MAX_SESSIONS:
        # 按 started_at 排序，删除最旧的
        sorted_sessions = sorted(
            quiz_sessions.items(),
            key=lambda x: x[1].started_at
        )
        # 保留最新的 MAX_SESSIONS * 0.8 个
        keep_count = int(MAX_SESSIONS * 0.8)
        keys_to_remove = [k for k, _ in sorted_sessions[:-keep_count]]

        for key in keys_to_remove:
            del quiz_sessions[key]

        logger.warning(
            f"⚠️ Session 数量超过限制 ({MAX_SESSIONS})，"
            f"已清理 {len(keys_to_remove)} 个最旧 session"
        )


# ============ 辅助函数 ============

def classify_question_dimension(question_text: str) -> str:
    """
    根据题目文本判断能力维度

    Returns:
        str: 能力维度 (comprehension, logic, terminology, memory, application, stability)
    """
    question_lower = question_text.lower()

    # 理解类题目关键词
    comprehension_keywords = ['理解', '解释', '说明', '描述', '阐述', '分析', '总结', '概括',
                             'understand', 'explain', 'describe', 'analyze', 'summarize']
    # 逻辑类题目关键词
    logic_keywords = ['推导', '证明', '为什么', '原因', '因此', '逻辑', '推理', '判断',
                      'derive', 'prove', 'why', 'reason', 'logic', 'deduce']
    # 术语类题目关键词
    terminology_keywords = ['定义', '术语', '概念', '名称', '符号', '什么是',
                            'define', 'term', 'concept', 'what is', 'notation']
    # 记忆类题目关键词
    memory_keywords = ['记住', '背诵', '列举', '写出', '公式', '数值',
                       'remember', 'list', 'write', 'formula', 'value']
    # 应用类题目关键词
    application_keywords = ['计算', '求解', '应用', '使用', '解决', '实践',
                            'calculate', 'solve', 'apply', 'use', 'implement']

    if any(keyword in question_lower for keyword in logic_keywords):
        return 'logic'
    elif any(keyword in question_lower for keyword in comprehension_keywords):
        return 'comprehension'
    elif any(keyword in question_lower for keyword in terminology_keywords):
        return 'terminology'
    elif any(keyword in question_lower for keyword in memory_keywords):
        return 'memory'
    elif any(keyword in question_lower for keyword in application_keywords):
        return 'application'
    else:
        return 'comprehension'  # 默认为理解类


# ============ API 端点 ============

@router.post("/generate", response_model=List[QuestionResponse])
async def generate_questions(
    request: QuestionGenerate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    AI 自动生成题目（集成真实的 AI 生成逻辑）

    使用 Examiner Agent 生成题目，支持：
    - 多种题型（选择题、填空题、简答题）
    - 可定制难度和数量
    - 六维能力评估
    """
    from app.agents.nodes.examiner import ExaminerAgent
    from app.core.config import settings
    from app.core.logging_config import get_logger

    logger = get_logger(__name__)

    # 验证文档和章节是否存在
    document_result = await db.execute(
        select(Document).where(Document.id == request.document_id)
    )
    document = document_result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )

    # 初始化章节标题（用于 fallback）
    chapter_title = None

    try:
        # 获取章节/小节内容和标题
        chapter_title, chapter_content = await _get_chapter_content_for_generation(
            request.document_id,
            request.chapter_number,
            db,
            subsection_number=request.subsection_number
        )

        # 创建 Examiner Agent
        examiner = ExaminerAgent(
            api_key=settings.DASHSCOPE_API_KEY,
            model=getattr(settings, 'MODEL_NAME', 'qwen-max')
        )

        # 构建符合 ExaminerAgent 要求的 state 结构
        teaching_state = {
            "student_level": current_user.cognitive_level or 3,
            "chapter_title": chapter_title,
            "chapter_content": chapter_content,
            "learning_objectives": [],
            "wrong_questions": []
        }

        # 调用 AI 生成题目（使用正确的参数名）
        logger.info(f"调用AI生成题目: document={request.document_id}, chapter={request.chapter_number}, count={request.count}")
        questions_data = await examiner.generate_questions(
            state=teaching_state,
            num_questions=request.count
        )

        # 验证并保存题目
        saved_questions = []
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
                    # 从 ["A. xxx", "B. xxx"] 转换为 {"A": "xxx", "B": "xxx"}
                    options_dict = {}
                    for opt in options_raw:
                        if isinstance(opt, str) and len(opt) > 2:
                            match = opt[0]  # 取第一个字符作为选项字母
                            content = opt[2:] if opt[1] == '.' or opt[1] == '.' else opt[3:] if opt[2] == '.' else opt
                            options_dict[match.upper()] = content.strip()
                        elif isinstance(opt, dict):
                            options_dict = opt
                            break
                elif isinstance(options_raw, dict):
                    options_dict = options_raw

            # 获取题目类型和难度
            raw_question_type = q_data.get('question_type') or q_data.get('type') or request.question_type
            # 映射 AI 返回的类型到前端支持的类型
            question_type_mapping = {
                'conceptual': 'choice',  # 概念题作为选择题
                'multiple_choice': 'choice',
                'single_choice': 'choice',
            }
            question_type = question_type_mapping.get(raw_question_type, raw_question_type)
            difficulty = q_data.get('difficulty') or q_data.get('difficulty_level') or request.difficulty

            # 创建新题目
            question = Question(
                document_id=request.document_id,
                chapter_number=request.chapter_number,
                subsection_number=request.subsection_number,  # 标记小节
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
            saved_questions.append(question)

        await db.commit()

        # 刷新以获取 ID
        for q in saved_questions:
            await db.refresh(q)

        logger.info(f"✓ 成功生成并保存 {len(saved_questions)} 道题目")
        return saved_questions

    except Exception as e:
        logger.error(f"❌ AI生成题目失败: {type(e).__name__}: {str(e)}", exc_info=True)
        # 降级：返回示例题目作为备选方案
        logger.warning("⚠️  降级到示例题目生成")
        return await _generate_fallback_questions(request, db, chapter_title)


async def _get_chapter_content_for_generation(
    document_id: int,
    chapter_number: int,
    db: AsyncSession,
    subsection_number: Optional[str] = None
) -> tuple[str, str]:
    """
    获取章节/小节信息用于生成题目

    使用 ChromaDB 检索实际章节内容，确保 AI 生成与主题相关的题目

    Args:
        subsection_number: 小节编号（如 "1.1"），如果提供则生成小节级别的题目

    Returns:
        tuple: (title, prompt)
    """
    from app.core.logging_config import get_logger
    from app.core.chroma import search_documents
    from dashscope import TextEmbedding
    logger = get_logger(__name__)

    # 获取文档信息
    document_result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = document_result.scalar_one_or_none()
    document_title = document.title if document else "教材"
    md5_hash = document.md5_hash if document else None

    # 初始化章节内容
    chapter_content = ""

    # 如果有 ChromaDB，尝试检索实际内容
    if md5_hash:
        try:
            # 构建查询文本，用于检索相关内容
            if subsection_number:
                # 先获取小节标题
                from sqlalchemy import text
                subsection_query = text("""
                    SELECT subsection_title
                    FROM subsections
                    WHERE document_id = :document_id
                      AND chapter_number = :chapter_number
                      AND subsection_number = :subsection_number
                    LIMIT 1
                """)
                result = await db.execute(
                    subsection_query,
                    {"document_id": document_id, "chapter_number": chapter_number, "subsection_number": subsection_number}
                )
                row = result.fetchone()

                if row:
                    subsection_title = row[0]
                    query_text = f"{document_title} 第{chapter_number}章 {subsection_title} {subsection_number}"
                else:
                    query_text = f"{document_title} 第{chapter_number}章 {subsection_number}"
            else:
                # 获取章节标题
                progress_result = await db.execute(
                    select(Progress).where(
                        Progress.document_id == document_id,
                        Progress.chapter_number == chapter_number
                    )
                )
                progress = progress_result.scalar_one_or_none()
                chapter_title = progress.chapter_title if progress else f"第{chapter_number}章"
                query_text = f"{document_title} {chapter_title}"

            # 使用 DashScope 生成查询嵌入（与教学系统保持一致）
            embed_response = TextEmbedding.call(
                model='text-embedding-v2',
                input=query_text,
                text_type='document'
            )

            if embed_response.status_code == 200:
                query_embedding = embed_response.output['embeddings'][0]['embedding']

                # 从 ChromaDB 检索相关内容
                from app.core.chroma import query_document_chunks
                results = query_document_chunks(
                    md5_hash=md5_hash,
                    query_embedding=query_embedding,
                    n_results=10  # 获取更多上下文
                )

                if results and results.get('documents'):
                    # 合并检索到的文档片段
                    chunks = results['documents'][0]
                    chapter_content = "\n\n".join(chunks)
                    logger.info(f"从 ChromaDB 检索到 {len(chunks)} 个相关文档片段，共 {len(chapter_content)} 字符")

        except Exception as e:
            logger.warning(f"从 ChromaDB 检索内容失败: {e}，将使用章节标题生成")

    # 如果指定了小节，获取小节标题
    if subsection_number:
        from sqlalchemy import text

        # 从 subsections 表获取小节信息
        subsection_query = text("""
            SELECT subsection_title
            FROM subsections
            WHERE document_id = :document_id
              AND chapter_number = :chapter_number
              AND subsection_number = :subsection_number
            LIMIT 1
        """)

        result = await db.execute(
            subsection_query,
            {"document_id": document_id, "chapter_number": chapter_number, "subsection_number": subsection_number}
        )
        row = result.fetchone()

        if row:
            subsection_title = row[0]
            title = f"{subsection_title}（{subsection_number}）"

            # 构建提示词：如果有实际内容，使用内容；否则使用标题
            if chapter_content:
                prompt = f"""小节主题：{subsection_title}
小节编号：{subsection_number}
所属章节：第{chapter_number}章
所属文档：{document_title}

相关内容参考：
{chapter_content}

请基于上述内容，生成关于"{subsection_title}"的测试题目。题目应该聚焦于该小节的知识点，选项和解析都要基于给定的内容。"""
            else:
                prompt = f"""小节主题：{subsection_title}
小节编号：{subsection_number}
所属章节：第{chapter_number}章
所属文档：{document_title}

请基于小节主题"{subsection_title}"生成相关的测试题目。
AI 可以利用自身的知识库，围绕这个具体的小节主题出题，题目应该聚焦于该小节的知识点。"""

            logger.info(f"小节 {chapter_number}.{subsection_number} ({subsection_title}) - AI 生成题目 (内容长度: {len(chapter_content)})")
            return title, prompt

    # 没有小节编号，获取章节级别的标题
    progress_result = await db.execute(
        select(Progress).where(
            Progress.document_id == document_id,
            Progress.chapter_number == chapter_number
        )
    )
    progress = progress_result.scalar_one_or_none()

    chapter_title = progress.chapter_title if progress else f"第{chapter_number}章"

    # 构建提示词：如果有实际内容，使用内容；否则使用标题
    if chapter_content:
        prompt = f"""章节主题：{chapter_title}
所属文档：{document_title}

相关内容参考：
{chapter_content}

请基于上述内容，生成关于"{chapter_title}"的测试题目。题目应该基于给定的文档内容，确保与教材内容相关。"""
    else:
        prompt = f"""章节主题：{chapter_title}
所属文档：{document_title}

请基于"{chapter_title}"这个主题，生成相关的测试题目。
AI 可以利用自身的知识库，围绕这个主题出题。"""

    logger.info(f"章节 {chapter_number} ({chapter_title}) - AI 生成题目 (内容长度: {len(chapter_content)})")

    return chapter_title, prompt




async def _generate_fallback_questions(request: QuestionGenerate, db: AsyncSession, chapter_title: str = None) -> List[Question]:
    """
    降级方案：生成示例题目

    当 AI 生成失败时使用，生成基于章节标题的基础题目
    """
    questions = []

    # 获取章节标题用于生成更合理的题目
    if not chapter_title:
        progress_result = await db.execute(
            select(Progress).where(
                Progress.document_id == request.document_id,
                Progress.chapter_number == request.chapter_number
            )
        )
        progress = progress_result.scalar_one_or_none()
        chapter_title = progress.chapter_title if progress else f"第{request.chapter_number}章"

    for i in range(request.count):
        # 基于章节标题生成题目
        question_text = f'关于"{chapter_title}"的测试题 {i+1}'
        if request.subsection_number:
            question_text = f'关于"{chapter_title}"（{request.subsection_number}）的测试题 {i+1}'

        # 生成简单的选项
        options_dict = {
            "A": f"关于{chapter_title}的正确陈述",
            "B": f"关于{chapter_title}的错误陈述",
            "C": f"关于{chapter_title}的不完整陈述",
            "D": f"关于{chapter_title}的其他相关陈述"
        }

        question = Question(
            document_id=request.document_id,
            chapter_number=request.chapter_number,
            subsection_number=request.subsection_number,
            question_type=request.question_type,
            question_text=question_text,
            options=json.dumps(options_dict) if request.question_type == "choice" else None,
            correct_answer="A",
            explanation=f'这是基于章节主题"{chapter_title}"生成的示例题目。\n\n【注意】AI 自动生成功能暂时不可用，这是备用题目。\n建议稍后重试或使用"学习"功能后再测试。',
            difficulty=request.difficulty,
            competency_dimension=classify_question_dimension(chapter_title),
            created_by="AI_Fallback"
        )
        db.add(question)
        questions.append(question)

    await db.commit()
    for q in questions:
        await db.refresh(q)

    logger.warning(f"⚠️  已生成 {len(questions)} 道 fallback 题目（章节：{chapter_title}）")
    return questions


@router.get("/questions/{document_id}/{chapter_number}")
async def get_chapter_questions(
    document_id: int,
    chapter_number: int,
    subsection_number: Optional[str] = None,
    question_type: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定章节（或小节）的题目列表

    支持的查询参数：
    - subsection_number: 小节编号（如 "1.1"），不传则返回整个章节的题目
    - question_type: 题目类型（如 "choice"）
    """
    try:
        # 构建查询条件
        conditions = [
            Question.document_id == document_id,
            Question.chapter_number == chapter_number,
            Question.is_active == 1
        ]

        # 如果指定了小节，添加小节筛选条件
        if subsection_number:
            conditions.append(Question.subsection_number == subsection_number)

        query = select(Question).where(and_(*conditions))

        if question_type:
            query = query.where(Question.question_type == question_type)

        result = await db.execute(query)
        questions = result.scalars().all()

        # 快速构造响应
        questions_data = []
        for q in questions:
            q_dict = {
                "id": q.id,
                "question_type": q.question_type,
                "question_text": q.question_text,
                "difficulty": q.difficulty,
                "competency_dimension": q.competency_dimension,
                "correct_answer": q.correct_answer,
                "explanation": q.explanation
            }
            # 只有选择题才有 options
            if q.options:
                try:
                    import json
                    q_dict["options"] = json.loads(q.options) if isinstance(q.options, str) else q.options
                except json.JSONDecodeError as e:
                    logger.warning(f"题目 {q.id} 的 options JSON 解析失败: {e}")
                    q_dict["options"] = None
            questions_data.append(q_dict)

        return {
            "questions": questions_data,
            "total": len(questions_data),
            "chapter_number": chapter_number
        }
    except Exception as e:
        from app.core.logging_config import get_logger
        logger = get_logger(__name__)
        logger.error(f"获取题目失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"获取题目失败: {str(e)}"
        )


@router.post("/submit", response_model=QuizSubmitResponse)
async def submit_answer(
    submission: QuizSubmit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    提交单个题目的答案
    """
    try:
        # 获取题目信息
        question_result = await db.execute(
            select(Question).where(Question.id == submission.question_id)
        )
        question = question_result.scalar_one_or_none()

        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="题目不存在"
            )

        # 验证答案
        is_correct = submission.user_answer.strip().upper() == question.correct_answer.strip().upper()

        # 获取或创建 progress 记录
        progress_result = await db.execute(
            select(Progress).where(
                and_(
                    Progress.user_id == submission.user_id,
                    Progress.document_id == question.document_id,
                    Progress.chapter_number == question.chapter_number
                )
            )
        )
        progress = progress_result.scalar_one_or_none()

        if not progress:
            # 创建 progress 记录
            progress = Progress(
                user_id=submission.user_id,
                document_id=question.document_id,
                chapter_number=question.chapter_number,
                status="in_progress",
                cognitive_level_assigned=current_user.cognitive_level
            )
            db.add(progress)
            await db.flush()  # 获取 ID

        # 记录答题尝试（使用 competency_dimension 而不是重新分类）
        attempt = QuizAttempt(
            user_id=submission.user_id,
            progress_id=progress.id,
            question_id=question.id,
            question_text=question.question_text,
            user_answer=submission.user_answer,
            correct_answer=question.correct_answer,
            is_correct=1 if is_correct else 0,
            time_spent_seconds=submission.time_spent_seconds
        )
        db.add(attempt)

        # 更新 progress 统计
        all_attempts_result = await db.execute(
            select(QuizAttempt).where(QuizAttempt.progress_id == progress.id)
        )
        all_attempts = all_attempts_result.scalars().all()

        total_attempts = len(all_attempts) + 1  # 包括当前这次
        correct_attempts = sum(1 for a in all_attempts if a.is_correct == 1) + (1 if is_correct else 0)
        progress.quiz_attempts = total_attempts
        progress.quiz_success_rate = correct_attempts / total_attempts if total_attempts > 0 else 0.0

        # 提交事务
        await db.commit()
        await db.refresh(attempt)

        # 生成反馈
        if is_correct:
            feedback = "✅ 回答正确！"
        else:
            feedback = f"❌ 回答错误。正确答案是：{question.correct_answer}"

        return QuizSubmitResponse(
            is_correct=is_correct,
            correct_answer=question.correct_answer,
            explanation=question.explanation,
            feedback=feedback,
            competency_dimension=question.competency_dimension
        )
    
    except HTTPException:
        # 重新抛出 HTTP 异常
        raise
    except Exception as e:
        # 回滚事务
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交答案失败: {str(e)}"
        )


@router.post("/chapter-test", response_model=ChapterTestResponse)
async def create_chapter_test(
    request: ChapterTestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建章节测试（随机抽取题目）
    """
    # 获取章节所有题目
    result = await db.execute(
        select(Question).where(
            and_(
                Question.document_id == request.document_id,
                Question.chapter_number == request.chapter_number,
                Question.is_active == 1
            )
        )
    )
    all_questions = result.scalars().all()

    if len(all_questions) < request.question_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"章节题目不足，当前只有 {len(all_questions)} 道题，需要至少 {request.question_count} 道"
        )

    # 随机抽取题目（简化版，实际应该使用 random.sample）
    import random
    selected_questions = random.sample(list(all_questions), request.question_count)

    # 生成测试 ID
    test_id = str(uuid.uuid4())

    return ChapterTestResponse(
        test_id=test_id,
        questions=selected_questions,
        total_questions=len(selected_questions),
        time_limit_minutes=30  # 默认30分钟
    )


@router.post("/chapter-test/submit", response_model=ChapterTestResult)
async def submit_chapter_test(
    submission: ChapterTestSubmit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    提交章节测试答案
    """
    correct_count = 0
    competency_scores = {
        "comprehension": 0.0,
        "logic": 0.0,
        "terminology": 0.0,
        "memory": 0.0,
        "application": 0.0,
        "stability": 0.0
    }
    competency_counts = {
        "comprehension": 0,
        "logic": 0,
        "terminology": 0,
        "memory": 0,
        "application": 0,
        "stability": 0
    }

    # 批量获取题目信息
    question_ids = [ans["question_id"] for ans in submission.answers]
    questions_result = await db.execute(
        select(Question).where(Question.id.in_(question_ids))
    )
    questions_map = {q.id: q for q in questions_result.scalars().all()}

    # 验证答案并记录
    for answer_item in submission.answers:
        question = questions_map.get(answer_item["question_id"])
        if not question:
            continue

        user_answer = answer_item.get("answer", "")
        is_correct = user_answer.strip().upper() == question.correct_answer.strip().upper()

        if is_correct:
            correct_count += 1

        # 统计能力维度
        dimension = question.competency_dimension or "comprehension"
        if is_correct:
            competency_scores[dimension] = competency_scores.get(dimension, 0.0) + 1.0
        competency_counts[dimension] = competency_counts.get(dimension, 0) + 1

    # 计算各维度正确率
    for dimension in competency_scores:
        if competency_counts[dimension] > 0:
            competency_scores[dimension] /= competency_counts[dimension]
        else:
            competency_scores[dimension] = 0.0

    total_count = len(submission.answers)
    score = (correct_count / total_count * 100) if total_count > 0 else 0.0
    passed = score >= 60.0

    # 生成建议
    recommendations = []
    if passed:
        recommendations.append("🎉 恭喜通过测试！可以进入下一章节学习。")
    else:
        recommendations.append("📚 建议复习本章内容后再进行测试。")

    # 找出薄弱维度
    weak_dimensions = [d for d, s in competency_scores.items() if s < 0.6 and competency_counts[d] > 0]
    if weak_dimensions:
        recommendations.append(f"💪 需要加强的能力维度：{', '.join(weak_dimensions)}")

    return ChapterTestResult(
        score=score,
        correct_count=correct_count,
        total_count=total_count,
        competency_scores=competency_scores,
        passed=passed,
        recommendations=recommendations
    )


# ============ 新增：Session 测试流程端点 ============

class StartSessionRequest(BaseModel):
    """开始测试请求"""
    document_id: int
    chapter_number: int
    question_count: int = 10
    mode: str = "practice"  # practice 或 test


@router.post("/start-session")
async def start_quiz_session(
    request: StartSessionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    开始一个新的测试 session

    返回 session_id 和题目列表
    """
    # 清理过期 session（每次创建新 session 时执行）
    cleanup_expired_sessions()
    prune_sessions_if_needed()

    # 获取章节题目
    result = await db.execute(
        select(Question).where(
            and_(
                Question.document_id == request.document_id,
                Question.chapter_number == request.chapter_number,
                Question.is_active == 1
            )
        )
    )
    all_questions = result.scalars().all()

    if len(all_questions) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="该章节暂无题目，请等待 AI 生成或手动添加题目"
        )

    # 随机抽取题目
    import random
    count = min(request.question_count, len(all_questions))
    selected_questions = random.sample(list(all_questions), count)

    # 构造题目数据（不包含答案）
    questions_data = []
    for q in selected_questions:
        q_dict = {
            "id": q.id,
            "question_type": q.question_type,
            "question_text": q.question_text,
            "difficulty": q.difficulty,
            "competency_dimension": q.competency_dimension
        }
        if q.options:
            try:
                q_dict["options"] = json.loads(q.options) if isinstance(q.options, str) else q.options
            except json.JSONDecodeError as e:
                logger.warning(f"题目 {q.id} 的 options JSON 解析失败: {e}")
                q_dict["options"] = None
        questions_data.append(q_dict)

    # 创建 session
    session_id = str(uuid.uuid4())
    session = QuizSession(
        session_id=session_id,
        user_id=current_user.id,
        document_id=request.document_id,
        chapter_number=request.chapter_number,
        questions=questions_data,
        mode=request.mode
    )
    quiz_sessions[session_id] = session

    return {
        "session_id": session_id,
        "questions": questions_data,
        "total_questions": len(questions_data),
        "estimated_time": len(questions_data) * 2,  # 每题约 2 分钟
        "mode": request.mode
    }


class SubmitAnswerRequest(BaseModel):
    """提交答案请求"""
    answer: str
    time_spent: int = 0  # 秒


@router.post("/{session_id}/submit-answer")
async def submit_session_answer(
    session_id: str,
    question_id: int,
    request: SubmitAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    提交单题答案，返回即时反馈

    返回:
    - is_correct: 是否正确
    - correct_answer: 正确答案
    - explanation: 解析
    - feedback: 反馈信息
    """
    # 获取 session
    session = quiz_sessions.get(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="测试 session 不存在或已过期"
        )

    # 验证用户
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此 session"
        )

    # 获取题目信息
    question_result = await db.execute(
        select(Question).where(Question.id == question_id)
    )
    question = question_result.scalar_one_or_none()

    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="题目不存在"
        )

    # 验证答案
    is_correct = request.answer.strip().upper() == question.correct_answer.strip().upper()

    # 记录答案和结果
    session.answers[question_id] = request.answer
    session.results[question_id] = is_correct

    # 生成反馈
    if is_correct:
        feedback = "✅ 回答正确！"
    else:
        feedback = f"❌ 回答错误。正确答案是：{question.correct_answer}"

    return {
        "is_correct": is_correct,
        "correct_answer": question.correct_answer,
        "explanation": question.explanation,
        "feedback": feedback,
        "question_number": session.current_question_index + 1
    }


@router.post("/{session_id}/complete")
async def complete_quiz_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    完成测试，返回完整分析

    返回:
    - score: 总分
    - total: 总题数
    - correct: 正确数
    - passed: 是否通过
    - competency_analysis: 能力分析
    - weak_points: 薄弱环节
    - recommendations: 学习建议
    - mistake_ids: 错题 ID 列表
    """
    # 获取 session
    session = quiz_sessions.get(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="测试 session 不存在或已过期"
        )

    # 验证用户
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此 session"
        )

    # 标记完成
    session.completed_at = datetime.now()

    # 获取题目信息（用于分析）
    question_ids = [q["id"] for q in session.questions]
    questions_result = await db.execute(
        select(Question).where(Question.id.in_(question_ids))
    )
    questions_map = {q.id: q for q in questions_result.scalars().all()}

    # 统计结果
    total = len(session.questions)
    correct = sum(1 for q_id in session.results if session.results.get(q_id, False))
    score = (correct / total * 100) if total > 0 else 0
    passed = score >= 60

    # 能力维度分析
    competency_scores = {
        "comprehension": {"correct": 0, "total": 0},
        "logic": {"correct": 0, "total": 0},
        "terminology": {"correct": 0, "total": 0},
        "memory": {"correct": 0, "total": 0},
        "application": {"correct": 0, "total": 0},
        "stability": {"correct": 0, "total": 0}
    }

    mistake_ids = []

    for q_id, is_correct in session.results.items():
        question = questions_map.get(q_id)
        if not question:
            continue

        dimension = question.competency_dimension or "comprehension"
        competency_scores[dimension]["total"] += 1
        if is_correct:
            competency_scores[dimension]["correct"] += 1
        else:
            mistake_ids.append(q_id)

    # 计算各维度得分
    competency_analysis = {}
    for dim, data in competency_scores.items():
        if data["total"] > 0:
            competency_analysis[dim] = round(
                (data["correct"] / data["total"]) * 100, 1
            )
        else:
            competency_analysis[dim] = None

    # 识别薄弱环节
    weak_points = []
    for dim, score_val in competency_analysis.items():
        if score_val is not None and score_val < 60:
            weak_points.append({
                "dimension": dim,
                "score": score_val,
                "name": {
                    "comprehension": "理解力",
                    "logic": "逻辑推理",
                    "terminology": "术语掌握",
                    "memory": "记忆力",
                    "application": "应用能力",
                    "stability": "稳定性"
                }.get(dim, dim)
            })

    # 生成学习建议
    recommendations = []

    if passed:
        recommendations.append("🎉 恭喜你通过测试！可以进入下一章节学习了。")
    else:
        recommendations.append("📚 建议复习本章内容后再进行测试。")

    if score >= 90:
        recommendations.append("⭐ 表现优秀！你的掌握程度很高。")
    elif score >= 70:
        recommendations.append("👍 表现良好，继续保持！")
    elif score >= 50:
        recommendations.append("💪 还需要继续努力，建议针对错题进行复习。")

    if weak_points:
        weak_names = [w["name"] for w in weak_points]
        recommendations.append(f"📌 建议加强对以下能力的练习：{', '.join(weak_names)}")

    if mistake_ids:
        recommendations.append(f"📝 你有 {len(mistake_ids)} 道错题，建议加入错题本进行复习。")

    # 计算用时
    time_spent_minutes = 0
    if session.completed_at and session.started_at:
        time_spent = (session.completed_at - session.started_at).total_seconds()
        time_spent_minutes = int(time_spent / 60)

    # 清理 session（完成后立即删除以释放内存）
    # Session 数据已通过返回值传递给前端，无需保留
    del quiz_sessions[session_id]

    return {
        "score": round(score, 1),
        "total": total,
        "correct": correct,
        "passed": passed,
        "competency_analysis": competency_analysis,
        "weak_points": weak_points,
        "recommendations": recommendations,
        "mistake_ids": mistake_ids,
        "time_spent_minutes": time_spent_minutes
    }
