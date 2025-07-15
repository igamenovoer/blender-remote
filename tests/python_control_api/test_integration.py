#!/usr/bin/env python3
"""
Integration test for the complete Python Control API.
"""

import sys
import os
import traceback
import tempfile
import numpy as np

# Add src to path to import blender_remote
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

try:
    import blender_remote

    def test_full_workflow():
        """Test a complete workflow using the Python Control API."""
        print("Testing complete workflow...")

        # Connect to Blender
        client = blender_remote.connect_to_blender(port=6688)
        print(f"Connected to Blender: {client.host}:{client.port}")

        # Test connection
        if not client.test_connection():
            print("ERROR: Cannot connect to Blender")
            return False

        # Create managers
        scene_manager = blender_remote.create_scene_manager(client)
        asset_manager = blender_remote.create_asset_manager(client)

        # Step 1: Clear scene (keep camera and lights)
        print("\n1. Clearing scene...")
        scene_manager.clear_scene(keep_camera=True, keep_light=True)

        # Step 2: Create some objects using direct Blender Python
        print("\n2. Creating objects...")
        create_objects_code = """
import bpy

# Create a cube
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0), size=2.0)
cube_obj = bpy.context.active_object
cube_obj.name = "WorkflowCube"
print("OBJECT_CREATED:" + cube_obj.name)

# Create a sphere
bpy.ops.mesh.primitive_uv_sphere_add(location=(3, 0, 0), radius=1.0)
sphere_obj = bpy.context.active_object
sphere_obj.name = "WorkflowSphere"
print("OBJECT_CREATED:" + sphere_obj.name)

# Create a cylinder
bpy.ops.mesh.primitive_cylinder_add(location=(-3, 0, 0), radius=0.8, depth=2.0)
cylinder_obj = bpy.context.active_object
cylinder_obj.name = "WorkflowCylinder"
print("OBJECT_CREATED:" + cylinder_obj.name)
"""
        result = scene_manager.client.execute_python(create_objects_code)
        
        # Extract object names
        cube_name = sphere_name = cylinder_name = None
        for line in result.split('\n'):
            if line.startswith("OBJECT_CREATED:"):
                obj_name = line[15:]
                if "Cube" in obj_name:
                    cube_name = obj_name
                elif "Sphere" in obj_name:
                    sphere_name = obj_name
                elif "Cylinder" in obj_name:
                    cylinder_name = obj_name

        print(f"Created objects: {cube_name}, {sphere_name}, {cylinder_name}")

        # Step 3: List and verify objects
        print("\n3. Verifying objects...")
        objects = scene_manager.list_objects(object_type="MESH")
        workflow_objects = [obj for obj in objects if obj.name.startswith("Workflow")]
        print(f"Found {len(workflow_objects)} workflow objects")

        # Step 4: Manipulate objects
        print("\n4. Manipulating objects...")
        for i, obj in enumerate(workflow_objects):
            # Move objects up
            obj.location = np.array([obj.location[0], obj.location[1], 1.0])
            # Scale objects
            obj.scale = np.array([0.8, 0.8, 0.8])

        # Apply batch update
        update_results = scene_manager.update_scene_objects(workflow_objects)
        print(f"Update results: {update_results}")

        # Step 5: Position camera
        print("\n5. Positioning camera...")
        scene_manager.set_camera_location(location=(10, -10, 5), target=(0, 0, 1))

        # Step 6: Take screenshot
        print("\n6. Taking screenshot...")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            screenshot_path = tmp_file.name

        screenshot_result = scene_manager.take_screenshot(screenshot_path)
        print(f"Screenshot result: {screenshot_result}")

        # Step 7: Export object as GLB
        print("\n7. Exporting object as GLB...")
        try:
            glb_scene = scene_manager.get_object_as_glb(cube_name)
            print(f"GLB export successful: {type(glb_scene)}")
        except Exception as e:
            print(f"GLB export failed: {e}")

        # Step 8: Test asset manager
        print("\n8. Testing asset manager...")
        libraries = asset_manager.list_asset_libraries()
        print(f"Found {len(libraries)} asset libraries")

        # Step 9: Clean up
        print("\n9. Cleaning up...")
        for obj_name in [cube_name, sphere_name, cylinder_name]:
            if obj_name:  # Only delete if object was created successfully
                scene_manager.delete_object(obj_name)

        # Clean up temporary file
        try:
            os.unlink(screenshot_path)
        except:
            pass

        print("Workflow completed successfully!")
        return True

    def test_error_handling():
        """Test error handling in the API."""
        print("\nTesting error handling...")

        client = blender_remote.connect_to_blender(port=6688)
        scene_manager = blender_remote.create_scene_manager(client)

        # Test deleting non-existent object
        print("Testing deletion of non-existent object...")
        result = scene_manager.delete_object("NonExistentObject")
        print(f"Delete non-existent object result: {result}")

        # Test moving non-existent object
        print("Testing move of non-existent object...")
        result = scene_manager.move_object("NonExistentObject", (0, 0, 0))
        print(f"Move non-existent object result: {result}")

        # Test invalid Blender operation
        print("Testing invalid Blender operation...")
        try:
            # Test with invalid Blender Python code
            invalid_code = """
import bpy
bpy.ops.mesh.primitive_nonexistent_add()  # This should fail
"""
            scene_manager.client.execute_python(invalid_code)
            print("ERROR: Should have raised exception")
            return False
        except Exception as e:
            print(f"Correctly caught exception: {type(e).__name__}: {e}")

        return True

    def test_data_type_functionality():
        """Test data type functionality and attrs features."""
        print("\nTesting data type functionality...")

        # Test SceneObject creation and manipulation
        print("Testing SceneObject...")
        obj = blender_remote.SceneObject(
            name="TestObject",
            type="MESH",
            location=[1, 2, 3],
            rotation=[1, 0, 0, 0],
            scale=[1, 1, 1],
        )

        print(f"Created SceneObject: {obj.name}")
        print(f"Location: {obj.location}")
        print(f"World transform shape: {obj.world_transform.shape}")

        # Test copy functionality
        obj_copy = obj.copy()
        print(f"Copied object: {obj_copy.name}")

        # Test CameraSettings
        print("Testing CameraSettings...")
        camera = blender_remote.CameraSettings(location=[5, -5, 3], target=[0, 0, 0])

        print(f"Camera direction: {camera.direction}")
        print(f"Camera distance: {camera.distance}")

        # Test RenderSettings
        print("Testing RenderSettings...")
        render = blender_remote.RenderSettings(resolution=[1920, 1080], samples=64)

        print(f"Render resolution: {render.width}x{render.height}")
        print(f"Aspect ratio: {render.aspect_ratio}")

        return True

    def test_convenience_functions():
        """Test convenience functions in the API."""
        print("\nTesting convenience functions...")

        # Test connect_to_blender
        client = blender_remote.connect_to_blender(port=6688)
        print(f"Connected via convenience function: {client.host}:{client.port}")

        # Test create_scene_manager with auto-client
        scene_manager = blender_remote.create_scene_manager(port=6688)
        print(
            f"Created scene manager: {scene_manager.client.host}:{scene_manager.client.port}"
        )

        # Test create_asset_manager with auto-client
        asset_manager = blender_remote.create_asset_manager(port=6688)
        print(
            f"Created asset manager: {asset_manager.client.host}:{asset_manager.client.port}"
        )

        # Test with existing client
        scene_manager2 = blender_remote.create_scene_manager(client)
        print(
            f"Created scene manager with existing client: {scene_manager2.client.host}:{scene_manager2.client.port}"
        )

        return True

    def test_api_imports():
        """Test that all API components can be imported."""
        print("\nTesting API imports...")

        # Test main classes
        assert hasattr(blender_remote, "BlenderMCPClient")
        assert hasattr(blender_remote, "BlenderSceneManager")
        assert hasattr(blender_remote, "BlenderAssetManager")
        print("✓ Main classes imported")

        # Test data types
        assert hasattr(blender_remote, "SceneObject")
        assert hasattr(blender_remote, "AssetLibrary")
        assert hasattr(blender_remote, "AssetCollection")
        assert hasattr(blender_remote, "RenderSettings")
        assert hasattr(blender_remote, "CameraSettings")
        assert hasattr(blender_remote, "MaterialSettings")
        assert hasattr(blender_remote, "SceneInfo")
        assert hasattr(blender_remote, "ExportSettings")
        print("✓ Data types imported")

        # Test exceptions
        assert hasattr(blender_remote, "BlenderRemoteError")
        assert hasattr(blender_remote, "BlenderMCPError")
        assert hasattr(blender_remote, "BlenderConnectionError")
        assert hasattr(blender_remote, "BlenderCommandError")
        assert hasattr(blender_remote, "BlenderTimeoutError")
        print("✓ Exceptions imported")

        # Test convenience functions
        assert hasattr(blender_remote, "connect_to_blender")
        assert hasattr(blender_remote, "create_scene_manager")
        assert hasattr(blender_remote, "create_asset_manager")
        print("✓ Convenience functions imported")

        return True

    def run_all_tests():
        """Run all integration tests."""
        print("=" * 60)
        print("BLD Remote MCP Python Control API Integration Tests")
        print("=" * 60)

        tests = [
            test_api_imports,
            test_convenience_functions,
            test_data_type_functionality,
            test_error_handling,
            test_full_workflow,
        ]

        passed = 0
        total = len(tests)

        for test in tests:
            try:
                if test():
                    passed += 1
                    print(f"✓ {test.__name__} PASSED")
                else:
                    print(f"✗ {test.__name__} FAILED")
            except Exception as e:
                print(f"✗ {test.__name__} ERROR: {str(e)}")
                traceback.print_exc()

        print("\n" + "=" * 60)
        print(f"Integration Test Results: {passed}/{total} tests passed")
        print("=" * 60)

        if passed == total:
            print(
                "[SUCCESS] All integration tests passed! Python Control API is working correctly."
            )
        else:
            print("[FAIL] Some integration tests failed. Please check the results above.")

        return passed == total

    if __name__ == "__main__":
        success = run_all_tests()
        sys.exit(0 if success else 1)

except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure to run this script from the project root directory")
    sys.exit(1)
except Exception as e:
    print(f"Unexpected error: {e}")
    traceback.print_exc()
    sys.exit(1)
