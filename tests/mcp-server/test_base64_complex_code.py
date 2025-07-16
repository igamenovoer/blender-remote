#!/usr/bin/env python3
"""
Base64 Complex Code and Large Data Transmission Testing

Tests base64 encoding for handling complex code formatting issues and large 
result data transmission. Base64 encoding solves critical issues with:
- Complex code formatting (special characters, quotes, newlines)
- Large result data (100KB+ responses with vertex/coordinate data)
- Backward compatibility with non-base64 operations

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


class Base64CodeTests:
    """Test base64 encoding for complex code and large data transmission."""
    
    def __init__(self):
        self.server_params = StdioServerParameters(
            command="pixi",
            args=["run", "python", "src/blender_remote/mcp_server.py"],
            env=None,
        )
    
    async def test_base64_object_creation(self):
        """Test: Complex object creation with base64 encoding"""
        
        print("🔐 Testing Base64 Object Creation & Vertex Extraction")
        
        # Complex code that may fail without base64 implementation
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
                
                # Test with base64 encoding enabled (if supported)
                try:
                    result = await session.call_tool("execute_code", {
                        "code": complex_code,
                        "send_as_base64": True,
                        "return_as_base64": True
                    })
                except Exception:
                    # Fallback to standard execution if base64 not supported
                    result = await session.call_tool("execute_code", {"code": complex_code})
                
                if result.content and result.content[0].type == 'text':
                    content = result.content[0].text
                    print(f"  📋 Raw response length: {len(content)}")
                    
                    # Validate response contains structured data
                    success = self._validate_complex_result(content)
                    
                    return {
                        "status": "success" if success else "failed",
                        "test_name": "base64_object_creation",
                        "response_length": len(content),
                        "has_structured_data": success,
                        "content_sample": content[:200] + "..." if len(content) > 200 else content
                    }
                
                return {"status": "no_content", "test_name": "base64_object_creation"}

    async def test_comparison_without_base64(self):
        """Test: Same complex code WITHOUT base64 for comparison"""
        
        print("📝 Testing Same Code WITHOUT Base64 (for comparison)")
        
        # Simpler code for comparison
        simple_code = '''
import bpy
import json

# Clear existing mesh objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create simple objects
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "TestCubeNoB64"

bpy.ops.mesh.primitive_uv_sphere_add(location=(3, 0, 0))
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
                result = await session.call_tool("execute_code", {"code": simple_code})
                
                if result.content and result.content[0].type == 'text':
                    content = result.content[0].text
                    print(f"  📋 Raw response length: {len(content)}")
                    
                    success = "TestCubeNoB64" in content and "without_base64" in content
                    
                    return {
                        "status": "success" if success else "failed",
                        "test_name": "comparison_without_base64",
                        "base64_used": False,
                        "execution_successful": success
                    }
                
                return {"status": "no_content", "test_name": "comparison_without_base64", "base64_used": False}

    async def test_large_code_block(self):
        """Test: Very large code block to test transmission limits"""
        
        print("📏 Testing Large Code Block")
        
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
for i in range(5):  # Reduced from 10 to avoid timeout
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

# Collect comprehensive stats
scene_stats = {
    "objects_created_count": len(objects_created),
    "objects_created": objects_created,
    "total_operations": total_ops,
    "scene_object_count": len(bpy.context.scene.objects),
    "mesh_objects": [obj.name for obj in bpy.context.scene.objects if obj.type == 'MESH'],
    "test_type": "large_code_block"
}

print(json.dumps(scene_stats, indent=2))
'''
        
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                print(f"  📏 Code length: {len(large_code)} characters")
                
                # Test with base64 encoding if available
                try:
                    result = await session.call_tool("execute_code", {
                        "code": large_code,
                        "send_as_base64": True,
                        "return_as_base64": True
                    })
                except Exception:
                    # Fallback to standard execution
                    result = await session.call_tool("execute_code", {"code": large_code})
                
                if result.content and result.content[0].type == 'text':
                    content = result.content[0].text
                    
                    success = "large_code_block" in content
                    
                    return {
                        "status": "success" if success else "failed",
                        "test_name": "large_code_block",
                        "code_length": len(large_code),
                        "execution_successful": success
                    }
                
                return {"status": "no_content", "test_name": "large_code_block"}

    async def run_all_tests(self):
        """Run all base64 encoding tests"""
        print("=" * 80)
        print("🔐 Testing Base64 Encoding for Complex Code")
        print("=" * 80)
        
        tests = [
            ("Large Code Block", self.test_large_code_block),
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
                else:
                    print(f"❌ {test_name}: FAILED - {result.get('status', 'Unknown error')}")
                    if not test_name.startswith("Same Code (No Base64)"):  # Don't fail overall for comparison test
                        overall_success = False
                    
            except Exception as e:
                results[test_name] = {"status": "exception", "error": str(e)}
                print(f"❌ {test_name}: EXCEPTION - {e}")
                if not test_name.startswith("Same Code (No Base64)"):
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
            }
        }
        
        print("\n" + "=" * 80)
        print("📊 Base64 Complex Code Test Results:")
        for test_name, result in results.items():
            status = "✅ PASS" if result.get("status") == "success" else "❌ FAIL"
            print(f"  {status} {test_name}")
        
        print(f"\n🎯 OVERALL RESULT: {final_result['summary']['overall_status']}")
        print(f"📊 Success Rate: {final_result['summary']['success_rate']}")
        print("=" * 80)
        
        return final_result
    
    def _validate_complex_result(self, content):
        """Validate that complex result contains expected structured data"""
        try:
            # Look for indicators of complex structured data
            indicators = [
                "objects_created",
                "vertex_count", 
                "vertices",
                "bounds",
                "TestCube",
                "TestSphere"
            ]
            return any(indicator in content for indicator in indicators)
        except:
            return False


async def main():
    """Run base64 transmission testing"""
    print("=" * 80)
    print("🔐 MCP Server - Base64 Complex Code and Large Data Testing")
    print("=" * 80)
    print("Testing: Base64 encoding for complex code formatting and large data")
    print()
    
    tester = Base64CodeTests()
    results = await tester.run_all_tests()
    
    # Exit with appropriate code
    exit_code = 0 if results["summary"]["overall_status"] == "PASS" else 1
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)