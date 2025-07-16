# Python API Reference

Control Blender programmatically using Python classes that communicate with the BLD Remote MCP service.

## Overview

**Core Classes:**
- **BlenderMCPClient** - Direct communication with Blender service
- **BlenderSceneManager** - High-level scene and object management

**Prerequisites:**
- Blender running with BLD_Remote_MCP addon enabled
- Service listening on port 6688 (default)

## Quick Start

```python
from blender_remote.client import BlenderMCPClient
from blender_remote.scene_manager import BlenderSceneManager

# Connect to Blender
client = BlenderMCPClient()
scene_manager = BlenderSceneManager(client)

# Create objects
scene_manager.add_cube(location=(0, 0, 0), name="MyCube")
scene_manager.add_sphere(location=(2, 0, 0), name="MySphere")

# Execute custom Blender code
client.execute_python('''
import bpy
bpy.ops.mesh.primitive_cylinder_add(location=(0, 2, 0))
''')

# Export GLB
glb_data = scene_manager.get_object_as_glb("MyCube")
```

## Core Classes

### BlenderMCPClient

Direct communication with the BLD Remote MCP service.

#### Constructor

```python
from blender_remote.client import BlenderMCPClient

client = BlenderMCPClient(host="127.0.0.1", port=6688, timeout=30.0)
```

**Parameters:**
- `host` (str): Server hostname, default "127.0.0.1"
- `port` (int): Server port, default 6688
- `timeout` (float): Connection timeout in seconds, default 30.0

#### Methods

##### execute_python(code: str) -> str

Execute Python code in Blender's context.

```python
result = client.execute_python('''
import bpy
bpy.ops.mesh.primitive_cube_add(location=(2, 0, 0))
cube = bpy.context.active_object
cube.name = "MyCube"
''')
```

##### get_scene_info() -> dict

Get scene information including objects and properties.

```python
scene_info = client.get_scene_info()
print(f"Objects: {len(scene_info.get('objects', []))}")
```

##### get_object_info(object_name: str) -> dict

Get detailed object information.

```python
obj_info = client.get_object_info("Cube")
print(f"Location: {obj_info.get('location')}")
```

##### test_connection() -> bool

Test connection to service.

```python
if client.test_connection():
    print("Connected to Blender")
```

### BlenderSceneManager

High-level scene and object management.

#### Constructor

```python
from blender_remote.scene_manager import BlenderSceneManager

scene_manager = BlenderSceneManager(client)
```

#### Core Methods

##### Object Creation

```python
# Create primitives
scene_manager.add_cube(location=(0, 0, 0), name="MyCube")
scene_manager.add_sphere(location=(2, 0, 0), name="MySphere")
scene_manager.add_primitive(primitive_type="cylinder", location=(0, 2, 0))

# Delete objects
scene_manager.delete_object("MyCube")
scene_manager.clear_scene()  # Delete all objects
```

##### GLB Export

```python
# Export object as GLB binary data
glb_data = scene_manager.get_object_as_glb_raw("MyCube")

# Export object as trimesh Scene
scene_obj = scene_manager.get_object_as_glb("MyCube")
```

## Error Handling

```python
from blender_remote.exceptions import BlenderConnectionError, BlenderExecutionError

try:
    client = BlenderMCPClient()
    result = client.execute_python("invalid python code")
except BlenderConnectionError:
    print("Cannot connect to Blender service")
except BlenderExecutionError:
    print("Python code execution failed")
```

## Complete Example

```python
from blender_remote.client import BlenderMCPClient
from blender_remote.scene_manager import BlenderSceneManager

# Setup
client = BlenderMCPClient()
scene_manager = BlenderSceneManager(client)

# Clear scene and create objects
scene_manager.clear_scene()
scene_manager.add_cube(location=(0, 0, 0), name="Cube1")
scene_manager.add_sphere(location=(3, 0, 0), name="Sphere1")

# Export GLB
glb_data = scene_manager.get_object_as_glb_raw("Cube1")
with open("output.glb", "wb") as f:
    f.write(glb_data)

print("GLB exported successfully")
```

## Troubleshooting

**Connection refused:**
```bash
# Check if Blender service is running
blender-remote-cli status

# Restart if needed
blender-remote-cli start
```

**Import errors:**
```bash
# Verify installation
pip show blender-remote

# Reinstall if needed
pip install --upgrade blender-remote
```

**Python execution errors:**
- Check Blender console for detailed error messages
- Verify Python syntax in executed code
- Ensure objects exist before referencing them