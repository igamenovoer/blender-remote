# How to Check if a Registered Timer Function is Executed in Blender

## Problem
After calling `bpy.app.timers.register(execute_wrapper, first_interval=0.0)` in Blender, you cannot directly wait for the timer to complete because timers are asynchronous and run on Blender's main thread event loop.

## Key Points About Blender Timers

1. **Timers are asynchronous**: `bpy.app.timers.register()` schedules a function to run later and returns immediately
2. **Main thread execution**: Timers run on Blender's main thread, so blocking/waiting would freeze the UI
3. **No built-in synchronization**: There's no direct way to wait for timer completion

## Solution Approaches

### 1. Callback Pattern (Recommended)
Instead of waiting, use a callback approach:

```python
def execute_wrapper():
    # Your timer logic here
    print("Timer executed")
    # Call next function when done
    on_timer_complete()
    return None  # Unregister timer

def on_timer_complete():
    # Code to run after timer completes
    print("Timer finished, continuing...")

bpy.app.timers.register(execute_wrapper, first_interval=0.0)
```

### 2. State Variable Pattern
Use a global state variable to track completion:

```python
timer_completed = False

def execute_wrapper():
    global timer_completed
    # Your timer logic here
    timer_completed = True
    return None  # Unregister timer

def check_completion():
    if timer_completed:
        # Continue with next steps
        print("Timer completed, proceeding...")
    else:
        # Check again later
        bpy.app.timers.register(check_completion, first_interval=0.1)

bpy.app.timers.register(execute_wrapper, first_interval=0.0)
bpy.app.timers.register(check_completion, first_interval=0.1)
```

### 3. Queue-based Pattern
Use a queue for communication between timer and main code:

```python
import queue
result_queue = queue.Queue()

def execute_wrapper():
    # Your timer logic here
    result = "Timer completed"
    result_queue.put(result)
    return None

def process_results():
    try:
        result = result_queue.get_nowait()
        print(f"Got result: {result}")
        # Continue processing
    except queue.Empty:
        # Check again later
        bpy.app.timers.register(process_results, first_interval=0.1)

bpy.app.timers.register(execute_wrapper, first_interval=0.0)
bpy.app.timers.register(process_results, first_interval=0.1)
```

### 4. Current Implementation Pattern (Polling)
The current code in `_execute_command_sync()` uses a polling approach:

```python
def _execute_command_sync(self, command):
    """Execute command synchronously using Blender timer for main thread access."""
    # Use a shared container to get results from timer callback
    result_container = {"response": None, "done": False}
    
    def execute_wrapper():
        try:
            result_container["response"] = self.execute_command(command)
        except Exception as e:
            log_error(f"Error executing command: {str(e)}")
            result_container["response"] = {
                "status": "error",
                "message": str(e)
            }
        finally:
            result_container["done"] = True
        return None
    
    # Schedule execution in main thread
    bpy.app.timers.register(execute_wrapper, first_interval=0.0)
    
    # Wait for completion (polling)
    timeout = 30.0  # 30 second timeout
    start_time = time.time()
    while not result_container["done"]:
        time.sleep(0.01)  # Small sleep to avoid busy waiting
        if time.time() - start_time > timeout:
            return {"status": "error", "message": "Command execution timeout"}
    
    return result_container["response"]
```

## Best Practices

1. **Use callbacks when possible** - The callback pattern is usually the most straightforward approach
2. **Avoid blocking the main thread** - Never use busy waiting without sleep intervals
3. **Implement timeouts** - Always have a timeout mechanism to prevent infinite waiting
4. **Use small sleep intervals** - When polling, use `time.sleep(0.01)` to avoid excessive CPU usage
5. **Handle exceptions properly** - Always wrap timer functions in try-catch blocks

## Important Notes

- **Cannot use threading.Event or similar** - Blender's main thread management doesn't work well with standard threading synchronization primitives
- **Background mode considerations** - Timer behavior may differ between GUI and background modes
- **Memory management** - Make sure to clean up references in shared containers to prevent memory leaks

## Background Mode Behavior

### Does `bpy.app.timers.register()` work in background mode?

**Yes, timers work in background mode.** The timer system is part of Blender's core event loop and executes regardless of GUI presence.

#### Key Points:
1. **Timers execute normally** - Registered functions will run at scheduled intervals
2. **Event loop still active** - Background mode maintains the main thread event loop
3. **No UI overhead** - May actually have more consistent timing without viewport updates

#### Example:
```python
# This works identically in both GUI and background mode
def background_timer():
    print(f"Timer executed at {time.time()}")
    return None  # Unregister after execution

bpy.app.timers.register(background_timer, first_interval=0.0)
```

#### Background Mode Considerations:
- **Process lifetime**: Script must stay alive long enough for timers to execute
- **No UI operations**: Avoid viewport screenshots, UI updates within timer functions  
- **Version compatibility**: Older Blender versions (2.79) may not support timers in headless mode
- **Error handling**: Background errors may be less visible, ensure proper logging

#### Current Implementation Analysis:
The polling pattern in `_execute_command_sync()` works well in background mode because:
- Timer registration and execution work normally
- Polling loop (`while not result_container["done"]`) keeps the process alive
- No UI dependencies in the synchronization mechanism

## Impact of Sleep-Loop on Timer Execution

### How does a sleep-loop in the main thread affect `bpy.app.timers.register()` execution?

**Sleep-loops in the main thread will NOT significantly impact timer execution** because `time.sleep()` yields control back to the OS scheduler, allowing other processes and the event loop to continue.

#### Key Technical Details:

1. **`time.sleep()` is non-blocking to event loop**: When the main thread calls `time.sleep()`, it suspends execution and yields CPU time to the OS scheduler
2. **Timers run on main thread**: `bpy.app.timers` execute on Blender's main thread via the event loop
3. **Event loop continues**: During sleep periods, the event loop can still process timer callbacks

#### Sleep-Loop Pattern Analysis:

```python
# This pattern allows timers to execute normally
import time

def main_loop():
    while True:
        time.sleep(0.05)  # 50ms sleep
        # Other minimal work

def my_timer():
    print(f"Timer executed at {time.time()}")
    return 0.1  # Re-register for 100ms later

bpy.app.timers.register(my_timer, first_interval=0.0)
main_loop()  # This won't block timer execution
```

#### Timing Considerations:

- **Sleep interval impact**: 50ms sleep allows timers with >= 50ms intervals to execute reliably
- **Timer precision**: Timers scheduled < 50ms may experience some jitter due to sleep granularity  
- **CPU efficiency**: Sleep-loops are CPU-friendly compared to busy-waiting

#### What WOULD block timer execution:

```python
# BAD: This would block timers
def blocking_computation():
    for i in range(1000000):
        result = complex_calculation()  # No sleep, keeps CPU busy
        
# BAD: Infinite loop without yielding
def busy_wait():
    while True:
        pass  # Blocks event loop completely
```

#### Best Practices for Sleep-Loops:

1. **Use reasonable intervals**: 10-100ms sleep intervals work well
2. **Shorter than timer intervals**: Keep sleep duration shorter than your timer intervals
3. **Consider alternatives**: For long-running processes, threading may be better
4. **Monitor performance**: Watch for timer execution delays in practice

#### Current Implementation Compatibility:

Your polling pattern in `_execute_command_sync()` works well with sleep-loops:
- The `time.sleep(0.01)` in the polling loop is much shorter than typical main thread sleep
- Timer execution happens independently of the polling sleep
- Both can coexist without interference
