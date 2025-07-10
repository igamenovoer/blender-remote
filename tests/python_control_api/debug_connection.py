#!/usr/bin/env python3
"""
Debug connection to BLD Remote MCP service.
"""

import socket
import json
import time


def test_raw_connection():
    """Test raw socket connection to BLD Remote MCP service."""
    print("Testing raw socket connection to BLD Remote MCP service...")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)

    try:
        sock.connect(("127.0.0.1", 6688))
        print("Connected successfully")

        # Test basic scene info command
        command = {"type": "get_scene_info", "params": {}}
        print(f"Sending command: {command}")
        sock.sendall(json.dumps(command).encode("utf-8"))

        # Try to receive response
        response = sock.recv(8192)
        print(f"Response length: {len(response)}")
        if response:
            print(f"Response: {response.decode('utf-8')}")
            return True
        else:
            print("No response received")
            return False

    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        sock.close()


def test_execute_code():
    """Test execute code command."""
    print("\nTesting execute code command...")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)

    try:
        sock.connect(("127.0.0.1", 6688))
        print("Connected successfully")

        # Test execute code command
        command = {
            "type": "execute_code",
            "params": {
                "code": 'import bpy; print("Hello from Blender!"); result = "success"'
            },
        }
        print(f"Sending command: {command}")
        sock.sendall(json.dumps(command).encode("utf-8"))

        # Try to receive response
        response = sock.recv(8192)
        print(f"Response length: {len(response)}")
        if response:
            print(f"Response: {response.decode('utf-8')}")
            return True
        else:
            print("No response received")
            return False

    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        sock.close()


if __name__ == "__main__":
    print("=" * 60)
    print("BLD Remote MCP Connection Debug")
    print("=" * 60)

    result1 = test_raw_connection()
    result2 = test_execute_code()

    print("\n" + "=" * 60)
    print(
        f"Results: get_scene_info={'PASS' if result1 else 'FAIL'}, execute_code={'PASS' if result2 else 'FAIL'}"
    )
    print("=" * 60)
