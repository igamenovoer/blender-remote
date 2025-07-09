# blender-remote

🎯 **Control Blender from any LLM-powered IDE with zero configuration**

blender-remote is a production-ready MCP (Model Context Protocol) server that enables AI coding assistants to control Blender remotely. Simply run `uvx blender-remote` and your LLM can inspect scenes, execute Python code, and capture screenshots directly from Blender.

## ✨ Key Features

- **🚀 Zero Installation**: Run `uvx blender-remote` - no pip install needed
- **🤖 LLM Integration**: Works with VSCode Claude, Cursor, and other MCP-compatible IDEs
- **📱 GUI + Background Mode**: Unique support for both interactive and headless Blender
- **🔧 Complete Blender Control**: Execute any Blender Python API code through your AI assistant
- **📸 Screenshot Capture**: Get viewport images as base64 data for LLM analysis
- **🔄 Thread-Safe**: Handles concurrent requests with UUID-based file management
- **⚡ Production Ready**: Built on thoroughly tested BLD_Remote_MCP service

## 🎯 Quick Start for LLM Users

### 1. Install Blender Add-on

```bash
# Create the addon zip file from source
cd blender-remote/  # Your cloned repository
cd blender_addon/
zip -r bld_remote_mcp.zip bld_remote_mcp/

# Install to Blender
mkdir -p ~/.config/blender/4.4/scripts/addons/
cp bld_remote_mcp.zip ~/.config/blender/4.4/scripts/addons/
cd ~/.config/blender/4.4/scripts/addons/
unzip bld_remote_mcp.zip
```

**Note**: The `bld_remote_mcp.zip` file is not included in the repository and must be created by users from the `blender_addon/bld_remote_mcp/` directory.

### 2. Start Blender with Auto-Service

```bash
# Set environment variables and start Blender
export BLD_REMOTE_MCP_PORT=6688
export BLD_REMOTE_MCP_START_NOW=1
blender &  # or "blender --background" for headless mode
```

### 3. Configure Your LLM IDE

**VSCode (with Claude/Cursor extensions):**
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

**Claude Desktop:**
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

### 4. Start Creating with AI! 🎉

Your LLM can now:
- **Inspect scenes**: "What objects are in the current Blender scene?"
- **Execute code**: "Create a blue metallic cube at position (2, 0, 0)"
- **Take screenshots**: "Show me the current viewport"
- **Automate workflows**: "Create a donut tutorial scene with lighting"

## 🏗️ Architecture

```
LLM IDE (VSCode/Claude) 
    ↓ MCP Protocol
blender-remote (uvx)
    ↓ JSON-TCP (port 6688)
BLD_Remote_MCP (Blender addon)
    ↓ Python API
Blender (GUI or --background)
```

## 📋 Available MCP Tools

| Tool | Description | Example Use |
|------|-------------|-------------|
| `get_scene_info()` | List all objects, materials, and scene properties | Scene analysis |
| `get_object_info(name)` | Get detailed object properties | Object inspection |
| `execute_blender_code(code)` | Run Python code in Blender context | Any Blender operation |
| `get_viewport_screenshot()` | Capture viewport as base64 image | Visual feedback |
| `check_connection_status()` | Verify service health | Debugging |

## 🔧 Advanced Usage

### Manual Installation (for development)

```bash
# Clone and install from source
git clone https://github.com/igamenovoer/blender-remote.git
cd blender-remote
pixi install  # or pip install -e .
```

### CLI Tools (for testing)

```bash
# Check connection to BLD_Remote_MCP service
blender-remote status

# Execute Blender Python code
blender-remote exec "bpy.ops.mesh.primitive_cube_add()"

# Get scene information
blender-remote scene

# Capture viewport screenshot
blender-remote screenshot
```

### Python API (for custom scripts)

```python
# Direct connection to BLD_Remote_MCP service
import socket
import json

# Connect to service
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('127.0.0.1', 6688))

# Send command
command = {"type": "execute_code", "params": {"code": "bpy.ops.mesh.primitive_cube_add()"}}
sock.sendall(json.dumps(command).encode('utf-8'))

# Get response
response = json.loads(sock.recv(4096).decode('utf-8'))
print(response)
sock.close()
```

## 🧪 Testing & Development

This project uses [pixi](https://pixi.sh) for environment management:

```bash
# Install pixi (if not already installed)
curl -fsSL https://pixi.sh/install.sh | bash

# Create development environment
pixi install

# Run comprehensive test suite
pixi run python tests/run_dual_service_tests.py

# Quick smoke test
pixi run python tests/smoke_test.py

# Test MCP server functionality
pixi run python tests/mcp-server/test_fastmcp_server.py
```

## 📁 Project Structure

```
blender-remote/
├── blender_addon/              # Blender add-ons
│   └── bld_remote_mcp/        # BLD_Remote_MCP service (port 6688)
├── src/blender_remote/         # Python package (src layout)
│   ├── mcp_server.py          # FastMCP server implementation
│   └── cli.py                 # CLI tools
├── tests/                      # Comprehensive test suite
│   ├── mcp-server/            # MCP server functionality tests
│   ├── integration/           # Service comparison tests
│   └── others/                # Development scripts
├── docs/                      # Documentation
├── examples/                  # Usage examples
└── context/                   # AI assistant resources
```

## ⚠️ Background Mode Support

**Unique Advantage**: Unlike other Blender MCP solutions, blender-remote supports both GUI and background modes:

- **GUI Mode**: Full functionality including viewport screenshots
- **Background Mode**: Code execution and scene inspection (screenshots unavailable)
- **Automatic Detection**: Service gracefully handles mode limitations

```bash
# GUI mode (recommended for development)
blender &

# Background mode (for servers/CI)
blender --background &
```

## 🔧 Troubleshooting

### Common Issues

**"Connection refused" error:**
- Ensure Blender is running with BLD_Remote_MCP addon enabled
- Check service is listening: `netstat -tlnp | grep 6688`
- Try restarting Blender with environment variables set

**"No module named 'fastmcp'" error:**
- Install with uvx: `uvx blender-remote` (handles dependencies automatically)
- For development: `pixi run pip install fastmcp>=2.0.0`

**Screenshots not working:**
- Only available in GUI mode (`blender`, not `blender --background`)
- Service will return clear error message in background mode

### Debug Mode

```bash
# Test MCP server directly
pixi run python -m blender_remote.mcp_server

# Test with FastMCP inspector
pixi run fastmcp dev src/blender_remote/mcp_server.py
```

## 🤝 Contributing

Contributions are welcome! Please see our comprehensive test suite and development workflow:

1. **Fork the repository** and create a feature branch
2. **Run tests**: `pixi run python tests/run_dual_service_tests.py`
3. **Add tests** for new functionality
4. **Submit pull request** with clear description

## 📄 License

[MIT License](LICENSE)

## 🙏 Credits

This project was inspired by [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp), which demonstrated the potential for integrating Blender with the Model Context Protocol. We extend our gratitude to the original developers for pioneering this concept.

blender-remote builds upon this foundation with enhanced features including background mode support, thread-safe operations, comprehensive testing, and production-ready deployment capabilities.

## 🔗 Links

- **📚 Documentation**: [https://igamenovoer.github.io/blender-remote/](https://igamenovoer.github.io/blender-remote/)
- **🐛 Issue Tracker**: [Report bugs and request features](https://github.com/igamenovoer/blender-remote/issues)
- **💬 Discussions**: [Community support](https://github.com/igamenovoer/blender-remote/discussions)
- **🎥 Examples**: [Usage examples and workflows](https://github.com/igamenovoer/blender-remote/tree/main/examples)

---

**🎯 Ready to enhance your Blender workflow with AI? Start with `uvx blender-remote` today!**