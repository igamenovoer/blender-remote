# Python Control API Tests

This directory contains tests for the Python Control API implementation for blender-remote.

## Test Files

### `test_basic_connection.py`
Tests basic connection functionality:
- Connection to BLD Remote MCP service
- Service status checking
- Basic scene information retrieval
- Python code execution

### `test_scene_operations.py`
Tests scene management operations:
- Scene manager creation
- Object listing and filtering
- Primitive object creation (cubes, spheres, cylinders)
- Object manipulation (move, delete)
- Batch object updates
- Scene data types and attrs functionality

### `test_asset_operations.py`
Tests asset management operations:
- Asset manager creation
- Asset library listing and validation
- Collection browsing and search
- Blend file enumeration
- Asset data types functionality

### `test_integration.py`
Comprehensive integration tests:
- Complete workflow testing
- Error handling verification
- Data type functionality
- Convenience function testing
- API import verification

## Prerequisites

Before running these tests, ensure:

1. **Blender is running** with the BLD Remote MCP service active on port 6688
2. **Python environment** has the required dependencies installed
3. **Working directory** is the project root

## Running the Tests

### Individual Test Files
```bash
# From project root directory
python tests/python_control_api/test_basic_connection.py
python tests/python_control_api/test_scene_operations.py
python tests/python_control_api/test_asset_operations.py
python tests/python_control_api/test_integration.py
```

### All Tests
```bash
# Run all tests in sequence
for test in tests/python_control_api/test_*.py; do
    echo "Running $test..."
    python "$test"
    echo "---"
done
```

## Setting up Blender for Testing

1. **Start Blender** with BLD Remote MCP service:
   ```bash
   export BLD_REMOTE_MCP_PORT=6688
   export BLD_REMOTE_MCP_START_NOW=1
   /apps/blender-4.4.3-linux-x64/blender &
   ```

2. **Wait for service** to start (usually ~10 seconds)

3. **Verify service** is running:
   ```bash
   netstat -tlnp | grep 6688
   ```

## Test Output

Each test file provides detailed output including:
- Test progress and results
- Object creation and manipulation details
- Error messages and stack traces (if any)
- Final pass/fail summary

Example output:
```
============================================================
BLD Remote MCP Python Control API Integration Tests
============================================================

Testing API imports...
✓ Main classes imported
✓ Data types imported
✓ Exceptions imported
✓ Convenience functions imported
✓ test_api_imports PASSED

Testing convenience functions...
Connected via convenience function: localhost:6688
Created scene manager: localhost:6688
Created asset manager: localhost:6688
Created scene manager with existing client: localhost:6688
✓ test_convenience_functions PASSED

... (more test output)

============================================================
Integration Test Results: 5/5 tests passed
============================================================
🎉 All integration tests passed! Python Control API is working correctly.
```

## Troubleshooting

### Connection Issues
- Ensure Blender is running with BLD Remote MCP service
- Check that port 6688 is available and not blocked
- Verify the service is listening: `netstat -tlnp | grep 6688`

### Import Errors
- Run tests from project root directory
- Ensure Python path includes `src/` directory
- Check that all required dependencies are installed

### Service Errors
- Restart Blender if the service becomes unresponsive
- Check Blender console for error messages
- Verify the BLD Remote MCP addon is properly installed

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

## Adding New Tests

When adding new tests:
1. Follow the existing naming convention (`test_*.py`)
2. Include proper error handling and cleanup
3. Test both success and failure scenarios
4. Document the test purpose and expected behavior
5. Update this README with new test descriptions