"""Remote code execution helpers.

This module wraps the MCP `execute_code` command and provides a small, typed
interface for running Python code inside a remote Blender process.

The primary entry points are:
- `execute_code`, for executing arbitrary code and returning stdout/stderr.
- `execute_json`, for executing code that prints a single JSON object to stdout.
"""

from __future__ import annotations

import base64
import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import click

from blender_remote.cli.transport import connect_and_send_command


@dataclass(frozen=True, slots=True)
class RemoteExecResult:
    """Captured result for a remote `execute_code` invocation.

    Attributes
    ----------
    stdout : str
        Captured standard output.
    stderr : str
        Captured standard error.
    duration : float or None
        Optional execution duration (seconds) reported by the remote addon.
    """

    stdout: str
    stderr: str
    duration: float | None


def _extract_execute_code_result(response: Mapping[str, Any]) -> RemoteExecResult:
    """Convert an MCP `execute_code` response mapping into a typed result.

    Parameters
    ----------
    response : collections.abc.Mapping[str, Any]
        Raw response returned by `connect_and_send_command`.

    Returns
    -------
    RemoteExecResult
        Parsed stdout/stderr/duration fields.

    Raises
    ------
    click.ClickException
        If the response indicates failure or is missing expected fields.
    """
    if response.get("status") != "success":
        message = response.get("message") or "Remote command failed"
        raise click.ClickException(str(message))

    payload = response.get("result")
    if not isinstance(payload, Mapping):
        raise click.ClickException("Remote response missing result payload")

    if not payload.get("executed", False):
        raise click.ClickException("Remote code did not report successful execution")

    output = payload.get("output")
    stdout = payload.get("result") or ""
    stderr = ""
    if isinstance(output, Mapping):
        stdout = str(output.get("stdout") or stdout)
        stderr = str(output.get("stderr") or "")

    duration_value = payload.get("duration")
    duration: float | None
    try:
        duration = float(duration_value) if duration_value is not None else None
    except (TypeError, ValueError):
        duration = None

    return RemoteExecResult(stdout=stdout, stderr=stderr, duration=duration)


def execute_code(
    *,
    code: str,
    port: int,
    socket_timeout_seconds: float,
    remote_timeout_seconds: float | None = None,
    code_is_base64: bool = True,
) -> RemoteExecResult:
    """Execute Python code remotely via the MCP `execute_code` command.

    Parameters
    ----------
    code : str
        Python source to execute in the remote Blender process.
    port : int
        MCP TCP port to connect to.
    socket_timeout_seconds : float
        Client-side socket timeout used while waiting for the response.
    remote_timeout_seconds : float, optional
        Optional server-side timeout override for this request (must be supported
        by the remote addon).
    code_is_base64 : bool, optional
        If True, transmit `code` base64-encoded to avoid encoding issues.

    Returns
    -------
    RemoteExecResult
        Captured stdout/stderr and optional duration.

    Raises
    ------
    click.ClickException
        If the remote command fails.
    """
    params: dict[str, Any] = {
        "code_is_base64": code_is_base64,
        "return_as_base64": False,
    }

    if code_is_base64:
        params["code"] = base64.b64encode(code.encode("utf-8")).decode("ascii")
    else:
        params["code"] = code

    if remote_timeout_seconds is not None:
        params["_timeout_seconds"] = remote_timeout_seconds

    response = connect_and_send_command(
        "execute_code",
        params,
        port=port,
        timeout=socket_timeout_seconds,
    )
    return _extract_execute_code_result(response)


def execute_json(
    *,
    code: str,
    port: int,
    socket_timeout_seconds: float,
    remote_timeout_seconds: float | None = None,
    code_is_base64: bool = True,
) -> dict[str, Any]:
    """Execute code remotely and parse a JSON object from stdout.

    Parameters
    ----------
    code : str
        Python source expected to print a single JSON object to stdout.
    port : int
        MCP TCP port to connect to.
    socket_timeout_seconds : float
        Client-side socket timeout used while waiting for the response.
    remote_timeout_seconds : float, optional
        Optional server-side timeout override for this request.
    code_is_base64 : bool, optional
        If True, transmit `code` base64-encoded to avoid encoding issues.

    Returns
    -------
    dict[str, Any]
        Parsed JSON object.

    Raises
    ------
    click.ClickException
        If stdout is empty, cannot be parsed as JSON, or does not contain a JSON
        object at the top level.
    """
    result = execute_code(
        code=code,
        port=port,
        socket_timeout_seconds=socket_timeout_seconds,
        remote_timeout_seconds=remote_timeout_seconds,
        code_is_base64=code_is_base64,
    )

    stdout = result.stdout.strip()
    if not stdout:
        details = result.stderr.strip()
        raise click.ClickException(
            "Remote script produced no stdout; cannot parse JSON"
            + (f"\n\nstderr:\n{details}" if details else "")
        )

    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise click.ClickException(
            f"Remote script did not return valid JSON ({exc})\n\nstdout:\n{stdout}\n\nstderr:\n{result.stderr}"
        ) from exc

    if not isinstance(parsed, dict):
        raise click.ClickException("Remote JSON result must be an object")

    return parsed
