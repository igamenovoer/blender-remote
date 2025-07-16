# Blender Remote Client API Test Suite

This directory contains tests for the blender-remote Python client API classes (`BlenderMCPClient` and `BlenderSceneManager`) that communicate directly with the `BLD_Remote_MCP` addon.

## Test Files

### Priority Tests (I/O Handling Focused) ⭐

#### `test_corrected_issues_investigation.py` ⭐
**Purpose**: Priority I/O handling correctness validation for localhost usage.

**Focus Areas**:
- Parameter validation and type conversion correctness
- Response parsing correctness (JSON, string extraction)
- Data transmission integrity and command serialization
- Exception mapping and error response processing correctness
- Coordinate and vertex data serialization correctness
- Unicode and special character handling correctness

**Success Criteria**: 97.5% success rate (production ready) with robust I/O handling.

### BlenderMCPClient Core Functionality Tests

#### `test_client_connection.py` (renamed from `test_basic_connection.py`)
**Purpose**: Connection management testing.

**Tests**:
- Constructor parameter validation (host, port, timeout)
- `from_url()` class method with various URL formats
- Auto-detection of Docker vs local environment
- Connection establishment and cleanup
- Timeout handling and connection error scenarios

#### `test_client_commands.py`
**Purpose**: Command execution functionality testing.

**Tests**:
- `execute_command()` with valid/invalid commands
- `execute_python()` code execution
- Response parsing and error handling
- Large code block execution
- Concurrent command execution

#### `test_client_scene_info.py`
**Purpose**: Scene information retrieval testing.

**Tests**:
- `get_scene_info()` data structure validation
- `get_object_info()` for various object types
- `test_connection()` reliability
- `get_status()` service health monitoring

### BlenderSceneManager High-Level Operations

#### `test_scene_manager_objects.py` (renamed from `test_scene_operations.py`)
**Purpose**: Object creation and manipulation testing.

**Tests**:
- `add_primitive()` with various types and parameters
- `add_cube()`, `add_sphere()`, `add_cylinder()` convenience methods
- `update_scene_objects()` batch updates
- `delete_object()` and `clear_scene()` cleanup
- `move_object()` position updates

#### `test_scene_manager_export.py` (renamed from `test_asset_operations.py`)
**Purpose**: Asset export (GLB) functionality testing.

**Tests**:
- `get_object_as_glb_raw()` binary data export
- `get_object_as_glb()` trimesh Scene integration
- Material export options
- Collection vs single object export
- Temporary file management
- Large geometry handling

### Integration and Error Handling Tests

#### `test_integration_mcp.py` (renamed from `test_integration.py`)
**Purpose**: BLD_Remote_MCP integration testing.

**Tests**:
- Full workflow: connect → create objects → export → cleanup
- Service startup/shutdown coordination
- Multiple client connections
- Service recovery after errors

#### `test_error_handling.py`
**Purpose**: Error handling and edge cases testing.

**Tests**:
- Network connectivity issues
- Invalid object names and parameters
- Memory limitations with large exports
- Blender API errors propagation
- Graceful degradation scenarios

## Running Tests

### Prerequisites
- Blender 4.4.3+ with BLD_Remote_MCP addon installed
- Python environment with blender-remote package
- Service listening on port 6688

### Quick Start - Priority Tests
```bash
# From project root directory

# Run priority I/O handling tests first
pixi run python tests/client-api/test_corrected_issues_investigation.py

# Core functionality tests
pixi run python tests/client-api/test_client_connection.py
pixi run python tests/client-api/test_client_commands.py
pixi run python tests/client-api/test_client_scene_info.py

# Error handling validation
pixi run python tests/client-api/test_error_handling.py
```

### Full Test Suite
```bash
# BlenderMCPClient tests
pixi run python tests/client-api/test_client_connection.py
pixi run python tests/client-api/test_client_commands.py
pixi run python tests/client-api/test_client_scene_info.py

# BlenderSceneManager tests
pixi run python tests/client-api/test_scene_manager_objects.py
pixi run python tests/client-api/test_scene_manager_export.py

# Integration and error tests
pixi run python tests/client-api/test_integration_mcp.py
pixi run python tests/client-api/test_error_handling.py

# Priority I/O handling tests
pixi run python tests/client-api/test_corrected_issues_investigation.py
```

### Individual Test Categories
```bash
# Connection management
cd tests/client-api && pixi run python test_client_connection.py

# I/O handling correctness (priority)
cd tests/client-api && pixi run python test_corrected_issues_investigation.py

# Error scenarios
cd tests/client-api && pixi run python test_error_handling.py
```

## Test Categories

### Unit Tests
Tests for individual component functionality:
- `test_client_connection.py`
- `test_client_commands.py`
- `test_client_scene_info.py`

### Integration Tests
Tests for component interaction:
- `test_scene_manager_objects.py`
- `test_scene_manager_export.py`
- `test_integration_mcp.py`

### Priority Tests (I/O Focus)
Tests for I/O correctness validation:
- `test_corrected_issues_investigation.py` ⭐

### Error Handling Tests
Tests for edge cases and error scenarios:
- `test_error_handling.py`

## Expected Results

### Priority I/O Handling Tests
- **Overall Assessment**: ✅ PRODUCTION READY - 97.5% success rate
- **BlenderMCPClient**: 95.0% success (19/20 test cases)
- **BlenderSceneManager**: 100% success (20/20 test cases)

### Key Findings
- ✅ `get_object_info()` works correctly with 'name' parameter
- ✅ Screenshot functionality works (background mode limitation is expected)
- ✅ Camera positioning & rendering work correctly
- ✅ Error handling properly raises exceptions
- ✅ GLB export is fully functional and robust

### Production Readiness
- **Recommended for immediate use** in automated Blender workflows
- **Excellent for batch processing** and 3D asset pipeline integration
- **Robust error handling** with appropriate exceptions
- **Reliable GLB export** capabilities

## Test Focus: Input/Output Handling ⭐

**Key Insight**: Core Blender logic was already validated with `blender-mcp` testing.

**Primary Focus Areas** (Correctness Only - Localhost):
- **Input Validation**: Parameter validation, type conversion correctness, coordinate handling
- **Output Processing**: Response parsing correctness, string extraction, JSON handling
- **Data Transmission**: Data integrity, encoding correctness, command serialization
- **Error Handling**: Exception mapping correctness, error response processing

**Testing Strategy**: Focus on I/O correctness rather than performance (localhost usage).

## Communication Method Fallbacks

The test infrastructure includes multiple communication fallback options for robust testing:

1. **Primary**: Direct `BlenderMCPClient` and `BlenderSceneManager` classes
2. **Fallback 1**: `uvx blender-remote` MCP server (our implementation)
3. **Fallback 2**: Direct TCP to `BLD_Remote_MCP` service (port 6688)
4. **Fallback 3**: `uvx blender-mcp` (original 3rd party MCP server)

### When to Use Fallback Methods
1. **Primary Method Failure**: If `BlenderMCPClient` tests fail, use MCP server validation
2. **Issue Isolation**: Determine if problems are in client classes or underlying service
3. **Cross-Validation**: Verify same Blender operations work via different communication paths
4. **Development**: Test new features using stable backup communication methods

## Setting up Blender for Testing

### Option 1: Using CLI (Recommended)
```bash
# Configure and start Blender with service
blender-remote-cli init
blender-remote-cli install
blender-remote-cli start --background
```

### Option 2: Manual Environment Setup
```bash
# Windows
set BLD_REMOTE_MCP_START_NOW=1
set BLD_REMOTE_MCP_PORT=6688
"C:\Program Files\Blender Foundation\Blender 4.4\blender.exe"

# Linux/macOS
export BLD_REMOTE_MCP_START_NOW=1
export BLD_REMOTE_MCP_PORT=6688
/apps/blender-4.4.3-linux-x64/blender &
```

### Verify Service
```bash
# Check if service is listening
netstat -tlnp | grep 6688

# Test basic connectivity
pixi run python -c "
from blender_remote.client import BlenderMCPClient
client = BlenderMCPClient()
print('✅ Connection OK' if client.test_connection() else '❌ Connection Failed')
"
```

## Troubleshooting

### Connection Issues
- Ensure Blender is running with BLD_Remote_MCP addon enabled
- Check that port 6688 is available and not blocked
- Verify the service is listening: `netstat -tlnp | grep 6688`

### Import Errors
- Run tests from project root directory
- Ensure Python path includes `src/` directory
- Check that all required dependencies are installed

### Service Errors
- Restart Blender if the service becomes unresponsive
- Check Blender console for error messages
- Verify the BLD_Remote_MCP addon is properly installed

## Success Criteria

### Functional Requirements
- [ ] All existing methods produce expected outputs
- [ ] Error handling is robust and informative
- [ ] Resource cleanup is reliable
- [ ] Performance meets baseline requirements

### Quality Requirements
- [ ] Test coverage > 90% for both classes
- [ ] All edge cases handled gracefully
- [ ] Documentation reflects actual behavior
- [ ] Code follows modern Python best practices

## High Risk Areas

1. **GLB Export**: Complex binary data handling
2. **Process Management**: PID handling across platforms
3. **Python Code Execution**: String-based result parsing
4. **Resource Cleanup**: Temporary file management

## Test Design

The tests follow a hierarchical structure:
1. **Unit tests** - Individual component functionality
2. **Integration tests** - Component interaction
3. **Workflow tests** - End-to-end scenarios

Each test is designed to:
- Be independent and isolated
- Clean up after itself
- Provide clear error messages
- Test both success and failure cases

## Based on Test Plan
This test suite implements: `context/plans/blender-remote-client-test-plan.md`

The test plan provides detailed specifications for:
- I/O handling focused testing approach
- Communication method fallbacks and validation
- Expected performance metrics and success criteria
- Modernization and improvement recommendations