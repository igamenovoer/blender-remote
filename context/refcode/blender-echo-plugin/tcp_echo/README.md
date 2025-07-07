# TCP Echo Blender Plugin

## Overview

This Blender addon runs a simple TCP server that can receive commands to be executed within Blender. It is specifically designed to be robust and stable when running in Blender's background mode (`--background`), making it ideal for automation and remote control scenarios.

The server listens on a specified port, accepts JSON-based commands, executes them, and returns a JSON response.

## How It Works

The core of the addon is a combination of an `asyncio` TCP server and a careful integration with Blender's Python environment.

1.  **`__init__.py`**: This is the main addon file.
    *   It defines the `TCPEchoProtocol`, which handles incoming connections and data.
    *   It includes the `start_server_from_script()` function, which is the designated entry point for starting the server from an external script.
    *   It manages a `tcp_echo_server_running` property on the scene to track the server's state.
    *   The `register()` and `unregister()` functions handle the setup and teardown of the addon's properties.

2.  **`async_loop.py`**: This helper module contains the logic for driving the `asyncio` event loop within Blender.
    *   The `kick_async_loop()` function is the key component. It performs a single iteration of the event loop, allowing `asyncio` tasks (like the TCP server) to be processed without blocking Blender. This is crucial for background mode operation where there is no continuous UI-driven event loop.

3.  **Background Mode Operation**:
    *   The addon is designed to be controlled by an external Python script (like the provided `install_and_run_tcp_echo.py`).
    *   This external script is responsible for:
        1.  Installing and enabling the addon.
        2.  Calling `start_server_from_script()` to initiate the server.
        3.  Running a `while` loop that repeatedly calls `async_loop.kick_async_loop()`. This keeps the Blender process alive and ensures the `asyncio` server can process requests.
    *   This architecture avoids the common pitfalls of using `bpy.context` in background mode and ensures a stable, long-running server process.

## Usage

To use this plugin, you need an external Python script to launch Blender and manage the server lifecycle.

### 1. Start the Server

Use a script to launch Blender in the background and run the server. The `install_and_run_tcp_echo.py` script in the parent directory is a complete example.

**Command:**
```powershell
$env:BLENDER_HTTP_ECHO_PORT='23333'; & "path/to/blender.exe" --background --python install_and_run_tcp_echo.py
```

*   `BLENDER_HTTP_ECHO_PORT`: (Optional) Sets the port for the server. Defaults to `23333`.

### 2. Send Commands

Commands are sent as JSON strings over a TCP connection. The `test_client.py` script provides a clear example.

**JSON Command Format:**
```json
{
  "message": "Your message here",
  "code": "bpy.ops.mesh.primitive_cube_add()"
}
```

*   `message`: A simple string that the server will print to the console.
*   `code`: A string of Python code to be executed within Blender.

### 3. Stop the Server

To shut down the server and the Blender process gracefully, send a command containing the `quit_blender` string.

**JSON Quit Command:**
```json
{
  "code": "quit_blender"
}
```

The addon will detect this, raise a `SystemExit` exception, and the runner script will catch it, allowing for a clean shutdown.

## Example Client Interaction

```python
import socket
import json

def send_request(port, request_data):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('127.0.0.1', port))
        s.sendall(json.dumps(request_data).encode('utf-8'))
        response = s.recv(1024)
        print(f"Received: {response.decode('utf-8')}")

# Create a cube
send_request(23333, {"code": "bpy.ops.mesh.primitive_cube_add()"})

# Shut down the server
send_request(23333, {"code": "quit_blender"})
