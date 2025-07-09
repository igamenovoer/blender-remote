"""
Blender Remote Control Library

A Python package for remotely controlling Blender through MCP server connections.
"""

__version__ = "0.1.0"
__author__ = "blender-remote contributors"

# Import main entry points
from .mcp_server import main as mcp_server_main
from .cli import main as cli_main

__all__ = ["mcp_server_main", "cli_main", "__version__"]