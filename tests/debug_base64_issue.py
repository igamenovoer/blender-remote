#!/usr/bin/env python3
"""
Debug Base64 Issue - Test the exact JSON response from Blender
"""

import asyncio
import json
import socket

async def test_direct_blender_communication():
    """Test direct communication with Blender to see the raw response"""
    
    print("[SEARCH] Testing direct communication with Blender TCP service...")
    
    # Simple code that produces JSON output
    simple_json_code = '''
import json
result = {"test": "simple", "value": 123}
print(json.dumps(result))
'''
    
    # Complex code that might cause issues
    complex_json_code = '''
import json
result = {
    "test": "complex", 
    "quotes": "This has \\"quotes\\" and 'apostrophes'",
    "newlines": "Line 1\\nLine 2\\nLine 3",
    "special": "Special chars: \\t\\r\\n"
}
print(json.dumps(result))
'''
    
    tests = [
        ("Simple JSON (no base64)", {"type": "execute_code", "params": {"code": simple_json_code}}),
        ("Simple JSON (with base64)", {"type": "execute_code", "params": {"code": simple_json_code, "code_is_base64": False, "return_as_base64": True}}),
        ("Complex JSON (no base64)", {"type": "execute_code", "params": {"code": complex_json_code}}),
        ("Complex JSON (with base64)", {"type": "execute_code", "params": {"code": complex_json_code, "code_is_base64": False, "return_as_base64": True}}),
    ]
    
    for test_name, command in tests:
        print(f"\n[INFO] Testing: {test_name}")
        
        try:
            # Connect to Blender
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('127.0.0.1', 6688))
            
            # Send command
            message = json.dumps(command)
            print(f"  [SEND] Sending: {message[:100]}...")
            sock.sendall(message.encode('utf-8'))
            
            # Receive response
            response_data = sock.recv(8192)
            raw_response = response_data.decode('utf-8')
            print(f"  [RECEIVE] Raw response length: {len(raw_response)}")
            print(f"  [RECEIVE] Raw response preview: {raw_response[:200]}...")
            
            try:
                parsed_response = json.loads(raw_response)
                print(f"  [PASS] JSON parsing successful")
                print(f"  [STATS] Response status: {parsed_response.get('status')}")
                if 'result' in parsed_response:
                    result = parsed_response['result']
                    print(f"  [STATS] Result type: {type(result)}")
                    if isinstance(result, dict):
                        print(f"  [STATS] Result keys: {list(result.keys())}")
                        if 'result_is_base64' in result:
                            print(f"  [ENCODE] Base64 encoded: {result['result_is_base64']}")
            except json.JSONDecodeError as e:
                print(f"  [FAIL] JSON parsing failed: {e}")
                print(f"  [LOG] Raw response: {repr(raw_response)}")
                
            sock.close()
            
        except Exception as e:
            print(f"  [FAIL] Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_direct_blender_communication())