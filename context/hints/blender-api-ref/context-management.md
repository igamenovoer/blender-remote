# Context Management - Blender Python API Reference

## Context Access

From BlenderPythonDoc: `bpy.context.html`

**Core context properties:**
```python
# Current objects
bpy.context.object          # Active object (may be None)
bpy.context.active_object   # Active object (same as above)
bpy.context.selected_objects  # List of selected objects

# Scene and collections
bpy.context.scene           # Current scene
bpy.context.collection      # Active collection

# UI context
bpy.context.window          # Current window
bpy.context.screen          # Current screen
bpy.context.area            # Current area
bpy.context.region          # Current region
```

## Context Override Pattern (Advanced)

**⚠️ Note**: `temp_override` is not in BlenderPythonDoc 4.4 - newer API

**From our successful debugging - working pattern:**
```python
def get_3d_viewport_context():
    """Get 3D viewport area for context operations."""
    areas_3d = [area for area in bpy.context.window.screen.areas 
                if area.type == 'VIEW_3D']
    
    if not areas_3d:
        return None
    
    area = areas_3d[0]
    
    # Find window region within the area
    regions_window = [region for region in area.regions 
                     if region.type == 'WINDOW']
    
    return area, regions_window[0] if regions_window else None

def context_override_simple(area):
    """Simple context override that works reliably."""
    return bpy.context.temp_override(area=area)

def context_override_complex(area, region):
    """Complex context override (less reliable)."""
    return bpy.context.temp_override(
        window=bpy.context.window,
        area=area,
        region=region
    )
```

## Context Requirements by Operation

**From our testing and debugging:**

### ✅ No Context Override Needed
```python
# These work in default context
bpy.ops.mesh.primitive_cube_add()
bpy.context.scene.objects
len(bpy.data.objects)
obj.location = (1, 2, 3)
```

### ⚠️ Context Override Required
```python
# These need 3D viewport context
bpy.ops.object.select_all()
bpy.ops.object.delete()
bpy.ops.object.mode_set()  # Sometimes
```

## Working Context Override Examples

**Scene clearing (from our fixes):**
```python
def clear_scene_with_context():
    """Clear scene with proper context management."""
    
    # Get 3D viewport area
    areas_3d = [area for area in bpy.context.window.screen.areas 
                if area.type == 'VIEW_3D']
    
    if areas_3d:
        area_3d = areas_3d[0]
        
        # Use simplified context override
        with bpy.context.temp_override(area=area_3d):
            # Ensure object mode
            if (bpy.context.active_object and 
                bpy.context.active_object.mode != 'OBJECT'):
                bpy.ops.object.mode_set(mode='OBJECT')
            
            # Select and delete
            bpy.ops.object.select_all(action='DESELECT')
            # ... selection logic ...
            bpy.ops.object.delete()
    else:
        # Fallback without context (may fail)
        raise RuntimeError("No 3D viewport available for context operations")
```

**Object creation with context (when needed):**
```python
def create_with_context_fallback(primitive_type, location):
    """Create primitive with context fallback."""
    
    # Try without context first (usually works)
    try:
        getattr(bpy.ops.mesh, f'primitive_{primitive_type}_add')(location=location)
        return bpy.context.active_object.name
        
    except RuntimeError as e:
        # Fallback with context override
        print(f"Retrying with context override: {e}")
        
        areas_3d = [area for area in bpy.context.window.screen.areas 
                    if area.type == 'VIEW_3D']
        
        if areas_3d:
            with bpy.context.temp_override(area=areas_3d[0]):
                getattr(bpy.ops.mesh, f'primitive_{primitive_type}_add')(location=location)
                return bpy.context.active_object.name
        else:
            raise RuntimeError("No 3D viewport available for context fallback")
```

## Mode Management

**Object mode requirements:**
```python
def ensure_object_mode():
    """Ensure we're in object mode for operations."""
    if bpy.context.active_object:
        if bpy.context.active_object.mode != 'OBJECT':
            # This may need context override
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except RuntimeError:
                print("Warning: Could not set object mode - context may be incorrect")
                return False
    return True

def safe_mode_set(mode='OBJECT'):
    """Set mode with context handling."""
    areas_3d = [area for area in bpy.context.window.screen.areas 
                if area.type == 'VIEW_3D']
    
    if areas_3d:
        with bpy.context.temp_override(area=areas_3d[0]):
            bpy.ops.object.mode_set(mode=mode)
    else:
        # Try without context (may fail)
        bpy.ops.object.mode_set(mode=mode)
```

## Context Debugging

**Check available context:**
```python
def debug_context():
    """Debug current context state."""
    print(f"Window: {bpy.context.window}")
    print(f"Screen: {bpy.context.screen}")
    print(f"Areas: {len(bpy.context.screen.areas) if bpy.context.screen else 0}")
    
    for i, area in enumerate(bpy.context.screen.areas if bpy.context.screen else []):
        print(f"  Area {i}: {area.type}")
        if area.type == 'VIEW_3D':
            regions = [r.type for r in area.regions]
            print(f"    Regions: {regions}")
    
    print(f"Active object: {bpy.context.active_object}")
    print(f"Selected: {len(bpy.context.selected_objects)}")

def check_3d_viewport():
    """Check if 3D viewport is available."""
    areas_3d = [area for area in bpy.context.window.screen.areas 
                if area.type == 'VIEW_3D']
    
    if not areas_3d:
        print("ERROR: No 3D viewport found")
        return False
    
    area = areas_3d[0]
    regions_window = [region for region in area.regions 
                     if region.type == 'WINDOW']
    
    if not regions_window:
        print("WARNING: No window region in 3D viewport")
    
    print(f"3D viewport available: {len(areas_3d)} areas, {len(regions_window)} window regions")
    return True
```

## Context Override Best Practices

**From our debugging experience:**

1. **Use minimal overrides**: `temp_override(area=area_3d)` works better than complex overrides
2. **Check area availability**: Always verify 3D viewport exists
3. **Object mode first**: Ensure object mode before selection/deletion operations
4. **Graceful fallbacks**: Try without context first, then with override
5. **Error handling**: Wrap context operations in try/catch blocks

**Pattern hierarchy:**
```python
def operation_with_context_hierarchy():
    """Try operations in order of reliability."""
    
    # 1. Try without context (works for many operations)
    try:
        return perform_operation()
    except RuntimeError:
        pass
    
    # 2. Try with simple area override
    areas_3d = [area for area in bpy.context.window.screen.areas 
                if area.type == 'VIEW_3D']
    
    if areas_3d:
        try:
            with bpy.context.temp_override(area=areas_3d[0]):
                return perform_operation()
        except RuntimeError:
            pass
    
    # 3. Last resort - complex override or alternative method
    # ... implement fallback strategy ...
    
    raise RuntimeError("All context strategies failed")
```

## Notes for blender-remote Testing

- **Context dependency**: Not all operations need context override
- **3D viewport required**: Most problematic operations need VIEW_3D area
- **Mode prerequisites**: Object mode often required before operations
- **Simplified overrides**: Use minimal context parameters for better reliability
- **Detection patterns**: Check for areas_3d availability before attempting overrides
- **Error indication**: "poll() failed" means context is incorrect