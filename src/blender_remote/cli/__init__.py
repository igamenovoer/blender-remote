"""blender-remote CLI package.

This package backs the `blender-remote-cli` entrypoint.
"""

from .app import cli
from .config import BlenderRemoteConfig

__all__ = ["BlenderRemoteConfig", "cli"]
