# Object Creation Examples

These examples demonstrate how to create, modify, and manipulate objects in Blender using the MCP server.

## Example 1: Basic Primitive Creation

### Description
Create basic primitive objects (cube, sphere, cylinder) at different positions.

### LLM Prompt
```
Create a blue cube at position (0, 0, 0), a red sphere at (2, 0, 0), and a green cylinder at (-2, 0, 0).
```

### Expected Result
The MCP server will execute:
```python
import bpy

# Create cube
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "BlueCube"

# Create blue material for cube
blue_mat = bpy.data.materials.new(name="BlueMaterial")
blue_mat.use_nodes = True
blue_mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.0, 0.0, 1.0, 1.0)
cube.data.materials.append(blue_mat)

# Create sphere
bpy.ops.mesh.primitive_uv_sphere_add(location=(2, 0, 0))
sphere = bpy.context.active_object
sphere.name = "RedSphere"

# Create red material for sphere
red_mat = bpy.data.materials.new(name="RedMaterial")
red_mat.use_nodes = True
red_mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (1.0, 0.0, 0.0, 1.0)
sphere.data.materials.append(red_mat)

# Create cylinder
bpy.ops.mesh.primitive_cylinder_add(location=(-2, 0, 0))
cylinder = bpy.context.active_object
cylinder.name = "GreenCylinder"

# Create green material for cylinder
green_mat = bpy.data.materials.new(name="GreenMaterial")
green_mat.use_nodes = True
green_mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.0, 1.0, 0.0, 1.0)
cylinder.data.materials.append(green_mat)

print("Created three colored primitives")
```

### Verification
```
Show me the updated scene information to confirm all objects were created with the correct materials.
```

### Variations
- "Create a purple torus at (0, 0, 2)"
- "Add a yellow plane at (0, -2, 0)"
- "Create an orange icosphere at (0, 2, 0)"

---

## Example 2: Object with Custom Properties

### Description
Create an object with specific scale, rotation, and custom properties.

### LLM Prompt
```
Create a cube at (1, 1, 1) that is scaled to 1.5 times its original size, rotated 45 degrees around the Z-axis, and has a metallic gold material.
```

### Expected Result
```python
import bpy
import bmesh
from mathutils import Euler
import math

# Create cube at specified location
bpy.ops.mesh.primitive_cube_add(location=(1, 1, 1))
cube = bpy.context.active_object
cube.name = "GoldCube"

# Set scale
cube.scale = (1.5, 1.5, 1.5)

# Set rotation (45 degrees = π/4 radians)
cube.rotation_euler = Euler((0, 0, math.radians(45)), 'XYZ')

# Create metallic gold material
gold_mat = bpy.data.materials.new(name="GoldMaterial")
gold_mat.use_nodes = True
nodes = gold_mat.node_tree.nodes
principled = nodes["Principled BSDF"]

# Set gold color and metallic properties
principled.inputs["Base Color"].default_value = (1.0, 0.766, 0.336, 1.0)  # Gold color
principled.inputs["Metallic"].default_value = 1.0
principled.inputs["Roughness"].default_value = 0.2

# Apply material to cube
cube.data.materials.append(gold_mat)

print(f"Created {cube.name} with scale {cube.scale} and rotation {cube.rotation_euler}")
```

### Verification
```
Tell me the exact scale, rotation, and material properties of the GoldCube object.
```

### Variations
- "Create a silver cylinder rotated 30 degrees around the X-axis"
- "Make a bronze sphere that's half the normal size"
- "Create a copper torus with a rough surface finish"

---

## Example 3: Complex Object with Modifiers

### Description
Create an object and apply modifiers to it.

### LLM Prompt
```
Create a cube and add a subdivision surface modifier and a bevel modifier to make it look smoother.
```

### Expected Result
```python
import bpy

# Create cube
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "SmoothCube"

# Add subdivision surface modifier
subsurf = cube.modifiers.new(name="SubSurf", type='SUBSURF')
subsurf.levels = 2
subsurf.render_levels = 2

# Add bevel modifier
bevel = cube.modifiers.new(name="Bevel", type='BEVEL')
bevel.width = 0.05
bevel.segments = 3

# Create a material for the smooth cube
smooth_mat = bpy.data.materials.new(name="SmoothMaterial")
smooth_mat.use_nodes = True
principled = smooth_mat.node_tree.nodes["Principled BSDF"]
principled.inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1.0)
principled.inputs["Roughness"].default_value = 0.1

cube.data.materials.append(smooth_mat)

print(f"Created {cube.name} with {len(cube.modifiers)} modifiers")
```

### Verification
```
Show me the details of the SmoothCube object including its modifiers.
```

### Variations
- "Add a mirror modifier to the cube"
- "Create a cylinder with an array modifier"
- "Make a sphere with a displace modifier"

---

## Example 4: Text Object Creation

### Description
Create and customize text objects in Blender.

### LLM Prompt
```
Create a 3D text object that says "Hello MCP" with a red material and extrude it to give it depth.
```

### Expected Result
```python
import bpy

# Create text object
bpy.ops.object.text_add(location=(0, 0, 0))
text_obj = bpy.context.active_object
text_obj.name = "HelloMCP"

# Set text content
text_obj.data.body = "Hello MCP"

# Configure text properties
text_obj.data.extrude = 0.1  # Give depth
text_obj.data.bevel_depth = 0.01  # Add bevel
text_obj.data.bevel_resolution = 3

# Create red material
red_mat = bpy.data.materials.new(name="RedTextMaterial")
red_mat.use_nodes = True
principled = red_mat.node_tree.nodes["Principled BSDF"]
principled.inputs["Base Color"].default_value = (1.0, 0.0, 0.0, 1.0)
principled.inputs["Metallic"].default_value = 0.5
principled.inputs["Roughness"].default_value = 0.3

text_obj.data.materials.append(red_mat)

print(f"Created 3D text: '{text_obj.data.body}'")
```

### Verification
```
Show me the properties of the HelloMCP text object.
```

### Variations
- "Create blue text that says 'Blender Remote'"
- "Make a text object with a different font"
- "Create text with a gradient material"

---

## Example 5: Curve Object Creation

### Description
Create curve objects and convert them to meshes.

### LLM Prompt
```
Create a Bezier curve in the shape of a spiral, then convert it to a mesh and give it a thickness.
```

### Expected Result
```python
import bpy
import bmesh
from mathutils import Vector
import math

# Create a Bezier curve
bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0))
curve = bpy.context.active_object
curve.name = "SpiralCurve"

# Clear existing points
curve.data.splines.clear()

# Create new spline
spline = curve.data.splines.new(type='BEZIER')
spline.bezier_points.add(count=10)  # Add 10 points

# Create spiral shape
for i, point in enumerate(spline.bezier_points):
    angle = i * 0.5
    radius = i * 0.2
    x = math.cos(angle) * radius
    y = math.sin(angle) * radius
    z = i * 0.1
    
    point.co = (x, y, z)
    point.handle_left_type = 'AUTO'
    point.handle_right_type = 'AUTO'

# Set curve properties
curve.data.bevel_depth = 0.05  # Give thickness
curve.data.bevel_resolution = 3
curve.data.resolution_u = 12

# Create material
spiral_mat = bpy.data.materials.new(name="SpiralMaterial")
spiral_mat.use_nodes = True
principled = spiral_mat.node_tree.nodes["Principled BSDF"]
principled.inputs["Base Color"].default_value = (0.5, 0.2, 0.8, 1.0)  # Purple

curve.data.materials.append(spiral_mat)

print(f"Created spiral curve with {len(spline.bezier_points)} points")
```

### Verification
```
Show me the details of the SpiralCurve object.
```

### Variations
- "Create a circle curve and convert it to mesh"
- "Make a heart-shaped curve"
- "Create a path curve for animation"

---

## Example 6: Instanced Objects (Array)

### Description
Create multiple copies of an object using arrays or duplication.

### LLM Prompt
```
Create a row of 5 cubes spaced 3 units apart along the X-axis, each with a different color.
```

### Expected Result
```python
import bpy

# Colors for the cubes
colors = [
    (1.0, 0.0, 0.0, 1.0),  # Red
    (0.0, 1.0, 0.0, 1.0),  # Green
    (0.0, 0.0, 1.0, 1.0),  # Blue
    (1.0, 1.0, 0.0, 1.0),  # Yellow
    (1.0, 0.0, 1.0, 1.0)   # Magenta
]

color_names = ["Red", "Green", "Blue", "Yellow", "Magenta"]

for i in range(5):
    # Create cube at position
    x_pos = i * 3.0
    bpy.ops.mesh.primitive_cube_add(location=(x_pos, 0, 0))
    cube = bpy.context.active_object
    cube.name = f"{color_names[i]}Cube"
    
    # Create material
    mat = bpy.data.materials.new(name=f"{color_names[i]}Material")
    mat.use_nodes = True
    principled = mat.node_tree.nodes["Principled BSDF"]
    principled.inputs["Base Color"].default_value = colors[i]
    
    cube.data.materials.append(mat)

print("Created 5 colored cubes in a row")
```

### Verification
```
Show me all objects in the scene and their positions.
```

### Variations
- "Create a 3x3 grid of spheres"
- "Make a circle of cylinders around the origin"
- "Create a stack of cubes vertically"

---

## Example 7: Procedural Mesh Creation

### Description
Create custom mesh geometry using bmesh.

### LLM Prompt
```
Create a custom pyramid mesh with a square base and triangular sides.
```

### Expected Result
```python
import bpy
import bmesh
from mathutils import Vector

# Create new mesh
mesh = bpy.data.meshes.new("PyramidMesh")
obj = bpy.data.objects.new("CustomPyramid", mesh)

# Link to scene
bpy.context.collection.objects.link(obj)

# Create bmesh instance
bm = bmesh.new()

# Create pyramid vertices
# Base vertices (square)
base_verts = [
    bm.verts.new((-1, -1, 0)),
    bm.verts.new((1, -1, 0)),
    bm.verts.new((1, 1, 0)),
    bm.verts.new((-1, 1, 0))
]

# Top vertex
top_vert = bm.verts.new((0, 0, 2))

# Create base face
bm.faces.new(base_verts)

# Create triangular faces
for i in range(4):
    next_i = (i + 1) % 4
    bm.faces.new([base_verts[i], base_verts[next_i], top_vert])

# Update mesh
bm.to_mesh(mesh)
bm.free()

# Create material
pyramid_mat = bpy.data.materials.new(name="PyramidMaterial")
pyramid_mat.use_nodes = True
principled = pyramid_mat.node_tree.nodes["Principled BSDF"]
principled.inputs["Base Color"].default_value = (0.8, 0.6, 0.2, 1.0)  # Gold

obj.data.materials.append(pyramid_mat)

print(f"Created custom pyramid with {len(mesh.vertices)} vertices and {len(mesh.polygons)} faces")
```

### Verification
```
Show me the details of the CustomPyramid object including vertex and face count.
```

### Variations
- "Create a custom hexagonal prism"
- "Make a star-shaped mesh"
- "Create a custom gear shape"

---

## Example 8: Object Grouping and Hierarchy

### Description
Create objects and organize them in a hierarchy.

### LLM Prompt
```
Create a simple house scene with a main building, roof, door, and windows, all properly grouped together.
```

### Expected Result
```python
import bpy

# Create empty for house group
bpy.ops.object.empty_add(location=(0, 0, 0))
house_empty = bpy.context.active_object
house_empty.name = "HouseGroup"

# Create main building (scaled cube)
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 1))
building = bpy.context.active_object
building.name = "MainBuilding"
building.scale = (2, 2, 1)
building.parent = house_empty

# Create roof (scaled pyramid)
bpy.ops.mesh.primitive_cone_add(location=(0, 0, 2.5), vertices=4)
roof = bpy.context.active_object
roof.name = "Roof"
roof.scale = (2.5, 2.5, 1)
roof.parent = house_empty

# Create door
bpy.ops.mesh.primitive_cube_add(location=(0, -2, 0.5))
door = bpy.context.active_object
door.name = "Door"
door.scale = (0.4, 0.1, 1)
door.parent = house_empty

# Create windows
window_positions = [(-1, -2, 1.2), (1, -2, 1.2)]
for i, pos in enumerate(window_positions):
    bpy.ops.mesh.primitive_cube_add(location=pos)
    window = bpy.context.active_object
    window.name = f"Window{i+1}"
    window.scale = (0.3, 0.1, 0.3)
    window.parent = house_empty

# Create materials
building_mat = bpy.data.materials.new(name="BuildingMaterial")
building_mat.use_nodes = True
building_mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.8, 0.7, 0.6, 1.0)
building.data.materials.append(building_mat)

roof_mat = bpy.data.materials.new(name="RoofMaterial")
roof_mat.use_nodes = True
roof_mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.6, 0.2, 0.2, 1.0)
roof.data.materials.append(roof_mat)

print("Created house scene with grouped objects")
```

### Verification
```
Show me the scene hierarchy and which objects are parented to what.
```

### Variations
- "Create a car with wheels, body, and lights grouped together"
- "Make a tree with trunk, branches, and leaves"
- "Create a table with legs properly grouped"

---

## Example 9: Dynamic Object Creation

### Description
Create objects based on mathematical functions or patterns.

### LLM Prompt
```
Create a spiral of small cubes that follow a mathematical spiral pattern, with each cube getting slightly smaller as it goes up.
```

### Expected Result
```python
import bpy
import math

# Clear existing objects (optional)
# bpy.ops.object.select_all(action='SELECT')
# bpy.ops.object.delete()

# Create spiral of cubes
num_cubes = 20
for i in range(num_cubes):
    # Calculate spiral position
    angle = i * 0.5  # Angle increment
    radius = 0.5 + i * 0.1  # Increasing radius
    height = i * 0.2  # Height increment
    
    x = math.cos(angle) * radius
    y = math.sin(angle) * radius
    z = height
    
    # Create cube
    bpy.ops.mesh.primitive_cube_add(location=(x, y, z))
    cube = bpy.context.active_object
    cube.name = f"SpiralCube{i:02d}"
    
    # Scale based on position (smaller as it goes up)
    scale_factor = 1.0 - (i / num_cubes) * 0.5
    cube.scale = (scale_factor, scale_factor, scale_factor)
    
    # Color based on position
    hue = i / num_cubes
    # Convert HSV to RGB (simplified)
    if hue < 1/3:
        r, g, b = 1, hue * 3, 0
    elif hue < 2/3:
        r, g, b = 1 - (hue - 1/3) * 3, 1, 0
    else:
        r, g, b = 0, 1, (hue - 2/3) * 3
    
    # Create material
    mat = bpy.data.materials.new(name=f"SpiralMat{i:02d}")
    mat.use_nodes = True
    principled = mat.node_tree.nodes["Principled BSDF"]
    principled.inputs["Base Color"].default_value = (r, g, b, 1.0)
    
    cube.data.materials.append(mat)

print(f"Created spiral of {num_cubes} cubes")
```

### Verification
```
Show me how many objects are now in the scene and take a screenshot to see the spiral pattern.
```

### Variations
- "Create a wave pattern of spheres"
- "Make a grid of cubes with random heights"
- "Create a flower pattern with cylinders"

---

## Example 10: Object Duplication and Modification

### Description
Create an object and then duplicate it with variations.

### LLM Prompt
```
Create a base cube, then duplicate it 4 times, each with a different material and slightly different position and rotation.
```

### Expected Result
```python
import bpy
import math

# Create base cube
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
base_cube = bpy.context.active_object
base_cube.name = "BaseCube"

# Base material
base_mat = bpy.data.materials.new(name="BaseMaterial")
base_mat.use_nodes = True
base_mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.5, 0.5, 0.5, 1.0)
base_cube.data.materials.append(base_mat)

# Duplicate configurations
configs = [
    {"pos": (2, 0, 0), "rot": (0, 0, 45), "color": (1, 0, 0, 1), "name": "RedCube"},
    {"pos": (0, 2, 0), "rot": (0, 45, 0), "color": (0, 1, 0, 1), "name": "GreenCube"},
    {"pos": (-2, 0, 0), "rot": (45, 0, 0), "color": (0, 0, 1, 1), "name": "BlueCube"},
    {"pos": (0, -2, 0), "rot": (15, 30, 45), "color": (1, 1, 0, 1), "name": "YellowCube"}
]

for i, config in enumerate(configs):
    # Duplicate the base cube
    bpy.ops.object.duplicate()
    duplicate = bpy.context.active_object
    duplicate.name = config["name"]
    
    # Set position
    duplicate.location = config["pos"]
    
    # Set rotation (convert degrees to radians)
    duplicate.rotation_euler = [math.radians(r) for r in config["rot"]]
    
    # Create new material
    mat = bpy.data.materials.new(name=f"{config['name']}Material")
    mat.use_nodes = True
    principled = mat.node_tree.nodes["Principled BSDF"]
    principled.inputs["Base Color"].default_value = config["color"]
    
    # Replace material
    duplicate.data.materials.clear()
    duplicate.data.materials.append(mat)

print("Created base cube and 4 duplicates with variations")
```

### Verification
```
Show me all the cube objects in the scene and their positions and rotations.
```

### Variations
- "Create a sphere and duplicate it in a circle pattern"
- "Make cylinders with different heights and colors"
- "Create text objects with different fonts and sizes"

---

## Best Practices for Object Creation

### Planning Your Objects
1. **Think hierarchically**: Group related objects together
2. **Name consistently**: Use descriptive names for objects and materials
3. **Consider scale**: Keep objects at reasonable sizes for your scene
4. **Plan materials**: Create reusable materials for similar objects

### Efficient Creation
1. **Batch similar operations**: Create multiple objects of the same type together
2. **Use references**: Store frequently used values in variables
3. **Reuse materials**: Don't create new materials for every object
4. **Clean up**: Remove unused materials and objects

### Error Prevention
1. **Check active object**: Ensure the right object is selected
2. **Validate parameters**: Check location, rotation, and scale values
3. **Handle naming conflicts**: Use unique names for objects
4. **Test incrementally**: Create one object at a time for complex scenes

### Advanced Techniques
1. **Use bmesh for complex geometry**: Create custom meshes programmatically
2. **Apply modifiers**: Use modifiers for non-destructive editing
3. **Create instances**: Use linked duplicates for performance
4. **Organize hierarchy**: Use empties and parenting for complex scenes

---

**Next: Continue with [Screenshot Workflows](03_screenshot_workflows.md) to learn about visual feedback techniques!**