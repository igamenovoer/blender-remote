#!/usr/bin/env python3
"""
Simplified Synchronous Execution Test
Goal: Test synchronous execution with smaller code blocks to isolate issues
"""

import asyncio
import json
import sys
import time
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class SimplifiedBlenderTests:
    def __init__(self):
        self.server_params = StdioServerParameters(
            command="pixi",
            args=["run", "python", "src/blender_remote/mcp_server.py"],
            env=None,
        )
    
    async def test_simple_object_creation(self):
        """Test: Simple object creation and data extraction"""
        
        print("🎲 Testing Simple Object Creation")
        
        # Simplified code - no triple quotes to avoid JSON issues
        code = "import bpy; import json; bpy.ops.mesh.primitive_cube_add(location=(1, 2, 3)); cube = bpy.context.active_object; result = {'name': cube.name, 'location': list(cube.location), 'type': cube.type}; print(json.dumps(result))"
        
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool("execute_code", {"code": code})
                
                if result.content and result.content[0].type == 'text':
                    content = result.content[0].text
                    print(f"  📋 Raw response: {content[:200]}...")
                    
                    # Look for JSON in the response
                    try:
                        lines = content.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line.startswith('{') and line.endswith('}'):
                                parsed_result = json.loads(line)
                                print(f"  ✅ Object created: {parsed_result.get('name', 'Unknown')}")
                                print(f"  ✅ Location: {parsed_result.get('location', [0,0,0])}")
                                print(f"  ✅ Type: {parsed_result.get('type', 'Unknown')}")
                                
                                return {
                                    "status": "success",
                                    "test_name": "simple_object_creation",
                                    "structured_data": parsed_result
                                }
                        
                        # If no JSON found, check if execution was successful
                        if "executed successfully" in content.lower():
                            return {
                                "status": "success_no_json",
                                "test_name": "simple_object_creation",
                                "message": "Code executed but no JSON data found",
                                "raw_content": content
                            }
                        else:
                            return {
                                "status": "execution_failed",
                                "test_name": "simple_object_creation",
                                "raw_content": content
                            }
                            
                    except json.JSONDecodeError as e:
                        print(f"  ❌ JSON parse error: {e}")
                        return {"status": "json_parse_error", "error": str(e), "raw_content": content}
                
                return {"status": "no_content", "result": result}

    async def test_simple_scene_query(self):
        """Test: Simple scene information query"""
        
        print("🏠 Testing Simple Scene Query")
        
        code = "import bpy; import json; objects = [{'name': obj.name, 'type': obj.type} for obj in bpy.context.scene.objects]; result = {'scene_name': bpy.context.scene.name, 'object_count': len(objects), 'objects': objects}; print(json.dumps(result))"
        
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool("execute_code", {"code": code})
                
                if result.content and result.content[0].type == 'text':
                    content = result.content[0].text
                    print(f"  📋 Raw response: {content[:200]}...")
                    
                    try:
                        lines = content.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line.startswith('{') and line.endswith('}'):
                                parsed_result = json.loads(line)
                                print(f"  ✅ Scene: {parsed_result.get('scene_name', 'Unknown')}")
                                print(f"  ✅ Object count: {parsed_result.get('object_count', 0)}")
                                
                                return {
                                    "status": "success",
                                    "test_name": "simple_scene_query",
                                    "structured_data": parsed_result
                                }
                        
                        return {
                            "status": "success_no_json",
                            "test_name": "simple_scene_query",
                            "message": "Code executed but no JSON data found",
                            "raw_content": content
                        }
                            
                    except json.JSONDecodeError as e:
                        print(f"  ❌ JSON parse error: {e}")
                        return {"status": "json_parse_error", "error": str(e), "raw_content": content}
                
                return {"status": "no_content", "result": result}

    async def test_simple_calculation(self):
        """Test: Simple mathematical calculation"""
        
        print("🧮 Testing Simple Calculation")
        
        code = "import json; import math; result = {'pi': math.pi, 'sqrt_2': math.sqrt(2), 'calculation': 5 * 7 + 3}; print(json.dumps(result))"
        
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool("execute_code", {"code": code})
                
                if result.content and result.content[0].type == 'text':
                    content = result.content[0].text
                    print(f"  📋 Raw response: {content[:200]}...")
                    
                    try:
                        lines = content.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line.startswith('{') and line.endswith('}'):
                                parsed_result = json.loads(line)
                                print(f"  ✅ Pi: {parsed_result.get('pi', 0)}")
                                print(f"  ✅ Sqrt(2): {parsed_result.get('sqrt_2', 0)}")
                                print(f"  ✅ Calculation: {parsed_result.get('calculation', 0)}")
                                
                                return {
                                    "status": "success",
                                    "test_name": "simple_calculation",
                                    "structured_data": parsed_result
                                }
                        
                        return {
                            "status": "success_no_json",
                            "test_name": "simple_calculation",
                            "message": "Code executed but no JSON data found",
                            "raw_content": content
                        }
                            
                    except json.JSONDecodeError as e:
                        print(f"  ❌ JSON parse error: {e}")
                        return {"status": "json_parse_error", "error": str(e), "raw_content": content}
                
                return {"status": "no_content", "result": result}

    async def run_all_tests(self):
        """Run all simplified synchronous execution tests"""
        print("=" * 80)
        print("🔬 Testing Simplified Synchronous Execution")
        print("=" * 80)
        
        tests = [
            ("Simple Calculation", self.test_simple_calculation),
            ("Simple Scene Query", self.test_simple_scene_query),
            ("Simple Object Creation", self.test_simple_object_creation)
        ]
        
        results = {}
        overall_success = True
        
        for test_name, test_func in tests:
            print(f"\n📋 Running: {test_name}")
            try:
                result = await test_func()
                results[test_name] = result
                
                if result["status"] == "success":
                    print(f"✅ {test_name}: PASSED")
                    
                    # Validate that we got structured data
                    if "structured_data" in result and result["structured_data"]:
                        print(f"  📊 Structured data received: {type(result['structured_data']).__name__}")
                    else:
                        print(f"  ⚠️ No structured data in response")
                        overall_success = False
                elif result["status"] == "success_no_json":
                    print(f"⚠️ {test_name}: PARTIAL - Code executed but no JSON data")
                    overall_success = False
                else:
                    print(f"❌ {test_name}: FAILED - {result.get('error', 'Unknown error')}")
                    overall_success = False
                    
            except Exception as e:
                results[test_name] = {"status": "exception", "error": str(e)}
                print(f"❌ {test_name}: EXCEPTION - {e}")
                overall_success = False
        
        # Summary
        passed_tests = sum(1 for result in results.values() if result.get("status") == "success")
        total_tests = len(tests)
        
        final_result = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_type": "Simplified Synchronous Execution",
            "individual_results": results,
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": f"{passed_tests}/{total_tests}",
                "overall_status": "PASS" if overall_success else "FAIL"
            }
        }
        
        print("\n" + "=" * 80)
        print("📊 Simplified Synchronous Execution Test Results:")
        for test_name, result in results.items():
            status = "✅ PASS" if result.get("status") == "success" else "❌ FAIL"
            print(f"  {status} {test_name}")
        
        print(f"\n🎯 OVERALL RESULT: {final_result['summary']['overall_status']}")
        print(f"📊 Success Rate: {final_result['summary']['success_rate']}")
        print("=" * 80)
        
        return final_result

async def main():
    tester = SimplifiedBlenderTests()
    results = await tester.run_all_tests()
    
    # Save results to log file
    log_file = "context/logs/tests/synchronous-execution-simple.log"
    try:
        with open(log_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"📝 Results saved to: {log_file}")
    except Exception as e:
        print(f"⚠️ Could not save results: {e}")
    
    # Exit with appropriate code
    sys.exit(0 if results["summary"]["overall_status"] == "PASS" else 1)

if __name__ == "__main__":
    results = asyncio.run(main())