"""A Blender addon that runs a background TCP server to execute commands.

This addon is designed to be run in Blender's background mode. It starts an
`asyncio` TCP server that listens for JSON commands, executes them within
Blender's context, and returns a response. It is controlled by an external
Python script that manages the Blender process and the `asyncio` event loop.

"""
import bpy
import os
import json
import asyncio
import traceback
from bpy.props import BoolProperty

from . import async_loop

bl_info = {
    "name": "TCP Echo Server (Background-Safe)",
    "author": "Cline",
    "version": (2, 0, 0),
    "blender": (3, 0, 0),
    "location": "N/A",
    "description": "A simple asyncio TCP server that echoes messages, designed for background mode.",
    "category": "Development",
}

# Global variables to hold the server state
tcp_server = None
server_task = None
server_port = 0

def cleanup_server():
    """Stop the TCP server and clean up associated resources.

    This function is idempotent and can be called multiple times without
    side effects. It closes the server, cancels the asyncio task, and resets
    the global state variables.

    """
    global tcp_server, server_task, server_port
    if not tcp_server and not server_task:
        return

    print("TCP Echo: Cleaning up server...")
    if tcp_server:
        tcp_server.close()
        tcp_server = None
    if server_task:
        server_task.cancel()
        server_task = None
    server_port = 0
    
    if bpy.data.scenes:
        bpy.data.scenes[0].tcp_echo_server_running = False
    print("TCP Echo: Server cleanup complete.")

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
        "message": "Task received.",
        "source": f"tcp://127.0.0.1:{server_port}"
    }
    if "message" in data:
        print(f"Message received: {data['message']}")
        response["message"] = f"Printed message: {data['message']}"
    if "code" in data:
        code_to_run = data['code']
        print(f"Executing code: {code_to_run}")
        try:
            # Special handling for the quit command
            if "quit_blender" in code_to_run:
                print("Shutdown command received. Raising SystemExit.")
                # This will be caught by the main script's finally block
                raise SystemExit("Shutdown requested by client.")
            else:
                # Run other code in a deferred context
                def code_runner():
                    exec(code_to_run, {'bpy': bpy})
                bpy.app.timers.register(code_runner, first_interval=0.01)
                response["message"] = "Code execution scheduled."
        except Exception as e:
            print(f"Error executing code: {e}")
            traceback.print_exc()
            response["response"] = "FAILED"
            response["message"] = f"Error executing code: {str(e)}"
    return response

class TCPEchoProtocol(asyncio.Protocol):
    """The asyncio Protocol for handling client connections."""

    def connection_made(self, transport):
        """Called when a connection is made."""
        self.transport = transport
        peername = transport.get_extra_info('peername')
        print(f"Connection from {peername}")

    def data_received(self, data):
        """Called when data is received from the client."""
        try:
            message = json.loads(data.decode())
            response = process_message(message)
            self.transport.write(json.dumps(response).encode())
        except Exception as e:
            print(f"Error processing message: {e}")
            traceback.print_exc()
        finally:
            self.transport.close()

    def connection_lost(self, exc):
        """Called when the connection is lost or closed."""
        print("Client connection closed")

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
        tcp_server = await loop.create_server(TCPEchoProtocol, '127.0.0.1', port)
        server_task = asyncio.ensure_future(tcp_server.serve_forever())
        print(f"TCP Echo server started on port {port}")
        if scene_to_update:
            scene_to_update.tcp_echo_server_running = True
    except Exception as e:
        print(f"Failed to start server: {e}")
        cleanup_server()

def start_server_from_script():
    """Start the TCP server from an external script.

    This is the main entry point for starting the server. It reads the port
    from an environment variable, gets a reference to a scene, and schedules
    the `start_server_task` to run on the asyncio event loop.

    """
    port = int(os.environ.get('BLENDER_HTTP_ECHO_PORT', 23333))
    # Use bpy.data.scenes[0] as it's reliable in background mode
    scene = bpy.data.scenes[0] if bpy.data.scenes else None
    
    asyncio.ensure_future(start_server_task(port, scene))
    
    # Ensure the async loop machinery is ready
    try:
        async_loop.register()
    except ValueError:
        # Already registered, which is fine.
        pass

# No UI classes are needed for a background-only addon

def register():
    """Register the addon's properties and classes with Blender."""
    bpy.types.Scene.tcp_echo_server_running = BoolProperty(
        name="Server Running",
        description="Indicates if the TCP Echo server is active.",
        default=False
    )

def unregister():
    """Unregister the addon and clean up all resources."""
    cleanup_server()
    try:
        del bpy.types.Scene.tcp_echo_server_running
    except (AttributeError, RuntimeError):
        pass
    try:
        async_loop.unregister()
    except (RuntimeError, ValueError):
        pass
