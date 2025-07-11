# How to Get Blender Object Data into NumPy Arrays

This guide explains how to efficiently extract object data from Blender into NumPy arrays using the Python API. We will cover two main tasks:
1.  Getting an object's vertex coordinates in world space.
2.  Getting an object's transformation matrix.

## 1. Getting Vertices in World Space as a NumPy Array

To get the vertices of a mesh object in world coordinates, you need to perform two steps:
1.  Get the vertex coordinates in the object's local space.
2.  Transform these local coordinates into world space using the object's world matrix.

The most efficient way to read many vertex coordinates is to use the `foreach_get` method, which directly copies the data into a pre-allocated array.

### Implementation

```python
import bpy
import numpy as np

def get_vertices_in_world_space(obj):
    """
    Gets the vertices of a mesh object in world space.

    Parameters:
    - obj (bpy.types.Object): The object to get the vertices from.

    Returns:
    - np.ndarray: A NumPy array of shape (N, 3) where N is the number of vertices.
    """
    if obj.type != 'MESH':
        return None

    # Get the world matrix of the object
    world_matrix = np.array(obj.matrix_world)

    # Get the vertices in local space
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

# --- Example Usage ---
# Make sure you have an active object selected, and it is a mesh
active_obj = bpy.context.active_object
if active_obj:
    vertices = get_vertices_in_world_space(active_obj)
    if vertices is not None:
        print(f"Successfully retrieved {len(vertices)} vertices.")
        print("First 5 vertices:\n", vertices[:5])
else:
    print("No active object selected.")
```

## 2. Getting the Object's Transform as a 4x4 NumPy Matrix

Each object in Blender has a `matrix_world` property that represents its transformation (location, rotation, and scale) in world space. This is a `mathutils.Matrix` object, which can be easily converted to a NumPy array.

### Implementation

```python
import bpy
import numpy as np

def get_object_transform_matrix(obj):
    """
    Gets the 4x4 world transformation matrix of an object.

    Parameters:
    - obj (bpy.types.Object): The object to get the matrix from.

    Returns:
    - np.ndarray: A 4x4 NumPy array representing the object's world matrix.
    """
    return np.array(obj.matrix_world)

# --- Example Usage ---
# Make sure you have an active object selected
active_obj = bpy.context.active_object
if active_obj:
    transform_matrix = get_object_transform_matrix(active_obj)
    print(f"Transformation matrix for '{active_obj.name}':")
    print(transform_matrix)
else:
    print("No active object selected.")
```

By using these methods, you can efficiently interface Blender's data with NumPy for any external processing or analysis you need to perform.
