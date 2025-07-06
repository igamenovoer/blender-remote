# API Reference

Complete reference for the Blender Remote Python API.

## Core Classes

### BlenderConnection

The main interface for connecting to and controlling Blender.

```python
from blender_remote import BlenderConnection

client = BlenderConnection(host="localhost", port=5555)
```

#### Connection Methods

##### `connect(host, port, timeout=10)`
Establish connection to Blender instance.

**Parameters:**
- `host` (str): Blender server hostname or IP
- `port` (int): Port number (default: 5555)
- `timeout` (float): Connection timeout in seconds

**Returns:** `BlenderConnection` instance

**Example:**
```python
client = blender_remote.connect("localhost", 5555)
```

##### `disconnect()`
Close the connection to Blender.

```python
client.disconnect()
```

##### `is_connected()`
Check if connection is active.

**Returns:** `bool` - True if connected

## Scene Management

### Clear and Reset

##### `clear_scene()`
Remove all objects from the scene.

```python
client.clear_scene()
```

##### `reset_scene()`
Reset scene to default state (equivalent to File → New).

```python
client.reset_scene()
```

### File Operations

##### `save_file(filepath)`
Save current Blender file.

**Parameters:**
- `filepath` (str): Path to save the file

```python
client.save_file("my_project.blend")
```

##### `open_file(filepath)`
Open a Blender file.

**Parameters:**
- `filepath` (str): Path to the file to open

```python
client.open_file("existing_project.blend")
```

##### `import_file(filepath, file_type="auto")`
Import external file into current scene.

**Parameters:**
- `filepath` (str): Path to file to import
- `file_type` (str): File type ("obj", "fbx", "gltf", "auto")

```python
client.import_file("model.obj", "obj")
```

## Object Creation

### Primitives

##### `create_primitive(primitive_type, **kwargs)`
Create primitive objects.

**Parameters:**
- `primitive_type` (str): Type of primitive
  - `"cube"`, `"sphere"`, `"cylinder"`, `"cone"`, `"torus"`, `"plane"`
- `location` (tuple): (x, y, z) position
- `rotation` (tuple): (x, y, z) rotation in radians
- `scale` (tuple): (x, y, z) scale factors

**Returns:** Object reference

**Example:**
```python
cube = client.create_primitive(
    "cube",
    location=(0, 0, 1),
    rotation=(0.5, 0, 0),
    scale=(2, 2, 2)
)
```

### Mesh Operations

##### `create_mesh(name, vertices, edges, faces)`
Create custom mesh from geometry data.

**Parameters:**
- `name` (str): Name for the mesh object
- `vertices` (list): List of (x, y, z) vertex coordinates
- `edges` (list): List of (v1, v2) edge definitions
- `faces` (list): List of vertex indices defining faces

**Returns:** Object reference

**Example:**
```python
vertices = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]
faces = [(0, 1, 2, 3)]
quad = client.create_mesh("MyQuad", vertices, [], faces)
```

## Object Manipulation

### Transform Operations

##### `set_location(obj, location)`
Set object location.

**Parameters:**
- `obj`: Object reference
- `location` (tuple): (x, y, z) coordinates

```python
client.set_location(cube, (5, 0, 2))
```

##### `set_rotation(obj, rotation)`
Set object rotation.

**Parameters:**
- `obj`: Object reference
- `rotation` (tuple): (x, y, z) rotation in radians

```python
import math
client.set_rotation(cube, (0, 0, math.pi/4))  # 45° around Z
```

##### `set_scale(obj, scale)`
Set object scale.

**Parameters:**
- `obj`: Object reference
- `scale` (tuple): (x, y, z) scale factors

```python
client.set_scale(cube, (2, 1, 0.5))
```

### Object Properties

##### `get_object_info(obj)`
Get detailed information about an object.

**Returns:** Dictionary with object properties

```python
info = client.get_object_info(cube)
print(f"Location: {info['location']}")
print(f"Rotation: {info['rotation']}")
```

##### `select_object(obj)`
Select an object in Blender.

```python
client.select_object(cube)
```

##### `delete_object(obj)`
Delete an object from the scene.

```python
client.delete_object(cube)
```

## Materials and Shading

### Material Creation

##### `create_material(name)`
Create a new material.

**Parameters:**
- `name` (str): Material name

**Returns:** Material reference

```python
material = client.create_material("MyMaterial")
```

##### `set_material_property(material, property_name, value)`
Set material property.

**Parameters:**
- `material`: Material reference
- `property_name` (str): Property name
- `value`: Property value

**Common Properties:**
- `"base_color"`: (r, g, b, a) tuple
- `"metallic"`: float (0.0-1.0)
- `"roughness"`: float (0.0-1.0)
- `"emission_strength"`: float

```python
client.set_material_property(material, "base_color", (0.8, 0.2, 0.2, 1.0))
client.set_material_property(material, "metallic", 0.5)
client.set_material_property(material, "roughness", 0.3)
```

##### `assign_material(obj, material)`
Assign material to object.

```python
client.assign_material(cube, material)
```

### Texture Management

##### `create_texture(name, image_path)`
Create texture from image file.

**Parameters:**
- `name` (str): Texture name
- `image_path` (str): Path to image file

**Returns:** Texture reference

```python
texture = client.create_texture("WoodTexture", "textures/wood.jpg")
```

## Lighting

### Light Creation

##### `create_light(light_type, **kwargs)`
Create light source.

**Parameters:**
- `light_type` (str): Type of light
  - `"SUN"`, `"POINT"`, `"SPOT"`, `"AREA"`
- `location` (tuple): (x, y, z) position
- `rotation` (tuple): (x, y, z) rotation

**Returns:** Light reference

```python
sun = client.create_light("SUN", location=(5, 5, 10))
point = client.create_light("POINT", location=(2, 2, 3))
```

### Light Properties

##### `set_light_power(light, power)`
Set light strength/power.

**Parameters:**
- `light`: Light reference
- `power` (float): Light power in watts

```python
client.set_light_power(sun, 10.0)
```

##### `set_light_color(light, color)`
Set light color.

**Parameters:**
- `light`: Light reference
- `color` (tuple): (r, g, b) color values

```python
client.set_light_color(point, (1.0, 0.8, 0.6))  # Warm white
```

## Camera Control

### Camera Positioning

##### `set_camera_location(location)`
Position the active camera.

**Parameters:**
- `location` (tuple): (x, y, z) coordinates

```python
client.set_camera_location((10, -10, 8))
```

##### `set_camera_rotation(rotation)`
Set camera rotation.

**Parameters:**
- `rotation` (tuple): (x, y, z) rotation in radians

```python
client.set_camera_rotation((1.1, 0, 0.785))
```

##### `set_camera_target(target)`
Point camera at specific location.

**Parameters:**
- `target` (tuple): (x, y, z) coordinates to look at

```python
client.set_camera_target((0, 0, 0))  # Look at origin
```

### Camera Properties

##### `set_camera_lens(focal_length)`
Set camera focal length.

**Parameters:**
- `focal_length` (float): Focal length in mm

```python
client.set_camera_lens(50.0)  # 50mm lens
```

## Rendering

### Render Settings

##### `set_render_resolution(width, height)`
Set render resolution.

**Parameters:**
- `width` (int): Image width in pixels
- `height` (int): Image height in pixels

```python
client.set_render_resolution(1920, 1080)
```

##### `set_render_engine(engine)`
Set rendering engine.

**Parameters:**
- `engine` (str): Render engine name
  - `"CYCLES"`, `"EEVEE"`, `"WORKBENCH"`

```python
client.set_render_engine("CYCLES")
```

##### `set_render_samples(samples)`
Set render sample count (for Cycles).

**Parameters:**
- `samples` (int): Number of samples

```python
client.set_render_samples(128)
```

### Rendering Operations

##### `render(output_path, frame=None)`
Render current scene.

**Parameters:**
- `output_path` (str): Path for output image
- `frame` (int, optional): Specific frame to render

**Returns:** Path to rendered image

```python
client.render("my_render.png")
client.render("frame_010.png", frame=10)
```

##### `render_animation(output_dir, start_frame=1, end_frame=250)`
Render animation sequence.

**Parameters:**
- `output_dir` (str): Directory for output frames
- `start_frame` (int): First frame to render
- `end_frame` (int): Last frame to render

```python
client.render_animation("animation_frames/", 1, 100)
```

## Animation

### Keyframe Management

##### `set_keyframe(obj, property_name, frame, value)`
Set keyframe for object property.

**Parameters:**
- `obj`: Object reference
- `property_name` (str): Property to animate
- `frame` (int): Frame number
- `value`: Property value

```python
# Animate cube location
client.set_keyframe(cube, "location", 1, (0, 0, 0))
client.set_keyframe(cube, "location", 50, (5, 0, 0))
```

##### `set_frame(frame_number)`
Set current frame.

**Parameters:**
- `frame_number` (int): Frame to set as current

```python
client.set_frame(25)
```

## Error Handling

### Exception Classes

```python
from blender_remote import (
    ConnectionError,
    BlenderError,
    TimeoutError,
    InvalidParameterError
)

try:
    client = blender_remote.connect("localhost", 5555)
    result = client.create_primitive("cube")
except ConnectionError:
    print("Failed to connect to Blender")
except BlenderError as e:
    print(f"Blender operation failed: {e}")
except TimeoutError:
    print("Operation timed out")
except InvalidParameterError as e:
    print(f"Invalid parameter: {e}")
```

## Utility Functions

##### `get_blender_version()`
Get version of connected Blender instance.

**Returns:** Version string

```python
version = client.get_blender_version()
print(f"Blender version: {version}")
```

##### `execute_script(script_code)`
Execute arbitrary Python code in Blender.

**Parameters:**
- `script_code` (str): Python code to execute

```python
client.execute_script("""
import bpy
bpy.ops.mesh.primitive_monkey_add()
""")
```

## Best Practices

### Context Management

Use context managers for automatic cleanup:

```python
with blender_remote.connect("localhost", 5555) as client:
    cube = client.create_primitive("cube")
    client.render("output.png")
# Connection automatically closed
```

### Batch Operations

For better performance, batch operations when possible:

```python
# Instead of individual calls
operations = [
    ("create_primitive", "cube", {"location": (i, 0, 0)})
    for i in range(10)
]
results = client.batch_execute(operations)
```

### Error Recovery

Implement robust error handling:

```python
def safe_render(client, output_path, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.render(output_path)
        except TimeoutError:
            if attempt == max_retries - 1:
                raise
            print(f"Render timeout, retrying... ({attempt + 1}/{max_retries})")
```