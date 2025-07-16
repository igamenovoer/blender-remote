#!/usr/bin/env python3
"""
Synchronous Execution Testing with Custom Results

Tests that the MCP server executes Blender code and returns custom, structured
results synchronously. This is the core value proposition - executing custom 
Blender Python code and getting back meaningful data, not just "success" messages.

Based on: context/plans/mcp-server-comprehensive-test-plan.md
"""

import asyncio
import json
import sys
import os
import time
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Add project src to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(project_root, "src"))


class BlenderAutomationTests:
    """Test synchronous execution of complex Blender automation with custom results."""
    
    def __init__(self):
        self.server_params = StdioServerParameters(
            command="pixi",
            args=["run", "python", "src/blender_remote/mcp_server.py"],
            env=None,
        )
    
    async def test_object_creation_and_vertex_extraction(self):
        """Test: Create objects and extract vertex coordinates"""
        
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
                return result

    async def test_material_creation_and_properties(self):
        """Test: Create materials and extract properties"""
        
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
                return result

    async def test_animation_and_transform_data(self):
        """Test: Create animation and extract transform data"""
        
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
                return result

    async def run_all_tests(self):
        """Run all synchronous execution tests"""
        print("🔬 Testing Synchronous Execution with Custom Results...")
        
        tests = [
            ("Object Creation & Vertex Extraction", self.test_object_creation_and_vertex_extraction),
            ("Material Creation & Properties", self.test_material_creation_and_properties),
            ("Animation & Transform Data", self.test_animation_and_transform_data),
        ]
        
        results = {}
        for test_name, test_func in tests:
            print(f"\n📋 Running: {test_name}")
            try:
                result = await test_func()
                
                # Validate that we got structured data back
                success = self._validate_result(result)
                results[test_name] = {"status": "success" if success else "failed", "result": result}
                print(f"✅ {test_name}: {'PASSED' if success else 'FAILED'}")
                
            except Exception as e:
                results[test_name] = {"status": "error", "error": str(e)}
                print(f"❌ {test_name}: FAILED - {e}")
        
        return results
    
    def _validate_result(self, result):
        """Validate that result contains structured JSON data"""
        try:
            if not result or not hasattr(result, 'content') or not result.content:
                return False
            
            content = result.content[0].text
            # Look for JSON structure in the response
            return "{" in content and "}" in content and ("objects_created" in content or "materials_created" in content or "animation_frames" in content)
        except:
            return False


async def main():
    """Run synchronous execution testing"""
    print("=" * 80)
    print("🔬 MCP Server - Synchronous Execution with Custom Results Testing")
    print("=" * 80)
    print("Testing: Custom Blender code execution with structured result return")
    print()
    
    tester = BlenderAutomationTests()
    results = await tester.run_all_tests()
    
    print("\n📊 Synchronous Execution Test Results:")
    passed_count = 0
    total_count = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result["status"] == "success" else "❌ FAIL"
        print(f"  {status} {test_name}")
        if result["status"] == "success":
            passed_count += 1
    
    success_rate = (passed_count / total_count * 100) if total_count > 0 else 0
    overall_status = "PASS" if passed_count == total_count else "FAIL"
    
    print(f"\n🎯 OVERALL RESULT: {overall_status}")
    print(f"📊 Success Rate: {passed_count}/{total_count} ({success_rate:.1f}%)")
    
    if overall_status == "PASS":
        print("✅ Synchronous execution with custom results works correctly")
    else:
        print("❌ Synchronous execution validation failed")
    
    return 0 if overall_status == "PASS" else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)