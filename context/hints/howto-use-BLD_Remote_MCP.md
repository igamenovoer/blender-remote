# HEADER
- **Created**: 2025-01-08 22:30:00
- **Modified**: 2025-01-08 22:30:00
- **Summary**: Comprehensive usage guide for BLD Remote MCP plugin covering installation, configuration, API usage, and testing strategies.

# How to Use BLD Remote MCP

## Overview

BLD Remote MCP is a minimal Blender MCP (Model Context Protocol) service that enables remote control of Blender through a simple TCP server. Unlike the reference BlenderAutoMCP implementation, BLD Remote MCP is specifically designed to work reliably in both GUI and background modes, making it suitable for headless deployments and automated workflows.

**Key Features:**
- ✅ **Background Mode Compatible**: Works in `blender --background` unlike BlenderAutoMCP
- ✅ **Simple JSON Protocol**: No complex MCP JSON-RPC overhead
- ✅ **Environment Configuration**: Clean auto-start via environment variables
- ✅ **Python API**: 7 core functions for programmatic control
- ✅ **Proven Architecture**: Based on battle-tested blender-echo-plugin patterns

## Installation

### Prerequisites
- Blender 4.4.3 (path: `/apps/blender-4.4.3-linux-x64/blender`)
- Python 3.11+ (included with Blender)
- Network access to localhost ports 6688-6799

### Plugin Installation

The plugin is automatically installed at:
```
/home/igamenovoer/.config/blender/4.4/scripts/addons/bld_remote_mcp/
```

**Manual Installation** (if needed):
```bash
# Copy plugin to Blender addons directory
cp -r /workspace/code/blender-remote/blender_addon/bld_remote_mcp/ \
      /home/igamenovoer/.config/blender/4.4/scripts/addons/

# Verify installation
ls -la /home/igamenovoer/.config/blender/4.4/scripts/addons/bld_remote_mcp/
```

## Configuration

### Environment Variables

BLD Remote MCP uses two environment variables for configuration:

| Variable | Default | Description |
|----------|---------|-------------|
| `BLD_REMOTE_MCP_PORT` | `6688` | TCP port for the MCP service |
| `BLD_REMOTE_MCP_START_NOW` | `false` | Auto-start service on addon load |

**Environment Variable Usage:**
```bash
# Configure port
export BLD_REMOTE_MCP_PORT=6700

# Enable auto-start
export BLD_REMOTE_MCP_START_NOW=true
# or
export BLD_REMOTE_MCP_START_NOW=1
```

### Service Configuration

**Default Configuration:**
- **Port**: 6688
- **Host**: 127.0.0.1 (localhost only)
- **Protocol**: JSON over TCP
- **Auto-start**: Disabled
- **Background Mode**: Supported

## Python API Reference

The plugin provides a simple Python API accessible as `import bld_remote`:

### Core Functions

#### `get_status()`
Returns detailed service status information.

```python
import bld_remote
status = bld_remote.get_status()
print(status)
# Output: {'running': True, 'port': 6688, 'connections': 0, 'uptime': 125.3}
```

#### `start_mcp_service()`
Start the MCP service. Raises exception on failure.

```python
import bld_remote
try:
    bld_remote.start_mcp_service()
    print("✅ Service started successfully")
except Exception as e:
    print(f"❌ Service failed to start: {e}")
```

#### `stop_mcp_service()`
Stop the MCP service, disconnecting all clients forcefully.

```python
import bld_remote
bld_remote.stop_mcp_service()
print("🛑 Service stopped")
```

#### `is_mcp_service_up()`
Check if MCP service is running.

```python
import bld_remote
if bld_remote.is_mcp_service_up():
    print("✅ Service is running")
else:
    print("❌ Service is not running")
```

#### `get_startup_options()`
Return information about environment variables and configuration.

```python
import bld_remote
options = bld_remote.get_startup_options()
print(options)
# Output: {'BLD_REMOTE_MCP_PORT': '6688 (default)', 'BLD_REMOTE_MCP_START_NOW': 'false (default)', ...}
```

#### `set_mcp_service_port(port_number)`
Set port number (only when service is stopped).

```python
import bld_remote
if not bld_remote.is_mcp_service_up():
    bld_remote.set_mcp_service_port(6700)
    print("✅ Port set to 6700")
else:
    print("❌ Cannot change port while service is running")
```

#### `get_mcp_service_port()`
Return the current configured port.

```python
import bld_remote
port = bld_remote.get_mcp_service_port()
print(f"Current port: {port}")
# Output: Current port: 6688
```

## Usage Patterns

### GUI Mode Usage

#### Manual Service Control

**Starting Blender:**
```bash
# Start Blender normally
/apps/blender-4.4.3-linux-x64/blender
```

**In Blender Console:**
```python
# Enable addon (if not auto-enabled)
import bpy
bpy.ops.preferences.addon_enable(module='bld_remote_mcp')

# Start service manually
import bld_remote
bld_remote.start_mcp_service()

# Check status
print(bld_remote.get_status())
```

#### Auto-Start Configuration

**Environment Setup:**
```bash
# Configure auto-start
export BLD_REMOTE_MCP_PORT=6688
export BLD_REMOTE_MCP_START_NOW=true

# Start Blender - service starts automatically
/apps/blender-4.4.3-linux-x64/blender
```

**Verification:**
```python
# In Blender console
import bld_remote
print(f"Service running: {bld_remote.is_mcp_service_up()}")
print(f"Port: {bld_remote.get_mcp_service_port()}")
```

### Background Mode Usage

#### Method 1: External Script (Recommended)

**Using the external script:**
```bash
# Start with specific port
python3 /workspace/code/blender-remote/scripts/start_bld_remote_background.py --port 6688

# Or use default port (6688)
python3 /workspace/code/blender-remote/scripts/start_bld_remote_background.py
```

**Script Features:**
- Finds available port automatically
- Manages Blender process lifecycle
- Handles graceful shutdown
- Provides connection testing

#### Method 2: Environment Variables

**Direct Blender startup:**
```bash
# Configure environment
export BLD_REMOTE_MCP_PORT=6688
export BLD_REMOTE_MCP_START_NOW=true

# Start Blender in background with addon enable
/apps/blender-4.4.3-linux-x64/blender --background --python -c "
import bpy
bpy.ops.preferences.addon_enable(module='bld_remote_mcp')
import bld_remote_mcp.async_loop as async_loop
async_loop.ensure_async_loop()

# Keep Blender alive
import time
while True:
    stop_loop = async_loop.kick_async_loop()
    if stop_loop:
        break
    time.sleep(0.01)
"
```

## Client Connection

### Protocol Format

BLD Remote MCP uses a simple JSON protocol:

**Request Format:**
```json
{
    "message": "Optional message string",
    "code": "Python code to execute in Blender"
}
```

**Response Format:**
```json
{
    "response": "OK" | "ERROR",
    "message": "Status message",
    "source": "tcp://127.0.0.1:6688"
}
```

### Basic Client Examples

#### Python Socket Client

```python
import socket
import json

def send_command(host='127.0.0.1', port=6688, message="", code=""):
    """Send command to BLD Remote MCP service"""
    try:
        # Create socket connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        
        # Prepare command
        command = {
            "message": message,
            "code": code
        }
        
        # Send command
        sock.sendall(json.dumps(command).encode('utf-8'))
        
        # Receive response
        response = json.loads(sock.recv(4096).decode('utf-8'))
        sock.close()
        
        return response
        
    except Exception as e:
        return {"response": "ERROR", "message": str(e)}

# Usage examples
response = send_command(
    message="Hello Blender!",
    code="import bpy; print(f'Scene: {bpy.context.scene.name}')"
)
print(response)
```

#### Blender Scene Operations

```python
# Add a cube
response = send_command(
    message="Add cube",
    code="""
import bpy
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 2))
cube = bpy.context.active_object
cube.name = "RemoteCube"
print(f"Added cube: {cube.name}")
"""
)

# Get scene information
response = send_command(
    message="Get scene info",
    code="""
import bpy
scene = bpy.context.scene
objects = list(scene.objects)
print(f"Scene: {scene.name}")
print(f"Objects: {len(objects)}")
for obj in objects:
    print(f"  - {obj.name} ({obj.type})")
"""
)

# Modify object
response = send_command(
    message="Move cube",
    code="""
import bpy
cube = bpy.data.objects.get("RemoteCube")
if cube:
    cube.location = (1, 1, 3)
    print(f"Moved cube to: {cube.location}")
else:
    print("Cube not found")
"""
)
```

### Advanced Client Patterns

#### Using BlenderMCPClient (Compatibility Layer)

```python
# Add auto_mcp_remote to path for compatibility
import sys
sys.path.insert(0, '/workspace/code/blender-remote/context/refcode')

from auto_mcp_remote import BlenderMCPClient

# Connect to BLD Remote MCP
client = BlenderMCPClient(host="localhost", port=6688, timeout=30.0)

# Test connection
if client.test_connection():
    print("✅ Connected to BLD Remote MCP")
    
    # Execute Python code
    result = client.execute_python("""
import bpy
scene_name = bpy.context.scene.name
object_count = len(bpy.context.scene.objects)
print(f"Scene: {scene_name}, Objects: {object_count}")
""")
    
    print(f"Result: {result}")
else:
    print("❌ Connection failed")
```

#### Using BlenderSceneManager

```python
from auto_mcp_remote import BlenderSceneManager

# Create scene manager
scene = BlenderSceneManager(client)

# Get scene summary
summary = scene.get_scene_summary()
print(f"Scene: {summary['name']}, Objects: {summary['object_count']}")

# Add and manipulate objects
cube_name = scene.add_cube(location=(0, 0, 2), size=1.0, name="TestCube")
print(f"Added cube: {cube_name}")

# Move object
moved = scene.move_object(cube_name, location=(1, 1, 3))
print(f"Moved cube: {moved}")

# Clean up
deleted = scene.delete_object(cube_name)
print(f"Deleted cube: {deleted}")
```

## Testing and Validation

### Built-in Testing Framework

BLD Remote MCP includes a comprehensive testing framework based on the proven `auto_mcp_remote` interface:

#### Quick Smoke Test

```python
# Run basic functionality test
exec(open('/workspace/code/blender-remote/tests/smoke_test.py').read())
```

#### Comprehensive Test Suite

```python
# Run full test suite
exec(open('/workspace/code/blender-remote/tests/test_bld_remote_mcp.py').read())
```

#### Dual Service Testing (GUI Mode)

```python
# Test both BLD Remote MCP and BlenderAutoMCP simultaneously
exec(open('/workspace/code/blender-remote/tests/run_dual_service_tests.py').read())
```

### Manual Testing Procedures

#### Test 1: Basic Connectivity

```python
import socket
import json

def test_connectivity(port=6688):
    """Test basic service connectivity"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0
    except:
        return False

# Test connectivity
if test_connectivity():
    print("✅ Service is responding")
else:
    print("❌ Service is not responding")
```

#### Test 2: Python Code Execution

```python
def test_code_execution():
    """Test Python code execution capability"""
    response = send_command(
        message="Test execution",
        code="""
import bpy
result = f"Blender version: {bpy.app.version_string}"
print(result)
"""
    )
    
    if response.get("response") == "OK":
        print("✅ Code execution successful")
        return True
    else:
        print(f"❌ Code execution failed: {response}")
        return False

test_code_execution()
```

#### Test 3: Blender API Access

```python
def test_blender_api():
    """Test Blender API access"""
    response = send_command(
        message="Test Blender API",
        code="""
import bpy
scene = bpy.context.scene
print(f"Scene name: {scene.name}")
print(f"Object count: {len(scene.objects)}")
for obj in scene.objects:
    print(f"  - {obj.name} ({obj.type}) at {obj.location}")
"""
    )
    
    return response.get("response") == "OK"

if test_blender_api():
    print("✅ Blender API access successful")
else:
    print("❌ Blender API access failed")
```

### Performance Testing

#### Concurrent Connections Test

```python
import threading
import time

def concurrent_test(port=6688, num_clients=5):
    """Test multiple concurrent connections"""
    results = []
    
    def single_client_test(client_id):
        try:
            response = send_command(
                port=port,
                message=f"Client {client_id}",
                code=f"print(f'Client {client_id} executed successfully')"
            )
            results.append(response.get("response") == "OK")
        except Exception as e:
            print(f"Client {client_id} failed: {e}")
            results.append(False)
    
    # Start concurrent clients
    threads = []
    for i in range(num_clients):
        thread = threading.Thread(target=single_client_test, args=(i,))
        threads.append(thread)
        thread.start()
        time.sleep(0.1)  # Small delay between connections
    
    # Wait for completion
    for thread in threads:
        thread.join()
    
    success_count = sum(results)
    print(f"Concurrent test: {success_count}/{num_clients} clients successful")
    return success_count == num_clients

# Run concurrent test
concurrent_test()
```

## Troubleshooting

### Common Issues

#### Issue 1: Service Won't Start

**Symptoms:**
- `start_mcp_service()` raises exception
- Port binding errors
- Permission denied errors

**Solutions:**
```python
# Check if port is available
import socket
def check_port(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('127.0.0.1', port))
        sock.close()
        return True
    except OSError:
        return False

# Find available port
for port in range(6688, 6800):
    if check_port(port):
        print(f"Available port: {port}")
        break

# Set new port and try again
import bld_remote
bld_remote.set_mcp_service_port(port)
bld_remote.start_mcp_service()
```

#### Issue 2: Background Mode Fails

**Symptoms:**
- Service starts but doesn't respond
- Blender exits immediately
- Context access errors

**Solutions:**
```bash
# Use external script (recommended)
python3 /workspace/code/blender-remote/scripts/start_bld_remote_background.py --port 6700

# Or check environment setup
export BLD_REMOTE_MCP_PORT=6700
export BLD_REMOTE_MCP_START_NOW=true
echo "Environment configured"
```

#### Issue 3: Connection Timeouts

**Symptoms:**
- Client connections timeout
- Service appears running but unresponsive
- Slow response times

**Solutions:**
```python
# Increase client timeout
client = BlenderMCPClient(host="localhost", port=6688, timeout=60.0)

# Check service status
import bld_remote
print(bld_remote.get_status())

# Restart service if needed
bld_remote.stop_mcp_service()
time.sleep(2)
bld_remote.start_mcp_service()
```

#### Issue 4: Python Code Execution Fails

**Symptoms:**
- Code doesn't execute
- Blender API errors
- Import failures

**Solutions:**
```python
# Test basic execution
response = send_command(
    code="""
try:
    import bpy
    print("✅ bpy imported successfully")
    print(f"Blender version: {bpy.app.version_string}")
except Exception as e:
    print(f"❌ bpy import failed: {e}")
"""
)

# Check execution environment
response = send_command(
    code="""
import sys
print(f"Python path: {sys.path[:3]}")
print(f"Current working directory: {os.getcwd()}")
"""
)
```

### Debug Commands

#### Service Status Check

```python
# Complete service diagnostic
import bld_remote

print("=== BLD Remote MCP Diagnostic ===")
print(f"Service running: {bld_remote.is_mcp_service_up()}")
print(f"Port: {bld_remote.get_mcp_service_port()}")
print(f"Status: {bld_remote.get_status()}")
print(f"Startup options: {bld_remote.get_startup_options()}")
```

#### Network Diagnostic

```bash
# Check if port is listening
netstat -tlnp | grep 6688

# Check for Blender processes
ps aux | grep blender | grep -v grep

# Kill existing Blender processes
pkill -f blender
```

#### Log Analysis

```python
# Check for service logs in Blender console
# Look for messages starting with [BLD Remote]

# Enable verbose logging if needed
import bld_remote_mcp.utils as utils
utils.set_log_level('DEBUG')
```

## Comparison with BlenderAutoMCP

### Feature Comparison

| Feature | BLD Remote MCP | BlenderAutoMCP |
|---------|---------------|----------------|
| **Background Mode** | ✅ Fully supported | ❌ Limited/untested |
| **Protocol** | Simple JSON | Full MCP JSON-RPC |
| **Dependencies** | None | Multiple 3rd party |
| **Port** | 6688 (default) | 9876 (default) |
| **Auto-start** | Environment variable | Environment variable |
| **3rd Party Assets** | ❌ No | ✅ PolyHaven, Sketchfab |
| **Architecture** | Simple TCP server | Modular MCP server |

### Usage Compatibility

Both services can run simultaneously without conflict:

```python
# Connect to both services
bld_remote_client = BlenderMCPClient(port=6688)  # Our service
auto_mcp_client = BlenderMCPClient(port=9876)    # Reference service

# Cross-validate results
bld_scene = bld_remote_client.get_scene_info()
auto_scene = auto_mcp_client.get_scene_info()

print(f"BLD Remote: {bld_scene}")
print(f"Auto MCP: {auto_scene}")
```

### Migration from BlenderAutoMCP

```python
# Replace BlenderAutoMCP calls
# OLD: BlenderAutoMCP on port 9876
# NEW: BLD Remote MCP on port 6688

# Change connection
# OLD:
# client = BlenderMCPClient(port=9876)
# NEW:
client = BlenderMCPClient(port=6688)

# All other API calls remain the same
result = client.execute_python("print('Hello World')")
```

## Best Practices

### Development Workflow

1. **Use GUI Mode for Development**: More reliable for testing and debugging
2. **Test Both Modes**: Validate functionality in both GUI and background modes
3. **Port Management**: Use dynamic port selection to avoid conflicts
4. **Error Handling**: Always wrap service calls in try-catch blocks
5. **Service Lifecycle**: Properly start/stop services during development

### Production Deployment

1. **Background Mode**: Use external script for production deployments
2. **Port Configuration**: Set explicit port via environment variables
3. **Monitoring**: Implement health checks and service monitoring
4. **Graceful Shutdown**: Handle signal interrupts for clean shutdown
5. **Resource Management**: Monitor memory and CPU usage

### Code Examples

```python
# Production-ready service management
import bld_remote
import time
import signal
import sys

def signal_handler(signum, frame):
    """Handle graceful shutdown"""
    print("Shutting down service...")
    if bld_remote.is_mcp_service_up():
        bld_remote.stop_mcp_service()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Start service with error handling
try:
    bld_remote.start_mcp_service()
    print("✅ Service started successfully")
    
    # Keep service running
    while True:
        if not bld_remote.is_mcp_service_up():
            print("⚠️ Service stopped unexpectedly")
            break
        time.sleep(1)
        
except Exception as e:
    print(f"❌ Service failed: {e}")
    sys.exit(1)
```

This comprehensive guide provides everything needed to effectively use BLD Remote MCP in both development and production environments, with extensive examples and troubleshooting guidance.