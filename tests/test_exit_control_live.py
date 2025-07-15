"""
Live test script for the new exit control methods in BlenderMCPClient.
This script tests the methods against a running BLD_Remote_MCP service.
"""
import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'context', 'refcode'))

from auto_mcp_remote.blender_mcp_client import BlenderMCPClient
from auto_mcp_remote.data_types import BlenderMCPError

def test_exit_control_methods():
    """Test the new exit control methods against a live BLD_Remote_MCP service."""
    client = BlenderMCPClient(host='localhost', port=6688)  # BLD Remote MCP port
    
    print("[TESTING] Testing BlenderMCPClient exit control methods (LIVE)...")
    
    # Test 1: Connection test
    try:
        print("\n1. Testing connection...")
        if client.test_connection():
            print("   [PASS] Connection successful")
        else:
            print("   [FAIL] Connection failed")
            return False
    except Exception as e:
        print(f"   [FAIL] Connection test failed: {e}")
        return False
    
    # Test 2: Get Blender PID
    try:
        print("\n2. Testing get_blender_pid()...")
        pid = client.get_blender_pid()
        print(f"   [PASS] Blender PID: {pid}")
        if not isinstance(pid, int) or pid <= 0:
            print(f"   [FAIL] Invalid PID: {pid}")
            return False
        
        # Verify PID is actually a Blender process
        try:
            import psutil
            process = psutil.Process(pid)
            process_name = process.name()
            print(f"   [PASS] Process name: {process_name}")
            if "blender" not in process_name.lower():
                print(f"   [WARNING]  Warning: Process name '{process_name}' doesn't contain 'blender'")
        except ImportError:
            print("   ℹ️  psutil not available, skipping process name verification")
        except Exception as e:
            print(f"   [WARNING]  Could not verify process name: {e}")
            
    except Exception as e:
        print(f"   [FAIL] get_blender_pid() failed: {e}")
        return False
    
    # Test 3: Execute some test Python code to verify the service works
    try:
        print("\n3. Testing Python code execution...")
        test_code = "import bpy; print(f'Blender version: {bpy.app.version}')"
        result = client.execute_python(test_code)
        print(f"   [PASS] Python execution result: {result.strip()}")
    except Exception as e:
        print(f"   [FAIL] Python execution failed: {e}")
        return False
    
    # Test 4: Test send_exit_request (but warn user first)
    print("\n4. Testing send_exit_request()...")
    user_input = input("   [WARNING]  This will gracefully exit Blender. Continue? (y/N): ")
    if user_input.lower() in ['y', 'yes']:
        try:
            print("   [CONNECT] Sending exit request...")
            success = client.send_exit_request()
            print(f"   [PASS] Exit request sent: {success}")
            
            # Wait a moment and check if service is still accessible
            print("   ⏳ Waiting 3 seconds to check if service shut down...")
            time.sleep(3)
            
            try:
                client.test_connection()
                print("   [WARNING]  Service still accessible after exit request")
            except:
                print("   [PASS] Service is no longer accessible (expected after exit)")
                
        except Exception as e:
            print(f"   [FAIL] send_exit_request() failed: {e}")
            return False
    else:
        print("   ⏭️  Skipping exit request test (user choice)")
    
    # Test 5: Test kill_blender_process (only if service is still running)
    print("\n5. Testing kill_blender_process()...")
    user_input = input("   [WARNING]  This will forcefully kill Blender. Continue? (y/N): ")
    if user_input.lower() in ['y', 'yes']:
        try:
            print("   💀 Killing Blender process...")
            success = client.kill_blender_process()
            print(f"   [PASS] Kill process result: {success}")
            
            # Wait a moment and check if service is still accessible
            print("   ⏳ Waiting 3 seconds to check if process was killed...")
            time.sleep(3)
            
            try:
                client.test_connection()
                print("   [WARNING]  Service still accessible after kill")
            except:
                print("   [PASS] Service is no longer accessible (expected after kill)")
                
        except Exception as e:
            print(f"   [FAIL] kill_blender_process() failed: {e}")
            return False
    else:
        print("   ⏭️  Skipping kill process test (user choice)")
    
    print("\n[SUCCESS] All available tests completed successfully!")
    return True

if __name__ == "__main__":
    success = test_exit_control_methods()
    sys.exit(0 if success else 1)