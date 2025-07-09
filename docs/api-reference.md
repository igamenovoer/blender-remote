# API Reference

This document provides comprehensive API reference for all MCP tools available in blender-remote. Each tool is documented with parameters, return types, error handling, and usage examples.

## Tool Overview

| Tool | Purpose | GUI Required | Parameters |
|------|---------|--------------|------------|
| [`get_scene_info`](#get_scene_info) | Scene inspection | No | None |
| [`get_object_info`](#get_object_info) | Object details | No | `object_name` |
| [`execute_blender_code`](#execute_blender_code) | Code execution | No | `code` |
| [`get_viewport_screenshot`](#get_viewport_screenshot) | Screenshot capture | **Yes** | `max_size`, `filepath`, `format` |
| [`check_connection_status`](#check_connection_status) | Health check | No | None |

## get_scene_info

Retrieves comprehensive information about the current Blender scene including objects, materials, and frame settings.

### Parameters

None

### Returns

```typescript
{
  status: "success" | "error",
  result: {
    scene_name: string,
    total_objects: number,
    total_materials: number,
    current_frame: number,
    frame_range: [number, number],
    objects: Array<{
      name: string,
      type: string,
      location: [number, number, number],
      rotation: [number, number, number],
      scale: [number, number, number],
      visible: boolean,
      material_slots: string[]
    }>,
    materials: string[]
  }
}
```

### Example Response

```json
{
  "status": "success",
  "result": {
    "scene_name": "Scene",
    "total_objects": 4,
    "total_materials": 3,
    "current_frame": 1,
    "frame_range": [1, 250],
    "objects": [
      {
        "name": "Cube",
        "type": "MESH",
        "location": [0.0, 0.0, 0.0],
        "rotation": [0.0, 0.0, 0.0],
        "scale": [1.0, 1.0, 1.0],
        "visible": true,
        "material_slots": ["Material"]
      },
      {
        "name": "Camera",
        "type": "CAMERA",
        "location": [7.36, -6.93, 4.96],
        "rotation": [1.11, 0.0, 0.81],
        "scale": [1.0, 1.0, 1.0],
        "visible": true,
        "material_slots": []
      },
      {
        "name": "Light",
        "type": "LIGHT",
        "location": [4.08, 1.01, 5.90],
        "rotation": [0.65, 0.06, -1.89],
        "scale": [1.0, 1.0, 1.0],
        "visible": true,
        "material_slots": []
      }
    ],
    "materials": ["Material", "Material.001", "Glass"]
  }
}
```

### Error Handling

```json
{
  "status": "error",
  "message": "Failed to retrieve scene information: Connection timeout"
}
```

### Usage Examples

**LLM Prompts:**
- "What objects are in the current scene?"
- "Show me all materials in the scene"
- "List all visible objects with their positions"
- "What's the current frame range?"

**CLI:**
```bash
blender-remote scene
```

**Python:**
```python
import json
from blender_remote.mcp_server import get_scene_info

result = get_scene_info()
print(f"Scene has {result['total_objects']} objects")
```

---

## get_object_info

Retrieves detailed information about a specific object in the scene.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `object_name` | `string` | Yes | Name of the object to inspect |

### Returns

```typescript
{
  status: "success" | "error",
  result: {
    name: string,
    type: string,
    location: [number, number, number],
    rotation: [number, number, number],
    scale: [number, number, number],
    dimensions: [number, number, number],
    visible: boolean,
    material_slots: string[],
    vertex_count?: number,     // Only for MESH objects
    face_count?: number,       // Only for MESH objects
    bone_count?: number,       // Only for ARMATURE objects
    lamp_type?: string,        // Only for LIGHT objects
    camera_type?: string,      // Only for CAMERA objects
    focal_length?: number,     // Only for CAMERA objects
    modifier_count?: number,   // Only for MESH objects
    constraints?: string[]     // Constraint names
  }
}
```

### Example Response

```json
{
  "status": "success",
  "result": {
    "name": "Cube",
    "type": "MESH",
    "location": [0.0, 0.0, 0.0],
    "rotation": [0.0, 0.0, 0.0],
    "scale": [1.0, 1.0, 1.0],
    "dimensions": [2.0, 2.0, 2.0],
    "visible": true,
    "material_slots": ["Material"],
    "vertex_count": 8,
    "face_count": 6,
    "modifier_count": 0,
    "constraints": []
  }
}
```

### Error Handling

```json
{
  "status": "error",
  "message": "Object 'NonExistentObject' not found in scene"
}
```

### Usage Examples

**LLM Prompts:**
- "Tell me about the Cube object"
- "What are the dimensions of the Camera?"
- "Show me the material slots for the Sphere"
- "How many vertices does the Monkey have?"

**CLI:**
```bash
blender-remote object --name "Cube"
```

**Python:**
```python
result = get_object_info("Cube")
if result["status"] == "success":
    obj = result["result"]
    print(f"{obj['name']}: {obj['vertex_count']} vertices, {obj['face_count']} faces")
```

---

## execute_blender_code

Executes Python code in Blender's context with full access to the Blender Python API.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `code` | `string` | Yes | Python code to execute in Blender |

### Returns

```typescript
{
  status: "success" | "error",
  result: string,           // Success message or return value
  output?: string,          // Any print statements or stdout
  execution_time?: number   // Execution time in seconds
}
```

### Example Response

```json
{
  "status": "success",
  "result": "Code executed successfully",
  "output": "Created cube at (2, 0, 0)\nCube name: Cube.001\n",
  "execution_time": 0.023
}
```

### Error Handling

```json
{
  "status": "error",
  "message": "Python code execution failed",
  "error_type": "SyntaxError",
  "details": "invalid syntax (<string>, line 1)"
}
```

### Code Examples

#### Basic Object Creation
```python
# Create a cube
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))

# Create a sphere
bpy.ops.mesh.primitive_uv_sphere_add(location=(2, 0, 0))

# Create a cylinder
bpy.ops.mesh.primitive_cylinder_add(location=(-2, 0, 0))
```

#### Material Creation
```python
# Create a new material
mat = bpy.data.materials.new(name="BlueMetal")
mat.use_nodes = True

# Get the principled BSDF node
principled = mat.node_tree.nodes["Principled BSDF"]

# Set material properties
principled.inputs["Base Color"].default_value = (0.2, 0.4, 0.8, 1.0)
principled.inputs["Metallic"].default_value = 0.8
principled.inputs["Roughness"].default_value = 0.2

# Assign to active object
bpy.context.active_object.data.materials.append(mat)
```

#### Camera Setup
```python
# Add camera
bpy.ops.object.camera_add(location=(7, -7, 5))
camera = bpy.context.active_object

# Point camera at origin
camera.rotation_euler = (1.1, 0, 0.8)

# Set as active camera
bpy.context.scene.camera = camera
```

#### Lighting Setup
```python
# Add sun light
bpy.ops.object.light_add(type='SUN', location=(4, 4, 8))
sun = bpy.context.active_object
sun.data.energy = 5.0

# Add area light
bpy.ops.object.light_add(type='AREA', location=(-4, -4, 6))
area = bpy.context.active_object
area.data.energy = 10.0
area.data.size = 5.0
```

#### Animation Setup
```python
# Set frame range
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 120

# Animate object rotation
obj = bpy.context.active_object
obj.rotation_euler = (0, 0, 0)
obj.keyframe_insert(data_path="rotation_euler", frame=1)

obj.rotation_euler = (0, 0, 6.28)  # Full rotation
obj.keyframe_insert(data_path="rotation_euler", frame=120)
```

### Usage Examples

**LLM Prompts:**
- "Create a blue metallic cube at position (2, 0, 0)"
- "Add a camera looking at the origin"
- "Set up a three-point lighting system"
- "Create a donut with chocolate icing"

**CLI:**
```bash
blender-remote exec "bpy.ops.mesh.primitive_cube_add(location=(0, 0, 2))"
```

**Python:**
```python
code = """
import bpy
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 2))
cube = bpy.context.active_object
cube.name = "MyCube"
print(f"Created {cube.name}")
"""

result = execute_blender_code(code)
print(result["output"])
```

---

## get_viewport_screenshot

Captures the current viewport as a base64-encoded image. **Requires GUI mode** - not available in background mode.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `max_size` | `number` | No | `800` | Maximum image dimension (width or height) |
| `filepath` | `string` | No | `auto` | Custom file path (auto-generated if not provided) |
| `format` | `string` | No | `"PNG"` | Image format: "PNG", "JPEG" |

### Returns

```typescript
{
  status: "success" | "error",
  result: {
    type: "image",
    data: string,          // Base64-encoded image data
    mimeType: string,      // MIME type (image/png, image/jpeg)
    size: number,          // File size in bytes
    dimensions: {
      width: number,
      height: number
    }
  }
}
```

### Example Response

```json
{
  "status": "success",
  "result": {
    "type": "image",
    "data": "iVBORw0KGgoAAAANSUhEUgAAA...",
    "mimeType": "image/png",
    "size": 61868,
    "dimensions": {
      "width": 800,
      "height": 600
    }
  }
}
```

### Error Handling

#### Background Mode Error
```json
{
  "status": "error",
  "message": "Screenshot capture is not supported in background mode. Please run Blender in GUI mode for screenshot functionality."
}
```

#### File System Error
```json
{
  "status": "error",
  "message": "Failed to capture screenshot: Permission denied writing to /tmp/screenshot.png"
}
```

### File Management

The screenshot tool uses UUID-based temporary files for thread safety:

1. **Automatic Filename**: When no `filepath` is provided, generates unique name: `blender_screenshot_{uuid}.{format}`
2. **Temporary Directory**: Uses system temp directory (`/tmp/` on Linux/Mac, `%TEMP%` on Windows)
3. **Automatic Cleanup**: Files are automatically deleted after reading into memory
4. **Thread Safety**: Multiple concurrent requests get unique filenames

### Usage Examples

**LLM Prompts:**
- "Show me the current viewport"
- "Take a screenshot of the scene"
- "Capture the viewport and analyze the composition"
- "Show me what the scene looks like now"

**CLI:**
```bash
blender-remote screenshot
blender-remote screenshot --size 1200 --format JPEG
```

**Python:**
```python
# Basic screenshot
result = get_viewport_screenshot()
if result["status"] == "success":
    image_data = result["result"]["data"]
    # image_data is base64 encoded

# High-quality screenshot
result = get_viewport_screenshot(max_size=1920, format="PNG")

# Custom file path
result = get_viewport_screenshot(filepath="/tmp/my_screenshot.png")
```

---

## check_connection_status

Verifies the health and connectivity of the BLD_Remote_MCP service.

### Parameters

None

### Returns

```typescript
{
  status: "success" | "error",
  result: {
    service: string,         // Service name
    port: number,           // Port number
    blender_version: string,
    addon_version: string,
    mode: "GUI" | "BACKGROUND",
    uptime: string,         // HH:MM:SS format
    scene_name: string,
    object_count: number,
    memory_usage?: number   // MB
  }
}
```

### Example Response

```json
{
  "status": "success",
  "result": {
    "service": "BLD_Remote_MCP",
    "port": 6688,
    "blender_version": "4.4.3",
    "addon_version": "1.0.0",
    "mode": "GUI",
    "uptime": "01:23:45",
    "scene_name": "Scene",
    "object_count": 4,
    "memory_usage": 156.3
  }
}
```

### Error Handling

```json
{
  "status": "error",
  "message": "Connection to BLD_Remote_MCP service failed: Connection refused"
}
```

### Usage Examples

**LLM Prompts:**
- "Check if Blender is connected"
- "What's the service status?"
- "Is the MCP server running?"
- "Show me the connection info"

**CLI:**
```bash
blender-remote status
```

**Python:**
```python
result = check_connection_status()
if result["status"] == "success":
    info = result["result"]
    print(f"Connected to {info['service']} on port {info['port']}")
    print(f"Blender {info['blender_version']} in {info['mode']} mode")
```

---

## Error Handling

### Common Error Types

#### Connection Errors
```json
{
  "status": "error",
  "type": "connection_failed",
  "message": "Connection to BLD_Remote_MCP service failed",
  "details": "Connection refused on port 6688"
}
```

#### Parameter Errors
```json
{
  "status": "error",
  "type": "invalid_parameter",
  "message": "Invalid parameter 'object_name'",
  "details": "Parameter cannot be empty"
}
```

#### Execution Errors
```json
{
  "status": "error",
  "type": "execution_error",
  "message": "Python code execution failed",
  "error_type": "AttributeError",
  "details": "'NoneType' object has no attribute 'data'"
}
```

#### Mode Limitation Errors
```json
{
  "status": "error",
  "type": "mode_limitation",
  "message": "Screenshot capture requires GUI mode",
  "details": "Current mode: BACKGROUND"
}
```

### Error Recovery

Most errors are recoverable:

1. **Connection Errors**: Automatic reconnection attempts
2. **Parameter Errors**: Clear error messages for correction
3. **Execution Errors**: Blender continues running, only specific operation fails
4. **Mode Limitations**: Clear explanation of what's not supported

### Best Practices

1. **Always Check Status**: Use `check_connection_status()` before complex operations
2. **Handle Errors Gracefully**: Check `status` field in all responses
3. **Use Appropriate Modes**: GUI for screenshots, background for automation
4. **Validate Parameters**: Check parameter types and ranges before sending

## Authentication & Security

### Local Access Only

The MCP server is designed for local development:

- **Binding**: Service binds to `127.0.0.1` (localhost only)
- **No Authentication**: No username/password required
- **Port Based**: Security through port access control
- **Process Isolation**: Runs in Blender's sandboxed environment

### Code Execution Security

When using `execute_blender_code()`:

- **Blender Context**: Code runs in Blender's Python environment
- **Limited File Access**: Restricted to Blender's capabilities
- **Memory Isolated**: Cannot access other processes
- **Error Contained**: Exceptions don't crash the service

### Best Practices

1. **Local Development Only**: Don't expose to network
2. **Validate Input**: Check code before execution
3. **Monitor Resources**: Watch memory usage in complex operations
4. **Use Firewall**: Block external access to port 6688

## Performance Considerations

### Response Times

Typical response times:
- `get_scene_info()`: 10-50ms
- `get_object_info()`: 5-20ms
- `execute_blender_code()`: 50-1000ms (depends on code complexity)
- `get_viewport_screenshot()`: 100-500ms (depends on scene complexity)
- `check_connection_status()`: 5-15ms

### Optimization Tips

1. **Batch Operations**: Group related code in single `execute_blender_code()` calls
2. **Efficient Queries**: Use `get_object_info()` for specific objects instead of full scene dumps
3. **Screenshot Sizing**: Use appropriate `max_size` for your needs
4. **Connection Reuse**: MCP server maintains persistent connections

### Memory Management

- **Automatic Cleanup**: Screenshot files are automatically deleted
- **Connection Pooling**: Single connection reused for multiple requests
- **Memory Monitoring**: Available through `check_connection_status()`

### Concurrency

- **Thread Safe**: Multiple requests handled safely
- **UUID Files**: Unique filenames prevent conflicts
- **Connection Limits**: Service handles reasonable concurrent load

## Versioning

### API Compatibility

The API follows semantic versioning:
- **Major Version**: Breaking changes to tool interfaces
- **Minor Version**: New tools or enhanced functionality
- **Patch Version**: Bug fixes and performance improvements

### Current Version: 1.0.0

**Supported Blender Versions**: 4.4.3+  
**MCP Protocol Version**: 1.0.0  
**Python Version**: 3.10+

### Backward Compatibility

- **Tool Signatures**: Parameter names and types remain stable
- **Return Formats**: Response structure maintained across patch versions
- **Error Handling**: Error format consistency maintained

## Migration Guide

### From BlenderAutoMCP

Tool mapping for migration:

| BlenderAutoMCP | blender-remote | Notes |
|----------------|----------------|-------|
| `get_scene_info()` | `get_scene_info()` | Same functionality |
| `execute_code()` | `execute_blender_code()` | Same functionality |
| `get_viewport_screenshot()` | `get_viewport_screenshot()` | Enhanced with UUID files |
| `get_object_info()` | `get_object_info()` | Same functionality |

### From Direct Socket Connection

**Before (Direct Socket)**:
```python
import socket, json
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('127.0.0.1', 6688))
request = {"type": "get_scene_info", "params": {}}
sock.send(json.dumps(request).encode())
response = json.loads(sock.recv(4096).decode())
sock.close()
```

**After (MCP)**:
```bash
# Just use the MCP tool - connection handled automatically
uvx blender-remote
```

## Examples and Tutorials

### Complete Scene Creation

```python
# Create a complete scene with the MCP server
scene_code = """
import bpy
import bmesh
from mathutils import Vector

# Clear existing scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create ground plane
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "Ground"

# Create main object - a house
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
house = bpy.context.active_object
house.name = "House"
house.scale = (2, 2, 1)

# Create roof
bpy.ops.mesh.primitive_cone_add(location=(0, 0, 2.5))
roof = bpy.context.active_object
roof.name = "Roof"
roof.scale = (2.5, 2.5, 1)

# Add camera
bpy.ops.object.camera_add(location=(8, -8, 5))
camera = bpy.context.active_object
camera.rotation_euler = (1.1, 0, 0.8)
bpy.context.scene.camera = camera

# Add lighting
bpy.ops.object.light_add(type='SUN', location=(4, 4, 8))
sun = bpy.context.active_object
sun.data.energy = 5.0

# Create materials
# House material
house_mat = bpy.data.materials.new(name="HouseMaterial")
house_mat.use_nodes = True
house_mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.8, 0.6, 0.4, 1.0)
house.data.materials.append(house_mat)

# Roof material
roof_mat = bpy.data.materials.new(name="RoofMaterial")
roof_mat.use_nodes = True
roof_mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.6, 0.2, 0.2, 1.0)
roof.data.materials.append(roof_mat)

print("Scene created successfully!")
"""

# Execute the code
result = execute_blender_code(scene_code)
print(result["output"])

# Take a screenshot
screenshot = get_viewport_screenshot(max_size=1200)
print(f"Screenshot captured: {screenshot['result']['dimensions']}")
```

### Advanced Object Analysis

```python
# Get detailed analysis of all objects
scene = get_scene_info()
for obj in scene["result"]["objects"]:
    detail = get_object_info(obj["name"])
    print(f"{obj['name']} ({obj['type']}): {detail['result']['dimensions']}")
```

---

**For more examples, see the [examples directory](../examples/) and [usage documentation](mcp-server.md).**