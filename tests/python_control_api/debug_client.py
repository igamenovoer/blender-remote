#!/usr/bin/env python3
"""
Debug BlenderMCPClient implementation.
"""

import sys
import os

# Add src to path to import blender_remote
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import blender_remote

def test_client_get_scene_info():
    """Test client get_scene_info method with debug."""
    print("Testing BlenderMCPClient.get_scene_info()...")
    
    try:
        client = blender_remote.BlenderMCPClient(port=6688)
        print(f"Created client: {client.host}:{client.port}")
        
        # Test the raw execute_command method first
        print("\nTesting execute_command('get_scene_info')...")
        response = client.execute_command("get_scene_info")
        print(f"Raw response: {response}")
        
        # Test the get_scene_info method
        print("\nTesting get_scene_info()...")
        scene_info = client.get_scene_info()
        print(f"Scene info: {scene_info}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_client_execute_python():
    """Test client execute_python method."""
    print("\nTesting BlenderMCPClient.execute_python()...")
    
    try:
        client = blender_remote.BlenderMCPClient(port=6688)
        
        code = '''
import bpy
print("Testing from client!")
objects = [obj.name for obj in bpy.context.scene.objects]
print(f"Objects: {objects}")
result = f"Found {len(objects)} objects"
'''
        
        result = client.execute_python(code)
        print(f"Execute result: {result}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("BlenderMCPClient Debug")
    print("=" * 60)
    
    result1 = test_client_get_scene_info()
    result2 = test_client_execute_python()
    
    print("\n" + "=" * 60)
    print(f"Results: get_scene_info={'PASS' if result1 else 'FAIL'}, execute_python={'PASS' if result2 else 'FAIL'}")
    print("=" * 60)