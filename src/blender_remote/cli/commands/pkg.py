"""`blender-remote-cli pkg` command group.

This module defines CLI entry points for managing Python packages inside the
remote Blender Python environment, including:
- inspecting environment details (`pkg info`)
- ensuring pip is available (`pkg bootstrap`)
- installing packages (`pkg install`)
- running arbitrary pip commands (`pkg pip -- ...`)
- managing an offline wheelhouse cache (`pkg push`, `pkg purge-cache`)
"""

from __future__ import annotations

import json
from pathlib import Path

import click

from blender_remote.cli.pkg.bootstrap import bootstrap_pip
from blender_remote.cli.pkg.info import (
    get_remote_python_info,
    render_remote_python_info,
)
from blender_remote.cli.pkg.install import install_packages
from blender_remote.cli.pkg.pip import run_pip
from blender_remote.cli.pkg.purge_cache import purge_remote_wheelhouse
from blender_remote.cli.pkg.push import push_wheels


@click.group()
def pkg() -> None:
    """Manage Python packages in the remote Blender Python environment."""


@pkg.command()
@click.option("--port", type=int, help="Override MCP port")
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Print a single JSON object to stdout (no extra text)",
)
def info(port: int | None, json_output: bool) -> None:
    """Show remote Blender/Python environment details for packaging decisions.

    Parameters
    ----------
    port : int, optional
        Optional MCP port override.
    json_output : bool
        If True, print a single JSON object to stdout.
    """
    info_data = get_remote_python_info(port=port)

    if json_output:
        click.echo(json.dumps(info_data, ensure_ascii=True))
        return

    click.echo(render_remote_python_info(info_data))


@pkg.command()
@click.option("--port", type=int, help="Override MCP port")
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
    help="Local path to a get-pip.py to transfer (for controller-offline scenarios)",
)
@click.option(
    "--upgrade",
    is_flag=True,
    help="Attempt to upgrade pip after bootstrapping (may fail on offline remotes)",
)
def bootstrap(
    port: int | None,
    method: str,
    get_pip_path: Path | None,
    upgrade: bool,
) -> None:
    """Ensure pip exists on the remote Blender Python.

    Parameters
    ----------
    port : int, optional
        Optional MCP port override.
    method : str
        Bootstrapping method (`auto`, `ensurepip`, `get-pip`).
    get_pip_path : pathlib.Path, optional
        Optional local `get-pip.py` to upload when the controller is offline.
    upgrade : bool
        If True, attempt to upgrade pip after bootstrapping.
    """
    bootstrap_pip(port=port, method=method, get_pip_path=get_pip_path, upgrade=upgrade)


@pkg.command()
@click.option("--port", type=int, help="Override MCP port")
@click.option("--upgrade", is_flag=True, help="Pass --upgrade to pip")
@click.option("--force-reinstall", is_flag=True, help="Pass --force-reinstall to pip")
@click.option("--no-deps", is_flag=True, help="Pass --no-deps to pip")
@click.option(
    "--remote-wheelhouse",
    type=str,
    help="Install offline from a remote wheelhouse (implies --no-index --find-links)",
)
@click.argument("package_spec", nargs=-1)
def install(
    port: int | None,
    upgrade: bool,
    force_reinstall: bool,
    no_deps: bool,
    remote_wheelhouse: str | None,
    package_spec: tuple[str, ...],
) -> None:
    """Install packages into the remote Blender Python site-packages.

    Parameters
    ----------
    port : int, optional
        Optional MCP port override.
    upgrade : bool
        If True, pass `--upgrade` to pip.
    force_reinstall : bool
        If True, pass `--force-reinstall` to pip.
    no_deps : bool
        If True, pass `--no-deps` to pip.
    remote_wheelhouse : str, optional
        If provided, assume the remote is offline and install from this remote
        wheelhouse directory.
    package_spec : tuple[str, ...]
        One or more package specs (name/version constraints only).
    """
    install_packages(
        package_spec=list(package_spec),
        port=port,
        upgrade=upgrade,
        force_reinstall=force_reinstall,
        no_deps=no_deps,
        remote_wheelhouse=remote_wheelhouse,
    )


@pkg.command(
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True}
)
@click.option("--port", type=int, help="Override MCP port")
@click.argument("pip_args", nargs=-1, type=click.UNPROCESSED)
def pip(port: int | None, pip_args: tuple[str, ...]) -> None:
    """Run arbitrary pip commands on the remote Blender Python (escape hatch).

    Parameters
    ----------
    port : int, optional
        Optional MCP port override.
    pip_args : tuple[str, ...]
        Raw pip arguments. Use `--` to separate from CLI options.
    """
    if not pip_args:
        raise click.ClickException("Usage: blender-remote-cli pkg pip -- PIP_ARGS...")
    run_pip(port=port, pip_args=list(pip_args))


@pkg.command()
@click.option("--port", type=int, help="Override MCP port")
@click.option(
    "--remote-wheelhouse",
    required=True,
    type=str,
    help="Remote wheelhouse directory to write wheels into",
)
@click.option(
    "--chunk-size",
    type=int,
    default=5 * 1024 * 1024,
    show_default=True,
    help="Upload chunk size in bytes (pre-base64)",
)
@click.argument(
    "wheelhouse_or_wheel",
    nargs=-1,
    type=click.Path(exists=True, path_type=Path),
)
def push(
    port: int | None,
    remote_wheelhouse: str,
    chunk_size: int,
    wheelhouse_or_wheel: tuple[Path, ...],
) -> None:
    """Upload wheels into the remote wheelhouse cache for offline installs.

    Parameters
    ----------
    port : int, optional
        Optional MCP port override.
    remote_wheelhouse : str
        Remote directory where wheels should be written.
    chunk_size : int
        Upload chunk size in bytes (pre-base64).
    wheelhouse_or_wheel : tuple[pathlib.Path, ...]
        One or more local `.whl` files or directories to scan for `.whl` files.
    """
    if not wheelhouse_or_wheel:
        raise click.ClickException("Must provide at least one wheel file or directory")
    push_wheels(
        inputs=list(wheelhouse_or_wheel),
        remote_wheelhouse=remote_wheelhouse,
        port=port,
        chunk_size=chunk_size,
    )


@pkg.command(name="purge-cache")
@click.option("--port", type=int, help="Override MCP port")
@click.option(
    "--remote-wheelhouse",
    required=True,
    type=str,
    help="Remote wheelhouse directory to purge",
)
@click.option("--yes", is_flag=True, help="Skip confirmation")
def purge_cache(port: int | None, remote_wheelhouse: str, yes: bool) -> None:
    """Delete everything in the remote wheelhouse cache (does not uninstall packages).

    Parameters
    ----------
    port : int, optional
        Optional MCP port override.
    remote_wheelhouse : str
        Remote wheelhouse directory to purge.
    yes : bool
        If True, skip confirmation.
    """
    if not yes:
        prompt = f"Delete all cached wheels in remote wheelhouse '{remote_wheelhouse}'?"
        if not click.confirm(prompt, default=False):
            click.echo("Aborted.")
            return
    purge_remote_wheelhouse(remote_wheelhouse=remote_wheelhouse, port=port)
