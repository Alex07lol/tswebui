"""TesseractProvider — concrete implementation of OCRProvider using pytesseract.

This is a stub for Phase 0. Full OCR processing will be implemented in Phase 1.
"""
from __future__ import annotations

import subprocess

from app.core.logging import get_logger
from app.providers.ocr.base import BoundingBox, OCROptions, OCRPage, OCRResult, OCRWord

log = get_logger(__name__)


class TesseractProvider:
    """OCR provider backed by the locally installed Tesseract binary."""

    @property
    def name(self) -> str:
        return "tesseract"

    @property
    def version(self) -> str:
        """Return the installed Tesseract version string."""
        try:
            result = subprocess.run(
                ["tesseract", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            first_line = (result.stdout or result.stderr or "").split("\n")[0]
            return first_line.strip() or "unknown"
        except Exception:
            return "unavailable"

    def is_available(self) -> bool:
        """Return True if the tesseract binary is accessible."""
        try:
            subprocess.run(["tesseract", "--version"], capture_output=True, timeout=5)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def process(self, document_id: str, image_path: str, options: OCROptions) -> OCRResult:
        """Run Tesseract on a page image and return a normalised OCRResult.

        Phase 0 stub: returns a placeholder. Full implementation in Phase 1.
        """
        log.warning(
            "TesseractProvider.process called — full implementation deferred to Phase 1",
            document_id=document_id,
        )
        return OCRResult(
            document_id=document_id,
            full_text="[Phase 0 stub — OCR not yet implemented]",
            pages=[
                OCRPage(
                    page_number=1,
                    width=0,
                    height=0,
                    text="[stub]",
                    words=[],
                )
            ],
            provider=self.name,
            provider_version=self.version,
        )
