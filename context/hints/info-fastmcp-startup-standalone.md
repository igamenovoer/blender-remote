# How to Start FastMCP Server Standalone with Uvicorn

This guide explains how to run a `fastmcp` server as a standalone service using `uvicorn`, a lightning-fast ASGI server. This is useful for exposing the MCP server over HTTP, allowing clients to interact with it without using the standard `uvx` or `fastmcp run` commands.

## Key Concepts

- **ASGI**: Asynchronous Server Gateway Interface is a standard for Python asynchronous web servers and applications.
- **Uvicorn**: A high-performance ASGI server.
- **FastMCP as ASGI**: A `FastMCP` instance is a valid ASGI application, which means `uvicorn` can run it directly.

## Command to Run the Server

The general command to run an ASGI application with `uvicorn` is:

```bash
uvicorn [path.to.module]:[asgi_app_instance] --host [ip_address] --port [port_number]
```

### Applying to `blender-remote`

For the `blender-remote` MCP server located at `src/blender_remote/mcp_server.py`:

- **Module Path**: `src.blender_remote.mcp_server`
- **ASGI App Instance**: The `FastMCP` instance is named `mcp`.

Therefore, the command to start the server is:

```bash
uvicorn src.blender_remote.mcp_server:mcp --host 127.0.0.1 --port 8000
```

### Command Breakdown

- `uvicorn`: The command to start the uvicorn server.
- `src.blender_remote.mcp_server:mcp`: Specifies the location of the ASGI application.
  - `src.blender_remote.mcp_server`: The Python module path.
  - `mcp`: The variable name of the `FastMCP` instance inside that module.
- `--host 127.0.0.1`: The IP address to listen on. `127.0.0.1` for localhost.
- `--port 8000`: The port to listen on.

## Important Considerations

- **Working Directory**: This command must be run from the root of the `blender-remote` project directory so that `src` is in the Python path.
- **Dependencies**: Ensure that `uvicorn` and other necessary packages are installed in your environment. You can add it to your `pyproject.toml` or install it directly:
  ```bash
  pip install uvicorn
  ```
- **Blender Connection**: The `mcp_server.py` script is designed to connect to a running Blender instance. When you run the server with `uvicorn`, it will still attempt to connect to the Blender addon service on the host and port specified by its own command-line arguments or configuration. The `--host` and `--port` for `uvicorn` are for the MCP server itself, not for the connection to Blender.
