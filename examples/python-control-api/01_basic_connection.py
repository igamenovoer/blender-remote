#!/usr/bin/env python3
"""
Basic Connection Example - Python Control API

This example demonstrates how to connect to Blender using the Python Control API
and perform basic operations.

Prerequisites:
- Blender running with BLD Remote MCP service on port 6688
- blender-remote package installed
"""

import blender_remote
import time


def main():
    """Demonstrate basic connection and operations."""
    print("=== Basic Connection Example ===")
    
    # Step 1: Connect to Blender
    print("\n1. Connecting to Blender...")
    try:
        client = blender_remote.connect_to_blender(port=6688)
        print(f"✓ Connected to Blender at {client.host}:{client.port}")
    except blender_remote.BlenderConnectionError as e:
        print(f"✗ Connection failed: {e}")
        print("Make sure Blender is running with BLD Remote MCP service")
        return
    
    # Step 2: Test connection
    print("\n2. Testing connection...")
    if client.test_connection():
        print("✓ Connection test passed")
    else:
        print("✗ Connection test failed")
        return
    
    # Step 3: Get service status
    print("\n3. Getting service status...")
    status = client.get_status()
    print(f"Service: {status['service']}")
    print(f"Host: {status['host']}")
    print(f"Port: {status['port']}")
    print(f"Scene objects: {status.get('scene_objects', 'N/A')}")
    
    # Step 4: Get scene information
    print("\n4. Getting scene information...")
    scene_info = client.get_scene_info()
    print(f"Scene name: {scene_info.get('name', 'N/A')}")
    print(f"Object count: {scene_info.get('object_count', 0)}")
    
    # List objects
    objects = scene_info.get('objects', [])
    if objects:
        print("Objects in scene:")
        for obj in objects:
            print(f"  - {obj['name']} ({obj['type']}) at {obj['location']}")
    
    # Step 5: Execute simple Python code
    print("\n5. Executing Python code...")
    code = """
import bpy
print("Hello from Blender!")
print(f"Blender version: {bpy.app.version}")
scene_name = bpy.context.scene.name
print(f"Current scene: {scene_name}")
"""
    
    try:
        result = client.execute_python(code)
        print(f"Execution result: {result}")
    except blender_remote.BlenderCommandError as e:
        print(f"Code execution failed: {e}")
    
    # Step 6: Get object details
    print("\n6. Getting object details...")
    objects = scene_info.get('objects', [])
    if objects:
        first_obj = objects[0]
        obj_name = first_obj['name']
        
        try:
            obj_details = client.get_object_info(obj_name)
            print(f"Details for '{obj_name}':")
            print(f"  Type: {obj_details.get('type', 'N/A')}")
            print(f"  Location: {obj_details.get('location', 'N/A')}")
            print(f"  Visible: {obj_details.get('visible', 'N/A')}")
        except blender_remote.BlenderCommandError as e:
            print(f"Failed to get object details: {e}")
    
    print("\n=== Basic Connection Example Complete ===")


if __name__ == "__main__":
    main()