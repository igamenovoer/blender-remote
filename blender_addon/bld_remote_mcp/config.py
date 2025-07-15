"""Configuration management for BLD Remote MCP addon."""

import os
from .utils import log_info, log_warning, log_debug, log_error


def get_mcp_port():
    """Get MCP port from environment or default to 6688."""
    log_debug("Reading MCP port configuration...")
    port_str = os.environ.get('BLD_REMOTE_MCP_PORT', '6688')
    log_info(f"BLD_REMOTE_MCP_PORT: {port_str}")
    
    try:
        port = int(port_str)
        log_debug(f"Port parsed as integer: {port}")
        
        if port < 1024 or port > 65535:
            log_warning(f"Invalid port {port} (out of range 1024-65535), using default 6688")
            return 6688
        
        log_info(f"Using port: {port}")
        return port
    except ValueError as e:
        log_warning(f"Invalid port value '{port_str}' (not an integer), using default 6688")
        log_debug(f"Port parsing error: {e}")
        return 6688


def should_auto_start():
    """Check if service should start automatically."""
    log_debug("Checking auto-start configuration...")
    start_now_raw = os.environ.get('BLD_REMOTE_MCP_START_NOW', 'false')
    start_now = start_now_raw.lower()
    log_info(f"BLD_REMOTE_MCP_START_NOW: {start_now_raw}")
    
    auto_start_values = ('true', '1', 'yes', 'on')
    result = start_now in auto_start_values
    log_info(f"Auto-start enabled: {result}")
    return result


def get_startup_options():
    """Return information about environment variables."""
    log_debug("Gathering startup options...")
    
    # Get raw environment values
    port_env = os.environ.get('BLD_REMOTE_MCP_PORT')
    start_env = os.environ.get('BLD_REMOTE_MCP_START_NOW')
    
    # Format display values
    port_display = port_env if port_env else '6688 (default)'
    start_display = start_env if start_env else 'false (default)'
    
    options = {
        'BLD_REMOTE_MCP_PORT': port_display,
        'BLD_REMOTE_MCP_START_NOW': start_display,
        'auto_start_enabled': should_auto_start(),
        'configured_port': get_mcp_port()
    }
    
    log_debug(f"Startup options compiled: {options}")
    return options


def log_startup_config():
    """Log the current startup configuration."""
    log_debug("=== STARTUP CONFIGURATION ===")
    try:
        # Get configuration values using the functions that already log essential info
        configured_port = get_mcp_port()  # This will log port info
        auto_start = should_auto_start()  # This will log auto-start info
        
        log_debug("=== STARTUP CONFIGURATION COMPLETE ===")
    except Exception as e:
        log_error(f"ERROR: Failed to log startup configuration: {e}")
        import traceback
        log_error(f"Traceback: {traceback.format_exc()}")