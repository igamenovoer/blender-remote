# MCP Server Test Suite

This directory contains tests for the blender-remote MCP server functionality.

## Test Files

### Core MCP Server Tests
- `test_fastmcp_server.py` - FastMCP server functionality validation
- `test_mcp_server.py` - General MCP server testing
- `test_mcp_start.py` - MCP server startup testing
- `run_mcp_server.py` - Development server runner

### Screenshot Functionality Tests
- `test_base64_screenshot.py` - Base64 screenshot encoding validation
- `test_viewport_screenshot.py` - Viewport screenshot capture testing
- `test_background_screenshot.py` - Background mode screenshot limitation testing

### Code Execution Tests
- `test_numpy_execution.py` - NumPy code execution validation
- `test_scoping_issue.py` - Python scoping behavior testing
- `test_original_failing_code.py` - Original user code validation

## Running Tests

### Prerequisites
- Blender running with BLD_Remote_MCP addon enabled
- Service listening on port 6688
- GUI mode for screenshot tests

### Individual Tests
```bash
# Run from project root
pixi run python tests/mcp-server/test_fastmcp_server.py
pixi run python tests/mcp-server/test_base64_screenshot.py
```

### Test Categories
- **Integration Tests**: Tests that require running Blender instance
- **Unit Tests**: Tests that can run independently
- **Screenshot Tests**: Tests that require GUI mode (not background)
- **Code Execution Tests**: Tests that validate Python code execution

## Test Results
All tests validate the MCP server's compatibility with:
- LLM clients expecting base64 image data
- Concurrent screenshot requests (UUID-based)
- Complex Python code execution with proper scoping
- Background mode limitations and error handling