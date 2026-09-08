"""Structured logging using structlog with stdlib fallback."""
from __future__ import annotations

import logging
import sys
from typing import Any

try:
    import structlog
    _HAS_STRUCTLOG = True
except ImportError:
    _HAS_STRUCTLOG = False


class _StdlibKwargLogger:
    """Wrapper around stdlib logger to tolerate arbitrary keyword arguments."""

    def __init__(self, logger: logging.Logger) -> None:
        self._l = logger

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        extra_str = " ".join(f"{k}={v!r}" for k, v in kwargs.items()) if kwargs else ""
        self._l.debug(f"{msg} {extra_str}".rstrip(), *args)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        extra_str = " ".join(f"{k}={v!r}" for k, v in kwargs.items()) if kwargs else ""
        self._l.info(f"{msg} {extra_str}".rstrip(), *args)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        extra_str = " ".join(f"{k}={v!r}" for k, v in kwargs.items()) if kwargs else ""
        self._l.warning(f"{msg} {extra_str}".rstrip(), *args)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        extra_str = " ".join(f"{k}={v!r}" for k, v in kwargs.items()) if kwargs else ""
        self._l.error(f"{msg} {extra_str}".rstrip(), *args)


def configure_logging(log_level: str = "INFO", log_format: str = "console") -> None:
    """Configure structlog for the application."""
    level = getattr(logging, log_level.upper(), logging.INFO)

    if _HAS_STRUCTLOG:
        shared_processors: list[Any] = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
        ]

        if log_format == "json":
            processors = shared_processors + [
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(),
            ]
        else:
            processors = shared_processors + [
                structlog.dev.ConsoleRenderer(colors=False),
            ]

        structlog.configure(
            processors=processors,
            wrapper_class=structlog.make_filtering_bound_logger(level),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(sys.stdout),
            cache_logger_on_first_use=True,
        )

    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
        level=level,
    )


def get_logger(name: str) -> Any:
    """Return a logger instance for the given module name."""
    if _HAS_STRUCTLOG:
        return structlog.get_logger(name)
    return _StdlibKwargLogger(logging.getLogger(name))
