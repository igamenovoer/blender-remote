#!/usr/bin/env python3
"""
Basic Connection Example

This example demonstrates the fundamental connection and communication
with the BLD Remote MCP background service.

Prerequisites:
- BLD Remote MCP service running (use start_service.py)
- Default port 6688 or specify different port

Usage:
    python3 01_basic_connection.py
    python3 01_basic_connection.py --port 9999
"""

import sys
import os
import argparse

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import BldRemoteClient, blender_connection, check_service_health, print_status

def basic_connection_test(port: int = 6688):
    """
    Test basic connection and messaging functionality.
    
    Args:
        port: Service port number
    """
    print(f"🔗 Testing basic connection to BLD Remote MCP service on port {port}")
    print("=" * 60)
    
    # 1. Check service health first
    print("1. Checking service health...")
    health = check_service_health(port=port)
    print_status(health)
    
    if not health["responsive"]:
        print("\\n❌ Service is not available. Please start the service first:")
        print(f"   python3 start_service.py --port {port}")
        return False
    
    print("\\n2. Testing basic messaging...")
    
    try:
        # Method 1: Using context manager (recommended)
        with blender_connection(port=port) as client:
            print("   ✓ Connected successfully using context manager")
            
            # Send a simple message
            response = client.send_message("Hello from basic connection test!")
            print(f"   📨 Message response: {response}")
            
            # Validate response
            if response.get("response") == "OK":
                print("   ✓ Message sent successfully")
            else:
                print(f"   ❌ Unexpected response: {response}")
        
        print("   ✓ Connection closed cleanly")
        
    except Exception as e:
        print(f"   ❌ Connection test failed: {e}")
        return False
    
    print("\\n3. Testing manual connection management...")
    
    try:
        # Method 2: Manual connection management
        client = BldRemoteClient(port=port)
        client.connect()
        print("   ✓ Manual connection established")
        
        # Send another message
        response = client.send_message("Hello from manual connection!")
        print(f"   📨 Manual response: {response}")
        
        # Clean up
        client.disconnect()
        print("   ✓ Manual connection closed")
        
    except Exception as e:
        print(f"   ❌ Manual connection test failed: {e}")
        return False
    
    print("\\n4. Testing connection parameters...")
    
    try:
        # Test with custom timeout
        with blender_connection(port=port, timeout=5.0) as client:
            response = client.send_message("Testing with 5s timeout")
            print(f"   ⏱️ Timeout test response: {response}")
            print("   ✓ Custom timeout working")
            
    except Exception as e:
        print(f"   ❌ Timeout test failed: {e}")
        return False
    
    print("\\n✅ All basic connection tests passed!")
    return True

def connection_error_handling_demo(port: int = 6688):
    """
    Demonstrate proper error handling for connection issues.
    
    Args:
        port: Service port number
    """
    print("\\n🛡️ Testing connection error handling...")
    print("=" * 60)
    
    # Test connection to wrong port
    wrong_port = port + 1000
    print(f"1. Testing connection to wrong port {wrong_port}...")
    
    try:
        with blender_connection(port=wrong_port, timeout=2.0) as client:
            client.send_message("This should fail")
    except ConnectionError as e:
        print(f"   ✓ Correctly caught ConnectionError: {e}")
    except Exception as e:
        print(f"   ❌ Unexpected error type: {type(e).__name__}: {e}")
    
    # Test connection timeout
    print("\\n2. Testing connection timeout (this may take a moment)...")
    
    try:
        client = BldRemoteClient(host="192.0.2.1", port=port, timeout=1.0)  # RFC5737 test IP
        client.connect()
        client.send_message("This should timeout")
    except ConnectionError as e:
        print(f"   ✓ Correctly handled timeout: {e}")
    except Exception as e:
        print(f"   ❌ Unexpected error type: {type(e).__name__}: {e}")
    finally:
        try:
            client.disconnect()
        except:
            pass
    
    print("\\n✅ Error handling tests completed")

def main():
    parser = argparse.ArgumentParser(description='Test basic BLD Remote MCP connection')
    parser.add_argument('--port', type=int, default=6688,
                        help='Service port (default: 6688)')
    parser.add_argument('--skip-errors', action='store_true',
                        help='Skip error handling demonstration')
    
    args = parser.parse_args()
    
    print("BLD Remote MCP - Basic Connection Example")
    print("=" * 50)
    
    # Run basic connection tests
    success = basic_connection_test(args.port)
    
    if success and not args.skip_errors:
        # Run error handling demo
        connection_error_handling_demo(args.port)
    
    if success:
        print("\\n🎉 Basic connection example completed successfully!")
        print("\\nNext steps:")
        print("  • Try: python3 02_code_execution.py")
        print("  • Try: python3 03_scene_manipulation.py")
    else:
        print("\\n❌ Basic connection tests failed")
        print("\\nTroubleshooting:")
        print(f"  • Ensure service is running: python3 start_service.py --port {args.port}")
        print("  • Check for port conflicts with: netstat -tlnp | grep", args.port)
        print("  • Verify Blender addon is installed and enabled")
        
        sys.exit(1)

if __name__ == '__main__':
    main()