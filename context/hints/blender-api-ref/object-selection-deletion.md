# Object Selection and Deletion - Blender Python API Reference

## Core Selection Operations

From BlenderPythonDoc: `bpy.ops.object.html`

**Select All Objects:**
```python
bpy.ops.object.select_all(action='TOGGLE')
```

**Action options:**
- `'SELECT'` - Select all objects
- `'DESELECT'` - Deselect all objects  
- `'TOGGLE'` - Toggle selection state
- `'INVERT'` - Invert current selection

**Delete Selected Objects:**
```python
bpy.ops.object.delete(use_global=False, confirm=True)
```

**Mode Management:**
```python
bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
```

**Mode options:**
- `'OBJECT'` - Object mode (required for selection/deletion)
- `'EDIT'` - Edit mode
- `'SCULPT'` - Sculpt mode
- `'VERTEX_PAINT'` - Vertex paint mode
- `'WEIGHT_PAINT'` - Weight paint mode
- `'TEXTURE_PAINT'` - Texture paint mode
- `'PARTICLE_EDIT'` - Particle edit mode
- `'POSE'` - Pose mode (for armatures)

## Context Requirements ⚠️

**❌ These operations REQUIRE proper context:**
- `bpy.ops.object.select_all()`
- `bpy.ops.object.delete()`
- Most object-level operations

**Context error pattern:**
```
RuntimeError: Operator bpy.ops.object.select_all.poll() failed, context is incorrect
```

## Working Context Override Pattern

**From our successful fixes:**
```python
def clear_scene_with_context(keep_camera=True, keep_light=True):
    """Clear scene with proper context setup."""
    
    # Find 3D viewport area
    areas_3d = [area for area in bpy.context.window.screen.areas 
                if area.type == 'VIEW_3D']
    
    if areas_3d:
        area_3d = areas_3d[0]
        
        # Use simplified context override (area only)
        with bpy.context.temp_override(area=area_3d):
            # Ensure object mode first
            if (bpy.context.active_object and 
                bpy.context.active_object.mode != 'OBJECT'):
                bpy.ops.object.mode_set(mode='OBJECT')
            
            # Clear selection
            bpy.ops.object.select_all(action='DESELECT')
            
            # Set up keep types
            keep_types = []
            if keep_camera:
                keep_types.append('CAMERA')
            if keep_light:
                keep_types.append('LIGHT')
            
            # Select objects to delete
            for obj in bpy.context.scene.objects:
                if obj.type not in keep_types:
                    obj.select_set(True)
            
            # Delete selected objects
            bpy.ops.object.delete()
    else:
        # Fallback without context (may fail)
        print("WARNING: No 3D viewport found for context")
```

## Individual Object Selection

**Direct object selection (no context needed):**
```python
# Select specific object by name
if "ObjectName" in bpy.data.objects:
    obj = bpy.data.objects["ObjectName"]
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
```

**Deselect specific object:**
```python
obj.select_set(False)
```

## Object Deletion Patterns

**Delete by name (safe method):**
```python
def delete_object_by_name(object_name):
    """Delete object by name without operators."""
    if object_name in bpy.data.objects:
        obj = bpy.data.objects[object_name]
        bpy.data.objects.remove(obj, do_unlink=True)
        return True
    return False
```

**Delete with selection (requires context):**
```python
def delete_selected_with_context():
    """Delete selected objects with proper context."""
    areas_3d = [area for area in bpy.context.window.screen.areas 
                if area.type == 'VIEW_3D']
    
    if areas_3d:
        with bpy.context.temp_override(area=areas_3d[0]):
            if bpy.context.active_object:
                if bpy.context.active_object.mode != 'OBJECT':
                    bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.delete()
```

## Context Override Requirements

**Hierarchy of context needs:**
1. **Object Creation**: Usually works without context override
2. **Scene Info**: Works without context override  
3. **Object Selection**: Requires `temp_override(area=area_3d)` + object mode
4. **Object Deletion**: Requires `temp_override(area=area_3d)` + object mode

**Key insights from our debugging:**
- **Simplified override works better**: Use `temp_override(area=area_3d)` only
- **Complex overrides fail**: Don't use `window`, `region` parameters together
- **Object mode required**: Always ensure `mode='OBJECT'` before operations
- **Area detection**: Always check for 3D viewport availability

## Error Handling

**Context detection pattern:**
```python
def ensure_object_context():
    """Ensure proper context for object operations."""
    # Find 3D viewport
    areas_3d = [area for area in bpy.context.window.screen.areas 
                if area.type == 'VIEW_3D']
    
    if not areas_3d:
        raise RuntimeError("No 3D viewport found - operations may fail")
    
    # Ensure object mode
    if (bpy.context.active_object and 
        bpy.context.active_object.mode != 'OBJECT'):
        # This might fail without context, so wrap it
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except RuntimeError:
            print("Warning: Could not set object mode")
    
    return areas_3d[0]
```

## Selection State Query

**Check object selection:**
```python
# Check if object is selected
is_selected = obj.select_get()

# Get all selected objects
selected_objects = bpy.context.selected_objects

# Check active object
active_obj = bpy.context.active_object
```

## Notes for blender-remote Testing

- **Context dependency**: Selection/deletion operations ALWAYS need proper context
- **Area requirement**: Need 3D viewport area for context override
- **Mode management**: Object mode is prerequisite for most operations
- **Fallback strategies**: Direct `bpy.data.objects.remove()` avoids context issues
- **Error patterns**: `poll() failed` indicates context problems