#!/usr/bin/env python3
"""
Debug BlenderMCPClient sequence of calls.
"""

import sys
import os

# Add src to path to import blender_remote
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import blender_remote

def test_single_calls():
    """Test individual client calls."""
    print("Testing individual client calls...")
    
    try:
        # Test 1: get_scene_info only
        print("\n1. Testing get_scene_info only...")
        client1 = blender_remote.BlenderMCPClient(port=6688)
        scene_info = client1.get_scene_info()
        print(f"Scene info success: {len(scene_info.get('objects', []))} objects")
        
        # Test 2: execute_python only
        print("\n2. Testing execute_python only...")
        client2 = blender_remote.BlenderMCPClient(port=6688)
        result = client2.execute_python('print("Hello"); result = "test"')
        print(f"Execute python success: {result}")
        
        return True
        
    except Exception as e:
        print(f"Error in single calls: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sequence_calls():
    """Test sequence of calls on same client."""
    print("\nTesting sequence of calls on same client...")
    
    try:
        client = blender_remote.BlenderMCPClient(port=6688)
        
        # First call
        print("First call: get_scene_info...")
        scene_info = client.get_scene_info()
        print(f"First call success: {len(scene_info.get('objects', []))} objects")
        
        # Second call
        print("Second call: execute_python...")
        result = client.execute_python('print("Hello2"); result = "test2"')
        print(f"Second call success: {result}")
        
        return True
        
    except Exception as e:
        print(f"Error in sequence calls: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_execute_python():
    """Test multiple execute_python calls."""
    print("\nTesting multiple execute_python calls...")
    
    try:
        for i in range(3):
            print(f"Execute python call {i+1}...")
            client = blender_remote.BlenderMCPClient(port=6688)
            result = client.execute_python(f'print("Test {i+1}"); result = "test_{i+1}"')
            print(f"Call {i+1} success: {result}")
        
        return True
        
    except Exception as e:
        print(f"Error in multiple execute_python: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("BlenderMCPClient Sequence Debug")
    print("=" * 60)
    
    result1 = test_single_calls()
    result2 = test_sequence_calls()
    result3 = test_multiple_execute_python()
    
    print("\n" + "=" * 60)
    print(f"Results:")
    print(f"  Single calls: {'PASS' if result1 else 'FAIL'}")
    print(f"  Sequence calls: {'PASS' if result2 else 'FAIL'}")
    print(f"  Multiple execute_python: {'PASS' if result3 else 'FAIL'}")
    print("=" * 60)