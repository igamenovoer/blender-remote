# API reference

you need to write the API reference for the below sections, each section creates a separate file in the `docs/api` folder. Note that the documentation is built using the `mkdocs` tool.

The original `api-reference.md` is deprecated, we will remove them in the future.

For how to use the API, please refer to the `tests` folder.

## Python Client API

This section provides an overview of the Python client API for interacting with the Blender Addon. It includes all functions in 
- `src/blender_remote/client.py` 
- `src/blender_remote/scene_manager.py`
- `src/blender_remote/asset_manager.py`(not tested yet, use at your own risk)

## Blender Addon API

This section is about the Blender Addon API, called within blender, the `bld_remote` module, which you can find in the `src/blender_remote/addon/bld_remote_mcp/__init__.py` file.

## MCP Server API

This section is about the tools provided by the MCP server, to the LLM, which you can find in the `src/mcp_server/mcp_server.py` file.