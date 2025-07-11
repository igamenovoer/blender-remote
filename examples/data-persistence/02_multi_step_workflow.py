#!/usr/bin/env python3
"""
Multi-Step Workflow Example

Demonstrates using persistence for complex multi-step operations.
This example simulates a 3-step animation workflow where each step
builds on the previous one's results.
"""

import json
import socket
import sys
import time


def send_command(command_type, params=None):
    """Send command to BLD Remote MCP service."""
    if params is None:
        params = {}
    
    command = {"type": command_type, "params": params}
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(('127.0.0.1', 6688))
        sock.send(json.dumps(command).encode())
        response = json.loads(sock.recv(8192).decode())
        return response
    finally:
        sock.close()


def step1_scene_setup():
    """Step 1: Set up scene and store configuration."""
    print("🎬 Step 1: Setting up scene...")
    
    # Create objects and store their names
    code = """
import bpy

# Clear existing mesh objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False, confirm=False)

# Create animation objects
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "AnimatedCube"

bpy.ops.mesh.primitive_sphere_add(location=(3, 0, 0))
sphere = bpy.context.active_object
sphere.name = "AnimatedSphere"

# Store scene configuration
import bld_remote
scene_config = {
    "objects": ["AnimatedCube", "AnimatedSphere"],
    "frame_start": 1,
    "frame_end": 120,
    "fps": 24,
    "setup_timestamp": bpy.context.scene.frame_current
}
bld_remote.persist.put_data("scene_config", scene_config)

print(f"Scene setup complete: {len(scene_config['objects'])} objects created")
"""
    
    response = send_command("execute_code", {"code": code})
    if response.get('status') != 'success':
        raise Exception(f"Step 1 failed: {response}")
    
    # Verify configuration was stored
    response = send_command("get_persist_data", {"key": "scene_config"})
    if response.get('status') == 'success' and response['result']['found']:
        config = response['result']['data']
        print(f"   ✅ Stored config for {len(config['objects'])} objects")
        print(f"   Animation: frames {config['frame_start']}-{config['frame_end']}")
    else:
        raise Exception("Failed to store scene configuration")


def step2_calculate_keyframes():
    """Step 2: Calculate keyframes based on scene configuration."""
    print("🎯 Step 2: Calculating keyframes...")
    
    # Get scene configuration from previous step
    response = send_command("get_persist_data", {"key": "scene_config"})
    if not (response.get('status') == 'success' and response['result']['found']):
        raise Exception("Scene configuration not found. Run step 1 first.")
    
    config = response['result']['data']
    
    code = f"""
import bpy
import bld_remote
import math

# Get configuration from persistence
config = bld_remote.persist.get_data("scene_config")
if not config:
    raise Exception("Scene configuration not found")

# Calculate keyframes for each object
keyframes = {{}}
for obj_name in config["objects"]:
    obj = bpy.data.objects.get(obj_name)
    if obj:
        # Calculate circular motion keyframes
        frames = []
        for frame in range(config["frame_start"], config["frame_end"] + 1, 10):
            angle = (frame / config["frame_end"]) * 2 * math.pi
            x = 3 * math.cos(angle)
            z = 2 * math.sin(angle)
            frames.append({{
                "frame": frame,
                "location": [x, 0, z],
                "rotation": [0, 0, angle]
            }})
        keyframes[obj_name] = frames

# Store calculated keyframes
bld_remote.persist.put_data("keyframes", keyframes)

print(f"Calculated keyframes for {{len(keyframes)}} objects")
for obj_name, frames in keyframes.items():
    print(f"  {{obj_name}}: {{len(frames)}} keyframes")
"""
    
    response = send_command("execute_code", {"code": code})
    if response.get('status') != 'success':
        raise Exception(f"Step 2 failed: {response}")
    
    # Verify keyframes were calculated
    response = send_command("get_persist_data", {"key": "keyframes"})
    if response.get('status') == 'success' and response['result']['found']:
        keyframes = response['result']['data']
        print(f"   ✅ Calculated keyframes for {len(keyframes)} objects")
        for obj_name, frames in keyframes.items():
            print(f"      {obj_name}: {len(frames)} keyframes")
    else:
        raise Exception("Failed to store keyframes")


def step3_apply_animation():
    """Step 3: Apply keyframes to objects."""
    print("🎭 Step 3: Applying animation...")
    
    # Get keyframes from previous step
    response = send_command("get_persist_data", {"key": "keyframes"})
    if not (response.get('status') == 'success' and response['result']['found']):
        raise Exception("Keyframes not found. Run step 2 first.")
    
    keyframes = response['result']['data']
    
    code = """
import bpy
import bld_remote

# Get keyframes from persistence
keyframes = bld_remote.persist.get_data("keyframes")
if not keyframes:
    raise Exception("Keyframes not found")

# Apply keyframes to objects
animation_stats = {}
for obj_name, frames in keyframes.items():
    obj = bpy.data.objects.get(obj_name)
    if obj:
        # Clear existing keyframes
        obj.animation_data_clear()
        
        # Apply new keyframes
        for frame_data in frames:
            frame = frame_data["frame"]
            location = frame_data["location"]
            rotation = frame_data["rotation"]
            
            # Set location
            obj.location = location
            obj.keyframe_insert(data_path="location", frame=frame)
            
            # Set rotation
            obj.rotation_euler = rotation
            obj.keyframe_insert(data_path="rotation_euler", frame=frame)
        
        animation_stats[obj_name] = len(frames)

# Store final results
result = {
    "animated_objects": list(animation_stats.keys()),
    "total_keyframes": sum(animation_stats.values()),
    "completion_timestamp": bpy.context.scene.frame_current
}
bld_remote.persist.put_data("animation_result", result)

print(f"Animation applied to {len(animation_stats)} objects")
print(f"Total keyframes: {result['total_keyframes']}")
"""
    
    response = send_command("execute_code", {"code": code})
    if response.get('status') != 'success':
        raise Exception(f"Step 3 failed: {response}")
    
    # Get final results
    response = send_command("get_persist_data", {"key": "animation_result"})
    if response.get('status') == 'success' and response['result']['found']:
        result = response['result']['data']
        print(f"   ✅ Animated {len(result['animated_objects'])} objects")
        print(f"   Total keyframes: {result['total_keyframes']}")
    else:
        raise Exception("Failed to get animation results")


def cleanup():
    """Clean up stored data."""
    print("🧹 Cleaning up stored data...")
    
    keys_to_remove = ["scene_config", "keyframes", "animation_result"]
    for key in keys_to_remove:
        response = send_command("remove_persist_data", {"key": key})
        if response.get('status') == 'success':
            removed = response['result']['removed']
            print(f"   {key}: {'✅ removed' if removed else '⚠️  not found'}")


def main():
    print("🚀 Multi-Step Workflow Example")
    print("=" * 50)
    print("This example demonstrates a 3-step animation workflow:")
    print("1. Scene setup and configuration storage")
    print("2. Keyframe calculation based on stored config")
    print("3. Animation application using calculated keyframes")
    print()
    
    try:
        # Run the complete workflow
        step1_scene_setup()
        print()
        
        step2_calculate_keyframes()
        print()
        
        step3_apply_animation()
        print()
        
        cleanup()
        print()
        
        print("✅ Multi-step workflow completed successfully!")
        print("🎬 Your objects should now be animated with circular motion")
        
    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        cleanup()  # Clean up even on failure
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())