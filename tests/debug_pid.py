"""
Debug script to check what's happening with the get_blender_pid() method.
"""
import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'context', 'refcode'))

from auto_mcp_remote.blender_mcp_client import BlenderMCPClient

def debug_pid():
    """Debug the get_blender_pid() method."""
    client = BlenderMCPClient(host='localhost', port=6688)
    
    print("🔍 Debugging get_blender_pid() method...")
    
    # Test connection first
    try:
        if not client.test_connection():
            print("❌ Connection failed")
            return
        print("✅ Connection successful")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    # Test raw execute_code command
    try:
        print("\n📡 Testing raw execute_code command...")
        code = "import os; print(os.getpid())"
        response = client.execute_command("execute_code", {"code": code})
        print(f"Raw response: {json.dumps(response, indent=2)}")
        
        # Check response structure
        if response.get("status") == "success":
            result = response.get("result", {})
            print(f"Result dict: {result}")
            execution_result = result.get("result", "")
            print(f"Execution result: '{execution_result}'")
            print(f"Execution result type: {type(execution_result)}")
            print(f"Execution result length: {len(execution_result)}")
            print(f"Execution result repr: {repr(execution_result)}")
        else:
            print(f"❌ Command failed: {response.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Raw execute_code failed: {e}")
        
    # Test execute_python method
    try:
        print("\n🐍 Testing execute_python method...")
        code = "import os; print(os.getpid())"
        result = client.execute_python(code)
        print(f"execute_python result: '{result}'")
        print(f"execute_python result type: {type(result)}")
        print(f"execute_python result length: {len(result)}")
        print(f"execute_python result repr: {repr(result)}")
        
    except Exception as e:
        print(f"❌ execute_python failed: {e}")

if __name__ == "__main__":
    debug_pid()