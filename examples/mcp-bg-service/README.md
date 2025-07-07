# BLD Remote MCP Background Service Examples

This directory contains practical examples demonstrating how to use the BLD Remote MCP background service for remote Blender control.

## Overview

The BLD Remote MCP service provides a simple TCP-based interface to control Blender remotely in both GUI and background modes. These examples show various use cases from basic connections to advanced automation workflows.

## Prerequisites

1. **BLD Remote MCP Addon Installed**:
   ```bash
   # Copy addon to Blender addons directory
   cp -r ../../blender_addon/bld_remote_mcp ~/.config/blender/4.4/scripts/addons/
   ```

2. **Python Dependencies** (for examples):
   ```bash
   pip install pillow requests  # Optional, for advanced examples
   ```

3. **Blender Executable**: Set path in environment
   ```bash
   export BLENDER_EXEC_PATH="/path/to/blender"
   ```

## Quick Start

### Start Background Service
```bash
# Option 1: Using our background script
python3 ../../scripts/start_bld_remote_background.py --port 6688

# Option 2: Using example starter
python3 start_service.py --port 6688

# Option 3: Manual with environment variables
export BLD_REMOTE_MCP_PORT=6688
export BLD_REMOTE_MCP_START_NOW=true
blender --background
```

### Test Connection
```bash
# Run basic connection test
python3 01_basic_connection.py

# Execute some Blender code
python3 02_code_execution.py
```

## Example Categories

### Basic Usage
- **`01_basic_connection.py`** - Simple connection and messaging
- **`02_code_execution.py`** - Execute Blender Python code remotely
- **`start_service.py`** - Start background service with options

### Scene Manipulation
- **`03_scene_manipulation.py`** - Create objects, materials, lighting
- **`04_batch_processing.py`** - Process multiple operations efficiently
- **`06_file_operations.py`** - Load/save Blender files remotely

### Automation Workflows
- **`05_health_monitoring.py`** - Service health checks and monitoring
- **`07_render_automation.py`** - Automated rendering workflows
- **`08_asset_generation.py`** - Procedural asset creation
- **`09_batch_converter.py`** - Convert multiple files

### Utilities
- **`utils.py`** - Shared utilities and helper functions
- **`config.py`** - Configuration management

## Message Protocol

All examples use the simple JSON protocol:

```python
# Command format
{
    "message": "Optional description",
    "code": "bpy.ops.mesh.primitive_cube_add()"
}

# Response format  
{
    "response": "OK",
    "message": "Code execution scheduled",
    "source": "tcp://127.0.0.1:6688"
}
```

## Environment Variables

- **`BLD_REMOTE_MCP_PORT`**: Service port (default: 6688)
- **`BLD_REMOTE_MCP_START_NOW`**: Auto-start service (true/false)
- **`BLENDER_EXEC_PATH`**: Path to Blender executable

## Common Patterns

### Connection Management
```python
from utils import BldRemoteClient

with BldRemoteClient(port=6688) as client:
    response = client.execute_code("print('Hello Blender!')")
    print(response)
```

### Error Handling
```python
try:
    client = BldRemoteClient()
    result = client.execute_code("bpy.ops.mesh.primitive_cube_add()")
    if result['response'] != 'OK':
        print(f"Command failed: {result['message']}")
except ConnectionError:
    print("Could not connect to Blender service")
```

### Batch Operations
```python
commands = [
    "bpy.ops.mesh.primitive_cube_add()",
    "bpy.ops.mesh.primitive_uv_sphere_add()",
    "bpy.ops.mesh.primitive_cylinder_add()"
]

for cmd in commands:
    client.execute_code(cmd)
```

## Troubleshooting

### Service Not Starting
```bash
# Check if Blender is running
ps aux | grep blender

# Check if port is listening
netstat -tlnp | grep 6688

# Check Blender addon is enabled
python3 -c "
import socket, json
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    sock.connect(('127.0.0.1', 6688))
    print('Service is running')
except:
    print('Service not available')
finally:
    sock.close()
"
```

### Connection Issues
1. **Port conflicts**: Try different port with `--port` option
2. **Firewall**: Ensure localhost connections allowed
3. **Blender crashes**: Check Blender console for errors
4. **Addon not loaded**: Verify addon copied to correct directory

### Performance Tips
1. **Batch commands**: Group related operations
2. **Async clients**: Use threading for multiple concurrent operations
3. **Keep connections short**: Close connections after use
4. **Monitor memory**: Restart service periodically for long-running workflows

## Security Notes

⚠️ **Security Warning**: The service executes arbitrary Python code. Only use on trusted networks.

- Service binds to localhost (127.0.0.1) only
- No authentication implemented
- Suitable for development and local automation
- NOT recommended for production or network exposure

## Contributing Examples

When adding new examples:
1. Follow the naming convention: `##_descriptive_name.py`
2. Include docstring with purpose and usage
3. Add error handling and user feedback
4. Update this README with description
5. Test in both GUI and background modes
6. Keep examples focused and practical

## Related Documentation

- **Implementation Guide**: `../../context/summaries/bld-remote-mcp-implementation-complete.md`
- **Background Patterns**: `../../context/summaries/blender-background-mode-patterns-comparison.md`
- **Project Goal**: `../../context/tasks/blender-bg-mcp/goal.md`