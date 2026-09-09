---
name: ocr-platform-workflow
description: "Step-by-step runbook for developing, testing, and deploying a feature on the OCR Platform (tswebui). Use when adding a new API endpoint, service, or UI view."
---

# OCR Platform Feature Development Workflow

## Prerequisites

- Backend running: `uvicorn app.main:app --reload` from `ocr-platform/backend/`
- Frontend dev server: `npm run dev` from `ocr-platform/frontend/`
- Activated venv: `source .venv/bin/activate` from `ocr-platform/backend/`

---

## Step 1 — Plan

Before writing code:
1. Identify the **service layer** file: `app/services/{domain}/{name}.py`
2. Identify the **API handler** file: `app/api/{name}.py`
3. Identify the **test file**: `tests/test_{name}.py`
4. Confirm the feature aligns with `conductor/product.md` goals

---

## Step 2 — Service Layer First

```python
# app/services/{domain}/{name}.py
from __future__ import annotations
from app.core.logging import get_logger
log = get_logger(__name__)

# Pure logic, no FastAPI dependencies
# Testable in isolation
```

Rules:
- No `Request`, `Response`, or `Depends` imports in service files
- Return plain Python dataclasses or Pydantic models
- Log key decisions with `log.info(...)` / `log.warning(...)`

---

## Step 3 — API Handler

```python
# app/api/{name}.py
from __future__ import annotations
from fastapi import APIRouter
from pydantic import BaseModel
from app.services.{domain}.{name} import ...

router = APIRouter()

class {Name}Request(BaseModel): ...
class {Name}Response(BaseModel): ...

@router.post("/{route}", response_model={Name}Response)
async def handler(body: {Name}Request) -> {Name}Response:
    result = service_function(body.field)
    return {Name}Response(...)
```

---

## Step 4 — Register Router

In `app/main.py`, inside `create_app()`:

```python
from app.api import {name}
app.include_router({name}.router, prefix="/api", tags=["{name}"])
```

---

## Step 5 — Write Tests

```python
# tests/test_{name}.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_{feature}_happy_path():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/api/{route}", json={...})
    assert resp.status_code == 200
    data = resp.json()
    assert data["key"] == expected_value
```

Run: `python -m pytest tests/test_{name}.py -v`

---

## Step 6 — Frontend Integration

1. Add API call using native `fetch` (no axios)
2. Follow motion.dev spring animation pattern for new UI elements
3. Use BKLit components for metrics / charts
4. Respect zero-glassmorphism palette

---

## Step 7 — Build & Verify

```bash
# Backend tests
cd ocr-platform/backend
python -m pytest tests/ -v --tb=short

# Frontend build
cd ocr-platform/frontend
npm run build
```

---

## Step 8 — Commit & Push

```bash
git add -A
git commit -m "feat: {short description}"
git push origin main
```

---

## Common Pitfalls

| Issue | Fix |
|-------|-----|
| `noexec` error on `/storage/emulated/0/` | Move binaries to `~/bin/` |
| `structlog.stdlib.add_logger_name` crash | Remove it; use `PrintLoggerFactory` only |
| esbuild import error | Use `build.target: 'esnext'` in vite.config |
| `asyncio_mode` not found | Add `asyncio_mode = "auto"` in `pyproject.toml` |
