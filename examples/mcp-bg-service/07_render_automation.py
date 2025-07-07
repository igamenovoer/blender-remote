#!/usr/bin/env python3
"""
Render Automation Example

This example demonstrates automated rendering workflows using the
BLD Remote MCP background service for batch rendering operations.

Prerequisites:
- BLD Remote MCP service running
- Blender with rendering capabilities
- Sufficient disk space for output files

Usage:
    python3 07_render_automation.py
    python3 07_render_automation.py --output-dir ./renders --format PNG
"""

import sys
import os
import argparse
import time
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import blender_connection, check_service_health

def setup_render_scene(client, output_dir: str):
    """Set up a scene for rendering demonstrations."""
    print("🎬 Setting up render scene...")
    
    scene_code = f'''
import bpy
import mathutils
import os

# Clear existing scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False, confirm=False)

print("Creating render scene...")

# Create main subject - a monkey head
bpy.ops.mesh.primitive_monkey_add(location=(0, 0, 1))
suzanne = bpy.context.active_object
suzanne.name = "Suzanne"

# Add some supporting geometry
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "Ground"

bpy.ops.mesh.primitive_cube_add(size=0.5, location=(-2, -2, 0.25))
cube1 = bpy.context.active_object
cube1.name = "Cube1"

bpy.ops.mesh.primitive_cube_add(size=0.3, location=(2, -1, 0.15))
cube2 = bpy.context.active_object
cube2.name = "Cube2"

# Create materials
# Material for Suzanne
suzanne_mat = bpy.data.materials.new(name="Suzanne_Material")
suzanne_mat.use_nodes = True
suzanne_nodes = suzanne_mat.node_tree.nodes
suzanne_principled = suzanne_nodes.get('Principled BSDF')
if suzanne_principled:
    suzanne_principled.inputs['Base Color'].default_value = (0.8, 0.3, 0.1, 1.0)
    suzanne_principled.inputs['Roughness'].default_value = 0.3
    suzanne_principled.inputs['Metallic'].default_value = 0.2

suzanne.data.materials.append(suzanne_mat)

# Material for ground
ground_mat = bpy.data.materials.new(name="Ground_Material")
ground_mat.use_nodes = True
ground_nodes = ground_mat.node_tree.nodes
ground_principled = ground_nodes.get('Principled BSDF')
if ground_principled:
    ground_principled.inputs['Base Color'].default_value = (0.6, 0.6, 0.7, 1.0)
    ground_principled.inputs['Roughness'].default_value = 0.8

ground.data.materials.append(ground_mat)

# Materials for cubes
cube1_mat = bpy.data.materials.new(name="Cube1_Material")
cube1_mat.use_nodes = True
cube1_nodes = cube1_mat.node_tree.nodes
cube1_principled = cube1_nodes.get('Principled BSDF')
if cube1_principled:
    cube1_principled.inputs['Base Color'].default_value = (0.2, 0.8, 0.2, 1.0)
    cube1_principled.inputs['Roughness'].default_value = 0.1
    cube1_principled.inputs['Metallic'].default_value = 0.8

cube1.data.materials.append(cube1_mat)

cube2_mat = bpy.data.materials.new(name="Cube2_Material")
cube2_mat.use_nodes = True
cube2_nodes = cube2_mat.node_tree.nodes
cube2_principled = cube2_nodes.get('Principled BSDF')
if cube2_principled:
    cube2_principled.inputs['Base Color'].default_value = (0.2, 0.2, 0.8, 1.0)
    cube2_principled.inputs['Roughness'].default_value = 0.05
    cube2_principled.inputs['Metallic'].default_value = 1.0

cube2.data.materials.append(cube2_mat)

# Set up lighting
# Remove default light
if "Light" in bpy.data.objects:
    bpy.data.objects.remove(bpy.data.objects["Light"], do_unlink=True)

# Add main light
bpy.ops.object.light_add(type='SUN', location=(4, 2, 8))
sun = bpy.context.active_object
sun.name = "Main_Light"
sun.data.energy = 3.0
sun.rotation_euler = (0.3, 0.5, 0)

# Add fill light
bpy.ops.object.light_add(type='AREA', location=(-3, 3, 5))
area = bpy.context.active_object
area.name = "Fill_Light"
area.data.energy = 2.0
area.data.size = 2.0

# Set up camera
if "Camera" in bpy.data.objects:
    bpy.data.objects.remove(bpy.data.objects["Camera"], do_unlink=True)

bpy.ops.object.camera_add(location=(5, -4, 3))
camera = bpy.context.active_object
camera.name = "Render_Camera"

# Point camera at Suzanne
target = mathutils.Vector((0, 0, 1))
direction = target - camera.location
camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

# Set as active camera
bpy.context.scene.camera = camera

# Set up render settings
scene = bpy.context.scene
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 50  # 50% for faster rendering

# Set output path
output_path = r"{output_dir}"
os.makedirs(output_path, exist_ok=True)
scene.render.filepath = os.path.join(output_path, "render_")

print(f"Render scene setup complete!")
print(f"Output directory: {{output_path}}")
print(f"Resolution: {{scene.render.resolution_x}}x{{scene.render.resolution_y}} ({{scene.render.resolution_percentage}}%)")
    '''
    
    response = client.execute_code(scene_code, "Setup render scene")
    return response

def configure_render_settings(client, render_engine: str = 'EEVEE', samples: int = 64):
    """Configure render engine and quality settings."""
    print(f"⚙️ Configuring render settings (Engine: {render_engine}, Samples: {samples})...")
    
    config_code = f'''
import bpy

scene = bpy.context.scene

# Set render engine
scene.render.engine = '{render_engine}'

if scene.render.engine == 'CYCLES':
    # Cycles settings
    scene.cycles.samples = {samples}
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    
    # Use GPU if available
    prefs = bpy.context.preferences
    cprefs = prefs.addons['cycles'].preferences
    
    # Enable GPU devices
    cprefs.refresh_devices()
    for device in cprefs.devices:
        if device.type == 'CUDA' or device.type == 'OPENCL' or device.type == 'OPTIX':
            device.use = True
            print(f"Enabled GPU device: {{device.name}} ({{device.type}})")
    
    scene.cycles.device = 'GPU'
    
elif scene.render.engine == 'EEVEE':
    # EEVEE settings
    scene.eevee.taa_render_samples = {samples}
    scene.eevee.use_ssr = True
    scene.eevee.use_ssr_refraction = True
    scene.eevee.use_bloom = True
    scene.eevee.use_volumetric_lighting = True

# Color management
scene.view_settings.view_transform = 'Filmic'
scene.view_settings.look = 'Medium High Contrast'

print(f"Render engine: {{scene.render.engine}}")
if scene.render.engine == 'CYCLES':
    print(f"Cycles samples: {{scene.cycles.samples}}")
elif scene.render.engine == 'EEVEE':
    print(f"EEVEE samples: {{scene.eevee.taa_render_samples}}")
    '''
    
    response = client.execute_code(config_code, "Configure render settings")
    return response

def render_single_frame(client, frame: int, output_name: str = ""):
    """Render a single frame."""
    print(f"🖼️ Rendering frame {frame}...")
    
    render_code = f'''
import bpy
import os
import time

scene = bpy.context.scene

# Set frame
scene.frame_set({frame})

# Set output filename
if "{output_name}":
    base_path = scene.render.filepath
    scene.render.filepath = os.path.join(os.path.dirname(base_path), "{output_name}_frame_{frame:04d}")

print(f"Rendering frame {frame}...")
print(f"Output: {{scene.render.filepath}}")

start_time = time.time()

# Render
bpy.ops.render.render(write_still=True)

end_time = time.time()
render_time = end_time - start_time

print(f"Frame {frame} rendered in {{render_time:.2f}} seconds")
print(f"Saved to: {{scene.render.filepath}}")
    '''
    
    response = client.execute_code(render_code, f"Render frame {frame}")
    return response

def render_animation_sequence(client, start_frame: int = 1, end_frame: int = 10, 
                            output_name: str = "animation"):
    """Render an animation sequence."""
    print(f"🎞️ Rendering animation sequence (frames {start_frame}-{end_frame})...")
    
    # First, set up simple animation
    animation_code = f'''
import bpy
import math

scene = bpy.context.scene
scene.frame_start = {start_frame}
scene.frame_end = {end_frame}

# Animate the main subject (Suzanne)
suzanne = bpy.data.objects.get("Suzanne")
if suzanne:
    # Clear existing animation
    suzanne.animation_data_clear()
    
    # Animate rotation
    suzanne.rotation_euler = (0, 0, 0)
    suzanne.keyframe_insert(data_path="rotation_euler", frame={start_frame})
    
    suzanne.rotation_euler = (0, 0, 2 * math.pi)
    suzanne.keyframe_insert(data_path="rotation_euler", frame={end_frame})
    
    # Set interpolation to linear
    if suzanne.animation_data and suzanne.animation_data.action:
        for fcurve in suzanne.animation_data.action.fcurves:
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation = 'LINEAR'
    
    print(f"Added rotation animation to Suzanne")

# Animate camera for more dynamic shot
camera = bpy.data.objects.get("Render_Camera")
if camera:
    # Clear existing animation
    camera.animation_data_clear()
    
    # Animate camera position - orbit around subject
    import mathutils
    
    center = mathutils.Vector((0, 0, 1))
    radius = 6
    height = 3
    
    for frame in range({start_frame}, {end_frame} + 1):
        scene.frame_set(frame)
        
        # Calculate orbit position
        angle = (frame - {start_frame}) / ({end_frame} - {start_frame}) * math.pi * 0.5
        
        x = center.x + radius * math.cos(angle)
        y = center.y + radius * math.sin(angle) - 4
        z = center.z + height
        
        camera.location = (x, y, z)
        
        # Point camera at center
        direction = center - camera.location
        camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        
        # Insert keyframes
        camera.keyframe_insert(data_path="location", frame=frame)
        camera.keyframe_insert(data_path="rotation_euler", frame=frame)
    
    print(f"Added orbit animation to camera")

print(f"Animation setup complete for frames {start_frame}-{end_frame}")
    '''
    
    client.execute_code(animation_code, "Setup animation")
    
    # Render each frame
    render_times = []
    
    for frame in range(start_frame, end_frame + 1):
        frame_start = time.time()
        
        render_code = f'''
import bpy
import time
import os

scene = bpy.context.scene
scene.frame_set({frame})

# Set output filename
base_path = scene.render.filepath
filename = "{output_name}_frame_{frame:04d}"
scene.render.filepath = os.path.join(os.path.dirname(base_path), filename)

print(f"Rendering frame {frame}/{end_frame}...")

start_time = time.time()
bpy.ops.render.render(write_still=True)
end_time = time.time()

render_time = end_time - start_time
print(f"Frame {frame} completed in {{render_time:.2f}}s")
        '''
        
        response = client.execute_code(render_code, f"Render frame {frame}")
        
        frame_time = time.time() - frame_start
        render_times.append(frame_time)
        
        progress = ((frame - start_frame + 1) / (end_frame - start_frame + 1)) * 100
        print(f"  Progress: {progress:.1f}% (Frame {frame}/{end_frame})")
    
    total_time = sum(render_times)
    avg_time = total_time / len(render_times)
    
    print(f"\\n📊 Animation Render Complete:")
    print(f"  • Total frames: {end_frame - start_frame + 1}")
    print(f"  • Total time: {total_time:.2f}s")
    print(f"  • Average per frame: {avg_time:.2f}s")
    print(f"  • Estimated FPS: {1.0/avg_time:.2f}")

def render_multiple_angles(client, angles: list, output_name: str = "angle"):
    """Render the scene from multiple camera angles."""
    print(f"📐 Rendering {len(angles)} different camera angles...")
    
    for i, angle_data in enumerate(angles):
        location, rotation = angle_data
        
        print(f"  Setting up angle {i+1}/{len(angles)}: {location}")
        
        camera_code = f'''
import bpy
import mathutils

# Position camera
camera = bpy.data.objects.get("Render_Camera")
if camera:
    camera.location = {location}
    
    # Point at target (Suzanne)
    target = mathutils.Vector((0, 0, 1))
    direction = target - camera.location
    camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
    print(f"Camera positioned at {{camera.location}}")

# Render
scene = bpy.context.scene
base_path = scene.render.filepath
filename = "{output_name}_angle_{i+1:02d}"
scene.render.filepath = os.path.join(os.path.dirname(base_path), filename)

print(f"Rendering angle {i+1}...")
import time
start_time = time.time()
bpy.ops.render.render(write_still=True)
end_time = time.time()

print(f"Angle {i+1} rendered in {{end_time - start_time:.2f}}s")
        '''
        
        response = client.execute_code(camera_code, f"Render angle {i+1}")

def main():
    parser = argparse.ArgumentParser(description='Automated rendering via BLD Remote MCP')
    parser.add_argument('--port', type=int, default=6688,
                        help='Service port (default: 6688)')
    parser.add_argument('--output-dir', default='./renders',
                        help='Output directory for renders (default: ./renders)')
    parser.add_argument('--engine', choices=['EEVEE', 'CYCLES'], default='EEVEE',
                        help='Render engine (default: EEVEE)')
    parser.add_argument('--samples', type=int, default=64,
                        help='Render samples (default: 64)')
    parser.add_argument('--format', choices=['PNG', 'JPEG', 'TIFF'], default='PNG',
                        help='Output format (default: PNG)')
    parser.add_argument('--animation', action='store_true',
                        help='Render animation sequence')
    parser.add_argument('--frames', type=int, default=10,
                        help='Number of frames for animation (default: 10)')
    parser.add_argument('--angles', action='store_true',
                        help='Render multiple camera angles')
    
    args = parser.parse_args()
    
    print("BLD Remote MCP - Render Automation Example")
    print("=" * 50)
    
    # Check service availability
    print("🔍 Checking service availability...")
    health = check_service_health(port=args.port)
    if not health["responsive"]:
        print("❌ Service not available. Start with: python3 start_service.py")
        sys.exit(1)
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    print(f"📁 Output directory: {output_dir.absolute()}")
    
    try:
        with blender_connection(port=args.port, timeout=30.0) as client:
            
            # Set up render scene
            setup_render_scene(client, str(output_dir))
            
            # Configure render settings
            configure_render_settings(client, args.engine, args.samples)
            
            # Set output format
            format_code = f'''
import bpy
scene = bpy.context.scene

format_mapping = {{
    'PNG': 'PNG',
    'JPEG': 'JPEG', 
    'TIFF': 'TIFF'
}}

scene.render.image_settings.file_format = format_mapping['{args.format}']

if '{args.format}' == 'JPEG':
    scene.render.image_settings.quality = 90
elif '{args.format}' == 'PNG':
    scene.render.image_settings.compression = 15

print(f"Output format set to: {args.format}")
            '''
            client.execute_code(format_code, "Set output format")
            
            if args.animation:
                # Render animation sequence
                render_animation_sequence(client, 1, args.frames, "animation")
                
            elif args.angles:
                # Render multiple angles
                angles = [
                    ((5, -4, 3), None),    # Default angle
                    ((7, 0, 2), None),     # Side view
                    ((0, -6, 4), None),    # Front view
                    ((2, 2, 5), None),     # Top-down angle
                    ((-3, -3, 1.5), None), # Low angle
                ]
                render_multiple_angles(client, angles, "angle")
                
            else:
                # Single frame render
                render_single_frame(client, 1, "single")
            
    except Exception as e:
        print(f"❌ Render automation failed: {e}")
        sys.exit(1)
    
    print("\\n🎉 Render automation completed successfully!")
    print(f"\\nOutput files saved to: {output_dir.absolute()}")
    print("\\nNext steps:")
    print("  • Check the output directory for rendered images")
    print("  • Try different render engines and settings")
    print("  • Experiment with animation: --animation --frames 30")
    print("  • Try multiple angles: --angles")

if __name__ == '__main__':
    main()