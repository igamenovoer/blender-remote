"""
BLD Remote MCP - Minimal Blender Command Server with Background Support

This addon provides a simple TCP server that can run in both Blender GUI and 
background modes, allowing remote control of Blender via JSON commands.

Based on the proven blender-echo-plugin pattern.
"""

import bpy
import os
import json
import asyncio
import traceback
import signal
import atexit
from bpy.props import BoolProperty

from . import async_loop
from .utils import log_info, log_warning, log_error

bl_info = {
    "name": "BLD Remote MCP",
    "author": "Claude Code", 
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "N/A",
    "description": "Simple command server for remote Blender control with background support",
    "category": "Development",
}

# Global variables to hold the server state
tcp_server = None
server_task = None
server_port = 0

def _is_background_mode():
    """Check if Blender is running in background mode"""
    return bpy.app.background

def _signal_handler(signum, frame):
    """Handle shutdown signals in background mode"""
    log_info(f"Received signal {signum}, shutting down server...")
    cleanup_server()
    if _is_background_mode():
        bpy.ops.wm.quit_blender()

def _cleanup_on_exit():
    """Cleanup function for exit handler"""
    try:
        if tcp_server:
            log_info("BLD Remote: Cleaning up on process exit...")
            cleanup_server()
    except Exception as e:
        log_error(f"BLD Remote: Error during cleanup: {e}")

def _start_background_keepalive():
    """Note: Background keep-alive is managed by external script, not internal blocking"""
    log_info("Background mode detected - external script should manage keep-alive loop")


def cleanup_server():
    """Stop the TCP server and clean up associated resources.

    This function is idempotent and can be called multiple times without
    side effects. It closes the server, cancels the asyncio task, and resets
    the global state variables.
    """
    global tcp_server, server_task, server_port
    if not tcp_server and not server_task:
        return

    log_info("Cleaning up server...")
    
    # Background mode cleanup will be handled by external script
    
    if tcp_server:
        tcp_server.close()
        tcp_server = None
    if server_task:
        server_task.cancel()
        server_task = None
    server_port = 0
    
    try:
        if bpy.data.scenes:
            bpy.data.scenes[0].bld_remote_server_running = False
    except (AttributeError, TypeError):
        # In restricted context, can't access scenes
        pass
        
    log_info("Server cleanup complete")


def process_message(data):
    """Process an incoming JSON message from a client.

    The message can contain a simple string to be echoed or a string of
    Python code to be executed within Blender.

    Parameters
    ----------
    data : dict
        The decoded JSON data from the client.

    Returns
    -------
    dict
        A dictionary containing the response to be sent back to the client.

    Raises
    ------
    SystemExit
        If the received code contains the string "quit_blender", this
        exception is raised to signal the main script to terminate.
    """
    response = {
        "response": "OK",
        "message": "Task received",
        "source": f"tcp://127.0.0.1:{server_port}"
    }
    
    if "message" in data:
        log_info(f"Message received: {data['message']}")
        response["message"] = f"Printed message: {data['message']}"
        
    if "code" in data:
        code_to_run = data['code']
        log_info(f"Executing code: {code_to_run}")
        try:
            # Special handling for the quit command
            if "quit_blender" in code_to_run:
                log_info("Shutdown command received. Raising SystemExit")
                raise SystemExit("Shutdown requested by client")
            else:
                # Run other code in a deferred context
                def code_runner():
                    exec(code_to_run, {'bpy': bpy})
                bpy.app.timers.register(code_runner, first_interval=0.01)
                response["message"] = "Code execution scheduled"
        except Exception as e:
            log_error(f"Error executing code: {e}")
            traceback.print_exc()
            response["response"] = "FAILED"
            response["message"] = f"Error executing code: {str(e)}"
            
    return response


class BldRemoteProtocol(asyncio.Protocol):
    """The asyncio Protocol for handling client connections."""

    def connection_made(self, transport):
        """Called when a connection is made."""
        self.transport = transport
        peername = transport.get_extra_info('peername')
        log_info(f"Connection from {peername}")

    def data_received(self, data):
        """Called when data is received from the client."""
        try:
            message = json.loads(data.decode())
            response = process_message(message)
            self.transport.write(json.dumps(response).encode())
        except Exception as e:
            log_error(f"Error processing message: {e}")
            traceback.print_exc()
        finally:
            self.transport.close()

    def connection_lost(self, exc):
        """Called when the connection is lost or closed."""
        log_info("Client connection closed")


async def start_server_task(port, scene_to_update):
    """Create and start the asyncio TCP server.

    This coroutine sets up the server, starts it, and updates a scene
    property to indicate that the server is running.

    Parameters
    ----------
    port : int
        The port number for the server to listen on.
    scene_to_update : bpy.types.Scene or None
        The Blender scene to update with the server's running status.
        If None, no scene property is updated.
    """
    global tcp_server, server_task, server_port
    server_port = port
    loop = asyncio.get_event_loop()
    try:
        tcp_server = await loop.create_server(BldRemoteProtocol, '127.0.0.1', port)
        server_task = asyncio.ensure_future(tcp_server.serve_forever())
        log_info(f"BLD Remote server started on port {port}")
        if scene_to_update:
            scene_to_update.bld_remote_server_running = True
    except Exception as e:
        log_error(f"Failed to start server: {e}")
        cleanup_server()


def start_server_from_script():
    """Start the TCP server from an external script.

    This is the main entry point for starting the server. It reads the port
    from an environment variable, gets a reference to a scene, and schedules
    the `start_server_task` to run on the asyncio event loop.
    """
    port = int(os.environ.get('BLD_REMOTE_MCP_PORT', 6688))
    # Try to get scene reference, handle restricted context
    scene = None
    try:
        if hasattr(bpy.data, 'scenes') and bpy.data.scenes:
            scene = bpy.data.scenes[0]
    except (AttributeError, TypeError):
        # In restricted context, we can't access scenes - that's OK
        pass
    
    asyncio.ensure_future(start_server_task(port, scene))
    
    # Ensure the async loop machinery is ready
    try:
        async_loop.register()
    except ValueError:
        # Already registered, which is fine
        pass


# =============================================================================
# Python API Module (bld_remote)
# =============================================================================

def get_status():
    """Return service status dictionary."""
    global tcp_server, server_port
    
    return {
        "running": tcp_server is not None,
        "port": server_port,
        "address": f"127.0.0.1:{server_port}",
        "server_object": tcp_server is not None
    }


def start_mcp_service():
    """Start MCP service, raise exception on failure."""
    global tcp_server
    
    if tcp_server is not None:
        log_info("Server already running")
        return
    
    try:
        start_server_from_script()
        log_info("Server start initiated")
        
    except Exception as e:
        error_msg = f"Failed to start server: {e}"
        log_error(error_msg)
        raise RuntimeError(error_msg)


def stop_mcp_service():
    """Stop MCP service, disconnects all clients forcefully."""
    cleanup_server()


def get_startup_options():
    """Return information about environment variables."""
    return {
        'BLD_REMOTE_MCP_PORT': os.environ.get('BLD_REMOTE_MCP_PORT', '6688 (default)'),
        'BLD_REMOTE_MCP_START_NOW': os.environ.get('BLD_REMOTE_MCP_START_NOW', 'false (default)'),
        'configured_port': int(os.environ.get('BLD_REMOTE_MCP_PORT', 6688))
    }


def is_mcp_service_up():
    """Return true/false, check if MCP service is up and running."""
    return tcp_server is not None


def set_mcp_service_port(port_number):
    """Set the port number of MCP service, only callable when service is stopped."""
    global server_port
    
    if tcp_server is not None:
        raise RuntimeError("Cannot change port while server is running. Stop service first.")
    
    if not isinstance(port_number, int) or port_number < 1024 or port_number > 65535:
        raise ValueError("Port number must be an integer between 1024 and 65535")
    
    # Set environment variable for next start
    os.environ['BLD_REMOTE_MCP_PORT'] = str(port_number)
    log_info(f"MCP service port set to {port_number}")


def get_mcp_service_port():
    """Return the current configured port."""
    return int(os.environ.get('BLD_REMOTE_MCP_PORT', 6688))


# =============================================================================
# Blender Addon Registration  
# =============================================================================

def register():
    """Register the addon's properties and classes with Blender."""
    # Register async loop
    async_loop.register()
    
    # Add scene properties
    bpy.types.Scene.bld_remote_server_running = BoolProperty(
        name="BLD Remote Server Running",
        description="Indicates if the BLD Remote server is active",
        default=False
    )
    
    # Set up asyncio
    async_loop.setup_asyncio_executor()
    
    # Log startup configuration  
    from .config import log_startup_config
    log_startup_config()
    
    # Install signal handlers and exit handlers for background mode
    if _is_background_mode():
        signal.signal(signal.SIGTERM, _signal_handler)
        signal.signal(signal.SIGINT, _signal_handler)
        atexit.register(_cleanup_on_exit)
        log_info("Background mode detected - signal handlers installed")
    
    # Auto-start if configured
    from .config import should_auto_start
    if should_auto_start():
        log_info("Auto-start enabled, attempting to start server")
        try:
            start_mcp_service()
            
            # In background mode, start keep-alive loop
            if _is_background_mode():
                log_info("Background mode - starting keep-alive loop")
                _start_background_keepalive()
                
        except Exception as e:
            log_warning(f"Auto-start failed: {e}")
    
    log_info("BLD Remote MCP addon registered")


def unregister():
    """Unregister the addon and clean up all resources."""
    # Stop server
    cleanup_server()
    
    # Clean up scene properties
    try:
        del bpy.types.Scene.bld_remote_server_running
    except (AttributeError, RuntimeError):
        pass
    
    # Unregister async loop
    async_loop.unregister()
    
    log_info("BLD Remote MCP addon unregistered")


# =============================================================================
# Module Interface - Make API available as bld_remote when imported
# =============================================================================

import sys

class BldRemoteAPI:
    """API module for BLD Remote."""
    
    get_status = staticmethod(get_status)
    start_mcp_service = staticmethod(start_mcp_service)
    stop_mcp_service = staticmethod(stop_mcp_service)
    get_startup_options = staticmethod(get_startup_options)
    is_mcp_service_up = staticmethod(is_mcp_service_up)
    set_mcp_service_port = staticmethod(set_mcp_service_port)
    get_mcp_service_port = staticmethod(get_mcp_service_port)

# Register the API in sys.modules so it can be imported as 'import bld_remote'
sys.modules['bld_remote'] = BldRemoteAPI()