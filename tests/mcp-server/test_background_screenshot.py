#!/usr/bin/env python3
"""
Test script for BLD Remote MCP get_viewport_screenshot functionality in background mode.
"""
import socket
import json
import time
import os
import tempfile
import subprocess
import signal
import sys


def test_background_screenshot():
    """Test the get_viewport_screenshot functionality in background mode."""
    print(f"[TESTING] Testing BLD Remote MCP get_viewport_screenshot in background mode...")
    print("=" * 70)

    # Create a background script that keeps Blender running
    background_script = """
import bpy
import bld_remote
import time
import sys

# Start the MCP service
print("Starting BLD Remote MCP service...")
bld_remote.start_mcp_service()
print("Service started, waiting for connections...")

# Keep the script running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Interrupted, shutting down...")
    bld_remote.stop_mcp_service()
    sys.exit(0)
"""

    # Write the background script to a temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(background_script)
        script_path = f.name

    # Start Blender in background with the script
    print(f"[ROCKET] Starting Blender in background mode with script...")
    env = os.environ.copy()
    env["BLD_REMOTE_MCP_PORT"] = "6688"
    env["BLD_REMOTE_MCP_START_NOW"] = "0"  # Don't auto-start, we'll start manually

    blender_process = subprocess.Popen(
        [
            "/apps/blender-4.4.3-linux-x64/blender",
            "--background",
            "--python",
            script_path,
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        # Wait for the service to start
        print("⏳ Waiting for service to start...")
        time.sleep(5)

        # Check if the process is still running
        if blender_process.poll() is not None:
            print("[FAIL] Blender process exited unexpectedly")
            stdout, stderr = blender_process.communicate()
            print(f"Output: {stdout}")
            return

        # Test the screenshot functionality
        print(f"[LINK] Testing viewport screenshot in background mode...")

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(("127.0.0.1", 6688))

            # Test viewport screenshot - should fail in background mode
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                temp_filepath = tmp.name

            command = {
                "type": "get_viewport_screenshot",
                "params": {"filepath": temp_filepath, "max_size": 400, "format": "png"},
            }

            print(f"[SEND] Sending get_viewport_screenshot command...")
            sock.sendall(json.dumps(command).encode("utf-8"))
            response_data = sock.recv(4096)
            response = json.loads(response_data.decode("utf-8"))

            print(f"📨 Response: {response}")

            if response.get("status") == "error":
                error_msg = response.get("message", "Unknown error")
                if "background mode" in error_msg.lower():
                    print(f"[PASS] Expected error for background mode: {error_msg}")
                    print(f"[PASS] Background mode limitation handled correctly!")
                else:
                    print(f"[FAIL] Unexpected error: {error_msg}")
            else:
                print(f"[FAIL] Expected error but got success: {response}")

            sock.close()

        except ConnectionRefusedError:
            print(f"[FAIL] Connection refused - service not running on port 6688")
        except Exception as e:
            print(f"[FAIL] Test failed: {e}")

        print(f"\n[SUCCESS] BACKGROUND MODE TEST COMPLETED!")

    finally:
        # Clean up
        print(f"🧹 Cleaning up...")
        if blender_process.poll() is None:
            blender_process.terminate()
            blender_process.wait(timeout=10)

        try:
            os.unlink(script_path)
        except:
            pass


if __name__ == "__main__":
    test_background_screenshot()
