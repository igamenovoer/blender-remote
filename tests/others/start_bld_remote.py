#!/usr/bin/env python3
"""
Start BLD_Remote_MCP service using BlenderAutoMCP as a control channel.
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

    print("✅ auto_mcp_remote client loaded successfully")
except ImportError as e:
    print(f"❌ Cannot import auto_mcp_remote: {e}")
    sys.exit(1)


def check_service(port, name):
    """Check if service is running on port."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(("127.0.0.1", port))
        sock.close()
        return result == 0
    except:
        return False


def main():
    print("🔄 Starting BLD_Remote_MCP service via BlenderAutoMCP...")

    # Check current status
    bld_remote_running = check_service(6688, "BLD_Remote_MCP")
    blender_auto_running = check_service(9876, "BlenderAutoMCP")

    print(
        f"BLD_Remote_MCP (6688): {'✅ RUNNING' if bld_remote_running else '❌ NOT RUNNING'}"
    )
    print(
        f"BlenderAutoMCP (9876): {'✅ RUNNING' if blender_auto_running else '❌ NOT RUNNING'}"
    )

    if bld_remote_running:
        print("✅ BLD_Remote_MCP is already running!")
        return

    if not blender_auto_running:
        print(
            "❌ BlenderAutoMCP is not running. Cannot use it to start BLD_Remote_MCP."
        )
        print("Please start Blender with both services:")
        print("export BLENDER_AUTO_MCP_SERVICE_PORT=9876 BLENDER_AUTO_MCP_START_NOW=1")
        print("export BLD_REMOTE_MCP_PORT=6688 BLD_REMOTE_MCP_START_NOW=1")
        print("/apps/blender-4.4.3-linux-x64/blender")
        return

    # Use BlenderAutoMCP to start our service
    print("🔌 Connecting to BlenderAutoMCP to start BLD_Remote_MCP...")

    try:
        client = BlenderMCPClient(port=9876)

        # Start our service
        start_code = """
import bld_remote
import os

# Set port for our service
os.environ['BLD_REMOTE_MCP_PORT'] = '6688'

# Check if already running
if bld_remote.is_mcp_service_up():
    print("BLD_Remote_MCP is already running")
    result = "already_running"
else:
    print("Starting BLD_Remote_MCP service...")
    try:
        bld_remote.start_mcp_service()
        time.sleep(2)  # Give it time to start
        
        if bld_remote.is_mcp_service_up():
            print("✅ BLD_Remote_MCP started successfully!")
            result = "started_successfully"
        else:
            print("❌ BLD_Remote_MCP failed to start")
            result = "failed_to_start"
    except Exception as e:
        print(f"❌ Error starting BLD_Remote_MCP: {e}")
        result = f"error: {e}"
"""

        print("📤 Sending start command...")
        response = client.execute_python(start_code)
        print(f"📥 Response: {response}")

        # Wait a moment and check if service started
        time.sleep(3)
        bld_remote_running = check_service(6688, "BLD_Remote_MCP")

        if bld_remote_running:
            print("🎉 SUCCESS! BLD_Remote_MCP is now running on port 6688")
        else:
            print("❌ FAILED: BLD_Remote_MCP is still not responding on port 6688")

        client.disconnect()

    except Exception as e:
        print(f"❌ Error communicating with BlenderAutoMCP: {e}")


if __name__ == "__main__":
    main()
