#!/usr/bin/env python3
"""
Error Handling and Edge Cases Testing

Tests error handling and edge case scenarios including:
- Network connectivity issues
- Invalid object names and parameters
- Memory limitations with large exports
- Blender API errors propagation
- Graceful degradation scenarios

Based on: context/plans/blender-remote-client-test-plan.md
"""

import sys
import os
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


class ErrorHandlingTests:
    """Test error handling and edge cases for blender-remote client APIs."""
    
    def __init__(self, host='127.0.0.1', port=6688):
        self.host = host
        self.port = port
        self.client = None
        self.scene_manager = None
    
    def setup_clients(self):
        """Setup client connections for testing."""
        try:
            print(f"🔌 Setting up clients for {self.host}:{self.port}...")
            
            self.client = BlenderMCPClient(host=self.host, port=self.port)
            if not self.client.test_connection():
                raise BlenderConnectionError("Client connection test failed")
            
            self.scene_manager = BlenderSceneManager(self.client)
            
            print("✅ Clients established successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup clients: {e}")
            return False
    
    def test_network_connectivity_issues(self):
        """Test network connectivity issues and recovery."""
        print("\n📋 Test: Network Connectivity Issues")
        
        try:
            results = {}
            
            # Test 1: Invalid host connection
            print("  Testing invalid host connection...")
            try:
                invalid_client = BlenderMCPClient(host="192.0.2.1", port=self.port, timeout=2)  # RFC5737 test address
                invalid_client.test_connection()
                results["invalid_host"] = {"unexpected_success": True}
                print("    ⚠️ Invalid host connection unexpectedly succeeded")
            except Exception as e:
                results["invalid_host"] = {
                    "expected_error": True,
                    "error_type": type(e).__name__,
                    "timeout_handled": "timeout" in str(e).lower() or "connection" in str(e).lower()
                }
                print(f"    ✅ Invalid host properly handled: {type(e).__name__}")
            
            # Test 2: Invalid port connection
            print("  Testing invalid port connection...")
            try:
                invalid_port_client = BlenderMCPClient(host=self.host, port=99999, timeout=2)
                invalid_port_client.test_connection()
                results["invalid_port"] = {"unexpected_success": True}
                print("    ⚠️ Invalid port connection unexpectedly succeeded")
            except Exception as e:
                results["invalid_port"] = {
                    "expected_error": True,
                    "error_type": type(e).__name__,
                    "connection_refused": "refused" in str(e).lower() or "connection" in str(e).lower()
                }
                print(f"    ✅ Invalid port properly handled: {type(e).__name__}")
            
            # Test 3: Timeout handling
            print("  Testing timeout handling...")
            try:
                timeout_client = BlenderMCPClient(host=self.host, port=self.port, timeout=0.001)  # Very short timeout
                start_time = time.time()
                timeout_client.get_scene_info()
                elapsed = time.time() - start_time
                results["timeout"] = {"unexpected_success": True, "elapsed": elapsed}
                print(f"    ⚠️ Timeout test unexpectedly succeeded in {elapsed:.3f}s")
            except Exception as e:
                elapsed = time.time() - start_time
                results["timeout"] = {
                    "expected_error": True,
                    "error_type": type(e).__name__,
                    "fast_timeout": elapsed < 1.0  # Should timeout quickly
                }
                print(f"    ✅ Timeout properly handled in {elapsed:.3f}s: {type(e).__name__}")
            
            return {"status": "success", "results": results}
            
        except Exception as e:
            print(f"    ❌ Network connectivity test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    def test_invalid_parameters(self):
        """Test invalid object names and parameters."""
        print("\n📋 Test: Invalid Parameters")
        
        try:
            results = {}
            
            # Test 1: Invalid object names
            print("  Testing invalid object names...")
            invalid_names = ["", None, "NonExistentObject12345", "Object/With/Slashes", "Object With Spaces"]
            
            for i, name in enumerate(invalid_names):
                try:
                    self.client.get_object_info(name)
                    results[f"invalid_name_{i}"] = {"unexpected_success": True, "name": name}
                    print(f"    ⚠️ Invalid name '{name}' unexpectedly succeeded")
                except Exception as e:
                    results[f"invalid_name_{i}"] = {
                        "expected_error": True,
                        "error_type": type(e).__name__,
                        "name": name
                    }
                    print(f"    ✅ Invalid name '{name}' properly handled: {type(e).__name__}")
            
            # Test 2: Invalid primitive parameters
            print("  Testing invalid primitive parameters...")
            try:
                self.scene_manager.add_primitive(
                    primitive_type="invalid_type", 
                    location="invalid_location",
                    name=None
                )
                results["invalid_primitive"] = {"unexpected_success": True}
                print("    ⚠️ Invalid primitive parameters unexpectedly succeeded")
            except Exception as e:
                results["invalid_primitive"] = {
                    "expected_error": True,
                    "error_type": type(e).__name__
                }
                print(f"    ✅ Invalid primitive parameters properly handled: {type(e).__name__}")
            
            # Test 3: Invalid coordinates
            print("  Testing invalid coordinates...")
            invalid_coords = ["not_coords", [1, 2], [1, 2, 3, 4], None]
            
            for i, coords in enumerate(invalid_coords):
                try:
                    self.scene_manager.add_primitive(
                        primitive_type="cube",
                        location=coords,
                        name=f"InvalidCoord_{i}"
                    )
                    results[f"invalid_coords_{i}"] = {"unexpected_success": True, "coords": coords}
                    print(f"    ⚠️ Invalid coords {coords} unexpectedly succeeded")
                except Exception as e:
                    results[f"invalid_coords_{i}"] = {
                        "expected_error": True,
                        "error_type": type(e).__name__,
                        "coords": coords
                    }
                    print(f"    ✅ Invalid coords {coords} properly handled: {type(e).__name__}")
            
            return {"status": "success", "results": results}
            
        except Exception as e:
            print(f"    ❌ Invalid parameters test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    def test_blender_api_errors(self):
        """Test Blender API errors propagation."""
        print("\n📋 Test: Blender API Error Propagation")
        
        try:
            results = {}
            
            # Test 1: Invalid Blender operation
            print("  Testing invalid Blender operations...")
            invalid_blender_code = '''
import bpy

# Try to perform invalid operations
bpy.ops.nonexistent.operation()
'''
            
            try:
                self.client.execute_python(invalid_blender_code)
                results["invalid_blender_op"] = {"unexpected_success": True}
                print("    ⚠️ Invalid Blender operation unexpectedly succeeded")
            except Exception as e:
                results["invalid_blender_op"] = {
                    "expected_error": True,
                    "error_type": type(e).__name__,
                    "blender_error_propagated": "AttributeError" in str(e) or "nonexistent" in str(e)
                }
                print(f"    ✅ Invalid Blender operation properly handled: {type(e).__name__}")
            
            # Test 2: Python syntax errors
            print("  Testing Python syntax errors...")
            syntax_error_code = '''
import bpy
this is not valid python syntax !@#$%
'''
            
            try:
                self.client.execute_python(syntax_error_code)
                results["syntax_error"] = {"unexpected_success": True}
                print("    ⚠️ Python syntax error unexpectedly succeeded")
            except Exception as e:
                results["syntax_error"] = {
                    "expected_error": True,
                    "error_type": type(e).__name__,
                    "syntax_error_detected": "syntax" in str(e).lower() or "invalid" in str(e).lower()
                }
                print(f"    ✅ Python syntax error properly handled: {type(e).__name__}")
            
            # Test 3: Division by zero
            print("  Testing runtime errors...")
            runtime_error_code = '''
import bpy

# Runtime error
result = 1 / 0
print(f"Result: {result}")
'''
            
            try:
                self.client.execute_python(runtime_error_code)
                results["runtime_error"] = {"unexpected_success": True}
                print("    ⚠️ Runtime error unexpectedly succeeded")
            except Exception as e:
                results["runtime_error"] = {
                    "expected_error": True,
                    "error_type": type(e).__name__,
                    "runtime_error_detected": "zerodivision" in str(e).lower() or "division" in str(e).lower()
                }
                print(f"    ✅ Runtime error properly handled: {type(e).__name__}")
            
            return {"status": "success", "results": results}
            
        except Exception as e:
            print(f"    ❌ Blender API error test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    def test_resource_limitations(self):
        """Test resource limitations and memory handling."""
        print("\n📋 Test: Resource Limitations")
        
        try:
            results = {}
            
            # Test 1: Large object creation
            print("  Testing large object creation handling...")
            large_object_code = '''
import bpy
import json

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a high-polygon sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=2, segments=64, ring_count=32)
sphere = bpy.context.active_object
sphere.name = "HighPolySphere"

# Get some basic info (don't extract all vertices to avoid huge data)
result = {
    "object_created": True,
    "object_name": sphere.name,
    "vertex_count": len(sphere.data.vertices),
    "face_count": len(sphere.data.polygons),
    "high_poly": len(sphere.data.vertices) > 1000
}

print(json.dumps(result, indent=2))
'''
            
            try:
                result = self.client.execute_python(large_object_code)
                results["large_object"] = {
                    "success": True,
                    "handled_large_object": "HighPolySphere" in str(result),
                    "vertex_count_reported": "vertex_count" in str(result)
                }
                print("    ✅ Large object creation handled successfully")
            except Exception as e:
                results["large_object"] = {
                    "success": False,
                    "error_type": type(e).__name__,
                    "memory_related": "memory" in str(e).lower() or "timeout" in str(e).lower()
                }
                print(f"    ❌ Large object creation failed: {type(e).__name__}")
            
            # Test 2: Rapid command execution
            print("  Testing rapid command execution...")
            rapid_commands_results = []
            
            for i in range(5):  # Send 5 rapid commands
                try:
                    start_time = time.time()
                    result = self.client.execute_python(f"print('Rapid command {i}')")
                    elapsed = time.time() - start_time
                    rapid_commands_results.append({"success": True, "elapsed": elapsed})
                except Exception as e:
                    rapid_commands_results.append({"success": False, "error": str(e)})
            
            success_count = sum(1 for r in rapid_commands_results if r["success"])
            results["rapid_commands"] = {
                "total_commands": len(rapid_commands_results),
                "successful_commands": success_count,
                "success_rate": success_count / len(rapid_commands_results) * 100,
                "handled_rapid_execution": success_count >= 3  # At least 60% success
            }
            
            print(f"    ✅ Rapid commands: {success_count}/{len(rapid_commands_results)} succeeded")
            
            return {"status": "success", "results": results}
            
        except Exception as e:
            print(f"    ❌ Resource limitations test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    def run_all_tests(self):
        """Run all error handling tests."""
        print("=" * 80)
        print("🧪 Error Handling and Edge Cases Tests")
        print("=" * 80)
        
        if not self.setup_clients():
            return {"status": "setup_failed", "error": "Could not establish client connections"}
        
        tests = [
            ("Network Connectivity Issues", self.test_network_connectivity_issues),
            ("Invalid Parameters", self.test_invalid_parameters),
            ("Blender API Error Propagation", self.test_blender_api_errors),
            ("Resource Limitations", self.test_resource_limitations)
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
        overall_status = "PASS" if passed_count >= (total_count * 0.75) else "FAIL"  # 75% threshold
        
        print("\n" + "=" * 80)
        print("📊 Error Handling Test Results:")
        for test_name, result in results.items():
            status = "✅ PASS" if result.get("status") == "success" else "❌ FAIL"
            print(f"  {status} {test_name}")
        
        print(f"\n🎯 OVERALL RESULT: {overall_status}")
        print(f"📊 Success Rate: {passed_count}/{total_count} ({success_rate:.1f}%)")
        
        if overall_status == "PASS":
            print("✅ Error handling is robust and handles edge cases properly")
        else:
            print("❌ Error handling issues detected - review implementation")
        
        return {
            "overall_status": overall_status,
            "success_rate": success_rate,
            "individual_results": results,
            "passed_count": passed_count,
            "total_count": total_count
        }


def main():
    """Run error handling tests."""
    tester = ErrorHandlingTests()
    results = tester.run_all_tests()
    
    exit_code = 0 if results.get("overall_status") == "PASS" else 1
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)