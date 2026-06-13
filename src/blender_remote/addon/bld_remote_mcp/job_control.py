"""Cooperative job control primitives for the Blender TCP add-on.

The types in this module intentionally do not import :mod:`bpy`. They are used
inside Blender, but keeping the state machine pure Python makes cancellation
semantics testable without launching Blender.
"""

from __future__ import annotations

import itertools
import threading
import time
import traceback as traceback_module
from collections import deque
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


class BlenderMainThreadItemKind(StrEnum):
    """Kinds of work that can own the Blender main-thread executor."""

    USER_JOB = "user_job"
    SYSTEM_OPERATION = "system_operation"


class BlenderQueueCapacityError(RuntimeError):
    """Raised when a bounded scheduler queue cannot accept more work."""

    error_code = "queue_capacity_exceeded"

    def __init__(
        self,
        *,
        queue_name: str,
        limit: int,
        attempted_item_id: str | None = None,
    ) -> None:
        self.queue_name = queue_name
        self.limit = limit
        self.attempted_item_id = attempted_item_id
        message = f"{queue_name} queue capacity exceeded"
        if attempted_item_id is not None:
            message = f"{message} for {attempted_item_id}"
        message = f"{message}; limit={limit}"
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-friendly structured error metadata."""
        return {
            "error_code": self.error_code,
            "queue_name": self.queue_name,
            "limit": self.limit,
            "attempted_item_id": self.attempted_item_id,
        }


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
    active: bool = False
    queue_position: int | None = None
    queue_name: str | None = None

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
            "active": self.active,
            "queue_position": self.queue_position,
            "queue_name": self.queue_name,
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
    active: bool = False
    queue_position: int | None = None
    queue_name: str | None = None
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
            active=self.active,
            queue_position=self.queue_position,
            queue_name=self.queue_name,
        )


class BlenderJobRegistry:
    """Thread-safe registry for Blender-side cooperative jobs."""

    def __init__(
        self,
        prefix: str = "job",
        *,
        terminal_retention_limit: int | None = None,
    ) -> None:
        self._prefix = prefix
        self._terminal_retention_limit = terminal_retention_limit
        self._counter = itertools.count(1)
        self._jobs: dict[str, _BlenderJobRecord] = {}
        self._lock = threading.RLock()

    @property
    def terminal_retention_limit(self) -> int | None:
        """Return the maximum retained terminal job records, if bounded."""
        return self._terminal_retention_limit

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

    def list_snapshots(
        self,
        *,
        status: BlenderJobStatus | str | None = None,
        include_terminal: bool = True,
        limit: int | None = None,
    ) -> list[BlenderJobSnapshot]:
        """Return snapshots for known jobs in creation order."""
        if isinstance(status, str):
            try:
                status = BlenderJobStatus(status)
            except ValueError as exc:
                raise ValueError(f"Unknown job status: {status}") from exc

        with self._lock:
            snapshots = [
                record.snapshot()
                for record in sorted(self._jobs.values(), key=lambda item: item.created_at)
                if (status is None or record.status == status)
                and (include_terminal or record.status not in TERMINAL_JOB_STATUSES)
            ]

        if limit is not None:
            snapshots = snapshots[: max(0, limit)]
        return snapshots

    def set_queue_metadata(
        self,
        job_id: str,
        *,
        queue_position: int | None,
        queue_name: str | None,
    ) -> BlenderJobSnapshot | None:
        """Update queue metadata for a known job without changing its lifecycle."""
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                return None
            if record.status in TERMINAL_JOB_STATUSES:
                return record.snapshot()
            record.queue_position = queue_position
            record.queue_name = queue_name
            record.active = False
            record.updated_at = time.time()
            return record.snapshot()

    def set_active_metadata(
        self,
        job_id: str,
        *,
        active: bool,
        queue_name: str | None = None,
    ) -> BlenderJobSnapshot | None:
        """Update active-item metadata for a known job."""
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                return None
            if record.status in TERMINAL_JOB_STATUSES:
                return record.snapshot()
            record.active = active
            record.queue_position = None
            record.queue_name = queue_name if active else None
            record.updated_at = time.time()
            return record.snapshot()

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
            record.active = True
            record.queue_position = None
            record.queue_name = BlenderMainThreadItemKind.USER_JOB.value
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
            record.active = False
            record.queue_position = None
            record.queue_name = None
            record.result = result
            record.error = error
            record.traceback = traceback
            if metadata:
                record.metadata.update(metadata)
            record.completed.set()
            snapshot = record.snapshot()
            self._prune_terminal_records_locked()
            return snapshot

    def _prune_terminal_records_locked(self) -> None:
        limit = self._terminal_retention_limit
        if limit is None:
            return
        if limit < 0:
            return

        terminal_records = [
            record
            for record in self._jobs.values()
            if record.status in TERMINAL_JOB_STATUSES
        ]
        overflow = len(terminal_records) - limit
        if overflow <= 0:
            return

        terminal_records.sort(
            key=lambda record: record.completed_at or record.updated_at or record.created_at
        )
        for record in terminal_records[:overflow]:
            self._jobs.pop(record.job_id, None)


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
SystemOperationBody = Callable[[], Any]


@dataclass
class _ScheduledJob:
    job_id: str
    body: JobBody


@dataclass
class _ScheduledSystemOperation:
    operation_id: str
    command_type: str
    body: SystemOperationBody
    created_at: float
    completed: threading.Event = field(default_factory=threading.Event)
    result: Any = None
    error: str | None = None
    traceback: str | None = None


@dataclass(frozen=True)
class BlenderMainThreadItemSnapshot:
    """JSON-friendly snapshot of the active main-thread item."""

    kind: BlenderMainThreadItemKind
    item_id: str
    started_at: float
    job_id: str | None = None
    operation_id: str | None = None
    command_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert the active item snapshot to a JSON-serializable dictionary."""
        return {
            "kind": self.kind.value,
            "item_id": self.item_id,
            "job_id": self.job_id,
            "operation_id": self.operation_id,
            "command_type": self.command_type,
            "started_at": self.started_at,
        }


class BlenderJobScheduler:
    """Serialized scheduler for Blender main-thread work.

    User jobs and system-defined Blender operations share one active executor.
    Pending system operations have priority over pending user jobs, but no item
    can interrupt the item that is already running.
    """

    def __init__(
        self,
        registry: BlenderJobRegistry,
        *,
        max_queued_user_jobs: int | None = None,
        max_queued_system_operations: int | None = None,
    ) -> None:
        self._registry = registry
        self._user_queue: deque[_ScheduledJob] = deque()
        self._system_operation_queue: deque[_ScheduledSystemOperation] = deque()
        self._active_item: BlenderMainThreadItemSnapshot | None = None
        self._operation_counter = itertools.count(1)
        self._max_queued_user_jobs = max_queued_user_jobs
        self._max_queued_system_operations = max_queued_system_operations
        self._lock = threading.RLock()

    @property
    def active_job_id(self) -> str | None:
        """Return the currently running job id, if any."""
        with self._lock:
            if (
                self._active_item is None
                or self._active_item.kind != BlenderMainThreadItemKind.USER_JOB
            ):
                return None
            return self._active_item.job_id

    def get_active_item(self) -> dict[str, Any] | None:
        """Return the active main-thread item without blocking on the item."""
        with self._lock:
            return None if self._active_item is None else self._active_item.to_dict()

    def get_queue_status(self) -> dict[str, Any]:
        """Return current queue lengths, ids, and configured capacities."""
        with self._lock:
            active_item = (
                None if self._active_item is None else self._active_item.to_dict()
            )
            queued_user_job_ids = [job.job_id for job in self._user_queue]
            queued_system_operations = [
                {
                    "operation_id": operation.operation_id,
                    "command_type": operation.command_type,
                    "queue_position": index,
                    "created_at": operation.created_at,
                }
                for index, operation in enumerate(self._system_operation_queue, start=1)
            ]
            return {
                "active_item": active_item,
                "queued_user_jobs": len(self._user_queue),
                "queued_user_job_ids": queued_user_job_ids,
                "queued_system_operations": len(self._system_operation_queue),
                "queued_system_operation_ids": [
                    operation["operation_id"] for operation in queued_system_operations
                ],
                "queued_system_operation_details": queued_system_operations,
                "capacity": {
                    "max_queued_user_jobs": self._max_queued_user_jobs,
                    "max_queued_system_operations": self._max_queued_system_operations,
                    "terminal_job_retention_limit": self._registry.terminal_retention_limit,
                },
            }

    def submit(self, job_id: str, body: JobBody) -> BlenderJobSnapshot:
        """Queue one main-thread job for later scheduler execution."""
        with self._lock:
            self._ensure_capacity_locked(
                queue_name=BlenderMainThreadItemKind.USER_JOB.value,
                queue_length=len(self._user_queue),
                limit=self._max_queued_user_jobs,
                attempted_item_id=job_id,
            )
            self._user_queue.append(_ScheduledJob(job_id=job_id, body=body))
            self._refresh_user_queue_positions_locked()
        return self._registry.require_snapshot(job_id)

    def submit_system_operation(
        self,
        command_type: str,
        body: SystemOperationBody,
    ) -> _ScheduledSystemOperation:
        """Queue one allowlisted system operation for main-thread execution."""
        with self._lock:
            operation_id = f"sysop-{next(self._operation_counter)}"
            self._ensure_capacity_locked(
                queue_name=BlenderMainThreadItemKind.SYSTEM_OPERATION.value,
                queue_length=len(self._system_operation_queue),
                limit=self._max_queued_system_operations,
                attempted_item_id=operation_id,
            )
            operation = _ScheduledSystemOperation(
                operation_id=operation_id,
                command_type=command_type,
                body=body,
                created_at=time.time(),
            )
            self._system_operation_queue.append(operation)
            return operation

    def run_system_operation(
        self,
        command_type: str,
        body: SystemOperationBody,
        *,
        timeout_seconds: float | None,
    ) -> Any:
        """Queue a system operation and wait for its result."""
        operation = self.submit_system_operation(command_type, body)
        if not operation.completed.wait(timeout_seconds):
            raise TimeoutError(
                f"System operation {operation.operation_id} timed out while waiting"
            )
        if operation.error is not None:
            raise RuntimeError(operation.error)
        return operation.result

    def step(self, max_budget_ms: float | None = None) -> int:
        """Run queued main-thread items until the budget is exhausted.

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

            scheduled_job: _ScheduledJob | None = None
            scheduled_operation: _ScheduledSystemOperation | None = None

            with self._lock:
                if self._active_item is not None:
                    return processed
                if self._system_operation_queue:
                    scheduled_operation = self._system_operation_queue.popleft()
                    self._active_item = BlenderMainThreadItemSnapshot(
                        kind=BlenderMainThreadItemKind.SYSTEM_OPERATION,
                        item_id=scheduled_operation.operation_id,
                        operation_id=scheduled_operation.operation_id,
                        command_type=scheduled_operation.command_type,
                        started_at=time.time(),
                    )
                elif self._user_queue:
                    scheduled_job = self._user_queue.popleft()
                    self._active_item = BlenderMainThreadItemSnapshot(
                        kind=BlenderMainThreadItemKind.USER_JOB,
                        item_id=scheduled_job.job_id,
                        job_id=scheduled_job.job_id,
                        started_at=time.time(),
                    )
                    self._registry.set_active_metadata(
                        scheduled_job.job_id,
                        active=True,
                        queue_name=BlenderMainThreadItemKind.USER_JOB.value,
                    )
                    self._refresh_user_queue_positions_locked()
                else:
                    return processed

            try:
                if scheduled_operation is not None:
                    self._run_system_operation(scheduled_operation)
                elif scheduled_job is not None:
                    self._run_user_job(scheduled_job)
            finally:
                processed += 1
                with self._lock:
                    if scheduled_job is not None:
                        self._registry.set_active_metadata(
                            scheduled_job.job_id,
                            active=False,
                        )
                    self._active_item = None

    def _run_user_job(self, scheduled: _ScheduledJob) -> None:
        snapshot = self._registry.require_snapshot(scheduled.job_id)
        token = BlenderJobCancellationToken(self._registry, scheduled.job_id)

        try:
            if snapshot.cancel_requested:
                self._registry.mark_cancelled(
                    scheduled.job_id, reason="cancelled before start"
                )
                return

            self._registry.mark_running(scheduled.job_id)
            token.check_cancelled()
            result = scheduled.body(token)
            self._registry.mark_completed(scheduled.job_id, result)
        except BlenderJobTimedOut as exc:
            self._registry.mark_timed_out(scheduled.job_id, error=str(exc))
        except BlenderJobCancelled as exc:
            self._registry.mark_cancelled(scheduled.job_id, reason=str(exc))
        except Exception as exc:
            self._registry.mark_failed(
                scheduled.job_id,
                str(exc),
                traceback=traceback_module.format_exc(),
            )

    def _run_system_operation(self, operation: _ScheduledSystemOperation) -> None:
        try:
            operation.result = operation.body()
        except Exception as exc:
            operation.error = str(exc)
            operation.traceback = traceback_module.format_exc()
        finally:
            operation.completed.set()

    def _refresh_user_queue_positions_locked(self) -> None:
        for index, scheduled in enumerate(self._user_queue, start=1):
            self._registry.set_queue_metadata(
                scheduled.job_id,
                queue_position=index,
                queue_name=BlenderMainThreadItemKind.USER_JOB.value,
            )

    def _ensure_capacity_locked(
        self,
        *,
        queue_name: str,
        queue_length: int,
        limit: int | None,
        attempted_item_id: str | None,
    ) -> None:
        if limit is None:
            return
        if queue_length >= limit:
            raise BlenderQueueCapacityError(
                queue_name=queue_name,
                limit=limit,
                attempted_item_id=attempted_item_id,
            )
