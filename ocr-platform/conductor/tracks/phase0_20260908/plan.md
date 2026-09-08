# Implementation Plan: Phase 0 — Foundation

**Track ID:** phase0_20260908
**Spec:** [spec.md](./spec.md)
**Created:** 2026-09-08
**Status:** [x] Complete

## Overview

Build the complete project foundation: backend core (config, DB, logging, security), all ORM domain models, provider interfaces + implementations, Pydantic configuration schema, FastAPI app with health endpoint, Alembic setup, Docker files, and scripts. (UI design deferred to subsequent phases as requested).

---

## Phase 1: Project Structure & Backend Core

- [x] Task 1.1: Create all backend directory structure
- [x] Task 1.2: Write `pyproject.toml` with all dependencies
- [x] Task 1.3: Write `app/core/config.py` (Settings with pydantic-settings)
- [x] Task 1.4: Write `app/core/logging.py` (structlog setup with stdlib fallback)
- [x] Task 1.5: Write `app/core/database.py` (async engine, session, Base)
- [x] Task 1.6: Write `app/core/security.py` (JWT + bcrypt utilities)

---

## Phase 2: Domain Models (ORM)

- [x] Task 2.1: Write `app/models/base.py` (UUID PK + timestamp mixins)
- [x] Task 2.2: Write `app/models/user.py`
- [x] Task 2.3: Write `app/models/document.py` + `DocumentPage`
- [x] Task 2.4: Write `app/models/ocr.py` (OCRJob, OCRResult, OCRPage, OCRWord)
- [x] Task 2.5: Write `app/models/configuration.py` (Configuration, ConfigurationVersion, ExtractionField, ExtractionRule)
- [x] Task 2.6: Write `app/models/dataset.py` + `DatasetDocument`
- [x] Task 2.7: Write `app/models/discovery.py` (DiscoveryRun, DocumentCluster, PatternProposal)
- [x] Task 2.8: Write `app/models/extraction.py` (ExtractionJob, ExtractionResult, ExtractedValue, ExtractionEvidence)
- [x] Task 2.9: Write `app/models/test.py` (TestSuite, TestCase, TestRun)
- [x] Task 2.10: Write `app/models/audit.py` (AuditLog)
- [x] Task 2.11: Write `app/models/__init__.py` (import and export all models)

---

## Phase 3: Provider Interfaces & Implementations

- [x] Task 3.1: Write `app/providers/ocr/base.py` (OCRProvider Protocol + data contracts)
- [x] Task 3.2: Write `app/providers/ocr/registry.py` (provider registry)
- [x] Task 3.3: Write `app/providers/storage/base.py` (StorageProvider Protocol)
- [x] Task 3.4: Write `app/providers/storage/local.py` (LocalStorageProvider)
- [x] Task 3.5: Write `app/providers/queue/base.py` (QueueProvider Protocol)
- [x] Task 3.6: Write `app/providers/queue/inline.py` (InlineQueueProvider)
- [x] Task 3.7: Write `app/services/ocr/tesseract.py` (TesseractProvider stub)

---

## Phase 4: Configuration Schema (Pydantic)

- [x] Task 4.1: Write `app/schemas/configuration.py` with all enums, sub-schemas, and root ConfigurationSchema
- [x] Task 4.2: Write tests for schema validation (valid config, invalid strategy/field ID)

---

## Phase 5: FastAPI App, Health API & Alembic

- [x] Task 5.1: Write `app/api/health.py`
- [x] Task 5.2: Write `app/main.py` (lifespan, CORS, router registration, provider registration)
- [x] Task 5.3: Write `alembic.ini` and `alembic/env.py`
- [x] Task 5.4: Write `alembic/script.py.mako` template
- [x] Task 5.5: Create `alembic/versions/.gitkeep`
- [x] Task 5.6: Write `.env.example`

---

## Phase 6: Docker, Scripts & Root Files

- [x] Task 6.1: Write `docker-compose.yml`
- [x] Task 6.2: Write `docker/Dockerfile.backend`, `Dockerfile.worker`
- [x] Task 6.3: Write `scripts/install.sh`, `scripts/dev.sh`, `scripts/migrate.sh`, `scripts/setup-tesseract.sh`
- [x] Task 6.4: Write root `README.md` and `.gitignore`

---

## Verification Summary

- [x] Provider protocols (OCR, Storage, Queue) tested and verified
- [x] TesseractProvider implements OCRProvider Protocol
- [x] LocalStorageProvider and InlineQueueProvider tested
- [x] All 20 domain models defined with UUID PKs and timestamps
- [x] Configuration schema defined with all required strategies and validation
- [x] Docker and deployment configurations created
