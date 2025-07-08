# Test Instructions for BLD_Remote_MCP vs BlenderAutoMCP

## Quick Start

### Step 1: Start Both Services
```bash
# Run this in your terminal (not via the bash tool)
./start_dual_services.sh
```

### Step 2: Verify Services Are Running
```bash
# Use pixi to check if both services are responding
pixi run python simple_test.py
```

Expected output:
```
Port 6688 (BLD_Remote_MCP): CONNECTED
Port 9876 (BlenderAutoMCP): CONNECTED
At least one service is running!
```

### Step 3: Run All Tests
```bash
# Run comprehensive test suite
./run_tests_with_pixi.sh
```

## Individual Test Commands (using pixi)

### Basic Comparison Test
```bash
# Tests that both services handle identical commands
pixi run python run_comparison_test.py
```

### Detailed Protocol Analysis
```bash
# Examines response formats and error handling
pixi run python detailed_comparison_test.py
```

### Protocol Compatibility Test
```bash
# Tests different message formats
pixi run python protocol_comparison_test.py
```

### Manual Testing Example
```bash
# Simple manual test example
pixi run python tests/manual_test_example.py
```

### Comprehensive Test Suite
```bash
# Run pytest-based test suite (when services are running)
pixi run python tests/smoke_test.py

# Or run the full test runner
pixi run python tests/run_dual_service_tests.py --quick
```

## What to Look For

### ✅ Success Indicators
- Both services respond to identical commands
- Response formats are compatible
- Error handling is consistent
- No functional differences detected

### ❌ Potential Issues
- Port connection failures
- Response format differences
- Performance regressions
- Service startup problems

## Troubleshooting

### Services Not Starting
1. Check if Blender path is correct: `/apps/blender-4.4.3-linux-x64/blender`
2. Verify addons are installed:
   - BLD_Remote_MCP: `~/.config/blender/4.4/scripts/addons/bld_remote_mcp/`
   - BlenderAutoMCP: Should auto-load in Blender
3. Check logs: `tail -f /tmp/blender_dual_output.log`

### Port Conflicts
```bash
# Check what's using the ports
netstat -tlnp | grep -E "(6688|9876)"

# Kill conflicting processes
pkill -f blender
```

### Context Errors
The logs show modal operator context errors, but the fallback mode should handle this. Services should still function via the TCP protocol.

## Expected Test Results

When both services are working correctly, you should see:
- All basic comparison tests PASS (8/8 tests)
- Both services handle Python execution identically
- Blender API access works on both services
- Error handling is graceful and consistent

The key finding should be: **"BLD_Remote_MCP functions identically to BlenderAutoMCP!"**