# How to Keep Blender Alive in Background Mode

## Problem

When running Blender in background mode (`blender --background`), Blender will exit immediately after executing a Python script unless you implement a proper keep-alive mechanism. This is because background mode has no GUI event loop to keep the process running.

## Core Principle

**Drive the existing asyncio event loop** instead of creating new loops or relying on status checks. The key is to use the addon's `async_loop.kick_async_loop()` function to process asyncio events continuously.

## Proven Solution Pattern

Based on successful implementations in `blender-echo-plugin` and `blender-remote-cli`:

```python
import time
import signal
import sys

# Global flag to control the keep-alive loop
_keep_running = True

def signal_handler(signum, frame):
    global _keep_running
    print(f"Received signal {signum}, shutting down...")
    _keep_running = False
    
    # Try to gracefully shutdown services
    try:
        # Your cleanup code here
        pass
    except Exception as e:
        print(f"Error during cleanup: {e}")
    
    time.sleep(0.5)  # Allow cleanup time
    sys.exit(0)

# Install signal handlers
signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Termination

# Import the addon's async loop module
from your_addon import async_loop

print("Starting background mode keep-alive loop...")

try:
    # Give services time to start up
    time.sleep(2)
    
    # Main keep-alive loop - drive the async event loop
    while _keep_running:
        # This is the heart of background mode operation
        # It drives the asyncio event loop, allowing servers to run
        if async_loop.kick_async_loop():
            # The loop has no more tasks and wants to stop
            print("Async loop completed, exiting...")
            break
        time.sleep(0.05)  # 50ms sleep to prevent high CPU usage
        
except KeyboardInterrupt:
    print("Interrupted by user, shutting down...")
    _keep_running = False
except Exception as e:
    print(f"Error in keep-alive loop: {e}")
    _keep_running = False

print("Background mode keep-alive loop finished, Blender will exit.")
```

## Key Technical Details

### 1. Optimal Sleep Timing
- **Use 50ms (0.05 seconds)** for responsive processing without high CPU usage
- **Avoid 1-second sleeps** - they cause delayed responsiveness
- **Don't use no sleep** - it will consume 100% CPU

### 2. Event Loop Management
- **Drive the existing loop**: Use `async_loop.kick_async_loop()`
- **Don't create new loops**: Never use `asyncio.new_event_loop()` or `loop.run_forever()`
- **Exit when loop completes**: When `kick_async_loop()` returns `True`, exit gracefully

### 3. Signal Handling
- **Install SIGINT and SIGTERM handlers** for graceful shutdown
- **Use global flags** to communicate shutdown state
- **Allow cleanup time** before exiting

## Common Mistakes to Avoid

### ❌ Wrong: Creating Separate Async Loop
```python
# DON'T DO THIS
def run_forever():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_forever()

thread = threading.Thread(target=run_forever, daemon=True)
thread.start()
```

### ❌ Wrong: Status-Based Exit Logic
```python
# DON'T DO THIS
while _keep_running:
    time.sleep(1)
    if not service.is_running():
        print("Service stopped, exiting...")
        break
```

### ❌ Wrong: Long Sleep Intervals
```python
# DON'T DO THIS
while _keep_running:
    time.sleep(1)  # Too slow, use 0.05 instead
```

### ✅ Correct: Drive Existing Event Loop
```python
# DO THIS
while _keep_running:
    if async_loop.kick_async_loop():
        break
    time.sleep(0.05)
```

## Real-World Example: blender-remote-cli

Here's the complete working implementation from `src/blender_remote/cli.py`:

```python
# In background mode, add proper keep-alive mechanism
if background:
    startup_code.append(
        """
# Keep Blender running in background mode
import time
import signal
import sys

# Global flag to control the keep-alive loop
_keep_running = True

def signal_handler(signum, frame):
    global _keep_running
    print(f"Received signal {signum}, shutting down...")
    _keep_running = False
    
    # Try to gracefully shutdown the MCP service
    try:
        import bld_remote
        if bld_remote.is_mcp_service_up():
            bld_remote.stop_mcp_service()
            print("MCP service stopped")
    except Exception as e:
        print(f"Error stopping MCP service: {e}")
    
    time.sleep(0.5)
    sys.exit(0)

# Install signal handlers
signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Termination

print("Blender running in background mode. Press Ctrl+C to exit.")

# Keep the main thread alive by driving the async loop
try:
    # Give the MCP service time to start up
    time.sleep(2)
    
    print("✅ Starting main background loop...")
    
    # Import the async loop module to drive the event loop
    import bld_remote
    from bld_remote_mcp import async_loop
    
    # Main keep-alive loop - drive the async event loop
    while _keep_running:
        if async_loop.kick_async_loop():
            print("Async loop completed, exiting...")
            break
        time.sleep(0.05)  # 50ms sleep to prevent high CPU usage
            
except KeyboardInterrupt:
    print("Interrupted by user, shutting down...")
    _keep_running = False

print("Background mode keep-alive loop finished, Blender will exit.")
"""
    )
```

## Architecture Understanding

### Background vs GUI Mode
- **GUI Mode**: Blender's UI event loop keeps the process alive
- **Background Mode**: No UI, so external script must provide keep-alive mechanism
- **Modal Operators**: Work in GUI mode but fall back to app timers in background

### Event Loop Coordination
- **Addon creates asyncio tasks**: Server operations run as asyncio tasks
- **Script drives the loop**: External script calls `kick_async_loop()` to process events
- **Cooperative execution**: Both addon and script coordinate to keep everything running

## Testing Your Implementation

### 1. Start Background Mode
```bash
blender --background --python your_script.py &
```

### 2. Verify Process Stays Running
```bash
ps aux | grep blender | grep -v grep
# Should show your Blender process running
```

### 3. Test Service Functionality
```bash
# Test whatever service your addon provides
curl http://localhost:6688/status
# Or use appropriate client tools
```

### 4. Test Graceful Shutdown
```bash
kill -TERM <blender_pid>
# Process should shut down cleanly with your cleanup messages
```

## Performance Considerations

### CPU Usage
- **50ms sleep interval**: Provides ~20 loop iterations per second
- **Responsive**: Quick enough for real-time operations
- **Efficient**: Low CPU usage during idle periods

### Memory Management
- **Event loop cleanup**: `kick_async_loop()` handles task cleanup automatically
- **No memory leaks**: Proper signal handling prevents resource leaks
- **Garbage collection**: Asyncio tasks are properly disposed

## Integration with Different Addons

### For TCP Servers
```python
# Import your addon's async loop module
from your_tcp_addon import async_loop

while _keep_running:
    if async_loop.kick_async_loop():
        break
    time.sleep(0.05)
```

### For HTTP Servers
```python
# Same pattern works for HTTP servers
from your_http_addon import async_loop

while _keep_running:
    if async_loop.kick_async_loop():
        break
    time.sleep(0.05)
```

### For Custom Services
```python
# Any addon using asyncio can use this pattern
from your_service_addon import async_loop

while _keep_running:
    if async_loop.kick_async_loop():
        break
    time.sleep(0.05)
```

## Troubleshooting

### Process Exits Immediately
- **Check if addon is loaded**: Ensure your addon is properly installed and enabled
- **Verify async_loop import**: Make sure the async loop module is accessible
- **Check for exceptions**: Look for error messages in the console output

### High CPU Usage
- **Check sleep interval**: Ensure you're using `time.sleep(0.05)` or similar
- **Verify kick_async_loop**: Make sure you're calling the function correctly
- **Monitor task count**: Excessive tasks might indicate a problem

### Service Not Responding
- **Allow startup time**: Give services 2-5 seconds to initialize
- **Check port conflicts**: Ensure no other process is using the same port
- **Verify in GUI mode first**: Test your addon in GUI mode before background

## Best Practices

### 1. Graceful Startup
```python
# Give services time to start
time.sleep(2)
print("✅ Services initialized, starting main loop...")
```

### 2. Robust Error Handling
```python
try:
    while _keep_running:
        if async_loop.kick_async_loop():
            break
        time.sleep(0.05)
except Exception as e:
    print(f"Error in main loop: {e}")
    # Cleanup and exit gracefully
```

### 3. Clear Status Messages
```python
print("Blender running in background mode. Press Ctrl+C to exit.")
print("✅ Starting main background loop...")
print("Background mode keep-alive loop finished, Blender will exit.")
```

### 4. Proper Cleanup
```python
def signal_handler(signum, frame):
    # Stop services in correct order
    # Allow time for cleanup
    # Exit cleanly
    pass
```

## References

- **Successful Implementation**: `src/blender_remote/cli.py` (blender-remote project)
- **Reference Pattern**: `context/refcode/blender-echo-plugin/install_and_run_tcp_echo.py`
- **Bug Fix Documentation**: `context/logs/2025-07-11_cli-background-mode-bug-fix-success.md`

## Summary

The key to keeping Blender alive in background mode is to **drive the existing asyncio event loop** using your addon's `async_loop.kick_async_loop()` function with 50ms sleep intervals. Avoid creating new loops, status-based exit logic, or long sleep times. Implement proper signal handling for graceful shutdown, and always test your implementation thoroughly.