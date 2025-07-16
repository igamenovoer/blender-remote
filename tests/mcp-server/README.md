# MCP Server Drop-in Replacement Test Suite

This directory contains tests for validating that our MCP server (`uvx blender-remote` + `BLD_Remote_MCP`) serves as a drop-in replacement for the reference implementation (`uvx blender-mcp` + `BlenderAutoMCP`).

## Test Files

### Core Drop-in Replacement Tests

#### `test_functional_equivalence.py` ⭐
**Purpose**: Validate functional equivalence of shared methods between our stack and the reference stack.

**Tests**:
- `get_scene_info` - Scene and object information retrieval
- `get_object_info` - Detailed object information
- `execute_code` - Python code execution in Blender
- `get_viewport_screenshot` - Viewport image capture (GUI mode)

**Success Criteria**: Same inputs produce functionally equivalent outputs for all shared methods.

#### `test_synchronous_execution.py` ⭐
**Purpose**: Validate that MCP server executes custom Blender code and returns structured results synchronously.

**Tests**:
- Object creation with vertex coordinate extraction
- Material creation with property extraction  
- Animation data and transform calculations
- Complex geometry operations with mathematical analysis

**Success Criteria**: Returns custom, structured JSON data immediately (not just "executed successfully").

#### `test_base64_complex_code.py` ⭐
**Purpose**: Validate base64 encoding for complex code formatting and large data transmission.

**Tests**:
- Complex code with special characters, quotes, newlines
- Large result data (100KB+ responses with vertex/coordinate data)
- Backward compatibility with non-base64 operations
- Performance comparison between base64 and standard transmission

**Success Criteria**: Complex code executes without formatting issues, large data transmits reliably.

#### `test_service_validation.py`
**Purpose**: Basic TCP service availability and health checking.

**Tests**:
- Connection to BLD_Remote_MCP service on port 6688
- Basic command execution validation
- Service health check with Blender info extraction
- Multiple port scanning for service discovery

**Success Criteria**: Service responds correctly to basic validation commands.

### Legacy Test Files (Preserved)

These files were kept from the previous test structure and may provide additional validation:

- `test_mcp_server.py` - Basic MCP server functionality validation
- `test_fastmcp_server.py` - FastMCP server implementation testing
- `test_base64_screenshot.py` - Base64 screenshot encoding validation
- `test_viewport_screenshot.py` - Viewport screenshot capture testing
- `test_background_screenshot.py` - Background mode screenshot limitation testing
- `test_numpy_execution.py` - NumPy code execution validation
- `test_scoping_issue.py` - Python scoping behavior testing
- `test_original_failing_code.py` - Original user code validation
- `run_mcp_server.py` - Development server runner

## Running Tests

### Prerequisites
- Blender running with BLD_Remote_MCP addon enabled
- Service listening on port 6688
- MCP dependencies installed: `pixi add mcp`

### Quick Start
```bash
# From project root directory

# Run core drop-in replacement tests
pixi run python tests/mcp-server/test_service_validation.py
pixi run python tests/mcp-server/test_functional_equivalence.py
pixi run python tests/mcp-server/test_synchronous_execution.py
pixi run python tests/mcp-server/test_base64_complex_code.py
```

### Individual Tests
```bash
# Service validation (run first)
pixi run python tests/mcp-server/test_service_validation.py

# Functional equivalence validation
pixi run python tests/mcp-server/test_functional_equivalence.py

# Synchronous execution with custom results
pixi run python tests/mcp-server/test_synchronous_execution.py

# Base64 complex code transmission
pixi run python tests/mcp-server/test_base64_complex_code.py

# Legacy tests
pixi run python tests/mcp-server/test_mcp_server.py
pixi run python tests/mcp-server/test_fastmcp_server.py
```

### Interactive Testing
```bash
# MCP Inspector for interactive validation
pixi run mcp dev src/blender_remote/mcp_server.py
# Then open http://localhost:3000 and test methods manually
```

## Test Categories

### Integration Tests
Tests that require a running Blender instance with BLD_Remote_MCP addon:
- `test_functional_equivalence.py`
- `test_synchronous_execution.py`
- `test_base64_complex_code.py`
- `test_service_validation.py`

### Unit Tests
Tests that can run independently or with minimal setup:
- `test_mcp_server.py` (import and basic validation)

### GUI Mode Tests
Tests that require Blender in GUI mode (not background):
- `test_viewport_screenshot.py`
- `test_base64_screenshot.py`

### Background Mode Tests
Tests that work in both GUI and background mode:
- `test_functional_equivalence.py`
- `test_synchronous_execution.py`
- `test_base64_complex_code.py`

## Expected Results

### Functional Equivalence
- All shared methods return structurally equivalent data
- Same error handling behavior as reference implementation
- Compatible parameter structure and validation

### Synchronous Execution
- Immediate return of custom structured results
- JSON-formatted data with:
  - Object creation details (names, counts, properties)
  - Vertex/coordinate data with mathematical calculations
  - Material properties and shader parameters
  - Animation keyframe and transformation data

### Base64 Transmission
- Complex code with special characters executes successfully
- Large vertex data (490+ vertices) transmits without truncation
- Backward compatibility maintained for non-base64 operations
- Performance acceptable for localhost usage

### Service Validation
- Connection established on port 6688
- Basic commands execute successfully
- Health check returns Blender version and scene information
- Multiple connection attempts succeed consistently

## Troubleshooting

### Service Not Responding
1. Check if Blender is running: `ps aux | grep blender`
2. Verify addon is enabled: Edit → Preferences → Add-ons → "BLD Remote MCP"
3. Check port availability: `netstat -tlnp | grep 6688`
4. Restart Blender and retry

### MCP Dependencies Missing
```bash
# Install MCP CLI tools
pixi add mcp

# Verify installation
pixi run mcp --version
```

### Test Failures
1. **Functional Equivalence**: Compare outputs with reference implementation
2. **Synchronous Execution**: Check for JSON formatting in results
3. **Base64 Transmission**: Verify large data isn't being truncated
4. **Service Validation**: Ensure basic connectivity works first

### Background vs GUI Mode
- Screenshots only work in GUI mode (expected limitation)
- All other functionality should work in both modes
- Use `blender-remote-cli start` for GUI mode
- Use `blender-remote-cli start --background` for background mode

## Success Criteria Summary

### Overall Drop-in Replacement Validation
✅ **Functional Equivalence**: Same inputs → same functional outputs
✅ **Synchronous Execution**: Custom code → structured results immediately  
✅ **Base64 Transmission**: Complex code + large data → reliable transmission
✅ **Service Availability**: Basic connectivity + health monitoring

### Key Performance Indicators
- **Method Availability**: All shared methods accessible via MCP
- **Input Compatibility**: Same parameter structure accepted
- **Output Equivalence**: Functionally equivalent results returned
- **Custom Results**: Structured data from Blender code execution
- **Large Data**: 100KB+ responses handled correctly via base64

## Based on Test Plan
This test suite implements: `context/plans/mcp-server-comprehensive-test-plan.md`

The test plan provides detailed specifications for:
- Cross-platform testing procedures (Windows, Linux, macOS)
- Expected result structures and validation criteria
- Performance benchmarks and success thresholds
- Troubleshooting guides and fallback procedures