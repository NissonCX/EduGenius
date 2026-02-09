# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EduGenius is an AI-powered adaptive education platform that uses a multi-agent system (LangGraph) to provide personalized learning experiences. The system features adaptive difficulty levels (L1-L5), real-time streaming AI responses, and comprehensive progress tracking.

**Tech Stack:**
- **Frontend**: Next.js 16 with App Router, TypeScript 5, React 19, TailwindCSS 4
- **Backend**: FastAPI with Python 3.10+, SQLAlchemy 2 (async), Redis caching
- **AI**: LangGraph 0.2 multi-agent system, DashScope (通义千问) LLM, ChromaDB vector embeddings
- **Document Processing**: PaddleOCR for PDF text extraction, PyMuPDF, python-docx, python-pptx

## Quick Start

```bash
# One-command setup (installs dependencies, initializes DB, starts both services)
./start-dev.sh

# Stop all services
./stop-dev.sh
```

## Development Commands

### Frontend (Next.js)
```bash
npm run dev          # Start development server (localhost:3000)
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
```

### Backend (FastAPI)
```bash
cd api
python main.py              # Run backend directly
uvicorn main:app --reload   # Run with auto-reload
```

### Database
```bash
cd api
python3 init_db.py          # Initialize database
python3 migrations/add_*.py # Run specific migrations
```

## Architecture

### Multi-Agent Teaching System

The core AI teaching system uses LangGraph workflows with three specialized agents:

1. **Architect** (`api/app/agents/nodes/architect.py`): Analyzes content and designs learning paths
2. **Examiner** (`api/app/agents/nodes/examiner.py`): Generates and evaluates quiz questions
3. **Tutor** (`api/app/agents/nodes/tutor.py`): Provides explanations, hints, and summaries

The workflow graph (`api/app/agents/graphs/teaching_graph.py`) orchestrates these agents with:
- State management through `TeachingState` (`api/app/agents/state/teaching_state.py`)
- Adaptive level adjustment (L1-L5) based on performance
- SSE streaming for real-time responses
- Session management with automatic cleanup

### API Structure (`api/app/api/endpoints/`)

- `documents.py` - Document upload and processing (PDF, Word, PowerPoint)
- `teaching.py` - AI teaching sessions with SSE streaming
- `users.py` - Authentication (JWT), registration, password reset
- `quiz.py` - Quiz CRUD and management
- `quiz_ai.py` - AI-generated quiz questions
- `mistakes.py` - Error collection and review
- `knowledge.py` - Knowledge graph endpoints

### Frontend Structure (`src/`)

- `app/` - Next.js App Router pages (dashboard, study, quiz, mistakes, upload, documents)
- `components/` - React components organized by feature
- `lib/` - Utilities (API client with auto-refresh, config, cache, LaTeX processor)
- `types/` - TypeScript type definitions

### Key Patterns

**API Authentication**: The frontend uses `fetchWithAuth` (`src/lib/api-client.ts`) which automatically:
- Attaches JWT tokens to requests
- Detects 401 errors and refreshes tokens
- Queues concurrent requests during token refresh
- Redirects to login on auth failure

**Document Processing Pipeline**:
1. Upload via `documents.py` endpoint
2. MD5 hash calculation for deduplication
3. OCR text extraction (PaddleOCR) if needed
4. Chapter/subsection extraction
5. Content stored in SQLite, embeddings in ChromaDB

**Adaptive Learning Levels** (`api/app/agents/state/level_prompts.py`):
- L1 (Gentle) → L5 (Strict) teaching styles
- Automatic adjustment based on quiz performance
- Custom prompts for each level

## Configuration

**Backend** (`api/.env`):
```bash
DASHSCOPE_API_KEY=your_dashscope_key  # Required - Primary LLM
JWT_SECRET_KEY=your_jwt_secret        # Required
DATABASE_URL=sqlite+aiosqlite:///./edugenius.db
REDIS_HOST=localhost
REDIS_PORT=6379
CHROMA_PERSIST_DIR=./chroma_db
```

**Frontend** (`.env.local`):
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Python Config** (`api/app/core/config.py`): Centralized settings management with validation.

## Important Notes

- **SSE Streaming**: Teaching sessions use Server-Sent Events for real-time AI responses. The `TeachingStreamHandler` class manages this.
- **Session Management**: Active sessions are tracked in-memory and cleaned up after timeout.
- **Redis Caching**: Used for performance optimization; gracefully degrades if Redis is unavailable.
- **OCR Semaphore**: Limits concurrent OCR operations to prevent resource exhaustion (`api/app/core/ocr_semaphore.py`).
- **Type Safety**: Frontend uses strict TypeScript; backend uses Pydantic for validation.

## Common Work

When modifying the teaching system:
1. Agent logic is in `api/app/agents/nodes/`
2. State definitions are in `api/app/agents/state/teaching_state.py`
3. Workflow changes go in `api/app/agents/graphs/teaching_graph.py`
4. Frontend teaching UI is in `src/app/study/` and `src/app/learn/`

When adding new API endpoints:
1. Create endpoint file in `api/app/api/endpoints/`
2. Register router in `api/main.py`
3. Add TypeScript types in `src/types/`
4. Use `fetchWithAuth` for authenticated requests

## Testing

- Backend tests can be run from `api/` directory
- Frontend tests are in `src/lib/__tests__/`
- Use `api/run_upload_test.sh` to test document upload
