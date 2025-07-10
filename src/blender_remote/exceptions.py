"""
Custom exceptions for Blender Remote Control Library.
"""


class BlenderRemoteError(Exception):
    """Base exception for Blender Remote Control operations."""

    pass


class BlenderMCPError(BlenderRemoteError):
    """Exception raised when MCP communication fails."""

    pass


class BlenderConnectionError(BlenderMCPError):
    """Exception raised when connection to Blender MCP service fails."""

    pass


class BlenderCommandError(BlenderMCPError):
    """Exception raised when a Blender command execution fails."""

    pass


class BlenderTimeoutError(BlenderMCPError):
    """Exception raised when a Blender operation times out."""

    pass
