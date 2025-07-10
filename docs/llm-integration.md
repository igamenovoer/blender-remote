# LLM Integration Guide

Control Blender through LLM using the Model Context Protocol (MCP). This enables LLMs to experiment with Blender operations and help you create new APIs.

## Prerequisites

1. **Blender with BLD_Remote_MCP addon installed**
2. **Service running on port 6688**
3. **uvx available**

```bash
# Verify setup
netstat -tlnp | grep 6688
uvx blender-remote --help
```

## VSCode Configuration

### Compatible Extensions
- Claude Dev
- Cursor
- Cline
- Continue
- Aider

### Setup

1. **Open VSCode Settings** (`Ctrl+Shift+P` → "Preferences: Open User Settings (JSON)")

2. **Add Configuration:**
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

3. **Restart VSCode**

## Claude Desktop

### Setup

1. **Open Claude Desktop Configuration:**
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/claude/claude_desktop_config.json`

2. **Add Configuration:**
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

3. **Restart Claude Desktop**

## Cursor IDE

### Setup

1. **Open Settings** (`Ctrl+,`)
2. **Search for "MCP"**
3. **Add Server:**
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

## Usage Examples

### Basic Operations
```
"What objects are in the current Blender scene?"
"Create a blue metallic cube at position (2, 0, 0)"
"Show me the current viewport"
"Delete all objects and create a simple scene"
```

### LLM-Assisted API Development
```
"Try creating 10 cubes in a grid pattern"
"Based on what worked, create a create_cube_grid() function"
"Help me automate material assignment for multiple objects"
"Create a batch processing function for object transformations"
```

### Advanced Workflows
```
"Set up a three-point lighting system"
"Create an animation with keyframes"
"Generate a procedural material"
"Export the scene to GLB format"
```

## Available Tools

| Tool | Description | GUI Required |
|------|-------------|--------------|
| `get_scene_info()` | List all objects, materials, properties | No |
| `get_object_info(name)` | Get detailed object properties | No |
| `execute_blender_code(code)` | Run Python code in Blender | No |
| `get_viewport_screenshot()` | Capture viewport image | **Yes** |
| `check_connection_status()` | Verify service health | No |

## Troubleshooting

### MCP Server Not Found
```bash
# Install with uvx
uvx blender-remote

# Verify installation
which uvx
uvx --version
```

### Connection Issues
```bash
# Check Blender service
netstat -tlnp | grep 6688

# Test direct connection
python -c "
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('127.0.0.1', 6688))
print('Connected successfully')
sock.close()
"
```

### IDE Not Detecting MCP
1. **Restart IDE** after configuration
2. **Check JSON syntax** in config file
3. **Verify extension** supports MCP
4. **Check logs** in IDE developer tools

## Best Practices

### Effective Prompts
- **Be specific**: "Create a 2x2x2 red cube at (0,0,0)" vs "make a cube"
- **Ask for explanations**: "Explain what this code does before running it"
- **Request validation**: "Check if the object exists before modifying it"

### LLM-Assisted Development
1. **Start simple**: Ask LLM to create basic operations
2. **Iterate**: Build on successful operations
3. **Document**: Ask LLM to explain the code it creates
4. **Test**: Verify operations work in your environment

### Code Organization
- **Ask for functions**: "Create a reusable function for this operation"
- **Request error handling**: "Add proper error checking to this code"
- **Modular design**: "Break this into smaller, focused functions"

## Integration Patterns

### Experimental Development
```
You: "Try different ways to create a material with procedural textures"
LLM: [Experiments with various approaches using execute_blender_code()]
LLM: "Based on the experiments, here's the most effective approach..."
You: "Now create a Python function I can use in my automation scripts"
```

### Rapid Prototyping
```
You: "Create a scene with 5 random objects with different materials"
LLM: [Uses multiple tool calls to build the scene]
You: "Now show me the viewport and adjust the lighting"
LLM: [Takes screenshot, analyzes, adjusts lighting]
You: "Export this as a reusable scene template function"
```

## Security Considerations

- **Code Review**: Always review LLM-generated code before using in production
- **Sandboxing**: Use in isolated Blender instances for testing
- **Validation**: Verify operations don't have unintended side effects
- **Backups**: Save important scenes before running experimental code