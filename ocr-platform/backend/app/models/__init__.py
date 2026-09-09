"""SQLAlchemy ORM models for ocr-platform.

Import all models here so Alembic autogenerate can discover them.
"""
from app.models.audit import AuditLog
from app.models.configuration import (
    Configuration,
    ConfigurationVersion,
    ExtractionField,
    ExtractionRule,
)
from app.models.dataset import Dataset, DatasetDocument
from app.models.discovery import (
    DiscoveryRun,
    DocumentCluster,
    PatternProposal,
)
from app.models.document import Document, DocumentPage
from app.models.extraction import (
    ExtractionEvidence,
    ExtractionJob,
    ExtractionResult,
    ExtractedValue,
)
from app.models.locator import ExtractionLocator, LocatorExample, SearchIndexMetadata
from app.models.ocr import OCRJob, OCRPage, OCRResult, OCRWord
from app.models.test import TestCase, TestRun, TestSuite
from app.models.user import User
from app.models.website import (
    DocumentVisibility,
    Website,
    WebsiteCollection,
    WebsitePage,
    WebsiteVersion,
)

__all__ = [
    "AuditLog",
    "Configuration",
    "ConfigurationVersion",
    "Dataset",
    "DatasetDocument",
    "DiscoveryRun",
    "DocumentCluster",
    "Document",
    "DocumentPage",
    "DocumentVisibility",
    "ExtractionEvidence",
    "ExtractionField",
    "ExtractionJob",
    "ExtractionLocator",
    "ExtractionResult",
    "ExtractionRule",
    "ExtractedValue",
    "LocatorExample",
    "OCRJob",
    "OCRPage",
    "OCRResult",
    "OCRWord",
    "PatternProposal",
    "SearchIndexMetadata",
    "TestCase",
    "TestRun",
    "TestSuite",
    "User",
    "Website",
    "WebsiteCollection",
    "WebsitePage",
    "WebsiteVersion",
]
