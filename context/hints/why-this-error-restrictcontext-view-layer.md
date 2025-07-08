# Understanding and Resolving the `_RestrictContext` Error in Blender

## The Problem: `'_RestrictContext' object has no attribute 'view_layer'`

This error occurs when a Blender script or addon attempts to access parts of the `bpy.context` that are not available in the current execution environment. Specifically, it arises when trying to start a modal operator—which relies on a window manager—in a context where no window is available. This is common in the following scenarios:

- **Headless Mode**: When running Blender from the command line using the `-b` or `--background` flag, no graphical interface is loaded, and therefore `bpy.context.window` and `bpy.context.window_manager` are unavailable.
- **During Startup**: When an addon is being registered, the full UI context may not yet be initialized, leading to the same restrictions.

The function `ensure_async_loop` in `bld_remote_mcp/async_loop.py` is designed to start a modal operator to drive the `asyncio` event loop. When this function is called in a restricted context, it fails with the `_RestrictContext` error because it cannot access the necessary window manager.

## The Solution: A Robust Fallback to `bpy.app.timers`

To ensure that the `asyncio` loop runs reliably in all environments—both with and without a UI—the `ensure_async_loop` function should be updated to include a fallback mechanism. When the modal operator cannot be started, the function should instead register a timer with `bpy.app.timers`. This approach is more robust because `bpy.app.timers` are not dependent on the UI and can run in any context.

Here is the recommended implementation:

```python
def ensure_async_loop():
    """Ensure the asyncio loop is running, starting it if necessary.
    
    This function will first attempt to start a modal operator to drive the
    asyncio loop. If this fails due to a restrictive context (e.g., in
    headless mode), it will fall back to using an app timer.
    """
    log_info("=== ENSURING ASYNC LOOP ===")
    if _loop_kicking_operator_running:
        log_info("Loop-kicking operator is already running.")
        return

    log_info("Attempting to start modal operator for asyncio loop...")
    try:
        # Check for a valid context to run the modal operator
        if bpy.context.window_manager and bpy.context.window:
            bpy.ops.bld_remote.async_loop('INVOKE_DEFAULT')
            log_info("✅ Successfully invoked modal operator.")
            return
        else:
            log_warning("No valid window context, falling back to app timer.")
            raise RuntimeError("No valid window context for modal operator")
    except (RuntimeError, AttributeError) as e:
        log_warning(f"Could not start modal operator: {e}. Falling back to app timer.")
        
        # Fallback for headless or context-restricted environments
        if not bpy.app.timers.is_registered(kick_async_loop):
            # The timer will automatically stop when kick_async_loop returns False
            bpy.app.timers.register(kick_async_loop, first_interval=0.01)
            log_info("✅ Registered app timer for asyncio loop.")
        else:
            log_info("App timer for asyncio loop is already registered.")
```

### How It Works

1. **Context Check**: The function first checks if a valid window context is available.
2. **Modal Operator**: If a window is present, it attempts to start the modal operator as before.
3. **Fallback to Timer**: If the context is restricted, it catches the resulting `RuntimeError` or `AttributeError` and falls back to using `bpy.app.timers.register()`.
4. **Reliable Execution**: This ensures that `kick_async_loop` is called periodically, allowing `asyncio` tasks to execute even in headless mode.

By implementing this change, the `blender-remote` addon will be more robust and versatile, supporting both interactive UI sessions and automated background processes.
