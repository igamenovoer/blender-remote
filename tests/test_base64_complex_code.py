#!/usr/bin/env python3
"""
Test Base64 Encoding for Complex Code Execution
Goal: Verify that base64 encoding solves the formatting issues with large/complex code blocks
"""

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
        
        print("[ENCODE] Testing Base64 Object Creation & Vertex Extraction")
        
        # This is the same complex code that was failing before
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
                    print(f"  [INFO] Raw response length: {len(content)}")
                    
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
                                    # First try to parse the entire output as JSON
                                    parsed_result = json.loads(output_result.strip())
                                    
                                    print(f"  [PASS] Successfully parsed JSON result!")
                                    print(f"  [STATS] Objects created: {parsed_result.get('objects_created', [])}")
                                    print(f"  [STATS] Total vertices: {parsed_result.get('total_vertices', 0)}")
                                    print(f"  [STATS] Cube vertices: {parsed_result.get('cube_data', {}).get('vertex_count', 0)}")
                                    print(f"  [STATS] Sphere vertices: {parsed_result.get('sphere_data', {}).get('vertex_count', 0)}")
                                    
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
                                    print(f"  [FAIL] Failed to parse JSON from output: {e}")
                                    return {
                                        "status": "json_parse_error",
                                        "test_name": "base64_object_creation",
                                        "error": str(e),
                                        "raw_output": output_result,
                                        "base64_used": True
                                    }
                            else:
                                print(f"  [WARNING] Execution successful but no result output")
                                return {
                                    "status": "no_output",
                                    "test_name": "base64_object_creation",
                                    "response_data": response_data,
                                    "base64_used": True
                                }
                        else:
                            print(f"  [FAIL] Code execution failed")
                            return {
                                "status": "execution_failed",
                                "test_name": "base64_object_creation",
                                "response_data": response_data,
                                "base64_used": True
                            }
                            
                    except json.JSONDecodeError as e:
                        print(f"  [FAIL] Failed to parse response JSON: {e}")
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
        
        print("[LOG] Testing Same Code WITHOUT Base64 (for comparison)")
        
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
                    print(f"  [INFO] Raw response length: {len(content)}")
                    
                    try:
                        response_data = json.loads(content)
                        
                        if response_data.get("executed", False):
                            output_result = response_data.get("result", "")
                            
                            if "TestCubeNoB64" in output_result:
                                print(f"  [PASS] Non-base64 execution successful")
                                return {
                                    "status": "success",
                                    "test_name": "comparison_without_base64",
                                    "base64_used": False,
                                    "execution_successful": True
                                }
                            else:
                                print(f"  [WARNING] Execution result unclear")
                                return {
                                    "status": "unclear_result",
                                    "test_name": "comparison_without_base64",
                                    "base64_used": False,
                                    "raw_output": output_result
                                }
                        else:
                            print(f"  [FAIL] Non-base64 execution failed")
                            return {
                                "status": "execution_failed",
                                "test_name": "comparison_without_base64",
                                "base64_used": False,
                                "response_data": response_data
                            }
                            
                    except json.JSONDecodeError as e:
                        print(f"  [FAIL] Failed to parse non-base64 response: {e}")
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
        
        print("[SIZE] Testing Large Code Block with Base64")
        
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
                
                print(f"  [SIZE] Code length: {len(large_code)} characters")
                
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
                                print(f"  [PASS] Large code block executed successfully with base64!")
                                return {
                                    "status": "success",
                                    "test_name": "large_code_block",
                                    "code_length": len(large_code),
                                    "base64_used": True,
                                    "execution_successful": True
                                }
                            else:
                                print(f"  [WARNING] Large code execution unclear")
                                return {
                                    "status": "unclear_result",
                                    "test_name": "large_code_block",
                                    "code_length": len(large_code),
                                    "base64_used": True
                                }
                        else:
                            print(f"  [FAIL] Large code execution failed")
                            return {
                                "status": "execution_failed",
                                "test_name": "large_code_block",
                                "code_length": len(large_code),
                                "base64_used": True,
                                "response_data": response_data
                            }
                            
                    except json.JSONDecodeError as e:
                        print(f"  [FAIL] Failed to parse large code response: {e}")
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
        print("[ENCODE] Testing Base64 Encoding for Complex Code")
        print("=" * 80)
        
        tests = [
            ("Large Code Block (Base64)", self.test_large_code_block),
            ("Complex Object Creation (Base64)", self.test_base64_object_creation),
            ("Same Code (No Base64) - Comparison", self.test_comparison_without_base64)
        ]
        
        results = {}
        overall_success = True
        
        for test_name, test_func in tests:
            print(f"\n[INFO] Running: {test_name}")
            try:
                result = await test_func()
                results[test_name] = result
                
                if result["status"] == "success":
                    print(f"[PASS] {test_name}: PASSED")
                    
                    if result.get("structured_data") or result.get("execution_successful"):
                        print(f"  [STATS] Base64 method: {'Enabled' if result.get('base64_used') else 'Disabled'}")
                    else:
                        print(f"  [WARNING] Success but no structured data")
                else:
                    print(f"[FAIL] {test_name}: FAILED - {result.get('error', result.get('status', 'Unknown error'))}")
                    if not test_name.startswith("Same Code (No Base64)"):  # Don't fail overall for comparison test
                        overall_success = False
                    
            except Exception as e:
                results[test_name] = {"status": "exception", "error": str(e)}
                print(f"[FAIL] {test_name}: EXCEPTION - {e}")
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
                "complex_code_support": "[PASS] Base64 enables complex code execution" if overall_success else "[FAIL] Base64 did not solve complex code issues",
                "formatting_issues_solved": "[PASS] JSON formatting issues resolved" if overall_success else "[FAIL] JSON formatting issues persist",
                "backward_compatibility": "[PASS] Non-base64 execution still works" if any(r.get("base64_used") == False and r.get("status") == "success" for r in results.values()) else "[WARNING] Check backward compatibility"
            }
        }
        
        print("\n" + "=" * 80)
        print("[STATS] Base64 Complex Code Test Results:")
        for test_name, result in results.items():
            status = "[PASS] PASS" if result.get("status") == "success" else "[FAIL] FAIL"
            base64_indicator = "[ENCODE]" if result.get("base64_used") else "[LOG]"
            print(f"  {status} {base64_indicator} {test_name}")
        
        print(f"\n[RESULT] OVERALL RESULT: {final_result['summary']['overall_status']}")
        print(f"[STATS] Success Rate: {final_result['summary']['success_rate']}")
        print("\n[ENCODE] Base64 Feature Validation:")
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
        print(f"[LOG] Results saved to: {log_file}")
    except Exception as e:
        print(f"[WARNING] Could not save results: {e}")
    
    # Exit with appropriate code
    sys.exit(0 if results["summary"]["overall_status"] == "PASS" else 1)

if __name__ == "__main__":
    results = asyncio.run(main())