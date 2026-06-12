from __future__ import annotations

import importlib.util
import sys
import threading
import time
from pathlib import Path

import pytest

JOB_CONTROL_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "blender_remote"
    / "addon"
    / "bld_remote_mcp"
    / "job_control.py"
)

spec = importlib.util.spec_from_file_location("bld_remote_job_control", JOB_CONTROL_PATH)
assert spec is not None
assert spec.loader is not None
job_control = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = job_control
spec.loader.exec_module(job_control)

BlenderJobCancelled = job_control.BlenderJobCancelled
BlenderJobRegistry = job_control.BlenderJobRegistry
BlenderJobScheduler = job_control.BlenderJobScheduler
BlenderJobStatus = job_control.BlenderJobStatus


def test_registry_transitions_and_result_retrieval() -> None:
    registry = BlenderJobRegistry(prefix="test")

    created = registry.create_job(metadata={"purpose": "unit"})
    assert created.job_id == "test-1"
    assert created.status == BlenderJobStatus.QUEUED
    assert created.metadata == {"purpose": "unit"}

    running = registry.mark_running(created.job_id)
    assert running.status == BlenderJobStatus.RUNNING
    assert running.started_at is not None

    completed = registry.mark_completed(created.job_id, {"ok": True})
    assert completed.status == BlenderJobStatus.COMPLETED
    assert completed.result == {"ok": True}
    assert completed.terminal

    cancelled_after_complete = registry.request_cancel(created.job_id)
    assert cancelled_after_complete is not None
    assert cancelled_after_complete.status == BlenderJobStatus.COMPLETED
    assert cancelled_after_complete.result == {"ok": True}

    assert registry.wait(created.job_id, 0.01).status == BlenderJobStatus.COMPLETED


def test_cancel_is_idempotent_for_queued_job() -> None:
    registry = BlenderJobRegistry(prefix="test")
    created = registry.create_job()

    first = registry.request_cancel(created.job_id, reason="user")
    second = registry.request_cancel(created.job_id, reason="ignored")

    assert first is not None
    assert first.status == BlenderJobStatus.CANCELLING
    assert first.cancel_requested
    assert second is not None
    assert second.status == BlenderJobStatus.CANCELLING

    cancelled = registry.mark_cancelled(created.job_id, reason="checkpoint")
    assert cancelled.status == BlenderJobStatus.CANCELLED
    assert cancelled.metadata["cancel_reason"] == "checkpoint"

    completed_after_cancel = registry.mark_completed(created.job_id, {"late": True})
    assert completed_after_cancel.status == BlenderJobStatus.CANCELLED
    assert completed_after_cancel.result is None


def test_scheduler_enforces_single_pending_or_running_job() -> None:
    registry = BlenderJobRegistry(prefix="test")
    scheduler = BlenderJobScheduler(registry)
    first = registry.create_job()
    second = registry.create_job()

    scheduler.submit(first.job_id, lambda token: "done")

    with pytest.raises(RuntimeError):
        scheduler.submit(second.job_id, lambda token: "blocked")

    processed = scheduler.step()
    assert processed == 1
    assert registry.require_snapshot(first.job_id).status == BlenderJobStatus.COMPLETED

    scheduler.submit(second.job_id, lambda token: "done-2")
    scheduler.step()
    assert registry.require_snapshot(second.job_id).result == "done-2"


def test_control_plane_cancel_while_scheduler_job_is_running() -> None:
    registry = BlenderJobRegistry(prefix="test")
    scheduler = BlenderJobScheduler(registry)
    created = registry.create_job()
    started = threading.Event()

    def cooperative_job(token):
        started.set()
        while not token.cancel_requested:
            time.sleep(0.01)
        token.check_cancelled()
        raise AssertionError("cancel checkpoint should raise")

    scheduler.submit(created.job_id, cooperative_job)
    runner = threading.Thread(target=scheduler.step)
    runner.start()

    assert started.wait(1.0)
    cancelled = registry.request_cancel(created.job_id, reason="user")
    assert cancelled is not None
    assert cancelled.status == BlenderJobStatus.CANCELLING
    assert cancelled.cancel_requested

    runner.join(1.0)
    assert not runner.is_alive()
    terminal = registry.require_snapshot(created.job_id)
    assert terminal.status == BlenderJobStatus.CANCELLED
    assert terminal.terminal


def test_cancellation_token_checkpoint_raises() -> None:
    registry = BlenderJobRegistry(prefix="test")
    scheduler = BlenderJobScheduler(registry)
    created = registry.create_job()

    def cooperative_job(token):
        registry.request_cancel(token.job_id, reason="inside")
        with pytest.raises(BlenderJobCancelled):
            token.check_cancelled()
        raise BlenderJobCancelled("observed")

    scheduler.submit(created.job_id, cooperative_job)
    scheduler.step()

    terminal = registry.require_snapshot(created.job_id)
    assert terminal.status == BlenderJobStatus.CANCELLED
