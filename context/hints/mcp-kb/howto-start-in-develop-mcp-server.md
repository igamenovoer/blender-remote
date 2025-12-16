# How to Start MCP Server in VS Code During Development

This guide explains how to properly configure and start the blender-remote MCP server in VS Code for development purposes.

## Prerequisites

- VS Code with MCP extension installed
- Pixi environment manager installed
- Blender-remote project with pixi configuration

## Configuration

### 1. MCP Server Configuration

Create or update `.vscode/mcp.json` in your project root:

```json
{
    "servers": {
        "blender-remote-dev": {
            "command": "pixi",
            "args": [
                "run",
                "mcp-server",
                "--mcp-port",
                "8088",
                "--blender-port",
                "6688"
            ],
            "cwd": "/workspace/code/blender-remote"
        }
    },
    "inputs": []
}
```

### 2. Key Configuration Elements

- **`"command": "pixi"`** - Uses pixi to manage the Python environment
- **`"args": ["run", "mcp-server", ...]`** - Runs the predefined pixi task with arguments
- **`"cwd": "/path/to/project"`** - Sets working directory (absolute path required)
- **`--mcp-port 8088`** - Port for MCP server (adjust as needed)
- **`--blender-port 6688`** - Port to connect to Blender's BLD_Remote_MCP service

## How It Works

### Pixi Task Integration

The configuration leverages the pixi task defined in `pyproject.toml`:

```toml
[tool.pixi.tasks]
mcp-server = "python -m blender_remote.mcp_server"
```

This approach provides:
- **Automatic environment activation** - Pixi handles Python environment setup
- **Dependency management** - All packages from `pyproject.toml` are available
- **Consistent execution** - Same environment as other development tasks
- **No manual PYTHONPATH** - Pixi manages module resolution

### Architecture

```
VS Code MCP Extension → pixi run mcp-server → Python Module → Blender TCP Service
```

## Starting the Server

### Method 1: VS Code MCP Extension
1. Open VS Code in the project directory
2. The MCP extension should automatically detect the configuration
3. Start the server through the MCP extension interface

### Method 2: Manual Command Line (for testing)
```bash
cd /workspace/code/blender-remote
pixi run mcp-server --mcp-port 8088 --blender-port 6688
```

## Troubleshooting

### Common Issues

1. **"unexpected argument '--cwd' found"**
   - ❌ Don't use `--cwd` in pixi run arguments
   - ✅ Use `"cwd"` property in VS Code configuration

2. **"Module not found"**
   - Ensure `cwd` points to the project root with `pyproject.toml`
   - Verify pixi environment includes all dependencies

3. **"Port already in use"**
   - Change `--mcp-port` to an available port
   - Check for other running MCP servers

### Verification Commands

Test the pixi environment:
```bash
pixi run python -c "import blender_remote; print('✅ Module imported successfully')"
```

Test the MCP server directly:
```bash
pixi run mcp-server --help
```

## Development Workflow

1. **Start Blender** with the BLD_Remote_MCP addon enabled (port 6688)
2. **Configure VS Code** with the MCP server settings above
3. **Start MCP server** through VS Code MCP extension
4. **Begin development** - the server will connect to Blender automatically

## Port Configuration

- **MCP Server Port** (8088): Used by VS Code to communicate with the MCP server
- **Blender Port** (6688): Used by MCP server to communicate with Blender
- Make sure these ports don't conflict with other services

## Benefits of This Setup

- ✅ **Environment isolation** - Pixi manages dependencies
- ✅ **Reproducible builds** - Locked environment via `pixi.lock`
- ✅ **Easy maintenance** - Single configuration in `pyproject.toml`
- ✅ **Development efficiency** - Fast startup and reload
- ✅ **Cross-platform compatibility** - Works on Linux, macOS, Windows

## Next Steps

After the MCP server is running:
1. Test connection to Blender
2. Verify MCP tools are accessible in VS Code
3. Begin Blender automation development
