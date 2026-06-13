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
BlenderQueueCapacityError = job_control.BlenderQueueCapacityError
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


def test_scheduler_runs_user_jobs_fifo_without_parallel_execution() -> None:
    registry = BlenderJobRegistry(prefix="test")
    scheduler = BlenderJobScheduler(registry)
    first = registry.create_job()
    second = registry.create_job()
    observed: list[str] = []
    active_count = 0
    max_active_count = 0

    def make_job(label: str):
        def run(_token):
            nonlocal active_count, max_active_count
            active_count += 1
            max_active_count = max(max_active_count, active_count)
            observed.append(label)
            time.sleep(0.01)
            active_count -= 1
            return label

        return run

    scheduler.submit(first.job_id, make_job("first"))
    scheduler.submit(second.job_id, make_job("second"))

    first_snapshot = registry.require_snapshot(first.job_id)
    second_snapshot = registry.require_snapshot(second.job_id)
    assert first_snapshot.queue_position == 1
    assert second_snapshot.queue_position == 2

    processed = scheduler.step()
    assert processed == 2
    assert observed == ["first", "second"]
    assert max_active_count == 1
    assert registry.require_snapshot(first.job_id).status == BlenderJobStatus.COMPLETED
    assert registry.require_snapshot(second.job_id).result == "second"


def test_scheduler_prioritizes_system_operation_after_active_job() -> None:
    registry = BlenderJobRegistry(prefix="test")
    scheduler = BlenderJobScheduler(registry)
    first = registry.create_job()
    second = registry.create_job()
    started = threading.Event()
    release = threading.Event()
    observed: list[str] = []
    system_result: list[str] = []

    def first_job(_token):
        observed.append("first-start")
        started.set()
        assert release.wait(1.0)
        observed.append("first-end")
        return "first"

    def second_job(_token):
        observed.append("second")
        return "second"

    scheduler.submit(first.job_id, first_job)
    scheduler.submit(second.job_id, second_job)

    runner = threading.Thread(target=scheduler.step)
    runner.start()
    assert started.wait(1.0)

    def run_system_operation() -> None:
        result = scheduler.run_system_operation(
            "get_scene_info",
            lambda: observed.append("system") or "system",
            timeout_seconds=1.0,
        )
        system_result.append(result)

    system_runner = threading.Thread(target=run_system_operation)
    system_runner.start()

    deadline = time.monotonic() + 1.0
    while time.monotonic() < deadline:
        queue_status = scheduler.get_queue_status()
        if queue_status["queued_system_operations"] == 1:
            break
        time.sleep(0.01)
    assert scheduler.get_queue_status()["queued_system_operations"] == 1

    release.set()
    runner.join(1.0)
    system_runner.join(1.0)

    assert not runner.is_alive()
    assert not system_runner.is_alive()
    assert observed == ["first-start", "first-end", "system", "second"]
    assert system_result == ["system"]
    assert registry.require_snapshot(second.job_id).status == BlenderJobStatus.COMPLETED


def test_scheduler_mixed_adversarial_sequence_preserves_order_and_metadata() -> None:
    registry = BlenderJobRegistry(prefix="test")
    scheduler = BlenderJobScheduler(registry)
    active = registry.create_job()
    first_queued = registry.create_job()
    cancelled_queued = registry.create_job()
    second_queued = registry.create_job()
    late_queued = registry.create_job()
    started = threading.Event()
    release = threading.Event()
    observed: list[str] = []

    def active_job(_token):
        observed.append("active-start")
        started.set()
        assert release.wait(1.0)
        observed.append("active-end")
        return "active"

    def make_user_job(label: str):
        def run(_token):
            observed.append(label)
            return label

        return run

    scheduler.submit(active.job_id, active_job)
    scheduler.submit(first_queued.job_id, make_user_job("user-1"))
    scheduler.submit(cancelled_queued.job_id, make_user_job("cancelled-should-not-run"))
    scheduler.submit(second_queued.job_id, make_user_job("user-2"))

    runner = threading.Thread(target=scheduler.step)
    runner.start()
    assert started.wait(1.0)

    scheduler.submit_system_operation("get_scene_info", lambda: observed.append("sys-1"))
    scheduler.submit_system_operation("get_object_info", lambda: observed.append("sys-2"))
    scheduler.submit(late_queued.job_id, make_user_job("user-3"))
    registry.request_cancel(cancelled_queued.job_id, reason="adversarial")

    queue_status = scheduler.get_queue_status()
    assert queue_status["active_item"]["job_id"] == active.job_id
    assert queue_status["queued_user_jobs"] == 4
    assert queue_status["queued_system_operations"] == 2

    queued_positions = {
        snapshot.job_id: snapshot.queue_position
        for snapshot in registry.list_snapshots(include_terminal=False)
        if snapshot.queue_name == "user_job" and not snapshot.active
    }
    assert queued_positions == {
        first_queued.job_id: 1,
        cancelled_queued.job_id: 2,
        second_queued.job_id: 3,
        late_queued.job_id: 4,
    }

    release.set()
    runner.join(1.0)

    assert not runner.is_alive()
    assert observed == [
        "active-start",
        "active-end",
        "sys-1",
        "sys-2",
        "user-1",
        "user-2",
        "user-3",
    ]
    assert scheduler.get_active_item() is None
    assert scheduler.get_queue_status()["queued_user_jobs"] == 0
    assert registry.require_snapshot(cancelled_queued.job_id).status == (
        BlenderJobStatus.CANCELLED
    )
    assert registry.require_snapshot(late_queued.job_id).result == "user-3"


def test_queued_job_timeout_clock_starts_when_job_runs() -> None:
    registry = BlenderJobRegistry(prefix="test")
    scheduler = BlenderJobScheduler(registry)
    active = registry.create_job()
    timed = registry.create_job(job_timeout_seconds=0.05)
    started = threading.Event()
    release = threading.Event()
    observed: list[str] = []

    def active_job(_token):
        started.set()
        assert release.wait(1.0)
        observed.append("active")
        return "active"

    def timed_job(token):
        observed.append("timed-started")
        time.sleep(0.08)
        token.check_cancelled()
        observed.append("timed-finished")
        return "timed"

    scheduler.submit(active.job_id, active_job)
    scheduler.submit(timed.job_id, timed_job)

    runner = threading.Thread(target=scheduler.step)
    runner.start()
    assert started.wait(1.0)
    time.sleep(0.1)

    assert registry.require_snapshot(timed.job_id).status == BlenderJobStatus.QUEUED

    release.set()
    runner.join(1.0)

    assert not runner.is_alive()
    assert observed == ["active", "timed-started"]
    terminal = registry.require_snapshot(timed.job_id)
    assert terminal.status == BlenderJobStatus.TIMED_OUT
    assert terminal.started_at is not None


def test_queued_job_cancelled_before_start_does_not_run_body() -> None:
    registry = BlenderJobRegistry(prefix="test")
    scheduler = BlenderJobScheduler(registry)
    first = registry.create_job()
    second = registry.create_job()
    started = threading.Event()
    release = threading.Event()
    executed = False

    def first_job(_token):
        started.set()
        assert release.wait(1.0)
        return "first"

    def second_job(_token):
        nonlocal executed
        executed = True
        return "second"

    scheduler.submit(first.job_id, first_job)
    scheduler.submit(second.job_id, second_job)

    runner = threading.Thread(target=scheduler.step)
    runner.start()
    assert started.wait(1.0)

    cancelled = registry.request_cancel(second.job_id, reason="pre-start")
    assert cancelled is not None
    assert cancelled.cancel_requested

    release.set()
    runner.join(1.0)

    assert not runner.is_alive()
    assert executed is False
    assert registry.require_snapshot(second.job_id).status == BlenderJobStatus.CANCELLED


def test_scheduler_queue_capacity_errors_are_structured() -> None:
    registry = BlenderJobRegistry(prefix="test")
    scheduler = BlenderJobScheduler(
        registry,
        max_queued_user_jobs=1,
        max_queued_system_operations=1,
    )
    first = registry.create_job()
    second = registry.create_job()

    scheduler.submit(first.job_id, lambda token: "first")
    with pytest.raises(BlenderQueueCapacityError) as user_error:
        scheduler.submit(second.job_id, lambda token: "second")

    assert user_error.value.to_dict() == {
        "error_code": "queue_capacity_exceeded",
        "queue_name": "user_job",
        "limit": 1,
        "attempted_item_id": second.job_id,
    }

    scheduler.submit_system_operation("get_scene_info", lambda: "scene")
    with pytest.raises(BlenderQueueCapacityError) as system_error:
        scheduler.submit_system_operation("get_object_info", lambda: "object")

    assert system_error.value.to_dict()["queue_name"] == "system_operation"


def test_registry_prunes_terminal_records_with_retention_limit() -> None:
    registry = BlenderJobRegistry(prefix="test", terminal_retention_limit=1)
    first = registry.create_job()
    second = registry.create_job()

    registry.mark_completed(first.job_id, "first")
    registry.mark_completed(second.job_id, "second")

    snapshots = registry.list_snapshots()
    assert [snapshot.job_id for snapshot in snapshots] == [second.job_id]
    assert registry.get_snapshot(first.job_id) is None


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
