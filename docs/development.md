# Development Guide

This guide covers the development of blender-remote, including architecture, adding new features, testing, and contributing to the project.

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    LLM IDE Layer                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   VSCode    │  │   Claude    │  │   Cursor    │            │
│  │ (Claude Dev)│  │  Desktop    │  │   (AI)      │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────┬───────────────────────────────────────┘
                          │ MCP Protocol (stdio)
┌─────────────────────────▼───────────────────────────────────────┐
│                  MCP Server Layer                               │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │            uvx blender-remote                               ││
│  │  ┌─────────────────────────────────────────────────────────┐││
│  │  │         src/blender_remote/mcp_server.py                │││
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │││
│  │  │  │   FastMCP   │  │    Tool     │  │ Connection  │    │││
│  │  │  │   Server    │  │  Handlers   │  │  Manager    │    │││
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘    │││
│  │  └─────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────┬───────────────────────────────────────┘
                          │ JSON-TCP (port 6688)
┌─────────────────────────▼───────────────────────────────────────┐
│                 Blender Service Layer                           │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │         blender_addon/bld_remote_mcp/                       ││
│  │  ┌─────────────────────────────────────────────────────────┐││
│  │  │                __init__.py                              │││
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │││
│  │  │  │   TCP       │  │  Command    │  │   Scene     │    │││
│  │  │  │  Server     │  │  Handlers   │  │  Manager    │    │││
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘    │││
│  │  └─────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────┬───────────────────────────────────────┘
                          │ Blender Python API
┌─────────────────────────▼───────────────────────────────────────┐
│                    Blender Application                          │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          ││
│  │  │    Scene    │  │  Objects    │  │  Viewport   │          ││
│  │  │  Manager    │  │  Manager    │  │  Renderer   │          ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘          ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **LLM Request**: IDE sends MCP request via stdio
2. **MCP Processing**: FastMCP server processes request
3. **Tool Execution**: Appropriate tool handler is called
4. **Blender Communication**: JSON-TCP request to BLD_Remote_MCP
5. **Blender Execution**: Blender addon executes operation
6. **Response Chain**: Results flow back through the layers

## Project Structure

```
blender-remote/
├── src/blender_remote/              # Python package
│   ├── __init__.py                  # Package initialization
│   ├── mcp_server.py               # FastMCP server implementation
│   └── cli.py                      # CLI tools
├── blender_addon/                  # Blender addon
│   └── bld_remote_mcp/            # BLD_Remote_MCP service
│       ├── __init__.py            # Main addon logic
│       ├── config.py              # Configuration management
│       ├── utils.py               # Utility functions
│       └── async_loop.py          # Async event loop
├── tests/                         # Test suite
│   ├── mcp-server/               # MCP server tests
│   ├── integration/              # Integration tests
│   └── others/                   # Development scripts
├── docs/                         # Documentation
├── examples/                     # Usage examples
└── context/                      # Development context
```

## Development Environment Setup

### Prerequisites

- **Python 3.10+**
- **Blender 4.4.3+**
- **pixi** (recommended) or **pip**
- **Git**

### Setup Steps

1. **Clone Repository**
   ```bash
   git clone https://github.com/igamenovoer/blender-remote.git
   cd blender-remote
   ```

2. **Install Dependencies**
   ```bash
   # Option 1: Using pixi (recommended)
   pixi install
   
   # Option 2: Using pip
   pip install -e .
   ```

3. **Install Blender Addon**
   ```bash
   # Copy addon to Blender directory
   cp -r blender_addon/bld_remote_mcp/ ~/.config/blender/4.4/scripts/addons/
   ```

4. **Configure Environment**
   ```bash
   export BLD_REMOTE_MCP_PORT=6688
   export BLD_REMOTE_MCP_START_NOW=1
   ```

5. **Start Blender**
   ```bash
   blender &
   ```

6. **Verify Setup**
   ```bash
   pixi run python tests/smoke_test.py
   ```

## MCP Server Architecture

### Core Components

#### 1. FastMCP Server (`src/blender_remote/mcp_server.py`)

```python
from fastmcp import FastMCP

# Create MCP server instance
mcp = FastMCP("Blender Remote MCP")

# Connection management
class ConnectionManager:
    def __init__(self):
        self.socket = None
        self.connected = False
    
    def connect(self):
        # Handle connection to BLD_Remote_MCP
        pass
    
    def send_command(self, command):
        # Send JSON-TCP command
        pass
```

#### 2. Tool Handlers

Each MCP tool is implemented as a handler function:

```python
@mcp.tool()
async def get_scene_info(ctx: Context) -> dict:
    """Get information about the current Blender scene."""
    try:
        # Connect to BLD_Remote_MCP
        conn = await get_connection()
        
        # Send command
        command = {"type": "get_scene_info", "params": {}}
        result = await conn.send_command(command)
        
        # Process response
        return result
    except Exception as e:
        await ctx.error(f"Failed to get scene info: {e}")
        return {"status": "error", "message": str(e)}
```

#### 3. Connection Management

```python
class ConnectionManager:
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = int(os.getenv("BLD_REMOTE_MCP_PORT", "6688"))
        self.socket = None
        self.connected = False
    
    async def ensure_connection(self):
        """Ensure connection is established."""
        if not self.connected:
            await self.connect()
    
    async def connect(self):
        """Connect to BLD_Remote_MCP service."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
        except Exception as e:
            raise ConnectionError(f"Failed to connect: {e}")
    
    async def send_command(self, command):
        """Send command and get response."""
        await self.ensure_connection()
        
        # Send command
        data = json.dumps(command).encode('utf-8')
        self.socket.sendall(data)
        
        # Receive response
        response = self.socket.recv(4096).decode('utf-8')
        return json.loads(response)
```

## Adding New MCP Tools

### Step 1: Define Tool Function

```python
@mcp.tool()
async def my_new_tool(ctx: Context, param1: str, param2: int = 10) -> dict:
    """
    Brief description of what this tool does.
    
    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2 (optional)
    
    Returns:
        Dictionary with result data
    """
    try:
        # Validate parameters
        if not param1:
            await ctx.error("param1 is required")
            return {"status": "error", "message": "param1 is required"}
        
        # Connect to BLD_Remote_MCP
        conn = await get_connection()
        
        # Prepare command
        command = {
            "type": "my_new_command",
            "params": {
                "param1": param1,
                "param2": param2
            }
        }
        
        # Send command
        result = await conn.send_command(command)
        
        # Log success
        await ctx.info(f"Tool executed successfully: {result}")
        
        return result
        
    except Exception as e:
        await ctx.error(f"Tool failed: {e}")
        return {"status": "error", "message": str(e)}
```

### Step 2: Add Blender Handler

In `blender_addon/bld_remote_mcp/__init__.py`:

```python
def handle_my_new_command(params):
    """Handle my_new_command in Blender."""
    try:
        param1 = params.get("param1")
        param2 = params.get("param2", 10)
        
        # Perform Blender operations
        result = perform_blender_operation(param1, param2)
        
        return {
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

# Register handler
COMMAND_HANDLERS["my_new_command"] = handle_my_new_command
```

### Step 3: Add Tests

Create `tests/mcp-server/test_my_new_tool.py`:

```python
import pytest
from blender_remote.mcp_server import my_new_tool

@pytest.mark.asyncio
async def test_my_new_tool():
    """Test my_new_tool functionality."""
    # Mock context
    class MockContext:
        def __init__(self):
            self.messages = []
        
        async def info(self, msg):
            self.messages.append(("info", msg))
        
        async def error(self, msg):
            self.messages.append(("error", msg))
    
    ctx = MockContext()
    
    # Test successful execution
    result = await my_new_tool(ctx, "test_param", 20)
    assert result["status"] == "success"
    
    # Test error handling
    result = await my_new_tool(ctx, "", 20)
    assert result["status"] == "error"
```

### Step 4: Update Documentation

Add to `docs/api-reference.md`:

```markdown
## my_new_tool

Description of what the tool does.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `param1` | `string` | Yes | Description of param1 |
| `param2` | `number` | No | Description of param2 (default: 10) |

### Returns

```typescript
{
  status: "success" | "error",
  result: {
    // Description of return structure
  }
}
```

### Example Usage

**LLM Prompt:** "Use my new tool with parameter 'test'"

**CLI:** `blender-remote my-new-tool --param1 "test" --param2 20`
```

## Testing Framework

### Test Structure

```
tests/
├── mcp-server/              # MCP server functionality tests
│   ├── test_fastmcp_server.py    # FastMCP server tests
│   ├── test_scene_info.py        # Scene info tool tests
│   ├── test_code_execution.py    # Code execution tests
│   └── test_screenshots.py       # Screenshot tests
├── integration/             # Integration tests
│   ├── test_dual_service.py      # Compare with BlenderAutoMCP
│   └── test_performance.py       # Performance benchmarks
├── others/                  # Development scripts
└── conftest.py             # Test configuration
```

### Running Tests

```bash
# Run all tests
pixi run python tests/run_dual_service_tests.py

# Run specific test category
pixi run python tests/run_dual_service_tests.py --mcp-server

# Run with verbose output
pixi run python tests/run_dual_service_tests.py --verbose

# Quick smoke test
pixi run python tests/smoke_test.py
```

### Test Categories

#### Unit Tests
Test individual components in isolation:

```python
@pytest.mark.unit
async def test_connection_manager():
    """Test connection manager functionality."""
    manager = ConnectionManager()
    
    # Test connection
    await manager.connect()
    assert manager.connected
    
    # Test command sending
    result = await manager.send_command({"type": "test"})
    assert result["status"] == "success"
```

#### Integration Tests
Test complete workflows:

```python
@pytest.mark.integration
async def test_scene_workflow():
    """Test complete scene creation workflow."""
    # Create scene
    code = "bpy.ops.mesh.primitive_cube_add()"
    result = await execute_blender_code(code)
    assert result["status"] == "success"
    
    # Verify scene
    scene = await get_scene_info()
    assert scene["result"]["total_objects"] > 0
    
    # Take screenshot
    if not is_background_mode():
        screenshot = await get_viewport_screenshot()
        assert screenshot["status"] == "success"
```

#### Performance Tests
Measure response times and resource usage:

```python
@pytest.mark.performance
async def test_tool_performance():
    """Test tool performance."""
    import time
    
    start = time.time()
    result = await get_scene_info()
    duration = time.time() - start
    
    assert result["status"] == "success"
    assert duration < 0.1  # Should be under 100ms
```

### Test Utilities

```python
# tests/conftest.py
import pytest
from blender_remote.mcp_server import ConnectionManager

@pytest.fixture
async def connection():
    """Provide a connection to BLD_Remote_MCP."""
    manager = ConnectionManager()
    await manager.connect()
    yield manager
    manager.close()

@pytest.fixture
def mock_context():
    """Provide a mock MCP context."""
    class MockContext:
        def __init__(self):
            self.messages = []
        
        async def info(self, msg):
            self.messages.append(("info", msg))
        
        async def error(self, msg):
            self.messages.append(("error", msg))
    
    return MockContext()
```

## Debugging

### Development Mode

Run MCP server in development mode:

```bash
# Start with debug logging
export BLD_REMOTE_MCP_LOG_LEVEL=DEBUG
pixi run python -m blender_remote.mcp_server

# Use FastMCP inspector
pixi run fastmcp dev src/blender_remote/mcp_server.py
```

### Connection Debugging

```python
# Test direct connection
import socket
import json

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('127.0.0.1', 6688))

command = {"type": "get_scene_info", "params": {}}
sock.sendall(json.dumps(command).encode())

response = sock.recv(4096).decode()
print(json.loads(response))
sock.close()
```

### Common Issues

#### Port Already in Use
```bash
# Find process using port
lsof -i :6688

# Kill process
kill -9 <PID>
```

#### Import Errors
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Install in development mode
pip install -e .
```

#### Blender Addon Issues
```bash
# Check addon directory
ls ~/.config/blender/4.4/scripts/addons/bld_remote_mcp/

# Check Blender console for errors
# Window → Toggle System Console (Windows)
# Or run from terminal (Linux/Mac)
```

## Code Quality

### Style Guide

Follow PEP 8 with these additions:

```python
# Function naming
async def get_scene_info():  # snake_case for functions
    pass

# Class naming
class ConnectionManager:  # PascalCase for classes
    pass

# Constants
DEFAULT_PORT = 6688  # UPPER_CASE for constants

# Type hints
async def my_tool(ctx: Context, param: str) -> dict:
    pass
```

### Linting

```bash
# Run linting
pixi run lint

# Format code
pixi run format

# Type checking
pixi run mypy src/
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

## Performance Optimization

### Connection Pooling

```python
class ConnectionPool:
    def __init__(self, max_connections=5):
        self.pool = []
        self.max_connections = max_connections
    
    async def get_connection(self):
        if self.pool:
            return self.pool.pop()
        return await self.create_connection()
    
    async def return_connection(self, conn):
        if len(self.pool) < self.max_connections:
            self.pool.append(conn)
        else:
            conn.close()
```

### Caching

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_cached_scene_info():
    """Cache scene info for performance."""
    return get_scene_info()
```

### Async Optimization

```python
import asyncio

async def batch_operations():
    """Execute multiple operations concurrently."""
    tasks = [
        get_scene_info(),
        get_object_info("Cube"),
        get_object_info("Camera")
    ]
    
    results = await asyncio.gather(*tasks)
    return results
```

## Security Considerations

### Input Validation

```python
def validate_object_name(name: str) -> bool:
    """Validate object name input."""
    if not name or not isinstance(name, str):
        return False
    
    # Check for dangerous characters
    dangerous_chars = ['/', '\\', '..', ';', '|']
    if any(char in name for char in dangerous_chars):
        return False
    
    return True
```

### Code Execution Safety

```python
def sanitize_code(code: str) -> str:
    """Sanitize Python code before execution."""
    # Remove dangerous imports
    dangerous_imports = ['os', 'sys', 'subprocess', 'socket']
    
    for imp in dangerous_imports:
        if f'import {imp}' in code:
            raise ValueError(f"Import of {imp} not allowed")
    
    return code
```

### Error Handling

```python
async def safe_execute(func, *args, **kwargs):
    """Safely execute function with error handling."""
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        # Log error without exposing sensitive information
        logger.error(f"Function {func.__name__} failed: {type(e).__name__}")
        return {"status": "error", "message": "Internal error occurred"}
```

## Contributing

### Development Workflow

1. **Fork Repository**
   ```bash
   git clone https://github.com/yourusername/blender-remote.git
   cd blender-remote
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/my-new-feature
   ```

3. **Make Changes**
   - Write code following style guide
   - Add tests for new functionality
   - Update documentation

4. **Test Changes**
   ```bash
   pixi run python tests/run_dual_service_tests.py
   ```

5. **Commit Changes**
   ```bash
   git add .
   git commit -m "Add new MCP tool for X functionality"
   ```

6. **Push and Create PR**
   ```bash
   git push origin feature/my-new-feature
   # Create pull request on GitHub
   ```

### Pull Request Guidelines

1. **Description**: Clear description of changes and motivation
2. **Tests**: Include tests for new functionality
3. **Documentation**: Update relevant documentation
4. **Backward Compatibility**: Ensure no breaking changes
5. **Performance**: Consider performance implications

### Code Review Process

1. **Automated Checks**: CI runs tests and linting
2. **Manual Review**: Core maintainers review code
3. **Feedback**: Address review comments
4. **Approval**: Get approval from maintainers
5. **Merge**: Maintainers merge approved PRs

## Release Process

### Version Management

```bash
# Update version in pyproject.toml
version = "1.1.0"

# Create git tag
git tag -a v1.1.0 -m "Release version 1.1.0"
git push origin v1.1.0
```

### Build Process

```bash
# Build package
pixi run build

# Test installation
pip install dist/blender-remote-1.1.0.tar.gz

# Test functionality
uvx blender-remote --help
```

### Publishing

```bash
# Upload to PyPI
pixi run publish

# Update documentation
pixi run docs
```

## Troubleshooting Development Issues

### Common Problems

#### FastMCP Import Errors
```bash
# Install correct version
pip install fastmcp>=2.0.0

# Check installation
python -c "import fastmcp; print(fastmcp.__version__)"
```

#### Blender Connection Issues
```bash
# Check service status
netstat -tlnp | grep 6688

# Restart Blender
pkill -f blender
export BLD_REMOTE_MCP_START_NOW=1
blender &
```

#### Test Failures
```bash
# Run specific test
pytest tests/mcp-server/test_fastmcp_server.py -v

# Debug test
pytest tests/mcp-server/test_fastmcp_server.py --pdb
```

### Getting Help

1. **Documentation**: Check existing docs first
2. **Issues**: Search GitHub issues for similar problems
3. **Discussions**: Use GitHub discussions for questions
4. **Code**: Read existing code for patterns

## Future Development

### Planned Features

1. **Enhanced Tools**
   - Animation control tools
   - Rendering pipeline tools
   - Asset management tools

2. **Performance Improvements**
   - Connection pooling
   - Response caching
   - Async optimizations

3. **UI Improvements**
   - Better error messages
   - Progress indicators
   - Configuration GUI

### Contributing Ideas

1. **New MCP Tools**: Implement additional Blender functionality
2. **IDE Integrations**: Support for more IDEs
3. **Documentation**: Improve docs and examples
4. **Testing**: Add more comprehensive tests

## Resources

### Documentation
- [MCP Server Guide](mcp-server.md)
- [API Reference](api-reference.md)
- [LLM Integration](llm-integration.md)

### External Resources
- [FastMCP Documentation](https://fastmcp.readthedocs.io/)
- [Blender Python API](https://docs.blender.org/api/current/)
- [Model Context Protocol](https://spec.modelcontextprotocol.io/)

### Community
- [GitHub Repository](https://github.com/igamenovoer/blender-remote)
- [Issue Tracker](https://github.com/igamenovoer/blender-remote/issues)
- [Discussions](https://github.com/igamenovoer/blender-remote/discussions)

---

**Ready to contribute to blender-remote? Start with the [development setup](#development-environment-setup) and check out the [issue tracker](https://github.com/igamenovoer/blender-remote/issues) for good first issues!**