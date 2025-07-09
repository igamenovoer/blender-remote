# Pythontic Interface to Control Blender via MCP

With `BLD_Remote_MCP`, we can now auto-start MCP (model context protocol) service within Blender and control it via MCP, this is convenient for LLM but not for human programmer. For human programmer, we need python APIs, running outside of Blender process and control Blender using pythonic interfaces, encapsulating the MCP calls.

The goal is to develop a set of pythonic classes and functions to provide human-friendly control facilities, to remotely control a Blender process.

## Design

A reference design is in `context/refcode/auto_mcp_remote` (actually you can copy most APIs here with minimal changes),which includes:
- `BlenderMCPClient`, a client that talk to blender via MCP calls, primarily allowing arbitrary code to be sent to Blender and get executed. It mimics the way `src/blender_remote/mcp_server.py` communicates with the addon on the blender side (`blender_addon/bld_remote_mcp`), and expose the addon's functionality as pythonic APIs. This client is the basis of everything else, much like a specialized socket on which other communication functions built.
- `BlenderSceneManager`, provides high-level functions to manage objects in the current blender scene, which mainly executes code via `BlenderMCPClient`
- `BlenderAssetManager`, provides APIs to access the Blender Asset Library, like instancing the assets, listing assets, etc.

We wrap many of the data objects using `attrs` structures, with these convention:
- by default use `@attrs.define(kw_only=True, eq=False)` for attrs classes, forcing users to be explicit with the named arguments
- whenever possible, allow all members to have default values, using `[]` for list and `{}` for dict (note that you have to use factory method in attrs definitions), or `None` as default. This allows for exploration of object members
- minimize redundency, if a member can be computed from another, then you should make it into a property and compute the value on the flow


