# How to Create and Render with a Camera at Specific Location and Orientation

This guide explains how to create a camera at a specific location with a given view direction and up vector, then render an image using Blender's Python API.

## Overview

To create a camera with specific orientation, we need to:
1. Create a camera object
2. Set its location
3. Calculate and set its rotation matrix based on view direction and up vector
4. Set it as the active camera
5. Render the image

## Key Concepts

### Camera Coordinate System
- In Blender, cameras look down their **negative Z-axis**
- The **positive Y-axis** points up by default
- The **positive X-axis** points to the right

### View Direction vs Camera Direction
- The **view direction** is where we want the camera to look
- The **camera direction** is the camera's negative Z-axis
- So camera direction = -view_direction

## Complete Implementation

```python
import bpy
import numpy as np
from mathutils import Vector, Matrix

def create_camera_with_orientation(location, view_direction, up_vector, name="CustomCamera"):
    """
    Create a camera at a specific location with given view direction and up vector.
    
    Args:
        location (Vector or tuple): Camera position in world space
        view_direction (Vector or tuple): Direction the camera should look at
        up_vector (Vector or tuple): Up direction for the camera
        name (str): Name for the camera object
    
    Returns:
        bpy.types.Object: The created camera object
    """
    # Ensure inputs are numpy arrays and normalize using numpy
    location = np.array(location, dtype=np.float64)
    view_direction = np.array(view_direction, dtype=np.float64)
    up_vector = np.array(up_vector, dtype=np.float64)
    
    # Normalize vectors using numpy
    view_direction = view_direction / np.linalg.norm(view_direction)
    up_vector = up_vector / np.linalg.norm(up_vector)
    
    # Create camera data and object
    camera_data = bpy.data.cameras.new(name=name)
    camera_object = bpy.data.objects.new(name, camera_data)
    
    # Add camera to scene
    bpy.context.scene.collection.objects.link(camera_object)
    
    # Set camera location
    camera_object.location = Vector(location)
    
    # Calculate camera orientation using numpy
    # Camera looks down negative Z, so camera Z-axis = -view_direction
    camera_z = -view_direction
    
    # Calculate camera X-axis (right direction): X = up × Z (cross product)
    camera_x = np.cross(up_vector, camera_z)
    camera_x = camera_x / np.linalg.norm(camera_x)
    
    # Recalculate camera Y-axis: Y = Z × X
    camera_y = np.cross(camera_z, camera_x)
    camera_y = camera_y / np.linalg.norm(camera_y)
    
    # Create rotation matrix from orthonormal basis vectors
    rotation_matrix = Matrix([
        [camera_x[0], camera_y[0], camera_z[0], 0],
        [camera_x[1], camera_y[1], camera_z[1], 0],
        [camera_x[2], camera_y[2], camera_z[2], 0],
        [0, 0, 0, 1]
    ])
    
    # Apply the transformation matrix
    camera_object.matrix_world = Matrix.Translation(Vector(location)) @ rotation_matrix
    
    return camera_object

def create_camera_look_at(location, target, up_vector=(0, 0, 1), name="LookAtCamera"):
    """
    Create a camera at a specific location looking at a target point.
    
    Args:
        location (Vector or tuple): Camera position
        target (Vector or tuple): Point to look at
        up_vector (Vector or tuple): Up direction for the camera
        name (str): Name for the camera object
    
    Returns:
        bpy.types.Object: The created camera object
    """
    location = Vector(location)
    target = Vector(target)
    
    # Calculate view direction from camera to target
    view_direction = (target - location).normalized()
    
    return create_camera_with_orientation(location, view_direction, up_vector, name)

def create_camera_using_track_quat(location, view_direction, up_vector, name="TrackQuatCamera"):
    """
    Alternative implementation using Vector.to_track_quat() method.
    
    Args:
        location (Vector or tuple): Camera position
        view_direction (Vector or tuple): Direction to look
        up_vector (Vector or tuple): Up direction
        name (str): Name for the camera object
    
    Returns:
        bpy.types.Object: The created camera object
    """
    # Ensure inputs are Vector objects
    location = Vector(location)
    view_direction = Vector(view_direction).normalized()
    up_vector = Vector(up_vector).normalized()
    
    # Create camera data and object
    camera_data = bpy.data.cameras.new(name=name)
    camera_object = bpy.data.objects.new(name, camera_data)
    
    # Add camera to scene
    bpy.context.scene.collection.objects.link(camera_object)
    
    # Set camera location
    camera_object.location = location
    
    # Use to_track_quat to get orientation
    # Camera looks down -Z axis, so negate view direction
    camera_direction = -view_direction
    
    # Determine up axis character
    up_axis = 'Y'  # Default
    if abs(up_vector.z) > abs(up_vector.y) and abs(up_vector.z) > abs(up_vector.x):
        up_axis = 'Z'
    elif abs(up_vector.x) > abs(up_vector.y):
        up_axis = 'X'
    
    # Get quaternion rotation
    quat = camera_direction.to_track_quat('-Z', up_axis)
    
    # Apply rotation
    camera_object.rotation_euler = quat.to_euler()
    
    return camera_object

def render_with_camera(camera_object, output_filepath, resolution=(1920, 1080)):
    """
    Render an image using the specified camera.
    
    Args:
        camera_object (bpy.types.Object): Camera to render with
        output_filepath (str): Path to save the rendered image
        resolution (tuple): Resolution as (width, height)
    """
    # Set the camera as active
    bpy.context.scene.camera = camera_object
    
    # Configure render settings
    render = bpy.context.scene.render
    render.resolution_x = resolution[0]
    render.resolution_y = resolution[1]
    render.filepath = output_filepath
    
    # Set image format (optional)
    render.image_settings.file_format = 'PNG'
    render.image_settings.color_mode = 'RGBA'
    
    # Perform the render
    bpy.ops.render.render(write_still=True)
    
    print(f"Rendered image saved to: {output_filepath}")

# Example usage functions
def example_basic_usage():
    """Example of basic camera creation and rendering."""
    # Clear existing cameras
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='CAMERA')
    bpy.ops.object.delete(use_global=False)
    
    # Create a camera looking at the origin from above
    camera_location = (5, -5, 5)
    view_direction = (-1, 1, -1)  # Looking toward origin
    up_vector = (0, 0, 1)  # Z-up
    
    camera = create_camera_with_orientation(
        location=camera_location,
        view_direction=view_direction,
        up_vector=up_vector,
        name="CustomCamera"
    )
    
    # Render the scene
    render_with_camera(camera, "/tmp/rendered_image.png")

def example_look_at_usage():
    """Example of look-at camera creation."""
    # Create a camera looking at a specific object
    camera_location = (10, 0, 5)
    target_location = (0, 0, 0)  # Look at origin
    up_vector = (0, 0, 1)
    
    camera = create_camera_look_at(
        location=camera_location,
        target=target_location,
        up_vector=up_vector,
        name="LookAtCamera"
    )
    
    # Render the scene
    render_with_camera(camera, "/tmp/lookat_render.png", (1920, 1080))

def example_multiple_cameras():
    """Example creating multiple cameras with different orientations."""
    # Camera positions around a sphere
    positions = [
        (5, 0, 3),   # Front
        (0, 5, 3),   # Right  
        (-5, 0, 3),  # Back
        (0, -5, 3),  # Left
        (0, 0, 8),   # Top
    ]
    
    cameras = []
    for i, pos in enumerate(positions):
        # All cameras look at origin
        view_dir = Vector((0, 0, 0)) - Vector(pos)
        up_vec = (0, 0, 1)
        
        camera = create_camera_with_orientation(
            location=pos,
            view_direction=view_dir,
            up_vector=up_vec,
            name=f"Camera_{i+1}"
        )
        cameras.append(camera)
        
        # Render from each camera
        render_with_camera(camera, f"/tmp/camera_{i+1}_render.png")
    
    print(f"Created {len(cameras)} cameras and rendered {len(cameras)} images")

# Advanced example with custom camera settings
def example_custom_camera_settings():
    """Example with custom camera parameters."""
    # Create camera
    camera = create_camera_look_at(
        location=(8, -8, 6),
        target=(0, 0, 1),
        up_vector=(0, 0, 1),
        name="CustomizedCamera"
    )
    
    # Customize camera settings
    camera_data = camera.data
    camera_data.lens = 50  # 50mm lens
    camera_data.sensor_width = 36  # Full frame sensor
    camera_data.clip_start = 0.1
    camera_data.clip_end = 1000
    
    # Set depth of field (optional)
    camera_data.dof.use_dof = True
    camera_data.dof.focus_distance = 10
    camera_data.dof.aperture_fstop = 2.8
    
    # Render with custom settings
    render_with_camera(camera, "/tmp/custom_camera_render.png", (2560, 1440))
```

## Usage Notes

### 1. Coordinate System
Make sure you understand Blender's coordinate system:
- Z-axis points up by default
- Cameras look down their negative Z-axis
- Right-handed coordinate system

### 2. Vector Normalization
Always normalize direction vectors to avoid unexpected scaling:
```python
view_direction = Vector(view_direction).normalized()
up_vector = Vector(up_vector).normalized()
```

### 3. Orthogonal Up Vector
The up vector should be roughly perpendicular to the view direction for best results. If they're parallel, the camera orientation may be unpredictable.

### 4. Alternative Method with Constraints
You can also use Blender's Track To constraint:
```python
def create_camera_with_constraint(location, target_location, name="ConstraintCamera"):
    # Create camera
    camera_data = bpy.data.cameras.new(name=name)
    camera_object = bpy.data.objects.new(name, camera_data)
    bpy.context.scene.collection.objects.link(camera_object)
    
    # Set location
    camera_object.location = location
    
    # Create target empty
    target_empty = bpy.data.objects.new("CameraTarget", None)
    target_empty.location = target_location
    bpy.context.scene.collection.objects.link(target_empty)
    
    # Add Track To constraint
    constraint = camera_object.constraints.new(type='TRACK_TO')
    constraint.target = target_empty
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis = 'UP_Y'
    
    return camera_object, target_empty
```

### 5. Render Settings
Common render settings you might want to configure:
```python
render = bpy.context.scene.render
render.engine = 'CYCLES'  # or 'BLENDER_EEVEE'
render.resolution_x = 1920
render.resolution_y = 1080
render.resolution_percentage = 100
render.image_settings.file_format = 'PNG'
render.image_settings.color_mode = 'RGBA'
render.image_settings.compression = 15  # PNG compression
```

## Troubleshooting

### Camera Not Visible in Render
- Ensure the camera is set as active: `bpy.context.scene.camera = camera_object`
- Check that objects are within the camera's clipping range
- Verify the camera is not inside other objects

### Unexpected Orientation
- Double-check that view direction and up vector are not parallel
- Ensure vectors are normalized
- Remember that cameras look down their negative Z-axis

### Matrix Math Issues
- Use `Matrix.Translation(location) @ rotation_matrix` for proper matrix multiplication
- Ensure rotation matrix is orthonormal (orthogonal unit vectors)
- Check matrix order - transformation order matters

This guide provides everything needed to create cameras with specific orientations and render images programmatically in Blender.

## Tested Working Example

Here's a complete working example that has been tested with the Blender MCP:

```python
import bpy
import numpy as np
from mathutils import Vector, Matrix

def create_camera_complete_test():
    """Complete tested example of camera creation with numpy"""
    # Clear existing cameras (optional)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='CAMERA')
    bpy.ops.object.delete(use_global=False)
    
    # Define camera parameters using numpy
    location = np.array([8, -8, 6], dtype=np.float64)
    target = np.array([0, 0, 0], dtype=np.float64)  # Look at cube
    up_vector = np.array([0, 0, 1], dtype=np.float64)
    
    # Calculate view direction
    view_direction = target - location
    view_direction = view_direction / np.linalg.norm(view_direction)
    up_vector = up_vector / np.linalg.norm(up_vector)
    
    # Create camera
    camera_data = bpy.data.cameras.new(name="TestCamera")
    camera_object = bpy.data.objects.new("TestCamera", camera_data)
    bpy.context.scene.collection.objects.link(camera_object)
    camera_object.location = Vector(location)
    
    # Calculate orthonormal basis using numpy
    camera_z = -view_direction  # Camera looks down -Z
    camera_x = np.cross(up_vector, camera_z)
    camera_x = camera_x / np.linalg.norm(camera_x)
    camera_y = np.cross(camera_z, camera_x)
    
    # Create and apply rotation matrix
    rotation_matrix = Matrix([
        [camera_x[0], camera_y[0], camera_z[0], 0],
        [camera_x[1], camera_y[1], camera_z[1], 0],
        [camera_x[2], camera_y[2], camera_z[2], 0],
        [0, 0, 0, 1]
    ])
    
    camera_object.matrix_world = Matrix.Translation(Vector(location)) @ rotation_matrix
    
    # Set as active camera and configure render
    bpy.context.scene.camera = camera_object
    render = bpy.context.scene.render
    render.resolution_x = 800
    render.resolution_y = 600
    render.filepath = "/tmp/test_camera_render.png"
    render.image_settings.file_format = 'PNG'
    
    # Render the image
    bpy.ops.render.render(write_still=True)
    
    print(f"✓ Camera created and image rendered successfully!")
    return camera_object

# Execute the test
camera = create_camera_complete_test()
```

This example has been successfully tested and creates a camera that properly looks at the default cube from the specified position using numpy for all vector calculations.
