# MCP CLI Tools Tests

This directory contains test scripts for Model Context Protocol (MCP) CLI tools and programmatic interaction methods.

## Test Scripts

### **`test_mcp_cli_client_pixi.py` (RECOMMENDED)**
- **Purpose**: Test MCP CLI tools using pixi environment and official MCP Python SDK
- **Approach**: Official MCP protocol compliance using `mcp[cli]` package
- **Environment**: Uses pixi for package management (recommended for this project)
- **Features**: 
  - Tool discovery and listing
  - Scene information retrieval
  - Code execution in Blender
  - Screenshot capture testing
  - Proper error handling and logging

### **`test_mcp_cli_client.py`**
- **Purpose**: Test MCP CLI tools using uv environment
- **Approach**: Official MCP protocol compliance using `mcp[cli]` package  
- **Environment**: Uses uv for package management
- **Features**: Similar to pixi version but with uv-based server parameters

### **`test_blender_mcp_direct.py`**
- **Purpose**: Test direct TCP socket connection and FastMCP tool imports
- **Approach**: Two testing methods:
  1. Direct TCP socket communication with BlenderAutoMCP (port 9876)
  2. Direct tool import from FastMCP-based blender-mcp server
- **Features**:
  - Socket-based JSON protocol testing
  - Direct function call testing
  - Integration status checking

### **`test_blender_mcp_programmatic.py`**
- **Purpose**: Test HTTP-based programmatic interaction (deprecated approach)
- **Approach**: Subprocess and HTTP requests using uvicorn
- **Status**: Limited success due to FastMCP compatibility issues
- **Note**: Kept for reference, not recommended for new development

## Usage

### Quick Testing Commands

```bash
# Test recommended MCP CLI approach (pixi)
pixi run python tests/mcp-cli-tools/test_mcp_cli_client_pixi.py

# Test MCP CLI approach (uv)
uv run python tests/mcp-cli-tools/test_mcp_cli_client.py

# Test direct TCP and tool import approaches
pixi run python tests/mcp-cli-tools/test_blender_mcp_direct.py

# Test programmatic HTTP approach (limited success)
pixi run python tests/mcp-cli-tools/test_blender_mcp_programmatic.py
```

### Prerequisites

1. **Blender with MCP services running**:
   ```bash
   # Check if services are running
   netstat -tlnp | grep -E "(9876|6688)"
   
   # Should show:
   # BlenderAutoMCP on port 9876
   # BLD Remote MCP on port 6688
   ```

2. **Dependencies available**:
   ```bash
   # MCP CLI tools
   pixi list | grep mcp  # Should show: mcp 1.10.1
   
   # Additional dependencies
   pixi list | grep -E "(requests|uvicorn|fastmcp)"
   ```

### Expected Test Results

**Successful MCP CLI Test**:
- ✅ Session initialization
- ✅ Tool discovery (17 tools for blender-mcp)
- ✅ Scene information retrieval
- ✅ Code execution in Blender
- ✅ Screenshot capture (if in GUI mode)

**Successful Direct TCP Test**:
- ✅ BlenderAutoMCP connection (port 9876)
- ✅ BLD Remote MCP connection (port 6688)
- ✅ JSON protocol communication
- ✅ Tool function execution

## Test Categories

### 1. **Official Protocol Tests**
- `test_mcp_cli_client_pixi.py` (recommended)
- `test_mcp_cli_client.py`

**Purpose**: Validate official MCP protocol compliance and SDK functionality.

### 2. **Low-Level Protocol Tests**
- `test_blender_mcp_direct.py`

**Purpose**: Test direct TCP communication and FastMCP tool imports.

### 3. **Legacy/Reference Tests**
- `test_blender_mcp_programmatic.py`

**Purpose**: HTTP-based approach reference (limited success).

## Integration with Project

These tests validate the MCP interaction patterns documented in:
- `/context/hints/howto-call-mcp-server-via-python.md`
- `/.magic-context/mcp-dev/howto-call-mcp-servers-programmatically.md`

They serve as:
- **Reference implementations** for MCP client patterns
- **Validation tools** for our MCP server implementations  
- **Development aids** for debugging MCP integration issues
- **Documentation examples** for proper MCP usage

## Troubleshooting

### Common Issues

1. **"Connection Refused"**: 
   - Ensure Blender is running with MCP addons enabled
   - Check ports with `netstat -tlnp | grep -E "(9876|6688)"`

2. **"Module not found 'mcp'"**:
   - Install MCP CLI tools: `pixi add "mcp[cli]"`
   - Use pixi environment: `pixi run python script.py`

3. **"FastMCP object is not callable"**:
   - Known limitation with HTTP approach
   - Use MCP CLI tools instead

4. **Timeout errors**:
   - Server may be overloaded
   - Check Blender console for errors
   - Restart Blender if needed

### Debug Commands

```bash
# Check Blender process
ps aux | grep blender | grep -v grep

# Check MCP services
netstat -tlnp | grep -E "(9876|6688)"

# Test basic connectivity
telnet localhost 9876
telnet localhost 6688
```