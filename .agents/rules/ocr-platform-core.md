# OCR Platform — Core Agent Rules

trigger: always_on

---

## Project Identity

This is the **OCR Platform** (`ocr-platform`) — a modular, configurable document
extraction platform. Canonical root:

```
/data/data/com.termux/files/home/storage/downloads/tswebui/
```

Sub-directories:
- `ocr-platform/backend/`  — FastAPI + SQLAlchemy async API
- `ocr-platform/frontend/` — React 18 + TypeScript + Vite + Tailwind + motion.dev
- `ocr-platform/conductor/` — Conductor project management artifacts

---

## Architecture Invariants (NEVER violate)

1. **Configuration over code** — extraction behaviour must remain fully
   declarative. No hard-coded field names or patterns inside service code.
2. **Provider-based OCR** — always route through `OCRProvider` in
   `app/providers/ocr/base.py`. Never call `pytesseract` directly.
3. **Evidence preservation** — every `ExtractedValue` must carry its bounding
   box, OCR confidence, matched rule ID, and anchor text.
4. **Async everywhere** — all DB access uses `AsyncSession`. No sync `execute()`.
5. **Pydantic v2** — use `model_config`, `field_validator`. Never v1 `validator`.

---

## Python Backend Conventions

- All files begin with `from __future__ import annotations`
- Logging: `from app.core.logging import get_logger; log = get_logger(__name__)`
- Settings: `from app.core.config import settings`
- DB sessions: `Depends(get_session)` — never instantiate manually
- UUID PKs stored as `str` (not `uuid.UUID` objects)
- `await session.commit()` only in `get_session` dependency, never in services

### New Router Checklist
1. Create `app/api/{name}.py` with `router = APIRouter()`
2. Add `app/services/{name}/` package
3. Register in `app/main.py` → `create_app()`
4. Write `tests/test_{name}.py`

---

## Frontend Conventions

### Zero Glassmorphism Policy
- **Forbidden:** `backdrop-blur`, `backdrop-filter`, `bg-white/10`, `bg-opacity-*`
- **Allowed:** Solid zinc surfaces: `bg-zinc-950`, `bg-zinc-900`, `bg-zinc-50`

### Colour Palette
| Purpose            | Class                      |
|--------------------|----------------------------|
| Page background    | `bg-zinc-950`              |
| Card / panel       | `bg-zinc-900`              |
| Raised element     | `bg-zinc-800`              |
| Border dark mode   | `border-zinc-800`          |
| Primary text       | `text-white`               |
| Muted text         | `text-zinc-400`            |
| Accent             | `text-white bg-zinc-700`   |
| Destructive        | `text-red-400`             |
| Success            | `text-emerald-400`         |

### Typography
- UI: **Plus Jakarta Sans** (`font-sans`)
- Code/values: **JetBrains Mono** (`font-mono`)

### Motion Rules
- `import { motion, AnimatePresence } from 'motion/react'`
- Spring: `{ type: "spring", stiffness: 400, damping: 30 }`
- Fade-in: `initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}`
- Slide-in: `initial={{ x: "100%" }} animate={{ x: 0 }}`
- Wrap conditionals in `<AnimatePresence mode="wait">`

### Component Rules
- BKLit components in `frontend/src/components/BKLit*.tsx`
- Use `BKLitMetricCard` for KPI tiles
- Use `BKLitSparkline`/`BKLitAreaChart` for time-series data
- No third-party UI libraries beyond listed deps

---

## Testing Rules

- `python -m pytest tests/ -v --tb=short` from `ocr-platform/backend/`
- All new services need `tests/test_{service}.py`
- Use `httpx.AsyncClient(app=app, base_url="http://test")` for API tests
- Never commit with failing tests

---

## Git Discipline

- Conventional commits: `feat:`, `fix:`, `test:`, `refactor:`, `chore:`
- One logical unit per commit
- Always push to `origin main` after each phase
- Remote: `https://github.com/Alex07lol/tswebui.git`

---

## Termux Constraints

- `/storage/emulated/0/` is `noexec` — no native `.so` execution from there
- Use `python -m pytest` (not bare `pytest`)
- Use `npm run build` from `ocr-platform/frontend/`
- esbuild-wasm is bundler fallback; `build.target: 'esnext'` in vite.config
