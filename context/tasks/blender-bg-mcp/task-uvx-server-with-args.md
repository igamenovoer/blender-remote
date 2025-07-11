✅ **COMPLETED** - We need to add some arguments to our IDE-side MCP server `uvx blender-remote` command to support additional features

```json
"mcp": {
    "blender-mcp": {
        "type": "stdio",
        "command": "uvx",
        "args": [
            "blender-mcp",
            "--host", <= this is the new argument
            "127.0.0.1",
            "--port", <= this is the new argument
            "6688"
        ]
    },
},
```

we allow the user to specify the host and port for the `BLD_Remote_MCP`, so that it can find the blender-side mcp service.

if not specified, then default value is:
- for port, we will look at the `~/.config/blender-remote/bld-remote-config.yaml` file, and use the `mcp_service.default_port` as the port. If not found either, then use `6688` as the default port.
- for host, we will use `127.0.0.1` as the default host.
- print host info to stdout when starting the server, so that user can see it easily.

## Implementation Status

✅ **COMPLETED** (2025-07-11)
- Added `--host` and `--port` arguments to `uvx blender-remote` command
- Implemented config file integration with priority system (CLI > config > default)
- Added connection info display to stdout
- Comprehensive testing completed
- Git commit: `aa71001`

### Usage Examples:
```bash
# Default settings
uvx blender-remote

# Custom host and port
uvx blender-remote --host 192.168.1.100 --port 7777

# Override port only
uvx blender-remote --port 9999
```

### IDE Configuration:
```json
"mcp": {
    "blender-mcp": {
        "type": "stdio",
        "command": "uvx",
        "args": [
            "blender-remote",
            "--host", "127.0.0.1",
            "--port", "6688"
        ]
    }
}
```