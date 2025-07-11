# How to Interact with an MCP Server Programmatically

This guide explains different ways to start and interact with an MCP server (like the `blender-mcp` server):
1.  **Using MCP CLI Tools**: The standard way to interact with MCP servers using the official `mcp[cli]` package.
2.  **Programmatically with a Python Script**: Writing a Python script that launches, controls, and communicates with the server. Ideal for automated testing and building custom clients.
3.  **Manually with `curl`**: Starting the server from the command line and using `curl` to send HTTP requests. Great for manual debugging and exploring the API.

---

## Section 1: Using MCP CLI Tools (Recommended)

The `blender-mcp` server is a proper MCP-compliant server built with `FastMCP`, which means it works perfectly with the official MCP CLI tools. This is the **recommended approach** for most use cases.

### Installation

```bash
# Install the MCP CLI tools
pip install "mcp[cli]"
# or using uv (recommended)
uv add "mcp[cli]"
```

### Usage Examples

#### Development and Testing with MCP Inspector

The MCP Inspector provides an interactive web interface for testing your server:

```bash
# Test the server with MCP Inspector
uv run mcp dev context/refcode/blender-mcp/src/blender_mcp/server.py

# With additional dependencies if needed
uv run mcp dev context/refcode/blender-mcp/src/blender_mcp/server.py --with tempfile --with pathlib
```

This opens a web interface where you can:
- See all available tools and their schemas
- Test tools interactively
- View real-time logs
- Debug issues easily

#### Direct Server Execution

```bash
# Run the server directly
uv run mcp run context/refcode/blender-mcp/src/blender_mcp/server.py

# With specific transport (stdio is default)
uv run mcp run context/refcode/blender-mcp/src/blender_mcp/server.py --transport stdio
```

#### Claude Desktop Integration

```bash
# Install in Claude Desktop
uv run mcp install context/refcode/blender-mcp/src/blender_mcp/server.py --name "Blender MCP Server"

# With environment variables if needed
uv run mcp install context/refcode/blender-mcp/src/blender_mcp/server.py \
  --name "Blender MCP Server" \
  -v BLENDER_HOST=localhost \
  -v BLENDER_PORT=9876
```

#### Programmatic MCP Client

You can also create a custom MCP client to interact with the server:

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def interact_with_blender_mcp():
    # Configure server parameters
    server_params = StdioServerParameters(
        command="python",
        args=["/workspace/code/blender-remote/context/refcode/blender-mcp/src/blender_mcp/server.py"],
        env=None,
    )
    
    # Connect to server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {[tool.name for tool in tools.tools]}")
            
            # Call get_scene_info tool
            scene_result = await session.call_tool("get_scene_info", {})
            print(f"Scene info: {scene_result}")
            
            # Execute Blender code
            code_result = await session.call_tool("execute_blender_code", {
                "code": "import bpy; bpy.ops.mesh.primitive_cube_add(location=(2, 2, 2))"
            })
            print(f"Code execution result: {code_result}")

# Run the client
asyncio.run(interact_with_blender_mcp())
```

### Why Use MCP CLI Tools?

1. **Standard Protocol**: Uses the official MCP protocol for maximum compatibility
2. **Built-in Tools**: MCP Inspector, Claude Desktop integration, etc.
3. **Proper Error Handling**: Better error messages and debugging
4. **Type Safety**: Full schema validation and type checking
5. **Ecosystem Integration**: Works with all MCP-compatible clients

---

## Section 2: Programmatic Interaction with a Python Script (HTTP)

**Note**: This approach is less common since the server is MCP-compliant and works better with the official MCP CLI tools. However, it's useful for specific HTTP-based integration scenarios.

This approach encapsulates the entire server lifecycle within a single "client" script, which launches the server as a subprocess and communicates with it via HTTP requests.

### Core Components
-   **`subprocess` module**: For creating and managing the server process.
-   **`requests` library**: For sending HTTP requests to the server's tool endpoints.
-   **An MCP Server**: The server script you want to control (e.g., `blender-mcp/src/blender_mcp/server.py`).

### Step-by-Step Implementation

#### Step 1: Start the MCP Server as a Subprocess
Use `subprocess.Popen` to execute the server script in a non-blocking way. It's crucial to set the `cwd` (current working directory) to the server's directory to ensure all relative paths and module imports work correctly.

```python
import subprocess
import sys
import os

def start_mcp_server_with_uvicorn(server_script_path, host='127.0.0.1', port=8000):
    """Starts the MCP server as a subprocess using uvicorn."""
    server_dir = os.path.dirname(server_script_path)
    
    print(f"Starting MCP server from: {server_dir} on port {port}")
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server:mcp", "--host", host, "--port", str(port)],
        cwd=server_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    print(f"MCP Server started with PID: {process.pid}")
    return process
```

#### Step 2: Wait for the Server to Initialize
Poll a known endpoint (like the root URL) until it responds successfully.

```python
import time
import requests

def wait_for_server(url, timeout=20):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                print("Server is up and running!")
                return True
        except requests.ConnectionError:
            time.sleep(0.5)
    print("Server failed to start within the timeout period.")
    return False
```

#### Step 3: Call a Tool via HTTP
Tools are exposed as HTTP endpoints. `POST` a JSON payload with the tool's parameters to `http://<host>:<port>/tools/<tool_name>`.

```python
def call_tool(base_url, tool_name, params={}):
    url = f"{base_url}/tools/{tool_name}"
    headers = {'Content-Type': 'application/json'}
    
    print(f"--- Calling tool: {tool_name} with params: {params} ---")
    try:
        response = requests.post(url, json=params, headers=headers)
        response.raise_for_status()
        result = response.json()
        print("Response received:", result)
        return result
    except requests.exceptions.RequestException as e:
        print(f"Error calling tool {tool_name}: {e}")
        return None
```

#### Step 4: Shut Down the Server
Terminate the server process to free up resources.

```python
def shutdown_server(server_process):
    print("--- Shutting down MCP server ---")
    server_process.terminate()
    try:
        server_process.communicate(timeout=5)
        print("Server terminated gracefully.")
    except subprocess.TimeoutExpired:
        print("Server did not terminate, killing.")
        server_process.kill()
```

### Complete Example Script

```python
# --- Full script combining all steps ---
import subprocess
import requests
import time
import sys
import os
import json

# (Paste the four functions from above here: start_mcp_server_with_uvicorn, wait_for_server, call_tool, shutdown_server)

def main_programmatic_test():
    SERVER_SCRIPT_PATH = 'context/refcode/blender-mcp/src/blender_mcp/server.py'
    HOST = '127.0.0.1'
    PORT = 8000
    BASE_URL = f"http://{HOST}:{PORT}"

    # NOTE: Blender must be running with the addon enabled for the server to connect to it.
    server_process = start_mcp_server_with_uvicorn(SERVER_SCRIPT_PATH, host=HOST, port=PORT)
    
    try:
        if not wait_for_server(BASE_URL):
            stdout, stderr = server_process.communicate()
            print("--- Server STDOUT ---\n", stdout.decode())
            print("--- Server STDERR ---\n", stderr.decode())
            return

        call_tool(BASE_URL, "get_scene_info")
        code = "import bpy; bpy.ops.mesh.primitive_uv_sphere_add(location=(0, 0, 5))"
        call_tool(BASE_URL, "execute_blender_code", {"code": code})
        call_tool(BASE_URL, "get_scene_info")

    finally:
        shutdown_server(server_process)

if __name__ == "__main__":
    # Ensure you have requests and uvicorn installed:
    # pip install requests uvicorn
    main_programmatic_test()
```

---

## Section 3: Manual Interaction with `curl`

This method is great for quick, manual tests and for exploring the server's API without writing any Python code.

### Step 1: Start the Server Manually with Uvicorn
**Note**: For regular development, use `uv run mcp dev` instead. This manual approach is for specific HTTP testing scenarios.

First, you need to start the MCP server from your terminal so that it listens for HTTP requests.

1.  **Navigate to the server's source directory**:
    ```bash
    cd context/refcode/blender-mcp/src
    ```

2.  **Run the `uvicorn` command**:
    ```bash
    uvicorn blender_mcp.server:mcp --host 127.0.0.1 --port 8000
    ```
    -   `blender_mcp.server:mcp`: Tells `uvicorn` to find the `mcp` object in the `blender_mcp/server.py` file.
    -   This command will occupy your terminal until you stop it (with `Ctrl+C`).
    -   Remember, the Blender addon must be running for the server to connect to it.

### Step 2: Interact with Tools using `curl`
With the server running, you can now use `curl` from another terminal to send requests.

#### Tool URL Structure
The URL for any tool is: `http://<host>:<port>/tools/<tool_name>`

#### Example 1: Calling a Tool with No Parameters (`get_scene_info`)
Send an empty JSON object `{}` as the body.

```bash
curl -X POST -H "Content-Type: application/json" \
-d '{}' \
http://127.0.0.1:8000/tools/get_scene_info
```

#### Example 2: Calling a Tool with Parameters (`execute_blender_code`)
Pass arguments as a JSON object in the request body.

```bash
CODE_TO_RUN="import bpy; print(f'Active scene is: {bpy.context.scene.name}')"

curl -X POST -H "Content-Type: application/json" \
-d "{\"code\": \"$CODE_TO_RUN\"}" \
http://127.0.0.1:8000/tools/execute_blender_code
```

#### Example 3: Calling a Tool with Multiple Parameters (`download_polyhaven_asset`)

```bash
curl -X POST -H "Content-Type: application/json" \
-d '{"asset_id": "blue_photo_studio", "asset_type": "hdris", "resolution": "1k"}' \
http://127.0.0.1:8000/tools/download_polyhaven_asset
```

## Conclusion

You now have three different ways to interact with the `blender-mcp` server:

1. **MCP CLI Tools (Recommended)**: Use `uv run mcp dev` for development, `uv run mcp install` for Claude Desktop integration, and create MCP clients using the official SDK. This is the standard, most compatible approach.

2. **HTTP/REST API**: Use the programmatic Python approach for building automated tests and custom HTTP clients, or the manual `curl` approach for quick debugging and API exploration.

3. **Custom Integration**: Build your own clients using the MCP Python SDK for maximum flexibility and type safety.

### Project-Specific Notes for `blender-mcp`

- **Prerequisites**: Always ensure Blender is running with the addon enabled (listening on port 9876) before starting the MCP server
- **Server Location**: The server is located at `context/refcode/blender-mcp/src/blender_mcp/server.py`
- **Available Tools**: The server provides tools like `get_scene_info`, `execute_blender_code`, `get_viewport_screenshot`, and various asset management tools
- **Development**: Use the MCP Inspector (`uv run mcp dev`) for the best development experience
- **Production**: Use Claude Desktop integration (`uv run mcp install`) for end-user deployment

The MCP CLI approach is recommended as it provides the best developer experience and full compatibility with the MCP ecosystem.
