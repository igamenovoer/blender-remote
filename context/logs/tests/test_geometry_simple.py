import socket
import json
import logging

def test_simple_geometry_extraction(host='127.0.0.1', port=6688):
    """Test simple geometry extraction with immediate result"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Simple geometry code that returns results immediately
    geometry_code = '''
import bpy
import json

# Create a simple cube
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = 'TestCube'

# Get basic geometry info
vertices = cube.data.vertices
vertex_list = []
for v in vertices:
    vertex_list.append([v.co.x, v.co.y, v.co.z])

# Create result
result = {
    'object_name': cube.name,
    'vertex_count': len(vertices),
    'vertices_local': vertex_list,
    'location': [cube.location.x, cube.location.y, cube.location.z],
    'bounds': {
        'min': [min(v[0] for v in vertex_list), min(v[1] for v in vertex_list), min(v[2] for v in vertex_list)],
        'max': [max(v[0] for v in vertex_list), max(v[1] for v in vertex_list), max(v[2] for v in vertex_list)]
    }
}

print("=== GEOMETRY EXTRACTION RESULT ===")
print(json.dumps(result, indent=2))
'''

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        logger.info(f"Connected to {host}:{port}")
        
        # Send geometry extraction command
        command = {"message": "simple geometry test", "code": geometry_code}
        sock.sendall(json.dumps(command).encode('utf-8'))
        
        # Receive response
        response_data = sock.recv(8192)
        response = json.loads(response_data.decode('utf-8'))
        
        logger.info(f"Received response")
        sock.close()
        
        return response
        
    except Exception as e:
        logger.error(f"TCP geometry extraction test failed: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    result = test_simple_geometry_extraction()
    print("\n=== SIMPLE GEOMETRY TEST RESULT ===")
    print(json.dumps(result, indent=2))