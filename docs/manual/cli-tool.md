# CLI Tool Reference

`blender-remote-cli` is a comprehensive command-line interface that manages the entire blender-remote ecosystem, from initial setup to advanced debugging.

## Overview

The CLI tool provides a complete workflow for blender-remote operations:

- **Automatic Setup**: Platform-specific auto-detection of Blender installations (Windows/macOS)
- **Configuration Management**: YAML-based settings with dot-notation access via OmegaConf
- **Addon Management**: Automated installation and export of BLD_Remote_MCP addon
- **Process Control**: Launch Blender in GUI or background mode with MCP service
- **Code Execution**: Direct Python code execution in Blender with base64 encoding support
- **Debug Tools**: Alternative TCP-based executor for testing and development

## Installation

The CLI tool is included with blender-remote:

```bash
pip install blender-remote
blender-remote-cli --help
```

## Platform Support

- **Windows**: Full support with registry-based Blender detection
- **macOS**: Full support with Spotlight-based Blender detection  
- **Linux**: Full support with manual path configuration

## Quick Start

### Basic Workflow

```bash
# 1. Initialize configuration (auto-detects on Windows/macOS)
blender-remote-cli init

# 2. Install BLD Remote MCP addon
blender-remote-cli install

# 3. Start Blender with MCP service
blender-remote-cli start

# 4. Execute Python code
blender-remote-cli execute --code "print('Hello from Blender!')"
```

### Configuration Management

```bash
# View all settings
blender-remote-cli config get

# Modify settings
blender-remote-cli config set mcp_service.default_port=7777

# Check connection
blender-remote-cli status
```

## Command Reference

### `init` - Initialize Configuration

**Purpose**: Sets up blender-remote by detecting Blender installation and creating configuration.

**Usage:**
```bash
blender-remote-cli init [blender_executable_path] [OPTIONS]
```

**Arguments:**
- `blender_executable_path` (optional) - Path to Blender executable

**Options:**
- `--backup` - Create backup of existing configuration file

**Platform-Specific Behavior:**

- **Windows**: Searches Windows Registry for Blender 4.x installations, checks common installation paths, and searches system PATH
- **macOS**: Uses Spotlight (mdfind) to locate Blender.app, checks standard installation locations
- **Linux**: Prompts for manual path entry if not provided

**Examples:**
```bash
# Auto-detection (Windows/macOS)
blender-remote-cli init

# Specify path explicitly
blender-remote-cli init /usr/bin/blender

# Initialize with backup
blender-remote-cli init --backup
```

**Detection Process:**
1. Validates Blender version (requires 4.0+)
2. Discovers addon directories using Blender's Python API
3. Tests directory write permissions
4. Creates configuration at `~/.config/blender-remote/bld-remote-config.yaml`

**Generated Configuration:**
```yaml
blender:
  version: "4.4.3"                    # Auto-detected version
  exec_path: "/usr/bin/blender"       # Blender executable path
  root_dir: "/usr/share/blender"      # Installation directory
  plugin_dir: "/home/user/.config/blender/4.4/scripts/addons"  # Addon directory
  
  # Additional detected paths (informational)
  user_addons: "/home/user/.config/blender/4.4/scripts/addons"
  all_addon_paths: ["/usr/share/blender/scripts/addons", ...]
  extensions_dir: "/home/user/.config/blender/4.4/extensions"  # Blender 4.2+

mcp_service:
  default_port: 6688   # Default TCP port for MCP service
  log_level: INFO      # Logging verbosity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
```

### `install` - Install Addon

**Purpose**: Installs the BLD_Remote_MCP addon into Blender's addon directory.

**Usage:**
```bash
blender-remote-cli install
```

**Auto-Detection**: If no configuration exists, automatically detects Blender on Windows/macOS.

**Installation Process:**
1. Locates addon files (from package or development directory)
2. Creates temporary zip archive
3. Uses Blender's Python API to install addon
4. Enables addon and saves preferences
5. Verifies successful installation

**Addon Locations:**
- Development: `./blender_addon/bld_remote_mcp/`
- Installed: Retrieved from package resources
- Target: `{blender_addon_dir}/bld_remote_mcp/`

**Example Output:**
```
[INSTALL] Installing bld_remote_mcp addon...
[ADDON] Using addon: /tmp/bld_remote_mcp.zip
Installing addon from: /tmp/bld_remote_mcp.zip
Enabling addon: bld_remote_mcp
Saving user preferences...
[SUCCESS] Addon installed successfully!
[LOCATION] Addon location: /home/user/.config/blender/4.4/scripts/addons/bld_remote_mcp
```

### `config` - Configuration Management

**Purpose**: View and modify configuration using OmegaConf with dot notation.

#### `config get` - View Configuration

**Usage:**
```bash
blender-remote-cli config get [key]
```

**Arguments:**
- `key` (optional) - Specific configuration key using dot notation

**Examples:**
```bash
# View all configuration
blender-remote-cli config get

# Get specific value
blender-remote-cli config get blender.version

# Get nested value
blender-remote-cli config get mcp_service.default_port
```

#### `config set` - Modify Configuration

**Usage:**
```bash
blender-remote-cli config set <key>=<value>
```

**Type Conversion:**
- **Integers**: `7777` → `7777`
- **Floats**: `30.5` → `30.5`
- **Booleans**: `true`/`false` → `True`/`False`
- **Strings**: Anything else remains string

**Examples:**
```bash
# Set port
blender-remote-cli config set mcp_service.default_port=7777

# Set logging level
blender-remote-cli config set mcp_service.log_level=DEBUG

# Set nested values (creates structure if needed)
blender-remote-cli config set mcp_service.advanced.timeout=45.0
```

### `start` - Start Blender with MCP Service

**Purpose**: Launches Blender with BLD_Remote_MCP service configured and running.

**Usage:**
```bash
blender-remote-cli start [OPTIONS] [-- blender_args...]
```

**Options:**
- `--background` - Run Blender headless (no GUI)
- `--pre-file PATH` - Execute Python file before service starts
- `--pre-code CODE` - Execute Python code before service starts
- `--port PORT` - Override MCP service port (default: 6688)
- `--scene PATH` - Open .blend file on startup
- `--log-level LEVEL` - Set logging verbosity (DEBUG, INFO, WARNING, ERROR, CRITICAL)

**Environment Variables Set:**
- `BLD_REMOTE_MCP_PORT` - Service port number
- `BLD_REMOTE_MCP_START_NOW` - Always set to '1' for auto-start
- `BLD_REMOTE_LOG_LEVEL` - Logging verbosity

**Examples:**
```bash
# GUI mode with default settings
blender-remote-cli start

# Background mode for automation
blender-remote-cli start --background

# Development setup
blender-remote-cli start --port=7777 --log-level=DEBUG

# Open scene with pre-execution script
blender-remote-cli start --scene=project.blend --pre-file=setup.py

# Inline code execution
blender-remote-cli start --pre-code="bpy.context.scene.render.engine='CYCLES'"

# Pass Blender arguments
blender-remote-cli start -- --factory-startup --debug-cycles
```

**Background Mode:**
- Includes keep-alive script to prevent Blender from exiting
- Handles SIGINT/SIGTERM for graceful shutdown
- Processes queued commands via `bld_remote.step()`
- Ideal for headless servers and CI/CD pipelines

### `execute` - Execute Python Code

**Purpose**: Runs Python code in the Blender process via MCP service.

**Usage:**
```bash
blender-remote-cli execute [CODE_FILE] [OPTIONS]
```

**Arguments:**
- `CODE_FILE` (optional) - Python file to execute

**Options:**
- `-c, --code TEXT` - Python code string to execute
- `--use-base64` - Encode code as base64 before transmission
- `--return-base64` - Request base64-encoded results
- `--port PORT` - Override MCP service port

**Base64 Encoding:**
Use for code with:
- Complex formatting or indentation
- Special characters or nested quotes
- Large scripts (>1KB)
- Binary data or unicode

**Examples:**
```bash
# Simple inline code
blender-remote-cli execute --code "print(len(bpy.data.objects))"

# Add a cube
blender-remote-cli execute -c "bpy.ops.mesh.primitive_cube_add(location=(2,0,0))"

# Execute file
blender-remote-cli execute my_script.py

# Complex script with base64
blender-remote-cli execute complex_script.py --use-base64 --return-base64

# Custom port
blender-remote-cli execute --code "print('Hello')" --port 7777
```

**Output:**
```
[FILE] Executing code from: script.py
[LENGTH] Code length: 245 characters
[CONNECT] Connecting to Blender BLD_Remote_MCP service (port 6688)...
[SUCCESS] Code execution successful!
[OUTPUT] Output:
Hello from Blender!
```

### `status` - Check Connection Status

**Purpose**: Tests connection to running BLD_Remote_MCP service.

**Usage:**
```bash
blender-remote-cli status
```

**Information Displayed:**
- Connection status (success/failure)
- Service port number
- Current scene name
- Object count in scene

**Example Output:**
```
Checking connection to Blender BLD_Remote_MCP service...
Connected to Blender BLD_Remote_MCP service (port 6688)
   Scene: Scene
   Objects: 3
```

**Common Issues:**
- "Connection refused" - Service not running (use `start` command)
- "Connection failed" - Wrong port or firewall blocking

### `export` - Export Components

**Purpose**: Extracts addon source code or scripts for manual installation or inspection.

**Usage:**
```bash
blender-remote-cli export --content TYPE -o OUTPUT_DIR
```

**Options:**
- `--content TYPE` (required) - Content to export: 'addon' or 'keep-alive.py'
- `-o, --output-dir PATH` (required) - Output directory path

**Content Types:**
- `addon` - Extracts BLD_Remote_MCP addon source to `OUTPUT_DIR/bld_remote_mcp/`
- `keep-alive.py` - Exports background mode keep-alive script

**Examples:**
```bash
# Export addon source
blender-remote-cli export --content addon -o ./exported

# Export keep-alive script
blender-remote-cli export --content keep-alive.py -o ./scripts
```

**Use Cases:**
- Manual addon installation
- Source code inspection
- Custom deployment scripts
- Debugging addon issues

### `debug` - Debug Tools

**Purpose**: Alternative TCP-based executor for testing and development.

#### `debug install`

**Usage:**
```bash
blender-remote-cli debug install
```

Installs the `simple-tcp-executor` addon - a lightweight TCP server for testing code execution patterns.

#### `debug start`

**Usage:**
```bash
blender-remote-cli debug start [OPTIONS]
```

**Options:**
- `--background` - Run Blender headless
- `--port PORT` - TCP server port (default: 7777)

**Environment Variable:**
- `BLD_DEBUG_TCP_PORT` - Default port if not specified

**Examples:**
```bash
# Start debug server in GUI mode
blender-remote-cli debug start

# Background mode with custom port
blender-remote-cli debug start --background --port 8888
```

**Debug Features:**
- Simple TCP protocol (no MCP overhead)
- Direct code execution without service layer
- Manual step() processing in background mode
- Debug logging to `/tmp/blender_debug.log`

## Configuration Management

### Configuration File

**Location**: Platform-specific via `platformdirs`:
- Linux: `~/.config/blender-remote/bld-remote-config.yaml`
- macOS: `~/Library/Application Support/blender-remote/bld-remote-config.yaml`
- Windows: `%APPDATA%\blender-remote\bld-remote-config.yaml`

**OmegaConf Features:**
- Type-safe value conversion
- Dot notation for nested access
- Graceful missing key handling
- Clean YAML formatting

**Backup Management:**
```bash
# Create backup during init
blender-remote-cli init --backup

# Manual backup
cp ~/.config/blender-remote/bld-remote-config.yaml \
   ~/.config/blender-remote/bld-remote-config.yaml.bak
```

## Socket Communication

**Protocol Details:**
- TCP socket communication
- JSON message format
- Optimized chunk reading (128KB chunks)
- Maximum response size: 10MB
- Timeout: 60 seconds
- Automatic connection cleanup

**Message Format:**
```json
{
  "type": "command_type",
  "params": {
    "key": "value"
  }
}
```

## Advanced Usage

### Development Workflow

```bash
# Initialize with auto-detection
blender-remote-cli init

# Install addon
blender-remote-cli install

# Development mode with logging
blender-remote-cli start --pre-file=dev_setup.py \
  --port=7777 --scene=test.blend --log-level=DEBUG

# Test connection
blender-remote-cli status

# Execute test code
blender-remote-cli execute --code "print(bpy.app.version_string)"
```

### Headless Automation

```bash
# Start background service
blender-remote-cli start --background --port=6688 &

# Wait for startup
sleep 10

# Run automation script
blender-remote-cli execute automation.py --use-base64

# Stop service
pkill -f blender
```

### CI/CD Integration

```yaml
# Example GitHub Actions workflow
- name: Setup Blender
  run: |
    blender-remote-cli init /usr/bin/blender
    blender-remote-cli install
    
- name: Run Tests
  run: |
    blender-remote-cli start --background &
    sleep 10
    blender-remote-cli execute tests/run_tests.py
```

## Environment Variables

**Service Control:**
- `BLD_REMOTE_MCP_PORT` - MCP service port (overrides config)
- `BLD_REMOTE_MCP_START_NOW` - Auto-start service ('1' or 'true')
- `BLD_REMOTE_LOG_LEVEL` - Logging verbosity

**Debug Mode:**
- `BLD_DEBUG_TCP_PORT` - Debug server port (default: 7777)

## Troubleshooting

### Common Issues

**Configuration Not Found**
```bash
# Initialize first
blender-remote-cli init

# Or specify Blender path
blender-remote-cli init /path/to/blender
```

**Auto-Detection Failed**
```bash
# Windows - Check registry
reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall" /s | findstr /i blender

# macOS - Use Spotlight
mdfind -name Blender.app

# Linux - Find manually
which blender
find /usr -name blender 2>/dev/null
```

**Addon Installation Issues**
```bash
# Verify Blender version (must be 4.0+)
blender --version

# Check addon directory permissions
ls -la ~/.config/blender/*/scripts/addons/

# Try manual installation
blender-remote-cli export --content addon -o /tmp
# Then install via Blender preferences
```

**Connection Problems**
```bash
# Check if service is running
ps aux | grep blender

# Test port availability
nc -zv localhost 6688

# Check firewall
sudo ufw status  # Linux
```

**Code Execution Errors**
```bash
# Use base64 for complex code
blender-remote-cli execute script.py --use-base64 --return-base64

# Check service logs
blender-remote-cli start --log-level=DEBUG
```

### Debug Commands

```bash
# Verbose configuration check
blender-remote-cli config get | grep -E "port|path|version"

# Test with debug server
blender-remote-cli debug install
blender-remote-cli debug start --port 8888

# Monitor service output
blender-remote-cli start --pre-code="
import logging
logging.basicConfig(level=logging.DEBUG)
print('Debug mode active')
"
```

## Integration Examples

### MCP Protocol Configuration

```json
{
  "mcpServers": {
    "blender-remote": {
      "command": "uvx",
      "args": ["blender-remote"],
      "env": {
        "BLD_REMOTE_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Python API Integration

```python
import subprocess
import time
import blender_remote

# Start service via CLI
process = subprocess.Popen([
    'blender-remote-cli', 'start', '--background'
])

# Wait for service startup
time.sleep(5)

# Connect and use API
client = blender_remote.connect_to_blender(port=6688)
scene = blender_remote.create_scene_manager(client)

# Your automation code
scene.add_cube(location=(0, 0, 0))
```

### Shell Script Automation

```bash
#!/bin/bash
# render_automation.sh

# Start Blender service
blender-remote-cli start --background --scene=template.blend &
BLENDER_PID=$!

# Wait for startup
sleep 10

# Run render script
blender-remote-cli execute render_script.py --use-base64

# Cleanup
kill $BLENDER_PID
```

## Command Reference Summary

| Command | Purpose |
|---------|--------|
| `init` | Initialize configuration with Blender detection |
| `install` | Install BLD_Remote_MCP addon |
| `config get/set` | View/modify configuration |
| `start` | Launch Blender with MCP service |
| `execute` | Run Python code in Blender |
| `status` | Check service connection |
| `export` | Extract addon or scripts |
| `debug install/start` | Debug tools for development |

## Best Practices

1. **Initial Setup**: Always run `init` before other commands
2. **Port Management**: Use consistent ports across your workflow
3. **Background Mode**: Add proper shutdown handling in scripts
4. **Code Execution**: Use base64 for scripts >1KB or with special characters
5. **Logging**: Set appropriate log levels (INFO for production, DEBUG for development)
6. **Error Handling**: Check `status` before executing code
7. **Cleanup**: Properly terminate background processes