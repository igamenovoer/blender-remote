from __future__ import annotations

import click

from ..config import BlenderRemoteConfig
from ..constants import DEFAULT_PORT
from ..transport import connect_and_send_command


@click.command()
@click.option(
    "--port",
    type=int,
    help="Override default MCP port; if omitted, use mcp_service.default_port from config or the built-in default",
)
def status(port: int | None) -> None:
    """Check connection status to a running Blender MCP service.

    Parameters
    ----------
    port:
        Optional MCP port to query. If ``None``, the CLI uses the port from
        configuration (``mcp_service.default_port``) or ``DEFAULT_PORT``.
    """
    click.echo("Checking connection to Blender BLD_Remote_MCP service...")

    # Resolve port: explicit CLI argument wins, otherwise fall back to config/default.
    effective_port: int
    if port is not None:
        effective_port = port
    else:
        config = BlenderRemoteConfig()
        configured_port = config.get("mcp_service.default_port")
        effective_port = configured_port or DEFAULT_PORT

    response = connect_and_send_command("get_scene_info", port=effective_port)

    if response.get("status") == "success":
        click.echo(f"Connected to Blender BLD_Remote_MCP service (port {effective_port})")
        scene_info = response.get("result", {})
        scene_name = scene_info.get("name", "Unknown")
        object_count = scene_info.get("object_count", 0)
        click.echo(f"   Scene: {scene_name}")
        click.echo(f"   Objects: {object_count}")
    else:
        error_msg = response.get("message", "Unknown error")
        click.echo(f"Connection failed: {error_msg}")
        click.echo("   Make sure Blender is running with BLD_Remote_MCP addon enabled")

