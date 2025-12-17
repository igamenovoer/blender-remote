"""Remote pip bootstrapping utilities.

This module backs `blender-remote-cli pkg bootstrap` and provides best-effort
mechanisms to ensure `pip` is available in the remote Blender Python
environment.
"""

from __future__ import annotations

import tempfile
import urllib.request
from pathlib import Path
from typing import Any

import click

from blender_remote.cli.pkg.ports import resolve_mcp_port
from blender_remote.cli.pkg.remote_exec import execute_json
from blender_remote.cli.pkg.upload import upload_file


def _run_python_module(
    *,
    module: str,
    args: list[str],
    port: int,
    socket_timeout_seconds: float,
    remote_timeout_seconds: float,
) -> dict[str, Any]:
    """Run `python -m <module> ...` on the remote Blender Python.

    Parameters
    ----------
    module : str
        Module name to execute with `-m`.
    args : list[str]
        Arguments to pass to the module.
    port : int
        MCP TCP port of the remote Blender MCP service.
    socket_timeout_seconds : float
        Client-side socket timeout while waiting for a response.
    remote_timeout_seconds : float
        Remote execution timeout override (server side).

    Returns
    -------
    dict[str, Any]
        JSON summary containing the command, return code, stdout/stderr and
        duration.
    """
    code = rf"""
import json
import subprocess
import sys
import time

import bpy

python_exe = getattr(bpy.app, "binary_path_python", "") or sys.executable
python_args = tuple(getattr(bpy.app, "python_args", ()))

cmd = [python_exe, *python_args, "-m", {module!r}, *{args!r}]
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
        port=port,
        socket_timeout_seconds=socket_timeout_seconds,
        remote_timeout_seconds=remote_timeout_seconds,
        code_is_base64=True,
    )


def _run_python_script(
    *,
    script_path: str,
    args: list[str],
    port: int,
    socket_timeout_seconds: float,
    remote_timeout_seconds: float,
) -> dict[str, Any]:
    """Run a Python script file on the remote Blender Python.

    Parameters
    ----------
    script_path : str
        Remote filesystem path to the script.
    args : list[str]
        Script arguments.
    port : int
        MCP TCP port of the remote Blender MCP service.
    socket_timeout_seconds : float
        Client-side socket timeout while waiting for a response.
    remote_timeout_seconds : float
        Remote execution timeout override (server side).

    Returns
    -------
    dict[str, Any]
        JSON summary containing the command, return code, stdout/stderr and
        duration.
    """
    code = rf"""
import json
import subprocess
import sys
import time

import bpy

python_exe = getattr(bpy.app, "binary_path_python", "") or sys.executable
python_args = tuple(getattr(bpy.app, "python_args", ()))

cmd = [python_exe, *python_args, {script_path!r}, *{args!r}]
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
        port=port,
        socket_timeout_seconds=socket_timeout_seconds,
        remote_timeout_seconds=remote_timeout_seconds,
        code_is_base64=True,
    )


def _get_remote_temp_path(*, port: int, filename: str) -> str:
    """Return a remote tempdir path for a given filename.

    Parameters
    ----------
    port : int
        MCP TCP port of the remote Blender MCP service.
    filename : str
        Basename to join with the remote temporary directory.

    Returns
    -------
    str
        Remote filesystem path inside `tempfile.gettempdir()`.
    """
    code = rf"""
import json
import os
import tempfile

path = os.path.join(tempfile.gettempdir(), {filename!r})
print(json.dumps({{"path": path}}, ensure_ascii=True))
"""
    result = execute_json(
        code=code, port=port, socket_timeout_seconds=15.0, remote_timeout_seconds=15.0
    )
    return str(result["path"])


def bootstrap_pip(
    *,
    port: int | None,
    method: str,
    get_pip_path: Path | None,
    upgrade: bool,
) -> None:
    """Ensure `pip` is available on the remote Blender Python.

    Parameters
    ----------
    port : int, optional
        Optional MCP port override.
    method : str
        Bootstrapping method (`auto`, `ensurepip`, or `get-pip`).
    get_pip_path : pathlib.Path, optional
        Optional local `get-pip.py` path to upload (useful when the controller
        machine is offline).
    upgrade : bool
        If True, attempt `pip install --upgrade pip` after bootstrapping.

    Raises
    ------
    click.ClickException
        If bootstrapping fails.
    """
    mcp_port = resolve_mcp_port(port)
    method = method.lower()

    click.echo("[BOOTSTRAP] Checking remote pip availability...")
    pip_check = _run_python_module(
        module="pip",
        args=["--version"],
        port=mcp_port,
        socket_timeout_seconds=30.0,
        remote_timeout_seconds=60.0,
    )

    if int(pip_check.get("returncode", 1)) == 0:
        click.echo(
            f"[OK] pip is already available: {str(pip_check.get('stdout','')).strip()}"
        )
        if upgrade:
            click.echo("[BOOTSTRAP] Upgrading pip (best-effort)...")
            upgrade_result = _run_python_module(
                module="pip",
                args=["install", "--upgrade", "pip"],
                port=mcp_port,
                socket_timeout_seconds=300.0,
                remote_timeout_seconds=600.0,
            )
            if int(upgrade_result.get("returncode", 1)) != 0:
                raise click.ClickException(
                    "pip upgrade failed\n\nstdout:\n"
                    + str(upgrade_result.get("stdout", ""))
                    + "\n\nstderr:\n"
                    + str(upgrade_result.get("stderr", ""))
                )
            click.echo("[OK] pip upgraded")
        return

    if method == "get-pip":
        ensurepip_allowed = False
    elif method == "ensurepip":
        ensurepip_allowed = True
    else:
        ensurepip_allowed = True

    if ensurepip_allowed:
        click.echo("[BOOTSTRAP] Trying ensurepip...")
        ensurepip_result = _run_python_module(
            module="ensurepip",
            args=["--upgrade"],
            port=mcp_port,
            socket_timeout_seconds=120.0,
            remote_timeout_seconds=300.0,
        )
        if int(ensurepip_result.get("returncode", 1)) == 0:
            click.echo("[OK] ensurepip succeeded")
            if upgrade:
                click.echo("[BOOTSTRAP] Upgrading pip (best-effort)...")
                upgrade_result = _run_python_module(
                    module="pip",
                    args=["install", "--upgrade", "pip"],
                    port=mcp_port,
                    socket_timeout_seconds=300.0,
                    remote_timeout_seconds=600.0,
                )
                if int(upgrade_result.get("returncode", 1)) != 0:
                    raise click.ClickException(
                        "pip upgrade failed\n\nstdout:\n"
                        + str(upgrade_result.get("stdout", ""))
                        + "\n\nstderr:\n"
                        + str(upgrade_result.get("stderr", ""))
                    )
                click.echo("[OK] pip upgraded")
            return
        click.echo("[WARN] ensurepip failed; falling back to get-pip")

    # get-pip fallback
    local_get_pip: Path
    if get_pip_path is not None:
        local_get_pip = get_pip_path
    else:
        url = "https://bootstrap.pypa.io/get-pip.py"
        click.echo(f"[BOOTSTRAP] Downloading get-pip.py from {url} ...")
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:  # noqa: S310
                content = resp.read()
        except Exception as exc:  # noqa: BLE001
            raise click.ClickException(
                "Failed to download get-pip.py. If your controller is offline, provide a local script via --get-pip PATH.\n\n"
                f"Download error: {exc}"
            ) from exc

        temp_dir = Path(tempfile.gettempdir())
        local_get_pip = temp_dir / "blender_remote_get_pip.py"
        local_get_pip.write_bytes(content)

    remote_get_pip_path = _get_remote_temp_path(
        port=mcp_port, filename="blender_remote_get_pip.py"
    )
    click.echo(f"[BOOTSTRAP] Uploading get-pip.py to remote: {remote_get_pip_path}")
    upload_file(
        local_path=local_get_pip,
        remote_path=remote_get_pip_path,
        port=mcp_port,
        chunk_size=1 * 1024 * 1024,
    )

    click.echo("[BOOTSTRAP] Running get-pip.py on remote...")
    run_result = _run_python_script(
        script_path=remote_get_pip_path,
        args=[],
        port=mcp_port,
        socket_timeout_seconds=600.0,
        remote_timeout_seconds=1200.0,
    )
    if int(run_result.get("returncode", 1)) != 0:
        raise click.ClickException(
            "get-pip.py execution failed\n\nstdout:\n"
            + str(run_result.get("stdout", ""))
            + "\n\nstderr:\n"
            + str(run_result.get("stderr", ""))
        )

    # Best-effort cleanup
    execute_json(
        code=rf"import json, os; p={remote_get_pip_path!r};\n"
        r"ok=False\n"
        r"try:\n"
        r"    os.unlink(p)\n"
        r"    ok=True\n"
        r"except Exception:\n"
        r"    ok=False\n"
        r"print(json.dumps({'deleted': ok}, ensure_ascii=True))\n",
        port=mcp_port,
        socket_timeout_seconds=30.0,
        remote_timeout_seconds=60.0,
        code_is_base64=True,
    )

    click.echo("[BOOTSTRAP] Verifying pip...")
    verify = _run_python_module(
        module="pip",
        args=["--version"],
        port=mcp_port,
        socket_timeout_seconds=60.0,
        remote_timeout_seconds=120.0,
    )
    if int(verify.get("returncode", 1)) != 0:
        raise click.ClickException(
            "pip still not available after bootstrapping\n\nstdout:\n"
            + str(verify.get("stdout", ""))
            + "\n\nstderr:\n"
            + str(verify.get("stderr", ""))
        )

    click.echo(f"[OK] pip is now available: {str(verify.get('stdout','')).strip()}")
    if upgrade:
        click.echo("[BOOTSTRAP] Upgrading pip (best-effort)...")
        upgrade_result = _run_python_module(
            module="pip",
            args=["install", "--upgrade", "pip"],
            port=mcp_port,
            socket_timeout_seconds=300.0,
            remote_timeout_seconds=600.0,
        )
        if int(upgrade_result.get("returncode", 1)) != 0:
            raise click.ClickException(
                "pip upgrade failed\n\nstdout:\n"
                + str(upgrade_result.get("stdout", ""))
                + "\n\nstderr:\n"
                + str(upgrade_result.get("stderr", ""))
            )
        click.echo("[OK] pip upgraded")
