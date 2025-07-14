# GLB/GLTF Export - Blender Python API Reference

## Core Export Operation

From BlenderPythonDoc: `bpy.ops.export_scene.html`

**Complete GLB Export Function:**
```python
bpy.ops.export_scene.gltf(
    filepath='',                    # Required: output file path
    check_existing=True,            # Check if file exists
    export_format='GLB',            # 'GLB' or 'GLTF_SEPARATE' or 'GLTF_EMBEDDED'
    ui_tab='GENERAL',               # UI tab (not relevant for scripting)
    export_copyright='',            # Copyright information
    export_image_format='AUTO',     # Image format: 'AUTO', 'JPEG', 'PNG'
    export_texture_dir='',          # Texture directory
    export_keep_originals=False,    # Keep original images
    export_texcoords=True,          # Export UV coordinates
    export_normals=True,            # Export vertex normals
    export_materials='EXPORT',      # 'EXPORT', 'PLACEHOLDER', 'NONE'
    export_cameras=False,           # Export cameras
    use_selection=False,            # Export only selected objects
    use_visible=False,              # Export only visible objects
    use_renderable=False,           # Export only renderable objects
    export_apply=False,             # Apply modifiers
    export_yup=True,                # Y-up coordinate system
    # ... many more parameters available
)
```

## Practical Export Pattern

**Working pattern from our scene_manager:**
```python
def export_object_to_glb(object_name, filepath, with_material=True):
    """Export object or collection to GLB with proper setup."""
    
    # Clear selection first
    bpy.ops.object.select_all(action='DESELECT')
    
    # Check if it's an object or collection
    is_object = object_name in bpy.data.objects
    is_collection = object_name in bpy.data.collections
    
    if not is_object and not is_collection:
        raise ValueError(f"'{object_name}' not found as object or collection")
    
    if is_object:
        # Select single object
        obj = bpy.data.objects[object_name]
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
    elif is_collection:
        # Select all mesh objects in collection
        collection = bpy.data.collections[object_name]
        selected_count = 0
        
        def select_objects_in_collection(coll):
            nonlocal selected_count
            for obj in coll.objects:
                if obj.type == 'MESH':  # Only mesh objects for GLB
                    obj.select_set(True)
                    selected_count += 1
                    if bpy.context.view_layer.objects.active is None:
                        bpy.context.view_layer.objects.active = obj
            
            # Handle child collections recursively
            for child_coll in coll.children:
                select_objects_in_collection(child_coll)
        
        select_objects_in_collection(collection)
        
        if selected_count == 0:
            raise ValueError("No mesh objects found in collection")
    
    # Export with proper settings
    export_materials = 'EXPORT' if with_material else 'NONE'
    
    bpy.ops.export_scene.gltf(
        filepath=filepath,
        use_selection=True,              # Export only selected
        export_format='GLB',             # Binary format
        export_materials=export_materials,
        export_apply=True,               # Apply transforms
        export_yup=False,                # Keep original coordinate system
        export_texcoords=True,           # UV coordinates
        export_normals=True              # Vertex normals
    )
```

## Base64 Export for Network Transfer

**Pattern for remote transfer (from our implementation):**
```python
import base64
import tempfile
import os

def export_to_glb_base64(object_name, with_material=True):
    """Export object to GLB and return as base64 string."""
    
    # Create temporary file
    temp_dir = tempfile.gettempdir()
    temp_filepath = os.path.join(temp_dir, f"temp_{object_name}.glb")
    
    try:
        # Export to temporary file
        export_object_to_glb(object_name, temp_filepath, with_material)
        
        # Read file and encode as base64
        if os.path.exists(temp_filepath):
            with open(temp_filepath, 'rb') as f:
                glb_bytes = f.read()
            
            glb_base64 = base64.b64encode(glb_bytes).decode('utf-8')
            file_size = len(glb_bytes)
            
            print(f"EXPORT_SUCCESS:{file_size}")
            print("GLB_BASE64_START")
            print(glb_base64)
            print("GLB_BASE64_END")
            
            return glb_base64
            
    finally:
        # Cleanup temporary file
        if os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
            except OSError:
                pass
```

## Export Format Options

**Format types:**
- `'GLB'` - Binary format (single file, recommended)
- `'GLTF_SEPARATE'` - Text format with separate files
- `'GLTF_EMBEDDED'` - Text format with embedded data

**Material export options:**
- `'EXPORT'` - Export all materials and textures
- `'PLACEHOLDER'` - Export placeholder materials
- `'NONE'` - No materials

**Selection options:**
- `use_selection=True` - Export only selected objects
- `use_visible=True` - Export only visible objects
- `use_renderable=True` - Export only renderable objects

## Common Export Settings

**For game engines (Unity, Unreal):**
```python
bpy.ops.export_scene.gltf(
    filepath=filepath,
    export_format='GLB',
    export_yup=True,              # Y-up for game engines
    export_apply=True,            # Apply modifiers/transforms
    export_materials='EXPORT',
    export_texcoords=True,
    export_normals=True
)
```

**For web/three.js:**
```python
bpy.ops.export_scene.gltf(
    filepath=filepath,
    export_format='GLB',
    export_yup=False,             # Keep Z-up for three.js
    export_apply=True,
    export_materials='EXPORT',
    export_image_format='JPEG',   # Smaller file size
    export_texcoords=True
)
```

**For 3D printing:**
```python
bpy.ops.export_scene.gltf(
    filepath=filepath,
    export_format='GLB',
    export_materials='NONE',      # No materials needed
    export_apply=True,            # Apply all modifiers
    export_normals=True,
    export_texcoords=False        # No UVs needed
)
```

## Error Handling

**Common export errors:**
```python
def safe_glb_export(filepath, **kwargs):
    """Export with error handling."""
    try:
        # Validate file path
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Check selection
        if kwargs.get('use_selection', False):
            if not bpy.context.selected_objects:
                raise ValueError("No objects selected for export")
        
        # Perform export
        bpy.ops.export_scene.gltf(filepath=filepath, **kwargs)
        
        # Verify file was created
        if not os.path.exists(filepath):
            raise RuntimeError("Export failed - file not created")
            
        return True
        
    except Exception as e:
        print(f"EXPORT_ERROR:{str(e)}")
        return False
```

## Selection Requirements

**Object type filtering:**
```python
# Only select mesh objects for GLB export
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        obj.select_set(True)
    else:
        obj.select_set(False)
```

**Collection handling:**
```python
def select_collection_meshes(collection_name):
    """Select all mesh objects in a collection."""
    if collection_name not in bpy.data.collections:
        return 0
    
    collection = bpy.data.collections[collection_name]
    selected_count = 0
    
    # Deselect all first
    bpy.ops.object.select_all(action='DESELECT')
    
    # Select mesh objects in collection
    for obj in collection.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
            selected_count += 1
    
    return selected_count
```

## Notes for blender-remote Testing

- **Selection critical**: Always set up proper selection before export
- **File path validation**: Check directory exists and is writable
- **Format consistency**: Use 'GLB' for binary, single-file output
- **Material handling**: Consider bandwidth vs quality for remote transfer
- **Error detection**: Check file existence after export operation
- **Memory management**: Clean up temporary files in network scenarios