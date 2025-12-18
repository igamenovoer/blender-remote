"""`blender-remote-cli pkg` command group.

This module defines CLI entry points for managing Python packages inside
Blender's embedded Python environment for a **local** Blender installation.

All Python execution is performed by launching the configured Blender
executable in background mode (`<blender> --background --python <script.py>`).
"""

from __future__ import annotations

import json
from pathlib import Path

import click

from blender_remote.cli.pkg.bootstrap import bootstrap_pip
from blender_remote.cli.pkg.info import (
    get_blender_python_info,
    render_blender_python_info,
)
from blender_remote.cli.pkg.pip import run_pip


@click.group()
def pkg() -> None:
    """Manage Python packages in Blender's embedded Python (local)."""


@pkg.command()
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Print a single JSON object to stdout (no extra text)",
)
def info(json_output: bool) -> None:
    """Show Blender/Python environment details for packaging decisions.

    Parameters
    ----------
    json_output : bool
        If True, print a single JSON object to stdout.
    """
    info_data = get_blender_python_info()

    if json_output:
        click.echo(json.dumps(info_data, ensure_ascii=True))
        return

    click.echo(render_blender_python_info(info_data))


@pkg.command()
@click.option(
    "--method",
    type=click.Choice(["auto", "ensurepip", "get-pip"], case_sensitive=False),
    default="auto",
    show_default=True,
    help="Bootstrapping method to use",
)
@click.option(
    "--get-pip",
    "get_pip_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Local path to a get-pip.py to run inside Blender Python",
)
@click.option(
    "--upgrade",
    is_flag=True,
    help="Attempt to upgrade pip after bootstrapping (may fail when offline)",
)
def bootstrap(method: str, get_pip_path: Path | None, upgrade: bool) -> None:
    """Ensure pip exists for Blender's embedded Python.

    Parameters
    ----------
    method : str
        Bootstrapping method (`auto`, `ensurepip`, `get-pip`).
    get_pip_path : pathlib.Path, optional
        Optional local `get-pip.py` to run inside Blender Python.
    upgrade : bool
        If True, attempt to upgrade pip after bootstrapping.
    """
    bootstrap_pip(method=method, get_pip_path=get_pip_path, upgrade=upgrade)


@pkg.command(
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True}
)
@click.argument("pip_args", nargs=-1, type=click.UNPROCESSED)
def pip(pip_args: tuple[str, ...]) -> None:
    """Run arbitrary pip commands inside Blender Python (escape hatch).

    Parameters
    ----------
    pip_args : tuple[str, ...]
        Raw pip arguments. Use `--` to separate from CLI options.
    """
    if not pip_args:
        raise click.ClickException("Usage: blender-remote-cli pkg pip -- PIP_ARGS...")
    run_pip(pip_args=list(pip_args))
