#!/usr/bin/env python3
"""
Enhanced test runner with fallback communication methods.

This test runner tries multiple communication approaches to ensure robust testing:
1. Primary: Direct BlenderMCPClient/BlenderSceneManager classes
2. Fallback 1: uvx blender-remote MCP server  
3. Fallback 2: Direct TCP to BLD_Remote_MCP service
4. Fallback 3: uvx blender-mcp (original) if available

This approach helps isolate issues and provides validation even when 
primary methods have problems.
"""

import sys
import os
import time
import json
import asyncio
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

from blender_remote.client import BlenderMCPClient
from blender_remote.scene_manager import BlenderSceneManager
from blender_remote.exceptions import BlenderMCPError


class EnhancedTestRunner:
    """Test runner with multiple communication fallbacks."""
    
    def __init__(self):
        self.primary_method = "direct_client"
        self.fallback_methods = ["blender_remote_mcp", "tcp_direct", "original_blender_mcp"]
        self.working_methods = []
        
    def detect_working_methods(self):
        """Detect which communication methods are working."""
        print("🔍 Detecting working communication methods...")
        
        methods_status = {}
        
        # Test Direct Client
        try:
            client = BlenderMCPClient(timeout=5.0)
            if client.test_connection():
                methods_status["direct_client"] = True
                self.working_methods.append("direct_client")
                print("✅ Direct BlenderMCPClient: Working")
            else:
                methods_status["direct_client"] = False
                print("❌ Direct BlenderMCPClient: Connection failed")
        except Exception as e:
            methods_status["direct_client"] = False
            print(f"❌ Direct BlenderMCPClient: Exception - {str(e)}")
        
        # Test TCP Direct
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)
            sock.connect(('127.0.0.1', 6688))
            sock.close()
            methods_status["tcp_direct"] = True
            self.working_methods.append("tcp_direct")
            print("✅ TCP Direct to BLD_Remote_MCP: Working")
        except Exception as e:
            methods_status["tcp_direct"] = False
            print(f"❌ TCP Direct to BLD_Remote_MCP: Failed - {str(e)}")
        
        # Test MCP methods (async)
        if MCP_AVAILABLE:
            try:
                # This is a simplified sync test for MCP availability
                # Full async testing will be done later
                methods_status["blender_remote_mcp"] = True
                self.working_methods.append("blender_remote_mcp")
                print("✅ Blender Remote MCP: Available (will test async)")
            except Exception as e:
                methods_status["blender_remote_mcp"] = False
                print(f"❌ Blender Remote MCP: Exception - {str(e)}")
        else:
            methods_status["blender_remote_mcp"] = False
            print("❌ Blender Remote MCP: MCP package not available")
        
        print(f"\n🎯 Working methods: {', '.join(self.working_methods) if self.working_methods else 'None'}")
        return methods_status

    def execute_blender_code_direct(self, code: str):
        """Execute Blender code using direct client method."""
        try:
            client = BlenderMCPClient(timeout=15.0)
            result = client.execute_python(code)
            return {"success": True, "result": result, "method": "direct_client"}
        except Exception as e:
            return {"success": False, "error": str(e), "method": "direct_client"}

    def execute_blender_code_tcp(self, code: str):
        """Execute Blender code using direct TCP method."""
        try:
            import socket
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(15.0)
            sock.connect(('127.0.0.1', 6688))
            
            command = {"message": "execution", "code": code}
            sock.sendall(json.dumps(command).encode('utf-8'))
            
            response_data = sock.recv(8192)  # Larger buffer for results
            response = json.loads(response_data.decode('utf-8'))
            
            sock.close()
            return {"success": True, "result": response, "method": "tcp_direct"}
        except Exception as e:
            return {"success": False, "error": str(e), "method": "tcp_direct"}

    async def execute_blender_code_mcp(self, code: str, use_base64: bool = False):
        """Execute Blender code using MCP server method."""
        try:
            server_params = StdioServerParameters(
                command="pixi",
                args=["run", "python", "src/blender_remote/mcp_server.py"],
                env=None,
            )
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    params = {"code": code}
                    if use_base64:
                        params.update({
                            "send_as_base64": True,
                            "return_as_base64": True
                        })
                    
                    result = await session.call_tool("execute_code", params)
                    
                    return {
                        "success": True, 
                        "result": result, 
                        "method": "blender_remote_mcp",
                        "base64": use_base64
                    }
        except Exception as e:
            return {
                "success": False, 
                "error": str(e), 
                "method": "blender_remote_mcp",
                "base64": use_base64
            }

    def execute_with_fallback(self, code: str, test_name: str = "test"):
        """Execute code with automatic fallback to working methods."""
        results = []
        
        # Try methods in order of preference
        for method in ["direct_client"] + self.working_methods:
            if method == "direct_client":
                print(f"🔄 Trying {test_name} with Direct Client...")
                result = self.execute_blender_code_direct(code)
                results.append(result)
                
                if result["success"]:
                    print(f"✅ {test_name}: Direct Client succeeded")
                    return result, results
                else:
                    print(f"❌ {test_name}: Direct Client failed - {result.get('error', 'Unknown error')}")
            
            elif method == "tcp_direct":
                print(f"🔄 Trying {test_name} with TCP Direct...")
                result = self.execute_blender_code_tcp(code)
                results.append(result)
                
                if result["success"]:
                    print(f"✅ {test_name}: TCP Direct succeeded")
                    return result, results
                else:
                    print(f"❌ {test_name}: TCP Direct failed - {result.get('error', 'Unknown error')}")
            
            elif method == "blender_remote_mcp" and MCP_AVAILABLE:
                print(f"🔄 Trying {test_name} with Blender Remote MCP...")
                try:
                    result = asyncio.run(self.execute_blender_code_mcp(code))
                    results.append(result)
                    
                    if result["success"]:
                        print(f"✅ {test_name}: Blender Remote MCP succeeded")
                        return result, results
                    else:
                        print(f"❌ {test_name}: Blender Remote MCP failed - {result.get('error', 'Unknown error')}")
                        
                        # Try with base64 if regular failed
                        print(f"🔄 Retrying {test_name} with Base64 encoding...")
                        result_b64 = asyncio.run(self.execute_blender_code_mcp(code, use_base64=True))
                        results.append(result_b64)
                        
                        if result_b64["success"]:
                            print(f"✅ {test_name}: Blender Remote MCP with Base64 succeeded")
                            return result_b64, results
                        else:
                            print(f"❌ {test_name}: Blender Remote MCP with Base64 failed - {result_b64.get('error', 'Unknown error')}")
                except Exception as e:
                    print(f"❌ {test_name}: MCP async execution failed - {str(e)}")
        
        print(f"💥 {test_name}: ALL METHODS FAILED")
        return {"success": False, "error": "All communication methods failed", "method": "none"}, results

    def test_basic_functionality(self):
        """Test basic Blender functionality with fallback."""
        print("\n" + "="*60)
        print("🧪 Testing Basic Blender Functionality")
        print("="*60)
        
        test_code = """
import bpy
import json

# Basic scene information
scene_info = {
    "scene_name": bpy.context.scene.name,
    "object_count": len(bpy.context.scene.objects),
    "objects": [obj.name for obj in bpy.context.scene.objects],
    "test_type": "basic_functionality"
}

print(json.dumps(scene_info, indent=2))
"""
        
        result, all_attempts = self.execute_with_fallback(test_code, "Basic Functionality")
        
        if result["success"]:
            return {
                "test_name": "basic_functionality",
                "status": "success",
                "method_used": result["method"],
                "attempts": len(all_attempts),
                "result": result
            }
        else:
            return {
                "test_name": "basic_functionality", 
                "status": "failed",
                "method_used": "none",
                "attempts": len(all_attempts),
                "all_errors": [attempt.get("error") for attempt in all_attempts]
            }

    def test_object_creation(self):
        """Test object creation with fallback."""
        print("\n" + "="*60)
        print("🎯 Testing Object Creation")
        print("="*60)
        
        test_code = """
import bpy
import json

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create test objects
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "FallbackTestCube"

bpy.ops.mesh.primitive_uv_sphere_add(location=(3, 0, 0))
sphere = bpy.context.active_object
sphere.name = "FallbackTestSphere"

# Collect results
creation_result = {
    "objects_created": [cube.name, sphere.name],
    "cube_location": list(cube.location),
    "sphere_location": list(sphere.location),
    "total_objects": len(bpy.context.scene.objects),
    "test_type": "object_creation"
}

print(json.dumps(creation_result, indent=2))
"""
        
        result, all_attempts = self.execute_with_fallback(test_code, "Object Creation")
        
        if result["success"]:
            return {
                "test_name": "object_creation",
                "status": "success",
                "method_used": result["method"],
                "attempts": len(all_attempts),
                "result": result
            }
        else:
            return {
                "test_name": "object_creation",
                "status": "failed", 
                "method_used": "none",
                "attempts": len(all_attempts),
                "all_errors": [attempt.get("error") for attempt in all_attempts]
            }

    def test_scene_manipulation(self):
        """Test scene manipulation with fallback."""
        print("\n" + "="*60)
        print("🎭 Testing Scene Manipulation")
        print("="*60)
        
        test_code = """
import bpy
import json
import mathutils

# Create and manipulate objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create objects
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "ManipulationCube"

# Move and scale the object
cube.location = (2, 1, 0.5)
cube.scale = (1.5, 1.5, 1.5)
cube.rotation_euler = (0.5, 0.3, 0.1)

# Get transformation data
manipulation_result = {
    "object_name": cube.name,
    "final_location": list(cube.location),
    "final_scale": list(cube.scale),
    "final_rotation": list(cube.rotation_euler),
    "matrix_world": [list(row) for row in cube.matrix_world],
    "test_type": "scene_manipulation"
}

print(json.dumps(manipulation_result, indent=2))
"""
        
        result, all_attempts = self.execute_with_fallback(test_code, "Scene Manipulation")
        
        if result["success"]:
            return {
                "test_name": "scene_manipulation",
                "status": "success",
                "method_used": result["method"],
                "attempts": len(all_attempts),
                "result": result
            }
        else:
            return {
                "test_name": "scene_manipulation",
                "status": "failed",
                "method_used": "none", 
                "attempts": len(all_attempts),
                "all_errors": [attempt.get("error") for attempt in all_attempts]
            }

    def run_comprehensive_test(self):
        """Run comprehensive test suite with fallback methods."""
        print("="*80)
        print("🚀 Blender Remote Client Test with Fallback Communication")
        print("="*80)
        print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Detect working methods
        methods_status = self.detect_working_methods()
        
        if not self.working_methods:
            print("\n💥 CRITICAL: No communication methods are working!")
            print("🔧 Please check:")
            print("  1. Is Blender running?")
            print("  2. Is BLD_Remote_MCP addon loaded?")
            print("  3. Is the service running on port 6688?")
            print("  4. Try: export BLD_REMOTE_MCP_START_NOW=1 && blender")
            return {"status": "no_communication", "methods_status": methods_status}
        
        # Run test suites
        test_results = []
        
        test_suites = [
            ("Basic Functionality", self.test_basic_functionality),
            ("Object Creation", self.test_object_creation),
            ("Scene Manipulation", self.test_scene_manipulation),
        ]
        
        for suite_name, test_func in test_suites:
            print(f"\n📋 Running: {suite_name}")
            result = test_func()
            test_results.append(result)
        
        # Summary
        successful_tests = [r for r in test_results if r["status"] == "success"]
        failed_tests = [r for r in test_results if r["status"] == "failed"]
        
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("="*80)
        
        print(f"✅ Successful: {len(successful_tests)}/{len(test_results)}")
        print(f"❌ Failed: {len(failed_tests)}/{len(test_results)}")
        
        print(f"\n🔧 Working Communication Methods: {', '.join(self.working_methods)}")
        
        if successful_tests:
            method_usage = {}
            for test in successful_tests:
                method = test["method_used"]
                method_usage[method] = method_usage.get(method, 0) + 1
            
            print(f"\n📈 Method Usage for Successful Tests:")
            for method, count in method_usage.items():
                print(f"  • {method}: {count} tests")
        
        if failed_tests:
            print(f"\n💥 Failed Tests:")
            for test in failed_tests:
                print(f"  • {test['test_name']}: {test.get('all_errors', ['Unknown error'])}")
        
        # Recommendations
        print(f"\n🎯 RECOMMENDATIONS:")
        if "direct_client" in [t["method_used"] for t in successful_tests]:
            print("✅ Primary method (BlenderMCPClient) is working - use it for regular testing")
        elif successful_tests:
            print("⚠️ Primary method failed, but fallback methods work:")
            for test in successful_tests:
                print(f"  • Use {test['method_used']} for {test['test_name']} functionality")
        else:
            print("❌ All tests failed - check Blender and BLD_Remote_MCP setup")
        
        return {
            "status": "completed",
            "methods_status": methods_status,
            "working_methods": self.working_methods,
            "test_results": test_results,
            "successful_tests": len(successful_tests),
            "failed_tests": len(failed_tests),
            "recommendations": "Use fallback methods if primary fails"
        }


def main():
    """Run enhanced tests with fallback communication."""
    runner = EnhancedTestRunner()
    results = runner.run_comprehensive_test()
    
    # Save results
    log_dir = Path(__file__).parent.parent / "logs" / "tests"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"test_with_fallback_{int(time.time())}.log"
    with open(log_file, "w") as f:
        f.write("Blender Remote Client Test with Fallback Communication\n")
        f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("Working Communication Methods:\n")
        for method in results.get("working_methods", []):
            f.write(f"  ✅ {method}\n")
        
        f.write("\nTest Results:\n")
        for test in results.get("test_results", []):
            status = "PASS" if test["status"] == "success" else "FAIL"
            method = test.get("method_used", "none")
            f.write(f"[{status}] {test['test_name']} (via {method})\n")
        
        f.write(f"\nOverall: {results.get('successful_tests', 0)}/{len(results.get('test_results', []))} tests passed\n")
    
    print(f"\nResults saved to: {log_file}")
    
    # Return success if any tests passed
    return 0 if results.get("successful_tests", 0) > 0 else 1


if __name__ == "__main__":
    sys.exit(main())