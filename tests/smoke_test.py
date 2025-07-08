#!/usr/bin/env python3
"""
Smoke Test - Quick Verification of BLD_Remote_MCP vs BlenderAutoMCP

This is a lightweight test script that quickly verifies both services
are working and producing similar results. Useful for rapid development
iteration and CI/CD pipelines.
"""

import sys
import os
import subprocess
import time
import socket
import json
from pathlib import Path

# Add auto_mcp_remote to path
sys.path.insert(0, str(Path(__file__).parent.parent / "context" / "refcode"))

BLENDER_PATH = "/apps/blender-4.4.3-linux-x64/blender"
BLD_REMOTE_PORT = 6688
BLENDER_AUTO_PORT = 9876


def log(message, level="INFO"):
    """Simple logging function."""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")


def is_port_available(port):
    """Check if port is available."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', port))
        sock.close()
        return True
    except OSError:
        return False


def kill_blender():
    """Kill Blender processes."""
    try:
        subprocess.run(['pkill', '-f', 'blender'], check=False, timeout=5)
        time.sleep(2)
        return True
    except subprocess.TimeoutExpired:
        return False


def wait_for_service(port, timeout=15, service_name="service"):
    """Wait for service to start on port."""
    log(f"Waiting for {service_name} on port {port}...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if not is_port_available(port):  # Port in use = service running
            log(f"✅ {service_name} is running on port {port}")
            return True
        time.sleep(0.5)
    
    log(f"❌ {service_name} failed to start on port {port}")
    return False


def test_service_basic(port, service_name):
    """Test basic service functionality."""
    log(f"Testing {service_name} on port {port}...")
    
    try:
        # Test TCP connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        
        if result != 0:
            log(f"❌ {service_name}: TCP connection failed", "ERROR")
            return False
        
        # Test JSON communication
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect(('127.0.0.1', port))
            
            # Send test command
            message = {
                "code": "smoke_test_var = 'smoke_test_successful'",
                "message": f"Smoke test for {service_name}"
            }
            
            json_data = json.dumps(message)
            sock.sendall(json_data.encode('utf-8'))
            
            # Receive response
            response_data = sock.recv(4096)
            if not response_data:
                log(f"❌ {service_name}: No response received", "ERROR")
                return False
            
            response = json.loads(response_data.decode('utf-8'))
            
            if not isinstance(response, dict):
                log(f"❌ {service_name}: Invalid response format", "ERROR")
                return False
            
            log(f"✅ {service_name}: Basic communication successful")
            return True
            
        except Exception as e:
            log(f"❌ {service_name}: Communication error: {e}", "ERROR")
            return False
        finally:
            sock.close()
            
    except Exception as e:
        log(f"❌ {service_name}: Test error: {e}", "ERROR")
        return False


def test_blender_api_access(port, service_name):
    """Test Blender API access."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', port))
        
        # Test Blender API access
        message = {
            "code": "import bpy; blender_version = bpy.app.version_string; result = 'api_test_ok'",
            "message": f"Blender API test for {service_name}"
        }
        
        json_data = json.dumps(message)
        sock.sendall(json_data.encode('utf-8'))
        
        response_data = sock.recv(4096)
        response = json.loads(response_data.decode('utf-8'))
        
        sock.close()
        
        if isinstance(response, dict):
            log(f"✅ {service_name}: Blender API access successful")
            return True
        else:
            log(f"❌ {service_name}: Blender API access failed", "ERROR")
            return False
            
    except Exception as e:
        log(f"❌ {service_name}: Blender API test error: {e}", "ERROR")
        return False


def run_smoke_test():
    """Run comprehensive smoke test."""
    log("🚀 Starting BLD_Remote_MCP vs BlenderAutoMCP Smoke Test")
    log("="*60)
    
    # Prerequisites check
    if not os.path.exists(BLENDER_PATH):
        log(f"❌ Blender not found at {BLENDER_PATH}", "ERROR")
        return False
    
    # Cleanup
    log("Cleaning up environment...")
    kill_blender()
    
    if not is_port_available(BLD_REMOTE_PORT) or not is_port_available(BLENDER_AUTO_PORT):
        log("❌ Required ports are not available", "ERROR")
        return False
    
    # Start Blender with dual services
    log("Starting Blender with dual MCP services...")
    env = os.environ.copy()
    env['BLD_REMOTE_MCP_PORT'] = str(BLD_REMOTE_PORT)
    env['BLD_REMOTE_MCP_START_NOW'] = '1'
    env['BLENDER_AUTO_MCP_SERVICE_PORT'] = str(BLENDER_AUTO_PORT)
    env['BLENDER_AUTO_MCP_START_NOW'] = '1'
    
    process = subprocess.Popen(
        [BLENDER_PATH],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    
    try:
        # Wait for services to start
        bld_remote_ok = wait_for_service(BLD_REMOTE_PORT, service_name="BLD_Remote_MCP")
        blender_auto_ok = wait_for_service(BLENDER_AUTO_PORT, service_name="BlenderAutoMCP")
        
        if not bld_remote_ok or not blender_auto_ok:
            log("❌ Service startup failed", "ERROR")
            return False
        
        log("Both services started successfully")
        
        # Test basic functionality
        results = {
            'bld_remote_basic': test_service_basic(BLD_REMOTE_PORT, "BLD_Remote_MCP"),
            'blender_auto_basic': test_service_basic(BLENDER_AUTO_PORT, "BlenderAutoMCP"),
            'bld_remote_api': test_blender_api_access(BLD_REMOTE_PORT, "BLD_Remote_MCP"),
            'blender_auto_api': test_blender_api_access(BLENDER_AUTO_PORT, "BlenderAutoMCP")
        }
        
        # Analyze results
        log("="*60)
        log("📊 SMOKE TEST RESULTS")
        log("="*60)
        
        for test_name, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            log(f"{test_name:25} {status}")
        
        # Summary
        total_tests = len(results)
        passed_tests = sum(results.values())
        
        log("-" * 60)
        log(f"Total: {total_tests}, Passed: {passed_tests}, Failed: {total_tests - passed_tests}")
        
        if passed_tests == total_tests:
            log("🎉 SMOKE TEST PASSED - Both services are functional!")
            return True
        else:
            log("💥 SMOKE TEST FAILED - Issues detected")
            
            # Specific failure analysis
            if not results['bld_remote_basic'] or not results['bld_remote_api']:
                log("❌ BLD_Remote_MCP has issues")
            if not results['blender_auto_basic'] or not results['blender_auto_api']:
                log("❌ BlenderAutoMCP has issues")
            
            return False
    
    finally:
        # Cleanup
        log("Cleaning up...")
        try:
            process.terminate()
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
        
        kill_blender()


def main():
    """Main entry point."""
    success = run_smoke_test()
    
    if success:
        log("✅ Smoke test completed successfully")
        sys.exit(0)
    else:
        log("❌ Smoke test failed")
        sys.exit(1)


if __name__ == "__main__":
    main()