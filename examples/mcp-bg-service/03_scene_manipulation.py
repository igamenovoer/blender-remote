#!/usr/bin/env python3
"""
Scene Manipulation Example

This example demonstrates creating and manipulating Blender scenes remotely
using the BLD Remote MCP background service.

Prerequisites:
- BLD Remote MCP service running
- Blender with scene manipulation capabilities

Usage:
    python3 03_scene_manipulation.py
    python3 03_scene_manipulation.py --port 9999 --keep-existing
"""

import sys
import os
import argparse
import time

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import blender_connection, check_service_health, batch_execute

def clear_scene(client):
    """Clear the current scene of all mesh objects."""
    print("   🗑️ Clearing existing scene...")
    
    clear_code = '''
import bpy

# Select all objects
bpy.ops.object.select_all(action='SELECT')

# Delete selected objects
bpy.ops.object.delete(use_global=False, confirm=False)

print(f"Scene cleared. Remaining objects: {len(bpy.data.objects)}")
    '''
    
    response = client.execute_code(clear_code, "Clear scene")
    return response

def create_basic_geometry(client):
    """Create basic geometric objects in the scene."""
    print("   📦 Creating basic geometry...")
    
    # Create objects one by one with proper spacing
    objects = [
        ("Cube", "bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))"),
        ("Sphere", "bpy.ops.mesh.primitive_uv_sphere_add(location=(3, 0, 0))"),
        ("Cylinder", "bpy.ops.mesh.primitive_cylinder_add(location=(6, 0, 0))"),
        ("Cone", "bpy.ops.mesh.primitive_cone_add(location=(0, 3, 0))"),
        ("Torus", "bpy.ops.mesh.primitive_torus_add(location=(3, 3, 0))"),
        ("Monkey", "bpy.ops.mesh.primitive_monkey_add(location=(6, 3, 0))")
    ]
    
    for name, code in objects:
        response = client.execute_code(code, f"Create {name}")
        print(f"      ✓ Created {name}")
        time.sleep(0.1)  # Small delay between objects
    
    # Name the objects properly
    naming_code = '''
import bpy

# Get all mesh objects and rename them
mesh_objects = [obj for obj in bpy.data.objects if obj.type == 'MESH']
names = ['MCP_Cube', 'MCP_Sphere', 'MCP_Cylinder', 'MCP_Cone', 'MCP_Torus', 'MCP_Monkey']

for i, obj in enumerate(mesh_objects):
    if i < len(names):
        obj.name = names[i]
        print(f"Renamed object to {obj.name}")

print(f"Created {len(mesh_objects)} geometric objects")
    '''
    
    response = client.execute_code(naming_code, "Name objects")
    return response

def create_materials(client):
    """Create and apply materials to objects."""
    print("   🎨 Creating materials...")
    
    material_code = '''
import bpy

# Define materials with different colors
materials_data = [
    ("MCP_Red", (1.0, 0.2, 0.2, 1.0)),
    ("MCP_Green", (0.2, 1.0, 0.2, 1.0)),
    ("MCP_Blue", (0.2, 0.2, 1.0, 1.0)),
    ("MCP_Yellow", (1.0, 1.0, 0.2, 1.0)),
    ("MCP_Purple", (1.0, 0.2, 1.0, 1.0)),
    ("MCP_Orange", (1.0, 0.6, 0.2, 1.0))
]

# Create materials
created_materials = []
for name, color in materials_data:
    if name not in bpy.data.materials:
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        
        # Set the base color
        if mat.node_tree:
            nodes = mat.node_tree.nodes
            principled = nodes.get('Principled BSDF')
            if principled:
                principled.inputs['Base Color'].default_value = color
        
        created_materials.append(mat.name)
        print(f"Created material: {name}")
    else:
        print(f"Material already exists: {name}")

print(f"Total materials available: {len(bpy.data.materials)}")
    '''
    
    response = client.execute_code(material_code, "Create materials")
    
    # Apply materials to objects
    print("   🖌️ Applying materials to objects...")
    
    apply_code = '''
import bpy

# Get mesh objects and materials
mesh_objects = [obj for obj in bpy.data.objects if obj.type == 'MESH']
material_names = ['MCP_Red', 'MCP_Green', 'MCP_Blue', 'MCP_Yellow', 'MCP_Purple', 'MCP_Orange']

# Apply materials to objects
for i, obj in enumerate(mesh_objects):
    if i < len(material_names):
        mat_name = material_names[i]
        mat = bpy.data.materials.get(mat_name)
        
        if mat and obj.data:
            # Clear existing materials
            obj.data.materials.clear()
            # Apply new material
            obj.data.materials.append(mat)
            print(f"Applied {mat_name} to {obj.name}")

print("Material application complete")
    '''
    
    response = client.execute_code(apply_code, "Apply materials")
    return response

def setup_lighting(client):
    """Set up lighting for the scene."""
    print("   💡 Setting up lighting...")
    
    lighting_code = '''
import bpy
import mathutils

# Remove default light if it exists
if "Light" in bpy.data.objects:
    bpy.data.objects.remove(bpy.data.objects["Light"], do_unlink=True)

# Add main sun light
bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
sun = bpy.context.active_object
sun.name = "MCP_Sun"
sun.data.energy = 3.0

# Add fill light
bpy.ops.object.light_add(type='AREA', location=(-5, -5, 8))
area = bpy.context.active_object
area.name = "MCP_Fill"
area.data.energy = 2.0
area.data.size = 4.0

# Add accent light
bpy.ops.object.light_add(type='SPOT', location=(8, -3, 6))
spot = bpy.context.active_object
spot.name = "MCP_Accent"
spot.data.energy = 50.0
spot.data.spot_size = 1.2
spot.data.spot_blend = 0.3

# Point spot light at center
target = mathutils.Vector((3, 1.5, 0))
direction = target - spot.location
spot.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

print(f"Created lighting setup with {len([obj for obj in bpy.data.objects if obj.type == 'LIGHT'])} lights")
    '''
    
    response = client.execute_code(lighting_code, "Setup lighting")
    return response

def setup_camera(client):
    """Set up camera for the scene."""
    print("   📷 Setting up camera...")
    
    camera_code = '''
import bpy
import mathutils

# Remove default camera if it exists
if "Camera" in bpy.data.objects:
    bpy.data.objects.remove(bpy.data.objects["Camera"], do_unlink=True)

# Add new camera with better position
bpy.ops.object.camera_add(location=(12, -8, 6))
camera = bpy.context.active_object
camera.name = "MCP_Camera"

# Point camera at the center of our objects
target = mathutils.Vector((3, 1.5, 0))
direction = target - camera.location
camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

# Set as active camera
bpy.context.scene.camera = camera

# Adjust camera settings
camera.data.lens = 35  # 35mm lens
camera.data.clip_start = 0.1
camera.data.clip_end = 1000

print(f"Camera setup complete: {camera.name} at {camera.location}")
print(f"Camera focal length: {camera.data.lens}mm")
    '''
    
    response = client.execute_code(camera_code, "Setup camera")
    return response

def scene_statistics(client):
    """Get detailed scene statistics."""
    print("   📊 Getting scene statistics...")
    
    stats_code = '''
import bpy

# Count different object types
object_types = {}
for obj in bpy.data.objects:
    obj_type = obj.type
    object_types[obj_type] = object_types.get(obj_type, 0) + 1

print("=== Scene Statistics ===")
print(f"Scene name: {bpy.context.scene.name}")
print(f"Total objects: {len(bpy.data.objects)}")

for obj_type, count in sorted(object_types.items()):
    print(f"  {obj_type}: {count}")

print(f"Materials: {len(bpy.data.materials)}")
print(f"Meshes: {len(bpy.data.meshes)}")
print(f"Lights: {len(bpy.data.lights)}")
print(f"Cameras: {len(bpy.data.cameras)}")

# List all objects with their locations
print("\\n=== Object Details ===")
for obj in bpy.data.objects:
    loc = obj.location
    print(f"{obj.name} ({obj.type}): ({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f})")

# Check active camera
if bpy.context.scene.camera:
    print(f"\\nActive camera: {bpy.context.scene.camera.name}")
else:
    print("\\nNo active camera set")
    '''
    
    response = client.execute_code(stats_code, "Scene statistics")
    return response

def animate_objects(client):
    """Add simple animation to the objects."""
    print("   🎬 Adding animation...")
    
    animation_code = '''
import bpy
import math

# Set frame range
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 120

# Get mesh objects
mesh_objects = [obj for obj in bpy.data.objects if obj.type == 'MESH']

print(f"Adding rotation animation to {len(mesh_objects)} objects")

for i, obj in enumerate(mesh_objects):
    # Clear existing keyframes
    obj.animation_data_clear()
    
    # Set rotation animation
    obj.rotation_euler = (0, 0, 0)
    obj.keyframe_insert(data_path="rotation_euler", frame=1)
    
    # Different rotation speeds for each object
    rotation_speed = (i + 1) * 0.5
    obj.rotation_euler = (0, 0, rotation_speed * 2 * math.pi)
    obj.keyframe_insert(data_path="rotation_euler", frame=120)
    
    # Set interpolation to linear
    if obj.animation_data and obj.animation_data.action:
        for fcurve in obj.animation_data.action.fcurves:
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation = 'LINEAR'
    
    print(f"  Animated {obj.name} with speed {rotation_speed:.1f}")

print("Animation setup complete!")
print(f"Frame range: {scene.frame_start} - {scene.frame_end}")
    '''
    
    response = client.execute_code(animation_code, "Add animation")
    return response

def main():
    parser = argparse.ArgumentParser(description='Demonstrate scene manipulation via BLD Remote MCP')
    parser.add_argument('--port', type=int, default=6688,
                        help='Service port (default: 6688)')
    parser.add_argument('--keep-existing', action='store_true',
                        help='Keep existing objects in scene')
    parser.add_argument('--no-animation', action='store_true',
                        help='Skip animation setup')
    parser.add_argument('--simple', action='store_true',
                        help='Create simple scene only')
    
    args = parser.parse_args()
    
    print("BLD Remote MCP - Scene Manipulation Example")
    print("=" * 50)
    
    # Check service availability
    print("🔍 Checking service availability...")
    health = check_service_health(port=args.port)
    if not health["responsive"]:
        print("❌ Service not available. Start with: python3 start_service.py")
        sys.exit(1)
    
    print("✅ Service is available")
    
    try:
        with blender_connection(port=args.port) as client:
            
            print("\\n🏗️ Building scene...")
            
            # Clear scene unless keeping existing
            if not args.keep_existing:
                clear_scene(client)
            
            # Create geometry
            create_basic_geometry(client)
            
            if not args.simple:
                # Create and apply materials
                create_materials(client)
                
                # Set up lighting
                setup_lighting(client)
                
                # Set up camera
                setup_camera(client)
                
                # Add animation
                if not args.no_animation:
                    animate_objects(client)
            
            # Show final statistics
            print("\\n📈 Final scene information:")
            scene_statistics(client)
            
    except Exception as e:
        print(f"❌ Scene manipulation failed: {e}")
        sys.exit(1)
    
    print("\\n🎉 Scene manipulation completed successfully!")
    print("\\nThe scene now contains:")
    print("  • 6 geometric objects with materials")
    if not args.simple:
        print("  • 3-point lighting setup")
        print("  • Positioned camera")
        if not args.no_animation:
            print("  • Rotation animations")
    
    print("\\nNext steps:")
    print("  • View in Blender GUI to see the results")
    print("  • Try: python3 07_render_automation.py")
    print("  • Try: python3 04_batch_processing.py")

if __name__ == '__main__':
    main()