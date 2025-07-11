# BLD Remote MCP Logging Control

The BLD Remote MCP addon now supports environment variable control for logging verbosity.

## Environment Variable

Set `BLD_REMOTE_LOG_LEVEL` to control which log messages are displayed:

- `DEBUG` - Shows all messages (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `INFO` - Shows INFO and above (INFO, WARNING, ERROR, CRITICAL) - **DEFAULT**
- `WARNING` - Shows WARNING and above (WARNING, ERROR, CRITICAL)  
- `ERROR` - Shows ERROR and above (ERROR, CRITICAL)
- `CRITICAL` - Shows only CRITICAL messages

The environment variable is case-insensitive and defaults to `INFO` if not set or invalid.

## Usage Examples

### Show only errors and critical messages:
```bash
export BLD_REMOTE_LOG_LEVEL=ERROR
blender --background --python-expr "import bld_remote; bld_remote.start_mcp_service()"
```

### Show all debug information:
```bash
export BLD_REMOTE_LOG_LEVEL=DEBUG
blender --background --python-expr "import bld_remote; bld_remote.start_mcp_service()"
```

### Suppress verbose logging (warnings and above only):
```bash
export BLD_REMOTE_LOG_LEVEL=WARNING
blender --background --python-expr "import bld_remote; bld_remote.start_mcp_service()"
```

## Available Log Functions

The utils module provides these logging functions:

- `log_debug(message)` - Debug information
- `log_info(message)` - General information  
- `log_warning(message)` - Warning messages
- `log_error(message)` - Error messages
- `log_critical(message)` - Critical messages

All messages follow the format: `[BLD Remote][LEVEL][TIME] message`

## Testing

Run the test suite to verify logging control:
```bash
python tests/test_logging_control.py
```