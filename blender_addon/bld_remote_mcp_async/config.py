"""Configuration management for BLD Remote MCP addon."""

import os
from .utils import log_info, log_warning


def get_mcp_port():
    """Get MCP port from environment or default to 6688."""
    log_info("Reading MCP port configuration...")
    port_str = os.environ.get('BLD_REMOTE_MCP_PORT', '6688')
    log_info(f"Raw port value from environment: '{port_str}'")
    
    try:
        port = int(port_str)
        log_info(f"Port parsed as integer: {port}")
        
        if port < 1024 or port > 65535:
            log_warning(f"Invalid port {port} (out of range 1024-65535), using default 6688")
            return 6688
        
        log_info(f"Valid port configured: {port}")
        return port
    except ValueError as e:
        log_warning(f"Invalid port value '{port_str}' (not an integer), using default 6688")
        log_warning(f"Port parsing error: {e}")
        return 6688


def should_auto_start():
    """Check if service should start automatically."""
    log_info("Checking auto-start configuration...")
    start_now_raw = os.environ.get('BLD_REMOTE_MCP_START_NOW', 'false')
    start_now = start_now_raw.lower()
    log_info(f"Raw auto-start value: '{start_now_raw}' -> normalized: '{start_now}'")
    
    auto_start_values = ('true', '1', 'yes', 'on')
    result = start_now in auto_start_values
    log_info(f"Auto-start enabled: {result} (checked against: {auto_start_values})")
    return result


def get_startup_options():
    """Return information about environment variables."""
    log_info("Gathering startup options...")
    
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
    
    log_info(f"Startup options compiled: {options}")
    return options


def log_startup_config():
    """Log the current startup configuration."""
    log_info("=== STARTUP CONFIGURATION ===")
    try:
        options = get_startup_options()
        log_info("Current BLD Remote MCP configuration:")
        log_info(f"  ⚙️  Configured Port: {options['configured_port']}")
        log_info(f"  ▶️  Auto-start Enabled: {options['auto_start_enabled']}")
        log_info(f"  🌍 Environment Variables:")
        log_info(f"    BLD_REMOTE_MCP_PORT: {options['BLD_REMOTE_MCP_PORT']}")
        log_info(f"    BLD_REMOTE_MCP_START_NOW: {options['BLD_REMOTE_MCP_START_NOW']}")
        
        # Additional environment info
        log_info(f"  💻 Environment details:")
        for key in ['BLD_REMOTE_MCP_PORT', 'BLD_REMOTE_MCP_START_NOW']:
            env_value = os.environ.get(key)
            if env_value:
                log_info(f"    {key} is SET to '{env_value}'")
            else:
                log_info(f"    {key} is NOT SET (using default)")
                
        log_info("=== STARTUP CONFIGURATION COMPLETE ===")
    except Exception as e:
        log_error(f"ERROR: Failed to log startup configuration: {e}")
        import traceback
        log_error(f"Traceback: {traceback.format_exc()}")