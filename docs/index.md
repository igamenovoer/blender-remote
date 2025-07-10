# Blender Remote

Control Blender remotely using Python API and LLM through MCP (Model Context Protocol).

## Key Features

### 1. **Dual Control Interface: Python API + LLM**
Use both Python API and LLM simultaneously to control Blender. The MCP protocol enables LLMs to experiment with Blender operations and help you create new APIs based on their interactions.

```python
# Python API
import blender_remote
client = blender_remote.connect_to_blender(port=6688)
scene_manager = blender_remote.create_scene_manager(client)
cube_name = scene_manager.add_cube(location=(2, 0, 0), size=1.5)
```

```bash
# LLM via MCP
uvx blender-remote  # Start MCP server for Claude, VSCode, Cursor, etc.
```

### 2. **Background Mode Support**
Run Blender completely headless for automation without GUI.

```bash
# GUI mode with auto-start service
export BLD_REMOTE_MCP_START_NOW=1
blender &

# Background mode for automation
blender --background --python start_service.py &
```

## Installation

```bash
pip install blender-remote
```

## Quick Start

### 1. Install Blender Addon

**Option A: Automated (Recommended)**
```bash
blender-remote-cli init /path/to/blender
blender-remote-cli install
```

**Option B: Manual**
```bash
cd blender-remote/blender_addon/
zip -r bld_remote_mcp.zip bld_remote_mcp/
# Install via Blender: Edit > Preferences > Add-ons > Install > Enable "BLD Remote MCP"
```

### 2. Start Blender with Service

```bash
# GUI mode
export BLD_REMOTE_MCP_START_NOW=1
blender &

# Background mode
echo 'import bld_remote; bld_remote.start_mcp_service()' > start_service.py
blender --background --python start_service.py &
```

### 3. Use Python API

```python
import blender_remote

# Connect to Blender
client = blender_remote.connect_to_blender(port=6688)

# High-level scene operations
scene_manager = blender_remote.create_scene_manager(client)
cube_name = scene_manager.add_cube(location=(0, 0, 0), size=2.0)
scene_manager.set_camera_location(location=(7, -7, 5), target=(0, 0, 0))

# Direct code execution
result = client.execute_python("bpy.ops.mesh.primitive_sphere_add()")
```

### 4. Use with LLM

**Configure LLM IDE (VSCode/Claude/Cursor):**
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

**Then ask your LLM:**
- "What objects are in the current Blender scene?"
- "Create a blue metallic cube at position (2, 0, 0)"
- "Show me the current viewport"
- "Help me create a new API function for batch object creation"

## Available MCP Tools

| Tool | Description | GUI Required |
|------|-------------|--------------|
| `get_scene_info()` | List all objects, materials, and scene properties | No |
| `get_object_info(name)` | Get detailed object properties | No |
| `execute_blender_code(code)` | Run Python code in Blender context | No |
| `get_viewport_screenshot()` | Capture viewport image | **Yes** |
| `check_connection_status()` | Verify service health | No |

## How It Works

```
External Python ←─────┐
                      │
LLM (Claude/VSCode) ←─┼─→ MCP/JSON-TCP (port 6688) ←─ BLD_Remote_MCP (addon)
                      │                                      ↓
Python Control API ←──┘                               Blender Python API
                                                             ↓
                                                     Blender (GUI/background)
```

## Example: LLM-Assisted API Development

1. **LLM experiments**: "Try creating 10 cubes in a grid pattern"
2. **LLM observes**: Uses `execute_blender_code()` to test different approaches
3. **LLM creates API**: "Based on what worked, let me create a `create_cube_grid()` function"
4. **You integrate**: Add the LLM-created function to your Python automation

## Documentation

### User Guides
- **[CLI Configuration Tool](cli-tool.md)** - Setup and management
- **[MCP Server Guide](mcp-server.md)** - Server configuration
- **[LLM Integration Guide](llm-integration.md)** - IDE setup
- **[Python Control API](python-control-api.md)** - Python usage
- **[API Reference](api-reference.md)** - Tool documentation

### Developer Resources
- **[Development Guide](development.md)** - Architecture and contributing

## Socket-Level Communication

```python
import socket, json

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('127.0.0.1', 6688))
command = {"type": "execute_code", "params": {"code": "bpy.ops.mesh.primitive_cube_add()"}}
sock.send(json.dumps(command).encode())
response = json.loads(sock.recv(4096).decode())
sock.close()
```

## CLI Configuration Tool

```bash
# Setup and management
blender-remote-cli init /path/to/blender
blender-remote-cli install
blender-remote-cli start --background
blender-remote-cli config set mcp_service.default_port=7777
blender-remote-cli status
```

## Testing

```bash
# Full test suite
pixi run python tests/run_dual_service_tests.py

# Quick verification
pixi run python tests/smoke_test.py

# MCP server functionality
pixi run python tests/mcp-server/test_fastmcp_server.py
```

## Troubleshooting

**"Connection refused" error:**
- Ensure Blender is running with BLD_Remote_MCP addon enabled
- Check: `netstat -tlnp | grep 6688`

**Screenshots not working:**
- Only available in GUI mode (`blender`, not `blender --background`)

**MCP server not found:**
- Install with uvx: `uvx blender-remote`

### Debug Mode

```bash
# Test MCP server directly
pixi run python -m blender_remote.mcp_server

# Use FastMCP inspector
pixi run fastmcp dev src/blender_remote/mcp_server.py
```

## License

[MIT License](../LICENSE)

## Credits

Inspired by [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) with enhanced background mode support, thread-safe operations, and production-ready deployment.