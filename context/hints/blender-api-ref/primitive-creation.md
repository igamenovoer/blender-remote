# Primitive Object Creation - Blender Python API Reference

## Core Primitive Operations

From BlenderPythonDoc: `bpy.ops.mesh.html`

**Cube Creation:**
```python
bpy.ops.mesh.primitive_cube_add(
    size=2.0,                    # Edge length
    calc_uvs=True,               # Generate UV coordinates
    enter_editmode=False,        # Stay in object mode
    align='WORLD',               # Alignment ('WORLD', 'VIEW', 'CURSOR')
    location=(0.0, 0.0, 0.0),    # World location
    rotation=(0.0, 0.0, 0.0),    # Euler rotation in radians
    scale=(1.0, 1.0, 1.0)        # Scale factors (typically ignored, use size)
)
```

**Sphere Creation:**
```python
bpy.ops.mesh.primitive_uv_sphere_add(
    radius=1.0,                  # Sphere radius
    rings=32,                    # Number of rings
    segments=16,                 # Number of segments
    calc_uvs=True,
    enter_editmode=False,
    align='WORLD',
    location=(0.0, 0.0, 0.0),
    rotation=(0.0, 0.0, 0.0),
    scale=(1.0, 1.0, 1.0)
)
```

**Cylinder Creation:**
```python
bpy.ops.mesh.primitive_cylinder_add(
    vertices=32,                 # Number of vertices in base circle
    radius=1.0,                  # Base radius
    depth=2.0,                   # Height/depth
    end_fill_type='NGON',        # End cap type ('NGON', 'TRIFAN')
    calc_uvs=True,
    enter_editmode=False,
    align='WORLD',
    location=(0.0, 0.0, 0.0),
    rotation=(0.0, 0.0, 0.0),
    scale=(1.0, 1.0, 1.0)
)
```

**Plane Creation:**
```python
bpy.ops.mesh.primitive_plane_add(
    size=2.0,                    # Edge length
    calc_uvs=True,
    enter_editmode=False,
    align='WORLD',
    location=(0.0, 0.0, 0.0),
    rotation=(0.0, 0.0, 0.0),
    scale=(1.0, 1.0, 1.0)
)
```

## Context Requirements

**✅ Generally work WITHOUT context override:**
- Most primitive creation operations work in default context
- Object becomes active object: `bpy.context.active_object`

**Pattern from our testing:**
```python
# This usually works without context override
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
obj = bpy.context.active_object

# Set properties after creation
obj.name = "MyNewCube"
obj.rotation_euler = (0.5, 0, 0)
obj.scale = (2.0, 2.0, 2.0)
```

## Post-Creation Object Manipulation

**Setting object properties:**
```python
# Get the created object
obj = bpy.context.active_object

# Set name
obj.name = "CustomName"

# Set transforms
obj.location = (x, y, z)
obj.rotation_euler = (rx, ry, rz)  # Radians
obj.scale = (sx, sy, sz)

# Set visibility
obj.hide_viewport = False
obj.hide_render = False
```

## Object Creation Pattern for blender-remote

**Successful pattern from our fixes:**
```python
def create_primitive_safe(primitive_type, location=(0,0,0), name=None):
    """Create primitive with proper error handling."""
    
    # Create primitive (usually works without context)
    try:
        getattr(bpy.ops.mesh, f'primitive_{primitive_type}_add')(location=location)
        obj = bpy.context.active_object
        
        # Set name if provided
        if name:
            obj.name = name
            
        # Return object name for verification
        print(f"OBJECT_NAME:{obj.name}")
        return obj.name
        
    except RuntimeError as e:
        print(f"OBJECT_ERROR:Creation failed - {str(e)}")
        return ""
```

## Error Handling

**Common errors:**
- `RuntimeError`: Context incorrect (rare for primitive creation)
- `AttributeError`: Wrong primitive type name
- `TypeError`: Invalid parameter values

**Safe parameter validation:**
```python
def validate_location(location):
    """Validate location parameter."""
    if len(location) != 3:
        raise ValueError("location must have 3 elements")
    return tuple(float(x) for x in location)

# Usage
location = validate_location((x, y, z))
bpy.ops.mesh.primitive_cube_add(location=location)
```

## Available Primitive Types

**Standard primitives (all support similar parameters):**
- `primitive_cube_add`
- `primitive_uv_sphere_add`
- `primitive_ico_sphere_add`
- `primitive_cylinder_add`
- `primitive_cone_add`
- `primitive_plane_add`
- `primitive_circle_add`
- `primitive_torus_add`

## Notes for blender-remote Testing

- **Context independence**: Primitive creation usually doesn't need context override
- **Name extraction**: Use `bpy.context.active_object.name` after creation
- **Transform application**: Set transforms AFTER creation for predictable results
- **Error patterns**: RuntimeError indicates context issues (rare for creation)