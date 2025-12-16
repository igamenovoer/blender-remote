"""Shared constants for the blender-remote CLI."""

from __future__ import annotations

import os
from pathlib import Path

import platformdirs

# Cross-platform configuration directory using platformdirs
CONFIG_DIR = Path(platformdirs.user_config_dir(appname="blender-remote", appauthor="blender-remote"))
CONFIG_FILE = CONFIG_DIR / "bld-remote-config.yaml"

# Configuration constants that align with MCPServerConfig
# NOTE: These values must stay in sync with MCPServerConfig in mcp_server.py
DEFAULT_PORT = 6688  # Should match MCPServerConfig.FALLBACK_BLENDER_PORT
DETECT_BLENDER_INFO_TIMEOUT_SECONDS = float(os.environ.get("BLENDER_REMOTE_DETECT_TIMEOUT", "120"))
SOCKET_TIMEOUT_SECONDS = 60.0  # Should match MCPServerConfig.SOCKET_TIMEOUT_SECONDS
SOCKET_RECV_CHUNK_SIZE = 131072  # Should match MCPServerConfig.SOCKET_RECV_CHUNK_SIZE (128KB)
SOCKET_MAX_RESPONSE_SIZE = 10 * 1024 * 1024  # Should match MCPServerConfig.SOCKET_MAX_RESPONSE_SIZE (10MB)

