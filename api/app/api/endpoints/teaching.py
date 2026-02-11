"""
FastAPI endpoints for the multi-agent teaching system with SSE streaming.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import asyncio
import time
from datetime import datetime, timedelta

from app.db.database import get_db
from app.agents.state.teaching_state import TeachingState
from app.agents.graphs.teaching_graph import create_simple_teaching_flow, TeachingStreamHandler
from app.core.security import get_current_user, get_current_user_optional
from app.models.document import User
from app.core.logging_config import get_logger
from langchain_core.messages import HumanMessage, AIMessage

logger = get_logger(__name__)


router = APIRouter(prefix="/api/teaching", tags=["teaching"])


# ============ Request/Response Models ============
class StartSessionRequest(BaseModel):
    """Request to start a teaching session."""
    user_id: int
    document_id: int
    chapter_number: int
    student_level: int = 1  # Default to L1


class AnswerQuestionRequest(BaseModel):
    """Request to submit an answer."""
    question_id: str
    answer: str


class AskQuestionRequest(BaseModel):
    """Request to ask a question to the tutor."""
    question: str


# ============ In-Memory Session Storage ============
# In production, use Redis or a proper session store
active_sessions: Dict[str, Dict[str, Any]] = {}

# Session 配置
SESSION_TTL_SECONDS = 3600  # 1 小时过期
MAX_SESSIONS = 1000  # 最大 session 数量
SESSION_LAST_ACCESS_KEY = "_last_access"
SESSION_CREATED_AT_KEY = "_created_at"

# 🔥 SSE 连接跟踪 - 防止连接泄漏
active_sse_connections: Dict[str, Any] = {}

# 全局清理任务引用
_cleanup_task: Optional[asyncio.Task] = None


async def cleanup_expired_sessions():
    """
    清理过期的 session
    - 移除超过 TTL 的 session
    - 如果超过最大数量，移除最旧的 session
    """
    try:
        current_time = time.time()

        # 找出过期的 session
        expired_sessions = []
        for session_id, session_data in active_sessions.items():
            last_access = session_data.get(SESSION_LAST_ACCESS_KEY, 0)
            if current_time - last_access > SESSION_TTL_SECONDS:
                expired_sessions.append(session_id)

        # 移除过期 session
        for session_id in expired_sessions:
            del active_sessions[session_id]

        if expired_sessions:
            logger.info(f"🧹 清理了 {len(expired_sessions)} 个过期 session")

        # 如果仍然超过最大数量，移除最旧的
        if len(active_sessions) > MAX_SESSIONS:
            # 按创建时间排序，移除最旧的
            sessions_by_age = sorted(
                active_sessions.items(),
                key=lambda x: x[1].get(SESSION_CREATED_AT_KEY, 0)
            )

            num_to_remove = len(active_sessions) - MAX_SESSIONS
            for session_id, _ in sessions_by_age[:num_to_remove]:
                del active_sessions[session_id]

            logger.info(f"🧹 清理了 {num_to_remove} 个最旧的 session")

    except Exception as e:
        logger.error(f"❌ 清理 session 失败: {e}")


async def session_cleanup_task():
    """
    定时清理任务的协程
    每 5 分钟执行一次清理
    """
    while True:
        try:
            await asyncio.sleep(300)  # 5 分钟
            await cleanup_expired_sessions()
            await cleanup_stale_sse_connections()  # 🔥 同时清理 SSE 连接
        except asyncio.CancelledError:
            logger.info("🛑 Session 清理任务已停止")
            break
        except Exception as e:
            logger.error(f"❌ Session 清理任务异常: {e}")
            # 继续运行，不要因为单次错误而停止


def start_session_cleanup_task() -> asyncio.Task:
    """
    启动清理任务（由 main.py 的 lifespan 调用）
    
    Returns:
        asyncio.Task: 清理任务
    """
    global _cleanup_task
    if _cleanup_task is None or _cleanup_task.done():
        _cleanup_task = asyncio.create_task(session_cleanup_task())
        logger.info("✅ Session 清理任务已启动")
    return _cleanup_task


def update_session_access(session_id: str, session_data: Dict[str, Any]):
    """更新 session 的最后访问时间"""
    current_time = time.time()
    session_data[SESSION_LAST_ACCESS_KEY] = current_time
    if SESSION_CREATED_AT_KEY not in session_data:
        session_data[SESSION_CREATED_AT_KEY] = current_time
    active_sessions[session_id] = session_data


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """获取 session 并更新访问时间"""
    session_data = active_sessions.get(session_id)
    if session_data:
        update_session_access(session_id, session_data)
    return session_data


# ============ SSE 连接管理 ============
async def check_client_disconnect(response: StreamingResponse) -> bool:
    """
    检查客户端是否已断开连接

    Returns:
        True if client disconnected
    """
    # FastAPI 的 StreamingResponse 会在客户端断开时触发异常
    # 我们通过捕获生成器中的异常来检测断开
    return False


def track_sse_connection(connection_id: str, request_type: str = "unknown"):
    """跟踪 SSE 连接"""
    active_sse_connections[connection_id] = {
        "connected_at": time.time(),
        "request_type": request_type,
        "active": True
    }
    logger.info(f"📡 SSE 连接建立: {connection_id} ({request_type})")


def untrack_sse_connection(connection_id: str):
    """取消跟踪 SSE 连接"""
    if connection_id in active_sse_connections:
        conn = active_sse_connections.pop(connection_id)
        duration = time.time() - conn["connected_at"]
        logger.info(f"📡 SSE 连接关闭: {connection_id} (持续 {duration:.1f}秒)")


async def cleanup_stale_sse_connections():
    """清理超过 10 分钟的 SSE 连接"""
    try:
        current_time = time.time()
        stale_connections = []
        for conn_id, conn_data in active_sse_connections.items():
            if current_time - conn_data["connected_at"] > 600:  # 10分钟
                stale_connections.append(conn_id)

        for conn_id in stale_connections:
            untrack_sse_connection(conn_id)

        if stale_connections:
            logger.info(f"🧹 清理了 {len(stale_connections)} 个过期的 SSE 连接")
    except Exception as e:
        logger.error(f"❌ 清理 SSE 连接失败: {e}")


# ============ Helper Functions ============
async def get_chapter_content(
    db: AsyncSession,
    document_id: int,
    chapter_number: int
) -> tuple[str, str]:
    """
    Retrieve chapter content from database.

    Args:
        db: Database session
        document_id: Document ID
        chapter_number: Chapter number

    Returns:
        Tuple of (chapter_title, chapter_content)
    """
    from app.core.chroma import get_document_collection
    from app.models.document import Document
    from sqlalchemy import select

    # Get document info
    doc_result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = doc_result.scalar_one_or_none()

    if not document or not document.md5_hash:
        return (
            f"第{chapter_number}章",
            f"未找到文档内容。"
        )

    # Get chapter title from progress table
    from app.models.document import Progress
    progress_result = await db.execute(
        select(Progress).where(
            Progress.document_id == document_id,
            Progress.chapter_number == chapter_number
        )
    )
    progress = progress_result.scalar_one_or_none()

    chapter_title = progress.chapter_title if progress else f"第{chapter_number}章"

    # Retrieve document chunks from ChromaDB
    collection = get_document_collection(document.md5_hash)
    if not collection or collection.count() == 0:
        return (
            chapter_title,
            f"文档内容尚未处理完成，请稍后再试。"
        )

    # Get all chunks and combine them
    results = collection.get()
    if results and results['documents']:
        # Combine all chunks into full text
        full_text = "\n\n".join(results['documents'])

        # Try to extract specific chapter content
        # Look for chapter markers in the text
        import re

        # Pattern to find the chapter start
        chapter_patterns = [
            rf'第{chapter_number}章',
            rf'第\s*{chapter_number}\s*章',
            rf'Chapter\s*{chapter_number}',
        ]

        chapter_start = -1
        for pattern in chapter_patterns:
            match = re.search(pattern, full_text)
            if match:
                chapter_start = match.start()
                break

        if chapter_start >= 0:
            # Try to find where the next chapter starts
            next_chapter_patterns = [
                rf'第{chapter_number + 1}章',
                rf'第\s*{chapter_number + 1}\s*章',
                rf'Chapter\s*{chapter_number + 1}',
            ]

            chapter_end = len(full_text)
            for pattern in next_chapter_patterns:
                match = re.search(pattern, full_text[chapter_start:])
                if match:
                    chapter_end = chapter_start + match.start()
                    break

            # Extract chapter content
            chapter_content = full_text[chapter_start:chapter_end].strip()

            # If content is too short, just return full text
            if len(chapter_content) < 500:
                chapter_content = full_text
        else:
            # No chapter marker found, return full text
            chapter_content = full_text

        # Limit content length to avoid overwhelming the LLM
        if len(chapter_content) > 15000:
            chapter_content = chapter_content[:15000] + "\n\n(内容过长，已截断)"

        # 如果内容太少，给出提示
        if len(chapter_content) < 500:
            chapter_content = f"⚠️ 文档内容提取不完整（可能是因为PDF是扫描版）。\n\n当前可用的内容:\n\n{chapter_content}\n\n💡 建议：\n1. 重新上传文字版PDF\n2. 或使用支持OCR的工具处理扫描版PDF"

        return (chapter_title, chapter_content)

    return (
        chapter_title,
        "⚠️ 无法获取文档内容。这可能是因为：\n1. PDF是扫描版，文字无法提取\n2. 文档处理尚未完成\n\n💡 建议：请重新上传文字版PDF教科书。"
    )


# ============ Endpoints ============
@router.post("/session/start")
async def start_teaching_session(
    request: StartSessionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Start a new teaching session with SSE streaming.

    This endpoint:
    1. Creates initial state
    2. Runs Architect node (design curriculum)
    3. Runs Tutor node (provide explanation)
    4. Runs Examiner node (generate questions)
    5. Streams results via SSE
    """
    # Get chapter content
    chapter_title, chapter_content = await get_chapter_content(
        db,
        request.document_id,
        request.chapter_number
    )

    # Check if document is OCR-generated
    from app.models.document import Document
    from sqlalchemy import select

    doc_result = await db.execute(
        select(Document).where(Document.id == request.document_id)
    )
    document = doc_result.scalar_one_or_none()

    is_ocr_document = False
    ocr_warning_message = None

    if document and document.has_text_layer == 0:
        is_ocr_document = True
        ocr_confidence = document.ocr_confidence or 0.0
        ocr_warning_message = (
            "📖 **OCR识别说明**\n\n"
            f"我已通过AI视觉识别技术读取了这本扫描教材（识别置信度：{ocr_confidence*100:.1f}%）。\n\n"
            "**请注意**：\n"
            "• 某些复杂公式、符号可能存在细微偏差\n"
            "• 建议您结合原书核对重要内容\n"
            "• 我会尽力为您提供准确的学习指导\n\n"
            "让我们开始学习吧！"
        )

    # Create initial conversation history with OCR warning if applicable
    conversation_history = []
    if ocr_warning_message:
        conversation_history.append(AIMessage(content=ocr_warning_message))

    # Create initial state
    initial_state: TeachingState = {
        # Student Information
        "student_level": request.student_level,
        "user_id": request.user_id,
        "document_id": request.document_id,

        # Chapter Information
        "current_chapter": request.chapter_number,
        "chapter_title": chapter_title,
        "chapter_content": chapter_content,

        # Learning Progress
        "learning_objectives": [],
        "wrong_questions": [],
        "correct_questions": [],
        "quiz_attempts": 0,
        "success_rate": 0.0,

        # Agent Outputs
        "architect_plan": None,
        "examiner_questions": [],
        "tutor_explanation": None,
        "feedback": None,

        # Session State
        "conversation_history": conversation_history,
        "current_step": "init",
        "needs_level_adjustment": False,

        # Streaming
        "streaming_content": None,

        # OCR metadata
        "is_ocr_document": is_ocr_document,
        "ocr_confidence": document.ocr_confidence if document else 0.0
    }

    # Store session with timestamp
    session_id = f"{request.user_id}_{request.document_id}_{request.chapter_number}"
    update_session_access(session_id, initial_state)

    # Create stream handler
    graph = create_simple_teaching_flow()
    stream_handler = TeachingStreamHandler(graph)

    # 🔥 生成唯一的连接 ID 用于跟踪
    connection_id = f"session_start_{request.user_id}_{request.document_id}_{request.chapter_number}_{int(time.time() * 1000)}"

    async def event_generator():
        """Generate SSE events."""
        timeout_seconds = 300  # 5分钟超时

        # 🔥 跟踪 SSE 连接
        track_sse_connection(connection_id, "session_start")

        try:
            async with asyncio.timeout(timeout_seconds):
                async for event in stream_handler.stream_teaching_session(initial_state):
                    # Format as SSE
                    event_data = json.dumps(event, ensure_ascii=True)
                    yield f"data: {event_data}\n\n"

                    # Small delay between events
                    await asyncio.sleep(0.1)

        except asyncio.TimeoutError:
            timeout_event = {
                "type": "error",
                "message": "请求超时，请稍后重试"
            }
            yield f"data: {json.dumps(timeout_event, ensure_ascii=False)}\n\n"
        except asyncio.CancelledError:
            # 🔥 客户端断开连接或请求被取消
            logger.info(f"🔌 SSE 连接被取消: {connection_id}")
            raise
        except GeneratorExit:
            # 🔥 客户端断开连接
            logger.info(f"🔌 SSE 客户端断开: {connection_id}")
            raise
        except Exception as e:
            error_event = {
                "type": "error",
                "message": str(e)
            }
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
        finally:
            # 🔥 清理连接
            untrack_sse_connection(connection_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/session/{session_id}/answer")
async def submit_answer(
    session_id: str,
    request: AnswerQuestionRequest
):
    """
    Submit an answer and stream evaluation feedback.

    Returns SSE stream with evaluation results and feedback.
    """
    # Get session state
    state = get_session(session_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Create stream handler
    graph = create_simple_teaching_flow()
    stream_handler = TeachingStreamHandler(graph)

    # 🔥 生成唯一的连接 ID
    connection_id = f"answer_{session_id}_{int(time.time() * 1000)}"

    async def event_generator():
        """Generate SSE events for answer evaluation."""
        # 🔥 跟踪 SSE 连接
        track_sse_connection(connection_id, "submit_answer")

        try:
            async for event in stream_handler.stream_answer_evaluation(
                state,
                request.question_id,
                request.answer
            ):
                event_data = json.dumps(event, ensure_ascii=False)
                yield f"data: {event_data}\n\n"
                await asyncio.sleep(0.05)

            # Update session state
            update_session_access(session_id, state)

        except asyncio.CancelledError:
            logger.info(f"🔌 SSE 连接被取消: {connection_id}")
            raise
        except GeneratorExit:
            logger.info(f"🔌 SSE 客户端断开: {connection_id}")
            raise
        except Exception as e:
            error_event = {
                "type": "error",
                "message": str(e)
            }
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
        finally:
            # 🔥 清理连接
            untrack_sse_connection(connection_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


@router.post("/session/{session_id}/ask")
async def ask_tutor(
    session_id: str,
    request: AskQuestionRequest
):
    """
    Ask the tutor a question and stream the response.

    Returns SSE stream with tutor's answer.
    """
    from app.agents.nodes.tutor import TutorAgent

    # Get session state
    state = get_session(session_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Add question to conversation history
    state["conversation_history"].append(HumanMessage(content=request.question))

    # Create tutor and get answer
    tutor = TutorAgent()

    # 🔥 生成唯一的连接 ID
    connection_id = f"ask_tutor_{session_id}_{int(time.time() * 1000)}"

    async def event_generator():
        """Generate SSE events for tutor response."""
        timeout_seconds = 120  # 2分钟超时

        # 🔥 跟踪 SSE 连接
        track_sse_connection(connection_id, "ask_tutor")

        try:
            async with asyncio.timeout(timeout_seconds):
                # Send typing indicator
                typing_event = {
                    "type": "tutor_thinking",
                    "message": "老师正在思考..."
                }
                yield f"data: {json.dumps(typing_event, ensure_ascii=False)}\n\n"

                # Get answer
                answer = await tutor.answer_question(state, request.question)

                # Stream the answer
                response_event = {
                    "type": "tutor_response",
                    "content": answer
                }
                yield f"data: {json.dumps(response_event, ensure_ascii=False)}\n\n"

                # Update conversation history
                state["conversation_history"].append(AIMessage(content=answer))
                active_sessions[session_id] = state

        except asyncio.TimeoutError:
            timeout_event = {
                "type": "error",
                "message": "请求超时，请稍后重试"
            }
            yield f"data: {json.dumps(timeout_event, ensure_ascii=False)}\n\n"
        except asyncio.CancelledError:
            logger.info(f"🔌 SSE 连接被取消: {connection_id}")
            raise
        except GeneratorExit:
            logger.info(f"🔌 SSE 客户端断开: {connection_id}")
            raise
        except Exception as e:
            error_event = {
                "type": "error",
                "message": str(e)
            }
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
        finally:
            # 🔥 清理连接
            untrack_sse_connection(connection_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


@router.get("/session/{session_id}/status")
async def get_session_status(session_id: str):
    """
    Get current session status without streaming.
    """
    state = get_session(session_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return {
        "session_id": session_id,
        "student_level": state["student_level"],
        "quiz_attempts": state["quiz_attempts"],
        "success_rate": state["success_rate"],
        "correct_count": len(state["correct_questions"]),
        "wrong_count": len(state["wrong_questions"]),
        "current_step": state["current_step"]
    }


@router.delete("/session/{session_id}")
async def end_session(session_id: str):
    """
    End a teaching session and clean up.
    """
    if session_id in active_sessions:
        del active_sessions[session_id]
        return {"message": "Session ended successfully"}

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Session not found"
    )


@router.get("/levels")
async def get_level_descriptions():
    """
    Get descriptions of all cognitive levels (L1-L5).
    """
    from app.agents.state.level_prompts import LEVEL_DESCRIPTIONS

    return {
        "levels": LEVEL_DESCRIPTIONS,
        "adjustment_rules": {
            "upgrade": "正确率 >= 85%，连续答对3题",
            "downgrade": "正确率 <= 50%，连续答错2题"
        }
    }


@router.post("/session/{session_id}/hint")
async def get_hint(
    session_id: str,
    question_id: str,
    attempt: int = 1
):
    """
    Get a hint for a specific question.

    Streams the hint via SSE.
    """
    from app.agents.nodes.tutor import tutor_hint_node

    # Get session state
    state = get_session(session_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # 🔥 生成唯一的连接 ID
    connection_id = f"hint_{session_id}_{question_id}_{int(time.time() * 1000)}"

    async def event_generator():
        """Generate SSE events for hint."""
        # 🔥 跟踪 SSE 连接
        track_sse_connection(connection_id, "hint")

        try:
            # Get hint
            state = await tutor_hint_node(state, question_id, attempt)
            active_sessions[session_id] = state

            hint_event = {
                "type": "hint",
                "content": state.get("streaming_content", ""),
                "attempt": attempt
            }
            yield f"data: {json.dumps(hint_event, ensure_ascii=False)}\n\n"

        except asyncio.CancelledError:
            logger.info(f"🔌 SSE 连接被取消: {connection_id}")
            raise
        except GeneratorExit:
            logger.info(f"🔌 SSE 客户端断开: {connection_id}")
            raise
        except Exception as e:
            error_event = {
                "type": "error",
                "message": str(e)
            }
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
        finally:
            # 🔥 清理连接
            untrack_sse_connection(connection_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


# ============ 新增：简化对话端点 ============
class ChatRequest(BaseModel):
    """简化对话请求（兼容前端）"""
    message: str
    chapter_id: str = "1"
    student_level: int = 3
    stream: bool = True
    user_id: Optional[int] = None  # 可选，如果提供则验证
    document_id: Optional[int] = None  # 文档ID
    subsection_id: Optional[str] = None  # 小节ID
    subsection_title: Optional[str] = None  # 小节标题


# ============ 新增：学习进度分析端点 ============

async def calculate_completion_progress(
    db: AsyncSession,
    user_id: int,
    document_id: int,
    chapter_number: int
) -> dict:
    """
    计算章节完成度 (0-100%)

    根据对话轮数、对话深度、测试表现等综合计算
    """
    from app.models.document import ConversationHistory, QuizAttempt, Progress
    from sqlalchemy import select, func

    # 1. 获取对话数据
    conv_result = await db.execute(
        select(ConversationHistory).where(
            ConversationHistory.user_id == user_id,
            ConversationHistory.document_id == document_id,
            ConversationHistory.chapter_number == chapter_number
        )
    )
    conversations = conv_result.scalars().all()

    user_messages = [c for c in conversations if c.role == 'user']
    ai_messages = [c for c in conversations if c.role == 'assistant']

    # 2. 获取测试数据
    quiz_result = await db.execute(
        select(QuizAttempt).join(Progress).where(
            Progress.user_id == user_id,
            Progress.document_id == document_id,
            Progress.chapter_number == chapter_number
        )
    )
    quiz_attempts = quiz_result.scalars().all()

    # 3. 计算各项指标
    dialogue_rounds = len(user_messages)

    # 平均对话深度（字数）
    total_words = sum(len(c.content) for c in conversations)
    avg_depth = total_words / len(conversations) if conversations else 0

    # 测试表现
    quiz_score = 0
    if quiz_attempts:
        correct_count = sum(1 for q in quiz_attempts if q.is_correct)
        quiz_score = (correct_count / len(quiz_attempts)) * 100

    # 4. 综合计算
    progress = 0

    # 对话轮数（目标：至少10轮）- 权重 20%
    if dialogue_rounds >= 10:
        progress += 20
    else:
        progress += (dialogue_rounds / 10) * 20

    # 对话深度（目标：平均50字）- 权重 15%
    if avg_depth >= 50:
        progress += 15
    else:
        progress += (avg_depth / 50) * 15

    # 测试表现 - 权重 30%
    progress += quiz_score * 0.3

    # 活跃度（最近有学习）- 权重 10%
    if conversations:
        last_conv_time = max(c.created_at for c in conversations)
        if (datetime.now() - last_conv_time).days <= 7:
            progress += 10

    # 内容覆盖度（基础）- 权重 25%
    if dialogue_rounds >= 3:
        progress += 25
    elif dialogue_rounds >= 1:
        progress += 10

    return min(int(progress), 100)


@router.get("/progress-analysis")
async def get_progress_analysis(
    user_id: int,
    document_id: int,
    chapter_number: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    获取学习进度分析

    返回:
    - completion_percentage: 完成百分比 (0-100)
    - dialogue_rounds: 对话轮数
    - study_time_minutes: 学习时长（分钟）
    - keypoints_learned: 已学知识点
    - keypoints_learning: 学习中知识点
    - mastery_level: 掌握程度
    - recommendations: 学习建议
    """
    from app.models.document import ConversationHistory, QuizAttempt, Progress
    from sqlalchemy import select

    # 验证用户权限
    if current_user and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问其他用户的数据"
        )

    # 1. 计算完成度
    completion = await calculate_completion_progress(
        db, user_id, document_id, chapter_number
    )

    # 2. 获取对话数据
    conv_result = await db.execute(
        select(ConversationHistory).where(
            ConversationHistory.user_id == user_id,
            ConversationHistory.document_id == document_id,
            ConversationHistory.chapter_number == chapter_number
        ).order_by(ConversationHistory.created_at.desc())
    )
    conversations = conv_result.scalars().all()

    # 3. 计算学习时长（分钟）
    study_time_minutes = 0
    if conversations:
        # 假设每次对话平均 3 分钟
        study_time_minutes = len(conversations) * 3

    # 4. 获取测试数据
    quiz_result = await db.execute(
        select(QuizAttempt).join(Progress).where(
            Progress.user_id == user_id,
            Progress.document_id == document_id,
            Progress.chapter_number == chapter_number
        )
    )
    quiz_attempts = quiz_result.scalars().all()

    # 5. 分析掌握程度
    dialogue_rounds = len([c for c in conversations if c.role == 'user'])
    quiz_success_rate = 0
    if quiz_attempts:
        correct_count = sum(1 for q in quiz_attempts if q.is_correct)
        quiz_success_rate = (correct_count / len(quiz_attempts)) * 100

    # 判断掌握等级
    if quiz_success_rate >= 90 and dialogue_rounds >= 10:
        mastery_level = "advanced"
        mastery_text = "精通"
    elif quiz_success_rate >= 70 and dialogue_rounds >= 7:
        mastery_level = "proficient"
        mastery_text = "熟练"
    elif quiz_success_rate >= 50 and dialogue_rounds >= 5:
        mastery_level = "intermediate"
        mastery_text = "掌握"
    elif dialogue_rounds >= 3:
        mastery_level = "beginner"
        mastery_text = "入门"
    else:
        mastery_level = "novice"
        mastery_text = "初学"

    # 6. 生成学习建议
    recommendations = []
    if dialogue_rounds < 5:
        recommendations.append("建议多提问，与老师进行更多互动")
    if quiz_success_rate < 60 and quiz_attempts:
        recommendations.append("建议复习错题，巩固知识点")
    if completion < 50:
        recommendations.append("继续学习，完成更多对话练习")
    if completion >= 80:
        recommendations.append("可以尝试进行章节测试，检验学习成果")

    return {
        "completion_percentage": completion,
        "dialogue_rounds": dialogue_rounds,
        "study_time_minutes": study_time_minutes,
        "quiz_attempts": len(quiz_attempts),
        "quiz_success_rate": round(quiz_success_rate, 1),
        "mastery_level": mastery_level,
        "mastery_text": mastery_text,
        "recommendations": recommendations,
        "last_activity": conversations[0].created_at.isoformat() if conversations else None
    }


@router.get("/conversation-summary")
async def get_conversation_summary(
    user_id: int,
    document_id: int,
    chapter_number: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    获取对话摘要

    返回:
    - summary: 对话摘要
    - key_concepts: 讨论的关键概念
    - user_questions_count: 用户提问数
    - last_discussed: 最后讨论时间
    """
    from app.models.document import ConversationHistory
    from sqlalchemy import select

    # 验证用户权限
    if current_user and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问其他用户的数据"
        )

    # 获取对话记录
    result = await db.execute(
        select(ConversationHistory).where(
            ConversationHistory.user_id == user_id,
            ConversationHistory.document_id == document_id,
            ConversationHistory.chapter_number == chapter_number
        ).order_by(ConversationHistory.created_at.asc())
    )
    conversations = result.scalars().all()

    if not conversations:
        return {
            "summary": "还没有开始学习这个章节",
            "key_concepts": [],
            "user_questions_count": 0,
            "last_discussed": None
        }

    # 统计
    user_questions = [c for c in conversations if c.role == 'user']
    user_questions_count = len(user_questions)

    # 提取关键概念（简单实现：从用户问题中提取关键词）
    # TODO: 可以使用 NLP 技术进行更精确的关键词提取
    key_concepts = set()
    for conv in user_questions[:10]:  # 分析最近10个问题
        content = conv.content
        # 简单提取：识别中文词汇（2-4个字）
        import re
        concepts = re.findall(r'[\u4e00-\u9fff]{2,4}', content)
        key_concepts.update(concepts[:3])  # 每个问题最多取3个概念

    # 生成简单摘要
    if user_questions_count == 0:
        summary = "还没有提问，开始与老师对话吧！"
    elif user_questions_count < 5:
        summary = f"进行了 {user_questions_count} 轮对话，正在初步探索章节内容。"
    elif user_questions_count < 10:
        summary = f"进行了 {user_questions_count} 轮对话，逐步深入理解知识点。"
    else:
        summary = f"进行了 {user_questions_count} 轮对话，深入学习了章节内容。"

    return {
        "summary": summary,
        "key_concepts": list(key_concepts)[:10],  # 最多返回10个概念
        "user_questions_count": user_questions_count,
        "total_messages": len(conversations),
        "last_discussed": conversations[-1].created_at.isoformat() if conversations else None
    }


@router.post("/chat")
async def chat_with_tutor(
    request: ChatRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    带对话记忆的对话端点，兼容前端 StudyChat 组件调用格式。

    1. 加载历史对话记录
    2. 调用 Tutor 智能体生成回复
    3. 以 SSE 流式返回
    4. 自动保存对话到数据库
    """
    from app.agents.nodes.tutor import TutorAgent
    from app.core.config import settings, get_model_name
    from app.models.document import ConversationHistory
    from sqlalchemy import select

    # 获取真实用户 ID（优先使用认证用户，其次使用请求中的 user_id）
    user_id = current_user.id if current_user else request.user_id
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要提供用户认证"
        )

    # 🔥 加载历史对话记录（最近20条）
    history_query = select(ConversationHistory).where(
        ConversationHistory.user_id == user_id
    )

    # 如果指定了章节，加载该章节的历史记录
    if request.chapter_id:
        history_query = history_query.where(
            ConversationHistory.chapter_number == int(request.chapter_id)
        )

    # 如果指定了文档，加载该文档的历史记录
    if request.document_id:
        history_query = history_query.where(
            ConversationHistory.document_id == request.document_id
        )

    history_query = history_query.order_by(
        ConversationHistory.created_at.desc()
    ).limit(20)

    history_result = await db.execute(history_query)
    history_records = history_result.scalars().all()

    # 转换为 LangChain 消息格式（最新的在最后）
    conversation_history = []
    for record in reversed(history_records):
        if record.role == "user":
            conversation_history.append(HumanMessage(content=record.content))
        else:
            conversation_history.append(AIMessage(content=record.content))

    logger.info(f"📚 加载了 {len(conversation_history)} 条历史对话记录 for user {user_id}")

    # 创建 Tutor 智能体
    model_name = get_model_name(request.student_level)
    tutor = TutorAgent(api_key=settings.DASHSCOPE_API_KEY, model=model_name)

    # 准备对话状态（包含历史记录）
    temp_state: TeachingState = {
        "student_level": request.student_level,
        "user_id": user_id,
        "document_id": request.document_id or 1,
        "current_chapter": int(request.chapter_id),
        "chapter_title": f"第{request.chapter_id}章",
        "chapter_content": "",
        "learning_objectives": [],
        "wrong_questions": [],
        "correct_questions": [],
        "quiz_attempts": 0,
        "success_rate": 0.0,
        "architect_plan": None,
        "examiner_questions": [],
        "tutor_explanation": None,
        "feedback": None,
        "conversation_history": conversation_history,  # 🔥 使用加载的历史记录
        "current_step": "chat",
        "needs_level_adjustment": False,
        "streaming_content": None,
        "subsection_id": request.subsection_id,
        "subsection_title": request.subsection_title
    }

    if request.stream:
        # SSE 流式响应
        # 🔥 生成唯一的连接 ID 用于跟踪
        connection_id = f"chat_{user_id}_{int(time.time() * 1000)}"

        async def event_generator():
            timeout_seconds = 180  # 3分钟超时
            full_response = ""  # 用于存储完整响应

            # 🔥 跟踪 SSE 连接
            track_sse_connection(connection_id, "chat")

            try:
                async with asyncio.timeout(timeout_seconds):
                    # 生成回复
                    response = await tutor.answer_question(
                        temp_state,
                        request.message
                    )
                    full_response = response  # 保存完整响应

                    # 按词/短语分割（优化流式性能）
                    import re
                    # 按中文词汇、英文单词、标点符号分割
                    chunks = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9]+|[^\w\s]', response)

                    # 如果分词失败，回退到逐字发送
                    if not chunks:
                        chunks = list(response)

                    # 逐词发送
                    for chunk in chunks:
                        chunk_event = {
                            "content": chunk
                        }
                        yield f"data: {json.dumps(chunk_event, ensure_ascii=False)}\n\n"
                        await asyncio.sleep(0.03)  # 打字速度

                    # 发送完成标记
                    yield f"data: [DONE]\n\n"

                    # 🔥 保存对话到数据库（流式结束后）
                    try:
                        # 保存用户消息
                        user_conv = ConversationHistory(
                            user_id=user_id,
                            document_id=request.document_id or 1,
                            chapter_number=int(request.chapter_id),
                            subsection_id=request.subsection_id or None,
                            role="user",
                            content=request.message,
                            student_level_at_time=request.student_level
                        )
                        db.add(user_conv)

                        # 保存 AI 回复
                        assistant_conv = ConversationHistory(
                            user_id=user_id,
                            document_id=request.document_id or 1,
                            chapter_number=int(request.chapter_id),
                            subsection_id=request.subsection_id or None,
                            role="assistant",
                            content=full_response,
                            student_level_at_time=request.student_level
                        )
                        db.add(assistant_conv)

                        await db.commit()
                        logger.info(f"💾 已保存对话记录 for user {user_id}")
                    except Exception as save_error:
                        logger.error(f"❌ 保存对话失败: {save_error}")
                        # 不影响用户体验，继续响应

            except asyncio.TimeoutError:
                error_event = {
                    "type": "error",
                    "message": "请求超时，请稍后重试"
                }
                yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
            except asyncio.CancelledError:
                # 🔥 客户端断开连接或请求被取消
                logger.info(f"🔌 SSE 连接被取消: {connection_id}")
                raise  # 重新抛出以触发 finally 块
            except GeneratorExit:
                # 🔥 客户端断开连接（FastAPI 特有）
                logger.info(f"🔌 SSE 客户端断开: {connection_id}")
                raise
            except Exception as e:
                error_event = {
                    "type": "error",
                    "message": f"生成回复时出错: {str(e)}"
                }
                yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
            finally:
                # 🔥 无论什么情况都清理连接
                untrack_sse_connection(connection_id)
                logger.info(f"✅ SSE 连接已清理: {connection_id}")

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    else:
        # 非流式响应
        try:
            response = await tutor.answer_question(temp_state, request.message)
            return {"content": response}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"生成回复失败: {str(e)}"
            )
