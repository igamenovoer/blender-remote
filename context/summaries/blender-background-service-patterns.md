# Blender Background Service Patterns

## Overview

The blender-echo-plugin demonstrates how to create a robust TCP server inside Blender that can run in `blender --background` mode without any GUI dependencies. This is critical for creating headless Blender services that can be controlled remotely.

## Core Problem: Blender Background Mode Limitations

When running `blender --background <python script>`, Blender:
1. Executes the Python script at startup
2. **Immediately exits when the script finishes**
3. Has no GUI event loop to keep the process alive
4. Restricts access to many GUI-dependent APIs

## Solution Architecture

### 1. Asyncio Event Loop Integration

The key innovation is integrating asyncio with Blender's threading model:

```python
# async_loop.py - Critical event loop integration
def kick_async_loop(*args) -> bool:
    """Performs a single iteration of the asyncio event loop."""
    loop = asyncio.get_event_loop()
    
    # Check for running tasks
    all_tasks = asyncio.all_tasks(loop=loop)
    stop_after_this_kick = not len(all_tasks) or all(task.done() for task in all_tasks)
    
    # Execute one iteration
    loop.stop()
    loop.run_forever()
    
    return stop_after_this_kick
```

**Modal Operator for Event Loop**:
```python
class AsyncLoopModalOperator(bpy.types.Operator):
    def modal(self, context, event):
        if event.type != "TIMER":
            return {"PASS_THROUGH"}
        
        # Critical: Kick the asyncio loop periodically
        stop_after_this_kick = kick_async_loop()
        if stop_after_this_kick:
            return {"FINISHED"}
        
        return {"RUNNING_MODAL"}
```

### 2. Background-Safe TCP Server

**Server Implementation**:
```python
class TCPEchoProtocol(asyncio.Protocol):
    def data_received(self, data):
        try:
            message = json.loads(data.decode())
            response = process_message(message)
            self.transport.write(json.dumps(response).encode())
        finally:
            self.transport.close()

async def start_server_task(port, scene_to_update):
    global tcp_server, server_port
    server_port = port
    loop = asyncio.get_event_loop()
    
    tcp_server = await loop.create_server(TCPEchoProtocol, '127.0.0.1', port)
    server_task = asyncio.ensure_future(tcp_server.serve_forever())
    
    if scene_to_update:
        scene_to_update.tcp_echo_server_running = True
```

### 3. Safe Code Execution in Main Thread

**Critical Pattern - Timer-Based Execution**:
```python
def process_message(data):
    if "code" in data:
        code_to_run = data['code']
        
        # Special quit handling
        if "quit_blender" in code_to_run:
            raise SystemExit("Shutdown requested by client.")
        
        # CRITICAL: Execute in main thread via timer
        def code_runner():
            exec(code_to_run, {'bpy': bpy})
        
        bpy.app.timers.register(code_runner, first_interval=0.01)
```

### 4. Background-Safe Resource Access

**Avoid Context Dependencies**:
```python
# WRONG: Don't use bpy.context in background mode
# scene = bpy.context.scene  # May fail in background

# CORRECT: Use direct data access
scene = bpy.data.scenes[0] if bpy.data.scenes else None
```

### 5. Process Lifecycle Management

**External Script Pattern**:
```python
# External launcher script (not inside addon)
import bpy
import addon_utils

# 1. Install and enable addon
addon_utils.enable("tcp_echo")

# 2. Start the server
import tcp_echo
tcp_echo.start_server_from_script()

# 3. Keep Blender alive with event loop
try:
    while True:
        # CRITICAL: This keeps Blender alive and processes asyncio events
        from tcp_echo import async_loop
        should_stop = async_loop.kick_async_loop()
        if should_stop:
            break
        time.sleep(0.01)  # Small delay to prevent CPU spinning
except SystemExit:
    print("Shutdown requested, exiting cleanly")
finally:
    # Cleanup code here
    pass
```

**Addon Entry Point**:
```python
def start_server_from_script():
    """Entry point for external script to start server"""
    port = int(os.environ.get('BLENDER_HTTP_ECHO_PORT', 23333))
    scene = bpy.data.scenes[0] if bpy.data.scenes else None
    
    # Start the async server
    asyncio.ensure_future(start_server_task(port, scene))
    
    # Ensure async loop machinery is ready
    try:
        async_loop.register()
    except ValueError:
        pass  # Already registered
```

## Key Design Principles

### 1. **No GUI Dependencies**
```python
# No UI classes in background addon
bl_info = {
    "location": "N/A",  # No UI location
    "category": "Development",
}

# No bpy.types.Panel or UI operators
```

### 2. **Robust Cleanup**
```python
def cleanup_server():
    """Idempotent cleanup function"""
    global tcp_server, server_task
    
    if tcp_server:
        tcp_server.close()
        tcp_server = None
    
    if server_task:
        server_task.cancel()
        server_task = None
    
    # Safe scene property update
    if bpy.data.scenes:
        bpy.data.scenes[0].tcp_echo_server_running = False
```

### 3. **Exception Safety**
```python
def unregister():
    cleanup_server()
    try:
        del bpy.types.Scene.tcp_echo_server_running
    except (AttributeError, RuntimeError):
        pass  # Already cleaned up
    
    try:
        async_loop.unregister()
    except (RuntimeError, ValueError):
        pass  # Already unregistered
```

### 4. **Cross-Platform Asyncio Setup**
```python
def setup_asyncio_executor():
    """Platform-specific asyncio configuration"""
    import sys
    
    if sys.platform == "win32":
        # Windows needs ProactorEventLoop for proper operation
        asyncio.get_event_loop().close()
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    else:
        loop = asyncio.get_event_loop()
    
    # Thread pool for background tasks
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
    loop.set_default_executor(executor)
```

## Usage Pattern

### Launch Command
```bash
# Set port via environment variable
export BLENDER_HTTP_ECHO_PORT=23333
blender --background --python launcher_script.py
```

### Client Interaction
```python
import socket
import json

def send_command(port, command_data):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('127.0.0.1', port))
        s.sendall(json.dumps(command_data).encode('utf-8'))
        response = s.recv(1024)
        return json.loads(response.decode('utf-8'))

# Execute Blender code
send_command(23333, {"code": "bpy.ops.mesh.primitive_cube_add()"})

# Shutdown server
send_command(23333, {"code": "quit_blender"})
```

## Critical Success Factors

1. **Event Loop Integration**: The `kick_async_loop()` function is essential for making asyncio work in Blender's environment
2. **Main Thread Execution**: All `bpy.*` operations must use `bpy.app.timers.register()` from background threads
3. **External Process Management**: The external launcher script is crucial for keeping Blender alive
4. **Clean Shutdown**: The "quit_blender" pattern allows graceful termination
5. **Background Safety**: Avoid `bpy.context` and GUI-dependent APIs

## Advantages Over Simple Socket Approach

1. **Proper Asyncio Integration**: Handles multiple connections and concurrent operations
2. **Background Mode Support**: Works without any GUI components
3. **Process Lifecycle**: Controlled startup and shutdown
4. **Platform Compatibility**: Handles Windows/Linux asyncio differences
5. **Exception Safety**: Robust error handling and cleanup

This pattern enables creating truly headless Blender services that can run as background processes and be controlled remotely via TCP connections.