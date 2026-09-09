# Phase 8 — Advanced Intelligence Rules

trigger: model_decision

## When to apply

Apply these rules when working on Phase 8 features:
- Active learning / corrections subsystem
- AI-assisted rule and field suggestions
- Multi-OCR provider support
- Training pipeline / ground-truth dataset work

---

## Active Learning Rules

- Corrections API is at `POST /api/corrections`
- The `CorrectionEngine` singleton lives at `app/services/learning/corrections.py`
- Corrections are in-memory by default; the API layer can persist to DB if needed
- `CorrectionInsight.confidence_delta` is bounded: `0.0 ≤ delta ≤ 0.5`
- Anchor alias inference: look up to 3 tokens BEFORE the corrected value

## AI Suggestion Rules

- The suggestion engine at `app/services/intelligence/suggestions.py` is heuristic-only
- No external LLM calls — pattern matching and alias lookup only
- `POST /api/intelligence/suggest-rules` accepts `{ocr_text, top_k}`
- Confidence is in range `0.0 – 1.0` (never display raw floats; format as `{n}%`)

## Multi-Provider Rules

- All providers implement `OCRProvider` from `app/providers/ocr/base.py`
- Register new providers via `register_provider()` in `app/providers/ocr/registry.py`
- `MockVisionProvider` (`provider_id = "mock_vision"`) is the demo second engine
- UI must show provider name in result header, not internal ID

## Training Pipeline Rules

- Training subsystem at `app/services/ocr/training.py` is additive — never modifies OCR output
- `evaluate_ocr(predicted, ground_truth)` is the only public evaluation function
- CER and WER are expressed as floats 0.0–1.0 internally; display as percentages in UI
- Ground-truth files follow Tesseract convention: `{stem}.gt.txt` alongside image
