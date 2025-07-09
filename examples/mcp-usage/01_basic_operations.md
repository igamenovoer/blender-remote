# Basic Operations Examples

These examples demonstrate fundamental MCP server operations for scene inspection, object queries, and basic code execution.

## Example 1: Scene Inspection

### Description
Get comprehensive information about the current Blender scene including all objects, materials, and settings.

### LLM Prompt
```
What objects are currently in the Blender scene? Show me details about each object including their positions and types.
```

### Expected Result
The MCP server will use `get_scene_info()` and return:
- Scene name and basic properties
- List of all objects with names, types, and positions
- Material information
- Frame range details

### Example Response
```json
{
  "scene_name": "Scene",
  "total_objects": 3,
  "objects": [
    {
      "name": "Cube",
      "type": "MESH",
      "location": [0.0, 0.0, 0.0],
      "visible": true
    },
    {
      "name": "Camera",
      "type": "CAMERA", 
      "location": [7.36, -6.93, 4.96],
      "visible": true
    },
    {
      "name": "Light",
      "type": "LIGHT",
      "location": [4.08, 1.01, 5.90],
      "visible": true
    }
  ]
}
```

### Variations
- "List only the mesh objects in the scene"
- "Show me all materials and which objects use them"
- "What's the current frame range and active camera?"

---

## Example 2: Object Detailed Inspection

### Description
Get detailed information about a specific object including geometry, materials, and modifiers.

### LLM Prompt
```
Tell me everything about the Cube object - its dimensions, materials, vertex count, and any modifiers.
```

### Expected Result
The MCP server will use `get_object_info("Cube")` and return:
- Object properties (location, rotation, scale, dimensions)
- Mesh information (vertex count, face count)
- Material assignments
- Modifier information
- Constraints

### Example Response
```json
{
  "name": "Cube",
  "type": "MESH",
  "location": [0.0, 0.0, 0.0],
  "rotation": [0.0, 0.0, 0.0],
  "scale": [1.0, 1.0, 1.0],
  "dimensions": [2.0, 2.0, 2.0],
  "vertex_count": 8,
  "face_count": 6,
  "material_slots": ["Material"],
  "modifier_count": 0
}
```

### Variations
- "What are the exact dimensions of the Camera object?"
- "Show me the material setup for the Light object"
- "Which objects have modifiers applied?"

---

## Example 3: Connection Health Check

### Description
Verify that the MCP server is connected to Blender and get system information.

### LLM Prompt
```
Check if the Blender MCP service is running and show me the connection status.
```

### Expected Result
The MCP server will use `check_connection_status()` and return:
- Connection status
- Blender version information
- Service uptime
- Current mode (GUI/Background)
- Memory usage

### Example Response
```json
{
  "status": "connected",
  "service": "BLD_Remote_MCP",
  "port": 6688,
  "blender_version": "4.4.3",
  "mode": "GUI",
  "uptime": "00:15:23",
  "scene_name": "Scene",
  "object_count": 3
}
```

### Variations
- "Is Blender running in GUI or background mode?"
- "How long has the service been running?"
- "What version of Blender is being used?"

---

## Example 4: Basic Code Execution

### Description
Execute simple Python code in Blender to perform basic operations.

### LLM Prompt
```
Add a simple message to the Blender console saying "Hello from MCP server!"
```

### Expected Result
The MCP server will use `execute_blender_code()` with:
```python
print("Hello from MCP server!")
```

### Example Response
```json
{
  "status": "success",
  "result": "Code executed successfully",
  "output": "Hello from MCP server!\n"
}
```

### Variations
- "Print the current scene name"
- "Show me the number of objects in the scene"
- "Display the active camera name"

---

## Example 5: Object Creation (Basic)

### Description
Create a simple object using Blender's operators.

### LLM Prompt
```
Create a new sphere at position (2, 0, 0) in the scene.
```

### Expected Result
The MCP server will execute:
```python
import bpy
bpy.ops.mesh.primitive_uv_sphere_add(location=(2, 0, 0))
```

### Example Response
```json
{
  "status": "success",
  "result": "Code executed successfully",
  "output": "Created sphere at (2, 0, 0)\n"
}
```

### Follow-up Verification
```
Now show me the updated scene information to confirm the sphere was created.
```

### Variations
- "Add a cylinder at the origin"
- "Create a cube at position (-1, -1, 0)"
- "Add a torus at position (0, 2, 1)"

---

## Example 6: Object Property Queries

### Description
Query specific properties of objects without getting full object information.

### LLM Prompt
```
What is the exact location of the Camera object?
```

### Expected Result
The MCP server will use `get_object_info("Camera")` and extract the location:
```json
{
  "location": [7.36, -6.93, 4.96]
}
```

### Variations
- "What is the scale of the Cube object?"
- "Show me the rotation values for the Light"
- "What are the dimensions of all mesh objects?"

---

## Example 7: Material Information

### Description
Get information about materials in the scene.

### LLM Prompt
```
List all materials in the scene and tell me which objects use each material.
```

### Expected Result
The MCP server will combine `get_scene_info()` with object queries to show:
- All materials in the scene
- Which objects use each material
- Material properties

### Example Response
```json
{
  "materials": [
    {
      "name": "Material",
      "used_by": ["Cube"]
    },
    {
      "name": "Material.001", 
      "used_by": ["Sphere"]
    }
  ]
}
```

### Variations
- "Which objects don't have materials assigned?"
- "Show me all unique materials in the scene"
- "What material is the Cube using?"

---

## Example 8: Frame Range Information

### Description
Get information about animation and frame settings.

### LLM Prompt
```
What is the current frame range and what frame are we on?
```

### Expected Result
The MCP server will use `get_scene_info()` to return:
- Current frame number
- Frame start and end values
- Animation settings

### Example Response
```json
{
  "current_frame": 1,
  "frame_range": [1, 250],
  "frame_start": 1,
  "frame_end": 250
}
```

### Variations
- "Set the frame range to 1-120"
- "Go to frame 50"
- "What is the current playback frame?"

---

## Example 9: Visibility and Selection

### Description
Query object visibility and selection states.

### LLM Prompt
```
Which objects are currently visible in the scene?
```

### Expected Result
The MCP server will use `get_scene_info()` and filter for visible objects:
```json
{
  "visible_objects": [
    {"name": "Cube", "visible": true},
    {"name": "Camera", "visible": true}, 
    {"name": "Light", "visible": true}
  ]
}
```

### Variations
- "Hide the Cube object"
- "Show only mesh objects"
- "Select all objects in the scene"

---

## Example 10: Basic Error Handling

### Description
Handle common errors gracefully when objects don't exist or operations fail.

### LLM Prompt
```
Tell me about the object named "NonExistentObject"
```

### Expected Result
The MCP server will return a clear error message:
```json
{
  "status": "error",
  "message": "Object 'NonExistentObject' not found in scene"
}
```

### Follow-up Prompt
```
That's okay. Show me what objects do exist in the scene.
```

### Variations
- "Delete an object that doesn't exist"
- "Move a non-existent object"
- "Get material info for missing object"

---

## Workflow Examples

### Complete Scene Analysis Workflow

1. **Check Connection**
   ```
   Check if Blender is connected and running properly.
   ```

2. **Get Scene Overview**
   ```
   What objects are in the current scene?
   ```

3. **Detailed Object Analysis**
   ```
   Tell me more details about each mesh object in the scene.
   ```

4. **Material Analysis**
   ```
   Show me all materials and their assignments.
   ```

5. **Summary Report**
   ```
   Give me a summary of the current scene setup.
   ```

### Health Monitoring Workflow

1. **Service Status**
   ```
   Check the MCP service status and connection health.
   ```

2. **System Information**
   ```
   What version of Blender is running and in what mode?
   ```

3. **Scene Statistics**
   ```
   How many objects, materials, and lights are in the scene?
   ```

4. **Performance Check**
   ```
   Show me the current memory usage and uptime.
   ```

---

## Best Practices for Basic Operations

### Effective Prompting
- **Be specific**: Ask for exact information you need
- **Use follow-ups**: Build on previous responses
- **Verify results**: Always check if operations succeeded
- **Handle errors**: Gracefully handle missing objects or failed operations

### Performance Tips
- **Batch queries**: Get multiple pieces of information in one request
- **Use appropriate detail**: Don't request full scene info when you only need object count
- **Cache results**: Use previous responses to avoid redundant queries

### Error Prevention
- **Check existence**: Verify objects exist before querying details
- **Validate names**: Use exact object names (case-sensitive)
- **Handle modes**: Account for GUI vs background mode differences

---

**Next: Continue with [Object Creation Examples](02_object_creation.md) for more advanced operations!**