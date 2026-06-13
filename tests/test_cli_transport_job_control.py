from __future__ import annotations

from typing import Any

from blender_remote.cli import transport


def test_submit_code_job_uses_async_command(monkeypatch) -> None:
    calls: list[tuple[str, dict[str, Any] | None, str, int, float]] = []

    def fake_send(command_type, params=None, host="127.0.0.1", port=6688, timeout=1.0):
        calls.append((command_type, params, host, port, timeout))
        return {"status": "success", "result": {"job_id": "job-1"}}

    monkeypatch.setattr(transport, "connect_and_send_command", fake_send)

    response = transport.submit_code_job(
        "print('hello')",
        job_timeout_seconds=12.5,
        host="blender.local",
        port=7777,
        timeout=4.0,
    )

    assert response["result"]["job_id"] == "job-1"
    assert calls == [
        (
            "submit_code_job",
            {
                "code": "print('hello')",
                "code_is_base64": False,
                "return_as_base64": False,
                "job_timeout_seconds": 12.5,
            },
            "blender.local",
            7777,
            4.0,
        )
    ]


def test_job_inspection_and_cancel_helpers(monkeypatch) -> None:
    commands: list[tuple[str, dict[str, Any] | None]] = []

    def fake_send(command_type, params=None, **kwargs):
        commands.append((command_type, params))
        return {"status": "success", "result": {"ok": True}}

    monkeypatch.setattr(transport, "connect_and_send_command", fake_send)

    transport.get_job_status("job-1")
    transport.get_job_result("job-1")
    transport.cancel_job("job-1", reason="user")

    assert commands == [
        ("get_job_status", {"job_id": "job-1"}),
        ("get_job_result", {"job_id": "job-1"}),
        ("cancel_job", {"job_id": "job-1", "reason": "user"}),
    ]


def test_queue_active_and_list_helpers(monkeypatch) -> None:
    commands: list[tuple[str, dict[str, Any] | None]] = []

    def fake_send(command_type, params=None, **kwargs):
        commands.append((command_type, params))
        return {"status": "success", "result": {"ok": True}}

    monkeypatch.setattr(transport, "connect_and_send_command", fake_send)

    transport.get_queue_status()
    transport.get_active_item()
    transport.list_jobs(status="queued", include_terminal=False, limit=5)

    assert commands == [
        ("get_queue_status", {}),
        ("get_active_item", {}),
        (
            "list_jobs",
            {
                "include_terminal": False,
                "include_result": False,
                "status": "queued",
                "limit": 5,
            },
        ),
    ]


def test_execute_code_helper_preserves_sync_command(monkeypatch) -> None:
    calls: list[tuple[str, dict[str, Any] | None]] = []

    def fake_send(command_type, params=None, **kwargs):
        calls.append((command_type, params))
        return {"status": "success", "result": {"executed": True}}

    monkeypatch.setattr(transport, "connect_and_send_command", fake_send)

    transport.execute_code(
        "print('sync')",
        wait_timeout_seconds=5.0,
        job_timeout_seconds=10.0,
        detach_on_wait_timeout=True,
    )

    assert calls == [
        (
            "execute_code",
            {
                "code": "print('sync')",
                "code_is_base64": False,
                "return_as_base64": False,
                "detach_on_wait_timeout": True,
                "wait_timeout_seconds": 5.0,
                "job_timeout_seconds": 10.0,
            },
        )
    ]
