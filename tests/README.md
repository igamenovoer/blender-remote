# blender-remote Test Suite

This directory contains comprehensive tests for the blender-remote project, organized according to the test plans in `context/plans/`.

## Test Directory Structure

### `mcp-server/` - MCP Server Drop-in Replacement Tests
Tests that validate our MCP server (`uvx blender-remote` + `BLD_Remote_MCP`) serves as a drop-in replacement for the reference implementation (`uvx blender-mcp` + `BlenderAutoMCP`).

**Key Test Files:**
- `test_functional_equivalence.py` - Compare shared methods between our stack and reference stack
- `test_synchronous_execution.py` - Real-world Blender automation with custom structured results
- `test_base64_complex_code.py` - Base64 encoding for complex code and large data transmission
- `test_service_validation.py` - Basic TCP service availability and health checks

**Based on:** `context/plans/mcp-server-comprehensive-test-plan.md`

### `client-api/` - Blender Remote Client API Tests
Tests for the Python client API classes (`BlenderMCPClient` and `BlenderSceneManager`) that communicate directly with the `BLD_Remote_MCP` addon.

**Key Test Files:**
- `test_corrected_issues_investigation.py` - **Priority I/O handling focused tests**
- `test_client_connection.py` - Connection management (renamed from `test_basic_connection.py`)
- `test_client_commands.py` - Command execution functionality
- `test_client_scene_info.py` - Scene information retrieval
- `test_scene_manager_objects.py` - Object creation/manipulation (renamed from `test_scene_operations.py`)
- `test_scene_manager_export.py` - GLB export functionality (renamed from `test_asset_operations.py`)
- `test_integration_mcp.py` - Integration tests (renamed from `test_integration.py`)
- `test_error_handling.py` - Error scenarios and edge cases

**Based on:** `context/plans/blender-remote-client-test-plan.md`

## Test Focus Areas

### MCP Server Tests Priority
1. **Functional Equivalence** - Drop-in replacement validation
2. **Synchronous Execution** - Custom structured results from Blender code
3. **Base64 Transmission** - Complex code and large data handling
4. **Service Validation** - Basic connectivity and health

### Client API Tests Priority
1. **I/O Handling Correctness** ⭐ - Parameter validation, response parsing, data transmission
2. **Core Client Functionality** - Connection, commands, scene info
3. **Scene Manager Operations** - Object manipulation, export capabilities
4. **Error Handling** - Network issues, invalid parameters, API errors

## Running Tests

### Prerequisites
- Blender 4.4.3+ running with `BLD_Remote_MCP` addon installed and enabled
- Service listening on port 6688 (or configured port)
- Python environment with blender-remote package installed

### Quick Start
```bash
# From project root directory

# Run MCP server tests
pixi run python tests/mcp-server/test_functional_equivalence.py
pixi run python tests/mcp-server/test_synchronous_execution.py
pixi run python tests/mcp-server/test_base64_complex_code.py
pixi run python tests/mcp-server/test_service_validation.py

# Run client API tests (priority first)
pixi run python tests/client-api/test_corrected_issues_investigation.py
pixi run python tests/client-api/test_client_connection.py
pixi run python tests/client-api/test_client_commands.py
pixi run python tests/client-api/test_error_handling.py
```

### Individual Test Categories
```bash
# MCP Server drop-in replacement validation
cd tests/mcp-server && pixi run python test_functional_equivalence.py

# Client API I/O handling correctness (priority)
cd tests/client-api && pixi run python test_corrected_issues_investigation.py

# Error handling and edge cases
cd tests/client-api && pixi run python test_error_handling.py
```

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
pixi run python tests/mcp-server/test_service_validation.py
```

## Test Results Interpretation

### Success Criteria
- **MCP Server Tests**: All shared methods return functionally equivalent results
- **Client API Tests**: 90%+ success rate for I/O handling correctness
- **Error Handling**: Proper exception handling and graceful degradation
- **Integration Tests**: Full workflow validation

### Expected Performance
- **BlenderMCPClient**: 95%+ success rate for core functionality
- **BlenderSceneManager**: 100% success rate for scene operations  
- **Overall System**: 97%+ success rate for production readiness

## Troubleshooting

### Connection Issues
1. Verify Blender is running with BLD_Remote_MCP addon enabled
2. Check port 6688 availability: `netstat -tlnp | grep 6688`
3. Test service validation: `pixi run python tests/mcp-server/test_service_validation.py`

### Import Errors
1. Run tests from project root directory
2. Use `pixi run python` for consistent environment
3. Verify dependencies: `pixi install`

### Service Errors
1. Restart Blender if service becomes unresponsive
2. Check Blender console for BLD_Remote_MCP addon errors
3. Verify addon installation: Edit → Preferences → Add-ons → "BLD Remote MCP"

## Test Plan Updates

Both test suites are regularly updated based on:
- **MCP Server Plan**: `context/plans/mcp-server-comprehensive-test-plan.md`
- **Client API Plan**: `context/plans/blender-remote-client-test-plan.md`

Refer to these plans for detailed test specifications, expected results, and validation criteria.

## Cleanup

The test directory has been cleaned and reorganized as of 2025-07-16:
- **Removed**: Outdated test files and directories not aligned with current test plans
- **Reorganized**: Tests now follow the exact structure specified in test plans
- **Focus**: Priority on I/O correctness and drop-in replacement validation
- **Maintained**: All working tests were preserved and properly categorized