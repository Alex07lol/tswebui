"""Mock Vision OCR provider for multi-engine demonstration."""
from __future__ import annotations

from pathlib import Path

from app.providers.ocr.base import OCROptions, OCRPage, OCRProvider, OCRResult, OCRWord


class MockVisionProvider:
    """A deterministic mock OCR provider that simulates cloud OCR output.

    Satisfies the OCRProvider protocol without requiring any external library.
    Useful for:
    - Demonstrating multi-provider support
    - Testing provider-switching logic
    - CI/CD where Tesseract is unavailable
    """

    @property
    def name(self) -> str:
        return "mock_vision"

    @property
    def version(self) -> str:
        return "1.0.0"

    def process(self, document_id: str, image_path: str, options: OCROptions) -> OCRResult:
        """Return a synthetic OCR result derived from the image filename."""
        path = Path(image_path)
        stem_words = path.stem.replace("_", " ").replace("-", " ").split()
        mock_tokens = stem_words + [
            "Invoice", "Total", "$1,234.56", "Date", "2024-01-15",
            "PO", "12345", "Vendor", "ACME", "Corp",
        ]

        words: list[OCRWord] = []
        x, y = 50, 50
        for i, token in enumerate(mock_tokens):
            w_px = len(token) * 9
            words.append(
                OCRWord(
                    text=token,
                    confidence=0.92,
                    bounding_box={"x": x, "y": y, "width": w_px, "height": 18},
                )
            )
            x += w_px + 8
            if (i + 1) % 5 == 0:
                x, y = 50, y + 28

        full_text = " ".join(w.text for w in words)
        page = OCRPage(
            page_number=1,
            width=800,
            height=600,
            text=full_text,
            words=words,
        )
        return OCRResult(
            document_id=document_id,
            full_text=full_text,
            pages=[page],
            provider=self.name,
            provider_version=self.version,
        )

    def is_available(self) -> bool:
        return True
