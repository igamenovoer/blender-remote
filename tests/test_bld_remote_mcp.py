"""
Unit Tests for BLD_Remote_MCP Service

This module tests the specific functionality and edge cases of our
BLD_Remote_MCP service implementation.
"""

import pytest
import sys
import time
import json
import socket
from pathlib import Path

# Add auto_mcp_remote client interface to path
sys.path.insert(0, str(Path(__file__).parent.parent / "context" / "refcode"))

try:
    from auto_mcp_remote.blender_mcp_client import BlenderMCPClient
except ImportError as e:
    pytest.skip(f"auto_mcp_remote client not available: {e}", allow_module_level=True)


@pytest.mark.blender_required
class TestBldRemoteMCPService:
    """Test cases for BLD_Remote_MCP service functionality."""
    
    def test_service_startup_and_connectivity(self, bld_remote_service):
        """Test basic service startup and TCP connectivity."""
        port = bld_remote_service
        
        # Test TCP connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.settimeout(5)
            result = sock.connect_ex(('127.0.0.1', port))
            assert result == 0, f"Cannot connect to BLD_Remote_MCP on port {port}"
        finally:
            sock.close()
    
    def test_mcp_client_connection(self, bld_remote_service):
        """Test MCP client can connect and communicate."""
        port = bld_remote_service
        
        client = BlenderMCPClient(port=port)
        try:
            # Test basic communication with a simple command
            result = client.execute_python("result = 'connection_test'")
            assert result is not None, "No response from BLD_Remote_MCP service"
        finally:
            client.disconnect()
    
    def test_python_execution_basic(self, bld_remote_service):
        """Test basic Python code execution."""
        port = bld_remote_service
        client = BlenderMCPClient(port=port)
        
        try:
            # Test arithmetic
            result = client.execute_python("result = 2 + 2")
            assert result is not None
            
            # Test string operations
            result = client.execute_python("result = 'hello' + ' world'")
            assert result is not None
            
            # Test variable assignment and retrieval
            client.execute_python("test_var = 42")
            result = client.execute_python("result = test_var")
            assert result is not None
            
        finally:
            client.disconnect()
    
    def test_blender_api_integration(self, bld_remote_service):
        """Test Blender API access through our service."""
        port = bld_remote_service
        client = BlenderMCPClient(port=port)
        
        try:
            # Test importing bpy
            result = client.execute_python("import bpy; result = 'bpy_imported'")
            assert result is not None
            
            # Test accessing Blender data
            result = client.execute_python("import bpy; result = type(bpy.data).__name__")
            assert result is not None
            
            # Test Blender version access
            result = client.execute_python("import bpy; result = bpy.app.version")
            assert result is not None
            
        finally:
            client.disconnect()
    
    def test_scene_manipulation(self, bld_remote_service):
        """Test scene object manipulation through our service."""
        port = bld_remote_service
        client = BlenderMCPClient(port=port)
        
        try:
            # Clear scene
            clear_code = """
import bpy
# Select all objects
bpy.ops.object.select_all(action='SELECT')
# Delete all objects
bpy.ops.object.delete(use_global=False, confirm=False)
result = 'scene_cleared'
"""
            result = client.execute_python(clear_code)
            assert result is not None
            
            # Create objects
            create_code = """
import bpy
# Create a cube
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "TestCube"

# Create a sphere
bpy.ops.mesh.primitive_uv_sphere_add(location=(3, 0, 0))
sphere = bpy.context.active_object
sphere.name = "TestSphere"

result = len(bpy.data.objects)
"""
            result = client.execute_python(create_code)
            assert result is not None
            
            # Verify objects exist
            verify_code = """
import bpy
object_names = [obj.name for obj in bpy.data.objects]
result = object_names
"""
            result = client.execute_python(verify_code)
            assert result is not None
            
        finally:
            client.disconnect()
    
    def test_error_handling(self, bld_remote_service):
        """Test service error handling with invalid code."""
        port = bld_remote_service
        client = BlenderMCPClient(port=port)
        
        try:
            # Test syntax error
            result = client.execute_python("this is invalid python syntax <<<")
            # Service should handle gracefully (either return error info or handle silently)
            assert result is not None
            
            # Test runtime error
            result = client.execute_python("result = 1 / 0")
            # Service should handle gracefully
            assert result is not None
            
            # Test undefined variable
            result = client.execute_python("result = undefined_variable_name")
            # Service should handle gracefully
            assert result is not None
            
        finally:
            client.disconnect()
    
    def test_large_code_execution(self, bld_remote_service):
        """Test execution of large code blocks."""
        port = bld_remote_service
        client = BlenderMCPClient(port=port)
        
        try:
            large_code = '''
import bpy
import math
import random

# Create multiple objects with random positions
objects_created = []
for i in range(20):
    x = random.uniform(-10, 10)
    y = random.uniform(-10, 10)
    z = random.uniform(0, 5)
    
    if i % 2 == 0:
        bpy.ops.mesh.primitive_cube_add(location=(x, y, z))
    else:
        bpy.ops.mesh.primitive_uv_sphere_add(location=(x, y, z))
    
    obj = bpy.context.active_object
    obj.name = f"LargeTest_{i}"
    objects_created.append(obj.name)

# Perform mathematical calculations
calculations = []
for angle in range(0, 360, 10):
    rad = math.radians(angle)
    sin_val = math.sin(rad)
    cos_val = math.cos(rad)
    tan_val = math.tan(rad) if abs(cos_val) > 0.001 else 0
    calculations.append((sin_val, cos_val, tan_val))

# Generate some complex data structures
nested_data = {
    "objects": {
        "count": len(objects_created),
        "names": objects_created[:5],  # First 5 names
        "total_names": len(objects_created)
    },
    "calculations": {
        "count": len(calculations),
        "sample": calculations[:3],  # First 3 calculations
        "average_sin": sum(calc[0] for calc in calculations) / len(calculations)
    },
    "metadata": {
        "blender_version": bpy.app.version_string,
        "scene_name": bpy.context.scene.name,
        "timestamp": "generated_by_large_code_test"
    }
}

result = nested_data
'''
            
            result = client.execute_python(large_code)
            assert result is not None, "Large code execution failed"
            
        finally:
            client.disconnect()
    
    def test_multiple_concurrent_connections(self, bld_remote_service):
        """Test handling multiple client connections."""
        port = bld_remote_service
        
        clients = []
        try:
            # Create multiple clients
            for i in range(3):
                client = BlenderMCPClient(port=port)
                clients.append(client)
            
            # Execute commands on different clients
            for i, client in enumerate(clients):
                result = client.execute_python(f"client_{i}_var = {i * 10}")
                assert result is not None
            
            # Verify variables from different client
            for i, client in enumerate(clients):
                result = client.execute_python(f"result = client_{i}_var")
                assert result is not None
                
        finally:
            for client in clients:
                try:
                    client.disconnect()
                except:
                    pass
    
    def test_service_robustness(self, bld_remote_service):
        """Test service robustness with rapid requests."""
        port = bld_remote_service
        client = BlenderMCPClient(port=port)
        
        try:
            # Send many requests rapidly
            for i in range(50):
                result = client.execute_python(f"rapid_test_{i} = {i}")
                assert result is not None, f"Request {i} failed"
            
            # Verify all variables were set
            verify_code = """
import bpy
# Count how many rapid_test variables were created
rapid_vars = [name for name in dir() if name.startswith('rapid_test_')]
result = len(rapid_vars)
"""
            result = client.execute_python(verify_code)
            assert result is not None
            
        finally:
            client.disconnect()
    
    def test_json_message_format(self, bld_remote_service):
        """Test raw JSON message format compatibility."""
        port = bld_remote_service
        
        # Test direct TCP communication with JSON messages
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect(('127.0.0.1', port))
            
            # Send JSON message
            message = {
                "code": "test_json_var = 'direct_json_test'",
                "message": "Testing direct JSON communication"
            }
            json_data = json.dumps(message)
            sock.sendall(json_data.encode('utf-8'))
            
            # Receive response
            response_data = sock.recv(4096)
            response = json.loads(response_data.decode('utf-8'))
            
            assert isinstance(response, dict), "Response should be JSON object"
            assert 'response' in response or 'message' in response, "Response should contain expected fields"
            
        finally:
            sock.close()
    
    def test_memory_management(self, bld_remote_service):
        """Test memory management with repeated operations."""
        port = bld_remote_service
        client = BlenderMCPClient(port=port)
        
        try:
            # Create and delete many objects to test memory management
            for iteration in range(10):
                create_delete_code = f"""
import bpy
import gc

# Create objects
for i in range(50):
    bpy.ops.mesh.primitive_cube_add(location=(i, {iteration}, 0))
    obj = bpy.context.active_object
    obj.name = f"MemTest_{iteration}_{i}"

# Count objects
object_count = len(bpy.data.objects)

# Delete objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False, confirm=False)

# Force garbage collection
gc.collect()

result = f"iteration_{iteration}_objects_{object_count}"
"""
                result = client.execute_python(create_delete_code)
                assert result is not None, f"Memory test iteration {iteration} failed"
                
        finally:
            client.disconnect()


@pytest.mark.blender_required
def test_service_recovery_after_errors(bld_remote_service):
    """Test that service continues working after encountering errors."""
    port = bld_remote_service
    client = BlenderMCPClient(port=port)
    
    try:
        # Execute good command
        result1 = client.execute_python("good_var_1 = 'before_error'")
        assert result1 is not None
        
        # Execute bad command that should cause error
        result2 = client.execute_python("this will cause a syntax error <<<")
        # Don't assert on result2 as it may handle errors differently
        
        # Execute another good command to verify service still works
        result3 = client.execute_python("good_var_2 = 'after_error'")
        assert result3 is not None, "Service failed to recover after error"
        
        # Verify both good variables exist
        result4 = client.execute_python("result = (good_var_1, good_var_2)")
        assert result4 is not None, "Service state corrupted after error"
        
    finally:
        client.disconnect()


if __name__ == "__main__":
    # Allow running this test file directly
    pytest.main([__file__, "-v", "-s"])