"""Configuration management for BLD Remote MCP addon."""

import os
from .utils import log_info, log_warning


def get_mcp_port():
    """Get MCP port from environment or default to 6688."""
    port_str = os.environ.get('BLD_REMOTE_MCP_PORT', '6688')
    try:
        port = int(port_str)
        if port < 1024 or port > 65535:
            log_warning(f"Invalid port {port}, using default 6688")
            return 6688
        return port
    except ValueError:
        log_warning(f"Invalid port value '{port_str}', using default 6688")
        return 6688


def should_auto_start():
    """Check if service should start automatically."""
    start_now = os.environ.get('BLD_REMOTE_MCP_START_NOW', 'false').lower()
    return start_now in ('true', '1', 'yes', 'on')


def get_startup_options():
    """Return information about environment variables."""
    return {
        'BLD_REMOTE_MCP_PORT': os.environ.get('BLD_REMOTE_MCP_PORT', '6688 (default)'),
        'BLD_REMOTE_MCP_START_NOW': os.environ.get('BLD_REMOTE_MCP_START_NOW', 'false (default)'),
        'auto_start_enabled': should_auto_start(),
        'configured_port': get_mcp_port()
    }


def log_startup_config():
    """Log the current startup configuration."""
    options = get_startup_options()
    log_info("Startup configuration:")
    log_info(f"  Port: {options['configured_port']}")
    log_info(f"  Auto-start: {options['auto_start_enabled']}")
    log_info(f"  BLD_REMOTE_MCP_PORT: {options['BLD_REMOTE_MCP_PORT']}")
    log_info(f"  BLD_REMOTE_MCP_START_NOW: {options['BLD_REMOTE_MCP_START_NOW']}")