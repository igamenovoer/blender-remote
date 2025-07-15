#!/usr/bin/env python3
"""
Test Base64 Backward Compatibility and Basic Functionality
Goal: Verify base64 encoding works and doesn't break existing functionality
"""

import asyncio
import json
import sys
import time
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class Base64CompatibilityTests:
    def __init__(self):
        self.server_params = StdioServerParameters(
            command="pixi",
            args=["run", "python", "src/blender_remote/mcp_server.py"],
            env=None,
        )
    
    async def test_backward_compatibility(self):
        """Test: Ensure old execute_code calls still work"""
        
        print("[LOG] Testing Backward Compatibility (No Base64 Parameters)")
        
        simple_code = '''
import bpy
import json

# Simple test
result = {
    "test": "backward_compatibility",
    "scene_name": bpy.context.scene.name,
    "object_count": len(bpy.context.scene.objects)
}

print(json.dumps(result))
'''
        
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Test old style call (no base64 parameters)
                result = await session.call_tool("execute_code", {
                    "code": simple_code
                })
                
                if result.content and result.content[0].type == 'text':
                    content = result.content[0].text
                    
                    try:
                        response_data = json.loads(content)
                        
                        if response_data.get("executed", False):
                            output = response_data.get("result", "")
                            if "backward_compatibility" in output:
                                print(f"  [PASS] Backward compatibility maintained")
                                return {
                                    "status": "success",
                                    "test_name": "backward_compatibility",
                                    "base64_used": False,
                                    "execution_successful": True
                                }
                            else:
                                print(f"  [WARNING] Execution result unclear")
                                return {
                                    "status": "unclear_result", 
                                    "raw_output": output,
                                    "base64_used": False
                                }
                        else:
                            print(f"  [FAIL] Backward compatibility broken")
                            return {
                                "status": "execution_failed",
                                "response_data": response_data,
                                "base64_used": False
                            }
                    except json.JSONDecodeError as e:
                        print(f"  [FAIL] JSON parse error: {e}")
                        return {"status": "json_error", "error": str(e), "base64_used": False}
                
                return {"status": "no_content", "base64_used": False}

    async def test_simple_base64_encoding(self):
        """Test: Simple base64 code encoding"""
        
        print("[ENCODE] Testing Simple Base64 Code Encoding")
        
        simple_code = '''
import bpy
import json

result = {
    "test": "simple_base64",
    "encoded": True,
    "message": "Base64 encoding works!"
}

print(json.dumps(result))
'''
        
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Test with base64 encoding for code
                result = await session.call_tool("execute_code", {
                    "code": simple_code,
                    "send_as_base64": True
                })
                
                if result.content and result.content[0].type == 'text':
                    content = result.content[0].text
                    
                    try:
                        response_data = json.loads(content)
                        
                        if response_data.get("executed", False):
                            output = response_data.get("result", "")
                            if "simple_base64" in output:
                                print(f"  [PASS] Base64 code encoding works")
                                return {
                                    "status": "success",
                                    "test_name": "simple_base64_encoding",
                                    "base64_used": True,
                                    "execution_successful": True
                                }
                            else:
                                print(f"  [WARNING] Base64 execution result unclear")
                                return {
                                    "status": "unclear_result",
                                    "raw_output": output,
                                    "base64_used": True
                                }
                        else:
                            print(f"  [FAIL] Base64 code encoding failed")
                            return {
                                "status": "execution_failed",
                                "response_data": response_data,
                                "base64_used": True
                            }
                    except json.JSONDecodeError as e:
                        print(f"  [FAIL] JSON parse error: {e}")
                        return {"status": "json_error", "error": str(e), "base64_used": True}
                
                return {"status": "no_content", "base64_used": True}

    async def test_base64_result_encoding(self):
        """Test: Base64 result encoding"""
        
        print("[SEND] Testing Base64 Result Encoding")
        
        simple_code = '''
import json

result = {
    "test": "base64_result",
    "large_text": "This is a longer text that will be base64 encoded in the result. " * 10,
    "numbers": list(range(100)),
    "nested": {"deep": {"data": "structure"}}
}

print(json.dumps(result))
'''
        
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Test with base64 result encoding
                result = await session.call_tool("execute_code", {
                    "code": simple_code,
                    "return_as_base64": True
                })
                
                if result.content and result.content[0].type == 'text':
                    content = result.content[0].text
                    
                    try:
                        response_data = json.loads(content)
                        
                        if response_data.get("executed", False):
                            output = response_data.get("result", "")
                            if "base64_result" in output and len(output) > 100:
                                print(f"  [PASS] Base64 result encoding works")
                                return {
                                    "status": "success",
                                    "test_name": "base64_result_encoding",
                                    "base64_used": True,
                                    "result_length": len(output),
                                    "execution_successful": True
                                }
                            else:
                                print(f"  [WARNING] Base64 result unclear or too small")
                                return {
                                    "status": "unclear_result",
                                    "raw_output": output,
                                    "base64_used": True
                                }
                        else:
                            print(f"  [FAIL] Base64 result encoding failed")
                            return {
                                "status": "execution_failed",
                                "response_data": response_data,
                                "base64_used": True
                            }
                    except json.JSONDecodeError as e:
                        print(f"  [FAIL] JSON parse error: {e}")
                        return {"status": "json_error", "error": str(e), "base64_used": True}
                
                return {"status": "no_content", "base64_used": True}

    async def test_both_base64_encoding(self):
        """Test: Both code and result base64 encoding"""
        
        print("[ENCODE][SEND] Testing Both Code and Result Base64 Encoding")
        
        code_with_special_chars = '''
import json

# Code with various characters that might cause issues
special_text = "Special chars: \\"quotes\\", 'apostrophes', \\nNewlines\\n, \\tTabs\\t, unicode: αβγ"

result = {
    "test": "both_base64",
    "special_text": special_text,
    "json_string": '{\\"nested\\": \\"json\\"}',
    "multiline": """This is a
multiline
string""",
    "success": True
}

print(json.dumps(result))
'''
        
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Test with both base64 flags enabled
                result = await session.call_tool("execute_code", {
                    "code": code_with_special_chars,
                    "send_as_base64": True,
                    "return_as_base64": True
                })
                
                if result.content and result.content[0].type == 'text':
                    content = result.content[0].text
                    
                    try:
                        response_data = json.loads(content)
                        
                        if response_data.get("executed", False):
                            output = response_data.get("result", "")
                            if "both_base64" in output:
                                print(f"  [PASS] Both base64 encodings work together")
                                return {
                                    "status": "success",
                                    "test_name": "both_base64_encoding",
                                    "base64_used": True,
                                    "both_flags_used": True,
                                    "execution_successful": True
                                }
                            else:
                                print(f"  [WARNING] Both base64 result unclear")
                                return {
                                    "status": "unclear_result",
                                    "raw_output": output,
                                    "base64_used": True
                                }
                        else:
                            print(f"  [FAIL] Both base64 encodings failed")
                            return {
                                "status": "execution_failed",
                                "response_data": response_data,
                                "base64_used": True
                            }
                    except json.JSONDecodeError as e:
                        print(f"  [FAIL] JSON parse error: {e}")
                        return {"status": "json_error", "error": str(e), "base64_used": True}
                
                return {"status": "no_content", "base64_used": True}

    async def run_all_tests(self):
        """Run all base64 compatibility tests"""
        print("=" * 80)
        print("[ENCODE] Testing Base64 Compatibility and Basic Functionality")
        print("=" * 80)
        
        tests = [
            ("Backward Compatibility", self.test_backward_compatibility),
            ("Simple Base64 Code Encoding", self.test_simple_base64_encoding),
            ("Base64 Result Encoding", self.test_base64_result_encoding),
            ("Both Base64 Encodings", self.test_both_base64_encoding)
        ]
        
        results = {}
        overall_success = True
        
        for test_name, test_func in tests:
            print(f"\n[INFO] Running: {test_name}")
            try:
                result = await test_func()
                results[test_name] = result
                
                if result["status"] == "success":
                    print(f"[PASS] {test_name}: PASSED")
                    
                    base64_status = "[ENCODE] Base64" if result.get("base64_used") else "[LOG] Standard"
                    print(f"  [STATS] Method: {base64_status}")
                else:
                    print(f"[FAIL] {test_name}: FAILED - {result.get('error', result.get('status', 'Unknown error'))}")
                    overall_success = False
                    
            except Exception as e:
                results[test_name] = {"status": "exception", "error": str(e)}
                print(f"[FAIL] {test_name}: EXCEPTION - {e}")
                overall_success = False
        
        # Summary
        passed_tests = sum(1 for result in results.values() if result.get("status") == "success")
        total_tests = len(tests)
        
        final_result = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_type": "Base64 Compatibility and Basic Functionality",
            "individual_results": results,
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": f"{passed_tests}/{total_tests}",
                "overall_status": "PASS" if overall_success else "FAIL"
            },
            "compatibility_validation": {
                "backward_compatibility": "[PASS] Maintained" if results.get("Backward Compatibility", {}).get("status") == "success" else "[FAIL] Broken",
                "base64_code_encoding": "[PASS] Working" if results.get("Simple Base64 Code Encoding", {}).get("status") == "success" else "[FAIL] Failed",
                "base64_result_encoding": "[PASS] Working" if results.get("Base64 Result Encoding", {}).get("status") == "success" else "[FAIL] Failed",
                "combined_base64": "[PASS] Working" if results.get("Both Base64 Encodings", {}).get("status") == "success" else "[FAIL] Failed"
            }
        }
        
        print("\n" + "=" * 80)
        print("[STATS] Base64 Compatibility Test Results:")
        for test_name, result in results.items():
            status = "[PASS] PASS" if result.get("status") == "success" else "[FAIL] FAIL"
            method_indicator = "[ENCODE]" if result.get("base64_used") else "[LOG]"
            print(f"  {status} {method_indicator} {test_name}")
        
        print(f"\n[RESULT] OVERALL RESULT: {final_result['summary']['overall_status']}")
        print(f"[STATS] Success Rate: {final_result['summary']['success_rate']}")
        print("\n[ENCODE] Base64 Feature Validation:")
        for key, value in final_result['compatibility_validation'].items():
            print(f"  {value} {key.replace('_', ' ').title()}")
        print("=" * 80)
        
        return final_result

async def main():
    tester = Base64CompatibilityTests()
    results = await tester.run_all_tests()
    
    # Save results to log file
    log_file = "context/logs/tests/base64-compatibility.log"
    try:
        with open(log_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"[LOG] Results saved to: {log_file}")
    except Exception as e:
        print(f"[WARNING] Could not save results: {e}")
    
    # Exit with appropriate code
    sys.exit(0 if results["summary"]["overall_status"] == "PASS" else 1)

if __name__ == "__main__":
    results = asyncio.run(main())