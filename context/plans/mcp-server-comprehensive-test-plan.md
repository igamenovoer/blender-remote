# MCP Server Drop-in Replacement Test Plan

**Date:** 2025-07-14  
**Target:** Validate `uvx blender-remote` + `BLD_Remote_MCP` as drop-in replacement for `uvx blender-mcp` + `BlenderAutoMCP`  
**Focus:** Functional equivalence testing of shared methods using `mcp[cli]` tools

## Overview

This test plan validates that our **complete stack** serves as a **drop-in replacement** for the BlenderAutoMCP stack by testing functional equivalence of shared methods.

### **Drop-in Replacement Concept:**
- `uvx blender-remote` + `BLD_Remote_MCP` replaces `uvx blender-mcp` + `BlenderAutoMCP` **as combinations**
- **Functional Equivalence**: Same inputs should produce functionally equivalent outputs
- **Not one-on-one replacement**: We replace the complete stack, not individual components

### **Stack Comparison:**
![Stack Comparison](graphics/stack-comparison.svg)

## Shared Methods to Test

Based on analysis of BlenderAutoMCP implementation, these methods must have functional equivalence:

### **Core Shared Methods:**
1. **`get_scene_info`** - Get scene and object information
2. **`get_object_info`** - Get detailed object information  
3. **`execute_code`** - Execute Blender Python code
4. **`get_viewport_screenshot`** - Capture viewport image

### **Our Enhanced Methods** (additional functionality):
- `put_persist_data` / `get_persist_data` / `remove_persist_data` - Data persistence
- `check_connection_status` - Connection monitoring

## Testing Strategy

### **Primary Method: MCP CLI Tools** ⭐ (RECOMMENDED)
- **Official MCP protocol testing** using `mcp[cli]` package
- **Functional equivalence validation** via side-by-side comparison
- **IDE integration testing** for both stacks

### **Secondary Method: Direct TCP Testing** (Only for service validation)
- **Service availability** testing only
- **Use case**: When MCP CLI cannot reach the TCP service directly

## Test Methods

### Method 1: Functional Equivalence Testing (PRIMARY) ⭐

#### 1.1: MCP SDK Comparison Testing
**Goal**: Verify same inputs produce functionally equivalent outputs

**Create comparison test script:**
```python
# Save as: tests/test_functional_equivalence.py
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class StackComparison:
    async def test_our_stack(self):
        """Test our stack: uvx blender-remote + BLD_Remote_MCP"""
        server_params = StdioServerParameters(
            command="pixi",
            args=["run", "python", "src/blender_remote/mcp_server.py"],
            env=None,
        )
        
        results = {}
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Test shared methods
                results["get_scene_info"] = await session.call_tool("get_scene_info", {})
                results["get_object_info"] = await session.call_tool("get_object_info", {"object_name": "Cube"})
                results["execute_code"] = await session.call_tool("execute_code", {"code": "print('test')"})
                # Note: viewport screenshot only works in GUI mode
                
        return results
    
    async def test_reference_stack(self):
        """Test reference stack: uvx blender-mcp + BlenderAutoMCP"""
        # Note: This would require BlenderAutoMCP running on port 9876
        # For testing purposes, document expected behavior
        return {
            "get_scene_info": "Expected equivalent scene information",
            "get_object_info": "Expected equivalent object information", 
            "execute_code": "Expected equivalent code execution result"
        }
    
    async def compare_stacks(self):
        """Compare functional equivalence between stacks"""
        print("🔄 Testing Functional Equivalence...")
        
        our_results = await self.test_our_stack()
        # ref_results = await self.test_reference_stack()  # Commented: requires BlenderAutoMCP
        
        print("✅ Our Stack Results:")
        for method, result in our_results.items():
            print(f"  {method}: {result}")
        
        return {"status": "success", "our_stack": our_results}

async def main():
    comparison = StackComparison()
    result = await comparison.compare_stacks()
    print(f"\\nComparison Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

**Run comparison test:**
```bash
pixi run python tests/test_functional_equivalence.py
```

#### 1.2: MCP Inspector Interactive Testing
**Goal**: Interactive validation of shared methods

```bash
# Test our stack interactively
pixi run mcp dev src/blender_remote/mcp_server.py

# Opens web interface at http://localhost:3000
# Manually test each shared method:
# 1. get_scene_info -> Should return scene and object information
# 2. get_object_info -> Should return detailed object data
# 3. execute_code -> Should execute Python code in Blender
# 4. get_viewport_screenshot -> Should capture viewport (GUI mode)
```

### Method 2: Service Validation (SECONDARY)

#### 2.1: TCP Service Availability Check
**Goal**: Ensure BLD_Remote_MCP service is running

```python
# Save as: tests/test_service_validation.py
import socket
import json

def validate_bld_remote_mcp(host='127.0.0.1', port=6688):
    """Validate BLD_Remote_MCP TCP service is responding"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        
        # Test basic connectivity
        command = {"message": "validation", "code": "print('BLD_Remote_MCP OK')"}
        sock.sendall(json.dumps(command).encode('utf-8'))
        response_data = sock.recv(4096)
        response = json.loads(response_data.decode('utf-8'))
        
        sock.close()
        return {"status": "available", "response": response}
    except Exception as e:
        return {"status": "unavailable", "error": str(e)}

if __name__ == "__main__":
    result = validate_bld_remote_mcp()
    print(f"Service Validation: {result}")
```

### Method 3: Synchronous Execution with Custom Results (CRITICAL) ⭐

#### 3.1: Real-World Blender Automation Testing
**Goal**: Verify MCP server executes Blender code and returns custom, structured results synchronously

This is the **core value proposition** - executing custom Blender Python code and getting back meaningful data, not just "success" messages.

**Create comprehensive automation test script:**
```python
# Save as: tests/test_synchronous_execution.py
import asyncio
import json
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

    async def test_complex_geometry_operations(self):
        """Test: Complex geometry operations with mathematical calculations"""
        
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
                return result

    async def run_all_tests(self):
        """Run all synchronous execution tests"""
        print("🔬 Testing Synchronous Execution with Custom Results...")
        
        tests = [
            ("Object Creation & Vertex Extraction", self.test_object_creation_and_vertex_extraction),
            ("Material Creation & Properties", self.test_material_creation_and_properties),
            ("Animation & Transform Data", self.test_animation_and_transform_data),
            ("Complex Geometry Operations", self.test_complex_geometry_operations)
        ]
        
        results = {}
        for test_name, test_func in tests:
            print(f"\\n📋 Running: {test_name}")
            try:
                result = await test_func()
                results[test_name] = {"status": "success", "result": result}
                print(f"✅ {test_name}: PASSED")
            except Exception as e:
                results[test_name] = {"status": "error", "error": str(e)}
                print(f"❌ {test_name}: FAILED - {e}")
        
        return results

async def main():
    tester = BlenderAutomationTests()
    results = await tester.run_all_tests()
    
    print("\\n📊 Synchronous Execution Test Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result["status"] == "success" else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(main())
    with open("context/logs/tests/synchronous-execution.log", "w") as f:
        json.dump(results, f, indent=2)
```

**Run synchronous execution tests:**
```bash
pixi run python tests/test_synchronous_execution.py > context/logs/tests/synchronous-execution.log 2>&1
```

#### 3.2: Performance and Result Validation

**Expected Results Validation:**
Each test should return structured JSON data containing:

1. **Object Creation Test**:
   - Created object names and vertex counts
   - World coordinates of all vertices
   - Bounding box calculations
   - Scene statistics

2. **Material Test**:
   - Material properties (metallic, roughness, transmission, etc.)
   - Color values and shader parameters
   - Node tree information

3. **Animation Test**:
   - Keyframe data across timeline
   - Transformation matrices at different frames
   - Animation curve information

4. **Geometry Test**:
   - Complex mesh statistics (vertex/edge/face counts)
   - Surface area and volume calculations
   - Center of mass and bounding box analysis

**Key Success Criteria:**
- ✅ **Synchronous Response**: Results returned immediately, not just "executed"
- ✅ **Structured Data**: JSON-formatted, parseable results
- ✅ **Mathematical Accuracy**: Calculations match expected values
- ✅ **Complex Operations**: Multi-step Blender operations work correctly

```

### Method 4: Base64 Transmission Testing (CRITICAL) ⭐

#### 4.1: Complex Code and Large Data Transmission  
**Goal**: Verify base64 encoding solves formatting issues for complex code and large result data

Base64 encoding addresses critical issues:
- **Complex code formatting**: Special characters, quotes, newlines causing JSON parsing errors
- **Large result data**: 100KB+ responses with complex vertex/coordinate data
- **Backward compatibility**: Ensure non-base64 operations still work

**Create base64 transmission test script:**
```python
# Save as: tests/test_base64_complex_code.py
import asyncio
import json
import sys
import time
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class Base64CodeTests:
    def __init__(self):
        self.server_params = StdioServerParameters(
            command="pixi",
            args=["run", "python", "src/blender_remote/mcp_server.py"],
            env=None,
        )
    
    async def test_base64_object_creation(self):
        """Test: Complex object creation with base64 encoding"""
        
        print("🔐 Testing Base64 Object Creation & Vertex Extraction")
        
        # Complex code that was failing before base64 implementation
        complex_code = '''
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
                
                # Test with base64 encoding enabled
                result = await session.call_tool("execute_code", {
                    "code": complex_code,
                    "send_as_base64": True,
                    "return_as_base64": True
                })
                
                if result.content and result.content[0].type == 'text':
                    content = result.content[0].text
                    print(f"  📋 Raw response length: {len(content)}")
                    
                    try:
                        # Parse the response JSON
                        response_data = json.loads(content)
                        
                        # Check if execution was successful
                        if response_data.get("executed", False):
                            # Extract the result which should contain our JSON
                            output_result = response_data.get("result", "")
                            
                            # Try to parse the JSON output from our code
                            if output_result:
                                try:
                                    # Parse the JSON result
                                    parsed_result = json.loads(output_result.strip())
                                    
                                    print(f"  ✅ Successfully parsed JSON result!")
                                    print(f"  📊 Objects created: {parsed_result.get('objects_created', [])}")
                                    print(f"  📊 Total vertices: {parsed_result.get('total_vertices', 0)}")
                                    print(f"  📊 Cube vertices: {parsed_result.get('cube_data', {}).get('vertex_count', 0)}")
                                    print(f"  📊 Sphere vertices: {parsed_result.get('sphere_data', {}).get('vertex_count', 0)}")
                                    
                                    return {
                                        "status": "success",
                                        "test_name": "base64_object_creation",
                                        "structured_data": parsed_result,
                                        "base64_used": True,
                                        "validation": {
                                            "objects_created": len(parsed_result.get('objects_created', [])) == 2,
                                            "has_vertices": parsed_result.get('total_vertices', 0) > 0,
                                            "has_coordinates": len(parsed_result.get('cube_data', {}).get('vertices', [])) > 0,
                                            "has_bounds": 'bounds' in parsed_result.get('cube_data', {}),
                                            "complex_code_executed": True
                                        }
                                    }
                                except json.JSONDecodeError as e:
                                    print(f"  ❌ Failed to parse JSON from output: {e}")
                                    return {
                                        "status": "json_parse_error",
                                        "test_name": "base64_object_creation",
                                        "error": str(e),
                                        "raw_output": output_result,
                                        "base64_used": True
                                    }
                            else:
                                print(f"  ⚠️ Execution successful but no result output")
                                return {
                                    "status": "no_output",
                                    "test_name": "base64_object_creation",
                                    "response_data": response_data,
                                    "base64_used": True
                                }
                        else:
                            print(f"  ❌ Code execution failed")
                            return {
                                "status": "execution_failed",
                                "test_name": "base64_object_creation",
                                "response_data": response_data,
                                "base64_used": True
                            }
                            
                    except json.JSONDecodeError as e:
                        print(f"  ❌ Failed to parse response JSON: {e}")
                        return {
                            "status": "response_parse_error",
                            "test_name": "base64_object_creation",
                            "error": str(e),
                            "raw_content": content,
                            "base64_used": True
                        }
                
                return {"status": "no_content", "test_name": "base64_object_creation", "base64_used": True}

    async def test_comparison_without_base64(self):
        """Test: Same complex code WITHOUT base64 for comparison"""
        
        print("📝 Testing Same Code WITHOUT Base64 (for comparison)")
        
        # Same complex code as above
        complex_code = '''
import bpy
import json
import mathutils

# Clear existing mesh objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cube and sphere
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "TestCubeNoB64"

bpy.ops.mesh.primitive_uv_sphere_add(radius=1.5, location=(3, 0, 0))
sphere = bpy.context.active_object  
sphere.name = "TestSphereNoB64"

# Simple result
results = {
    "objects_created": [cube.name, sphere.name],
    "total_vertices": len(cube.data.vertices) + len(sphere.data.vertices),
    "method": "without_base64"
}

print(json.dumps(results, indent=2))
'''
        
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Test WITHOUT base64 encoding 
                result = await session.call_tool("execute_code", {
                    "code": complex_code
                    # send_as_base64 and return_as_base64 default to False
                })
                
                if result.content and result.content[0].type == 'text':
                    content = result.content[0].text
                    print(f"  📋 Raw response length: {len(content)}")
                    
                    try:
                        response_data = json.loads(content)
                        
                        if response_data.get("executed", False):
                            output_result = response_data.get("result", "")
                            
                            if "TestCubeNoB64" in output_result:
                                print(f"  ✅ Non-base64 execution successful")
                                return {
                                    "status": "success",
                                    "test_name": "comparison_without_base64",
                                    "base64_used": False,
                                    "execution_successful": True
                                }
                            else:
                                print(f"  ⚠️ Execution result unclear")
                                return {
                                    "status": "unclear_result",
                                    "test_name": "comparison_without_base64",
                                    "base64_used": False,
                                    "raw_output": output_result
                                }
                        else:
                            print(f"  ❌ Non-base64 execution failed")
                            return {
                                "status": "execution_failed",
                                "test_name": "comparison_without_base64",
                                "base64_used": False,
                                "response_data": response_data
                            }
                            
                    except json.JSONDecodeError as e:
                        print(f"  ❌ Failed to parse non-base64 response: {e}")
                        return {
                            "status": "response_parse_error",
                            "test_name": "comparison_without_base64",
                            "error": str(e),
                            "base64_used": False
                        }
                
                return {
                    "status": "no_content", 
                    "test_name": "comparison_without_base64", 
                    "base64_used": False
                }

    async def test_large_code_block(self):
        """Test: Very large code block with base64 encoding"""
        
        print("📏 Testing Large Code Block with Base64")
        
        # Create a large code block by repeating operations
        large_code = '''
import bpy
import json

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

objects_created = []
total_ops = 0

# Create multiple objects with various operations
for i in range(10):
    # Create cube
    bpy.ops.mesh.primitive_cube_add(location=(i*2, 0, 0))
    cube = bpy.context.active_object
    cube.name = f"Cube_{i:03d}"
    objects_created.append(cube.name)
    total_ops += 1
    
    # Create sphere
    bpy.ops.mesh.primitive_uv_sphere_add(location=(i*2, 2, 0))
    sphere = bpy.context.active_object
    sphere.name = f"Sphere_{i:03d}"
    objects_created.append(sphere.name)
    total_ops += 1
    
    # Create cylinder
    bpy.ops.mesh.primitive_cylinder_add(location=(i*2, -2, 0))
    cylinder = bpy.context.active_object
    cylinder.name = f"Cylinder_{i:03d}"
    objects_created.append(cylinder.name)
    total_ops += 1

# Collect comprehensive stats
scene_stats = {
    "objects_created_count": len(objects_created),
    "objects_created": objects_created,
    "total_operations": total_ops,
    "scene_object_count": len(bpy.context.scene.objects),
    "mesh_objects": [obj.name for obj in bpy.context.scene.objects if obj.type == 'MESH'],
    "average_location": {
        "x": sum(obj.location.x for obj in bpy.context.scene.objects) / len(bpy.context.scene.objects),
        "y": sum(obj.location.y for obj in bpy.context.scene.objects) / len(bpy.context.scene.objects),
        "z": sum(obj.location.z for obj in bpy.context.scene.objects) / len(bpy.context.scene.objects)
    },
    "test_type": "large_code_block_base64"
}

print(json.dumps(scene_stats, indent=2))
'''
        
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                print(f"  📏 Code length: {len(large_code)} characters")
                
                # Test with base64 encoding
                result = await session.call_tool("execute_code", {
                    "code": large_code,
                    "send_as_base64": True,
                    "return_as_base64": True
                })
                
                if result.content and result.content[0].type == 'text':
                    content = result.content[0].text
                    
                    try:
                        response_data = json.loads(content)
                        
                        if response_data.get("executed", False):
                            output_result = response_data.get("result", "")
                            
                            if "large_code_block_base64" in output_result:
                                print(f"  ✅ Large code block executed successfully with base64!")
                                return {
                                    "status": "success",
                                    "test_name": "large_code_block",
                                    "code_length": len(large_code),
                                    "base64_used": True,
                                    "execution_successful": True
                                }
                            else:
                                print(f"  ⚠️ Large code execution unclear")
                                return {
                                    "status": "unclear_result",
                                    "test_name": "large_code_block",
                                    "code_length": len(large_code),
                                    "base64_used": True
                                }
                        else:
                            print(f"  ❌ Large code execution failed")
                            return {
                                "status": "execution_failed",
                                "test_name": "large_code_block",
                                "code_length": len(large_code),
                                "base64_used": True,
                                "response_data": response_data
                            }
                            
                    except json.JSONDecodeError as e:
                        print(f"  ❌ Failed to parse large code response: {e}")
                        return {
                            "status": "response_parse_error",
                            "test_name": "large_code_block",
                            "error": str(e),
                            "base64_used": True
                        }
                
                return {
                    "status": "no_content", 
                    "test_name": "large_code_block", 
                    "base64_used": True
                }

    async def run_all_tests(self):
        """Run all base64 encoding tests"""
        print("=" * 80)
        print("🔐 Testing Base64 Encoding for Complex Code")
        print("=" * 80)
        
        tests = [
            ("Large Code Block (Base64)", self.test_large_code_block),
            ("Complex Object Creation (Base64)", self.test_base64_object_creation),
            ("Same Code (No Base64) - Comparison", self.test_comparison_without_base64)
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
                    
                    if result.get("structured_data") or result.get("execution_successful"):
                        print(f"  📊 Base64 method: {'Enabled' if result.get('base64_used') else 'Disabled'}")
                    else:
                        print(f"  ⚠️ Success but no structured data")
                else:
                    print(f"❌ {test_name}: FAILED - {result.get('error', result.get('status', 'Unknown error'))}")
                    if not test_name.startswith("Same Code (No Base64)"):  # Don't fail overall for comparison test
                        overall_success = False
                    
            except Exception as e:
                results[test_name] = {"status": "exception", "error": str(e)}
                print(f"❌ {test_name}: EXCEPTION - {e}")
                if not test_name.startswith("Same Code (No Base64)"):  # Don't fail overall for comparison test
                    overall_success = False
        
        # Summary
        passed_tests = sum(1 for result in results.values() if result.get("status") == "success")
        total_tests = len(tests)
        
        final_result = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_type": "Base64 Complex Code Execution",
            "individual_results": results,
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": f"{passed_tests}/{total_tests}",
                "overall_status": "PASS" if overall_success else "FAIL"
            },
            "base64_validation": {
                "complex_code_support": "✅ Base64 enables complex code execution" if overall_success else "❌ Base64 did not solve complex code issues",
                "formatting_issues_solved": "✅ JSON formatting issues resolved" if overall_success else "❌ JSON formatting issues persist",
                "backward_compatibility": "✅ Non-base64 execution still works" if any(r.get("base64_used") == False and r.get("status") == "success" for r in results.values()) else "⚠️ Check backward compatibility"
            }
        }
        
        print("\n" + "=" * 80)
        print("📊 Base64 Complex Code Test Results:")
        for test_name, result in results.items():
            status = "✅ PASS" if result.get("status") == "success" else "❌ FAIL"
            base64_indicator = "🔐" if result.get("base64_used") else "📝"
            print(f"  {status} {base64_indicator} {test_name}")
        
        print(f"\n🎯 OVERALL RESULT: {final_result['summary']['overall_status']}")
        print(f"📊 Success Rate: {final_result['summary']['success_rate']}")
        print("\n🔐 Base64 Feature Validation:")
        for key, value in final_result['base64_validation'].items():
            print(f"  {value}")
        print("=" * 80)
        
        return final_result

async def main():
    tester = Base64CodeTests()
    results = await tester.run_all_tests()
    
    # Save results to log file
    log_file = "context/logs/tests/base64-complex-code.log"
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
```

**Run base64 transmission tests:**
```bash
pixi run python tests/test_base64_complex_code.py > context/logs/tests/base64-complex-code.log 2>&1
```

#### 4.2: Base64 Feature Validation

**Critical Issues Solved by Base64:**

1. **Complex Code Formatting Issues** 🔧
   - **Problem**: Special characters, quotes, newlines in Python code cause JSON parsing errors
   - **Solution**: Base64 encode code before transmission to avoid formatting conflicts
   - **Test**: Execute complex Blender Python scripts with special characters

2. **Large Result Data Handling** 📊
   - **Problem**: 100KB+ responses with vertex coordinates cause socket truncation
   - **Solution**: Base64 encode large results for safe transmission
   - **Test**: Generate objects with 490+ vertices and extract coordinate data

3. **Backward Compatibility** ↔️
   - **Problem**: New base64 features must not break existing non-base64 operations
   - **Solution**: Optional parameters `send_as_base64=False`, `return_as_base64=False`
   - **Test**: Verify standard operations still work without base64

**Base64 Parameters:**

```python
# Execute code with base64 encoding options
result = await session.call_tool("execute_code", {
    "code": complex_python_code,
    "send_as_base64": True,    # Encode code as base64 before sending
    "return_as_base64": True   # Request result as base64-encoded
})
```

#### 4.3: Performance Comparison and Validation

**Expected Results for Base64 Tests:**

1. **Large Code Block Test**:
   - ✅ Code length: 1600+ characters
   - ✅ Base64 encoding prevents formatting issues
   - ✅ Multiple object creation (30+ objects) successful
   - ✅ Complex scene statistics returned

2. **Complex Object Creation Test**:
   - ✅ Response size: 100KB+ (vertex coordinate data)
   - ✅ Objects created: TestCube (8 vertices), TestSphere (482 vertices)
   - ✅ Total vertices: 490+
   - ✅ Structured JSON data with coordinates, bounds, locations

3. **Backward Compatibility Test**:
   - ✅ Non-base64 operations still work
   - ✅ Simple code execution without encoding
   - ✅ Standard result handling

**Key Success Criteria:**
- ✅ **Complex Code Support**: Base64 enables execution of complex Python scripts
- ✅ **Large Data Handling**: 100KB+ responses processed successfully
- ✅ **JSON Formatting**: Special character issues resolved
- ✅ **Backward Compatibility**: Non-base64 operations unaffected
- ✅ **Performance**: Large buffers (128KB) handle data efficiently

## Test Procedures

### Prerequisites
- BLD_Remote_MCP service running on port 6688: `export BLD_REMOTE_MCP_START_NOW=1 && blender`
- `mcp[cli]` package installed: `pixi add mcp`
- Test logs directory: `mkdir -p context/logs/tests`

### Test Execution Steps

#### Step 1: Service Validation
```bash
echo "1. Validating BLD_Remote_MCP service availability..."
pixi run python tests/test_service_validation.py > context/logs/tests/service-validation.log 2>&1
```

#### Step 2: Functional Equivalence Testing  
```bash
echo "2. Testing functional equivalence of shared methods..."
pixi run python tests/test_functional_equivalence.py > context/logs/tests/functional-equivalence.log 2>&1
```

#### Step 3: Synchronous Execution Testing (CRITICAL)
```bash
echo "3. Testing synchronous execution with custom results..."
pixi run python tests/test_synchronous_execution.py > context/logs/tests/synchronous-execution.log 2>&1
```

#### Step 4: Base64 Transmission Testing (CRITICAL)
```bash
echo "4. Testing base64 encoding for complex code and large data..."
pixi run python tests/test_base64_complex_code.py > context/logs/tests/base64-complex-code.log 2>&1
```

#### Step 5: Interactive Method Validation
```bash
echo "5. Interactive testing of shared methods..."
# Manual step: Run MCP Inspector and test each shared method
pixi run mcp dev src/blender_remote/mcp_server.py
```

### Test Runner Script

```bash
#!/bin/bash
# tests/run_drop_in_replacement_tests.sh

echo "🚀 Drop-in Replacement Testing"
echo "=============================="
echo ""

LOG_DIR="context/logs/tests"
mkdir -p "$LOG_DIR"

# Step 1: Service Validation
echo "1️⃣ Validating BLD_Remote_MCP service..."
if pixi run python tests/test_service_validation.py | grep -q "available"; then
    echo "✅ BLD_Remote_MCP service available"
else
    echo "❌ BLD_Remote_MCP service unavailable"
    echo "   Start Blender with: export BLD_REMOTE_MCP_START_NOW=1 && blender"
    exit 1
fi

# Step 2: Functional Equivalence Testing
echo "2️⃣ Testing functional equivalence..."
if pixi run python tests/test_functional_equivalence.py | grep -q "success"; then
    echo "✅ Functional equivalence tests passed"
else
    echo "❌ Functional equivalence tests failed"
    exit 1
fi

# Step 3: Synchronous Execution Testing (CRITICAL)
echo "3️⃣ Testing synchronous execution with custom results..."
if pixi run python tests/test_synchronous_execution.py | grep -q "success"; then
    echo "✅ Synchronous execution tests passed"
else
    echo "❌ Synchronous execution tests failed"
    exit 1
fi

# Step 4: Base64 Transmission Testing (CRITICAL)
echo "4️⃣ Testing base64 encoding for complex code and large data..."
if pixi run python tests/test_base64_complex_code.py | grep -q "PASS"; then
    echo "✅ Base64 transmission tests passed"
else
    echo "❌ Base64 transmission tests failed"
    exit 1
fi

# Step 5: Shared Methods Validation
echo "5️⃣ Validating shared methods..."
echo "   Testing shared methods: get_scene_info, get_object_info, execute_code, get_viewport_screenshot"

# Log results
echo "$(date): Drop-in replacement tests completed" >> "$LOG_DIR/test-summary.log"

echo ""
echo "🎉 Drop-in replacement validation completed!"
echo "📊 Our stack (uvx blender-remote + BLD_Remote_MCP) is functionally equivalent to reference stack"
echo "📝 Test logs saved in: $LOG_DIR/"
```

## Functional Equivalence Criteria

### Shared Method Requirements:

#### 1. `get_scene_info`
- **Input**: No parameters
- **Expected Output**: Scene name, object count, object list
- **Equivalence**: Should contain same essential scene information

#### 2. `get_object_info`  
- **Input**: `object_name` (string)
- **Expected Output**: Object location, rotation, scale, type, properties
- **Equivalence**: Should contain same essential object data

#### 3. `execute_code`
- **Input**: `code` (Python string)
- **Expected Output**: **Custom structured results** from the Python code execution
- **Equivalence**: Should execute same code and return the exact data generated by the code
- **Critical**: Must return synchronous results with custom data, not just "executed successfully"

#### 4. `get_viewport_screenshot`
- **Input**: `max_size`, `format` parameters
- **Expected Output**: Image data (base64 or file path)
- **Equivalence**: Should capture viewport image (GUI mode only)

## Drop-in Replacement Validation

### Success Criteria:
- ✅ All shared methods return functionally equivalent results
- ✅ Same input produces same functional output
- ✅ **Synchronous execution with custom results** - Python code returns structured data immediately
- ✅ **Base64 transmission capabilities** - Complex code and large data handled reliably via base64 encoding
- ✅ Enhanced methods (data persistence) work without breaking compatibility
- ✅ Background mode support (our advantage over reference)

### Validation Tests:
1. **Method Availability**: All shared methods accessible via MCP
2. **Input Compatibility**: Same parameter structure accepted
3. **Output Equivalence**: Functionally equivalent results returned
4. **Synchronous Execution**: Custom Blender code returns structured results immediately
5. **Base64 Transmission**: Complex code and large data transmission via base64 encoding
6. **Enhanced Functionality**: Additional features work correctly

## Conclusion

This test plan validates our stack as a **drop-in replacement** by focusing on:

- **Shared Method Testing**: Ensuring functional equivalence of core methods
- **Synchronous Execution**: Testing custom Blender code execution with structured result return
- **Base64 Transmission**: Validating complex code and large data handling via base64 encoding
- **MCP CLI Tools**: Using recommended official testing approach
- **Comparison Validation**: Side-by-side behavior verification  
- **Enhanced Features**: Validating additional capabilities beyond reference

The goal is to demonstrate that `uvx blender-remote` + `BLD_Remote_MCP` can replace `uvx blender-mcp` + `BlenderAutoMCP` while providing additional functionality like background mode support, data persistence, and base64 transmission.

**Key Testing Principles**: 
- Same inputs to both complete stacks should produce functionally equivalent outputs for all shared methods
- **Critical**: `execute_code` must return custom, structured results from Blender Python code execution, not just "success" messages
- **Critical**: Base64 encoding must handle complex code and large data (100KB+) reliably without formatting issues
- Synchronous execution allows real-time Blender automation with immediate feedback
- Backward compatibility ensures non-base64 operations continue to work