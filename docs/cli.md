# CLI Tools

Command-line interface for quick Blender operations and automation.

## Installation

The CLI tools are automatically installed with the `blender-remote` package:

```bash
pip install blender-remote
```

Verify installation:

```bash
blender-remote --version
```

## Basic Usage

```bash
blender-remote [OPTIONS] COMMAND [ARGS]...
```

### Global Options

- `--help`, `-h`: Show help message
- `--version`: Show version information
- `--host HOST`: Blender server host (default: localhost)
- `--port PORT`: Blender server port (default: 5555)
- `--timeout SECONDS`: Connection timeout (default: 10)
- `--verbose`, `-v`: Enable verbose output

## Commands

### Connection Management

#### `status`
Check connection status to Blender.

```bash
blender-remote status
```

**Example Output:**
```
✅ Connected to Blender 4.0.0 on localhost:5555
Server uptime: 2 hours, 34 minutes
Active objects: 3
```

#### `ping`
Test connection with simple ping.

```bash
blender-remote ping
```

### Code Execution

#### `exec`
Execute Python code in Blender.

```bash
blender-remote exec "bpy.ops.mesh.primitive_cube_add()"
```

**Options:**
- `--file`, `-f`: Execute code from file instead of command line

```bash
blender-remote exec --file my_script.py
```

**Examples:**
```bash
# Create a cube
blender-remote exec "bpy.ops.mesh.primitive_cube_add(location=(2, 0, 0))"

# Clear scene
blender-remote exec "bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()"

# Print current objects
blender-remote exec "print([obj.name for obj in bpy.context.scene.objects])"
```

#### `script`
Run a Python script file in Blender.

```bash
blender-remote script path/to/script.py
```

**Options:**
- `--args ARGS`: Pass arguments to the script

```bash
blender-remote script generate_scene.py --args "count=10 type=cube"
```

### Scene Management

#### `clear`
Clear the current scene.

```bash
blender-remote clear
```

**Options:**
- `--confirm`: Skip confirmation prompt

```bash
blender-remote clear --confirm
```

#### `save`
Save the current Blender file.

```bash
blender-remote save output.blend
```

#### `open`
Open a Blender file.

```bash
blender-remote open input.blend
```

### Object Operations

#### `create`
Create primitive objects.

```bash
blender-remote create PRIMITIVE [OPTIONS]
```

**Primitives:**
- `cube`, `sphere`, `cylinder`, `cone`, `torus`, `plane`

**Options:**
- `--location X Y Z`: Object location (default: 0 0 0)
- `--rotation X Y Z`: Object rotation in degrees (default: 0 0 0)
- `--scale X Y Z`: Object scale (default: 1 1 1)
- `--name NAME`: Object name

**Examples:**
```bash
# Create cube at origin
blender-remote create cube

# Create sphere with custom properties
blender-remote create sphere --location 2 0 1 --scale 1.5 1.5 1.5 --name "MySphere"

# Create rotated cylinder
blender-remote create cylinder --rotation 45 0 0
```

#### `list`
List objects in the scene.

```bash
blender-remote list
```

**Options:**
- `--type TYPE`: Filter by object type (mesh, light, camera, etc.)
- `--selected`: Only show selected objects

**Examples:**
```bash
# List all objects
blender-remote list

# List only mesh objects
blender-remote list --type mesh

# List selected objects
blender-remote list --selected
```

#### `delete`
Delete objects from the scene.

```bash
blender-remote delete OBJECT_NAME [OBJECT_NAME...]
```

**Options:**
- `--pattern PATTERN`: Delete objects matching pattern
- `--type TYPE`: Delete all objects of specific type
- `--confirm`: Skip confirmation

**Examples:**
```bash
# Delete specific objects
blender-remote delete Cube Sphere

# Delete all cubes (pattern matching)
blender-remote delete --pattern "Cube*"

# Delete all lights
blender-remote delete --type light --confirm
```

### Rendering

#### `render`
Render the current scene.

```bash
blender-remote render [OUTPUT_PATH]
```

**Options:**
- `--output`, `-o PATH`: Output file path (default: render.png)
- `--resolution WIDTH HEIGHT`: Render resolution
- `--engine ENGINE`: Render engine (cycles, eevee, workbench)
- `--samples SAMPLES`: Render samples (Cycles only)
- `--frame FRAME`: Render specific frame

**Examples:**
```bash
# Basic render
blender-remote render

# High-quality render
blender-remote render my_render.png --resolution 1920 1080 --engine cycles --samples 256

# Render specific frame
blender-remote render frame_010.png --frame 10
```

#### `render-animation`
Render animation sequence.

```bash
blender-remote render-animation [OUTPUT_DIR]
```

**Options:**
- `--output-dir`, `-o DIR`: Output directory (default: frames/)
- `--start-frame START`: First frame to render
- `--end-frame END`: Last frame to render
- `--resolution WIDTH HEIGHT`: Render resolution
- `--engine ENGINE`: Render engine

**Examples:**
```bash
# Render full animation
blender-remote render-animation

# Render frame range
blender-remote render-animation --start-frame 1 --end-frame 50 --output-dir my_animation/
```

### Camera Control

#### `camera`
Control camera settings and position.

```bash
blender-remote camera SUBCOMMAND [OPTIONS]
```

**Subcommands:**

##### `position`
Set camera position and rotation.

```bash
blender-remote camera position --location X Y Z --rotation X Y Z
```

##### `target`
Point camera at specific location.

```bash
blender-remote camera target X Y Z
```

##### `lens`
Set camera focal length.

```bash
blender-remote camera lens FOCAL_LENGTH
```

**Examples:**
```bash
# Position camera
blender-remote camera position --location 10 -10 8 --rotation 60 0 45

# Point camera at origin
blender-remote camera target 0 0 0

# Set 50mm lens
blender-remote camera lens 50
```

### Lighting

#### `light`
Create and manage lights.

```bash
blender-remote light create TYPE [OPTIONS]
```

**Light Types:**
- `sun`, `point`, `spot`, `area`

**Options:**
- `--location X Y Z`: Light location
- `--power POWER`: Light power/strength
- `--color R G B`: Light color (0-1 range)
- `--name NAME`: Light name

**Examples:**
```bash
# Create sun light
blender-remote light create sun --location 5 5 10 --power 10

# Create colored point light
blender-remote light create point --location 2 2 3 --color 1.0 0.8 0.6 --power 100
```

### Import/Export

#### `import`
Import external files.

```bash
blender-remote import FILE_PATH [OPTIONS]
```

**Options:**
- `--type TYPE`: File type (obj, fbx, gltf, auto)
- `--location X Y Z`: Import location
- `--scale SCALE`: Import scale

**Examples:**
```bash
# Import OBJ file
blender-remote import model.obj --type obj

# Import with custom position and scale
blender-remote import chair.fbx --location 2 0 0 --scale 0.5
```

#### `export`
Export scene or objects.

```bash
blender-remote export FILE_PATH [OPTIONS]
```

**Options:**
- `--type TYPE`: Export format (obj, fbx, gltf)
- `--selected`: Export only selected objects
- `--scale SCALE`: Export scale

**Examples:**
```bash
# Export scene as OBJ
blender-remote export scene.obj --type obj

# Export selected objects as FBX
blender-remote export selected_objects.fbx --type fbx --selected
```

## Configuration

### Configuration File

Create a configuration file at `~/.blender-remote/config.yaml`:

```yaml
# Default connection settings
default_host: localhost
default_port: 5555
default_timeout: 10

# Default render settings
render:
  resolution: [1920, 1080]
  engine: cycles
  samples: 128

# CLI preferences
cli:
  auto_confirm: false
  verbose: false
```

### Environment Variables

Set default values using environment variables:

```bash
export BLENDER_REMOTE_HOST=192.168.1.100
export BLENDER_REMOTE_PORT=5555
export BLENDER_REMOTE_TIMEOUT=15
```

## Scripting and Automation

### Batch Scripts

Create shell scripts for complex operations:

```bash
#!/bin/bash
# setup_scene.sh

# Clear scene
blender-remote clear --confirm

# Create objects
blender-remote create cube --location 0 0 0 --name "MainCube"
blender-remote create sphere --location 3 0 0 --name "Sphere1"
blender-remote create cylinder --location -3 0 0 --name "Cylinder1"

# Set up lighting
blender-remote light create sun --location 5 5 10 --power 10

# Position camera
blender-remote camera position --location 10 -10 8
blender-remote camera target 0 0 0

# Render
blender-remote render final_scene.png --resolution 1920 1080 --engine cycles
```

### Python Integration

Use CLI tools from Python scripts:

```python
import subprocess
import json

def blender_command(cmd):
    """Execute blender-remote command and return result."""
    result = subprocess.run(
        ["blender-remote"] + cmd,
        capture_output=True,
        text=True
    )
    return result.stdout, result.stderr, result.returncode

# Example usage
stdout, stderr, code = blender_command(["status"])
if code == 0:
    print("Blender is connected")
else:
    print(f"Connection failed: {stderr}")
```

### CI/CD Integration

Use in continuous integration pipelines:

```yaml
# .github/workflows/render.yml
name: Render Blender Scene

on: [push]

jobs:
  render:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Blender
      run: |
        # Install Blender and blender-remote
        pip install blender-remote
        
    - name: Start Blender service
      run: |
        # Start Blender with remote service
        
    - name: Render scene
      run: |
        blender-remote open scene.blend
        blender-remote render output.png --resolution 1920 1080
        
    - name: Upload renders
      uses: actions/upload-artifact@v3
      with:
        name: renders
        path: "*.png"
```

## Troubleshooting

### Common Issues

#### Command Not Found
```bash
bash: blender-remote: command not found
```
**Solution**: Ensure the package is installed and your PATH includes the Python scripts directory.

#### Connection Refused
```bash
Error: Could not connect to Blender at localhost:5555
```
**Solution**: Verify Blender is running with the remote service enabled.

#### Permission Denied
```bash
Error: Permission denied when saving file
```
**Solution**: Check file permissions and ensure Blender has write access to the target directory.

### Debug Mode

Enable verbose output for troubleshooting:

```bash
blender-remote --verbose status
blender-remote -v render output.png
```

### Log Files

CLI operations are logged to `~/.blender-remote/logs/cli.log`:

```bash
tail -f ~/.blender-remote/logs/cli.log
```

## Advanced Usage

### Custom Commands

Extend the CLI with custom commands by creating plugins:

```python
# ~/.blender-remote/plugins/my_commands.py

import click
from blender_remote.cli import cli

@cli.command()
@click.argument('count', type=int)
def create_grid(count):
    """Create a grid of cubes."""
    client = get_client()  # Implementation detail
    
    for x in range(count):
        for y in range(count):
            client.create_primitive(
                "cube",
                location=(x * 2, y * 2, 0),
                name=f"Cube_{x}_{y}"
            )
```

### Performance Tips

- Use `--confirm` to skip interactive prompts in scripts
- Batch operations when possible
- Use local connections for better performance
- Consider using the Python API for complex operations

### Security Considerations

- Only connect to trusted Blender instances
- Use SSH tunneling for remote connections
- Validate input parameters in batch scripts
- Consider authentication for production use