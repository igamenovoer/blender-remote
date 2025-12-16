from __future__ import annotations

import os
import subprocess
import tempfile

import click

from ..config import BlenderRemoteConfig
from ..constants import DEFAULT_PORT
from ..scripts import KEEPALIVE_SCRIPT


@click.command()
@click.option("--background", is_flag=True, help="Start Blender in background mode")
@click.option(
    "--pre-file",
    type=click.Path(exists=True),
    help="Python file to execute before startup",
)
@click.option("--pre-code", help="Python code to execute before startup")
@click.option("--port", type=int, help="Override default MCP port")
@click.option(
    "--scene",
    type=click.Path(exists=True),
    help="Open specified .blend scene file",
)
@click.option(
    "--log-level",
    type=click.Choice(
        ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False
    ),
    help="Override logging level for BLD_Remote_MCP",
)
@click.argument("blender_args", nargs=-1, type=click.UNPROCESSED)
def start(
    background: bool,
    pre_file: str | None,
    pre_code: str | None,
    port: int | None,
    scene: str | None,
    log_level: str | None,
    blender_args: tuple,
) -> int | None:
    """Start Blender with the BLD_Remote_MCP service enabled.

    Parameters
    ----------
    background:
        If ``True``, run Blender in background (headless) mode and use the
        keep-alive loop to keep the process alive for remote control.
    pre_file:
        Optional Python file executed in Blender prior to starting the MCP
        service; mutually exclusive with ``pre_code``.
    pre_code:
        Optional inline Python code executed before MCP startup; mutually
        exclusive with ``pre_file``.
    port:
        Optional TCP port override for the MCP service; if omitted, falls back
        to ``mcp_service.default_port`` from configuration or ``DEFAULT_PORT``.
    scene:
        Optional ``.blend`` file path to open when starting Blender.
    log_level:
        Optional log level string (e.g. ``\"DEBUG\"``, ``\"INFO\"``); if omitted,
        uses the configured ``mcp_service.log_level`` or ``\"INFO\"``.
    blender_args:
        Additional raw arguments passed directly to the Blender executable.

    Returns
    -------
    int or None
        The Blender process return code, or ``None`` if execution is interrupted
        before the subprocess completes.
    """
    if pre_file and pre_code:
        raise click.ClickException("Cannot use both --pre-file and --pre-code options")

    # Load config
    config = BlenderRemoteConfig()
    blender_config = config.get("blender")

    if not blender_config:
        raise click.ClickException("Blender configuration not found. Run 'init' first.")

    blender_path = blender_config.get("exec_path")
    mcp_port = port or config.get("mcp_service.default_port") or DEFAULT_PORT
    mcp_log_level = log_level or config.get("mcp_service.log_level") or "INFO"

    # Prepare startup code
    startup_code = []

    # Add pre-code if provided
    if pre_file:
        with open(pre_file) as f:
            startup_code.append(f.read())
    elif pre_code:
        startup_code.append(pre_code)

    # Add MCP service startup code - environment variables are set in shell
    startup_code.append(
        """
# Verify MCP environment configuration
import os
port = os.environ.get('BLD_REMOTE_MCP_PORT', 'not set')
start_now = os.environ.get('BLD_REMOTE_MCP_START_NOW', 'not set')
log_level = os.environ.get('BLD_REMOTE_LOG_LEVEL', 'not set')

print("[INFO] Environment: PORT=" + str(port) + ", START_NOW=" + str(start_now) + ", LOG_LEVEL=" + str(log_level))
print("[INFO] MCP service will start via addon auto-start mechanism")
"""
    )

    # In background mode, add proper keep-alive mechanism
    if background:
        startup_code.append(KEEPALIVE_SCRIPT)

    # Create temporary script file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as temp_file:
        temp_file.write("\n".join(startup_code))
        temp_script = temp_file.name

    try:
        # Build command
        cmd = [blender_path]

        # Add scene file if provided (must come before --background for background mode)
        if scene:
            cmd.append(scene)

        if background:
            cmd.append("--background")

        cmd.extend(["--python", temp_script])

        # Add additional blender arguments
        if blender_args:
            cmd.extend(blender_args)

        click.echo(f"[START] Starting Blender with BLD_Remote_MCP on port {mcp_port}...")

        if scene:
            click.echo(f"[SCENE] Opening scene: {scene}")

        if log_level:
            click.echo(f"[LOG] Log level override: {mcp_log_level.upper()}")

        if background:
            click.echo("[MODE] Background mode: Blender will run headless")
        else:
            click.echo("[MODE] GUI mode: Blender window will open")

        # Set up environment variables for Blender
        blender_env = os.environ.copy()
        blender_env["BLD_REMOTE_MCP_PORT"] = str(mcp_port)
        blender_env["BLD_REMOTE_MCP_START_NOW"] = "1"  # CLI always auto-starts
        blender_env["BLD_REMOTE_LOG_LEVEL"] = mcp_log_level.upper()

        # Execute Blender
        result = subprocess.run(cmd, timeout=None, env=blender_env)

        return result.returncode

    finally:
        # Clean up temporary script
        try:
            os.unlink(temp_script)
        except Exception:
            pass

