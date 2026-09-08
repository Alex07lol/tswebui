"""TesseractProvider — concrete implementation of OCRProvider using pytesseract."""
from __future__ import annotations

import subprocess
from pathlib import Path
from PIL import Image

try:
    import pytesseract
    _HAS_PYTESSERACT = True
except ImportError:
    _HAS_PYTESSERACT = False

from app.core.logging import get_logger
from app.providers.ocr.base import BoundingBox, OCROptions, OCRPage, OCRResult, OCRWord
from app.services.ocr.preprocessing import ImagePreprocessor

log = get_logger(__name__)


class TesseractProvider:
    """OCR provider backed by the locally installed Tesseract binary via pytesseract."""

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
        """Run Tesseract on a page image and return a normalised OCRResult."""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found at: {image_path}")

        image = Image.open(path)
        width, height = image.size

        # Preprocessing
        profile = options.extra.get("preprocessing") if options.extra else None
        if profile and isinstance(profile, list):
            proc_img = ImagePreprocessor.process(image, profile)
        else:
            proc_img = image

        config = f"--psm {options.psm} --oem {options.oem}"
        lang = options.language or "eng"

        words: list[OCRWord] = []
        page_text_lines: list[str] = []

        if _HAS_PYTESSERACT:
            try:
                data = pytesseract.image_to_data(
                    proc_img,
                    lang=lang,
                    config=config,
                    output_type=pytesseract.Output.DICT,
                )
                n_boxes = len(data.get("text", []))
                word_seq = 0
                current_line_words: list[str] = []
                last_line_num = -1

                for i in range(n_boxes):
                    raw_word = data["text"][i].strip()
                    if not raw_word:
                        continue

                    raw_conf = float(data["conf"][i])
                    # Tesseract uses -1 for layout blocks with no text
                    conf = max(0.0, min(1.0, raw_conf / 100.0)) if raw_conf >= 0 else 0.0

                    line_num = int(data.get("line_num", [0])[i])
                    block_num = int(data.get("block_num", [0])[i])

                    if last_line_num != -1 and line_num != last_line_num:
                        if current_line_words:
                            page_text_lines.append(" ".join(current_line_words))
                            current_line_words = []
                    last_line_num = line_num
                    current_line_words.append(raw_word)

                    words.append(
                        OCRWord(
                            text=raw_word,
                            confidence=round(conf, 4),
                            bounding_box=BoundingBox(
                                x=int(data["left"][i]),
                                y=int(data["top"][i]),
                                width=int(data["width"][i]),
                                height=int(data["height"][i]),
                            ),
                            word_index=word_seq,
                            line_number=line_num,
                            block_number=block_num,
                        )
                    )
                    word_seq += 1

                if current_line_words:
                    page_text_lines.append(" ".join(current_line_words))

            except Exception as e:
                log.warning("pytesseract extraction error, falling back to basic extraction", error=str(e))
                page_text_lines = ["[OCR failed or empty]"]
        else:
            page_text_lines = ["[pytesseract not installed]"]

        full_page_text = "\n".join(page_text_lines)
        if not full_page_text and words:
            full_page_text = " ".join(w.text for w in words)

        page = OCRPage(
            page_number=1,
            width=width,
            height=height,
            text=full_page_text,
            words=words,
        )

        return OCRResult(
            document_id=document_id,
            full_text=full_page_text,
            pages=[page],
            provider=self.name,
            provider_version=self.version,
        )
