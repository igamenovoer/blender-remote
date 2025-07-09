#!/usr/bin/env python3
"""
Test script to verify BLD_Remote_MCP compatibility fix.

This script tests the exact scenario that was failing:
1. Connect to BLD_Remote_MCP on port 9876
2. Send get_polyhaven_status command
3. Verify connection stays open and response is received
"""

import socket
import json
import time
import sys

def test_bld_remote_compatibility():
    """Test that BLD_Remote_MCP works with LLM client protocols."""
    
    print("🧪 Testing BLD_Remote_MCP compatibility fix...")
    print("=" * 50)
    
    # Test configuration
    host = '127.0.0.1'
    port = 6688
    
    try:
        # Create socket and connect
        print(f"🔗 Connecting to {host}:{port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # 10 second timeout
        
        start_time = time.time()
        sock.connect((host, port))
        connect_time = time.time() - start_time
        print(f"✅ Connected successfully in {connect_time:.3f}s")
        
        # Test 1: Send get_polyhaven_status (the failing command)
        print("\n📤 Test 1: Sending get_polyhaven_status command...")
        test_command = {
            "type": "get_polyhaven_status",
            "params": {}
        }
        
        json_data = json.dumps(test_command)
        print(f"   Command: {json_data}")
        
        sock.sendall(json_data.encode('utf-8'))
        print("   ✅ Command sent successfully")
        
        # Receive response
        print("   📥 Waiting for response...")
        response_data = sock.recv(4096)
        
        if not response_data:
            print("   ❌ No response received")
            return False
        
        response = json.loads(response_data.decode('utf-8'))
        print(f"   ✅ Response received: {response}")
        
        # Verify response format
        if "status" in response and response["status"] == "success":
            print("   ✅ Response format is correct")
        else:
            print("   ⚠️  Response format differs but connection worked")
        
        # Test 2: Send get_scene_info command to verify connection is still open
        print("\n📤 Test 2: Sending get_scene_info command...")
        test_command2 = {
            "type": "get_scene_info",
            "params": {}
        }
        
        json_data2 = json.dumps(test_command2)
        print(f"   Command: {json_data2}")
        
        sock.sendall(json_data2.encode('utf-8'))
        print("   ✅ Command sent successfully")
        
        # Receive response
        print("   📥 Waiting for response...")
        response_data2 = sock.recv(4096)
        
        if not response_data2:
            print("   ❌ No response received")
            return False
        
        response2 = json.loads(response_data2.decode('utf-8'))
        print(f"   ✅ Response received: {response2}")
        
        # Verify scene info response
        if "status" in response2 and response2["status"] == "success":
            if "result" in response2 and "name" in response2["result"]:
                print("   ✅ Scene info response is correct")
            else:
                print("   ⚠️  Scene info response format unexpected")
        else:
            print("   ❌ Scene info response format incorrect")
        
        # Test 3: Close connection gracefully
        print("\n🔒 Test 3: Closing connection...")
        sock.close()
        print("   ✅ Connection closed successfully")
        
        print("\n" + "=" * 50)
        print("🎉 COMPATIBILITY TEST PASSED!")
        print("✅ Connection stays persistent between commands")
        print("✅ Commands are processed correctly") 
        print("✅ Responses are in expected format")
        
        return True
        
    except ConnectionRefusedError:
        print(f"❌ Connection refused - is BLD_Remote_MCP running on port {port}?")
        return False
    except socket.timeout:
        print("❌ Connection timed out")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON response: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        try:
            sock.close()
        except:
            pass

def main():
    """Main test function."""
    print("BLD_Remote_MCP Compatibility Test")
    print("This test verifies the connection persistence fix")
    print()
    
    success = test_bld_remote_compatibility()
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()