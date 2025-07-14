# Blender Remote Client Testing Guide

This directory contains comprehensive tests for the blender-remote client classes with **I/O focused testing** and built-in fallback communication methods for robust validation.

## Testing Focus: Input/Output Handling ⭐

**Key Insight**: Core Blender logic was already validated with `blender-mcp` - problems typically arise in **input/output handling layers**.

**I/O Focus Areas** (Correctness Only - Localhost):
- **Input Validation**: Parameter validation, type conversion correctness, coordinate handling
- **Output Processing**: Response parsing correctness, string extraction, JSON handling  
- **Data Transmission**: Data integrity, encoding correctness, command serialization
- **Error Handling**: Exception mapping correctness, error response processing

## Quick Start

### 1. Run All Tests with Automatic Fallback
```bash
# Run complete test suite with fallback communication
pixi run python context/tests/run_all_tests.py
```

### 2. Test Communication Methods Detection
```bash
# Detect which communication methods are working
pixi run python context/tests/test_fallback_communication.py
```

### 3. Run I/O Focused Tests (Priority)
```bash
# Test input/output handling layers specifically
pixi run python context/tests/test_io_handling_focused.py
```

### 4. Run Enhanced Tests with Fallback
```bash
# Run tests that automatically fall back to working methods
pixi run python context/tests/test_with_fallback.py
```

## Communication Methods

The test infrastructure supports multiple communication paths to Blender:

| Method | Description | Use Case |
|--------|-------------|----------|
| **Direct Client** | `BlenderMCPClient` + `BlenderSceneManager` | Primary testing method |
| **Blender Remote MCP** | `uvx blender-remote` MCP server | Fallback when client classes fail |
| **TCP Direct** | Direct socket to BLD_Remote_MCP (port 6688) | Service-level validation |
| **Original Blender MCP** | `uvx blender-mcp` (3rd party) | Compatibility testing |

## Test Files Overview

| File | Purpose | Communication Method |
|------|---------|---------------------|
| `test_io_handling_focused.py` | **I/O boundary testing** ⭐ | Mock/Direct |
| `test_client_connection.py` | BlenderMCPClient connection tests | Direct Client |
| `test_scene_manager_objects.py` | Object manipulation tests | Direct Client |
| `test_scene_manager_export.py` | GLB export functionality tests | Direct Client |
| `test_fallback_communication.py` | Multi-method communication test | All Methods |
| `test_with_fallback.py` | Enhanced tests with auto-fallback | All Methods |
| `run_all_tests.py` | Complete test suite runner | All Methods |

## Troubleshooting Guide

### Problem: I/O handling issues (Priority Focus)

**Symptoms**: Core operations work via MCP server but fail via client classes

**Solution**: Run I/O focused tests to isolate the problem layer

```bash
# 1. Test I/O handling specifically
pixi run python context/tests/test_io_handling_focused.py

# 2. Cross-validate same operations via MCP server
pixi run mcp dev src/blender_remote/mcp_server.py
# Test same operations manually at http://localhost:3000

# 3. Compare results to identify I/O layer issues
```

**Common I/O Correctness Issues**:
- **String parsing fails**: Output format changed, affecting parsing logic correctness
- **Type conversion errors**: Coordinate/parameter validation incorrectness  
- **JSON parsing issues**: Invalid JSON or unexpected response format structure
- **Data transmission**: Encoding errors, character corruption, or data integrity issues
- **Error mapping**: Incorrect exception types or missing error detection

### Problem: Primary method (Direct Client) fails

**Solution**: Use fallback methods for validation

```bash
# 1. Check which methods work
pixi run python context/tests/test_fallback_communication.py

# 2. If MCP server works, use it for validation
pixi run mcp dev src/blender_remote/mcp_server.py
# Open http://localhost:3000 and test manually

# 3. If TCP works, use direct commands
python -c "
import socket, json
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('127.0.0.1', 6688))
command = {'message': 'test', 'code': 'print(\"Blender OK\")'}
sock.sendall(json.dumps(command).encode('utf-8'))
print(sock.recv(4096).decode('utf-8'))
sock.close()
"
```

### Problem: All communication methods fail

**Root Cause Checklist**:
1. ❓ Is Blender running?
2. ❓ Is BLD_Remote_MCP addon loaded in Blender?
3. ❓ Is the service running on port 6688?
4. ❓ Are there firewall/permission issues?

**Solution Steps**:
```bash
# 1. Start Blender with auto-start MCP service
export BLD_REMOTE_MCP_START_NOW=1
export BLD_REMOTE_MCP_PORT=6688
blender &

# 2. Wait for startup (10 seconds)
sleep 10

# 3. Test basic connectivity
netstat -tlnp | grep 6688

# 4. Re-run communication test
pixi run python context/tests/test_fallback_communication.py
```

### Problem: Tests pass but give unexpected results

**Cross-Validation Approach**:
```bash
# 1. Run same operation via multiple methods
pixi run python context/tests/test_with_fallback.py

# 2. Compare results between methods manually
# Run test via Direct Client
pixi run python context/tests/test_scene_manager_objects.py

# Run same operations via MCP server
pixi run mcp dev src/blender_remote/mcp_server.py
# Use web interface to execute same Blender code

# 3. Check for consistency issues
```

## Advanced Usage

### Manual MCP Server Testing
```bash
# Start MCP server in development mode
pixi run mcp dev src/blender_remote/mcp_server.py

# Access web interface at http://localhost:3000
# Test methods manually:
# - get_scene_info
# - get_object_info  
# - execute_code
# - get_viewport_screenshot
```

### Base64 Encoding Test (for complex code)
```bash
# Test complex code execution with base64 encoding
python -c "
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test():
    server_params = StdioServerParameters(
        command='pixi', args=['run', 'python', 'src/blender_remote/mcp_server.py']
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool('execute_code', {
                'code': 'import bpy; print(bpy.context.scene.name)',
                'send_as_base64': True,
                'return_as_base64': True
            })
            print(result.content[0].text if result.content else 'No content')

asyncio.run(test())
"
```

### Performance Comparison
```bash
# Run tests with timing to compare method performance
time pixi run python context/tests/test_client_connection.py
time pixi run python context/tests/test_with_fallback.py
```

## Integration with Development Workflow

### During Development
1. **Primary**: Use Direct Client classes for normal development
2. **Validation**: Use MCP server fallback to verify Blender operations work
3. **Debugging**: Use TCP direct to isolate service vs client issues

### During Testing
1. **Comprehensive**: Run `run_all_tests.py` for full validation
2. **Quick Check**: Run `test_fallback_communication.py` to verify setup
3. **Specific Issues**: Run individual test files for targeted debugging

### During CI/CD
1. **Robust Testing**: Use fallback methods to handle environment variations
2. **Issue Isolation**: Identify whether failures are in client code or service setup
3. **Compatibility**: Verify backward compatibility with original blender-mcp

## Expected Test Outputs

### Successful Test Run
```
=== Blender Remote Client Test Suite ===
Started at: 2025-07-14 15:30:00

🔍 Detecting working communication methods...
✅ Direct BlenderMCPClient: Working
✅ TCP Direct to BLD_Remote_MCP: Working
✅ Blender Remote MCP: Available (will test async)

[PASS] basic_functionality: Direct Client succeeded
[PASS] object_creation: Direct Client succeeded  
[PASS] scene_manipulation: Direct Client succeeded

✅ Successful: 3/3
🔧 Working Communication Methods: direct_client, tcp_direct, blender_remote_mcp
```

### Failure with Fallback Recovery
```
❌ Direct BlenderMCPClient: Connection failed
✅ TCP Direct to BLD_Remote_MCP: Working
✅ Blender Remote MCP: Available

🔄 Trying basic_functionality with TCP Direct...
✅ basic_functionality: TCP Direct succeeded

⚠️ Primary method failed, but fallback methods work:
  • Use tcp_direct for basic_functionality functionality
```

## Contributing

When adding new tests:
1. **Include fallback support** for robust testing
2. **Test cross-validation** between communication methods
3. **Document expected behavior** for each communication path
4. **Handle errors gracefully** with informative messages

For questions or issues, check the fallback communication logs in `context/logs/tests/`.