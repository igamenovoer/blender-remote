"""
BLD Remote MCP - Synchronous Blender Command Server with Background Support

This addon provides a synchronous TCP server that executes Python code immediately
and returns results with captured output. Works in both Blender GUI and background modes.

Architecture based on threading (not asyncio) for simplified synchronous execution.
"""

import bpy
import os
import json
import threading
import socket
import time
import signal
import atexit
import traceback
import io
import sys
import base64
import queue
from contextlib import redirect_stdout, redirect_stderr
from bpy.props import BoolProperty
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass

from . import persist
from .utils import log_info, log_warning, log_error, log_debug
from .config import get_mcp_port, should_auto_start


class BldRemoteMCPConfig:
    """Configuration constants for BLD Remote MCP server."""
    
    # Network Configuration
    DEFAULT_HOST = '127.0.0.1'
    DEFAULT_PORT = 6688
    SOCKET_LISTEN_BACKLOG = 5
    SOCKET_TIMEOUT_SECONDS = 1.0
    SOCKET_RECV_BUFFER_SIZE = 8192
    
    # Command Execution Timeouts
    COMMAND_EXECUTION_TIMEOUT_SECONDS = 30.0
    TIMER_FIRST_INTERVAL_SECONDS = 0.0
    SHUTDOWN_DELAY_SECONDS = 1.0
    
    # Threading and Polling
    THREAD_JOIN_TIMEOUT_SECONDS = 3.0
    POLLING_SLEEP_INTERVAL_SECONDS = 0.01
    ERROR_RECOVERY_SLEEP_SECONDS = 0.5
    
    # Data Limits and Formatting
    MAX_OBJECTS_IN_SCENE_INFO = 10
    LOCATION_PRECISION_DIGITS = 2
    CODE_PREVIEW_LENGTH = 100
    DEFAULT_VIEWPORT_MAX_SIZE = 800
    
    # Port Validation
    MIN_PORT_NUMBER = 1024
    MAX_PORT_NUMBER = 65535
    
    # Scene Index for Properties
    DEFAULT_SCENE_INDEX = 0
    
    # Version Information
    ADDON_VERSION = (1, 2, 3)
    BLENDER_MIN_VERSION = (3, 0, 0)
    
    # Initial State Values
    INITIAL_SERVER_PORT = 0
    
    # Socket Configuration
    SOCKET_REUSE_ADDRESS = 1
    
    # Version String for Logging
    VERSION_STRING = "v1.2.3"
    
    # Counter and State Values
    INITIAL_COUNTER_VALUE = 0
    QUEUE_EMPTY_SIZE = 0
    COUNTER_INCREMENT = 1
    
    # String Encoding Constants
    STRING_ENCODING_UTF8 = 'utf-8'
    STRING_ENCODING_ASCII = 'ascii'

bl_info = {
    "name": "BLD Remote MCP",
    "author": "Claude Code", 
    "version": (1, 2, 3),
    "blender": (3, 0, 0),
    "location": "N/A",
    "description": "Dual-mode command server for remote Blender control (GUI timer + background queue)",
    "category": "Development",
}

# Global server state
_tcp_server = None
_server_socket = None
_server_thread = None
_server_running = False
_server_port = BldRemoteMCPConfig.INITIAL_SERVER_PORT
_client_threads = []

# Background mode command queue
_command_queue = None
_background_mode = None


@dataclass
class ExecutionJob:
    """Represents a command execution job for background mode queue processing."""
    command: Dict[str, Any]
    callback: Callable[[Dict[str, Any]], None]
    completed: threading.Event
    result: Optional[Dict[str, Any]] = None


@dataclass
class ExecutionResult:
    """Result of synchronous code execution."""
    success: bool
    output: Dict[str, str]  # stdout, stderr
    result: Optional[Any]   # Extracted result value
    duration: float         # Execution time in seconds
    error: Optional[str]    # Error message if failed
    traceback: Optional[str] # Full traceback if failed
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON-serializable format."""
        return {
            "status": "success" if self.success else "error",
            "result": self._serialize_result(),
            "output": self.output,
            "duration": self.duration,
            "error": self.error,
            "traceback": self.traceback,
        }
    
    def _serialize_result(self):
        """Serialize result to JSON-compatible format."""
        if self.result is None:
            return None
        
        try:
            # Try direct JSON serialization first
            json.dumps(self.result)
            return self.result
        except (TypeError, ValueError):
            # Fallback to string representation
            return str(self.result)


class OutputCapture:
    """Comprehensive output capture for Blender operations."""
    
    def __init__(self):
        self.stdout_buffer = io.StringIO()
        self.stderr_buffer = io.StringIO()
        self.original_stdout = None
        self.original_stderr = None
        
    def __enter__(self):
        """Start capturing output streams."""
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = self.stdout_buffer
        sys.stderr = self.stderr_buffer
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore original output streams."""
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        
    def get_output(self) -> Dict[str, str]:
        """Get captured output."""
        return {
            "stdout": self.stdout_buffer.getvalue(),
            "stderr": self.stderr_buffer.getvalue(),
        }


class BldRemoteMCPServer:
    """Dual-mode TCP server for Blender remote control (GUI timer + background queue)."""
    
    def __init__(self, host=BldRemoteMCPConfig.DEFAULT_HOST, port=BldRemoteMCPConfig.DEFAULT_PORT):
        self.host = host
        self.port = port
        self.running = False
        self.server_socket = None
        self.server_thread = None
        self.client_threads = []
        self.background_mode = bpy.app.background
        
        # Background mode command queue for manual processing
        self.command_queue = queue.Queue() if self.background_mode else None
        
        log_debug(f"BldRemoteMCPServer initialized in {'background' if self.background_mode else 'GUI'} mode")
        
        # Install signal handlers for background mode
        if self.background_mode:
            # SIGINT is supported on all platforms
            signal.signal(signal.SIGINT, self._signal_handler)
            
            # SIGTERM is not available on Windows
            try:
                signal.signal(signal.SIGTERM, self._signal_handler)
            except (AttributeError, ValueError):
                # SIGTERM not available on this platform (e.g., Windows)
                log_debug("SIGTERM not available on this platform, using SIGINT only")
            
            atexit.register(self._cleanup_on_exit)
            log_debug("Background mode: Signal handlers and command queue initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals in background mode."""
        log_info(f"Received signal {signum}, shutting down server...")
        self.stop()
        if self.background_mode:
            bpy.ops.wm.quit_blender()
    
    def _cleanup_on_exit(self):
        """Cleanup function for exit handler."""
        try:
            if self.running:
                log_info("BLD Remote: Cleaning up on process exit...")
                self.stop()
        except Exception as e:
            log_error(f"BLD Remote: Error during cleanup: {e}")
    
    def start(self):
        """Start the TCP server."""
        if self.running:
            log_info("Server is already running")
            return True
            
        self.running = True
        
        try:
            # Create socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Note: Removed SO_REUSEADDR to ensure proper port conflict detection
            # Multiple instances should fail when trying to bind to the same port
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(BldRemoteMCPConfig.SOCKET_LISTEN_BACKLOG)
            
            # Start server thread
            self.server_thread = threading.Thread(target=self._server_loop)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            log_info(f"BLD Remote MCP server started on {self.host}:{self.port}")
            return True
                
        except OSError as e:
            log_error(f"Failed to start server on port {self.port}: {str(e)}")
            self.stop()
            return False
        except Exception as e:
            log_error(f"Failed to start server: {str(e)}")
            self.stop()
            return False
    
    def _server_loop(self):
        """Main server loop in a separate thread."""
        log_debug("Server thread started")
        self.server_socket.settimeout(BldRemoteMCPConfig.SOCKET_TIMEOUT_SECONDS)  # Timeout to allow for stopping
        
        while self.running:
            try:
                try:
                    client, address = self.server_socket.accept()
                    log_debug(f"Connected to client: {address}")
                    
                    # Handle client in a separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client,)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    self.client_threads.append(client_thread)
                except socket.timeout:
                    # Just check running condition
                    continue
                except Exception as e:
                    if self.running:  # Only log if we're supposed to be running
                        log_error(f"Error accepting connection: {str(e)}")
                    time.sleep(BldRemoteMCPConfig.ERROR_RECOVERY_SLEEP_SECONDS)
            except Exception as e:
                if self.running:  # Only log if we're supposed to be running
                    log_error(f"Error in server loop: {str(e)}")
                if not self.running:
                    break
                time.sleep(BldRemoteMCPConfig.ERROR_RECOVERY_SLEEP_SECONDS)
        
        log_debug("Server thread stopped")
    
    def _handle_client(self, client):
        """Handle connected client with synchronous execution."""
        log_debug("Client handler started")
        client.settimeout(None)  # No timeout
        buffer = b''
        
        try:
            while self.running:
                try:
                    data = client.recv(BldRemoteMCPConfig.SOCKET_RECV_BUFFER_SIZE)
                    if not data:
                        log_debug("Client disconnected")
                        break
                    
                    buffer += data
                    try:
                        # Try to parse command
                        command = json.loads(buffer.decode(BldRemoteMCPConfig.STRING_ENCODING_UTF8))
                        buffer = b''
                        
                        # Execute command synchronously in main thread using timer
                        response = self._execute_command_sync(command)
                        response_json = json.dumps(response)
                        
                        try:
                            client.sendall(response_json.encode(BldRemoteMCPConfig.STRING_ENCODING_UTF8))
                        except:
                            log_debug("Failed to send response - client disconnected")
                            break
                    except json.JSONDecodeError:
                        # Incomplete data, wait for more
                        pass
                except Exception as e:
                    log_error(f"Error receiving data: {str(e)}")
                    break
        except Exception as e:
            log_error(f"Error in client handler: {str(e)}")
        finally:
            try:
                client.close()
            except:
                pass
            log_debug("Client handler stopped")

    def _execute_command_sync(self, command):
        """Execute command synchronously using appropriate method based on mode."""
        if self.background_mode:
            # Background mode: Use queue-based execution with manual processing
            return self._execute_command_background_mode(command)
        else:
            # GUI mode: Use timer-based execution (existing approach)
            return self._execute_command_gui_mode(command)
    
    def _execute_command_gui_mode(self, command):
        """Execute command in GUI mode using Blender timers (existing approach)."""
        log_debug("Executing command in GUI mode using timer approach")
        
        # Use a shared container to get results from timer callback
        result_container = {"response": None, "done": False}
        
        def execute_wrapper():
            try:
                result_container["response"] = self.execute_command(command)
            except Exception as e:
                log_error(f"Error executing command: {str(e)}")
                result_container["response"] = {
                    "status": "error",
                    "message": str(e)
                }
            finally:
                result_container["done"] = True
            return None
        
        # Schedule execution in main thread
        bpy.app.timers.register(execute_wrapper, first_interval=BldRemoteMCPConfig.TIMER_FIRST_INTERVAL_SECONDS)
        
        # Wait for completion (polling)
        timeout = BldRemoteMCPConfig.COMMAND_EXECUTION_TIMEOUT_SECONDS  # Command execution timeout
        start_time = time.time()
        while not result_container["done"]:
            time.sleep(BldRemoteMCPConfig.POLLING_SLEEP_INTERVAL_SECONDS)  # Small sleep to avoid busy waiting
            if time.time() - start_time > timeout:
                return {"status": "error", "message": "Command execution timeout"}
        
        return result_container["response"]
    
    def _execute_command_background_mode(self, command):
        """Execute command in background mode using queue and callback system."""
        log_debug("Executing command in background mode using queue approach")
        
        # Create result container and synchronization event
        result_container = {"response": None}
        result_event = threading.Event()
        
        def result_callback(response: Dict[str, Any]) -> None:
            """Callback function to receive the result from main thread."""
            result_container["response"] = response
            result_event.set()
        
        # Create and queue the execution job
        job = ExecutionJob(
            command=command,
            callback=result_callback,
            completed=result_event
        )
        
        self.command_queue.put(job)
        log_debug(f"Command queued for background processing, queue size: {self.command_queue.qsize()}")
        
        # Wait for the result with timeout
        timeout = BldRemoteMCPConfig.COMMAND_EXECUTION_TIMEOUT_SECONDS  # Command execution timeout
        if result_event.wait(timeout):
            response = result_container.get("response")
            log_debug("Background command execution completed successfully")
            return response
        else:
            error_msg = f"Background command execution timeout after {timeout} seconds"
            log_error(error_msg)
            return {"status": "error", "message": error_msg}
    
    def step(self) -> None:
        """Process all pending commands in the queue - called manually in background mode."""
        if not self.background_mode or not self.command_queue:
            log_debug("step() called but not in background mode or no queue available")
            return
        
        processed_count = BldRemoteMCPConfig.INITIAL_COUNTER_VALUE
        
        # Process all jobs in the queue
        while not self.command_queue.empty():
            try:
                job = self.command_queue.get_nowait()
                processed_count += BldRemoteMCPConfig.COUNTER_INCREMENT
                
                log_debug(f"Processing command job {processed_count}: {job.command.get('type', 'unknown')}")
                
                # Execute the command in the main thread (thread-safe for Blender)
                try:
                    response = self.execute_command(job.command)
                    job.result = response
                    log_debug(f"Command job {processed_count} completed successfully")
                    
                except Exception as e:
                    error_response = {
                        "status": "error", 
                        "message": f"Command execution error: {str(e)}"
                    }
                    job.result = error_response
                    log_error(f"Command job {processed_count} failed: {e}")
                
                # Call the callback to notify the waiting thread
                try:
                    job.callback(job.result)
                    job.completed.set()
                except Exception as e:
                    log_error(f"Callback error for command job {processed_count}: {e}")
                    job.completed.set()
                
            except queue.Empty:
                break
            except Exception as e:
                log_error(f"Error processing command job: {e}")
        
        if processed_count > BldRemoteMCPConfig.INITIAL_COUNTER_VALUE:
            log_debug(f"step() processed {processed_count} command jobs")

    def execute_command(self, command):
        """Execute a command in the main Blender thread."""
        try:            
            return self._execute_command_internal(command)
                
        except Exception as e:
            log_error(f"Error executing command: {str(e)}")
            traceback.print_exc()
            return {"status": "error", "message": str(e)}

    def _execute_command_internal(self, command):
        """Internal command execution with proper context."""
        cmd_type = command.get("type")
        params = command.get("params", {})

        # Command handlers
        handlers = {
            "get_scene_info": self.get_scene_info,
            "get_object_info": self.get_object_info,
            "get_viewport_screenshot": self.get_viewport_screenshot,
            "execute_code": self.execute_code,
            "server_shutdown": self.server_shutdown,
            "get_polyhaven_status": self.get_polyhaven_status,
            "put_persist_data": self.put_persist_data,
            "get_persist_data": self.get_persist_data,
            "remove_persist_data": self.remove_persist_data,
        }

        handler = handlers.get(cmd_type)
        if handler:
            try:
                log_debug(f"Executing handler for {cmd_type}")
                result = handler(**params)
                log_debug(f"Handler execution complete")
                return {"status": "success", "result": result}
            except Exception as e:
                log_error(f"Error in handler: {str(e)}")
                traceback.print_exc()
                return {"status": "error", "message": str(e)}
        else:
            # Handle legacy message/code format for backward compatibility
            return self._handle_legacy_command(command)

    def _handle_legacy_command(self, data):
        """Handle legacy message/code format."""
        response = {
            "response": "OK",
            "message": "Task received",
            "source": f"tcp://{BldRemoteMCPConfig.DEFAULT_HOST}:{self.port}"
        }
        
        if "message" in data:
            message_content = data['message']
            log_debug(f"Processing message field: '{message_content}'")
            response["message"] = f"Printed message: {message_content}"
            
        if "code" in data:
            code_to_run = data['code']
            log_debug(f"Processing code field (length: {len(code_to_run)})")
            
            try:
                # Special handling for the quit command
                if "quit_blender" in code_to_run:
                    log_info("Detected quit_blender command in code")
                    log_info("Shutdown command received. Raising SystemExit")
                    raise SystemExit("Shutdown requested by client")
                else:
                    # Execute code synchronously with output capture
                    exec_result = self._execute_code_with_capture(code_to_run)
                    if exec_result.success:
                        response["message"] = "Code executed successfully"
                        if exec_result.output.get("stdout"):
                            response["output"] = exec_result.output["stdout"]
                    else:
                        response["response"] = "FAILED"
                        response["message"] = f"Error executing code: {exec_result.error}"
                        
            except SystemExit:
                log_info("SystemExit raised, re-raising for shutdown")
                raise
            except Exception as e:
                log_error(f"Error processing code execution: {e}")
                response["response"] = "FAILED"
                response["message"] = f"Error executing code: {str(e)}"
                
        return response

    def server_shutdown(self):
        """Shutdown command for graceful server termination."""
        def delayed_shutdown():
            self.stop()
            if self.background_mode:
                bpy.ops.wm.quit_blender()
            return None
        
        # Schedule shutdown after a brief delay
        bpy.app.timers.register(delayed_shutdown, first_interval=BldRemoteMCPConfig.SHUTDOWN_DELAY_SECONDS)
        return {"message": "Server shutdown initiated"}
    
    def stop(self):
        """Stop the TCP server."""
        log_info("Stopping BLD Remote MCP server...")
        self.running = False
        
        # Close socket first to stop accepting new connections
        if self.server_socket:
            try:
                self.server_socket.shutdown(socket.SHUT_RDWR)
            except:
                pass
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
        
        # Wait for server thread to finish
        if self.server_thread:
            try:
                if self.server_thread.is_alive():
                    self.server_thread.join(timeout=BldRemoteMCPConfig.THREAD_JOIN_TIMEOUT_SECONDS)
                    if self.server_thread.is_alive():
                        log_warning("Warning: Server thread did not stop cleanly")
            except:
                pass
            self.server_thread = None
        
        log_info("BLD Remote MCP server stopped")

    def get_scene_info(self):
        """Get information about the current Blender scene."""
        try:
            log_debug("Getting scene info...")
            scene_info = {
                "name": bpy.context.scene.name,
                "object_count": len(bpy.context.scene.objects),
                "objects": [],
                "materials_count": len(bpy.data.materials),
                "frame_current": bpy.context.scene.frame_current,
                "frame_start": bpy.context.scene.frame_start,
                "frame_end": bpy.context.scene.frame_end,
            }
            
            # Collect minimal object information (limit to first N objects)
            for i, obj in enumerate(bpy.context.scene.objects):
                if i >= BldRemoteMCPConfig.MAX_OBJECTS_IN_SCENE_INFO:
                    break
                    
                obj_info = {
                    "name": obj.name,
                    "type": obj.type,
                    "location": [round(float(obj.location.x), BldRemoteMCPConfig.LOCATION_PRECISION_DIGITS), 
                                round(float(obj.location.y), BldRemoteMCPConfig.LOCATION_PRECISION_DIGITS), 
                                round(float(obj.location.z), BldRemoteMCPConfig.LOCATION_PRECISION_DIGITS)],
                    "visible": obj.visible_get(),
                }
                scene_info["objects"].append(obj_info)
            
            log_debug(f"Scene info collected: {len(scene_info['objects'])} objects")
            return scene_info
        except Exception as e:
            log_error(f"Error in get_scene_info: {str(e)}")
            traceback.print_exc()
            return {"error": str(e)}
    
    def get_object_info(self, name=None):
        """Get detailed information about a specific object."""
        if not name:
            raise ValueError("name parameter is required")
            
        obj = bpy.data.objects.get(name)
        if not obj:
            raise ValueError(f"Object not found: {name}")
        
        # Basic object info
        obj_info = {
            "name": obj.name,
            "type": obj.type,
            "location": [obj.location.x, obj.location.y, obj.location.z],
            "rotation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z],
            "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            "visible": obj.visible_get(),
            "dimensions": list(obj.dimensions),
            "materials": [],
        }
        
        # Add material slots
        for slot in obj.material_slots:
            if slot.material:
                obj_info["materials"].append(slot.material.name)
        
        # Add mesh data if applicable
        if obj.type == 'MESH' and obj.data:
            mesh = obj.data
            obj_info["mesh"] = {
                "vertices": len(mesh.vertices),
                "edges": len(mesh.edges),
                "polygons": len(mesh.polygons),
            }
        
        return obj_info
    
    def get_viewport_screenshot(self, max_size=BldRemoteMCPConfig.DEFAULT_VIEWPORT_MAX_SIZE, filepath=None, format="png", **kwargs):
        """Capture a screenshot of the current 3D viewport."""
        log_debug(f"Getting viewport screenshot: filepath={filepath}, max_size={max_size}")
        
        # Check if we're in background mode (no GUI)
        if bpy.app.background:
            log_warning("get_viewport_screenshot called in background mode - no viewport available")
            raise ValueError("Viewport screenshots are not available in background mode")
        
        try:
            if not filepath:
                # Generate unique temporary filename
                import uuid
                import tempfile
                temp_dir = tempfile.gettempdir()
                unique_filename = f"blender_screenshot_{uuid.uuid4().hex}.{format}"
                filepath = os.path.join(temp_dir, unique_filename)
                log_debug(f"Generated unique temporary filepath: {filepath}")
            
            # Find the active 3D viewport
            area = None
            for a in bpy.context.screen.areas:
                if a.type == 'VIEW_3D':
                    area = a
                    break
            
            if not area:
                raise ValueError("No 3D viewport found")
            
            # Take screenshot with proper context override
            with bpy.context.temp_override(area=area):
                bpy.ops.screen.screenshot_area(filepath=filepath)
            
            # Load and resize if needed
            img = bpy.data.images.load(filepath)
            width, height = img.size
            
            if max(width, height) > max_size:
                scale = max_size / max(width, height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                img.scale(new_width, new_height)
                
                # Set format and save
                img.file_format = format.upper()
                img.save()
                width, height = new_width, new_height
            
            # Cleanup Blender image data
            bpy.data.images.remove(img)
            
            return {
                "success": True,
                "width": width,
                "height": height,
                "filepath": filepath
            }
            
        except Exception as e:
            log_error(f"Error capturing viewport screenshot: {e}")
            raise

    def execute_code(self, code=None, code_is_base64=False, return_as_base64=False, **kwargs):
        """Execute arbitrary Blender Python code with output capture.
        
        Args:
            code: Python code to execute (may be base64-encoded if code_is_base64=True)
            code_is_base64: If True, decode the code from base64 before execution
            return_as_base64: If True, encode the result as base64 for safe transmission
            **kwargs: Additional parameters for backward compatibility
        """
        if not code:
            raise ValueError("No code provided")
        
        # Decode base64 code if requested
        actual_code = code
        if code_is_base64:
            try:
                actual_code = base64.b64decode(code.encode(BldRemoteMCPConfig.STRING_ENCODING_ASCII)).decode(BldRemoteMCPConfig.STRING_ENCODING_UTF8)
                log_debug(f"Decoded base64 code (original length: {len(code)}, decoded length: {len(actual_code)})")
            except Exception as e:
                raise ValueError(f"Failed to decode base64 code: {e}")
        
        log_debug(f"Executing code: {actual_code[:BldRemoteMCPConfig.CODE_PREVIEW_LENGTH]}{'...' if len(actual_code) > BldRemoteMCPConfig.CODE_PREVIEW_LENGTH else ''}")
        
        exec_result = self._execute_code_with_capture(actual_code)
        
        if exec_result.success:
            result_data = {
                "executed": True,
                "result": exec_result.output.get("stdout", ""),
                "output": exec_result.output,
                "duration": exec_result.duration,
            }
            
            # Encode result as base64 if requested
            if return_as_base64:
                try:
                    # Encode the main result as base64
                    original_result = result_data["result"]
                    if original_result:
                        encoded_result = base64.b64encode(original_result.encode(BldRemoteMCPConfig.STRING_ENCODING_UTF8)).decode(BldRemoteMCPConfig.STRING_ENCODING_ASCII)
                        result_data["result"] = encoded_result
                        result_data["result_is_base64"] = True
                        log_debug(f"Encoded result as base64 (original length: {len(original_result)}, encoded length: {len(encoded_result)})")
                    else:
                        result_data["result_is_base64"] = False
                except Exception as e:
                    log_error(f"Failed to encode result as base64: {e}")
                    result_data["result_encode_error"] = str(e)
                    result_data["result_is_base64"] = False
            
            return result_data
        else:
            raise Exception(f"Code execution error: {exec_result.error}")

    def _execute_code_with_capture(self, code):
        """Execute code with comprehensive output capture."""
        start_time = time.time()
        
        try:
            # Create execution context
            exec_globals = {
                '__builtins__': __builtins__,
                'bpy': bpy,
            }
            
            # Capture output during execution
            with OutputCapture() as capture:
                exec(code, exec_globals, exec_globals)
            
            duration = time.time() - start_time
            captured_output = capture.get_output()
            
            # Try to extract result from globals
            result = exec_globals.get('_result', None)
            
            return ExecutionResult(
                success=True,
                output=captured_output,
                result=result,
                duration=duration,
                error=None,
                traceback=None
            )
            
        except Exception as e:
            duration = time.time() - start_time
            error_traceback = traceback.format_exc()
            
            return ExecutionResult(
                success=False,
                output={"stdout": "", "stderr": ""},
                result=None,
                duration=duration,
                error=str(e),
                traceback=error_traceback
            )

    def get_polyhaven_status(self):
        """Asset provider not supported - return disabled status."""
        return {"enabled": False, "reason": "Asset providers not supported"}

    def put_persist_data(self, key=None, data=None, **kwargs):
        """Store persistent data."""
        if key is None:
            raise ValueError("Missing 'key' parameter")
        if data is None:
            raise ValueError("Missing 'data' parameter")
        
        persist.put_data(key, data)
        return f"Data stored under key '{key}'"

    def get_persist_data(self, key=None, default=None, **kwargs):
        """Retrieve persistent data."""
        if key is None:
            raise ValueError("Missing 'key' parameter")
        
        data = persist.get_data(key, default)
        return {"data": data, "found": key in persist.get_keys()}

    def remove_persist_data(self, key=None, **kwargs):
        """Remove persistent data."""
        if key is None:
            raise ValueError("Missing 'key' parameter")
        
        removed = persist.remove_data(key)
        return {"removed": removed}


# Global server instance
_server_instance = None


def _get_global_command_queue():
    """Get the global command queue for background mode."""
    global _server_instance
    if _server_instance and _server_instance.background_mode:
        return _server_instance.command_queue
    return None


def step():
    """Process pending commands - called manually in background mode."""
    global _server_instance
    log_debug("Global step() function called")
    
    if _server_instance:
        _server_instance.step()
    else:
        log_debug("step() called but no server instance available")


def _is_background_mode():
    """Check if Blender is running in background mode."""
    return bpy.app.background


def _signal_handler(signum, frame):
    """Handle shutdown signals in background mode."""
    log_info(f"Received signal {signum}, shutting down server...")
    cleanup_server()
    if _is_background_mode():
        bpy.ops.wm.quit_blender()


def _cleanup_on_exit():
    """Cleanup function for exit handler."""
    try:
        if _server_instance:
            log_info("BLD Remote: Cleaning up on process exit...")
            cleanup_server()
    except Exception as e:
        log_error(f"BLD Remote: Error during cleanup: {e}")


def cleanup_server():
    """Stop the TCP server and clean up associated resources."""
    global _server_instance, _tcp_server, _server_socket, _server_thread, _server_running, _server_port
    
    log_debug("cleanup_server() called")
    
    if _server_instance:
        log_debug("Stopping server instance...")
        try:
            _server_instance.stop()
            log_debug("Server instance stopped successfully")
        except Exception as e:
            log_error(f"Error stopping server instance: {e}")
        _server_instance = None
    
    # Reset global state
    _tcp_server = None
    _server_socket = None
    _server_thread = None
    _server_running = False
    old_port = _server_port
    _server_port = BldRemoteMCPConfig.INITIAL_SERVER_PORT
    
    # Update scene property
    try:
        if hasattr(bpy, 'data') and hasattr(bpy.data, 'scenes') and bpy.data.scenes:
            bpy.data.scenes[BldRemoteMCPConfig.DEFAULT_SCENE_INDEX].bld_remote_server_running = False
            log_debug("Scene property updated successfully")
    except (AttributeError, TypeError) as e:
        log_debug(f"Cannot access scenes to update property: {e}")
    except Exception as e:
        log_error(f"Unexpected error updating scene property: {e}")
        
    log_debug("Server cleanup complete")


def start_server_from_script():
    """Start the TCP server from an external script."""
    global _server_instance, _tcp_server, _server_running, _server_port
    
    log_debug("start_server_from_script() called")
    
    # Get port configuration
    port = get_mcp_port()
    log_info(f"Starting server on port {port}")
    
    # Create and start server instance
    try:
        _server_instance = BldRemoteMCPServer(port=port)
        success = _server_instance.start()
        
        if success:
            _tcp_server = _server_instance  # For compatibility
            _server_running = True
            _server_port = port
            
            # Update scene property
            try:
                if hasattr(bpy, 'data') and hasattr(bpy.data, 'scenes') and bpy.data.scenes:
                    bpy.data.scenes[BldRemoteMCPConfig.DEFAULT_SCENE_INDEX].bld_remote_server_running = True
                    log_debug("Scene property updated to True")
            except Exception as e:
                log_debug(f"Cannot update scene property: {e}")
            
            log_info("[OK] Server started successfully")
        else:
            log_error("[FAIL] Server failed to start - port may already be in use")
            _server_instance = None
            raise RuntimeError(f"Failed to start server on port {port} - port may already be in use")
            
    except Exception as e:
        log_error(f"[FAIL] Error starting server: {e}")
        _server_instance = None
        raise


# =============================================================================
# Python API Module (bld_remote)
# =============================================================================

def get_status():
    """Return service status dictionary."""
    global _server_instance, _server_port
    
    status = {
        "running": _server_instance is not None and _server_instance.running,
        "port": _server_port,
        "address": f"{BldRemoteMCPConfig.DEFAULT_HOST}:{_server_port}",
        "server_object": _server_instance is not None
    }
    
    log_info(f"Status result: {status}")
    return status


def start_mcp_service():
    """Start MCP service, raise exception on failure."""
    global _server_instance
    
    log_debug("start_mcp_service() called")
    
    if _server_instance is not None and _server_instance.running:
        log_debug("[WARN] Server already running, nothing to do")
        return
    
    log_debug("Server not running, attempting to start...")
    try:
        start_server_from_script()
        log_debug("[OK] Server start initiated successfully")
        
    except Exception as e:
        error_msg = f"Failed to start server: {e}"
        log_error(f"ERROR in start_mcp_service(): {error_msg}")
        traceback.print_exc()
        raise RuntimeError(error_msg)


def stop_mcp_service():
    """Stop MCP service, disconnects all clients forcefully."""
    cleanup_server()


def get_startup_options():
    """Return information about environment variables."""
    from .config import get_startup_options
    return get_startup_options()


def is_mcp_service_up():
    """Return true/false, check if MCP service is up and running."""
    return _server_instance is not None and _server_instance.running


def set_mcp_service_port(port_number):
    """Set the port number of MCP service, only callable when service is stopped."""
    if _server_instance is not None and _server_instance.running:
        raise RuntimeError("Cannot change port while server is running. Stop service first.")
    
    if not isinstance(port_number, int) or port_number < BldRemoteMCPConfig.MIN_PORT_NUMBER or port_number > BldRemoteMCPConfig.MAX_PORT_NUMBER:
        raise ValueError(f"Port number must be an integer between {BldRemoteMCPConfig.MIN_PORT_NUMBER} and {BldRemoteMCPConfig.MAX_PORT_NUMBER}")
    
    # Set environment variable for next start
    os.environ['BLD_REMOTE_MCP_PORT'] = str(port_number)
    log_info(f"MCP service port set to {port_number}")


def get_mcp_service_port():
    """Return the current configured port."""
    return get_mcp_port()


# =============================================================================
# Blender Addon Registration  
# =============================================================================

def register():
    """Register the addon's properties and classes with Blender."""
    log_debug("=== BLD REMOTE MCP ADDON REGISTRATION STARTING ===")
    log_info(f"BLD Remote MCP {BldRemoteMCPConfig.VERSION_STRING} Loading")
    log_debug("register() function called")
    
    # Check Blender environment
    log_debug(f"Blender version: {bpy.app.version}")
    background_mode = _is_background_mode()
    log_info(f"Blender mode: {'Background' if background_mode else 'GUI'}")
    log_debug(f"Execution strategy: {'Queue-based (background)' if background_mode else 'Timer-based (GUI)'}")
    
    # Add scene properties
    log_debug("Adding scene properties...")
    try:
        bpy.types.Scene.bld_remote_server_running = BoolProperty(
            name="BLD Remote Server Running",
            description="Indicates if the BLD Remote server is active",
            default=False
        )
        log_debug("[OK] Scene property 'bld_remote_server_running' added")
    except Exception as e:
        log_error(f"ERROR: Failed to add scene property: {e}")
        raise
    
    # Log startup configuration  
    log_debug("Loading and logging startup configuration...")
    try:
        from .config import log_startup_config
        log_startup_config()
        log_debug("[OK] Startup configuration logged")
    except Exception as e:
        log_error(f"ERROR: Failed to log startup config: {e}")
    
    # Install signal handlers for background mode
    background_mode = _is_background_mode()
    if background_mode:
        log_debug("Background mode detected, installing signal handlers...")
        try:
            # SIGINT is supported on all platforms
            signal.signal(signal.SIGINT, _signal_handler)
            signals_installed = ["SIGINT"]
            
            # SIGTERM is not available on Windows
            try:
                signal.signal(signal.SIGTERM, _signal_handler)
                signals_installed.append("SIGTERM")
            except (AttributeError, ValueError):
                # SIGTERM not available on this platform (e.g., Windows)
                log_debug("SIGTERM not available on this platform, using SIGINT only")
            
            log_debug(f"[OK] Signal handlers ({', '.join(signals_installed)}) installed")
            
            atexit.register(_cleanup_on_exit)
            log_debug("[OK] Exit handler registered")
        except Exception as e:
            log_error(f"ERROR: Failed to setup background mode handlers: {e}")
    else:
        log_debug("GUI mode detected, skipping signal handler installation")
    
    # Auto-start if configured
    log_debug("Checking auto-start configuration...")
    try:
        auto_start = should_auto_start()
        
        if auto_start:
            log_info("Auto-start enabled, attempting to start server")
            try:
                start_mcp_service()
                # Log the execution mode for the started server
                if _server_instance:
                    mode = 'background (queue-based)' if _server_instance.background_mode else 'GUI (timer-based)'
                    log_debug(f"[OK] Server started in {mode} mode")
                log_debug("[OK] Auto-start server initialization completed")
            except Exception as e:
                log_error(f"[FAIL] Auto-start failed: {e}")
                traceback.print_exc()
                
                # In background mode, if auto-start was requested but failed, exit Blender
                if background_mode:
                    log_error("[CRITICAL] Background mode auto-start failed - forcing Blender exit")
                    raise SystemExit(f"Background mode auto-start failed: {e}")
                else:
                    log_warning("[WARN] Auto-start failed in GUI mode, but continuing...")
        else:
            log_debug("Auto-start disabled, server will not start automatically")
    except SystemExit:
        # Re-raise SystemExit to allow Blender to quit
        raise
    except Exception as e:
        log_error(f"ERROR: Failed to check auto-start config: {e}")
    
    log_debug("[OK] BLD Remote MCP addon registered successfully")
    log_debug("=== BLD REMOTE MCP ADDON REGISTRATION COMPLETED ===")


def unregister():
    """Unregister the addon and clean up all resources."""
    log_debug("=== BLD REMOTE MCP ADDON UNREGISTRATION STARTING ===")
    log_debug("unregister() function called")
    
    # Stop server
    log_debug("Stopping server and cleaning up resources...")
    try:
        cleanup_server()
        log_debug("[OK] Server cleanup completed")
    except Exception as e:
        log_error(f"ERROR: Failed to cleanup server: {e}")
    
    # Clean up scene properties
    log_debug("Removing scene properties...")
    try:
        del bpy.types.Scene.bld_remote_server_running
        log_debug("[OK] Scene property 'bld_remote_server_running' removed")
    except (AttributeError, RuntimeError) as e:
        log_debug(f"Scene property already removed or not accessible: {e}")
    except Exception as e:
        log_error(f"ERROR: Unexpected error removing scene property: {e}")
    
    log_debug("[OK] BLD Remote MCP addon unregistered successfully")
    log_debug("=== BLD REMOTE MCP ADDON UNREGISTRATION COMPLETED ===")


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
    
    # Background mode step processing
    step = staticmethod(step)
    
    # Persistence functionality
    persist = persist
    
    @staticmethod
    def is_background_mode():
        """Check if running in background mode."""
        return bpy.app.background
    
    @staticmethod
    def get_command_queue_size():
        """Get the current command queue size (background mode only)."""
        queue_obj = _get_global_command_queue()
        return queue_obj.qsize() if queue_obj else BldRemoteMCPConfig.QUEUE_EMPTY_SIZE

# Register the API in sys.modules so it can be imported as 'import bld_remote'
sys.modules['bld_remote'] = BldRemoteAPI()
log_debug("BldRemoteAPI registered in sys.modules with step() function")