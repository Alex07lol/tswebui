"""OCR Provider interface (Protocol) and shared data contracts.

All OCR providers MUST implement OCRProvider. Tesseract-specific behaviour
must be translated into these common structures before being returned.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class BoundingBox:
    """Pixel-coordinate bounding box of a word/region on a page."""

    x: int
    y: int
    width: int
    height: int


@dataclass
class OCRWord:
    """A single word with its confidence score and bounding box."""

    text: str
    confidence: float  # 0.0 – 1.0
    bounding_box: BoundingBox
    word_index: int = 0
    line_number: int = 0
    block_number: int = 0


@dataclass
class OCRPage:
    """OCR output for a single page."""

    page_number: int
    width: int
    height: int
    text: str
    words: list[OCRWord] = field(default_factory=list)


@dataclass
class OCRResult:
    """Normalised OCR result returned by every provider.

    Tesseract-specific quirks (e.g. -1 confidence, hOCR format) must be
    translated into this structure by TesseractProvider before returning.
    """

    document_id: str
    full_text: str
    pages: list[OCRPage]
    provider: str
    provider_version: str


@dataclass
class OCROptions:
    """Options passed to a provider for a single OCR run."""

    language: str = "eng"
    psm: int = 6  # Tesseract page segmentation mode
    oem: int = 3  # OCR Engine Mode
    extra: dict[str, object] = field(default_factory=dict)


@runtime_checkable
class OCRProvider(Protocol):
    """Interface contract all OCR providers must implement.

    Adding a new engine (e.g. Google Cloud Vision) only requires creating a
    class that satisfies this protocol — no changes to extraction logic.
    """

    @property
    def name(self) -> str:
        """Unique provider identifier (e.g. 'tesseract')."""
        ...

    @property
    def version(self) -> str:
        """Installed provider version string."""
        ...

    def process(self, document_id: str, image_path: str, options: OCROptions) -> OCRResult:
        """Run OCR on a single page image and return a normalised result.

        Args:
            document_id: Platform document ID for tracing.
            image_path: Absolute path to the preprocessed page image.
            options: OCR configuration options.

        Returns:
            A fully populated OCRResult.
        """
        ...

    def is_available(self) -> bool:
        """Return True if this provider is installed and accessible."""
        ...
