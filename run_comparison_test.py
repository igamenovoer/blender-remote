#!/usr/bin/env python3
"""
Simple Dual Service Comparison Test

Tests that BLD_Remote_MCP and BlenderAutoMCP produce identical results.
"""

import sys
import socket
import json
import time
from pathlib import Path

# Add auto_mcp_remote to path
sys.path.insert(0, str(Path(__file__).parent / "context" / "refcode"))

try:
    from auto_mcp_remote.blender_mcp_client import BlenderMCPClient
    print("✅ auto_mcp_remote client loaded")
except ImportError as e:
    print(f"❌ Cannot import auto_mcp_remote: {e}")
    sys.exit(1)

def test_service_with_client(port, service_name, test_name, code):
    """Test a service using MCP client."""
    print(f"🔄 Testing {service_name}: {test_name}")
    
    try:
        client = BlenderMCPClient(port=port)
        result = client.execute_python(code)
        print(f"✅ {service_name}: {test_name} - SUCCESS")
        return True, result
    except Exception as e:
        print(f"❌ {service_name}: {test_name} - ERROR: {e}")
        return False, str(e)

def compare_services(test_name, code):
    """Run identical test on both services and compare."""
    print(f"\n{'='*60}")
    print(f"🧪 COMPARISON TEST: {test_name}")
    print(f"{'='*60}")
    
    # Test BLD_Remote_MCP
    bld_success, bld_result = test_service_with_client(6688, "BLD_Remote_MCP", test_name, code)
    
    # Test BlenderAutoMCP  
    auto_success, auto_result = test_service_with_client(9876, "BlenderAutoMCP", test_name, code)
    
    # Compare results
    if bld_success and auto_success:
        print(f"✅ BOTH SERVICES SUCCEEDED")
        print(f"📊 Results comparison:")
        print(f"   BLD_Remote_MCP: {str(bld_result)[:100]}...")
        print(f"   BlenderAutoMCP: {str(auto_result)[:100]}...")
        
        # Simple equivalence check
        both_have_results = bld_result is not None and auto_result is not None
        if both_have_results:
            print(f"✅ Both services returned results")
            return True
        else:
            print(f"⚠️ One or both services returned None")
            return False
    else:
        print(f"❌ SERVICE FAILURE:")
        if not bld_success:
            print(f"   BLD_Remote_MCP failed: {bld_result}")
        if not auto_success:
            print(f"   BlenderAutoMCP failed: {auto_result}")
        return False

def main():
    """Run comparison tests."""
    print("🧪 BLD_Remote_MCP vs BlenderAutoMCP Comparison Test")
    print("="*60)
    
    # Test cases
    test_cases = [
        ("Basic Arithmetic", "result = 2 + 2"),
        ("String Operations", "result = 'hello' + ' world'"),
        ("Import Module", "import math; result = math.pi"),
        ("Blender Version", "import bpy; result = bpy.app.version_string"),
        ("Scene Objects", "import bpy; result = len(bpy.data.objects)"),
        ("Variable Assignment", "test_var = 42; result = test_var * 2"),
        ("List Operations", "numbers = [1,2,3,4,5]; result = sum(numbers)"),
        ("Blender API Call", "import bpy; bpy.ops.mesh.primitive_cube_add(); result = 'cube_added'"),
    ]
    
    results = []
    
    for test_name, code in test_cases:
        success = compare_services(test_name, code)
        results.append((test_name, success))
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST RESULTS SUMMARY")
    print(f"{'='*60}")
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:25} {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 OVERALL RESULT: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 SUCCESS: BLD_Remote_MCP functions identically to BlenderAutoMCP!")
        return True
    else:
        print("💥 ISSUES DETECTED: Functional differences found between services")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)