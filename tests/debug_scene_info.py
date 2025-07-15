"""
Debug script to check scene info structure.
"""
import sys
import os
import json
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from blender_remote.client import BlenderMCPClient

def debug_scene_info():
    """Debug the scene info structure."""
    client = BlenderMCPClient(host='localhost', port=6688)
    
    print("[SEARCH] Debugging scene info structure...")
    
    # Test connection first
    try:
        if not client.test_connection():
            print("[FAIL] Connection failed")
            return
        print("[PASS] Connection successful")
    except Exception as e:
        print(f"[FAIL] Connection failed: {e}")
        return
    
    # Get scene info
    try:
        print("\n[CONNECT] Getting scene info...")
        scene_info = client.get_scene_info()
        print(f"Scene info keys: {list(scene_info.keys())}")
        print(f"Scene info structure:\n{json.dumps(scene_info, indent=2)}")
        
    except Exception as e:
        print(f"[FAIL] get_scene_info failed: {e}")
        
    # Test setting a custom property
    try:
        print("\n[FIX] Setting custom property...")
        code = "import bpy; bpy.context.scene['test_pid'] = 12345"
        result = client.execute_python(code)
        print(f"Execute result: {result}")
        
        # Check scene info again
        scene_info = client.get_scene_info()
        print(f"Scene info after setting property:\n{json.dumps(scene_info, indent=2)}")
        
    except Exception as e:
        print(f"[FAIL] Setting custom property failed: {e}")

if __name__ == "__main__":
    debug_scene_info()