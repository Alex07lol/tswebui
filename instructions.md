# Tesseract OCR WebUI Platform
## Fully Configurable OCR Extraction + Example-Based Pattern Learning

**Status:** Architecture / Product Specification  
**Primary OCR Engine:** Tesseract OCR  
**Primary Interface:** WebUI  
**Architecture Style:** Modular, provider-based, configuration-driven  
**Core Principle:** No source-code changes should be required to change what the system extracts.

---

# 1. Product Definition

Build a configurable OCR platform around Tesseract where users can define, test, train, version, and deploy document extraction logic entirely from a WebUI.

The platform has two major operating modes:

## Mode A — Manual Configuration

The user tells the system:

- what information to look for
- what the information is called
- what format it should follow
- where it usually appears
- what text identifies it
- how the value should be cleaned
- how the value should be validated
- what output variable should receive it

Example:

```text
Look for: Invoice Number

Anchor:
Invoice No

Expected format:
INV-2026-00128

General format:
INV-{YYYY}-{NNNNN}

Output variable:
invoice_number
```

The system converts this into an executable extraction rule.

---

## Mode B — Example-Based Learning

The user provides `N` files containing examples of the same or related document type.

Example:

```text
invoice_01.pdf
invoice_02.pdf
invoice_03.pdf
...
invoice_N.pdf
```

The system:

```text
N Files
   ↓
OCR every file
   ↓
Preserve text + positions + confidence
   ↓
Compare documents
   ↓
Find recurring structures
   ↓
Find stable labels
   ↓
Find changing values
   ↓
Infer formats/patterns
   ↓
Generate variables and rules
   ↓
Show confidence and evidence
   ↓
User reviews and edits
   ↓
Save as a normal extraction configuration
```

The learned result is not a hidden model.

It becomes the same editable configuration format used by the manual mode.

---

# 2. Architecture Principles

The architecture must follow these principles.

## 2.1 Configuration Over Code

Extraction behaviour must be represented as configuration.

Bad:

```python
if "Invoice No" in text:
    invoice_number = ...
```

Good:

```yaml
field: invoice_number
anchor: Invoice No
strategy: same_line_after_anchor
pattern: INV-\d{4}-\d{5}
```

---

## 2.2 OCR Is a Provider

Tesseract is the default OCR implementation, not the center of the architecture.

The application communicates with:

```text
OCR Provider Interface
        │
        ├── Tesseract Provider
        │
        ├── Future OCR Provider
        │
        └── Custom Provider
```

This allows future OCR engines without rewriting extraction logic.

---

## 2.3 Training Means Pattern Learning First

The first "training" system should learn document structures and extraction rules.

It should not initially retrain Tesseract neural recognition models.

Two separate concepts must exist:

```text
Pattern Learning
    ↓
Learns:
- fields
- labels
- formats
- positions
- rules
```

and:

```text
OCR Model Training
    ↓
Learns:
- characters
- recognition model behaviour
- language/domain recognition
```

Pattern learning is part of the main product.

OCR model training is an optional advanced subsystem.

---

## 2.4 Every Result Needs Evidence

The system should never only return:

```json
{
  "invoice_number": "INV-2026-00128"
}
```

Internally, it should retain:

```json
{
  "field": "invoice_number",
  "raw_value": "INV-2026-00128",
  "normalized_value": "INV-2026-00128",
  "final_confidence": 0.96,
  "evidence": {
    "rule_id": "rule_invoice_number",
    "anchor": "Invoice No",
    "source_line": "Invoice No: INV-2026-00128",
    "ocr_confidence": 0.93,
    "bounding_box": {
      "x": 420,
      "y": 182,
      "width": 220,
      "height": 32
    }
  }
}
```

---

# 3. System Architecture

```text
                           ┌────────────────────────────┐
                           │           WEB UI           │
                           │                            │
                           │ Dashboard                  │
                           │ OCR Playground             │
                           │ Rule Builder               │
                           │ Dataset Trainer            │
                           │ Config Manager             │
                           │ Result Explorer            │
                           └──────────────┬─────────────┘
                                          │
                                  REST / WebSocket
                                          │
                           ┌──────────────▼─────────────┐
                           │       APPLICATION API      │
                           │                            │
                           │ Auth / Permissions         │
                           │ Config Management          │
                           │ OCR Jobs                   │
                           │ Extraction Jobs            │
                           │ Pattern Discovery Jobs     │
                           │ Result API                 │
                           └───────┬───────────┬────────┘
                                   │           │
                   ┌───────────────┘           └───────────────┐
                   ▼                                           ▼
        ┌─────────────────────┐                    ┌─────────────────────┐
        │    OCR SUBSYSTEM    │                    │ PATTERN SUBSYSTEM   │
        │                     │                    │                     │
        │ OCRProvider         │                    │ Document Analyzer   │
        │ TesseractProvider   │                    │ Alignment Engine    │
        │ Preprocessor        │                    │ Pattern Generator   │
        │ PDF/Image Loader    │                    │ Field Proposer      │
        └──────────┬──────────┘                    └──────────┬──────────┘
                   │                                          │
                   └──────────────────┬───────────────────────┘
                                      ▼
                          ┌────────────────────────┐
                          │   EXTRACTION ENGINE    │
                          │                        │
                          │ Anchor Matcher         │
                          │ Pattern Matcher        │
                          │ Region Matcher         │
                          │ Table Extractor        │
                          │ Candidate Resolver     │
                          └───────────┬────────────┘
                                      ▼
                          ┌────────────────────────┐
                          │ NORMALIZE + VALIDATE   │
                          │                        │
                          │ Normalizers            │
                          │ Type Converters        │
                          │ Validators             │
                          │ Confidence Engine      │
                          └───────────┬────────────┘
                                      ▼
                          ┌────────────────────────┐
                          │   RESULT / EXPORT      │
                          │                        │
                          │ JSON                   │
                          │ CSV                    │
                          │ Database               │
                          │ API                    │
                          │ Webhooks               │
                          └────────────────────────┘
```

---

# 4. Skills, Plugins, Providers, Components and Interactions

This separation must be maintained throughout the project.

## 4.1 Skills

Skills are user-facing or high-level capabilities.

```text
OCR Document
Extract Structured Data
Build Extraction Rule
Test Configuration
Learn Document Pattern
Classify Template
Validate Extraction
Export Results
Train OCR Model (future)
```

Skills orchestrate components and services.

---

## 4.2 Plugins

Plugins extend the platform without modifying core extraction architecture.

Examples:

```text
PDF Plugin
Excel Export Plugin
Webhook Plugin
Database Export Plugin
Table Extraction Plugin
LLM Assistance Plugin
Custom OCR Provider Plugin
Document Classifier Plugin
```

Plugin contract:

```text
Plugin
 ├── Metadata
 ├── Permissions
 ├── Configuration Schema
 ├── Lifecycle Hooks
 └── Registered Capabilities
```

---

## 4.3 Providers

Providers implement replaceable infrastructure or engines.

```text
OCR Provider
 ├── TesseractProvider
 └── FutureOCRProvider

Storage Provider
 ├── LocalStorageProvider
 └── S3StorageProvider

Queue Provider
 ├── LocalQueueProvider
 └── RedisQueueProvider
```

---

## 4.4 Components

Components are concrete internal modules.

```text
DocumentLoader
ImagePreprocessor
OCRProcessor
OCRResultStore

AnchorMatcher
RegexMatcher
TemplateMatcher
RegionMatcher
TableExtractor

Normalizer
Validator
TypeConverter

DocumentFingerprint
DocumentClusterer
SequenceAligner
PatternGeneralizer
ProposalGenerator

ConfidenceScorer
ConflictResolver
EvidenceBuilder
```

---

## 4.5 Interactions

### Manual extraction

```text
User Config
    ↓
Configuration Validator
    ↓
OCR Result
    ↓
Rule Execution
    ↓
Candidate Generation
    ↓
Candidate Validation
    ↓
Normalization
    ↓
Conflict Resolution
    ↓
Structured Result
```

### Pattern learning

```text
Dataset
    ↓
OCR Workers
    ↓
OCR Result Store
    ↓
Document Fingerprinting
    ↓
Document Clustering
    ↓
Sequence/Layout Alignment
    ↓
Stable Region Detection
    ↓
Variable Region Detection
    ↓
Pattern Generalization
    ↓
Rule Proposals
    ↓
Confidence Scoring
    ↓
User Review
    ↓
Configuration Version
```

---

# 5. Core Domain Model

The domain model should explicitly represent:

```text
Project
  ├── Files
  ├── OCR Results
  ├── Configurations
  │     └── Configuration Versions
  │             └── Fields
  │                     └── Rules
  ├── Datasets
  │     └── Dataset Files
  ├── Pattern Learning Runs
  │     └── Pattern Proposals
  ├── Extraction Jobs
  │     └── Extraction Results
  └── Test Suites
        └── Test Runs
```

---

# 6. Configuration Architecture

Configurations should be declarative and versioned.

Example:

```yaml
schema_version: 1

id: invoice_config
name: Invoice Extraction
version: 3

ocr_profile:
  provider: tesseract
  language: eng
  psm: 6

fields:

  - id: invoice_number

    metadata:
      display_name: Invoice Number
      description: Primary invoice identifier

    output:
      variable: invoice_number
      type: string
      required: true

    extraction:
      strategy: anchored_pattern

      anchor:
        value: Invoice No
        match: fuzzy
        minimum_similarity: 0.9

      search:
        direction: after
        scope: same_line

      pattern:
        type: template
        value: INV-{YYYY}-{NNNNN}

    normalization:
      - trim
      - uppercase

    validation:
      required: true
      regex: "^INV-\d{4}-\d{5}$"

    priority: 100
```

---

# 7. Configuration Schema Layers

The configuration should be divided into layers.

```text
OCR Layer
    ↓
Preprocessing Layer
    ↓
Template Classification Layer
    ↓
Extraction Layer
    ↓
Normalization Layer
    ↓
Validation Layer
    ↓
Output Layer
```

This prevents rules from becoming giant, unmaintainable objects.

---

# 8. OCR Subsystem

## Input Types

Initial support:

```text
PNG
JPG
JPEG
TIFF
BMP
PDF
```

Future:

```text
HEIC
DOCX rendering
scanned archive formats
```

---

## OCR Result Contract

Every provider should return a common structure.

```python
class OCRResult:
    document_id: str
    full_text: str
    pages: list[OCRPage]
    provider: str
    provider_version: str
```

```python
class OCRPage:
    page_number: int
    width: int
    height: int
    text: str
    blocks: list[OCRBlock]
```

```python
class OCRWord:
    text: str
    confidence: float
    bounding_box: BoundingBox
```

Tesseract-specific behaviour must be translated into this generic contract.

---

# 9. Image Preprocessing Architecture

Preprocessing must be configurable as a pipeline.

```text
Input Image
    ↓
Orientation Detection
    ↓
Rotation
    ↓
Resize
    ↓
Grayscale
    ↓
Denoise
    ↓
Contrast Enhancement
    ↓
Threshold
    ↓
Deskew
    ↓
OCR
```

Each step should be individually configurable.

Example:

```yaml
preprocessing:
  steps:
    - orientation_detect
    - resize:
        scale: 2
    - grayscale
    - denoise:
        level: medium
    - adaptive_threshold
    - deskew
```

The WebUI must allow:

```text
Original
vs
Preprocessed
vs
OCR Result
```

comparison.

---

# 10. WebUI Architecture

## Primary Navigation

```text
Dashboard

Documents
Datasets
Configurations
Pattern Trainer
OCR Playground
Extraction Results
Test Suites
Settings
```

---

# 11. OCR Playground

Purpose: rapidly test OCR and rules.

Layout:

```text
┌─────────────────────────────────────────────────────────────┐
│ Document Viewer                    │ OCR / Rules Panel       │
│                                    │                         │
│ [document image]                   │ Raw OCR Text            │
│                                    │                         │
│ highlighted words/regions          │ Selected Field          │
│                                    │                         │
│                                    │ Rule Preview            │
│                                    │                         │
│                                    │ Extracted Value         │
│                                    │ Confidence              │
└─────────────────────────────────────────────────────────────┘
```

Interactions:

- click OCR word
- highlight value
- select anchor
- create field from selection
- create region from selection
- inspect OCR confidence
- test current configuration
- compare preprocessing profiles

---

# 12. Visual Rule Builder

The user should not need regex knowledge.

Workflow:

```text
1. Name the field
        ↓
2. Select output type
        ↓
3. Tell system how to identify it
        ↓
4. Define where to search
        ↓
5. Define expected format
        ↓
6. Define cleanup
        ↓
7. Define validation
        ↓
8. Test
        ↓
9. Save
```

Example UI fields:

```text
Field Name:
[ Invoice Number                    ]

Output Variable:
[ invoice_number                   ]

Value Type:
[ String ▼                         ]

Anchor:
[ Invoice No                       ]

Search Direction:
[ After ▼                          ]

Search Scope:
[ Same Line ▼                      ]

Expected Format:
[ Template ▼                       ]

Template:
[ INV-{YYYY}-{NNNNN}              ]

Normalize:
[x] Trim
[x] Uppercase

Required:
[x]

[ Test Rule ]     [ Save Rule ]
```

---

# 13. Pattern Input System

The user can define patterns in multiple ways.

## Raw Regex

```regex
INV-\d{4}-\d{5}
```

---

## Human Template

```text
INV-{YYYY}-{NNNNN}
```

The system compiles this internally.

---

## Typed Pattern

```text
Date
Currency
Integer
Decimal
Email
Phone
UUID
Custom ID
```

---

## Example Pattern

The user supplies examples:

```text
INV-2026-00128
INV-2026-00129
INV-2026-00130
```

The platform suggests a generalized pattern.

---

# 14. Extraction Strategies

The extraction engine must support independent strategies.

## 14.1 Direct Pattern Search

```text
Search whole document for regex.
```

---

## 14.2 Anchored Pattern

```text
Anchor
   ↓
Search nearby
   ↓
Pattern match
```

---

## 14.3 Same-Line Value

```text
Invoice No: INV-2026-00128
```

---

## 14.4 Next-Line Value

```text
Customer Name:

Example Industries
```

---

## 14.5 Multi-Line Value

```text
Address:

123 Example Road
Kozhikode
Kerala
India
```

Stop conditions:

```text
next known anchor
blank line
maximum lines
region boundary
```

---

## 14.6 Region-Based Extraction

Rules can target:

```text
Top Left
Top Right
Bottom Left
Bottom Right
Custom Rectangle
Relative-to-Anchor Rectangle
```

A custom rectangle should be stored relative to page dimensions where possible.

---

## 14.7 Relative Position Extraction

Example:

```text
Find "Invoice No"
Take text within 300px to the right
```

This is more robust than absolute coordinates.

---

## 14.8 Table Extraction

Architecture:

```text
Table Detector
    ↓
Row Detector
    ↓
Column Detector
    ↓
Header Matcher
    ↓
Cell OCR Mapping
    ↓
Typed Field Extraction
```

Keep table extraction as a specialized component rather than overloading normal field rules.

---

# 15. Pattern Learning System

## Objective

Given `N` files, infer likely:

```text
Document templates
Stable labels
Variable values
Field names
Data types
Patterns
Extraction strategies
Relative positions
Validation rules
```

---

# 16. Dataset Processing Pipeline

```text
Dataset Created
    ↓
Files Uploaded
    ↓
File Validation
    ↓
Job Queue
    ↓
OCR Processing
    ↓
OCR Results Persisted
    ↓
Document Feature Extraction
    ↓
Document Clustering
    ↓
Per-Cluster Alignment
    ↓
Stable / Variable Detection
    ↓
Pattern Generalization
    ↓
Proposal Generation
    ↓
Confidence Scoring
    ↓
Review Session
```

---

# 17. Document Fingerprinting

Each OCR result should produce a fingerprint containing:

```text
Recurring phrases
Token types
Line structures
Approximate positions
Word frequencies
Potential labels
Potential values
Page count
Layout signature
```

Example:

```json
{
  "labels": [
    "Invoice No",
    "Date",
    "Customer",
    "Total"
  ],
  "layout_signature": "...",
  "page_count": 1
}
```

Fingerprints are used to cluster documents before alignment.

---

# 18. Document Clustering

Do not assume all N documents belong to one template.

Example:

```text
100 Files

Cluster A: 72
Cluster B: 23
Outliers: 5
```

The system should create:

```text
Template A
Template B
Review Outliers
```

instead of producing one broken universal rule set.

Clustering signals:

- shared labels
- text similarity
- page structure
- relative word positions
- layout fingerprints

---

# 19. Stable and Variable Region Detection

Given:

```text
Invoice No: INV-2026-00101
Invoice No: INV-2026-00102
Invoice No: INV-2026-00103
```

The system detects:

```text
Stable:
Invoice No:
INV-
-2026-
```

Variable:

```text
00101
00102
00103
```

Then it generalizes the entire value structure.

The result becomes:

```yaml
anchor: Invoice No
pattern:
  type: regex
  value: INV-\d{4}-\d{5}
```

---

# 20. Pattern Generalization Engine

The engine must infer patterns conservatively.

Inputs:

```text
ABC-0001
ABC-0002
ABC-0003
```

Candidate:

```regex
ABC-\d{4}
```

Inputs:

```text
08/09/2026
10/09/2026
12/09/2026
```

Candidate:

```text
DD/MM/YYYY
```

Inputs:

```text
₹1,250.00
₹5,600.00
₹12,000.00
```

Candidate:

```text
currency(INR)
```

The engine should generate several candidates where appropriate:

```text
Candidate A — Most specific
Candidate B — More flexible
Candidate C — Type-based
```

The user chooses or edits one.

---

# 21. Field Proposal Engine

A proposal should contain:

```json
{
  "proposal_id": "proposal_123",
  "field_name": "invoice_number",
  "display_name": "Invoice Number",

  "anchor": "Invoice No",

  "strategy": "same_line_after_anchor",

  "pattern": {
    "type": "regex",
    "value": "INV-\\d{4}-\\d{5}"
  },

  "evidence": {
    "documents_matched": 19,
    "documents_total": 20
  },

  "confidence": {
    "anchor": 0.98,
    "pattern": 1.0,
    "position": 0.94,
    "overall": 0.96
  }
}
```

---

# 22. Confidence Architecture

Confidence must not be a single unexplained number.

Use components:

```text
OCR Confidence
+
Anchor Match Confidence
+
Pattern Match Confidence
+
Position Consistency
+
Dataset Frequency
+
Validation Success
=
Final Confidence
```

Example:

```text
Field: Invoice Number

OCR:                 93%
Anchor consistency:  98%
Pattern consistency: 100%
Position:            94%
Validation:          100%

Overall:             96%
```

---

# 23. Outlier Handling

Outliers must remain visible.

Example:

```text
Dataset: 50 Files

46 match Template A
3 match Template B
1 is an outlier
```

UI actions:

```text
[ Assign to Template A ]
[ Assign to Template B ]
[ Create New Template ]
[ Exclude from Learning ]
```

The system must never silently discard data.

---

# 24. Template Classification

After learning, incoming documents should optionally pass through:

```text
Document
    ↓
OCR
    ↓
Template Classifier
    ↓
Template A / B / Unknown
    ↓
Template-Specific Configuration
    ↓
Extraction
```

Classification can use:

```text
Required labels
Unique phrases
Page count
Layout fingerprint
Relative label positions
```

---

# 25. User Training Workflow

```text
CREATE DATASET

Name:
Invoice Samples

Files:
[Upload 50 files]

                ↓

RUN DISCOVERY

[ Start Pattern Learning ]

                ↓

REVIEW

Detected Template A
Files: 42

Fields:

Invoice Number       96%
Invoice Date         94%
Customer Name        90%
Total                98%

                ↓

FOR EACH FIELD

[ Approve ]
[ Edit ]
[ Reject ]

                ↓

GENERATE CONFIGURATION

Invoice Template A
Version 1 Draft

                ↓

TEST

Run against dataset

                ↓

PUBLISH
```

---

# 26. Configuration Lifecycle

```text
Draft
  ↓
Tested
  ↓
Review
  ↓
Published
  ↓
Active
  ↓
Deprecated
```

Versioning:

```text
Invoice Config

v1
v2
v3 ← Active
v4 ← Draft
```

Every extraction result records the exact configuration version used.

---

# 27. Configuration Testing

Each configuration should own tests.

Example:

```yaml
test_case:
  file: invoice_001.pdf

  expected:
    invoice_number: INV-2026-00128
    total: 12450.00
```

Validation modes:

```text
Exact
Regex
Numeric Tolerance
Date Equivalent
Required Presence
Optional Presence
```

---

# 28. Regression Testing

When a user fixes an extraction failure:

```text
Broken Document
      ↓
Corrected Rule
      ↓
Save as Regression Test
```

Future versions must be tested against it.

This creates a continuously improving configuration library.

---

# 29. Backend Architecture

Recommended technology:

```text
Python
FastAPI
Pydantic
SQLAlchemy
Alembic
PostgreSQL
Redis (production jobs/cache)
Tesseract
OpenCV
Pillow
```

---

# 30. Backend Module Architecture

```text
backend/app/

├── api/
│   ├── documents.py
│   ├── ocr.py
│   ├── configurations.py
│   ├── datasets.py
│   ├── discovery.py
│   ├── extraction.py
│   ├── results.py
│   └── tests.py
│
├── domain/
│   ├── documents/
│   ├── ocr/
│   ├── configurations/
│   ├── extraction/
│   ├── datasets/
│   └── discovery/
│
├── services/
│   ├── ocr/
│   │   ├── base.py
│   │   ├── tesseract.py
│   │   └── preprocessing.py
│   │
│   ├── extraction/
│   │   ├── engine.py
│   │   ├── anchors.py
│   │   ├── patterns.py
│   │   ├── regions.py
│   │   ├── candidates.py
│   │   └── resolver.py
│   │
│   ├── discovery/
│   │   ├── fingerprint.py
│   │   ├── clustering.py
│   │   ├── alignment.py
│   │   ├── stable_variable.py
│   │   ├── generalization.py
│   │   └── proposals.py
│   │
│   ├── normalization/
│   ├── validation/
│   └── export/
│
├── providers/
│   ├── ocr/
│   ├── storage/
│   └── queue/
│
├── repositories/
├── models/
├── schemas/
├── workers/
├── core/
└── main.py
```

---

# 31. Frontend Architecture

Recommended:

```text
React
TypeScript
Vite
TanStack Query
Tailwind CSS
Monaco Editor
```

Structure:

```text
frontend/src/

├── app/
├── pages/
│   ├── Dashboard
│   ├── Documents
│   ├── OCRPlayground
│   ├── Configurations
│   ├── RuleBuilder
│   ├── Datasets
│   ├── PatternTrainer
│   ├── Results
│   └── Tests
│
├── components/
│   ├── DocumentViewer
│   ├── OCRTextViewer
│   ├── BoundingBoxOverlay
│   ├── RuleBuilder
│   ├── PatternEditor
│   ├── ProposalReview
│   ├── ConfidencePanel
│   └── VersionDiff
│
├── features/
│   ├── documents/
│   ├── configurations/
│   ├── discovery/
│   ├── extraction/
│   └── testing/
│
├── api/
├── hooks/
├── types/
└── utils/
```

---

# 32. Frontend Component Interactions

```text
DocumentViewer
      │
      ├── BoundingBoxOverlay
      │
      ├── OCRSelection
      │       ↓
      │   RuleBuilder
      │
      └── ExtractionResultPanel
              ↓
          EvidencePanel
```

The frontend should consume API schemas, not duplicate extraction logic.

---

# 33. API Architecture

## Documents

```http
POST /api/documents
GET  /api/documents
GET  /api/documents/{id}
DELETE /api/documents/{id}
```

## OCR

```http
POST /api/ocr/jobs
GET  /api/ocr/jobs/{id}
GET  /api/ocr/results/{document_id}
```

## Configurations

```http
GET    /api/configurations
POST   /api/configurations
GET    /api/configurations/{id}
PUT    /api/configurations/{id}
DELETE /api/configurations/{id}

POST /api/configurations/{id}/test
POST /api/configurations/{id}/publish
POST /api/configurations/{id}/rollback
```

## Datasets

```http
POST /api/datasets
GET  /api/datasets
POST /api/datasets/{id}/documents
```

## Discovery

```http
POST /api/datasets/{id}/discover
GET  /api/discovery/runs/{id}
GET  /api/discovery/runs/{id}/proposals
```

## Proposals

```http
POST /api/proposals/{id}/approve
POST /api/proposals/{id}/reject
PUT  /api/proposals/{id}
```

## Extraction

```http
POST /api/extraction/jobs
GET  /api/extraction/jobs/{id}
GET  /api/extraction/results/{id}
```

---

# 34. Background Job Architecture

Long-running operations must not block HTTP requests.

Jobs:

```text
OCR Job
Extraction Job
Dataset Discovery Job
Bulk Reprocessing Job
Test Suite Job
Export Job
```

Architecture:

```text
API
 ↓
Job Record
 ↓
Queue
 ↓
Worker
 ↓
Progress Events
 ↓
Database/Object Storage
 ↓
WebUI Progress
```

---

# 35. Storage Architecture

## Relational Database

Stores:

```text
Users
Projects
Configurations
Versions
Rules
Datasets
Jobs
Metadata
Results
Tests
Audit Logs
```

## Object Storage

Stores:

```text
Uploaded documents
Page images
Optional preprocessed images
Large OCR artifacts
Exports
```

---

# 36. Database Model

```text
users
organizations
projects

documents
document_pages

ocr_jobs
ocr_results
ocr_pages
ocr_words

configurations
configuration_versions
fields
extraction_rules

datasets
dataset_documents

discovery_runs
document_clusters
pattern_proposals

extraction_jobs
extraction_results
extracted_values
extraction_evidence

test_suites
test_cases
test_runs

audit_logs
```

For an MVP, organization-level tables can be simplified.

---

# 37. Security and Permissions

Permissions:

```text
project.read
project.write

document.upload
document.read
document.delete

ocr.execute

configuration.read
configuration.write
configuration.publish

dataset.read
dataset.write
dataset.discover

results.read
results.export

admin.manage
```

Roles:

```text
Admin
Editor
Operator
Viewer
```

---

# 38. Regex Safety

User-defined regex is potentially dangerous.

The system should:

- limit pattern size
- use safe regex execution where possible
- apply timeouts
- reject known catastrophic structures
- limit search input size

A rule must never be able to hang a worker indefinitely.

---

# 39. File Security

Validate:

```text
File extension
MIME type
File signature where possible
Maximum size
Page count
Archive nesting
```

Uploaded files must not be executable.

Store using generated IDs rather than user filenames.

---

# 40. Extensibility Architecture

All major systems should expose contracts.

```python
class OCRProvider(Protocol):
    def process(
        self,
        document: Document,
        options: OCROptions
    ) -> OCRResult:
        ...
```

```python
class ExtractionStrategy(Protocol):
    def extract(
        self,
        context: ExtractionContext,
        rule: ExtractionRule
    ) -> list[Candidate]:
        ...
```

```python
class PatternDetector(Protocol):
    def analyze(
        self,
        documents: list[OCRResult]
    ) -> list[PatternProposal]:
        ...
```

```python
class Normalizer(Protocol):
    def normalize(
        self,
        value: str,
        config: NormalizationConfig
    ) -> NormalizedValue:
        ...
```

---

# 41. Plugin Capability Model

Plugins should declare what they provide.

Example:

```json
{
  "plugin": "table-extraction",
  "version": "1.0",
  "capabilities": [
    "extraction_strategy.table"
  ],
  "permissions": [
    "document.read"
  ]
}
```

Core code should discover registered capabilities rather than hard-coding plugin implementations.

---

# 42. Installation Architecture

The project should support:

```text
Development
Production
Docker
Local standalone
```

Recommended project root:

```text
ocr-platform/

├── backend/
├── frontend/
├── workers/
├── docker/
├── scripts/
├── configs/
├── examples/
├── tests/
├── docs/
├── docker-compose.yml
├── .env.example
└── README.md
```

---

# 43. Installation Scripts

## `scripts/install.sh`

Responsibilities:

```text
Check operating system
Check Python
Check Node.js
Check Tesseract
Install dependencies
Create environment file
Initialize local storage
```

## `scripts/setup-tesseract.sh`

Responsibilities:

```text
Install Tesseract
Verify executable
Install requested language packs
Verify OCR test
```

## `scripts/dev.sh`

Starts:

```text
Database
Backend
Frontend
Worker
```

---

# 44. Docker Architecture

Services:

```text
frontend
backend
worker
postgres
redis
object-storage (optional)
```

```text
Browser
   ↓
Frontend
   ↓
Backend API
   ├── PostgreSQL
   ├── Redis
   ├── Object Storage
   └── Worker
          ↓
      Tesseract
```

---

# 45. Implementation Phases

# Phase 0 — Foundation

Build:

```text
Project structure
Configuration schema
Domain models
Provider interfaces
Database setup
Authentication foundation
Logging
Docker foundation
```

Success criteria:

- project starts
- database migrates
- frontend connects to backend
- provider interfaces exist
- configuration validation works

---

# Phase 1 — OCR MVP

Build:

```text
Document upload
Image/PDF handling
Tesseract provider
OCR jobs
OCR text storage
Word confidence
Bounding boxes
OCR viewer
```

Success criteria:

```text
Upload file
    ↓
OCR
    ↓
See text
    ↓
See word positions/confidence
```

---

# Phase 2 — Configurable Extraction

Build:

```text
Fields
Anchors
Regex patterns
Same-line extraction
Next-line extraction
Basic normalization
Validation
Structured output
```

Success criteria:

A new field can be created without backend code changes.

---

# Phase 3 — Visual Rule Builder

Build:

```text
Click OCR text
Create anchor
Select value
Generate rule
Test rule
Save rule
Visual evidence
```

Success criteria:

A non-programmer can configure an extraction rule.

---

# Phase 4 — Advanced Extraction

Build:

```text
Multi-line extraction
Regions
Relative positioning
Fuzzy anchors
Priorities
Conflict resolution
Typed patterns
Template classification foundation
```

---

# Phase 5 — Dataset Pattern Learning

Build:

```text
Dataset creation
Bulk upload
OCR queue
Fingerprinting
Clustering
Alignment
Stable/variable analysis
Pattern generalization
Proposal generation
Confidence scoring
```

Success criteria:

Given N similar files, the platform proposes editable extraction rules.

---

# Phase 6 — Learning Review UI

Build:

```text
Cluster view
Outlier view
Proposal review
Approve
Edit
Reject
Generate configuration
Run tests
Publish
```

---

# Phase 7 — Production Hardening

Build:

```text
RBAC
Audit logs
Rate limits
Retry policies
Monitoring
Metrics
Safe regex execution
Object storage
Backup strategy
```

---

# Phase 8 — Advanced Intelligence

Optional:

```text
Table learning
AI-assisted field naming
AI-assisted rule suggestions
Semantic extraction
OCR correction learning
Active learning from corrections
Multiple OCR providers
Actual Tesseract model training
```

---

# 46. Testing Strategy

## Unit Tests

Test:

```text
Anchor matching
Pattern compilation
Pattern generalization
Normalization
Validation
Confidence scoring
Conflict resolution
Configuration validation
```

---

## Integration Tests

Test:

```text
Document
 ↓
Preprocess
 ↓
Tesseract
 ↓
OCR Result
 ↓
Extraction
 ↓
Validation
 ↓
Structured Result
```

---

## Dataset Tests

Run configurations against known datasets.

Track:

```text
Field success rate
Missing values
Incorrect values
Validation failures
Average confidence
```

---

## Regression Tests

Every production failure that gets fixed should become a permanent test.

---

# 47. Observability

Each job receives:

```text
job_id
request_id
document_id
config_version_id
```

Events:

```text
document_uploaded
ocr_started
ocr_completed
ocr_failed

config_loaded
rule_started
candidate_found
candidate_rejected
validation_failed
field_extracted

discovery_started
documents_clustered
pattern_generated
proposal_created

job_completed
job_failed
```

---

# 48. Caching

Cache OCR output because extraction rules may change frequently while the document does not.

Cache key:

```text
file_hash
+
ocr_provider
+
ocr_provider_version
+
language
+
ocr_options
+
preprocessing_profile
```

Rule changes should reuse OCR results whenever possible.

---

# 49. Data Flow Example

```text
invoice.pdf
    ↓
File Hash
    ↓
OCR Cache Check
    │
    ├── HIT → Existing OCR Result
    │
    └── MISS
          ↓
      Preprocess
          ↓
      Tesseract
          ↓
      OCR Result Store
          ↓
      Config v3
          ↓
      Field Rules
          ↓
      Candidates
          ↓
      Normalize
          ↓
      Validate
          ↓
      Resolve
          ↓
      Result + Evidence
```

---

# 50. Future OCR Model Training Subsystem

This must remain separate from normal pattern learning.

Architecture:

```text
Ground Truth Dataset
    ↓
Image / Text Pair Validation
    ↓
Training Dataset Builder
    ↓
Tesseract Training Pipeline
    ↓
Generated TrainedData
    ↓
OCR Provider Registration
    ↓
New OCR Profile
```

The UI can eventually expose:

```text
Upload training images
Provide ground truth
Validate samples
Train model
Track model version
Activate OCR profile
```

But this should not block the main product.

---

# 51. Recommended MVP Stack

```text
Frontend:
React + TypeScript + Vite

Backend:
Python + FastAPI

OCR:
Tesseract + pytesseract/direct CLI

Image Processing:
OpenCV + Pillow

Database:
PostgreSQL
(SQLite allowed for development)

Jobs:
Redis + worker system
(simple in-process jobs allowed for first prototype)

Storage:
Local filesystem for MVP
S3-compatible storage for production
```

---

# 52. Verification Checklist

The project should not move to the next phase until these are verified.

## OCR

- [ ] PNG works
- [ ] JPG works
- [ ] PDF works
- [ ] OCR text is stored
- [ ] confidence is stored
- [ ] bounding boxes are stored

## Rule Builder

- [ ] create field
- [ ] create anchor
- [ ] define pattern
- [ ] same-line extraction
- [ ] next-line extraction
- [ ] normalization
- [ ] validation
- [ ] live test

## Pattern Learning

- [ ] process N files
- [ ] detect similar documents
- [ ] cluster templates
- [ ] detect stable labels
- [ ] detect variable values
- [ ] infer candidate patterns
- [ ] calculate confidence
- [ ] review proposals
- [ ] generate configuration

## Production

- [ ] permissions
- [ ] safe regex
- [ ] upload validation
- [ ] job retry
- [ ] audit logging
- [ ] regression tests

---

# 53. Recommended Development Order

```text
1. Domain model
2. OCR provider abstraction
3. Tesseract implementation
4. OCR result persistence
5. Extraction engine
6. Configuration schema
7. Rule testing API
8. OCR Playground
9. Visual Rule Builder
10. Configuration versions
11. Dataset architecture
12. Document fingerprinting
13. Clustering
14. Alignment
15. Pattern generalization
16. Proposal review UI
17. Automated regression testing
18. Production hardening
```

Do not build pattern learning before the extraction configuration model is stable.

Pattern learning should generate configurations.

Therefore the configuration model is the foundation.

---

# 54. AI Coding Agent Execution Prompt

> Build a modular web application named `ocr-platform`.
>
> The system is a configurable OCR extraction platform using Tesseract as the default OCR provider.
>
> Follow this architecture specification exactly in principle:
>
> - OCR must be provider-based.
> - Tesseract must not be coupled directly to extraction logic.
> - Extraction behaviour must be configuration-driven.
> - Users must be able to create and edit extraction rules through a WebUI.
> - Configurations must be versioned.
> - OCR output must preserve text, positions, and confidence.
> - Every extraction result must preserve evidence.
>
> Implement the project in phases. Do not build all advanced features before the foundation is working.
>
> First implement:
>
> 1. Domain models and configuration schemas.
> 2. OCRProvider abstraction.
> 3. TesseractProvider.
> 4. Document upload and OCR jobs.
> 5. OCR result persistence.
> 6. Extraction engine supporting anchors and patterns.
> 7. Normalization and validation.
> 8. Configuration CRUD and versioning.
> 9. OCR Playground and rule testing.
>
> Then implement visual rule building:
>
> - Create fields.
> - Define anchors.
> - Define search direction and scope.
> - Define patterns through regex, templates, types, or examples.
> - Test rules against documents.
> - Show evidence and confidence.
>
> Then implement example-based pattern learning:
>
> 1. Allow datasets containing N files.
> 2. Process files asynchronously.
> 3. Fingerprint documents.
> 4. Cluster similar templates.
> 5. Align OCR structures within clusters.
> 6. Detect stable and variable regions.
> 7. Generalize variable values into conservative patterns.
> 8. Generate field/rule proposals.
> 9. Calculate explainable confidence.
> 10. Provide approve/edit/reject workflows.
> 11. Convert approved proposals into the same normal configuration schema used by manual rules.
>
> Do not make learned rules opaque.
>
> Do not require an LLM for core functionality.
>
> Keep skills, plugins, providers, components, and interactions clearly separated.
>
> Use strong typing, schema validation, structured logging, database migrations, tests, and modular interfaces.
>
> Provide:
>
> - backend
> - frontend
> - worker system
> - database migrations
> - Docker configuration
> - installation scripts
> - sample configurations
> - automated tests
> - README
>
> At the end of every implementation phase, verify the phase using executable tests before continuing.

---

# 55. Final Architecture

```text
                         USER WEBUI
                             │
                             ▼
                    CONFIGURATION CONTROL
                             │
               ┌─────────────┼─────────────┐
               ▼             ▼             ▼
           OCR CONFIG     RULE CONFIG    DATASETS
               │             │             │
               ▼             │             ▼
         OCR PROVIDER         │      PATTERN LEARNING
               │             │             │
               └──────┬──────┴──────┬──────┘
                      ▼             ▼
                   OCR RESULT   CONFIGURATION
                      │             │
                      └──────┬──────┘
                             ▼
                      EXTRACTION ENGINE
                             │
                             ▼
                    NORMALIZE + VALIDATE
                             │
                             ▼
                    RESULT + CONFIDENCE
                             │
                             ▼
                   EXPORT / API / STORAGE
```

The central product artifact is the **Extraction Configuration**.

Manual users create it directly.

Pattern learning generates it.

AI assistance may suggest it.

Tests verify it.

Versions preserve it.

The extraction engine executes it.

This architecture keeps the system fully modifiable through the WebUI while allowing increasingly advanced learning and automation without turning the platform into an opaque black box.
