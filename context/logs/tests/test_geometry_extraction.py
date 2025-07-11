import socket
import json
import logging

def test_geometry_extraction_tcp(host='127.0.0.1', port=6688):
    """Test geometry extraction via direct TCP"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Geometry extraction code
    geometry_code = '''
import bpy
import numpy as np
import random
import json

# Create a cube at random location, rotation, and scale
random.seed(42)  # For reproducible testing
location = (random.uniform(-5, 5), random.uniform(-5, 5), random.uniform(-5, 5))
rotation = (random.uniform(0, 6.28), random.uniform(0, 6.28), random.uniform(0, 6.28))
scale = (random.uniform(0.5, 3), random.uniform(0.5, 3), random.uniform(0.5, 3))

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create the test cube
bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation, scale=scale)
cube = bpy.context.active_object
cube.name = 'TestCube'

# Get vertices in world space using efficient method
def get_vertices_in_world_space(obj):
    if obj.type != 'MESH':
        return None
    
    # Get the world matrix of the object
    world_matrix = np.array(obj.matrix_world)
    
    # Get the vertices in local space using foreach_get
    vertex_count = len(obj.data.vertices)
    local_vertices = np.empty(vertex_count * 3, dtype=np.float32)
    obj.data.vertices.foreach_get('co', local_vertices)
    local_vertices = local_vertices.reshape(vertex_count, 3)
    
    # Transform vertices to world space
    # Convert to homogeneous coordinates for transformation
    local_vertices_homogeneous = np.hstack((local_vertices, np.ones((vertex_count, 1))))
    
    # Apply the transformation
    world_vertices_homogeneous = local_vertices_homogeneous @ world_matrix.T
    
    # Convert back to 3D coordinates
    world_vertices = world_vertices_homogeneous[:, :3]
    
    return world_vertices

# Extract geometry data
vertices_world = get_vertices_in_world_space(cube)
transform_matrix = np.array(cube.matrix_world)

# Prepare data for MCP transmission (JSON-serializable)
geometry_data = {
    'object_name': cube.name,
    'vertex_count': len(vertices_world),
    'vertices_world_space': vertices_world.tolist(),
    'transform_matrix': transform_matrix.tolist(),
    'location': list(location),
    'rotation': list(rotation),
    'scale': list(scale),
    'bounds': {
        'min': vertices_world.min(axis=0).tolist(),
        'max': vertices_world.max(axis=0).tolist()
    }
}

# Return formatted result
result = {
    'status': 'success',
    'test_type': 'geometry_extraction_tcp',
    'geometry_data': geometry_data
}

print(json.dumps(result, indent=2))
'''

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        logger.info(f"Connected to {host}:{port}")
        
        # Send geometry extraction command
        command = {"message": "geometry extraction test", "code": geometry_code}
        sock.sendall(json.dumps(command).encode('utf-8'))
        
        # Receive large response (geometry data can be substantial)
        response_data = sock.recv(32768)  # Larger buffer for geometry data
        response = json.loads(response_data.decode('utf-8'))
        
        logger.info(f"Geometry extraction completed via TCP")
        sock.close()
        return response
    except Exception as e:
        logger.error(f"TCP geometry extraction test failed: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    result = test_geometry_extraction_tcp()
    print(json.dumps(result, indent=2))