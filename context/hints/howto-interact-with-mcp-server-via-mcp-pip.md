# How to Interact with MCP Server via MCP-PIP

This guide explains how to interact with Model Context Protocol (MCP) servers using the `mcp` Python SDK, including both command-line tools and programmatic client approaches.

## Installation

### Install MCP Python SDK

```bash
# Install the MCP SDK with CLI tools
pip install "mcp[cli]"

# Or using uv (recommended)
uv add "mcp[cli]"
```

### Additional Optional Dependencies

```bash
# For rich output formatting
pip install "mcp[rich]"

# For WebSocket support
pip install "mcp[ws]"

# All optional dependencies
pip install "mcp[cli,rich,ws]"
```

## Command Line Interface (CLI)

The MCP SDK provides several CLI commands for interacting with MCP servers:

### 1. Development and Testing

#### MCP Inspector (Interactive Testing)

```bash
# Test a server with the MCP Inspector
uv run mcp dev server.py

# With additional dependencies
uv run mcp dev server.py --with pandas --with numpy

# With editable local package
uv run mcp dev server.py --with-editable .
```

#### Direct Server Execution

```bash
# Run a server directly
uv run mcp run server.py

# Run with specific transport
uv run mcp run server.py --transport stdio
uv run mcp run server.py --transport sse
```

### 2. Claude Desktop Integration

```bash
# Install server in Claude Desktop
uv run mcp install server.py

# With custom name
uv run mcp install server.py --name "My Custom Server"

# With environment variables
uv run mcp install server.py -v API_KEY=abc123 -v DB_URL=postgres://...

# Load env vars from file
uv run mcp install server.py -f .env
```

### 3. Version Information

```bash
# Check MCP version
uv run mcp version
```

## Programmatic Client Interaction

### 1. Basic Client Setup

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def connect_to_server():
    # Configure server parameters
    server_params = StdioServerParameters(
        command="python",  # Or "uv", "uvx", "npx", etc.
        args=["server.py"],  # Server script and arguments
        env=None,  # Optional environment variables
    )
    
    # Connect to server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            
            # Now you can interact with the server
            await interact_with_server(session)

async def interact_with_server(session: ClientSession):
    # List available tools
    tools = await session.list_tools()
    print(f"Available tools: {[tool.name for tool in tools.tools]}")
    
    # List available resources
    resources = await session.list_resources()
    print(f"Available resources: {[res.uri for res in resources.resources]}")
    
    # List available prompts
    prompts = await session.list_prompts()
    print(f"Available prompts: {[prompt.name for prompt in prompts.prompts]}")
    
    # Call a tool
    if tools.tools:
        tool_name = tools.tools[0].name
        result = await session.call_tool(tool_name, arguments={"arg": "value"})
        print(f"Tool result: {result}")
    
    # Read a resource
    if resources.resources:
        resource_uri = resources.resources[0].uri
        content = await session.read_resource(resource_uri)
        print(f"Resource content: {content}")

# Run the client
asyncio.run(connect_to_server())
```

### 2. HTTP/SSE Client

```python
from mcp.client.sse import sse_client

async def connect_via_sse():
    # Connect to SSE server
    async with sse_client("http://localhost:8000/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            # Interact with server...
```

### 3. Streamable HTTP Client

```python
from mcp.client.streamable_http import streamablehttp_client

async def connect_via_streamable_http():
    # Connect to Streamable HTTP server
    async with streamablehttp_client("http://localhost:3000/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            # Interact with server...
```

### 4. Multi-Server Client Example

```python
import asyncio
import json
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPClientManager:
    def __init__(self, servers_config):
        self.servers_config = servers_config
        self.sessions = {}
        self.exit_stack = AsyncExitStack()
    
    async def initialize_servers(self):
        """Initialize all configured servers."""
        for name, config in self.servers_config.items():
            server_params = StdioServerParameters(
                command=config["command"],
                args=config["args"],
                env=config.get("env")
            )
            
            # Connect to server
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read, write = stdio_transport
            
            # Create session
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await session.initialize()
            
            self.sessions[name] = session
            print(f"✅ Connected to {name}")
    
    async def list_all_tools(self):
        """List tools from all servers."""
        all_tools = {}
        for name, session in self.sessions.items():
            tools = await session.list_tools()
            all_tools[name] = [tool.name for tool in tools.tools]
        return all_tools
    
    async def execute_tool(self, server_name, tool_name, arguments):
        """Execute a tool on a specific server."""
        if server_name not in self.sessions:
            raise ValueError(f"Server {server_name} not found")
        
        session = self.sessions[server_name]
        return await session.call_tool(tool_name, arguments)
    
    async def cleanup(self):
        """Clean up all connections."""
        await self.exit_stack.aclose()

# Usage example
async def main():
    # Server configuration
    servers_config = {
        "sqlite": {
            "command": "uvx",
            "args": ["mcp-server-sqlite", "--db-path", "./test.db"]
        },
        "filesystem": {
            "command": "uvx",
            "args": ["mcp-server-filesystem", "/path/to/files"]
        }
    }
    
    client = MCPClientManager(servers_config)
    
    try:
        await client.initialize_servers()
        
        # List all available tools
        tools = await client.list_all_tools()
        print(f"Available tools: {tools}")
        
        # Execute a tool
        result = await client.execute_tool(
            "sqlite", 
            "query", 
            {"sql": "SELECT * FROM users LIMIT 5"}
        )
        print(f"Query result: {result}")
        
    finally:
        await client.cleanup()

asyncio.run(main())
```

## Authentication (OAuth)

For servers that require authentication:

```python
from mcp.client.auth import OAuthClientProvider, TokenStorage
from mcp.client.streamable_http import streamablehttp_client
from mcp.shared.auth import OAuthClientMetadata, OAuthToken

class SimpleTokenStorage(TokenStorage):
    def __init__(self):
        self._tokens = None
        self._client_info = None
    
    async def get_tokens(self) -> OAuthToken | None:
        return self._tokens
    
    async def set_tokens(self, tokens: OAuthToken) -> None:
        self._tokens = tokens
    
    async def get_client_info(self):
        return self._client_info
    
    async def set_client_info(self, client_info) -> None:
        self._client_info = client_info

async def connect_with_auth():
    # Set up OAuth authentication
    oauth_auth = OAuthClientProvider(
        server_url="https://api.example.com",
        client_metadata=OAuthClientMetadata(
            client_name="My MCP Client",
            redirect_uris=["http://localhost:3000/callback"],
            grant_types=["authorization_code", "refresh_token"],
            response_types=["code"],
        ),
        storage=SimpleTokenStorage(),
        redirect_handler=lambda url: print(f"Visit: {url}"),
        callback_handler=lambda: ("auth_code", None),
    )
    
    # Use with streamable HTTP client
    async with streamablehttp_client(
        "https://api.example.com/mcp", 
        auth=oauth_auth
    ) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            # Now you have an authenticated session
```

## Server Configuration Examples

### Common Server Configurations

```json
{
  "mcpServers": {
    "sqlite": {
      "command": "uvx",
      "args": ["mcp-server-sqlite", "--db-path", "./database.db"]
    },
    "filesystem": {
      "command": "uvx", 
      "args": ["mcp-server-filesystem", "/home/user/documents"]
    },
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"]
    },
    "custom-python": {
      "command": "python",
      "args": ["custom_server.py"],
      "env": {
        "API_KEY": "your-api-key",
        "DEBUG": "true"
      }
    }
  }
}
```

### Using UV for Server Management

```bash
# Run server with UV
uvx mcp-server-sqlite --db-path ./test.db

# Run server with additional packages
uv run --with pandas --with numpy server.py
```

## Error Handling and Best Practices

### 1. Robust Client Implementation

```python
import asyncio
import logging
from typing import Any, Dict, List

class RobustMCPClient:
    def __init__(self, server_params, max_retries=3):
        self.server_params = server_params
        self.max_retries = max_retries
        self.logger = logging.getLogger(__name__)
    
    async def execute_tool_with_retry(self, session, tool_name, arguments, retries=None):
        """Execute a tool with retry logic."""
        if retries is None:
            retries = self.max_retries
        
        for attempt in range(retries):
            try:
                result = await session.call_tool(tool_name, arguments)
                return result
            except Exception as e:
                self.logger.warning(f"Tool execution failed (attempt {attempt + 1}): {e}")
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    async def safe_list_tools(self, session):
        """Safely list tools with error handling."""
        try:
            tools = await session.list_tools()
            return tools.tools
        except Exception as e:
            self.logger.error(f"Failed to list tools: {e}")
            return []
```

### 2. Connection Management

```python
async def managed_connection(server_params):
    """Context manager for MCP connections."""
    session = None
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session
    except Exception as e:
        logging.error(f"Connection failed: {e}")
        raise
    finally:
        if session:
            # Cleanup is handled by context managers
            pass
```

## Debugging and Monitoring

### 1. Enable Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# MCP specific logging
logging.getLogger('mcp').setLevel(logging.DEBUG)
```

### 2. Connection Diagnostics

```python
async def diagnose_connection(session):
    """Diagnose MCP server connection."""
    try:
        # Test basic connectivity
        await session.initialize()
        print("✅ Connection established")
        
        # Test capabilities
        tools = await session.list_tools()
        print(f"✅ Tools: {len(tools.tools)}")
        
        resources = await session.list_resources()
        print(f"✅ Resources: {len(resources.resources)}")
        
        prompts = await session.list_prompts()
        print(f"✅ Prompts: {len(prompts.prompts)}")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        raise
```

## Common Use Cases

### 1. Data Processing Pipeline

```python
async def data_processing_pipeline():
    """Example of using MCP for data processing."""
    server_params = StdioServerParameters(
        command="uvx",
        args=["mcp-server-sqlite", "--db-path", "./data.db"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Query data
            raw_data = await session.call_tool("query", {
                "sql": "SELECT * FROM raw_data"
            })
            
            # Process data (example)
            processed_data = await session.call_tool("execute", {
                "sql": "INSERT INTO processed_data SELECT * FROM raw_data WHERE condition = 'valid'"
            })
            
            return processed_data
```

### 2. File Operations

```python
async def file_operations():
    """Example of file operations via MCP."""
    server_params = StdioServerParameters(
        command="uvx",
        args=["mcp-server-filesystem", "/workspace"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # List files
            files = await session.call_tool("list_directory", {
                "path": "/workspace/data"
            })
            
            # Read file
            content = await session.read_resource("file:///workspace/data/input.txt")
            
            # Write file
            await session.call_tool("write_file", {
                "path": "/workspace/data/output.txt",
                "content": "processed data"
            })
```

## Summary

The MCP Python SDK provides comprehensive tools for interacting with MCP servers:

1. **CLI Tools**: For development, testing, and Claude Desktop integration
2. **Programmatic Clients**: For building custom applications
3. **Multiple Transports**: stdio, SSE, and Streamable HTTP
4. **Authentication**: OAuth support for secure connections
5. **Error Handling**: Robust connection and error management

Key benefits:
- **Standardized Protocol**: Consistent interface across different servers
- **Transport Flexibility**: Choose the best transport for your use case
- **Authentication Support**: Built-in OAuth for secure connections
- **Development Tools**: MCP Inspector for interactive testing
- **Integration Ready**: Easy Claude Desktop integration

This approach allows you to build robust MCP clients that can interact with any MCP-compliant server, whether it's a database interface, file system, web scraper, or custom business logic server.
