import socket
import json
import logging
import time

def test_geometry_extraction_with_output(host='127.0.0.1', port=6688):
    """Test geometry extraction via direct TCP with detailed output capture"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Geometry extraction code with detailed output
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

print(f"=== GEOMETRY EXTRACTION TEST ===")
print(f"Creating cube with:")
print(f"  Location: {location}")
print(f"  Rotation: {rotation}")
print(f"  Scale: {scale}")

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create the test cube
bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation, scale=scale)
cube = bpy.context.active_object
cube.name = 'TestCube'

print(f"Created cube: {cube.name}")

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

print(f"Extracted {len(vertices_world)} vertices")
print(f"Vertex bounds: min={vertices_world.min(axis=0)}, max={vertices_world.max(axis=0)}")

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
    'test_type': 'geometry_extraction_tcp_verbose',
    'geometry_data': geometry_data,
    'summary': {
        'vertices_extracted': len(vertices_world),
        'object_created': cube.name,
        'bounds_size': (vertices_world.max(axis=0) - vertices_world.min(axis=0)).tolist()
    }
}

print(f"=== GEOMETRY EXTRACTION COMPLETE ===")
print(f"Result summary: {result['summary']}")
print(f"Full result data follows:")
print(json.dumps(result, indent=2))
'''

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        logger.info(f"Connected to {host}:{port}")
        
        # Send geometry extraction command
        command = {"message": "geometry extraction verbose test", "code": geometry_code}
        sock.sendall(json.dumps(command).encode('utf-8'))
        
        # Receive response
        response_data = sock.recv(8192)  # Standard buffer first
        response = json.loads(response_data.decode('utf-8'))
        
        logger.info(f"Received response: {response}")
        sock.close()
        
        # Wait a moment for the code to execute and then try to read console output
        print("=== COMMAND SENT TO BLENDER ===")
        print(f"Response: {json.dumps(response, indent=2)}")
        
        # Try to get the actual execution output by running a simple query
        time.sleep(2)
        
        # Send a follow-up command to get console output or results
        sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock2.connect((host, port))
        
        # Query for recent objects to see if our cube was created
        query_code = '''
import bpy
import json

# Get scene info
scene = bpy.context.scene
objects = list(scene.objects)

# Look for our test cube
test_cube = None
for obj in objects:
    if obj.name == 'TestCube':
        test_cube = obj
        break

if test_cube:
    result = {
        'status': 'cube_found',
        'cube_name': test_cube.name,
        'cube_location': list(test_cube.location),
        'cube_rotation': list(test_cube.rotation_euler),
        'cube_scale': list(test_cube.scale),
        'vertex_count': len(test_cube.data.vertices) if test_cube.data else 0,
        'scene_objects': [obj.name for obj in objects]
    }
else:
    result = {
        'status': 'cube_not_found',
        'scene_objects': [obj.name for obj in objects]
    }

print(f"=== CUBE QUERY RESULT ===")
print(json.dumps(result, indent=2))
'''
        
        query_command = {"message": "cube query", "code": query_code}
        sock2.sendall(json.dumps(query_command).encode('utf-8'))
        query_response = sock2.recv(8192)
        query_result = json.loads(query_response.decode('utf-8'))
        
        print("=== CUBE QUERY RESPONSE ===")
        print(f"Query response: {json.dumps(query_result, indent=2)}")
        
        sock2.close()
        
        return {'initial_response': response, 'query_response': query_result}
        
    except Exception as e:
        logger.error(f"TCP geometry extraction test failed: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    result = test_geometry_extraction_with_output()
    print("\n=== FINAL TEST RESULT ===")
    print(json.dumps(result, indent=2))