# Bug Fix: CLI Background Mode Not Keeping Alive

## Problem

The `blender-remote-cli start --background` command exits immediately instead of keeping Blender running in the background with the MCP service active.

## Current Behavior

When running:
```bash
blender-remote-cli start --background
```

The process:
1. Starts Blender in background mode
2. Loads the BLD_Remote_MCP addon
3. Starts the MCP service on port 6688
4. Immediately exits with "Blender quit"

## Expected Behavior

The command should:
1. Start Blender in background mode
2. Load the BLD_Remote_MCP addon
3. Start the MCP service on port 6688
4. Keep Blender running until explicitly stopped (Ctrl+C or kill signal)

## Root Cause Analysis

The issue was in the CLI implementation (`src/blender_remote/cli.py`). The original approach tried to keep Blender alive using:
1. A separate asyncio thread with `loop.run_forever()`
2. Service status monitoring to decide when to exit

**Problems with the original approach:**
1. **Wrong event loop management**: Created a separate asyncio loop instead of driving the existing one
2. **Status-based exit logic**: Checked `bld_remote.is_mcp_service_up()` and exited when service wasn't detected
3. **Too long sleep intervals**: Used 1-second sleeps causing delayed responsiveness

## Solution Implementation

**Fixed approach based on `blender-echo-plugin` reference:**
1. **Drive the existing async loop**: Use `async_loop.kick_async_loop()` to process asyncio events
2. **Exception-based exit**: Only exit on exceptions or when async loop indicates completion
3. **Optimal sleep timing**: Use 50ms (0.05 seconds) sleep intervals for responsive processing

**Key changes in `/workspace/code/blender-remote/src/blender_remote/cli.py`:**

```python
# Before: Wrong approach
def run_forever():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_forever()
    except KeyboardInterrupt:
        pass

# After: Correct approach
while _keep_running:
    if async_loop.kick_async_loop():
        # The loop has no more tasks and wants to stop.
        print("Async loop completed, exiting...")
        break
    time.sleep(0.05)  # 50ms sleep to prevent high CPU usage
```

## Testing Results

✅ **Background mode now works correctly:**
1. `blender-remote-cli start --background` keeps Blender running
2. MCP service is accessible on port 6688
3. Service responds to commands correctly
4. Graceful shutdown with SIGTERM/SIGINT works properly

**Test commands:**
```bash
# Start background mode
pixi run blender-remote-cli start --background &

# Test service
pixi run blender-remote-cli status
# Output: ✅ Connected to Blender BLD_Remote_MCP service (port 6688)

# Test direct TCP connection
echo '{"type": "get_scene_info", "params": {}}' | nc -w 5 127.0.0.1 6688
# Output: {"status": "success", "result": {"name": "Scene", "object_count": 3, ...}}

# Graceful shutdown
kill -TERM <blender_pid>
```

## Related Files

- `src/blender_remote/cli.py` - **FIXED**: CLI command implementation
- `blender_addon/bld_remote_mcp/__init__.py` - MCP service lifecycle
- `blender_addon/bld_remote_mcp/async_loop.py` - Asyncio loop management

## Status

✅ **DONE** - Background mode now works properly with correct async loop management.

**Completion Date**: 2025-07-11  
**Implementation**: Complete fix applied to `src/blender_remote/cli.py`  
**Testing**: All functionality verified and working  
**Documentation**: Logged in `context/logs/2025-07-11_cli-background-mode-bug-fix-success.md`

## Key Lessons

1. **Follow proven patterns**: The `blender-echo-plugin` reference provided the correct approach
2. **Don't reinvent event loops**: Drive the existing async loop instead of creating new ones
3. **Exception-based control flow**: Exit on exceptions, not on status checks
4. **Optimal timing**: 50ms sleep intervals provide good responsiveness without high CPU usage