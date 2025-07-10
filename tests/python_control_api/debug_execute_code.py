#!/usr/bin/env python3
"""
Debug execute_code command specifically.
"""

import socket
import json
import time


def test_execute_code_raw():
    """Test execute_code with raw socket."""
    print("Testing execute_code with raw socket...")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(15)  # Longer timeout for code execution

    try:
        sock.connect(("127.0.0.1", 6688))
        print("Connected successfully")

        # Test execute code command with same code as client test
        code = """
import bpy
print("Testing from client!")
objects = [obj.name for obj in bpy.context.scene.objects]
print(f"Objects: {objects}")
result = f"Found {len(objects)} objects"
"""

        command = {"type": "execute_code", "params": {"code": code}}
        print(f"Sending command...")
        sock.sendall(json.dumps(command).encode("utf-8"))

        # Try to receive response
        print("Waiting for response...")
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


def test_simple_execute_code():
    """Test simple execute_code command."""
    print("\nTesting simple execute_code...")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)

    try:
        sock.connect(("127.0.0.1", 6688))
        print("Connected successfully")

        # Simple test
        command = {
            "type": "execute_code",
            "params": {"code": 'print("Hello"); result = "simple test"'},
        }
        print(f"Sending simple command...")
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
    print("Execute Code Debug")
    print("=" * 60)

    result1 = test_simple_execute_code()
    result2 = test_execute_code_raw()

    print("\n" + "=" * 60)
    print(
        f"Results: simple={'PASS' if result1 else 'FAIL'}, complex={'PASS' if result2 else 'FAIL'}"
    )
    print("=" * 60)
