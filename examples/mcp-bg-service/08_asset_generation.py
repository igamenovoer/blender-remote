#!/usr/bin/env python3
"""
Asset Generation Example

This example demonstrates procedural asset generation using the
BLD Remote MCP background service for automated content creation.

Prerequisites:
- BLD Remote MCP service running
- Blender with scripting capabilities

Usage:
    python3 08_asset_generation.py
    python3 08_asset_generation.py --buildings 5 --trees 10 --export
"""

import sys
import os
import argparse
import time
import random

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import blender_connection, check_service_health

def generate_procedural_building(client, building_id: int, location: tuple):
    """Generate a procedural building at the specified location."""
    
    building_code = f'''
import bpy
import bmesh
import random
import mathutils

def create_building(building_id, location):
    """Create a procedural building."""
    
    # Building parameters
    base_width = random.uniform(2, 4)
    base_depth = random.uniform(2, 4)
    height = random.uniform(3, 8)
    floors = int(height / 3) + 1
    
    # Create base mesh
    bpy.ops.mesh.primitive_cube_add(location=location)
    building = bpy.context.active_object
    building.name = f"Building_{{building_id:03d}}"
    
    # Scale to building dimensions
    building.scale = (base_width, base_depth, height)
    
    # Apply scale
    bpy.context.view_layer.objects.active = building
    bpy.ops.object.transform_apply(scale=True)
    
    # Enter edit mode to add details
    bpy.ops.object.mode_set(mode='EDIT')
    
    bm = bmesh.from_mesh(building.data)
    
    # Add floor divisions
    for floor in range(1, floors):
        floor_height = (floor / floors) * 2 - 1  # Normalize to [-1, 1]
        
        # Add horizontal edge loops for floors
        bmesh.ops.bisect_plane(
            bm,
            geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
            plane_co=(0, 0, floor_height),
            plane_no=(0, 0, 1),
            clear_inner=False,
            clear_outer=False
        )
    
    # Add some windows (simplified)
    if random.choice([True, False]):
        # Inset faces for window effect
        bmesh.ops.inset_faces(
            bm,
            faces=[f for f in bm.faces if abs(f.normal.z) < 0.5],  # Side faces
            thickness=0.1,
            depth=0.05
        )
    
    # Update mesh
    bmesh.update_edit_mesh(building.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Create building material
    mat_name = f"Building_Material_{{building_id}}"
    if mat_name not in bpy.data.materials:
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        
        # Random building color
        colors = [
            (0.8, 0.7, 0.6, 1.0),  # Beige
            (0.6, 0.6, 0.7, 1.0),  # Blue-gray
            (0.7, 0.6, 0.5, 1.0),  # Brown
            (0.8, 0.8, 0.8, 1.0),  # Light gray
            (0.5, 0.6, 0.5, 1.0),  # Green-gray
        ]
        
        color = random.choice(colors)
        
        nodes = mat.node_tree.nodes
        principled = nodes.get('Principled BSDF')
        if principled:
            principled.inputs['Base Color'].default_value = color
            principled.inputs['Roughness'].default_value = random.uniform(0.3, 0.8)
        
        building.data.materials.append(mat)
    
    print(f"Created building {{building_id}} at {{location}}: {{base_width:.1f}}x{{base_depth:.1f}}x{{height:.1f}}")
    return building

# Generate the building
building = create_building({building_id}, {location})
    '''
    
    response = client.execute_code(building_code, f"Generate building {building_id}")
    return response

def generate_procedural_tree(client, tree_id: int, location: tuple):
    """Generate a procedural tree at the specified location."""
    
    tree_code = f'''
import bpy
import bmesh
import random
import mathutils

def create_tree(tree_id, location):
    """Create a procedural tree."""
    
    # Tree parameters
    trunk_height = random.uniform(1.5, 3.0)
    trunk_radius = random.uniform(0.1, 0.2)
    crown_size = random.uniform(1.0, 2.5)
    tree_type = random.choice(['oak', 'pine', 'palm'])
    
    # Create trunk
    bpy.ops.mesh.primitive_cylinder_add(
        radius=trunk_radius,
        depth=trunk_height,
        location=(location[0], location[1], location[2] + trunk_height/2)
    )
    trunk = bpy.context.active_object
    trunk.name = f"Tree_Trunk_{{tree_id:03d}}"
    
    # Create crown based on tree type
    crown_location = (location[0], location[1], location[2] + trunk_height + crown_size/2)
    
    if tree_type == 'oak':
        # Spherical crown
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=crown_size,
            location=crown_location
        )
        crown = bpy.context.active_object
        
        # Make it slightly irregular
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.subdivide(number_cuts=2)
        bpy.ops.transform.random_deform(scale=(0.3, 0.3, 0.2))
        bpy.ops.object.mode_set(mode='OBJECT')
        
    elif tree_type == 'pine':
        # Conical crown
        bpy.ops.mesh.primitive_cone_add(
            radius1=crown_size * 0.8,
            radius2=0.1,
            depth=crown_size * 1.5,
            location=crown_location
        )
        crown = bpy.context.active_object
        
    else:  # palm
        # Palm-like crown with ico sphere
        bpy.ops.mesh.primitive_ico_sphere_add(
            radius=crown_size * 0.6,
            location=crown_location
        )
        crown = bpy.context.active_object
        
        # Elongate it
        crown.scale[2] = 0.5
        bpy.ops.object.transform_apply(scale=True)
    
    crown.name = f"Tree_Crown_{{tree_id:03d}}"
    
    # Create materials
    # Trunk material
    trunk_mat = bpy.data.materials.new(name=f"Trunk_Material_{{tree_id}}")
    trunk_mat.use_nodes = True
    trunk_nodes = trunk_mat.node_tree.nodes
    trunk_principled = trunk_nodes.get('Principled BSDF')
    if trunk_principled:
        trunk_principled.inputs['Base Color'].default_value = (0.4, 0.25, 0.15, 1.0)
        trunk_principled.inputs['Roughness'].default_value = 0.9
    
    trunk.data.materials.append(trunk_mat)
    
    # Crown material
    crown_mat = bpy.data.materials.new(name=f"Crown_Material_{{tree_id}}")
    crown_mat.use_nodes = True
    crown_nodes = crown_mat.node_tree.nodes
    crown_principled = crown_nodes.get('Principled BSDF')
    if crown_principled:
        # Different greens for different tree types
        if tree_type == 'oak':
            color = (0.2, 0.6, 0.2, 1.0)
        elif tree_type == 'pine':
            color = (0.1, 0.4, 0.2, 1.0)
        else:  # palm
            color = (0.3, 0.7, 0.3, 1.0)
        
        crown_principled.inputs['Base Color'].default_value = color
        crown_principled.inputs['Roughness'].default_value = 0.8
    
    crown.data.materials.append(crown_mat)
    
    # Parent crown to trunk
    crown.parent = trunk
    
    print(f"Created {{tree_type}} tree {{tree_id}} at {{location}}: trunk={{trunk_height:.1f}}m, crown={{crown_size:.1f}}m")
    return trunk, crown

# Generate the tree
trunk, crown = create_tree({tree_id}, {location})
    '''
    
    response = client.execute_code(tree_code, f"Generate tree {tree_id}")
    return response

def generate_street_layout(client, width: int = 20, height: int = 20):
    """Generate a street layout with roads and sidewalks."""
    
    street_code = f'''
import bpy
import bmesh

def create_street_layout(width, height):
    """Create a street layout."""
    
    # Clear existing streets
    for obj in bpy.data.objects:
        if obj.name.startswith(('Street_', 'Sidewalk_')):
            bpy.data.objects.remove(obj, do_unlink=True)
    
    # Create main roads
    roads = [
        # Horizontal roads
        {{
            'name': 'Street_Main_Horizontal',
            'location': (0, 0, 0.01),
            'scale': ({width}, 2, 0.01)
        }},
        # Vertical roads  
        {{
            'name': 'Street_Main_Vertical',
            'location': (0, 0, 0.01),
            'scale': (2, {height}, 0.01)
        }},
        # Secondary roads
        {{
            'name': 'Street_Secondary_1',
            'location': ({width//3}, 0, 0.01),
            'scale': (1, {height}, 0.01)
        }},
        {{
            'name': 'Street_Secondary_2',
            'location': (-{width//3}, 0, 0.01),
            'scale': (1, {height}, 0.01)
        }},
        {{
            'name': 'Street_Secondary_3',
            'location': (0, {height//3}, 0.01),
            'scale': ({width}, 1, 0.01)
        }},
        {{
            'name': 'Street_Secondary_4',
            'location': (0, -{height//3}, 0.01),
            'scale': ({width}, 1, 0.01)
        }}
    ]
    
    # Create road material
    road_mat = bpy.data.materials.new(name="Road_Material")
    road_mat.use_nodes = True
    road_nodes = road_mat.node_tree.nodes
    road_principled = road_nodes.get('Principled BSDF')
    if road_principled:
        road_principled.inputs['Base Color'].default_value = (0.2, 0.2, 0.2, 1.0)
        road_principled.inputs['Roughness'].default_value = 0.9
    
    # Create roads
    for road in roads:
        bpy.ops.mesh.primitive_cube_add(location=road['location'])
        road_obj = bpy.context.active_object
        road_obj.name = road['name']
        road_obj.scale = road['scale']
        
        # Apply scale
        bpy.context.view_layer.objects.active = road_obj
        bpy.ops.object.transform_apply(scale=True)
        
        # Apply material
        road_obj.data.materials.append(road_mat)
    
    # Create ground plane
    bpy.ops.mesh.primitive_plane_add(size={max(width, height) * 2}, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "Ground_Plane"
    
    # Ground material
    ground_mat = bpy.data.materials.new(name="Ground_Material")
    ground_mat.use_nodes = True
    ground_nodes = ground_mat.node_tree.nodes
    ground_principled = ground_nodes.get('Principled BSDF')
    if ground_principled:
        ground_principled.inputs['Base Color'].default_value = (0.3, 0.5, 0.2, 1.0)  # Grass color
        ground_principled.inputs['Roughness'].default_value = 0.8
    
    ground.data.materials.append(ground_mat)
    
    print(f"Created street layout: {{width}}x{{height}} units")
    return len(roads)

# Generate the street layout
num_roads = create_street_layout({width}, {height})
    '''
    
    response = client.execute_code(street_code, "Generate street layout")
    return response

def generate_city_block(client, num_buildings: int = 5, num_trees: int = 10):
    """Generate a complete city block with buildings and trees."""
    print(f"🏙️ Generating city block ({num_buildings} buildings, {num_trees} trees)...")
    
    # Clear scene first
    clear_code = '''
import bpy

# Select all objects except camera and lights
for obj in bpy.data.objects:
    if obj.type not in ['CAMERA', 'LIGHT']:
        bpy.data.objects.remove(obj, do_unlink=True)

print("Scene cleared for city generation")
    '''
    client.execute_code(clear_code, "Clear scene")
    
    # Generate street layout
    generate_street_layout(client, 30, 30)
    
    # Generate buildings
    print(f"🏢 Generating {num_buildings} buildings...")
    building_locations = []
    
    # Calculate building positions avoiding roads
    for i in range(num_buildings):
        # Place buildings in blocks
        block_x = random.choice([-10, -3, 3, 10])
        block_y = random.choice([-10, -3, 3, 10])
        
        # Add some randomness within the block
        x = block_x + random.uniform(-2, 2)
        y = block_y + random.uniform(-2, 2)
        z = 0
        
        location = (x, y, z)
        building_locations.append(location)
        
        generate_procedural_building(client, i + 1, location)
    
    # Generate trees
    print(f"🌳 Generating {num_trees} trees...")
    for i in range(num_trees):
        # Place trees in green spaces
        x = random.uniform(-12, 12)
        y = random.uniform(-12, 12)
        z = 0
        
        # Avoid placing trees too close to buildings
        too_close = False
        for bx, by, bz in building_locations:
            if ((x - bx) ** 2 + (y - by) ** 2) < 4:  # 2 unit minimum distance
                too_close = True
                break
        
        if not too_close:
            location = (x, y, z)
            generate_procedural_tree(client, i + 1, location)

def add_environmental_details(client):
    """Add environmental details like street lights, benches, etc."""
    print("🏮 Adding environmental details...")
    
    details_code = '''
import bpy
import random

def create_street_light(location, light_id):
    """Create a street light."""
    # Light pole
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.05,
        depth=3,
        location=(location[0], location[1], 1.5)
    )
    pole = bpy.context.active_object
    pole.name = f"StreetLight_Pole_{light_id}"
    
    # Light fixture
    bpy.ops.mesh.primitive_cube_add(
        size=0.3,
        location=(location[0], location[1], 2.8)
    )
    fixture = bpy.context.active_object
    fixture.name = f"StreetLight_Fixture_{light_id}"
    
    # Add light source
    bpy.ops.object.light_add(
        type='POINT',
        location=(location[0], location[1], 2.8)
    )
    light = bpy.context.active_object
    light.name = f"StreetLight_Light_{light_id}"
    light.data.energy = 10.0
    light.data.color = (1.0, 0.95, 0.8)  # Warm white
    
    # Materials
    pole_mat = bpy.data.materials.new(name=f"Pole_Material_{light_id}")
    pole_mat.use_nodes = True
    pole_nodes = pole_mat.node_tree.nodes
    pole_principled = pole_nodes.get('Principled BSDF')
    if pole_principled:
        pole_principled.inputs['Base Color'].default_value = (0.3, 0.3, 0.3, 1.0)
        pole_principled.inputs['Metallic'].default_value = 1.0
        pole_principled.inputs['Roughness'].default_value = 0.2
    
    pole.data.materials.append(pole_mat)
    fixture.data.materials.append(pole_mat)
    
    # Parent fixture and light to pole
    fixture.parent = pole
    light.parent = pole
    
    return pole

def create_bench(location, bench_id):
    """Create a park bench."""
    # Bench seat
    bpy.ops.mesh.primitive_cube_add(
        location=(location[0], location[1], 0.4),
        scale=(1.5, 0.4, 0.05)
    )
    seat = bpy.context.active_object
    seat.name = f"Bench_Seat_{bench_id}"
    
    # Bench back
    bpy.ops.mesh.primitive_cube_add(
        location=(location[0], location[1] + 0.3, 0.7),
        scale=(1.5, 0.1, 0.3)
    )
    back = bpy.context.active_object
    back.name = f"Bench_Back_{bench_id}"
    
    # Bench material
    bench_mat = bpy.data.materials.new(name=f"Bench_Material_{bench_id}")
    bench_mat.use_nodes = True
    bench_nodes = bench_mat.node_tree.nodes
    bench_principled = bench_nodes.get('Principled BSDF')
    if bench_principled:
        bench_principled.inputs['Base Color'].default_value = (0.4, 0.25, 0.15, 1.0)
        bench_principled.inputs['Roughness'].default_value = 0.8
    
    seat.data.materials.append(bench_mat)
    back.data.materials.append(bench_mat)
    
    # Parent back to seat
    back.parent = seat
    
    return seat

# Add street lights along roads
street_light_positions = [
    (8, 8, 0), (-8, 8, 0), (8, -8, 0), (-8, -8, 0),
    (0, 12, 0), (0, -12, 0), (12, 0, 0), (-12, 0, 0)
]

for i, pos in enumerate(street_light_positions):
    create_street_light(pos, i + 1)

# Add benches in park areas
bench_positions = [
    (5, 5, 0), (-5, 5, 0), (5, -5, 0), (-5, -5, 0)
]

for i, pos in enumerate(bench_positions):
    create_bench(pos, i + 1)

print(f"Added {len(street_light_positions)} street lights and {len(bench_positions)} benches")
    '''
    
    response = client.execute_code(details_code, "Add environmental details")
    return response

def export_assets(client, export_format: str = 'OBJ', output_dir: str = './assets'):
    """Export generated assets to files."""
    print(f"💾 Exporting assets in {export_format} format...")
    
    export_code = f'''
import bpy
import os

output_dir = r"{output_dir}"
os.makedirs(output_dir, exist_ok=True)

# Export different object types separately
export_groups = {{
    'buildings': [obj for obj in bpy.data.objects if obj.name.startswith('Building_')],
    'trees': [obj for obj in bpy.data.objects if obj.name.startswith('Tree_')],
    'streets': [obj for obj in bpy.data.objects if obj.name.startswith('Street_')],
    'lights': [obj for obj in bpy.data.objects if obj.name.startswith('StreetLight_')],
    'benches': [obj for obj in bpy.data.objects if obj.name.startswith('Bench_')]
}}

exported_files = []

for group_name, objects in export_groups.items():
    if not objects:
        continue
    
    # Select objects in group
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    
    if objects:
        bpy.context.view_layer.objects.active = objects[0]
        
        # Export based on format
        filename = f"{{group_name}}.{export_format.lower()}"
        filepath = os.path.join(output_dir, filename)
        
        if "{export_format}" == "OBJ":
            bpy.ops.export_scene.obj(
                filepath=filepath,
                use_selection=True,
                use_materials=True
            )
        elif "{export_format}" == "FBX":
            bpy.ops.export_scene.fbx(
                filepath=filepath,
                use_selection=True
            )
        elif "{export_format}" == "PLY":
            bpy.ops.export_mesh.ply(
                filepath=filepath,
                use_selection=True
            )
        
        exported_files.append(filename)
        print(f"Exported {{group_name}}: {{len(objects)}} objects -> {{filename}}")

print(f"Export complete! Files saved to: {{output_dir}}")
print(f"Exported files: {{', '.join(exported_files)}}")
    '''
    
    response = client.execute_code(export_code, "Export assets")
    return response

def main():
    parser = argparse.ArgumentParser(description='Generate procedural assets via BLD Remote MCP')
    parser.add_argument('--port', type=int, default=6688,
                        help='Service port (default: 6688)')
    parser.add_argument('--buildings', type=int, default=5,
                        help='Number of buildings to generate (default: 5)')
    parser.add_argument('--trees', type=int, default=10,
                        help='Number of trees to generate (default: 10)')
    parser.add_argument('--details', action='store_true',
                        help='Add environmental details (lights, benches)')
    parser.add_argument('--export', action='store_true',
                        help='Export generated assets')
    parser.add_argument('--export-format', choices=['OBJ', 'FBX', 'PLY'], default='OBJ',
                        help='Export format (default: OBJ)')
    parser.add_argument('--output-dir', default='./assets',
                        help='Output directory for exports (default: ./assets)')
    
    args = parser.parse_args()
    
    print("BLD Remote MCP - Asset Generation Example")
    print("=" * 50)
    
    # Check service availability
    print("🔍 Checking service availability...")
    health = check_service_health(port=args.port)
    if not health["responsive"]:
        print("❌ Service not available. Start with: python3 start_service.py")
        sys.exit(1)
    
    try:
        with blender_connection(port=args.port, timeout=60.0) as client:
            
            # Generate city block
            start_time = time.time()
            generate_city_block(client, args.buildings, args.trees)
            
            if args.details:
                add_environmental_details(client)
            
            generation_time = time.time() - start_time
            
            # Get final statistics
            stats_code = '''
import bpy

stats = {}
for obj in bpy.data.objects:
    obj_type = obj.type
    if obj_type == 'MESH':
        name_prefix = obj.name.split('_')[0]
        stats[name_prefix] = stats.get(name_prefix, 0) + 1

print("=== Generated Assets ===")
for asset_type, count in sorted(stats.items()):
    print(f"{asset_type}: {count}")

print(f"Total objects: {len(bpy.data.objects)}")
print(f"Materials created: {len(bpy.data.materials)}")
            '''
            
            client.execute_code(stats_code, "Get statistics")
            
            if args.export:
                export_assets(client, args.export_format, args.output_dir)
            
    except Exception as e:
        print(f"❌ Asset generation failed: {e}")
        sys.exit(1)
    
    print(f"\\n🎉 Asset generation completed in {generation_time:.2f} seconds!")
    print("\\nGenerated assets:")
    print(f"  • {args.buildings} procedural buildings with random properties")
    print(f"  • {args.trees} procedural trees of various types")
    print("  • Street layout with roads and ground plane")
    
    if args.details:
        print("  • Street lights and park benches")
    
    if args.export:
        print(f"  • Assets exported to {args.output_dir} in {args.export_format} format")
    
    print("\\nNext steps:")
    print("  • View the generated city in Blender")
    print("  • Try: --details to add environmental elements")
    print("  • Try: --export to save assets for other projects")
    print("  • Experiment with different building/tree counts")

if __name__ == '__main__':
    main()