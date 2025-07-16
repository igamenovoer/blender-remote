# Data Persistence

Store and retrieve data across multiple commands in the same Blender session.

## Overview

The data persistence feature allows you to:
- Store calculation results for later use
- Maintain state across multiple operations  
- Cache expensive computations
- Share data between different scripts

Data persists until Blender is closed or explicitly removed.

## Usage

### From Blender Scripts

```python
import bld_remote

# Store data
bld_remote.persist.put_data("my_result", {"vertices": 120, "faces": 200})

# Retrieve data
data = bld_remote.persist.get_data("my_result")
# Returns: {"vertices": 120, "faces": 200}

# Get with default
count = bld_remote.persist.get_data("missing_key", default=0)
# Returns: 0

# Remove data
bld_remote.persist.remove_data("my_result")

# Clear all data
bld_remote.persist.clear_data()
```

### From LLM Tools (MCP)

```python
# Store calculation result
put_persist_data(key="mesh_analysis", data={
    "total_vertices": 1540,
    "total_faces": 2980,
    "analysis_time": "2025-07-11T14:30:00"
})

# Retrieve in next command
result = get_persist_data(key="mesh_analysis")
# Access: result["total_vertices"]

# Remove when done
remove_persist_data(key="mesh_analysis")
```

### From Python Client

```python
from context.refcode.auto_mcp_remote.blender_mcp_client import BlenderMCPClient

client = BlenderMCPClient(port=6688)

# Store complex data
client.put_persist_data("scene_backup", {
    "objects": ["Cube", "Camera", "Light"],
    "materials": ["Material.001"],
    "timestamp": "2025-07-11"
})

# Retrieve data
backup = client.get_persist_data("scene_backup")
```

## Data Types

All Python data types are supported:
- Strings, numbers, booleans
- Lists and dictionaries
- Complex nested structures
- Custom objects (via pickle)

## Practical Examples

### Multi-step Animation
```python
# Step 1: Calculate keyframes
keyframes = calculate_complex_animation()
bld_remote.persist.put_data("animation_data", keyframes)

# Step 2: Apply to objects (separate command)
keyframes = bld_remote.persist.get_data("animation_data")
apply_keyframes_to_objects(keyframes)
```

### Caching Expensive Operations
```python
# Check if already calculated
cached = bld_remote.persist.get_data("mesh_subdivision")
if cached is None:
    # Expensive calculation
    result = perform_complex_subdivision()
    bld_remote.persist.put_data("mesh_subdivision", result)
else:
    result = cached
```

### Cross-command State
```python
# Initialize workflow state
bld_remote.persist.put_data("workflow_step", 1)
bld_remote.persist.put_data("processed_objects", [])

# Later commands can check and update state
step = bld_remote.persist.get_data("workflow_step")
if step == 1:
    # Do step 1 work
    bld_remote.persist.put_data("workflow_step", 2)
```

## Notes

- Data is stored in memory only (not saved to .blend file)
- Data persists until Blender is closed
- Keys are case-sensitive strings
- No size limits, but large data uses more memory