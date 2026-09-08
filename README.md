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

- [x] **Phase 0 — Foundation** (Domain models, Pydantic configuration schemas, provider protocols, database setup, health API)
- [x] **Phase 1 — OCR Pipeline** (Tesseract engine, document upload, PIL preprocessing, bounding boxes, word confidence, composite caching)
- [x] **Phase 2 — Extraction Engine** (Anchors [exact, fuzzy, regex], template & typed pattern compiler, sequential normalization, declarative validation, explainable confidence engine)
- [x] **Phase 3 — Configuration & Versioning** (Configuration CRUD, semantic version lifecycle: draft -> tested -> review -> published -> active -> deprecated, live rule testing API)
- [x] **Phase 4 — Advanced Extraction & Tabular Data** (Multi-line, region extraction, structured table & line-item detector with column alignments)
- [x] **Phase 5 — Dataset Pattern Learning** (Document visual fingerprinting, structural clustering, stable label detection, variable value alignment, configuration proposal learner)
- [x] **Phase 6 — Automated Regression Testing Suite** (Test suites, test cases, exact/regex/tolerance/date validation modes, execution runner with diffing and pass-rate calculation)
- [x] **Phase 7 — Production Hardening & Export** (JWT Authentication & RBAC, immutable audit logging, ReDoS-safe regex engine, CSV & JSON export subsystem)

## API Reference

### Health & System
- `GET /api/health` — System status, database health, provider availability.

### Documents & OCR
- `POST /api/documents` — Ingest document (PNG, JPG, PDF) with SHA256 deduplication and page splitting.
- `GET /api/documents` — List uploaded documents.
- `GET /api/documents/{id}` — Retrieve document metadata and page images.
- `DELETE /api/documents/{id}` — Delete document and page storage.
- `POST /api/ocr/jobs` — Enqueue or run OCR job with preprocessing and caching.
- `GET /api/ocr/jobs/{id}` — Check status of an OCR job.
- `GET /api/ocr/results/{doc_id}` — Word-level bounding boxes, text, and confidence scores.

### Configurations & Extraction Rules
- `POST /api/configurations` — Create new configuration or draft version.
- `GET /api/configurations` — List all configurations with current version status.
- `GET /api/configurations/{id}` — Retrieve configuration details and version history.
- `POST /api/configurations/{id}/publish` — Publish a draft configuration version.
- `POST /api/configurations/test/live` — Test rules on a document without persisting.

### Extraction Jobs & Results
- `POST /api/extraction/jobs` — Run persistent extraction using a configuration version.
- `GET /api/extraction/jobs/{id}` — Retrieve extraction job status.
- `GET /api/extraction/results/{id}` — Extraction result with field values and full evidence traces.
- `GET /api/results/{id}` — Full result details.
- `GET /api/results/document/{doc_id}` — Latest extraction result for document.
- `GET /api/results/{id}/export?format=json|csv` — Download result as JSON or CSV.
- `POST /api/results/batch-export` — Export multiple extraction results.

### Pattern Learning & Discovery
- `POST /api/datasets` — Create document training dataset.
- `POST /api/datasets/{id}/documents` — Add documents to training dataset.
- `POST /api/datasets/{id}/discovery` — Run automated fingerprinting, clustering, and rule proposals.
- `GET /api/discovery/{run_id}` — Inspect discovered clusters and candidate extraction proposals.
- `POST /api/discovery/proposals/{id}/accept` — Accept proposal into an extraction configuration.

### Regression Testing Suite
- `POST /api/tests/suites` — Create test suite for a configuration.
- `GET /api/tests/suites` — List test suites.
- `POST /api/tests/suites/{id}/cases` — Add test case / save regression test.
- `POST /api/tests/suites/{id}/run` — Execute test suite with expected vs actual diffing.
- `GET /api/tests/suites/{id}/runs` — Test run history and regression metrics.

### Authentication, RBAC & Audit
- `POST /api/auth/register` — Register user account.
- `POST /api/auth/login` — Authenticate and receive JWT access token.
- `GET /api/auth/me` — Current user profile.
- `GET /api/audit-logs` — Immutable audit trail of system events.
