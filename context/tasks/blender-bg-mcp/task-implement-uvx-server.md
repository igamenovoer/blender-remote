before we discuss feature req, make sure you know these names, which you can find in project memory:
`blender-mcp`, `BlenderAutoMCP`, `BLD_Remote_MCP`

now here is the feature request.

in `blender-mcp`, it as a `server.py` module, which allows it to work when executing `uvx blender-mcp`, and this command can be added to LLM-assisted IDE as MCP server, for example in vscode:

```json
"mcp": {
    "blender-mcp": {
        "type": "stdio",
        "command": "uvx",
        "args": [
            "blender-mcp"
        ]
    },
},
```

we also want this feature, we want to use `uvx blender-remote` to startup our server, for it to be used by LLM-assisted IDE as MCP server.