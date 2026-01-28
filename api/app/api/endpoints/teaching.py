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
from langchain_core.messages import HumanMessage, AIMessage


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

    except Exception as e:
        print(f"清理 session 失败: {e}")


async def session_cleanup_task():
    """
    定时清理任务的协程
    每 5 分钟执行一次清理
    """
    while True:
        await asyncio.sleep(300)  # 5 分钟
        await cleanup_expired_sessions()


# 启动清理任务
_cleanup_task = None


def get_session_cleanup_task():
    """获取或创建清理任务"""
    global _cleanup_task
    if _cleanup_task is None:
        _cleanup_task = asyncio.create_task(session_cleanup_task())
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
    # For now, return mock content
    # In production, retrieve from actual stored content
    return (
        f"第{chapter_number}章",
        f"这是第{chapter_number}章的内容。在实际实现中，这里会包含从文档中提取的完整章节文本。"
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
    # 启动清理任务
    get_session_cleanup_task()

    # Get chapter content
    chapter_title, chapter_content = await get_chapter_content(
        db,
        request.document_id,
        request.chapter_number
    )

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
        "conversation_history": [],
        "current_step": "init",
        "needs_level_adjustment": False,

        # Streaming
        "streaming_content": None
    }

    # Store session with timestamp
    session_id = f"{request.user_id}_{request.document_id}_{request.chapter_number}"
    update_session_access(session_id, initial_state)

    # Create stream handler
    graph = create_simple_teaching_flow()
    stream_handler = TeachingStreamHandler(graph)

    async def event_generator():
        """Generate SSE events."""
        try:
            async for event in stream_handler.stream_teaching_session(initial_state):
                # Format as SSE
                event_data = json.dumps(event, ensure_ascii=False)
                yield f"data: {event_data}\n\n"

                # Small delay between events
                await asyncio.sleep(0.1)

        except Exception as e:
            error_event = {
                "type": "error",
                "message": str(e)
            }
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

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

    async def event_generator():
        """Generate SSE events for answer evaluation."""
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

        except Exception as e:
            error_event = {
                "type": "error",
                "message": str(e)
            }
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

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

    async def event_generator():
        """Generate SSE events for tutor response."""
        try:
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

        except Exception as e:
            error_event = {
                "type": "error",
                "message": str(e)
            }
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

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

    async def event_generator():
        """Generate SSE events for hint."""
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

        except Exception as e:
            error_event = {
                "type": "error",
                "message": str(e)
            }
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

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


@router.post("/chat")
async def chat_with_tutor(
    request: ChatRequest,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    简化的对话端点，兼容前端 StudyChat 组件调用格式。

    直接调用 Tutor 智能体生成回复，并以 SSE 流式返回。
    """
    from app.agents.nodes.tutor import TutorAgent
    from app.core.config import settings, get_model_name

    # 获取真实用户 ID（优先使用认证用户，其次使用请求中的 user_id）
    user_id = current_user.id if current_user else request.user_id
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要提供用户认证"
        )

    # 创建 Tutor 智能体
    model_name = get_model_name(request.student_level)
    tutor = TutorAgent(api_key=settings.DASHSCOPE_API_KEY, model=model_name)

    # 准备对话状态
    temp_state: TeachingState = {
        "student_level": request.student_level,
        "user_id": user_id,  # 使用真实用户 ID
        "document_id": 1,  # TODO: 从数据库获取用户当前学习的文档
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
        "conversation_history": [],
        "current_step": "chat",
        "needs_level_adjustment": False,
        "streaming_content": None
    }

    if request.stream:
        # SSE 流式响应
        async def event_generator():
            try:
                # 生成回复
                response = await tutor.answer_question(
                    temp_state,
                    request.message
                )

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

            except Exception as e:
                error_event = {
                    "type": "error",
                    "message": f"生成回复时出错: {str(e)}"
                }
                yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

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
