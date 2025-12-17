"""Remote pip runner.

This module executes `python -m pip ...` inside the remote Blender Python
interpreter and returns a JSON summary that includes the command, exit code, and
captured stdout/stderr.
"""

from __future__ import annotations

from typing import Any

from blender_remote.cli.pkg.ports import resolve_mcp_port
from blender_remote.cli.pkg.remote_exec import execute_json


def run_remote_pip(
    *,
    port: int | None,
    pip_args: list[str],
    socket_timeout_seconds: float,
    remote_timeout_seconds: float,
) -> dict[str, Any]:
    """Run `python -m pip ...` on the remote Blender Python.

    Parameters
    ----------
    port : int, optional
        Optional MCP port override.
    pip_args : list[str]
        Arguments after `pip` (e.g. `["install", "requests"]`).
    socket_timeout_seconds : float
        Client-side socket timeout used while waiting for the response.
    remote_timeout_seconds : float
        Remote execution timeout override (server side).

    Returns
    -------
    dict[str, Any]
        JSON summary containing the command, return code, stdout/stderr, and
        duration.
    """
    mcp_port = resolve_mcp_port(port)

    code = rf"""
import json
import subprocess
import sys
import time

import bpy

python_exe = getattr(bpy.app, "binary_path_python", "") or sys.executable
python_args = tuple(getattr(bpy.app, "python_args", ()))

cmd = [python_exe, *python_args, "-m", "pip", *{pip_args!r}]
start = time.time()
proc = subprocess.run(cmd, capture_output=True, text=True)  # noqa: S603

def _trim(text: str, limit: int = 200_000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\\n...<truncated>..."

print(json.dumps({{
    "cmd": cmd,
    "returncode": proc.returncode,
    "stdout": _trim(proc.stdout or ""),
    "stderr": _trim(proc.stderr or ""),
    "duration_s": time.time() - start,
}}, ensure_ascii=True))
"""
    return execute_json(
        code=code,
        port=mcp_port,
        socket_timeout_seconds=socket_timeout_seconds,
        remote_timeout_seconds=remote_timeout_seconds,
        code_is_base64=True,
    )
