"""Queue/job-backend interface."""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class QueueProvider(Protocol):
    """Interface for dispatching background tasks."""

    def enqueue(
        self,
        task_name: str,
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] | None = None,
        job_id: str | None = None,
    ) -> str:
        """Submit a named task to the queue and return a job handle ID."""
        ...

    def get_status(self, job_id: str) -> dict[str, Any]:
        """Return current job status dict with at least a 'status' key."""
        ...
