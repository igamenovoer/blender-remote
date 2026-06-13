from __future__ import annotations

import importlib
import sys
import threading
import time
import types
from collections.abc import Iterator
from typing import Any

import pytest


class FakeTimers:
    def __init__(self) -> None:
        self.registered: list[Any] = []

    def register(self, callback: Any, *, first_interval: float = 0.0) -> None:
        self.registered.append(callback)

    def is_registered(self, callback: Any) -> bool:
        return callback in self.registered

    def unregister(self, callback: Any) -> None:
        self.registered.remove(callback)


@pytest.fixture()
def addon_module(monkeypatch: pytest.MonkeyPatch) -> Iterator[Any]:
    props_module = types.ModuleType("bpy.props")
    props_module.BoolProperty = lambda **_kwargs: None

    fake_bpy = types.ModuleType("bpy")
    fake_bpy.app = types.SimpleNamespace(
        background=False,
        timers=FakeTimers(),
    )
    fake_bpy.props = props_module
    fake_bpy.ops = types.SimpleNamespace(
        wm=types.SimpleNamespace(quit_blender=lambda: None)
    )
    fake_bpy.types = types.SimpleNamespace(Scene=type("Scene", (), {}))
    fake_bpy.data = types.SimpleNamespace(scenes=[])

    monkeypatch.setitem(sys.modules, "bpy", fake_bpy)
    monkeypatch.setitem(sys.modules, "bpy.props", props_module)
    sys.modules.pop("blender_remote.addon.bld_remote_mcp", None)
    module = importlib.import_module("blender_remote.addon.bld_remote_mcp")
    yield module
    sys.modules.pop("blender_remote.addon.bld_remote_mcp", None)


def test_execute_code_waits_for_terminal_scheduler_result(addon_module: Any) -> None:
    server = addon_module.BldRemoteMCPServer()
    server.running = True
    stop = threading.Event()

    def pump_scheduler() -> None:
        while not stop.is_set():
            server.step()
            time.sleep(0.005)

    pump = threading.Thread(target=pump_scheduler)
    pump.start()
    try:
        response = server._execute_job_control_command(
            {
                "type": "execute_code",
                "params": {
                    "code": "print('sync-done')",
                    "wait_timeout_seconds": 1.0,
                },
            }
        )
    finally:
        stop.set()
        pump.join(1.0)

    assert response["status"] == "success"
    assert response["result"]["status"] == "completed"
    assert response["result"]["result"] == "sync-done\n"
    assert response["result"]["job_id"].startswith("bld-job-")


def test_submit_code_job_returns_job_id_before_completion(addon_module: Any) -> None:
    server = addon_module.BldRemoteMCPServer()
    server.running = True

    response = server._execute_job_control_command(
        {
            "type": "submit_code_job",
            "params": {"code": "print('async-not-yet')"},
        }
    )
    job_id = response["result"]["job_id"]
    status = server._execute_job_control_command(
        {"type": "get_job_status", "params": {"job_id": job_id}}
    )

    assert response["status"] == "success"
    assert response["result"]["terminal"] is False
    assert response["result"]["status"] == "queued"
    assert status["result"]["status"] == "queued"

    server.step()
    result = server._execute_job_control_command(
        {"type": "get_job_result", "params": {"job_id": job_id}}
    )
    assert result["result"]["status"] == "completed"
    assert result["result"]["result"]["result"] == "async-not-yet\n"


def test_submit_code_jobs_queue_fifo_with_inspectable_metadata(addon_module: Any) -> None:
    server = addon_module.BldRemoteMCPServer()
    server.running = True

    first = server._execute_user_job_command(
        {"type": "submit_code_job", "params": {"code": "print('first')"}}
    )
    second = server._execute_user_job_command(
        {"type": "submit_code_job", "params": {"code": "print('second')"}}
    )
    queue_status = server._execute_immediate_control_command(
        {"type": "get_queue_status", "params": {}}
    )
    listed = server._execute_immediate_control_command(
        {"type": "list_jobs", "params": {"include_terminal": False}}
    )

    assert first["status"] == "success"
    assert second["status"] == "success"
    assert first["result"]["queue_position"] == 1
    assert second["result"]["queue_position"] == 2
    assert queue_status["result"]["queued_user_jobs"] == 2
    assert listed["result"]["count"] == 2

    server.step()

    first_result = server.get_job_result(first["result"]["job_id"])
    second_result = server.get_job_result(second["result"]["job_id"])
    assert first_result["status"] == "completed"
    assert second_result["status"] == "completed"
    assert first_result["result"]["result"] == "first\n"
    assert second_result["result"]["result"] == "second\n"


def test_sync_execute_code_waits_behind_queued_async_jobs(addon_module: Any) -> None:
    server = addon_module.BldRemoteMCPServer()
    server.running = True

    first = server._execute_user_job_command(
        {
            "type": "submit_code_job",
            "params": {"code": "import time\ntime.sleep(0.02)\nprint('first')"},
        }
    )
    second = server._execute_user_job_command(
        {
            "type": "submit_code_job",
            "params": {"code": "import time\ntime.sleep(0.02)\nprint('second')"},
        }
    )
    sync_response: dict[str, Any] = {}

    def run_sync_execute() -> None:
        sync_response.update(
            server._execute_user_job_command(
                {
                    "type": "execute_code",
                    "params": {
                        "code": "print('third')",
                        "wait_timeout_seconds": 1.0,
                    },
                }
            )
        )

    sync_thread = threading.Thread(target=run_sync_execute)
    sync_thread.start()

    deadline = time.monotonic() + 1.0
    while time.monotonic() < deadline:
        queue_status = server.get_queue_status()
        if queue_status["queued_user_jobs"] == 3:
            break
        time.sleep(0.01)
    assert server.get_queue_status()["queued_user_jobs"] == 3

    deadline = time.monotonic() + 2.0
    while sync_thread.is_alive() and time.monotonic() < deadline:
        server.step()
        time.sleep(0.005)
    sync_thread.join(1.0)

    assert not sync_thread.is_alive()
    assert sync_response["status"] == "success"
    assert sync_response["result"]["job_id"] == "bld-job-3"
    assert server.get_job_result(first["result"]["job_id"])["result"]["result"] == "first\n"
    assert server.get_job_result(second["result"]["job_id"])["result"]["result"] == "second\n"
    assert sync_response["result"]["result"] == "third\n"

    first_done = server.job_registry.require_snapshot(first["result"]["job_id"]).completed_at
    second_done = server.job_registry.require_snapshot(second["result"]["job_id"]).completed_at
    third_done = server.job_registry.require_snapshot("bld-job-3").completed_at
    assert first_done is not None
    assert second_done is not None
    assert third_done is not None
    assert first_done <= second_done <= third_done


def test_cancel_job_is_acknowledged_while_cooperative_job_runs(addon_module: Any) -> None:
    server = addon_module.BldRemoteMCPServer()
    server.running = True
    stop = threading.Event()

    def pump_scheduler() -> None:
        while not stop.is_set():
            server.step()
            time.sleep(0.005)

    pump = threading.Thread(target=pump_scheduler)
    pump.start()
    try:
        submitted = server._execute_job_control_command(
            {
                "type": "submit_code_job",
                "params": {
                    "code": (
                        "import time\n"
                        "while True:\n"
                        "    time.sleep(0.01)\n"
                        "    check_cancelled()\n"
                    )
                },
            }
        )
        job_id = submitted["result"]["job_id"]
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline:
            status = server.get_job_status(job_id)["status"]
            if status == "running":
                break
            time.sleep(0.01)
        assert server.get_job_status(job_id)["status"] == "running"

        cancelled = server._execute_job_control_command(
            {
                "type": "cancel_job",
                "params": {"job_id": job_id, "reason": "unit"},
            }
        )
        terminal = server.job_registry.wait(job_id, 1.0)
    finally:
        stop.set()
        pump.join(1.0)

    assert cancelled["status"] == "success"
    assert cancelled["result"]["status"] == "cancelling"
    assert cancelled["result"]["cancel_requested"] is True
    assert terminal is not None
    assert terminal.status.value == "cancelled"


def test_unknown_typed_command_returns_error_and_legacy_still_works(
    addon_module: Any,
) -> None:
    server = addon_module.BldRemoteMCPServer()

    unknown = server._execute_command_internal({"type": "unknown_rpc_command"})
    legacy = server._execute_command_internal({"message": "hello"})

    assert unknown == {
        "status": "error",
        "error_code": "unknown_rpc_command",
        "message": "Unknown command: unknown_rpc_command",
    }
    assert legacy["response"] == "OK"
    assert legacy["message"] == "Printed message: hello"


def test_priority_system_operation_rejects_arbitrary_code(addon_module: Any) -> None:
    server = addon_module.BldRemoteMCPServer()

    response = server._execute_command_sync(
        {
            "type": "priority_execute_code",
            "params": {"code": "print('not allowed')"},
        }
    )

    assert response["status"] == "error"
    assert response["error_code"] == "arbitrary_code_not_allowed_in_system_operation"
