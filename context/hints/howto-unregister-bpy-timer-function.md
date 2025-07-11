# How to Unregister a bpy.app.timers Function

## Overview

Blender's `bpy.app.timers` module is a powerful tool for scheduling functions to run after a specified delay, making it ideal for running tasks in the background without blocking the user interface. However, it is crucial to properly manage these timers and unregister them when they are no longer needed to prevent memory leaks and unexpected behavior.

This guide outlines the correct ways to unregister a timer function in Blender.

## Key Concepts

- **Registration**: You start a timer by calling `bpy.app.timers.register(my_function, first_interval=1.0)`. The function `my_function` will be executed after the interval.
- **Execution and Rescheduling**: When `my_function` is executed, its return value determines the timer's fate:
    - If it returns a `float` or `int`, the timer is rescheduled to run again after that many seconds.
    - If it returns `None` or nothing, the timer is automatically unregistered.
- **Unregistration**: You can also manually stop a timer from anywhere in your code.

There are two primary methods to stop a timer: implicit unregistration (from within the function) and explicit unregistration (from outside).

## Method 1: Implicit Unregistration (Returning `None`)

The most common and often cleanest way to stop a timer is to have the timer function unregister itself by returning `None`. This is the standard pattern for tasks that have a clear completion condition.

### How It Works
When the function registered with the timer returns `None`, Blender's timer system automatically removes it from the execution queue.

### Example: A Task That Runs for a Limited Time

```python
import bpy

class MyTimerTask:
    def __init__(self):
        self.counter = 5
        print("Timer started. Will run 5 times.")

    def run(self):
        if self.counter <= 0:
            print("Timer task finished. Unregistering.")
            return None  # This will unregister the timer

        print(f"Timer running... {self.counter} runs left.")
        self.counter -= 1
        return 1.0  # Reschedule to run again in 1 second

# To run this:
# task = MyTimerTask()
# bpy.app.timers.register(task.run)
```

**Best for**:
- Tasks that know when they are finished (e.g., polling for a result, animations, countdowns).
- Encapsulating the timer's lifecycle within the logic of the task itself.

## Method 2: Explicit Unregistration (`bpy.app.timers.unregister()`)

You can manually unregister a timer from any part of your code using `bpy.app.timers.unregister()`. This is useful when the lifetime of the timer is controlled by external events, such as user interaction or the state of your addon.

### How It Works
You pass the exact same function object that was used for registration to the `unregister` method.

### Example: A Timer Controlled by an Operator

```python
import bpy

def my_persistent_task():
    """A task that runs every second until explicitly stopped."""
    print("Persistent task is running...")
    return 1.0

class StartMyTimer(bpy.types.Operator):
    bl_idname = "wm.start_my_timer"
    bl_label = "Start Timer"

    def execute(self, context):
        if not bpy.app.timers.is_registered(my_persistent_task):
            bpy.app.timers.register(my_persistent_task)
            self.report({'INFO'}, "Timer started.")
        else:
            self.report({'INFO'}, "Timer is already running.")
        return {'FINISHED'}

class StopMyTimer(bpy.types.Operator):
    bl_idname = "wm.stop_my_timer"
    bl_label = "Stop Timer"

    def execute(self, context):
        if bpy.app.timers.is_registered(my_persistent_task):
            bpy.app.timers.unregister(my_persistent_task)
            self.report({'INFO'}, "Timer stopped.")
        else:
            self.report({'INFO'}, "Timer was not running.")
        return {'FINISHED'}

# To use this, you would register these operators and call them.
```

## Best Practices and Common Pitfalls

### 1. Always Check Before Unregistering
Attempting to unregister a function that is not currently registered will raise a `ValueError`. To avoid this, always check first with `bpy.app.timers.is_registered()`.

```python
if bpy.app.timers.is_registered(my_function):
    bpy.app.timers.unregister(my_function)
```

### 2. Handling Timers with Arguments (`functools.partial`)
If you register a timer with arguments using `functools.partial`, you **must** keep a reference to the `partial` object to unregister it later.

```python
import bpy
from functools import partial

def my_task_with_args(arg1, arg2):
    print(f"Task running with {arg1} and {arg2}")
    return 1.0

# Store the partial object
timer_func = partial(my_task_with_args, "hello", 42)

# Register it
bpy.app.timers.register(timer_func)

# To unregister it later:
if bpy.app.timers.is_registered(timer_func):
    bpy.app.timers.unregister(timer_func)
```
**Pitfall**: Trying to unregister with `partial(my_task_with_args, "hello", 42)` again will **not** work, as it creates a *new* `partial` object. You must use the original one.

### 3. Cleanup in `unregister()`
When developing an addon, it's critical to clean up any running timers in your addon's `unregister()` function. This prevents errors when the addon is reloaded or disabled.

```python
# In your addon's __init__.py

_timer_func = None # Global-like variable to hold the timer function reference

def register():
    # ... your registration code ...
    global _timer_func
    _timer_func = partial(my_addon_task, some_data)
    bpy.app.timers.register(_timer_func)


def unregister():
    # ... your unregistration code ...
    global _timer_func
    if _timer_func and bpy.app.timers.is_registered(_timer_func):
        bpy.app.timers.unregister(_timer_func)
    _timer_func = None
```

## Summary

| Method | When to Use | How to Use |
|---|---|---|
| **Implicit (Return `None`)** | The task knows its own completion condition. | `return None` from the timer function. |
| **Explicit (`unregister()`)** | The timer's lifecycle is controlled by external events (e.g., UI, addon state). | Call `bpy.app.timers.unregister(your_function)`. |

By understanding these two methods and following best practices, you can create robust and well-behaved addons that use timers effectively without causing instability.
