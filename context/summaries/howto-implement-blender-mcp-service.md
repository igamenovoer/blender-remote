# HEADER
- **Created**: 2025-07-07 14:28:00
- **Modified**: 2025-07-08 16:20:00
- **Summary**: Implementation guide for Blender MCP services covering architecture, FastMCP integration, and background mode execution patterns.

# How to Implement Blender MCP Service

## Architecture Overview

Based on the blender-mcp reference implementation, the system consists of two main components:

1. **Blender Addon**: Creates a socket server inside Blender to receive and execute commands
2. **MCP Server**: FastMCP-based server that implements MCP protocol and connects to the Blender addon

```
MCP Client (Claude) <--MCP--> MCP Server <--Socket--> Blender Addon <--bpy--> Blender
```

## 1. Creating a Running Service in Blender

### Blender Addon Structure

```python
# Essential addon structure
bl_info = {
    "name": "Your MCP Addon",
    "author": "Author",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > YourTab",
    "description": "Blender MCP integration",
    "category": "Interface",
}

class BlenderMCPServer:
    def __init__(self, host='localhost', port=9876):
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.server_thread = None
```

### Key Components for Service Creation

**1. Socket Server in Separate Thread**
```python
def start(self):
    if self.running:
        return
    
    self.running = True
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.socket.bind((self.host, self.port))
    self.socket.listen(1)
    
    # CRITICAL: Use daemon thread to avoid blocking Blender
    self.server_thread = threading.Thread(target=self._server_loop)
    self.server_thread.daemon = True
    self.server_thread.start()
```

**2. Main Thread Execution Pattern**
```python
def _handle_client(self, client):
    # Handle in separate thread
    def execute_wrapper():
        try:
            response = self.execute_command(command)
            client.sendall(json.dumps(response).encode('utf-8'))
        except Exception as e:
            # Handle errors
            pass
        return None  # IMPORTANT: Return None for timers
    
    # CRITICAL: Execute in main thread using timers
    bpy.app.timers.register(execute_wrapper, first_interval=0.0)
```

**3. Command Execution Framework**
```python
def execute_command(self, command):
    cmd_type = command.get("type")
    params = command.get("params", {})
    
    handlers = {
        "get_scene_info": self.get_scene_info,
        "execute_code": self.execute_code,
        # Add more handlers...
    }
    
    handler = handlers.get(cmd_type)
    if handler:
        result = handler(**params)
        return {"status": "success", "result": result}
    else:
        return {"status": "error", "message": f"Unknown command: {cmd_type}"}
```

**4. Essential Blender Operations**
```python
def get_scene_info(self):
    """Get current scene information"""
    return {
        "name": bpy.context.scene.name,
        "object_count": len(bpy.context.scene.objects),
        "objects": [{"name": obj.name, "type": obj.type} 
                   for obj in bpy.context.scene.objects]
    }

def execute_code(self, code):
    """Execute arbitrary Python code"""
    namespace = {"bpy": bpy}
    exec(code, namespace)
    return {"executed": True}
```

**5. Addon Registration**
```python
def register():
    # Register properties
    bpy.types.Scene.mcp_port = bpy.props.IntProperty(
        name="Port", default=9876, min=1024, max=65535
    )
    bpy.types.Scene.mcp_server_running = bpy.props.BoolProperty(
        name="Server Running", default=False
    )
    
    # Register UI classes
    bpy.utils.register_class(MCPPanel)
    bpy.utils.register_class(StartServerOperator)

def unregister():
    # Stop server if running
    if hasattr(bpy.types, "mcp_server") and bpy.types.mcp_server:
        bpy.types.mcp_server.stop()
    
    # Unregister classes and properties
    del bpy.types.Scene.mcp_port
    # ... unregister other components
```

## 2. Python MCP Server Implementation

### MCP Server Structure with FastMCP

```python
from mcp.server.fastmcp import FastMCP, Context
import socket
import json

# Global connection management
_blender_connection = None

@dataclass
class BlenderConnection:
    host: str
    port: int
    sock: socket.socket = None
    
    def connect(self) -> bool:
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            return True
        except Exception as e:
            self.sock = None
            return False
    
    def send_command(self, command_type: str, params: dict = None) -> dict:
        command = {"type": command_type, "params": params or {}}
        
        self.sock.sendall(json.dumps(command).encode('utf-8'))
        response_data = self._receive_response()
        response = json.loads(response_data.decode('utf-8'))
        
        if response.get("status") == "error":
            raise Exception(response.get("message"))
        
        return response.get("result", {})
```

### Tool Implementation Pattern

```python
# Create MCP server instance
mcp = FastMCP("BlenderMCP", description="Blender integration via MCP")

def get_blender_connection():
    global _blender_connection
    if _blender_connection is None:
        _blender_connection = BlenderConnection(host="localhost", port=9876)
        if not _blender_connection.connect():
            raise Exception("Could not connect to Blender addon")
    return _blender_connection

@mcp.tool()
def get_scene_info(ctx: Context) -> str:
    """Get detailed information about the current Blender scene"""
    try:
        blender = get_blender_connection()
        result = blender.send_command("get_scene_info")
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def execute_blender_code(ctx: Context, code: str) -> str:
    """Execute Python code in Blender"""
    try:
        blender = get_blender_connection()
        result = blender.send_command("execute_code", {"code": code})
        return f"Code executed: {result.get('result', '')}"
    except Exception as e:
        return f"Error: {str(e)}"
```

## 3. Communication Protocol

### Message Format

**Request (MCP Server → Blender):**
```json
{
    "type": "command_name",
    "params": {
        "param1": "value1",
        "param2": "value2"
    }
}
```

**Response (Blender → MCP Server):**
```json
{
    "status": "success|error",
    "result": { /* command result data */ },
    "message": "error message if status is error"
}
```

### Error Handling

```python
def send_command(self, command_type: str, params: dict = None) -> dict:
    try:
        # Send command
        command = {"type": command_type, "params": params or {}}
        self.sock.sendall(json.dumps(command).encode('utf-8'))
        
        # Receive response with timeout
        self.sock.settimeout(15.0)
        response_data = self._receive_full_response()
        response = json.loads(response_data.decode('utf-8'))
        
        if response.get("status") == "error":
            raise Exception(response.get("message"))
        
        return response.get("result", {})
    
    except socket.timeout:
        self.sock = None  # Invalidate connection
        raise Exception("Timeout - try simplifying your request")
    except Exception as e:
        self.sock = None  # Invalidate connection  
        raise Exception(f"Communication error: {str(e)}")
```

## 4. Essential Blender Python API Usage

### Core Modules for MCP Integration

```python
import bpy              # Main Blender Python API
import bpy.context      # Current context (scene, objects, etc.)
import bpy.data         # All Blender data (meshes, materials, etc.)
import bpy.ops          # Operations (creating objects, etc.)
import bpy.app.timers   # Timer system for main thread execution
import mathutils        # Math utilities (Vector, Matrix, etc.)
```

### Key Patterns

**1. Context Access:**
```python
# Current scene
scene = bpy.context.scene

# Active object
obj = bpy.context.active_object

# Selected objects
selected = bpy.context.selected_objects

# All objects in scene
all_objects = bpy.context.scene.objects
```

**2. Data Access:**
```python
# All meshes
meshes = bpy.data.meshes

# All materials
materials = bpy.data.materials

# Get specific object by name
obj = bpy.data.objects.get("ObjectName")
```

**3. Operations:**
```python
# Add objects
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))

# Import/Export
bpy.ops.import_scene.gltf(filepath="path/to/file.gltf")
bpy.ops.export_scene.gltf(filepath="path/to/export.gltf")
```

**4. Threading Considerations:**
```python
# ALWAYS execute bpy operations in main thread
def safe_blender_operation():
    # Blender operations here
    bpy.ops.mesh.primitive_cube_add()
    return None  # Important for timers

# Schedule from background thread
bpy.app.timers.register(safe_blender_operation, first_interval=0.0)
```

## 5. Implementation Best Practices

### Connection Management
- Use persistent global connection
- Implement connection validation and reconnection
- Handle socket timeouts gracefully
- Invalidate connection on errors

### Thread Safety
- Socket server runs in background thread
- Command execution MUST happen in main thread via `bpy.app.timers`
- Never call `bpy.*` from background threads

### Error Handling
- Comprehensive exception handling at all levels
- Meaningful error messages for users
- Connection state management
- Graceful degradation

### Performance
- Limit data size in responses (e.g., max 10-20 objects)
- Use timeouts to prevent hanging
- Efficient JSON serialization
- Connection pooling if needed

### Security
- Validate all inputs
- Sanitize code execution (if allowing arbitrary code)
- Rate limiting considerations
- Safe file operations

## 6. Deployment Considerations

### Addon Installation
- Single `addon.py` file for easy installation
- Proper registration/unregistration
- User-friendly UI panel
- Clear status indicators

### MCP Server Distribution
- Package as standalone Python package
- Use `uvx` or similar for easy installation
- FastMCP for MCP protocol handling
- Clear configuration instructions

### Integration Testing
- Test addon/server communication
- Verify MCP protocol compliance
- Test error scenarios
- Performance under load

This guide provides the foundation for implementing a robust Blender MCP service based on proven patterns from the reference implementation.