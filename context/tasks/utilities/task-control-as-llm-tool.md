in `scripts` dir, create a script name `mcp-server-cli.py`, which is a cli python script, which will start the mcp server `src/blender_remote/mcp_server.py`, and communicate with it using `stdio` method, just like how `uvx blender-remote` works. This script mimics the process an LLM talks to the MCP server, allowing users to control the MCP server as if it were an LLM tool, for testing.

This script is intended to be used like this:
- use python to run the script, e.g. `python mcp-server-cli.py start --port 12345 --host localhost &`, starting up the server
- use the same script to interact with the MCP server, e.g. `python mcp-server-cli.py stop`, which will stop the MCP server and kill the caller `mcp-server-cli.py` script
- use `python mcp-server-cli.py [OPTIONS]` to talk to the MCP server.
- shared information is in a temporary file, which is created when the MCP server starts, and removed when the MCP server exits. This file is named `blender-remote-mcp-server.sock` and is located in the user temporary directory (see python `tempfile`).

`~/.config/blender-remote/bld-remote-config.yaml` stores default user config, which is controled by `src/blender_remote/cli.py` script, which is a cli tool to manage the MCP server. The config file (aka `UserConfig`) contains the port and other settings for the MCP server. For many options, if the default value can be obtained from the config file, then the script will use that value as default.

It has the following subcommands and options:
- `start`, start the MCP server, which will run the `src/blender_remote/mcp_server.py` script in a subprocess, and communicate with it using `stdio` method. `mcp-server-cli.py` will block until the MCP server exits.
- - `--port`, the port used by `BLD_Remote_MCP`, if not specified, use default from `UserConfig`.
- - `--host`, the host used by `BLD_Remote_MCP`.
- - these host and port means the same as `uvx blender-remote` command.
- - starting the MCP server will create a file named `blender-remote-mcp-server.sock` in the user temporary directory (see python `tempfile`), saving information about the `mcp-server.cli.py` and MCP server, such as the port and host used, so that users can connect to it later. When the `mcp-server-cli.py` exits, this file will be removed.
- `stop`, stop the MCP server and the caller `mcp-server-cli.py`, just kill them, and remove the `blender-remote-mcp-server.sock` file.
- `usetool`, use the MCP server as an LLM tool, which will send the input to the MCP server and print the output, just like how IDE like vscode uses MCP tools.
- - `--input`, the input to send to the MCP server, which is a string.
- - `--output`, the output file to save the response from the MCP server, if not specified, print to stdout.
- `list`, list the available tools in the MCP server, which will send a request to the MCP server and print the response.