#!/usr/bin/env python3
"""
Batch Processing Example

This example demonstrates efficient batch processing using the BLD Remote MCP
background service for handling multiple operations and workflows.

Prerequisites:
- BLD Remote MCP service running
- Sufficient system resources for batch operations

Usage:
    python3 04_batch_processing.py
    python3 04_batch_processing.py --operations 50 --concurrent
"""

import sys
import os
import argparse
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import blender_connection, check_service_health, batch_execute, BldRemoteClient

def simple_batch_demo(port: int = 6688, num_operations: int = 10):
    """
    Demonstrate simple sequential batch processing.
    
    Args:
        port: Service port number
        num_operations: Number of operations to perform
    """
    print(f"📦 Simple batch processing demo ({num_operations} operations)")
    print("=" * 60)
    
    # Prepare batch commands
    commands = []
    
    # Clear scene first
    commands.append({
        "code": """
import bpy
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False, confirm=False)
print("Scene cleared for batch processing")
        """,
        "message": "Clear scene"
    })
    
    # Generate multiple object creation commands
    for i in range(num_operations):
        x = (i % 5) * 2
        y = (i // 5) * 2
        z = 0
        
        commands.append({
            "code": f"""
import bpy
bpy.ops.mesh.primitive_cube_add(location=({x}, {y}, {z}))
cube = bpy.context.active_object
cube.name = "Batch_Cube_{i:03d}"
cube.scale = (0.8, 0.8, 0.8)
print(f"Created cube {i+1}/{num_operations}: {{cube.name}}")
            """,
            "message": f"Create cube {i+1}"
        })
    
    # Add a summary command
    commands.append({
        "code": """
import bpy
cubes = [obj for obj in bpy.data.objects if obj.name.startswith("Batch_Cube_")]
print(f"Batch processing complete! Created {len(cubes)} cubes total")
for i, cube in enumerate(cubes[:5]):  # Show first 5
    print(f"  {cube.name} at {cube.location}")
if len(cubes) > 5:
    print(f"  ... and {len(cubes) - 5} more")
        """,
        "message": "Summary"
    })
    
    print(f"Executing {len(commands)} commands sequentially...")
    start_time = time.time()
    
    # Execute batch
    responses = batch_execute(commands, port=port, delay=0.05)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Analyze results
    successful = sum(1 for r in responses if r.get('response') == 'OK')
    failed = len(responses) - successful
    
    print(f"\\n📊 Batch Results:")
    print(f"  • Total commands: {len(commands)}")
    print(f"  • Successful: {successful}")
    print(f"  • Failed: {failed}")
    print(f"  • Duration: {duration:.2f} seconds")
    print(f"  • Rate: {len(commands)/duration:.1f} commands/second")
    
    return successful == len(commands)

def concurrent_batch_demo(port: int = 6688, num_operations: int = 20, max_workers: int = 4):
    """
    Demonstrate concurrent batch processing with multiple connections.
    
    Args:
        port: Service port number
        num_operations: Number of operations to perform
        max_workers: Maximum concurrent workers
    """
    print(f"🚀 Concurrent batch processing demo ({num_operations} operations, {max_workers} workers)")
    print("=" * 60)
    
    def execute_single_operation(operation_id: int):
        """Execute a single operation in its own connection."""
        try:
            with blender_connection(port=port, timeout=10.0) as client:
                # Create a unique object for this operation
                x = (operation_id % 8) * 1.5
                y = (operation_id // 8) * 1.5
                z = operation_id * 0.1
                
                code = f"""
import bpy
import random

# Create object with random properties
obj_type = random.choice(['cube', 'sphere', 'cylinder'])

if obj_type == 'cube':
    bpy.ops.mesh.primitive_cube_add(location=({x}, {y}, {z}))
elif obj_type == 'sphere':
    bpy.ops.mesh.primitive_uv_sphere_add(location=({x}, {y}, {z}))
else:
    bpy.ops.mesh.primitive_cylinder_add(location=({x}, {y}, {z}))

obj = bpy.context.active_object
obj.name = f"Concurrent_{{obj_type.title()}}_{operation_id:03d}"

# Random scale
scale = random.uniform(0.5, 1.5)
obj.scale = (scale, scale, scale)

# Random rotation
obj.rotation_euler = (
    random.uniform(0, 3.14159),
    random.uniform(0, 3.14159), 
    random.uniform(0, 3.14159)
)

print(f"Worker created {{obj.name}} (scale: {{scale:.2f}})")
                """
                
                response = client.execute_code(code, f"Concurrent operation {operation_id}")
                
                return {
                    'operation_id': operation_id,
                    'success': response.get('response') == 'OK',
                    'response': response
                }
                
        except Exception as e:
            return {
                'operation_id': operation_id,
                'success': False,
                'error': str(e)
            }
    
    print("Clearing scene for concurrent demo...")
    
    # Clear scene first
    with blender_connection(port=port) as client:
        client.execute_code("""
import bpy
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False, confirm=False)
print("Scene cleared for concurrent processing")
        """, "Clear scene")
    
    print(f"Starting {num_operations} concurrent operations...")
    start_time = time.time()
    
    # Execute operations concurrently
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all operations
        future_to_operation = {
            executor.submit(execute_single_operation, i): i 
            for i in range(num_operations)
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_operation):
            operation_id = future_to_operation[future]
            try:
                result = future.result()
                results.append(result)
                
                if result['success']:
                    print(f"  ✓ Operation {operation_id} completed")
                else:
                    print(f"  ❌ Operation {operation_id} failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"  ❌ Operation {operation_id} exception: {e}")
                results.append({
                    'operation_id': operation_id,
                    'success': False,
                    'error': str(e)
                })
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Analyze results
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    
    print(f"\\n📊 Concurrent Batch Results:")
    print(f"  • Total operations: {num_operations}")
    print(f"  • Max workers: {max_workers}")
    print(f"  • Successful: {successful}")
    print(f"  • Failed: {failed}")
    print(f"  • Duration: {duration:.2f} seconds")
    print(f"  • Rate: {num_operations/duration:.1f} operations/second")
    
    # Get final object count
    with blender_connection(port=port) as client:
        response = client.execute_code("""
import bpy
concurrent_objects = [obj for obj in bpy.data.objects if obj.name.startswith("Concurrent_")]
print(f"Final count: {len(concurrent_objects)} concurrent objects created")

# Group by type
types = {}
for obj in concurrent_objects:
    obj_type = obj.name.split('_')[1]
    types[obj_type] = types.get(obj_type, 0) + 1

for obj_type, count in sorted(types.items()):
    print(f"  {obj_type}: {count}")
        """, "Count results")
    
    return successful >= (num_operations * 0.8)  # Allow 20% failure tolerance

def material_batch_processing(port: int = 6688):
    """
    Demonstrate batch processing for material creation and application.
    
    Args:
        port: Service port number
    """
    print("🎨 Material batch processing demo")
    print("=" * 60)
    
    # Generate multiple material creation commands
    material_commands = []
    
    # Create a variety of materials
    material_data = [
        ("Metal_Chrome", (0.8, 0.8, 0.9, 1.0), 0.0, 0.1),
        ("Metal_Gold", (1.0, 0.8, 0.3, 1.0), 0.0, 0.2),
        ("Metal_Copper", (0.9, 0.4, 0.2, 1.0), 0.0, 0.3),
        ("Plastic_Red", (0.8, 0.1, 0.1, 1.0), 0.8, 0.5),
        ("Plastic_Blue", (0.1, 0.3, 0.8, 1.0), 0.8, 0.5),
        ("Glass_Clear", (0.9, 0.9, 0.9, 1.0), 0.0, 0.0),
        ("Rubber_Black", (0.1, 0.1, 0.1, 1.0), 1.0, 0.9),
        ("Fabric_Wool", (0.6, 0.5, 0.4, 1.0), 0.9, 0.8)
    ]
    
    for name, color, roughness, specular in material_data:
        material_commands.append({
            "code": f"""
import bpy

# Create material with realistic properties
mat = bpy.data.materials.new(name="{name}")
mat.use_nodes = True

# Get the principled BSDF node
if mat.node_tree:
    nodes = mat.node_tree.nodes
    principled = nodes.get('Principled BSDF')
    
    if principled:
        # Set material properties
        principled.inputs['Base Color'].default_value = {color}
        principled.inputs['Roughness'].default_value = {roughness}
        principled.inputs['Specular'].default_value = {specular}
        
        # Special properties for specific materials
        if "{name}".startswith("Metal_"):
            principled.inputs['Metallic'].default_value = 1.0
        elif "{name}".startswith("Glass_"):
            principled.inputs['Transmission'].default_value = 0.9
            principled.inputs['IOR'].default_value = 1.52

print(f"Created material: {name}")
            """,
            "message": f"Create material {name}"
        })
    
    print(f"Creating {len(material_commands)} materials...")
    start_time = time.time()
    
    # Execute material creation batch
    responses = batch_execute(material_commands, port=port, delay=0.1)
    
    # Apply materials to existing objects
    application_code = """
import bpy
import random

# Get all mesh objects
mesh_objects = [obj for obj in bpy.data.objects if obj.type == 'MESH']
materials = [mat for mat in bpy.data.materials if mat.name.startswith(('Metal_', 'Plastic_', 'Glass_', 'Rubber_', 'Fabric_'))]

print(f"Applying {len(materials)} materials to {len(mesh_objects)} objects...")

# Randomly assign materials to objects
for obj in mesh_objects:
    if materials and obj.data:
        # Clear existing materials
        obj.data.materials.clear()
        
        # Assign random material
        mat = random.choice(materials)
        obj.data.materials.append(mat)
        print(f"Applied {mat.name} to {obj.name}")

print("Material application complete!")
    """
    
    with blender_connection(port=port) as client:
        client.execute_code(application_code, "Apply materials")
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Count successful material creations
    successful = sum(1 for r in responses if r.get('response') == 'OK')
    
    print(f"\\n📊 Material Batch Results:")
    print(f"  • Materials created: {successful}/{len(material_commands)}")
    print(f"  • Duration: {duration:.2f} seconds")
    print(f"  • Rate: {len(material_commands)/duration:.1f} materials/second")
    
    return successful == len(material_commands)

def main():
    parser = argparse.ArgumentParser(description='Demonstrate batch processing via BLD Remote MCP')
    parser.add_argument('--port', type=int, default=6688,
                        help='Service port (default: 6688)')
    parser.add_argument('--operations', type=int, default=10,
                        help='Number of operations for simple batch (default: 10)')
    parser.add_argument('--concurrent', action='store_true',
                        help='Run concurrent batch processing demo')
    parser.add_argument('--workers', type=int, default=4,
                        help='Number of concurrent workers (default: 4)')
    parser.add_argument('--materials', action='store_true',
                        help='Run material batch processing demo')
    
    args = parser.parse_args()
    
    print("BLD Remote MCP - Batch Processing Example")
    print("=" * 50)
    
    # Check service availability
    print("🔍 Checking service availability...")
    health = check_service_health(port=args.port)
    if not health["responsive"]:
        print("❌ Service not available. Start with: python3 start_service.py")
        sys.exit(1)
    
    print("✅ Service is available")
    
    all_success = True
    
    try:
        # Simple sequential batch processing
        print("\\n" + "="*60)
        success = simple_batch_demo(args.port, args.operations)
        all_success = all_success and success
        
        if args.concurrent:
            # Concurrent batch processing
            print("\\n" + "="*60)
            success = concurrent_batch_demo(args.port, args.operations * 2, args.workers)
            all_success = all_success and success
        
        if args.materials:
            # Material batch processing
            print("\\n" + "="*60)
            success = material_batch_processing(args.port)
            all_success = all_success and success
            
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")
        sys.exit(1)
    
    if all_success:
        print("\\n🎉 All batch processing examples completed successfully!")
        print("\\nKey takeaways:")
        print("  • Sequential processing: Simple, reliable, slower")
        print("  • Concurrent processing: Faster, requires careful resource management") 
        print("  • Batch utilities: Efficient for similar operations")
        print("\\nNext steps:")
        print("  • Try: python3 05_health_monitoring.py")
        print("  • Try: python3 07_render_automation.py")
    else:
        print("\\n⚠️ Some batch processing examples had issues")
        print("Check the output above for specific failures")

if __name__ == '__main__':
    main()