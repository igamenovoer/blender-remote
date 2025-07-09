#!/usr/bin/env python3
"""
Test the original failing numpy code that the user reported.
"""
import socket
import json
import time


def test_original_failing_code(host="127.0.0.1", port=6688):
    """Test the exact code that was failing before."""
    print(f"🧪 Testing original failing numpy code...")
    print("=" * 60)
    
    # The exact code from the user that was failing
    original_code = '''import bpy
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
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        print(f"✅ Connected to {host}:{port}")
        
        # Test the exact failing code
        print(f"\n📤 Testing original failing code...")
        
        command = {
            "type": "execute_code",
            "params": {
                "code": original_code
            }
        }
        
        print(f"📤 Sending code execution command...")
        sock.sendall(json.dumps(command).encode('utf-8'))
        print(f"⏳ Waiting for response...")
        
        response_data = sock.recv(8192)
        response = json.loads(response_data.decode('utf-8'))
        
        print(f"📨 Response: {response}")
        
        if response.get("status") == "success":
            print(f"✅ SUCCESS! The original failing code now works!")
            print(f"📋 Result: {response.get('result', {})}")
        else:
            error_msg = response.get("message", "Unknown error")
            print(f"❌ Still failing: {error_msg}")
        
        sock.close()
        print(f"🔒 Connection closed")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_original_failing_code()