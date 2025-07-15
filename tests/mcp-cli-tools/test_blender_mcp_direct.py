#!/usr/bin/env python3
"""
Test script to run the blender-mcp server directly and interact with it
"""

import sys
import os
import json
import socket
import subprocess
import time

# Add the blender-mcp source to Python path
sys.path.insert(0, os.path.join(os.getcwd(), "context/refcode/blender-mcp/src"))

def test_blender_connection_direct():
    """Test direct connection to BlenderAutoMCP (what blender-mcp connects to)"""
    print("=== TESTING DIRECT CONNECTION TO BLENDER AUTO MCP ===")
    print("This tests the connection that blender-mcp server uses internally")
    
    try:
        # Connect directly to BlenderAutoMCP on port 9876
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("127.0.0.1", 9876))
        
        # Test 1: Get scene info
        print("\n1. Testing get_scene_info command...")
        command = {"type": "get_scene_info", "params": {}}
        sock.sendall(json.dumps(command).encode('utf-8'))
        
        response_data = sock.recv(8192)
        response = json.loads(response_data.decode('utf-8'))
        print("Response:", json.dumps(response, indent=2))
        
        sock.close()
        
        # Test 2: Execute code
        print("\n2. Testing execute_code command...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("127.0.0.1", 9876))
        
        command = {
            "type": "execute_code", 
            "params": {"code": "import bpy; print(f'Scene: {bpy.context.scene.name}')"}
        }
        sock.sendall(json.dumps(command).encode('utf-8'))
        
        response_data = sock.recv(8192)
        response = json.loads(response_data.decode('utf-8'))
        print("Response:", json.dumps(response, indent=2))
        
        sock.close()
        
        # Test 3: Check integrations
        print("\n3. Testing integration status commands...")
        integrations = ["get_polyhaven_status", "get_sketchfab_status", "get_hyper3d_status"]
        
        for integration in integrations:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(("127.0.0.1", 9876))
            
            command = {"type": integration, "params": {}}
            sock.sendall(json.dumps(command).encode('utf-8'))
            
            response_data = sock.recv(8192)
            response = json.loads(response_data.decode('utf-8'))
            print(f"{integration}: {response.get('result', {}).get('enabled', 'unknown')}")
            
            sock.close()
            
        return True
        
    except Exception as e:
        print(f"Error testing direct connection: {e}")
        return False

def test_blender_mcp_tools():
    """Test the blender-mcp server tools directly by importing the module"""
    print("\n=== TESTING BLENDER-MCP TOOLS DIRECTLY ===")
    
    try:
        # Import the blender_mcp server module directly
        from blender_mcp.server import get_scene_info, execute_blender_code, get_polyhaven_status
        from mcp.server.fastmcp import Context
        
        # Create a mock context
        ctx = Context()
        
        print("1. Testing get_scene_info tool...")
        result = get_scene_info(ctx)
        print("Result:", result[:200] + "..." if len(result) > 200 else result)
        
        print("\n2. Testing execute_blender_code tool...")
        code = "import bpy; print(f'Active scene: {bpy.context.scene.name}')"
        result = execute_blender_code(ctx, code)
        print("Result:", result)
        
        print("\n3. Testing get_polyhaven_status tool...")
        result = get_polyhaven_status(ctx)
        print("Result:", result)
        
        return True
        
    except Exception as e:
        print(f"Error testing blender-mcp tools: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=== BLENDER-MCP INTERACTION TEST ===")
    print("Testing both direct connection and tool functionality")
    print()
    
    # Test 1: Direct connection to BlenderAutoMCP
    success1 = test_blender_connection_direct()
    
    # Test 2: blender-mcp tools
    success2 = test_blender_mcp_tools()
    
    print(f"\n=== RESULTS ===")
    print(f"Direct BlenderAutoMCP connection: {'[PASS] Success' if success1 else '[FAIL] Failed'}")
    print(f"blender-mcp tools test: {'[PASS] Success' if success2 else '[FAIL] Failed'}")

if __name__ == "__main__":
    main()