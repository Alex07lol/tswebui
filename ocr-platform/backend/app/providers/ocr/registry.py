"""OCR Provider registry — maps provider names to provider instances."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.providers.ocr.base import OCRProvider

_registry: dict[str, "OCRProvider"] = {}


def register_provider(provider: "OCRProvider") -> None:
    """Register an OCRProvider under its name."""
    _registry[provider.name] = provider


def get_provider(name: str) -> "OCRProvider":
    """Return a registered provider by name.

    Raises:
        KeyError: If provider is not registered.
    """
    if name not in _registry:
        raise KeyError(f"OCR provider '{name}' is not registered. Available: {list(_registry)}")
    return _registry[name]


def list_providers() -> list[str]:
    """Return names of all registered providers."""
    return list(_registry.keys())
