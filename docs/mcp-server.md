# MCP Server Documentation

The blender-remote MCP server enables seamless integration between AI-powered IDEs and Blender through the Model Context Protocol (MCP). This document provides comprehensive information about setup, configuration, tools, and usage.

## Overview

The MCP server acts as a bridge between your LLM IDE and Blender, allowing AI assistants to:
- Inspect Blender scenes and objects
- Execute Python code in Blender context
- Capture viewport screenshots
- Monitor service health
- Handle both GUI and background modes

## Architecture

```
LLM IDE (VSCode/Claude Desktop)
    ↓ MCP Protocol (stdio)
uvx blender-remote (FastMCP Server)
    ↓ JSON-TCP (port 6688)
BLD_Remote_MCP (Blender Addon)
    ↓ Blender Python API
Blender Application
```

## Installation & Setup

### 1. Install Blender Add-on

#### Step 1: Create the Add-on Zip File

The add-on zip file is not included in the repository and must be created from source:

```bash
# Navigate to the blender_addon directory from project root
cd blender-remote/blender_addon/
zip -r bld_remote_mcp.zip bld_remote_mcp/
```

This creates `bld_remote_mcp.zip` which you'll use for installation.

#### Step 2: Install via Blender GUI (Recommended)

1. **Open Blender**
2. Go to `Edit > Preferences` from the top menu bar
3. In the Preferences window, select the `Add-ons` tab
4. Click the `Install...` button (this opens Blender's file browser)
5. Navigate to your `blender_addon/` directory and select the `bld_remote_mcp.zip` file
6. Click `Install Add-on`
7. **Important**: Search for "BLD Remote MCP" in the add-on list and **enable it by ticking the checkbox**

#### Step 3: Verify Installation

**Critical**: This add-on has **no visible GUI panel**. You must verify installation through the system console.

**How to Access System Console:**
- **Windows**: Go to `Window > Toggle System Console` in Blender
- **macOS/Linux**: Start Blender from a terminal - log messages appear in the terminal

**Expected Log Messages:**

When you enable the add-on, look for these registration messages:
```
=== BLD REMOTE MCP ADDON REGISTRATION STARTING ===
🚀 DEV-TEST-UPDATE: BLD Remote MCP v1.0.2 Loading!
...
✅ BLD Remote MCP addon registered successfully
=== BLD REMOTE MCP ADDON REGISTRATION COMPLETED ===
```

If auto-start is configured (via environment variables), you'll also see:
```
✅ Starting server on port 6688
✅ BLD Remote server STARTED successfully on port 6688
Server is now listening for connections on 127.0.0.1:6688
```

#### Alternative: Manual Directory Installation

For development or if you prefer manual installation:

```bash
# Copy the addon directory directly
mkdir -p ~/.config/blender/4.4/scripts/addons/
cp -r bld_remote_mcp/ ~/.config/blender/4.4/scripts/addons/
# Restart Blender and enable the addon in preferences
```

### 2. Start Blender with Auto-Service

```bash
# Set environment variables for auto-start
export BLD_REMOTE_MCP_PORT=6688
export BLD_REMOTE_MCP_START_NOW=1

# Start Blender (GUI mode recommended)
blender &

# Or background mode (limited functionality)
blender --background &
```

### 3. Verify Service Status

```bash
# Check if service is running
netstat -tlnp | grep 6688

# Test connection
echo '{"type": "get_scene_info", "params": {}}' | nc localhost 6688
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BLD_REMOTE_MCP_PORT` | `6688` | TCP port for the service |
| `BLD_REMOTE_MCP_START_NOW` | `0` | Auto-start service on Blender launch |

### Service Configuration

The BLD_Remote_MCP service can be configured through Blender's addon preferences:

1. **Edit → Preferences → Add-ons**
2. **Search for "BLD Remote MCP"**
3. **Configure port and auto-start settings**

## MCP Tools Reference

### get_scene_info()

Retrieves comprehensive information about the current Blender scene.

**Parameters:** None

**Returns:**
```json
{
  "scene_name": "Scene",
  "total_objects": 3,
  "total_materials": 2,
  "current_frame": 1,
  "frame_range": [1, 250],
  "objects": [
    {
      "name": "Cube",
      "type": "MESH",
      "location": [0.0, 0.0, 0.0],
      "visible": true
    }
  ],
  "materials": ["Material", "Material.001"]
}
```

**Example LLM Usage:**
- "What objects are in the current scene?"
- "Show me all materials in the scene"
- "What's the current frame range?"

### get_object_info(object_name)

Retrieves detailed information about a specific object.

**Parameters:**
- `object_name` (string): Name of the object to inspect

**Returns:**
```json
{
  "name": "Cube",
  "type": "MESH",
  "location": [0.0, 0.0, 0.0],
  "rotation": [0.0, 0.0, 0.0],
  "scale": [1.0, 1.0, 1.0],
  "dimensions": [2.0, 2.0, 2.0],
  "visible": true,
  "material_slots": ["Material"],
  "vertex_count": 8,
  "face_count": 6
}
```

**Example LLM Usage:**
- "Tell me about the Cube object"
- "What are the dimensions of the Camera?"
- "Show me the material slots for the Sphere"

### execute_blender_code(code)

Executes Python code in Blender's context with full API access.

**Parameters:**
- `code` (string): Python code to execute

**Returns:**
```json
{
  "status": "success",
  "result": "Code executed successfully",
  "output": "Any print statements or returned values"
}
```

**Example LLM Usage:**
- "Create a blue metallic cube at position (2, 0, 0)"
- "Add a camera looking at the origin"
- "Set up a three-point lighting system"

**Common Code Patterns:**
```python
# Create objects
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))

# Modify materials
mat = bpy.data.materials.new(name="BlueMetal")
mat.use_nodes = True
mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0, 0, 1, 1)

# Camera operations
bpy.ops.object.camera_add(location=(7, -7, 5))
bpy.context.object.rotation_euler = (1.1, 0, 0.8)

# Lighting
bpy.ops.object.light_add(type='SUN', location=(4, 4, 8))
```

### get_viewport_screenshot(max_size, filepath, format)

Captures the current viewport as a base64-encoded image.

**Parameters:**
- `max_size` (integer, optional): Maximum image dimension (default: 800)
- `filepath` (string, optional): Custom file path (auto-generated if not provided)
- `format` (string, optional): Image format - 'PNG', 'JPEG' (default: 'PNG')

**Returns:**
```json
{
  "type": "image",
  "data": "base64-encoded-image-data",
  "mimeType": "image/png",
  "size": 61868,
  "dimensions": {
    "width": 800,
    "height": 600
  }
}
```

**Important Notes:**
- **GUI Mode Only**: Screenshots only work when Blender is running in GUI mode
- **Background Mode**: Returns clear error message explaining limitation
- **Thread Safety**: Uses UUID-based temporary files for concurrent requests
- **Auto-Cleanup**: Temporary files are automatically removed after reading

**Example LLM Usage:**
- "Show me the current viewport"
- "Take a screenshot of the scene"
- "Capture the viewport and analyze the composition"

### check_connection_status()

Verifies the health and connectivity of the BLD_Remote_MCP service.

**Parameters:** None

**Returns:**
```json
{
  "status": "connected",
  "service": "BLD_Remote_MCP",
  "port": 6688,
  "blender_version": "4.4.3",
  "addon_version": "1.0.0",
  "mode": "GUI",
  "uptime": "00:15:23"
}
```

**Example LLM Usage:**
- "Check if Blender is connected"
- "What's the service status?"
- "Is the MCP server running?"

## GUI vs Background Mode

### GUI Mode (Recommended)

**Full Functionality:**
- ✅ Scene inspection
- ✅ Code execution  
- ✅ Object manipulation
- ✅ Viewport screenshots
- ✅ Real-time visual feedback

**Usage:**
```bash
export BLD_REMOTE_MCP_START_NOW=1
blender &
```

### Background Mode (Limited)

**Available Features:**
- ✅ Scene inspection
- ✅ Code execution
- ✅ Object manipulation
- ❌ Viewport screenshots (returns clear error)

**Usage:**
```bash
export BLD_REMOTE_MCP_START_NOW=1
blender --background &
```

**Error Handling:**
When screenshots are requested in background mode, the service returns:
```json
{
  "status": "error",
  "message": "Screenshot capture is not supported in background mode. Please run Blender in GUI mode for screenshot functionality."
}
```

## Performance Considerations

### Connection Management
- **Persistent Connection**: MCP server maintains a single connection to BLD_Remote_MCP
- **Automatic Reconnection**: Handles service restarts gracefully
- **Connection Pooling**: Efficient resource usage for multiple requests

### Screenshot Optimization
- **UUID-based Filenames**: Prevents conflicts in concurrent requests
- **Automatic Cleanup**: Temporary files removed after reading
- **Size Limits**: Configurable maximum dimensions for performance
- **Format Support**: PNG for quality, JPEG for smaller files

### Code Execution
- **Scoped Execution**: Code runs in Blender's global context
- **Error Isolation**: Exceptions are captured and returned safely
- **Memory Management**: Efficient handling of large code blocks

## Security Considerations

### Code Execution Safety
- **Sandboxed Environment**: Code runs within Blender's Python context
- **No File System Access**: Limited to Blender's internal operations
- **Error Handling**: Malformed code returns errors without crashes

### Network Security
- **Local Only**: Service binds to localhost (127.0.0.1) by default
- **No Authentication**: Designed for local development use
- **Firewall Friendly**: Uses single TCP port (6688)

## Error Handling

### Common Error Types

**Connection Errors:**
```json
{
  "status": "error",
  "type": "connection_failed",
  "message": "Connection to BLD_Remote_MCP service failed"
}
```

**Code Execution Errors:**
```json
{
  "status": "error",
  "type": "execution_error",
  "message": "Python code execution failed",
  "details": "NameError: name 'invalid_function' is not defined"
}
```

**Background Mode Limitations:**
```json
{
  "status": "error",
  "type": "mode_limitation",
  "message": "Screenshot capture requires GUI mode"
}
```

### Error Recovery
- **Automatic Retry**: Connection errors trigger automatic reconnection
- **Graceful Degradation**: Service continues running despite individual failures
- **Clear Messages**: All errors include actionable error messages

## Troubleshooting

### Service Won't Start

**Check Addon Installation and Registration:**

First, verify the add-on is properly installed and enabled:

1. **Check File Installation:**
   ```bash
   # Verify addon directory exists
   ls ~/.config/blender/4.4/scripts/addons/bld_remote_mcp/
   ```

2. **Check Add-on is Enabled in Blender:**
   - Open Blender → `Edit > Preferences > Add-ons`
   - Search for "BLD Remote MCP" 
   - Ensure the checkbox is ticked ✓

3. **Verify Registration via Console:**
   
   **Critical**: Check the system console for registration messages:
   
   **Windows**: `Window > Toggle System Console`  
   **macOS/Linux**: Start Blender from terminal
   
   **Expected messages when enabling the add-on:**
   ```
   === BLD REMOTE MCP ADDON REGISTRATION STARTING ===
   🚀 DEV-TEST-UPDATE: BLD Remote MCP v1.0.2 Loading!
   ...
   ✅ BLD Remote MCP addon registered successfully
   === BLD REMOTE MCP ADDON REGISTRATION COMPLETED ===
   ```
   
   **If you don't see these messages**, the add-on failed to register. Check for error messages in the console.

**Verify Environment Variables:**
```bash
echo $BLD_REMOTE_MCP_PORT
echo $BLD_REMOTE_MCP_START_NOW
```

**Check Port Availability:**
```bash
# Check if port is in use
netstat -tlnp | grep 6688

# Kill existing processes if needed
pkill -f blender
```

### Connection Issues

**Test Direct Connection:**
```bash
# Test with netcat
echo '{"type": "get_scene_info", "params": {}}' | nc localhost 6688

# Test with Python
python -c "
import socket, json
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('127.0.0.1', 6688))
sock.send(json.dumps({'type': 'get_scene_info', 'params': {}}).encode())
print(sock.recv(4096).decode())
sock.close()
"
```

**Check Service Logs:**
```bash
# Enable debug logging in Blender console
# Window → Toggle System Console (Windows)
# Or run Blender from terminal (Linux/Mac)
```

### Screenshot Issues

**Verify GUI Mode:**
```bash
# Check if Blender is in GUI mode
ps aux | grep blender | grep -v "background"
```

**Test Screenshot Capability:**
```bash
# Use CLI tool to test
blender-remote screenshot
```

## Advanced Configuration

### Custom Port Configuration

**Environment Variable:**
```bash
export BLD_REMOTE_MCP_PORT=9999
```

**Blender Addon Settings:**
1. Edit → Preferences → Add-ons
2. Find "BLD Remote MCP"
3. Set custom port in addon preferences

### Integration with Build Systems

**Docker Integration:**
```dockerfile
FROM blender:4.4.3

# Install addon
COPY blender_addon/bld_remote_mcp/ /opt/blender/scripts/addons/

# Set environment
ENV BLD_REMOTE_MCP_PORT=6688
ENV BLD_REMOTE_MCP_START_NOW=1

# Start Blender in background
CMD ["blender", "--background", "--python-exit-code", "1"]
```

**CI/CD Integration:**
```yaml
# GitHub Actions example
- name: Setup Blender MCP
  run: |
    export BLD_REMOTE_MCP_START_NOW=1
    blender --background &
    sleep 10
    uvx blender-remote status
```

## Best Practices

### LLM Interaction Patterns

**Effective Prompts:**
- "Show me the current scene" → Uses `get_scene_info()`
- "Create a red cube at (1,1,1)" → Uses `execute_blender_code()`  
- "Take a screenshot" → Uses `get_viewport_screenshot()`

**Multi-step Workflows:**
- Start with scene inspection
- Execute code modifications
- Capture screenshots for verification
- Iterate based on visual feedback

### Performance Optimization

**Efficient Code Execution:**
- Group related operations in single execute calls
- Use Blender's batch operations when possible
- Minimize scene queries between operations

**Screenshot Management:**
- Use appropriate size limits for your use case
- Consider JPEG format for faster processing
- Let the service handle file management (don't specify filepath)

### Error Handling in LLM Workflows

**Graceful Degradation:**
- Always check connection status before complex operations
- Handle background mode limitations gracefully
- Provide alternative workflows when screenshots unavailable

## Migration Guide

### From BlenderAutoMCP

blender-remote is compatible with BlenderAutoMCP workflows:

**Tool Mapping:**
- `get_scene_info()` → Same functionality
- `execute_code()` → Same as `execute_blender_code()`
- `get_viewport_screenshot()` → Enhanced with UUID-based file management

**Key Improvements:**
- Background mode support
- Better error handling
- Thread-safe screenshot capture
- Automatic resource cleanup

### From Direct Socket Connection

**Before (Direct Socket):**
```python
import socket, json
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('127.0.0.1', 6688))
# Manual connection management
```

**After (MCP Server):**
```bash
# Just use uvx - no manual connection management
uvx blender-remote
```

## API Versioning

The MCP server follows semantic versioning:
- **Major**: Breaking changes to tool interfaces
- **Minor**: New tools or enhanced functionality
- **Patch**: Bug fixes and performance improvements

**Current Version**: 1.0.0
**Compatibility**: Blender 4.4.3+
**MCP Protocol**: 1.0.0

## Credits

This project was inspired by [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp), which demonstrated the potential for integrating Blender with the Model Context Protocol. We extend our gratitude to the original developers for pioneering this concept.

blender-remote builds upon this foundation with enhanced features including background mode support, thread-safe operations, comprehensive testing, and production-ready deployment capabilities.

## Support & Resources

### Documentation
- [API Reference](api-reference.md)
- [LLM Integration Guide](llm-integration.md)
- [Development Guide](development.md)

### Testing
- [MCP Server Tests](../tests/mcp-server/)
- [Integration Tests](../tests/integration/)
- [Usage Examples](../examples/)

### Community
- [GitHub Issues](https://github.com/igamenovoer/blender-remote/issues)
- [Discussions](https://github.com/igamenovoer/blender-remote/discussions)
- [Contributing Guide](development.md#contributing)

---

**Ready to integrate Blender with your AI workflow? Start with the [LLM Integration Guide](llm-integration.md)!**