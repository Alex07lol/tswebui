"""Image preprocessing pipeline for OCR optimization."""
from __future__ import annotations

from typing import Any
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


class ImagePreprocessor:
    """Configurable image preprocessing pipeline using PIL."""

    @staticmethod
    def process(image: Image.Image, profile: list[str | dict[str, Any]] | None = None) -> Image.Image:
        """Run image through a sequence of preprocessing steps.

        Supported steps:
            - "grayscale"
            - "contrast": {"factor": 2.0}
            - "sharpness": {"factor": 2.0}
            - "resize": {"scale": 2.0}
            - "threshold": {"threshold": 140}
            - "auto_contrast"
            - "denoise"
        """
        if not profile:
            # Default mild cleanup: grayscale + autocontrast
            return ImageOps.autocontrast(image.convert("L"))

        out = image.copy()
        for step in profile:
            if isinstance(step, str):
                name = step
                params: dict[str, Any] = {}
            elif isinstance(step, dict):
                name = list(step.keys())[0]
                params = step.get(name, {}) or {}
            else:
                continue

            out = ImagePreprocessor._apply_step(out, name, params)

        return out

    @staticmethod
    def _apply_step(image: Image.Image, name: str, params: dict[str, Any]) -> Image.Image:
        if name == "grayscale":
            return image.convert("L")
        elif name == "auto_contrast":
            gray = image.convert("L")
            return ImageOps.autocontrast(gray)
        elif name == "contrast":
            factor = float(params.get("factor", 1.5))
            enhancer = ImageEnhance.Contrast(image)
            return enhancer.enhance(factor)
        elif name == "sharpness":
            factor = float(params.get("factor", 1.5))
            enhancer = ImageEnhance.Sharpness(image)
            return enhancer.enhance(factor)
        elif name == "resize":
            scale = float(params.get("scale", 2.0))
            new_size = (int(image.width * scale), int(image.height * scale))
            return image.resize(new_size, Image.Resampling.LANCZOS)
        elif name == "denoise":
            return image.filter(ImageFilter.MedianFilter(size=3))
        elif name == "threshold":
            th = int(params.get("threshold", 140))
            gray = image.convert("L")
            return gray.point(lambda p: 255 if p > th else 0)
        return image
