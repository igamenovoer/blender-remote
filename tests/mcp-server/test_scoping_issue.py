#!/usr/bin/env python3
"""
Test script to investigate the scoping issue in code execution.
"""
import socket
import json
import time


def test_scoping_issue(host="127.0.0.1", port=6688):
    """Test different patterns to understand the scoping issue."""
    print(f"🔍 Testing scoping issue in BLD Remote MCP...")
    print("=" * 60)
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        print(f"✅ Connected to {host}:{port}")
        
        # Test 1: Simple import and use (should work)
        print(f"\n📤 Test 1: Simple import and use...")
        simple_code = '''
import numpy as np
print("NumPy available:", np.__version__)
arr = np.array([1, 2, 3])
print("Array:", arr)
'''
        
        command1 = {"type": "execute_code", "params": {"code": simple_code}}
        sock.sendall(json.dumps(command1).encode('utf-8'))
        response1 = json.loads(sock.recv(4096).decode('utf-8'))
        print(f"   Result: {response1}")
        
        # Test 2: Import in function (might fail)
        print(f"\n📤 Test 2: Import in function...")
        func_code = '''
def test_func():
    import numpy as np
    print("NumPy in function:", np.__version__)
    arr = np.array([1, 2, 3])
    print("Array in function:", arr)
    return arr

test_func()
'''
        
        command2 = {"type": "execute_code", "params": {"code": func_code}}
        sock.sendall(json.dumps(command2).encode('utf-8'))
        response2 = json.loads(sock.recv(4096).decode('utf-8'))
        print(f"   Result: {response2}")
        
        # Test 3: Global import, function use (should work)
        print(f"\n📤 Test 3: Global import, function use...")
        global_code = '''
import numpy as np

def test_func():
    print("NumPy in function via global:", np.__version__)
    arr = np.array([1, 2, 3])
    print("Array in function via global:", arr)
    return arr

test_func()
'''
        
        command3 = {"type": "execute_code", "params": {"code": global_code}}
        sock.sendall(json.dumps(command3).encode('utf-8'))
        response3 = json.loads(sock.recv(4096).decode('utf-8'))
        print(f"   Result: {response3}")
        
        # Test 4: Check globals and locals
        print(f"\n📤 Test 4: Check globals and locals...")
        check_code = '''
import numpy as np
print("Globals keys:", list(globals().keys()))
print("'np' in globals():", 'np' in globals())
print("'np' in locals():", 'np' in locals())

def test_func():
    print("In function - 'np' in globals():", 'np' in globals())
    print("In function - 'np' in locals():", 'np' in locals())
    try:
        print("In function - np.__version__:", np.__version__)
    except NameError as e:
        print("In function - NameError:", e)

test_func()
'''
        
        command4 = {"type": "execute_code", "params": {"code": check_code}}
        sock.sendall(json.dumps(command4).encode('utf-8'))
        response4 = json.loads(sock.recv(4096).decode('utf-8'))
        print(f"   Result: {response4}")
        
        sock.close()
        print(f"\n🔒 Connection closed")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_scoping_issue()