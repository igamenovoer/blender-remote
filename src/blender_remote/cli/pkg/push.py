"""Upload local wheels to a remote wheelhouse cache."""

from __future__ import annotations

from pathlib import Path

import click

from blender_remote.cli.pkg.ports import resolve_mcp_port
from blender_remote.cli.pkg.upload import upload_file


def push_wheels(
    *,
    inputs: list[Path],
    remote_wheelhouse: str,
    port: int | None,
    chunk_size: int,
) -> None:
    """Upload one or more `.whl` files into a remote wheelhouse directory.

    Parameters
    ----------
    inputs : list[pathlib.Path]
        One or more local wheel files or directories to scan for `.whl` files.
    remote_wheelhouse : str
        Remote directory path where wheels should be written.
    port : int, optional
        Optional MCP port override.
    chunk_size : int
        Upload chunk size in bytes (pre-base64).

    Raises
    ------
    click.ClickException
        If no wheels are found, inputs are invalid, or uploads fail.
    """
    if chunk_size <= 0:
        raise click.ClickException("--chunk-size must be > 0")

    if not remote_wheelhouse:
        raise click.ClickException("--remote-wheelhouse is required")

    mcp_port = resolve_mcp_port(port)

    remote_wheelhouse_norm = remote_wheelhouse.replace("\\", "/").rstrip("/")

    wheel_files: list[Path] = []
    for item in inputs:
        if item.is_dir():
            wheel_files.extend(sorted(item.rglob("*.whl")))
        elif item.is_file() and item.suffix.lower() == ".whl":
            wheel_files.append(item)
        else:
            raise click.ClickException(
                f"Unsupported input: {item} (expected .whl file or directory)"
            )

    if not wheel_files:
        raise click.ClickException("No .whl files found to upload")

    seen: set[Path] = set()
    unique_wheels: list[Path] = []
    for wheel in wheel_files:
        wheel_resolved = wheel.resolve()
        if wheel_resolved in seen:
            continue
        seen.add(wheel_resolved)
        unique_wheels.append(wheel)

    for wheel_path in unique_wheels:
        filename = wheel_path.name
        if ".." in filename or "/" in filename or "\\" in filename:
            raise click.ClickException(f"Unsafe wheel filename: {filename}")

        remote_path = f"{remote_wheelhouse_norm}/{filename}"
        click.echo(f"[PUSH] {wheel_path} -> {remote_path}")
        upload_file(
            local_path=wheel_path,
            remote_path=remote_path,
            port=mcp_port,
            chunk_size=chunk_size,
        )

    click.echo(
        f"[OK] Uploaded {len(unique_wheels)} wheel(s) to {remote_wheelhouse_norm}"
    )
