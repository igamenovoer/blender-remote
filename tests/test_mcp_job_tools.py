from __future__ import annotations

import asyncio
import base64
from typing import Any

from blender_remote import mcp_server


class FakeContext:
    def __init__(self) -> None:
        self.infos: list[str] = []
        self.errors: list[str] = []

    async def info(self, message: str) -> None:
        self.infos.append(message)

    async def error(self, message: str) -> None:
        self.errors.append(message)


class FakeBlenderConnection:
    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.responses = responses
        self.commands: list[dict[str, Any]] = []

    async def send_command(self, command: dict[str, Any]) -> dict[str, Any]:
        self.commands.append(command)
        return self.responses.pop(0)


def run_tool(tool, *args, **kwargs):
    return asyncio.run(tool.fn(*args, **kwargs))


def test_mcp_execute_code_preserves_sync_base64_flow() -> None:
    encoded = base64.b64encode(b"hello\n").decode("ascii")
    fake_conn = FakeBlenderConnection(
        [
            {
                "status": "success",
                "result": {
                    "executed": True,
                    "result": encoded,
                    "result_is_base64": True,
                },
            }
        ]
    )
    old_conn = mcp_server.blender_conn
    mcp_server.blender_conn = fake_conn
    try:
        result = run_tool(
            mcp_server.execute_code,
            "print('hello')",
            FakeContext(),
            send_as_base64=True,
            return_as_base64=True,
        )
    finally:
        mcp_server.blender_conn = old_conn

    assert result["result"] == "hello\n"
    assert fake_conn.commands == [
        {
            "type": "execute_code",
            "params": {
                "code": base64.b64encode(b"print('hello')").decode("ascii"),
                "code_is_base64": True,
                "return_as_base64": True,
            },
        }
    ]


def test_mcp_execute_code_returns_sync_failure() -> None:
    fake_conn = FakeBlenderConnection(
        [{"status": "error", "message": "Code execution failed"}]
    )
    old_conn = mcp_server.blender_conn
    ctx = FakeContext()
    mcp_server.blender_conn = fake_conn
    try:
        result = run_tool(mcp_server.execute_code, "1 / 0", ctx)
    finally:
        mcp_server.blender_conn = old_conn

    assert result == {"error": "Code execution failed"}
    assert ctx.errors == ["Code execution failed: Code execution failed"]


def test_mcp_execute_code_returns_sync_cancelled_result() -> None:
    fake_conn = FakeBlenderConnection(
        [
            {
                "status": "success",
                "result": {
                    "executed": False,
                    "status": "cancelled",
                    "job_id": "job-1",
                    "cancel_requested": True,
                },
            }
        ]
    )
    old_conn = mcp_server.blender_conn
    mcp_server.blender_conn = fake_conn
    try:
        result = run_tool(mcp_server.execute_code, "check_cancelled()", FakeContext())
    finally:
        mcp_server.blender_conn = old_conn

    assert result == {
        "executed": False,
        "status": "cancelled",
        "job_id": "job-1",
        "cancel_requested": True,
    }


def test_mcp_async_job_tools_send_job_control_commands() -> None:
    fake_conn = FakeBlenderConnection(
        [
            {"status": "success", "result": {"job_id": "job-1"}},
            {"status": "success", "result": {"status": "running"}},
            {"status": "success", "result": {"status": "completed", "result": {}}},
            {"status": "success", "result": {"status": "cancelling"}},
        ]
    )
    old_conn = mcp_server.blender_conn
    mcp_server.blender_conn = fake_conn
    try:
        submit_result = run_tool(
            mcp_server.submit_code_job,
            "print('async')",
            FakeContext(),
            job_timeout_seconds=3.0,
        )
        status_result = run_tool(
            mcp_server.get_job_status,
            "job-1",
            FakeContext(),
        )
        result_result = run_tool(
            mcp_server.get_job_result,
            "job-1",
            FakeContext(),
        )
        cancel_result = run_tool(
            mcp_server.cancel_job,
            "job-1",
            FakeContext(),
            reason="user",
        )
    finally:
        mcp_server.blender_conn = old_conn

    assert submit_result == {"job_id": "job-1"}
    assert status_result == {"status": "running"}
    assert result_result == {"status": "completed", "result": {}}
    assert cancel_result == {"status": "cancelling"}
    assert fake_conn.commands == [
        {
            "type": "submit_code_job",
            "params": {
                "code": "print('async')",
                "code_is_base64": False,
                "return_as_base64": False,
                "job_timeout_seconds": 3.0,
            },
        },
        {"type": "get_job_status", "params": {"job_id": "job-1"}},
        {"type": "get_job_result", "params": {"job_id": "job-1"}},
        {"type": "cancel_job", "params": {"job_id": "job-1", "reason": "user"}},
    ]


def test_mcp_get_job_result_decodes_nested_base64_result() -> None:
    encoded = base64.b64encode(b"async-result").decode("ascii")
    fake_conn = FakeBlenderConnection(
        [
            {
                "status": "success",
                "result": {
                    "status": "completed",
                    "result": {"result": encoded, "result_is_base64": True},
                },
            }
        ]
    )
    old_conn = mcp_server.blender_conn
    mcp_server.blender_conn = fake_conn
    try:
        result = run_tool(mcp_server.get_job_result, "job-1", FakeContext())
    finally:
        mcp_server.blender_conn = old_conn

    assert result["result"]["result"] == "async-result"
    assert "result_is_base64" not in result["result"]
