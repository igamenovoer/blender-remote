"""Blender background execution helpers for `blender-remote-cli pkg ...`.

This module provides a small utility layer for running Python code inside
Blender's embedded Python interpreter by launching Blender in background mode:

`<blender-executable> --background --python <script.py> -- ...`

It also provides a sentinel-based JSON extraction helper so callers can safely
retrieve machine-readable output even if Blender prints additional logs.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import click

from blender_remote.cli.config import BlenderRemoteConfig

JSON_BEGIN_SENTINEL = "__BLENDER_REMOTE_JSON_BEGIN__"
JSON_END_SENTINEL = "__BLENDER_REMOTE_JSON_END__"


def get_configured_blender_executable() -> Path:
    """Resolve the configured Blender executable path from CLI config.

    Returns
    -------
    pathlib.Path
        Path to the Blender executable as configured by `blender-remote-cli init`.

    Raises
    ------
    click.ClickException
        If the configuration is missing or the executable path is not set.
    """
    config = BlenderRemoteConfig()
    exec_path = config.get("blender.exec_path")
    if not exec_path:
        raise click.ClickException(
            "Blender executable path is not configured.\n"
            "Run `blender-remote-cli init [blender_path]` first."
        )

    blender_executable = Path(str(exec_path))
    if not blender_executable.exists():
        raise click.ClickException(
            f"Configured Blender executable does not exist: {blender_executable}"
        )

    return blender_executable


def get_cli_timeout_seconds(*, default: float = 300.0) -> float:
    """Resolve the CLI subprocess timeout for Blender runs.

    Parameters
    ----------
    default : float
        Fallback timeout when not configured (in seconds).

    Returns
    -------
    float
        Timeout in seconds.
    """
    config = BlenderRemoteConfig()
    timeout_value = None
    try:
        timeout_value = config.get("cli.timeout_sec")
    except click.ClickException:
        timeout_value = None

    if timeout_value is None:
        return default

    try:
        parsed = float(timeout_value)
    except (TypeError, ValueError):
        return default

    if parsed <= 0:
        return default

    return parsed


def run_blender_background_python(
    *,
    blender_executable: Path,
    python_script: str,
    script_args: list[str] | None = None,
    timeout_seconds: float,
    factory_startup: bool = True,
    quiet: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run a Python script inside Blender by launching Blender in background mode.

    Parameters
    ----------
    blender_executable : pathlib.Path
        Path to the Blender executable.
    python_script : str
        Python source code to write into a temporary `.py` file and execute.
    script_args : list[str], optional
        Arguments forwarded to the Python script after Blender's `--` separator.
    timeout_seconds : float
        Subprocess timeout in seconds.
    factory_startup : bool
        If True, add `--factory-startup` to reduce user-config interference.
    quiet : bool
        If True, add `--quiet` to suppress Blender startup messages.

    Returns
    -------
    subprocess.CompletedProcess[str]
        Completed process object containing stdout/stderr and return code.

    Raises
    ------
    click.ClickException
        If Blender cannot be executed or the subprocess times out.
    """
    script_args = script_args or []

    temp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            errors="replace",
            suffix=".py",
            delete=False,
        ) as handle:
            handle.write(python_script)
            temp_path = handle.name

        cmd: list[str] = [str(blender_executable)]
        if factory_startup:
            cmd.append("--factory-startup")
        if quiet:
            cmd.append("--quiet")
        cmd.extend(["--background", "--python", temp_path])
        if script_args:
            cmd.append("--")
            cmd.extend(script_args)

        try:
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise click.ClickException(
                f"Timeout running Blender background script after {timeout_seconds:.0f}s"
            ) from exc
        except FileNotFoundError as exc:
            raise click.ClickException(
                f"Blender executable not found: {blender_executable}"
            ) from exc
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError:
                pass


def run_blender_python_module(
    *,
    blender_executable: Path,
    module: str,
    module_args: list[str] | None,
    timeout_seconds: float,
    factory_startup: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run `python -m <module> ...` inside Blender's embedded Python.

    Parameters
    ----------
    blender_executable : pathlib.Path
        Path to the Blender executable.
    module : str
        Module name to execute (equivalent to `python -m <module>`).
    module_args : list[str], optional
        Arguments to pass to the module.
    timeout_seconds : float
        Subprocess timeout in seconds.
    factory_startup : bool
        If True, add `--factory-startup`.

    Returns
    -------
    subprocess.CompletedProcess[str]
        Completed process object containing stdout/stderr and return code.
    """
    module_args = module_args or []

    python_script = rf"""
import runpy
import sys
import traceback


def _args_after_double_dash(argv: list[str]) -> list[str]:
    if "--" in argv:
        idx = argv.index("--")
        return argv[idx + 1 :]
    return []


module = {module!r}
module_args = _args_after_double_dash(sys.argv)
sys.argv = [module, *module_args]

try:
    runpy.run_module(module, run_name="__main__")
except (ModuleNotFoundError, ImportError) as exc:
    print(f"Module not available: {{module}} ({{exc}})", file=sys.stderr)
    sys.exit(1)
except SystemExit as exc:
    code = exc.code
    if code is None:
        sys.exit(0)
    if isinstance(code, int):
        sys.exit(code)
    print(str(code), file=sys.stderr)
    sys.exit(1)
except Exception:
    traceback.print_exc()
    sys.exit(1)
"""

    return run_blender_background_python(
        blender_executable=blender_executable,
        python_script=python_script,
        script_args=module_args,
        timeout_seconds=timeout_seconds,
        factory_startup=factory_startup,
    )


def run_blender_python_path(
    *,
    blender_executable: Path,
    script_path: Path,
    script_args: list[str] | None,
    timeout_seconds: float,
    factory_startup: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run a Python script file via Blender's embedded Python (runpy.run_path).

    Parameters
    ----------
    blender_executable : pathlib.Path
        Path to the Blender executable.
    script_path : pathlib.Path
        Local path to a Python script accessible to the Blender process.
    script_args : list[str], optional
        Script arguments.
    timeout_seconds : float
        Subprocess timeout in seconds.
    factory_startup : bool
        If True, add `--factory-startup`.

    Returns
    -------
    subprocess.CompletedProcess[str]
        Completed process object containing stdout/stderr and return code.
    """
    script_args = script_args or []

    python_script = rf"""
import runpy
import sys
import traceback


def _args_after_double_dash(argv: list[str]) -> list[str]:
    if "--" in argv:
        idx = argv.index("--")
        return argv[idx + 1 :]
    return []


script_path = {str(script_path)!r}
script_args = _args_after_double_dash(sys.argv)
sys.argv = [script_path, *script_args]

try:
    runpy.run_path(script_path, run_name="__main__")
except SystemExit as exc:
    code = exc.code
    if code is None:
        sys.exit(0)
    if isinstance(code, int):
        sys.exit(code)
    print(str(code), file=sys.stderr)
    sys.exit(1)
except Exception:
    traceback.print_exc()
    sys.exit(1)
"""

    return run_blender_background_python(
        blender_executable=blender_executable,
        python_script=python_script,
        script_args=script_args,
        timeout_seconds=timeout_seconds,
        factory_startup=factory_startup,
    )


def extract_sentinel_json(text: str) -> dict[str, Any]:
    """Extract a JSON object printed between sentinel markers.

    Parameters
    ----------
    text : str
        Full stdout text from Blender.

    Returns
    -------
    dict[str, Any]
        Parsed JSON object.

    Raises
    ------
    click.ClickException
        If sentinels are missing or JSON cannot be parsed.
    """
    begin_index = text.rfind(JSON_BEGIN_SENTINEL)
    if begin_index == -1:
        raise click.ClickException(
            "Expected JSON begin sentinel not found in Blender output."
        )

    end_index = text.find(JSON_END_SENTINEL, begin_index)
    if end_index == -1:
        raise click.ClickException(
            "Expected JSON end sentinel not found in Blender output."
        )

    payload = text[begin_index + len(JSON_BEGIN_SENTINEL) : end_index].strip()
    if not payload:
        raise click.ClickException("Empty JSON payload in Blender output.")

    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise click.ClickException(f"Failed to parse JSON payload: {exc}") from exc

    if not isinstance(parsed, dict):
        raise click.ClickException("Expected a JSON object payload.")

    return parsed


def run_blender_background_json(
    *,
    blender_executable: Path,
    python_script: str,
    timeout_seconds: float,
    factory_startup: bool = True,
) -> dict[str, Any]:
    """Run a Blender background script and return its sentinel JSON payload.

    Parameters
    ----------
    blender_executable : pathlib.Path
        Path to the Blender executable.
    python_script : str
        Python script that prints JSON between sentinels.
    timeout_seconds : float
        Subprocess timeout in seconds.
    factory_startup : bool
        If True, add `--factory-startup`.

    Returns
    -------
    dict[str, Any]
        Parsed JSON payload.
    """
    result = run_blender_background_python(
        blender_executable=blender_executable,
        python_script=python_script,
        timeout_seconds=timeout_seconds,
        factory_startup=factory_startup,
    )

    return extract_sentinel_json(result.stdout or "")
