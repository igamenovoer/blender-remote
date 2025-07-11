import socket
import json
import time

def demonstrate_geometry_extraction():
    """Demonstrate geometry extraction with the BLD_Remote_MCP service"""
    
    print("=== BLD_Remote_MCP Geometry Extraction Demo ===")
    print("This demonstrates how the service handles geometry extraction commands.")
    print("The service schedules commands and executes them asynchronously in Blender.")
    print()
    
    # Connect to the service
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('127.0.0.1', 6688))
    
    # Send a geometry extraction command
    geometry_code = '''
import bpy
import json

# Clear scene and create test geometry
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create a cube at specific location
bpy.ops.mesh.primitive_cube_add(location=(2, 3, 4))
cube = bpy.context.active_object
cube.name = "DemoGeometryCube"

# Extract vertices in local space
vertices = []
for v in cube.data.vertices:
    vertices.append([v.co.x, v.co.y, v.co.z])

# Build comprehensive geometry data
geometry_data = {
    "object_name": cube.name,
    "vertex_count": len(vertices),
    "vertices_local": vertices,
    "world_location": [cube.location.x, cube.location.y, cube.location.z],
    "world_rotation": [cube.rotation_euler.x, cube.rotation_euler.y, cube.rotation_euler.z],
    "world_scale": [cube.scale.x, cube.scale.y, cube.scale.z],
    "dimensions": [cube.dimensions.x, cube.dimensions.y, cube.dimensions.z],
    "bounds": {
        "min": [min(v[0] for v in vertices), min(v[1] for v in vertices), min(v[2] for v in vertices)],
        "max": [max(v[0] for v in vertices), max(v[1] for v in vertices), max(v[2] for v in vertices)]
    },
    "material_count": len(cube.data.materials),
    "face_count": len(cube.data.polygons),
    "edge_count": len(cube.data.edges)
}

# Print the results (this goes to Blender console)
print("=== GEOMETRY EXTRACTION RESULTS ===")
print(f"Object: {geometry_data['object_name']}")
print(f"Vertices: {geometry_data['vertex_count']}")
print(f"Location: {geometry_data['world_location']}")
print(f"Dimensions: {geometry_data['dimensions']}")
print(f"Bounds: {geometry_data['bounds']}")
print("Complete geometry data:")
print(json.dumps(geometry_data, indent=2))
print("=== END GEOMETRY EXTRACTION ===")
'''
    
    # Send the command
    command = {
        "message": "Geometry extraction demonstration",
        "code": geometry_code
    }
    
    print("Sending geometry extraction command to BLD_Remote_MCP service...")
    sock.sendall(json.dumps(command).encode('utf-8'))
    
    # Receive response
    response_data = sock.recv(1024)
    response = json.loads(response_data.decode('utf-8'))
    
    print(f"Service Response: {json.dumps(response, indent=2)}")
    
    sock.close()
    
    print()
    print("=== Service Architecture Explanation ===")
    print("The BLD_Remote_MCP service operates asynchronously:")
    print("1. It receives commands via TCP and immediately responds with 'Code execution scheduled'")
    print("2. Commands are executed in Blender's main thread using the timer system")
    print("3. Execution results (print statements) appear in the Blender console")
    print("4. This design prevents blocking the TCP service while allowing complex operations")
    print()
    print("Expected Geometry Data Structure:")
    expected_data = {
        "object_name": "DemoGeometryCube",
        "vertex_count": 8,
        "vertices_local": [
            [-1.0, -1.0, -1.0], [1.0, -1.0, -1.0], [-1.0, 1.0, -1.0], [1.0, 1.0, -1.0],
            [-1.0, -1.0, 1.0], [1.0, -1.0, 1.0], [-1.0, 1.0, 1.0], [1.0, 1.0, 1.0]
        ],
        "world_location": [2.0, 3.0, 4.0],
        "bounds": {"min": [-1.0, -1.0, -1.0], "max": [1.0, 1.0, 1.0]},
        "dimensions": [2.0, 2.0, 2.0]
    }
    print(json.dumps(expected_data, indent=2))
    
    return response

if __name__ == "__main__":
    result = demonstrate_geometry_extraction()
    print(f"\n=== FINAL DEMO RESULT ===")
    print(f"Service successfully scheduled geometry extraction command")
    print(f"Check Blender console for actual execution results")