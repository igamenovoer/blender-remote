# Python Control API Reference

The Python Control API provides a high-level, pythonic interface for controlling Blender programmatically. Built on top of the BLD Remote MCP service, it offers convenient classes and methods for scene management, asset handling, and Blender automation.

## Overview

The Python Control API consists of three main components:

1. **BlenderMCPClient** - Direct client for BLD Remote MCP service communication
2. **BlenderSceneManager** - High-level scene manipulation and object management
3. **BlenderAssetManager** - Asset library browsing and import functionality

## Quick Start

### Installation

```bash
# Install from PyPI
pip install blender-remote

# Or install from source with pixi
git clone https://github.com/igamenovoer/blender-remote.git
cd blender-remote
pixi install
```

### Basic Usage

```python
import blender_remote

# Connect to Blender (make sure BLD Remote MCP service is running)
client = blender_remote.connect_to_blender(port=6688)

# Create scene manager
scene_manager = blender_remote.create_scene_manager(client)

# Add objects to scene
cube_name = scene_manager.add_cube(location=(0, 0, 0), size=2.0)
sphere_name = scene_manager.add_sphere(location=(3, 0, 0), radius=1.0)

# Set camera and render
scene_manager.set_camera_location(location=(7, -7, 5), target=(0, 0, 0))
scene_manager.render_image("/tmp/render.png", resolution=(1920, 1080))
```

## Core Classes

### BlenderMCPClient

Direct client for communicating with the BLD Remote MCP service running inside Blender.

#### Constructor

```python
client = blender_remote.BlenderMCPClient(host="localhost", port=6688, timeout=30.0)
```

**Parameters:**
- `host` (str, optional): Server hostname, defaults to "localhost"
- `port` (int, optional): Server port, defaults to 6688 (BLD Remote MCP)
- `timeout` (float, optional): Connection timeout in seconds, defaults to 30.0

#### Methods

##### execute_python(code: str) -> str

Execute Python code in Blender's context.

```python
result = client.execute_python("""
import bpy
bpy.ops.mesh.primitive_cube_add(location=(2, 0, 0))
cube = bpy.context.active_object
cube.name = "MyCube"
""")
print(result)  # "Code executed successfully"
```

##### get_scene_info() -> Dict[str, Any]

Get comprehensive scene information.

```python
scene_info = client.get_scene_info()
print(f"Scene has {len(scene_info['objects'])} objects")
```

##### get_object_info(object_name: str) -> Dict[str, Any]

Get detailed information about a specific object.

```python
obj_info = client.get_object_info("Cube")
print(f"Location: {obj_info['location']}")
```

##### take_screenshot(filepath: str, max_size: int = 1920, format: str = "png") -> Dict[str, Any]

Capture viewport screenshot.

```python
screenshot_info = client.take_screenshot("/tmp/screenshot.png", max_size=1920)
print(f"Screenshot saved: {screenshot_info['filepath']}")
```

##### test_connection() -> bool

Test connection to BLD Remote MCP service.

```python
if client.test_connection():
    print("Successfully connected to Blender")
else:
    print("Connection failed")
```

### BlenderSceneManager

High-level interface for scene manipulation and object management.

#### Constructor

```python
scene_manager = blender_remote.BlenderSceneManager(client)
# Or use convenience function
scene_manager = blender_remote.create_scene_manager(port=6688)
```

#### Scene Information

##### get_scene_info() -> SceneInfo

Get structured scene information as a SceneInfo object.

```python
scene_info = scene_manager.get_scene_info()
print(f"Scene has {scene_info.object_count} objects")
print(f"Mesh objects: {len(scene_info.mesh_objects)}")
```

##### list_objects(object_type: str = None) -> List[SceneObject]

List objects in the scene, optionally filtered by type.

```python
# List all objects
all_objects = scene_manager.list_objects()

# List only mesh objects
mesh_objects = scene_manager.list_objects("MESH")

# List only cameras
cameras = scene_manager.list_objects("CAMERA")
```

##### get_objects_top_level() -> List[SceneObject]

Get top-level objects (directly under Scene Collection).

```python
top_objects = scene_manager.get_objects_top_level()
for obj in top_objects:
    print(f"{obj.name} at {obj.location}")
```

#### Object Creation

##### add_primitive(primitive_type: str, location=None, rotation=None, scale=None, name=None) -> str

Add a primitive object to the scene.

```python
cube_name = scene_manager.add_primitive(
    "cube", 
    location=(0, 0, 0), 
    rotation=(0, 0, 0), 
    scale=(1, 1, 1),
    name="MyCube"
)
```

##### add_cube(location=None, size=2.0, name=None) -> str

Add a cube to the scene.

```python
cube_name = scene_manager.add_cube(
    location=(2, 0, 0), 
    size=1.5, 
    name="BigCube"
)
```

##### add_sphere(location=None, radius=1.0, name=None) -> str

Add a sphere to the scene.

```python
sphere_name = scene_manager.add_sphere(
    location=(-2, 0, 0), 
    radius=0.8, 
    name="SmallSphere"
)
```

##### add_cylinder(location=None, radius=1.0, depth=2.0, name=None) -> str

Add a cylinder to the scene.

```python
cylinder_name = scene_manager.add_cylinder(
    location=(0, 2, 0), 
    radius=0.5, 
    depth=3.0, 
    name="TallCylinder"
)
```

#### Object Manipulation

##### move_object(object_name: str, location) -> bool

Move an object to a new location.

```python
success = scene_manager.move_object("Cube", location=(3, 3, 1))
```

##### delete_object(object_name: str) -> bool

Delete an object by name.

```python
success = scene_manager.delete_object("Cube")
```

##### update_scene_objects(scene_objects: List[SceneObject]) -> Dict[str, bool]

Update multiple objects in batch.

```python
objects = scene_manager.list_objects("MESH")
for obj in objects:
    obj.location = obj.location + [0, 0, 1]  # Move all up by 1 unit
    obj.scale = [0.5, 0.5, 0.5]  # Scale down

update_results = scene_manager.update_scene_objects(objects)
```

#### Camera and Rendering

##### set_camera_location(location, target=None) -> bool

Set camera position and target.

```python
scene_manager.set_camera_location(
    location=(7, -7, 5), 
    target=(0, 0, 0)
)
```

##### render_image(filepath: str, resolution=None) -> bool

Render the scene to an image file.

```python
success = scene_manager.render_image(
    "/tmp/render.png", 
    resolution=(1920, 1080)
)
```

##### take_screenshot(filepath: str, max_size=1920, format="png") -> Dict[str, Any]

Capture viewport screenshot.

```python
screenshot_info = scene_manager.take_screenshot("/tmp/viewport.png")
```

#### Scene Management

##### clear_scene(keep_camera=True, keep_light=True) -> bool

Clear all objects from the scene.

```python
scene_manager.clear_scene(keep_camera=True, keep_light=True)
```

#### 3D Export

##### get_object_as_glb(object_name: str, with_material=True) -> trimesh.Scene

Export object as GLB and load as trimesh Scene.

```python
glb_scene = scene_manager.get_object_as_glb("Cube", with_material=True)
print(f"GLB scene has {len(glb_scene.geometry)} geometries")
```

##### get_object_as_glb_raw(object_name: str, with_material=True) -> bytes

Export object as GLB and return raw bytes.

```python
glb_bytes = scene_manager.get_object_as_glb_raw("Cube")
with open("/tmp/cube.glb", "wb") as f:
    f.write(glb_bytes)
```

### BlenderAssetManager

Interface for browsing and importing from Blender asset libraries.

#### Constructor

```python
asset_manager = blender_remote.BlenderAssetManager(client)
# Or use convenience function
asset_manager = blender_remote.create_asset_manager(port=6688)
```

#### Library Management

##### list_asset_libraries() -> List[AssetLibrary]

List all configured asset libraries.

```python
libraries = asset_manager.list_asset_libraries()
for lib in libraries:
    print(f"Library: {lib.name} at {lib.path}")
    print(f"Valid: {lib.is_valid}")
```

##### get_asset_library(library_name: str) -> Optional[AssetLibrary]

Get a specific asset library by name.

```python
lib = asset_manager.get_asset_library("My Library")
if lib:
    print(f"Found library at {lib.path}")
```

##### validate_library(library_name: str) -> Dict[str, Any]

Validate an asset library and return detailed status.

```python
validation = asset_manager.validate_library("My Library")
print(f"Valid: {validation['valid']}")
print(f"Blend files: {validation['blend_count']}")
print(f"Collections: {validation['collection_count']}")
```

#### Collection Management

##### list_library_collections(library_name: str) -> List[AssetCollection]

List all collections in a library.

```python
collections = asset_manager.list_library_collections("My Library")
for coll in collections:
    print(f"Collection: {coll.name} in {coll.file_path}")
```

##### search_collections(library_name: str, search_term: str) -> List[AssetCollection]

Search for collections by name.

```python
results = asset_manager.search_collections("My Library", "chair")
for coll in results:
    print(f"Found: {coll.name}")
```

##### import_collection(library_name: str, file_path: str, collection_name: str) -> bool

Import a collection from an asset library.

```python
success = asset_manager.import_collection(
    "My Library", 
    "furniture/chairs.blend", 
    "OfficeChair"
)
```

#### Catalog Management

##### list_library_catalogs(library_name: str) -> Dict[str, Any]

List all catalogs (directories and blend files) in a library.

```python
catalogs = asset_manager.list_library_catalogs("My Library")
print(f"Directories: {catalogs['directories']}")
print(f"Blend files: {catalogs['blend_files']}")
```

##### list_blend_files(library_name: str, subdirectory="") -> List[str]

List all blend files in a library or subdirectory.

```python
blend_files = asset_manager.list_blend_files("My Library", "furniture")
for file in blend_files:
    print(f"Blend file: {file}")
```

## Data Types

The API uses attrs-based data classes for structured data representation.

### SceneObject

Represents a Blender scene object with its properties.

```python
@attrs.define(kw_only=True, eq=False)
class SceneObject:
    name: str
    type: str
    location: np.ndarray = factory(lambda: np.zeros(3))
    rotation: np.ndarray = factory(lambda: np.array([1, 0, 0, 0]))  # quaternion
    scale: np.ndarray = factory(lambda: np.ones(3))
    visible: bool = True
    
    @property
    def world_transform(self) -> np.ndarray:
        """Get 4x4 world transformation matrix."""
        
    def set_world_transform(self, transform: np.ndarray):
        """Set object properties from 4x4 transformation matrix."""
        
    def copy(self) -> 'SceneObject':
        """Create a copy of this object."""
```

### AssetLibrary

Represents a Blender asset library configuration.

```python
@attrs.define(kw_only=True, eq=False)
class AssetLibrary:
    name: str
    path: str
    collections: List[str] = factory(list)
    
    @property
    def is_valid(self) -> bool:
        """Check if library path exists."""
```

### AssetCollection

Represents a collection from an asset library.

```python
@attrs.define(kw_only=True, eq=False)
class AssetCollection:
    name: str
    library_name: str
    file_path: str
    objects: List[str] = factory(list)
```

### SceneInfo

Comprehensive scene information container.

```python
@attrs.define(kw_only=True, eq=False)
class SceneInfo:
    objects: List[SceneObject] = factory(list)
    materials: List[MaterialSettings] = factory(list)
    camera: Optional[CameraSettings] = None
    render_settings: RenderSettings = factory(RenderSettings)
    collections: List[str] = factory(list)
    
    @property
    def object_count(self) -> int
    
    @property
    def mesh_objects(self) -> List[SceneObject]
    
    def get_object_by_name(self, name: str) -> Optional[SceneObject]
```

## Convenience Functions

### connect_to_blender(host="localhost", port=6688, timeout=30.0) -> BlenderMCPClient

Create a connection to the BLD Remote MCP service.

```python
client = blender_remote.connect_to_blender(port=6688)
```

### create_scene_manager(client=None, **kwargs) -> BlenderSceneManager

Create a scene manager instance.

```python
# With existing client
scene_manager = blender_remote.create_scene_manager(client)

# With auto-created client
scene_manager = blender_remote.create_scene_manager(port=6688)
```

### create_asset_manager(client=None, **kwargs) -> BlenderAssetManager

Create an asset manager instance.

```python
# With existing client
asset_manager = blender_remote.create_asset_manager(client)

# With auto-created client
asset_manager = blender_remote.create_asset_manager(port=6688)
```

## Error Handling

The API provides a comprehensive exception hierarchy:

### BlenderRemoteError

Base exception for all Blender Remote operations.

### BlenderMCPError

Base exception for MCP communication errors.

### BlenderConnectionError

Connection-related errors (network, timeout, etc.).

### BlenderCommandError

Command execution errors (Blender API failures).

### BlenderTimeoutError

Operation timeout errors.

### Example Error Handling

```python
import blender_remote

try:
    client = blender_remote.connect_to_blender(port=6688)
    scene_manager = blender_remote.create_scene_manager(client)
    
    # This might fail if object doesn't exist
    scene_manager.move_object("NonExistentObject", (0, 0, 0))
    
except blender_remote.BlenderConnectionError as e:
    print(f"Connection failed: {e}")
except blender_remote.BlenderCommandError as e:
    print(f"Command failed: {e}")
except blender_remote.BlenderMCPError as e:
    print(f"MCP error: {e}")
```

## Advanced Usage

### Batch Operations

```python
# Create multiple objects efficiently
scene_manager = blender_remote.create_scene_manager(port=6688)

# Clear scene
scene_manager.clear_scene()

# Create objects
objects = []
for i in range(5):
    cube_name = scene_manager.add_cube(
        location=(i * 2, 0, 0), 
        size=1.0, 
        name=f"Cube_{i}"
    )
    objects.append(cube_name)

# Get all objects and modify them
scene_objects = scene_manager.list_objects("MESH")
for obj in scene_objects:
    obj.location = obj.location + [0, 0, 1]  # Move up
    obj.scale = [0.8, 0.8, 0.8]  # Scale down

# Apply changes in batch
update_results = scene_manager.update_scene_objects(scene_objects)
```

### Asset Pipeline Integration

```python
# Complete asset import and scene setup
asset_manager = blender_remote.create_asset_manager(port=6688)
scene_manager = blender_remote.create_scene_manager(asset_manager.client)

# List available libraries
libraries = asset_manager.list_asset_libraries()
if libraries:
    lib = libraries[0]
    print(f"Using library: {lib.name}")
    
    # Search for specific assets
    chairs = asset_manager.search_collections(lib.name, "chair")
    if chairs:
        chair = chairs[0]
        print(f"Importing chair: {chair.name}")
        
        # Import asset
        success = asset_manager.import_collection(
            lib.name, 
            chair.file_path, 
            chair.name
        )
        
        if success:
            # Position camera for good view
            scene_manager.set_camera_location(
                location=(5, -5, 3), 
                target=(0, 0, 0)
            )
            
            # Render scene
            scene_manager.render_image("/tmp/chair_render.png")
```

### Animation Setup

```python
# Create animated scene
scene_manager = blender_remote.create_scene_manager(port=6688)

# Create objects
cube_name = scene_manager.add_cube(location=(0, 0, 0), name="AnimCube")

# Use direct Python code for animation
animation_code = """
import bpy

# Get the cube
cube = bpy.data.objects["AnimCube"]

# Set frame range
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 120

# Animate rotation
cube.rotation_euler = (0, 0, 0)
cube.keyframe_insert(data_path="rotation_euler", frame=1)

cube.rotation_euler = (0, 0, 6.28)  # Full rotation
cube.keyframe_insert(data_path="rotation_euler", frame=120)

# Animate location
cube.location = (0, 0, 0)
cube.keyframe_insert(data_path="location", frame=1)

cube.location = (0, 0, 3)
cube.keyframe_insert(data_path="location", frame=60)

cube.location = (0, 0, 0)
cube.keyframe_insert(data_path="location", frame=120)
"""

# Execute animation setup
scene_manager.client.execute_python(animation_code)

# Render animation frames
for frame in range(1, 121, 10):
    scene_manager.client.execute_python(f"bpy.context.scene.frame_set({frame})")
    scene_manager.render_image(f"/tmp/animation/frame_{frame:04d}.png")
```

## Best Practices

### Connection Management

```python
# Reuse clients for multiple operations
client = blender_remote.connect_to_blender(port=6688)
scene_manager = blender_remote.create_scene_manager(client)
asset_manager = blender_remote.create_asset_manager(client)

# Test connection before operations
if not client.test_connection():
    raise ConnectionError("Cannot connect to Blender")
```

### Error Handling

```python
# Always handle exceptions
try:
    result = scene_manager.add_cube(location=(0, 0, 0))
except blender_remote.BlenderConnectionError:
    print("Connection lost - try restarting Blender")
except blender_remote.BlenderCommandError as e:
    print(f"Command failed: {e}")
```

### Performance Optimization

```python
# Use batch operations when possible
objects = scene_manager.list_objects("MESH")
for obj in objects:
    obj.location = obj.location + [0, 0, 1]
    
# Single batch update instead of individual moves
scene_manager.update_scene_objects(objects)
```

### Memory Management

```python
# Use context managers for resource cleanup
import tempfile
import os

with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
    screenshot_path = tmp.name

try:
    scene_manager.take_screenshot(screenshot_path)
    # Process image...
finally:
    os.unlink(screenshot_path)  # Clean up
```

## Testing

The API includes comprehensive tests that can be run with pixi:

```bash
# Run all Python Control API tests
pixi run python tests/python_control_api/test_integration.py

# Run specific test categories
pixi run python tests/python_control_api/test_basic_connection.py
pixi run python tests/python_control_api/test_scene_operations.py
pixi run python tests/python_control_api/test_asset_operations.py
```

## Troubleshooting

### Common Issues

**Connection Errors:**
- Ensure Blender is running with BLD Remote MCP service
- Check that port 6688 is available: `netstat -tlnp | grep 6688`
- Verify addon is installed and enabled

**Import Errors:**
- Make sure package is installed: `pip install blender-remote`
- For development: `pixi install` in project directory

**Performance Issues:**
- Use batch operations for multiple object updates
- Reuse client connections instead of creating new ones
- Consider using background mode for headless operations

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test connection
client = blender_remote.connect_to_blender(port=6688)
status = client.get_status()
print(f"Connection status: {status}")
```

## Migration Guide

### From Direct Socket Code

**Before:**
```python
import socket, json
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('127.0.0.1', 6688))
command = {"type": "get_scene_info", "params": {}}
sock.send(json.dumps(command).encode())
response = json.loads(sock.recv(4096).decode())
```

**After:**
```python
import blender_remote
client = blender_remote.connect_to_blender(port=6688)
scene_info = client.get_scene_info()
```

### From BlenderAutoMCP

The API is designed to be compatible with BlenderAutoMCP patterns:

```python
# BlenderAutoMCP style
from blender_mcp_client import BlenderMCPClient
client = BlenderMCPClient(port=9876)

# blender-remote style
import blender_remote
client = blender_remote.connect_to_blender(port=6688)
```

## API Reference Summary

### Core Classes
- `BlenderMCPClient` - Direct MCP communication
- `BlenderSceneManager` - Scene manipulation
- `BlenderAssetManager` - Asset management

### Data Types
- `SceneObject` - Object representation
- `AssetLibrary` - Library configuration
- `AssetCollection` - Collection representation
- `SceneInfo` - Scene information container

### Convenience Functions
- `connect_to_blender()` - Create client
- `create_scene_manager()` - Create scene manager
- `create_asset_manager()` - Create asset manager

### Exception Hierarchy
- `BlenderRemoteError` - Base exception
- `BlenderMCPError` - MCP communication errors
- `BlenderConnectionError` - Connection errors
- `BlenderCommandError` - Command execution errors
- `BlenderTimeoutError` - Timeout errors

---

For more examples and advanced usage, see the [examples directory](../examples/) and [integration tests](../tests/python_control_api/).