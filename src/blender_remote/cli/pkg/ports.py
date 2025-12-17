"""Port resolution helpers for `blender-remote-cli`.

Functions
---------
resolve_mcp_port : Resolve the effective MCP port from CLI/config/defaults.
"""

from __future__ import annotations

from blender_remote.cli.config import BlenderRemoteConfig
from blender_remote.cli.constants import DEFAULT_PORT


def resolve_mcp_port(port: int | None) -> int:
    """Resolve the MCP port to connect to.

    Precedence is:
    1) explicit CLI option
    2) configuration value (`mcp_service.default_port`)
    3) built-in default (`DEFAULT_PORT`)

    Parameters
    ----------
    port : int, optional
        Optional explicit MCP port.

    Returns
    -------
    int
        The effective MCP port.
    """
    if port is not None:
        return port

    config = BlenderRemoteConfig()
    configured = config.get("mcp_service.default_port")
    return int(configured) if configured is not None else DEFAULT_PORT
