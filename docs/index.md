# Blender Remote

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

## 🚀 Quick Start

### For LLM Users

1. **Install Blender Add-on**
   ```bash
   cd ~/.config/blender/4.4/scripts/addons/
   wget -O bld_remote_mcp.zip https://github.com/igamenovoer/blender-remote/raw/main/blender_addon/bld_remote_mcp.zip
   unzip bld_remote_mcp.zip
   ```

2. **Start Blender with Auto-Service**
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

## 🔗 Links

- **📦 GitHub**: [igamenovoer/blender-remote](https://github.com/igamenovoer/blender-remote)
- **🐛 Issue Tracker**: [Report bugs and request features](https://github.com/igamenovoer/blender-remote/issues)
- **💬 Discussions**: [Community support](https://github.com/igamenovoer/blender-remote/discussions)
- **📖 Documentation**: [https://igamenovoer.github.io/blender-remote/](https://igamenovoer.github.io/blender-remote/)

---

**🎯 Ready to supercharge your Blender workflow with AI? Start with the [MCP Server Guide](mcp-server.md) or jump straight to [LLM Integration](llm-integration.md)!**
