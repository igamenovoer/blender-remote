# VSCode MCP Testing Guide

This guide shows how to test your `blender-remote` MCP server locally in VSCode before publishing to PyPI.

## Prerequisites

1. **Blender Running**: Make sure Blender is running with the BLD_Remote_MCP addon enabled:
   ```bash
   # Check if BLD_Remote_MCP is running
   netstat -tlnp | grep 6688
   ```

2. **Package Installed**: Install the package in development mode:
   ```bash
   pixi run pip install -e .
   ```

## VSCode Configuration

Your `.vscode/settings.json` is already configured with:

```json
{
  "mcp": {
    "servers": {
      "blender-remote-dev": {
        "type": "stdio",
        "command": ".pixi/envs/default/bin/python",
        "args": ["-m", "blender_remote.mcp_server"],
        "cwd": "/workspace/code/blender-remote",
        "env": {
          "PYTHONPATH": "/workspace/code/blender-remote/src",
          "BLD_REMOTE_MCP_PORT": "6688"
        }
      }
    }
  }
}
```

## Testing Steps

### 1. Verify Server Functionality
```bash
# Run the comprehensive test
pixi run python test_fastmcp_server.py
```

Expected output:
```
✅ FastMCP imports successful
✅ FastMCP server instance created successfully
✅ Successfully connected to BLD_Remote_MCP service
🎉 All tests passed! FastMCP server is ready for VSCode integration.
```

### 2. Test MCP Server Startup
```bash
# Test that the server starts correctly (will timeout after 5 seconds)
timeout 5s pixi run python -m blender_remote.mcp_server
```

Expected output:
```
🚀 Starting Blender Remote MCP Server...
📡 This server connects to BLD_Remote_MCP service in Blender (port 6688)
🔗 Make sure Blender is running with the BLD_Remote_MCP addon enabled

╭─ FastMCP 2.0 ────────────────────────────────────────────────────────────────╮
│     🖥️  Server name:     Blender Remote MCP                                   │
│     📦 Transport:       STDIO                                                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### 3. Use in VSCode

1. **Install MCP Extension**: Make sure you have an MCP-compatible extension in VSCode (like Claude Dev, Cline, etc.)

2. **Server Available**: Your MCP server will be available as `blender-remote-dev` in VSCode's MCP server list

3. **Available Tools**: The server provides these tools:
   - `get_scene_info` - Get Blender scene information  
   - `execute_blender_code` - Execute Python code in Blender
   - `get_object_info` - Get object details
   - `get_viewport_screenshot` - Capture viewport screenshots as base64 data (GUI mode only)
   - `check_connection_status` - Check connection to Blender

## Development Tools

### FastMCP Inspector
```bash
# Start with MCP Inspector for debugging
pixi run fastmcp dev src/blender_remote/mcp_server.py
```

### Manual Testing
```bash
# Test CLI commands directly
pixi run python -m blender_remote.cli status
pixi run python -m blender_remote.cli scene
pixi run python -m blender_remote.cli exec 'print("Hello from Blender")'
```

## Configuration for Production

After publishing to PyPI, users will configure their VSCode like this:

```json
{
  "mcp": {
    "servers": {
      "blender-remote": {
        "type": "stdio",
        "command": "uvx",
        "args": ["blender-remote"]
      }
    }
  }
}
```

## Troubleshooting

### Connection Issues
- **Error**: `Connection failed: [Errno 111] Connection refused`
- **Solution**: Make sure Blender is running with BLD_Remote_MCP addon enabled on port 6688

### Import Errors  
- **Error**: `ModuleNotFoundError: No module named 'fastmcp'`
- **Solution**: Run `pixi run pip install fastmcp>=2.0.0`

### PYTHONPATH Issues
- **Error**: `ModuleNotFoundError: No module named 'blender_remote'`
- **Solution**: The `.vscode/settings.json` includes the correct PYTHONPATH

## Features Available to LLM

Once connected, the LLM in VSCode can:

1. **Inspect Blender Scenes**: Get information about objects, materials, and scene structure
2. **Execute Python Code**: Run any Blender Python API code remotely
3. **Capture Screenshots**: Get viewport images (when Blender is in GUI mode)
4. **Monitor Connection**: Check if Blender is running and responsive

## Example LLM Interactions

The LLM can now say things like:
- "Show me what's in the current Blender scene"
- "Create a cube at position (2, 2, 2)"
- "Take a screenshot of the viewport"
- "List all the materials in the scene"

All of these will work through the MCP protocol connecting to your BLD_Remote_MCP service!