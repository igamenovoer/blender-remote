We need to add some arguments to our IDE-side MCP server `uvx blender-remote` command to support additional features

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