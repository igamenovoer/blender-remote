#!/usr/bin/env python3
"""
Debug the exact failing code from the test
"""

import asyncio
import json
import socket
import base64

async def test_failing_code():
    """Test the exact code that's failing in the base64 test"""
    
    print("🔍 Testing the exact failing code...")
    
    # This is the exact code from the failing test
    failing_code = '''
import bpy
import json
import mathutils

# Clear existing mesh objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cube and sphere
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "TestCube"

bpy.ops.mesh.primitive_uv_sphere_add(radius=1.5, location=(3, 0, 0))
sphere = bpy.context.active_object  
sphere.name = "TestSphere"

# Extract vertex data
def get_object_vertices(obj):
    """Get world coordinates of all vertices"""
    mesh = obj.data
    world_matrix = obj.matrix_world
    
    vertices = []
    for vertex in mesh.vertices:
        world_pos = world_matrix @ vertex.co
        vertices.append([world_pos.x, world_pos.y, world_pos.z])
    
    return {
        "name": obj.name,
        "vertex_count": len(vertices),
        "vertices": vertices,
        "location": [obj.location.x, obj.location.y, obj.location.z],
        "bounds": {
            "min": [min(v[i] for v in vertices) for i in range(3)],
            "max": [max(v[i] for v in vertices) for i in range(3)]
        }
    }

# Collect results
results = {
    "objects_created": [cube.name, sphere.name],
    "total_vertices": len(cube.data.vertices) + len(sphere.data.vertices),
    "cube_data": get_object_vertices(cube),
    "sphere_data": get_object_vertices(sphere),
    "scene_stats": {
        "object_count": len(bpy.context.scene.objects),
        "mesh_count": len([obj for obj in bpy.context.scene.objects if obj.type == 'MESH'])
    }
}

# Return structured JSON data
print(json.dumps(results, indent=2))
'''
    
    tests = [
        ("Failing code (no base64)", {
            "type": "execute_code", 
            "params": {"code": failing_code}
        }),
        ("Failing code (send base64)", {
            "type": "execute_code", 
            "params": {
                "code": base64.b64encode(failing_code.encode('utf-8')).decode('ascii'),
                "code_is_base64": True
            }
        }),
        ("Failing code (return base64)", {
            "type": "execute_code", 
            "params": {
                "code": failing_code,
                "return_as_base64": True
            }
        }),
        ("Failing code (both base64)", {
            "type": "execute_code", 
            "params": {
                "code": base64.b64encode(failing_code.encode('utf-8')).decode('ascii'),
                "code_is_base64": True,
                "return_as_base64": True
            }
        }),
    ]
    
    for test_name, command in tests:
        print(f"\n📋 Testing: {test_name}")
        
        try:
            # Connect to Blender
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('127.0.0.1', 6688))
            
            # Send command
            message = json.dumps(command)
            print(f"  📤 Sending command (length: {len(message)})")
            sock.sendall(message.encode('utf-8'))
            
            # Receive response - might need larger buffer for complex output
            response_data = b''
            sock.settimeout(10.0)  # 10 second timeout
            
            while True:
                try:
                    chunk = sock.recv(8192)
                    if not chunk:
                        break
                    response_data += chunk
                    # Try to parse JSON to see if we have complete response
                    try:
                        json.loads(response_data.decode('utf-8'))
                        break  # Successfully parsed, we have complete response
                    except json.JSONDecodeError:
                        continue  # Need more data
                except socket.timeout:
                    break
            
            raw_response = response_data.decode('utf-8')
            print(f"  📥 Raw response length: {len(raw_response)}")
            
            try:
                parsed_response = json.loads(raw_response)
                print(f"  ✅ JSON parsing successful")
                print(f"  📊 Response status: {parsed_response.get('status')}")
                
                if 'result' in parsed_response:
                    result = parsed_response['result']
                    print(f"  📊 Executed: {result.get('executed')}")
                    if result.get('result_is_base64'):
                        print(f"  🔐 Result is base64 encoded")
                        # Decode to see actual content
                        try:
                            decoded = base64.b64decode(result['result']).decode('utf-8')
                            print(f"  📊 Decoded result length: {len(decoded)}")
                            # Try to parse the decoded JSON
                            decoded_json = json.loads(decoded)
                            print(f"  📊 Decoded JSON keys: {list(decoded_json.keys())}")
                        except Exception as e:
                            print(f"  ⚠️ Could not decode base64 result: {e}")
                    else:
                        result_text = result.get('result', '')
                        print(f"  📊 Result length: {len(result_text)}")
                        if result_text:
                            # Try to parse as JSON
                            try:
                                result_json = json.loads(result_text)
                                print(f"  📊 Result JSON keys: {list(result_json.keys())}")
                            except:
                                print(f"  📊 Result preview: {result_text[:200]}...")
                        
            except json.JSONDecodeError as e:
                print(f"  ❌ JSON parsing failed: {e}")
                print(f"  📝 Error position: line {e.lineno}, column {e.colno}")
                print(f"  📝 Raw response preview: {repr(raw_response[:300])}")
                
                # Try to find where the JSON breaks
                lines = raw_response.split('\n')
                for i, line in enumerate(lines[:10], 1):
                    print(f"     Line {i}: {repr(line)}")
                
            sock.close()
            
        except Exception as e:
            print(f"  ❌ Connection/execution failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_failing_code())