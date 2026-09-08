# Tech Stack — OCR Platform

## Languages

| Language | Version | Role |
|----------|---------|------|
| Python | 3.11+ | Backend API, workers, OCR services |
| TypeScript | 5.x | Frontend UI |

## Frontend

| Library | Version | Purpose |
|---------|---------|---------|
| React | 18.x | UI framework |
| Vite | 5.x | Build tool / dev server |
| TanStack Query | 5.x | Server state management |
| Tailwind CSS | 3.x | Utility-first styling |
| React Router | 6.x | Client-side routing |
| Monaco Editor | latest | YAML/rule editing (Phase 2+) |

## Backend

| Library | Version | Purpose |
|---------|---------|---------|
| FastAPI | 0.115+ | Async REST API |
| Pydantic v2 | 2.x | Schema validation |
| SQLAlchemy | 2.x | Async ORM |
| Alembic | 1.x | Database migrations |
| structlog | 24.x | Structured logging |
| python-jose | 3.x | JWT authentication |
| passlib | 1.x | Password hashing |

## OCR & Image Processing

| Library | Purpose |
|---------|---------|
| Tesseract OCR | Default OCR engine |
| pytesseract | Python bindings for Tesseract |
| Pillow | Image loading/manipulation |
| OpenCV (headless) | Preprocessing pipeline |
| pdf2image | PDF → image conversion |

## Database

| Technology | Environment | Notes |
|------------|------------|-------|
| SQLite (aiosqlite) | Development / testing | Zero-config default |
| PostgreSQL 16 | Production | Via asyncpg |

## Queue / Jobs

| Technology | Environment |
|------------|------------|
| Inline (synchronous) | Development / testing |
| Celery + Redis | Production |

## Storage

| Backend | Environment |
|---------|------------|
| Local filesystem | Development / MVP |
| S3-compatible | Production |

## Infrastructure

| Tool | Purpose |
|------|---------|
| Docker | Container runtime |
| Docker Compose | Local multi-service orchestration |

## Key Architectural Constraints

- OCR must be provider-based — `TesseractProvider` must be swappable without touching extraction logic.
- Extraction behaviour must be configuration-driven (declarative YAML/JSON).
- Pattern learning generates the same configuration schema used by manual rules.
- Every extraction result must preserve full evidence (OCR confidence, bounding box, rule, anchor).
