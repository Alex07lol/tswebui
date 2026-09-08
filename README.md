# OCR Platform (`tswebui`)

A modular, configurable OCR extraction platform built on Tesseract.

## Core Principles

- **Configuration over code** — extraction behaviour is represented as versioned, declarative configuration; no code changes required to change extracted fields.
- **Provider-based OCR** — Tesseract is the default provider, but OCR engines are decoupled through standard provider interfaces (`OCRProvider`).
- **Example-based pattern learning** — learns templates, stable labels, variable values, and extraction rules from sample documents.
- **Explainable evidence** — every extracted value preserves raw/normalized values, bounding box coordinates, and confidence scores.

## Architecture

```
ocr-platform/
├── backend/                  Python FastAPI backend
│   ├── app/
│   │   ├── api/              REST endpoints (/api/health, etc.)
│   │   ├── core/             Config, database, logging, security
│   │   ├── models/           SQLAlchemy ORM models (full domain)
│   │   ├── providers/        OCR, Storage, and Queue protocols
│   │   ├── schemas/          Pydantic v2 configuration schemas
│   │   ├── services/         TesseractProvider & extraction logic
│   │   └── main.py           FastAPI entrypoint
│   ├── alembic/              Database migrations
│   └── tests/                Pytest test suite
├── docker/                   Dockerfiles for backend and workers
├── scripts/                  Install, dev, migrate, and tesseract scripts
├── conductor/                Conductor tracks & specifications
└── docker-compose.yml        Multi-service orchestration
```

## Quick Start

### 1. Environment Setup

```bash
cp backend/.env.example backend/.env
```

### 2. Run with Docker

```bash
docker compose up
```

### 3. Local Development

```bash
bash scripts/dev.sh
```

## Implementation Phases

- [x] **Phase 0 — Foundation** (domain models, configuration schema, provider protocols, database, health API)
- [ ] **Phase 1 — OCR MVP** (Tesseract engine, document upload, bounding boxes, word confidence)
- [ ] **Phase 2 — Configurable Extraction** (anchors, patterns, normalization, validation)
- [ ] **Phase 3 — Visual Rule Builder & Playground**
- [ ] **Phase 4 — Advanced Extraction** (multi-line, regions, relative positions)
- [ ] **Phase 5 — Dataset Pattern Learning** (fingerprinting, clustering, rule proposals)
- [ ] **Phase 6 — Learning Review UI**
- [ ] **Phase 7 — Production Hardening** (RBAC, audit logging, safe regex execution)
