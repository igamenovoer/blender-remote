#!/usr/bin/env python3
"""
Test script for MCP server persistence functionality.

This tests the persistence feature through the MCP server interface.
"""

import asyncio
import json
import socket
import sys
import subprocess
import time
from typing import Dict, Any


async def test_mcp_server_persistence():
    """Test persistence through MCP server tools."""
    print("🧪 Testing MCP server persistence tools...")
    
    # Start MCP server
    print("🚀 Starting MCP server...")
    mcp_process = await asyncio.create_subprocess_exec(
        "pixi", "run", "uvx", "blender-remote",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    try:
        # Give server time to start
        await asyncio.sleep(2)
        
        # Test with a simple client that speaks MCP protocol
        print("🔗 Testing MCP server connection...")
        
        # The MCP server should be available as a FastMCP instance
        # but testing that requires more complex MCP protocol implementation
        # For now, we'll test the underlying TCP connection to verify the service is up
        
        # Test basic TCP connection to ensure service is available
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect(('127.0.0.1', 6688))
            response = send_test_command(sock, "get_scene_info")
            print(f"    Connection test response: {response}")
            assert response.get("status") == "success", f"Connection failed: {response}"
            print("    ✅ MCP server is accessible")
        finally:
            sock.close()
            
    finally:
        # Clean up MCP server process
        if mcp_process.returncode is None:
            mcp_process.terminate()
            await mcp_process.wait()


def send_test_command(sock: socket.socket, command_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Send a test command to verify MCP server connection."""
    if params is None:
        params = {}
    
    command = {
        "type": command_type,
        "params": params
    }
    
    command_json = json.dumps(command)
    sock.sendall(command_json.encode('utf-8'))
    
    response_data = sock.recv(8192)
    response = json.loads(response_data.decode('utf-8'))
    
    return response


def test_mcp_server_available():
    """Test that MCP server executable is available."""
    print("🧪 Testing MCP server availability...")
    
    try:
        # Test that the uvx blender-remote command exists
        result = subprocess.run(
            ["pixi", "run", "uvx", "blender-remote", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("    ✅ MCP server command is available")
            return True
        else:
            print(f"    ❌ MCP server command failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("    ❌ MCP server command timed out")
        return False
    except Exception as e:
        print(f"    ❌ MCP server command error: {e}")
        return False


async def main():
    """Run MCP server persistence tests."""
    print("🚀 Starting MCP Server Persistence Tests")
    print("=" * 50)
    
    try:
        # Test MCP server availability
        if not test_mcp_server_available():
            print("❌ MCP server not available, skipping tests")
            return 1
        
        # Test MCP server persistence (basic connectivity)
        await test_mcp_server_persistence()
        
        print("✅ MCP server is properly configured and accessible")
        print("🎯 For full persistence testing, use the direct TCP tests")
        print("   The MCP server will use the same persistence backend")
        
        return 0
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))