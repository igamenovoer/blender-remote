#!/usr/bin/env python3
"""
Test script for programmatic interaction with blender-mcp server
Based on the guide at context/hints/howto-interact-with-mcp-server-programmatically.md
"""

import subprocess
import requests
import time
import sys
import os
import json

def start_mcp_server_with_uvicorn(server_script_path, host='127.0.0.1', port=8000):
    """Starts the MCP server as a subprocess using uvicorn."""
    server_dir = os.path.dirname(server_script_path)
    
    print(f"Starting MCP server from: {server_dir} on port {port}")
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "blender_mcp.server:mcp", "--host", host, "--port", str(port)],
        cwd=server_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    print(f"MCP Server started with PID: {process.pid}")
    return process

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

def shutdown_server(server_process):
    print("--- Shutting down MCP server ---")
    server_process.terminate()
    try:
        server_process.communicate(timeout=5)
        print("Server terminated gracefully.")
    except subprocess.TimeoutExpired:
        print("Server did not terminate, killing.")
        server_process.kill()

def main_programmatic_test():
    SERVER_SCRIPT_PATH = 'context/refcode/blender-mcp/src/blender_mcp/server.py'
    HOST = '127.0.0.1'
    PORT = 8000
    BASE_URL = f"http://{HOST}:{PORT}"

    print("=== PROGRAMMATIC BLENDER-MCP TEST ===")
    print(f"Server path: {SERVER_SCRIPT_PATH}")
    print(f"Will connect to Blender on port 9876")
    print()

    # Start the server
    server_process = start_mcp_server_with_uvicorn(SERVER_SCRIPT_PATH, host=HOST, port=PORT)
    
    try:
        # Wait for server to start
        if not wait_for_server(BASE_URL):
            stdout, stderr = server_process.communicate()
            print("--- Server STDOUT ---\n", stdout.decode())
            print("--- Server STDERR ---\n", stderr.decode())
            return

        print("\n=== Testing Tools ===")
        
        # Test 1: Get scene info
        print("1. Getting scene info...")
        call_tool(BASE_URL, "get_scene_info")
        
        # Test 2: Execute some simple Blender code
        print("\n2. Executing Blender code...")
        code = "import bpy; print(f'Scene has {len(bpy.context.scene.objects)} objects')"
        call_tool(BASE_URL, "execute_blender_code", {"code": code})
        
        # Test 3: Check various integration statuses
        print("\n3. Checking integration statuses...")
        call_tool(BASE_URL, "get_polyhaven_status")
        call_tool(BASE_URL, "get_sketchfab_status")
        call_tool(BASE_URL, "get_hyper3d_status")

        # Test 4: Add a simple object and check scene again
        print("\n4. Adding a simple cube and checking scene...")
        code = "import bpy; bpy.ops.mesh.primitive_cube_add(location=(2, 2, 2))"
        call_tool(BASE_URL, "execute_blender_code", {"code": code})
        call_tool(BASE_URL, "get_scene_info")

    finally:
        shutdown_server(server_process)

if __name__ == "__main__":
    # Check if dependencies are available
    try:
        import requests
        import uvicorn
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Install with: pip install requests uvicorn")
        sys.exit(1)
    
    main_programmatic_test()