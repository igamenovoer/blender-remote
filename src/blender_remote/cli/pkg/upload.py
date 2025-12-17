"""Remote filesystem upload utilities.

This module provides chunked file upload helpers used by `blender-remote-cli pkg`
to transfer wheels (and other small artifacts) into the remote Blender host.

Notes
-----
The remote transfer is implemented by sending small Python snippets to the MCP
`execute_code` command. Each snippet embeds one chunk as base64 and appends it to
an on-disk `.part` file. After all chunks are written, the `.part` file is
atomically moved into place with `os.replace`.
"""

from __future__ import annotations

import base64
from pathlib import Path

import click

from blender_remote.cli.pkg.remote_exec import execute_json


def upload_file(
    *,
    local_path: Path,
    remote_path: str,
    port: int,
    chunk_size: int,
) -> None:
    """Upload a local file to the remote filesystem via chunked execution.

    Parameters
    ----------
    local_path : pathlib.Path
        Local file path to upload.
    remote_path : str
        Absolute path on the remote host where the file should be written.
    port : int
        MCP TCP port of the remote Blender MCP service.
    chunk_size : int
        Chunk size in bytes, before base64 expansion.

    Raises
    ------
    click.ClickException
        If the local file is missing, empty, or chunk_size is invalid.
    """
    if chunk_size <= 0:
        raise click.ClickException("--chunk-size must be > 0")

    if not local_path.exists():
        raise click.ClickException(f"Local file not found: {local_path}")

    total = local_path.stat().st_size
    if total <= 0:
        raise click.ClickException(f"Refusing to upload empty file: {local_path}")

    part_path = f"{remote_path}.part"

    chunk_index = 0
    with local_path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break

            chunk_index += 1

            chunk_b64 = base64.b64encode(chunk).decode("ascii")
            mode = "wb" if chunk_index == 1 else "ab"

            code = rf"""
import base64
import json
from pathlib import Path

remote_path = {remote_path!r}
part_path = {part_path!r}
Path(part_path).parent.mkdir(parents=True, exist_ok=True)

data = base64.b64decode({chunk_b64!r}.encode("ascii"))
with open(part_path, {mode!r}) as f:
    f.write(data)

print(json.dumps({{"ok": True, "bytes_written": len(data)}}, ensure_ascii=True))
"""

            # Avoid double-base64 (the code already embeds base64 data).
            execute_json(
                code=code,
                port=port,
                socket_timeout_seconds=120.0,
                remote_timeout_seconds=120.0,
                code_is_base64=False,
            )

    if chunk_index == 0:
        raise click.ClickException(f"Refusing to upload empty file: {local_path}")

    finalize_code = rf"""
import json
import os

remote_path = {remote_path!r}
part_path = {part_path!r}
os.replace(part_path, remote_path)
print(json.dumps({{"ok": True}}, ensure_ascii=True))
"""
    execute_json(
        code=finalize_code,
        port=port,
        socket_timeout_seconds=120.0,
        remote_timeout_seconds=120.0,
        code_is_base64=True,
    )
