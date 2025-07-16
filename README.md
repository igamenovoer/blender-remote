# blender-remote

## Overview

**Purpose**: Enable complex Blender automation through LLM-assisted Python development, bridging the gap between AI-generated Blender scripts and external Python tools.

**Intended Users**:
- Developers who need complex Blender automation but lack time to master Blender's Python API
- Users uncomfortable writing Blender-side Python code within Blender's basic text editor
- Developers who rely heavily on LLMs for code generation and want to automate Blender tasks

**Our Solution**:
- Allow LLMs to generate Blender-side Python code and help wrap it into external Python APIs
- Provide background mode execution for full automation and batch processing
- **We DO NOT try to map all Blender Python API to Python or MCP** - instead, we provide infrastructure for users to develop their own Python tools to interact with Blender with LLM assistance
- **Ultimate outcome**: Use your VSCode with your own Python to control Blender, not constrained by Blender's barebone Python environment and editor, write complex Blender automation projects with ease

**System Architecture**:
- **`BLD_Remote_MCP`** - Blender addon using JSON-RPC to communicate with external callers
- **MCP Server** - Forwards MCP commands from LLM IDEs (VSCode, Claude, Cursor) to Blender addon  
- **Python Client** - Direct control of Blender addon, bypassing MCP server for automation scripts

![System Architecture](docs/architecture-full.svg)

**Key Features**:
- Seamless bridge between LLM-generated Blender-side code and external Python APIs
- Simultaneous LLM and Python client access with smooth code transition workflow
- LLM-assisted wrapper code generation for converting Blender scripts to Python APIs
- Background mode support for automation and batch processing
- Cross-platform support: Windows, Linux, macOS

**Caution**: This code is primarily written with AI assistance. Use at your own risk.

## Usage

### Installation

**Install the package**:
```bash
pip install blender-remote
```

**Install uv (required for MCP server)**:
```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Basic Usage

#### The CLI Approach

Use `blender-remote-cli` to set up and manage Blender integration:

**1. Initialize and install addon**:
```bash
# Auto-detect Blender (Windows/macOS) or specify path
blender-remote-cli init
blender-remote-cli install
```

**2. Verify installation in Blender GUI**:
- Open Blender → Edit → Preferences → Add-ons
- Search for "BLD Remote MCP" - should be enabled

**3. Configure service settings (optional, before starting)**:
```bash
# Configure custom port (default is 6688)
blender-remote-cli config set mcp_service.default_port=7777

# Configure logging level  
blender-remote-cli config set mcp_service.log_level=DEBUG

# View current configuration
blender-remote-cli config get mcp_service.default_port
```

**4. Start Blender with service**:
```bash
# GUI mode with service
blender-remote-cli start

# Background mode for automation  
blender-remote-cli start --background

# Load specific scene
blender-remote-cli start --scene=my_project.blend
```

**5. Execute commands on running Blender**:
```bash
# Execute Python code directly
blender-remote-cli execute -c "import bpy; bpy.ops.mesh.primitive_cube_add(location=(2, 0, 0))"

# Execute with custom port
blender-remote-cli execute -c 'import bpy; print(f"Blender {bpy.app.version_string}")' --port 7888

# Execute Python file
blender-remote-cli execute my_script.py

# Complex code with base64 encoding (recommended for multiline code)
blender-remote-cli execute -c "import bpy; [bpy.ops.mesh.primitive_cube_add(location=(i*2, 0, 0)) for i in range(3)]" --use-base64
```

#### The MCP Server Approach

For LLM IDEs like VSCode, Claude Desktop, or Cursor:

**1. Install Blender addon first** (see CLI approach above)

**2. Start Blender with service**:
```bash
blender-remote-cli start
```

**3. Configure your LLM IDE**:

**VSCode settings.json**:
```json
{
  "mcpServers": {
    "blender-remote": {
      "command": "uvx",
      "args": ["blender-remote"]
    }
  }
}
```

**Custom host/port configuration**:
```json
{
  "mcpServers": {
    "blender-remote": {
      "command": "uvx", 
      "args": ["blender-remote", "--host", "127.0.0.1", "--port", "6688"]
    }
  }
}
```

**4. Use with LLM**:
- "What objects are in the current Blender scene?"
- "Create a metallic blue cube at position (2, 0, 0)"
- "Export the current scene as GLB format"
- "Help me create a Python function to generate a grid of cubes"

#### The Python Client Approach

For direct Python automation scripts:

```python
import blender_remote

# Connect to running Blender service
client = blender_remote.connect_to_blender(port=6688)

# Execute Blender Python code directly
result = client.execute_python("bpy.ops.mesh.primitive_cube_add(location=(2, 0, 0))")

# Use scene manager for higher-level operations
scene_manager = blender_remote.create_scene_manager(client)
scene_manager.set_camera_location(location=(7, -7, 5), target=(0, 0, 0))

# Get scene information
scene_info = client.get_scene_info()
print(f"Scene has {len(scene_info['objects'])} objects")
```

### Advanced Usage

#### Using LLM to Develop Python Tools for Blender

**Example workflow**:

1. **Ask LLM**: "Create Blender code to generate a spiral of cubes"
2. **LLM generates**: Blender-side Python code using `bpy` operations
3. **Test in Blender**: Use MCP tools to execute and refine the code
4. **Ask LLM**: "Wrap this into a Python function I can call from external scripts"
5. **LLM creates wrapper**:

```python
def create_cube_spiral(client, count=10, radius=3):
    code = f"""
import bpy
import math

for i in range({count}):
    angle = i * (2 * math.pi / {count})
    x = {radius} * math.cos(angle)
    y = {radius} * math.sin(angle)
    z = i * 0.5
    bpy.ops.mesh.primitive_cube_add(location=(x, y, z))
"""
    return client.execute_python(code)

# Use the wrapper
client = blender_remote.connect_to_blender()
create_cube_spiral(client, count=15, radius=5)
```

#### Batch Processing Using Background Mode

**Automated batch workflow**:

```python
import blender_remote
import subprocess
import time
import os

# Start background Blender process using CLI (avoids path issues)
port = 7888
process = subprocess.Popen([
    "python", "-m", "blender_remote.cli", "start", "--background", "--port", str(port)
])

# Wait for service to start up
time.sleep(3)

# Connect to the background instance
client = blender_remote.connect_to_blender(port=port)

# Process multiple scene files
scene_dir = "tmp/test-scenes"
input_files = ["scene1.blend", "scene2.blend", "scene3.blend"]

for scene_file in input_files:
    scene_path = os.path.join(scene_dir, scene_file)
    scene_path_abs = os.path.abspath(scene_path)
    
    print(f"Processing {scene_file}...")
    
    # Load scene
    client.execute_python(f'bpy.ops.wm.open_mainfile(filepath="{scene_path_abs.replace(os.sep, "/")}")')
    
    # Process scene (your custom operations)
    client.execute_python("bpy.ops.mesh.primitive_cube_add(location=(0, 0, 2))")
    client.execute_python("bpy.ops.mesh.primitive_uv_sphere_add(location=(2, 0, 0))")
    
    # Export result
    output_file = scene_file.replace('.blend', '.glb')
    output_path = os.path.abspath(f"tmp/{output_file}")
    client.execute_python(f'bpy.ops.export_scene.gltf(filepath="{output_path.replace(os.sep, "/")}")')
    
    print(f"Exported {output_file}")

# Gracefully exit Blender
client.execute_python("bpy.ops.wm.quit_blender()")
process.wait()  # Wait for process to fully exit
```

## Documentation

- **Full Documentation**: [https://igamenovoer.github.io/blender-remote/](https://igamenovoer.github.io/blender-remote/)
- **Examples**: [examples/](https://github.com/igamenovoer/blender-remote/tree/main/examples)
- **Issues**: [Report bugs](https://github.com/igamenovoer/blender-remote/issues)

## Credits

Built upon the [blender-mcp](https://github.com/ahujasid/blender-mcp) project with enhanced background mode support, thread-safe operations, and production deployment capabilities.

## License

[MIT License](LICENSE)