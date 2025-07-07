# Blender Auto MCP Plugin

An enhanced version of the Blender MCP plugin that provides automatic startup capabilities and environment variable configuration for seamless integration with automated workflows and headless Blender operations.

## Overview

The Blender Auto MCP plugin extends the original Blender MCP functionality by adding:
- **Environment variable configuration** for automated setup
- **Background mode support** that prevents Blender from exiting
- **Multi-threaded MCP server** for handling multiple concurrent connections
- **Signal handling** for graceful shutdown in headless environments
- **Auto-startup capabilities** for CI/CD and automated workflows

## Features

### Core MCP Functionality
- **Scene Information**: Get detailed scene and object information
- **Code Execution**: Execute arbitrary Blender Python code remotely
- **Viewport Screenshots**: Capture 3D viewport images
- **PolyHaven Integration**: Download HDRIs, textures, and 3D models
- **Hyper3D Rodin Integration**: AI-powered 3D model generation
- **Sketchfab Integration**: Download and import Sketchfab models

### Enhanced Features
- **Environment Variable Configuration**: Set port and auto-start behavior via environment variables
- **Background Mode Support**: Keeps Blender alive in headless mode
- **Multi-Client Support**: Handle multiple simultaneous MCP connections
- **Cross-Platform Compatibility**: Optimized socket handling for Windows, Linux, and macOS
- **Graceful Shutdown**: Proper signal handling for clean termination
- **GUI Configuration Panel**: Visual interface for configuration and status

## Installation

1. Copy the `blender_auto_mcp` directory to your Blender addons folder:
   ```
   # Linux/macOS
   ~/.config/blender/[version]/scripts/addons/

   # Windows
   %APPDATA%\Blender Foundation\Blender\[version]\scripts\addons\
   ```

2. Enable the addon in Blender:
   - Go to `Edit > Preferences > Add-ons`
   - Search for "Blender Auto MCP"
   - Check the checkbox to enable

## Configuration

### Environment Variables

The plugin reads configuration from environment variables on startup:

```bash
# Set the MCP server port (default: 9876)
export BLENDER_AUTO_MCP_SERVICE_PORT=9876

# Enable automatic startup (0=disabled, 1=enabled)
export BLENDER_AUTO_MCP_START_NOW=1
```

### GUI Configuration

Access the configuration panel in the 3D Viewport:
1. Press `N` to open the sidebar
2. Look for the "Auto MCP" tab
3. Configure settings as needed

## Usage

### Automated/Headless Mode

For automated workflows or CI/CD pipelines:

```bash
# Set environment variables
export BLENDER_AUTO_MCP_SERVICE_PORT=9876
export BLENDER_AUTO_MCP_START_NOW=1

# Start Blender in background mode
blender --background --python-expr "import bpy; bpy.ops.preferences.addon_enable(module='blender_auto_mcp')"
```

The plugin will:
- Automatically start the MCP server on the specified port
- Keep Blender running until explicitly stopped
- Handle multiple concurrent MCP client connections
- Respond to shutdown signals gracefully

### Interactive Mode

For interactive use with Blender GUI:

1. **Enable the addon** (if not already enabled)
2. **Open the Auto MCP panel** (3D Viewport > Sidebar > Auto MCP tab)
3. **Configure settings** as needed
4. **Click "Start MCP Server"** to begin accepting connections

### Manual Control

You can manually start/stop the server regardless of environment variables:

- **Start Server**: Click "Start MCP Server" in the GUI panel
- **Stop Server**: Click "Stop MCP Server" in the GUI panel
- **Graceful Shutdown**: Send `server_shutdown` MCP command

## MCP Commands

The plugin supports all standard MCP commands plus additional functionality:

### Basic Commands
- `get_scene_info` - Get scene and object information
- `get_object_info` - Get detailed object information
- `execute_code` - Execute Blender Python code
- `get_viewport_screenshot` - Capture viewport image
- `server_shutdown` - Gracefully shutdown the server

### PolyHaven Commands
- `get_polyhaven_status` - Check PolyHaven integration status
- `get_polyhaven_categories` - Get asset categories
- `search_polyhaven_assets` - Search for assets
- `download_polyhaven_asset` - Download and import assets
- `set_texture` - Apply textures to objects

### Hyper3D/Rodin Commands
- `get_hyper3d_status` - Check Hyper3D integration status
- `create_rodin_job` - Create AI model generation job
- `poll_rodin_job_status` - Check job status
- `import_generated_asset` - Import generated models

### Sketchfab Commands
- `get_sketchfab_status` - Check Sketchfab integration status
- `search_sketchfab_models` - Search Sketchfab models
- `download_sketchfab_model` - Download and import models

## API Integration Setup

### PolyHaven
No API key required - uses public API.

### Hyper3D/Rodin
1. **Get API Key**: 
   - For hyper3d.ai: Sign up at [hyper3d.ai](https://hyper3d.ai)
   - For fal.ai: Sign up at [fal.ai](https://fal.ai)
   - Or use the free trial key (click "Set Free Trial API Key")

2. **Configure in GUI**:
   - Enable "Use Hyper3D Rodin 3D model generation"
   - Select platform (hyper3d.ai or fal.ai)
   - Enter your API key

### Sketchfab
1. **Get API Key**: 
   - Sign up at [sketchfab.com](https://sketchfab.com)
   - Go to Settings > Password & API
   - Generate an API token

2. **Configure in GUI**:
   - Enable "Use assets from Sketchfab"
   - Enter your API key

## Architecture

### Modular Design

The plugin uses a modular architecture for better maintainability and organization:

```
blender_auto_mcp/
├── __init__.py           # Main addon entry point and registration
├── server.py             # Core MCP server functionality
├── asset_providers.py    # External service integrations (PolyHaven, Hyper3D, Sketchfab)
├── ui_panel.py          # Blender UI components and operators
├── utils.py             # Utility functions and event handlers
├── test_scripts/        # Development and testing scripts
│   ├── force-close-port.ps1
│   ├── force-close-port.sh
│   ├── start-blender-mcp-gui.ps1
│   ├── start-blender-mcp-gui.sh
│   ├── start-blender-mcp-headless.ps1
│   └── start-blender-mcp-headless.sh
└── README.md           # This documentation
```

**Module Responsibilities:**
- **server.py**: `BlenderAutoMCPServer` class, networking, command execution
- **asset_providers.py**: External API integrations with handler factories
- **ui_panel.py**: All Blender UI panels, operators, and scene properties
- **utils.py**: Configuration loading, auto-start, event handlers
- **__init__.py**: Addon registration and module coordination

### Threading Model
- **Main Thread**: Blender's main thread handles all Blender operations
- **Server Thread**: Dedicated thread for accepting new connections
- **Client Threads**: Separate thread for each connected MCP client
- **Timer System**: Uses Blender's timer system to execute commands safely

### Background Mode
When running in background mode (`blender --background`), the plugin:
- Installs signal handlers for SIGTERM and SIGINT
- Registers atexit handlers for cleanup
- Uses Blender's timer system to prevent early exit
- Maintains the process until explicitly stopped

### Port Management
The plugin includes robust port cleanup mechanisms:
- Proper socket shutdown on server stop
- Python atexit handlers ensure cleanup when Blender closes
- Plugin disable handlers ensure cleanup when addon is disabled
- Multiple fallback cleanup mechanisms for reliability
- Cross-platform socket configuration:
  - **Windows**: Uses SO_EXCLUSIVEADDRUSE to prevent port hijacking
  - **Unix/Linux/macOS**: Uses SO_REUSEADDR to allow address reuse

### Platform Compatibility
The plugin is designed to work seamlessly across different operating systems:

**Windows:**
- Uses `SO_EXCLUSIVEADDRUSE` socket option for enhanced security
- Prevents port hijacking by other applications
- Automatic fallback to `SO_REUSEADDR` for older Windows versions
- Handles Windows-specific socket error codes (WinError 10022, 10013, 10048)

**Linux/macOS:**
- Uses standard `SO_REUSEADDR` socket option for address reuse
- Follows Unix socket conventions
- Compatible with system package managers and custom installations

**Cross-Platform Features:**
- Automatic OS detection and appropriate socket configuration
- Consistent API behavior across all platforms
- Platform-specific error messages and troubleshooting guidance

### Security
- **Code Execution**: Execute arbitrary Python code (use with caution)
- **File Download**: Secure file handling with path traversal protection
- **API Keys**: Stored as password fields in Blender preferences
- **Network**: Only accepts local connections by default

## Troubleshooting

### Common Issues

**Server won't start:**
- **Port conflicts**: If the port is already in use, the plugin will fail with a clear error message
- **Permission errors**: On Windows, some ports may be restricted. Try using ports above 1024 or run as administrator
- **Windows socket errors**: The plugin automatically handles Windows-specific socket configuration (SO_EXCLUSIVEADDRUSE vs SO_REUSEADDR)
- **Firewall issues**: Ensure Blender is allowed through your firewall
- **Multiple Blender instances**: Check if another Blender instance is already running the MCP server
- Use `netstat -ano | findstr :[PORT]` (Windows) or `lsof -i :[PORT]` (Mac/Linux) to check what's using the port
- Verify environment variables are set correctly
- Check Blender console for detailed error messages

**Environment variables not working:**
- Ensure variables are exported before starting Blender
- Check variable names are exactly as specified
- Restart Blender after setting variables

**Background mode exits immediately:**
- Ensure `BLENDER_AUTO_MCP_START_NOW=1` is set
- Check that the plugin is properly enabled
- Look for error messages in console output

**API integrations not working:**
- Verify API keys are correctly entered
- Check internet connection
- Enable relevant integration checkboxes
- Restart MCP connection after configuration changes

### Debug Mode

Enable verbose logging by setting environment variable:
```bash
export BLENDER_AUTO_MCP_DEBUG=1
```

### Log Files

Check Blender's console output for detailed error messages and status information.

## Development

### Project Structure
```
blender_auto_mcp/
├── __init__.py           # Main addon entry point and registration
├── server.py             # Core MCP server functionality
├── asset_providers.py    # External service integrations
├── ui_panel.py          # Blender UI components and operators
├── utils.py             # Utility functions and event handlers
├── test_scripts/        # Development and testing scripts
└── README.md           # This documentation
```

### Key Classes

**server.py:**
- `BlenderAutoMCPServer`: Main server implementation with networking and command execution

**asset_providers.py:**
- Handler factory functions: `get_polyhaven_handlers()`, `get_hyper3d_handlers()`, `get_sketchfab_handlers()`
- Individual provider methods for each external service

**ui_panel.py:**
- `BLENDER_AUTO_MCP_PT_Panel`: Main GUI panel
- `BLENDER_AUTO_MCP_OT_StartServer`: Server start operator
- `BLENDER_AUTO_MCP_OT_StopServer`: Server stop operator  
- `BLENDER_AUTO_MCP_OT_SetFreeTrialHyper3DAPIKey`: API key setup operator
- `BLENDER_AUTO_MCP_OT_BackgroundKeepAlive`: Background mode handler

**utils.py:**
- `load_environment_config()`: Environment variable parsing
- `auto_start_server()`: Automatic server startup logic
- `cleanup_on_exit()`, `ensure_server_after_load()`: Event handlers

### Modular Benefits

The modular architecture provides several advantages:

**Maintainability:**
- Each module has a single, well-defined responsibility
- Easy to locate and modify specific functionality
- Reduced complexity in individual files

**Extensibility:**
- New asset providers can be added to `asset_providers.py`
- UI components are cleanly separated from server logic  
- Handler factory pattern allows easy command registration

**Testing:**
- Individual modules can be tested in isolation
- Clear separation between UI, networking, and business logic
- Dependency injection makes testing easier

**Code Organization:**
- Related functionality is grouped together
- Import dependencies are explicit and minimal
- Global state is properly managed across modules

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly in both GUI and background modes
5. Submit a pull request

## License

This plugin extends the original Blender MCP addon and follows the same licensing terms.

## Support

For issues and questions:
1. Check this README for common solutions
2. Look at Blender console output for error messages
3. Test with environment variables and GUI configuration
4. Report issues with detailed reproduction steps

## Version History

### v1.1 (Current)
- **Modular Architecture**: Restructured codebase into focused modules for better maintainability
  - `server.py`: Core MCP server functionality 
  - `asset_providers.py`: External service integrations (PolyHaven, Hyper3D, Sketchfab)
  - `ui_panel.py`: Blender UI components and operators
  - `utils.py`: Utility functions and event handlers
  - `__init__.py`: Simplified addon entry point
- **Improved Code Organization**: Clear separation of concerns and reduced complexity
- **Enhanced Maintainability**: Each module has single responsibility and explicit dependencies
- **Better Testing Support**: Modular design enables isolated testing of components
- **Handler Factory Pattern**: Cleaner command registration for asset providers

### v1.0
- Initial implementation with environment variable support
- Background mode compatibility
- Multi-threaded MCP server
- Full feature parity with original Blender MCP
- Enhanced GUI with usage information
- Cross-platform socket handling (Windows SO_EXCLUSIVEADDRUSE vs Unix SO_REUSEADDR)
- Robust cleanup mechanisms using Python atexit handlers
- Port conflict detection and clear error reporting