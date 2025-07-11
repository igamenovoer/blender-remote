Now we will mimic ourselves as LLM, and talk to the mcp server for testing.

## How to start blender
- use `blender-remote-cli start --port 5533` to start the blender in GUI mode, which will start the MCP server automatically.
- use `blender-remote-cli start --background --port 5544` to start blender in background mode, which will also start the MCP server automatically. This command will generate a keep-alive script that keeps Blender running in the background.

## The MCP server
- the mcp server is in `src/blender_remote/mcp_server.py` file, which is a python script that implements the MCP server functionality using `fastmcp` library.
- we will call this server is `OurMCPServer`, which is a MCP server that can be controlled by LLM tools.
- there is another mcp server, the `BlenderAutoMCP` server, which is a reference, source code in `context/refcode/auto_mcp_remote`, can be served as a side channel. For this,

## What to test
- test all the tools provided