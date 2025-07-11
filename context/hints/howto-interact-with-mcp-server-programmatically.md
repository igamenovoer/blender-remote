# How to Interact with an MCP Server Programmatically

This guide explains two different ways to start and interact with an MCP server (like the `blender-mcp` server):
1.  **Programmatically with a Python Script**: This method involves writing a Python script that launches, controls, and communicates with the server. It's ideal for automated testing and building custom clients.
2.  **Manually with `curl`**: This method involves starting the server from the command line and using a tool like `curl` to send HTTP requests. It's great for manual debugging and exploring the API.

---

## Section 1: Programmatic Interaction with a Python Script

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

## Section 2: Manual Interaction with `curl`

This method is great for quick, manual tests and for exploring the server's API without writing any Python code.

### Step 1: Start the Server Manually with Uvicorn
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

Both methods allow you to interact with the MCP server over HTTP. The programmatic Python approach is best for building automated tests and clients, while the manual `curl` approach is excellent for quick debugging and API exploration.
