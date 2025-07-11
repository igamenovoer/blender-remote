#!/usr/bin/env python3
"""
Debug blocking mechanism
"""

import socket
import json
import time

def send_command(command, client_id):
    """Send a command and return the response"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', 7777))
        
        print(f"[{client_id}] Sending: {json.dumps(command)}")
        sock.sendall(json.dumps(command).encode('utf-8'))
        
        response = sock.recv(4096)
        result = json.loads(response.decode('utf-8'))
        
        print(f"[{client_id}] Response: {json.dumps(result)}")
        
        sock.close()
        return result
        
    except Exception as e:
        print(f"[{client_id}] Error: {e}")
        return None

def test_debug():
    """Debug the blocking mechanism step by step"""
    print("=== Debug Test 1: Basic get_scene_info ===")
    result1 = send_command({"type": "get_scene_info"}, "TEST1")
    
    print("\n=== Debug Test 2: Basic execute_code ===")
    result2 = send_command({
        "type": "execute_code", 
        "params": {"code": "print('Hello from execute_code')"}
    }, "TEST2")
    
    print("\n=== Debug Test 3: Two quick execute_code commands ===")
    result3a = send_command({
        "type": "execute_code", 
        "params": {"code": "print('Quick task A')"}
    }, "TEST3A")
    
    result3b = send_command({
        "type": "execute_code", 
        "params": {"code": "print('Quick task B')"}
    }, "TEST3B")
    
    print("\n=== Results Summary ===")
    print(f"Test 1 status: {result1.get('status') if result1 else 'ERROR'}")
    print(f"Test 2 status: {result2.get('status') if result2 else 'ERROR'}")
    print(f"Test 3A status: {result3a.get('status') if result3a else 'ERROR'}")
    print(f"Test 3B status: {result3b.get('status') if result3b else 'ERROR'}")

if __name__ == "__main__":
    test_debug()