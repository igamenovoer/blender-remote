from __future__ import annotations

from typing import Any

from click.testing import CliRunner

from blender_remote.cli.app import cli
from blender_remote.cli.commands import job as job_commands


def test_cli_job_queue_active_and_list_commands(monkeypatch) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []

    def fake_get_queue_status(**kwargs):
        calls.append(("queue", kwargs))
        return {"status": "success", "result": {"queued_user_jobs": 0}}

    def fake_get_active_item(**kwargs):
        calls.append(("active", kwargs))
        return {"status": "success", "result": {"active_item": None}}

    def fake_list_jobs(**kwargs):
        calls.append(("list", kwargs))
        return {"status": "success", "result": {"count": 0, "jobs": []}}

    monkeypatch.setattr(job_commands.transport, "get_queue_status", fake_get_queue_status)
    monkeypatch.setattr(job_commands.transport, "get_active_item", fake_get_active_item)
    monkeypatch.setattr(job_commands.transport, "list_jobs", fake_list_jobs)

    runner = CliRunner()
    queue_result = runner.invoke(cli, ["job", "queue", "--port", "7777"])
    active_result = runner.invoke(cli, ["job", "active", "--port", "7777"])
    list_result = runner.invoke(
        cli,
        [
            "job",
            "list",
            "--status",
            "queued",
            "--exclude-terminal",
            "--include-result",
            "--limit",
            "5",
            "--port",
            "7777",
        ],
    )

    assert queue_result.exit_code == 0
    assert active_result.exit_code == 0
    assert list_result.exit_code == 0
    assert calls == [
        ("queue", {"port": 7777}),
        ("active", {"port": 7777}),
        (
            "list",
            {
                "status": "queued",
                "include_terminal": False,
                "include_result": True,
                "limit": 5,
                "port": 7777,
            },
        ),
    ]


def test_cli_job_submit_uses_async_transport(monkeypatch) -> None:
    calls: list[dict[str, Any]] = []

    def fake_submit_code_job(code, **kwargs):
        calls.append({"code": code, **kwargs})
        return {"status": "success", "result": {"job_id": "job-1"}}

    monkeypatch.setattr(job_commands.transport, "submit_code_job", fake_submit_code_job)

    result = CliRunner().invoke(
        cli,
        [
            "job",
            "submit",
            "--code",
            "print('queued')",
            "--job-timeout",
            "10",
            "--port",
            "7777",
        ],
    )

    assert result.exit_code == 0
    assert calls == [
        {
            "code": "print('queued')",
            "code_is_base64": False,
            "return_as_base64": False,
            "job_timeout_seconds": 10.0,
            "port": 7777,
        }
    ]
