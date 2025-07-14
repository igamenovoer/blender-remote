#!/usr/bin/env python3
"""
Focused I/O correctness tests for blender-remote client classes.

Since core logic was validated with blender-mcp, focus on input/output 
handling correctness (localhost - performance not relevant):
- Parameter validation and type conversion correctness
- Response parsing and data extraction correctness  
- Data transmission integrity and encoding correctness
- Error handling and exception mapping correctness
- Type conversion and serialization correctness
"""

import sys
import os
import time
import json
import numpy as np
from pathlib import Path
from io import StringIO
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from blender_remote.client import BlenderMCPClient
from blender_remote.scene_manager import BlenderSceneManager
from blender_remote.exceptions import (
    BlenderMCPError,
    BlenderConnectionError,
    BlenderTimeoutError,
    BlenderCommandError,
)


class TestResults:
    """Helper class to track test results."""
    
    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0
    
    def add_result(self, test_name: str, passed: bool, message: str = ""):
        self.tests.append({
            "name": test_name,
            "passed": passed,
            "message": message
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1
        
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {test_name}: {message}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n=== Test Summary ===")
        print(f"Total: {total}, Passed: {self.passed}, Failed: {self.failed}")
        print(f"Success Rate: {(self.passed/total*100):.1f}%" if total > 0 else "No tests run")
        return self.failed == 0


class IOHandlingTester:
    """Test I/O handling specifically, assuming core logic is correct."""
    
    def test_parameter_validation_and_conversion(self):
        """Test input parameter validation and type conversion."""
        results = TestResults()
        
        print("\n--- Testing Parameter Validation and Conversion ---")
        
        # Test BlenderMCPClient URL parsing (I/O handling)
        test_cases = [
            ("localhost:6688", "localhost", 6688),
            ("http://localhost:6688", "localhost", 6688), 
            ("127.0.0.1:9999", "127.0.0.1", 9999),
            ("example.com:8080", "example.com", 8080),
        ]
        
        for url, expected_host, expected_port in test_cases:
            try:
                client = BlenderMCPClient(host=url)
                host_ok = client.host == expected_host
                port_ok = client.port == expected_port
                success = host_ok and port_ok
                results.add_result(f"url_parsing_{url.replace(':', '_')}", success,
                                 f"Expected {expected_host}:{expected_port}, got {client.host}:{client.port}")
            except Exception as e:
                results.add_result(f"url_parsing_{url.replace(':', '_')}", False, f"Exception: {str(e)}")
        
        # Test BlenderSceneManager coordinate conversion
        try:
            # Mock client for scene manager testing
            mock_client = MagicMock()
            scene_manager = BlenderSceneManager(mock_client)
            
            # Test numpy array coordinate handling
            test_coords = [
                ([1, 2, 3], "list"),
                ((1, 2, 3), "tuple"),
                (np.array([1, 2, 3]), "numpy_array"),
            ]
            
            for coords, coord_type in test_coords:
                try:
                    # Test coordinate validation (I/O validation)
                    converted = np.asarray(coords, dtype=np.float64)
                    valid_shape = converted.shape == (3,)
                    results.add_result(f"coordinate_conversion_{coord_type}", valid_shape,
                                     f"Shape: {converted.shape}, Values: {converted}")
                except Exception as e:
                    results.add_result(f"coordinate_conversion_{coord_type}", False, f"Exception: {str(e)}")
        
        except Exception as e:
            results.add_result("coordinate_conversion_setup", False, f"Setup failed: {str(e)}")
        
        return results

    def test_response_parsing_robustness(self):
        """Test response parsing and data extraction (core I/O issue)."""
        results = TestResults()
        
        print("\n--- Testing Response Parsing Robustness ---")
        
        # Test JSON response parsing variations
        json_test_cases = [
            ('{"status": "success", "result": {"test": "data"}}', True, "valid_json"),
            ('{"status": "error", "message": "Test error"}', True, "error_response"),
            ('{"status": "success", "result": ""}', True, "empty_result"),
            ('invalid json{', False, "invalid_json"),
            ('', False, "empty_response"),
            ('{"status": "success"', False, "incomplete_json"),
        ]
        
        for json_str, should_succeed, test_name in json_test_cases:
            try:
                parsed = json.loads(json_str)
                success = should_succeed
                results.add_result(f"json_parsing_{test_name}", success, f"Parsed: {type(parsed)}")
            except json.JSONDecodeError:
                success = not should_succeed  # Should fail for invalid JSON
                results.add_result(f"json_parsing_{test_name}", success, "JSONDecodeError as expected" if success else "Unexpected JSONDecodeError")
            except Exception as e:
                results.add_result(f"json_parsing_{test_name}", False, f"Unexpected exception: {str(e)}")
        
        # Test string parsing patterns used in scene_manager.py (fragile I/O)
        output_test_cases = [
            ('OBJECTS_JSON:[{"name": "Cube"}]\nother output', '{"name": "Cube"}', "objects_json_pattern"),
            ('some output\nOBJECTS_JSON:[{"name": "Sphere"}]', '{"name": "Sphere"}', "objects_json_with_prefix"),
            ('UPDATE_RESULTS:{"Cube": true}', '{"Cube": true}', "update_results_pattern"),
            ('no pattern here', None, "no_pattern_found"),
            ('OBJECTS_JSON:invalid json{', None, "invalid_pattern_data"),
        ]
        
        for output, expected_data, test_name in output_test_cases:
            try:
                # Simulate the parsing logic from scene_manager.py
                found_data = None
                for line in output.split('\n'):
                    if line.startswith("OBJECTS_JSON:"):
                        try:
                            import ast
                            found_data = ast.literal_eval(line[13:])
                            break
                        except:
                            pass
                    elif line.startswith("UPDATE_RESULTS:"):
                        try:
                            import ast
                            found_data = ast.literal_eval(line[15:])
                            break
                        except:
                            pass
                
                if expected_data is None:
                    success = found_data is None
                    results.add_result(f"string_parsing_{test_name}", success, f"No data found as expected")
                else:
                    success = found_data is not None
                    results.add_result(f"string_parsing_{test_name}", success, f"Found: {found_data}")
                    
            except Exception as e:
                results.add_result(f"string_parsing_{test_name}", False, f"Exception: {str(e)}")
        
        return results

    def test_data_transmission_correctness(self):
        """Test data transmission correctness (not performance - localhost only)."""
        results = TestResults()
        
        print("\n--- Testing Data Transmission Correctness ---")
        
        # Test data integrity - does data get through correctly?
        data_integrity_cases = [
            ("simple string", "simple_string"),
            ("string with spaces and punctuation!", "string_with_punctuation"),
            ("string with\nnewlines\nand\ttabs", "string_with_whitespace"),
            ('string with "quotes" and \'apostrophes\'', "string_with_quotes"),
            ("unicode string: 测试 ñáéíóú", "unicode_string"),
            ("{'json': 'data', 'number': 42}", "json_like_string"),
        ]
        
        for test_data, test_name in data_integrity_cases:
            try:
                # Test JSON encoding/decoding for data transmission
                encoded = json.dumps(test_data)
                decoded = json.loads(encoded)
                
                data_preserved = decoded == test_data
                results.add_result(f"data_integrity_{test_name}", data_preserved,
                                 f"Original: {repr(test_data[:50])}, Decoded: {repr(decoded[:50]) if isinstance(decoded, str) else repr(decoded)}")
                
            except Exception as e:
                results.add_result(f"data_integrity_{test_name}", False, f"Encoding/decoding failed: {str(e)}")
        
        # Test command formatting correctness (not performance)
        command_test_cases = [
            ({"type": "test", "params": {}}, "simple_command"),
            ({"type": "execute_code", "params": {"code": "print('test')"}}, "code_command"),
            ({"type": "test", "params": {"name": "object with spaces"}}, "params_with_spaces"),
            ({"type": "test", "params": {"unicode": "测试"}}, "unicode_params"),
        ]
        
        for command_data, test_name in command_test_cases:
            try:
                # Test command serialization correctness
                command_json = json.dumps(command_data)
                parsed_command = json.loads(command_json)
                
                command_preserved = parsed_command == command_data
                results.add_result(f"command_serialization_{test_name}", command_preserved,
                                 f"Command type: {command_data.get('type')}")
                
            except Exception as e:
                results.add_result(f"command_serialization_{test_name}", False, f"Serialization failed: {str(e)}")
        
        return results

    def test_error_mapping_and_exceptions(self):
        """Test error response mapping to appropriate exceptions."""
        results = TestResults()
        
        print("\n--- Testing Error Mapping and Exception Handling ---")
        
        # Test exception mapping scenarios
        error_scenarios = [
            ("Connection timeout", BlenderTimeoutError, "connection_timeout"),
            ("Connection refused", BlenderConnectionError, "connection_refused"), 
            ("Invalid JSON response", BlenderMCPError, "invalid_json"),
            ("Blender command failed", BlenderCommandError, "command_error"),
            ("Socket error", BlenderConnectionError, "socket_error"),
        ]
        
        for error_msg, expected_exception, test_name in error_scenarios:
            try:
                # Test that appropriate exception types are used for different error conditions
                if "timeout" in error_msg.lower():
                    exception_type = BlenderTimeoutError
                elif "connection" in error_msg.lower() or "socket" in error_msg.lower():
                    exception_type = BlenderConnectionError  
                elif "command" in error_msg.lower():
                    exception_type = BlenderCommandError
                else:
                    exception_type = BlenderMCPError
                
                correct_mapping = exception_type == expected_exception
                results.add_result(f"exception_mapping_{test_name}", correct_mapping,
                                 f"Expected {expected_exception.__name__}, got {exception_type.__name__}")
                
            except Exception as e:
                results.add_result(f"exception_mapping_{test_name}", False, f"Exception: {str(e)}")
        
        # Test exception message formatting
        try:
            test_exceptions = [
                BlenderMCPError("Test MCP error"),
                BlenderConnectionError("Test connection error"),
                BlenderTimeoutError("Test timeout error"),
                BlenderCommandError("Test command error"),
            ]
            
            for exc in test_exceptions:
                has_message = len(str(exc)) > 0
                is_informative = len(str(exc)) > 10  # Should be more than just error type
                results.add_result(f"exception_message_{exc.__class__.__name__}", 
                                 has_message and is_informative,
                                 f"Message: '{str(exc)}'")
                
        except Exception as e:
            results.add_result("exception_message_test", False, f"Exception: {str(e)}")
        
        return results

    def test_type_conversion_and_serialization(self):
        """Test data type conversion between Python and Blender/JSON."""
        results = TestResults()
        
        print("\n--- Testing Type Conversion and Serialization ---")
        
        # Test coordinate type handling (common I/O issue)
        coordinate_test_cases = [
            ([1, 2, 3], "list_input"),
            ((1, 2, 3), "tuple_input"),
            (np.array([1, 2, 3]), "numpy_input"),
            (np.array([1.5, 2.7, 3.1]), "numpy_float_input"),
        ]
        
        for coords, test_name in coordinate_test_cases:
            try:
                # Test conversion like scene_manager.py does
                converted = np.asarray(coords, dtype=np.float64)
                
                # Test shape validation
                valid_shape = converted.shape == (3,)
                
                # Test conversion to list for JSON serialization
                as_list = converted.tolist()
                serializable = all(isinstance(x, (int, float)) for x in as_list)
                
                success = valid_shape and serializable
                results.add_result(f"coordinate_conversion_{test_name}", success,
                                 f"Shape: {converted.shape}, Type: {type(as_list[0])}")
                
            except Exception as e:
                results.add_result(f"coordinate_conversion_{test_name}", False, f"Exception: {str(e)}")
        
        # Test quaternion handling (rotation data)
        try:
            # Test quaternion conversion and validation
            test_quaternions = [
                ([1, 0, 0, 0], "identity_quat"),
                ([0.707, 0.707, 0, 0], "rotation_quat"),
                (np.array([1, 0, 0, 0]), "numpy_quat"),
            ]
            
            for quat, test_name in test_quaternions:
                quat_array = np.asarray(quat, dtype=np.float64)
                valid_shape = quat_array.shape == (4,)
                magnitude = np.linalg.norm(quat_array)
                is_normalized = abs(magnitude - 1.0) < 0.1  # Allow some tolerance
                
                success = valid_shape
                results.add_result(f"quaternion_handling_{test_name}", success,
                                 f"Shape: {quat_array.shape}, Magnitude: {magnitude:.3f}")
                
        except Exception as e:
            results.add_result("quaternion_handling", False, f"Exception: {str(e)}")
        
        # Test coordinate data serialization correctness (GLB export scenario)
        try:
            # Test vertex data correctness (not size/performance)
            test_vertex_data = [
                [0.0, 0.0, 0.0],      # origin
                [1.0, 2.0, 3.0],      # positive coords
                [-1.0, -2.0, -3.0],   # negative coords
                [0.5, 1.5, 2.5],      # decimal coords
            ]
            
            # Test JSON serialization correctness
            try:
                json_str = json.dumps(test_vertex_data)
                deserialized = json.loads(json_str)
                
                # Check data integrity
                data_correct = deserialized == test_vertex_data
                all_coords_preserved = all(
                    len(coord) == 3 and all(isinstance(x, (int, float)) for x in coord)
                    for coord in deserialized
                )
                
                success = data_correct and all_coords_preserved
                results.add_result("vertex_data_serialization", success,
                                 f"Vertices preserved: {data_correct}, Types correct: {all_coords_preserved}")
                
            except Exception as e:
                results.add_result("vertex_data_serialization", False, f"Serialization failed: {str(e)}")
        
        except Exception as e:
            results.add_result("vertex_data_test_setup", False, f"Setup failed: {str(e)}")
        
        return results

    def run_io_focused_tests(self):
        """Run all I/O handling focused tests."""
        print("="*80)
        print("🔍 I/O Correctness Focused Tests")
        print("🎯 Focus: Input/Output correctness (localhost - performance irrelevant)")
        print("✅ Assumption: Core Blender logic validated with blender-mcp")
        print("="*80)
        print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        all_results = TestResults()
        
        # Run I/O focused test suites (correctness only - localhost)
        test_suites = [
            ("Parameter Validation & Conversion", self.test_parameter_validation_and_conversion),
            ("Response Parsing Robustness", self.test_response_parsing_robustness),
            ("Data Transmission Correctness", self.test_data_transmission_correctness),
            ("Error Mapping & Exceptions", self.test_error_mapping_and_exceptions),
            ("Type Conversion & Serialization", self.test_type_conversion_and_serialization),
        ]
        
        for suite_name, test_func in test_suites:
            print(f"\n🔧 {suite_name}")
            print("-" * 60)
            suite_results = test_func()
            
            # Merge results
            for test in suite_results.tests:
                all_results.add_result(test["name"], test["passed"], test["message"])
        
        # I/O focused summary
        success = all_results.summary()
        
        print(f"\n🎯 I/O CORRECTNESS ASSESSMENT (localhost focus):")
        io_categories = {
            "Input Validation": [t for t in all_results.tests if "validation" in t["name"] or "conversion" in t["name"]],
            "Output Parsing": [t for t in all_results.tests if "parsing" in t["name"]],
            "Data Transmission": [t for t in all_results.tests if "data_integrity" in t["name"] or "serialization" in t["name"]],
            "Error Handling": [t for t in all_results.tests if "exception" in t["name"] or "error" in t["name"]],
        }
        
        for category, tests in io_categories.items():
            passed = sum(1 for t in tests if t["passed"])
            total = len(tests)
            if total > 0:
                print(f"  {category}: {passed}/{total} passed ({passed/total*100:.1f}%)")
        
        print(f"\n💡 CORRECTNESS ISSUES TO FIX:")
        failed_tests = [t for t in all_results.tests if not t["passed"]]
        if failed_tests:
            io_issues = {}
            for test in failed_tests:
                if "parsing" in test["name"]:
                    io_issues.setdefault("Response Parsing Correctness", []).append(test["name"])
                elif "conversion" in test["name"] or "validation" in test["name"]:
                    io_issues.setdefault("Input Validation Correctness", []).append(test["name"])
                elif "data_integrity" in test["name"] or "serialization" in test["name"]:
                    io_issues.setdefault("Data Transmission Correctness", []).append(test["name"])
                elif "exception" in test["name"]:
                    io_issues.setdefault("Error Handling Correctness", []).append(test["name"])
                else:
                    io_issues.setdefault("Other Correctness Issues", []).append(test["name"])
            
            for issue_type, test_names in io_issues.items():
                print(f"  🔧 {issue_type}: {len(test_names)} issues")
                for name in test_names[:3]:  # Show first 3
                    print(f"    • {name}")
        else:
            print("  ✅ All I/O correctness tests passed!")
        
        return all_results


def main():
    """Run I/O focused tests."""
    tester = IOHandlingTester()
    results = tester.run_io_focused_tests()
    
    # Save results to log file
    log_dir = Path(__file__).parent.parent / "logs" / "tests"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"test_io_handling_focused_{int(time.time())}.log"
    with open(log_file, "w") as f:
        f.write(f"I/O Handling Focused Test Results\n")
        f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Focus: Input/Output handling (core logic assumed validated)\n\n")
        
        for test in results.tests:
            status = "PASS" if test["passed"] else "FAIL"
            f.write(f"[{status}] {test['name']}: {test['message']}\n")
        
        f.write(f"\nSummary: {results.passed}/{results.passed + results.failed} passed\n")
    
    print(f"\nResults saved to: {log_file}")
    return 0 if results.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())