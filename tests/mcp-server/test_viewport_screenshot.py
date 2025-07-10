#!/usr/bin/env python3
"""
Test script for BLD Remote MCP get_viewport_screenshot functionality.
"""
import socket
import json
import time
import os
import tempfile


def test_viewport_screenshot(host="127.0.0.1", port=6688):
    """Test the get_viewport_screenshot functionality."""
    print(f"🧪 Testing BLD Remote MCP get_viewport_screenshot...")
    print("=" * 60)

    # Create a temporary file for the screenshot
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        temp_filepath = tmp.name

    try:
        print(f"🔗 Connecting to {host}:{port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        start_time = time.time()
        sock.connect((host, port))
        connect_time = time.time() - start_time
        print(f"✅ Connected successfully in {connect_time:.3f}s")

        # Test 1: Get viewport screenshot with all parameters
        print(f"\n📤 Test 1: Getting viewport screenshot...")
        print(f"   Temp file: {temp_filepath}")

        command = {
            "type": "get_viewport_screenshot",
            "params": {"filepath": temp_filepath, "max_size": 400, "format": "png"},
        }

        sock.sendall(json.dumps(command).encode("utf-8"))
        response_data = sock.recv(4096)
        response = json.loads(response_data.decode("utf-8"))

        print(f"   📨 Response: {response}")

        if response.get("status") == "success":
            result = response.get("result", {})
            print(f"   ✅ Screenshot captured successfully!")
            print(
                f"   📐 Dimensions: {result.get('width', 'unknown')}x{result.get('height', 'unknown')}"
            )
            print(f"   📁 File: {result.get('filepath', 'unknown')}")

            # Check if file exists
            if os.path.exists(temp_filepath):
                file_size = os.path.getsize(temp_filepath)
                print(f"   📂 File size: {file_size} bytes")
                print(f"   ✅ Screenshot file created successfully!")
            else:
                print(f"   ❌ Screenshot file not found!")

        elif response.get("status") == "error":
            error_msg = response.get("message", "Unknown error")
            print(f"   ❌ Error: {error_msg}")

            # Check if this is expected background mode error
            if "background mode" in error_msg.lower():
                print(f"   ℹ️ This is expected behavior in background mode")
            else:
                print(f"   ❌ Unexpected error occurred")
        else:
            print(f"   ❌ Unexpected response format: {response}")

        # Test 2: Get viewport screenshot with minimal parameters
        print(f"\n📤 Test 2: Getting viewport screenshot with minimal params...")

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp2:
            temp_filepath2 = tmp2.name

        command2 = {
            "type": "get_viewport_screenshot",
            "params": {"filepath": temp_filepath2},
        }

        sock.sendall(json.dumps(command2).encode("utf-8"))
        response_data2 = sock.recv(4096)
        response2 = json.loads(response_data2.decode("utf-8"))

        print(f"   📨 Response: {response2}")

        if response2.get("status") == "success":
            print(f"   ✅ Screenshot with default params successful!")
        else:
            print(
                f"   ❌ Screenshot with default params failed: {response2.get('message', 'Unknown error')}"
            )

        # Test 3: Error handling - no filepath
        print(f"\n📤 Test 3: Error handling (no filepath)...")

        command3 = {"type": "get_viewport_screenshot", "params": {}}

        sock.sendall(json.dumps(command3).encode("utf-8"))
        response_data3 = sock.recv(4096)
        response3 = json.loads(response_data3.decode("utf-8"))

        print(f"   📨 Response: {response3}")

        if response3.get("status") == "error":
            print(f"   ✅ Error handling works correctly: {response3.get('message')}")
        else:
            print(f"   ❌ Expected error but got: {response3}")

        print(f"\n🔒 Closing connection...")
        sock.close()
        print(f"   ✅ Connection closed successfully")

        # Clean up temp files
        try:
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)
            if os.path.exists(temp_filepath2):
                os.unlink(temp_filepath2)
        except Exception as e:
            print(f"   ⚠️ Warning: Could not clean up temp files: {e}")

        print(f"\n🎉 VIEWPORT SCREENSHOT TEST COMPLETED!")

    except ConnectionRefusedError:
        print(f"❌ Connection refused - is BLD Remote MCP running on port {port}?")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # Clean up temp files
        try:
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)
        except:
            pass


if __name__ == "__main__":
    test_viewport_screenshot()
