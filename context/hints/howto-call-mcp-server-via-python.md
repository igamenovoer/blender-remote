# How to Call MCP Servers via Python

This guide documents three practical approaches for calling MCP (Model Context Protocol) servers programmatically using Python.

## Overview

1. **🏆 MCP CLI Tools (RECOMMENDED)** - Official MCP protocol using the `mcp[cli]` package and Python SDK
2. **Direct TCP Socket Connection** - Direct communication with MCP servers via socket connections  
3. **Direct Tool Import (FastMCP only)** - Importing and calling FastMCP server tools directly in Python

## Approach 1: MCP CLI Tools (RECOMMENDED) ✅

### Installation
```bash
# Using pixi (recommended for this project)
pixi list | grep mcp  # Already available: mcp 1.10.1

# Using other package managers
uv add "mcp[cli]"
pip install "mcp[cli]"
```

### Server Startup
```bash
# MCP Inspector (interactive testing)
pixi run mcp dev context/refcode/blender-mcp/src/blender_mcp/server.py

# Direct execution
pixi run mcp run context/refcode/blender-mcp/src/blender_mcp/server.py --transport stdio
```

### Python SDK Implementation
```python
import asyncio
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def interact_with_mcp_server():
    server_params = StdioServerParameters(
        command="pixi",
        args=["run", "python", "path/to/server.py"],
        env=None,
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # List tools
            tools = await session.list_tools()
            print(f"Available tools: {[tool.name for tool in tools.tools]}")
            
            # Call tool
            result = await session.call_tool("get_scene_info", {})
            print(f"Result: {result}")

# Run client
asyncio.run(interact_with_mcp_server())
```

### Key Benefits
- ✅ Official protocol compliance
- ✅ Type safety and validation  
- ✅ Excellent debugging tools (MCP Inspector)
- ✅ Claude Desktop integration
- ✅ Future-proof compatibility

## Approach 2: Direct TCP Socket Connection ✅

### Implementation
```python
import socket
import json

def call_mcp_command(host="127.0.0.1", port=9876, command_type="get_scene_info", params=None):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    
    command = {"type": command_type, "params": params or {}}
    sock.sendall(json.dumps(command).encode('utf-8'))
    
    response_data = sock.recv(8192)
    response = json.loads(response_data.decode('utf-8'))
    
    sock.close()
    return response

# Usage
scene_info = call_mcp_command(port=9876, command_type="get_scene_info")
print(f"Scene: {scene_info['result']['name']}")
```

### Use Cases
- Low-level protocol control
- Non-MCP-compliant servers
- Simple automation scripts

## Approach 3: Direct Tool Import (FastMCP only) ✅

**Note**: This approach only works with FastMCP-based implementations. It requires direct access to the server code and is primarily useful for development and testing.

### Implementation
```python
import sys
sys.path.insert(0, "path/to/fastmcp/server/src")

# Only works with FastMCP servers
from blender_mcp.server import get_scene_info, execute_blender_code
from mcp.server.fastmcp import Context

ctx = Context()
scene_result = get_scene_info(ctx)
code_result = execute_blender_code(ctx, "import bpy; print('Hello')")
```

### Limitations
- Only compatible with FastMCP framework
- Requires server source code access
- Development/testing use only

## Testing

### Quick Test Commands
```bash
# Test MCP CLI approach
pixi run python test_mcp_cli_client_pixi.py

# Test direct connection
pixi run python test_blender_mcp_direct.py

# Check running servers
netstat -tlnp | grep -E "(9876|6688)"
```

### Test Files Available
- `test_mcp_cli_client_pixi.py` - MCP CLI test (recommended)
- `test_blender_mcp_direct.py` - Direct TCP and tool import tests

## Conclusion

**Recommended**: Use **MCP CLI Tools (Approach 1)** for standard-compliant, robust MCP server interaction with excellent developer experience and future compatibility.

**Alternative**: Use **Direct TCP Socket Connection (Approach 2)** for low-level control or non-MCP servers.

**Development Only**: Use **Direct Tool Import (Approach 3)** exclusively for FastMCP development and testing scenarios.