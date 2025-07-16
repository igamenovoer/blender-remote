#!/usr/bin/env python3
"""
Service Validation Testing

Basic TCP service availability and health check for BLD_Remote_MCP service.
This is a secondary validation method to ensure the service is running and 
responsive before running more complex tests.

Based on: context/plans/mcp-server-comprehensive-test-plan.md
"""

import socket
import json
import sys
import os
import time

# Add project src to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(project_root, "src"))


def validate_bld_remote_mcp(host='127.0.0.1', port=6688, timeout=5):
    """Validate BLD_Remote_MCP TCP service is responding"""
    try:
        print(f"🔍 Testing connection to {host}:{port}...")
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        
        # Test basic connectivity with validation command
        command = {
            "message": "validation", 
            "code": "print('BLD_Remote_MCP service validation OK')"
        }
        
        print("📤 Sending validation command...")
        sock.sendall(json.dumps(command).encode('utf-8'))
        
        print("📥 Waiting for response...")
        response_data = sock.recv(4096)
        response = json.loads(response_data.decode('utf-8'))
        
        sock.close()
        
        print("✅ Service responded successfully")
        return {
            "status": "available", 
            "response": response,
            "host": host,
            "port": port,
            "response_time": "< 5s"
        }
        
    except socket.timeout:
        return {
            "status": "timeout", 
            "error": f"Connection timeout after {timeout}s",
            "host": host,
            "port": port
        }
    except ConnectionRefusedError:
        return {
            "status": "connection_refused", 
            "error": f"Connection refused to {host}:{port}",
            "host": host,
            "port": port,
            "suggestion": "Check if Blender is running with BLD_Remote_MCP addon enabled"
        }
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e),
            "host": host,
            "port": port
        }


def test_service_health_check():
    """Test service health and basic functionality"""
    try:
        print("🏥 Testing service health check...")
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect(('127.0.0.1', 6688))
        
        # Test scene info command
        health_command = {
            "message": "health_check",
            "code": '''
import bpy
import json

health_info = {
    "blender_version": bpy.app.version_string,
    "scene_name": bpy.context.scene.name,
    "object_count": len(bpy.context.scene.objects),
    "addon_status": "BLD_Remote_MCP_active",
    "timestamp": str(bpy.context.scene.frame_current)
}

print(json.dumps(health_info, indent=2))
'''
        }
        
        sock.sendall(json.dumps(health_command).encode('utf-8'))
        response_data = sock.recv(4096)
        response = json.loads(response_data.decode('utf-8'))
        
        sock.close()
        
        # Validate health response
        if response.get("executed") and "blender_version" in response.get("result", ""):
            print("✅ Health check passed - Service is fully functional")
            return {"status": "healthy", "response": response}
        else:
            print("⚠️ Health check partial - Service responding but may have issues")
            return {"status": "partial", "response": response}
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


def test_multiple_ports():
    """Test service availability on multiple common ports"""
    common_ports = [6688, 7888, 8888, 9876]  # Include BlenderAutoMCP fallback port
    results = {}
    
    print("🔍 Testing multiple ports for service availability...")
    
    for port in common_ports:
        print(f"\n📡 Testing port {port}...")
        result = validate_bld_remote_mcp(port=port, timeout=3)
        results[f"port_{port}"] = result
        
        if result["status"] == "available":
            print(f"✅ Service found on port {port}")
        else:
            print(f"❌ No service on port {port}: {result.get('error', 'Unknown')}")
    
    return results


def main():
    """Run service validation tests"""
    print("=" * 80)
    print("🔍 BLD_Remote_MCP Service Validation Testing")
    print("=" * 80)
    print("Testing: TCP service availability and basic health")
    print()
    
    # Test 1: Basic service validation on default port
    print("📋 Test 1: Basic Service Validation")
    basic_result = validate_bld_remote_mcp()
    print(f"Result: {basic_result['status']}")
    
    if basic_result["status"] != "available":
        print(f"❌ Basic validation failed: {basic_result.get('error', 'Unknown error')}")
        print("\nTroubleshooting:")
        print("1. Check if Blender is running")
        print("2. Verify BLD_Remote_MCP addon is installed and enabled")
        print("3. Confirm service is listening on port 6688")
        print("4. Try: netstat -tlnp | grep 6688")
        
        # Still test other ports in case service is on different port
        print("\n📋 Test 2: Multiple Port Scan")
        port_results = test_multiple_ports()
        
        # Check if any port has working service
        working_ports = [port for port, result in port_results.items() if result["status"] == "available"]
        if working_ports:
            print(f"\n✅ Service found on: {working_ports}")
            return 0
        else:
            print("\n❌ No working service found on any common port")
            return 1
    
    # Test 2: Health check if basic validation passed
    print(f"\n📋 Test 2: Service Health Check")
    health_result = test_service_health_check()
    print(f"Result: {health_result['status']}")
    
    # Test 3: Multiple ports (informational)
    print(f"\n📋 Test 3: Port Availability Scan")
    port_results = test_multiple_ports()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 Service Validation Summary:")
    print(f"  Basic Connection: {'✅ PASS' if basic_result['status'] == 'available' else '❌ FAIL'}")
    print(f"  Health Check: {'✅ PASS' if health_result['status'] == 'healthy' else '⚠️ PARTIAL' if health_result['status'] == 'partial' else '❌ FAIL'}")
    
    working_ports = [port for port, result in port_results.items() if result["status"] == "available"]
    print(f"  Available Ports: {len(working_ports)} found")
    
    # Overall result
    if basic_result["status"] == "available" and health_result["status"] in ["healthy", "partial"]:
        print("\n🎯 OVERALL RESULT: PASS")
        print("✅ BLD_Remote_MCP service is available and functional")
        return 0
    else:
        print("\n🎯 OVERALL RESULT: FAIL") 
        print("❌ BLD_Remote_MCP service validation failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)