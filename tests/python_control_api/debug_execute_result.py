#!/usr/bin/env python3
"""
Debug execute_code result format.
"""

import socket
import json


def test_execute_code_result_format():
    """Test what execute_code actually returns."""
    print("Testing execute_code result format...")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)

    try:
        sock.connect(("127.0.0.1", 6688))
        print("Connected successfully")

        # Test code that should produce output
        code = """
import bpy
print("Hello from Blender!")
print(f"Blender version: {bpy.app.version}")
scene_objects = [obj.name for obj in bpy.context.scene.objects]
print(f"Scene objects: {scene_objects}")
result = f"Found {len(scene_objects)} objects: {scene_objects}"
"""

        command = {"type": "execute_code", "params": {"code": code}}
        print("Sending code execution command...")
        sock.sendall(json.dumps(command).encode("utf-8"))

        # Receive response
        response_data = sock.recv(8192)
        response = json.loads(response_data.decode("utf-8"))

        print("\nFull response structure:")
        print(json.dumps(response, indent=2))

        # Analyze the structure
        print(f"\nResponse status: {response.get('status')}")
        print(f"Response result type: {type(response.get('result'))}")
        print(f"Response result: {response.get('result')}")

        result_section = response.get("result", {})
        if isinstance(result_section, dict):
            print(f"\nResult section keys: {list(result_section.keys())}")
            for key, value in result_section.items():
                print(f"  {key}: {value}")

        return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        sock.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Execute Code Result Format Debug")
    print("=" * 60)

    test_execute_code_result_format()

    print("=" * 60)
