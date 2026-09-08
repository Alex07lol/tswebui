# Product Definition — OCR Platform

## Project Name

OCR Platform (`ocr-platform`)

## Description

A modular, configurable OCR extraction platform built on Tesseract that lets users define, test, and deploy document extraction logic entirely from a WebUI — without any source-code changes.

## Problem Statement

Extracting structured data from scanned documents (invoices, forms, IDs) today requires custom code for every document type. There is no good way for a non-programmer to configure, test, and maintain extraction rules, or to learn rules automatically from example files.

## Target Users

- **Business analysts / operations staff** who need to extract data from documents (invoices, purchase orders, forms) without programming knowledge.
- **Developers** who want a configurable, maintainable extraction pipeline that doesn't require code changes per document type.
- **Data teams** who need auditable, versioned extraction configurations with full evidence trails.

## Key Goals

1. **Configuration over code** — extraction behaviour is fully declarative; no source changes needed to add/change a field.
2. **Example-based learning** — upload N sample documents and get editable extraction rule proposals automatically.
3. **Full transparency** — every extracted value carries its evidence (OCR confidence, bounding box, matched rule, anchor text).
4. **Versioned configurations** — every extraction result records the exact configuration version that produced it.
5. **Provider-based OCR** — Tesseract is the default engine, not a hard dependency; any OCR provider can be swapped in.
