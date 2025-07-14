#!/usr/bin/env python3
"""
Fallback communication test for blender-remote client classes.

Tests multiple communication methods to isolate issues:
1. Direct BlenderMCPClient/BlenderSceneManager (primary)
2. uvx blender-remote MCP server (backup method 1)
3. uvx blender-mcp MCP server (backup method 2)

This helps identify where problems occur in the communication stack.
"""

import sys
import os
import time
import json
import asyncio
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("Warning: mcp package not available, MCP fallback tests will be skipped")

from blender_remote.client import BlenderMCPClient
from blender_remote.scene_manager import BlenderSceneManager
from blender_remote.exceptions import BlenderMCPError


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


class FallbackCommunicationTester:
    """Test communication using multiple methods for validation."""
    
    def __init__(self):
        self.test_code = """
import bpy
import json

# Clear scene and create test objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a simple cube
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "FallbackTestCube"

# Return structured data
result = {
    "test_type": "fallback_communication",
    "objects_created": [cube.name],
    "cube_location": list(cube.location),
    "scene_object_count": len(bpy.context.scene.objects),
    "success": True
}

print(json.dumps(result, indent=2))
"""

    def test_direct_client(self):
        """Test using direct BlenderMCPClient."""
        results = TestResults()
        
        try:
            print("\n--- Testing Direct BlenderMCPClient ---")
            
            # Test basic connection
            client = BlenderMCPClient(timeout=10.0)
            connected = client.test_connection()
            results.add_result("direct_client_connection", connected, f"Connection: {connected}")
            
            if connected:
                # Test Python execution
                try:
                    execution_result = client.execute_python(self.test_code)
                    results.add_result("direct_client_execution", True, f"Executed: {len(execution_result)} chars")
                    
                    # Test scene manager
                    scene_manager = BlenderSceneManager(client)
                    scene_info = scene_manager.get_scene_summary()
                    has_objects = "objects" in scene_info
                    results.add_result("direct_scene_manager", has_objects, f"Objects: {len(scene_info.get('objects', []))}")
                    
                except Exception as e:
                    results.add_result("direct_client_execution", False, f"Execution failed: {str(e)}")
            
        except Exception as e:
            results.add_result("direct_client_error", False, f"Client error: {str(e)}")
        
        return results

    async def test_blender_remote_mcp(self):
        """Test using uvx blender-remote MCP server."""
        results = TestResults()
        
        if not MCP_AVAILABLE:
            results.add_result("mcp_not_available", False, "MCP package not installed")
            return results
        
        try:
            print("\n--- Testing uvx blender-remote MCP Server ---")
            
            server_params = StdioServerParameters(
                command="pixi",
                args=["run", "python", "src/blender_remote/mcp_server.py"],
                env=None,
            )
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize session
                    await session.initialize()
                    results.add_result("blender_remote_mcp_init", True, "Session initialized")
                    
                    # Test get_scene_info
                    scene_result = await session.call_tool("get_scene_info", {})
                    has_scene_content = scene_result and scene_result.content
                    results.add_result("blender_remote_mcp_scene_info", has_scene_content, 
                                     f"Scene info: {len(str(scene_result.content)) if has_scene_content else 0} chars")
                    
                    # Test execute_code
                    code_result = await session.call_tool("execute_code", {"code": self.test_code})
                    has_code_content = code_result and code_result.content
                    results.add_result("blender_remote_mcp_execute_code", has_code_content,
                                     f"Code result: {len(str(code_result.content)) if has_code_content else 0} chars")
                    
                    # Test with base64 encoding if available
                    try:
                        base64_result = await session.call_tool("execute_code", {
                            "code": self.test_code,
                            "send_as_base64": True,
                            "return_as_base64": True
                        })
                        has_base64_content = base64_result and base64_result.content
                        results.add_result("blender_remote_mcp_base64", has_base64_content,
                                         f"Base64 result: {len(str(base64_result.content)) if has_base64_content else 0} chars")
                    except Exception as e:
                        results.add_result("blender_remote_mcp_base64", False, f"Base64 failed: {str(e)}")
        
        except Exception as e:
            results.add_result("blender_remote_mcp_error", False, f"MCP error: {str(e)}")
        
        return results

    async def test_blender_mcp_original(self):
        """Test using uvx blender-mcp (original) if available."""
        results = TestResults()
        
        if not MCP_AVAILABLE:
            results.add_result("mcp_not_available", False, "MCP package not installed")
            return results
        
        try:
            print("\n--- Testing uvx blender-mcp (Original) ---")
            
            # This would require the original blender-mcp to be running
            # For now, we'll document the approach and test connection
            
            server_params = StdioServerParameters(
                command="uvx",
                args=["blender-mcp"],
                env=None,
            )
            
            try:
                async with stdio_client(server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        results.add_result("original_blender_mcp_init", True, "Original MCP session initialized")
                        
                        # Test basic methods
                        scene_result = await session.call_tool("get_scene_info", {})
                        has_scene_content = scene_result and scene_result.content
                        results.add_result("original_blender_mcp_scene_info", has_scene_content,
                                         f"Original scene info: {len(str(scene_result.content)) if has_scene_content else 0} chars")
                        
            except Exception as e:
                results.add_result("original_blender_mcp_not_available", False, 
                                 f"Original blender-mcp not available: {str(e)}")
        
        except Exception as e:
            results.add_result("original_blender_mcp_error", False, f"Original MCP error: {str(e)}")
        
        return results

    def test_tcp_direct(self):
        """Test direct TCP connection to BLD_Remote_MCP service."""
        results = TestResults()
        
        try:
            print("\n--- Testing Direct TCP to BLD_Remote_MCP ---")
            
            import socket
            
            # Test TCP connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            
            try:
                sock.connect(('127.0.0.1', 6688))
                results.add_result("tcp_connection", True, "TCP connection successful")
                
                # Send test command
                command = {"message": "validation", "code": "print('TCP Test OK')"}
                sock.sendall(json.dumps(command).encode('utf-8'))
                
                # Receive response
                response_data = sock.recv(4096)
                response = json.loads(response_data.decode('utf-8'))
                
                has_response = bool(response)
                results.add_result("tcp_command", has_response, f"TCP response: {response}")
                
                sock.close()
                
            except Exception as e:
                results.add_result("tcp_connection", False, f"TCP failed: {str(e)}")
                try:
                    sock.close()
                except:
                    pass
        
        except Exception as e:
            results.add_result("tcp_error", False, f"TCP error: {str(e)}")
        
        return results

    async def run_comparison_test(self):
        """Run all communication methods and compare results."""
        print("=== Fallback Communication Test ===")
        print("Testing multiple communication methods for validation")
        print(f"Test started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        all_results = TestResults()
        method_results = {}
        
        # Test methods in order of preference
        test_methods = [
            ("Direct Client", self.test_direct_client, False),  # Sync
            ("Blender Remote MCP", self.test_blender_remote_mcp, True),  # Async
            ("TCP Direct", self.test_tcp_direct, False),  # Sync
            ("Original Blender MCP", self.test_blender_mcp_original, True),  # Async
        ]
        
        for method_name, test_func, is_async in test_methods:
            print(f"\n{'='*60}")
            print(f"Testing: {method_name}")
            print(f"{'='*60}")
            
            try:
                if is_async:
                    method_result = await test_func()
                else:
                    method_result = test_func()
                
                method_results[method_name] = method_result
                
                # Merge results
                for test in method_result.tests:
                    test_name = f"{method_name.lower().replace(' ', '_')}_{test['name']}"
                    all_results.add_result(test_name, test["passed"], test["message"])
                
                # Summary for this method
                success_rate = (method_result.passed / (method_result.passed + method_result.failed) * 100) if (method_result.passed + method_result.failed) > 0 else 0
                print(f"\n{method_name} Summary: {method_result.passed}/{method_result.passed + method_result.failed} passed ({success_rate:.1f}%)")
                
            except Exception as e:
                print(f"ERROR testing {method_name}: {str(e)}")
                all_results.add_result(f"{method_name.lower().replace(' ', '_')}_exception", False, f"Exception: {str(e)}")
        
        # Final comparison and recommendations
        print(f"\n{'='*60}")
        print("=== COMMUNICATION METHOD ANALYSIS ===")
        print(f"{'='*60}")
        
        working_methods = []
        for method_name, result in method_results.items():
            if result.passed > 0:
                working_methods.append(method_name)
                print(f"✅ {method_name}: {result.passed} tests passed")
            else:
                print(f"❌ {method_name}: No tests passed")
        
        if working_methods:
            print(f"\n🎯 WORKING COMMUNICATION METHODS: {', '.join(working_methods)}")
            if "Direct Client" in working_methods:
                print("✅ Primary method (Direct Client) is working")
            else:
                print("⚠️ Primary method failed, use backup methods:")
                for method in working_methods:
                    print(f"  • {method}")
        else:
            print("\n❌ NO COMMUNICATION METHODS WORKING")
            print("🔧 Troubleshooting steps:")
            print("  1. Check if Blender is running with BLD_Remote_MCP addon")
            print("  2. Verify BLD_Remote_MCP service is on port 6688")
            print("  3. Try starting Blender with: export BLD_REMOTE_MCP_START_NOW=1 && blender")
        
        # Overall summary
        success = all_results.summary()
        return all_results, method_results, working_methods


def main():
    """Run fallback communication tests."""
    tester = FallbackCommunicationTester()
    
    # Run the comparison test
    try:
        results, method_results, working_methods = asyncio.run(tester.run_comparison_test())
    except Exception as e:
        print(f"ERROR: Failed to run tests: {str(e)}")
        return 1
    
    # Save results to log file
    log_dir = Path(__file__).parent.parent / "logs" / "tests"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"test_fallback_communication_{int(time.time())}.log"
    with open(log_file, "w") as f:
        f.write(f"Fallback Communication Test Results\n")
        f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("Working Communication Methods:\n")
        for method in working_methods:
            f.write(f"  ✅ {method}\n")
        
        f.write("\nDetailed Results:\n")
        for test in results.tests:
            status = "PASS" if test["passed"] else "FAIL"
            f.write(f"[{status}] {test['name']}: {test['message']}\n")
        
        f.write(f"\nSummary: {results.passed}/{results.passed + results.failed} passed\n")
        
        f.write("\nRecommendations:\n")
        if "Direct Client" in working_methods:
            f.write("✅ Use BlenderMCPClient and BlenderSceneManager (primary method working)\n")
        elif working_methods:
            f.write("⚠️ Use backup communication methods:\n")
            for method in working_methods:
                f.write(f"  • {method}\n")
        else:
            f.write("❌ No communication methods working - check Blender and BLD_Remote_MCP setup\n")
    
    print(f"\nResults saved to: {log_file}")
    return 0 if working_methods else 1


if __name__ == "__main__":
    sys.exit(main())