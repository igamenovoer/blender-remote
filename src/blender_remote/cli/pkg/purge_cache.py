"""Remote wheelhouse cache management."""

from __future__ import annotations

import click

from blender_remote.cli.pkg.ports import resolve_mcp_port
from blender_remote.cli.pkg.remote_exec import execute_json


def purge_remote_wheelhouse(*, remote_wheelhouse: str, port: int | None) -> None:
    """Delete all files/directories in the remote wheelhouse cache.

    Parameters
    ----------
    remote_wheelhouse : str
        Remote directory path to purge.
    port : int, optional
        Optional MCP port override.

    Raises
    ------
    click.ClickException
        If `remote_wheelhouse` is empty or the remote command fails.
    """
    if not remote_wheelhouse:
        raise click.ClickException("--remote-wheelhouse is required")

    mcp_port = resolve_mcp_port(port)
    remote_wheelhouse_norm = remote_wheelhouse.replace("\\", "/")

    code = rf"""
import json
import shutil
from pathlib import Path

wheelhouse = Path({remote_wheelhouse_norm!r}).expanduser()

deleted_files = 0
deleted_dirs = 0

if wheelhouse.exists() and wheelhouse.is_dir():
    for child in wheelhouse.iterdir():
        try:
            if child.is_dir():
                shutil.rmtree(child)
                deleted_dirs += 1
            else:
                child.unlink()
                deleted_files += 1
        except Exception:
            # Best-effort purge; report counts only.
            pass

print(json.dumps({{
    "wheelhouse": str(wheelhouse),
    "existed": wheelhouse.exists(),
    "deleted_files": deleted_files,
    "deleted_dirs": deleted_dirs,
}}, ensure_ascii=True))
"""

    result = execute_json(
        code=code,
        port=mcp_port,
        socket_timeout_seconds=120.0,
        remote_timeout_seconds=300.0,
        code_is_base64=True,
    )

    click.echo(
        f"[OK] Purged remote wheelhouse {result.get('wheelhouse')} "
        f"(files={result.get('deleted_files')}, dirs={result.get('deleted_dirs')})"
    )
