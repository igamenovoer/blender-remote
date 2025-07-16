# Blender Remote

Control Blender remotely using Python API and LLM through MCP (Model Context Protocol).

## Overview

**blender-remote** provides two control interfaces:
- **Python API** for direct programmatic control
- **MCP server** for LLM integration (Claude, VSCode, Cursor)

Both interfaces run Blender in background mode for automation or GUI mode for interactive work.

```python
# Python API
from blender_remote.client import BlenderMCPClient
from blender_remote.scene_manager import BlenderSceneManager

client = BlenderMCPClient()
scene_manager = BlenderSceneManager(client)
client.execute_python('bpy.ops.mesh.primitive_cube_add(location=(2, 0, 0))')
```

```bash
# MCP server for LLMs
uvx blender-remote
```

## Key Features

- **Background Mode**: Run Blender headless for automation
- **GUI Mode**: Interactive development with full Blender interface  
- **Cross-Platform**: Windows, Linux, macOS support
- **GLB Export**: Export 3D models for web/game engines
- **CLI Management**: Process control and configuration tools

```bash
# Background mode
blender-remote-cli start --background

# GUI mode  
blender-remote-cli start
```

## Installation

```bash
pip install blender-remote
```

## Quick Start

### 1. Setup

```bash
# Install package
pip install blender-remote

# Setup Blender addon
blender-remote-cli init
blender-remote-cli install
```

### 2. Start Service

```bash
# Background mode (automation)
blender-remote-cli start --background

# GUI mode (interactive)  
blender-remote-cli start
```

### 3. Use Python API

```python
from blender_remote.client import BlenderMCPClient
from blender_remote.scene_manager import BlenderSceneManager

# Connect
client = BlenderMCPClient()
scene_manager = BlenderSceneManager(client)

# Create objects
scene_manager.add_cube(location=(0, 0, 0), name="MyCube")
scene_manager.add_sphere(location=(2, 0, 0), name="MySphere")

# Export GLB
glb_data = scene_manager.get_object_as_glb("MyCube")
```

### 4. Use with LLM

Configure MCP in your IDE (Claude Desktop, VSCode, Cursor):

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

Then ask your LLM:
- "What objects are in the Blender scene?"
- "Create a cube at position (2, 0, 0)"
- "Export the scene as GLB"

## MCP Tools

| Tool | Description | GUI Required |
|------|-------------|--------------|
| `get_scene_info` | List objects and scene properties | No |
| `get_object_info` | Get object details | No |
| `execute_code` | Run Python code in Blender | No |
| `get_viewport_screenshot` | Capture viewport image | Yes |
| `check_connection_status` | Verify service health | No |

## Architecture

![Blender Remote Full Architecture](architecture-full.svg)

## Documentation

- **[CLI Tool](cli-tool.md)** - Command-line interface reference
- **[Python API](python-control-api.md)** - Programming interface
- **[LLM Integration](llm-integration.md)** - MCP server usage  
- **[MCP Server](mcp-server.md)** - Server setup and tools
- **[API Reference](api-reference.md)** - Complete tool reference

## CLI Reference

```bash
# Setup
blender-remote-cli init          # Auto-detect Blender
blender-remote-cli install       # Install addon

# Control
blender-remote-cli start          # Start GUI mode
blender-remote-cli start --background  # Start background mode  
blender-remote-cli status         # Check service status
```

## Troubleshooting

**Connection refused:**
- Check Blender is running: `blender-remote-cli status`
- Verify addon enabled: Blender > Preferences > Add-ons > "BLD Remote MCP"

**Screenshots not working:**
- Requires GUI mode (not background)

## License

[MIT License](../LICENSE)