# BlenderAutoMCP Interaction Guide

## Overview

BlenderAutoMCP is a production-ready 3rd party Blender MCP addon that provides comprehensive remote control capabilities for Blender. This guide documents how to interact with it using the client modules in `context/refcode/auto_mcp_remote/`.

**Service Details:**
- **Port**: 9876 (TCP)
- **Protocol**: JSON commands over TCP sockets
- **Status**: ✅ Operational, GUI mode only
- **Limitation**: Cannot run in `blender --background` mode

## Architecture Overview

The interaction follows a three-layer architecture:

### 1. Low-Level Communication (BlenderMCPClient)
- Direct TCP socket communication
- JSON command format: `{"type": "command_type", "params": {...}}`
- Handles connection, timeouts, and error processing
- Auto-detects Docker environments

### 2. High-Level Managers
- **BlenderSceneManager**: Scene manipulation, object creation, camera control
- **BlenderAssetManager**: Asset library management (not fully implemented)

### 3. Data Types
- **SceneObject**: Represents Blender objects with numpy-based transforms
- **BlenderMCPError**: Custom exception handling

## Core Command Types

### Essential Commands (Available in Our Implementation)
1. **execute_code**: Execute arbitrary Python code in Blender
2. **get_scene_info**: Get current scene information (objects, materials, etc.)
3. **get_object_info**: Get detailed info about specific object
4. **get_viewport_screenshot**: Capture viewport screenshot
5. **server_shutdown**: Gracefully shutdown the MCP server

### Asset Provider Commands (NOT in Our Implementation)
- **PolyHaven Integration**: search_polyhaven_assets, download_polyhaven_asset, set_texture
- **Hyper3D/Rodin Integration**: create_rodin_job, poll_rodin_job_status, import_generated_asset
- **Sketchfab Integration**: search_sketchfab_models, download_sketchfab_model

## Client Usage Patterns

### Basic Client Usage

```python
from context.refcode.auto_mcp_remote import BlenderMCPClient

# Connect to BlenderAutoMCP
client = BlenderMCPClient(host="localhost", port=9876, timeout=30.0)

# Test connection
if client.test_connection():
    print("✅ Connected to BlenderAutoMCP")
else:
    print("❌ Connection failed")

# Execute Python code
result = client.execute_python("print('Hello from Blender!')")
print(f"Result: {result}")

# Get scene information
scene_info = client.get_scene_info()
print(f"Scene: {scene_info['name']}, Objects: {scene_info['object_count']}")

# Get object details
if scene_info['objects']:
    obj_name = scene_info['objects'][0]['name']
    obj_info = client.get_object_info(obj_name)
    print(f"Object {obj_name}: {obj_info}")

# Take screenshot
screenshot_info = client.take_screenshot("/tmp/viewport.png")
print(f"Screenshot: {screenshot_info}")
```

### Scene Manager Usage

```python
from context.refcode.auto_mcp_remote import BlenderMCPClient, BlenderSceneManager

# Create client and scene manager
client = BlenderMCPClient(port=9876)
scene = BlenderSceneManager(client)

# List all objects
objects = scene.list_objects()
print(f"Found {len(objects)} objects")

# Create primitives
cube_name = scene.add_cube(location=(0, 0, 0), size=2.0, name="TestCube")
sphere_name = scene.add_sphere(location=(3, 0, 0), radius=1.0, name="TestSphere")

# Move objects
scene.move_object(cube_name, location=(1, 1, 1))

# Set camera position
scene.set_camera_location(location=(7, -7, 5), target=(0, 0, 0))

# Render scene
scene.render_image("/tmp/render.png", resolution=(1920, 1080))

# Export object as GLB
glb_data = scene.get_object_as_glb_raw(cube_name, with_material=True)
with open("/tmp/exported_cube.glb", "wb") as f:
    f.write(glb_data)

# Clean up
scene.delete_object(cube_name)
scene.delete_object(sphere_name)
```

### Raw Command Execution

```python
# Execute raw MCP commands
response = client.execute_command("get_scene_info", {})
print(f"Raw response: {response}")

# Execute code with complex operations
complex_code = """
import bpy
import bmesh

# Create and modify mesh
bpy.ops.mesh.primitive_cube_add()
cube = bpy.context.active_object
cube.name = "ModifiedCube"

# Enter edit mode and subdivide
bpy.context.view_layer.objects.active = cube
bpy.ops.object.mode_set(mode='EDIT')

bm = bmesh.from_mesh(cube.data)
bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=2, use_grid_fill=True)
bm.to_mesh(cube.data)
bm.free()

bpy.ops.object.mode_set(mode='OBJECT')
print(f"Created and modified cube: {cube.name}")
"""

result = client.execute_python(complex_code)
print(f"Complex operation result: {result}")
```

## Message Format

### Request Format
```json
{
    "type": "command_type",
    "params": {
        "param1": "value1",
        "param2": "value2"
    }
}
```

### Response Format
```json
{
    "status": "success" | "error",
    "result": {...},
    "message": "error message if status is error"
}
```

## Error Handling

```python
from context.refcode.auto_mcp_remote.data_types import BlenderMCPError

try:
    # Risky operation
    result = client.execute_python("invalid_syntax +++ error")
except BlenderMCPError as e:
    print(f"Blender MCP Error: {e}")
except Exception as e:
    print(f"General error: {e}")
```

## Connection Options

### Auto-Detection
```python
# Auto-detects Docker environment
client = BlenderMCPClient()  # Uses localhost or host.docker.internal
```

### Explicit Configuration
```python
# Specific host and port
client = BlenderMCPClient(host="192.168.1.100", port=9876, timeout=60.0)

# From URL
client = BlenderMCPClient.from_url("http://blender-server:9876")
```

## Performance Considerations

1. **Connection Pooling**: Create one client instance and reuse it
2. **Timeouts**: Adjust timeout based on operation complexity
3. **Large Data**: Use base64 encoding for binary data transfer
4. **Error Recovery**: Implement retry logic for network issues

## Environment Setup

### Starting BlenderAutoMCP
```bash
# Kill existing Blender processes
pkill -f blender

# Start with auto-start MCP (GUI mode required)
export BLENDER_AUTO_MCP_SERVICE_PORT=9876
export BLENDER_AUTO_MCP_START_NOW=1
/apps/blender-4.4.3-linux-x64/blender &

# Wait for startup
sleep 10

# Verify service is running
netstat -tlnp | grep 9876
```

### Testing Connection
```bash
# Simple connection test
echo '{"type": "get_scene_info", "params": {}}' | nc 127.0.0.1 9876
```

## Key Differences from Our Implementation

| Feature | BlenderAutoMCP | BLD Remote MCP |
|---------|----------------|----------------|
| **Port** | 9876 | 6688 |
| **Background Mode** | ❌ GUI only | ✅ GUI + Background |
| **Asset Providers** | ✅ Full integration | ❌ Excluded |
| **Commands** | 15+ commands | 5 essential commands |
| **Purpose** | Full-featured | Minimal essential |

## Integration Notes

- **Use as Reference**: BlenderAutoMCP serves as our architectural reference
- **Client Compatibility**: Our BLD Remote MCP should work with similar client code
- **Command Subset**: We implement only the essential commands (no asset providers)
- **Same JSON Format**: Maintain compatibility with existing client patterns

## Troubleshooting

### Common Issues
1. **Connection Refused**: Check if Blender is running and service is started
2. **Background Mode**: BlenderAutoMCP won't start in `blender --background`
3. **Port Conflicts**: Ensure no other service is using port 9876
4. **Timeout Errors**: Increase timeout for complex operations

### Debug Commands
```python
# Test basic connectivity
client.test_connection()

# Check service status
scene_info = client.get_scene_info()
print(f"Service responsive: {scene_info is not None}")

# Execute simple test
result = client.execute_python("print('Service test')")
print(f"Execution works: {'Service test' in result}")
```

This guide provides the foundation for understanding how to interact with BlenderAutoMCP and serves as a reference for implementing compatible interfaces in our minimal BLD Remote MCP service.