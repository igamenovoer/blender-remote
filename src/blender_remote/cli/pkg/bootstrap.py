"""Pip bootstrapping utilities for Blender's embedded Python.

This module backs `blender-remote-cli pkg bootstrap` and provides best-effort
mechanisms to ensure `pip` is available in Blender's embedded Python
environment, by launching Blender in background mode and running Python code in
that interpreter.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import click

from blender_remote.cli.pkg.blender_background import (
    get_cli_timeout_seconds,
    get_configured_blender_executable,
    run_blender_python_module,
    run_blender_python_path,
)


def bootstrap_pip(
    *,
    method: str,
    get_pip_path: Path | None,
    upgrade: bool,
) -> None:
    """Ensure `pip` exists for Blender's embedded Python.

    Parameters
    ----------
    method : str
        Bootstrapping method (`auto`, `ensurepip`, `get-pip`).
    get_pip_path : pathlib.Path, optional
        Optional local `get-pip.py` path (required for `get-pip` method and as a
        fallback when `ensurepip` is unavailable).
    upgrade : bool
        If True, attempt to upgrade pip after bootstrapping.

    Raises
    ------
    click.ClickException
        If bootstrapping fails or pip remains unavailable.
    """
    normalized_method = (method or "").lower()
    if normalized_method not in {"auto", "ensurepip", "get-pip"}:
        raise click.ClickException(f"Unknown bootstrap method: {method!r}")

    blender_executable = get_configured_blender_executable()
    timeout_seconds = get_cli_timeout_seconds(default=300.0)

    pip_version = _probe_pip(
        blender_executable=blender_executable, timeout_seconds=timeout_seconds
    )
    if pip_version is not None:
        click.echo(f"[OK] pip is available: {pip_version}")
        if upgrade:
            _upgrade_pip(
                blender_executable=blender_executable, timeout_seconds=timeout_seconds
            )
        return

    need_get_pip = normalized_method == "get-pip"

    if normalized_method in {"auto", "ensurepip"}:
        click.echo("[BOOTSTRAP] Trying ensurepip...")
        ensurepip_result = run_blender_python_module(
            blender_executable=blender_executable,
            module="ensurepip",
            module_args=["--upgrade"],
            timeout_seconds=timeout_seconds,
        )
        _echo_process_output(ensurepip_result)

        if ensurepip_result.returncode != 0:
            if normalized_method == "ensurepip":
                raise click.ClickException(
                    f"ensurepip failed (exit code {ensurepip_result.returncode})"
                )
            need_get_pip = True

    if need_get_pip:
        if get_pip_path is None:
            if normalized_method == "get-pip":
                raise click.ClickException(
                    "--get-pip PATH is required for --method get-pip"
                )
            raise click.ClickException(
                "ensurepip failed and no get-pip script was provided.\n"
                "Re-run with `--method get-pip --get-pip <PATH>`."
            )

        click.echo(f"[BOOTSTRAP] Running get-pip.py: {get_pip_path}")
        get_pip_result = run_blender_python_path(
            blender_executable=blender_executable,
            script_path=get_pip_path,
            script_args=[],
            timeout_seconds=timeout_seconds,
        )
        _echo_process_output(get_pip_result)

        if get_pip_result.returncode != 0:
            raise click.ClickException(
                f"get-pip.py failed (exit code {get_pip_result.returncode})"
            )

    pip_version = _probe_pip(
        blender_executable=blender_executable, timeout_seconds=timeout_seconds
    )
    if pip_version is None:
        raise click.ClickException("pip is still not available after bootstrapping")

    click.echo(f"[OK] pip is now available: {pip_version}")
    if upgrade:
        _upgrade_pip(
            blender_executable=blender_executable, timeout_seconds=timeout_seconds
        )


def _probe_pip(*, blender_executable: Path, timeout_seconds: float) -> str | None:
    """Check whether `pip` is importable/usable in Blender Python.

    Returns
    -------
    str | None
        Version string from `pip --version` when available, otherwise None.
    """
    result = run_blender_python_module(
        blender_executable=blender_executable,
        module="pip",
        module_args=["--version"],
        timeout_seconds=timeout_seconds,
    )
    if result.returncode != 0:
        return None

    version = (result.stdout or "").strip()
    return version or None


def _upgrade_pip(*, blender_executable: Path, timeout_seconds: float) -> None:
    """Attempt to upgrade pip inside Blender Python (best-effort).

    Raises
    ------
    click.ClickException
        If pip upgrade fails.
    """
    click.echo("[BOOTSTRAP] Upgrading pip (best-effort)...")
    result = run_blender_python_module(
        blender_executable=blender_executable,
        module="pip",
        module_args=["install", "--upgrade", "pip"],
        timeout_seconds=timeout_seconds,
    )
    _echo_process_output(result)

    if result.returncode != 0:
        raise click.ClickException(
            f"pip upgrade failed (exit code {result.returncode})"
        )

    click.echo("[OK] pip upgraded")


def _echo_process_output(result: subprocess.CompletedProcess[str]) -> None:
    """Echo a completed process output to the console."""
    if result.stdout:
        click.echo(result.stdout, nl=not result.stdout.endswith("\n"))
    if result.stderr:
        click.echo(result.stderr, err=True, nl=not result.stderr.endswith("\n"))
