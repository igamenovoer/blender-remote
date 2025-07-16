# Blender Addon API Reference

The `BLD_Remote_MCP` addon runs a TCP server inside Blender, allowing external applications to send commands and execute Python code. It also provides a Python module, `bld_remote`, for direct use in Blender scripts.

**File:** `src/blender_remote/addon/bld_remote_mcp/__init__.py`

## `bld_remote` Python Module

When the addon is enabled, it registers a module named `bld_remote` that can be imported directly in Blender's Python environment. This is the primary way to control the MCP service from other scripts within Blender.

```python
import bld_remote

# Check if the server is running
status = bld_remote.get_status()
print(f"Server running: {status['running']} on port {status['port']}")

# Start the service if it's not running
if not status['running']:
    bld_remote.start_mcp_service()
```

### Module Functions

#### `get_status()`
Returns a dictionary with the current status of the MCP service.

- **Returns (dict):** A dictionary containing `running` (bool), `port` (int), and other status info.

#### `start_mcp_service()`
Starts the TCP server. If the server is already running, this function does nothing. It will raise a `RuntimeError` if it fails to start (e.g., if the port is already in use).

#### `stop_mcp_service()`
Stops the TCP server and disconnects all clients.

#### `is_mcp_service_up()`
A quick check to see if the service is running.

- **Returns (bool):** `True` if the server is active, `False` otherwise.

#### `get_mcp_service_port()`
Gets the port number the server is configured to run on.

- **Returns (int):** The port number.

#### `set_mcp_service_port(port_number)`
Sets the port for the MCP service. This can only be called when the service is stopped.

- **`port_number` (int):** The new port to use.

#### `step()`
When running in **background mode**, this function must be called repeatedly in your script's main loop. It processes all pending commands from the queue. In GUI mode, this function has no effect as commands are processed automatically by a timer.

**Example for background mode:**
```python
# From tests/mcp-server/test_background_screenshot.py
import bld_remote
import time
import sys

# Start the service
bld_remote.start_mcp_service()
print("Service started, waiting for connections...")

# Keep the script running
while True:
    try:
        bld_remote.step()  # Process pending commands
        time.sleep(0.01)   # Small delay to prevent CPU spinning
    except KeyboardInterrupt:
        bld_remote.stop_mcp_service()
        sys.exit(0)
```

#### `is_background_mode()`
Checks if Blender is running in headless (background) mode.

- **Returns (bool):** `True` if in background mode.

#### `get_startup_options()`
Gets the startup configuration options for the MCP service.

- **Returns (dict):** A dictionary containing startup options including port, host, and auto-start settings.

#### `get_command_queue_size()`
Gets the current size of the command queue (background mode only).

- **Returns (int):** The number of commands in the queue, or -1 if the queue is not available.

#### `persist`
The `bld_remote.persist` object provides a simple key-value store for persisting data across different commands or sessions.

- **`bld_remote.persist.put_data(key, data)`:** Stores a value.
- **`bld_remote.persist.get_data(key, default=None)`:** Retrieves a value.
- **`bld_remote.persist.remove_data(key)`:** Deletes a value.
- **`bld_remote.persist.get_keys()`:** Returns a list of all stored keys.

**Example:**
```python
import bld_remote

# Store some data
bld_remote.persist.put_data("my_key", {"value": 42})

# Retrieve data
data = bld_remote.persist.get_data("my_key")
print(f"Retrieved: {data}")

# List all keys
keys = bld_remote.persist.get_keys()
print(f"All keys: {keys}")
```

## Server Commands

The TCP server listens for JSON commands. These are the commands that the `BlenderMCPClient` sends.

### `get_scene_info`
Retrieves a summary of the current scene.

- **Params:** None
- **Returns:** A dictionary with scene statistics, including object count and a list of the first 10 objects.

### `get_object_info`
Gets detailed information about a specific object.

- **Params:** `{"name": "ObjectName"}`
- **Returns:** A dictionary with the object's properties (location, rotation, materials, etc.).

### `execute_code`
Executes a string of Python code in Blender's global context.

- **Params:**
    - `code` (str): The code to run.
    - `code_is_base64` (bool): Set to `True` if the code is base64 encoded.
    - `return_as_base64` (bool): Set to `True` to receive the result as a base64 encoded string.
- **Returns:** The result of the execution, typically the standard output.

### `get_viewport_screenshot`
Captures a screenshot of the 3D viewport. This command only works when Blender is running in GUI mode.

- **Params:**
    - `max_size` (int): The maximum dimension for the image.
    - `filepath` (str): A path to save the file to. If not provided, a temporary file is created.
    - `format` (str): Image format (`"png"` or `"jpg"`).
- **Returns:** A dictionary with the `width`, `height`, and `filepath` of the saved image.

### `server_shutdown`
Gracefully shuts down the MCP server.

- **Params:** None
- **Returns:** A success message confirming shutdown.

### `get_polyhaven_status`
Gets the status of the Polyhaven addon integration.

- **Params:** None  
- **Returns:** A dictionary with the Polyhaven addon status.

### Data Persistence Commands

- **`put_persist_data`**: Stores data.
  - **Params:** `{"key": "my_key", "data": "my_data"}`
  - **Returns:** Confirmation of data storage.
- **`get_persist_data`**: Retrieves data.
  - **Params:** `{"key": "my_key", "default": "default_value"}`
  - **Returns:** The stored data or default value.
- **`remove_persist_data`**: Deletes data.
  - **Params:** `{"key": "my_key"}`
  - **Returns:** Confirmation of data removal.
