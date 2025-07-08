#!/usr/bin/env python3
"""
Manual Test Example - Simple Dual Service Verification

This script provides a simple example of how to manually test both
BLD_Remote_MCP and BlenderAutoMCP services running in Blender.

Use this as a reference for creating custom tests or debugging specific issues.
"""

import sys
import time
import json
import socket
from pathlib import Path

# Add auto_mcp_remote to path
sys.path.insert(0, str(Path(__file__).parent.parent / "context" / "refcode"))

def test_service_simple(port, service_name):
    """Simple test of a service on given port."""
    print(f"\n🔌 Testing {service_name} on port {port}")
    
    try:
        # Create socket connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect(('127.0.0.1', port))
        
        # Send test command
        test_command = {
            "code": "test_result = 2 + 2; print(f'Test calculation: {test_result}')",
            "message": f"Simple test for {service_name}"
        }
        
        message_json = json.dumps(test_command)
        print(f"📤 Sending: {message_json}")
        
        sock.sendall(message_json.encode('utf-8'))
        
        # Receive response
        response_data = sock.recv(4096)
        response = json.loads(response_data.decode('utf-8'))
        
        print(f"📥 Response: {response}")
        sock.close()
        
        if isinstance(response, dict) and 'response' in response:
            print(f"✅ {service_name}: SUCCESS")
            return True
        else:
            print(f"❌ {service_name}: Unexpected response format")
            return False
            
    except Exception as e:
        print(f"❌ {service_name}: ERROR - {e}")
        return False


def test_blender_api_simple(port, service_name):
    """Simple Blender API test."""
    print(f"\n🔍 Testing Blender API access - {service_name}")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect(('127.0.0.1', port))
        
        # Test Blender API
        api_command = {
            "code": """
import bpy
version_info = bpy.app.version_string
object_count = len(bpy.data.objects)
print(f'Blender version: {version_info}')
print(f'Objects in scene: {object_count}')
api_test_result = f'version_{version_info}_objects_{object_count}'
""",
            "message": f"Blender API test for {service_name}"
        }
        
        message_json = json.dumps(api_command)
        print(f"📤 Sending API test: {message_json[:100]}...")
        
        sock.sendall(message_json.encode('utf-8'))
        
        response_data = sock.recv(4096)
        response = json.loads(response_data.decode('utf-8'))
        
        print(f"📥 API Response: {response}")
        sock.close()
        
        print(f"✅ {service_name}: Blender API accessible")
        return True
        
    except Exception as e:
        print(f"❌ {service_name}: API test failed - {e}")
        return False


def main():
    """Run manual test example."""
    print("🧪 Manual Dual Service Test Example")
    print("="*50)
    print("This script assumes Blender is running with both services:")
    print("- BLD_Remote_MCP on port 6688")
    print("- BlenderAutoMCP on port 9876")
    print()
    print("To start Blender with both services:")
    print("export BLD_REMOTE_MCP_PORT=6688 BLD_REMOTE_MCP_START_NOW=1")
    print("export BLENDER_AUTO_MCP_SERVICE_PORT=9876 BLENDER_AUTO_MCP_START_NOW=1")
    print("/apps/blender-4.4.3-linux-x64/blender")
    print("="*50)
    
    # Test both services
    bld_remote_basic = test_service_simple(6688, "BLD_Remote_MCP")
    blender_auto_basic = test_service_simple(9876, "BlenderAutoMCP")
    
    if bld_remote_basic and blender_auto_basic:
        print("\n🔍 Both services responding, testing Blender API...")
        
        bld_remote_api = test_blender_api_simple(6688, "BLD_Remote_MCP")
        blender_auto_api = test_blender_api_simple(9876, "BlenderAutoMCP")
        
        # Results summary
        print("\n📊 Test Results Summary")
        print("-" * 30)
        print(f"BLD_Remote_MCP Basic:  {'✅ PASS' if bld_remote_basic else '❌ FAIL'}")
        print(f"BLD_Remote_MCP API:    {'✅ PASS' if bld_remote_api else '❌ FAIL'}")
        print(f"BlenderAutoMCP Basic:  {'✅ PASS' if blender_auto_basic else '❌ FAIL'}")
        print(f"BlenderAutoMCP API:    {'✅ PASS' if blender_auto_api else '❌ FAIL'}")
        
        all_passed = all([bld_remote_basic, bld_remote_api, blender_auto_basic, blender_auto_api])
        
        if all_passed:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Both services are working correctly")
        else:
            print("\n💥 SOME TESTS FAILED")
            print("❌ Check service status and configuration")
            
    else:
        print("\n💥 Basic connectivity failed")
        print("❌ Make sure both services are running in Blender")
    
    print("\n" + "="*50)


if __name__ == "__main__":
    main()