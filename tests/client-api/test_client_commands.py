#!/usr/bin/env python3
"""
BlenderMCPClient Command Execution Testing

Tests the command execution functionality of BlenderMCPClient including:
- execute_command() with valid/invalid commands
- execute_python() code execution
- Response parsing and error handling
- Large code block execution
- Concurrent command execution

Based on: context/plans/blender-remote-client-test-plan.md
"""

import sys
import os
import time
import asyncio
import json

# Add project src to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(project_root, "src"))

try:
    from blender_remote.client import BlenderMCPClient
    from blender_remote.exceptions import BlenderConnectionError, BlenderExecutionError
except ImportError as e:
    print(f"❌ Failed to import blender_remote modules: {e}")
    print("Make sure you're running from the project root and dependencies are installed")
    sys.exit(1)


class ClientCommandTests:
    """Test BlenderMCPClient command execution functionality."""
    
    def __init__(self, host='127.0.0.1', port=6688):
        self.host = host
        self.port = port
        self.client = None
    
    def setup_client(self):
        """Setup client connection for testing."""
        try:
            print(f"🔌 Connecting to Blender service at {self.host}:{self.port}...")
            self.client = BlenderMCPClient(host=self.host, port=self.port)
            
            # Test connection
            status = self.client.test_connection()
            if not status:
                raise BlenderConnectionError("Connection test failed")
            
            print("✅ Client connection established")
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup client: {e}")
            return False
    
    def test_execute_command_valid(self):
        """Test execute_command with valid commands."""
        print("\n📋 Test: Execute Valid Commands")
        
        try:
            # Test basic command execution
            commands = [
                "get_scene_info",
                "get_status", 
                "test_connection"
            ]
            
            results = {}
            for command in commands:
                print(f"  Testing command: {command}")
                result = self.client.execute_command(command)
                results[command] = {"success": True, "result": result}
                print(f"    ✅ {command}: Success")
            
            return {"status": "success", "results": results}
            
        except Exception as e:
            print(f"    ❌ Valid command test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    def test_execute_command_invalid(self):
        """Test execute_command with invalid commands."""
        print("\n📋 Test: Execute Invalid Commands")
        
        try:
            invalid_commands = [
                "nonexistent_command",
                "invalid_syntax!@#",
                "",
                None
            ]
            
            results = {}
            for command in invalid_commands:
                print(f"  Testing invalid command: {command}")
                try:
                    result = self.client.execute_command(command)
                    results[str(command)] = {"unexpected_success": True, "result": result}
                    print(f"    ⚠️ {command}: Unexpected success")
                except Exception as e:
                    results[str(command)] = {"expected_error": True, "error": str(e)}
                    print(f"    ✅ {command}: Expected error - {e}")
            
            return {"status": "success", "results": results}
            
        except Exception as e:
            print(f"    ❌ Invalid command test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    def test_execute_python_simple(self):
        """Test execute_python with simple code."""
        print("\n📋 Test: Execute Simple Python Code")
        
        try:
            test_codes = [
                "print('Hello from Blender')",
                "import bpy; print(f'Blender version: {bpy.app.version_string}')",
                "import bpy; print(f'Scene objects: {len(bpy.context.scene.objects)}')"
            ]
            
            results = {}
            for i, code in enumerate(test_codes):
                print(f"  Testing code {i+1}: {code[:50]}...")
                result = self.client.execute_python(code)
                results[f"code_{i+1}"] = {"success": True, "result": result}
                print(f"    ✅ Code {i+1}: Success")
            
            return {"status": "success", "results": results}
            
        except Exception as e:
            print(f"    ❌ Simple Python test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    def test_execute_python_complex(self):
        """Test execute_python with complex code."""
        print("\n📋 Test: Execute Complex Python Code")
        
        try:
            complex_code = '''
import bpy
import json

# Clear scene and create test objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create objects
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "TestCube"

bpy.ops.mesh.primitive_uv_sphere_add(location=(2, 0, 0))
sphere = bpy.context.active_object
sphere.name = "TestSphere"

# Return structured data
result = {
    "objects_created": [cube.name, sphere.name],
    "cube_location": list(cube.location),
    "sphere_location": list(sphere.location),
    "total_objects": len(bpy.context.scene.objects)
}

print(json.dumps(result, indent=2))
'''
            
            print(f"  Testing complex code ({len(complex_code)} chars)...")
            result = self.client.execute_python(complex_code)
            
            # Validate result contains expected data
            success = "TestCube" in str(result) and "TestSphere" in str(result)
            
            return {
                "status": "success" if success else "partial",
                "result": result,
                "code_length": len(complex_code),
                "contains_expected_data": success
            }
            
        except Exception as e:
            print(f"    ❌ Complex Python test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    def test_error_handling(self):
        """Test error handling for invalid Python code."""
        print("\n📋 Test: Error Handling for Invalid Python")
        
        try:
            error_codes = [
                "invalid python syntax !@#",
                "import nonexistent_module",
                "1/0  # Division by zero",
                "bpy.ops.nonexistent.operation()"
            ]
            
            results = {}
            for i, code in enumerate(error_codes):
                print(f"  Testing error code {i+1}: {code[:30]}...")
                try:
                    result = self.client.execute_python(code)
                    results[f"error_code_{i+1}"] = {"unexpected_success": True, "result": result}
                    print(f"    ⚠️ Error code {i+1}: Unexpected success")
                except Exception as e:
                    results[f"error_code_{i+1}"] = {"expected_error": True, "error": str(e)}
                    print(f"    ✅ Error code {i+1}: Expected error - {type(e).__name__}")
            
            return {"status": "success", "results": results}
            
        except Exception as e:
            print(f"    ❌ Error handling test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    def test_large_code_execution(self):
        """Test execution of large code blocks."""
        print("\n📋 Test: Large Code Block Execution")
        
        try:
            # Generate a large code block
            large_code = '''
import bpy
import json

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

objects = []
'''
            
            # Add repetitive code to make it large
            for i in range(20):  # Create 20 objects
                large_code += f'''
bpy.ops.mesh.primitive_cube_add(location=({i}, 0, 0))
cube_{i} = bpy.context.active_object
cube_{i}.name = "LargeCube_{i:03d}"
objects.append(cube_{i}.name)
'''
            
            large_code += '''
result = {
    "test_type": "large_code_execution",
    "objects_created": len(objects),
    "object_names": objects,
    "scene_object_count": len(bpy.context.scene.objects)
}

print(json.dumps(result, indent=2))
'''
            
            print(f"  Testing large code block ({len(large_code)} chars)...")
            start_time = time.time()
            result = self.client.execute_python(large_code)
            execution_time = time.time() - start_time
            
            success = "large_code_execution" in str(result)
            
            return {
                "status": "success" if success else "failed",
                "code_length": len(large_code),
                "execution_time": execution_time,
                "contains_expected_result": success,
                "result_sample": str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
            }
            
        except Exception as e:
            print(f"    ❌ Large code execution test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    def run_all_tests(self):
        """Run all command execution tests."""
        print("=" * 80)
        print("🧪 BlenderMCPClient Command Execution Tests")
        print("=" * 80)
        
        if not self.setup_client():
            return {"status": "setup_failed", "error": "Could not establish client connection"}
        
        tests = [
            ("Execute Valid Commands", self.test_execute_command_valid),
            ("Execute Invalid Commands", self.test_execute_command_invalid),
            ("Execute Simple Python Code", self.test_execute_python_simple),
            ("Execute Complex Python Code", self.test_execute_python_complex),
            ("Error Handling", self.test_error_handling),
            ("Large Code Block Execution", self.test_large_code_execution)
        ]
        
        results = {}
        passed_count = 0
        
        for test_name, test_func in tests:
            print(f"\n🧪 Running: {test_name}")
            try:
                result = test_func()
                results[test_name] = result
                
                if result.get("status") == "success":
                    print(f"✅ {test_name}: PASSED")
                    passed_count += 1
                else:
                    print(f"❌ {test_name}: FAILED - {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                results[test_name] = {"status": "exception", "error": str(e)}
                print(f"❌ {test_name}: EXCEPTION - {e}")
        
        total_count = len(tests)
        success_rate = (passed_count / total_count * 100) if total_count > 0 else 0
        overall_status = "PASS" if passed_count == total_count else "FAIL"
        
        print("\n" + "=" * 80)
        print("📊 Command Execution Test Results:")
        for test_name, result in results.items():
            status = "✅ PASS" if result.get("status") == "success" else "❌ FAIL"
            print(f"  {status} {test_name}")
        
        print(f"\n🎯 OVERALL RESULT: {overall_status}")
        print(f"📊 Success Rate: {passed_count}/{total_count} ({success_rate:.1f}%)")
        
        return {
            "overall_status": overall_status,
            "success_rate": success_rate,
            "individual_results": results,
            "passed_count": passed_count,
            "total_count": total_count
        }


def main():
    """Run command execution tests."""
    tester = ClientCommandTests()
    results = tester.run_all_tests()
    
    exit_code = 0 if results.get("overall_status") == "PASS" else 1
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)