# Product Guidelines — OCR Platform

## Voice and Tone

**Professional and precise.** UI text should be clear, technical where necessary, and never ambiguous. Avoid jargon where a plain term works equally well.

## Design Principles

1. **Configuration over code** — users should never need to touch source code to change extraction behaviour.
2. **Transparency over magic** — every result must be explainable; confidence scores must show their components.
3. **Non-destructive by default** — never silently discard data; outliers are visible, not hidden.
4. **Progressive complexity** — simple tasks should be simple; advanced features shouldn't block basic use.
5. **Provider agnosticism** — no core logic should depend on Tesseract specifically.

## UI Standards

- Sidebar navigation with clear section labels.
- Status indicators on all async operations (jobs must show progress).
- Evidence panels always available when a value is selected.
- Diff views for configuration version comparisons.

## API Standards

- RESTful resource URLs: `/api/{resource}` and `/api/{resource}/{id}`.
- All async operations return a job record immediately; poll or websocket for progress.
- All responses include evidence/metadata where applicable.
- Error responses: `{ "detail": "...", "code": "..." }`.
