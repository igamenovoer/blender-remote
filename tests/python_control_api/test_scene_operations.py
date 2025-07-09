#!/usr/bin/env python3
"""
Test scene operations with BLD Remote MCP service.
"""

import sys
import os
import traceback
import numpy as np

# Add src to path to import blender_remote
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

try:
    import blender_remote
    
    def test_scene_manager_creation():
        """Test creating scene manager."""
        print("Testing scene manager creation...")
        
        # Method 1: Create with existing client
        client = blender_remote.connect_to_blender(port=6688)
        scene_manager = blender_remote.create_scene_manager(client)
        print(f"Created scene manager with client: {scene_manager.client.host}:{scene_manager.client.port}")
        
        # Method 2: Create with auto-client
        scene_manager2 = blender_remote.create_scene_manager(port=6688)
        print(f"Created scene manager with auto-client: {scene_manager2.client.host}:{scene_manager2.client.port}")
        
        return True
    
    def test_object_listing():
        """Test listing objects in scene."""
        print("\nTesting object listing...")
        
        scene_manager = blender_remote.create_scene_manager(port=6688)
        
        # List all objects
        print("Listing all objects...")
        all_objects = scene_manager.list_objects()
        print(f"Found {len(all_objects)} objects:")
        for obj in all_objects:
            print(f"  - {obj.name} ({obj.type}) at {obj.location}")
        
        # List only mesh objects
        print("\nListing mesh objects...")
        mesh_objects = scene_manager.list_objects(object_type="MESH")
        print(f"Found {len(mesh_objects)} mesh objects:")
        for obj in mesh_objects:
            print(f"  - {obj.name} at {obj.location}")
        
        # List top-level objects
        print("\nListing top-level objects...")
        top_level_objects = scene_manager.get_objects_top_level()
        print(f"Found {len(top_level_objects)} top-level objects:")
        for obj in top_level_objects:
            print(f"  - {obj.name} ({obj.type})")
        
        return True
    
    def test_primitive_creation():
        """Test creating primitive objects."""
        print("\nTesting primitive creation...")
        
        scene_manager = blender_remote.create_scene_manager(port=6688)
        
        # Create a cube
        print("Creating cube...")
        cube_name = scene_manager.add_cube(location=(2, 0, 0), size=1.0, name="TestCube")
        print(f"Created cube: {cube_name}")
        
        # Create a sphere
        print("Creating sphere...")
        sphere_name = scene_manager.add_sphere(location=(-2, 0, 0), radius=0.8, name="TestSphere")
        print(f"Created sphere: {sphere_name}")
        
        # Create a cylinder
        print("Creating cylinder...")
        cylinder_name = scene_manager.add_cylinder(location=(0, 2, 0), radius=0.5, depth=2.0, name="TestCylinder")
        print(f"Created cylinder: {cylinder_name}")
        
        # Verify objects were created
        print("Verifying created objects...")
        all_objects = scene_manager.list_objects()
        created_objects = [obj for obj in all_objects if obj.name.startswith("Test")]
        print(f"Found {len(created_objects)} test objects")
        
        return len(created_objects) == 3
    
    def test_object_manipulation():
        """Test manipulating objects."""
        print("\nTesting object manipulation...")
        
        scene_manager = blender_remote.create_scene_manager(port=6688)
        
        # Create a test object
        test_obj_name = scene_manager.add_cube(location=(0, 0, 0), name="ManipulationTest")
        print(f"Created test object: {test_obj_name}")
        
        # Move the object
        print("Moving object...")
        success = scene_manager.move_object(test_obj_name, location=(3, 3, 1))
        print(f"Move operation: {'SUCCESS' if success else 'FAILED'}")
        
        # Verify the move
        objects = scene_manager.list_objects()
        test_obj = next((obj for obj in objects if obj.name == test_obj_name), None)
        if test_obj:
            print(f"Object location after move: {test_obj.location}")
        
        # Clean up - delete the test object
        print("Cleaning up test object...")
        delete_success = scene_manager.delete_object(test_obj_name)
        print(f"Delete operation: {'SUCCESS' if delete_success else 'FAILED'}")
        
        return success and delete_success
    
    def test_scene_data_types():
        """Test scene data types and attrs functionality."""
        print("\nTesting scene data types...")
        
        scene_manager = blender_remote.create_scene_manager(port=6688)
        
        # Get structured scene info
        scene_info = scene_manager.get_scene_info()
        print(f"Scene info type: {type(scene_info)}")
        print(f"Object count: {scene_info.object_count}")
        print(f"Mesh objects: {len(scene_info.mesh_objects)}")
        
        # Test SceneObject attrs functionality
        if scene_info.objects:
            obj = scene_info.objects[0]
            print(f"First object: {obj.name}")
            print(f"  Type: {obj.type}")
            print(f"  Location: {obj.location}")
            print(f"  Rotation: {obj.rotation}")
            print(f"  Scale: {obj.scale}")
            print(f"  Visible: {obj.visible}")
            
            # Test world transform property
            transform = obj.world_transform
            print(f"  World transform shape: {transform.shape}")
            
            # Test copy functionality
            obj_copy = obj.copy()
            print(f"  Copy created: {obj_copy.name}")
        
        return True
    
    def test_batch_object_updates():
        """Test batch updating multiple objects."""
        print("\nTesting batch object updates...")
        
        scene_manager = blender_remote.create_scene_manager(port=6688)
        
        # Create multiple test objects
        test_objects = []
        for i in range(3):
            obj_name = scene_manager.add_cube(location=(i*2, 0, 0), name=f"BatchTest{i}")
            test_objects.append(obj_name)
        
        print(f"Created {len(test_objects)} test objects")
        
        # Get the objects and modify them
        objects = scene_manager.list_objects()
        batch_objects = [obj for obj in objects if obj.name.startswith("BatchTest")]
        
        # Modify their properties
        for i, obj in enumerate(batch_objects):
            obj.location = np.array([i*2, 2, 1])  # Move them
            obj.scale = np.array([0.5, 0.5, 0.5])  # Scale them down
        
        # Batch update
        print("Performing batch update...")
        update_results = scene_manager.update_scene_objects(batch_objects)
        print(f"Update results: {update_results}")
        
        # Verify updates
        print("Verifying updates...")
        updated_objects = scene_manager.list_objects()
        batch_updated = [obj for obj in updated_objects if obj.name.startswith("BatchTest")]
        
        for obj in batch_updated:
            print(f"  {obj.name}: location={obj.location}, scale={obj.scale}")
        
        # Clean up
        print("Cleaning up batch test objects...")
        for obj_name in test_objects:
            scene_manager.delete_object(obj_name)
        
        return all(update_results.values())
    
    def run_all_tests():
        """Run all scene operation tests."""
        print("=" * 60)
        print("BLD Remote MCP Scene Operations Tests")
        print("=" * 60)
        
        tests = [
            test_scene_manager_creation,
            test_object_listing,
            test_primitive_creation,
            test_object_manipulation,
            test_scene_data_types,
            test_batch_object_updates
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
        print(f"Test Results: {passed}/{total} tests passed")
        print("=" * 60)
        
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