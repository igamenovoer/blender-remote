#!/usr/bin/env python3
"""
Test script to verify that numpy imports work in BLD Remote MCP code execution.
"""
import socket
import json
import time


def test_numpy_execution(host="127.0.0.1", port=6688):
    """Test that numpy imports and execution work properly."""
    print(f"[TESTING] Testing BLD Remote MCP numpy code execution...")
    print("=" * 60)

    # The problematic code from the user that was failing
    test_code = '''import bpy
import numpy as np
from mathutils import Vector, Matrix

def create_camera_complete_test():
    """Complete tested example of camera creation with numpy"""
    # Clear existing cameras (optional)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='CAMERA')
    bpy.ops.object.delete(use_global=False)
    
    # Define camera parameters using numpy
    location = np.array([8, -8, 6], dtype=np.float64)
    target = np.array([0, 0, 0], dtype=np.float64)  # Look at cube
    up_vector = np.array([0, 0, 1], dtype=np.float64)
    
    # Calculate view direction
    view_direction = target - location
    view_direction = view_direction / np.linalg.norm(view_direction)
    up_vector = up_vector / np.linalg.norm(up_vector)
    
    # Create camera
    camera_data = bpy.data.cameras.new(name="TestCamera")
    camera_object = bpy.data.objects.new("TestCamera", camera_data)
    bpy.context.scene.collection.objects.link(camera_object)
    camera_object.location = Vector(location)
    
    # Calculate orthonormal basis using numpy
    camera_z = -view_direction  # Camera looks down -Z
    camera_x = np.cross(up_vector, camera_z)
    camera_x = camera_x / np.linalg.norm(camera_x)
    camera_y = np.cross(camera_z, camera_x)
    
    # Create and apply rotation matrix
    rotation_matrix = Matrix([
        [camera_x[0], camera_y[0], camera_z[0], 0],
        [camera_x[1], camera_y[1], camera_z[1], 0],
        [camera_x[2], camera_y[2], camera_z[2], 0],
        [0, 0, 0, 1]
    ])
    
    camera_object.matrix_world = Matrix.Translation(Vector(location)) @ rotation_matrix
    
    # Set as active camera and configure render
    bpy.context.scene.camera = camera_object
    render = bpy.context.scene.render
    render.resolution_x = 800
    render.resolution_y = 600
    render.filepath = "/tmp/test_camera_render.png"
    render.image_settings.file_format = 'PNG'
    
    # Render the image
    bpy.ops.render.render(write_still=True)
    
    print(f"✓ Camera created and image rendered successfully!")
    return camera_object

# Execute the test
camera = create_camera_complete_test()
print(f"Final test complete! Camera: {camera.name} at {camera.location}")
'''

    try:
        print(f"[LINK] Connecting to {host}:{port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        start_time = time.time()
        sock.connect((host, port))
        connect_time = time.time() - start_time
        print(f"[PASS] Connected successfully in {connect_time:.3f}s")

        # Test 1: Using new command-based interface
        print(f"\n[SEND] Test 1: Testing numpy code execution via execute_code command...")

        command = {"type": "execute_code", "params": {"code": test_code}}

        sock.sendall(json.dumps(command).encode("utf-8"))
        response_data = sock.recv(8192)  # Larger buffer for potential error messages
        response = json.loads(response_data.decode("utf-8"))

        print(f"   📨 Response: {response}")

        if response.get("status") == "success":
            print(f"   [PASS] Code executed successfully via command interface!")
            result = response.get("result", {})
            print(f"   [INFO] Result: {result}")
        else:
            error_msg = response.get("message", "Unknown error")
            print(f"   [FAIL] Error: {error_msg}")

        # Test 2: Using legacy code interface
        print(f"\n[SEND] Test 2: Testing numpy code execution via legacy code interface...")

        legacy_message = {"code": test_code}

        sock.sendall(json.dumps(legacy_message).encode("utf-8"))
        response_data2 = sock.recv(8192)
        response2 = json.loads(response_data2.decode("utf-8"))

        print(f"   📨 Response: {response2}")

        if response2.get("response") == "OK":
            print(f"   [PASS] Code executed successfully via legacy interface!")
            print(f"   [INFO] Message: {response2.get('message', 'No message')}")
        else:
            print(f"   [FAIL] Error: {response2.get('message', 'Unknown error')}")

        # Test 3: Simple numpy test
        print(f"\n[SEND] Test 3: Simple numpy import test...")

        simple_test = """
import numpy as np
print("NumPy version:", np.__version__)
arr = np.array([1, 2, 3, 4, 5])
print("Array:", arr)
print("Array sum:", np.sum(arr))
print("[PASS] NumPy import and basic operations work!")
"""

        simple_command = {"type": "execute_code", "params": {"code": simple_test}}

        sock.sendall(json.dumps(simple_command).encode("utf-8"))
        response_data3 = sock.recv(4096)
        response3 = json.loads(response_data3.decode("utf-8"))

        print(f"   📨 Response: {response3}")

        if response3.get("status") == "success":
            print(f"   [PASS] Simple numpy test passed!")
        else:
            print(
                f"   [FAIL] Simple numpy test failed: {response3.get('message', 'Unknown error')}"
            )

        print(f"\n[SECURE] Closing connection...")
        sock.close()
        print(f"   [PASS] Connection closed successfully")

        print(f"\n[SUCCESS] NUMPY EXECUTION TEST COMPLETED!")

    except ConnectionRefusedError:
        print(f"[FAIL] Connection refused - is BLD Remote MCP running on port {port}?")
        print(f"   Try starting Blender with the service first")
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_numpy_execution()
