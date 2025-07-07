# BLD Remote MCP Implementation - Complete Implementation Guide

## Overview

This document chronicles the complete implementation of the BLD Remote MCP service, documenting the journey from initial requirements to working background-mode service, including all key learnings, architectural decisions, and proven patterns discovered.

## Project Goal

Implement a minimal Blender MCP service with background running support, based on the specification in `context/tasks/blender-bg-mcp/goal.md`:

- **Target**: Simple TCP server that can run in both `blender --background` and GUI modes
- **Environment Control**: `BLD_REMOTE_MCP_PORT=6688`, `BLD_REMOTE_MCP_START_NOW=true/false`
- **Python API**: Module `bld_remote` with 7 core functions
- **Protocol**: Simple JSON messages with `"message"` and `"code"` fields
- **No 3rd party dependencies**: Unlike reference blender-mcp implementation

## Implementation Journey

### Phase 1: Research and Reference Analysis

**Reference Implementations Studied:**

1. **context/refcode/blender-echo-plugin/** - ✅ **PROVEN for background mode**
   - Simple TCP server with JSON command processing
   - External script manages background mode lifecycle
   - Manual event loop kicking with `kick_async_loop()`
   - **Key Insight**: Background mode requires external process management

2. **context/refcode/blender_auto_mcp/** - ⚠️ **Complex but untested in background**
   - Modular architecture with auto-start capabilities
   - Internal `asyncio.run()` blocking approach
   - **Critical Discovery**: NOT thoroughly tested in background mode
   - **User Warning**: "blender_auto_mcp is NOT thoroughly tested in blender background mode, so be careful"

3. **context/refcode/blender-mcp/** - Reference but deprecated
   - Original monolithic implementation
   - Replaced by blender_auto_mcp

### Phase 2: Initial Implementation Attempts

**First Attempt: Complex MCP Integration**
- ❌ Tried to implement full MCP protocol directly in Blender addon
- ❌ Used FastMCP patterns with complex asyncio integration
- **Issues**: Operator registration failures, asyncio conflicts

**Second Attempt: Following blender_auto_mcp Pattern**  
- ❌ Attempted internal `asyncio.run()` blocking for background mode
- ❌ Complex signal handling and shutdown events
- **Critical Error**: `asyncio.run()` blocks before server starts in background mode

**User Guidance Received:**
> "note that @context/refcode/blender-echo-plugin/ contains approach as to how to create a background running service that also functions in GUI mode, learn from it, that is the only method I tried that works"

### Phase 3: Proven Implementation - Echo Plugin Pattern

**Architecture Decision**: Follow blender-echo-plugin pattern exactly
- Simple TCP server in Blender addon
- External script for background mode management
- Manual asyncio event loop kicking

**Key Implementation Details:**

```python
# Simple JSON protocol
{
    "message": "Hello from client",
    "code": "print('Executing in Blender')"
}

# Response format
{
    "response": "OK",
    "message": "Code execution scheduled", 
    "source": "tcp://127.0.0.1:6688"
}
```

## Final Working Architecture

### Blender Addon: `blender_addon/bld_remote_mcp/`

**Core Components:**
1. **`__init__.py`** - Main addon with TCP server and Python API
2. **`async_loop.py`** - Asyncio event loop management (from echo-plugin)
3. **`utils.py`** - Logging utilities with required format
4. **`config.py`** - Environment variable handling

**TCP Server Pattern:**
```python
class BldRemoteProtocol(asyncio.Protocol):
    def data_received(self, data):
        message = json.loads(data.decode())
        response = process_message(message)
        self.transport.write(json.dumps(response).encode())
        self.transport.close()

def process_message(data):
    if "code" in data:
        def code_runner():
            exec(code_to_run, {'bpy': bpy})
        bpy.app.timers.register(code_runner, first_interval=0.01)
    return {"response": "OK", "message": "Code execution scheduled"}
```

**Python API Module:**
```python
# Available as: import bld_remote
def get_status()              # Return service status dictionary
def start_mcp_service()       # Start MCP service, raise exception on failure  
def stop_mcp_service()        # Stop MCP service, disconnects all clients forcefully
def get_startup_options()     # Return information about environment variables
def is_mcp_service_up()       # Return true/false, check if MCP service is up and running
def set_mcp_service_port(port_number)  # Set port number, only when service is stopped
def get_mcp_service_port()    # Return the current configured port
```

### Background Mode Script: `scripts/start_bld_remote_background.py`

**External Script Pattern (Proven Approach):**
```python
# 1. Create Python script for Blender
script_content = '''
import bpy
import os
os.environ['BLD_REMOTE_MCP_PORT'] = '{port}'
bpy.ops.preferences.addon_enable(module='bld_remote_mcp')
import bld_remote_mcp.async_loop as async_loop
async_loop.ensure_async_loop()

# Main background loop - keeps Blender alive
while True:
    stop_loop = async_loop.kick_async_loop()
    if stop_loop:
        break
    time.sleep(0.01)
'''

# 2. Start Blender with script
subprocess.Popen([blender_path, '--background', '--python', script_path])
```

## Key Technical Discoveries

### 1. Background Mode Patterns - Critical Learnings

**❌ WRONG: Internal Blocking Approach**
```python
# DON'T DO THIS - blocks before server starts
def register():
    if should_auto_start() and bpy.app.background:
        start_mcp_service()
        asyncio.run(background_main())  # ❌ BLOCKS HERE
```

**✅ CORRECT: External Script Management**
```python
# Addon just provides the server capability
def register():
    if should_auto_start():
        start_mcp_service()  # Server starts
        # External script manages the lifecycle

# External script keeps Blender alive
while True:
    kick_async_loop()  # Process asyncio events
    time.sleep(0.01)   # Prevent CPU spinning
```

### 2. Asyncio Integration Patterns

**Event Loop Management:**
- Use modal operator for GUI mode: `bpy.ops.bld_remote.async_loop()`
- Use manual kicking for background mode: `kick_async_loop()`
- Thread-safe execution with `bpy.app.timers.register()`

**Common Pitfalls Avoided:**
- ❌ `asyncio.run()` in addon registration
- ❌ Complex signal handling in background mode
- ❌ Trying to access `bpy.context` in restricted mode
- ❌ printf-style logging calls: `log_debug("task #%i", idx)` → `log_debug(f"task #{idx}")`

### 3. Environment Variable Configuration

**Working Pattern:**
```bash
export BLD_REMOTE_MCP_PORT=6688
export BLD_REMOTE_MCP_START_NOW=true
blender --background  # Addon auto-starts server
```

**Auto-start Logic:**
```python
def should_auto_start():
    start_now = os.environ.get('BLD_REMOTE_MCP_START_NOW', 'false').lower()
    return start_now in ('true', '1', 'yes', 'on')
```

## Testing Results

### GUI Mode Testing ✅
- **Setup**: Start Blender normally, enable addon manually
- **Server**: Runs on configurable port with async loop operator
- **Commands**: JSON messages processed successfully
- **Shutdown**: Clean shutdown with server cleanup

### Background Mode Testing ✅
- **Setup**: `python3 scripts/start_bld_remote_background.py --port 6691`
- **Process**: External script manages Blender lifecycle
- **Server**: TCP server listening and responding to commands
- **Shutdown**: Graceful shutdown with `quit_blender` command

**Test Results:**
```bash
# Background mode test successful
Response: {'response': 'OK', 'message': 'Code execution scheduled', 'source': 'tcp://127.0.0.1:6691'}
✓ BLD Remote MCP background mode test SUCCESSFUL!
```

## Critical User Guidance Received

### Blender Process Management
**User Memory**: "blender path is /home/igamenovoer/apps/blender-4.4.3-linux-x64/blender, you can start it yourself"

**Process Management Learnings:**
- Kill existing processes: `pkill -f blender`
- GUI mode stays running until killed
- Background mode exits immediately without blocking operation
- Wait ~10 seconds for startup, not 2 minutes
- Use external scripts for background mode management

### Reference Implementation Guidance
**User Warning**: "blender_auto_mcp is NOT thoroughly tested in blender background mode, so be careful, the thing that has been tested is @context/refcode/blender-echo-plugin/"

**Key Insight**: Use proven patterns rather than complex untested approaches.

### Background Mode Strategy
**User Feedback**: "note that if you start blender in background mode without infinite-loop, then the blender exits after started up"

**Solution**: External script with manual event loop kicking.

## Architectural Lessons Learned

### 1. Modularity vs Simplicity
- **blender_auto_mcp**: Complex modular architecture, untested background mode
- **blender-echo-plugin**: Simple focused approach, proven background mode
- **Choice**: Simple proven patterns > complex untested features

### 2. Background Mode Strategies
- **Internal blocking**: Elegant but doesn't work (blocks before server starts)
- **External management**: More complex but proven to work
- **Manual loop kicking**: Required for background asyncio processing

### 3. Error Handling Patterns
- Handle restricted context in addon registration
- Use thread-safe code execution with timers
- Graceful degradation when scenes not accessible
- Proper cleanup with signal handlers and atexit

## File Structure Created

```
blender-remote/
├── blender_addon/bld_remote_mcp/     # Blender addon
│   ├── __init__.py                   # Main addon with TCP server + Python API
│   ├── async_loop.py                 # Event loop management (from echo-plugin)
│   ├── utils.py                      # Logging with required format
│   └── config.py                     # Environment variable handling
└── scripts/
    └── start_bld_remote_background.py # External background mode script
```

## Usage Documentation

### GUI Mode
```bash
# Start Blender normally
blender

# In Blender console or via addon UI:
import bld_remote
bld_remote.start_mcp_service()
```

### Background Mode  
```bash
# Using external script (recommended)
python3 scripts/start_bld_remote_background.py --port 6688

# Or with environment variables
export BLD_REMOTE_MCP_PORT=6688
export BLD_REMOTE_MCP_START_NOW=true
blender --background --python -c "import bpy; bpy.ops.preferences.addon_enable(module='bld_remote_mcp')"
```

### Client Connection
```python
import socket, json

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('127.0.0.1', 6688))

command = {
    "message": "Hello Blender!",
    "code": "import bpy; bpy.ops.mesh.primitive_cube_add()"
}

sock.sendall(json.dumps(command).encode('utf-8'))
response = json.loads(sock.recv(4096).decode('utf-8'))
sock.close()

print(response)  # {'response': 'OK', 'message': 'Code execution scheduled', ...}
```

## Future Improvements

### Potential Enhancements
1. **MCP Protocol Support**: Add full MCP JSON-RPC 2.0 protocol
2. **Authentication**: Basic API key or token-based auth
3. **WebSocket Support**: For real-time bidirectional communication
4. **GUI Panel**: N-panel interface for server control
5. **Logging Options**: File-based logging with rotation

### Architecture Considerations
- Keep external script pattern for background mode reliability
- Consider FastMCP integration for full MCP protocol support
- Maintain simplicity - avoid complex internal state management
- Follow proven patterns from blender-echo-plugin

## Conclusion

The BLD Remote MCP implementation successfully demonstrates that:

1. **Simple patterns work**: Echo-plugin approach > complex modular architectures
2. **External management**: Required for reliable background mode operation  
3. **Manual event loops**: Necessary for asyncio integration in background mode
4. **Environment configuration**: Clean way to control auto-start behavior
5. **Thread-safe execution**: Critical for Blender Python API operations

The implementation provides a solid foundation for Blender remote control that works reliably in both GUI and background modes, following proven patterns and avoiding common pitfalls discovered during development.

**Key Success Metric**: Both GUI and background modes tested successfully with proper server lifecycle management and clean shutdown procedures.