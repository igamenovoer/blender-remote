"""
Blender MCP Remote Tools - Human-friendly Python APIs for remote-controlling Blender

This module provides easy-to-use Python classes for interacting with a running Blender process
via the MCP (Model Context Protocol) server. Designed for human programmers, not AI agents.

Examples
--------
Basic usage:
    >>> from blender_tools.remote import BlenderMCPClient, BlenderAssetManager, BlenderSceneManager
    >>> 
    >>> # Connect to Blender
    >>> client = BlenderMCPClient()
    >>> 
    >>> # Manage assets
    >>> assets = BlenderAssetManager(client)
    >>> collections = assets.list_library_collections("blender-assets")
    >>> 
    >>> # Manage scene
    >>> scene = BlenderSceneManager(client)
    >>> scene.clear_scene()
    >>> scene.add_cube(location=np.array([0, 0, 0]))
"""

from .data_types import SceneObject, BlenderMCPError
from .blender_mcp_client import BlenderMCPClient
from .blender_asset_manager import BlenderAssetManager
from .blender_scene_manager import BlenderSceneManager

__all__ = [
    "BlenderMCPClient",
    "BlenderMCPError",
    "BlenderAssetManager",
    "BlenderSceneManager",
    "SceneObject",
]


# Convenience functions for quick access
def connect_to_blender(host: str = None, port: int = 9876) -> BlenderMCPClient:
    """
    Connect to Blender MCP server.
    
    Parameters
    ----------
    host : str, optional
        Server hostname (auto-detects if None).
    port : int, default 9876
        Server port.
        
    Returns
    -------
    BlenderMCPClient
        BlenderMCPClient instance.
        
    Raises
    ------
    BlenderMCPError
        If connection fails.
    """
    client = BlenderMCPClient(host, port)
    if not client.test_connection():
        raise BlenderMCPError(f"Cannot connect to Blender MCP server at {client.host}:{client.port}")
    return client


def quick_scene_setup():
    """
    Quick setup for Blender remote control.
    
    Returns
    -------
    tuple of (BlenderMCPClient, BlenderAssetManager, BlenderSceneManager)
        Tuple of (client, asset_manager, scene_manager).
    """
    client = connect_to_blender()
    assets = BlenderAssetManager(client)
    scene = BlenderSceneManager(client)
    return client, assets, scene