# CLI Configuration Tool

**New in v1.2.0:** `blender-remote-cli` provides comprehensive configuration management, addon installation, and Blender process control for the blender-remote ecosystem.

## Overview

The CLI tool simplifies the setup and management of blender-remote by automating common tasks:

- **Configuration Management**: Auto-detect Blender paths and create configuration files
- **Addon Installation**: Automated BLD Remote MCP addon installation
- **Process Control**: Start Blender with service in GUI or background modes
- **Settings Management**: Configure service ports and behavior

## Installation

After installing blender-remote, the CLI tool is immediately available:

```bash
pip install blender-remote
blender-remote-cli --help
```

## Quick Start

### Basic Setup

```bash
# 1. Initialize configuration with auto-detection
blender-remote-cli init /path/to/blender

# 2. Install BLD Remote MCP addon automatically
blender-remote-cli install

# 3. Start Blender with service
blender-remote-cli start
```

### Configuration Check

```bash
# View current configuration
blender-remote-cli config get

# Check service connection
blender-remote-cli status
```

## Commands Reference

### `init` - Initialize Configuration

Initialize blender-remote configuration with automatic path detection.

**Usage:**
```bash
blender-remote-cli init <blender_executable_path> [OPTIONS]
```

**Options:**
- `--backup` - Create backup of existing configuration file

**Examples:**
```bash
# Basic initialization
blender-remote-cli init /usr/bin/blender

# Initialize with backup
blender-remote-cli init /usr/bin/blender --backup
```

**What it does:**
1. Detects Blender version (requires Blender 4.0+)
2. Auto-discovers Blender root and addon directories
3. Creates `~/.config/blender-remote/bld-remote-config.yaml`
4. Sets default MCP service port (6688)

**Configuration Structure:**
```yaml
blender:
  version: "4.4.3"
  exec_path: "/usr/bin/blender"
  root_dir: "/usr/share/blender"
  plugin_dir: "/home/user/.config/blender/4.4/scripts/addons"

mcp_service:
  default_port: 6688
```

### `install` - Install Addon

Automatically install the BLD Remote MCP addon to Blender.

**Usage:**
```bash
blender-remote-cli install
```

**Requirements:**
- Configuration must exist (run `init` first)
- Blender executable must be accessible

**What it does:**
1. Creates addon zip from development files or package data
2. Uses Blender CLI to install and enable addon
3. Saves Blender preferences to persist installation
4. Verifies installation success

### `config` - Configuration Management

Manage configuration settings with dot notation support.

**Usage:**
```bash
# Set configuration value
blender-remote-cli config set <key>=<value>

# Get specific value
blender-remote-cli config get <key>

# Get all configuration
blender-remote-cli config get
```

**Examples:**
```bash
# Change default port
blender-remote-cli config set mcp_service.default_port=7777

# Get Blender version
blender-remote-cli config get blender.version

# View all settings
blender-remote-cli config get
```

**Supported Value Types:**
- **Integers**: `port=7777`
- **Floats**: `timeout=30.5`
- **Booleans**: `auto_start=true` or `auto_start=false`
- **Strings**: `path=/usr/bin/blender`

### `start` - Start Blender

Start Blender with BLD Remote MCP service automatically configured.

**Usage:**
```bash
blender-remote-cli start [OPTIONS] [-- blender_args...]
```

**Options:**
- `--background` - Start in background mode (headless)
- `--pre-file=<path>` - Execute Python file before service startup
- `--pre-code=<code>` - Execute Python code before service startup
- `--port=<port>` - Override default MCP service port

**Examples:**
```bash
# Start in GUI mode
blender-remote-cli start

# Start in background mode
blender-remote-cli start --background

# Custom port
blender-remote-cli start --port=8888

# Execute setup script
blender-remote-cli start --pre-file=setup.py

# Execute inline code
blender-remote-cli start --pre-code="print('Custom startup')"

# Pass arguments to Blender
blender-remote-cli start -- --factory-startup --no-addons

# Combine options
blender-remote-cli start --background --port=7777 -- --factory-startup
```

**Pre-execution Scripts:**
- Use `--pre-file` to run setup scripts before service starts
- Use `--pre-code` for inline Python code
- Cannot use both options simultaneously
- Scripts run in Blender's Python context

**Background Mode Features:**
- Automatic asyncio event loop to prevent immediate exit
- All service functions work except viewport screenshots
- Perfect for CI/CD and headless automation

### `status` - Check Connection

Check connection status to running BLD Remote MCP service.

**Usage:**
```bash
blender-remote-cli status
```

**What it shows:**
- Connection success/failure
- Service port information
- Current scene name and object count
- Helpful troubleshooting messages

**Example Output:**
```
🔍 Checking connection to Blender BLD_Remote_MCP service...
✅ Connected to Blender BLD_Remote_MCP service (port 6688)
   Scene: Scene
   Objects: 3
```

## Configuration File

### Location
`~/.config/blender-remote/bld-remote-config.yaml`

### Structure
```yaml
blender:
  version: "4.4.3"                    # Auto-detected Blender version
  exec_path: "/usr/bin/blender"       # Path to Blender executable
  root_dir: "/usr/share/blender"      # Blender installation directory
  plugin_dir: "/home/user/.config/blender/4.4/scripts/addons"  # Addons directory

mcp_service:
  default_port: 6688                  # Default MCP service port
```

### Backup and Restore
```bash
# Create backup during init
blender-remote-cli init /usr/bin/blender --backup

# Backup file created at:
# ~/.config/blender-remote/bld-remote-config.yaml.bak
```

## Advanced Usage

### CI/CD Integration

```bash
# Automated setup for CI environments
blender-remote-cli init $BLENDER_PATH
blender-remote-cli install
blender-remote-cli start --background &

# Wait for service startup
sleep 10

# Run automation
python automation_script.py
```

### Docker Integration

```dockerfile
FROM blender:4.4.3

# Install blender-remote
RUN pip install blender-remote

# Setup configuration
RUN blender-remote-cli init /usr/local/blender/blender
RUN blender-remote-cli install

# Start with background service
CMD ["blender-remote-cli", "start", "--background"]
```

### Development Workflow

```bash
# Setup development environment
blender-remote-cli init /usr/bin/blender
blender-remote-cli install

# Start with development script
blender-remote-cli start --pre-file=dev_setup.py --port=7777

# Test connection
blender-remote-cli status
```

## Troubleshooting

### Common Issues

**"Configuration file not found"**
```bash
# Run init first
blender-remote-cli init /path/to/blender
```

**"Blender executable not found"**
```bash
# Check path and permissions
ls -la /path/to/blender
which blender
```

**"Addon installation failed"**
```bash
# Check Blender version (must be 4.0+)
blender --version

# Verify addon directory exists
ls -la ~/.config/blender/4.4/scripts/addons/
```

**"Connection refused"**
```bash
# Ensure Blender is running with service
blender-remote-cli start &
sleep 10
blender-remote-cli status
```

### Debug Information

```bash
# Check configuration
blender-remote-cli config get

# Test with verbose output
blender-remote-cli start --pre-code="print('Service starting...')"

# Check if service port is in use
netstat -tlnp | grep 6688
```

## Integration with Other Tools

### MCP Protocol

The CLI tool sets up the service that MCP clients connect to:

```json
{
  "mcpServers": {
    "blender-remote": {
      "command": "uvx",
      "args": ["blender-remote"]
    }
  }
}
```

### Python Control API

Start service with CLI, then use Python API:

```python
import blender_remote

# Connect to CLI-started service
client = blender_remote.connect_to_blender(port=6688)
scene_manager = blender_remote.create_scene_manager(client)
```

### Automation Scripts

```python
# automation_with_cli.py
import subprocess
import time
import blender_remote

# Start Blender with CLI
subprocess.Popen(['blender-remote-cli', 'start', '--background'])
time.sleep(10)  # Wait for startup

# Use Python API
client = blender_remote.connect_to_blender()
# ... automation code ...
```

## Environment Variables

The CLI tool respects these environment variables:

- `BLD_REMOTE_MCP_PORT` - Default service port (overridden by config)
- `BLD_REMOTE_MCP_START_NOW` - Auto-start service (set by CLI)

## Examples

### Complete Setup Workflow

```bash
# 1. Install blender-remote
pip install blender-remote

# 2. Initialize configuration
blender-remote-cli init /usr/bin/blender

# 3. Install addon
blender-remote-cli install

# 4. Configure custom port
blender-remote-cli config set mcp_service.default_port=7777

# 5. Start service
blender-remote-cli start --background

# 6. Verify connection
blender-remote-cli status
```

### Automated Asset Generation

```bash
# Start with setup script
blender-remote-cli start --background --pre-file=asset_setup.py

# In another terminal, run automation
python asset_generation.py
```

### Development Testing

```bash
# Start with development settings
blender-remote-cli start --port=9999 --pre-code="
import bpy
bpy.context.preferences.view.show_splash = False
print('Development mode active')
"
```