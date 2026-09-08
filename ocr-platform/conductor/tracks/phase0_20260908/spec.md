# Specification: Phase 0 — Foundation

**Track ID:** phase0_20260908
**Type:** Feature
**Created:** 2026-09-08
**Status:** In Progress

## Summary

Build the complete project foundation for the OCR Platform: directory structure, domain models, provider interfaces, database setup, authentication primitives, logging, configuration schema, and Docker/scripts scaffolding.

## Context

This is the mandatory first phase before any OCR or extraction work can begin. The configuration model and provider contracts established here are the foundation that all subsequent phases depend on. From `instructions.md` §53: "Do not build pattern learning before the extraction configuration model is stable."

## Acceptance Criteria

- [ ] Project starts (`uvicorn app.main:app` runs without error)
- [ ] Database migrates cleanly (Alembic `upgrade head` succeeds on SQLite)
- [ ] Frontend dev server connects and shows the dashboard
- [ ] All provider interfaces (OCRProvider, StorageProvider, QueueProvider) exist as typed Protocols
- [ ] TesseractProvider stub satisfies the OCRProvider Protocol
- [ ] Configuration schema validates a valid YAML config document
- [ ] Configuration schema rejects invalid configs with clear errors
- [ ] `/api/health` returns 200 with provider list
- [ ] All backend tests pass (`pytest -v`)

## Out of Scope

- Actual OCR processing (Phase 1)
- File upload endpoints (Phase 1)
- Extraction engine (Phase 2)
- Pattern learning (Phase 5)
- Authentication login flow / JWT endpoints (Phase 7)

## Technical Notes

- SQLite + aiosqlite for dev; PostgreSQL + asyncpg for production
- Inline queue provider for dev; Celery for production
- Alembic autogenerate from SQLAlchemy models
- All models use UUID primary keys and timestamp mixins
