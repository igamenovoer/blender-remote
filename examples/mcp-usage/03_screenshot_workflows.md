# Screenshot Workflows

These examples demonstrate how to effectively use the screenshot functionality of the MCP server for visual feedback and analysis.

## Important Note

**Screenshots require GUI mode**: The `get_viewport_screenshot()` tool only works when Blender is running in GUI mode. In background mode, it returns a clear error message.

## Example 1: Basic Screenshot Capture

### Description
Capture a basic screenshot of the current viewport for visual confirmation.

### LLM Prompt
```
Take a screenshot of the current Blender viewport so I can see what's in the scene.
```

### Expected Result
The MCP server will use `get_viewport_screenshot()` and return:
- Base64 encoded image data
- Image dimensions and file size
- MIME type information

### Example Response
```json
{
  "type": "image",
  "data": "iVBORw0KGgoAAAANSUhEUgAAA...",
  "mimeType": "image/png",
  "size": 61868,
  "dimensions": {
    "width": 800,
    "height": 600
  }
}
```

### Variations
- "Show me what the scene looks like now"
- "Capture the current viewport"
- "Take a screenshot for reference"

---

## Example 2: High-Quality Screenshot

### Description
Capture a high-resolution screenshot for detailed analysis.

### LLM Prompt
```
Take a high-resolution screenshot of the viewport, maximum 1920 pixels, in PNG format.
```

### Expected Result
The MCP server will use `get_viewport_screenshot(max_size=1920, format="PNG")` and return a high-quality image.

### Technical Details
- **Max Size**: 1920 pixels for the largest dimension
- **Format**: PNG for lossless quality
- **File Management**: Automatic UUID-based naming and cleanup

### Variations
- "Capture a 4K quality screenshot"
- "Take a detailed screenshot for analysis"
- "Get a high-resolution image of the scene"

---

## Example 3: Iterative Design with Visual Feedback

### Description
Create objects, take screenshots, and iterate based on visual feedback.

### LLM Prompt
```
Create a red cube in the center of the scene, then take a screenshot so I can see how it looks.
```

### Step-by-Step Workflow

1. **Create Object**
   ```python
   import bpy
   
   # Create red cube
   bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
   cube = bpy.context.active_object
   cube.name = "RedCube"
   
   # Create red material
   red_mat = bpy.data.materials.new(name="RedMaterial")
   red_mat.use_nodes = True
   red_mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (1.0, 0.0, 0.0, 1.0)
   cube.data.materials.append(red_mat)
   ```

2. **Take Screenshot**
   The MCP server captures the viewport showing the red cube.

3. **Follow-up Iteration**
   ```
   The cube looks good, but can you make it blue instead and move it slightly to the right?
   ```

### Expected Workflow
- Object creation → Screenshot → Analysis → Modification → Screenshot → Repeat

### Variations
- "Create a sphere and show me how it looks with different materials"
- "Add lighting and take screenshots to compare different setups"
- "Create a scene and iterate on the composition"

---

## Example 4: Composition Analysis

### Description
Use screenshots to analyze scene composition and make improvements.

### LLM Prompt
```
Create a simple product showcase scene with a cube, add some lighting, then take a screenshot and analyze the composition.
```

### Expected Workflow

1. **Create Scene**
   ```python
   import bpy
   
   # Create product (cube)
   bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
   cube = bpy.context.active_object
   
   # Add materials
   mat = bpy.data.materials.new(name="ProductMaterial")
   mat.use_nodes = True
   principled = mat.node_tree.nodes["Principled BSDF"]
   principled.inputs["Base Color"].default_value = (0.2, 0.6, 0.8, 1.0)
   principled.inputs["Metallic"].default_value = 0.7
   principled.inputs["Roughness"].default_value = 0.1
   cube.data.materials.append(mat)
   
   # Add ground plane
   bpy.ops.mesh.primitive_plane_add(location=(0, 0, -1), size=10)
   
   # Add lighting
   bpy.ops.object.light_add(type='SUN', location=(4, 4, 8))
   sun = bpy.context.active_object
   sun.data.energy = 5.0
   
   # Position camera
   bpy.context.scene.camera.location = (3, -3, 2)
   bpy.context.scene.camera.rotation_euler = (1.1, 0, 0.8)
   ```

2. **Take Screenshot**
   Capture the current composition.

3. **Analysis Follow-up**
   ```
   Based on the screenshot, how can I improve the lighting and composition?
   ```

### Expected Analysis
The LLM can analyze the screenshot and suggest:
- Lighting improvements
- Camera angle adjustments
- Object positioning
- Material modifications

### Variations
- "Create an architectural scene and analyze the lighting"
- "Set up a character scene and evaluate the composition"
- "Design a logo presentation and optimize the setup"

---

## Example 5: Before/After Comparison

### Description
Take screenshots before and after modifications to compare changes.

### LLM Prompt
```
First, take a screenshot of the current scene as a "before" reference, then add better lighting and materials, and take an "after" screenshot to compare.
```

### Step-by-Step Process

1. **Before Screenshot**
   ```
   Take a screenshot of the current scene state.
   ```

2. **Make Improvements**
   ```python
   import bpy
   
   # Improve lighting
   bpy.ops.object.light_add(type='AREA', location=(-2, -2, 4))
   area_light = bpy.context.active_object
   area_light.data.energy = 50.0
   area_light.data.size = 2.0
   
   # Add rim light
   bpy.ops.object.light_add(type='SPOT', location=(2, 2, 3))
   spot_light = bpy.context.active_object
   spot_light.data.energy = 30.0
   spot_light.data.spot_size = 0.5
   
   # Improve materials on existing objects
   for obj in bpy.context.scene.objects:
       if obj.type == 'MESH' and obj.data.materials:
           mat = obj.data.materials[0]
           if mat.use_nodes:
               principled = mat.node_tree.nodes["Principled BSDF"]
               principled.inputs["Roughness"].default_value = 0.2
   ```

3. **After Screenshot**
   ```
   Now take another screenshot to see the improvements.
   ```

4. **Comparison**
   ```
   Compare the before and after screenshots and tell me what improved.
   ```

### Expected Comparison
The LLM can compare the two images and identify:
- Lighting quality improvements
- Material appearance changes
- Overall scene quality enhancements

### Variations
- "Compare different camera angles"
- "Show before/after material changes"
- "Demonstrate different lighting setups"

---

## Example 6: Multi-Angle Documentation

### Description
Take screenshots from different angles to document a 3D object or scene.

### LLM Prompt
```
Create a interesting 3D object, then take screenshots from 4 different angles (front, side, top, perspective) to document it completely.
```

### Implementation

1. **Create Object**
   ```python
   import bpy
   import bmesh
   
   # Create interesting object (twisted cube)
   bpy.ops.mesh.primitive_cube_add()
   cube = bpy.context.active_object
   
   # Add twist modifier
   twist = cube.modifiers.new(name="Twist", type='SIMPLE_DEFORM')
   twist.deform_method = 'TWIST'
   twist.angle = 1.0
   
   # Add material
   mat = bpy.data.materials.new(name="TwistMaterial")
   mat.use_nodes = True
   principled = mat.node_tree.nodes["Principled BSDF"]
   principled.inputs["Base Color"].default_value = (0.8, 0.3, 0.1, 1.0)
   principled.inputs["Metallic"].default_value = 0.8
   cube.data.materials.append(mat)
   ```

2. **Set Camera Positions and Capture**
   ```python
   import bpy
   from mathutils import Vector
   
   camera = bpy.context.scene.camera
   
   # Front view
   camera.location = (0, -5, 0)
   camera.rotation_euler = (1.5708, 0, 0)  # 90 degrees
   # Take screenshot here
   
   # Side view
   camera.location = (5, 0, 0)
   camera.rotation_euler = (1.5708, 0, 1.5708)
   # Take screenshot here
   
   # Top view
   camera.location = (0, 0, 5)
   camera.rotation_euler = (0, 0, 0)
   # Take screenshot here
   
   # Perspective view
   camera.location = (3, -3, 2)
   camera.rotation_euler = (1.1, 0, 0.8)
   # Take screenshot here
   ```

### Workflow Prompts
```
1. Take a screenshot from the front view
2. Move camera to side view and take another screenshot
3. Set up top view and capture
4. Finally, set up a nice perspective view and take a final screenshot
```

### Variations
- "Document a character model from multiple angles"
- "Create technical drawings with orthographic views"
- "Show a product from customer viewpoints"

---

## Example 7: Animation Frame Capture

### Description
Capture screenshots at different animation frames to show motion.

### LLM Prompt
```
Create a simple animation of a cube rotating, then take screenshots at different frames to show the motion sequence.
```

### Implementation

1. **Create Animation**
   ```python
   import bpy
   
   # Create cube
   bpy.ops.mesh.primitive_cube_add()
   cube = bpy.context.active_object
   
   # Set up animation
   bpy.context.scene.frame_start = 1
   bpy.context.scene.frame_end = 60
   
   # Keyframe initial rotation
   bpy.context.scene.frame_set(1)
   cube.rotation_euler = (0, 0, 0)
   cube.keyframe_insert(data_path="rotation_euler")
   
   # Keyframe final rotation
   bpy.context.scene.frame_set(60)
   cube.rotation_euler = (0, 0, 6.28)  # Full rotation
   cube.keyframe_insert(data_path="rotation_euler")
   
   # Add material
   mat = bpy.data.materials.new(name="AnimMaterial")
   mat.use_nodes = True
   principled = mat.node_tree.nodes["Principled BSDF"]
   principled.inputs["Base Color"].default_value = (0.1, 0.8, 0.3, 1.0)
   cube.data.materials.append(mat)
   ```

2. **Capture Sequence**
   ```python
   # Go to frame 1
   bpy.context.scene.frame_set(1)
   # Take screenshot
   
   # Go to frame 20
   bpy.context.scene.frame_set(20)
   # Take screenshot
   
   # Go to frame 40
   bpy.context.scene.frame_set(40)
   # Take screenshot
   
   # Go to frame 60
   bpy.context.scene.frame_set(60)
   # Take screenshot
   ```

### Workflow Prompts
```
1. Set the timeline to frame 1 and take a screenshot
2. Jump to frame 20 and capture the rotation
3. Go to frame 40 and take another screenshot
4. Finally, go to frame 60 and show the complete rotation
```

### Variations
- "Create a bouncing ball animation and capture key frames"
- "Show a camera flythrough with screenshots"
- "Document a character animation sequence"

---

## Example 8: Error Handling - Background Mode

### Description
Demonstrate proper error handling when screenshots are requested in background mode.

### LLM Prompt
```
Take a screenshot of the current scene.
```

### When in Background Mode
The MCP server will return:
```json
{
  "status": "error",
  "message": "Screenshot capture is not supported in background mode. Please run Blender in GUI mode for screenshot functionality."
}
```

### Graceful Handling
```
I understand screenshots aren't available in background mode. Instead, can you tell me what objects are in the scene and their positions?
```

### Alternative Workflow
When screenshots aren't available:
1. Use `get_scene_info()` for scene overview
2. Use `get_object_info()` for detailed object information
3. Use code execution to analyze scene properties
4. Create detailed text descriptions of the scene

### Variations
- "Describe the scene layout without screenshots"
- "Generate a text-based scene report"
- "Create a scene summary for documentation"

---

## Example 9: Screenshot Size Optimization

### Description
Choose appropriate screenshot sizes for different use cases.

### Different Size Use Cases

1. **Quick Preview** (400px)
   ```
   Take a small screenshot just for a quick preview of the scene.
   ```

2. **Standard Review** (800px - default)
   ```
   Take a screenshot for standard review and analysis.
   ```

3. **High Detail** (1200px)
   ```
   Take a detailed screenshot for close inspection.
   ```

4. **Presentation Quality** (1920px)
   ```
   Take a high-resolution screenshot for presentation purposes.
   ```

### Size Recommendations
- **400px**: Quick LLM analysis, fast response
- **800px**: Standard workflow, good balance
- **1200px**: Detailed analysis, material review
- **1920px**: Final presentation, high-quality output

### Performance Considerations
- Larger screenshots take longer to process
- More memory usage for large images
- Network transfer time for base64 data
- LLM processing time for large images

### Variations
- "Take a thumbnail screenshot for quick reference"
- "Capture a high-res image for detailed analysis"
- "Generate a screenshot optimized for mobile viewing"

---

## Example 10: Visual Debugging Workflow

### Description
Use screenshots to debug scene issues and make corrections.

### LLM Prompt
```
I'm having trouble with my scene lighting. Take a screenshot, analyze what's wrong, and suggest fixes.
```

### Debugging Process

1. **Capture Current State**
   ```
   Take a screenshot of the current scene to see the lighting issues.
   ```

2. **Analysis**
   The LLM can analyze the screenshot for:
   - Lighting problems (too dark, too bright, harsh shadows)
   - Composition issues (objects not visible, bad angles)
   - Material problems (incorrect colors, reflection issues)

3. **Implement Fixes**
   ```python
   import bpy
   
   # Example fixes based on analysis
   # Add fill lighting
   bpy.ops.object.light_add(type='AREA', location=(-2, -2, 3))
   fill_light = bpy.context.active_object
   fill_light.data.energy = 20.0
   fill_light.data.size = 3.0
   
   # Adjust existing lights
   for obj in bpy.context.scene.objects:
       if obj.type == 'LIGHT':
           obj.data.energy *= 0.7  # Reduce harsh lighting
   ```

4. **Verify Fixes**
   ```
   Take another screenshot to see if the lighting improvements worked.
   ```

### Common Issues to Debug
- **Too Dark**: Add more lights or increase energy
- **Too Bright**: Reduce light energy or add diffusion
- **Harsh Shadows**: Add fill lighting or soften existing lights
- **Poor Composition**: Adjust camera position or object placement
- **Material Issues**: Modify roughness, metallic, or color values

### Variations
- "Debug shadow issues in the scene"
- "Fix overexposed areas in the render"
- "Correct color balance problems"

---

## Best Practices for Screenshot Workflows

### Planning Your Shots
1. **Define Purpose**: Know why you're taking the screenshot
2. **Choose Appropriate Size**: Match resolution to use case
3. **Consider Lighting**: Ensure adequate lighting for visibility
4. **Frame Composition**: Position camera for best view

### Efficient Workflows
1. **Use Descriptive Requests**: Be specific about what you want to see
2. **Iterate Systematically**: Make one change at a time
3. **Document Changes**: Keep track of what you've modified
4. **Save Important Views**: Note camera positions for good angles

### Error Prevention
1. **Check GUI Mode**: Ensure Blender is in GUI mode for screenshots
2. **Verify Viewport**: Make sure viewport is visible and active
3. **Test Incrementally**: Take screenshots after each major change
4. **Handle Failures**: Have fallback plans for when screenshots fail

### Advanced Techniques
1. **Automated Documentation**: Create consistent camera angles
2. **Comparative Analysis**: Use before/after techniques
3. **Multi-angle Coverage**: Document from multiple perspectives
4. **Animation Sequences**: Capture motion over time

---

## Troubleshooting Screenshot Issues

### Common Problems

**No Image Returned**
- Check if Blender is in GUI mode
- Verify viewport is active and visible
- Ensure no modal operators are running

**Poor Image Quality**
- Increase screenshot size
- Improve scene lighting
- Check camera position and angle

**Slow Performance**
- Reduce screenshot size
- Simplify scene complexity
- Use JPEG format for smaller files

**Memory Issues**
- Use smaller screenshot sizes
- Clear unused materials and objects
- Restart Blender if necessary

### Debug Commands
```python
# Check current mode
import bpy
print(bpy.app.background)  # True if background mode

# Check viewport
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        print(f"3D Viewport found: {area}")

# Check camera
print(f"Active camera: {bpy.context.scene.camera}")
```

---

**Next: Continue with [Complex Scene Creation](04_complex_scenes.md) to learn about building complete scenes with multiple objects and advanced features!**