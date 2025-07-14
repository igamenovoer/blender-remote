#!/usr/bin/env python3
"""
Test script for BlenderSceneManager object manipulation functionality.

Tests object creation, modification, deletion, and scene operations.
"""

import sys
import os
import time
import numpy as np
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from blender_remote.client import BlenderMCPClient
from blender_remote.scene_manager import BlenderSceneManager
from blender_remote.data_types import SceneObject
from blender_remote.exceptions import BlenderMCPError


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
        client = BlenderMCPClient(timeout=15.0)
        if not client.test_connection():
            return None, "Could not connect to BLD_Remote_MCP service"
        
        scene_manager = BlenderSceneManager(client)
        return scene_manager, None
    except Exception as e:
        return None, f"Setup failed: {str(e)}"


def test_scene_info():
    """Test scene information retrieval."""
    results = TestResults()
    scene_manager, error = setup_scene_manager()
    
    if scene_manager is None:
        results.add_result("scene_setup", False, error)
        return results
    
    try:
        # Test get_scene_summary
        summary = scene_manager.get_scene_summary()
        has_objects = "objects" in summary
        results.add_result("get_scene_summary", has_objects, f"Objects found: {len(summary.get('objects', []))}")
        
        # Test get_scene_info (structured data)
        scene_info = scene_manager.get_scene_info()
        has_typed_objects = hasattr(scene_info, 'objects') and isinstance(scene_info.objects, list)
        results.add_result("get_scene_info", has_typed_objects, f"SceneInfo objects: {len(scene_info.objects)}")
        
        # Test list_objects
        objects = scene_manager.list_objects()
        results.add_result("list_objects", isinstance(objects, list), f"Found {len(objects)} objects")
        
        # Test list_objects with type filter
        cameras = scene_manager.list_objects(object_type="CAMERA")
        results.add_result("list_objects_filtered", isinstance(cameras, list), f"Found {len(cameras)} cameras")
        
    except Exception as e:
        results.add_result("scene_info_test", False, f"Exception: {str(e)}")
    
    return results


# test_primitive_creation function removed - primitive creation methods no longer supported in BlenderSceneManager


def test_object_manipulation():
    """Test object movement and property updates."""
    results = TestResults()
    scene_manager, error = setup_scene_manager()
    
    if scene_manager is None:
        results.add_result("scene_setup", False, error)
        return results
    
    test_object = None
    
    try:
        # Create test object using direct Blender Python code
        create_cube_code = """
import bpy
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
cube_obj = bpy.context.active_object
cube_obj.name = "ManipulationTest"
print("OBJECT_CREATED:" + cube_obj.name)
"""
        result = scene_manager.client.execute_python(create_cube_code)
        
        # Extract object name from output
        test_object = None
        for line in result.split('\n'):
            if line.startswith("OBJECT_CREATED:"):
                test_object = line[15:]
                break
        results.add_result("create_test_object", bool(test_object), f"Created: {test_object}")
        
        if test_object:
            # Test move_object
            new_location = [3, 2, 1]
            move_success = scene_manager.move_object(test_object, new_location)
            results.add_result("move_object", move_success, f"Moved to {new_location}")
            
            # Test update_scene_objects with SceneObject
            scene_obj = SceneObject(
                name=test_object,
                type="MESH",
                location=np.array([1, 1, 1]),
                rotation=np.array([1, 0, 0, 0]),  # quaternion
                scale=np.array([2, 2, 2]),
                visible=True
            )
            
            update_results = scene_manager.update_scene_objects([scene_obj])
            update_success = update_results.get(test_object, False)
            results.add_result("update_scene_objects", update_success, f"Update result: {update_results}")
            
            # Verify object properties changed
            objects = scene_manager.list_objects()
            updated_obj = None
            for obj in objects:
                if test_object in obj.name:
                    updated_obj = obj
                    break
            
            if updated_obj:
                location_close = np.allclose(updated_obj.location, [1, 1, 1], atol=0.1)
                scale_close = np.allclose(updated_obj.scale, [2, 2, 2], atol=0.1)
                results.add_result("verify_updates", location_close and scale_close, 
                                 f"Location: {updated_obj.location}, Scale: {updated_obj.scale}")
    
    except Exception as e:
        results.add_result("object_manipulation", False, f"Exception: {str(e)}")
    
    # Cleanup
    if test_object:
        try:
            scene_manager.delete_object(test_object)
        except:
            pass
    
    return results


def test_scene_operations():
    """Test scene-wide operations like clear_scene."""
    results = TestResults()
    scene_manager, error = setup_scene_manager()
    
    if scene_manager is None:
        results.add_result("scene_setup", False, error)
        return results
    
    created_objects = []
    
    try:
        # Create multiple test objects using direct Blender Python code
        create_objects_code = """
import bpy
for i in range(3):
    bpy.ops.mesh.primitive_cube_add(location=(i*2, 0, 0))
    cube_obj = bpy.context.active_object
    cube_obj.name = f"ClearTest_{i}"
    print("OBJECT_CREATED:" + cube_obj.name)
"""
        result = scene_manager.client.execute_python(create_objects_code)
        
        # Extract object names from output
        for line in result.split('\n'):
            if line.startswith("OBJECT_CREATED:"):
                obj_name = line[15:]
                created_objects.append(obj_name)
        
        results.add_result("create_multiple_objects", len(created_objects) == 3, 
                          f"Created {len(created_objects)} objects")
        
        # Get initial object count
        initial_objects = scene_manager.list_objects()
        initial_count = len(initial_objects)
        
        # Test clear_scene (but keep camera and light)
        clear_success = scene_manager.clear_scene(keep_camera=True, keep_light=True)
        results.add_result("clear_scene", clear_success, "Clear scene executed")
        
        # Verify objects were removed
        final_objects = scene_manager.list_objects()
        final_count = len(final_objects)
        
        # Should have fewer objects now (at least the 3 we created should be gone)
        objects_removed = initial_count - final_count >= len(created_objects)
        results.add_result("verify_clear", objects_removed, 
                          f"Objects before: {initial_count}, after: {final_count}")
        
        # Verify camera and lights still exist
        remaining_objects = scene_manager.list_objects()
        has_camera = any(obj.type == "CAMERA" for obj in remaining_objects)
        has_light = any(obj.type == "LIGHT" for obj in remaining_objects)
        
        results.add_result("keep_camera", has_camera, "Camera preserved")
        results.add_result("keep_light", has_light, "Light preserved")
    
    except Exception as e:
        results.add_result("scene_operations", False, f"Exception: {str(e)}")
    
    return results


def test_error_handling():
    """Test error handling for invalid operations."""
    results = TestResults()
    scene_manager, error = setup_scene_manager()
    
    if scene_manager is None:
        results.add_result("scene_setup", False, error)
        return results
    
    try:
        # Test deleting non-existent object
        delete_result = scene_manager.delete_object("NonExistentObject")
        results.add_result("delete_nonexistent", not delete_result, 
                          f"Delete returned: {delete_result}")
        
        # Test moving non-existent object
        move_result = scene_manager.move_object("NonExistentObject", [0, 0, 0])
        results.add_result("move_nonexistent", not move_result, 
                          f"Move returned: {move_result}")
        
        # Test invalid parameter handling - we'll test with invalid object type
        try:
            # Test directly with invalid Blender operations
            invalid_code = """
import bpy
bpy.ops.mesh.primitive_nonexistent_add()  # This should fail
"""
            scene_manager.client.execute_python(invalid_code)
            results.add_result("invalid_operation", False, "Should have raised exception")
        except Exception as e:
            results.add_result("invalid_operation", True, f"Correctly raised exception: {type(e).__name__}")
    
    except Exception as e:
        results.add_result("error_handling", False, f"Exception: {str(e)}")
    
    return results


def main():
    """Run all scene manager object tests."""
    print("=== BlenderSceneManager Object Tests ===")
    print(f"Test started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_results = TestResults()
    
    # Run test suites
    test_suites = [
        ("Scene Information Tests", test_scene_info),
        # Primitive Creation Tests removed - methods no longer supported
        ("Object Manipulation Tests", test_object_manipulation),
        ("Scene Operations Tests", test_scene_operations),
        ("Error Handling Tests", test_error_handling),
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
    
    log_file = log_dir / f"test_scene_manager_objects_{int(time.time())}.log"
    with open(log_file, "w") as f:
        f.write(f"BlenderSceneManager Object Test Results\n")
        f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for test in all_results.tests:
            status = "PASS" if test["passed"] else "FAIL"
            f.write(f"[{status}] {test['name']}: {test['message']}\n")
        
        f.write(f"\nSummary: {all_results.passed}/{all_results.passed + all_results.failed} passed\n")
    
    print(f"\nResults saved to: {log_file}")
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())