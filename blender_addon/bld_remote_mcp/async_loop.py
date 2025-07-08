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
    if sys.platform == "win32":
        # On Windows, use ProactorEventLoop for proper operation
        try:
            asyncio.get_event_loop().close()
        except:
            pass
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    else:
        loop = asyncio.get_event_loop()

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
    loop.set_default_executor(executor)


def kick_async_loop(*args) -> bool:
    """Performs a single iteration of the asyncio event loop.

    :return: whether the asyncio loop should stop after this kick.
    """
    loop = asyncio.get_event_loop()

    # Even when we want to stop, we always need to do one more
    # 'kick' to handle task-done callbacks.
    stop_after_this_kick = False

    if loop.is_closed():
        log_warning("loop closed, stopping immediately.")
        return True

    # Passing an explicit loop is required. Without it, the function uses
    # asyncio.get_running_loop(), which raises a RuntimeError as the current
    # loop isn't running.
    all_tasks = asyncio.all_tasks(loop=loop)
    
    # Add debugging for task processing
    log_info(f"kick_async_loop: {len(all_tasks)} tasks to process")

    if not len(all_tasks):
        log_info("no more scheduled tasks, stopping after this kick.")
        stop_after_this_kick = True

    elif all(task.done() for task in all_tasks):
        log_info(
            f"all {len(all_tasks)} tasks are done, fetching results and stopping after this kick."
        )
        stop_after_this_kick = True

        # Clean up circular references between tasks.
        gc.collect()

        for task_idx, task in enumerate(all_tasks):
            if not task.done():
                continue

            try:
                res = task.result()
                log_info(f"   task #{task_idx}: result={res!r}")
            except asyncio.CancelledError:
                # No problem, we want to stop anyway.
                log_info(f"   task #{task_idx}: cancelled")
            except Exception:
                print("{}: resulted in exception".format(task))
                traceback.print_exc()
    else:
        # There are tasks that are not done yet
        log_info(f"Processing {len(all_tasks)} tasks...")
        for task_idx, task in enumerate(all_tasks):
            if task.done():
                log_info(f"   task #{task_idx}: already done")
            else:
                log_info(f"   task #{task_idx}: pending - {task}")

    loop.stop()
    loop.run_forever()

    return stop_after_this_kick


def ensure_async_loop():
    log_info("Starting asyncio loop")
    result = bpy.ops.bld_remote.async_loop()
    log_info(f"Result of starting modal operator is {result!r}")
    
    # Add extra debugging
    log_info(f"Loop kicking operator running: {_loop_kicking_operator_running}")
    
    # Check if there are any scheduled tasks
    try:
        loop = asyncio.get_event_loop()
        all_tasks = asyncio.all_tasks(loop=loop)
        log_info(f"Number of scheduled asyncio tasks: {len(all_tasks)}")
        for i, task in enumerate(all_tasks):
            log_info(f"Task {i}: {task}")
    except Exception as e:
        log_info(f"Error checking tasks: {e}")


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

        log_info("Modal operator invoke called")
        
        if _loop_kicking_operator_running:
            log_info("Another loop-kicking operator is already running.")
            return {"PASS_THROUGH"}

        log_info("Starting new modal operator")
        context.window_manager.modal_handler_add(self)
        _loop_kicking_operator_running = True

        wm = context.window_manager
        self.timer = wm.event_timer_add(0.00025, window=context.window)
        log_info("Modal operator timer added, returning RUNNING_MODAL")

        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        global _loop_kicking_operator_running

        # If _loop_kicking_operator_running is set to False, someone called
        # erase_async_loop(). This is a signal that we really should stop
        # running.
        if not _loop_kicking_operator_running:
            return {"FINISHED"}

        if event.type != "TIMER":
            return {"PASS_THROUGH"}

        # Only log occasionally to avoid spam
        if hasattr(self, '_modal_call_count'):
            self._modal_call_count += 1
        else:
            self._modal_call_count = 1
            
        if self._modal_call_count % 1000 == 1:  # Log every 1000 calls
            log_info(f"Modal operator processing timer event (call #{self._modal_call_count})")

        stop_after_this_kick = kick_async_loop()
        if stop_after_this_kick:
            context.window_manager.event_timer_remove(self.timer)
            _loop_kicking_operator_running = False

            log_info("Stopped asyncio loop kicking")
            return {"FINISHED"}

        return {"RUNNING_MODAL"}


def register():
    try:
        bpy.utils.register_class(BLD_REMOTE_OT_async_loop)
    except ValueError as e:
        if "already registered" in str(e):
            # Already registered, that's fine
            pass
        else:
            raise


def unregister():
    try:
        bpy.utils.unregister_class(BLD_REMOTE_OT_async_loop)
    except (ValueError, RuntimeError):
        # Not registered or already unregistered, that's fine
        pass