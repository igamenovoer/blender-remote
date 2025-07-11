import socket
import json

def test_geometry_extraction_direct():
    """Test geometry extraction with direct connection"""
    
    # Connect to BLD_Remote_MCP
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('127.0.0.1', 6688))
    
    # Send geometry extraction command
    geometry_code = '''
import bpy
import json

# Create cube and get geometry
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()
bpy.ops.mesh.primitive_cube_add(location=(2, 3, 4))
cube = bpy.context.active_object
cube.name = "GeometryTestCube"

# Get vertices in local space
vertices = []
for v in cube.data.vertices:
    vertices.append([v.co.x, v.co.y, v.co.z])

# Get world space location
world_location = [cube.location.x, cube.location.y, cube.location.z]

result = {
    "object_name": cube.name,
    "vertex_count": len(vertices),
    "vertices_local": vertices,
    "world_location": world_location,
    "bounds": {
        "min": [min(v[0] for v in vertices), min(v[1] for v in vertices), min(v[2] for v in vertices)],
        "max": [max(v[0] for v in vertices), max(v[1] for v in vertices), max(v[2] for v in vertices)]
    }
}

print("=== GEOMETRY EXTRACTION RESULT ===")
print(json.dumps(result, indent=2))
'''
    
    command = {'message': 'geometry extraction direct', 'code': geometry_code}
    sock.sendall(json.dumps(command).encode('utf-8'))
    response = sock.recv(1024)
    sock.close()
    
    return json.loads(response.decode('utf-8'))

if __name__ == "__main__":
    result = test_geometry_extraction_direct()
    print("=== DIRECT GEOMETRY TEST RESULT ===")
    print(json.dumps(result, indent=2))