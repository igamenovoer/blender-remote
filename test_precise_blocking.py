#!/usr/bin/env python3
"""
Test blocking with very precise timing
"""

import socket
import json
import time
import threading

def send_execute_code(code, client_id, delay=0):
    """Send an execute_code command with optional delay"""
    if delay > 0:
        time.sleep(delay)
        
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', 7777))
        
        command = {
            "type": "execute_code",
            "params": {"code": code}
        }
        
        print(f"[{client_id}] Sending execute_code at {time.time():.3f}...")
        sock.sendall(json.dumps(command).encode('utf-8'))
        
        response = sock.recv(4096)
        result = json.loads(response.decode('utf-8'))
        
        print(f"[{client_id}] Response at {time.time():.3f}: {result}")
        
        sock.close()
        return result
        
    except Exception as e:
        print(f"[{client_id}] Error: {e}")
        return None

def test_precise_blocking():
    """Test blocking with precise timing"""
    print("Testing precise execute_code blocking...")
    
    # Very long code that will definitely take time
    long_code = """
import time
print('Long task starting...')
for i in range(5):
    print(f'Long task step {i+1}/5')
    time.sleep(1)
print('Long task done!')
"""
    
    # Quick code 
    quick_code = "print('Quick task - should be blocked!')"
    
    # Start tasks with very small delays
    results = []
    threads = []
    
    def run_task(code, client_id, delay):
        result = send_execute_code(code, client_id, delay)
        results.append((client_id, result))
    
    # Start long task
    t1 = threading.Thread(target=run_task, args=(long_code, "LONG_TASK", 0))
    # Start quick task very shortly after
    t2 = threading.Thread(target=run_task, args=(quick_code, "QUICK_TASK", 0.1))
    # Start another quick task even later
    t3 = threading.Thread(target=run_task, args=(quick_code, "QUICK_TASK2", 0.2))
    
    threads = [t1, t2, t3]
    
    for t in threads:
        t.start()
    
    for t in threads:
        t.join()
    
    # Analyze results
    print("\n=== Results Analysis ===")
    blocked_count = 0
    for client_id, result in results:
        if result and result.get('status') == 'blocked':
            print(f"✅ {client_id} was correctly blocked")
            blocked_count += 1
        else:
            print(f"❌ {client_id} was NOT blocked: {result}")
    
    if blocked_count > 0:
        print(f"\n✅ Blocking is working! {blocked_count} clients were blocked.")
    else:
        print(f"\n❌ Blocking is NOT working. No clients were blocked.")

if __name__ == "__main__":
    test_precise_blocking()