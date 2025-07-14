# Blender Python API Reference for blender-remote

This directory contains curated Blender Python API documentation snippets based on:
- Official BlenderPythonDoc 4.4 reference (`context/refcode/blender_python_reference_4_4/`)
- Practical debugging experience from blender-remote client testing
- Working patterns discovered during comprehensive I/O boundary testing

## API Reference Files

### Core Operations
- **[bmesh-operations.md](bmesh-operations.md)** - BMesh API patterns, memory management, common errors
- **[primitive-creation.md](primitive-creation.md)** - Object creation operations, parameter handling
- **[object-selection-deletion.md](object-selection-deletion.md)** - Selection and deletion with context requirements
- **[glb-export.md](glb-export.md)** - GLB/GLTF export operations, format options, base64 transfer

### Context and I/O
- **[context-management.md](context-management.md)** - Context override patterns, 3D viewport requirements
- **[response-parsing.md](response-parsing.md)** - BLD Remote MCP response parsing, I/O patterns

## Key Insights from Debugging

### Critical Fixes Applied (2025-07-14)

#### 1. Response Field Parsing (CRITICAL)
**Problem**: Reading wrong response field caused empty results
**File**: `src/blender_remote/client.py:307-314`
```python
# BEFORE (wrong)
return response.get("result", {}).get("message", "")

# AFTER (correct)  
result_data = response.get("result", {})
output = result_data.get("result", "")
if not output:
    output = result_data.get("output", {}).get("stdout", "")
return output
```

#### 2. Context Setup for Operations (CRITICAL)
**Problem**: `bpy.ops.object.select_all()` failed with context errors
**File**: `src/blender_remote/scene_manager.py:367-385`
```python
# Working pattern
areas_3d = [area for area in bpy.context.window.screen.areas if area.type == 'VIEW_3D']
if areas_3d:
    with bpy.context.temp_override(area=areas_3d[0]):
        if bpy.context.active_object and bpy.context.active_object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        # ... operations ...
```

#### 3. BMesh API Compatibility (HIGH)
**Problem**: Wrong bmesh API usage
**File**: `context/tests/test_scene_manager_export.py:307-308`
```python
# BEFORE (incorrect)
bm = bmesh.from_mesh(obj.data)

# AFTER (correct)
bm = bmesh.new()
bm.from_mesh(obj.data)
```

## Context Requirements Hierarchy

Based on comprehensive testing:

1. **✅ No Context Override Needed**
   - Object creation (`bpy.ops.mesh.primitive_*_add`)
   - Scene info access (`bpy.context.scene`)
   - Object property setting (`obj.location = ...`)

2. **⚠️ Context Override Required**
   - Object selection (`bpy.ops.object.select_all`)
   - Object deletion (`bpy.ops.object.delete`)
   - Mode switching (sometimes)

## API Usage Patterns

### Safe Object Creation
```python
# This pattern works reliably without context override
bpy.ops.mesh.primitive_cube_add(location=(x, y, z))
obj = bpy.context.active_object
obj.name = "MyObject"
print(f"OBJECT_NAME:{obj.name}")
```

### Safe Scene Clearing
```python
# This pattern requires context override
areas_3d = [area for area in bpy.context.window.screen.areas if area.type == 'VIEW_3D']
if areas_3d:
    with bpy.context.temp_override(area=areas_3d[0]):
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        # ... select objects to delete ...
        bpy.ops.object.delete()
```

### Safe BMesh Operations
```python
# This pattern prevents memory leaks and API errors
bm = bmesh.new()
try:
    bm.from_mesh(obj.data)
    # ... modify bmesh ...
    bm.to_mesh(obj.data)
finally:
    bm.free()
```

### Safe GLB Export
```python
# This pattern handles selection and export reliably
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
bpy.context.view_layer.objects.active = obj

bpy.ops.export_scene.gltf(
    filepath=filepath,
    use_selection=True,
    export_format='GLB',
    export_materials='EXPORT'
)
```

## Error Patterns and Solutions

### Context Errors
```
RuntimeError: Operator bpy.ops.object.select_all.poll() failed, context is incorrect
```
**Solution**: Use `temp_override(area=area_3d)` with 3D viewport area

### BMesh Errors
```
AttributeError: module 'bmesh' has no attribute 'from_mesh'
```
**Solution**: Use `bm = bmesh.new(); bm.from_mesh(mesh)` pattern

### Empty Results
```
Object creation returns empty string instead of object name
```
**Solution**: Check `response["result"]["result"]` field, not `response["result"]["message"]`

## Performance Results

After applying these fixes:
- **Object Creation**: 0% → 100% success rate
- **Scene Operations**: 50% → 91.7% success rate  
- **GLB Export**: 40% → 70% success rate

## Documentation Sources

- **BlenderPythonDoc 4.4**: `/workspace/code/blender-remote/context/refcode/blender_python_reference_4_4/`
- **Test Results**: `/workspace/code/blender-remote/context/logs/tests/`
- **Debug Analysis**: `/workspace/code/blender-remote/context/logs/debug_fixes_summary_2025-07-14.md`

## Usage in blender-remote

These patterns are specifically designed for:
- **Remote Blender control** via BLD Remote MCP service
- **Network-based I/O** with structured response parsing
- **Error recovery** and fallback communication methods
- **Production reliability** in server environments

## Best Practices

1. **Always use documented API patterns** from these reference files
2. **Implement proper error handling** for context-dependent operations
3. **Use structured print output** for parseable remote communication
4. **Test with fallback methods** to isolate client vs service issues
5. **Validate response structure** before parsing data fields