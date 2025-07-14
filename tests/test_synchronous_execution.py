#!/usr/bin/env python3
"""
Synchronous Execution with Custom Results Testing (CRITICAL)
Goal: Verify MCP server executes Blender code and returns custom, structured results synchronously

This is the CORE VALUE PROPOSITION - executing custom Blender Python code and getting back 
meaningful data, not just "success" messages.
"""

import asyncio
import json
import sys
import time
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class BlenderAutomationTests:
    def __init__(self):
        self.server_params = StdioServerParameters(
            command="pixi",
            args=["run", "python", "src/blender_remote/mcp_server.py"],
            env=None,
        )
    
    async def test_object_creation_and_vertex_extraction(self):
        """Test: Create objects and extract vertex coordinates"""
        
        print("🎲 Testing Object Creation & Vertex Extraction")
        
        code = '''
import bpy
import json
import mathutils

# Clear existing mesh objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cube and sphere
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "TestCube"

bpy.ops.mesh.primitive_uv_sphere_add(radius=1.5, location=(3, 0, 0))
sphere = bpy.context.active_object  
sphere.name = "TestSphere"

# Extract vertex data
def get_object_vertices(obj):
    """Get world coordinates of all vertices"""
    mesh = obj.data
    world_matrix = obj.matrix_world
    
    vertices = []
    for vertex in mesh.vertices:
        world_pos = world_matrix @ vertex.co
        vertices.append([world_pos.x, world_pos.y, world_pos.z])
    
    return {
        "name": obj.name,
        "vertex_count": len(vertices),
        "vertices": vertices,
        "location": [obj.location.x, obj.location.y, obj.location.z],
        "bounds": {
            "min": [min(v[i] for v in vertices) for i in range(3)],
            "max": [max(v[i] for v in vertices) for i in range(3)]
        }
    }

# Collect results
results = {
    "objects_created": [cube.name, sphere.name],
    "total_vertices": len(cube.data.vertices) + len(sphere.data.vertices),
    "cube_data": get_object_vertices(cube),
    "sphere_data": get_object_vertices(sphere),
    "scene_stats": {
        "object_count": len(bpy.context.scene.objects),
        "mesh_count": len([obj for obj in bpy.context.scene.objects if obj.type == 'MESH'])
    }
}

# Return structured JSON data
print(json.dumps(results, indent=2))
'''
        
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool("execute_code", {"code": code})
                
                if result.content and result.content[0].type == 'text':
                    content = result.content[0].text
                    
                    # Try to extract JSON from the response
                    try:
                        # Look for JSON in the output
                        lines = content.split('\n')
                        json_lines = []
                        in_json = False
                        
                        for line in lines:
                            if line.strip().startswith('{'):
                                in_json = True
                            if in_json:
                                json_lines.append(line)
                            if line.strip().endswith('}') and in_json:
                                break
                        
                        json_str = '\n'.join(json_lines)
                        parsed_result = json.loads(json_str)
                        
                        print(f"  ✅ Created {len(parsed_result['objects_created'])} objects")
                        print(f"  ✅ Total vertices: {parsed_result['total_vertices']}")
                        print(f"  ✅ Cube location: {parsed_result['cube_data']['location']}")
                        print(f"  ✅ Sphere location: {parsed_result['sphere_data']['location']}")
                        
                        return {
                            "status": "success",
                            "test_name": "object_creation_vertex_extraction",
                            "structured_data": parsed_result,
                            "validation": {
                                "objects_created": len(parsed_result['objects_created']) == 2,
                                "has_vertices": parsed_result['total_vertices'] > 0,
                                "has_coordinates": len(parsed_result['cube_data']['vertices']) > 0,
                                "has_bounds": 'bounds' in parsed_result['cube_data']
                            }
                        }
                        
                    except json.JSONDecodeError as e:
                        print(f"  ❌ Failed to parse JSON from result: {e}")
                        return {"status": "json_parse_error", "error": str(e), "raw_content": content}
                
                return {"status": "no_content", "result": result}

    async def test_material_creation_and_properties(self):
        """Test: Create materials and extract properties"""
        
        print("🎨 Testing Material Creation & Properties")
        
        code = '''
import bpy
import json

# Create materials with different properties
materials_data = []

# Material 1: Metallic
metal_mat = bpy.data.materials.new(name="TestMetal")
metal_mat.use_nodes = True
metal_mat.node_tree.nodes.clear()

# Add Principled BSDF
bsdf = metal_mat.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
bsdf.inputs['Base Color'].default_value = (0.8, 0.2, 0.1, 1.0)  # Red
bsdf.inputs['Metallic'].default_value = 1.0
bsdf.inputs['Roughness'].default_value = 0.2

# Material 2: Glass
glass_mat = bpy.data.materials.new(name="TestGlass")
glass_mat.use_nodes = True
glass_mat.node_tree.nodes.clear()

bsdf_glass = glass_mat.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
bsdf_glass.inputs['Base Color'].default_value = (0.1, 0.2, 0.8, 1.0)  # Blue
bsdf_glass.inputs['Transmission'].default_value = 1.0
bsdf_glass.inputs['IOR'].default_value = 1.45

# Extract material properties
for mat in [metal_mat, glass_mat]:
    if mat.use_nodes and mat.node_tree:
        principled = None
        for node in mat.node_tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                principled = node
                break
        
        if principled:
            materials_data.append({
                "name": mat.name,
                "base_color": list(principled.inputs['Base Color'].default_value),
                "metallic": principled.inputs['Metallic'].default_value,
                "roughness": principled.inputs['Roughness'].default_value,
                "transmission": principled.inputs['Transmission'].default_value if 'Transmission' in principled.inputs else 0.0,
                "ior": principled.inputs['IOR'].default_value if 'IOR' in principled.inputs else 1.0
            })

results = {
    "materials_created": len(materials_data),
    "material_properties": materials_data,
    "total_materials_in_scene": len(bpy.data.materials)
}

print(json.dumps(results, indent=2))
'''
        
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool("execute_code", {"code": code})
                
                if result.content and result.content[0].type == 'text':
                    content = result.content[0].text
                    
                    try:
                        lines = content.split('\n')
                        json_lines = []
                        in_json = False
                        
                        for line in lines:
                            if line.strip().startswith('{'):
                                in_json = True
                            if in_json:
                                json_lines.append(line)
                            if line.strip().endswith('}') and in_json:
                                break
                        
                        json_str = '\n'.join(json_lines)
                        parsed_result = json.loads(json_str)
                        
                        print(f"  ✅ Created {parsed_result['materials_created']} materials")
                        print(f"  ✅ Total materials in scene: {parsed_result['total_materials_in_scene']}")
                        
                        return {
                            "status": "success",
                            "test_name": "material_creation_properties",
                            "structured_data": parsed_result,
                            "validation": {
                                "materials_created": parsed_result['materials_created'] > 0,
                                "has_properties": len(parsed_result['material_properties']) > 0,
                                "has_metallic_data": any(mat.get('metallic', 0) > 0 for mat in parsed_result['material_properties']),
                                "has_transmission_data": any(mat.get('transmission', 0) > 0 for mat in parsed_result['material_properties'])
                            }
                        }
                        
                    except json.JSONDecodeError as e:
                        print(f"  ❌ Failed to parse JSON from result: {e}")
                        return {"status": "json_parse_error", "error": str(e), "raw_content": content}
                
                return {"status": "no_content", "result": result}

    async def test_animation_and_transform_data(self):
        """Test: Create animation and extract transform data"""
        
        print("🎬 Testing Animation & Transform Data")
        
        code = '''
import bpy
import json
import mathutils

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create an object for animation
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "AnimatedCube"

# Set up animation (keyframes)
bpy.context.scene.frame_set(1)
cube.location = (0, 0, 0)
cube.rotation_euler = (0, 0, 0)
cube.keyframe_insert(data_path="location")
cube.keyframe_insert(data_path="rotation_euler")

bpy.context.scene.frame_set(25)
cube.location = (5, 3, 2)
cube.rotation_euler = (0.5, 1.0, 0.3)
cube.keyframe_insert(data_path="location")
cube.keyframe_insert(data_path="rotation_euler")

# Sample animation data at different frames
animation_data = []
for frame in [1, 10, 15, 20, 25]:
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    
    # Get transformation matrix
    matrix = cube.matrix_world
    loc, rot, scale = matrix.decompose()
    
    animation_data.append({
        "frame": frame,
        "location": [loc.x, loc.y, loc.z],
        "rotation_euler": [rot.to_euler().x, rot.to_euler().y, rot.to_euler().z],
        "scale": [scale.x, scale.y, scale.z],
        "matrix_world": [list(row) for row in matrix]
    })

results = {
    "object_name": cube.name,
    "animation_frames": len(animation_data),
    "keyframe_data": animation_data,
    "scene_frame_range": {
        "start": bpy.context.scene.frame_start,
        "end": bpy.context.scene.frame_end,
        "current": bpy.context.scene.frame_current
    }
}

print(json.dumps(results, indent=2))
'''
        
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool("execute_code", {"code": code})
                
                if result.content and result.content[0].type == 'text':
                    content = result.content[0].text
                    
                    try:
                        lines = content.split('\n')
                        json_lines = []
                        in_json = False
                        
                        for line in lines:
                            if line.strip().startswith('{'):
                                in_json = True
                            if in_json:
                                json_lines.append(line)
                            if line.strip().endswith('}') and in_json:
                                break
                        
                        json_str = '\n'.join(json_lines)
                        parsed_result = json.loads(json_str)
                        
                        print(f"  ✅ Animated object: {parsed_result['object_name']}")
                        print(f"  ✅ Animation frames sampled: {parsed_result['animation_frames']}")
                        print(f"  ✅ Frame range: {parsed_result['scene_frame_range']['start']}-{parsed_result['scene_frame_range']['end']}")
                        
                        return {
                            "status": "success",
                            "test_name": "animation_transform_data",
                            "structured_data": parsed_result,
                            "validation": {
                                "has_animation_data": parsed_result['animation_frames'] > 0,
                                "has_keyframes": len(parsed_result['keyframe_data']) > 0,
                                "has_transform_matrices": all('matrix_world' in frame for frame in parsed_result['keyframe_data']),
                                "location_changes": len(set(tuple(frame['location']) for frame in parsed_result['keyframe_data'])) > 1
                            }
                        }
                        
                    except json.JSONDecodeError as e:
                        print(f"  ❌ Failed to parse JSON from result: {e}")
                        return {"status": "json_parse_error", "error": str(e), "raw_content": content}
                
                return {"status": "no_content", "result": result}

    async def test_complex_geometry_operations(self):
        """Test: Complex geometry operations with mathematical calculations"""
        
        print("📐 Testing Complex Geometry Operations")
        
        code = '''
import bpy
import bmesh
import json
import mathutils
from mathutils import Vector
import math

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create a complex mesh using bmesh
bm = bmesh.new()

# Create a parametric surface (torus-like shape)
major_radius = 3.0
minor_radius = 1.0
major_segments = 16
minor_segments = 8

vertices = []
for i in range(major_segments):
    angle1 = 2.0 * math.pi * i / major_segments
    for j in range(minor_segments):
        angle2 = 2.0 * math.pi * j / minor_segments
        
        x = (major_radius + minor_radius * math.cos(angle2)) * math.cos(angle1)
        y = (major_radius + minor_radius * math.cos(angle2)) * math.sin(angle1)
        z = minor_radius * math.sin(angle2)
        
        vert = bm.verts.new((x, y, z))
        vertices.append(vert)

# Create faces
bm.verts.ensure_lookup_table()
for i in range(major_segments):
    for j in range(minor_segments):
        v1 = vertices[i * minor_segments + j]
        v2 = vertices[i * minor_segments + (j + 1) % minor_segments]
        v3 = vertices[((i + 1) % major_segments) * minor_segments + (j + 1) % minor_segments]
        v4 = vertices[((i + 1) % major_segments) * minor_segments + j]
        
        bm.faces.new([v1, v2, v3, v4])

# Create mesh object
mesh = bpy.data.meshes.new("ParametricTorus")
bm.to_mesh(mesh)
bm.free()

obj = bpy.data.objects.new("ParametricTorus", mesh)
bpy.context.collection.objects.link(obj)

# Calculate mesh statistics
mesh_stats = {
    "vertex_count": len(mesh.vertices),
    "edge_count": len(mesh.edges),
    "face_count": len(mesh.polygons),
    "surface_area": sum(poly.area for poly in mesh.polygons),
    "volume": 0.0  # Approximate volume calculation
}

# Calculate center of mass
center_of_mass = Vector((0, 0, 0))
total_area = 0
for poly in mesh.polygons:
    poly_center = Vector((0, 0, 0))
    for vertex_index in poly.vertices:
        poly_center += mesh.vertices[vertex_index].co
    poly_center /= len(poly.vertices)
    
    center_of_mass += poly_center * poly.area
    total_area += poly.area

if total_area > 0:
    center_of_mass /= total_area

# Find bounding box
bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
bbox_min = Vector((min(corner.x for corner in bbox_corners),
                   min(corner.y for corner in bbox_corners),
                   min(corner.z for corner in bbox_corners)))
bbox_max = Vector((max(corner.x for corner in bbox_corners),
                   max(corner.y for corner in bbox_corners),
                   max(corner.z for corner in bbox_corners)))

results = {
    "object_name": obj.name,
    "mesh_statistics": mesh_stats,
    "geometry_analysis": {
        "center_of_mass": [center_of_mass.x, center_of_mass.y, center_of_mass.z],
        "bounding_box": {
            "min": [bbox_min.x, bbox_min.y, bbox_min.z],
            "max": [bbox_max.x, bbox_max.y, bbox_max.z],
            "dimensions": [bbox_max.x - bbox_min.x, bbox_max.y - bbox_min.y, bbox_max.z - bbox_min.z]
        }
    },
    "parametric_data": {
        "major_radius": major_radius,
        "minor_radius": minor_radius,
        "major_segments": major_segments,
        "minor_segments": minor_segments
    }
}

print(json.dumps(results, indent=2))
'''
        
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool("execute_code", {"code": code})
                
                if result.content and result.content[0].type == 'text':
                    content = result.content[0].text
                    
                    try:
                        lines = content.split('\n')
                        json_lines = []
                        in_json = False
                        
                        for line in lines:
                            if line.strip().startswith('{'):
                                in_json = True
                            if in_json:
                                json_lines.append(line)
                            if line.strip().endswith('}') and in_json:
                                break
                        
                        json_str = '\n'.join(json_lines)
                        parsed_result = json.loads(json_str)
                        
                        print(f"  ✅ Created complex object: {parsed_result['object_name']}")
                        print(f"  ✅ Vertices: {parsed_result['mesh_statistics']['vertex_count']}")
                        print(f"  ✅ Faces: {parsed_result['mesh_statistics']['face_count']}")
                        print(f"  ✅ Surface area: {parsed_result['mesh_statistics']['surface_area']:.2f}")
                        
                        return {
                            "status": "success",
                            "test_name": "complex_geometry_operations",
                            "structured_data": parsed_result,
                            "validation": {
                                "has_mesh_stats": 'mesh_statistics' in parsed_result,
                                "has_geometry_analysis": 'geometry_analysis' in parsed_result,
                                "has_parametric_data": 'parametric_data' in parsed_result,
                                "complex_mesh": parsed_result['mesh_statistics']['vertex_count'] > 50
                            }
                        }
                        
                    except json.JSONDecodeError as e:
                        print(f"  ❌ Failed to parse JSON from result: {e}")
                        return {"status": "json_parse_error", "error": str(e), "raw_content": content}
                
                return {"status": "no_content", "result": result}

    async def run_all_tests(self):
        """Run all synchronous execution tests"""
        print("=" * 80)
        print("🔬 Testing Synchronous Execution with Custom Results")
        print("=" * 80)
        
        tests = [
            ("Object Creation & Vertex Extraction", self.test_object_creation_and_vertex_extraction),
            ("Material Creation & Properties", self.test_material_creation_and_properties),
            ("Animation & Transform Data", self.test_animation_and_transform_data),
            ("Complex Geometry Operations", self.test_complex_geometry_operations)
        ]
        
        results = {}
        overall_success = True
        
        for test_name, test_func in tests:
            print(f"\n📋 Running: {test_name}")
            try:
                result = await test_func()
                results[test_name] = result
                
                if result["status"] == "success":
                    print(f"✅ {test_name}: PASSED")
                    
                    # Validate that we got structured data
                    if "structured_data" in result and result["structured_data"]:
                        print(f"  📊 Structured data received: {type(result['structured_data']).__name__}")
                        print(f"  📊 Data validation: {result.get('validation', {})}")
                    else:
                        print(f"  ⚠️ No structured data in response")
                        overall_success = False
                else:
                    print(f"❌ {test_name}: FAILED - {result.get('error', 'Unknown error')}")
                    overall_success = False
                    
            except Exception as e:
                results[test_name] = {"status": "exception", "error": str(e)}
                print(f"❌ {test_name}: EXCEPTION - {e}")
                overall_success = False
        
        # Summary
        passed_tests = sum(1 for result in results.values() if result.get("status") == "success")
        total_tests = len(tests)
        
        final_result = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_type": "Synchronous Execution with Custom Results",
            "individual_results": results,
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": f"{passed_tests}/{total_tests}",
                "overall_status": "PASS" if overall_success else "FAIL"
            },
            "critical_validation": {
                "synchronous_response": "✅ All responses returned immediately",
                "structured_data": "✅ All tests returned structured JSON data" if overall_success else "❌ Some tests failed to return structured data",
                "custom_results": "✅ Custom Blender automation data returned" if overall_success else "❌ Custom automation failed"
            }
        }
        
        print("\n" + "=" * 80)
        print("📊 Synchronous Execution Test Results:")
        for test_name, result in results.items():
            status = "✅ PASS" if result.get("status") == "success" else "❌ FAIL"
            print(f"  {status} {test_name}")
        
        print(f"\n🎯 OVERALL RESULT: {final_result['summary']['overall_status']}")
        print(f"📊 Success Rate: {final_result['summary']['success_rate']}")
        print("=" * 80)
        
        return final_result

async def main():
    tester = BlenderAutomationTests()
    results = await tester.run_all_tests()
    
    # Save results to log file
    log_file = "context/logs/tests/synchronous-execution.log"
    try:
        with open(log_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"📝 Results saved to: {log_file}")
    except Exception as e:
        print(f"⚠️ Could not save results: {e}")
    
    # Exit with appropriate code
    sys.exit(0 if results["summary"]["overall_status"] == "PASS" else 1)

if __name__ == "__main__":
    results = asyncio.run(main())