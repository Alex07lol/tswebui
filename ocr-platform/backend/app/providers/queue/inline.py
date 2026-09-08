"""Inline (synchronous) queue provider for development and testing.

Runs tasks immediately in the calling thread. Not suitable for production.
"""
from __future__ import annotations

import traceback
import uuid
from typing import Any, Callable

from app.core.logging import get_logger

log = get_logger(__name__)

_task_registry: dict[str, Callable[..., Any]] = {}
_job_store: dict[str, dict[str, Any]] = {}


def register_task(name: str, fn: Callable[..., Any]) -> None:
    """Register a callable as a named background task."""
    _task_registry[name] = fn


class InlineQueueProvider:
    """Executes tasks synchronously for development/testing."""

    def enqueue(
        self,
        task_name: str,
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] | None = None,
        job_id: str | None = None,
    ) -> str:
        """Run the task immediately and record its outcome."""
        jid = job_id or str(uuid.uuid4())
        fn = _task_registry.get(task_name)
        if fn is None:
            _job_store[jid] = {"status": "failed", "error": f"Unknown task: {task_name}"}
            return jid

        _job_store[jid] = {"status": "running"}
        try:
            fn(*(args or ()), **(kwargs or {}))
            _job_store[jid] = {"status": "completed"}
            log.info("Inline task completed", task=task_name, job_id=jid)
        except Exception as exc:
            _job_store[jid] = {"status": "failed", "error": str(exc)}
            log.error("Inline task failed", task=task_name, job_id=jid, exc=traceback.format_exc())
        return jid

    def get_status(self, job_id: str) -> dict[str, Any]:
        """Return stored job status."""
        return _job_store.get(job_id, {"status": "unknown"})
