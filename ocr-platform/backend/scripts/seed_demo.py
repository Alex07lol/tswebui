"""Seed script to populate rich demo data for tswebui platform."""
from __future__ import annotations

import asyncio
import io
import json
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import AsyncSessionLocal, create_all_tables
from app.models.document import Document, DocumentPage
from app.models.ocr import OCRResult, OCRPage, OCRWord
from app.models.configuration import Configuration, ConfigurationVersion, ExtractionField, ExtractionRule
from app.models.extraction import ExtractionJob, ExtractionResult, ExtractedValue, ExtractionEvidence
from app.models.dataset import Dataset, DatasetDocument
from app.models.discovery import DiscoveryRun, DocumentCluster, PatternProposal
from app.models.test import TestSuite, TestCase, TestRun
from app.models.audit import AuditLog
from app.providers.storage.local import LocalStorageProvider


def generate_invoice_image() -> bytes:
    """Generate a clean synthetic invoice PNG image."""
    img = Image.new("RGB", (800, 1050), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Header
    draw.rectangle([(40, 40), (760, 90)], fill=(30, 30, 35))
    draw.text((60, 52), "ACME LOGISTICS INC.", fill=(255, 255, 255))
    draw.text((620, 52), "INVOICE", fill=(255, 255, 255))

    # Metadata section
    draw.text((60, 130), "Billed To: Globex Corporation", fill=(50, 50, 50))
    draw.text((60, 155), "123 Business Avenue, Suite 400", fill=(100, 100, 100))

    draw.text((460, 130), "Invoice Number: INV-2026-00128", fill=(20, 20, 20))
    draw.text((460, 155), "Invoice Date: 2026-03-15", fill=(20, 20, 20))
    draw.text((460, 180), "Due Date: 2026-04-15", fill=(20, 20, 20))

    # Table Header
    draw.rectangle([(40, 240), (760, 270)], fill=(240, 240, 245))
    draw.text((60, 248), "Item Description", fill=(30, 30, 30))
    draw.text((400, 248), "Qty", fill=(30, 30, 30))
    draw.text((500, 248), "Unit Price", fill=(30, 30, 30))
    draw.text((650, 248), "Total", fill=(30, 30, 30))

    # Table Rows
    rows = [
        ("Express Freight Delivery #991", "2", "$350.00", "$700.00"),
        ("Warehouse Handling Fee", "1", "$220.50", "$220.50"),
        ("Overnight Storage Facility", "5", "$100.00", "$500.00"),
    ]
    y = 290
    for desc, qty, unit, total in rows:
        draw.text((60, y), desc, fill=(40, 40, 40))
        draw.text((410, y), qty, fill=(40, 40, 40))
        draw.text((500, y), unit, fill=(40, 40, 40))
        draw.text((650, y), total, fill=(40, 40, 40))
        draw.line([(40, y + 25), (760, y + 25)], fill=(230, 230, 230), width=1)
        y += 40

    # Total Box
    draw.rectangle([(480, 480), (760, 540)], fill=(245, 245, 250), outline=(200, 200, 200))
    draw.text((500, 500), "Total Amount: $1,420.50", fill=(10, 10, 10))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


async def seed() -> None:
    await create_all_tables()
    storage = LocalStorageProvider()

    async with AsyncSessionLocal() as session:
        print("Generating sample invoice...")
        content = generate_invoice_image()
        doc_id = str(uuid.uuid4())

        # Save files to storage
        storage.save(f"documents/{doc_id}/original.png", io.BytesIO(content), "image/png")
        storage.save(f"documents/{doc_id}/pages/page_1.png", io.BytesIO(content), "image/png")

        doc = Document(
            id=doc_id,
            filename="sample_invoice_acme.png",
            original_filename="sample_invoice_acme.png",
            mime_type="image/png",
            file_size_bytes=len(content),
            storage_path=f"documents/{doc_id}/original.png",
            file_hash="mock_hash_" + doc_id[:8],
            page_count=1,
            status="ready",
        )
        session.add(doc)

        doc_page = DocumentPage(
            id=str(uuid.uuid4()),
            document_id=doc_id,
            page_number=1,
            image_path=f"documents/{doc_id}/pages/page_1.png",
            width=800,
            height=1050,
        )
        session.add(doc_page)

        # 2. OCR Result with tokens and bounding boxes
        ocr_res_id = str(uuid.uuid4())
        ocr_result = OCRResult(
            id=ocr_res_id,
            document_id=doc_id,
            provider="tesseract",
            provider_version="5.3.4",
            language="eng",
            full_text=(
                "ACME LOGISTICS INC. INVOICE\n"
                "Billed To: Globex Corporation\n"
                "Invoice Number: INV-2026-00128\n"
                "Invoice Date: 2026-03-15\n"
                "Due Date: 2026-04-15\n"
                "Total Amount: $1,420.50"
            ),
            cache_key="demo_cache_key_" + doc_id[:8],
        )
        session.add(ocr_result)

        ocr_page = OCRPage(
            id=str(uuid.uuid4()),
            ocr_result_id=ocr_res_id,
            page_number=1,
            width=800,
            height=1050,
            text=ocr_result.full_text,
        )
        session.add(ocr_page)

        sample_tokens = [
            ("ACME", 60, 52, 60, 20, 0.98, 1),
            ("LOGISTICS", 130, 52, 90, 20, 0.97, 1),
            ("INC.", 230, 52, 40, 20, 0.96, 1),
            ("INVOICE", 620, 52, 80, 20, 0.99, 1),
            ("Invoice", 460, 130, 50, 18, 0.96, 2),
            ("Number:", 515, 130, 60, 18, 0.95, 2),
            ("INV-2026-00128", 585, 130, 140, 18, 0.98, 2),
            ("Invoice", 460, 155, 50, 18, 0.95, 3),
            ("Date:", 515, 155, 45, 18, 0.96, 3),
            ("2026-03-15", 565, 155, 95, 18, 0.97, 3),
            ("Due", 460, 180, 30, 18, 0.94, 4),
            ("Date:", 495, 180, 45, 18, 0.95, 4),
            ("2026-04-15", 545, 180, 95, 18, 0.97, 4),
            ("Total", 500, 500, 45, 20, 0.96, 5),
            ("Amount:", 550, 500, 65, 20, 0.95, 5),
            ("$1,420.50", 625, 500, 85, 20, 0.98, 5),
        ]
        for idx, (text, x, y, w, h, conf, line) in enumerate(sample_tokens):
            session.add(OCRWord(
                id=str(uuid.uuid4()),
                page_id=ocr_page.id,
                text=text,
                confidence=conf,
                bbox_x=x,
                bbox_y=y,
                bbox_width=w,
                bbox_height=h,
                word_index=idx,
                line_number=line,
                block_number=1,
            ))

        # 3. Extraction Configuration
        config = Configuration(
            id=str(uuid.uuid4()),
            name="Standard Invoice Parser",
            slug="standard_invoice",
            description="Extracts invoice number, date, and total amount with anchor matching.",
        )
        session.add(config)

        version = ConfigurationVersion(
            id=str(uuid.uuid4()),
            configuration_id=config.id,
            version_number=1,
            status="active",
            schema_version=1,
            change_notes="Initial production invoice extraction rules",
        )
        session.add(version)

        # Field: invoice_number
        f1 = ExtractionField(
            id=str(uuid.uuid4()),
            version_id=version.id,
            field_id="invoice_number",
            display_name="Invoice Number",
            output_variable="invoice_number",
            output_type="string",
            required=True,
            priority=100,
        )
        session.add(f1)
        r1 = ExtractionRule(
            id=str(uuid.uuid4()),
            field_id=f1.id,
            rule_name="Anchor Invoice Number",
            strategy="same_line",
            anchor_config=json.dumps({"value": "Invoice Number", "match": "fuzzy", "minimum_similarity": 0.85}),
            search_config=json.dumps({"direction": "after", "scope": "same_line", "max_lines": 1}),
            pattern_config=json.dumps({"type": "regex", "value": "INV-\\d{4}-\\d+"}),
            priority=100,
            is_enabled=True,
        )
        session.add(r1)

        # Field: total_amount
        f2 = ExtractionField(
            id=str(uuid.uuid4()),
            version_id=version.id,
            field_id="total_amount",
            display_name="Total Amount",
            output_variable="total_amount",
            output_type="currency",
            required=True,
            priority=90,
        )
        session.add(f2)
        r2 = ExtractionRule(
            id=str(uuid.uuid4()),
            field_id=f2.id,
            rule_name="Anchor Total Amount",
            strategy="same_line",
            anchor_config=json.dumps({"value": "Total Amount", "match": "fuzzy", "minimum_similarity": 0.85}),
            search_config=json.dumps({"direction": "after", "scope": "same_line", "max_lines": 1}),
            pattern_config=json.dumps({"type": "regex", "value": "\\$[\\d,]+\\.\\d{2}"}),
            priority=90,
            is_enabled=True,
        )
        session.add(r2)

        # 4. Extraction Job & Result
        job = ExtractionJob(
            id=str(uuid.uuid4()),
            document_id=doc.id,
            config_version_id=version.id,
            status="completed",
        )
        session.add(job)

        ext_result = ExtractionResult(
            id=str(uuid.uuid4()),
            job_id=job.id,
            document_id=doc.id,
            config_version_id=version.id,
            overall_confidence=0.97,
        )
        session.add(ext_result)

        v1 = ExtractedValue(
            id=str(uuid.uuid4()),
            result_id=ext_result.id,
            field_id="invoice_number",
            output_variable="invoice_number",
            raw_value="INV-2026-00128",
            normalized_value="INV-2026-00128",
            final_confidence=0.98,
            validation_passed=True,
            validation_message="Regex pattern match verified",
        )
        session.add(v1)
        session.add(ExtractionEvidence(
            id=str(uuid.uuid4()),
            extracted_value_id=v1.id,
            anchor_text="Invoice Number:",
            source_line="Invoice Number: INV-2026-00128",
            ocr_confidence=0.98,
            bbox_x=585,
            bbox_y=130,
            bbox_width=140,
            bbox_height=18,
            page_number=1,
        ))

        v2 = ExtractedValue(
            id=str(uuid.uuid4()),
            result_id=ext_result.id,
            field_id="total_amount",
            output_variable="total_amount",
            raw_value="$1,420.50",
            normalized_value="1420.50",
            final_confidence=0.96,
            validation_passed=True,
            validation_message="Currency parsed to decimal",
        )
        session.add(v2)
        session.add(ExtractionEvidence(
            id=str(uuid.uuid4()),
            extracted_value_id=v2.id,
            anchor_text="Total Amount:",
            source_line="Total Amount: $1,420.50",
            ocr_confidence=0.96,
            bbox_x=625,
            bbox_y=500,
            bbox_width=85,
            bbox_height=20,
            page_number=1,
        ))

        # 5. Regression Test Suite
        suite = TestSuite(
            id=str(uuid.uuid4()),
            configuration_id=config.id,
            name="Invoice Regression Test Suite",
            description="Continuous validation suite against ground-truth vendor documents",
        )
        session.add(suite)

        case = TestCase(
            id=str(uuid.uuid4()),
            suite_id=suite.id,
            document_id=doc.id,
            name="INV-2026-00128 Golden Reference",
            expected_values_json=json.dumps({"invoice_number": "INV-2026-00128", "total_amount": "1420.50"}),
            validation_mode="exact",
            is_regression=True,
        )
        session.add(case)

        run = TestRun(
            id=str(uuid.uuid4()),
            suite_id=suite.id,
            config_version_id=version.id,
            status="passed",
            total_cases=1,
            passed_cases=1,
            failed_cases=0,
            pass_rate=1.0,
            results_json=json.dumps([{
                "case_id": case.id,
                "case_name": case.name,
                "status": "passed",
                "diff": None
            }]),
        )
        session.add(run)

        # 6. Training Dataset & Pattern Discovery
        dataset = Dataset(
            id=str(uuid.uuid4()),
            name="North American Vendor Invoices",
            description="Sample set of recurring vendor invoice templates for pattern learning",
            document_count=5,
            status="active",
        )
        session.add(dataset)
        session.add(DatasetDocument(
            id=str(uuid.uuid4()),
            dataset_id=dataset.id,
            document_id=doc.id,
            added_order=1,
        ))

        disc_run = DiscoveryRun(
            id=str(uuid.uuid4()),
            dataset_id=dataset.id,
            status="completed",
            documents_processed=5,
            clusters_found=2,
            proposals_generated=3,
        )
        session.add(disc_run)

        cluster1 = DocumentCluster(
            id=str(uuid.uuid4()),
            run_id=disc_run.id,
            label="Template A (Modern Logistics)",
            document_count=3,
            is_outlier=False,
        )
        cluster2 = DocumentCluster(
            id=str(uuid.uuid4()),
            run_id=disc_run.id,
            label="Template B (Compact Grid)",
            document_count=2,
            is_outlier=False,
        )
        session.add(cluster1)
        session.add(cluster2)

        session.add(PatternProposal(
            id=str(uuid.uuid4()),
            cluster_id=cluster1.id,
            field_name="invoice_number",
            display_name="Invoice Number",
            anchor="Invoice Number:",
            strategy="same_line",
            pattern_json="INV-\\d{4}-\\d{5}",
            confidence_anchor=0.97,
            confidence_pattern=0.96,
            confidence_position=0.94,
            confidence_overall=0.96,
            status="approved",
        ))
        session.add(PatternProposal(
            id=str(uuid.uuid4()),
            cluster_id=cluster1.id,
            field_name="invoice_date",
            display_name="Invoice Date",
            anchor="Invoice Date:",
            strategy="same_line",
            pattern_json="\\d{4}-\\d{2}-\\d{2}",
            confidence_anchor=0.95,
            confidence_pattern=0.95,
            confidence_position=0.92,
            confidence_overall=0.94,
            status="approved",
        ))
        session.add(PatternProposal(
            id=str(uuid.uuid4()),
            cluster_id=cluster2.id,
            field_name="total_amount",
            display_name="Total Amount",
            anchor="Total Amount:",
            strategy="same_line",
            pattern_json="\\$[\\d,]+\\.\\d{2}",
            confidence_anchor=0.94,
            confidence_pattern=0.93,
            confidence_position=0.91,
            confidence_overall=0.93,
            status="pending",
        ))

        # 7. Audit log entries
        session.add(AuditLog(
            id=str(uuid.uuid4()),
            event_type="document.uploaded",
            resource_type="document",
            resource_id=doc.id,
            details_json=json.dumps({"filename": doc.original_filename, "size": doc.file_size_bytes}),
        ))
        session.add(AuditLog(
            id=str(uuid.uuid4()),
            event_type="ocr.completed",
            resource_type="document",
            resource_id=doc.id,
            details_json=json.dumps({"tokens": len(sample_tokens), "provider": "tesseract"}),
        ))
        session.add(AuditLog(
            id=str(uuid.uuid4()),
            event_type="extraction.completed",
            resource_type="document",
            resource_id=doc.id,
            details_json=json.dumps({"confidence": 0.97, "fields": ["invoice_number", "total_amount"]}),
        ))

        await session.commit()
        print("Demo data seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
