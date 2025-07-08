# Tests

This directory contains the comprehensive test suite for the blender-remote project, with specialized dual-service comparison tests for BLD_Remote_MCP vs BlenderAutoMCP.

## Purpose

Tests ensure:
- **BLD_Remote_MCP functions identically to BlenderAutoMCP** (primary focus)
- Remote control library functions correctly
- Communication protocols work as expected
- CLI tools behave properly
- Add-ons integrate correctly with Blender
- Error handling works in various scenarios
- Performance characteristics are acceptable

## Structure

```
tests/
├── integration/                           # Integration and comparison tests
│   ├── test_dual_service_comparison.py   # Functional equivalence tests
│   └── test_performance_comparison.py    # Performance comparison tests
├── test_bld_remote_mcp.py                # Unit tests for our MCP service
├── run_dual_service_tests.py             # Comprehensive test runner
├── smoke_test.py                          # Quick verification script
└── conftest.py                           # pytest configuration and fixtures
```

## Quick Start

### Smoke Test (30 seconds)
```bash
# Quick verification that both services work
./tests/smoke_test.py
```

### Full Comparison Suite (5-10 minutes)
```bash
# Run complete comparison between BLD_Remote_MCP and BlenderAutoMCP
./tests/run_dual_service_tests.py

# Quick tests only (skip performance tests)
./tests/run_dual_service_tests.py --quick

# Performance tests only
./tests/run_dual_service_tests.py --performance
```

### Individual Test Categories
```bash
# Unit tests (our service only)
./tests/run_dual_service_tests.py --unit

# Integration tests (dual service comparison)
./tests/run_dual_service_tests.py --integration

# Verbose output
./tests/run_dual_service_tests.py --verbose
```

## Test Categories

### 1. Dual Service Comparison Tests
**File**: `integration/test_dual_service_comparison.py`
- Tests functional equivalence between BLD_Remote_MCP and BlenderAutoMCP
- Both services run simultaneously in GUI mode
- Identical commands sent to both services
- Responses compared for consistency
- **Key Tests**:
  - Basic connectivity
  - Python code execution
  - Blender API access
  - Scene object manipulation
  - Error handling consistency
  - Large code block execution

### 2. Performance Comparison Tests  
**File**: `integration/test_performance_comparison.py`
- Measures execution time for identical operations
- Ensures BLD_Remote_MCP performance is within acceptable range (≤2x slower)
- **Performance Tests**:
  - Simple command latency
  - Blender API call performance
  - Object creation speed
  - Large code execution time
  - Connection overhead

### 3. BLD_Remote_MCP Unit Tests
**File**: `test_bld_remote_mcp.py`
- Tests specific functionality of our service implementation
- **Unit Tests**:
  - Service startup and connectivity
  - Python execution capabilities
  - Blender API integration
  - Scene manipulation
  - Error handling robustness
  - Memory management
  - Concurrent connections

## Prerequisites

- **Blender 4.4.3** installed at `/apps/blender-4.4.3-linux-x64/blender`
- **BLD_Remote_MCP addon** installed at `~/.config/blender/4.4/scripts/addons/bld_remote_mcp/`
- **BlenderAutoMCP** reference service (should auto-load in Blender)
- **Python packages**: `pytest`, `auto_mcp_remote` client modules

## Test Environment

### Service Configuration
- **BLD_Remote_MCP**: Port 6688 (configurable via `BLD_REMOTE_MCP_PORT`)
- **BlenderAutoMCP**: Port 9876 (reference implementation)
- **Test Mode**: GUI mode with both services running simultaneously

### Environment Variables
```bash
export BLD_REMOTE_MCP_PORT=6688
export BLD_REMOTE_MCP_START_NOW=1
export BLENDER_AUTO_MCP_SERVICE_PORT=9876
export BLENDER_AUTO_MCP_START_NOW=1
```

## Running Individual Tests

```bash
# Run all tests with pytest
pytest

# Specific test files
pytest tests/test_bld_remote_mcp.py
pytest tests/integration/test_dual_service_comparison.py  
pytest tests/integration/test_performance_comparison.py

# With coverage
pytest --cov=blender_remote tests/

# Exclude slow tests
pytest -m "not slow"

# Only dual-service tests
pytest -m "dual_service"
```

## Test Results Interpretation

### ✅ Success Criteria
- All dual-service comparison tests pass
- Performance within 2x of BlenderAutoMCP
- No functional differences detected
- Error handling behaves consistently

### ❌ Failure Indicators
- Response differences between services
- Performance regressions >2x slower
- Service startup failures
- Inconsistent error handling

## Troubleshooting

### Common Issues
1. **Port conflicts**: Services fail to start
   - Solution: Kill existing Blender processes: `pkill -f blender`

2. **Service startup timeout**: Services don't respond within timeout
   - Solution: Increase timeout or check addon installation

3. **Import errors**: `auto_mcp_remote` not found
   - Solution: Verify `context/refcode/auto_mcp_remote/` exists

4. **Test failures**: Functional differences detected
   - Solution: Review test output and compare service logs

### Debug Mode
```bash
# Run with maximum verbosity
./tests/run_dual_service_tests.py --verbose

# Check service logs during test
tail -f /tmp/blender_dual_services.log
```

## Development Workflow

1. **Make changes** to BLD_Remote_MCP
2. **Run smoke test** for quick verification: `./tests/smoke_test.py`
3. **Run full suite** for comprehensive validation: `./tests/run_dual_service_tests.py`
4. **Check performance** if needed: `./tests/run_dual_service_tests.py --performance`

## Testing Challenges

Testing Blender MCP services requires special consideration:
- **Dual service coordination**: Both services must start successfully
- **GUI mode requirement**: BlenderAutoMCP only works in GUI mode
- **Service startup timing**: Services need time to initialize
- **Process cleanup**: Blender processes must be killed between tests
- **Port management**: Avoid conflicts between test runs