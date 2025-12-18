"""High-level wrapper around running `pip` in Blender's embedded Python.

This module backs `blender-remote-cli pkg pip -- ...`.
"""

from __future__ import annotations

import subprocess

import click

from blender_remote.cli.pkg.blender_background import (
    get_cli_timeout_seconds,
    get_configured_blender_executable,
    run_blender_python_module,
)


def run_pip(*, pip_args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run an arbitrary pip command in Blender and stream output locally.

    Parameters
    ----------
    pip_args : list[str]
        Arguments after `pip` (e.g. `["list", "--format=json"]`).

    Returns
    -------
    subprocess.CompletedProcess[str]
        Completed process result from the Blender invocation.

    Raises
    ------
    click.ClickException
        If the pip command exits with a non-zero status code.
    """
    if not pip_args:
        raise click.ClickException("Usage: blender-remote-cli pkg pip -- PIP_ARGS...")

    blender_executable = get_configured_blender_executable()
    timeout_seconds = get_cli_timeout_seconds(default=300.0)

    result = run_blender_python_module(
        blender_executable=blender_executable,
        module="pip",
        module_args=pip_args,
        timeout_seconds=timeout_seconds,
    )

    if result.stdout:
        click.echo(result.stdout, nl=not result.stdout.endswith("\n"))
    if result.stderr:
        click.echo(result.stderr, err=True, nl=not result.stderr.endswith("\n"))

    if result.returncode != 0:
        raise click.ClickException(f"pip exited with code {result.returncode}")

    return result
