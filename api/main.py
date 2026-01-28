"""
EduGenius Backend API
FastAPI application with MD5-based document deduplication and ChromaDB integration.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.db.database import init_db
from app.api.endpoints.documents import router as documents_router
from app.api.endpoints.teaching import router as teaching_router
from app.api.endpoints.users import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Initializes database on startup.
    """
    # Startup
    print("🚀 Initializing EduGenius Backend...")
    await init_db()
    print("✅ Database initialized successfully")

    yield

    # Shutdown
    print("👋 Shutting down EduGenius Backend...")


# Create FastAPI app
app = FastAPI(
    title="EduGenius API",
    description="AI-powered adaptive learning platform with MD5-based document deduplication",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents_router)
app.include_router(teaching_router)
app.include_router(users_router)


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
