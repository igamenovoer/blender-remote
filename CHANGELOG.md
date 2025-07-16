# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
### Changed
### Fixed
### Security

## [1.2.2] - 2025-07-16

### Fixed
- **Critical**: Fixed Blender addon GUI installation failure caused by non-literal values in bl_info dictionary
- bl_info now uses literal values instead of config constants to satisfy ast.literal_eval requirements
- Resolves `ValueError: malformed node or string` when installing addon through Blender's GUI

## [1.2.1] - 2025-07-16

### Fixed
- **Critical**: Fixed addon packaging issue where `blender-remote-cli install` failed after pip installation
- Moved Blender addon files from `blender_addon/` to `src/blender_remote/addon/` for proper packaging
- Updated pyproject.toml to use `package-data` instead of `data-files` for addon inclusion
- Modernized resource access in CLI with fallback chain: importlib.resources → importlib_resources → pkg_resources
- Both `bld_remote_mcp` and `simple-tcp-executor` addons now properly included in pip packages

## [1.2.0] - 2025-07-16

### Added
- **Cross-platform support**: Full Windows, Linux, and macOS compatibility
- **Auto-detection**: Automatic Blender installation detection on Windows and macOS
- **Base64 encoding**: Secure code transmission for complex scripts and cross-platform robustness
- **Data persistence**: Stateful workflows with key-value data storage across sessions
- **Background mode**: Robust background execution with proper signal handling and keep-alive loops
- **CLI enhancements**: Comprehensive command-line interface with configuration management
- **Debug tools**: Simple TCP executor addon for testing and development
- **Process management**: Improved start/stop/status commands with proper cleanup
- **Configuration system**: YAML-based configuration with OmegaConf integration
- **Socket optimization**: Enhanced socket handling with proper timeouts and error recovery

### Changed
- **Architecture**: Dual-mode server implementation (GUI timer-based + background queue-based)
- **Documentation**: Complete overhaul with cross-platform guides and API reference
- **CLI interface**: Unified command structure with improved error handling
- **Version consistency**: Synchronized version numbers across all components
- **Resource handling**: Modernized package resource access for better compatibility

### Fixed
- **Background mode**: Proper signal handling and process termination
- **Timer execution**: Resolved modal operator timer issues in background mode
- **Port conflicts**: Better detection and handling of port conflicts
- **Cross-platform paths**: Consistent path handling across operating systems
- **Installation**: Robust addon installation with proper error reporting

### Security
- **Code transmission**: Base64 encoding prevents code injection and encoding issues
- **Input validation**: Enhanced parameter validation for all MCP endpoints
- **Process isolation**: Improved separation between GUI and background modes

## [1.1.0] - 2025-07-09

### Added
- **Automation focus**: Enhanced automation capabilities for batch operations
- **Scene management**: Improved scene manipulation and object handling
- **Export features**: GLB/GLTF export functionality with proper error handling
- **Asset management**: Basic asset loading and manipulation capabilities

### Changed
- **API structure**: Refined Python control API with better error handling
- **Documentation**: Updated examples and usage guides
- **Performance**: Optimized command execution and response handling

### Fixed
- **Connection stability**: Improved client-server connection reliability
- **Error handling**: Better error messages and exception handling
- **Memory management**: Reduced memory leaks in long-running sessions

## [1.0.0] - 2025-07-09

### Added
- **Initial release**: Basic Blender remote control functionality
- **MCP server**: Model Context Protocol server implementation
- **Python API**: Direct Python client API for programmatic control
- **CLI tools**: Basic command-line interface
- **Scene operations**: Fundamental scene manipulation capabilities
- **Screenshot capture**: Viewport screenshot functionality
- **Code execution**: Remote Python code execution in Blender
- **Multi-platform**: Initial Windows and Linux support

### Security
- **Local network**: Designed for local network use with basic authentication

## Release Notes

### Migration Guide: 1.2.0 to 1.2.1

This is a bugfix release that resolves a critical packaging issue. No API changes or breaking changes.

**If you experienced addon installation failures:**
1. Update to 1.2.1: `pip install --upgrade blender-remote`
2. Retry installation: `blender-remote-cli install`

### Migration Guide: 1.1.0 to 1.2.0

**Breaking Changes:**
- CLI command structure has changed. Use `blender-remote-cli --help` for new commands.
- Configuration now uses YAML format instead of JSON.
- Some API endpoints have new parameter names for consistency.

**New Features:**
- Run `blender-remote-cli init` to set up auto-detection on Windows/macOS.
- Use `--use-base64` and `--return-base64` flags for robust code transmission.
- Background mode now supports proper signal handling and cleanup.

### Migration Guide: 1.0.0 to 1.1.0

**New Features:**
- Enhanced scene management with better object manipulation.
- GLB export functionality for 3D asset workflows.
- Improved error handling and connection stability.

## Support

- **Documentation**: https://igamenovoer.github.io/blender-remote/
- **Repository**: https://github.com/igamenovoer/blender-remote
- **Issues**: https://github.com/igamenovoer/blender-remote/issues
- **PyPI**: https://pypi.org/project/blender-remote/

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.