import bpy
import mathutils
import json
import threading
import socket
import time
import tempfile
import traceback
import os
import signal
import atexit
import asyncio
import io
from contextlib import redirect_stdout


class BlenderAutoMCPServer:
    def __init__(self, host='localhost', port=9876):
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.server_thread = None
        self.background_mode = self._is_background_mode()
        self.shutdown_event = None  # For asyncio background mode
        
        # Install signal handlers and exit handlers for background mode
        if self.background_mode:
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
            atexit.register(self._cleanup_on_exit)
    
    def __del__(self):
        """Final cleanup when object is being destroyed"""
        try:
            if hasattr(self, 'running') and self.running:
                self.stop()
        except:
            pass  # Ignore errors during destruction
    
    def _is_background_mode(self):
        """Check if Blender is running in background mode"""
        return bpy.app.background
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals in background mode"""
        print(f"Received signal {signum}, shutting down server...")
        self.stop()
        if self.background_mode:
            bpy.ops.wm.quit_blender()
    
    def _cleanup_on_exit(self):
        """Cleanup function for exit handler"""
        try:
            if self.running:
                print("Auto MCP: Cleaning up on process exit...")
                self.stop()
        except Exception as e:
            print(f"Auto MCP: Error during cleanup: {e}")
    
    def start(self):
        if self.running:
            print("Server is already running")
            return True
            
        self.running = True
        
        try:
            # Create socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Set socket options for address reuse
            if os.name == 'nt':  # For Windows
                # On Windows, using SO_EXCLUSIVEADDRUSE is generally better to prevent
                # other sockets from binding to the same address and port.
                # Setting both SO_REUSEADDR and SO_EXCLUSIVEADDRUSE is an error.
                if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
                    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                else:
                    # Fallback for older Windows versions that might not have SO_EXCLUSIVEADDRUSE
                    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            else:  # For other OS (Linux, macOS)
                # On Unix-like systems, SO_REUSEADDR is standard.
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)  # Increased from 1 to 5 for multiple connections
            
            # Start server thread
            self.server_thread = threading.Thread(target=self._server_loop)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            print(f"Blender Auto MCP server started on {self.host}:{self.port}")
            
            # In background mode, keep the process alive
            if self.background_mode:
                self._keep_alive_in_background()
            
            return True
                
        except OSError as e:
            error_code = getattr(e, 'winerror', None) if hasattr(e, 'winerror') else e.errno
            if error_code == 10013:  # Windows permission error
                print(f"Failed to start server on port {self.port}: Permission denied. Port may be restricted or in use by another service.")
                print("Try using a different port (e.g., 9876) or run Blender as administrator.")
            elif error_code == 10048 or 'Address already in use' in str(e):  # Port already in use
                print(f"Failed to start server on port {self.port}: Port is already in use.")
                print("Another application or Blender instance may be using this port.")
                print("Try stopping other instances or use a different port.")
            else:
                print(f"Failed to start server on port {self.port}: {str(e)}")
            self.stop()
            return False
        except Exception as e:
            print(f"Failed to start server: {str(e)}")
            self.stop()
            return False
    
    def _keep_alive_in_background(self):
        """Initialize asyncio event for background mode keep-alive"""
        print("Background mode detected - initializing shutdown event for asyncio")
        
        # Create asyncio event for shutdown signaling
        self.shutdown_event = asyncio.Event()
        
        print("Shutdown event initialized for background mode")
    
    def stop(self):
        print("Stopping Blender Auto MCP server...")
        self.running = False
        
        # Signal asyncio shutdown event if in background mode
        if self.background_mode and self.shutdown_event:
            print("Signaling asyncio shutdown event")
            try:
                # Set the shutdown event to signal the background keep-alive loop to exit
                if not self.shutdown_event.is_set():
                    self.shutdown_event.set()
                    print("Shutdown event set successfully")
            except Exception as e:
                print(f"Error signaling shutdown event: {e}")
        
        # Close socket first to stop accepting new connections
        if self.socket:
            try:
                # Shutdown the socket for both reading and writing
                self.socket.shutdown(socket.SHUT_RDWR)
            except:
                pass
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        # Wait for server thread to finish
        if self.server_thread:
            try:
                if self.server_thread.is_alive():
                    self.server_thread.join(timeout=3.0)
                    if self.server_thread.is_alive():
                        print("Warning: Server thread did not stop cleanly")
            except:
                pass
            self.server_thread = None
        
        print("Blender Auto MCP server stopped")
    
    def _server_loop(self):
        """Main server loop in a separate thread"""
        print("Server thread started")
        self.socket.settimeout(1.0)  # Timeout to allow for stopping
        
        while self.running:
            try:
                # Accept new connection
                try:
                    client, address = self.socket.accept()
                    print(f"Connected to client: {address}")
                    
                    # Handle client in a separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client,)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                except socket.timeout:
                    # Just check running condition
                    continue
                except Exception as e:
                    if self.running:  # Only log if we're supposed to be running
                        print(f"Error accepting connection: {str(e)}")
                    time.sleep(0.5)
            except Exception as e:
                if self.running:  # Only log if we're supposed to be running
                    print(f"Error in server loop: {str(e)}")
                if not self.running:
                    break
                time.sleep(0.5)
        
        print("Server thread stopped")
    
    def _handle_client(self, client):
        """Handle connected client"""
        print("Client handler started")
        client.settimeout(None)  # No timeout
        buffer = b''
        
        try:
            while self.running:
                # Receive data
                try:
                    data = client.recv(8192)
                    if not data:
                        print("Client disconnected")
                        break
                    
                    buffer += data
                    try:
                        # Try to parse command
                        command = json.loads(buffer.decode('utf-8'))
                        buffer = b''
                        
                        # Execute command in Blender's main thread
                        def execute_wrapper():
                            try:
                                response = self.execute_command(command)
                                response_json = json.dumps(response)
                                try:
                                    client.sendall(response_json.encode('utf-8'))
                                except:
                                    print("Failed to send response - client disconnected")
                            except Exception as e:
                                print(f"Error executing command: {str(e)}")
                                traceback.print_exc()
                                try:
                                    error_response = {
                                        "status": "error",
                                        "message": str(e)
                                    }
                                    client.sendall(json.dumps(error_response).encode('utf-8'))
                                except:
                                    pass
                            return None
                        
                        # Schedule execution in main thread
                        bpy.app.timers.register(execute_wrapper, first_interval=0.0)
                    except json.JSONDecodeError:
                        # Incomplete data, wait for more
                        pass
                except Exception as e:
                    print(f"Error receiving data: {str(e)}")
                    break
        except Exception as e:
            print(f"Error in client handler: {str(e)}")
        finally:
            try:
                client.close()
            except:
                pass
            print("Client handler stopped")

    def execute_command(self, command):
        """Execute a command in the main Blender thread"""
        try:            
            return self._execute_command_internal(command)
                
        except Exception as e:
            print(f"Error executing command: {str(e)}")
            traceback.print_exc()
            return {"status": "error", "message": str(e)}

    def _execute_command_internal(self, command):
        """Internal command execution with proper context"""
        from .asset_providers import get_polyhaven_handlers, get_hyper3d_handlers, get_sketchfab_handlers
        
        cmd_type = command.get("type")
        params = command.get("params", {})

        # Get configuration from scene properties
        scene = bpy.context.scene
        
        # Base handlers that are always available
        handlers = {
            "get_scene_info": self.get_scene_info,
            "get_object_info": self.get_object_info,
            "get_viewport_screenshot": self.get_viewport_screenshot,
            "execute_code": self.execute_code,
            "server_shutdown": self.server_shutdown,
        }
        
        # Add provider-specific handlers based on scene configuration
        if hasattr(scene, 'blender_auto_mcp_use_polyhaven') and scene.blender_auto_mcp_use_polyhaven:
            handlers.update(get_polyhaven_handlers(self))
        
        if hasattr(scene, 'blender_auto_mcp_use_hyper3d') and scene.blender_auto_mcp_use_hyper3d:
            handlers.update(get_hyper3d_handlers(self))
            
        if hasattr(scene, 'blender_auto_mcp_use_sketchfab') and scene.blender_auto_mcp_use_sketchfab:
            handlers.update(get_sketchfab_handlers(self))

        handler = handlers.get(cmd_type)
        if handler:
            try:
                print(f"Executing handler for {cmd_type}")
                result = handler(**params)
                print(f"Handler execution complete")
                return {"status": "success", "result": result}
            except Exception as e:
                print(f"Error in handler: {str(e)}")
                traceback.print_exc()
                return {"status": "error", "message": str(e)}
        else:
            return {"status": "error", "message": f"Unknown command type: {cmd_type}"}

    def server_shutdown(self):
        """Shutdown command for graceful server termination"""
        def delayed_shutdown():
            self.stop()
            if self.background_mode:
                bpy.ops.wm.quit_blender()
            return None
        
        # Schedule shutdown after a brief delay
        bpy.app.timers.register(delayed_shutdown, first_interval=1.0)
        return {"message": "Server shutdown initiated"}
    
    def get_scene_info(self):
        """Get information about the current Blender scene"""
        try:
            print("Getting scene info...")
            # Simplify the scene info to reduce data size
            scene_info = {
                "name": bpy.context.scene.name,
                "object_count": len(bpy.context.scene.objects),
                "objects": [],
                "materials_count": len(bpy.data.materials),
            }
            
            # Collect minimal object information (limit to first 10 objects)
            for i, obj in enumerate(bpy.context.scene.objects):
                if i >= 10:  # Reduced from 20 to 10
                    break
                    
                obj_info = {
                    "name": obj.name,
                    "type": obj.type,
                    # Only include basic location data
                    "location": [round(float(obj.location.x), 2), 
                                round(float(obj.location.y), 2), 
                                round(float(obj.location.z), 2)],
                }
                scene_info["objects"].append(obj_info)
            
            print(f"Scene info collected: {len(scene_info['objects'])} objects")
            return scene_info
        except Exception as e:
            print(f"Error in get_scene_info: {str(e)}")
            traceback.print_exc()
            return {"error": str(e)}
    
    @staticmethod
    def _get_aabb(obj):
        """ Returns the world-space axis-aligned bounding box (AABB) of an object. """
        if obj.type != 'MESH':
            raise TypeError("Object must be a mesh")

        # Get the bounding box corners in local space
        local_bbox_corners = [mathutils.Vector(corner) for corner in obj.bound_box]

        # Convert to world coordinates
        world_bbox_corners = [obj.matrix_world @ corner for corner in local_bbox_corners]

        # Compute axis-aligned min/max coordinates
        min_corner = mathutils.Vector(map(min, zip(*world_bbox_corners)))
        max_corner = mathutils.Vector(map(max, zip(*world_bbox_corners)))

        return [
            [*min_corner], [*max_corner]
        ]

    def get_object_info(self, name):
        """Get detailed information about a specific object"""
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
            "materials": [],
        }

        if obj.type == "MESH":
            bounding_box = self._get_aabb(obj)
            obj_info["world_bounding_box"] = bounding_box
        
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
    
    def get_viewport_screenshot(self, max_size=800, filepath=None, format="png"):
        """
        Capture a screenshot of the current 3D viewport and save it to the specified path.
        
        Parameters:
        - max_size: Maximum size in pixels for the largest dimension of the image
        - filepath: Path where to save the screenshot file
        - format: Image format (png, jpg, etc.)
        
        Returns success/error status
        """
        try:
            if not filepath:
                return {"error": "No filepath provided"}
            
            # Find the active 3D viewport
            area = None
            for a in bpy.context.screen.areas:
                if a.type == 'VIEW_3D':
                    area = a
                    break
            
            if not area:
                return {"error": "No 3D viewport found"}
            
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
            return {"error": str(e)}
    
    def execute_code(self, code):
        """Execute arbitrary Blender Python code"""
        # This is powerful but potentially dangerous - use with caution
        try:
            # Create a local namespace for execution
            namespace = {"bpy": bpy}

            # Capture stdout during execution, and return it as result
            capture_buffer = io.StringIO()
            with redirect_stdout(capture_buffer):
                exec(code, namespace)
            
            captured_output = capture_buffer.getvalue()
            return {"executed": True, "result": captured_output}
        except Exception as e:
            raise Exception(f"Code execution error: {str(e)}")