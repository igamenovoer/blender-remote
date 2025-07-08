"""Manages the asyncio loop for background-safe operation.

Based on blender-echo-plugin implementation.
"""

import asyncio
import traceback
import concurrent.futures
import gc
import sys
import bpy
from .utils import log_info, log_warning, log_debug, log_error

# Keeps track of whether a loop-kicking operator is already running.
_loop_kicking_operator_running = False


def setup_asyncio_executor():
    """Sets up AsyncIO to run properly on each platform."""
    log_info("=== SETTING UP ASYNCIO EXECUTOR ===")
    log_info(f"Platform: {sys.platform}")
    
    if sys.platform == "win32":
        log_info("Windows platform detected, using ProactorEventLoop")
        # On Windows, use ProactorEventLoop for proper operation
        try:
            existing_loop = asyncio.get_event_loop()
            log_info(f"Existing event loop: {existing_loop}")
            existing_loop.close()
            log_info("Existing event loop closed")
        except Exception as e:
            log_info(f"No existing event loop to close or error closing: {e}")
        
        log_info("Creating ProactorEventLoop...")
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
        log_info(f"ProactorEventLoop set: {loop}")
    else:
        log_info("Non-Windows platform, using default event loop")
        loop = asyncio.get_event_loop()
        log_info(f"Got event loop: {loop}")

    log_info("Creating ThreadPoolExecutor...")
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
    log_info(f"ThreadPoolExecutor created: {executor}")
    
    log_info("Setting default executor...")
    loop.set_default_executor(executor)
    log_info(f"Default executor set for loop: {loop}")
    log_info("=== ASYNCIO EXECUTOR SETUP COMPLETED ===")


def kick_async_loop(*args) -> bool:
    """Performs a single iteration of the asyncio event loop.

    :return: whether the asyncio loop should stop after this kick.
    """
    # Get loop information
    try:
        loop = asyncio.get_event_loop()
    except Exception as e:
        log_error(f"Failed to get event loop: {e}")
        return True

    # Even when we want to stop, we always need to do one more
    # 'kick' to handle task-done callbacks.
    stop_after_this_kick = False

    if loop.is_closed():
        log_warning("Event loop is closed, stopping immediately")
        return True

    # Passing an explicit loop is required. Without it, the function uses
    # asyncio.get_running_loop(), which raises a RuntimeError as the current
    # loop isn't running.
    try:
        all_tasks = asyncio.all_tasks(loop=loop)
    except Exception as e:
        log_error(f"Failed to get all tasks: {e}")
        return True
    
    # Log task processing details with throttling
    task_count = len(all_tasks)
    
    # Create a counter for this function to throttle logging
    if not hasattr(kick_async_loop, '_call_count'):
        kick_async_loop._call_count = 0
    kick_async_loop._call_count += 1
    
    # Only log detailed info every 10000 calls to avoid spam (significantly reduced verbosity)
    should_log_details = (kick_async_loop._call_count % 10000 == 1) or task_count > 1
    
    # if should_log_details:
    #     log_info(f"kick_async_loop (call #{kick_async_loop._call_count}): {task_count} tasks to process")

    if not task_count:
        if should_log_details:
            log_info("No more scheduled tasks, stopping after this kick")
        stop_after_this_kick = True

    elif all(task.done() for task in all_tasks):
        if should_log_details:
            log_info(f"All {task_count} tasks are done, fetching results and stopping after this kick")
        stop_after_this_kick = True

        # Clean up circular references between tasks.
        gc.collect()

        if should_log_details:
            for task_idx, task in enumerate(all_tasks):
                if not task.done():
                    continue

                try:
                    res = task.result()
                    log_info(f"   task #{task_idx}: result={res!r}")
                except asyncio.CancelledError:
                    # No problem, we want to stop anyway.
                    log_info(f"   task #{task_idx}: cancelled")
                except Exception as task_e:
                    log_error(f"   task #{task_idx}: resulted in exception: {task_e}")
                    log_error(f"   task #{task_idx}: {traceback.format_exc()}")
    else:
        # There are tasks that are not done yet
        # if should_log_details:
        #     log_info(f"Processing {task_count} active tasks...")
        #     for task_idx, task in enumerate(all_tasks):
        #         if task.done():
        #             log_info(f"   task #{task_idx}: done")
        #         else:
        #             log_info(f"   task #{task_idx}: pending - {task}")
        pass

    # Run the loop
    try:
        loop.stop()
        loop.run_forever()
    except Exception as e:
        log_error(f"Error running event loop: {e}")
        return True

    return stop_after_this_kick


def ensure_async_loop():
    """Ensure the asyncio loop is running, starting it if necessary.
    
    This function will first attempt to start a modal operator to drive the
    asyncio loop. If this fails due to a restrictive context (e.g., during
    addon startup or in headless mode), it will fall back to using app timers.
    """
    log_info("=== ENSURING ASYNC LOOP ===")
    log_info("ensure_async_loop() called")
    log_info(f"Current loop kicking operator status: {_loop_kicking_operator_running}")
    
    log_info("Starting modal operator for asyncio loop...")
    try:
        # Check for a valid context to run the modal operator
        if hasattr(bpy.context, 'window_manager') and bpy.context.window_manager and hasattr(bpy.context, 'window') and bpy.context.window:
            result = bpy.ops.bld_remote.async_loop()
            log_info(f"✅ Modal operator started successfully: {result!r}")
        else:
            log_info("No valid window context, falling back to app timer")
            raise RuntimeError("No valid window context for modal operator")
    except (RuntimeError, AttributeError) as e:
        log_warning(f"Could not start modal operator: {e}. Falling back to app timer.")
        
        # Fallback for headless or context-restricted environments
        if not bpy.app.timers.is_registered(kick_async_loop):
            # The timer will automatically stop when kick_async_loop returns False
            bpy.app.timers.register(kick_async_loop, first_interval=0.01)
            log_info("✅ Registered app timer for asyncio loop (fallback mode)")
        else:
            log_info("App timer for asyncio loop is already registered")
        return
    
    # Add extra debugging
    log_info(f"Loop kicking operator running after start: {_loop_kicking_operator_running}")
    
    # Check if there are any scheduled tasks
    log_info("Checking scheduled asyncio tasks...")
    try:
        loop = asyncio.get_event_loop()
        log_info(f"Got event loop: {loop}")
        log_info(f"Loop is closed: {loop.is_closed()}")
        log_info(f"Loop is running: {loop.is_running()}")
        
        all_tasks = asyncio.all_tasks(loop=loop)
        task_count = len(all_tasks)
        log_info(f"Number of scheduled asyncio tasks: {task_count}")
        
        if task_count > 0:
            for i, task in enumerate(all_tasks):
                task_info = f"Task {i}: {task} (done: {task.done()}"
                if task.done():
                    try:
                        if task.cancelled():
                            task_info += ", cancelled"
                        else:
                            task_info += f", result available"
                    except Exception:
                        task_info += ", result error"
                task_info += ")"
                log_info(task_info)
        else:
            log_info("No tasks currently scheduled")
            
    except Exception as e:
        log_error(f"Error checking asyncio tasks: {e}")
        log_error(f"Task check traceback: {traceback.format_exc()}")
    
    log_info("=== ASYNC LOOP ENSURE COMPLETED ===")


def erase_async_loop():
    global _loop_kicking_operator_running

    log_debug("Erasing async loop")

    loop = asyncio.get_event_loop()
    loop.stop()


class BLD_REMOTE_OT_async_loop(bpy.types.Operator):
    bl_idname = "bld_remote.async_loop"
    bl_label = "Runs the asyncio main loop"

    timer = None

    def __del__(self):
        global _loop_kicking_operator_running

        # This can be required when the operator is running while Blender
        # (re)loads a file. The operator then doesn't get the chance to
        # finish the async tasks, hence stop_after_this_kick is never True.
        _loop_kicking_operator_running = False

    def execute(self, context):
        return self.invoke(context, None)

    def invoke(self, context, event):
        global _loop_kicking_operator_running

        log_info("=== MODAL OPERATOR INVOKE ===")
        log_info(f"Modal operator invoke called - context: {context}, event: {event}")
        log_info(f"Current _loop_kicking_operator_running: {_loop_kicking_operator_running}")
        
        if _loop_kicking_operator_running:
            log_info("⚠️ Another loop-kicking operator is already running, passing through")
            return {"PASS_THROUGH"}

        log_info("Starting new modal operator...")
        try:
            context.window_manager.modal_handler_add(self)
            log_info("✅ Modal handler added to window manager")
        except Exception as e:
            log_error(f"ERROR: Failed to add modal handler: {e}")
            return {"CANCELLED"}
        
        _loop_kicking_operator_running = True
        log_info(f"Set _loop_kicking_operator_running to: {_loop_kicking_operator_running}")

        try:
            wm = context.window_manager
            log_info(f"Got window manager: {wm}")
            log_info(f"Current window: {context.window}")
            
            # Use a fast timer for responsive asyncio processing
            timer_interval = 0.00025  # 0.25ms
            self.timer = wm.event_timer_add(timer_interval, window=context.window)
            log_info(f"✅ Modal operator timer added (interval: {timer_interval}s): {self.timer}")
        except Exception as e:
            log_error(f"ERROR: Failed to add timer: {e}")
            _loop_kicking_operator_running = False
            return {"CANCELLED"}
        
        log_info("Modal operator setup complete, returning RUNNING_MODAL")
        log_info("=== MODAL OPERATOR INVOKE COMPLETED ===")
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        global _loop_kicking_operator_running

        # If _loop_kicking_operator_running is set to False, someone called
        # erase_async_loop(). This is a signal that we really should stop
        # running.
        if not _loop_kicking_operator_running:
            log_info("⚠️ _loop_kicking_operator_running is False, finishing modal operator")
            try:
                if hasattr(self, 'timer') and self.timer:
                    context.window_manager.event_timer_remove(self.timer)
                    log_info("Timer removed during early finish")
            except Exception as e:
                log_error(f"Error removing timer during early finish: {e}")
            return {"FINISHED"}

        if event.type != "TIMER":
            return {"PASS_THROUGH"}

        # Initialize and track modal call count
        if not hasattr(self, '_modal_call_count'):
            self._modal_call_count = 0
            log_info("Modal operator processing started")
            
        self._modal_call_count += 1
            
        # Log progress periodically to avoid spam but provide visibility
        should_log = (self._modal_call_count % 1000 == 1) or (self._modal_call_count <= 10)
        if should_log:
            log_info(f"Modal operator processing timer event (call #{self._modal_call_count})")

        # Process asyncio loop
        try:
            stop_after_this_kick = kick_async_loop()
        except Exception as e:
            log_error(f"ERROR: Exception in kick_async_loop: {e}")
            log_error(f"Traceback: {traceback.format_exc()}")
            stop_after_this_kick = True  # Stop on error
            
        if stop_after_this_kick:
            log_info(f"Asyncio loop requested stop after {self._modal_call_count} modal calls")
            
            try:
                context.window_manager.event_timer_remove(self.timer)
                log_info("✅ Timer removed successfully")
            except Exception as e:
                log_error(f"ERROR: Failed to remove timer: {e}")
            
            _loop_kicking_operator_running = False
            log_info(f"Set _loop_kicking_operator_running to: {_loop_kicking_operator_running}")

            log_info("✅ Stopped asyncio loop kicking - modal operator finished")
            return {"FINISHED"}

        return {"RUNNING_MODAL"}


def register():
    log_info("Registering BLD_REMOTE_OT_async_loop operator...")
    try:
        bpy.utils.register_class(BLD_REMOTE_OT_async_loop)
        log_info("✅ BLD_REMOTE_OT_async_loop operator registered successfully")
    except ValueError as e:
        if "already registered" in str(e):
            # Already registered, that's fine
            log_info("⚠️ BLD_REMOTE_OT_async_loop operator already registered")
        else:
            log_error(f"ERROR: Failed to register BLD_REMOTE_OT_async_loop operator: {e}")
            raise
    except Exception as e:
        log_error(f"ERROR: Unexpected error registering operator: {e}")
        raise


def unregister():
    log_info("Unregistering BLD_REMOTE_OT_async_loop operator...")
    try:
        bpy.utils.unregister_class(BLD_REMOTE_OT_async_loop)
        log_info("✅ BLD_REMOTE_OT_async_loop operator unregistered successfully")
    except (ValueError, RuntimeError) as e:
        # Not registered or already unregistered, that's fine
        log_info(f"⚠️ BLD_REMOTE_OT_async_loop operator not registered or already unregistered: {e}")
    except Exception as e:
        log_error(f"ERROR: Unexpected error unregistering operator: {e}")
        # Don't raise during unregistration