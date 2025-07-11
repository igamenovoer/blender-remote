# Data Persistence with MCP Tools

This example shows how to use data persistence through MCP tools for stateful LLM interactions.

## Prerequisites

1. Start Blender with BLD Remote MCP service
2. Start MCP server: `uvx blender-remote`
3. Configure your LLM IDE to use the MCP server

## Example Workflow

### 1. Store Scene Analysis

```
Store the current scene analysis for later use:

put_persist_data(
    key="scene_analysis", 
    data={
        "total_objects": 3,
        "mesh_objects": ["Cube", "Sphere", "Cylinder"],
        "lights": ["Light"],
        "cameras": ["Camera"],
        "analysis_date": "2025-07-11",
        "complexity_score": 85
    }
)
```

### 2. Multi-Step Animation Setup

**Step 1 - Store Animation Plan:**
```
put_persist_data(
    key="animation_plan",
    data={
        "target_objects": ["Cube", "Sphere"],
        "animation_type": "rotation",
        "duration_frames": 120,
        "keyframe_interval": 10
    }
)
```

**Step 2 - Calculate Keyframes:**
```python
# Get the animation plan
plan = get_persist_data(key="animation_plan")

# Execute code to calculate keyframes based on plan
execute_blender_code("""
import bpy
import math

# Get animation plan from persistence
import bld_remote
plan = bld_remote.persist.get_data("animation_plan")

keyframes = {}
for obj_name in plan["target_objects"]:
    obj = bpy.data.objects.get(obj_name)
    if obj:
        frames = []
        for frame in range(1, plan["duration_frames"] + 1, plan["keyframe_interval"]):
            angle = (frame / plan["duration_frames"]) * 2 * math.pi
            frames.append({
                "frame": frame,
                "rotation": [0, 0, angle]
            })
        keyframes[obj_name] = frames

# Store calculated keyframes
bld_remote.persist.put_data("calculated_keyframes", keyframes)
""")
```

**Step 3 - Apply Animation:**
```python
execute_blender_code("""
import bpy
import bld_remote

# Get keyframes from persistence
keyframes = bld_remote.persist.get_data("calculated_keyframes")

for obj_name, frames in keyframes.items():
    obj = bpy.data.objects.get(obj_name)
    if obj:
        for frame_data in frames:
            bpy.context.scene.frame_set(frame_data["frame"])
            obj.rotation_euler = frame_data["rotation"]
            obj.keyframe_insert(data_path="rotation_euler")
""")
```

### 3. Caching Expensive Operations

**Store expensive calculation:**
```python
execute_blender_code("""
import bpy
import bld_remote
import time

# Check if already calculated
cached = bld_remote.persist.get_data("mesh_complexity")
if cached is None:
    # Expensive calculation
    start_time = time.time()
    complexity_data = {}
    
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            mesh = obj.data
            complexity_data[obj.name] = {
                "vertices": len(mesh.vertices),
                "faces": len(mesh.polygons),
                "complexity_score": len(mesh.vertices) + len(mesh.polygons) * 2
            }
    
    processing_time = time.time() - start_time
    
    # Store with metadata
    result = {
        "data": complexity_data,
        "processing_time": processing_time,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    bld_remote.persist.put_data("mesh_complexity", result)
    print(f"Calculated complexity in {processing_time:.2f}s")
else:
    print(f"Using cached complexity from {cached['timestamp']}")
""")
```

**Retrieve cached data:**
```
complexity = get_persist_data(key="mesh_complexity")
```

### 4. Cross-Session State Management

**Initialize workflow state:**
```
put_persist_data(
    key="rendering_workflow",
    data={
        "current_step": 1,
        "total_steps": 5,
        "completed_tasks": [],
        "render_settings": {
            "quality": "high",
            "samples": 128,
            "resolution": [1920, 1080]
        }
    }
)
```

**Check and update state:**
```python
workflow = get_persist_data(key="rendering_workflow")

if workflow["current_step"] == 1:
    # Do step 1 work
    execute_blender_code("""
    # Configure render settings
    import bpy
    bpy.context.scene.cycles.samples = 128
    """)
    
    # Update workflow state
    workflow["current_step"] = 2
    workflow["completed_tasks"].append("render_settings_configured")
    put_persist_data(key="rendering_workflow", data=workflow)
```

### 5. Data Cleanup

**Remove specific data:**
```
remove_persist_data(key="scene_analysis")
```

**Check what's stored:**
```python
execute_blender_code("""
import bld_remote
keys = bld_remote.persist.get_keys()
info = bld_remote.persist.get_storage_info()
print(f"Stored keys: {keys}")
print(f"Storage info: {info}")
""")
```

## Tips for LLM Usage

1. **Use descriptive keys:** Instead of "data1", use "scene_analysis_2025_07_11"
2. **Store metadata:** Include timestamps, processing time, parameters used
3. **Check before computing:** Always check if expensive data is already cached
4. **Clean up:** Remove data when no longer needed to free memory
5. **Document state:** Store workflow step and progress information

## Common Patterns

### Progressive Enhancement
```
# Store basic data first
put_persist_data(key="basic_scene", data={"objects": 3})

# Enhance with more detail later
scene_data = get_persist_data(key="basic_scene")
scene_data["detailed_analysis"] = detailed_results
put_persist_data(key="basic_scene", data=scene_data)
```

### Conditional Processing
```python
# Only process if not already done
execute_blender_code("""
import bld_remote
if bld_remote.persist.get_data("materials_processed") is None:
    # Do expensive material processing
    process_materials()
    bld_remote.persist.put_data("materials_processed", True)
""")
```

### Error Recovery
```python
# Store intermediate results for error recovery
execute_blender_code("""
import bld_remote
try:
    # Risky operation
    result = complex_operation()
    bld_remote.persist.put_data("operation_result", result)
except Exception as e:
    # Restore from last known good state
    last_good = bld_remote.persist.get_data("last_good_state")
    if last_good:
        restore_state(last_good)
""")
```