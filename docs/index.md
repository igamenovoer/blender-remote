# Blender Remote

🎯 **Automate Blender workflows with external Python control, background operation, and LLM integration**

blender-remote enables comprehensive Blender automation through multiple interfaces: auto-start service for external Python control, background mode operation for headless workflows, MCP server for LLM integration, and direct Python APIs. Perfect for CI/CD pipelines, render farms, and AI-assisted 3D workflows.

## ✨ Core Capabilities

### 1. **🔧 Auto-Start Service for External Automation**
```bash
export BLD_REMOTE_MCP_START_NOW=1
blender &  # Service auto-starts on port 6688
python automation_script.py  # External Python control
```
**Use cases**: CI/CD pipelines, batch processing, automated asset generation

### 2. **🖥️ Background Mode Operation**
```bash
# Start headless Blender with service
blender --background --python start_service.py &
python headless_automation.py  # Same API, no GUI
```
**Use cases**: Headless servers, Docker containers, cloud rendering

### 3. **🤖 MCP Server for LLM Integration**
```bash
uvx blender-remote  # Standard MCP protocol
```
**Compatible with**: VSCode Claude, Claude Desktop, Cursor, and other LLM IDEs

### 4. **🐍 Python Control Classes**
Direct Python API for programmatic Blender control

### 5. **⚙️ CLI Configuration Tool**
```bash
blender-remote-cli init /path/to/blender  # Auto-setup
blender-remote-cli install               # Install addon
blender-remote-cli start --background    # Launch service
```
**Perfect for**: Automated setup, configuration management, CI/CD integration

## 🚀 Quick Start

### For Automation Users

**Auto-Start Service Pattern:**
```bash
# 1. Install addon and set auto-start
export BLD_REMOTE_MCP_START_NOW=1
blender &

# 2. External Python automation
python -c "
import socket, json
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('127.0.0.1', 6688))
cmd = {'type': 'execute_code', 'params': {'code': 'bpy.ops.mesh.primitive_cube_add()'}}
sock.send(json.dumps(cmd).encode())
response = sock.recv(4096).decode()
print('Blender automated:', response)
sock.close()
"
```

**Background Mode Pattern:**
```bash
# 1. Create startup script
echo 'import bld_remote; bld_remote.start_mcp_service()' > start_bg.py

# 2. Launch headless Blender
blender --background --python start_bg.py &

# 3. Same external automation (no GUI required)
python your_automation_script.py
```

### For LLM Users

1. **Install Blender Add-on**
   
   **Option A: Automated Setup (Recommended)**
   ```bash
   pip install blender-remote
   blender-remote-cli init /path/to/blender
   blender-remote-cli install
   ```
   
   **Option B: Manual Setup**
   
   **Create the zip file:**
   ```bash
   cd blender-remote/blender_addon/
   zip -r bld_remote_mcp.zip bld_remote_mcp/
   ```
   
   **Install via Blender GUI:**
   1. Open Blender → `Edit > Preferences > Add-ons`
   2. Click `Install...` and select `bld_remote_mcp.zip`
   3. Search for "BLD Remote MCP" and enable it ✓
   
   **Verify installation via system console:**
   - **Windows**: `Window > Toggle System Console`
   - **macOS/Linux**: Start Blender from terminal
   
   **Look for:** `✅ BLD Remote MCP addon registered successfully`
   
   **Note**: The `bld_remote_mcp.zip` file must be created from the `blender_addon/bld_remote_mcp/` directory.

2. **Start Blender with Auto-Service**
   
   **Option A: Using CLI Tool (Recommended)**
   ```bash
   blender-remote-cli start  # GUI mode
   # or
   blender-remote-cli start --background  # Headless mode
   ```
   
   **Option B: Manual Environment Setup**
   ```bash
   export BLD_REMOTE_MCP_PORT=6688
   export BLD_REMOTE_MCP_START_NOW=1
   blender &
   ```

3. **Configure Your LLM IDE**
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

4. **Start Creating with AI!** 🎉
   - "What objects are in the current Blender scene?"
   - "Create a blue metallic cube at position (2, 0, 0)"
   - "Take a screenshot of the current viewport"

### For Developers

```bash
# Clone and install
git clone https://github.com/igamenovoer/blender-remote.git
cd blender-remote
pixi install

# Run tests
pixi run python tests/run_dual_service_tests.py

# Test MCP server
pixi run python tests/mcp-server/test_fastmcp_server.py
```

## 📚 Documentation

### User Guides
- **[CLI Configuration Tool](cli-tool.md)** - Complete setup and management with the CLI tool
- **[MCP Server Guide](mcp-server.md)** - Complete server setup and configuration
- **[LLM Integration Guide](llm-integration.md)** - VSCode, Claude Desktop, and other IDE setup
- **[API Reference](api-reference.md)** - Comprehensive tool documentation

### Developer Resources
- **[Development Guide](development.md)** - Architecture, contributing, and extending
- **[Test Suite](../tests/)** - Comprehensive testing framework
- **[Examples](../examples/)** - Usage examples and workflows

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

| Tool | Description | GUI Required |
|------|-------------|--------------|
| `get_scene_info()` | Scene inspection and object listing | No |
| `get_object_info(name)` | Detailed object properties | No |
| `execute_blender_code(code)` | Python code execution | No |
| `get_viewport_screenshot()` | Screenshot capture | **Yes** |
| `check_connection_status()` | Service health monitoring | No |

## 🔧 Advanced Features

### Background Mode Support

**Unique Advantage**: Unlike other Blender MCP solutions, blender-remote supports both GUI and background modes:

- **GUI Mode**: Full functionality including viewport screenshots
- **Background Mode**: Code execution and scene inspection (screenshots unavailable)
- **Automatic Detection**: Service gracefully handles mode limitations

### Thread-Safe Operations

- **UUID-based Files**: Unique filenames prevent conflicts in parallel requests
- **Automatic Cleanup**: Temporary files removed after use
- **Concurrent Requests**: Safe handling of multiple simultaneous operations

### Production Ready

- **Comprehensive Testing**: Dual-service comparison tests with BlenderAutoMCP
- **Error Handling**: Graceful degradation and clear error messages
- **Performance Optimized**: Efficient connection management and resource usage

## 🧪 Testing

The project includes a comprehensive test suite:

```bash
# Full test suite (compares with BlenderAutoMCP)
pixi run python tests/run_dual_service_tests.py

# Quick verification
pixi run python tests/smoke_test.py

# MCP server functionality
pixi run python tests/mcp-server/test_fastmcp_server.py

# Performance benchmarks
pixi run python tests/integration/test_performance_comparison.py
```

## 🔍 Troubleshooting

### Common Issues

**"Connection refused" error:**
- Ensure Blender is running with BLD_Remote_MCP addon enabled
- Check: `netstat -tlnp | grep 6688`

**Screenshots not working:**
- Only available in GUI mode (`blender`, not `blender --background`)
- Service returns clear error message in background mode

**MCP server not found:**
- Install with uvx: `uvx blender-remote`
- Check PATH and restart IDE

### Debug Mode

```bash
# Test MCP server directly
pixi run python -m blender_remote.mcp_server

# Use FastMCP inspector
pixi run fastmcp dev src/blender_remote/mcp_server.py
```

## 🤝 Contributing

We welcome contributions! Please see our [Development Guide](development.md) for:

- **Architecture Overview**: Understanding the system design
- **Adding New Tools**: Implementing additional MCP functionality
- **Testing Framework**: Comprehensive test suite
- **Code Quality**: Style guide and best practices

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make changes and add tests
4. Run the test suite
5. Submit a pull request

## 📄 License

[MIT License](../LICENSE)

## 🙏 Credits

This project was inspired by [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp), which demonstrated the potential for integrating Blender with the Model Context Protocol. We extend our gratitude to the original developers for pioneering this concept.

blender-remote builds upon this foundation with enhanced features including background mode support, thread-safe operations, comprehensive testing, and production-ready deployment capabilities.

## 🔗 Links

- **📦 GitHub**: [igamenovoer/blender-remote](https://github.com/igamenovoer/blender-remote)
- **🐛 Issue Tracker**: [Report bugs and request features](https://github.com/igamenovoer/blender-remote/issues)
- **💬 Discussions**: [Community support](https://github.com/igamenovoer/blender-remote/discussions)
- **📖 Documentation**: [https://igamenovoer.github.io/blender-remote/](https://igamenovoer.github.io/blender-remote/)

---

**🎯 Ready to supercharge your Blender workflow with AI? Start with the [MCP Server Guide](mcp-server.md) or jump straight to [LLM Integration](llm-integration.md)!**
