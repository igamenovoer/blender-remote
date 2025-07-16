# MCP Server API Reference

The MCP Server is a `FastMCP` server that acts as a bridge between an MCP-compatible IDE (like VS Code with the MCP extension) and the `BLD_Remote_MCP` addon running in Blender. It exposes a set of tools that can be called from the IDE to control Blender.

**File:** `src/blender_remote/mcp_server.py`
**Command:** `blender-remote`

## Tools

These are the functions decorated with `@mcp.tool()` that are available to the LLM or IDE.

### `get_scene_info()`
Retrieves a summary of the current scene from Blender.

- **Parameters:** None
- **Returns (dict):** A dictionary containing scene information, such as a list of objects and materials.

**Example:**
```python
# From tests/mcp-server/test_functional_equivalence.py
async with mcp.server.stdio.stdio_client() as (read, write):
    async with MCPClient(read, write) as client:
        async with client.create_session() as session:
            result = await session.call_tool("get_scene_info", {})
            print(f"Scene info: {result}")
```

### `execute_code(code, send_as_base64=False, return_as_base64=False)`
Executes a string of Python code within Blender's context. This is a powerful tool for performing custom actions.

- **`code` (str):** The Python code to execute.
- **`send_as_base64` (bool):** If `True`, the code string is encoded to base64 before being sent to Blender, which helps prevent issues with special characters.
- **`return_as_base64` (bool):** If `True`, the result from Blender is expected to be base64 encoded.
- **Returns (dict):** A dictionary containing the output from the executed code.

**Example:**
```python
# From tests/mcp-server/test_synchronous_execution.py
# Simple code execution
result = await session.call_tool("execute_code", {"code": "print('Hello from Blender!')"})

# Complex code with base64 encoding
complex_code = '''
import bpy
import numpy as np

# Create objects
for i in range(5):
    bpy.ops.mesh.primitive_cube_add(location=(i*2, 0, 0))
    obj = bpy.context.active_object
    obj.name = f"Cube_{i}"
'''
result = await session.call_tool("execute_code", {
    "code": complex_code,
    "send_as_base64": True,
    "return_as_base64": True
})
```

### `get_object_info(object_name)`
Gets detailed information for a specific object in the scene.

- **`object_name` (str):** The name of the object to query.
- **Returns (dict):** A dictionary containing the object's properties like location, rotation, scale, and materials.

**Example:**
```python
# From tests/mcp-server/test_functional_equivalence.py
result = await session.call_tool("get_object_info", {"object_name": "Cube"})
print(f"Cube info: {result}")
```

### `get_viewport_screenshot(max_size=800, format="png")`
Captures a screenshot of the 3D viewport and returns it as a base64-encoded image. This tool only works when Blender is running in GUI mode.

- **`max_size` (int):** The maximum dimension (width or height) of the resulting image.
- **`format` (str):** The image format, either `"png"` or `"jpg"`.
- **Returns (dict):** An MCP-compliant image dictionary, with the `type` set to `"image"` and the `data` field containing the base64 string.

**Example:**
```python
# From tests/mcp-server/test_functional_equivalence.py
try:
    result = await session.call_tool("get_viewport_screenshot", {"max_size": 400})
    # Result contains base64 encoded image data
except Exception as e:
    print(f"Screenshot failed (expected in background mode): {e}")
```

### `check_connection_status()`
Verifies the connection to the underlying `BLD_Remote_MCP` service in Blender.

- **Parameters:** None
- **Returns (dict):** A dictionary with the connection `status` (`"connected"`, `"disconnected"`, or `"error"`) and details about the connection.

### Data Persistence Tools

These tools interact with the simple key-value store in the Blender addon.

#### `put_persist_data(key, data)`
Stores a piece of data under a specific key.

- **`key` (str):** The key to store the data under.
- **`data` (any):** The data to store. It should be JSON-serializable.
- **Returns (dict):** A success or error message.

#### `get_persist_data(key, default=None)`
Retrieves data that was previously stored.

- **`key` (str):** The key of the data to retrieve.
- **`default` (any):** A default value to return if the key is not found.
- **Returns (dict):** A dictionary containing the `data` and a `found` (bool) flag.

#### `remove_persist_data(key)`
Deletes a piece of data from the store.

- **`key` (str):** The key of the data to remove.
- **Returns (dict):** A dictionary with a `removed` (bool) flag.
