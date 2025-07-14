# How to Properly Keep Blender Alive and Process Events in Background Mode

## The Problem: Timers and Other Events Failing to Execute

When running Blender in background mode, a common issue is that `bpy.app.timers` and other scheduled events fail to run, often leading to timeouts. This happens when using a simple `while...sleep` loop to keep the Blender process alive.

The root cause is a concurrency conflict:

1.  **Main Thread Monopoly:** A `while True: time.sleep(x)` loop in your main script takes complete control of Blender's main thread.
2.  **Event Starvation:** While `time.sleep()` pauses the thread, it does **not** yield control to Blender's internal event-processing system.
3.  **The Deadlock:** Blender's event queue, which holds tasks scheduled by `bpy.app.timers`, never gets processed because the main thread is stuck in the sleep loop. The scheduled tasks are never executed.

This leads to a deadlock where a worker thread might be waiting for a result from a timer that can never run.

## The Solution: Use a Modal Operator

The correct, idiomatic way to keep Blender alive while allowing its event system to function is to use a **modal operator**. A modal operator hands control over to Blender's native event loop, ensuring that timers, async tasks, and other events are processed correctly.

### Implementation Steps

Here is how to modify `src/blender_remote/cli.py` to use a modal operator instead of the `while...sleep` loop.

#### 1. Define the Modal Operator

Create a class for the modal operator. This operator's only job is to run continuously, keeping Blender alive.

```python
import bpy
import time

class BackgroundKeeperOperator(bpy.types.Operator):
    """
    A simple modal operator that keeps Blender running in the background
    and allows the event loop to process timers and other events.
    """
    bl_idname = "wm.background_keeper"
    bl_label = "Background Process Keeper"

    _timer = None
    _keep_running = True

    def modal(self, context, event):
        # The 'ESC' key event is a conventional way to stop modal operators,
        # but in background mode, we rely on signal handlers.
        if event.type == 'ESC' or not self._keep_running:
            self.cancel(context)
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        # Add a timer to keep the event loop responsive.
        self._timer = context.window_manager.event_timer_add(0.5, window=context.window)
        context.window_manager.modal_handler_add(self)
        print("✅ Background modal operator started. Blender is now alive and responsive.")
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)
        print("Background modal operator stopped.")

    @classmethod
    def shutdown(cls):
        """Class method to signal the operator to stop."""
        cls._keep_running = False
```

#### 2. Modify the Keep-Alive Section in `src/blender_remote/cli.py`

In the `start` command function within `src/blender_remote/cli.py`, replace the entire `while _keep_running:` block with the registration and invocation of this new modal operator.

```python
# In src/blender_remote/cli.py, inside the 'start' function's background block...

    # In background mode, add proper keep-alive mechanism
    if background:
        # NOTE: The existing 'while...sleep' loop is replaced by this new code.
        startup_code.append(
            '''
# --- Proper Keep-Alive using a Modal Operator ---
import bpy
import time
import signal
import sys

# Define the Modal Operator to keep Blender alive and responsive
class BackgroundKeeperOperator(bpy.types.Operator):
    bl_idname = "wm.background_keeper"
    bl_label = "Background Process Keeper"

    _timer = None
    _keep_running = True

    def modal(self, context, event):
        if not self.__class__._keep_running:
            self.cancel(context)
            return {'CANCELLED'}
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        self._timer = context.window_manager.event_timer_add(0.5, window=context.window)
        context.window_manager.modal_handler_add(self)
        print("✅ Background modal operator started. Blender is now alive and responsive.")
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)
        print("Background modal operator stopped.")
    
    @classmethod
    def shutdown(cls):
        print("Signal received, telling modal operator to shut down...")
        cls._keep_running = False

# Signal handler to gracefully stop the modal operator
def signal_handler(signum, frame):
    print(f"Received signal {signum}, shutting down...")
    BackgroundKeeperOperator.shutdown()
    
    # Try to gracefully shutdown the MCP service
    try:
        import bld_remote
        if bld_remote.is_mcp_service_up():
            bld_remote.stop_mcp_service()
            print("MCP service stopped")
    except Exception as e:
        print(f"Error stopping MCP service: {e}")

    # Give it a moment to process the shutdown
    time.sleep(1.0)
    sys.exit(0)

# Install signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

print("Blender running in background mode. Press Ctrl+C to exit.")

# Register the operator and run it
try:
    bpy.utils.register_class(BackgroundKeeperOperator)
    # Invoke the modal operator to start the event loop
    bpy.ops.wm.background_keeper('INVOKE_DEFAULT')

except Exception as e:
    print(f"Error starting background keeper: {e}")
'''
        )
```

### Why This Works

*   **Hands Control to Blender:** Calling `bpy.ops.wm.background_keeper('INVOKE_DEFAULT')` starts the operator and gives control of the main thread back to Blender's internal event loop.
*   **Event Processing:** Because Blender's native event loop is running, it can now properly check its event queue and execute any timers scheduled by `bpy.app.timers.register()`.
*   **Responsiveness:** The modal operator keeps Blender from exiting while allowing all other scheduled background tasks to run as intended, fixing the timeout issue.
*   **Graceful Shutdown:** The `signal_handler` now communicates with the operator via a class variable (`_keep_running`) to ensure a clean exit.

This is the standard and most robust pattern for running Blender headless while needing to process events.

### Official Documentation References

For more details on the concepts used in this solution, refer to the official Blender Python API documentation:

*   **`bpy.types.Operator`**: The base class for creating operators, including the `modal()` and `invoke()` methods essential for this pattern.
    *   Reference: `context/refcode/blender_python_reference_4_4/bpy.types.Operator.html`
*   **`bpy.types.WindowManager`**: Contains the methods for managing timers and modal handlers (`event_timer_add`, `modal_handler_add`).
    *   Reference: `context/refcode/blender_python_reference_4_4/bpy.types.WindowManager.html`
*   **`bpy.app.timers`**: The module for scheduling functions to run in the future, which the modal operator pattern enables.
    *   Reference: `context/refcode/blender_python_reference_4_4/bpy.app.timers.html`

## Clarification: Why This Doesn't Cause a Deadlock

It might seem that having the network thread wait for a timer to complete while the main thread (managed by the modal operator) is also in a loop would cause a deadlock. However, this is not the case due to the clear separation of roles between the threads.

### The Two-Thread System Explained

1.  **The Network Thread (Worker):**
    *   This thread is created by the `socketserver` to handle a single client connection. Its job is to receive a command and send a response.
    *   It calls `_execute_command_sync`, which schedules the task for the main thread and then **waits** in a polling loop (`while not result_container["done"]...`).
    *   Crucially, this **only blocks the network thread**. It does not block Blender's main thread. This is perfectly acceptable as this thread's only purpose is to serve one client's request.

2.  **Blender's Main Thread (Executor):**
    *   This is the only thread that can safely run `bpy` commands.
    *   The modal operator ensures this thread is continuously running Blender's native event loop.
    *   When `bpy.app.timers.register()` is called from the network thread, the task is placed into the main thread's event queue.
    *   Because the modal operator is active, the main thread is free to see this new task, execute it, and update the shared `result_container`.

### The Restaurant Analogy

*   **Network Thread = A Waiter.** The waiter takes an order (the command), places it on the kitchen's order queue, and then **waits** for the food to be prepared. The waiter is "blocked," but the kitchen can still operate.
*   **Main Thread = The Chef.** The chef is continuously working, checking the order queue. The chef sees the order, prepares the food (executes the command), and puts the finished dish on the counter (updates the `result_container`).
*   **Modal Operator = The Kitchen Manager.** The manager ensures the chef is always working and checking for new orders, keeping the kitchen (the event loop) running smoothly.

The system works because the thread that is **waiting** (the network thread) is separate from the thread that is **doing the work** (the main thread). The original `while...sleep` loop failed because it was like the kitchen manager forcing the chef to take a nap every few seconds, preventing them from ever checking the order queue.
