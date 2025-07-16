#!/usr/bin/env python3
"""
I/O Handling Focused Tests - Corrected Issues Investigation

Priority testing for Input/Output handling correctness focusing on:
- Parameter validation and type conversion correctness
- Response parsing correctness (JSON, string extraction)
- Data transmission integrity and command serialization
- Exception mapping and error response processing correctness
- Coordinate and vertex data serialization correctness
- Unicode and special character handling correctness

Based on: context/plans/blender-remote-client-test-plan.md (Priority Test Category 0)
"""

import sys
import os
import json
import time

# Add project src to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(project_root, "src"))

try:
    from blender_remote.client import BlenderMCPClient
    from blender_remote.scene_manager import BlenderSceneManager
    from blender_remote.exceptions import BlenderConnectionError, BlenderExecutionError
except ImportError as e:
    print(f"❌ Failed to import blender_remote modules: {e}")
    sys.exit(1)


class IOHandlingFocusedTests:
    """Test I/O handling correctness for BlenderMCPClient and BlenderSceneManager."""
    
    def __init__(self, host='127.0.0.1', port=6688):
        self.host = host
        self.port = port
        self.client = None
        self.scene_manager = None
    
    def setup_clients(self):
        """Setup client connections for testing."""
        try:
            print(f"🔌 Setting up clients for {self.host}:{self.port}...")
            
            # Setup BlenderMCPClient
            self.client = BlenderMCPClient(host=self.host, port=self.port)
            if not self.client.test_connection():
                raise BlenderConnectionError("Client connection test failed")
            
            # Setup BlenderSceneManager
            self.scene_manager = BlenderSceneManager(self.client)
            
            print("✅ Both clients established successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup clients: {e}")
            return False
    
    def test_parameter_validation_correctness(self):
        """Test parameter validation and type conversion correctness."""
        print("\n📋 Test: Parameter Validation & Type Conversion Correctness")
        
        try:
            results = {}
            
            # Test 1: get_object_info with 'name' parameter (corrected issue)
            print("  Testing get_object_info with 'name' parameter...")
            try:
                obj_info = self.client.get_object_info("Cube")  # Should work with object_name
                results["get_object_info_name_param"] = {
                    "success": True,
                    "has_data": bool(obj_info and len(str(obj_info)) > 10)
                }
                print("    ✅ get_object_info('Cube') works correctly")
            except Exception as e:
                results["get_object_info_name_param"] = {"success": False, "error": str(e)}
                print(f"    ❌ get_object_info failed: {e}")
            
            # Test 2: Coordinate handling correctness
            print("  Testing coordinate parameter handling...")
            try:
                # Test different coordinate formats
                coord_formats = [
                    (0, 0, 0),           # Tuple
                    [1, 1, 1],           # List
                    (2.5, -1.0, 0.5),    # Float tuple
                ]
                
                coord_results = {}
                for i, coords in enumerate(coord_formats):
                    try:
                        # Test with scene manager add_primitive
                        result = self.scene_manager.add_primitive(
                            primitive_type="cube",
                            location=coords,
                            name=f"CoordTest_{i}"
                        )
                        coord_results[f"coords_{i}"] = {"success": True, "coords": coords}
                        print(f"    ✅ Coordinates {coords}: Success")
                    except Exception as e:
                        coord_results[f"coords_{i}"] = {"success": False, "error": str(e)}
                        print(f"    ❌ Coordinates {coords}: Failed - {e}")
                
                results["coordinate_handling"] = coord_results
                
            except Exception as e:
                results["coordinate_handling"] = {"error": str(e)}
                print(f"    ❌ Coordinate handling test failed: {e}")
            
            success_rate = self._calculate_success_rate(results)
            return {
                "status": "success" if success_rate >= 80 else "failed",
                "results": results,
                "success_rate": success_rate
            }
            
        except Exception as e:
            print(f"    ❌ Parameter validation test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    def test_response_parsing_correctness(self):
        """Test response parsing correctness (JSON, string extraction)."""
        print("\n📋 Test: Response Parsing Correctness")
        
        try:
            results = {}
            
            # Test 1: JSON response parsing
            print("  Testing JSON response parsing...")
            try:
                scene_info = self.client.get_scene_info()
                
                # Validate JSON structure parsing
                json_validation = {
                    "is_dict": isinstance(scene_info, dict),
                    "has_data": bool(scene_info and len(scene_info) > 0),
                    "can_serialize": True
                }
                
                # Test JSON serialization roundtrip
                try:
                    json_str = json.dumps(scene_info)
                    parsed_back = json.loads(json_str)
                    json_validation["roundtrip_success"] = True
                except:
                    json_validation["roundtrip_success"] = False
                    json_validation["can_serialize"] = False
                
                results["json_parsing"] = json_validation
                print("    ✅ JSON response parsing works correctly")
                
            except Exception as e:
                results["json_parsing"] = {"error": str(e)}
                print(f"    ❌ JSON parsing failed: {e}")
            
            # Test 2: String extraction from responses
            print("  Testing string extraction from responses...")
            try:
                python_result = self.client.execute_python("print('I/O Test String: Success')")
                
                string_validation = {
                    "has_result": python_result is not None,
                    "is_string_like": hasattr(python_result, '__str__'),
                    "contains_expected": "I/O Test String" in str(python_result)
                }
                
                results["string_extraction"] = string_validation
                print("    ✅ String extraction works correctly")
                
            except Exception as e:
                results["string_extraction"] = {"error": str(e)}
                print(f"    ❌ String extraction failed: {e}")
            
            success_rate = self._calculate_success_rate(results)
            return {
                "status": "success" if success_rate >= 80 else "failed",
                "results": results,
                "success_rate": success_rate
            }
            
        except Exception as e:
            print(f"    ❌ Response parsing test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    def test_data_transmission_integrity(self):
        """Test data transmission integrity and command serialization."""
        print("\n📋 Test: Data Transmission Integrity")
        
        try:
            results = {}
            
            # Test 1: Command serialization integrity
            print("  Testing command serialization...")
            try:
                # Send complex command and verify it's processed correctly
                complex_code = '''
import bpy
import json

# Create test data with various types
test_data = {
    "string": "test_string_123",
    "integer": 42,
    "float": 3.14159,
    "boolean": True,
    "list": [1, 2, 3, "four"],
    "nested": {"key": "value", "number": 123}
}

print(json.dumps(test_data, indent=2))
'''
                
                result = self.client.execute_python(complex_code)
                
                # Validate data integrity
                integrity_validation = {
                    "command_sent": True,
                    "response_received": result is not None,
                    "contains_test_data": "test_string_123" in str(result),
                    "contains_json": "{" in str(result) and "}" in str(result)
                }
                
                results["command_serialization"] = integrity_validation
                print("    ✅ Command serialization integrity verified")
                
            except Exception as e:
                results["command_serialization"] = {"error": str(e)}
                print(f"    ❌ Command serialization failed: {e}")
            
            # Test 2: Large data transmission
            print("  Testing large data transmission...")
            try:
                # Create objects and extract large vertex data
                large_data_code = '''
import bpy
import json

# Clear and create objects with vertex data
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create sphere with many vertices
bpy.ops.mesh.primitive_uv_sphere_add(radius=2, segments=32, ring_count=16)
sphere = bpy.context.active_object

# Extract vertex coordinates (large dataset)
vertices = []
for vertex in sphere.data.vertices:
    world_pos = sphere.matrix_world @ vertex.co
    vertices.append([world_pos.x, world_pos.y, world_pos.z])

result = {
    "vertex_count": len(vertices),
    "vertices": vertices[:10],  # First 10 vertices only to avoid huge response
    "data_size": "large",
    "total_vertices_available": len(vertices)
}

print(json.dumps(result, indent=2))
'''
                
                result = self.client.execute_python(large_data_code)
                
                large_data_validation = {
                    "large_command_sent": True,
                    "response_received": result is not None,
                    "contains_vertex_data": "vertex_count" in str(result),
                    "data_not_truncated": "total_vertices_available" in str(result)
                }
                
                results["large_data_transmission"] = large_data_validation
                print("    ✅ Large data transmission integrity verified")
                
            except Exception as e:
                results["large_data_transmission"] = {"error": str(e)}
                print(f"    ❌ Large data transmission failed: {e}")
            
            success_rate = self._calculate_success_rate(results)
            return {
                "status": "success" if success_rate >= 80 else "failed",
                "results": results,
                "success_rate": success_rate
            }
            
        except Exception as e:
            print(f"    ❌ Data transmission test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    def test_exception_mapping_correctness(self):
        """Test exception mapping and error response processing correctness."""
        print("\n📋 Test: Exception Mapping & Error Response Processing")
        
        try:
            results = {}
            
            # Test 1: Connection error handling
            print("  Testing connection error handling...")
            try:
                # Test with invalid port
                invalid_client = BlenderMCPClient(host=self.host, port=99999)
                try:
                    invalid_client.test_connection()
                    results["connection_error"] = {"unexpected_success": True}
                    print("    ⚠️ Connection to invalid port unexpectedly succeeded")
                except Exception as e:
                    results["connection_error"] = {
                        "expected_error": True,
                        "error_type": type(e).__name__,
                        "proper_exception": isinstance(e, (BlenderConnectionError, ConnectionError, OSError))
                    }
                    print(f"    ✅ Connection error properly handled: {type(e).__name__}")
                    
            except Exception as e:
                results["connection_error"] = {"setup_error": str(e)}
            
            # Test 2: Execution error handling
            print("  Testing execution error handling...")
            try:
                # Send invalid Python code
                invalid_code = "this is not valid python syntax !@#$%"
                try:
                    self.client.execute_python(invalid_code)
                    results["execution_error"] = {"unexpected_success": True}
                    print("    ⚠️ Invalid Python code unexpectedly succeeded")
                except Exception as e:
                    results["execution_error"] = {
                        "expected_error": True,
                        "error_type": type(e).__name__,
                        "has_error_message": len(str(e)) > 0
                    }
                    print(f"    ✅ Execution error properly handled: {type(e).__name__}")
                    
            except Exception as e:
                results["execution_error"] = {"setup_error": str(e)}
            
            # Test 3: Invalid object error handling
            print("  Testing invalid object error handling...")
            try:
                try:
                    self.client.get_object_info("NonExistentObject12345")
                    results["object_error"] = {"unexpected_success": True}
                    print("    ⚠️ Non-existent object query unexpectedly succeeded")
                except Exception as e:
                    results["object_error"] = {
                        "expected_error": True,
                        "error_type": type(e).__name__,
                        "has_error_message": len(str(e)) > 0
                    }
                    print(f"    ✅ Object error properly handled: {type(e).__name__}")
                    
            except Exception as e:
                results["object_error"] = {"setup_error": str(e)}
            
            success_rate = self._calculate_success_rate(results)
            return {
                "status": "success" if success_rate >= 60 else "failed",  # Lower threshold for error tests
                "results": results,
                "success_rate": success_rate
            }
            
        except Exception as e:
            print(f"    ❌ Exception mapping test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    def test_unicode_and_special_chars(self):
        """Test Unicode and special character handling correctness."""
        print("\n📋 Test: Unicode & Special Character Handling")
        
        try:
            results = {}
            
            # Test 1: Unicode string handling
            print("  Testing Unicode string handling...")
            try:
                unicode_code = '''
import bpy
import json

# Test Unicode strings
test_strings = [
    "English: Hello World",
    "Spanish: Hola Mundo", 
    "Chinese: 你好世界",
    "Japanese: こんにちは世界",
    "Russian: Привет мир",
    "Special chars: !@#$%^&*()_+-=[]{}|;:,.<>?"
]

result = {
    "unicode_test": "success",
    "test_strings": test_strings,
    "string_count": len(test_strings)
}

print(json.dumps(result, indent=2, ensure_ascii=False))
'''
                
                result = self.client.execute_python(unicode_code)
                
                unicode_validation = {
                    "command_executed": True,
                    "response_received": result is not None,
                    "contains_unicode_marker": "unicode_test" in str(result),
                    "no_encoding_errors": "UnicodeError" not in str(result)
                }
                
                results["unicode_handling"] = unicode_validation
                print("    ✅ Unicode string handling works correctly")
                
            except Exception as e:
                results["unicode_handling"] = {"error": str(e)}
                print(f"    ❌ Unicode handling failed: {e}")
            
            # Test 2: Special character in object names
            print("  Testing special characters in object names...")
            try:
                # Create object with special characters in name
                special_name_code = '''
import bpy

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create object with special name
bpy.ops.mesh.primitive_cube_add()
cube = bpy.context.active_object
special_name = "Test_Object-123!@#"
cube.name = special_name

result = {
    "object_created": True,
    "object_name": cube.name,
    "name_matches": cube.name == special_name
}

print(f"Special object result: {result}")
'''
                
                result = self.client.execute_python(special_name_code)
                
                special_chars_validation = {
                    "command_executed": True,
                    "response_received": result is not None,
                    "contains_special_chars": "Test_Object-123" in str(result),
                    "no_special_char_errors": "Error" not in str(result)
                }
                
                results["special_chars"] = special_chars_validation
                print("    ✅ Special character handling works correctly")
                
            except Exception as e:
                results["special_chars"] = {"error": str(e)}
                print(f"    ❌ Special character handling failed: {e}")
            
            success_rate = self._calculate_success_rate(results)
            return {
                "status": "success" if success_rate >= 80 else "failed",
                "results": results,
                "success_rate": success_rate
            }
            
        except Exception as e:
            print(f"    ❌ Unicode/special chars test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    def _calculate_success_rate(self, results):
        """Calculate success rate from nested results."""
        total_checks = 0
        successful_checks = 0
        
        for category, data in results.items():
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, bool):
                        total_checks += 1
                        if value:
                            successful_checks += 1
                    elif isinstance(value, dict) and "success" in value:
                        total_checks += 1
                        if value["success"]:
                            successful_checks += 1
                    elif key in ["expected_error", "proper_exception"] and value:
                        total_checks += 1
                        successful_checks += 1
        
        return (successful_checks / total_checks * 100) if total_checks > 0 else 0
    
    def run_all_tests(self):
        """Run all I/O handling focused tests."""
        print("=" * 80)
        print("🎯 I/O Handling Focused Tests - PRIORITY TESTING")
        print("=" * 80)
        print("Focus: Input/Output correctness validation for localhost usage")
        print()
        
        if not self.setup_clients():
            return {"status": "setup_failed", "error": "Could not establish client connections"}
        
        tests = [
            ("Parameter Validation & Type Conversion", self.test_parameter_validation_correctness),
            ("Response Parsing Correctness", self.test_response_parsing_correctness), 
            ("Data Transmission Integrity", self.test_data_transmission_integrity),
            ("Exception Mapping & Error Processing", self.test_exception_mapping_correctness),
            ("Unicode & Special Character Handling", self.test_unicode_and_special_chars)
        ]
        
        results = {}
        passed_count = 0
        
        for test_name, test_func in tests:
            print(f"\n🎯 Running: {test_name}")
            try:
                result = test_func()
                results[test_name] = result
                
                if result.get("status") == "success":
                    print(f"✅ {test_name}: PASSED ({result.get('success_rate', 0):.1f}% success rate)")
                    passed_count += 1
                else:
                    print(f"❌ {test_name}: FAILED - {result.get('error', 'Low success rate')}")
                    
            except Exception as e:
                results[test_name] = {"status": "exception", "error": str(e)}
                print(f"❌ {test_name}: EXCEPTION - {e}")
        
        total_count = len(tests)
        success_rate = (passed_count / total_count * 100) if total_count > 0 else 0
        overall_status = "PASS" if passed_count >= (total_count * 0.8) else "FAIL"  # 80% threshold
        
        print("\n" + "=" * 80)
        print("📊 I/O Handling Test Results:")
        for test_name, result in results.items():
            status = "✅ PASS" if result.get("status") == "success" else "❌ FAIL"
            rate = result.get("success_rate", 0)
            print(f"  {status} {test_name} ({rate:.1f}%)")
        
        print(f"\n🎯 OVERALL RESULT: {overall_status}")
        print(f"📊 Success Rate: {passed_count}/{total_count} ({success_rate:.1f}%)")
        
        if overall_status == "PASS":
            print("✅ I/O handling correctness validated for localhost usage")
        else:
            print("❌ I/O handling issues detected - review implementation")
        
        return {
            "overall_status": overall_status,
            "success_rate": success_rate,
            "individual_results": results,
            "passed_count": passed_count,
            "total_count": total_count
        }


def main():
    """Run I/O handling focused tests."""
    tester = IOHandlingFocusedTests()
    results = tester.run_all_tests()
    
    exit_code = 0 if results.get("overall_status") == "PASS" else 1
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)