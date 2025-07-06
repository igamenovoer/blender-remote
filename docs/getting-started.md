# Getting Started

This guide will walk you through your first remote Blender session using Blender Remote.

## Prerequisites

Before starting, ensure you have:

- ✅ [Installed Blender Remote](installation.md)
- ✅ Installed the Blender add-on
- ✅ Blender running with the add-on enabled

## Your First Remote Session

### Step 1: Start Blender and the Service

1. Launch Blender
2. Ensure the Blender Remote add-on is enabled
3. In the add-on preferences, click **Start Service**
4. You should see a confirmation message that the service is listening

### Step 2: Connect from Python

Create a new Python file (`my_first_session.py`) and add:

```python
import blender_remote

# Connect to the running Blender instance
client = blender_remote.connect("localhost", 5555)
print("Connected to Blender!")

# Your first command: clear the default scene
client.clear_scene()

# Create a simple cube
cube = client.create_primitive("cube", location=(0, 0, 0))
print(f"Created cube: {cube}")

# Set up basic lighting
light = client.create_light("SUN", location=(4, 4, 4))

# Position the camera
client.set_camera_location((7, -7, 5))
client.set_camera_target((0, 0, 0))

# Render the scene
output_path = "my_first_render.png"
client.render(output_path)
print(f"Rendered scene to: {output_path}")

# Disconnect
client.disconnect()
print("Session complete!")
```

### Step 3: Run Your Script

```bash
python my_first_session.py
```

You should see output like:
```
Connected to Blender!
Created cube: <Cube object reference>
Rendered scene to: my_first_render.png
Session complete!
```

## Common Operations

### Scene Management

```python
# Clear the entire scene
client.clear_scene()

# Save the current file
client.save_file("my_scene.blend")

# Open a different file
client.open_file("existing_scene.blend")
```

### Object Creation

```python
# Create primitives
cube = client.create_primitive("cube", location=(0, 0, 0))
sphere = client.create_primitive("sphere", location=(2, 0, 0), scale=(1.5, 1.5, 1.5))
cylinder = client.create_primitive("cylinder", location=(-2, 0, 0))

# Create with custom properties
torus = client.create_primitive(
    "torus",
    location=(0, 2, 0),
    rotation=(0.5, 0, 0),
    scale=(2, 2, 2)
)
```

### Materials and Textures

```python
# Create a material
material = client.create_material("MyMaterial")

# Set material properties
client.set_material_property(material, "base_color", (0.8, 0.2, 0.2, 1.0))
client.set_material_property(material, "metallic", 0.5)
client.set_material_property(material, "roughness", 0.3)

# Apply material to object
client.assign_material(cube, material)
```

### Camera and Rendering

```python
# Camera positioning
client.set_camera_location((10, -10, 8))
client.set_camera_rotation((1.1, 0, 0.785))

# Camera targeting (look at a point)
client.set_camera_target((0, 0, 1))

# Render settings
client.set_render_resolution(1920, 1080)
client.set_render_samples(128)
client.set_render_engine("CYCLES")

# Render current frame
client.render("output.png")

# Render animation
client.render_animation("animation_frames/")
```

### Lighting

```python
# Create different light types
sun_light = client.create_light("SUN", location=(5, 5, 10))
point_light = client.create_light("POINT", location=(-3, 2, 4))
spot_light = client.create_light("SPOT", location=(0, -5, 3))

# Adjust light properties
client.set_light_power(sun_light, 10.0)
client.set_light_color(point_light, (1.0, 0.8, 0.6))
```

## Using the CLI

For quick operations, use the command-line interface:

```bash
# Check connection status
blender-remote status

# Execute arbitrary Python code
blender-remote exec "bpy.ops.mesh.primitive_cube_add()"

# Render current scene
blender-remote render --output my_render.png

# Get help
blender-remote --help
```

## Advanced Example: Procedural Scene

Here's a more complex example that creates a procedural scene:

```python
import blender_remote
import math

client = blender_remote.connect("localhost", 5555)

# Clear scene
client.clear_scene()

# Create a grid of cubes with varying heights
for x in range(-5, 6):
    for y in range(-5, 6):
        # Calculate height based on distance from center
        distance = math.sqrt(x*x + y*y)
        height = max(0.1, 3 - distance * 0.3)
        
        # Create cube
        cube = client.create_primitive(
            "cube",
            location=(x * 2, y * 2, height / 2),
            scale=(0.8, 0.8, height)
        )
        
        # Color based on height
        if distance < 3:
            color = (1.0, 0.5, 0.2, 1.0)  # Orange
        elif distance < 5:
            color = (0.2, 0.8, 0.2, 1.0)  # Green
        else:
            color = (0.2, 0.2, 0.8, 1.0)  # Blue
        
        # Create and apply material
        material = client.create_material(f"Material_{x}_{y}")
        client.set_material_property(material, "base_color", color)
        client.assign_material(cube, material)

# Set up lighting and camera
client.create_light("SUN", location=(10, 10, 15))
client.set_camera_location((15, -15, 12))
client.set_camera_target((0, 0, 2))

# Render
client.set_render_resolution(1920, 1080)
client.render("procedural_scene.png")

client.disconnect()
print("Procedural scene created and rendered!")
```

## Error Handling

Always include proper error handling in your scripts:

```python
import blender_remote

try:
    client = blender_remote.connect("localhost", 5555, timeout=10)
    
    # Your operations here
    result = client.create_primitive("cube")
    
except blender_remote.ConnectionError as e:
    print(f"Failed to connect to Blender: {e}")
except blender_remote.BlenderError as e:
    print(f"Blender operation failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
finally:
    if 'client' in locals():
        client.disconnect()
```

## Next Steps

Now that you've completed your first session:

1. **Explore the [API Reference](api-reference.md)** - Learn about all available commands
2. **Check out [CLI Tools](cli.md)** - Master the command-line interface
3. **Read [Development Guide](development.md)** - Contribute to the project
4. **Browse [Blender Add-on](blender-addon.md)** - Understand the server-side implementation

## Tips and Best Practices

### Performance
- Use batch operations when possible
- Minimize the number of round-trips for better performance
- Consider using async operations for complex scenes

### Debugging
- Enable verbose logging to troubleshoot issues
- Use the Blender console to see server-side errors
- Test operations manually in Blender first

### Security
- Only connect to trusted Blender instances
- Use SSH tunneling for remote connections over the internet
- Consider authentication for production deployments