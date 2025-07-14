#!/usr/bin/env python3
"""
Test script for BlenderMCPClient connection functionality.

Tests basic connection management, URL parsing, environment detection,
and connection error handling.
"""

import sys
import os
import time
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from blender_remote.client import BlenderMCPClient
from blender_remote.exceptions import (
    BlenderMCPError,
    BlenderConnectionError,
    BlenderTimeoutError,
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


def test_constructor_defaults():
    """Test BlenderMCPClient constructor with default parameters."""
    results = TestResults()
    
    try:
        # Test default constructor
        client = BlenderMCPClient()
        results.add_result("constructor_defaults", True, f"Host: {client.host}, Port: {client.port}")
        
        # Test with custom parameters
        client2 = BlenderMCPClient(host="example.com", port=8080, timeout=60.0)
        expected = (client2.host == "example.com" and 
                   client2.port == 8080 and 
                   client2.timeout == 60.0)
        results.add_result("constructor_custom", expected, f"Host: {client2.host}, Port: {client2.port}")
        
    except Exception as e:
        results.add_result("constructor_test", False, f"Exception: {str(e)}")
    
    return results


def test_url_parsing():
    """Test URL parsing functionality."""
    results = TestResults()
    
    test_cases = [
        ("localhost:6688", "localhost", 6688),
        ("http://localhost:6688", "localhost", 6688),
        ("example.com:9999", "example.com", 9999),
        ("http://127.0.0.1:6688", "127.0.0.1", 6688),
    ]
    
    for url, expected_host, expected_port in test_cases:
        try:
            client = BlenderMCPClient(host=url)
            success = (client.host == expected_host and client.port == expected_port)
            results.add_result(f"url_parse_{url}", success, 
                             f"Expected {expected_host}:{expected_port}, got {client.host}:{client.port}")
        except Exception as e:
            results.add_result(f"url_parse_{url}", False, f"Exception: {str(e)}")
    
    # Test from_url class method
    try:
        client = BlenderMCPClient.from_url("localhost:6688")
        success = (client.host == "localhost" and client.port == 6688)
        results.add_result("from_url_method", success, f"Host: {client.host}, Port: {client.port}")
    except Exception as e:
        results.add_result("from_url_method", False, f"Exception: {str(e)}")
    
    return results


def test_connection_failure():
    """Test connection failure handling."""
    results = TestResults()
    
    # Test connection to non-existent service
    client = BlenderMCPClient(host="localhost", port=99999, timeout=2.0)
    
    try:
        client.test_connection()
        results.add_result("connection_failure", False, "Should have failed to connect")
    except (BlenderConnectionError, BlenderTimeoutError, BlenderMCPError):
        results.add_result("connection_failure", True, "Correctly handled connection failure")
    except Exception as e:
        results.add_result("connection_failure", False, f"Unexpected exception: {str(e)}")
    
    return results


def test_live_connection():
    """Test connection to actual BLD_Remote_MCP service if available."""
    results = TestResults()
    
    # Try to connect to default service
    client = BlenderMCPClient(timeout=5.0)
    
    try:
        connected = client.test_connection()
        if connected:
            results.add_result("live_connection", True, "Successfully connected to BLD_Remote_MCP")
            
            # Test get_status if connected
            try:
                status = client.get_status()
                service_ok = status.get("status") == "connected"
                results.add_result("live_status", service_ok, f"Status: {status.get('status')}")
            except Exception as e:
                results.add_result("live_status", False, f"Status check failed: {str(e)}")
                
        else:
            results.add_result("live_connection", False, "Connection test returned False")
            
    except Exception as e:
        results.add_result("live_connection", False, f"Connection failed: {str(e)}")
    
    return results


def test_python_execution():
    """Test Python code execution if service is available."""
    results = TestResults()
    
    client = BlenderMCPClient(timeout=10.0)
    
    try:
        # Simple test code
        test_code = "print('Hello from Blender')"
        result = client.execute_python(test_code)
        
        # BLD_Remote_MCP doesn't capture print output, so just check for no error
        results.add_result("python_execution", True, f"Code executed: {result}")
        
        # Test with Blender API access
        blender_code = """
import bpy
scene_name = bpy.context.scene.name
print(f"Scene name: {scene_name}")
"""
        result2 = client.execute_python(blender_code)
        results.add_result("blender_api_access", True, f"Blender API accessible: {result2}")
        
    except Exception as e:
        results.add_result("python_execution", False, f"Execution failed: {str(e)}")
    
    return results


def main():
    """Run all connection tests."""
    print("=== BlenderMCPClient Connection Tests ===")
    print(f"Test started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_results = TestResults()
    
    # Run test suites
    test_suites = [
        ("Constructor Tests", test_constructor_defaults),
        ("URL Parsing Tests", test_url_parsing),
        ("Connection Failure Tests", test_connection_failure),
        ("Live Connection Tests", test_live_connection),
        ("Python Execution Tests", test_python_execution),
    ]
    
    for suite_name, test_func in test_suites:
        print(f"\n--- {suite_name} ---")
        suite_results = test_func()
        
        # Merge results
        for test in suite_results.tests:
            all_results.add_result(test["name"], test["passed"], test["message"])
    
    # Final summary
    success = all_results.summary()
    
    # Save results to log file
    log_dir = Path(__file__).parent.parent / "logs" / "tests"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"test_client_connection_{int(time.time())}.log"
    with open(log_file, "w") as f:
        f.write(f"BlenderMCPClient Connection Test Results\n")
        f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for test in all_results.tests:
            status = "PASS" if test["passed"] else "FAIL"
            f.write(f"[{status}] {test['name']}: {test['message']}\n")
        
        f.write(f"\nSummary: {all_results.passed}/{all_results.passed + all_results.failed} passed\n")
    
    print(f"\nResults saved to: {log_file}")
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())