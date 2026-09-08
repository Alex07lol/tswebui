"""Structured logging using structlog with stdlib fallback."""
from __future__ import annotations

import logging
import sys
from typing import Any


def configure_logging(log_level: str = "INFO", log_format: str = "console") -> None:
    """Configure structlog for the application."""
    try:
        import structlog

        level = getattr(logging, log_level.upper(), logging.INFO)

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

        logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level)

    except ImportError:
        logging.basicConfig(
            level=getattr(logging, log_level.upper(), logging.INFO),
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            stream=sys.stdout,
        )


def get_logger(name: str) -> Any:
    """Return a bound logger for the given module name."""
    try:
        import structlog
        return structlog.get_logger(name)
    except ImportError:
        return logging.getLogger(name)
