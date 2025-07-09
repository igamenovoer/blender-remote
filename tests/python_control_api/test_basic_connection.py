#!/usr/bin/env python3
"""
Test basic connection to BLD Remote MCP service.
"""

import sys
import os
import traceback

# Add src to path to import blender_remote
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

try:
    import blender_remote
    
    def test_basic_connection():
        """Test basic connection to BLD Remote MCP service."""
        print("Testing basic connection to BLD Remote MCP service...")
        
        # Create client
        client = blender_remote.connect_to_blender(port=6688)
        print(f"Created client: {client.host}:{client.port}")
        
        # Test connection
        print("Testing connection...")
        is_connected = client.test_connection()
        print(f"Connection test: {'PASS' if is_connected else 'FAIL'}")
        
        if not is_connected:
            print("ERROR: Could not connect to BLD Remote MCP service")
            print("Make sure Blender is running with BLD Remote MCP service on port 6688")
            return False
        
        # Get service status
        print("Getting service status...")
        status = client.get_status()
        print(f"Service status: {status}")
        
        return True
    
    def test_scene_info():
        """Test getting scene information."""
        print("\nTesting scene information...")
        
        # Add a small delay to avoid overwhelming the service
        import time
        time.sleep(1)
        
        client = blender_remote.connect_to_blender(port=6688)
        
        # Test raw scene info
        print("Getting raw scene info...")
        scene_info = client.get_scene_info()
        print(f"Scene objects count: {len(scene_info.get('objects', []))}")
        
        # Test structured scene info
        print("Getting structured scene info...")
        scene_manager = blender_remote.create_scene_manager(client)
        structured_info = scene_manager.get_scene_info()
        print(f"Structured scene objects count: {structured_info.object_count}")
        
        return True
    
    def test_python_execution():
        """Test executing Python code in Blender."""
        print("\nTesting Python code execution...")
        
        # Add a small delay to avoid overwhelming the service
        import time
        time.sleep(1)
        
        client = blender_remote.connect_to_blender(port=6688)
        
        # Simple test
        code = '''
import bpy
print("Hello from Blender!")
print(f"Blender version: {bpy.app.version}")
result = "Python execution successful"
'''
        
        print("Executing Python code in Blender...")
        result = client.execute_python(code)
        print(f"Execution result: {result}")
        
        return True
    
    def run_all_tests():
        """Run all connection tests."""
        print("=" * 60)
        print("BLD Remote MCP Connection Tests")
        print("=" * 60)
        
        tests = [
            test_basic_connection,
            test_scene_info,
            test_python_execution
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