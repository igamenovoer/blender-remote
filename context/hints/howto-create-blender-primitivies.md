# How to Create Blender Primitives with Python API (Blender 4.x)

This document provides a comprehensive reference for creating primitive objects in Blender using the Python API. It covers mesh primitives, curve primitives, surface primitives, and metaball primitives.

## Overview

Blender's Python API provides several categories of primitive creation functions:

- **Mesh Primitives**: `bpy.ops.mesh.primitive_*` - Standard geometric meshes
- **Curve Primitives**: `bpy.ops.curve.primitive_*` - Bezier and NURBS curves
- **Surface Primitives**: `bpy.ops.surface.primitive_*` - NURBS surfaces
- **Metaball Primitives**: `bpy.ops.object.metaball_add` - Organic blob-like objects

## Mesh Primitives

### Basic Mesh Creation Pattern

All mesh primitives follow a similar pattern with common parameters:

```python
import bpy

# Common parameters for all mesh primitives
bpy.ops.mesh.primitive_[shape]_add(
    size=2.0,                          # Overall size
    location=(0, 0, 0),               # 3D location
    rotation=(0, 0, 0),               # Rotation in radians
    scale=(1, 1, 1),                  # Scale factors
    align='WORLD',                    # 'WORLD', 'VIEW', or 'CURSOR'
    enter_editmode=False,             # Enter edit mode after creation
    calc_uvs=True                     # Generate UV coordinates
)
```

### Cube

```python
# Basic cube
bpy.ops.mesh.primitive_cube_add(
    size=2.0,
    location=(0, 0, 0),
    rotation=(0, 0, 0),
    scale=(1, 1, 1)
)

# Cube with custom location and rotation
bpy.ops.mesh.primitive_cube_add(
    size=1.5,
    location=(3, 0, 0),
    rotation=(0, 0, 0.785398),  # 45 degrees in radians
    enter_editmode=True
)
```

### Sphere (UV Sphere)

```python
# Basic UV sphere
bpy.ops.mesh.primitive_uv_sphere_add(
    radius=1.0,
    segments=32,         # Horizontal segments
    ring_count=16,       # Vertical rings
    location=(0, 0, 0),
    calc_uvs=True
)

# High-detail sphere
bpy.ops.mesh.primitive_uv_sphere_add(
    radius=2.0,
    segments=64,
    ring_count=32,
    location=(5, 0, 0)
)
```

### Icosphere

```python
# Basic icosphere (more uniform triangles)
bpy.ops.mesh.primitive_ico_sphere_add(
    radius=1.0,
    subdivisions=2,      # Number of subdivisions (1-10)
    location=(0, 0, 0),
    calc_uvs=True
)

# Smooth icosphere
bpy.ops.mesh.primitive_ico_sphere_add(
    radius=1.5,
    subdivisions=3,
    location=(0, 3, 0)
)
```

### Cylinder

```python
# Basic cylinder
bpy.ops.mesh.primitive_cylinder_add(
    radius=1.0,
    depth=2.0,
    vertices=32,         # Number of vertices in circle
    end_fill_type='NGON',  # 'NOTHING', 'NGON', 'TRIFAN'
    location=(0, 0, 0),
    calc_uvs=True
)

# Cylinder without caps
bpy.ops.mesh.primitive_cylinder_add(
    radius=1.0,
    depth=3.0,
    vertices=16,
    end_fill_type='NOTHING',
    location=(3, 3, 0)
)
```

### Cone

```python
# Basic cone
bpy.ops.mesh.primitive_cone_add(
    vertices=32,
    radius1=1.0,         # Base radius
    radius2=0.0,         # Top radius (0 = pointed)
    depth=2.0,
    end_fill_type='NGON',
    location=(0, 0, 0),
    calc_uvs=True
)

# Truncated cone (frustum)
bpy.ops.mesh.primitive_cone_add(
    vertices=16,
    radius1=1.5,
    radius2=0.5,
    depth=2.0,
    location=(6, 0, 0)
)
```

### Torus

```python
# Basic torus
bpy.ops.mesh.primitive_torus_add(
    major_radius=1.0,    # Main ring radius
    minor_radius=0.25,   # Tube radius
    major_segments=48,   # Segments around main ring
    minor_segments=12,   # Segments around tube
    location=(0, 0, 0),
    generate_uvs=True
)

# Custom torus with different proportions
bpy.ops.mesh.primitive_torus_add(
    major_radius=2.0,
    minor_radius=0.5,
    major_segments=32,
    minor_segments=16,
    location=(5, 5, 0)
)
```

### Plane

```python
# Basic plane
bpy.ops.mesh.primitive_plane_add(
    size=2.0,
    location=(0, 0, 0),
    calc_uvs=True
)

# Subdivided plane (grid)
bpy.ops.mesh.primitive_grid_add(
    x_subdivisions=10,
    y_subdivisions=10,
    size=2.0,
    location=(4, 0, 0),
    calc_uvs=True
)
```

### Circle

```python
# Basic circle
bpy.ops.mesh.primitive_circle_add(
    vertices=32,
    radius=1.0,
    fill_type='NGON',    # 'NOTHING', 'NGON', 'TRIFAN'
    location=(0, 0, 0),
    calc_uvs=True
)

# Circle outline only
bpy.ops.mesh.primitive_circle_add(
    vertices=24,
    radius=1.5,
    fill_type='NOTHING',
    location=(3, 0, 0)
)
```

### Monkey (Suzanne)

```python
# Blender's test mesh "Suzanne"
bpy.ops.mesh.primitive_monkey_add(
    size=2.0,
    location=(0, 0, 0),
    calc_uvs=True
)
```

## Curve Primitives

### Bezier Curve

```python
# Basic bezier curve
bpy.ops.curve.primitive_bezier_curve_add(
    radius=1.0,
    location=(0, 0, 0),
    enter_editmode=False
)

# Bezier circle
bpy.ops.curve.primitive_bezier_circle_add(
    radius=1.0,
    location=(3, 0, 0),
    enter_editmode=False
)
```

### NURBS Curve

```python
# NURBS curve
bpy.ops.curve.primitive_nurbs_curve_add(
    radius=1.0,
    location=(0, 0, 0),
    enter_editmode=False
)

# NURBS circle
bpy.ops.curve.primitive_nurbs_circle_add(
    radius=1.0,
    location=(3, 0, 0),
    enter_editmode=False
)

# NURBS path
bpy.ops.curve.primitive_nurbs_path_add(
    radius=1.0,
    location=(0, 3, 0),
    enter_editmode=False
)
```

## Surface Primitives

### NURBS Surfaces

```python
# NURBS surface patch
bpy.ops.surface.primitive_nurbs_surface_surface_add(
    radius=1.0,
    location=(0, 0, 0),
    enter_editmode=False
)

# NURBS surface circle
bpy.ops.surface.primitive_nurbs_surface_circle_add(
    radius=1.0,
    location=(3, 0, 0),
    enter_editmode=False
)

# NURBS surface cylinder
bpy.ops.surface.primitive_nurbs_surface_cylinder_add(
    radius=1.0,
    location=(0, 3, 0),
    enter_editmode=False
)

# NURBS surface sphere
bpy.ops.surface.primitive_nurbs_surface_sphere_add(
    radius=1.0,
    location=(3, 3, 0),
    enter_editmode=False
)

# NURBS surface torus
bpy.ops.surface.primitive_nurbs_surface_torus_add(
    radius=1.0,
    location=(0, 0, 3),
    enter_editmode=False
)
```

## Metaball Primitives

```python
# Basic metaball
bpy.ops.object.metaball_add(
    type='BALL',         # 'BALL', 'CAPSULE', 'PLANE', 'ELLIPSOID', 'CUBE'
    radius=1.0,
    location=(0, 0, 0),
    enter_editmode=False
)

# Metaball capsule
bpy.ops.object.metaball_add(
    type='CAPSULE',
    radius=1.0,
    location=(3, 0, 0)
)

# Metaball cube
bpy.ops.object.metaball_add(
    type='CUBE',
    radius=1.0,
    location=(0, 3, 0)
)
```

## Practical Examples

### Creating a Scene with Multiple Primitives

```python
import bpy
import bmesh
from mathutils import Vector

def create_primitive_scene():
    # Clear existing mesh objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # Create a grid of different primitives
    primitives = [
        ('cube', lambda pos: bpy.ops.mesh.primitive_cube_add(size=1.5, location=pos)),
        ('sphere', lambda pos: bpy.ops.mesh.primitive_uv_sphere_add(radius=0.8, location=pos)),
        ('cylinder', lambda pos: bpy.ops.mesh.primitive_cylinder_add(radius=0.6, depth=1.5, location=pos)),
        ('cone', lambda pos: bpy.ops.mesh.primitive_cone_add(radius1=0.8, depth=1.5, location=pos)),
        ('torus', lambda pos: bpy.ops.mesh.primitive_torus_add(major_radius=0.6, minor_radius=0.2, location=pos)),
        ('monkey', lambda pos: bpy.ops.mesh.primitive_monkey_add(size=1.2, location=pos))
    ]
    
    # Arrange primitives in a 2x3 grid
    for i, (name, create_func) in enumerate(primitives):
        x = (i % 3) * 3
        y = (i // 3) * 3
        pos = (x, y, 0)
        
        create_func(pos)
        
        # Rename the object
        bpy.context.active_object.name = f"Primitive_{name}"
    
    # Add some lights
    bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
    bpy.ops.object.light_add(type='AREA', location=(-5, -5, 5))

# Run the function
create_primitive_scene()
```

### Creating Parametric Shapes

```python
import bpy
import math

def create_spiral_of_cubes(count=20, radius=5, height=10):
    """Create a spiral of cubes"""
    for i in range(count):
        angle = i * (2 * math.pi / count) * 3  # 3 complete rotations
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        z = (i / count) * height
        
        bpy.ops.mesh.primitive_cube_add(
            size=0.5,
            location=(x, y, z),
            rotation=(0, 0, angle)
        )
        
        # Name the cube
        bpy.context.active_object.name = f"Cube_Spiral_{i:02d}"

def create_tower_of_shapes():
    """Create a tower using different primitive shapes"""
    shapes = [
        ('base', lambda z: bpy.ops.mesh.primitive_cylinder_add(radius=3, depth=1, location=(0, 0, z))),
        ('level1', lambda z: bpy.ops.mesh.primitive_cube_add(size=4, location=(0, 0, z))),
        ('level2', lambda z: bpy.ops.mesh.primitive_cylinder_add(radius=2, depth=2, location=(0, 0, z))),
        ('level3', lambda z: bpy.ops.mesh.primitive_ico_sphere_add(radius=1.5, location=(0, 0, z))),
        ('top', lambda z: bpy.ops.mesh.primitive_cone_add(radius1=1, depth=2, location=(0, 0, z)))
    ]
    
    current_height = 0
    for name, create_func in shapes:
        create_func(current_height)
        bpy.context.active_object.name = f"Tower_{name}"
        current_height += 2

# Usage examples
create_spiral_of_cubes(30, 8, 15)
create_tower_of_shapes()
```

## Advanced Tips and Techniques

### 1. Using Context Override for Specific Locations

```python
import bpy
from bpy import context

# Override context to place objects at cursor location
override_context = context.copy()
override_context['location'] = context.scene.cursor.location

with context.temp_override(**override_context):
    bpy.ops.mesh.primitive_cube_add(align='CURSOR')
```

### 2. Batch Creation with Material Assignment

```python
import bpy

def create_primitive_with_material(primitive_func, mat_name, color):
    """Create a primitive and assign a material"""
    primitive_func()
    obj = bpy.context.active_object
    
    # Create material
    mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    
    # Set base color
    principled = nodes.get("Principled BSDF")
    if principled:
        principled.inputs["Base Color"].default_value = (*color, 1.0)
    
    # Assign material
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
    
    return obj

# Create colored primitives
red_cube = create_primitive_with_material(
    lambda: bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0)),
    "Red_Material", (1, 0, 0)
)

blue_sphere = create_primitive_with_material(
    lambda: bpy.ops.mesh.primitive_uv_sphere_add(location=(3, 0, 0)),
    "Blue_Material", (0, 0, 1)
)
```

### 3. Creating Primitives with Custom Properties

```python
import bpy

def create_tagged_primitive(primitive_type, location, custom_props=None):
    """Create a primitive with custom properties"""
    if primitive_type == 'cube':
        bpy.ops.mesh.primitive_cube_add(location=location)
    elif primitive_type == 'sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(location=location)
    elif primitive_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(location=location)
    
    obj = bpy.context.active_object
    
    # Add custom properties
    if custom_props:
        for key, value in custom_props.items():
            obj[key] = value
    
    return obj

# Create primitives with metadata
cube_obj = create_tagged_primitive('cube', (0, 0, 0), {
    'type': 'building_block',
    'material_type': 'concrete',
    'health': 100
})

sphere_obj = create_tagged_primitive('sphere', (3, 0, 0), {
    'type': 'projectile',
    'damage': 25,
    'speed': 15.0
})
```

## Common Parameters Reference

### Alignment Options
- `'WORLD'` - Align to world coordinates
- `'VIEW'` - Align to current view
- `'CURSOR'` - Align to 3D cursor orientation

### Fill Types (for cylinders, cones, circles)
- `'NOTHING'` - No fill (hollow)
- `'NGON'` - Single n-sided polygon
- `'TRIFAN'` - Triangle fan from center

### Metaball Types
- `'BALL'` - Spherical metaball
- `'CAPSULE'` - Capsule/pill shaped
- `'PLANE'` - Flat plane
- `'ELLIPSOID'` - Elliptical shape
- `'CUBE'` - Cubic metaball

## Performance Considerations

1. **Subdivision Levels**: Higher subdivision creates more detailed but heavier geometry
2. **UV Generation**: Set `calc_uvs=False` if UV coordinates aren't needed
3. **Batch Operations**: Use `bpy.context.view_layer.update()` after batch primitive creation
4. **Memory Management**: Delete unused objects with `bpy.data.objects.remove(obj, do_unlink=True)`

## Integration with blender-remote

When using these primitives with the blender-remote system, wrap them in functions:

```python
def create_cube_at_location(client, location=(0, 0, 0), size=2.0):
    """Create a cube using blender-remote client"""
    code = f"""
import bpy
bpy.ops.mesh.primitive_cube_add(
    size={size},
    location={location}
)
"""
    return client.execute_python(code)

def create_sphere_with_subdivisions(client, location=(0, 0, 0), subdivisions=2):
    """Create an icosphere with custom subdivisions"""
    code = f"""
import bpy
bpy.ops.mesh.primitive_ico_sphere_add(
    subdivisions={subdivisions},
    location={location}
)
"""
    return client.execute_python(code)

# Usage with blender-remote
client = blender_remote.connect_to_blender()
create_cube_at_location(client, (2, 0, 0), 1.5)
create_sphere_with_subdivisions(client, (0, 2, 0), 3)
```

This reference should provide a solid foundation for creating any primitive geometry in Blender using Python, whether working directly in Blender or through the blender-remote system.
