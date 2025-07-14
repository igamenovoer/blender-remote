#!/usr/bin/env python3
"""
Focused test for get_object_as_glb() method in BlenderSceneManager.

This test specifically focuses on the GLB export functionality with 
detailed debugging to identify and fix any issues.
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


def setup_test_environment():
    """Set up a clean test environment with a simple object."""
    try:
        client = BlenderMCPClient(timeout=30.0)
        if not client.test_connection():
            return None, None, "Could not connect to BLD_Remote_MCP service"
        
        scene_manager = BlenderSceneManager(client)
        
        # Clear scene and create a simple test object
        print("Setting up test environment...")
        scene_manager.clear_scene(keep_camera=True, keep_light=True)
        
        # Create a simple cube using direct Blender Python code
        create_cube_code = """
import bpy

# Create a simple cube
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0), size=2.0)
cube_obj = bpy.context.active_object
cube_obj.name = "GLBTestCube"

# Ensure it's selected and active
bpy.context.view_layer.objects.active = cube_obj
cube_obj.select_set(True)

print("TEST_OBJECT_CREATED:" + cube_obj.name)
"""
        result = scene_manager.client.execute_python(create_cube_code)
        
        # Extract object name
        test_object_name = None
        for line in result.split('\n'):
            if line.startswith("TEST_OBJECT_CREATED:"):
                test_object_name = line[20:]
                break
        
        if not test_object_name:
            return None, None, "Failed to create test object"
        
        print(f"✓ Test object created: {test_object_name}")
        return scene_manager, test_object_name, None
        
    except Exception as e:
        return None, None, f"Setup failed: {str(e)}"


def test_glb_raw_export_basic():
    """Test basic GLB raw export functionality."""
    print("\n=== Testing Basic GLB Raw Export ===")
    
    scene_manager, test_object, error = setup_test_environment()
    if scene_manager is None:
        print(f"✗ Setup failed: {error}")
        return False
    
    try:
        print(f"Exporting object '{test_object}' as raw GLB...")
        glb_data = scene_manager.get_object_as_glb_raw(test_object, with_material=True)
        
        # Validate GLB data
        if not isinstance(glb_data, bytes):
            print(f"✗ Expected bytes, got {type(glb_data)}")
            return False
        
        if len(glb_data) == 0:
            print("✗ GLB data is empty")
            return False
        
        if glb_data[:4] != b'glTF':
            print(f"✗ Invalid GLB magic number: {glb_data[:4]}")
            return False
        
        print(f"✓ GLB export successful: {len(glb_data)} bytes")
        print(f"  Magic number: {glb_data[:4]}")
        print(f"  Version: {int.from_bytes(glb_data[4:8], 'little')}")
        print(f"  Length: {int.from_bytes(glb_data[8:12], 'little')}")
        
        return True
        
    except Exception as e:
        print(f"✗ GLB export failed: {str(e)}")
        return False
    finally:
        # Cleanup
        try:
            scene_manager.delete_object(test_object)
        except:
            pass


def test_glb_trimesh_export_basic():
    """Test basic GLB trimesh export functionality."""
    print("\n=== Testing Basic GLB Trimesh Export ===")
    
    if not TRIMESH_AVAILABLE:
        print("✗ Trimesh not available, skipping test")
        return False
    
    scene_manager, test_object, error = setup_test_environment()
    if scene_manager is None:
        print(f"✗ Setup failed: {error}")
        return False
    
    try:
        print(f"Exporting object '{test_object}' as trimesh Scene...")
        trimesh_scene = scene_manager.get_object_as_glb(test_object, with_material=True)
        
        # Validate trimesh Scene
        if not isinstance(trimesh_scene, trimesh.Scene):
            print(f"✗ Expected trimesh.Scene, got {type(trimesh_scene)}")
            return False
        
        if len(trimesh_scene.geometry) == 0:
            print("✗ Trimesh scene has no geometry")
            return False
        
        # Get first geometry
        first_geom = next(iter(trimesh_scene.geometry.values()))
        
        print(f"✓ Trimesh export successful")
        print(f"  Scene type: {type(trimesh_scene)}")
        print(f"  Geometries: {len(trimesh_scene.geometry)}")
        print(f"  Geometry names: {list(trimesh_scene.geometry.keys())}")
        print(f"  First geometry type: {type(first_geom)}")
        
        if hasattr(first_geom, 'vertices'):
            print(f"  Vertices: {len(first_geom.vertices)}")
        if hasattr(first_geom, 'faces'):
            print(f"  Faces: {len(first_geom.faces)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Trimesh export failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        try:
            scene_manager.delete_object(test_object)
        except:
            pass


def test_glb_export_options():
    """Test GLB export with different options."""
    print("\n=== Testing GLB Export Options ===")
    
    scene_manager, test_object, error = setup_test_environment()
    if scene_manager is None:
        print(f"✗ Setup failed: {error}")
        return False
    
    success_count = 0
    total_tests = 0
    
    try:
        # Test with materials
        total_tests += 1
        try:
            glb_with_mat = scene_manager.get_object_as_glb_raw(test_object, with_material=True)
            print(f"✓ Export with materials: {len(glb_with_mat)} bytes")
            success_count += 1
        except Exception as e:
            print(f"✗ Export with materials failed: {str(e)}")
        
        # Test without materials
        total_tests += 1
        try:
            glb_no_mat = scene_manager.get_object_as_glb_raw(test_object, with_material=False)
            print(f"✓ Export without materials: {len(glb_no_mat)} bytes")
            success_count += 1
        except Exception as e:
            print(f"✗ Export without materials failed: {str(e)}")
        
        # Test with custom temp directory
        total_tests += 1
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                glb_custom_temp = scene_manager.get_object_as_glb_raw(
                    test_object, 
                    with_material=True,
                    blender_temp_dir=temp_dir,
                    keep_temp_file=False
                )
                print(f"✓ Export with custom temp dir: {len(glb_custom_temp)} bytes")
                success_count += 1
        except Exception as e:
            print(f"✗ Export with custom temp dir failed: {str(e)}")
        
        # Test keeping temp file
        total_tests += 1
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                glb_keep_temp = scene_manager.get_object_as_glb_raw(
                    test_object,
                    with_material=True,
                    blender_temp_dir=temp_dir,
                    keep_temp_file=True
                )
                print(f"✓ Export keeping temp file: {len(glb_keep_temp)} bytes")
                success_count += 1
        except Exception as e:
            print(f"✗ Export keeping temp file failed: {str(e)}")
        
        print(f"\nOptions test summary: {success_count}/{total_tests} passed")
        return success_count == total_tests
        
    finally:
        # Cleanup
        try:
            scene_manager.delete_object(test_object)
        except:
            pass


def test_glb_export_debug_output():
    """Test GLB export with debug output to see what's happening."""
    print("\n=== Testing GLB Export with Debug Output ===")
    
    scene_manager, test_object, error = setup_test_environment()
    if scene_manager is None:
        print(f"✗ Setup failed: {error}")
        return False
    
    try:
        # Get the GLB export code and run it step by step for debugging
        debug_code = f'''
import bpy
import os
import tempfile
import base64
import time

print("=== GLB Export Debug ===")
print(f"Looking for object: '{test_object}'")

# Check if object exists
is_object = "{test_object}" in bpy.data.objects
is_collection = "{test_object}" in bpy.data.collections

print(f"Is object: {{is_object}}")
print(f"Is collection: {{is_collection}}")

if is_object:
    obj = bpy.data.objects["{test_object}"]
    print(f"Object found: {{obj.name}}")
    print(f"Object type: {{obj.type}}")
    print(f"Object location: {{obj.location}}")
    
    # Clear selection and select our object
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    
    print(f"Object selected: {{obj.select_get()}}")
    print(f"Object is active: {{bpy.context.view_layer.objects.active == obj}}")
    
    # Try to export
    temp_dir = tempfile.gettempdir()
    temp_filepath = os.path.join(temp_dir, f"debug_export_{{int(time.time())}}.glb")
    
    print(f"Temp file path: {{temp_filepath}}")
    
    try:
        bpy.ops.export_scene.gltf(
            filepath=temp_filepath,
            use_selection=True,
            export_format='GLB',
            export_materials='EXPORT',
            export_apply=True,
            export_yup=False,
            export_texcoords=True,
            export_normals=True
        )
        
        print("GLB export operation completed")
        
        if os.path.exists(temp_filepath):
            file_size = os.path.getsize(temp_filepath)
            print(f"GLB file created successfully: {{file_size}} bytes")
            
            # Read and encode
            with open(temp_filepath, 'rb') as f:
                glb_bytes = f.read()
            
            glb_base64 = base64.b64encode(glb_bytes).decode('utf-8')
            print(f"GLB base64 length: {{len(glb_base64)}}")
            print("GLB_BASE64_START")
            print(glb_base64)
            print("GLB_BASE64_END")
            
            # Cleanup
            os.remove(temp_filepath)
            
        else:
            print("ERROR: GLB file was not created")
            
    except Exception as e:
        print(f"Export operation failed: {{str(e)}}")
        import traceback
        traceback.print_exc()
        
else:
    print(f"ERROR: Object '{test_object}' not found")

print("=== Debug Complete ===")
'''
        
        print("Running debug export...")
        result = scene_manager.client.execute_python(debug_code)
        
        print("Debug output:")
        print(result)
        
        # Try to extract GLB data from debug output
        lines = result.split('\n')
        in_base64_section = False
        glb_base64 = ""
        
        for line in lines:
            if line == "GLB_BASE64_START":
                in_base64_section = True
            elif line == "GLB_BASE64_END":
                in_base64_section = False
                break
            elif in_base64_section:
                glb_base64 += line
        
        if glb_base64:
            try:
                import base64
                glb_bytes = base64.b64decode(glb_base64)
                print(f"✓ Successfully decoded GLB data: {len(glb_bytes)} bytes")
                print(f"  Magic number: {glb_bytes[:4]}")
                return True
            except Exception as e:
                print(f"✗ Failed to decode GLB data: {str(e)}")
                return False
        else:
            print("✗ No GLB data found in debug output")
            return False
        
    finally:
        # Cleanup
        try:
            scene_manager.delete_object(test_object)
        except:
            pass


def main():
    """Run focused GLB export tests."""
    print("🔍 Focused GLB Export Testing for get_object_as_glb()")
    print("=" * 60)
    print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Trimesh available: {TRIMESH_AVAILABLE}")
    
    tests = [
        ("Basic GLB Raw Export", test_glb_raw_export_basic),
        ("Basic GLB Trimesh Export", test_glb_trimesh_export_basic),
        ("GLB Export Options", test_glb_export_options),
        ("GLB Export Debug", test_glb_export_debug_output),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"💥 {test_name} ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print(f"🎯 GLB Export Test Results: {passed}/{total} tests passed")
    print(f"📊 Success Rate: {(passed/total*100):.1f}%")
    
    # Save results
    log_dir = Path(__file__).parent.parent / "logs" / "tests"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"test_glb_export_focused_{int(time.time())}.log"
    with open(log_file, "w") as f:
        f.write(f"Focused GLB Export Test Results\n")
        f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Success Rate: {(passed/total*100):.1f}% ({passed}/{total})\n\n")
        f.write("Test Results:\n")
        for i, (test_name, _) in enumerate(tests):
            status = "PASS" if i < passed else "FAIL" 
            f.write(f"[{status}] {test_name}\n")
    
    print(f"📝 Results saved to: {log_file}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())