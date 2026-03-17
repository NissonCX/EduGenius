"""
EduGenius Backend API
FastAPI application with MD5-based document deduplication and ChromaDB integration.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import asyncio

from app.db.database import init_db
from app.api.endpoints.documents import router as documents_router
from app.api.endpoints.teaching import router as teaching_router
from app.api.endpoints.users import router as users_router
from app.api.endpoints.quiz import router as quiz_router
from app.api.endpoints import quiz_ai
quiz_ai_router = quiz_ai.router
from app.api.endpoints.mistakes import router as mistakes_router
from app.api.endpoints.knowledge import router as knowledge_router
from app.core.errors import register_exception_handlers
from app.core.logging_config import setup_logging, get_logger
from app.core.redis_client import redis_client

# 初始化日志系统
log_level = os.getenv("LOG_LEVEL", "INFO")
enable_json_logs = os.getenv("ENABLE_JSON_LOGS", "false").lower() == "true"
setup_logging(log_level=log_level, enable_json=enable_json_logs)
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Initializes database on startup and manages background tasks.
    """
    # Startup
    logger.info("🚀 Initializing EduGenius Backend...")
    await init_db()
    logger.info("✅ Database initialized successfully")

    # 🔥 初始化 Redis 缓存
    from app.core.redis_client import init_redis
    redis_ok = await init_redis()
    if redis_ok:
        logger.info("✅ Redis 缓存已启用")
    else:
        logger.info("⚠️ Redis 缓存未启用，将使用数据库直接查询")

    # 启动 Session 清理任务
    from app.api.endpoints.teaching import start_session_cleanup_task
    cleanup_task = start_session_cleanup_task()
    logger.info("✅ Session cleanup task started")

    yield

    # Shutdown
    logger.info("👋 Shutting down EduGenius Backend...")

    # 🔥 关闭 Redis 连接
    from app.core.redis_client import close_redis
    await close_redis()
    logger.info("✅ Redis 连接已关闭")

    # 停止清理任务
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            logger.info("✅ Session cleanup task stopped")
        except Exception as e:
            logger.error(f"❌ Error stopping cleanup task: {e}")


# Create FastAPI app
app = FastAPI(
    title="EduGenius API",
    description="AI-powered adaptive learning platform with MD5-based document deduplication",
    version="1.0.0",
    lifespan=lifespan
)

# 注册异常处理器
register_exception_handlers(app)

# CORS middleware for frontend integration
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents_router)
app.include_router(teaching_router)
app.include_router(users_router)
app.include_router(quiz_router)
app.include_router(quiz_ai_router)  # 新增：AI出题路由
app.include_router(mistakes_router)
app.include_router(knowledge_router)  # 新增：知识图谱路由


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "EduGenius API - AI 自适应教育平台",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "documents": "/api/documents",
            "teaching": "/api/teaching",
            "users": "/api/users",
            "quiz": "/api/quiz",
            "knowledge": "/api/knowledge",
            "health": "/health"
        },
        "features": {
            "md5_deduplication": "文档 MD5 去重",
            "multi_agent_teaching": "多智能体教学系统",
            "adaptive_levels": "L1-L5 自适应等级",
            "sse_streaming": "SSE 流式输出",
            "knowledge_graph": "知识图谱可视化",
            "redis_cache": "Redis 缓存优化"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    # 检查 Redis 状态
    redis_status = "disconnected"
    if redis_client:
        try:
            is_connected = await redis_client.is_connected()
            redis_status = "connected" if is_connected else "disconnected"
        except Exception as e:
            logger.warning(f"Redis 连接检查失败: {e}")
            redis_status = "error"

    return {
        "status": "healthy",
        "service": "EduGenius Backend",
        "database": "connected",
        "redis": redis_status,
        "chroma_db": "initialized",
        "langgraph": "ready",
        "agents": ["Architect", "Examiner", "Tutor"],
        "cache": "enabled" if redis_status == "connected" else "disabled"
    }


@app.get("/api/test")
async def test_endpoint():
    """简单的测试端点"""
    import time
    start = time.time()
    return {
        "message": "API is working!",
        "timestamp": start,
        "server": "EduGenius Backend"
    }


@app.get("/api/test-db")
async def test_db_endpoint():
    """测试数据库连接"""
    from app.db.database import get_db
    from app.models.document import Question
    from sqlalchemy import select

    async for db in get_db():
        result = await db.execute(
            select(Question).where(
                Question.document_id == 3,
                Question.chapter_number == 1
            ).limit(1)
        )
        q = result.scalar_one_or_none()
        return {
            "db_connected": True,
            "found_question": q.question_text if q else None
        }
    return {"db_connected": False}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
