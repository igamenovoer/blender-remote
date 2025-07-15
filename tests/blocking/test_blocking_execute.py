#!/usr/bin/env python3
"""
Test blocking with two execute_code commands
"""

import socket
import json
import time
import threading

def send_execute_code(code, client_id):
    """Send an execute_code command"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', 7777))
        
        command = {
            "type": "execute_code",
            "params": {
                "code": code
            }
        }
        
        print(f"[{client_id}] Sending execute_code...")
        sock.sendall(json.dumps(command).encode('utf-8'))
        
        response = sock.recv(4096)
        result = json.loads(response.decode('utf-8'))
        
        print(f"[{client_id}] Response: {result}")
        
        sock.close()
        return result
        
    except Exception as e:
        print(f"[{client_id}] Error: {e}")
        return None

def test_execute_blocking():
    """Test blocking with two execute_code commands"""
    print("Testing execute_code blocking...")
    
    # Code that takes time to execute
    long_code = "import time; print('Long task starting...'); time.sleep(3); print('Long task done')"
    
    # Quick code that should be blocked
    quick_code = "print('Quick task executed')"
    
    def send_long_task():
        send_execute_code(long_code, "LONG_EXEC")
    
    # Start the long task in a thread
    long_thread = threading.Thread(target=send_long_task)
    long_thread.start()
    
    # Give it a moment to start
    time.sleep(0.5)
    
    # Try to send a quick execute_code - this should be blocked
    result = send_execute_code(quick_code, "QUICK_EXEC")
    
    # Wait for the long task to finish
    long_thread.join()
    
    # Check if the quick command was blocked
    if result and result.get('status') == 'blocked':
        print("[PASS] Blocking is working correctly!")
    else:
        print("[FAIL] Blocking is NOT working - quick execute_code was not blocked")
        print(f"Quick task result: {result}")

if __name__ == "__main__":
    test_execute_blocking()