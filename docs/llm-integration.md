# LLM IDE Integration Guide

This guide shows how to integrate blender-remote with various LLM-powered IDEs and applications through the Model Context Protocol (MCP). Whether you're using VSCode, Claude Desktop, Cursor, or other MCP-compatible tools, this guide will get you up and running.

## Prerequisites

Before configuring your IDE, ensure you have:

1. **Blender with BLD_Remote_MCP addon installed**
2. **Service running on port 6688**
3. **uvx available** (for production use)

### Quick Setup Verification

```bash
# Check if service is running
netstat -tlnp | grep 6688

# Test MCP server
uvx blender-remote --help
```

## VSCode Integration

### Compatible Extensions

blender-remote works with any VSCode extension that supports MCP:

- **Claude Dev** - AI coding assistant
- **Cursor** - AI-powered editor
- **Cline** - Claude-based coding assistant
- **Continue** - Open-source AI coding assistant
- **Aider** - AI pair programming

### Configuration

#### Method 1: User Settings (Recommended)

1. **Open VSCode Settings**
   - `Ctrl+Shift+P` → "Preferences: Open User Settings (JSON)"
   - Or `File → Preferences → Settings` → Click JSON icon

2. **Add MCP Server Configuration**

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

#### Method 2: Workspace Settings

Create `.vscode/settings.json` in your project:

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

#### Method 3: Development Configuration

For development or testing:

```json
{
  "mcp": {
    "servers": {
      "blender-remote-dev": {
        "type": "stdio",
        "command": "python",
        "args": ["-m", "blender_remote.mcp_server"],
        "cwd": "/path/to/blender-remote",
        "env": {
          "PYTHONPATH": "/path/to/blender-remote/src",
          "BLD_REMOTE_MCP_PORT": "6688"
        }
      }
    }
  }
}
```

### Verification

1. **Restart VSCode** after adding configuration
2. **Open Command Palette** (`Ctrl+Shift+P`)
3. **Look for MCP tools** in your AI assistant extension
4. **Test with simple prompt**: "What objects are in my Blender scene?"

## Claude Desktop Integration

### Configuration File Location

- **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/claude/claude_desktop_config.json`

### Configuration

Create or edit the configuration file:

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

### Advanced Configuration

With custom environment variables:

```json
{
  "mcpServers": {
    "blender-remote": {
      "command": "uvx",
      "args": ["blender-remote"],
      "env": {
        "BLD_REMOTE_MCP_PORT": "6688"
      }
    }
  }
}
```

### Verification

1. **Restart Claude Desktop**
2. **Check for MCP tools** in the interface
3. **Test with prompt**: "Show me the current Blender scene"

## Cursor Integration

Cursor uses the same configuration as VSCode:

### Settings Configuration

1. **Open Cursor Settings**
   - `Ctrl+Shift+P` → "Preferences: Open User Settings (JSON)"

2. **Add MCP Configuration**

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

### Cursor-Specific Features

Cursor's AI can leverage blender-remote for:
- **Code Generation**: "Generate a Blender script to create a house"
- **Scene Analysis**: "Analyze the current Blender scene composition"
- **Visual Feedback**: "Show me the viewport and suggest improvements"

## Continue.dev Integration

### Configuration

Add to your Continue configuration file:

```json
{
  "mcpServers": [
    {
      "name": "blender-remote",
      "command": "uvx",
      "args": ["blender-remote"]
    }
  ]
}
```

### Usage with Continue

Continue can use blender-remote for:
- **Rapid Prototyping**: Quick 3D scene creation
- **Educational Content**: Teaching Blender scripting
- **Asset Generation**: Creating models through AI prompts

## Other MCP-Compatible Tools

### Aider Integration

```bash
# Start Aider with MCP support
aider --mcp-server "uvx blender-remote"
```

### Custom MCP Clients

For custom applications, use the MCP protocol directly:

```python
import subprocess
import json

# Start MCP server
process = subprocess.Popen(
    ["uvx", "blender-remote"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Send MCP request
request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "get_scene_info",
        "arguments": {}
    }
}

process.stdin.write(json.dumps(request) + "\n")
process.stdin.flush()

# Read response
response = process.stdout.readline()
print(json.loads(response))
```

## Environment Configuration

### Port Configuration

If you need to use a different port:

```bash
# Set environment variable
export BLD_REMOTE_MCP_PORT=9999

# Update MCP configuration
{
  "mcp": {
    "servers": {
      "blender-remote": {
        "type": "stdio",
        "command": "uvx",
        "args": ["blender-remote"],
        "env": {
          "BLD_REMOTE_MCP_PORT": "9999"
        }
      }
    }
  }
}
```

### Multiple Blender Instances

For multiple Blender instances:

```json
{
  "mcp": {
    "servers": {
      "blender-main": {
        "type": "stdio",
        "command": "uvx",
        "args": ["blender-remote"],
        "env": {
          "BLD_REMOTE_MCP_PORT": "6688"
        }
      },
      "blender-preview": {
        "type": "stdio",
        "command": "uvx",
        "args": ["blender-remote"],
        "env": {
          "BLD_REMOTE_MCP_PORT": "6689"
        }
      }
    }
  }
}
```

## Common Usage Patterns

### Scene Analysis Workflow

1. **Initial Inspection**
   - "What objects are in the current scene?"
   - "Show me the materials used"
   - "What's the current camera setup?"

2. **Visual Assessment**
   - "Take a screenshot of the current viewport"
   - "Show me the scene from the camera's perspective"

3. **Iterative Improvement**
   - "The lighting seems too dark, add more lights"
   - "Create a more interesting camera angle"
   - "Add some color variation to the materials"

### Code Generation Workflow

1. **High-Level Request**
   - "Create a simple house with a roof and windows"
   - "Set up a product showcase scene"
   - "Create an abstract geometric composition"

2. **Refinement**
   - "Make the house more detailed"
   - "Add better materials to the objects"
   - "Improve the lighting setup"

3. **Validation**
   - "Show me the result"
   - "Render a preview"
   - "Check the object count and complexity"

### Educational Workflow

1. **Learning Assistance**
   - "Explain how to create a donut in Blender"
   - "Show me the steps to add a material"
   - "Demonstrate mesh editing techniques"

2. **Code Explanation**
   - "Explain this Blender Python code"
   - "What does this modifier do?"
   - "How can I optimize this script?"

3. **Best Practices**
   - "What are the best practices for scene organization?"
   - "How should I structure my materials?"
   - "What's the recommended workflow for animation?"

## Troubleshooting

### Server Not Found

**Error**: "MCP server 'blender-remote' not found"

**Solutions**:
1. Ensure uvx is installed: `pip install uvx`
2. Test command manually: `uvx blender-remote --help`
3. Check PATH environment variable
4. Restart your IDE after configuration changes

### Connection Refused

**Error**: "Connection refused to localhost:6688"

**Solutions**:
1. Check if Blender is running: `ps aux | grep blender`
2. Verify BLD_Remote_MCP addon is enabled
3. Check port availability: `netstat -tlnp | grep 6688`
4. Try restarting Blender with environment variables:
   ```bash
   export BLD_REMOTE_MCP_START_NOW=1
   blender &
   ```

### Tools Not Available

**Error**: "No MCP tools available"

**Solutions**:
1. Check MCP server configuration syntax
2. Verify your IDE extension supports MCP
3. Check extension logs for error messages
4. Try manual MCP server test:
   ```bash
   uvx blender-remote
   # Should show server startup message
   ```

### Background Mode Issues

**Error**: "Screenshot not supported in background mode"

**Solutions**:
1. Start Blender in GUI mode: `blender &` (not `blender --background`)
2. Use headless alternatives for server environments
3. Check mode with: `ps aux | grep blender | grep -v background`

### Performance Issues

**Slow Response Times**:
1. Check if Blender is overloaded with heavy scenes
2. Reduce screenshot size in requests
3. Use efficient Blender Python code
4. Consider local network latency

## Advanced Configuration

### Custom Tool Configuration

Some IDEs allow custom tool configurations:

```json
{
  "mcp": {
    "servers": {
      "blender-remote": {
        "type": "stdio",
        "command": "uvx",
        "args": ["blender-remote"],
        "tools": {
          "get_scene_info": {
            "description": "Get information about the current Blender scene"
          },
          "execute_blender_code": {
            "description": "Execute Python code in Blender",
            "parameters": {
              "code": {
                "type": "string",
                "description": "Python code to execute"
              }
            }
          }
        }
      }
    }
  }
}
```

### Logging Configuration

Enable detailed logging for debugging:

```json
{
  "mcp": {
    "servers": {
      "blender-remote": {
        "type": "stdio",
        "command": "uvx",
        "args": ["blender-remote"],
        "env": {
          "BLD_REMOTE_MCP_LOG_LEVEL": "DEBUG"
        }
      }
    }
  }
}
```

### Security Configuration

For production environments:

```json
{
  "mcp": {
    "servers": {
      "blender-remote": {
        "type": "stdio",
        "command": "uvx",
        "args": ["blender-remote"],
        "env": {
          "BLD_REMOTE_MCP_SECURE": "true",
          "BLD_REMOTE_MCP_ALLOWED_HOSTS": "localhost,127.0.0.1"
        }
      }
    }
  }
}
```

## Best Practices

### IDE Configuration

1. **Use Specific Names**: Name your MCP servers descriptively
2. **Environment Isolation**: Use separate configurations for different projects
3. **Version Control**: Include workspace MCP configurations in version control
4. **Documentation**: Document custom configurations for your team

### Prompt Engineering

1. **Be Specific**: "Create a red metallic cube at position (2, 0, 0)" vs "add object"
2. **Use Context**: "Based on the current scene, add complementary lighting"
3. **Iterate**: Build complex scenes step by step
4. **Verify**: Always ask for screenshots to verify results

### Performance Optimization

1. **Batch Operations**: Group related commands in single requests
2. **Efficient Queries**: Use specific object queries instead of full scene dumps
3. **Screenshot Management**: Use appropriate sizes for your use case
4. **Connection Management**: Let the MCP server handle connections

## IDE-Specific Tips

### VSCode

- **Command Palette**: Use `Ctrl+Shift+P` to find MCP-related commands
- **Settings Sync**: MCP configurations sync with VSCode settings
- **Extension Updates**: Keep your AI extension updated for best MCP support

### Claude Desktop

- **Conversation Context**: MCP tools maintain context across conversation
- **File Attachments**: Can combine screenshots with file analysis
- **Multi-modal**: Excellent for visual feedback workflows

### Cursor

- **Code Completion**: Integrate Blender scripting with AI code completion
- **Inline Editing**: Edit Blender scripts with AI assistance
- **Project Context**: Cursor understands your project structure

## Migration from Other Tools

### From Blender Python Scripts

**Before**:
```python
# Manual Blender scripting
import bpy
bpy.ops.mesh.primitive_cube_add()
```

**After**:
```
# Natural language with AI
"Create a blue metallic cube in the scene"
```

### From Manual Blender Workflows

**Before**:
1. Open Blender
2. Manually create objects
3. Set materials
4. Position camera
5. Render

**After**:
1. Ask AI: "Create a product showcase scene"
2. AI handles all steps automatically
3. Review with screenshots
4. Iterate with natural language

## Future Enhancements

### Planned Features

- **Real-time Collaboration**: Multi-user MCP sessions
- **Extended Tool Set**: Animation, simulation, and rendering tools
- **Visual Prompting**: Use screenshots as input for modifications
- **Template Library**: Pre-built scene templates accessible via MCP

### Community Contributions

- **Custom Tools**: Extend MCP server with specialized tools
- **IDE Plugins**: Create IDE-specific plugins for enhanced integration
- **Workflow Templates**: Share common workflow patterns
- **Educational Content**: Create tutorials and learning materials

## Support and Resources

### Documentation
- [MCP Server Documentation](mcp-server.md)
- [API Reference](api-reference.md)
- [Development Guide](development.md)

### Community
- [GitHub Issues](https://github.com/igamenovoer/blender-remote/issues)
- [Discussions](https://github.com/igamenovoer/blender-remote/discussions)
- [Examples Repository](../examples/)

### Professional Support
- [Commercial Support](mailto:support@blender-remote.com)
- [Training Services](https://blender-remote.com/training)
- [Custom Development](https://blender-remote.com/services)

---

**Ready to supercharge your Blender workflow with AI? Configure your IDE and start creating!**