# TSWebUI — Universal Data-Driven Website & Application Builder

## System Design, Architecture, Required Changes, Implementation Plan, and AI Build Prompt

**Repository:** `Alex07lol/tswebui`  
**Primary product:** TSWebUI OCR + extraction + data + website/application platform  
**OCR engine:** Tesseract  
**Admin UI:** private control plane  
**Public UI:** separate consumer-facing web application  
**Backend:** shared domain/API layer with strict admin/public authorization boundaries  
**Initial local ports:** Admin `5173`, Public Site `5174`, Backend `8000`  
**Initial database:** PostgreSQL  

---

# 1. Executive Summary

TSWebUI should no longer treat the Website Builder as a specialized “drawing search portal builder.” It should become a **general-purpose, data-driven website and lightweight application builder** whose first-class data sources happen to be produced by OCR and document extraction.

The system must support many domains:

- engineering drawings
- warranties
- product catalogs
- invoices
- certificates
- receipts
- inspection records
- manuals
- asset registers
- archives
- equipment databases
- dashboards
- searchable document libraries
- custom business portals

The core design principle is:

```text
Documents / Images / OCR / Manual Data / Future External Data
                         ↓
                  Unified Data Model
                         ↓
              Universal Website Builder
                         ↓
        Pages + Components + Data Bindings
                         ↓
        Actions + Conditions + Computations
                         ↓
                Preview / Publication
                         ↓
                Public Website/App
```

A drawing portal is therefore just one template built on the same universal system.

A warranty lookup site, for example, should use exactly the same underlying builder primitives:

```text
Data Source: Warranty Records
    ↓
Home Page
    ├── Heading
    ├── Serial Number Input
    └── Search Action

Results Page
    └── Warranty Result Card
         ├── Product Name ← bound field
         ├── Serial Number ← bound field
         ├── Customer ← bound field
         ├── Expiry Date ← bound field
         └── Status ← computed/conditional field
```

The builder must be powerful enough for developers and advanced users while remaining approachable for non-technical users.

---

# 2. Product Vision

## 2.1 What TSWebUI becomes

TSWebUI becomes a pipeline with four major layers:

```text
1. INGEST
   Files → OCR → OCR tokens

2. UNDERSTAND
   OCR tokens → extraction fields → locators → structured records

3. MODEL
   Structured records → reusable data sources / schemas / relationships

4. BUILD
   Data sources → website/app → publication → public users
```

The Website Builder must not know whether a record came from:

- Tesseract
- a PDF
- an image
- manual entry
- an imported dataset
- a future API/database integration

It only consumes a typed data model.

## 2.2 Product statement

> **Build websites and lightweight data-driven applications from information TSWebUI already understands.**

Users can start from a template, build from scratch, or customize an existing generated site.

---

# 3. Design Principles

## 3.1 Universal instead of domain-specific

Do not hard-code concepts such as `drawing_number`, `project`, or `revision` into the Website Builder.

These may be fields in one setup, but they must not be required by the platform.

Examples:

```text
Engineering:
- drawing_number
- revision
- project

Warranty:
- serial_number
- product_name
- customer
- purchase_date
- expiry_date

Invoice:
- invoice_number
- customer
- total
- invoice_date
- status
```

The builder operates on generic fields and types.

## 3.2 OCR is an ingestion mechanism, not the public application's search engine

Search must never invoke Tesseract for every public query.

Correct:

```text
OCR once
   ↓
Extract once
   ↓
Store structured data
   ↓
Index
   ↓
Search indexed data
```

Incorrect:

```text
Public search
   ↓
Open PDF
   ↓
Run OCR
   ↓
Search OCR text
```

## 3.3 Published state is isolated from drafts

A published site must be based on an immutable publication snapshot.

Draft changes must never silently modify the live public site.

## 3.4 Security is enforced by authorization, not ports

`5173` versus `5174` is not a security boundary.

The backend must enforce:

- authentication
- authorization
- resource ownership
- public visibility
- website publication state
- document membership
- file access rules

## 3.5 Non-technical users should not need code

The default builder experience is visual and configuration-driven.

Advanced users can use expressions and extensions, but arbitrary JavaScript execution must not be the default path.

## 3.6 Everything should be composable

A site template is just a collection of:

- pages
- component trees
- data bindings
- actions
- conditions
- theme tokens
- route definitions

This prevents a future explosion of special-case site builders.

---

# 4. Target Architecture

```text
                              ┌─────────────────────┐
                              │   SOURCE MATERIAL   │
                              │ PDF / Image / File  │
                              └──────────┬──────────┘
                                         ↓
                              ┌─────────────────────┐
                              │    OCR / TESSERACT  │
                              └──────────┬──────────┘
                                         ↓
                              ┌─────────────────────┐
                              │     OCR TOKENS      │
                              │ text + bbox + page  │
                              └──────────┬──────────┘
                                         ↓
                              ┌─────────────────────┐
                              │ EXTRACTION / SETUPS │
                              └──────────┬──────────┘
                                         ↓
                              ┌─────────────────────┐
                              │      LOCATORS       │
                              │ pattern + anchors   │
                              │ relative position   │
                              └──────────┬──────────┘
                                         ↓
                              ┌─────────────────────┐
                              │ STRUCTURED RECORDS  │
                              │ typed field values  │
                              └──────────┬──────────┘
                                         ↓
                              ┌─────────────────────┐
                              │      DATA MODEL     │
                              │ sources / schemas   │
                              │ records / relations │
                              └──────────┬──────────┘
                                         ↓
              ┌──────────────────────────┴──────────────────────────┐
              │                                                     │
              ▼                                                     ▼
      ┌──────────────────┐                                 ┌──────────────────┐
      │  SEARCH / QUERY  │                                 │ WEBSITE BUILDER  │
      └────────┬─────────┘                                 └────────┬─────────┘
               │                                                    │
               │                              ┌─────────────────────┼─────────────────────┐
               │                              ↓                     ↓                     ↓
               │                          PAGES                COMPONENTS             ACTIONS
               │                              │                     │                     │
               │                              └──────────────┬──────┴─────────────────────┘
               │                                             ↓
               │                                    DATA BINDINGS / LOGIC
               │                                             ↓
               └─────────────────────────────────────────────┤
                                                             ↓
                                                       PUBLIC RUNTIME
                                                             ↓
                                                        END USERS
```

---

# 5. Domain Boundaries

The implementation should clearly separate the following concepts.

## 5.1 Skills

Skills represent user-facing workflows or capabilities.

Initial Website Builder skills:

```text
Build Website
Start From Template
Create Custom Page
Add Component
Bind Component To Data
Configure Search
Configure Filters
Configure Actions
Configure Conditions
Create Computed Field
Preview Website
Manage Public Documents
Publish Website
Unpublish Website
Manage Website Versions
```

OCR/extraction skills remain separate:

```text
Scan Document
Teach From Examples
Map PDF Field
Create Extraction Rule
Test Locator
Review Extraction
Correct Extraction
```

## 5.2 Plugins

Plugins extend the platform safely.

Potential future plugins:

```text
Chart Plugin
3D Model Viewer Plugin
Map Plugin
Advanced Table Plugin
External API Connector
CRM Connector
Analytics Plugin
Authentication Provider
Storage Provider
Search Provider
```

Plugins must declare:

- name
- version
- capabilities
- inputs
- outputs
- permissions
- settings
- compatible runtime version

## 5.3 Providers

Providers abstract infrastructure or implementation choices.

Required provider interfaces:

```text
SearchProvider
StorageProvider
PublicationProvider
WebsiteThemeProvider
DataProvider
PDFViewerProvider
AuthenticationProvider
```

Initial implementations can remain local/PostgreSQL-backed.

## 5.4 Components

Components are reusable visual/runtime building blocks.

Components should be independent from any particular business domain.

## 5.5 Interactions

Interactions describe what happens when users act.

Examples:

```text
click
submit
search
navigate
filter
sort
open
close
select
load
```

---

# 6. Universal Data Layer

The Website Builder must consume a generic data model.

## 6.1 DataSource

Recommended model:

```text
DataSource
├── id
├── name
├── slug
├── description
├── source_type
├── schema_id
├── status
├── created_by
├── created_at
└── updated_at
```

`source_type` examples:

```text
ocr_records
manual
imported
computed
external_api (future)
database (future)
```

## 6.2 DataSchema

```text
DataSchema
├── id
├── name
├── version
└── fields[]
```

Field schema:

```text
DataField
├── id
├── key
├── label
├── type
├── required
├── searchable
├── sortable
├── filterable
├── displayable
├── format
└── validation
```

Types should support at least:

```text
string
long_text
integer
decimal
boolean
date
datetime
email
url
file
image
document
json
```

Potential later types:

```text
currency
percentage
location
rich_text
reference
multi_reference
```

## 6.3 DataRecord

A normalized record should reference a data source and retain provenance.

```text
DataRecord
├── id
├── data_source_id
├── source_document_id (nullable)
├── values_json
├── status
├── created_at
└── updated_at
```

The record may represent:

- one OCR’d document
- one extracted product
- one warranty
- one invoice
- one certificate
- one manually entered item

## 6.4 Relationships

Support generic references:

```text
DataRelation
├── id
├── source_record_id
├── source_field_id
├── target_record_id
├── target_field_id
└── relation_type
```

Examples:

```text
Warranty → Product
Invoice → Customer
Certificate → Employee
Drawing → Project
Asset → Maintenance Record
```

This is important for moving from simple document search to genuine applications.

---

# 7. Connecting OCR/Setups to the Universal Data Model

The existing Setup/Field architecture remains the canonical extraction configuration.

The flow becomes:

```text
Setup
  ↓
Setup Field / Extraction Field
  ↓
Locator / Pattern / Extraction Rule
  ↓
Extracted Value
  ↓
DataRecord
```

A setup should be able to expose a `DataSource` schema automatically.

Example:

```text
Setup: Warranty Documents

Fields:
    serial_number → string
    product_name  → string
    customer_name → string
    purchase_date → date
    expiry_date   → date
```

The Website Builder receives:

```text
Warranty Documents
    ├── Serial Number
    ├── Product Name
    ├── Customer Name
    ├── Purchase Date
    └── Expiry Date
```

It does not receive hard-coded drawing-specific fields.

---

# 8. PDF Visual Field Mapping

The existing visual PDF mapper remains important, but its role is clarified.

It is an **extraction authoring tool**, not a website-specific feature.

Correct architecture:

```text
PDF selection
      ↓
OCR token inspection
      ↓
Locator analysis
      ↓
ExtractionLocator
      ↓
Compiled extraction rule
      ↓
Setup Field
      ↓
Structured DataRecord
      ↓
Website Builder
```

## 8.1 Selection should create fields when needed

Current limitation:

```text
field must already exist
```

Required UX:

```text
Select text/region
      ↓
“What should this be?”
      ↓
Existing field / New field
      ↓
Create field + locator
```

Example:

```text
Selected OCR text:
“ABC-123456”

What should this be?

○ Existing field
  Serial Number

○ Create new field
  [ Serial Number ]
  Type: String
```

## 8.2 Locator data

A locator should capture more than pixel coordinates.

Minimum learned information:

```text
field_id
setup_id
source_document_id
page_number
selected_text
ocr_token_ids
bounding_box
page_width
page_height
relative_x
relative_y
relative_width
relative_height
nearby_text
anchor_candidates
line_index
column_index
text_pattern
expected_type
ocr_confidence
orientation
region_signature
template_label
```

A locator matcher should combine several signals.

```text
Locator Match Score =
    position similarity
  + anchor similarity
  + nearby structure similarity
  + pattern validation
  + OCR confidence
  + template compatibility
```

Absolute pixel coordinates alone are insufficient.

## 8.3 Multiple locators per field

A field may have multiple valid templates/layouts.

```text
Field: Serial Number
    ├── Locator A → Template A
    ├── Locator B → Template B
    └── Locator C → Template C
```

---

# 9. Extraction Locator as Canonical Source

`ExtractionLocator` is the higher-level learned representation.

The compiled `ExtractionRule` is derived from it.

Correct relationship:

```text
ExtractionLocator
      ↓ compile
ExtractionRule
      ↓ execute
Extraction result
```

Do not create a second independent source of truth.

If a locator is updated:

```text
Update locator
    ↓
recompile
    ↓
replace/update derived rule
    ↓
mark affected records for re-extraction when necessary
```

Recommended domain structure:

```text
Setup
  └── Field
       └── Locator
            └── LocatorExample[]
```

Optional:

```text
Template
  └── Locator
```

---

# 10. Universal Website Model

The Website object must become a container for an application definition rather than a document-search configuration only.

Recommended high-level model:

```text
Website
├── id
├── name
├── slug
├── description
├── status
├── created_by
├── created_at
└── published_version_id
```

The website references one or more data sources.

```text
WebsiteDataSource
├── website_id
├── data_source_id
├── alias
├── default_source
└── permissions
```

---

# 11. Website Versioning

## 11.1 Required lifecycle

```text
draft
   ↓
preview
   ↓
published
   ↓
unpublished / archived
```

Published versions are immutable.

## 11.2 Correct model

```text
Website
   │
   ├── Draft Version
   │       ├── editable
   │       └── previewable
   │
   ├── Published Version
   │       └── immutable snapshot
   │
   └── Archived Versions
```

`published_version_id` on `Website` should point to the immutable live version.

Editing the website after publication must create or modify a draft version only.

Publishing promotes the draft into a new immutable snapshot.

Previous published version becomes archived.

## 11.3 Never expose draft as public fallback

Public API behavior must be:

```text
Find published website
    ↓
Find published_version_id
    ↓
Return exact published snapshot
```

Never:

```text
No published version
    ↓
Use latest draft
```

If no published site/version exists, return an unavailable/not-published response.

---

# 12. Website Pages

A website consists of pages.

```text
Website
 ├── Home
 ├── Search
 ├── Results
 ├── Detail
 ├── Collections
 ├── About
 └── Custom Pages
```

Pages must be configurable.

Recommended model:

```text
WebsitePage
├── id
├── website_version_id
├── route
├── title
├── page_type
├── layout_config_json
├── component_tree_json
└── settings_json
```

`component_tree_json` represents the visual hierarchy.

Example:

```json
{
  "type": "page",
  "children": [
    {
      "type": "container",
      "children": [
        {
          "type": "heading",
          "props": {"text": "Warranty Lookup"}
        },
        {
          "type": "search-input",
          "bindings": {
            "queryField": "serial_number"
          }
        }
      ]
    }
  ]
}
```

---

# 13. Component System

Components are generic.

## 13.1 Core layout components

```text
Page
Container
Section
Row
Column
Grid
Stack
Spacer
Divider
```

## 13.2 Content components

```text
Heading
Text
RichText
Image
Icon
Button
Link
Video
```

## 13.3 Data components

```text
DataText
DataCard
DataList
DataGrid
DataTable
DataDetail
DataBadge
DataImage
DataFile
```

## 13.4 Search components

```text
SearchInput
SearchResults
Filter
FilterGroup
SortControl
Pagination
ResultCount
```

## 13.5 Document components

```text
PDFViewer
DocumentPreview
DocumentDownload
Thumbnail
DocumentMetadata
```

## 13.6 Visualization components

```text
Metric
Chart
Progress
StatisticCard
Timeline
```

## 13.7 Interaction components

```text
Form
Input
Select
DatePicker
Checkbox
Radio
Modal
Tabs
Accordion
```

## 13.8 Advanced extensibility components

```text
CustomComponent
PluginComponent
Embed
```

---

# 14. Component Configuration

Every component should have a predictable model:

```text
Component
├── type
├── id
├── props
├── style
├── responsive
├── bindings
├── events
├── visibility
└── children
```

Example:

```json
{
  "type": "data-card",
  "id": "product-card",
  "bindings": {
    "title": "product_name",
    "subtitle": "serial_number",
    "meta": "expiry_date"
  },
  "events": {
    "click": [
      {
        "action": "navigate",
        "target": "/products/{id}"
      }
    ]
  }
}
```

---

# 15. Data Binding System

This is one of the most important additions.

A component must be able to consume data without domain-specific code.

## 15.1 Binding model

```text
Component Property
       ↓
Binding
       ↓
Data Source
       ↓
Record
       ↓
Field
```

Example:

```text
Text Component
     ↓
Bind to field
     ↓
Warranty Records → Product Name
```

## 15.2 Binding types

Support:

```text
static
field
record
collection
computed
context
query
```

## 15.3 Binding context

A rendered component should have a context such as:

```text
site
page
current_record
current_collection
search_query
user
route_params
```

Example:

```text
current_record.serial_number
current_record.product_name
route_params.id
search_query
```

The runtime should resolve these through a controlled binding engine.

---

# 16. Search as a First-Class Service

Search must be generalized.

Do not hard-code field names such as:

```text
<title>
<drawing_number>
<drawing_no>
<invoice_number>
```

Instead, the Website Builder explicitly configures which fields are searchable.

Example:

```text
Search Configuration

Data Source: Warranty Records

Searchable fields:
[x] Serial Number
[x] Product Name
[ ] Customer Name
[ ] Purchase Date
```

The Website Builder should load these fields dynamically from the chosen data source/schema.

## 16.1 SearchProvider

Interface:

```text
search(query, filters, sort, pagination, data_source)
```

Initial provider:

```text
DatabaseSearchProvider
```

Future providers:

```text
MeilisearchProvider
OpenSearchProvider
ElasticsearchProvider
```

## 16.2 Service boundary

Public routes should not instantiate a provider directly.

Correct:

```text
Public API
   ↓
PublicSiteService
   ↓
WebsiteSearchService
   ↓
SearchProvider
```

This maintains provider abstraction.

---

# 17. Collections

Collections must be functional, not cosmetic.

Current `filter_query_json` concept should become a real query definition.

Example:

```text
Collection: Active Warranties

Filter:
    expiry_date >= today
```

Or:

```text
Collection: Electrical Drawings

Filter:
    discipline = "Electrical"
```

A collection becomes:

```text
WebsiteCollection
├── website_version_id
├── name
├── slug
├── description
├── data_source_id
├── filter_definition
├── sort_definition
└── display_definition
```

The public runtime must actually apply the filter.

---

# 18. Actions

Actions allow the website to behave like an application.

## 18.1 Core actions

```text
navigate
search
filter
sort
open_document
download_file
submit_form
set_state
show_modal
hide_modal
refresh
```

## 18.2 Example

```text
Serial Number Input
      ↓
Search Button
      ↓
search(action)
      ↓
Warranty Data Source
      ↓
Results
      ↓
Navigate to result
```

## 18.3 Action model

```text
Action
├── type
├── input_mapping
├── target
├── condition
└── options
```

Actions must be validated and allowlisted.

---

# 19. Conditions and Conditional Visibility

Users should be able to construct rules visually.

Example:

```text
Show Warranty Status
WHEN
    expiry_date is after today
```

Rule model:

```text
Condition
├── left_operand
├── operator
└── right_operand
```

Operators:

```text
equals
not_equals
contains
starts_with
ends_with
greater_than
less_than
greater_or_equal
less_or_equal
is_empty
is_not_empty
in
not_in
```

Compound rules:

```text
AND
OR
NOT
```

The expression engine must be deterministic, sandboxed, and non-Turing-complete where possible.

---

# 20. Computed Fields

Users should be able to derive useful values from extracted data.

Example:

```text
expiry_date - today
```

or:

```text
full_name = first_name + " " + last_name
```

or:

```text
total = quantity * unit_price
```

Computed fields must use a controlled expression language.

Never execute arbitrary server-side Python or arbitrary browser JavaScript from a public website configuration.

---

# 21. Forms

The Website Builder should eventually support forms.

Example:

```text
Warranty Claim

Name
Email
Serial Number
Problem Description
Submit
```

Form submission can later connect to:

```text
internal workflow
webhook
email provider
data record
external API
```

MVP may support a basic form system with a secure backend action.

---

# 22. Customization

“Custom stuff” must be supported without making the normal builder difficult.

Use three progressive levels.

## Level 1 — Visual configuration

```text
Drag
Drop
Select
Configure
Bind
Preview
```

## Level 2 — Expressions

Controlled expressions such as:

```text
{{ current_record.product_name }}
{{ current_record.expiry_date }}
{{ route_params.id }}
```

and safe conditional expressions through the rule engine.

## Level 3 — Developer extensions

Developers can install/register custom components or plugins.

Example:

```text
3D CAD Viewer
Interactive Map
Specialized Chart
Company-specific Widget
```

Plugins must run inside a capability/permission model.

---

# 23. Plugin Architecture

Plugin manifest concept:

```json
{
  "name": "cad-viewer",
  "version": "1.0.0",
  "components": [
    "cad-viewer"
  ],
  "permissions": [
    "read:public-data"
  ]
}
```

Plugins must declare the data they can read/write.

Potential permission examples:

```text
read:public-data
read:website-context
network:external-api
write:form-submissions
```

Do not grant arbitrary filesystem/database access to public components.

---

# 24. Theme System

The theme system should be generic and token-based.

```text
Theme
├── colors
├── typography
├── spacing
├── radii
├── shadows
├── breakpoints
├── component_defaults
└── custom_css (optional/sanitized)
```

Starter themes:

```text
Clean
Modern
Corporate
Technical
Minimal
Dark
```

Themes should apply to components through tokens rather than duplicated style declarations.

---

# 25. Website Templates

Templates are data-driven starting points.

Initial templates:

```text
Blank Website
Search Portal
Document Library
Warranty Lookup
Product Catalog
Invoice Portal
Certificate Verification
Data Dashboard
Knowledge Archive
Media Gallery
```

A template should contain:

```text
pages
component trees
bindings
actions
conditions
theme
search configuration
```

It must not contain a separate custom implementation for each domain.

---

# 26. Example: Engineering Drawing Portal

```text
Data Source
Engineering Drawings

Fields
- Drawing Number
- Title
- Revision
- Project
- Discipline
- Date
- PDF
```

Site:

```text
Home
 ├── Heading
 ├── Search Input
 └── Featured Drawings

Search
 ├── Search Input
 ├── Discipline Filter
 └── Result Grid

Detail
 ├── Drawing Title
 ├── Drawing Number
 ├── Revision
 ├── Project
 └── PDF Viewer
```

---

# 27. Example: Warranty Website

Same builder, different data source.

```text
Data Source
Warranty Records

Fields
- Serial Number
- Product Name
- Customer Name
- Purchase Date
- Expiry Date
- Product Image
- Warranty Document
```

Home:

```text
“Check Your Warranty”

[ Serial Number ] [ Search ]
```

Result:

```text
Product: Model X
Serial: ABC-123456
Purchase Date: 12 Jan 2026
Expiry: 12 Jan 2028

Warranty Status
ACTIVE
```

The status can be computed:

```text
expiry_date >= today
```

---

# 28. Example: Certificate Verification

Data source:

```text
Certificate
- Certificate Number
- Holder Name
- Issue Date
- Expiry Date
- Certificate Type
- Issuing Organization
- Certificate PDF
```

Public flow:

```text
Enter certificate number
       ↓
Search
       ↓
Verify record
       ↓
Show certificate details
       ↓
Open PDF
```

---

# 29. Example: Dashboard

The same data source can be used without a document viewer.

```text
Dashboard

┌──────────────┐ ┌──────────────┐
│ Active       │ │ Expiring     │
│ Warranties   │ │ Soon         │
└──────────────┘ └──────────────┘

               Chart

             Data Table
```

This demonstrates why “document portal” cannot remain the core Website Builder abstraction.

---

# 30. Public Runtime

The public-site application should be a generic renderer for published site definitions.

Suggested architecture:

```text
public-site/
 ├── runtime/
 │   ├── PageRenderer
 │   ├── ComponentRenderer
 │   ├── BindingResolver
 │   ├── ActionExecutor
 │   ├── ConditionEvaluator
 │   ├── DataClient
 │   └── RouteResolver
 ├── pages/
 ├── components/
 ├── theme/
 └── app/
```

The runtime should render configuration rather than contain hard-coded domain pages.

---

# 31. Public Routing

Use actual URL routing, not React state alone.

Recommended route model:

```text
/{site-slug}
/{site-slug}/search
/{site-slug}/documents/:id
/{site-slug}/collections/:collection-slug
/{site-slug}/pages/:page-slug
```

Alternatively, if a deployment hosts one site per public runtime:

```text
/
/search
/items/:id
/collections/:slug
/pages/:page-slug
```

The important requirement is that pages are deep-linkable.

Refresh must not destroy navigation state.

---

# 32. Public Site Configuration

The public frontend must never call `/api/admin/*`.

Current problematic behavior:

```text
public-site
   ↓
/api/admin/websites
```

Required behavior:

```text
public-site
   ↓
/api/public/sites/{slug}
```

Public site discovery, where needed, should use a safe public endpoint or an environment-provided slug.

Example environment setting:

```text
VITE_PUBLIC_SITE_SLUG=my-site
```

---

# 33. Admin API Security

Current `/api/admin/*` naming is not enough.

All administrative routers must use authenticated authorization dependencies.

Recommended pattern:

```python
admin_router = APIRouter(
    dependencies=[Depends(require_admin)]
)
```

Permission-level checks should be added where appropriate.

Example permissions:

```text
website:read
website:create
website:edit
website:publish
website:unpublish
locator:read
locator:create
locator:edit
document:read
document:publish
system:admin
```

---

# 34. Audit Legacy Routes

The existing backend contains legacy routes outside `/api/admin`, including document, OCR, configuration, extraction, audit, setup, teach, training, and related endpoints.

Every endpoint must be classified:

```text
Public
Authenticated user
Admin/editor
System admin
```

Do not assume an old route is safe because the new admin routers are protected.

A migration should progressively move sensitive endpoints under explicit admin namespaces or attach equivalent authorization dependencies.

---

# 35. Document Publication Model

Publishing a website must **never** automatically expose all documents.

Current dangerous behavior conceptually:

```text
Publish website
   ↓
index all ready documents
   ↓
make_public=True
   ↓
all ready documents become public
```

This must be removed.

## 35.1 Required explicit relationship

Introduce:

```text
WebsiteDocument
├── id
├── website_id
├── document_id
├── included
├── published
├── created_at
├── updated_at
└── published_at
```

Or use a separate membership + publication model.

The key distinction is:

```text
Included in site
        ≠
Publicly visible
```

## 35.2 Publication flow

```text
Admin selects documents
     ↓
WebsiteDocument.included = true
     ↓
Preview
     ↓
Publication snapshot
     ↓
Only explicitly included + public documents are exposed
```

---

# 36. Visibility Model

Document visibility should be explicit.

Suggested states:

```text
private
internal
included
published
archived
```

The exact implementation may use flags plus lifecycle state, but semantics must remain clear.

Public API should enforce:

```text
website is published
AND
published version exists
AND
website document is included
AND
document is published/public
```

---

# 37. File Access Security

Never expose filesystem paths directly.

Public file access should be through authorization-aware endpoints such as:

```text
GET /api/public/sites/{slug}/documents/{id}/file
```

The backend validates all publication and membership rules before streaming the file.

Thumbnails follow the same principle.

---

# 38. Public API

Suggested endpoints:

```text
GET    /api/public/sites/{slug}
GET    /api/public/sites/{slug}/pages/{page_slug}
GET    /api/public/sites/{slug}/search
GET    /api/public/sites/{slug}/collections/{collection_slug}
GET    /api/public/sites/{slug}/records/{record_id}
GET    /api/public/sites/{slug}/documents/{document_id}
GET    /api/public/sites/{slug}/documents/{document_id}/file
GET    /api/public/sites/{slug}/documents/{document_id}/thumbnail
POST   /api/public/sites/{slug}/actions/{action_id}
```

Public responses must be restricted to the published snapshot.

---

# 39. Admin Website API

Suggested endpoints:

```text
GET    /api/admin/websites
POST   /api/admin/websites
GET    /api/admin/websites/{id}
PATCH  /api/admin/websites/{id}
DELETE /api/admin/websites/{id}
POST   /api/admin/websites/{id}/versions
POST   /api/admin/websites/{id}/preview
POST   /api/admin/websites/{id}/publish
POST   /api/admin/websites/{id}/unpublish
GET    /api/admin/websites/{id}/data-sources
POST   /api/admin/websites/{id}/data-sources
GET    /api/admin/websites/{id}/pages
POST   /api/admin/websites/{id}/pages
PATCH  /api/admin/pages/{id}
DELETE /api/admin/pages/{id}
POST   /api/admin/websites/{id}/documents
PATCH  /api/admin/websites/{id}/documents/{document_id}
```

All require authentication/authorization.

---

# 40. Website Builder UX

The visual builder should feel like a product builder, not a JSON editor.

Recommended workspace:

```text
┌─────────────┬──────────────────────────┬───────────────────┐
│ Components  │        Canvas            │ Properties        │
│             │                          │                   │
│ Heading     │   ┌──────────────────┐   │ Text              │
│ Text        │   │                  │   │ Font              │
│ Button      │   │     WEBSITE      │   │ Size              │
│ Image       │   │                  │   │ Alignment         │
│ Data Card   │   │                  │   │ Binding           │
│ Search      │   │                  │   │ Condition         │
│ Table       │   │                  │   │ Actions           │
│ Chart       │   └──────────────────┘   │                   │
└─────────────┴──────────────────────────┴───────────────────┘
```

Top bar:

```text
Website Name
[Pages]
[Data]
[Preview]
[Publish]
```

---

# 41. Beginner Mode

For non-technical users, hide unnecessary complexity.

User sees:

```text
Add Section
Add Search
Add Card
Choose Data
Choose Field
Set Style
```

Advanced settings remain expandable.

Example:

```text
Product Name

Display:
● Text

Data:
Product Catalog → Product Name

Style:
[Advanced]
```

---

# 42. Advanced Mode

Advanced users can inspect:

```text
Component tree
Bindings
Expressions
Actions
Route configuration
Responsive settings
Plugin configuration
```

The advanced UI should never be required for basic publishing.

---

# 43. Automatic Site Generation

TSWebUI should be able to generate an initial site from a data source.

Input:

```text
Data Source: Warranty Records
```

System infers:

```text
Likely title field
Likely identifier field
Searchable fields
Display fields
Date fields
Image fields
Document/file fields
```

Then proposes:

```text
Suggested Site:

Home
Search
Result
Detail
```

The user can accept and customize it.

This is a **generator**, not a hard-coded site type.

---

# 44. Field Role Classification

A data field can have optional semantic roles.

Example:

```text
Field: Serial Number
Role:
[x] Identifier
[x] Searchable
[ ] Title
```

Another:

```text
Field: Product Name
Role:
[x] Title
[x] Searchable
[x] Displayable
```

Roles help the builder suggest layouts, but they must remain configurable.

---

# 45. Search Configuration UX

Never ask users to type:

```text
title,drawing_number,project,date
```

Instead:

```text
Choose what users can search

[x] Product Name
[x] Serial Number
[ ] Customer
[ ] Purchase Date
```

Filter configuration uses field selectors too.

---

# 46. Responsive Design

The runtime must support:

```text
mobile
 tablet
 desktop
```

Components can have responsive overrides:

```text
columns:
  desktop = 4
  tablet = 2
  mobile = 1
```

---

# 47. Accessibility

Generated public sites should support:

- semantic HTML
- keyboard navigation
- visible focus states
- accessible names
- appropriate labels
- sufficient contrast
- responsive text
- screen-reader compatibility
- accessible form validation

Accessibility should be a runtime/component responsibility instead of relying on every user to know WCAG concepts.

---

# 48. Public Runtime Error Handling

The public site must not expose the admin control plane.

Current behavior such as:

```text
Open Admin Control Plane (:5173)
```

should be removed from public-facing production/error states.

Use a neutral message:

```text
This portal is currently unavailable.
```

Developer diagnostics belong in development-only tooling/logs.

---

# 49. Routing and Deployment

Development defaults:

```text
Admin frontend:  http://localhost:5173
Public frontend: http://localhost:5174
Backend:         http://localhost:8000
```

These must be configurable.

Production should support deployment behind one domain or multiple domains.

Example:

```text
admin.example.com
portal.example.com
api.example.com
```

Do not encode localhost URLs into application logic.

---

# 50. Search/Data Provider Abstraction

Required abstractions:

```text
DataProvider
SearchProvider
StorageProvider
PublicationProvider
```

Initial implementations:

```text
PostgresDataProvider
DatabaseSearchProvider
LocalStorageProvider
DatabasePublicationProvider
```

Potential future implementations:

```text
ExternalDatabaseProvider
S3StorageProvider
MeilisearchProvider
OpenSearchProvider
CloudPublicationProvider
```

---

# 51. Website Builder State Model

Editor state should distinguish:

```text
saved
unsaved
previewing
publishing
published
```

Autosave can be implemented later, but the state model should anticipate it.

---

# 52. Draft Editing Rules

Rule:

```text
published version = immutable
```

Therefore:

```text
Edit published site
      ↓
Create/activate draft
      ↓
Modify draft
      ↓
Preview draft
      ↓
Publish draft
      ↓
New immutable published snapshot
```

Never mutate the active published version directly.

---

# 53. Publication Snapshot Contents

A published snapshot should contain or reference immutable definitions for:

```text
website metadata
pages
routes
component trees
bindings
search configuration
collection definitions
actions
conditions
computed fields
theme
data source mappings
public document membership
publication metadata
```

The snapshot should be self-contained enough that later draft modifications cannot affect it.

---

# 54. Publication Process

Recommended sequence:

```text
1. Validate draft
2. Validate bindings
3. Validate references
4. Validate routes
5. Validate actions
6. Validate conditions
7. Validate public data permissions
8. Resolve included documents/records
9. Create immutable publication snapshot
10. Update website.published_version_id
11. Index/reindex only published data
12. Mark previous publication archived
```

If validation fails, do not publish.

---

# 55. Validation Engine

The builder needs pre-publish validation.

Examples:

```text
ERROR:
Data binding references deleted field “serial_number”.

ERROR:
Page route “/search” conflicts with another page.

ERROR:
Public component requests a private data source.

WARNING:
Image component has no accessible description.

WARNING:
Search has no searchable fields.
```

Publishing should be blocked on errors.

---

# 56. Public Data Security Model

A data source may contain fields that should not be public.

Example:

```text
Warranty Record

PUBLIC:
- Serial Number
- Product Name
- Expiry Date

PRIVATE:
- Internal Cost
- Staff Notes
- Internal Ticket Number
```

Field-level publication permissions should be supported.

```text
DataField.public_readable = true/false
```

Public components must not be able to bind to private fields.

---

# 57. Record-Level Security

Some records may be private while others are public.

Example:

```text
Document A → public
Document B → private
Document C → internal
```

Search results, details, thumbnails, downloads, and any related action must apply the same visibility checks.

Do not secure only the search endpoint while leaving a document-detail endpoint open.

---

# 58. Website Membership

Explicitly model which records/documents belong to a website.

Example:

```text
Website A
 ├── Record 1 ✓
 ├── Record 2 ✓
 └── Record 3 ✗

Website B
 ├── Record 1 ✗
 └── Record 3 ✓
```

This supports multiple websites over the same underlying data source.

---

# 59. Reusable Data Across Websites

A single extraction/data source can power multiple sites.

Example:

```text
Warranty Data
    ├── Customer Portal
    ├── Internal Dashboard
    └── Public Product Lookup
```

The websites can have different field visibility and presentation while sharing the same normalized data.

---

# 60. Existing Repository Alignment

The existing repository already contains many pieces of the intended architecture:

```text
ocr-platform/backend
ocr-platform/frontend
ocr-platform/public-site
```

Existing useful pieces include:

```text
admin/locators.py
admin/websites.py
public/sites.py
services/locators/
services/search/
services/teach/
models/locator.py
models/website.py
frontend/PDFFieldMapperView.tsx
frontend/WebsiteBuilderView.tsx
public-site/src/App.tsx
```

The implementation should extend these rather than rebuilding the OCR system from scratch.

---

# 61. Required Changes to Existing Implementation

## P0 — Security and data exposure

### A. Protect admin APIs

Add explicit authentication/RBAC dependencies to:

```text
/api/admin/*
```

and audit all legacy sensitive routes outside this namespace.

### B. Remove public-site → admin API calls

Replace any:

```text
/api/admin/*
```

usage in `public-site` with public APIs only.

### C. Stop publishing all ready documents

Remove behavior equivalent to:

```python
index_all_documents_for_website(..., make_public=True)
```

unless constrained to explicit WebsiteDocument membership.

### D. Separate website membership from public visibility

Introduce `WebsiteDocument` or equivalent explicit relationship.

### E. Remove public draft fallback

Public API must only serve an immutable published version.

### F. Stop mutating published versions

Editing after publication must target a draft.

---

# 62. Required Website Builder Refactor

Replace drawing-specific defaults such as:

```text
title
drawing_number
project
revision
date
```

with dynamic schema-driven configuration.

Remove UI flows that require comma-separated field strings.

Instead:

```text
Load selected Data Source
        ↓
Load schema fields
        ↓
Display field picker
        ↓
User selects fields
```

---

# 63. Required PDF Mapper Refactor

The visual mapper should support:

```text
Select text/region
      ↓
Create new field or map existing field
      ↓
Learn locator
      ↓
Save example
      ↓
Test against other documents
      ↓
Accept/reject
```

The field-mapper UI should make the locator's learned reasoning visible at a beginner-friendly level, for example:

```text
Matched because:
✓ Same relative position
✓ Found anchor “Serial Number”
✓ Pattern matches
✓ OCR confidence high
```

Advanced users may inspect detailed scores and bounding boxes.

---

# 64. Required Website Builder UI Refactor

The current Website Builder UI is too specialized.

Refactor into:

```text
Website Builder

├── Pages
├── Data
├── Components
├── Design
├── Actions
├── Rules
├── Preview
└── Publish
```

## Data panel

```text
Sources
  ├── Warranty Records
  ├── Products
  └── Documents

Fields
  ├── Serial Number
  ├── Product Name
  └── Expiry Date
```

## Components panel

```text
Layout
Content
Data
Search
Forms
Documents
Charts
Advanced
```

## Properties panel

Dynamic based on selected component.

---

# 65. Required Public-Site Refactor

Replace the current fixed page-switching approach with a generic route-aware runtime.

Current state-driven page switching:

```text
currentTab
selectedDocId
```

should become a router-backed system.

The public application should resolve:

```text
route
   ↓
published site definition
   ↓
page
   ↓
component tree
   ↓
bindings/actions
```

---

# 66. Required Collection Refactor

Collections must become actual queryable datasets.

Implement:

```text
collection filter
collection sort
collection pagination
collection display
```

Public collection route must use the same search/query infrastructure as normal search.

---

# 67. Required Search Refactor

Search configuration must be schema driven.

Remove hard-coded special cases where possible.

For compatibility during migration, legacy field-name heuristics can remain in a clearly isolated compatibility layer, but the Website Builder must use explicit field IDs/keys from the schema.

---

# 68. Required Service Layer Refactor

Public endpoints should not directly instantiate database providers.

Required service chain:

```text
API
 ↓
Service
 ↓
Provider
 ↓
Repository/DB
```

Example:

```text
GET /api/public/sites/demo/search
        ↓
PublicSearchService
        ↓
WebsiteSearchService
        ↓
SearchProvider
        ↓
PostgreSQL
```

---

# 69. Suggested Database Model

```text
users
 └── websites.created_by

websites
 ├── website_versions
 ├── website_data_sources
 ├── website_pages
 ├── website_collections
 ├── website_documents
 └── website_publications

website_versions
 └── immutable published snapshots

data_sources
 └── data_schemas
       └── data_fields

 data_sources
 └── data_records
       └── data_relations

documents
 ├── extraction results
 ├── visibility
 └── website_documents

setups
 └── fields
       └── locators
             └── locator_examples
```

The exact normalization can vary, but the semantic boundaries must remain.

---

# 70. Suggested New Models

At minimum consider:

```text
DataSource
DataSchema
DataField
DataRecord
DataRelation
WebsiteDataSource
WebsiteDocument
WebsitePublication
ComponentDefinition
WebsiteAction
WebsiteCondition
ComputedField
```

Potentially:

```text
WebsiteRoute
WebsiteAsset
WebsiteForm
FormSubmission
PluginInstallation
PluginPermission
```

---

# 71. Project Structure

Recommended target structure:

```text
ocr-platform/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── admin/
│   │   │   │   ├── websites.py
│   │   │   │   ├── pages.py
│   │   │   │   ├── locators.py
│   │   │   │   ├── data_sources.py
│   │   │   │   └── documents.py
│   │   │   └── public/
│   │   │       ├── sites.py
│   │   │       ├── pages.py
│   │   │       ├── search.py
│   │   │       ├── records.py
│   │   │       └── files.py
│   │   ├── auth/
│   │   ├── models/
│   │   │   ├── website.py
│   │   │   ├── website_version.py
│   │   │   ├── data.py
│   │   │   ├── locator.py
│   │   │   └── document.py
│   │   ├── services/
│   │   │   ├── websites/
│   │   │   ├── data/
│   │   │   ├── search/
│   │   │   ├── locators/
│   │   │   ├── publication/
│   │   │   └── permissions/
│   │   ├── providers/
│   │   │   ├── search/
│   │   │   ├── storage/
│   │   │   ├── publication/
│   │   │   └── data/
│   │   └── repositories/
│   └── tests/
│
├── frontend/
│   ├── views/
│   │   ├── WebsiteBuilderView.tsx
│   │   ├── PDFFieldMapperView.tsx
│   │   └── ...
│   ├── website-builder/
│   │   ├── components/
│   │   ├── canvas/
│   │   ├── properties/
│   │   ├── data-binding/
│   │   ├── actions/
│   │   ├── rules/
│   │   └── validation/
│   └── ...
│
├── public-site/
│   ├── src/
│   │   ├── runtime/
│   │   ├── components/
│   │   ├── bindings/
│   │   ├── actions/
│   │   ├── routing/
│   │   └── theme/
│   └── ...
│
├── scripts/
├── docker/
└── docker-compose.yml
```

---

# 72. Frontend Builder Internal Architecture

Use explicit layers:

```text
EditorState
    ↓
PageTree
    ↓
ComponentSelection
    ↓
PropertyEditor
    ↓
BindingEditor
    ↓
ActionEditor
    ↓
RuleEditor
    ↓
Validation
    ↓
Version API
```

Do not mix preview rendering concerns with database mutation logic.

---

# 73. Component Registry

The frontend and public runtime need a central component registry.

Example:

```ts
componentRegistry = {
  heading: HeadingComponent,
  text: TextComponent,
  button: ButtonComponent,
  dataCard: DataCardComponent,
  dataTable: DataTableComponent,
  searchInput: SearchInputComponent,
  searchResults: SearchResultsComponent,
  pdfViewer: PdfViewerComponent,
};
```

A component definition also contains metadata used by the builder:

```text
component name
category
editable properties
bindable properties
supported events
responsive support
required permissions
```

---

# 74. Component Manifest

Recommended generic representation:

```json
{
  "type": "data-card",
  "label": "Data Card",
  "category": "data",
  "props": {
    "title": {
      "type": "binding",
      "required": true
    },
    "subtitle": {
      "type": "binding"
    }
  },
  "events": {
    "click": true
  }
}
```

This makes the builder extensible without hard-coding every field of every component.

---

# 75. Safe Expression Engine

Implement a small expression language for:

```text
field references
literals
basic arithmetic
string concatenation
safe date operations
comparisons
boolean logic
```

Example:

```text
current_record.expiry_date >= today()
```

Never evaluate arbitrary Python/JavaScript from user-authored website configuration on the backend.

---

# 76. Caching

Public configuration should be cacheable.

Cache candidates:

```text
published site configuration
published pages
public data schema
searchable indexes
thumbnails
```

Cache invalidation occurs on publication changes.

Draft edits must not invalidate or mutate the live public snapshot except through explicit publish.

---

# 77. Performance Requirements

Public search should be based on indexed structured data.

Target behavior:

```text
Search request
   ↓
< normal API response latency
```

No synchronous OCR execution in the search path.

Large document lists should use pagination.

PDF files should be streamed.

Heavy parsing should happen asynchronously where possible.

---

# 78. Background Jobs

Future/optional jobs:

```text
OCR processing
Extraction
Locator regression testing
Search indexing
Thumbnail generation
Publication validation
Static asset preparation
```

A publication job may be asynchronous for large sites, but the initial implementation can be synchronous for small/local datasets while retaining a service boundary.

---

# 79. Observability

Log:

```text
website publish
website unpublish
website edits
locator changes
extraction failures
search failures
public access errors
permission denials
```

Audit records should include:

```text
actor
action
resource
timestamp
before/after reference where safe
```

---

# 80. Testing Strategy

Testing must cover the universal system, not only the drawing example.

## 80.1 Unit tests

Test:

```text
schema handling
binding resolution
conditions
computed fields
action validation
route resolution
publication validation
visibility checks
search configuration
locator matching
```

## 80.2 API tests

Test:

```text
admin authentication
admin authorization
public-only access
published-only access
website membership
field visibility
file authorization
```

## 80.3 Integration tests

Test end-to-end:

```text
document
→ OCR
→ extraction
→ data source
→ website builder
→ publication
→ public search
→ public detail
```

## 80.4 UI tests

Test:

```text
create website
choose data source
add page
add component
bind field
configure search
preview
publish
edit draft
publish new version
```

## 80.5 Regression tests

Specifically lock down the P0 security failures:

```text
Public site cannot call admin route.

Non-admin cannot call admin route.

Publishing site does not publish every ready document.

Public API never returns draft configuration.

Published version cannot be mutated through draft edit.

Private fields never appear in public responses.

Private documents cannot be downloaded through guessed URLs.
```

---

# 81. Universal Acceptance Tests

The implementation is acceptable only when these examples work without custom per-domain code.

## Test A — Drawings

```text
Create Setup
Map title
Extract drawings
Create website from data source
Create search page
Search title
Open PDF
```

## Test B — Warranty

```text
Create Warranty Setup
Fields:
serial_number
product_name
purchase_date
expiry_date

Create Website
Use Warranty template
Bind search to serial_number
Display product/expiry
Compute active status
Publish
```

## Test C — Certificates

```text
Create Certificate Setup
Create public verification page
Search certificate number
Show record
Open certificate PDF
```

## Test D — Dashboard

```text
Use an extracted data source
Create dashboard
Add metric
Add chart
Add data table
Publish
```

No domain-specific Website Builder code should be required for B, C, or D.

---

# 82. Migration Strategy

Do not rewrite the current system in one large change.

## Phase 0 — Security hardening

1. Protect admin endpoints.
2. Audit legacy routes.
3. Remove admin calls from public-site.
4. Add explicit website-document membership.
5. Stop automatic public exposure.
6. Remove public draft fallback.
7. Freeze published versions.

This phase is mandatory before exposing the current builder beyond trusted local use.

## Phase 1 — Generalize website data model

1. Add DataSource/DataSchema/DataField abstractions.
2. Bridge Setup/Fields into DataSources.
3. Add field IDs/roles.
4. Refactor search config to schema-driven selection.

## Phase 2 — Generalize the builder

1. Build page model.
2. Build component tree model.
3. Create component registry.
4. Add data binding.
5. Add visual property editor.
6. Add generic search components.

## Phase 3 — Application capabilities

1. Actions.
2. Conditions.
3. Computed fields.
4. Forms.
5. Collection query definitions.

## Phase 4 — Public runtime

1. Implement generic renderer.
2. Implement actual routing.
3. Implement public data client.
4. Implement route/page rendering.
5. Implement published snapshot resolution.

## Phase 5 — Templates and generator

1. Blank.
2. Search portal.
3. Document library.
4. Warranty lookup.
5. Product catalog.
6. Certificate verification.
7. Dashboard.
8. Automatic starter site generation.

## Phase 6 — Extensibility

1. Plugin registry.
2. Custom component contracts.
3. Capability permissions.
4. Developer extensions.
5. Additional providers.

---

# 83. Installation / Development Script Requirements

The repository should retain a simple single-command developer experience.

Expected:

```bash
./launch.sh
```

or an equivalent command that starts:

```text
backend
admin frontend
public frontend
```

Development environment variables should include configurable endpoints such as:

```text
BACKEND_URL=http://localhost:8000
ADMIN_URL=http://localhost:5173
PUBLIC_SITE_URL=http://localhost:5174
VITE_API_BASE_URL=http://localhost:8000
VITE_PUBLIC_SITE_SLUG=demo
```

No code should hard-code localhost addresses when configuration can be used.

---

# 84. Data Flow Example

A complete warranty flow should look like:

```text
Warranty PDF
    ↓
Tesseract
    ↓
OCR Tokens
    ↓
Setup: Warranty
    ↓
Locator:
Serial Number
Product Name
Purchase Date
Expiry Date
    ↓
Extraction
    ↓
Data Record
    {
      serial_number: "ABC-123456",
      product_name: "Model X",
      purchase_date: "2026-01-12",
      expiry_date: "2028-01-12"
    }
    ↓
Data Source: Warranty Records
    ↓
Website Builder
    ↓
Search Component
    ↓
Binding: serial_number
    ↓
Public Runtime
    ↓
Customer searches ABC-123456
    ↓
Indexed data lookup
    ↓
Warranty detail page
```

---

# 85. What the System Must Not Become

Avoid these traps:

## Not a drawing-only application

Do not build additional drawing-specific systems for every new domain.

## Not a generic page-image editor first

Do not spend the first iteration building a full Wix/Figma clone.

The important differentiator is **data-aware websites/applications**.

## Not a separate OCR engine for the public site

Use existing extraction data.

## Not an unsafe arbitrary-code execution platform

Use controlled expressions and plugins.

## Not a document dump

Website publication must require explicit inclusion/visibility.

---

# 86. Recommended MVP Boundary

The first universal release should support:

```text
Pages
Components
Data Sources
Data Fields
Data Binding
Search
Filters
Collections
Detail Views
Documents/PDF Viewer
Theme
Conditions
Simple Computed Fields
Preview
Immutable Publish
Explicit Public Document Membership
```

This is already substantially more powerful than a document portal while remaining feasible.

Forms, charts, advanced workflows, and plugins can then be layered on top.

---

# 87. AI Coding Agent Execution Prompt

Use the following prompt with a coding agent working directly on the repository.

```text
You are modifying the existing repository Alex07lol/tswebui.

Goal:
Transform the current OCR/document website builder into a universal data-driven website and lightweight application builder while preserving the existing OCR, extraction, Setup, Field, Locator, and Teach From Examples capabilities.

Do not rewrite the project from scratch.
Inspect the existing implementation first and reuse working services/models/components where practical.

============================================================
PRODUCT REQUIREMENTS
============================================================

1. The Website Builder must no longer be drawing-specific.
2. It must support arbitrary data domains such as drawings, warranties, invoices, certificates, products, assets, dashboards, archives, and custom datasets.
3. OCR/extraction remains the ingestion layer.
4. The Website Builder consumes normalized structured data.
5. Users must be able to create pages, add reusable components, bind component properties to data fields, configure search, filters, actions, conditions, and computed values.
6. A blank website must be possible.
7. Templates must be generated from generic page/component/binding configuration rather than domain-specific implementations.
8. Advanced users should be able to use controlled expressions and eventually plugins/custom components.
9. Never execute arbitrary Python/JavaScript from website configuration.

============================================================
MANDATORY SECURITY FIXES
============================================================

A. Add explicit authentication and authorization to all admin endpoints.
B. Audit and protect legacy admin-sensitive endpoints outside /api/admin.
C. The public frontend must never call /api/admin/*.
D. Remove any public fallback to a draft/latest website version.
E. Published website versions must be immutable.
F. Editing a published website must create/edit a draft only.
G. Publishing a website must NOT make all ready documents public.
H. Introduce explicit WebsiteDocument or equivalent website-record membership.
I. Separate website inclusion from public visibility.
J. Public search, detail, thumbnails, files, and actions must all enforce publication and visibility rules.
K. Never expose filesystem paths.
L. Field-level public visibility must be enforced.

============================================================
DOMAIN MODEL
============================================================

Add or evolve models toward:

Website
WebsiteVersion
WebsitePage
WebsiteCollection
WebsiteDataSource
WebsiteDocument / WebsiteRecordMembership
WebsitePublication
DataSource
DataSchema
DataField
DataRecord
DataRelation
ComputedField
WebsiteAction
WebsiteCondition

Preserve existing:
Setup
ExtractionField
ExtractionLocator
ExtractionRule
Document
OCR models

Bridge Setup/Fields into DataSources/Schemas rather than duplicating extraction semantics.

============================================================
DATA MODEL
============================================================

DataSource:
- id
- name
- slug
- description
- source_type
- schema_id
- status
- created_by
- timestamps

DataSchema:
- id
- name
- version
- fields

DataField:
- id
- key
- label
- type
- required
- searchable
- sortable
- filterable
- displayable
- public_readable
- semantic roles where useful

DataRecord:
- id
- data_source_id
- source_document_id nullable
- values_json
- status
- timestamps

DataRelation:
- source record/field
- target record/field
- relation type

============================================================
WEBSITE VERSIONING
============================================================

Published version is immutable.
Website has published_version_id.
Editing after publication targets a draft.
Publishing validates the draft, creates/promotes a new immutable snapshot, archives the previous publication, and updates published_version_id.

Public API returns only the exact published snapshot.

============================================================
WEBSITE BUILDER
============================================================

Refactor the current WebsiteBuilderView into a general builder with sections/panels roughly corresponding to:

Pages
Data
Components
Design
Actions
Rules
Preview
Publish

The builder must dynamically load fields from the selected DataSource.
Do NOT use hard-coded comma-separated field settings such as title,drawing_number,project,date.

Implement a reusable component registry with categories:

Layout
Content
Data
Search
Forms
Documents
Charts
Advanced

At minimum support:
Container
Section
Heading
Text
Button
Image
DataCard
DataList
DataTable
SearchInput
SearchResults
Filter
Pagination
DocumentMetadata
PDFViewer

Each component should have:
- type
- id
- props
- style
- responsive
- bindings
- events
- visibility
- children

============================================================
DATA BINDING
============================================================

Implement generic bindings:
static
field
record
collection
computed
context
query

Use a controlled binding resolver.
Example:
current_record.product_name
current_record.serial_number
route_params.id

============================================================
SEARCH
============================================================

Search fields must come from DataSchema/DataField selection.
Do not rely on hard-coded special field names.
Legacy heuristics may remain isolated for compatibility only.

Service chain:
Public API -> PublicSiteService -> WebsiteSearchService -> SearchProvider

Do not instantiate DatabaseSearchProvider directly inside API route handlers.

============================================================
COLLECTIONS
============================================================

Make WebsiteCollection functional.
Implement:
- data source
- filter definition
- sort definition
- pagination
- display definition

Public collection routes must actually apply those filters using the same query/search service layer.

============================================================
ACTIONS
============================================================

Implement a safe action system with allowlisted operations:
- navigate
- search
- filter
- sort
- open_document
- download_file
- submit_form (basic if feasible)
- set_state
- show_modal
- refresh

Use explicit input mapping.

============================================================
CONDITIONS / EXPRESSIONS
============================================================

Implement a controlled rule engine.
Operators should include:
equals
not_equals
contains
starts_with
ends_with
greater_than
less_than
greater_or_equal
less_or_equal
is_empty
is_not_empty
in
not_in

Support AND/OR/NOT.

Implement simple computed fields with safe expressions for:
- field references
- literals
- arithmetic
- string concatenation
- dates
- comparisons
- boolean logic

Do not run arbitrary Python/JavaScript.

============================================================
PUBLIC RUNTIME
============================================================

Refactor public-site into a generic runtime that renders published site/page/component definitions.

Do not maintain domain-specific hard-coded pages for drawings only.

Use real routing so direct URLs and browser refresh work.
Suggested routes:
/{site-slug}
/{site-slug}/search
/{site-slug}/documents/:id
/{site-slug}/collections/:slug
/{site-slug}/pages/:page-slug

The public app must use only /api/public/* endpoints.

============================================================
VISUAL PDF FIELD MAPPER
============================================================

Keep the existing PDFFieldMapperView and improve it so selecting text/region can:
1. map to an existing field, or
2. create a new field and locator together.

Locator must capture/use:
- bbox
- page dimensions
- relative position
- page number
- OCR token IDs
- selected text
- nearby text
- anchor candidates
- line/column structure
- pattern
- expected type
- OCR confidence
- template label/signature

Matching must combine multiple signals, not absolute pixel position only.

Allow multiple locators per field.

Keep ExtractionLocator as the canonical learned representation and ExtractionRule as the compiled/derived representation.
Locator changes must recompile the derived rule as appropriate.

============================================================
PUBLIC DOCUMENT MEMBERSHIP
============================================================

Introduce WebsiteDocument or equivalent membership model.

A website should explicitly specify which documents/records it contains.
Publishing must operate only on those included resources.
Do not convert all ready documents to public.

============================================================
FILES
============================================================

Serve files only through authorization-aware endpoints.
Never expose raw filesystem locations.

============================================================
THEME
============================================================

Create a token-based theme model:
colors
typography
spacing
radii
shadows
breakpoints
component defaults

============================================================
TEMPLATES
============================================================

Implement templates as configuration presets only:
- Blank
- Search Portal
- Document Library
- Warranty Lookup
- Product Catalog
- Invoice Portal
- Certificate Verification
- Data Dashboard

All templates must use the same generic builder/runtime.

============================================================
AUTO-GENERATION
============================================================

Given a DataSource, infer a starter website:
- candidate title field
- candidate identifier field
- searchable fields
- display fields
- date/image/document fields

Generate generic pages and bindings.
Allow user to modify everything.

============================================================
TESTING
============================================================

Add regression tests proving:
1. admin routes require auth
2. non-admin cannot use admin routes
3. public site never requires/admin-calls admin API
4. publishing does not expose every ready document
5. private documents remain inaccessible
6. private fields remain inaccessible
7. public API never returns draft configuration
8. published versions cannot be mutated by draft edits
9. collection filters are applied
10. arbitrary domains work without special-case code

Add end-to-end tests for at least:
- engineering drawings
- warranties
- certificates
- dashboard

============================================================
IMPLEMENTATION METHOD
============================================================

1. Inspect repository and existing tests first.
2. Make the P0 security/publication changes first.
3. Add migrations/models incrementally.
4. Add service abstractions before large UI changes.
5. Generalize the DataSource/schema layer.
6. Refactor WebsiteBuilderView into generic builder architecture.
7. Refactor public-site into generic published runtime and real routing.
8. Add templates and auto-generation.
9. Preserve existing OCR/Teach/Locator workflows.
10. Run backend tests and frontend type/build checks after every substantial stage.
11. Never delete working functionality merely to simplify implementation.
12. Keep legacy compatibility shims isolated and documented.

============================================================
ACCEPTANCE CRITERIA
============================================================

The task is complete only when a non-technical user can:

A. Create a new Setup for an arbitrary document type.
B. Define fields without drawing-specific naming requirements.
C. Teach field locations visually from a PDF/image.
D. Extract structured records.
E. Create a website from those records.
F. Select any fields through a visual field picker.
G. Add and arrange generic components.
H. Bind components to arbitrary fields.
I. Configure search/filters without typing field-name strings.
J. Add conditions/computed values.
K. Preview the draft.
L. Publish an immutable version.
M. Access only explicitly public/included records from the public site.
N. Deep-link directly to public pages/details.
O. Repeat the same workflow for drawings, warranties, certificates, products, or other data with no domain-specific builder implementation.

Start by inspecting the current codebase and produce a safe incremental implementation plan, then implement the highest-priority changes directly in the repository.
```

---

# 88. Definition of Done

The Website Builder is considered successfully generalized when the following statement is true:

> A new data domain can be introduced by defining its data/extraction fields and optionally a template, without writing a new Website Builder or Public Site implementation for that domain.

The architecture should therefore support:

```text
NEW DOMAIN
   ↓
NEW DATA SOURCE / SCHEMA
   ↓
EXISTING BUILDER
   ↓
EXISTING COMPONENTS
   ↓
EXISTING RUNTIME
   ↓
NEW WEBSITE
```

That is the central architectural goal.

---

# 89. Final Product Shape

The finished TSWebUI platform should conceptually look like:

```text
                        TSWEBUI
                           │
      ┌────────────────────┼────────────────────┐
      │                    │                    │
      ▼                    ▼                    ▼
    INGEST               UNDERSTAND           BUILD
      │                    │                    │
 OCR / Files         Setups / Locators     Website Builder
      │                    │                    │
      └────────────────────┼────────────────────┘
                           ▼
                      DATA PLATFORM
                           │
              ┌────────────┼─────────────┐
              ▼            ▼             ▼
           Search        Records       Relations
              │            │             │
              └────────────┼─────────────┘
                           ▼
                    APPLICATION MODEL
                           │
       ┌───────────────────┼────────────────────┐
       ▼                   ▼                    ▼
     Pages             Components            Actions
       │                   │                    │
       └───────────────────┼────────────────────┘
                           ▼
                      PUBLIC RUNTIME
                           │
                           ▼
                     ANY WEBSITE / APP
```

The drawing portal remains supported.
It is simply no longer the boundary of the product.

TSWebUI should be able to turn extracted information into a **custom, searchable, data-driven public experience**, with the complexity available when needed and hidden when it is not.
