"""High-level wrapper around remote pip execution."""

from __future__ import annotations

from typing import Any

import click

from blender_remote.cli.pkg.pip_runner import run_remote_pip


def run_pip(*, port: int | None, pip_args: list[str]) -> dict[str, Any]:
    """Run an arbitrary pip command remotely and stream output locally.

    Parameters
    ----------
    port : int, optional
        Optional MCP port override.
    pip_args : list[str]
        Arguments after `pip` (e.g. `["list", "--format=json"]`).

    Returns
    -------
    dict[str, Any]
        JSON summary returned by the remote runner.

    Raises
    ------
    click.ClickException
        If the remote pip command exits with a non-zero status code.
    """
    result = run_remote_pip(
        port=port,
        pip_args=pip_args,
        socket_timeout_seconds=600.0,
        remote_timeout_seconds=1200.0,
    )

    stdout = str(result.get("stdout") or "")
    stderr = str(result.get("stderr") or "")
    if stdout:
        click.echo(stdout, nl=not stdout.endswith("\n"))
    if stderr:
        click.echo(stderr, err=True, nl=not stderr.endswith("\n"))

    returncode = int(result.get("returncode", 1))
    if returncode != 0:
        raise click.ClickException(f"pip exited with code {returncode}")

    return result
