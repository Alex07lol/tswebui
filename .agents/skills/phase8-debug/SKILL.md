---
name: phase8-debug
description: "Debugging runbook for Phase 8 Advanced Intelligence features: corrections API, AI suggestions, multi-provider OCR, and training pipeline. Use when Phase 8 endpoints return unexpected results or tests fail."
---

# Phase 8 Debugging Runbook

## Corrections Subsystem

### Symptoms
- `POST /api/corrections` returns 422 — missing required fields `document_id`, `field_name`, `corrected_value`
- Confidence delta is 0 — no previous corrections recorded for that field_name
- Anchor aliases are empty — `ocr_tokens` list was not passed or too short

### Debugging Steps
1. Check singleton state: `GET /api/corrections/fields` — lists all fields with corrections
2. Check field insight: `GET /api/corrections/{field_name}/insight`
3. Restart server resets in-memory state — corrections are not persisted across restarts

### Fix
Pass complete `ocr_tokens` list from the OCR result words when submitting a correction.

---

## AI Suggestions Subsystem

### Symptoms
- Empty suggestions for invoice-like text — check if any UPPER-CASE text is present (SWIFT pattern needs it)
- Lowercase-only text returns no alias matches — expected: alias matching is case-insensitive, but SWIFT pattern matches require uppercase letters
- `confidence` values seem low — confidence is capped at 1.0, alias length drives it

### Debugging Steps
1. Test directly: `POST /api/intelligence/suggest-rules` with `{"ocr_text": "Invoice Total $100", "top_k": 5}`
2. Check `app/services/intelligence/suggestions.py` `FIELD_CATALOGUE` for alias coverage
3. Add a new alias to the catalogue if a common label is missing

---

## Mock Vision Provider

### Symptoms
- `provider_id` in result is `"mock_vision"` but extraction used Tesseract — check that the UI correctly passes `provider_id` in the OCR job request
- `is_available()` always returns True — this is intentional (mock is always ready)

### Checking Provider Registry
```python
from app.providers.ocr.registry import list_providers
print(list_providers())  # Should include both "tesseract" and "mock_vision"
```

---

## Training Pipeline

### Symptoms
- CER/WER returns 0.0 for clearly different strings — check if both strings are empty (empty/empty = 0)
- WER seems off — word tokenization splits on whitespace; punctuation attached to words counts as part of the token

### Quick Test
```bash
curl -X POST http://localhost:8000/api/training/evaluate \
  -H "Content-Type: application/json" \
  -d '{"predicted_text": "helo world", "ground_truth_text": "hello world"}'
# Expected: cer > 0, wer = 0 (same word count, same structure)
```

---

## Running Tests
```bash
cd ocr-platform/backend
python3 -m pytest tests/test_phase8.py -v
```

All 22 Phase 8 tests should pass. If any fail:
1. Check for import errors (usually a missing `__init__.py`)
2. Check for `noexec` errors (use `tmp_path` fixture, not `/tmp`)
3. Check `ASGITransport` usage — ensure `from httpx import ASGITransport`
