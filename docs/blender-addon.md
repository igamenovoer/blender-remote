# Blender Add-on

The Blender Remote add-on enables remote control capabilities within Blender by running a server that listens for commands from external clients.

## Installation

### Download and Install

1. Download the latest add-on from the [releases page](https://github.com/igamenovoer/blender-remote/releases)
2. In Blender, go to **Edit → Preferences → Add-ons**
3. Click **Install...** and select the downloaded file
4. Enable the add-on by checking the box next to "Remote Control"

### From Source

For development or latest features:

1. Clone the repository:
   ```bash
   git clone https://github.com/igamenovoer/blender-remote.git
   ```

2. In Blender preferences, click **Install...** and navigate to:
   ```
   blender-remote/blender_addon/
   ```

3. Select the entire folder or create a ZIP file from the contents

## Configuration

### Add-on Preferences

Access add-on preferences through **Edit → Preferences → Add-ons → Remote Control**.

#### Network Settings

| Setting | Default | Description |
|---------|---------|-------------|
| **Host** | `127.0.0.1` | IP address to bind the server to |
| **Port** | `5555` | Port number for incoming connections |
| **Max Connections** | `10` | Maximum concurrent client connections |

#### Security Settings

| Setting | Default | Description |
|---------|---------|-------------|
| **Allow External** | `False` | Accept connections from other machines |
| **Require Auth** | `False` | Require authentication for connections |
| **API Key** | `(empty)` | Authentication key for secure connections |

#### Logging Settings

| Setting | Default | Description |
|---------|---------|-------------|
| **Log Level** | `INFO` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) |
| **Log to File** | `True` | Save logs to file |
| **Log File Path** | `~/.blender-remote/server.log` | Location for log files |

### Service Control

#### Starting the Service

**Manual Start:**
1. In add-on preferences, click **Start Service**
2. Verify the status shows "Running" with green indicator

**Auto-start:**
1. Enable **Start on Startup** in preferences
2. Service will automatically start when Blender launches

#### Stopping the Service

- Click **Stop Service** in add-on preferences
- Or restart Blender

### Status Monitoring

The add-on provides real-time status information:

- **Connection Status**: Shows if server is running
- **Client Count**: Number of connected clients
- **Uptime**: How long the service has been running
- **Last Activity**: Timestamp of most recent command

## Features

### Remote Command Execution

The add-on accepts and executes various types of commands:

#### Scene Operations
- Object creation, modification, and deletion
- Material and texture management
- Camera and lighting control
- Rendering operations

#### File Operations
- Scene saving and loading
- Import/export of external files
- Project management

#### Real-time Feedback
- Command results and status updates
- Error reporting and debugging information
- Progress updates for long-running operations

### MCP Protocol Support

Built-in Model Context Protocol (MCP) server for AI assistant integration:

- **Structured Commands**: Well-defined command schema
- **Type Safety**: Parameter validation and type checking
- **Documentation**: Self-documenting API endpoints
- **Extensibility**: Easy addition of new commands

### Security Features

#### Access Control
- IP-based connection filtering
- Optional authentication with API keys
- Command permission levels

#### Audit Logging
- All commands logged with timestamps
- Client identification and tracking
- Security event monitoring

## Command Protocol

### Command Structure

Commands are sent as JSON messages:

```json
{
  "id": "unique_command_id",
  "method": "create_primitive",
  "params": {
    "primitive_type": "cube",
    "location": [0, 0, 1],
    "scale": [2, 2, 2]
  }
}
```

### Response Format

Responses include status and result data:

```json
{
  "id": "unique_command_id",
  "success": true,
  "result": {
    "object_id": "cube_001",
    "name": "Cube"
  },
  "error": null
}
```

### Error Handling

Error responses provide detailed information:

```json
{
  "id": "unique_command_id",
  "success": false,
  "result": null,
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "Invalid primitive type: 'invalid_shape'",
    "details": {
      "parameter": "primitive_type",
      "valid_values": ["cube", "sphere", "cylinder", "cone", "torus", "plane"]
    }
  }
}
```

## Supported Commands

### Object Management

#### `create_primitive`
Create primitive objects (cube, sphere, cylinder, etc.)

**Parameters:**
- `primitive_type` (string): Type of primitive
- `location` (array): [x, y, z] position
- `rotation` (array): [x, y, z] rotation in radians
- `scale` (array): [x, y, z] scale factors
- `name` (string, optional): Object name

#### `delete_object`
Remove objects from scene

**Parameters:**
- `object_name` (string): Name of object to delete
- `object_id` (string, alternative): ID of object to delete

#### `transform_object`
Modify object transforms

**Parameters:**
- `object_name` (string): Target object
- `location` (array, optional): New location
- `rotation` (array, optional): New rotation
- `scale` (array, optional): New scale

### Material System

#### `create_material`
Create new material

**Parameters:**
- `name` (string): Material name
- `base_color` (array, optional): [r, g, b, a] color
- `metallic` (float, optional): Metallic value (0-1)
- `roughness` (float, optional): Roughness value (0-1)

#### `assign_material`
Apply material to object

**Parameters:**
- `object_name` (string): Target object
- `material_name` (string): Material to assign

### Lighting

#### `create_light`
Add light sources

**Parameters:**
- `light_type` (string): "SUN", "POINT", "SPOT", "AREA"
- `location` (array): Light position
- `power` (float): Light strength
- `color` (array, optional): [r, g, b] color

### Camera Control

#### `set_camera_transform`
Position and orient camera

**Parameters:**
- `location` (array): Camera position
- `rotation` (array): Camera rotation
- `target` (array, optional): Point to look at

### Rendering

#### `render_image`
Render current scene

**Parameters:**
- `output_path` (string): File path for rendered image
- `resolution` (array, optional): [width, height]
- `engine` (string, optional): "CYCLES", "EEVEE", "WORKBENCH"
- `samples` (integer, optional): Render samples

#### `render_animation`
Render animation sequence

**Parameters:**
- `output_directory` (string): Directory for frames
- `start_frame` (integer): First frame
- `end_frame` (integer): Last frame
- `resolution` (array, optional): [width, height]

### File Operations

#### `save_file`
Save current Blender file

**Parameters:**
- `filepath` (string): Path to save file
- `check_existing` (boolean, optional): Check if file exists

#### `open_file`
Load Blender file

**Parameters:**
- `filepath` (string): Path to file to open

## Development

### Adding Custom Commands

Extend the add-on with custom commands:

1. **Create Command Handler:**
   ```python
   # In blender_addon/commands/my_commands.py
   
   def my_custom_command(params):
       """Custom command implementation."""
       try:
           # Your command logic here
           result = perform_operation(params)
           return {"success": True, "result": result}
       except Exception as e:
           return {"success": False, "error": str(e)}
   ```

2. **Register Command:**
   ```python
   # In blender_addon/__init__.py
   
   from .commands.my_commands import my_custom_command
   
   COMMAND_REGISTRY = {
       "my_custom_command": my_custom_command,
       # ... other commands
   }
   ```

### Testing Commands

Test commands directly in Blender's Python console:

```python
import json
from blender_remote_addon import execute_command

# Test command
command = {
    "id": "test_001",
    "method": "create_primitive",
    "params": {"primitive_type": "cube"}
}

result = execute_command(command)
print(json.dumps(result, indent=2))
```

### Debugging

#### Enable Debug Logging

Set log level to DEBUG in add-on preferences to see detailed execution information.

#### Console Output

Monitor the Blender system console for real-time log messages:
- **Windows**: Window → Toggle System Console
- **macOS**: Start Blender from terminal
- **Linux**: Start Blender from terminal

#### Log Files

Check log files for persistent debugging information:
```
~/.blender-remote/server.log
```

## Performance Considerations

### Optimization Tips

1. **Batch Operations**: Group multiple commands to reduce overhead
2. **Efficient Queries**: Use object IDs instead of names when possible
3. **Resource Management**: Clean up temporary objects and materials
4. **Memory Usage**: Monitor memory for large scenes or long sessions

### Resource Limits

Be aware of Blender's limits:
- **Memory**: Large scenes may consume significant RAM
- **Processing**: Complex operations may block the interface
- **File Size**: Very large files may cause delays

### Monitoring

The add-on provides performance metrics:
- Command execution times
- Memory usage statistics  
- Connection status and throughput

## Troubleshooting

### Common Issues

#### Service Won't Start
- **Check Port**: Ensure port is not already in use
- **Firewall**: Verify firewall allows connections on the port
- **Permissions**: Check Blender has necessary system permissions

#### Connection Refused
- **Service Status**: Verify service is running in add-on preferences
- **Network**: Test network connectivity between client and server
- **Authentication**: Check API key if authentication is enabled

#### Commands Fail
- **Syntax**: Verify command JSON structure
- **Parameters**: Check parameter types and values
- **Context**: Ensure Blender is in appropriate mode for the operation

### Debug Tools

#### Connection Test
Use the built-in connection test tool in add-on preferences.

#### Command History
Review recent commands in the add-on's command history panel.

#### Network Monitor
Monitor network traffic to debug connection issues.

## Security Best Practices

### Network Security
- Use localhost (127.0.0.1) for local connections only
- Enable authentication for external connections
- Use VPN or SSH tunneling for remote access over internet

### Access Control
- Set strong API keys if authentication is enabled
- Regularly rotate API keys
- Monitor connection logs for suspicious activity

### File System Security
- Limit file operation permissions
- Validate file paths to prevent directory traversal
- Use sandboxed directories for temporary files

## Integration Examples

### CI/CD Pipeline
```yaml
# GitHub Actions example
steps:
  - name: Render Blender Scene
    run: |
      # Start Blender with remote service
      blender --background --python start_service.py &
      
      # Wait for service to start
      sleep 10
      
      # Execute render commands
      blender-remote open scene.blend
      blender-remote render output.png
```

### Docker Container
```dockerfile
FROM ubuntu:22.04

# Install Blender
RUN apt-get update && apt-get install -y blender

# Install blender-remote
RUN pip install blender-remote

# Copy add-on and auto-start script
COPY blender_addon/ /opt/blender-addons/
COPY startup.py /opt/

# Start Blender with remote service
CMD ["blender", "--background", "--python", "/opt/startup.py"]
```

### Web Service Integration
```python
# Flask web service example
from flask import Flask, request, jsonify
import blender_remote

app = Flask(__name__)
client = blender_remote.connect("localhost", 5555)

@app.route('/render', methods=['POST'])
def render_scene():
    data = request.json
    
    # Set up scene based on request
    client.clear_scene()
    client.create_primitive(data['object_type'])
    
    # Render and return result
    output_path = f"renders/{data['filename']}"
    client.render(output_path)
    
    return jsonify({"status": "success", "file": output_path})
```