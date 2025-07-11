# CLI Usage Examples

This document demonstrates the enhanced `blender-remote-cli` features.

## New Features Added

### 1. Logging Control in Configuration

The `init` command now includes logging level configuration:

```bash
# Initialize configuration with logging support
blender-remote-cli init /apps/blender-4.4.3-linux-x64/blender

# Output includes:
# 📊 Default log level: INFO
```

The generated config includes `log_level`:
```yaml
blender:
  version: 4.4.3
  exec_path: /apps/blender-4.4.3-linux-x64/blender
  root_dir: /apps/blender-4.4.3-linux-x64
  plugin_dir: /home/user/.config/blender/4.4/scripts/addons

mcp_service:
  default_port: 6688
  log_level: INFO  # NEW: Logging control
```

### 2. Configuration Management

Set logging level in config:
```bash
# Change default logging level
blender-remote-cli config set mcp_service.log_level=DEBUG

# Change default port  
blender-remote-cli config set mcp_service.default_port=7777

# Get specific configuration
blender-remote-cli config get mcp_service.log_level

# Get all configuration
blender-remote-cli config get
```

### 3. Scene File Support

Start Blender with a specific scene file:
```bash
# GUI mode with scene
blender-remote-cli start --scene /path/to/my_project.blend

# Background mode with scene
blender-remote-cli start --background --scene /path/to/my_project.blend
```

### 4. Runtime Log Level Override

Override the default logging level for a session:
```bash
# Debug level for troubleshooting
blender-remote-cli start --log-level DEBUG

# Only errors and critical messages
blender-remote-cli start --log-level ERROR

# Background mode with specific log level
blender-remote-cli start --background --log-level WARNING
```

### 5. Combined Usage Examples

```bash
# Production workflow: background mode, specific scene, minimal logging
blender-remote-cli start \
  --background \
  --scene /projects/animation.blend \
  --log-level ERROR \
  --port 8888

# Development workflow: GUI mode, debug logging
blender-remote-cli start \
  --scene /dev/test_scene.blend \
  --log-level DEBUG

# Automated rendering: background mode with pre-script
blender-remote-cli start \
  --background \
  --scene /render/project.blend \
  --pre-file /scripts/setup_render.py \
  --log-level INFO
```

## Environment Variables

The CLI automatically sets these environment variables for BLD_Remote_MCP:

- `BLD_REMOTE_MCP_PORT`: Port number (from config or --port override)
- `BLD_REMOTE_MCP_START_NOW`: Set to '1' to auto-start service
- `BLD_REMOTE_LOG_LEVEL`: Logging level (from config or --log-level override)

## Complete Workflow Example

```bash
# 1. Initialize configuration
blender-remote-cli init /apps/blender-4.4.3-linux-x64/blender

# 2. Install the addon
blender-remote-cli install

# 3. Configure logging for development
blender-remote-cli config set mcp_service.log_level=DEBUG

# 4. Start Blender with specific scene and custom port
blender-remote-cli start \
  --scene /projects/my_scene.blend \
  --port 7777 \
  --log-level INFO

# 5. Check service status (from another terminal)
blender-remote-cli status
```

All these features maintain backward compatibility with existing workflows while providing enhanced control over logging and scene management.