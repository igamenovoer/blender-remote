"""Cooperative job control primitives for the Blender TCP add-on.

The types in this module intentionally do not import :mod:`bpy`. They are used
inside Blender, but keeping the state machine pure Python makes cancellation
semantics testable without launching Blender.
"""

from __future__ import annotations

import itertools
import queue
import threading
import time
import traceback as traceback_module
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class BlenderJobStatus(StrEnum):
    """Lifecycle states for one Blender-side job."""

    QUEUED = "queued"
    RUNNING = "running"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    KILLED = "killed"


TERMINAL_JOB_STATUSES = frozenset(
    {
        BlenderJobStatus.CANCELLED,
        BlenderJobStatus.COMPLETED,
        BlenderJobStatus.FAILED,
        BlenderJobStatus.TIMED_OUT,
        BlenderJobStatus.KILLED,
    }
)


class BlenderJobCancelled(Exception):
    """Raised when cooperative cancellation is observed at a checkpoint."""


class BlenderJobTimedOut(Exception):
    """Raised when a job observes its own timeout at a checkpoint."""


@dataclass(frozen=True)
class BlenderJobSnapshot:
    """Immutable, JSON-friendly view of a job record."""

    job_id: str
    status: BlenderJobStatus
    cancel_requested: bool
    created_at: float
    updated_at: float
    started_at: float | None = None
    completed_at: float | None = None
    job_timeout_seconds: float | None = None
    result: Any = None
    error: str | None = None
    traceback: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def terminal(self) -> bool:
        """Return whether this snapshot represents a terminal job state."""
        return self.status in TERMINAL_JOB_STATUSES

    def to_dict(self, include_result: bool = True) -> dict[str, Any]:
        """Convert the snapshot to a JSON-serializable dictionary."""
        data: dict[str, Any] = {
            "job_id": self.job_id,
            "status": self.status.value,
            "cancel_requested": self.cancel_requested,
            "terminal": self.terminal,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "job_timeout_seconds": self.job_timeout_seconds,
            "error": self.error,
            "traceback": self.traceback,
            "metadata": dict(self.metadata),
        }
        if include_result:
            data["result"] = self.result
        return data


@dataclass
class _BlenderJobRecord:
    job_id: str
    status: BlenderJobStatus
    created_at: float
    updated_at: float
    started_at: float | None = None
    completed_at: float | None = None
    job_timeout_seconds: float | None = None
    cancel_requested: bool = False
    result: Any = None
    error: str | None = None
    traceback: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    completed: threading.Event = field(default_factory=threading.Event)

    def snapshot(self) -> BlenderJobSnapshot:
        return BlenderJobSnapshot(
            job_id=self.job_id,
            status=self.status,
            cancel_requested=self.cancel_requested,
            created_at=self.created_at,
            updated_at=self.updated_at,
            started_at=self.started_at,
            completed_at=self.completed_at,
            job_timeout_seconds=self.job_timeout_seconds,
            result=self.result,
            error=self.error,
            traceback=self.traceback,
            metadata=dict(self.metadata),
        )


class BlenderJobRegistry:
    """Thread-safe registry for Blender-side cooperative jobs."""

    def __init__(self, prefix: str = "job") -> None:
        self._prefix = prefix
        self._counter = itertools.count(1)
        self._jobs: dict[str, _BlenderJobRecord] = {}
        self._lock = threading.RLock()

    def create_job(
        self,
        *,
        job_timeout_seconds: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> BlenderJobSnapshot:
        """Create and store a queued job record."""
        with self._lock:
            job_id = f"{self._prefix}-{next(self._counter)}"
            now = time.time()
            record = _BlenderJobRecord(
                job_id=job_id,
                status=BlenderJobStatus.QUEUED,
                created_at=now,
                updated_at=now,
                job_timeout_seconds=job_timeout_seconds,
                metadata=dict(metadata or {}),
            )
            self._jobs[job_id] = record
            return record.snapshot()

    def get_snapshot(self, job_id: str) -> BlenderJobSnapshot | None:
        """Return a snapshot for a known job id."""
        with self._lock:
            record = self._jobs.get(job_id)
            return None if record is None else record.snapshot()

    def require_snapshot(self, job_id: str) -> BlenderJobSnapshot:
        """Return a snapshot or raise KeyError for an unknown job id."""
        snapshot = self.get_snapshot(job_id)
        if snapshot is None:
            raise KeyError(job_id)
        return snapshot

    def mark_running(self, job_id: str) -> BlenderJobSnapshot:
        """Move a queued job to running unless it is already terminal/cancelling."""
        with self._lock:
            record = self._jobs[job_id]
            if record.status in TERMINAL_JOB_STATUSES:
                return record.snapshot()
            if record.status == BlenderJobStatus.CANCELLING:
                return record.snapshot()
            if record.status != BlenderJobStatus.QUEUED:
                raise RuntimeError(
                    f"Cannot mark {job_id} running from {record.status.value}"
                )
            now = time.time()
            record.status = BlenderJobStatus.RUNNING
            record.started_at = now
            record.updated_at = now
            return record.snapshot()

    def request_cancel(
        self, job_id: str, *, reason: str | None = None
    ) -> BlenderJobSnapshot | None:
        """Request cooperative cancellation for a queued or running job."""
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                return None
            if record.status in TERMINAL_JOB_STATUSES:
                return record.snapshot()
            record.cancel_requested = True
            record.status = BlenderJobStatus.CANCELLING
            record.updated_at = time.time()
            if reason is not None:
                record.metadata["cancel_reason"] = reason
            return record.snapshot()

    def mark_cancelled(
        self, job_id: str, *, result: Any = None, reason: str | None = None
    ) -> BlenderJobSnapshot:
        """Record a terminal cancelled outcome idempotently."""
        metadata = {"cancel_reason": reason} if reason is not None else None
        return self._mark_terminal(
            job_id,
            BlenderJobStatus.CANCELLED,
            result=result,
            metadata=metadata,
        )

    def mark_completed(self, job_id: str, result: Any = None) -> BlenderJobSnapshot:
        """Record a terminal successful outcome idempotently."""
        return self._mark_terminal(job_id, BlenderJobStatus.COMPLETED, result=result)

    def mark_failed(
        self,
        job_id: str,
        error: str,
        *,
        traceback: str | None = None,
        result: Any = None,
    ) -> BlenderJobSnapshot:
        """Record a terminal failed outcome idempotently."""
        return self._mark_terminal(
            job_id,
            BlenderJobStatus.FAILED,
            result=result,
            error=error,
            traceback=traceback,
        )

    def mark_timed_out(
        self, job_id: str, *, error: str | None = None, result: Any = None
    ) -> BlenderJobSnapshot:
        """Record a terminal timed-out outcome idempotently."""
        return self._mark_terminal(
            job_id,
            BlenderJobStatus.TIMED_OUT,
            result=result,
            error=error,
        )

    def mark_killed(
        self, job_id: str, *, error: str | None = None, result: Any = None
    ) -> BlenderJobSnapshot:
        """Record a terminal killed outcome idempotently."""
        return self._mark_terminal(
            job_id,
            BlenderJobStatus.KILLED,
            result=result,
            error=error,
        )

    def wait(
        self, job_id: str, timeout_seconds: float | None = None
    ) -> BlenderJobSnapshot | None:
        """Wait for a job to become terminal and return its latest snapshot."""
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                return None
            completed = record.completed

        completed.wait(timeout_seconds)
        return self.get_snapshot(job_id)

    def is_cancel_requested(self, job_id: str) -> bool:
        """Return whether cancellation was requested for a known job."""
        with self._lock:
            record = self._jobs.get(job_id)
            return bool(record and record.cancel_requested)

    def check_timeout(self, job_id: str) -> bool:
        """Request cancellation and return True if a job timeout has expired."""
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None or record.status in TERMINAL_JOB_STATUSES:
                return False
            if record.job_timeout_seconds is None or record.started_at is None:
                return False
            deadline = record.started_at + record.job_timeout_seconds
            if time.time() <= deadline:
                return False
            record.cancel_requested = True
            record.status = BlenderJobStatus.CANCELLING
            record.updated_at = time.time()
            record.metadata["timeout_requested"] = True
            return True

    def _mark_terminal(
        self,
        job_id: str,
        status: BlenderJobStatus,
        *,
        result: Any = None,
        error: str | None = None,
        traceback: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> BlenderJobSnapshot:
        with self._lock:
            record = self._jobs[job_id]
            if record.status in TERMINAL_JOB_STATUSES:
                return record.snapshot()
            now = time.time()
            record.status = status
            record.updated_at = now
            record.completed_at = now
            record.result = result
            record.error = error
            record.traceback = traceback
            if metadata:
                record.metadata.update(metadata)
            record.completed.set()
            return record.snapshot()


class BlenderJobCancellationToken:
    """Cancellation checkpoint helper exposed to executing job code."""

    def __init__(self, registry: BlenderJobRegistry, job_id: str) -> None:
        self._registry = registry
        self.job_id = job_id

    @property
    def cancel_requested(self) -> bool:
        """Return whether cooperative cancellation was requested."""
        return self._registry.is_cancel_requested(self.job_id)

    def check_cancelled(self) -> None:
        """Raise when cancellation or timeout has been observed."""
        if self._registry.check_timeout(self.job_id):
            raise BlenderJobTimedOut(f"Job {self.job_id} timed out")
        if self.cancel_requested:
            raise BlenderJobCancelled(f"Job {self.job_id} cancelled")


JobBody = Callable[[BlenderJobCancellationToken], Any]


@dataclass
class _ScheduledJob:
    job_id: str
    body: JobBody


class BlenderJobScheduler:
    """Single-active-job scheduler for Blender main-thread work."""

    def __init__(self, registry: BlenderJobRegistry) -> None:
        self._registry = registry
        self._queue: queue.Queue[_ScheduledJob] = queue.Queue()
        self._active_job_id: str | None = None
        self._lock = threading.RLock()

    @property
    def active_job_id(self) -> str | None:
        """Return the currently running job id, if any."""
        with self._lock:
            return self._active_job_id

    def submit(self, job_id: str, body: JobBody) -> BlenderJobSnapshot:
        """Queue one main-thread job for later scheduler execution."""
        with self._lock:
            if self._active_job_id is not None or not self._queue.empty():
                active = self._active_job_id or "queued job"
                raise RuntimeError(
                    f"Cannot submit {job_id}; {active} is active"
                )
            self._queue.put(_ScheduledJob(job_id=job_id, body=body))
        return self._registry.require_snapshot(job_id)

    def step(self, max_budget_ms: float | None = None) -> int:
        """Run queued jobs until the budget is exhausted.

        Python and Blender API calls cannot be preempted mid-call. The budget is
        therefore checked between jobs and prevents starting more work after the
        budget expires.
        """
        start = time.monotonic()
        processed = 0

        while True:
            if max_budget_ms is not None and processed > 0:
                elapsed_ms = (time.monotonic() - start) * 1000.0
                if elapsed_ms >= max_budget_ms:
                    return processed

            with self._lock:
                if self._active_job_id is not None:
                    return processed
                try:
                    scheduled = self._queue.get_nowait()
                except queue.Empty:
                    return processed
                self._active_job_id = scheduled.job_id

            try:
                snapshot = self._registry.require_snapshot(scheduled.job_id)
                token = BlenderJobCancellationToken(
                    self._registry, scheduled.job_id
                )

                if snapshot.cancel_requested:
                    self._registry.mark_cancelled(
                        scheduled.job_id, reason="cancelled before start"
                    )
                    continue

                self._registry.mark_running(scheduled.job_id)
                token.check_cancelled()
                result = scheduled.body(token)
                self._registry.mark_completed(scheduled.job_id, result)
            except BlenderJobTimedOut as exc:
                self._registry.mark_timed_out(scheduled.job_id, error=str(exc))
            except BlenderJobCancelled as exc:
                self._registry.mark_cancelled(
                    scheduled.job_id, reason=str(exc)
                )
            except Exception as exc:
                self._registry.mark_failed(
                    scheduled.job_id,
                    str(exc),
                    traceback=traceback_module.format_exc(),
                )
            finally:
                processed += 1
                with self._lock:
                    self._active_job_id = None
