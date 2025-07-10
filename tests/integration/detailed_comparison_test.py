#!/usr/bin/env python3
"""
Detailed Comparison Test - Check actual response content and error handling
"""

import sys
import socket
import json
import time
from pathlib import Path

# Add auto_mcp_remote to path
sys.path.insert(0, str(Path(__file__).parent / "context" / "refcode"))

try:
    from auto_mcp_remote.blender_mcp_client import BlenderMCPClient

    print("✅ auto_mcp_remote client loaded")
except ImportError as e:
    print(f"❌ Cannot import auto_mcp_remote: {e}")
    sys.exit(1)


def test_raw_tcp(port, service_name, message):
    """Test raw TCP communication to see actual responses."""
    print(f"🔌 Testing {service_name} via raw TCP...")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect(("127.0.0.1", port))

        # Send JSON message
        json_msg = json.dumps(message)
        print(f"📤 Sending: {json_msg}")
        sock.sendall(json_msg.encode("utf-8"))

        # Receive response
        response_data = sock.recv(4096)
        response = json.loads(response_data.decode("utf-8"))

        sock.close()

        print(f"📥 Raw response: {response}")
        return response

    except Exception as e:
        print(f"❌ Raw TCP test failed: {e}")
        return None


def test_detailed_comparison():
    """Run detailed comparison tests."""
    print("🔍 DETAILED COMPARISON TEST")
    print("=" * 60)

    # Test 1: Simple calculation with detailed response
    print("\n📊 Test 1: Detailed Response Comparison")
    message = {
        "code": "calculation_result = 10 * 5 + 3; print(f'Calculation: {calculation_result}')",
        "message": "Detailed test calculation",
    }

    bld_response = test_raw_tcp(6688, "BLD_Remote_MCP", message)
    auto_response = test_raw_tcp(9876, "BlenderAutoMCP", message)

    print(f"\n📊 Response Structure Comparison:")
    if bld_response and auto_response:
        print(f"BLD_Remote_MCP fields: {list(bld_response.keys())}")
        print(f"BlenderAutoMCP fields: {list(auto_response.keys())}")

        # Check if both have similar structure
        common_fields = set(bld_response.keys()) & set(auto_response.keys())
        print(f"Common fields: {common_fields}")

        if "response" in common_fields:
            print(
                f"Both have 'response' field: BLD='{bld_response['response']}', Auto='{auto_response['response']}'"
            )

    # Test 2: Error handling comparison
    print("\n💥 Test 2: Error Handling Comparison")
    error_message = {
        "code": "this_will_cause_syntax_error <<<",
        "message": "Error handling test",
    }

    bld_error = test_raw_tcp(6688, "BLD_Remote_MCP", error_message)
    auto_error = test_raw_tcp(9876, "BlenderAutoMCP", error_message)

    print(f"\n📊 Error Response Comparison:")
    if bld_error and auto_error:
        print(f"BLD_Remote_MCP error response: {bld_error}")
        print(f"BlenderAutoMCP error response: {auto_error}")

    # Test 3: Blender API detailed test
    print("\n🎮 Test 3: Blender API Detailed Test")
    api_message = {
        "code": """
import bpy
version = bpy.app.version
version_string = bpy.app.version_string
object_count = len(bpy.data.objects)
scene_name = bpy.context.scene.name

result_info = {
    'version': version,
    'version_string': version_string,
    'objects': object_count,
    'scene': scene_name
}

print(f'Blender info: {result_info}')
api_result = result_info
""",
        "message": "Detailed Blender API test",
    }

    bld_api = test_raw_tcp(6688, "BLD_Remote_MCP", api_message)
    auto_api = test_raw_tcp(9876, "BlenderAutoMCP", api_message)

    print(f"\n📊 API Response Comparison:")
    if bld_api and auto_api:
        print(f"Both services provided API responses")
        print(f"BLD response status: {bld_api.get('response', 'no response field')}")
        print(f"Auto response status: {auto_api.get('response', 'no response field')}")


def main():
    print("🔍 BLD_Remote_MCP Detailed Comparison Test")
    print("=" * 60)

    # Verify both services are running
    def check_port(port, name):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(("127.0.0.1", port))
            sock.close()
            return result == 0
        except:
            return False

    bld_running = check_port(6688, "BLD_Remote_MCP")
    auto_running = check_port(9876, "BlenderAutoMCP")

    print(f"BLD_Remote_MCP (6688): {'✅ RUNNING' if bld_running else '❌ NOT RUNNING'}")
    print(
        f"BlenderAutoMCP (9876): {'✅ RUNNING' if auto_running else '❌ NOT RUNNING'}"
    )

    if not (bld_running and auto_running):
        print("❌ Both services must be running for comparison test")
        return False

    test_detailed_comparison()

    print(f"\n{'='*60}")
    print("✅ DETAILED COMPARISON COMPLETE")
    print("Check the output above to verify response structures match")
    print(f"{'='*60}")

    return True


if __name__ == "__main__":
    main()
