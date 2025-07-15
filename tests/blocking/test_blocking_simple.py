#!/usr/bin/env python3
"""
Simple test to check if blocking is working
"""

import socket
import json
import time
import threading

def send_command(command, client_id):
    """Send a command and return the response"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', 7777))
        
        print(f"[{client_id}] Sending: {command}")
        sock.sendall(json.dumps(command).encode('utf-8'))
        
        response = sock.recv(4096)
        result = json.loads(response.decode('utf-8'))
        
        print(f"[{client_id}] Response: {result}")
        
        sock.close()
        return result
        
    except Exception as e:
        print(f"[{client_id}] Error: {e}")
        return None

def test_simple_blocking():
    """Test blocking with a simple approach"""
    print("Testing simple blocking...")
    
    # Start a long-running command
    command1 = {
        "type": "execute_code", 
        "params": {
            "code": "import time; print('Long task starting...'); time.sleep(5); print('Long task done')"
        }
    }
    
    def send_long_command():
        send_command(command1, "LONG_TASK")
    
    # Start the long command in a thread
    long_thread = threading.Thread(target=send_long_command)
    long_thread.start()
    
    # Give it a moment to start
    time.sleep(0.5)
    
    # Now try to send a quick command - this should be blocked
    command2 = {
        "type": "get_scene_info"
    }
    
    result = send_command(command2, "QUICK_TASK")
    
    # Wait for the long command to finish
    long_thread.join()
    
    # Check if the quick command was blocked
    if result and result.get('status') == 'blocked':
        print("[PASS] Blocking is working correctly!")
    else:
        print("[FAIL] Blocking is NOT working - quick command was not blocked")

if __name__ == "__main__":
    test_simple_blocking()