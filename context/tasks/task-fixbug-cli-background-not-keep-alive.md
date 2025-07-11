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

## Analysis

From the logs, we can see:
- The MCP service is started successfully
- The asyncio loop is set up with modal operator
- But Blender exits immediately after setup

The issue appears to be that in background mode, Blender doesn't have a GUI event loop to keep it running, and the current implementation doesn't provide an alternative keep-alive mechanism.

## Observed Logs

```
[BLD Remote][INFO][14:05:57] Background mode detected - external script should manage keep-alive loop
[BLD Remote][INFO][14:05:57] ✅ Background keep-alive setup completed
```

This suggests the code expects external keep-alive management but doesn't implement it.

## Root Cause

The CLI command starts Blender but doesn't implement a proper keep-alive loop for background mode. The current implementation relies on GUI event loops which don't exist in `--background` mode.

## Proposed Solution

1. **CLI Implementation**: Add a keep-alive loop in the CLI that waits for the Blender process and monitors the MCP service
2. **Blender Addon**: Implement a background-mode compatible keep-alive mechanism
3. **Signal Handling**: Ensure proper cleanup on termination signals

## Workaround

Use `blender-remote-cli start &` (GUI mode in background) instead of `--background` flag until this is fixed.

## Priority

High - This affects the core functionality of background mode operation.

## Related Files

- `src/blender_remote/cli.py` - CLI command implementation
- `blender_addon/bld_remote_mcp/__init__.py` - MCP service lifecycle
- `blender_addon/bld_remote_mcp/async_loop.py` - Asyncio loop management

## Testing

To verify the fix:
1. Run `blender-remote-cli start --background`
2. Verify Blender process stays running
3. Test MCP service connectivity on port 6688
4. Test graceful shutdown with Ctrl+C