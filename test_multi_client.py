#!/usr/bin/env python3
"""
Test script to verify multi-client blocking functionality
"""

import socket
import json
import time
import threading
import sys

def test_client(client_id, delay=0):
    """Test a single client connection with optional delay"""
    if delay > 0:
        time.sleep(delay)
    
    try:
        print(f"Client {client_id}: Connecting...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', 7777))
        
        # Send a command that takes time to execute
        command = {
            "type": "execute_code",
            "params": {
                "code": f"import time; print('Client {client_id} executing...'); time.sleep(2); print('Client {client_id} done')"
            }
        }
        
        print(f"Client {client_id}: Sending command...")
        sock.sendall(json.dumps(command).encode('utf-8'))
        
        # Receive response
        response = sock.recv(4096)
        result = json.loads(response.decode('utf-8'))
        
        print(f"Client {client_id}: Response: {result}")
        
        sock.close()
        
    except Exception as e:
        print(f"Client {client_id}: Error: {e}")

def test_blocking():
    """Test that clients are blocked when a command is executing"""
    print("Testing multi-client blocking functionality...")
    print("=" * 50)
    
    # First, test that the server is working
    print("1. Testing basic connection...")
    test_client("TEST")
    
    print("\n2. Testing concurrent clients (should see blocking)...")
    
    # Start multiple clients simultaneously
    threads = []
    for i in range(3):
        t = threading.Thread(target=test_client, args=(f"CONCURRENT_{i}", i * 0.1))
        threads.append(t)
        t.start()
    
    # Wait for all threads to complete
    for t in threads:
        t.join()
    
    print("\n3. Testing sequential clients (should all succeed)...")
    
    # Test sequential clients with delay
    for i in range(3):
        time.sleep(3)  # Wait for previous command to complete
        test_client(f"SEQUENTIAL_{i}")

if __name__ == "__main__":
    print("Multi-client blocking test starting...")
    print("Make sure Blender is running with BLD_Remote_MCP on port 7777")
    print()
    
    # Wait a bit for server to be ready
    time.sleep(2)
    
    test_blocking()
    
    print("\nTest completed!")