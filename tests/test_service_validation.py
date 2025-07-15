#!/usr/bin/env python3
"""
Service Validation Test - TCP Service Availability Check
Goal: Ensure BLD_Remote_MCP service is running and responding on port 6688
"""

import socket
import json
import time
import sys

def validate_bld_remote_mcp(host='127.0.0.1', port=6688):
    """Validate BLD_Remote_MCP TCP service is responding"""
    print(f"[SEARCH] Testing BLD_Remote_MCP service at {host}:{port}")
    
    try:
        # Test basic connectivity
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # 10 second timeout
        
        print(f"[CONNECT] Connecting to {host}:{port}...")
        sock.connect((host, port))
        print("[PASS] TCP connection established")
        
        # Test basic communication
        command = {"message": "validation", "code": "print('BLD_Remote_MCP Service Validation Test OK')"}
        message = json.dumps(command)
        
        print(f"[SEND] Sending validation command...")
        sock.sendall(message.encode('utf-8'))
        print("[PASS] Command sent successfully")
        
        # Receive response
        print("[RECEIVE] Waiting for response...")
        response_data = sock.recv(4096)
        response = json.loads(response_data.decode('utf-8'))
        print("[PASS] Response received successfully")
        
        sock.close()
        
        result = {
            "status": "available",
            "host": host,
            "port": port,
            "response": response,
            "test_time": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        print(f"[SUCCESS] Service validation successful!")
        print(f"[INFO] Response details: {response}")
        return result
        
    except socket.timeout:
        error_msg = f"Connection timeout to {host}:{port}"
        print(f"[FAIL] {error_msg}")
        return {"status": "timeout", "error": error_msg, "host": host, "port": port}
        
    except ConnectionRefusedError:
        error_msg = f"Connection refused by {host}:{port} - service not running"
        print(f"[FAIL] {error_msg}")
        return {"status": "connection_refused", "error": error_msg, "host": host, "port": port}
        
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON response: {str(e)}"
        print(f"[FAIL] {error_msg}")
        return {"status": "invalid_response", "error": error_msg, "host": host, "port": port}
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"[FAIL] {error_msg}")
        return {"status": "error", "error": error_msg, "host": host, "port": port}

def test_service_health():
    """Extended service health check"""
    print("\n[HEALTH] Extended Service Health Check")
    
    # Test multiple rapid connections
    success_count = 0
    total_tests = 3
    
    for i in range(total_tests):
        print(f"\n[INFO] Health check {i+1}/{total_tests}")
        result = validate_bld_remote_mcp()
        if result["status"] == "available":
            success_count += 1
            time.sleep(1)  # Brief pause between tests
        else:
            print(f"[FAIL] Health check {i+1} failed")
            break
    
    health_result = {
        "success_rate": f"{success_count}/{total_tests}",
        "health_status": "healthy" if success_count == total_tests else "unhealthy"
    }
    
    print(f"\n[HEALTH] Health Check Result: {health_result['health_status']}")
    print(f"[STATS] Success Rate: {health_result['success_rate']}")
    
    return health_result

if __name__ == "__main__":
    print("=" * 60)
    print("[TEST] BLD_Remote_MCP Service Validation Test")
    print("=" * 60)
    
    # Basic service validation
    validation_result = validate_bld_remote_mcp()
    
    if validation_result["status"] == "available":
        # Extended health check
        health_result = test_service_health()
        
        # Final result
        final_result = {
            "service_validation": validation_result,
            "health_check": health_result,
            "overall_status": "PASS" if health_result["health_status"] == "healthy" else "FAIL"
        }
        
        print("\n" + "=" * 60)
        print(f"[RESULT] OVERALL TEST RESULT: {final_result['overall_status']}")
        print("=" * 60)
        
        # Save results to log file
        log_file = "context/logs/tests/service-validation.log"
        try:
            with open(log_file, "w") as f:
                json.dump(final_result, f, indent=2)
            print(f"[LOG] Results saved to: {log_file}")
        except Exception as e:
            print(f"[WARNING] Could not save results: {e}")
        
        # Exit with appropriate code
        sys.exit(0 if final_result["overall_status"] == "PASS" else 1)
    else:
        print(f"\n[FAIL] Service validation failed: {validation_result}")
        print("[TIP] Make sure Blender is running with: export BLD_REMOTE_MCP_START_NOW=1 && blender")
        sys.exit(1)