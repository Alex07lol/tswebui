"""Tests for the OCR provider interface and registry."""
from __future__ import annotations

import pytest

from app.providers.ocr.base import OCROptions, OCRProvider, OCRResult
from app.providers.ocr.registry import (
    get_provider,
    list_providers,
    register_provider,
)
from app.services.ocr.tesseract import TesseractProvider


def test_tesseract_provider_implements_protocol() -> None:
    """TesseractProvider must satisfy the OCRProvider Protocol."""
    provider = TesseractProvider()
    assert isinstance(provider, OCRProvider)


def test_tesseract_provider_name() -> None:
    provider = TesseractProvider()
    assert provider.name == "tesseract"


def test_tesseract_provider_stub_process() -> None:
    """TesseractProvider.process stub returns a valid OCRResult."""
    provider = TesseractProvider()
    res = provider.process("doc_1", "/tmp/dummy.png", OCROptions())
    assert isinstance(res, OCRResult)
    assert res.document_id == "doc_1"
    assert res.provider == "tesseract"
    assert len(res.pages) == 1


def test_provider_registry_register_and_get() -> None:
    """Registering and retrieving a provider by name must work."""
    provider = TesseractProvider()
    register_provider(provider)
    retrieved = get_provider("tesseract")
    assert retrieved.name == "tesseract"


def test_provider_registry_unknown_raises() -> None:
    with pytest.raises(KeyError):
        get_provider("__nonexistent_provider__")


def test_list_providers_includes_tesseract() -> None:
    provider = TesseractProvider()
    register_provider(provider)
    assert "tesseract" in list_providers()
