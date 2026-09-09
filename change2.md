# tswebui — OCR + Website Builder + Public Document Portal

## System Design, Architecture, Implementation Plan, and AI Build Prompt

**Repository:** `Alex07lol/tswebui`  
**Primary Admin Application:** `tswebui`  
**OCR Engine:** Tesseract  
**Admin UI:** private control plane  
**Public UI:** separate consumer website on a different local port  
**Architecture:** shared backend/domain with isolated admin and public interfaces

---

# 1. Product Vision

Extend `tswebui` from an OCR/extraction platform into a complete document-intelligence and document-website platform.

The administrator should be able to:

1. Upload drawings, PDFs, scans, and other documents.
2. OCR them with Tesseract.
3. Teach the system what information to find.
4. Select fields directly on a PDF to teach position and structure.
5. Test those learned locators against the rest of the documents.
6. Build a public website from the extracted data.
7. Choose searchable fields and visible metadata.
8. Preview the website.
9. Publish it.
10. Run the public site locally on a different port.

A typical use case:

```text
Drawing PDFs
    ↓
Tesseract OCR
    ↓
Extract:
- Title
- Drawing Number
- Revision
- Project
- Date
    ↓
Website Builder
    ↓
Engineering Drawing Library
    ↓
Search "Pump Room Layout"
    ↓
Matching drawing
    ↓
PDF viewer
```

The important idea is that the website consumes the **existing OCR/extraction data**. It does not become a second OCR system.

---

# 2. Two Experiences, One Platform

```text
                         SHARED PLATFORM
                                │
                 ┌──────────────┴──────────────┐
                 │                             │
                 ▼                             ▼
           TSWebUI ADMIN                 PUBLIC WEBSITE
           private/admin                  consumer/public
                 │                             │
                 └──────────────┬──────────────┘
                                ▼
                         SHARED BACKEND
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                 ▼
             OCR            Extraction        Documents
              │                 │                 │
              └─────────────────┼─────────────────┘
                                ▼
                           PostgreSQL
```

The applications are separate at the UX and route/security boundaries, but they share the same domain and data layer.

---

# 3. Admin Application

TSWebUI remains the administrator's control plane.

Suggested navigation:

```text
Home
Documents
Scan & Inspect
Teach From Examples
Setups
Website Builder
Advanced Tools
```

Advanced Tools:

```text
Advanced Rule Editor
OCR Inspector
Pattern Analysis
Tests & Regression
Activity & System
```

The admin application requires authentication and RBAC.

Only users with the required administrative/editor permissions can access website authoring, OCR configuration, publishing, and system administration.

---

# 4. Public Website Application

The public site is a separate frontend.

Development:

```text
Admin:
http://localhost:5173

Public:
http://localhost:5174

Backend:
http://localhost:8000
```

Make all ports configurable through environment variables.

The public application must not reuse the admin application's navigation or expose admin functionality.

It should only consume explicitly published public data.

---

# 5. Security Boundary

Do not treat different ports as the security mechanism.

Port separation is for operational and UX separation.

Security must come from:

```text
Authentication
Authorization
Route separation
Published-data filtering
Private/public document flags
CORS configuration
Secure file streaming
```

Suggested route namespaces:

```text
/api/admin/*
/api/public/*
```

Admin routes require authenticated users and permissions.

Public routes return only published content.

Public routes must never expose:

```text
draft websites
draft configurations
training datasets
audit logs
internal extraction evidence
private documents
OCR execution endpoints
rule-editing endpoints
administrative metadata
```

---

# 6. Website Builder

Add a new skill:

```text
Build Document Website
```

The website builder should initially be a **document portal builder**, not a generic visual website builder.

The first target use cases are:

```text
Engineering Drawing Library
Technical Document Archive
Warranty Document Portal
Product Document Search
Inspection Records
Project Drawing Library
```

---

# 7. Website Domain Model

Add first-class objects:

```text
Website
WebsiteVersion
WebsitePage
WebsiteCollection
WebsiteSearchConfiguration
WebsiteFieldMapping
WebsiteDocumentView
WebsiteTheme
WebsitePublication
DocumentVisibility
```

Conceptual hierarchy:

```text
Website
├── Versions
├── Pages
├── Collections
├── Search Configuration
├── Field Mappings
├── Document View
├── Theme
└── Publication
```

A website references an existing OCR Setup.

Do not duplicate the OCR configuration.

---

# 8. Example Website

Suppose the OCR Setup has:

```text
title
drawing_number
revision
project
date
```

Create:

```text
Website:
Engineering Drawing Library
```

Search fields:

```text
Title
Drawing Number
Project
Revision
```

Document page:

```text
Title
Drawing Number
Revision
Project
Date
PDF
```

The generated public site might look like:

```text
Engineering Drawing Library

[ Search drawings... ]

-----------------------------------

Pump Room Layout

Drawing No: P-2048
Revision: C
Project: Plant Expansion

[ View Drawing ]
```

---

# 9. Simple Website Builder UX

The primary workflow should be:

```text
Create Website
      ↓
Name Website
      ↓
Choose Setup
      ↓
Choose Search Fields
      ↓
Choose Display Fields
      ↓
Configure Results
      ↓
Configure Document Page
      ↓
Choose Theme
      ↓
Preview
      ↓
Publish
```

A beginner should not need to understand:

```text
database schemas
API objects
ORM models
field IDs
SQL
```

Advanced options can expose deeper control.

---

# 10. Website Pages

Initial supported page types:

```text
Home
Search
Search Results
Document Detail
Collection
About
```

Recommended generated structure:

```text
Home
├── Header
├── Search
├── Featured Collections
└── Recent Documents

Search
├── Search box
├── Filters
└── Results

Document Detail
├── Title
├── Metadata
├── PDF Viewer
└── Related Documents
```

---

# 11. Search System

Search is based on **already extracted OCR data**.

Do not perform Tesseract OCR during a search request.

Pipeline:

```text
Document
 ↓
OCR
 ↓
Extraction
 ↓
Search Index
 ↓
Public Search
```

Search must support:

```text
full-text query
structured field filters
pagination
sorting
exact matches
partial matches
```

---

# 12. Search Provider

Create:

```python
class SearchProvider(Protocol):
    async def index_document(self, document, metadata):
        ...

    async def search(self, query, filters, page, page_size):
        ...

    async def remove_document(self, document_id):
        ...
```

Initial provider:

```text
PostgresSearchProvider
```

Future providers:

```text
MeilisearchProvider
OpenSearchProvider
ElasticsearchProvider
TypesenseProvider
```

The rest of the application must not depend directly on a particular search engine.

---

# 13. Search Ranking

Prefer results in this order:

```text
Exact title
↓
Title prefix
↓
Structured field match
↓
Drawing number match
↓
Full OCR text match
```

Example:

```text
Search:
Pump Room Layout
```

A document whose `title` exactly equals `Pump Room Layout` should outrank a document where the phrase merely appears somewhere inside OCR text.

---

# 14. Public Document Page

Each public document should support:

```text
Title
Metadata
Thumbnail
PDF Viewer
Download
Page navigation
```

Example route:

```text
/documents/<document-id>
```

Optional deep link:

```text
/documents/<document-id>?page=3
```

---

# 15. PDF Viewer

Use a reusable PDF viewer component/provider.

Initial functionality:

```text
Zoom
Fit width
Fit page
Page navigation
Page thumbnails
Search within PDF
Full screen
Download
```

Do not couple the website directly to a single PDF implementation.

Create:

```python
class PDFViewerProvider(Protocol):
    ...
```

Future providers can include specialized viewers.

---

# 16. Critical Feature — PDF Field Mapper

Add a specialized administrator tool:

```text
Teach From PDF
```

or:

```text
PDF Field Mapper
```

It must allow the administrator to open an OCR'd PDF and select:

```text
single word
text range
text block
rectangle/region
```

Example:

```text
┌──────────────────────────────────────┐
│ ENGINEERING DRAWING                  │
│                                      │
│       PUMP ROOM LAYOUT               │
│                                      │
│                                      │
│ Drawing No: P-2048                   │
│ Revision: C                          │
└──────────────────────────────────────┘
```

Admin selects:

```text
PUMP ROOM LAYOUT
```

Then:

```text
Use as Field

Field:
[ Title ▼ ]

[ Save ]
```

---

# 17. Selection Data to Capture

When the user selects an element, capture:

```text
selected text
OCR token IDs
page number
page dimensions
bounding box
nearby words
nearby lines
nearby labels
line structure
word order
OCR confidence
candidate text pattern
relative location
```

Use existing OCR word/bounding-box data instead of creating a parallel coordinate system.

---

# 18. Locator Concept

Introduce:

## Extraction Locator

A locator describes how to find a field again.

It must support:

```text
page strategy
relative region
anchor text
nearby words
text structure
expected value type
pattern
line relationship
position tolerance
template association
priority
```

Example:

```yaml
field_id: title

locator:
  page:
    mode: first

  region:
    x: 0.12
    y: 0.72
    width: 0.45
    height: 0.08

  anchor:
    candidates:
      - TITLE
      - DRAWING TITLE

  structure:
    same_line: true
    expected_type: text

  tolerance:
    x: 0.08
    y: 0.05
```

---

# 19. Do Not Depend Only on Absolute Coordinates

A locator must not simply say:

```text
x = 124
y = 842
```

because:

```text
DPI can change
PDF rendering size can change
page dimensions can change
templates can shift
```

Use relative coordinates plus structural information.

Preferred signals:

```text
relative position
anchor
nearby text
text structure
pattern
page
template
OCR confidence
```

---

# 20. Locator Matching

When extracting a future document:

```text
Candidate
 ↓
Anchor similarity
 ↓
Structural similarity
 ↓
Relative position
 ↓
Pattern validation
 ↓
OCR confidence
 ↓
Template compatibility
 ↓
Final score
```

If several candidates exist, rank them.

Never silently choose a low-confidence candidate when ambiguity is meaningful.

---

# 21. Multiple Locators Per Field

Support:

```text
Title
├── Locator A — Template A
├── Locator B — Template B
└── Locator C — Alternate title block
```

All locators can be enabled simultaneously.

The extraction system selects the best valid candidate.

---

# 22. Cross-Document Testing

After saving a locator:

```text
[ Test on Other Documents ]
```

Show:

```text
Document 01 ✓
Document 02 ✓
Document 03 ✓
Document 04 ✓
Document 05 ✗
```

Then:

```text
4 / 5 matched
```

Possible actions:

```text
Adjust Locator
Add Example
Create Alternate Locator
Assign to Another Template
```

This should be a major part of the mapper workflow.

---

# 23. Multi-Example Locator Learning

Allow users to select the same field on several documents.

Example:

```text
Document 1 → Title
Document 2 → Title
Document 3 → Title
```

The system should learn:

```text
stable region
stable page
common nearby labels
common structure
common relative position
```

Then generate a generalized locator.

This is different from simply averaging coordinates.

---

# 24. Structural Learning

When selecting:

```text
PUMP ROOM LAYOUT
```

the system should record not just the rectangle, but also context such as:

```text
near:
TITLE

same line:
yes

line position:
near title block

expected value:
text

number of words:
3

document template:
engineering-drawing-A
```

This lets the rule survive reasonable layout changes.

---

# 25. Mapper → Normal Extraction Rule

A PDF selection must become a normal extraction artifact.

Flow:

```text
PDF Selection
 ↓
Extraction Locator
 ↓
Extraction Rule
 ↓
Setup Field
 ↓
Normal Extraction Engine
```

Do not create a special "PDF-only" extraction engine.

This ensures all extraction methods remain compatible.

---

# 26. Website + Setup Integration

The website references an existing Setup.

Example:

```text
Setup:
Engineering Drawing Metadata

Fields:
title
drawing_number
revision
project
date
```

Website:

```text
Engineering Drawing Library
```

The website builder can automatically suggest:

```text
Search:
title
drawing_number
project
revision

Display:
title
drawing_number
revision
project
date
```

The admin can edit these mappings.

---

# 27. Collection System

Allow websites to organize documents into collections.

Example:

```text
Pump Room Drawings
Electrical Drawings
HVAC Drawings
Structural Drawings
```

A collection may be based on metadata filters:

```text
project = Plant Expansion
discipline = Mechanical
```

Collections should reference existing documents instead of duplicating them.

---

# 28. Website Field Mapping

Example:

```yaml
source:
  setup_id: engineering_drawings

search:
  fields:
    - title
    - drawing_number
    - project
    - revision

results:
  title: title
  metadata:
    - drawing_number
    - revision
    - project

document:
  title: title
  metadata:
    - drawing_number
    - revision
    - project
    - date
```

---

# 29. Website Theme

Initial theme system:

```text
Logo
Primary color
Background
Typography
Header
Footer
Card style
Button style
```

Provide several document-oriented presets.

Do not build an unrestricted visual editor in the first version.

The architecture should allow one later.

---

# 30. Website Preview

Admin must be able to:

```text
Edit
Preview
Publish
```

Preview should use the same public renderer used by production.

Example:

```text
http://localhost:5174/preview/<site-id>
```

Draft data may be used only through authenticated/preview-specific access.

---

# 31. Publication Model

Website lifecycle:

```text
Draft
↓
Preview
↓
Published
↓
Unpublished
↓
Archived
```

Publishing should create a stable published version/snapshot where appropriate.

Only the published version should be visible publicly.

---

# 32. Public Document Visibility

Every document should have an explicit visibility state:

```text
Private
Public
Unpublished
```

A document being OCR'd does not make it public.

A document being associated with a website does not automatically make it public.

Publication must be explicit.

---

# 33. Public File Streaming

Never expose filesystem/object-storage paths directly.

Use:

```text
/api/public/sites/{slug}/documents/{id}/file
```

Check:

```text
site is published
document belongs to site
document is public
file exists
```

Then stream the PDF.

---

# 34. Website Versioning

Website versions are separate from OCR Setup versions.

Example:

```text
Setup v3
Website v7
```

This allows:

```text
OCR changes
```

and:

```text
website design/search changes
```

to evolve independently.

---

# 35. Dependency Awareness

If a website references a field:

```text
title
```

and an admin tries to remove/rename it, show:

```text
This field is used by:

Engineering Drawing Library
Project Archive

Changing it may affect these websites.
```

Do not silently break published websites.

---

# 36. Search Index Updating

When extracted metadata changes:

```text
Document reprocessed
 ↓
Extracted fields updated
 ↓
Search index updated
 ↓
Website reflects update
```

Under snapshot publication:

```text
Document reprocessed
 ↓
Draft/public data changes
 ↓
Admin republishes if required
```

Choose and document one clear publication strategy.

---

# 37. Public Frontend Structure

```text
public-site/
├── src/
│   ├── app/
│   ├── pages/
│   │   ├── Home
│   │   ├── Search
│   │   ├── Document
│   │   └── Collection
│   ├── components/
│   │   ├── SiteHeader
│   │   ├── SearchBox
│   │   ├── FilterPanel
│   │   ├── ResultCard
│   │   ├── DocumentMetadata
│   │   └── PDFViewer
│   ├── api/
│   ├── types/
│   └── styles/
└── package.json
```

---

# 38. Admin Frontend Additions

Preserve the current admin frontend.

Add:

```text
WebsiteBuilderView
WebsitePreviewView
PDFFieldMapperView
LocatorEditor
LocatorTestPanel
WebsiteFieldMapper
SearchConfigurator
PublicationPanel
```

The existing advanced OCR/rule components remain available.

---

# 39. Backend Additions

Add services:

```text
WebsiteService
WebsiteVersionService
WebsitePublicationService
WebsiteSearchService
WebsiteDocumentService

LocatorService
LocatorMatcher
LocatorScorer
LocatorLearningService

PublicSiteService
PublicDocumentService
DocumentVisibilityService
SearchIndexer
SearchRanker
```

---

# 40. Providers

Add provider abstractions:

```text
SearchProvider
PDFViewerProvider
PublicationProvider
WebsiteThemeProvider
WebsiteDataProvider
```

Existing OCR provider architecture remains unchanged.

---

# 41. Skills

Add:

```text
Build Document Website
Configure Website Search
Map PDF Field
Learn Field Location
Preview Website
Publish Website
Manage Public Documents
```

---

# 42. Plugins

Future plugins:

```text
CAD Drawing Viewer
GIS / Map Viewer
Image Gallery
External Search
SSO
Analytics
Cloud Storage
QR Code Generator
External Database
Document Comments
```

---

# 43. Database Additions

Add models/tables approximately equivalent to:

```text
websites
website_versions
website_pages
website_collections
website_search_fields
website_document_views
website_publications
document_visibility

extraction_locators
locator_examples
locator_versions

search_index_metadata
```

Use foreign keys to existing:

```text
documents
setups
setup_fields
configuration_versions
extraction_results
```

Avoid duplicating the actual OCR/extraction data.

---

# 44. API

## Admin

```http
POST   /api/admin/websites
GET    /api/admin/websites
GET    /api/admin/websites/{id}
PUT    /api/admin/websites/{id}
DELETE /api/admin/websites/{id}

POST   /api/admin/websites/{id}/preview
POST   /api/admin/websites/{id}/publish
POST   /api/admin/websites/{id}/unpublish

PUT    /api/admin/websites/{id}/search
PUT    /api/admin/websites/{id}/theme
PUT    /api/admin/websites/{id}/document-view
```

## Locator

```http
POST /api/admin/locators
GET  /api/admin/locators/{id}
PUT  /api/admin/locators/{id}
POST /api/admin/locators/{id}/test
POST /api/admin/locators/{id}/examples
```

## Public

```http
GET /api/public/sites/{slug}
GET /api/public/sites/{slug}/search
GET /api/public/sites/{slug}/collections
GET /api/public/sites/{slug}/documents/{id}
GET /api/public/sites/{slug}/documents/{id}/file
```

---

# 45. Local Development

Provide one command such as:

```bash
bash scripts/dev-all.sh
```

which starts:

```text
Backend     :8000
Admin UI    :5173
Public UI   :5174
Worker      as required
Database    as required
```

Also provide individual commands:

```bash
npm run dev:admin
npm run dev:public
```

Document everything in README.

---

# 46. Docker

Recommended services:

```text
backend
admin
public
worker
postgres
redis
```

The public and admin frontends should have separate containers/builds.

---

# 47. Authentication and Roles

Roles:

```text
ADMIN
EDITOR
OCR_OPERATOR
WEBSITE_EDITOR
VIEWER
PUBLIC
```

At minimum:

```text
ADMIN:
everything

EDITOR:
OCR/configuration/content editing

WEBSITE_EDITOR:
website creation/editing/publishing

OCR_OPERATOR:
document processing

VIEWER:
read-only admin access

PUBLIC:
published public site only
```

Sensitive system settings and audit logs remain admin-only.

---

# 48. Audit Events

Record:

```text
website.created
website.updated
website.previewed
website.published
website.unpublished

locator.created
locator.updated
locator.tested

document.visibility_changed
website.field_mapping_changed
```

Integrate with the existing audit system.

---

# 49. Performance Rules

Never execute:

```text
Tesseract
full PDF analysis
full extraction
```

during a public search request.

Precompute:

```text
OCR
extraction
search metadata
thumbnails
```

Cache:

```text
published website configuration
document metadata
thumbnails
```

---

# 50. Thumbnail Pipeline

Recommended:

```text
PDF uploaded
 ↓
Page rendering
 ↓
Thumbnail generated
 ↓
Stored
```

Search results can then show document previews cheaply.

---

# 51. Error Handling

Admin:

```text
Could not find the Title field in 3 documents.

[Show Documents]
[Adjust Locator]
[Add Example]
```

Public:

```text
No matching drawings were found.
```

Never expose backend stack traces to public users.

---

# 52. Observability

Add job/request IDs to:

```text
OCR
extraction
locator testing
search
publication
```

Log:

```text
locator.created
locator.match_failed
website.published
public.search
public.document_view
public.pdf_download
```

---

# 53. Testing

## Backend tests

```text
website CRUD
website versioning
publication
public data filtering
document visibility
locator creation
locator matching
locator scoring
cross-document locator testing
search
search indexing
```

## Frontend tests

```text
website builder
PDF field mapper
locator editor
preview
public search
document page
PDF viewer
```

## End-to-end test

The flagship test should be:

```text
Upload Drawing PDF
 ↓
Run OCR
 ↓
Open PDF Mapper
 ↓
Select drawing title
 ↓
Create Title locator
 ↓
Test locator against other drawings
 ↓
Save Setup
 ↓
Create Website
 ↓
Choose Title as search field
 ↓
Publish
 ↓
Open localhost:5174
 ↓
Search title
 ↓
Open result
 ↓
View PDF
```

This proves the entire architecture works together.

---

# 54. Implementation Phases

## Phase 17 — Website Domain Foundation

Build:

```text
Website models
Website versions
Publication
Visibility
Pages
Collections
Database migrations
Admin/public route separation
```

Verify:

```text
draft website exists
published website exists
public API returns published website only
```

---

## Phase 18 — Public Document Website

Build:

```text
React public frontend
Home
Search
Results
Document detail
PDF viewer
responsive layout
```

Verify:

```text
localhost:5174
```

works independently from the admin application.

---

## Phase 19 — Website Builder

Build:

```text
Create Website
Select Setup
Select search fields
Select display fields
Configure results
Configure document page
Theme
Preview
Publish
```

---

## Phase 20 — PDF Field Mapper

Build:

```text
OCR-aware PDF viewer
text selection
region selection
field assignment
locator creation
locator testing
```

---

## Phase 21 — Locator Learning

Build:

```text
multiple examples
structural analysis
relative positioning
anchor discovery
template association
alternate locators
confidence scoring
```

---

## Phase 22 — Search

Build:

```text
indexing
structured filters
full-text search
ranking
pagination
reindexing
```

---

## Phase 23 — Publication and Security Hardening

Build:

```text
published snapshots
RBAC
public/private validation
dependency checks
secure PDF streaming
audit events
```

---

## Phase 24 — Automated Website Generation

Eventually allow:

```text
Teach From Examples
 ↓
Discover fields
 ↓
Create Setup
 ↓
Create Website
 ↓
Automatically suggest search fields
 ↓
Automatically generate document pages
 ↓
Preview
 ↓
Publish
```

This should become the easiest complete workflow.

---

# 55. Recommended Final User Experience

Administrator:

```text
Upload 50 drawings
        ↓
Teach From Examples
        ↓
System finds:

Title
Drawing Number
Revision
Project
Date
        ↓
Open PDF
        ↓
Click/select Title
        ↓
"Use this structure for other drawings?"
        ↓
YES
        ↓
System tests all drawings
        ↓
Create Setup
        ↓
Create Document Website
        ↓
Select Title + Drawing Number + Project as search fields
        ↓
Preview
        ↓
Publish
```

End user:

```text
Engineering Drawing Library

[ Search drawings... ]

"Pump Room Layout"

        ↓

Pump Room Layout
Drawing No: P-2048
Revision: C
Project: Plant Expansion

[ View Drawing ]

        ↓

PDF Viewer
```

The administrator teaches the system once; the public website turns the resulting structured information into a useful searchable document experience.

---

# 56. Final Architecture Principle

The new system must preserve this chain:

```text
DOCUMENT
   ↓
TESSERACT OCR
   ↓
OCR TOKENS + POSITIONS + CONFIDENCE
   ↓
EXTRACTION SETUP
   ↓
LOCATORS + PATTERNS + STRUCTURE
   ↓
STRUCTURED METADATA
   ↓
SEARCH INDEX
   ↓
WEBSITE CONFIGURATION
   ↓
PUBLIC WEBSITE
   ↓
SEARCH
   ↓
DOCUMENT
   ↓
PDF VIEWER
```

The PDF Field Mapper is not a separate OCR feature.

It is a visual way of creating better extraction locators.

The Website Builder is not a separate database.

It is a presentation/search layer over the existing extracted document intelligence.

---

# 57. AI Coding Agent Execution Prompt

> Extend the existing `Alex07lol/tswebui` repository into a combined OCR, document-intelligence, and document-website platform.
>
> Do not rebuild the current OCR architecture from scratch.
>
> Preserve the existing:
>
> - Tesseract provider architecture
> - OCR result structures
> - bounding boxes
> - confidence data
> - extraction engine
> - Setup/Teach architecture
> - pattern learning
> - configurations
> - validation
> - normalization
> - regression testing
> - RBAC
> - audit logging
> - advanced rule editor
>
> The new system has two experiences:
>
> 1. Private TSWebUI admin application.
> 2. Separate public consumer website.
>
> The admin application runs on one frontend port and the public website runs on a different frontend port during development.
>
> Recommended defaults:
>
> Admin: `5173`
> Public: `5174`
> Backend: `8000`
>
> Make ports configurable.
>
> Do not simply hide admin navigation from the public site.
>
> Implement a true public/admin boundary using:
>
> `/api/admin/*`
>
> and:
>
> `/api/public/*`
>
> Admin routes require authentication and appropriate RBAC permissions.
>
> Public routes return only explicitly published public data.
>
> Never expose through public routes:
>
> - draft configurations
> - training datasets
> - audit logs
> - internal extraction evidence
> - private documents
> - OCR execution endpoints
> - rule-editing APIs
> - administrative metadata
>
> ---
>
> # WEBSITE BUILDER
>
> Add a new Website Builder into the admin application.
>
> Do not build a generic visual page editor initially.
>
> Build a document-centric website builder.
>
> The first workflow is:
>
> Create Website
>
> →
>
> Name Website
>
> →
>
> Choose existing Setup
>
> →
>
> Select fields searchable by the public user
>
> →
>
> Select fields shown on results
>
> →
>
> Select metadata shown on document pages
>
> →
>
> Configure document/PDF viewer
>
> →
>
> Configure theme
>
> →
>
> Preview
>
> →
>
> Publish
>
> Create backend models for:
>
> Website
> WebsiteVersion
> WebsitePage
> WebsiteCollection
> WebsiteSearchConfiguration
> WebsiteFieldMapping
> WebsiteDocumentView
> WebsiteTheme
> WebsitePublication
> DocumentVisibility
>
> Do not duplicate OCR/extraction data.
>
> Website fields should reference existing Setup fields.
>
> ---
>
> # PUBLIC WEBSITE
>
> Build a separate React/TypeScript frontend named `public-site`.
>
> It must have its own application shell and navigation.
>
> Initial pages:
>
> Home
> Search
> Search Results
> Document Detail
> Collection
>
> The public application must be capable of:
>
> searching titles and other extracted fields
> showing result cards
> opening documents
> viewing PDFs
> downloading PDFs when permitted
>
> The public site should be responsive and accessible.
>
> ---
>
> # SEARCH
>
> Add a SearchProvider interface.
>
> Initial implementation should use PostgreSQL search/structured queries.
>
> Do not call Tesseract during search requests.
>
> Index already-extracted fields and OCR metadata.
>
> Search ranking should prefer:
>
> 1. exact title
> 2. title prefix
> 3. structured field match
> 4. drawing number match
> 5. full OCR text match
>
> Support:
>
> - text query
> - structured filters
> - pagination
> - sorting
>
> ---
>
> # PDF VIEWER
>
> Add a reusable PDF viewer component/provider.
>
> Initial features:
>
> - page navigation
> - zoom
> - fit width
> - fit page
> - thumbnails
> - search within PDF
> - full screen
> - download
>
> Do not couple public rendering tightly to an implementation-specific PDF library.
>
> ---
>
> # PDF FIELD MAPPER
>
> This is a critical feature.
>
> Add an administrator workflow called:
>
> `Teach From PDF`
>
> The admin can open a PDF with OCR data and select:
>
> - a word
> - a text range
> - a text block
> - a rectangular region
>
> When selected, the system must capture:
>
> - selected OCR text
> - OCR token IDs
> - page number
> - page dimensions
> - bounding box
> - nearby words
> - nearby lines
> - nearby labels
> - line structure
> - word order
> - OCR confidence
> - relative position
> - candidate pattern
>
> Then ask the admin:
>
> `What field is this?`
>
> Example:
>
> `Title`
>
> Create a persistent Extraction Locator.
>
> ---
>
> # LOCATOR MODEL
>
> Implement an Extraction Locator as a first-class domain object.
>
> It must support:
>
> - relative page position
> - relative bounding box
> - anchor text
> - nearby words
> - structure
> - expected value type
> - pattern
> - line relationship
> - position tolerance
> - template association
> - priority
>
> Do not use absolute pixel coordinates as the only matching strategy.
>
> Prefer:
>
> - relative coordinates
> - anchor similarity
> - structural similarity
> - position
> - pattern validation
> - OCR confidence
> - template compatibility
>
> Multiple locators must be allowed for the same field.
>
> Example:
>
> `title`
>
> can have:
>
> `locator_title_template_a`
> `locator_title_template_b`
> `locator_title_alternate`
>
> ---
>
> # LOCATOR TESTING
>
> After creating a locator, allow:
>
> `Test on Other Documents`
>
> Show document-by-document results.
>
> Example:
>
> Document 01 ✓
> Document 02 ✓
> Document 03 ✓
> Document 04 ✗
>
> Show:
>
> `3 / 4 matched`
>
> Allow:
>
> - adjust locator
> - add examples
> - create alternate locator
> - associate with another template
>
> ---
>
> # MULTI-EXAMPLE LEARNING
>
> Allow the admin to select the same field on multiple documents.
>
> Use the examples to learn:
>
> - stable region
> - relative position
> - common anchors
> - structure
> - template compatibility
>
> Generate a generalized locator.
>
> Do not simply average coordinates.
>
> ---
>
> # EXTRACTION INTEGRATION
>
> A locator created using the PDF mapper must become a normal extraction artifact.
>
> Required pipeline:
>
> PDF selection
>
> →
>
> Extraction Locator
>
> →
>
> Extraction Rule
>
> →
>
> Setup Field
>
> →
>
> Existing Extraction Engine
>
> Do not create a parallel PDF-specific extraction engine.
>
> ---
>
> # WEBSITE MAPPING
>
> A Website should reference an existing Setup.
>
> Example:
>
> Setup:
> `Engineering Drawing Metadata`
>
> Fields:
>
> - title
> - drawing_number
> - revision
> - project
> - date
>
> Website:
> `Engineering Drawing Library`
>
> Search:
>
> - title
> - drawing_number
> - project
> - revision
>
> Result card:
>
> - title
> - drawing_number
> - revision
>
> Document page:
>
> - title
> - drawing_number
> - revision
> - project
> - date
> - PDF
>
> ---
>
> # PUBLIC DATA SECURITY
>
> Every document must have explicit visibility.
>
> Possible states:
>
> - private
> - public
> - unpublished
>
> A document being uploaded or OCR'd must not make it public.
>
> Public PDF streaming must use an authorization-aware endpoint such as:
>
> `/api/public/sites/{slug}/documents/{id}/file`
>
> Check:
>
> - website is published
> - document belongs to the website
> - document is public
> - file exists
>
> Then stream the PDF.
>
> Never expose raw storage paths.
>
> ---
>
> # VERSIONING
>
> Website versions and OCR Setup versions are independent.
>
> Example:
>
> Setup v3
>
> Website v7
>
> Keep dependency tracking so changes to Setup fields warn about affected websites.
>
> ---
>
> # PREVIEW AND PUBLICATION
>
> Support:
>
> Draft
> Preview
> Published
> Unpublished
> Archived
>
> Preview should use the same public rendering components as the production public site.
>
> Validate:
>
> - referenced Setup exists
> - referenced fields exist
> - public documents are valid
> - search mappings are valid
> - document-view mappings are valid
> - website slug is valid
> - theme configuration is valid
>
> Do not publish if validation fails.
>
> ---
>
> # PROJECT STRUCTURE
>
> Preserve the existing project structure where practical.
>
> Add:
>
> `frontend/admin`
>
> `public-site`
>
> Backend namespaces:
>
> `api/admin`
> `api/public`
> `services/websites`
> `services/locators`
> `services/search`
> `services/publication`
> `providers/search`
> `providers/pdf_viewer`
> `providers/publication`
>
> ---
>
> # LOCAL DEVELOPMENT
>
> Add/update:
>
> `scripts/dev-all.sh`
> `scripts/dev-admin.sh`
> `scripts/dev-public.sh`
>
> The all-in-one command should start:
>
> Backend
> Admin
> Public
> Worker if required
>
> Update `.env.example` and README.
>
> ---
>
> # TESTING
>
> Add tests for:
>
> - website CRUD
> - website versioning
> - publication
> - public filtering
> - document visibility
> - locator creation
> - locator matching
> - locator scoring
> - multi-example locator learning
> - search
> - search indexing
> - secure PDF access
>
> Add frontend tests for:
>
> - website builder
> - PDF field mapper
> - locator editor
> - website preview
> - public search
> - document detail
>
> Add a complete E2E test:
>
> Upload drawing
>
> →
>
> OCR
>
> →
>
> select title in PDF
>
> →
>
> create locator
>
> →
>
> test against other documents
>
> →
>
> create Setup
>
> →
>
> create Website
>
> →
>
> configure title as search field
>
> →
>
> publish
>
> →
>
> open public site
>
> →
>
> search title
>
> →
>
> open result
>
> →
>
> view PDF
>
> ---
>
> # UX PRINCIPLE
>
> The administrator should be able to teach the system visually:
>
> `Click what this thing is`
>
> rather than manually building every coordinate and regex rule.
>
> For example:
>
> `Select "PUMP ROOM LAYOUT"`
>
> →
>
> `Field: Title`
>
> →
>
> `Use this structure`
>
> →
>
> test across drawings.
>
> Advanced rule configuration must remain available, but it must be an extension of the simple visual teaching workflow.
>
> ---
>
> # FINAL PRODUCT PRINCIPLE
>
> Build around this chain:
>
> `PDF → Select → Learn Structure → Extract → Index → Search → View PDF`
>
> TSWebUI is the private control plane where the administrator teaches and publishes.
>
> The public site is the consumer-facing document portal.
>
> Both must use the same underlying OCR and extraction data.
>
> Implement incrementally.
>
> Verify every phase before moving to the next.
>
> Do not create parallel systems that duplicate OCR, extraction, or document storage.
