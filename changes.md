# UX Refactor Plan — tswebui OCR Platform
**Status:** PLAN ONLY — not yet implemented  
**Target:** Consumer-first UX layer over the existing declarative OCR extraction architecture  
**Principle:** Simple users interact with Setups and Fields. Power users keep full access to every existing engine feature.

---

## Table of Contents

1. [Goals & Non-Goals](#1-goals--non-goals)
2. [Architecture Overview — What Changes, What Stays](#2-architecture-overview--what-changes-what-stays)
3. [Backend Changes](#3-backend-changes)
   - 3.1 New: Human Pattern Language Parser
   - 3.2 New: Automatic Extraction Strategy Generator
   - 3.3 New: Setup API (thin adapter over Configuration)
   - 3.4 New: Setups → Fields API (adapter over ExtractionField)
   - 3.5 New: Ambiguity Resolution API
   - 3.6 New: OCR Error Tolerance Layer
   - 3.7 New: Output Type Inference
   - 3.8 New: Teach From Examples one-step API
   - 3.9 Unchanged Backend Modules
4. [Frontend Changes](#4-frontend-changes)
   - 4.1 Navigation Restructure
   - 4.2 Home Screen
   - 4.3 Create Setup Flow
   - 4.4 Field Card (Simple Mode)
   - 4.5 Scan Documents View
   - 4.6 Results View (Consumer)
   - 4.7 Teach From Examples (renamed PatternTrainer)
   - 4.8 My Setups View
   - 4.9 Advanced Tools Section
   - 4.10 Confidence Display
   - 4.11 Ambiguity Resolution UI
   - 4.12 Human Correction Loop UI
5. [New Files — Backend](#5-new-files--backend)
6. [New Files — Frontend](#6-new-files--frontend)
7. [Modified Files — Backend](#7-modified-files--backend)
8. [Modified Files — Frontend](#8-modified-files--frontend)
9. [Deleted / Retired Files](#9-deleted--retired-files)
10. [Terminology Mapping](#10-terminology-mapping)
11. [Test Plan](#11-test-plan)
12. [Implementation Phases](#12-implementation-phases)
13. [API Contract Reference](#13-api-contract-reference)

---

## 1. Goals & Non-Goals

### Goals
- Replace the engineering-dashboard home with a "What would you like to do?" screen.
- Introduce **Setup** as the primary user-facing concept (maps to `Configuration`).
- Introduce **Field** as the primary sub-concept (maps to `ExtractionField`).
- Provide a beginner-friendly pattern input system (human pattern language, examples, selected text, plain language).
- Automate extraction strategy selection — users never choose `same_line` / `anchored_pattern` manually.
- Rename UI surfaces to plain language per the terminology map.
- Move all technical surfaces to **Advanced Tools**.
- Add OCR error tolerance for common confusion characters.
- Add output type inference so users don't pick String/Date/Currency.
- Add user-friendly confidence display (Very High / High / Medium / Low + "Why?").
- Add ambiguity UI when multiple candidates are found.
- Add human correction loop with explicit user confirmation before changing production configs.

### Non-Goals
- Do NOT rewrite the backend OCR engine.
- Do NOT remove or break any existing API route (only add new ones).
- Do NOT change `TesseractProvider`, extraction engine, pattern learning, or regression runner.
- Do NOT alter existing database models.
- Do NOT remove Advanced Rule Editor or any advanced view.
- Do NOT change audit logging.

---

## 2. Architecture Overview — What Changes, What Stays

```
┌─────────────────────────────────────────────────┐
│                  FRONTEND LAYER                  │
│                                                  │
│  Consumer Views        Advanced Tools            │
│  ─────────────         ──────────────            │
│  Home                  OCR Inspector             │
│  Scan Documents        Advanced Rule Editor      │
│  Teach From Examples   Pattern Analysis          │
│  My Setups             Test & Regression         │
│  Results               Activity & System         │
└──────────────┬──────────────────────────────────┘
               │ HTTP (unchanged routes preserved)
               │ New: /api/setups  /api/fields
               │      /api/pattern-parser
               │      /api/auto-strategy
               │      /api/teach
┌──────────────▼──────────────────────────────────┐
│            ADAPTER LAYER (new backend)           │
│                                                  │
│  SetupService           PatternParser            │
│  FieldService           AutoStrategyGenerator    │
│  TeachService           AmbiguityResolver        │
│  OutputTypeInferrer     OCRToleranceMatcher      │
└──────────────┬──────────────────────────────────┘
               │ calls existing services
┌──────────────▼──────────────────────────────────┐
│           EXISTING BACKEND (UNCHANGED)           │
│                                                  │
│  Configuration / ConfigurationVersion            │
│  ExtractionField / ExtractionRule                │
│  Extraction Engine                               │
│  OCR Provider (Tesseract + MockVision)           │
│  Pattern Discovery / Clustering                  │
│  Regression Runner                               │
│  Audit Logger                                    │
│  Normalization / Validation                      │
└─────────────────────────────────────────────────┘
```

**The adapter layer translates between human intent and existing internal models.**  
No existing model, table, or API route is removed.

---

## 3. Backend Changes

### 3.1 New: Human Pattern Language Parser

**File:** `app/services/pattern/human_parser.py`

**Purpose:** Convert human-readable tokens like `SN-{YYYY}-{NNNNNN}` into internal regex patterns.

**Token Mapping:**

| Token | Meaning | Generated Regex |
|-------|---------|----------------|
| `{YYYY}` | 4-digit year | `\d{4}` |
| `{YY}` | 2-digit year | `\d{2}` |
| `{MM}` | Month 01–12 | `(?:0[1-9]\|1[0-2])` |
| `{DD}` | Day 01–31 | `(?:0[1-9]\|[12]\d\|3[01])` |
| `{N}` | Single digit | `\d` |
| `{NN}` | 2 digits | `\d{2}` |
| `{NNN}` | 3 digits | `\d{3}` |
| `{NNNN}` | 4 digits | `\d{4}` |
| `{NNNNN}` | 5 digits | `\d{5}` |
| `{NNNNNN}` | 6 digits | `\d{6}` |
| `{A}` | Single letter | `[A-Za-z]` |
| `{AA}` | 2 letters | `[A-Za-z]{2}` |
| `{AAA}` | 3 letters | `[A-Za-z]{3}` |
| `{AAAA}` | 4 letters | `[A-Za-z]{4}` |
| `{TEXT}` | Any word characters | `[\w\s]+?` |
| `{ANY}` | Any characters | `.+?` |
| `{EMAIL}` | Email address | `[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}` |
| `{PHONE}` | Phone number | `[\+]?[\d\s\-\(\)]{7,15}` |
| `{MONEY}` | Currency amount | `[\$£€₹]?\s?[\d,]+(?:\.\d{2})?` |

**Example:**
- Input: `SN-{YYYY}-{NNNNNN}`
- Output: `SN-\d{4}-\d{6}`

**Additional feature — example learning:**  
Given a list of examples (`SN-2026-001234`, `SN-2026-001235`), infer a pattern by finding the common fixed prefix/suffix and classifying variable segments.

**Additional feature — plain language:**  
Given `"starts with SN, then the year, then six numbers"`, parse key phrases into tokens using a lookup table of common descriptions:
- "year" → `{YYYY}`
- "six numbers" / "6 digits" → `{NNNNNN}`
- "followed by" / "then" → separator preserved

**OCR Tolerance:**  
After compiling the pattern, if safe for the context, optionally generate OCR-tolerant variant:
- `O` → `[O0]`
- `I` / `l` → `[Il1]`
- `S` → `[S5]`
- `B` → `[B8]`

Only applied when the pattern context is non-numeric (e.g., alphanumeric identifiers, not pure numeric amounts).

**API Endpoint:** `POST /api/pattern-parser/compile`  
Request: `{ "human_pattern": "SN-{YYYY}-{NNNNNN}", "ocr_tolerant": true }`  
Response: `{ "regex": "SN-\d{4}-\d{6}", "ocr_tolerant_regex": "SN-\d{4}-\d{6}", "tokens": [...], "example_match": "SN-2026-001234" }`

**API Endpoint:** `POST /api/pattern-parser/from-examples`  
Request: `{ "examples": ["SN-2026-001234", "SN-2026-001235"] }`  
Response: `{ "inferred_human_pattern": "SN-{YYYY}-{NNNNNN}", "regex": "...", "confidence": 0.95 }`

**API Endpoint:** `POST /api/pattern-parser/from-description`  
Request: `{ "description": "Starts with SN, followed by the year, then six numbers" }`  
Response: `{ "inferred_human_pattern": "SN-{YYYY}-{NNNNNN}", "regex": "...", "confidence": 0.8 }`

---

### 3.2 New: Automatic Extraction Strategy Generator

**File:** `app/services/extraction/auto_strategy.py`

**Purpose:** Given a human field definition (name, pattern, examples), automatically generate a complete `ExtractionRule` without requiring the user to choose strategy.

**Algorithm:**

```
Step 1: Scan document OCR tokens for values matching the compiled pattern.

Step 2: If exactly one match → high confidence, use direct_pattern strategy.

Step 3: If multiple matches found:
  a. Inspect tokens within 3 words to the left of each match.
  b. Score tokens as likely label candidates (match known label vocabulary OR contain field_name keywords).
  c. If a label candidate is found consistently → anchored_pattern strategy with inferred anchor.
  d. If no consistent label → record all candidates, trigger ambiguity flow.

Step 4: If zero matches found:
  a. Try OCR-tolerant variant of the pattern.
  b. Try fuzzy matching (edit distance ≤ 2) for fixed portions.
  c. If still zero → report "Not found" with suggestions.

Step 5: If multiple documents are provided, check layout consistency:
  a. If the match appears at a consistent Y-coordinate range → add region constraint.
  b. If the match appears consistently in a table column → table strategy.

Step 6: Return generated ExtractionRule payload ready to be saved via existing /api/configurations endpoint.
```

**Common label vocabulary (built-in):**  
For a field named `serial_number`, auto-seed anchors with common labels:
- `Serial Number`, `Serial No`, `S/N`, `Serial #`, `SN`

For a field named `invoice_number`:
- `Invoice #`, `Invoice No`, `Invoice Number`, `Bill No`

Extend this vocabulary from the existing `app/services/intelligence/suggestions.py` `FIELD_CATALOGUE`.

**API Endpoint:** `POST /api/auto-strategy/generate`  
Request:
```json
{
  "document_ids": ["doc-uuid-1", "doc-uuid-2"],
  "field_name": "serial_number",
  "human_pattern": "SN-{YYYY}-{NNNNNN}",
  "examples": ["SN-2026-001234"],
  "ocr_tolerant": true
}
```
Response:
```json
{
  "generated_rule": { /* ExtractionRule payload */ },
  "strategy_chosen": "anchored_pattern",
  "confidence": 0.92,
  "anchors_found": ["Serial Number", "S/N"],
  "candidates_found": 1,
  "ambiguous": false,
  "explanation": [
    "Found 1 value matching SN-YYYY-NNNNNN",
    "Found label 'Serial Number' consistently 2 words to the left",
    "High confidence — single unambiguous match with label"
  ]
}
```

---

### 3.3 New: Setup API

**File:** `app/api/setups.py`  
**File:** `app/services/setup/setup_service.py`

**Purpose:** Expose a consumer-facing Setup API that internally creates/reads `Configuration` + `ConfigurationVersion`.

**What a Setup is internally:**  
- One `Configuration` record (slug = slugify(setup_name))
- One or more `ConfigurationVersion` records
- Fields are `ExtractionField` records belonging to the latest version

**API Routes:**

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/api/setups` | List all setups (maps to `/api/configurations`) |
| POST | `/api/setups` | Create a setup → creates Configuration + initial version |
| GET | `/api/setups/{setup_id}` | Get setup with fields (joined view model) |
| PUT | `/api/setups/{setup_id}` | Rename setup |
| DELETE | `/api/setups/{setup_id}` | Delete setup (soft delete via config) |
| POST | `/api/setups/{setup_id}/scan` | Upload doc + run extraction using latest version |
| GET | `/api/setups/{setup_id}/results` | Results for this setup |
| GET | `/api/setups/{setup_id}/history` | Version history |

**SetupResponse view model** (frontend-facing):
```json
{
  "id": "config-uuid",
  "name": "Laptop Warranty Documents",
  "slug": "laptop-warranty-documents",
  "description": "",
  "field_count": 4,
  "last_scanned": "2026-09-09T00:00:00Z",
  "created_at": "2026-09-08T00:00:00Z",
  "status": "ready",
  "version_id": "version-uuid"
}
```

**Internally:** `SetupService` delegates to the existing `configurations` API service — no new database tables needed.

---

### 3.4 New: Fields API (Setup context)

**File:** `app/api/setup_fields.py`  
**File:** `app/services/setup/field_service.py`

**Purpose:** Expose beginner-friendly field management that auto-generates `field_id`, `output_variable`, and internal rule from human inputs.

**Auto-generation rules:**
- `display_name` = "Serial Number" (user-provided)
- `field_id` = slugify(display_name) = `serial_number`
- `output_variable` = `serial_number` (same as field_id by default)
- `slug` = `serial-number`

**API Routes:**

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/api/setups/{setup_id}/fields` | List fields in simple view model |
| POST | `/api/setups/{setup_id}/fields` | Add field (auto-generate IDs, call auto-strategy) |
| PUT | `/api/setups/{setup_id}/fields/{field_id}` | Update field display name or pattern |
| DELETE | `/api/setups/{setup_id}/fields/{field_id}` | Remove field |
| GET | `/api/setups/{setup_id}/fields/{field_id}/advanced` | Full ExtractionField + ExtractionRule data for Advanced Editor |

**FieldRequest (simple mode):**
```json
{
  "display_name": "Serial Number",
  "human_pattern": "SN-{YYYY}-{NNNNNN}",
  "examples": ["SN-2026-001234"],
  "description": "optional plain language"
}
```

**FieldResponse (simple mode):**
```json
{
  "field_id": "serial_number",
  "display_name": "Serial Number",
  "human_pattern": "SN-{YYYY}-{NNNNNN}",
  "status": "ready",
  "output_type_inferred": "text",
  "confidence_label": "Very High",
  "confidence_score": 0.95,
  "last_example_found": "SN-2026-004821"
}
```

---

### 3.5 New: Ambiguity Resolution API

**File:** `app/api/ambiguity.py`  
**File:** `app/services/extraction/ambiguity.py`

**Purpose:** When auto-strategy finds multiple equally valid candidates, surface them to the user for resolution rather than guessing.

**API Routes:**

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/api/setups/{setup_id}/fields/{field_id}/candidates?document_id=X` | Return all candidates with context |
| POST | `/api/setups/{setup_id}/fields/{field_id}/resolve` | User selects a candidate; updates rule |

**CandidateResponse:**
```json
{
  "field_id": "serial_number",
  "ambiguous": true,
  "candidates": [
    {
      "id": "candidate-1",
      "value": "SN-2026-001234",
      "context_before": "Serial Number:",
      "context_after": "Product ID: LP-001",
      "confidence": 0.88,
      "page": 1,
      "bounding_box": { "x": 100, "y": 240, "width": 140, "height": 18 }
    },
    {
      "id": "candidate-2",
      "value": "SN-2026-001235",
      "context_before": "Replacement Serial:",
      "context_after": "Warranty Code: WC-999",
      "confidence": 0.61,
      "page": 1,
      "bounding_box": { "x": 100, "y": 480, "width": 140, "height": 18 }
    }
  ]
}
```

---

### 3.6 New: OCR Error Tolerance Layer

**File:** `app/services/pattern/ocr_tolerance.py`

**Purpose:** Augment compiled patterns with character-class alternatives for common OCR confusion pairs, applied selectively.

**Rules (applied only where contextually safe):**

| Confusion pair | Applied when |
|----------------|-------------|
| `O` / `0` | In alphanumeric identifiers (not in pure date/number segments) |
| `I` / `1` / `l` | In alphanumeric identifiers |
| `S` / `5` | In alphanumeric identifiers |
| `B` / `8` | In alphanumeric identifiers |
| `G` / `6` | In alphanumeric identifiers |
| `Z` / `2` | In alphanumeric identifiers |

**Algorithm:**
1. Parse the compiled regex into segments.
2. For each character-class segment containing `[A-Za-z]`:
   - Expand to include confused digits.
3. For each numeric-only segment (`\d{n}`):
   - Do NOT apply — pure numeric fields must not match letters.
4. Return both original and tolerant patterns.
5. Extraction engine tries original first; falls back to tolerant on no-match.

---

### 3.7 New: Output Type Inference

**File:** `app/services/pattern/type_inferrer.py`

**Purpose:** Infer the output type from human pattern or examples without user input.

**Inference rules:**

| Condition | Inferred Type |
|-----------|--------------|
| Pattern contains `{YYYY}`, `{MM}`, `{DD}` | `date` |
| Pattern contains `{MONEY}` | `currency` |
| Examples match `\d{2}/\d{2}/\d{4}` or similar | `date` |
| Examples match currency pattern | `currency` |
| Pattern is pure `{N+}` digits | `number` |
| Pattern contains mixed alpha/numeric | `text` |
| No pattern, free text examples | `text` |
| Boolean keywords in name (is_, has_, active) | `boolean` |

**Returns:** `{ "inferred_type": "date", "confidence": 0.98, "display_format": "DD/MM/YYYY" }`

The frontend shows the inferred type as a soft hint (e.g., "Looks like a date"). User can override in Advanced Settings.

---

### 3.8 New: Teach From Examples One-Step API

**File:** `app/api/teach.py`  
**File:** `app/services/teach/teach_service.py`

**Purpose:** Allow users to upload documents directly without manually creating a Dataset first. Internally creates a Dataset, runs discovery, and surfaces results in consumer language.

**Flow:**
1. `POST /api/teach` — upload files (multipart), immediately creates a hidden Dataset + kicks off clustering/fingerprinting.
2. `GET /api/teach/{session_id}` — poll status (analyzing / complete).
3. `GET /api/teach/{session_id}/layouts` — returns layout groups (clusters renamed to "layouts").
4. `GET /api/teach/{session_id}/proposals` — returns discovered fields as simple proposals.
5. `POST /api/teach/{session_id}/save-setup` — user accepts proposals; creates `Configuration` + `ConfigurationVersion` from proposals.

**Layout response (consumer language):**
```json
{
  "layouts": [
    {
      "id": "cluster-uuid-1",
      "label": "Layout A",
      "document_count": 42,
      "sample_document_id": "doc-uuid"
    },
    {
      "id": "cluster-uuid-2",
      "label": "Layout B",
      "document_count": 8,
      "sample_document_id": "doc-uuid"
    }
  ]
}
```

**Proposal response (consumer language):**
```json
{
  "proposals": [
    {
      "id": "proposal-uuid",
      "suggested_name": "Invoice Number",
      "human_pattern": "INV-{YYYY}-{NNNNN}",
      "example_found": "INV-2026-00128",
      "confidence_label": "Very High",
      "confidence_score": 0.96,
      "why": [
        "Found in 42 of 42 documents",
        "Appears near 'Invoice Number'",
        "Matches the same format every time"
      ],
      "action": "pending"
    }
  ]
}
```

`action` can be: `"use"` / `"edit"` / `"skip"`.

`POST /api/teach/{session_id}/save-setup` converts accepted proposals into a full `Configuration` + `ConfigurationVersion` using the same internal schema as manual rule creation.

---

### 3.9 Unchanged Backend Modules

The following backend files are **NOT modified:**

- `app/providers/ocr/base.py` — OCRProvider protocol
- `app/providers/ocr/registry.py` — provider registry
- `app/services/ocr/tesseract.py` — Tesseract integration
- `app/services/ocr/preprocessing.py` — image preprocessing
- `app/services/extraction/engine.py` — extraction engine
- `app/services/extraction/anchors.py` — anchor matching
- `app/services/extraction/confidence.py` — confidence scoring
- `app/services/extraction/patterns.py` — pattern compilation
- `app/services/extraction/table.py` — table extraction
- `app/services/discovery/clustering.py` — document clustering
- `app/services/discovery/fingerprint.py` — structural fingerprinting
- `app/services/discovery/learner.py` — pattern learning
- `app/services/normalization/normalizer.py` — normalization
- `app/services/validation/validator.py` — validation
- `app/services/testing/runner.py` — regression runner
- `app/services/audit_service.py` — audit logging
- `app/services/learning/corrections.py` — correction engine
- `app/models/` — ALL model files unchanged
- `app/api/configurations.py` — preserved as-is
- `app/api/audit.py` — preserved as-is
- `app/api/tests.py` — preserved as-is
- `app/api/extraction.py` — preserved as-is
- `app/api/discovery.py` — preserved as-is
- `app/api/corrections.py` — preserved as-is
- `app/api/intelligence.py` — preserved as-is
- `app/api/training.py` — preserved as-is

---

## 4. Frontend Changes

### 4.1 Navigation Restructure

**File to modify:** `src/components/Navigation.tsx`

**Current navigation items:**
```
Overview | OCR Playground | Rule Builder | Pattern Trainer | Extraction Results | Regression Suite | Audit Logs
```

**New primary navigation:**
```
Home | Scan Documents | Teach From Examples | My Setups | Results
```

**New secondary section — Advanced Tools (collapsible):**
```
▸ Advanced Tools
  OCR Inspector         (was: OCR Playground)
  Advanced Rule Editor  (was: Rule Builder)
  Pattern Analysis      (was: Pattern Trainer — advanced mode)
  Test & Regression     (was: Regression Suite)
  Activity & System     (was: Audit Logs + Overview metrics)
```

**Implementation details:**
- Primary nav: 5 horizontal tabs / sidebar items, always visible.
- Advanced Tools: collapsible group, shown below primary nav, collapsed by default.
- Route structure:
  - `/` → HomeView
  - `/scan` → ScanDocumentsView
  - `/teach` → TeachFromExamplesView
  - `/setups` → MySetupsView
  - `/setups/:id` → SetupDetailView
  - `/setups/:id/fields/:fieldId` → FieldDetailView
  - `/results` → ResultsView
  - `/advanced/inspector` → OCRInspectorView (was OCRPlaygroundView)
  - `/advanced/rule-editor` → AdvancedRuleEditorView (was RuleBuilderView)
  - `/advanced/pattern-analysis` → PatternAnalysisView (was PatternTrainerView)
  - `/advanced/regression` → RegressionView (was RegressionSuiteView)
  - `/advanced/activity` → ActivityView (was AuditLogsView)

---

### 4.2 Home Screen

**New file:** `src/views/HomeView.tsx`  
**Replaces:** `src/views/OverviewView.tsx` (OverviewView moves to Advanced Tools → Activity & System)

**Layout:**
```
What would you like to do?

[Card 1: Scan Documents]
Upload documents and extract information
using one of your saved setups.
→ Go to Scan

[Card 2: Teach From Examples]
Upload similar documents and let the system
discover repeating information automatically.
→ Get Started

[Card 3: Create a Setup]
Tell the system what information you want to find.
→ New Setup

[Card 4: View Results]
Review and export information from processed documents.
→ View Results
```

**Each card:**
- Large icon (lucide icon)
- Title (Plus Jakarta Sans, `text-xl font-semibold`)
- Description (`text-zinc-400 text-sm`)
- Action button that navigates to the relevant view
- `motion.div` with spring entrance animation (staggered by 60ms per card)
- Flat zinc-900 background, 1px border, hover border-zinc-600

**No metrics, no API status, no OCR engine stats on this screen.**  
(Those remain accessible in Advanced Tools → Activity & System)

---

### 4.3 Create Setup Flow

**New file:** `src/views/CreateSetupView.tsx`  
**New component:** `src/components/setup/AddFieldModal.tsx`  
**New component:** `src/components/setup/PatternInput.tsx`  
**New component:** `src/components/setup/FieldCard.tsx`

**Step 1 — Setup Name:**
```
What kind of documents are these?

[Input: "Laptop Warranty Documents"]

Next →
```

**Step 2 — Add Fields:**
```
Laptop Warranty Documents

What information do you want to find?

[+ Add Something]

[List of added FieldCards]

[Save Setup]  [Back]
```

**Add Something Modal — step by step:**

```
Step A: What should we call this?
[Input: "Serial Number"]

Step B: What does it usually look like?

[Tab: Pattern]  [Tab: Examples]  [Tab: Select from document]  [Tab: Describe it]

─── Pattern Tab ───
SN-{YYYY}-{NNNNNN}
Hint: Use {YYYY} for year, {NNNN} for numbers, {AAA} for letters

Matches values like: SN-2026-001234

─── Examples Tab ───
Paste example values (one per line):
SN-2026-001234
SN-2026-001235
SN-2026-001236

─── Select from document Tab ───
[Shows current document pages if a document was previously uploaded]
[User clicks a value]
"Should I look for values similar to SN-2026-001234?"

─── Describe it Tab ───
[Input: "Starts with SN, followed by the year, then six numbers"]
[Analyze] → shows interpreted pattern

Step C: (shown automatically)
Output type (inferred): Text  ✓  (tap to change)

[Add This Field]
```

**Implementation:**
- `PatternInput` component handles all four tabs with shared output: `{ humanPattern, examples, description, selectedText }`
- On submit, calls `POST /api/setups/{id}/fields` with simplified payload.
- Backend auto-generates `field_id`, `output_variable`, calls pattern parser + auto-strategy.
- Response returns `FieldResponse` which the UI renders as a `FieldCard`.

---

### 4.4 Field Card (Simple Mode)

**Component:** `src/components/setup/FieldCard.tsx`

**Display:**
```
┌─────────────────────────────────────────────┐
│  Serial Number                              │
│                                             │
│  Looks like:                                │
│  SN-{YYYY}-{NNNNNN}                         │
│                                             │
│  Output type: Text                          │
│  Status: ● Ready                            │
│                                             │
│  [Edit]  [Test]  [Remove]  [···Advanced]   │
└─────────────────────────────────────────────┘
```

- Does NOT show: field_id, output_variable, regex, anchor, search geometry, priority.
- `[Edit]` → reopens AddFieldModal in edit mode.
- `[Test]` → opens inline test panel; user uploads a document and sees what was found.
- `[Remove]` → confirmation dialog, then deletes.
- `[···Advanced]` → navigates to Advanced Rule Editor for that specific field.

---

### 4.5 Scan Documents View

**New file:** `src/views/ScanDocumentsView.tsx`  
**Replaces the primary extraction workflow** (ExtractionResultsView moved to Advanced Tools area and simplified here)

**Layout:**
```
Scan Documents

Step 1: Choose a setup
[Dropdown or card grid of "My Setups"]

Step 2: Upload document
[DropZone component]

Step 3: [Scan →]

─── Results ───
[ResultsPanel — shows each field with found value + confidence label]
```

**If ambiguity is detected:**
```
We found 3 possible values for Serial Number.

[Candidate 1] SN-2026-001234  Near: "Serial Number"  ● Very High
[Candidate 2] SN-2026-001235  Near: "Replacement Serial"  ● Medium
[Candidate 3] SN-2026-001236  Near: "Reference"  ● Low

Which one is correct?
[Use this] for each candidate
```

---

### 4.6 Results View (Consumer)

**New file:** `src/views/ResultsView.tsx`

**Layout:**
```
Results

[Filter by setup dropdown]  [Date range]  [Export →]

Document: invoice_scan_001.pdf
Setup: Laptop Warranty Documents
Scanned: 09 Sep 2026 01:30

┌─────────────────────────────┐
│ Serial Number               │
│ SN-2026-004821              │
│ ● Very High                 │
│ [Why?] ▸                    │
│ [Correct this value]        │
└─────────────────────────────┘

┌─────────────────────────────┐
│ Warranty Code               │
│ WC-2026-9921                │
│ ● High                      │
└─────────────────────────────┘

[Export JSON]  [Export CSV]
```

**"Why?" expandable:**
```
● Very High — Why?

• Matches the format SN-{YYYY}-{NNNNNN}
• Found next to "Serial Number"
• Appears in the same location across similar documents
• Confidence score: 0.96
```

**"Correct this value" flow:**
```
What is the correct value for Serial Number?

Current: SN-2026-004821
Correct: [Input field]

[ ] Use this correction to improve future scans

[Save Correction]
```

If "Use this correction to improve future scans" is checked → calls `POST /api/corrections` and prompts for confirmation before applying to the active Setup.

---

### 4.7 Teach From Examples View

**New file:** `src/views/TeachFromExamplesView.tsx`  
**Replaces:** `src/views/PatternTrainerView.tsx` (PatternTrainerView moved to Advanced Tools → Pattern Analysis)

**Phase 1 — Upload:**
```
Teach From Examples

Upload several similar documents and let the system
discover repeating information automatically.

[DropZone — multiple files]

[Start Analysis →]
```

**Phase 2 — Analyzing:**
```
Analyzing your documents...

[Animated progress indicator]
• Reading text from 50 documents...  ✓
• Identifying document layouts...
• Discovering repeating information...
```

**Phase 3 — Layouts:**
```
We found 2 different document layouts.

[Layout A card]
42 documents
[View Sample]

[Layout B card]
8 documents
[View Sample]

[Continue →]
```

**Phase 4 — Proposals:**
```
Here's what we found:

[Proposal Card: Invoice Number]
Example found: INV-2026-00128
Looks like: INV-{YYYY}-{NNNNN}
● Very High confidence

Why?
• Found in 42 of 42 documents
• Appears near "Invoice Number"
• Matches the same format every time

[Use This]  [Edit]  [Don't Use]

─────────────────────────────────

[Proposal Card: Due Date]
...

[Save Setup →] (when at least 1 accepted)
```

**Save Setup step:**
```
Name this setup:

[Input: "Supplier Invoices"]

[Save Setup] → navigates to /setups/:id
```

---

### 4.8 My Setups View

**New file:** `src/views/MySetupsView.tsx`

**Layout:**
```
My Setups

[+ Create Setup]

[Setup Card: Laptop Warranty Documents]
4 fields  •  Last scanned: 2 hours ago
[Scan]  [Edit]  [View Results]

[Setup Card: Supplier Invoices]
6 fields  •  Last scanned: Yesterday
[Scan]  [Edit]  [View Results]
```

Each Setup Card:
- Setup name (large, Plus Jakarta Sans)
- Field count + last scan time
- Status pill (Ready / Draft / No Documents)
- Three action buttons

---

### 4.9 Advanced Tools Section

All existing views are preserved and accessible here. The views themselves are NOT deleted.

| Advanced Tool | Source View | Changes to view |
|---------------|-------------|-----------------|
| OCR Inspector | `OCRPlaygroundView.tsx` | - Rename in nav label only. - Add "Use this as an example" option when text is clicked (instead of auto-anchoring). - Add "Create field from selection" shortcut. |
| Advanced Rule Editor | `RuleBuilderView.tsx` | - Rename in nav label only. - Add banner: "Changes here will affect the simple view of this field." - Fields created in simple mode appear here for full editing. |
| Pattern Analysis | `PatternTrainerView.tsx` | - Rename in nav label only. - No functional changes required. |
| Test & Regression | `RegressionSuiteView.tsx` | - Rename in nav label only. |
| Activity & System | `AuditLogsView.tsx` + `OverviewView.tsx` combined | - Both views merged into tabbed interface: "Activity" tab (audit logs) + "System" tab (metrics/health from overview). |

---

### 4.10 Confidence Display

**New component:** `src/components/ConfidenceBadge.tsx`

**Mapping:**

| Score | Label | Colour |
|-------|-------|--------|
| ≥ 0.90 | Very High | `text-emerald-400` |
| ≥ 0.70 | High | `text-green-400` |
| ≥ 0.45 | Medium | `text-amber-400` |
| < 0.45 | Low | `text-red-400` |

**"Why?" expandable:**
```tsx
<ConfidenceBadge
  score={0.96}
  reasons={[
    "Matches the format SN-{YYYY}-{NNNNNN}",
    "Found next to 'Serial Number'",
    "Appears in same location across similar documents"
  ]}
  advancedScore={{ pattern: 0.98, anchor: 0.94, layout: 0.91 }}
/>
```

In simple mode: shows label + "Why?" link.  
In advanced mode (toggle): shows numeric scores per component.

---

### 4.11 Ambiguity Resolution UI

**New component:** `src/components/AmbiguityPanel.tsx`

Shown inline within `ScanDocumentsView` and `ResultsView` when `ambiguous: true` is returned.

```
We found 3 possible Serial Numbers.

● SN-2026-001234   Near: "Serial Number"    ● Very High  [Use This ✓]
● SN-2026-001235   Near: "Replacement SN"   ● Medium     [Use This]
● SN-2026-001236   Near: "Reference Code"   ● Low        [Use This]

Choosing the correct value will improve future scans.
```

On "Use This":
- Calls `POST /api/setups/{id}/fields/{fieldId}/resolve`
- Updates rule to prefer the chosen candidate's anchor/position.
- Shows confirmation: "Updated. Future scans will prefer this value."

---

### 4.12 Human Correction Loop UI

**Component embedded in:** `src/views/ResultsView.tsx`

Behaviour:
1. User clicks "Correct this value".
2. Input appears with current value.
3. Optional checkbox: "Use this to improve future scans".
4. If checkbox checked AND Save pressed:
   - Calls `POST /api/corrections`
   - Shows confirmation dialog: "Apply this correction to improve future extractions for [Setup Name]? This will update the active setup version."
   - [Apply] → calls internal update; [Not now] → saves correction for review only.
5. Correction stored either way for regression test purposes.

---

## 5. New Files — Backend

```
app/
  api/
    setups.py                         # Setup CRUD adapter
    setup_fields.py                   # Field CRUD adapter (simple mode)
    ambiguity.py                      # Candidate resolution
    teach.py                          # Teach From Examples session API
  services/
    setup/
      __init__.py
      setup_service.py                # Creates Configuration + Version
      field_service.py                # Creates ExtractionField + Rule from human input
    pattern/
      __init__.py
      human_parser.py                 # Human pattern language → regex
      ocr_tolerance.py                # OCR confusion character expansion
      type_inferrer.py                # Output type inference
    extraction/
      auto_strategy.py                # Automatic rule generation
      ambiguity.py                    # Multi-candidate resolution
    teach/
      __init__.py
      teach_service.py                # Wraps dataset/discovery/learner
  tests/                              # New test files (see §11)
    test_human_parser.py
    test_auto_strategy.py
    test_type_inferrer.py
    test_ocr_tolerance.py
    test_field_id_generation.py
    test_ambiguity.py
    test_teach_service.py
    test_setup_api.py
```

---

## 6. New Files — Frontend

```
src/
  views/
    HomeView.tsx                      # New home screen (replaces OverviewView as primary)
    CreateSetupView.tsx               # Setup creation wizard
    MySetupsView.tsx                  # Setup list
    SetupDetailView.tsx               # Single setup with fields
    ScanDocumentsView.tsx             # Upload + extract with a setup
    TeachFromExamplesView.tsx         # Guided discovery (replaces PatternTrainer as primary)
    ResultsView.tsx                   # Consumer-facing results with correction
  components/
    setup/
      FieldCard.tsx                   # Simple field display card
      AddFieldModal.tsx               # Add/edit field wizard
      PatternInput.tsx                # Four-tab pattern input component
      SetupCard.tsx                   # Setup list card
    ConfidenceBadge.tsx               # Score → label + why? expandable
    AmbiguityPanel.tsx                # Multi-candidate resolution
    AdvancedToolsSection.tsx          # Collapsible nav group
  lib/
    setupApi.ts                       # API calls for /api/setups and /api/fields
    teachApi.ts                       # API calls for /api/teach
    patternParser.ts                  # Client-side preview of human pattern parsing
```

---

## 7. Modified Files — Backend

| File | Change |
|------|--------|
| `app/main.py` | Register 4 new routers: setups, setup_fields, ambiguity, teach |
| `app/api/intelligence.py` | Minor: expose `FIELD_CATALOGUE` endpoint for frontend pattern hints |
| `app/services/intelligence/suggestions.py` | Extract `FIELD_CATALOGUE` into shared constant importable by `auto_strategy.py` |

---

## 8. Modified Files — Frontend

| File | Change |
|------|--------|
| `src/components/Navigation.tsx` | Full restructure — new primary nav + Advanced Tools collapsible |
| `src/App.tsx` | Add new routes, update route → view mapping |
| `src/views/OCRPlaygroundView.tsx` | Add "Use as example" button on text click; rename in breadcrumb to "OCR Inspector" |
| `src/views/RuleBuilderView.tsx` | Add "compatible with simple mode" banner; make accessible from FieldCard `[···Advanced]` |
| `src/views/AuditLogsView.tsx` | Rename to ActivityView in nav; add System tab with metrics |
| `src/lib/api.ts` | Add type definitions for SetupResponse, FieldResponse, ProposalResponse, CandidateResponse |

---

## 9. Deleted / Retired Files

**No files are deleted.** All existing views remain.  
Views that are superseded as primary navigation are moved to Advanced Tools:

| View | Old role | New role |
|------|----------|----------|
| `OverviewView.tsx` | Primary home | Advanced Tools → Activity & System (System tab) |
| `PatternTrainerView.tsx` | Primary nav | Advanced Tools → Pattern Analysis |
| `RegressionSuiteView.tsx` | Primary nav | Advanced Tools → Test & Regression |
| `AuditLogsView.tsx` | Primary nav | Advanced Tools → Activity & System (Activity tab) |

---

## 10. Terminology Mapping

| Old (technical) | New (user-facing) | Scope |
|-----------------|-------------------|-------|
| OCR Playground | OCR Inspector | Nav label, page title |
| Rule Builder | Advanced Rule Editor | Nav label, page title |
| Pattern Trainer | Teach From Examples (primary) / Pattern Analysis (advanced) | Nav label, page title |
| Configuration | Setup | All simple-mode UI |
| Configuration Version | Version History | In Setup Detail view |
| Extraction Rule | How to Find It | Field card advanced section |
| Generate Config | Save Setup | Button label |
| Proposal | Suggested Information | Teach flow |
| Anchor | Nearby Label | Simple mode |
| Regression Suite | Test & Regression | Advanced Tools nav |
| Audit Logs | Activity & System | Advanced Tools nav |
| Cluster | Layout | Teach From Examples phase 3 |
| Dataset | (hidden) | Created internally; not user-visible |
| Extraction Field | Field | Everywhere |
| Output Variable | (hidden in simple) | Advanced Settings only |
| Field ID | (hidden in simple) | Advanced Settings only |
| Anchored Pattern | (hidden) | Advanced Rule Editor only |
| Direct Pattern | (hidden) | Advanced Rule Editor only |
| Same Line | (hidden) | Advanced Rule Editor only |
| Region | (hidden) | Advanced Rule Editor only |

---

## 11. Test Plan

### 11.1 New Backend Tests

**`tests/test_human_parser.py`**
- `test_parse_YYYY_token()` → `\d{4}`
- `test_parse_NNNNNN_token()` → `\d{6}`
- `test_parse_MONEY_token()` → currency regex
- `test_parse_EMAIL_token()` → email regex
- `test_parse_composite_pattern_SN_YYYY_NNNNNN()` → full regex
- `test_compile_matches_example()` → compiled regex matches `SN-2026-001234`
- `test_infer_from_examples_serial()` → from 3 serial number examples, infer `SN-{YYYY}-{NNNNNN}`
- `test_infer_from_examples_invoice()` → from invoice examples, infer `INV-{YYYY}-{NNNNN}`
- `test_plain_language_year_and_six_numbers()` → returns `SN-{YYYY}-{NNNNNN}`
- `test_plain_language_date()` → "day, month, then year" → `{DD}/{MM}/{YYYY}`

**`tests/test_ocr_tolerance.py`**
- `test_no_tolerance_on_numeric_only()` → `\d{6}` not modified
- `test_tolerance_on_alphanumeric()` → `ABC` becomes `[A-Za-z][B8][C]` variant
- `test_O_zero_substitution()`
- `test_I_one_l_substitution()`
- `test_S_5_substitution()`

**`tests/test_type_inferrer.py`**
- `test_infer_date_from_pattern_tokens()`
- `test_infer_currency_from_MONEY_token()`
- `test_infer_number_from_pure_digit_pattern()`
- `test_infer_text_from_mixed_pattern()`
- `test_infer_from_date_examples()`
- `test_infer_from_currency_examples()`
- `test_no_override_on_ambiguous_pattern()`

**`tests/test_field_id_generation.py`**
- `test_display_name_to_field_id()` → `"Serial Number"` → `"serial_number"`
- `test_display_name_with_special_chars()` → `"Item #"` → `"item"`
- `test_duplicate_field_id_disambiguation()` → if `serial_number` exists, generates `serial_number_2`
- `test_output_variable_matches_field_id()`

**`tests/test_ambiguity.py`**
- `test_single_match_not_ambiguous()`
- `test_two_matches_triggers_ambiguous()`
- `test_resolve_candidate_updates_rule()`
- `test_candidates_have_context_before_after()`

**`tests/test_setup_api.py`**
- `test_create_setup_creates_configuration()`
- `test_create_setup_creates_initial_version()`
- `test_add_field_auto_generates_field_id()`
- `test_add_field_stores_extraction_rule()`
- `test_list_setups_returns_consumer_view_model()`
- `test_setup_scan_runs_extraction()`

**`tests/test_teach_service.py`**
- `test_teach_creates_dataset_internally()`
- `test_teach_returns_layouts_not_clusters()`
- `test_proposals_include_human_pattern()`
- `test_save_setup_creates_configuration()`
- `test_accepted_proposals_become_rules()`

**`tests/test_auto_strategy.py`**
- `test_single_match_uses_direct_pattern()`
- `test_multiple_matches_with_label_uses_anchored()`
- `test_no_match_tries_ocr_tolerant()`
- `test_no_match_at_all_returns_not_found()`
- `test_layout_consistent_adds_region_hint()`
- `test_field_catalogue_seeds_anchor_vocabulary()`

### 11.2 Existing Tests

All 48 existing tests must continue to pass without modification.

### 11.3 Frontend E2E Scenarios (manual test script)

**Scenario 1 — Beginner sub-1-minute flow:**
1. Open app → Home screen shown.
2. Click "Create a Setup" → CreateSetupView.
3. Enter "Laptop Warranty Documents" → Next.
4. Click "+ Add Something".
5. Enter "Serial Number" → Next.
6. Select "Pattern" tab, type `SN-{YYYY}-{NNNNNN}`.
7. Preview shows matching example.
8. Click "Add This Field".
9. Field card appears.
10. Click "Save Setup".
11. Redirected to MySetupsView, new setup listed.
12. Click "Scan".
13. Upload a document.
14. Click "Scan".
15. Result: "Serial Number: SN-2026-004821 — Very High".
✅ Success.

**Scenario 2 — Advanced rule workflow:**
1. Open Advanced Tools → Advanced Rule Editor.
2. Select existing setup.
3. Modify anchor strategy for a field.
4. Save version.
5. Return to MySetups → setup still shows correct field.
✅ Advanced rule compatible with simple mode.

**Scenario 3 — Simple mode → Advanced Editor round-trip:**
1. Create field in simple mode.
2. Click `[···Advanced]` on FieldCard.
3. Verify ExtractionRule is visible with correct strategy, pattern, anchor.
4. Modify anchor in Advanced Editor.
5. Return to FieldCard.
6. FieldCard still shows correctly (adapter re-reads from rule).
✅ Round-trip compatible.

**Scenario 4 — Teach From Examples:**
1. Upload 10 similar documents.
2. Wait for analysis.
3. "We found 1 document layout."
4. Proposals listed.
5. Accept 3 proposals.
6. Name setup "Supplier Invoices".
7. Save Setup.
8. New setup appears in MySetups with 3 fields.
✅ Teach flow complete.

**Scenario 5 — Regression still works:**
1. Open Advanced Tools → Test & Regression.
2. Existing test suite still shows results.
3. Add a correction from Results view.
4. Verify it appears as a regression candidate.
✅ No regression in regression suite.

**Scenario 6 — Audit logs still work:**
1. Open Advanced Tools → Activity & System.
2. Audit log shows all actions taken in above scenarios.
✅ Audit intact.

---

## 12. Implementation Phases

### Phase A — Backend Adapter Layer (no frontend changes yet)

**Duration estimate:** 2–3 sessions  
**Deliverables:**
1. `app/services/pattern/human_parser.py` + tests
2. `app/services/pattern/ocr_tolerance.py` + tests
3. `app/services/pattern/type_inferrer.py` + tests
4. `app/services/extraction/auto_strategy.py` + tests
5. `app/services/setup/setup_service.py` + `field_service.py`
6. `app/api/setups.py` + `app/api/setup_fields.py`
7. `app/services/extraction/ambiguity.py` + `app/api/ambiguity.py`
8. `app/services/teach/teach_service.py` + `app/api/teach.py`
9. Register all routers in `app/main.py`
10. All new tests passing

**Verification:** 48 existing tests + all new tests pass.

---

### Phase B — Navigation & Home Screen

**Duration estimate:** 1 session  
**Deliverables:**
1. `src/components/Navigation.tsx` restructured — primary nav + Advanced Tools collapsible
2. `src/App.tsx` updated with new routes
3. `src/views/HomeView.tsx` — 4 action cards, motion.dev stagger
4. Existing views still accessible via new routes

**Verification:** All existing views reachable. Home screen renders correctly.

---

### Phase C — My Setups + Create Setup Flow

**Duration estimate:** 2 sessions  
**Deliverables:**
1. `src/views/MySetupsView.tsx`
2. `src/views/CreateSetupView.tsx`
3. `src/components/setup/AddFieldModal.tsx`
4. `src/components/setup/PatternInput.tsx` (4 tabs)
5. `src/components/setup/FieldCard.tsx`
6. `src/components/setup/SetupCard.tsx`
7. `src/lib/setupApi.ts`
8. Client-side human pattern preview in `src/lib/patternParser.ts`

**Verification:** Scenario 1 (beginner flow) works end-to-end.

---

### Phase D — Scan Documents + Results + Ambiguity + Correction

**Duration estimate:** 2 sessions  
**Deliverables:**
1. `src/views/ScanDocumentsView.tsx`
2. `src/views/ResultsView.tsx`
3. `src/components/ConfidenceBadge.tsx`
4. `src/components/AmbiguityPanel.tsx`
5. Correction loop in ResultsView

**Verification:** Scenarios 2, 3, 5 work end-to-end.

---

### Phase E — Teach From Examples

**Duration estimate:** 1–2 sessions  
**Deliverables:**
1. `src/views/TeachFromExamplesView.tsx`
2. `src/lib/teachApi.ts`
3. Layout / proposal display with confidence badges
4. Save Setup step

**Verification:** Scenario 4 works end-to-end.

---

### Phase F — Advanced Tools polish + Activity & System merge

**Duration estimate:** 1 session  
**Deliverables:**
1. OCR Inspector minor additions (Use as example, Create field from selection)
2. Advanced Rule Editor banner + FieldCard `[···Advanced]` link
3. `ActivityView.tsx` — merged AuditLogs + System metrics tabs
4. All terminology labels updated in existing views

**Verification:** Scenarios 5, 6 work. All 48+ tests still pass.

---

### Phase G — Final Build, Tests, Push

1. Run full backend test suite.
2. `npm run build` → 0 TypeScript errors.
3. Manual E2E run of all 6 scenarios.
4. `git commit -m "feat: UX Refactor — consumer-first Setup/Field abstraction over existing OCR engine"`
5. `git push origin main`

---

## 13. API Contract Reference

### New Endpoints Summary

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/setups` | List all setups |
| POST | `/api/setups` | Create setup |
| GET | `/api/setups/{id}` | Get setup with fields |
| PUT | `/api/setups/{id}` | Rename setup |
| DELETE | `/api/setups/{id}` | Delete setup |
| POST | `/api/setups/{id}/scan` | Upload + extract |
| GET | `/api/setups/{id}/results` | Extraction results |
| GET | `/api/setups/{id}/history` | Version history |
| GET | `/api/setups/{id}/fields` | List fields (simple) |
| POST | `/api/setups/{id}/fields` | Add field (auto-generates rule) |
| PUT | `/api/setups/{id}/fields/{fid}` | Update field |
| DELETE | `/api/setups/{id}/fields/{fid}` | Delete field |
| GET | `/api/setups/{id}/fields/{fid}/advanced` | Full ExtractionField data |
| GET | `/api/setups/{id}/fields/{fid}/candidates` | Ambiguity candidates |
| POST | `/api/setups/{id}/fields/{fid}/resolve` | Resolve ambiguity |
| POST | `/api/pattern-parser/compile` | Compile human pattern → regex |
| POST | `/api/pattern-parser/from-examples` | Infer pattern from examples |
| POST | `/api/pattern-parser/from-description` | Infer pattern from description |
| POST | `/api/auto-strategy/generate` | Generate ExtractionRule from field def |
| POST | `/api/teach` | Start Teach session (upload files) |
| GET | `/api/teach/{session_id}` | Poll session status |
| GET | `/api/teach/{session_id}/layouts` | Get discovered layouts |
| GET | `/api/teach/{session_id}/proposals` | Get consumer-language proposals |
| POST | `/api/teach/{session_id}/save-setup` | Convert accepted proposals to Setup |

### Preserved Existing Endpoints (ALL kept as-is)

`/api/configurations`, `/api/documents`, `/api/ocr`, `/api/extraction`, `/api/discovery`, `/api/tests`, `/api/results`, `/api/audit-logs`, `/api/auth`, `/api/corrections`, `/api/intelligence`, `/api/training`, `/api/health`

---

*End of Plan*

**To begin implementation, proceed to Phase A — Backend Adapter Layer.**  
Run `python3 -m pytest tests/ -v` before and after each phase to ensure zero regressions.
