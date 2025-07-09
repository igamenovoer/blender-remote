#!/usr/bin/env python3
"""
Scene Management Example - Python Control API

This example demonstrates how to use BlenderSceneManager for high-level scene
operations including object creation, manipulation, and rendering.

Prerequisites:
- Blender running with BLD Remote MCP service on port 6688
- blender-remote package installed
"""

import blender_remote
import tempfile
import os


def main():
    """Demonstrate scene management operations."""
    print("=== Scene Management Example ===")
    
    # Step 1: Create scene manager
    print("\n1. Creating scene manager...")
    try:
        scene_manager = blender_remote.create_scene_manager(port=6688)
        print("✓ Scene manager created")
    except blender_remote.BlenderConnectionError as e:
        print(f"✗ Failed to create scene manager: {e}")
        return
    
    # Step 2: Get initial scene info
    print("\n2. Getting initial scene information...")
    scene_info = scene_manager.get_scene_info()
    print(f"Initial scene has {scene_info.object_count} objects")
    print(f"Mesh objects: {len(scene_info.mesh_objects)}")
    
    # Step 3: Clear scene (keep camera and lights)
    print("\n3. Clearing scene...")
    if scene_manager.clear_scene(keep_camera=True, keep_light=True):
        print("✓ Scene cleared successfully")
        
        # Check scene after clearing
        scene_info = scene_manager.get_scene_info()
        print(f"Scene now has {scene_info.object_count} objects")
    else:
        print("✗ Failed to clear scene")
    
    # Step 4: Create primitive objects
    print("\n4. Creating primitive objects...")
    
    # Create a cube
    cube_name = scene_manager.add_cube(location=(0, 0, 0), size=2.0, name="MainCube")
    print(f"Created cube: {cube_name}")
    
    # Create a sphere
    sphere_name = scene_manager.add_sphere(location=(3, 0, 0), radius=1.0, name="RedSphere")
    print(f"Created sphere: {sphere_name}")
    
    # Create a cylinder
    cylinder_name = scene_manager.add_cylinder(location=(-3, 0, 0), radius=0.8, depth=2.0, name="TallCylinder")
    print(f"Created cylinder: {cylinder_name}")
    
    # Verify objects were created
    scene_info = scene_manager.get_scene_info()
    print(f"Scene now has {scene_info.object_count} objects")
    
    # Step 5: List and examine objects
    print("\n5. Listing objects...")
    mesh_objects = scene_manager.list_objects("MESH")
    print(f"Found {len(mesh_objects)} mesh objects:")
    for obj in mesh_objects:
        print(f"  - {obj.name} ({obj.type}) at {obj.location}")
    
    # Step 6: Manipulate objects
    print("\n6. Manipulating objects...")
    
    # Move the cube
    if scene_manager.move_object(cube_name, location=(1, 1, 1)):
        print(f"✓ Moved {cube_name} to (1, 1, 1)")
    else:
        print(f"✗ Failed to move {cube_name}")
    
    # Batch update objects
    print("\n7. Batch updating objects...")
    objects = scene_manager.list_objects("MESH")
    for obj in objects:
        # Move all objects up by 1 unit
        obj.location = [obj.location[0], obj.location[1], obj.location[2] + 1]
        # Scale all objects down
        obj.scale = [0.8, 0.8, 0.8]
    
    update_results = scene_manager.update_scene_objects(objects)
    print(f"Update results: {update_results}")
    
    # Step 8: Set up camera
    print("\n8. Setting up camera...")
    if scene_manager.set_camera_location(location=(7, -7, 5), target=(0, 0, 1)):
        print("✓ Camera positioned successfully")
    else:
        print("✗ Failed to position camera")
    
    # Step 9: Take screenshot
    print("\n9. Taking screenshot...")
    try:
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            screenshot_path = tmp.name
        
        screenshot_result = scene_manager.take_screenshot(screenshot_path, max_size=800)
        
        if screenshot_result.get('success', False):
            print(f"✓ Screenshot saved to: {screenshot_path}")
            print(f"  Size: {screenshot_result.get('width', 0)}x{screenshot_result.get('height', 0)}")
        else:
            print("✗ Screenshot failed")
            
    except Exception as e:
        print(f"✗ Screenshot error: {e}")
    
    # Step 10: Render scene
    print("\n10. Rendering scene...")
    try:
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            render_path = tmp.name
        
        if scene_manager.render_image(render_path, resolution=(800, 600)):
            print(f"✓ Render saved to: {render_path}")
        else:
            print("✗ Render failed")
            
    except Exception as e:
        print(f"✗ Render error: {e}")
    
    # Step 11: Export objects
    print("\n11. Exporting objects...")
    try:
        # Export cube as GLB
        glb_scene = scene_manager.get_object_as_glb(cube_name, with_material=True)
        print(f"✓ Exported {cube_name} as GLB")
        print(f"  Scene type: {type(glb_scene)}")
        
        # Export raw GLB bytes
        glb_bytes = scene_manager.get_object_as_glb_raw(cube_name)
        print(f"✓ Exported {cube_name} as raw GLB ({len(glb_bytes)} bytes)")
        
    except Exception as e:
        print(f"✗ Export error: {e}")
    
    # Step 12: Final scene summary
    print("\n12. Final scene summary...")
    final_scene = scene_manager.get_scene_info()
    print(f"Final scene has {final_scene.object_count} objects")
    print(f"Mesh objects: {len(final_scene.mesh_objects)}")
    print(f"Light objects: {len(final_scene.light_objects)}")
    
    # List all objects with their properties
    print("\nFinal object list:")
    for obj in final_scene.objects:
        print(f"  - {obj.name} ({obj.type})")
        print(f"    Location: {obj.location}")
        print(f"    Scale: {obj.scale}")
        print(f"    Visible: {obj.visible}")
    
    print("\n=== Scene Management Example Complete ===")


if __name__ == "__main__":
    main()