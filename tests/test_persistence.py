#!/usr/bin/env python3
"""
Test script for BLD Remote MCP persistence functionality.

This tests the data persistence feature that allows storing and retrieving
data across multiple MCP command executions.
"""

import json
import socket
import sys
import time
from typing import Dict, Any


def send_mcp_command(host: str, port: int, command_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Send a command to the BLD Remote MCP service."""
    if params is None:
        params = {}
    
    command = {
        "type": command_type,
        "params": params
    }
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10.0)
    
    try:
        sock.connect((host, port))
        
        # Send command
        command_json = json.dumps(command)
        sock.sendall(command_json.encode('utf-8'))
        
        # Receive response
        response_data = sock.recv(8192)
        response = json.loads(response_data.decode('utf-8'))
        
        return response
        
    finally:
        sock.close()


def test_persistence_basic():
    """Test basic persistence operations."""
    host = "127.0.0.1"
    port = 6688
    
    print("🧪 Testing basic persistence operations...")
    
    # Test 1: Put data
    print("  📝 Test 1: Storing data...")
    response = send_mcp_command(host, port, "put_persist_data", {
        "key": "test_key",
        "data": "Hello, persistence!"
    })
    print(f"    Response: {response}")
    assert response.get("status") == "success", f"Put failed: {response}"
    print("    ✅ Data stored successfully")
    
    # Test 2: Get data
    print("  📖 Test 2: Retrieving data...")
    response = send_mcp_command(host, port, "get_persist_data", {
        "key": "test_key"
    })
    print(f"    Response: {response}")
    assert response.get("status") == "success", f"Get failed: {response}"
    result = response.get("result", {})
    assert result.get("found") == True, f"Data not found: {result}"
    assert result.get("data") == "Hello, persistence!", f"Data mismatch: {result}"
    print("    ✅ Data retrieved successfully")
    
    # Test 3: Get non-existent data
    print("  🔍 Test 3: Getting non-existent data...")
    response = send_mcp_command(host, port, "get_persist_data", {
        "key": "non_existent_key",
        "default": "default_value"
    })
    print(f"    Response: {response}")
    assert response.get("status") == "success", f"Get failed: {response}"
    result = response.get("result", {})
    assert result.get("found") == False, f"Should not find non-existent key: {result}"
    assert result.get("data") == "default_value", f"Default value not returned: {result}"
    print("    ✅ Non-existent data handled correctly")
    
    # Test 4: Remove data
    print("  🗑️  Test 4: Removing data...")
    response = send_mcp_command(host, port, "remove_persist_data", {
        "key": "test_key"
    })
    print(f"    Response: {response}")
    assert response.get("status") == "success", f"Remove failed: {response}"
    result = response.get("result", {})
    assert result.get("removed") == True, f"Data not removed: {result}"
    print("    ✅ Data removed successfully")
    
    # Test 5: Verify data is gone
    print("  🔍 Test 5: Verifying data is gone...")
    response = send_mcp_command(host, port, "get_persist_data", {
        "key": "test_key"
    })
    print(f"    Response: {response}")
    assert response.get("status") == "success", f"Get failed: {response}"
    result = response.get("result", {})
    assert result.get("found") == False, f"Data should be gone: {result}"
    print("    ✅ Data successfully removed")
    
    print("✅ All basic persistence tests passed!")


def test_persistence_complex_data():
    """Test persistence with complex data types."""
    host = "127.0.0.1"
    port = 6688
    
    print("🧪 Testing complex data persistence...")
    
    # Test complex data structure
    complex_data = {
        "numbers": [1, 2, 3, 4, 5],
        "nested": {
            "name": "test",
            "value": 42,
            "active": True
        },
        "string": "Complex data test"
    }
    
    print("  📝 Storing complex data...")
    response = send_mcp_command(host, port, "put_persist_data", {
        "key": "complex_key",
        "data": complex_data
    })
    print(f"    Response: {response}")
    assert response.get("status") == "success", f"Put failed: {response}"
    print("    ✅ Complex data stored successfully")
    
    print("  📖 Retrieving complex data...")
    response = send_mcp_command(host, port, "get_persist_data", {
        "key": "complex_key"
    })
    print(f"    Response: {response}")
    assert response.get("status") == "success", f"Get failed: {response}"
    result = response.get("result", {})
    assert result.get("found") == True, f"Data not found: {result}"
    retrieved_data = result.get("data")
    assert retrieved_data == complex_data, f"Data mismatch: {retrieved_data} != {complex_data}"
    print("    ✅ Complex data retrieved successfully")
    
    # Cleanup
    send_mcp_command(host, port, "remove_persist_data", {"key": "complex_key"})
    
    print("✅ Complex data persistence tests passed!")


def test_persistence_via_blender_api():
    """Test persistence using the bld_remote API inside Blender."""
    host = "127.0.0.1"
    port = 6688
    
    print("🧪 Testing persistence via Blender API...")
    
    # Test storing data using bld_remote.persist API
    code = """
import bld_remote

# Store some data
bld_remote.persist.put_data("api_test_key", {"message": "From Blender API", "number": 123})

# Retrieve it back
retrieved = bld_remote.persist.get_data("api_test_key")
print(f"Retrieved via API: {retrieved}")

# Store result for external verification
bld_remote.persist.put_data("api_test_result", retrieved)
"""
    
    print("  🐍 Executing Blender Python code...")
    response = send_mcp_command(host, port, "execute_code", {"code": code})
    print(f"    Response: {response}")
    assert response.get("status") == "success", f"Code execution failed: {response}"
    print("    ✅ Blender API code executed successfully")
    
    # Verify the result externally
    print("  📖 Verifying result externally...")
    response = send_mcp_command(host, port, "get_persist_data", {
        "key": "api_test_result"
    })
    print(f"    Response: {response}")
    assert response.get("status") == "success", f"Get failed: {response}"
    result = response.get("result", {})
    assert result.get("found") == True, f"Result not found: {result}"
    data = result.get("data")
    expected = {"message": "From Blender API", "number": 123}
    assert data == expected, f"Data mismatch: {data} != {expected}"
    print("    ✅ Blender API persistence works correctly")
    
    # Cleanup
    send_mcp_command(host, port, "remove_persist_data", {"key": "api_test_key"})
    send_mcp_command(host, port, "remove_persist_data", {"key": "api_test_result"})
    
    print("✅ Blender API persistence tests passed!")


def main():
    """Run all persistence tests."""
    print("🚀 Starting BLD Remote MCP Persistence Tests")
    print("=" * 50)
    
    try:
        # Test connection first
        print("🔗 Testing connection...")
        response = send_mcp_command("127.0.0.1", 6688, "get_scene_info")
        if response.get("status") != "success":
            print(f"❌ Connection failed: {response}")
            return 1
        print("✅ Connection established")
        print()
        
        # Run tests
        test_persistence_basic()
        print()
        test_persistence_complex_data()
        print()
        test_persistence_via_blender_api()
        print()
        
        print("🎉 All persistence tests passed!")
        return 0
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())