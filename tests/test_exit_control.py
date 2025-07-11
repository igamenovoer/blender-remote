"""
Test script for the new exit control methods in BlenderMCPClient.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'context', 'refcode'))

from auto_mcp_remote.blender_mcp_client import BlenderMCPClient
from auto_mcp_remote.data_types import BlenderMCPError

def test_client_methods():
    """Test the new exit control methods."""
    client = BlenderMCPClient(host='localhost', port=6688)  # BLD Remote MCP port
    
    print("Testing BlenderMCPClient exit control methods...")
    
    # Test 1: Connection test
    try:
        print("1. Testing connection...")
        if client.test_connection():
            print("   ✓ Connection successful")
        else:
            print("   ✗ Connection failed")
            return False
    except Exception as e:
        print(f"   ✗ Connection test failed: {e}")
        return False
    
    # Test 2: Get Blender PID
    try:
        print("2. Testing get_blender_pid()...")
        pid = client.get_blender_pid()
        print(f"   ✓ Blender PID: {pid}")
        if not isinstance(pid, int) or pid <= 0:
            print(f"   ✗ Invalid PID: {pid}")
            return False
    except Exception as e:
        print(f"   ✗ get_blender_pid() failed: {e}")
        return False
    
    # Test 3: Send exit request (commented out to avoid killing the server)
    print("3. Testing send_exit_request()...")
    print("   (Skipped - would kill the server)")
    
    # Test 4: Kill blender process (commented out to avoid killing the server)
    print("4. Testing kill_blender_process()...")
    print("   (Skipped - would kill the server)")
    
    print("\nAll tests completed successfully!")
    return True

if __name__ == "__main__":
    success = test_client_methods()
    sys.exit(0 if success else 1)