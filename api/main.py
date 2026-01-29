"""
EduGenius Backend API
FastAPI application with MD5-based document deduplication and ChromaDB integration.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.db.database import init_db
from app.api.endpoints.documents import router as documents_router
from app.api.endpoints.teaching import router as teaching_router
from app.api.endpoints.users import router as users_router
from app.api.endpoints.quiz import router as quiz_router
from app.api.endpoints.mistakes import router as mistakes_router
from app.core.errors import register_exception_handlers
from app.core.logging_config import setup_logging, get_logger

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
    
    # 启动 Session 清理任务
    from app.api.endpoints.teaching import start_session_cleanup_task
    cleanup_task = start_session_cleanup_task()
    logger.info("✅ Session cleanup task started")

    yield

    # Shutdown
    logger.info("👋 Shutting down EduGenius Backend...")
    
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
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
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
app.include_router(mistakes_router)


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
            "health": "/health"
        },
        "features": {
            "md5_deduplication": "文档 MD5 去重",
            "multi_agent_teaching": "多智能体教学系统",
            "adaptive_levels": "L1-L5 自适应等级",
            "sse_streaming": "SSE 流式输出"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "EduGenius Backend",
        "database": "connected",
        "chroma_db": "initialized",
        "langgraph": "ready",
        "agents": ["Architect", "Examiner", "Tutor"]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
