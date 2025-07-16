# Python Control API Manual

The Python Control API provides a powerful and intuitive way to control Blender programmatically from external Python scripts. This API enables you to automate Blender workflows, integrate Blender into larger pipelines, and build custom tools without directly working in Blender's interface.

## Concept and Architecture

The Python Control API follows a client-server architecture:

```
Your Python Script → Python API → TCP Socket → BLD_Remote_MCP → Blender
```

**Key Benefits:**
- **Remote Control**: Control Blender from any Python environment
- **High-Level Abstractions**: Simplified APIs for common tasks
- **Direct Python Execution**: Run any Blender Python code remotely
- **Robust Error Handling**: Proper exception handling and connection management
- **Asset Management**: Browse and import from Blender asset libraries

## Core Components

### 1. **BlenderMCPClient**
Low-level client for direct communication with Blender. Provides:
- Python code execution in Blender context
- Scene information retrieval
- Object property queries
- Connection management

### 2. **BlenderSceneManager**
High-level API for scene manipulation. Provides:
- Object creation and deletion
- Transform operations (move, scale, rotate)
- Camera and lighting setup
- Rendering and screenshot capture
- GLB/GLTF export functionality

### 3. **BlenderAssetManager**
Asset library management. Provides:
- Asset library browsing
- Collection listing and searching
- Asset importing from libraries
- Catalog navigation

## Prerequisites

1. **Blender Setup:**
   - Blender with BLD_Remote_MCP addon installed and enabled
   - Service running on port 6688 (default)
   
2. **Python Environment:**
   - Python 3.8 or higher
   - `blender-remote` package installed
   
3. **Start Blender Service:**
   ```bash
   blender-remote-cli start
   ```

## Quick Start

### Using Convenience Functions (Recommended)

```python
import blender_remote

# Connect to Blender (simplified)
client = blender_remote.connect_to_blender()
scene_manager = blender_remote.create_scene_manager()
asset_manager = blender_remote.create_asset_manager()

# Create objects
scene_manager.add_cube(location=(0, 0, 0), name="MyCube")
scene_manager.add_sphere(location=(2, 0, 0), name="MySphere")

# Take a screenshot
screenshot_path = scene_manager.take_screenshot(max_size_mb=5)
print(f"Screenshot saved to: {screenshot_path}")
```

### Manual Instantiation

```python
from blender_remote.client import BlenderMCPClient
from blender_remote.scene_manager import BlenderSceneManager
from blender_remote.asset_manager import BlenderAssetManager

# Connect to Blender
client = BlenderMCPClient(host="127.0.0.1", port=6688)
scene_manager = BlenderSceneManager(client)
asset_manager = BlenderAssetManager(client)
```

## API Reference

### Connection Functions

#### blender_remote.connect_to_blender()

Convenience function to create a BlenderMCPClient instance.

```python
import blender_remote

client = blender_remote.connect_to_blender()
if client.test_connection():
    print("Connected successfully!")
```

#### blender_remote.create_scene_manager()

Create a BlenderSceneManager instance with automatic client connection.

```python
scene_manager = blender_remote.create_scene_manager()
```

#### blender_remote.create_asset_manager()

Create a BlenderAssetManager instance with automatic client connection.

```python
asset_manager = blender_remote.create_asset_manager()
```

### BlenderMCPClient

Low-level client for direct Blender communication.

#### Constructor

```python
from blender_remote.client import BlenderMCPClient

client = BlenderMCPClient(host="127.0.0.1", port=6688, timeout=30.0)
```

**Parameters:**
- `host` (str): Server hostname, default "127.0.0.1"
- `port` (int): Server port, default 6688
- `timeout` (float): Connection timeout in seconds, default 30.0

#### Core Methods

##### execute_python(code: str) -> str

Execute Python code in Blender's context.

```python
result = client.execute_python('''
import bpy
# Access any Blender Python API
bpy.ops.mesh.primitive_cube_add(location=(2, 0, 0))
cube = bpy.context.active_object
cube.name = "MyCube"
cube.scale = (2, 2, 2)
print(f"Created {cube.name}")
''')
print(result)  # Output from Blender's console
```

##### get_scene_info() -> dict

Get comprehensive scene information.

```python
scene_info = client.get_scene_info()
print(f"Total objects: {scene_info['object_count']}")
print(f"Mesh objects: {scene_info['mesh_count']}")
print(f"Current frame: {scene_info['current_frame']}")

for obj in scene_info['objects']:
    print(f"- {obj['name']} ({obj['type']}) at {obj['location']}")
```

**Returns:**
```python
{
    'scene_name': str,
    'object_count': int,
    'mesh_count': int,
    'current_frame': int,
    'fps': int,
    'resolution_x': int,
    'resolution_y': int,
    'objects': [
        {
            'name': str,
            'type': str,  # 'MESH', 'CAMERA', 'LIGHT', etc.
            'location': [x, y, z],
            'rotation': [x, y, z],
            'scale': [x, y, z],
            'visible': bool
        },
        ...
    ]
}
```

##### get_object_info(object_name: str) -> dict

Get detailed information about a specific object.

```python
obj_info = client.get_object_info("Cube")
print(f"Vertices: {obj_info.get('vertex_count', 0)}")
print(f"Materials: {obj_info.get('materials', [])}")
```

##### test_connection() -> bool

Test connection to Blender service.

```python
if client.test_connection():
    print("Connected to Blender")
else:
    print("Connection failed")
```

##### get_service_status() -> dict

Get service status and version information.

```python
status = client.get_service_status()
print(f"Blender version: {status['blender_version']}")
print(f"Addon version: {status['addon_version']}")
```

### BlenderSceneManager

High-level API for scene manipulation and rendering.

#### Constructor

```python
from blender_remote.scene_manager import BlenderSceneManager

scene_manager = BlenderSceneManager(client)
```

#### Object Creation Methods

##### add_cube(location=(0,0,0), name=None, size=2)

Create a cube mesh object.

```python
cube = scene_manager.add_cube(
    location=(1, 2, 0),
    name="MyCube",
    size=1.5
)
```

##### add_sphere(location=(0,0,0), name=None, radius=1)

Create a UV sphere mesh object.

```python
sphere = scene_manager.add_sphere(
    location=(3, 0, 0),
    name="MySphere",
    radius=0.8
)
```

##### add_primitive(primitive_type, location=(0,0,0), **kwargs)

Create any Blender primitive object.

```python
# Cylinder
scene_manager.add_primitive(
    "cylinder",
    location=(0, 2, 0),
    radius=0.5,
    depth=2
)

# Torus
scene_manager.add_primitive(
    "torus",
    location=(0, -2, 0),
    major_radius=1,
    minor_radius=0.25
)
```

#### Object Management Methods

##### list_objects(object_type=None) -> list

List objects in the scene, optionally filtered by type.

```python
# List all objects
all_objects = scene_manager.list_objects()

# List only mesh objects
meshes = scene_manager.list_objects(object_type="MESH")

# List cameras
cameras = scene_manager.list_objects(object_type="CAMERA")
```

##### delete_object(object_name: str)

Delete a specific object by name.

```python
scene_manager.delete_object("MyCube")
```

##### clear_scene(keep_defaults=True)

Clear all objects from the scene.

```python
# Keep camera and lights
scene_manager.clear_scene(keep_defaults=True)

# Delete everything
scene_manager.clear_scene(keep_defaults=False)
```

##### move_object(object_name: str, location: tuple)

Move an object to a new location.

```python
scene_manager.move_object("MyCube", (5, 0, 2))
```

##### update_scene_objects(updates: list)

Batch update multiple objects efficiently.

```python
updates = [
    {
        "name": "Cube",
        "location": [2, 0, 0],
        "scale": [1.5, 1.5, 1.5]
    },
    {
        "name": "Sphere",
        "location": [0, 3, 0],
        "rotation": [0, 0, 1.57]  # 90 degrees in radians
    }
]
scene_manager.update_scene_objects(updates)
```

#### Camera and Rendering Methods

##### set_camera_location(location: tuple, look_at=(0,0,0))

Position the camera and point it at a target.

```python
# Position camera and look at origin
scene_manager.set_camera_location(
    location=(7, -7, 5),
    look_at=(0, 0, 0)
)
```

##### take_screenshot(output_path=None, max_size_mb=10) -> str

Capture a screenshot of the viewport.

```python
# Auto-generate filename
screenshot_path = scene_manager.take_screenshot(max_size_mb=5)

# Specific output path
screenshot_path = scene_manager.take_screenshot(
    output_path="/tmp/my_screenshot.png",
    max_size_mb=2
)
```

##### render_image(output_path: str, resolution=(1920, 1080)) -> str

Render the scene to an image file.

```python
# Render at specific resolution
rendered_path = scene_manager.render_image(
    output_path="/tmp/render.png",
    resolution=(1920, 1080)
)

# Render at 4K
rendered_path = scene_manager.render_image(
    output_path="/tmp/render_4k.png",
    resolution=(3840, 2160)
)
```

#### Export Methods

##### get_object_as_glb(object_name: str) -> trimesh.Scene

Export object as GLB and return as trimesh Scene object.

```python
import trimesh

scene = scene_manager.get_object_as_glb("MyCube")
print(f"Exported scene has {len(scene.geometry)} meshes")

# Save to file
scene.export("output.glb")
```

##### get_object_as_glb_raw(object_name: str) -> bytes

Export object as GLB binary data.

```python
glb_data = scene_manager.get_object_as_glb_raw("MyCube")

# Save to file
with open("output.glb", "wb") as f:
    f.write(glb_data)
```

##### export_scene_as_glb(output_path: str, selected_only=False)

Export entire scene or selected objects to GLB file.

```python
# Export entire scene
scene_manager.export_scene_as_glb("/tmp/full_scene.glb")

# Export only selected objects
scene_manager.export_scene_as_glb(
    "/tmp/selected.glb",
    selected_only=True
)
```

### BlenderAssetManager

Manage and import assets from Blender asset libraries.

#### Constructor

```python
from blender_remote.asset_manager import BlenderAssetManager

asset_manager = BlenderAssetManager(client)
```

#### Library Management Methods

##### list_asset_libraries() -> list

List all configured asset libraries.

```python
libraries = asset_manager.list_asset_libraries()
for lib in libraries:
    print(f"Library: {lib['name']}")
    print(f"  Path: {lib['path']}")
    print(f"  Type: {lib['type']}")
```

##### validate_library(library_name: str) -> dict

Validate that a library exists and is accessible.

```python
validation = asset_manager.validate_library("Characters")
if validation['valid']:
    print(f"Library has {validation['blend_file_count']} blend files")
else:
    print(f"Error: {validation['error']}")
```

#### Browsing Methods

##### browse_library_catalogs(library_name: str) -> dict

Browse the catalog structure of a library.

```python
catalogs = asset_manager.browse_library_catalogs("Characters")
for cat_id, cat_info in catalogs.items():
    print(f"Catalog: {cat_info['path']}")
    if cat_info['children']:
        print(f"  Children: {cat_info['children']}")
```

##### list_library_blend_files(library_name: str) -> list

List all blend files in a library.

```python
blend_files = asset_manager.list_library_blend_files("Characters")
for blend_file in blend_files:
    print(f"Blend file: {blend_file}")
```

##### list_blend_file_collections(library_name: str, blend_file: str) -> list

List collections within a specific blend file.

```python
collections = asset_manager.list_blend_file_collections(
    "Characters",
    "hero_character.blend"
)
for collection in collections:
    print(f"Collection: {collection}")
```

##### search_collections(library_name: str, search_term: str) -> list

Search for collections by name across all blend files.

```python
results = asset_manager.search_collections("Characters", "hero")
for result in results:
    print(f"Found: {result['collection']} in {result['blend_file']}")
```

#### Import Methods

##### import_collection(library_name: str, blend_file: str, collection_name: str) -> dict

Import a collection from an asset library.

```python
result = asset_manager.import_collection(
    library_name="Characters",
    blend_file="hero_character.blend",
    collection_name="HeroCharacter"
)

if result['success']:
    print(f"Imported {result['imported_objects']} objects")
    print(f"Collection: {result['collection_name']}")
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

## Complete Examples

### Example 1: Basic Scene Creation and Rendering

```python
import blender_remote

# Connect to Blender
client = blender_remote.connect_to_blender()
scene_manager = blender_remote.create_scene_manager()

try:
    # Test connection
    if not client.test_connection():
        print("Failed to connect to Blender")
        exit(1)
    
    # Clear scene and create objects
    scene_manager.clear_scene(keep_defaults=True)
    
    # Create a scene with primitives
    scene_manager.add_cube(location=(0, 0, 0), name="CenterCube")
    scene_manager.add_sphere(location=(3, 0, 0), name="RightSphere")
    scene_manager.add_primitive("cylinder", location=(-3, 0, 0))
    
    # Position camera
    scene_manager.set_camera_location(
        location=(7, -7, 5),
        look_at=(0, 0, 0)
    )
    
    # Take a screenshot
    screenshot = scene_manager.take_screenshot(max_size_mb=5)
    print(f"Screenshot saved: {screenshot}")
    
    # Render at HD resolution
    render = scene_manager.render_image(
        output_path="/tmp/my_render.png",
        resolution=(1920, 1080)
    )
    print(f"Render complete: {render}")
    
except Exception as e:
    print(f"Error: {e}")
```

### Example 2: Asset Library Import

```python
import blender_remote

# Connect
client = blender_remote.connect_to_blender()
asset_manager = blender_remote.create_asset_manager()
scene_manager = blender_remote.create_scene_manager()

# List available libraries
libraries = asset_manager.list_asset_libraries()
print("Available Asset Libraries:")
for lib in libraries:
    print(f"  - {lib['name']}: {lib['path']}")

# Browse a specific library
library_name = "Characters"  # Replace with your library name
if asset_manager.validate_library(library_name)['valid']:
    # Search for collections
    results = asset_manager.search_collections(library_name, "hero")
    
    if results:
        # Import the first result
        first = results[0]
        import_result = asset_manager.import_collection(
            library_name=library_name,
            blend_file=first['blend_file'],
            collection_name=first['collection']
        )
        
        if import_result['success']:
            print(f"Imported {import_result['imported_objects']} objects")
            
            # Position camera to view imported objects
            scene_manager.set_camera_location(
                location=(10, -10, 8),
                look_at=(0, 0, 1)
            )
            
            # Take screenshot of imported assets
            screenshot = scene_manager.take_screenshot()
            print(f"Screenshot: {screenshot}")
```

### Example 3: Batch Operations and Animation

```python
import blender_remote
import math

# Connect
client = blender_remote.connect_to_blender()
scene_manager = blender_remote.create_scene_manager()

# Create multiple objects in a circle
scene_manager.clear_scene(keep_defaults=True)

num_objects = 8
radius = 5

for i in range(num_objects):
    angle = (2 * math.pi * i) / num_objects
    x = radius * math.cos(angle)
    y = radius * math.sin(angle)
    
    # Alternate between cubes and spheres
    if i % 2 == 0:
        scene_manager.add_cube(
            location=(x, y, 0),
            name=f"Cube_{i}",
            size=0.8
        )
    else:
        scene_manager.add_sphere(
            location=(x, y, 0),
            name=f"Sphere_{i}",
            radius=0.5
        )

# Batch update - lift every other object
updates = []
for i in range(0, num_objects, 2):
    obj_name = f"Cube_{i}" if i % 4 == 0 else f"Sphere_{i}"
    updates.append({
        "name": obj_name,
        "location": [
            radius * math.cos(2 * math.pi * i / num_objects),
            radius * math.sin(2 * math.pi * i / num_objects),
            2  # Lift up
        ],
        "scale": [1.2, 1.2, 1.2]  # Make slightly larger
    })

scene_manager.update_scene_objects(updates)

# Setup camera for nice view
scene_manager.set_camera_location(
    location=(12, -12, 8),
    look_at=(0, 0, 1)
)

# Execute custom lighting setup
client.execute_python('''
import bpy

# Add area light
bpy.ops.object.light_add(type='AREA', location=(0, 0, 10))
light = bpy.context.active_object
light.data.energy = 500
light.data.size = 10

# Set world background
bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = (0.1, 0.1, 0.2, 1.0)
''')

# Render the scene
final_render = scene_manager.render_image(
    output_path="/tmp/circle_of_objects.png",
    resolution=(1920, 1080)
)
print(f"Final render: {final_render}")
```

### Example 4: Custom Python Execution

```python
import blender_remote

client = blender_remote.connect_to_blender()

# Execute complex Blender operations
result = client.execute_python('''
import bpy
import bmesh
import math

# Create a parametric spiral
verts = []
for i in range(100):
    t = i * 0.1
    x = math.cos(t) * (1 + t * 0.1)
    y = math.sin(t) * (1 + t * 0.1)
    z = t * 0.2
    verts.append((x, y, z))

# Create mesh
mesh = bpy.data.meshes.new("Spiral")
obj = bpy.data.objects.new("Spiral", mesh)
bpy.context.collection.objects.link(obj)

# Create mesh from verts
mesh.from_pydata(verts, [], [])
mesh.update()

# Add material
mat = bpy.data.materials.new("SpiralMat")
mat.use_nodes = True
mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.5, 0.8, 1.0, 1.0)
obj.data.materials.append(mat)

print(f"Created spiral with {len(verts)} vertices")
''')

print(result)
```

## Best Practices

### 1. Connection Management

```python
import blender_remote
from blender_remote.exceptions import BlenderConnectionError

def safe_connect():
    try:
        client = blender_remote.connect_to_blender()
        if not client.test_connection():
            raise BlenderConnectionError("Connection test failed")
        return client
    except BlenderConnectionError as e:
        print(f"Failed to connect: {e}")
        # Attempt to start service
        import subprocess
        subprocess.run(["blender-remote-cli", "start"])
        # Retry connection
        return blender_remote.connect_to_blender()
```

### 2. Error Recovery

```python
def safe_scene_operation(scene_manager, operation):
    try:
        # Store current scene state
        original_objects = scene_manager.list_objects()
        
        # Perform operation
        result = operation()
        
        return result
    except Exception as e:
        print(f"Operation failed: {e}")
        # Could implement rollback here if needed
        raise
```

### 3. Batch Operations

For better performance, use batch operations when updating multiple objects:

```python
# Inefficient - multiple round trips
for obj in objects:
    scene_manager.move_object(obj['name'], new_location)

# Efficient - single batch update
updates = [{'name': obj['name'], 'location': new_location} for obj in objects]
scene_manager.update_scene_objects(updates)
```

### 4. Resource Management

```python
# Clean up large exports
glb_data = scene_manager.get_object_as_glb_raw("LargeModel")
try:
    with open("output.glb", "wb") as f:
        f.write(glb_data)
finally:
    # Free memory
    del glb_data
```

## Troubleshooting

### Connection Issues

**Connection refused:**
```bash
# Check if Blender service is running
blender-remote-cli status

# Start or restart service
blender-remote-cli start

# Check if port is in use
lsof -i :6688  # Linux/macOS
netstat -an | findstr :6688  # Windows
```

**Import errors:**
```bash
# Verify installation
pip show blender-remote

# Reinstall if needed
pip install --upgrade blender-remote

# For development installation
pip install -e .
```

### Common Errors and Solutions

1. **"Object not found"**
   - Verify object name is correct (case-sensitive)
   - Use `scene_manager.list_objects()` to see available objects
   - Check if object was deleted in Blender UI

2. **"Python execution failed"**
   - Check Blender console for detailed error messages
   - Verify Python syntax in executed code
   - Ensure required modules are imported
   - Check Blender Python API compatibility

3. **"Timeout error"**
   - Increase timeout for long operations: `BlenderMCPClient(timeout=60.0)`
   - Break large operations into smaller chunks
   - Check if Blender is responding (not frozen)

4. **"Asset library not found"**
   - Verify library is configured in Blender preferences
   - Check library path exists and is accessible
   - Use `asset_manager.list_asset_libraries()` to see available libraries

### Debug Mode

Enable debug logging for detailed information:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Now all API calls will print debug information
client = blender_remote.connect_to_blender()
```

## Performance Tips

1. **Minimize execute_python() calls** - Batch operations when possible
2. **Use specific methods** - `add_cube()` is faster than `execute_python()` for simple tasks
3. **Cache scene information** - Don't repeatedly call `get_scene_info()` 
4. **Use appropriate export formats** - GLB is more efficient than OBJ for complex scenes
5. **Manage viewport updates** - Disable viewport updates for batch operations

## Integration Examples

### Flask Web Service

```python
from flask import Flask, jsonify
import blender_remote

app = Flask(__name__)
scene_manager = blender_remote.create_scene_manager()

@app.route('/api/create-cube')
def create_cube():
    cube = scene_manager.add_cube(name="APICube")
    return jsonify({"success": True, "object": cube})

@app.route('/api/render')
def render():
    path = scene_manager.render_image("/tmp/api_render.png")
    return jsonify({"success": True, "path": path})
```

### Jupyter Notebook

```python
# In Jupyter notebook
import blender_remote
from IPython.display import Image

scene = blender_remote.create_scene_manager()

# Create scene and render
scene.clear_scene()
scene.add_cube(location=(0, 0, 0))
scene.add_sphere(location=(2, 0, 0))

# Display render in notebook
render_path = scene.render_image("/tmp/notebook_render.png")
Image(render_path)
```