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
    "version": (1, 0, 2),
    "blender": (3, 0, 0),
    "location": "N/A",
    "description": "Simple command server for remote Blender control with background support [DEV-TEST-UPDATE]",
    "category": "Development",
}

# Global variables to hold the server state
tcp_server = None
server_task = None
server_port = 0

def _is_background_mode():
    """Check if Blender is running in background mode"""
    bg_mode = bpy.app.background
    log_info(f"Blender background mode check: {bg_mode}")
    return bg_mode

def _signal_handler(signum, frame):
    """Handle shutdown signals in background mode"""
    log_info(f"Signal handler triggered: signal={signum}, frame={frame}")
    log_info(f"Received signal {signum}, shutting down server...")
    cleanup_server()
    if _is_background_mode():
        log_info("Background mode detected, quitting Blender...")
        bpy.ops.wm.quit_blender()
    else:
        log_info("GUI mode detected, server stopped but Blender continues running")

def _cleanup_on_exit():
    """Cleanup function for exit handler"""
    log_info("Exit handler triggered, performing cleanup...")
    try:
        if tcp_server:
            log_info("BLD Remote: TCP server exists, cleaning up on process exit...")
            cleanup_server()
        else:
            log_info("BLD Remote: No TCP server to clean up on exit")
    except Exception as e:
        log_error(f"BLD Remote: Error during exit cleanup: {e}")
        import traceback
        log_error(f"BLD Remote: Exit cleanup traceback: {traceback.format_exc()}")

def _start_background_keepalive():
    """Note: Background keep-alive is managed by external script, not internal blocking"""
    log_info("Background mode detected - external script should manage keep-alive loop")


def get_scene_info():
    """Get information about the current Blender scene."""
    log_info("Getting scene info...")
    try:
        scene = bpy.context.scene
        scene_info = {
            "name": scene.name,
            "object_count": len(scene.objects),
            "objects": [],
            "materials_count": len(bpy.data.materials),
            "frame_current": scene.frame_current,
            "frame_start": scene.frame_start,
            "frame_end": scene.frame_end,
        }
        
        # Collect basic object information (limit to first 10 objects)
        for i, obj in enumerate(scene.objects):
            if i >= 10:
                break
            obj_info = {
                "name": obj.name,
                "type": obj.type,
                "location": list(obj.location),
                "visible": obj.visible_get(),
            }
            scene_info["objects"].append(obj_info)
        
        log_info(f"Scene info collected: {len(scene_info['objects'])} objects")
        return scene_info
    except Exception as e:
        log_error(f"Error getting scene info: {e}")
        raise


def get_object_info(object_name=None):
    """Get information about a specific object or all objects."""
    log_info(f"Getting object info for: {object_name if object_name else 'all objects'}")
    try:
        if object_name:
            # Get info for specific object
            obj = bpy.data.objects.get(object_name)
            if not obj:
                raise ValueError(f"Object '{object_name}' not found")
            
            return {
                "name": obj.name,
                "type": obj.type,
                "location": list(obj.location),
                "rotation": list(obj.rotation_euler),
                "scale": list(obj.scale),
                "visible": obj.visible_get(),
                "dimensions": list(obj.dimensions),
            }
        else:
            # Get info for all objects
            objects = []
            for obj in bpy.context.scene.objects:
                obj_info = {
                    "name": obj.name,
                    "type": obj.type,
                    "location": list(obj.location),
                    "visible": obj.visible_get(),
                }
                objects.append(obj_info)
            return {"objects": objects}
    except Exception as e:
        log_error(f"Error getting object info: {e}")
        raise


def execute_code(code=None, **kwargs):
    """Execute Python code in Blender context."""
    if not code:
        raise ValueError("No code provided")
    
    log_info(f"Executing code: {code[:100]}{'...' if len(code) > 100 else ''}")
    
    try:
        # Create execution context with full built-ins and bpy available
        # Use the same dictionary for both globals and locals to ensure proper scoping
        # This allows imports like 'import numpy as np' to work properly in functions
        exec_globals = {
            '__builtins__': __builtins__,
            'bpy': bpy,
        }
        
        # Execute the code with same dict for globals and locals
        exec(code, exec_globals, exec_globals)
        
        log_info("Code execution completed successfully")
        return {"message": "Code executed successfully"}
    except Exception as e:
        log_error(f"Error executing code: {e}")
        raise


def get_viewport_screenshot(max_size=800, filepath=None, format="png", **kwargs):
    """
    Capture a screenshot of the current 3D viewport and save it to the specified path.
    
    Parameters:
    - max_size: Maximum size in pixels for the largest dimension of the image
    - filepath: Path where to save the screenshot file
    - format: Image format (png, jpg, etc.)
    
    Returns success/error status
    """
    log_info(f"Getting viewport screenshot: filepath={filepath}, max_size={max_size}, format={format}")
    
    # Check if we're in background mode (no GUI)
    if _is_background_mode():
        log_warning("get_viewport_screenshot called in background mode - no viewport available")
        raise ValueError("Viewport screenshots are not available in background mode (blender --background)")
    
    try:
        if not filepath:
            # Generate unique temporary filename using UUID
            import uuid
            import tempfile
            temp_dir = tempfile.gettempdir()
            unique_filename = f"blender_screenshot_{uuid.uuid4().hex}.{format}"
            filepath = os.path.join(temp_dir, unique_filename)
            log_info(f"Generated unique temporary filepath: {filepath}")
        
        log_info("Searching for active 3D viewport...")
        # Find the active 3D viewport
        area = None
        for a in bpy.context.screen.areas:
            if a.type == 'VIEW_3D':
                area = a
                break
        
        if not area:
            raise ValueError("No 3D viewport found")
        
        log_info(f"Found 3D viewport area: {area}")
        
        # Take screenshot with proper context override
        log_info(f"Taking screenshot and saving to: {filepath}")
        with bpy.context.temp_override(area=area):
            bpy.ops.screen.screenshot_area(filepath=filepath)
        
        # Load and resize if needed
        log_info("Loading image for resizing...")
        img = bpy.data.images.load(filepath)
        width, height = img.size
        log_info(f"Original image size: {width}x{height}")
        
        if max(width, height) > max_size:
            log_info(f"Resizing image to max_size={max_size}")
            scale = max_size / max(width, height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            img.scale(new_width, new_height)
            
            # Set format and save
            img.file_format = format.upper()
            img.save()
            width, height = new_width, new_height
            log_info(f"Resized image to: {width}x{height}")
        
        # Cleanup Blender image data
        bpy.data.images.remove(img)
        
        result = {
            "success": True,
            "width": width,
            "height": height,
            "filepath": filepath
        }
        log_info(f"Screenshot captured successfully: {result}")
        return result
        
    except Exception as e:
        log_error(f"Error capturing viewport screenshot: {e}")
        raise


def cleanup_server():
    """Stop the TCP server and clean up associated resources.

    This function is idempotent and can be called multiple times without
    side effects. It closes the server, cancels the asyncio task, and resets
    the global state variables.
    """
    global tcp_server, server_task, server_port
    
    log_info(f"cleanup_server() called - tcp_server={tcp_server is not None}, server_task={server_task is not None}, server_port={server_port}")
    
    if not tcp_server and not server_task:
        log_info("cleanup_server: No server or task to clean up, returning early")
        return

    log_info("Starting server cleanup process...")
    
    # Background mode cleanup will be handled by external script
    log_info(f"Background mode: {_is_background_mode()}")
    
    if tcp_server:
        log_info("Closing TCP server...")
        try:
            tcp_server.close()
            log_info("TCP server closed successfully")
        except Exception as e:
            log_error(f"Error closing TCP server: {e}")
        tcp_server = None
        log_info("TCP server reference cleared")
        
    if server_task:
        log_info("Cancelling server task...")
        try:
            server_task.cancel()
            log_info("Server task cancelled successfully")
        except Exception as e:
            log_error(f"Error cancelling server task: {e}")
        server_task = None
        log_info("Server task reference cleared")
        
    old_port = server_port
    server_port = 0
    log_info(f"Server port reset from {old_port} to 0")
    
    # Update scene property
    try:
        if hasattr(bpy, 'data') and hasattr(bpy.data, 'scenes') and bpy.data.scenes:
            log_info("Updating scene property bld_remote_server_running to False...")
            bpy.data.scenes[0].bld_remote_server_running = False
            log_info("Scene property updated successfully")
        else:
            log_info("No scenes available to update property")
    except (AttributeError, TypeError) as e:
        # In restricted context, can't access scenes
        log_info(f"Cannot access scenes to update property (restricted context): {e}")
    except Exception as e:
        log_error(f"Unexpected error updating scene property: {e}")
        
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
    log_info(f"process_message() called with data keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
    log_info(f"Current server_port: {server_port}")
    
    # Check if this is a command-based message (BlenderAutoMCP compatibility)
    if "type" in data:
        cmd_type = data.get("type")
        params = data.get("params", {})
        log_info(f"Processing command type: {cmd_type}")
        
        # Handle basic commands that LLM clients expect
        if cmd_type == "get_scene_info":
            try:
                scene_info = get_scene_info()
                return {"status": "success", "result": scene_info}
            except Exception as e:
                log_error(f"Error getting scene info: {e}")
                return {"status": "error", "message": str(e)}
        
        elif cmd_type == "get_object_info":
            try:
                object_info = get_object_info(**params)
                return {"status": "success", "result": object_info}
            except Exception as e:
                log_error(f"Error getting object info: {e}")
                return {"status": "error", "message": str(e)}
        
        elif cmd_type == "execute_code":
            try:
                code_result = execute_code(**params)
                return {"status": "success", "result": code_result}
            except Exception as e:
                log_error(f"Error executing code: {e}")
                return {"status": "error", "message": str(e)}
        
        elif cmd_type == "server_shutdown":
            log_info("Server shutdown command received")
            # Schedule shutdown
            def delayed_shutdown():
                cleanup_server()
                if _is_background_mode():
                    bpy.ops.wm.quit_blender()
                return None
            bpy.app.timers.register(delayed_shutdown, first_interval=1.0)
            return {"status": "success", "message": "Server shutdown initiated"}
        
        elif cmd_type == "get_viewport_screenshot":
            try:
                screenshot_result = get_viewport_screenshot(**params)
                return {"status": "success", "result": screenshot_result}
            except Exception as e:
                log_error(f"Error getting viewport screenshot: {e}")
                return {"status": "error", "message": str(e)}
        
        elif cmd_type == "get_polyhaven_status":
            # Asset provider not supported - return disabled status
            return {"status": "success", "result": {"enabled": False, "reason": "Asset providers not supported"}}
        
        else:
            # Unknown command type
            log_warning(f"Unknown command type: {cmd_type}")
            return {"status": "error", "message": f"Unknown command type: {cmd_type}"}
    
    # Legacy message/code processing for backward compatibility
    response = {
        "response": "OK",
        "message": "Task received",
        "source": f"tcp://127.0.0.1:{server_port}"
    }
    log_info(f"Initial response prepared: {response}")
    
    if "message" in data:
        message_content = data['message']
        log_info(f"Processing message field: '{message_content}' (length: {len(message_content) if message_content else 0})")
        response["message"] = f"Printed message: {message_content}"
        log_info(f"Message processed, response updated")
        
    if "code" in data:
        code_to_run = data['code']
        code_length = len(code_to_run) if code_to_run else 0
        log_info(f"Processing code field (length: {code_length})")
        log_info(f"Code to execute: {code_to_run[:200]}{'...' if code_length > 200 else ''}")
        
        try:
            # Special handling for the quit command
            if "quit_blender" in code_to_run:
                log_info("Detected quit_blender command in code")
                log_info("Shutdown command received. Raising SystemExit")
                raise SystemExit("Shutdown requested by client")
            else:
                log_info("Code does not contain quit_blender, proceeding with execution")
                
                # Run other code in a deferred context
                def code_runner():
                    log_info(f"code_runner() executing: {code_to_run[:100]}{'...' if len(code_to_run) > 100 else ''}")
                    try:
                        # Create execution context with full built-ins and bpy available
                        # Use the same dictionary for both globals and locals to ensure proper scoping
                        # This allows imports like 'import numpy as np' to work properly in functions
                        exec_globals = {
                            '__builtins__': __builtins__,
                            'bpy': bpy,
                        }
                        exec(code_to_run, exec_globals, exec_globals)
                        log_info("Code execution completed successfully")
                    except Exception as exec_e:
                        log_error(f"Error during code execution in timer: {exec_e}")
                        import traceback
                        log_error(f"Code execution traceback: {traceback.format_exc()}")
                        
                log_info("Registering code_runner with Blender timer system...")
                bpy.app.timers.register(code_runner, first_interval=0.01)
                response["message"] = "Code execution scheduled"
                log_info("Code execution scheduled successfully")
                
        except SystemExit:
            log_info("SystemExit raised, re-raising for shutdown")
            raise
        except Exception as e:
            log_error(f"Error processing code execution: {e}")
            log_error(f"Exception type: {type(e).__name__}")
            traceback.print_exc()
            response["response"] = "FAILED"
            response["message"] = f"Error executing code: {str(e)}"
            log_error(f"Error response prepared: {response}")
            
    log_info(f"Final response: {response}")
    return response


class BldRemoteProtocol(asyncio.Protocol):
    """The asyncio Protocol for handling client connections."""

    def __init__(self):
        """Initialize protocol instance."""
        self.transport = None
        self.connection_start_time = None
        self.buffer = b''  # Buffer for incomplete messages
        log_info("BldRemoteProtocol instance created")

    def connection_made(self, transport):
        """Called when a connection is made."""
        import time
        self.transport = transport
        self.connection_start_time = time.time()
        peername = transport.get_extra_info('peername')
        sockname = transport.get_extra_info('sockname')
        log_info(f"NEW CLIENT CONNECTION from {peername} to {sockname}")
        log_info(f"Transport details: {transport}")
        log_info(f"Connection established at {self.connection_start_time}")

    def data_received(self, data):
        """Called when data is received from the client."""
        import time
        receive_time = time.time()
        data_length = len(data)
        log_info(f"DATA RECEIVED: {data_length} bytes at {receive_time}")
        log_info(f"Raw data preview: {data[:200]}{'...' if data_length > 200 else ''}")
        
        # Add to buffer
        self.buffer += data
        
        # Try to process complete messages from buffer
        while self.buffer:
            try:
                log_info("Attempting to decode buffered data as UTF-8...")
                decoded_data = self.buffer.decode('utf-8')
                log_info(f"Data decoded successfully, length: {len(decoded_data)}")
                
                log_info("Attempting to parse JSON...")
                message = json.loads(decoded_data)
                log_info(f"JSON parsed successfully: {type(message)} with keys {list(message.keys()) if isinstance(message, dict) else 'not a dict'}")
                
                # Clear buffer after successful parse
                self.buffer = b''
                
                log_info("Calling process_message()...")
                response = process_message(message)
                log_info(f"process_message() returned: {response}")
                
                log_info("Encoding response as JSON...")
                response_json = json.dumps(response)
                response_bytes = response_json.encode()
                log_info(f"Response encoded: {len(response_bytes)} bytes")
                
                log_info("Sending response to client...")
                self.transport.write(response_bytes)
                log_info("Response sent successfully")
                
            except json.JSONDecodeError as e:
                # Incomplete JSON - wait for more data
                log_info(f"Incomplete JSON data, waiting for more: {e}")
                break
            except UnicodeDecodeError as e:
                log_error(f"Unicode decode error: {e}")
                log_error(f"Invalid UTF-8 data received")
                # Clear buffer and send error response
                self.buffer = b''
                error_response = {"status": "error", "message": f"Invalid UTF-8: {str(e)}"}
                try:
                    self.transport.write(json.dumps(error_response).encode())
                except Exception as send_error:
                    log_error(f"Failed to send error response: {send_error}")
                break
            except Exception as e:
                log_error(f"Unexpected error processing message: {e}")
                log_error(f"Exception type: {type(e).__name__}")
                traceback.print_exc()
                # Clear buffer and send error response
                self.buffer = b''
                error_response = {"status": "error", "message": f"Processing error: {str(e)}"}
                try:
                    self.transport.write(json.dumps(error_response).encode())
                except Exception as send_error:
                    log_error(f"Failed to send error response: {send_error}")
                break

    def connection_lost(self, exc):
        """Called when the connection is lost or closed."""
        import time
        end_time = time.time()
        duration = end_time - self.connection_start_time if self.connection_start_time else 0
        
        if exc:
            log_info(f"CLIENT CONNECTION LOST with exception: {exc} (duration: {duration:.3f}s)")
        else:
            log_info(f"CLIENT CONNECTION CLOSED normally (duration: {duration:.3f}s)")
        
        log_info(f"Connection ended at {end_time}")


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
    
    log_info(f"=== START_SERVER_TASK BEGINNING ===")
    log_info(f"start_server_task() called with port={port}, scene_to_update={scene_to_update}")
    log_info(f"Current global state: tcp_server={tcp_server}, server_task={server_task}, server_port={server_port}")
    
    server_port = port
    log_info(f"Global server_port updated to: {server_port}")
    
    log_info("Getting asyncio event loop...")
    loop = asyncio.get_event_loop()
    log_info(f"Got asyncio event loop: {loop}")
    log_info(f"Loop is closed: {loop.is_closed()}")
    log_info(f"Loop is running: {loop.is_running()}")
    
    try:
        log_info(f"About to create TCP server on 127.0.0.1:{port}")
        log_info(f"Using protocol factory: {BldRemoteProtocol}")
        
        tcp_server = await loop.create_server(BldRemoteProtocol, '127.0.0.1', port)
        log_info(f"TCP server created successfully: {tcp_server}")
        log_info(f"Server socket info: {tcp_server.sockets}")
        
        log_info("Creating serve_forever task...")
        server_task = asyncio.ensure_future(tcp_server.serve_forever())
        log_info(f"Server task created: {server_task}")
        
        log_info(f"✅ BLD Remote server STARTED successfully on port {port}")
        log_info(f"Server is now listening for connections on 127.0.0.1:{port}")
        
        if scene_to_update:
            log_info(f"Updating scene property for scene: {scene_to_update}")
            scene_to_update.bld_remote_server_running = True
            log_info("✅ Scene property bld_remote_server_running set to True")
        else:
            log_info("No scene to update (scene_to_update is None)")
        
        log_info(f"=== START_SERVER_TASK COMPLETED SUCCESSFULLY ===")
            
    except OSError as e:
        # Handle socket-specific errors with detailed logging
        if "Address already in use" in str(e) or "address already in use" in str(e).lower():
            log_error(f"ERROR: Port {port} is already in use by another process")
            log_error(f"ERROR: Cannot start BLD Remote MCP server - port conflict detected")
            log_error(f"ERROR: Try using a different port or kill the process using port {port}")
            log_error(f"ERROR: Use 'netstat -tulnp | grep {port}' or 'lsof -i:{port}' to find the conflicting process")
        elif "Only one usage of each socket address" in str(e):
            log_error(f"ERROR: Port {port} is already in use (Windows)")
            log_error(f"ERROR: Cannot start BLD Remote MCP server - port conflict detected")
            log_error(f"ERROR: Try using a different port or close the application using port {port}")
        elif "Permission denied" in str(e) and port < 1024:
            log_error(f"ERROR: Permission denied for port {port} (privileged port)")
            log_error(f"ERROR: Ports below 1024 require administrator/root privileges")
            log_error(f"ERROR: Try using a port number above 1024 (e.g., 6688, 8080, 9999)")
        elif "Permission denied" in str(e):
            log_error(f"ERROR: Permission denied for port {port}")
            log_error(f"ERROR: Check if another service is using this port or if firewall is blocking it")
        else:
            log_error(f"ERROR: Socket error starting server on port {port}: {e}")
            log_error(f"ERROR: This is typically a port conflict or network configuration issue")
        
        log_error(f"ERROR: Socket error details: {type(e).__name__}: {e}")
        log_error(f"=== START_SERVER_TASK FAILED WITH SOCKET ERROR ===")
        cleanup_server()
        
    except PermissionError as e:
        log_error(f"ERROR: Permission denied starting server on port {port}")
        log_error(f"ERROR: {e}")
        if port < 1024:
            log_error(f"ERROR: Port {port} is a privileged port requiring administrator/root access")
            log_error(f"ERROR: Try using a port above 1024 (e.g., 6688, 8080, 9999)")
        else:
            log_error(f"ERROR: Check if firewall or security software is blocking port {port}")
        log_error(f"=== START_SERVER_TASK FAILED WITH PERMISSION ERROR ===")
        cleanup_server()
        
    except Exception as e:
        log_error(f"ERROR: Failed to start server on port {port}: {e}")
        log_error(f"ERROR: Exception type: {type(e).__name__}")
        import traceback
        log_error(f"ERROR: Detailed traceback: {traceback.format_exc()}")
        log_error(f"=== START_SERVER_TASK FAILED WITH UNEXPECTED ERROR ===")
        cleanup_server()


def start_server_from_script():
    """Start the TCP server from an external script.

    This is the main entry point for starting the server. It reads the port
    from an environment variable, gets a reference to a scene, and schedules
    the `start_server_task` to run on the asyncio event loop.
    """
    log_info("=== START_SERVER_FROM_SCRIPT BEGINNING ===")
    log_info("start_server_from_script() called")
    
    # Parse port from environment
    log_info("Reading port configuration from environment...")
    port_str = os.environ.get('BLD_REMOTE_MCP_PORT', '6688')
    log_info(f"Raw port value from environment: '{port_str}'")
    
    try:
        port = int(port_str)
        log_info(f"Port parsed successfully: {port}")
        if port < 1024 or port > 65535:
            log_error(f"ERROR: Invalid port {port}. Port must be between 1024 and 65535")
            log_error(f"ERROR: Consider using ports like 6688, 8080, 9999")
            log_error(f"=== START_SERVER_FROM_SCRIPT FAILED - INVALID PORT ===")
            return
        log_info(f"Port validation passed: {port}")
    except ValueError as e:
        log_error(f"ERROR: Invalid port value '{port_str}'. Must be a valid integer")
        log_error(f"ERROR: Port parsing failed: {e}")
        log_error(f"=== START_SERVER_FROM_SCRIPT FAILED - PORT PARSE ERROR ===")
        return
    
    log_info(f"✅ Starting server on port {port}")
    log_info(f"Background mode: {_is_background_mode()}")
    
    # Set up asyncio executor first
    log_info("Setting up asyncio executor...")
    try:
        async_loop.setup_asyncio_executor()
        log_info("✅ Asyncio executor setup completed")
    except Exception as e:
        log_error(f"ERROR: Failed to setup asyncio executor: {e}")
        log_error(f"=== START_SERVER_FROM_SCRIPT FAILED - ASYNCIO SETUP ERROR ===")
        return
    
    # Try to get scene reference, handle restricted context
    log_info("Attempting to get scene reference...")
    scene = None
    try:
        if hasattr(bpy, 'data'):
            log_info("bpy.data is available")
            if hasattr(bpy.data, 'scenes'):
                log_info("bpy.data.scenes is available")
                if bpy.data.scenes:
                    scene = bpy.data.scenes[0]
                    log_info(f"✅ Scene reference obtained: {scene} (name: {scene.name if hasattr(scene, 'name') else 'unknown'})")
                else:
                    log_info("bpy.data.scenes is empty")
            else:
                log_info("bpy.data.scenes is not available")
        else:
            log_info("bpy.data is not available")
    except (AttributeError, TypeError) as e:
        # In restricted context, we can't access scenes - that's OK
        log_info(f"Cannot access scenes (restricted context): {e}")
    except Exception as e:
        log_warning(f"Unexpected error getting scene reference: {e}")
    
    log_info(f"Scene reference result: {scene}")
    
    # Schedule the server task
    log_info(f"Scheduling server task for port {port}...")
    try:
        future = asyncio.ensure_future(start_server_task(port, scene))
        log_info(f"✅ Server task scheduled: {future}")
    except Exception as e:
        log_error(f"ERROR: Failed to schedule server task: {e}")
        log_error(f"=== START_SERVER_FROM_SCRIPT FAILED - TASK SCHEDULING ERROR ===")
        return
    
    # Ensure the async loop machinery is ready and start the modal operator
    log_info("Registering async loop machinery...")
    try:
        async_loop.register()
        log_info("✅ Async loop registered successfully")
    except ValueError as e:
        # Already registered, which is fine
        log_info(f"Async loop already registered: {e}")
    except Exception as e:
        log_error(f"ERROR: Failed to register async loop: {e}")
        log_error(f"=== START_SERVER_FROM_SCRIPT FAILED - ASYNC LOOP REGISTRATION ERROR ===")
        return
    
    # Start the modal operator to process asyncio events
    log_info("Starting modal operator for asyncio event processing...")
    try:
        async_loop.ensure_async_loop()
        log_info("✅ Modal operator started successfully")
        log_info(f"=== START_SERVER_FROM_SCRIPT COMPLETED SUCCESSFULLY ===")
    except Exception as e:
        log_error(f"ERROR: Failed to start modal operator: {e}")
        log_error(f"=== START_SERVER_FROM_SCRIPT FAILED - MODAL OPERATOR ERROR ===")


# =============================================================================
# Python API Module (bld_remote)
# =============================================================================

def get_status():
    """Return service status dictionary."""
    global tcp_server, server_port
    
    log_info(f"get_status() called - tcp_server={tcp_server is not None}, server_port={server_port}")
    
    status = {
        "running": tcp_server is not None,
        "port": server_port,
        "address": f"127.0.0.1:{server_port}",
        "server_object": tcp_server is not None
    }
    
    log_info(f"Status result: {status}")
    return status


def start_mcp_service():
    """Start MCP service, raise exception on failure."""
    global tcp_server
    
    log_info("start_mcp_service() called")
    log_info(f"Current server state: tcp_server={tcp_server is not None}")
    
    if tcp_server is not None:
        log_info("⚠️ Server already running, nothing to do")
        return
    
    log_info("Server not running, attempting to start...")
    try:
        start_server_from_script()
        log_info("✅ Server start initiated successfully")
        
    except Exception as e:
        error_msg = f"Failed to start server: {e}"
        log_error(f"ERROR in start_mcp_service(): {error_msg}")
        import traceback
        log_error(f"Traceback: {traceback.format_exc()}")
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
    log_info("=== BLD REMOTE MCP ADDON REGISTRATION STARTING ===")
    log_info("🚀 DEV-TEST-UPDATE: BLD Remote MCP v1.0.2 Loading!")
    log_info("🔧 This is the UPDATED version with development test modifications")
    log_info("🛠️ UPDATE #2: Added context fallback fix for modal operator")
    log_info("register() function called")
    
    # Check Blender environment
    log_info(f"Blender version: {bpy.app.version}")
    log_info(f"Blender background mode: {_is_background_mode()}")
    log_info(f"Python path: {os.sys.path[:3]}...")  # Show first few paths
    
    # Register async loop
    log_info("Registering async loop machinery...")
    try:
        async_loop.register()
        log_info("✅ Async loop registered successfully")
    except Exception as e:
        log_error(f"ERROR: Failed to register async loop: {e}")
        raise
    
    # Add scene properties
    log_info("Adding scene properties...")
    try:
        bpy.types.Scene.bld_remote_server_running = BoolProperty(
            name="BLD Remote Server Running",
            description="Indicates if the BLD Remote server is active",
            default=False
        )
        log_info("✅ Scene property 'bld_remote_server_running' added")
    except Exception as e:
        log_error(f"ERROR: Failed to add scene property: {e}")
        raise
    
    # Set up asyncio
    log_info("Setting up asyncio executor...")
    try:
        async_loop.setup_asyncio_executor()
        log_info("✅ Asyncio executor setup completed")
    except Exception as e:
        log_error(f"ERROR: Failed to setup asyncio executor: {e}")
        raise
    
    # Log startup configuration  
    log_info("Loading and logging startup configuration...")
    try:
        from .config import log_startup_config
        log_startup_config()
        log_info("✅ Startup configuration logged")
    except Exception as e:
        log_error(f"ERROR: Failed to log startup config: {e}")
        # Don't raise here, this is non-critical
    
    # Install signal handlers and exit handlers for background mode
    background_mode = _is_background_mode()
    if background_mode:
        log_info("Background mode detected, installing signal handlers...")
        try:
            signal.signal(signal.SIGTERM, _signal_handler)
            signal.signal(signal.SIGINT, _signal_handler)
            log_info("✅ Signal handlers (SIGTERM, SIGINT) installed")
            
            atexit.register(_cleanup_on_exit)
            log_info("✅ Exit handler registered")
            
            log_info("Background mode setup completed")
        except Exception as e:
            log_error(f"ERROR: Failed to setup background mode handlers: {e}")
            # Don't raise, continue with registration
    else:
        log_info("GUI mode detected, skipping signal handler installation")
    
    # Auto-start if configured
    log_info("Checking auto-start configuration...")
    try:
        from .config import should_auto_start
        auto_start = should_auto_start()
        log_info(f"Auto-start enabled: {auto_start}")
        
        if auto_start:
            log_info("✅ Auto-start enabled, attempting to start server")
            try:
                start_mcp_service()
                log_info("✅ Auto-start server initialization completed")
                
                # In background mode, start keep-alive loop
                if background_mode:
                    log_info("Background mode - starting keep-alive loop")
                    _start_background_keepalive()
                    log_info("✅ Background keep-alive setup completed")
                    
            except Exception as e:
                log_warning(f"⚠️ Auto-start failed: {e}")
                import traceback
                log_warning(f"Auto-start failure traceback: {traceback.format_exc()}")
        else:
            log_info("Auto-start disabled, server will not start automatically")
    except Exception as e:
        log_error(f"ERROR: Failed to check auto-start config: {e}")
        # Don't raise, continue with registration
    
    log_info("✅ BLD Remote MCP addon registered successfully")
    log_info("=== BLD REMOTE MCP ADDON REGISTRATION COMPLETED ===")


def unregister():
    """Unregister the addon and clean up all resources."""
    log_info("=== BLD REMOTE MCP ADDON UNREGISTRATION STARTING ===")
    log_info("unregister() function called")
    
    # Stop server
    log_info("Stopping server and cleaning up resources...")
    try:
        cleanup_server()
        log_info("✅ Server cleanup completed")
    except Exception as e:
        log_error(f"ERROR: Failed to cleanup server: {e}")
        # Continue with unregistration
    
    # Clean up scene properties
    log_info("Removing scene properties...")
    try:
        del bpy.types.Scene.bld_remote_server_running
        log_info("✅ Scene property 'bld_remote_server_running' removed")
    except (AttributeError, RuntimeError) as e:
        log_info(f"Scene property already removed or not accessible: {e}")
    except Exception as e:
        log_error(f"ERROR: Unexpected error removing scene property: {e}")
    
    # Unregister async loop
    log_info("Unregistering async loop machinery...")
    try:
        async_loop.unregister()
        log_info("✅ Async loop unregistered successfully")
    except Exception as e:
        log_error(f"ERROR: Failed to unregister async loop: {e}")
        # Continue anyway
    
    log_info("✅ BLD Remote MCP addon unregistered successfully")
    log_info("=== BLD REMOTE MCP ADDON UNREGISTRATION COMPLETED ===")


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