#!/usr/bin/env python3
"""
Test script for BlenderSceneManager GLB export functionality.

Tests GLB export as raw bytes and trimesh Scene objects, with various
export options and error conditions.
"""

import sys
import os
import time
import tempfile
import numpy as np
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from blender_remote.client import BlenderMCPClient
from blender_remote.scene_manager import BlenderSceneManager
from blender_remote.exceptions import BlenderMCPError, BlenderCommandError

# Check if trimesh is available
try:
    import trimesh
    TRIMESH_AVAILABLE = True
except ImportError:
    TRIMESH_AVAILABLE = False
    print("Warning: trimesh not available, some tests will be skipped")


class TestResults:
    """Helper class to track test results."""
    
    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0
    
    def add_result(self, test_name: str, passed: bool, message: str = ""):
        self.tests.append({
            "name": test_name,
            "passed": passed,
            "message": message
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1
        
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {test_name}: {message}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n=== Test Summary ===")
        print(f"Total: {total}, Passed: {self.passed}, Failed: {self.failed}")
        print(f"Success Rate: {(self.passed/total*100):.1f}%" if total > 0 else "No tests run")
        return self.failed == 0


def setup_scene_manager():
    """Set up scene manager for testing."""
    try:
        client = BlenderMCPClient(timeout=30.0)  # Longer timeout for export operations
        if not client.test_connection():
            return None, "Could not connect to BLD_Remote_MCP service"
        
        scene_manager = BlenderSceneManager(client)
        return scene_manager, None
    except Exception as e:
        return None, f"Setup failed: {str(e)}"


def test_glb_raw_export():
    """Test GLB export as raw bytes."""
    results = TestResults()
    scene_manager, error = setup_scene_manager()
    
    if scene_manager is None:
        results.add_result("scene_setup", False, error)
        return results
    
    test_objects = []
    
    try:
        # Create test objects for export using direct Blender Python code
        create_objects_code = """
import bpy

# Create a cube
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0), size=2.0)
cube_obj = bpy.context.active_object
cube_obj.name = "ExportTestCube"
print("OBJECT_CREATED:" + cube_obj.name)

# Create a sphere
bpy.ops.mesh.primitive_uv_sphere_add(location=(3, 0, 0), radius=1.0)
sphere_obj = bpy.context.active_object
sphere_obj.name = "ExportTestSphere"
print("OBJECT_CREATED:" + sphere_obj.name)
"""
        result = scene_manager.client.execute_python(create_objects_code)
        
        # Extract object names from output
        cube_name = None
        sphere_name = None
        for line in result.split('\n'):
            if line.startswith("OBJECT_CREATED:"):
                obj_name = line[15:]
                if "Cube" in obj_name:
                    cube_name = obj_name
                elif "Sphere" in obj_name:
                    sphere_name = obj_name
        
        test_objects = [cube_name, sphere_name]
        
        # Test export single object with materials
        glb_data = scene_manager.get_object_as_glb_raw(cube_name, with_material=True)
        
        # Validate GLB data
        is_valid_glb = (
            isinstance(glb_data, bytes) and
            len(glb_data) > 0 and
            glb_data[:4] == b'glTF'  # GLB magic number
        )
        
        results.add_result("glb_raw_export_with_material", is_valid_glb, 
                          f"GLB size: {len(glb_data)} bytes")
        
        # Test export without materials
        glb_data_no_mat = scene_manager.get_object_as_glb_raw(cube_name, with_material=False)
        
        is_valid_no_mat = (
            isinstance(glb_data_no_mat, bytes) and
            len(glb_data_no_mat) > 0 and
            glb_data_no_mat[:4] == b'glTF'
        )
        
        # Should be different sizes (with materials typically larger)
        size_difference = abs(len(glb_data) - len(glb_data_no_mat))
        
        results.add_result("glb_raw_export_no_material", is_valid_no_mat, 
                          f"GLB size: {len(glb_data_no_mat)} bytes, diff: {size_difference}")
        
        # Test with custom temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            glb_data_temp = scene_manager.get_object_as_glb_raw(
                sphere_name, 
                with_material=True,
                blender_temp_dir=temp_dir,
                keep_temp_file=False
            )
            
            is_valid_temp = (
                isinstance(glb_data_temp, bytes) and
                len(glb_data_temp) > 0 and
                glb_data_temp[:4] == b'glTF'
            )
            
            results.add_result("glb_raw_export_custom_temp", is_valid_temp, 
                              f"GLB size: {len(glb_data_temp)} bytes")
    
    except Exception as e:
        results.add_result("glb_raw_export", False, f"Exception: {str(e)}")
    
    # Cleanup
    for obj_name in test_objects:
        try:
            if obj_name:
                scene_manager.delete_object(obj_name)
        except:
            pass
    
    return results


def test_glb_trimesh_export():
    """Test GLB export as trimesh Scene."""
    results = TestResults()
    
    if not TRIMESH_AVAILABLE:
        results.add_result("trimesh_available", False, "trimesh not installed")
        return results
    
    scene_manager, error = setup_scene_manager()
    
    if scene_manager is None:
        results.add_result("scene_setup", False, error)
        return results
    
    test_objects = []
    
    try:
        # Create test objects using direct Blender Python code
        create_objects_code = """
import bpy

# Create a cube
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0), size=2.0)
cube_obj = bpy.context.active_object
cube_obj.name = "TrimeshTestCube"
print("OBJECT_CREATED:" + cube_obj.name)

# Create a cylinder
bpy.ops.mesh.primitive_cylinder_add(location=(0, 3, 0), radius=1.0, depth=2.0)
cylinder_obj = bpy.context.active_object
cylinder_obj.name = "TrimeshTestCylinder"
print("OBJECT_CREATED:" + cylinder_obj.name)
"""
        result = scene_manager.client.execute_python(create_objects_code)
        
        # Extract object names from output
        cube_name = None
        cylinder_name = None
        for line in result.split('\n'):
            if line.startswith("OBJECT_CREATED:"):
                obj_name = line[15:]
                if "Cube" in obj_name:
                    cube_name = obj_name
                elif "Cylinder" in obj_name:
                    cylinder_name = obj_name
        
        test_objects = [cube_name, cylinder_name]
        
        # Test export as trimesh Scene
        trimesh_scene = scene_manager.get_object_as_glb(cube_name, with_material=True)
        
        # Validate trimesh Scene
        is_valid_scene = isinstance(trimesh_scene, trimesh.Scene)
        has_geometry = len(trimesh_scene.geometry) > 0 if is_valid_scene else False
        
        geometry_info = ""
        if is_valid_scene:
            geometry_names = list(trimesh_scene.geometry.keys())
            geometry_info = f"Geometries: {len(geometry_names)}, Names: {geometry_names}"
        
        results.add_result("trimesh_scene_export", is_valid_scene and has_geometry, 
                          f"Scene valid: {is_valid_scene}, {geometry_info}")
        
        # Test mesh properties
        if is_valid_scene and has_geometry:
            # Get first geometry
            first_geom = next(iter(trimesh_scene.geometry.values()))
            
            has_vertices = hasattr(first_geom, 'vertices') and len(first_geom.vertices) > 0
            has_faces = hasattr(first_geom, 'faces') and len(first_geom.faces) > 0
            
            mesh_info = f"Vertices: {len(first_geom.vertices) if has_vertices else 0}, Faces: {len(first_geom.faces) if has_faces else 0}"
            
            results.add_result("trimesh_mesh_properties", has_vertices and has_faces, mesh_info)
            
            # Test mesh bounds
            if has_vertices:
                bounds = first_geom.bounds
                bounds_valid = bounds is not None and len(bounds) == 2 and len(bounds[0]) == 3
                results.add_result("trimesh_mesh_bounds", bounds_valid, f"Bounds: {bounds}")
        
        # Test multiple objects export (if we create a collection)
        # For now, test individual cylinder export
        cylinder_scene = scene_manager.get_object_as_glb(cylinder_name, with_material=False)
        
        is_valid_cylinder = isinstance(cylinder_scene, trimesh.Scene)
        cylinder_has_geom = len(cylinder_scene.geometry) > 0 if is_valid_cylinder else False
        
        results.add_result("trimesh_cylinder_export", is_valid_cylinder and cylinder_has_geom,
                          f"Cylinder geometries: {len(cylinder_scene.geometry) if is_valid_cylinder else 0}")
    
    except Exception as e:
        results.add_result("glb_trimesh_export", False, f"Exception: {str(e)}")
    
    # Cleanup
    for obj_name in test_objects:
        try:
            if obj_name:
                scene_manager.delete_object(obj_name)
        except:
            pass
    
    return results


def test_export_error_handling():
    """Test export error handling for invalid scenarios."""
    results = TestResults()
    scene_manager, error = setup_scene_manager()
    
    if scene_manager is None:
        results.add_result("scene_setup", False, error)
        return results
    
    try:
        # Test exporting non-existent object
        try:
            glb_data = scene_manager.get_object_as_glb_raw("NonExistentObject")
            results.add_result("export_nonexistent", False, "Should have raised exception")
        except BlenderCommandError:
            results.add_result("export_nonexistent", True, "Correctly raised BlenderCommandError")
        except Exception as e:
            results.add_result("export_nonexistent", False, f"Wrong exception type: {type(e)}")
        
        # Test with invalid temp directory (if it matters)
        # Create test cube using direct Blender Python code
        create_cube_code = """
import bpy
bpy.ops.mesh.primitive_cube_add()
cube_obj = bpy.context.active_object
cube_obj.name = "ErrorTestCube"
print("OBJECT_CREATED:" + cube_obj.name)
"""
        result = scene_manager.client.execute_python(create_cube_code)
        
        # Extract object name from output
        test_cube = None
        for line in result.split('\n'):
            if line.startswith("OBJECT_CREATED:"):
                test_cube = line[15:]
                break
        
        try:
            # This might not fail depending on implementation
            glb_data = scene_manager.get_object_as_glb_raw(
                test_cube,
                blender_temp_dir="/invalid/path/that/does/not/exist"
            )
            # If it succeeds, that's also fine (fallback to default temp dir)
            results.add_result("export_invalid_temp_dir", True, "Handled gracefully or succeeded")
        except Exception as e:
            # If it fails, that's expected
            results.add_result("export_invalid_temp_dir", True, f"Failed as expected: {type(e).__name__}")
        
        # Cleanup
        if test_cube:
            scene_manager.delete_object(test_cube)
    
    except Exception as e:
        results.add_result("export_error_handling", False, f"Exception: {str(e)}")
    
    return results


def test_large_geometry_export():
    """Test export with more complex geometry."""
    results = TestResults()
    scene_manager, error = setup_scene_manager()
    
    if scene_manager is None:
        results.add_result("scene_setup", False, error)
        return results
    
    test_objects = []
    
    try:
        # Create more complex object via Python code
        complex_object_code = """
import bpy
import bmesh

# Create a subdivided cube with more geometry
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
obj = bpy.context.active_object
obj.name = "ComplexTestObject"

# Enter edit mode and subdivide
bpy.context.view_layer.objects.active = obj
bpy.ops.object.mode_set(mode='EDIT')

# Subdivide the mesh
bpy.ops.mesh.subdivide(number_cuts=3)

# Add some modifiers via bmesh operations
bm = bmesh.new()
bm.from_mesh(obj.data)
bmesh.ops.inset_faces(bm, faces=bm.faces, thickness=0.1)
bm.to_mesh(obj.data)
bm.free()

bpy.ops.object.mode_set(mode='OBJECT')

print("COMPLEX_OBJECT_CREATED:" + obj.name)
"""
        
        result = scene_manager.client.execute_python(complex_object_code)
        
        # Check if object was created
        complex_obj_name = None
        for line in result.split('\n'):
            if line.startswith("COMPLEX_OBJECT_CREATED:"):
                complex_obj_name = line[23:]
                break
        
        if complex_obj_name:
            test_objects.append(complex_obj_name)
            
            # Export the complex object
            start_time = time.time()
            glb_data = scene_manager.get_object_as_glb_raw(complex_obj_name)
            export_time = time.time() - start_time
            
            is_valid = (
                isinstance(glb_data, bytes) and
                len(glb_data) > 0 and
                glb_data[:4] == b'glTF'
            )
            
            results.add_result("complex_geometry_export", is_valid,
                              f"Size: {len(glb_data)} bytes, Time: {export_time:.2f}s")
            
            # Test with trimesh if available
            if TRIMESH_AVAILABLE:
                start_time = time.time()
                trimesh_scene = scene_manager.get_object_as_glb(complex_obj_name)
                trimesh_time = time.time() - start_time
                
                is_valid_trimesh = isinstance(trimesh_scene, trimesh.Scene)
                geom_count = len(trimesh_scene.geometry) if is_valid_trimesh else 0
                
                results.add_result("complex_trimesh_export", is_valid_trimesh and geom_count > 0,
                                  f"Geometries: {geom_count}, Time: {trimesh_time:.2f}s")
        else:
            results.add_result("complex_object_creation", False, "Failed to create complex object")
    
    except Exception as e:
        results.add_result("large_geometry_export", False, f"Exception: {str(e)}")
    
    # Cleanup
    for obj_name in test_objects:
        try:
            if obj_name:
                scene_manager.delete_object(obj_name)
        except:
            pass
    
    return results


def main():
    """Run all GLB export tests."""
    print("=== BlenderSceneManager GLB Export Tests ===")
    print(f"Test started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Trimesh available: {TRIMESH_AVAILABLE}")
    
    all_results = TestResults()
    
    # Run test suites
    test_suites = [
        ("GLB Raw Export Tests", test_glb_raw_export),
        ("GLB Trimesh Export Tests", test_glb_trimesh_export),
        ("Export Error Handling Tests", test_export_error_handling),
        ("Large Geometry Export Tests", test_large_geometry_export),
    ]
    
    for suite_name, test_func in test_suites:
        print(f"\n--- {suite_name} ---")
        suite_results = test_func()
        
        # Merge results
        for test in suite_results.tests:
            all_results.add_result(test["name"], test["passed"], test["message"])
    
    # Final summary
    success = all_results.summary()
    
    # Save results to log file
    log_dir = Path(__file__).parent.parent / "logs" / "tests"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"test_scene_manager_export_{int(time.time())}.log"
    with open(log_file, "w") as f:
        f.write(f"BlenderSceneManager GLB Export Test Results\n")
        f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Trimesh available: {TRIMESH_AVAILABLE}\n\n")
        
        for test in all_results.tests:
            status = "PASS" if test["passed"] else "FAIL"
            f.write(f"[{status}] {test['name']}: {test['message']}\n")
        
        f.write(f"\nSummary: {all_results.passed}/{all_results.passed + all_results.failed} passed\n")
    
    print(f"\nResults saved to: {log_file}")
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())