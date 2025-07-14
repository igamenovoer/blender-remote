Some important rules you should remember:

## Names
- `blender-mcp`, a 3rd party MCP server for Blender, which is used to run Blender code and get back the result for IDE like VSCode, is uses `Model Control Protocol (MCP)`. The source code is in `context/refcode/blender-mcp`. This project can be considered `stable`, can be used as reference. It as a blender addon and a python MCP server (`context/refcode/blender-mcp/src/blender_mcp/server.py`), the blender addon communicates with the MCP server using json-rpc, and MCP server communicates with the IDE using Model Control Protocol (MCP).

- `BlenderAutoMCP`, a 3rd party MCP server for Blender, based on `blender-mcp`, adds some features like auto-start and port specification via environment variable, for better automation and integration. The source code is in `context/refcode/blender_auto_mcp`. This project can be considered `stable`, can be used as reference. It as a blender addon (`context/refcode/blender_auto_mcp/server.py`), and compatible with `blender-mcp` MCP server, so it can be used as a drop-in replacement for `blender-mcp`. In addtion, it removes all supports for 3rd asset services, like `Poly Haven`, `Sketchfab`, etc., so it is more lightweight and focused on MCP server functionality.

- `BLD_Remote_MCP`, the blender addon of this project, is a drop-in replacement for `BlenderAutoMCP` and `blender-mcp` on the Blender side, it is used to run Blender code and get back the result by MCP server. It has its own MCP server implementation, can be started via `uvx blender-remote`, which is a drop-in replacement for `uvx blender-mcp` and `BlenderAutoMCP`. The main features it adds is support for use in blender background mode, staring with `blender --background` command. Compared to `blender-mcp` or `BlenderAutoMCP`, it has no GUI, and you have to inspect the logs to see what happens. Source code is in `blender_addon/bld_remote_mcp`.

- `BlenderRemoteMCPServer`, the MCP server of this project, paired with `BLD_Remote_MCP` addon. `uvx blender-remote` + `BLD_Remote_MCP` is a drop-in replacement for `uvx blender-mcp` + `BlenderAutoMCP`. The server is not compatible with `blender-mcp` or `BlenderAutoMCP`, but it is compatible with `BLD_Remote_MCP` addon. Source code is in `src/blender_remote/mcp_server.py`. 

- `BlenderClientAPI`, the Python client API of this project, is used to control Blender remotely via Python API, and it communicates directly with the `BLD_Remote_MCP` addon, circumventing the MCP server (`uvx blender-remote`). This is useful for advanced users who want to control Blender directly without going through the MCP server, sometimes even calling `BLD_Remote_MCP` methods that are not exposed by the MCP server due to protocol limitations. Source code is in `src/blender_remote`, mainly `client.py` and `scene_manager.py`.

- `blender-remote-cli`, a command line interface for this project, is used to start Blender in background mode and keep it alive, and configure the ports and different parameters for the MCP server and addon. It is implemented in `src/blender_remote/cli.py`. It creates a startup script to keep Blender alive in background. It also installs the `BLD_Remote_MCP` addon to Blender, so you can use it without manually installing the addon. 

## Blender Process Management

You will need to start and stop the blender process quite often, so you need to know how to do it properly.

- Blender path: `/apps/blender-4.4.3-linux-x64/blender`
- To start in GUI mode, just run the executable, to start in background mode, use `blender --background`.
- Always start blender with `&`, so that it runs in background and does not block the terminal, and because it starts quite fast, in your Bash() command that starts Blender, you should ONLY timeout in 10 seconds, DO NOT wait for 2 minutes as default. It will not exit until you stop it manually, so NEVER TRY to wait for it to exit.

### NEW
- always prefer to use `blender-remote-cli` command to start Blender, it will create a startup script to keep Blender alive in background.

## Debugging Strategies
- `BlenderAutoMCP` with `uvx blender-mcp` consitutes a stable MCP server for Blender, so you can use it as a backup channel to test your code, if you find that `uvx blender-remote` + `BLD_Remote_MCP` does not work as expected. You can refer to `context/plans/mcp-server-comprehensive-test-plan.md` for details about how to test the MCP server.
- `mcp[cli]` can be used to test the MCP server, see `context/hints/howto-call-mcp-server-via-python.md` for details about how to use it.

## Development Environment

- During development, we use `pixi` to manage python packages and run python scripts, so DO NOT try to run python scripts directly, use `pixi run` command instead.

- For documentations, you can use:
- - graphviz to generate diagrams, using `dot` command, and put the generated `.svg` files in appropriate directories.
- - we use `mkdocs-material` for documentation.

- some utilities:
- - `jq`, a command-line JSON processor, is available for manipulating JSON data.

- `<workspace>/tmp` is a temporary directory for storing temporary files, will be deleted frequently, you can use it to store temporary files, better create subdirectories for different purposes, so that it is easier to manage.