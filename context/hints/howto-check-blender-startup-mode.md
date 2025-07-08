# How to Check Blender Startup Mode (Background vs GUI)

## Overview

When developing Blender add-ons that need to work in both GUI mode and background mode (`blender --background`), you need to detect which mode Blender is running in to adapt your code accordingly.

## Primary Method: `bpy.app.background`

The most reliable way to detect if Blender is running in background mode is using the `bpy.app.background` property:

```python
import bpy

if bpy.app.background:
    print("Blender is running in background mode (headless)")
    # Background mode logic here
else:
    print("Blender is running in GUI mode")
    # GUI mode logic here
```

### Property Details

- **Type**: `bool`
- **Value**: `True` when running with `blender --background` or `blender -b`
- **Value**: `False` when running with GUI (normal `blender` command)
- **Availability**: Available in all Blender versions with Python API

## Alternative Methods

### 1. Check for Window Manager

In background mode, certain GUI-related components are not available:

```python
import bpy

def is_background_mode():
    """Alternative method to check background mode"""
    try:
        # In background mode, window manager might not be fully initialized
        wm = bpy.context.window_manager
        return wm is None or len(wm.windows) == 0
    except:
        return True  # Assume background if context is not available
```

### 2. Check for Display Context

```python
import bpy

def has_display_context():
    """Check if display/GUI context is available"""
    try:
        # These will be None or unavailable in background mode
        return (bpy.context.screen is not None and 
                bpy.context.area is not None and 
                bpy.context.region is not None)
    except:
        return False
```

## Practical Usage Examples

### Example 1: Conditional Service Startup

```python
import bpy

def start_addon_service():
    """Start service with mode-appropriate configuration"""
    if bpy.app.background:
        # Background mode: Use asyncio event loop
        print("Starting service in background mode...")
        start_background_service()
    else:
        # GUI mode: Use modal operators
        print("Starting service in GUI mode...")
        start_gui_service()

def start_background_service():
    """Background-specific startup logic"""
    # Use asyncio for background operations
    import asyncio
    # Ensure event loop is running
    pass

def start_gui_service():
    """GUI-specific startup logic"""
    # Use modal operators for GUI operations
    pass
```

### Example 2: Viewport Operations

```python
import bpy

def take_screenshot():
    """Take screenshot with mode-appropriate method"""
    if bpy.app.background:
        # Background mode: Use offscreen rendering
        print("Background mode: Using offscreen rendering")
        return render_offscreen()
    else:
        # GUI mode: Use viewport capture
        print("GUI mode: Capturing viewport")
        return capture_viewport()

def render_offscreen():
    """Offscreen rendering for background mode"""
    # Set up offscreen rendering context
    pass

def capture_viewport():
    """Viewport capture for GUI mode"""
    # Access viewport directly
    pass
```

### Example 3: UI Registration

```python
import bpy

def register_ui():
    """Register UI components only in GUI mode"""
    if not bpy.app.background:
        # Only register panels/menus in GUI mode
        bpy.utils.register_class(MyPanel)
        bpy.utils.register_class(MyOperator)
        print("UI components registered for GUI mode")
    else:
        print("Background mode: Skipping UI registration")
```

## Common Patterns for Background Compatibility

### 1. Service Architecture

```python
class BlenderService:
    def __init__(self):
        self.is_background = bpy.app.background
        self.setup_mode_specific_components()
    
    def setup_mode_specific_components(self):
        if self.is_background:
            self.setup_background_components()
        else:
            self.setup_gui_components()
    
    def setup_background_components(self):
        # Background-specific setup
        pass
    
    def setup_gui_components(self):
        # GUI-specific setup
        pass
```

### 2. Event Loop Management

```python
import bpy
import asyncio

def ensure_event_loop():
    """Ensure asyncio event loop is available"""
    if bpy.app.background:
        # Background mode needs explicit event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop
    else:
        # GUI mode: Use modal operators instead
        return None
```

## Important Considerations

### Background Mode Limitations

1. **No GUI Context**: `bpy.context.screen`, `bpy.context.area`, `bpy.context.region` are `None`
2. **No Window Manager**: Limited or no window manager functionality
3. **No Modal Operators**: Standard GUI modal operators don't work
4. **No Viewport Access**: Direct viewport operations are not available
5. **No User Interaction**: No mouse/keyboard events

### GUI Mode Advantages

1. **Full Context Available**: All GUI contexts are accessible
2. **Modal Operators**: Can use Blender's modal operator system
3. **Viewport Access**: Direct access to 3D viewport
4. **User Interaction**: Full mouse/keyboard event handling

## Best Practices

1. **Always Check Mode**: Use `bpy.app.background` at the start of your addon
2. **Graceful Degradation**: Provide alternative functionality for background mode
3. **Separate Logic**: Keep background and GUI logic in separate functions
4. **Test Both Modes**: Test your addon in both GUI and background modes
5. **Document Limitations**: Clearly document what works in each mode

## Related Resources

- **Blender Python API Docs**: `bpy.app` module documentation
- **Background Rendering**: Blender manual on headless rendering
- **Modal Operators**: Blender operator system for GUI interactions
- **Asyncio Integration**: Python asyncio for background services

## Example Implementation

See the BLD Remote MCP service implementation in this project:
- `blender_addon/bld_remote_mcp/` - Background-compatible MCP service
- Uses `bpy.app.background` for mode detection
- Implements different startup patterns for each mode
