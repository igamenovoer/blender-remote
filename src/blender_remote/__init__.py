"""
Blender Remote Control Library

A Python package for remotely controlling Blender through MCP server connections.
"""

from typing import Optional, Callable, Any

__version__ = "1.1.0"
__author__ = "blender-remote contributors"

# Import main entry points (conditionally)
mcp_server_main: Optional[Callable[[], Any]] = None
cli_main: Optional[Callable[[], Any]] = None

try:
    from .mcp_server import main as mcp_server_main
except ImportError:
    pass

try:
    from .cli import cli as cli_main
except ImportError:
    pass

# Import core API components
from .client import BlenderMCPClient
from .scene_manager import BlenderSceneManager
from .asset_manager import BlenderAssetManager

# Import data types
from .data_types import (
    SceneObject,
    AssetLibrary,
    AssetCollection,
    RenderSettings,
    CameraSettings,
    MaterialSettings,
    SceneInfo,
    ExportSettings,
)

# Import exceptions
from .exceptions import (
    BlenderRemoteError,
    BlenderMCPError,
    BlenderConnectionError,
    BlenderCommandError,
    BlenderTimeoutError,
)


# Convenience factory functions
def connect_to_blender(
    host: str = "localhost", port: int = 6688, timeout: float = 30.0
) -> BlenderMCPClient:
    """
    Connect to BLD Remote MCP service.

    Parameters
    ----------
    host : str, default "localhost"
        Blender MCP service hostname.
    port : int, default 6688
        Blender MCP service port.
    timeout : float, default 30.0
        Connection timeout in seconds.

    Returns
    -------
    BlenderMCPClient
        Connected client instance.
    """
    return BlenderMCPClient(host=host, port=port, timeout=timeout)


def create_scene_manager(
    client: Optional[BlenderMCPClient] = None, **kwargs: Any
) -> BlenderSceneManager:
    """
    Create a BlenderSceneManager instance.

    Parameters
    ----------
    client : BlenderMCPClient, optional
        Existing client instance. If None, creates new client with kwargs.
    **kwargs
        Arguments passed to BlenderMCPClient constructor if client is None.

    Returns
    -------
    BlenderSceneManager
        Scene manager instance.
    """
    if client is None:
        client = connect_to_blender(**kwargs)
    return BlenderSceneManager(client)


def create_asset_manager(
    client: Optional[BlenderMCPClient] = None, **kwargs: Any
) -> BlenderAssetManager:
    """
    Create a BlenderAssetManager instance.

    Parameters
    ----------
    client : BlenderMCPClient, optional
        Existing client instance. If None, creates new client with kwargs.
    **kwargs
        Arguments passed to BlenderMCPClient constructor if client is None.

    Returns
    -------
    BlenderAssetManager
        Asset manager instance.
    """
    if client is None:
        client = connect_to_blender(**kwargs)
    return BlenderAssetManager(client)


# Build __all__ list dynamically based on what's available
__all__ = [
    # Version and metadata
    "__version__",
    # Core API (always available)
    "BlenderMCPClient",
    "BlenderSceneManager",
    "BlenderAssetManager",
    # Data types
    "SceneObject",
    "AssetLibrary",
    "AssetCollection",
    "RenderSettings",
    "CameraSettings",
    "MaterialSettings",
    "SceneInfo",
    "ExportSettings",
    # Exceptions
    "BlenderRemoteError",
    "BlenderMCPError",
    "BlenderConnectionError",
    "BlenderCommandError",
    "BlenderTimeoutError",
    # Convenience functions
    "connect_to_blender",
    "create_scene_manager",
    "create_asset_manager",
]

# Add conditionally imported items
if mcp_server_main is not None:
    __all__.append("mcp_server_main")
if cli_main is not None:
    __all__.append("cli_main")
