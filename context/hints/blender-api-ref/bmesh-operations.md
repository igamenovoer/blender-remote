# BMesh Operations - Blender Python API Reference

## Core BMesh Workflow Pattern

From BlenderPythonDoc: `bmesh.html`

**Standard BMesh usage pattern (ALWAYS use this):**
```python
import bmesh

# Get mesh data from current object
me = bpy.context.object.data

# Create new BMesh instance and load mesh data
bm = bmesh.new()   # create an empty BMesh
bm.from_mesh(me)   # fill it in from a Mesh

# Modify the BMesh (example modifications)
for v in bm.verts:
    v.co.x += 1.0

# Write BMesh back to mesh and cleanup
bm.to_mesh(me)
bm.free()  # CRITICAL: free memory and prevent further access
```

## Common BMesh Operations

**Create empty BMesh with operator support:**
```python
bm = bmesh.new(use_operators=True)  # Enables calling operators on BMesh
```

**Load mesh data:**
```python
bm.from_mesh(mesh_data)  # Load from mesh
```

**Write data back:**
```python
bm.to_mesh(mesh_data)  # Write to mesh
mesh_data.update()  # Update mesh display
```

**Memory management (CRITICAL):**
```python
bm.free()  # Always call this to prevent memory leaks
```

## BMesh API Error - WRONG vs RIGHT

**❌ WRONG (causes AttributeError):**
```python
# This fails: bmesh.from_mesh() doesn't exist as module function
bm = bmesh.from_mesh(obj.data)
```

**✅ RIGHT (documented pattern):**
```python
# This works: proper BMesh instance method
bm = bmesh.new()
bm.from_mesh(obj.data)
```

## Example: Adding Modifier Operations

From our GLB export test case:
```python
import bmesh

def add_inset_modifier(obj):
    """Add inset faces modifier via bmesh operations."""
    # Enter edit mode data
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    
    # Perform inset operation
    bmesh.ops.inset_faces(bm, faces=bm.faces, thickness=0.1)
    
    # Write back to mesh
    bm.to_mesh(obj.data)
    bm.free()
    
    # Update mesh display
    obj.data.update()
```

## Memory Management Best Practices

1. **Always pair `bmesh.new()` with `bmesh.free()`**
2. **Use try/finally blocks for error safety:**
   ```python
   bm = bmesh.new()
   try:
       bm.from_mesh(mesh_data)
       # ... operations ...
       bm.to_mesh(mesh_data)
   finally:
       bm.free()
   ```

3. **Don't reuse BMesh instances** - create new ones for each operation

## Related APIs

- `bmesh.ops.*` - BMesh operators for geometry modification
- `mesh.update()` - Update mesh display after BMesh operations
- `bpy.context.object.data` - Access active object's mesh data

## Notes for blender-remote Testing

- **Critical for GLB export**: Complex geometry requires proper BMesh API usage
- **Memory safety**: Essential in server environments to prevent leaks
- **Error patterns**: AttributeError indicates wrong API usage pattern