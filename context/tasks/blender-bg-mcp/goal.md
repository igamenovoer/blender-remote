# Minimal Blender MCP Service With Background Running Support

## Goal
We are developing a blender plugin that supports MCP (Model Context Protocol) in blender, so that it can be controlled by LLM.

The goal is to develop blender mcp server (inspired by `blender-mcp` in `context/refcode/blender-mcp`), which supports startup control with env variables, running without GUI so that it works in `blender --background` mode, and also has GUI when blender is started with GUI. Compared to the `blender-mcp`, this one is minimal, will NOT include access functions to 3rd party 3d model repositories (`sketchfab`, `Hyper3D`, `Poly Haven`, etc).

## Design

When printing logs to console, this plugin prints in this format:
`[BLD Remote][LogLevel][Time] <message>`

The plugin has two parts, as follows,

### Background MCP service

name this part as `mcp_bg_service`, it has the following features:
- no GUI, expected to be able to run in `blender --background` mode, will also run in blender GUI mode.
- runs in the background, within blender you can use python api to query its status and interact with it via python function calls.
- it is an MCP service like the `addon.py` in `blender-mcp` (context/refcode/blender-mcp), respond to normal MCP calls, the we expect on the python side we can use logics like `context/refcode/blender-mcp/src/blender_mcp/server.py` to interact with it.
- this background service can run along without GUI, so DO NOT call any GUI methods (in the coming sections).
- it supports multiple clients, client calls are just simply queued by the python runtime (like async or something), no concurrent call.

#### Environment Variable Control
it responds to these environment variables:
- `BLD_REMOTE_MCP_PORT=xxx`, set the default mcp port, if not set or empty, default port is `6688`
- `BLD_REMOTE_MCP_START_NOW=true/false`, default=false, whether to start the MCP service along with blender. If port conflict happens, print a warning. If env variable is not set or empty, treat it as false


#### Python API
It has an importable module, name it as `bld_remote`, and the user can do these:

```python
import bld_remote

# return a dict[str,str], as the status of the mcp service, it should also return something even if the mcp service is not running, in order to let the user deal with any error
bld_remote.get_status()

# start the mcp service, if already started then has no effect, if it fails to start then throw an exception, with reasons in it
bld_remote.start_mcp_service()

# stop the mcp service, similar to start_mcp_service(), disconnects all clients forcefully.
bld_remote.stop_mcp_service()

# return information about those environment variables
bld_remote.get_startup_options()

# return true/false, check if mcp service is up and running
bld_remote.is_mcp_service_up()

# set the port number of mcp service, only callable when mcp service is stopped, otherwise throws exception
bld_remote.set_mcp_service_port(port_number)

# the current configured port
bld_remote.get_mcp_service_port()
```

### GUI For User Interaction

name this part as `mcp_gui`, it can control the `mcp_bg_service` and display its status, just like the "view" in  model-view-controller architecture. it has the following features:
- this part starts with blender in GUI mode, shows itself in the `N panel` (viewport panel on the right side) as a menu, the menu name is `Blender Remote`

within menu, the user can:
- start/stop the `mcp_bg_service` with a start/stop button.
- a `refresh` button to get the mcp service status
- a text input, shown as `port:[text input]`, for the user to change MCP service port. If the port only applies when the `mcp_bg_service` is restarted (via start/stop or via python api)
- show the current running MCP service in `address:port` format, and whether the MCP service is stopped or started
- show the environment variables in the above used by mcp service.
- show usage of this plugin, within a foldable tag.

# Status Tracking

## Implementation Status

### Phase 1: Core Infrastructure (Priority: High)
- [ ] **1.1 Project Structure Setup**
  - [ ] Create `blender_addon/bld_remote_mcp/` directory structure
  - [ ] Implement basic addon registration in `__init__.py`
  - [ ] Set up logging system with format: `[BLD Remote][LogLevel][Time] <message>`

- [ ] **1.2 Configuration System**
  - [ ] Create `config.py` with environment variable handling
  - [ ] Implement configuration validation and defaults

- [ ] **1.3 Asyncio Integration**
  - [ ] Adapt `async_loop.py` from blender-echo-plugin
  - [ ] Ensure background-safe event loop management
  - [ ] Test asyncio integration in both GUI and background modes

### Phase 2: Background MCP Service (Priority: High)
- [ ] **2.1 MCP Server Implementation**
  - [ ] Create `mcp_bg_service.py` with FastMCP integration
  - [ ] Implement background-safe MCP server using asyncio patterns
  - [ ] Add connection handling for multiple clients
  - [ ] Implement graceful shutdown procedures

- [ ] **2.2 Command Handlers**
  - [ ] Create `command_handlers.py` with essential MCP tools
  - [ ] Implement `execute_python_code` tool
  - [ ] Implement `get_scene_info` tool
  - [ ] Implement `get_object_info` tool
  - [ ] Implement `create_primitive` tool
  - [ ] Implement `modify_object` tool
  - [ ] Implement `render_scene` tool

- [ ] **2.3 Python API Module**
  - [ ] Implement `get_status()` function
  - [ ] Implement `start_mcp_service()` function
  - [ ] Implement `stop_mcp_service()` function
  - [ ] Implement `get_startup_options()` function
  - [ ] Implement `is_mcp_service_up()` function
  - [ ] Implement `set_mcp_service_port(port)` function
  - [ ] Implement `get_mcp_service_port()` function

### Phase 3: GUI Components (Priority: Medium)
- [ ] **3.1 N Panel Implementation**
  - [ ] Create `mcp_gui.py` with Blender UI components
  - [ ] Implement "Blender Remote" panel in viewport N panel
  - [ ] Add conditional registration (GUI mode only)

- [ ] **3.2 GUI Controls**
  - [ ] Start/Stop button with service control
  - [ ] Refresh button for status updates
  - [ ] Port input field with validation
  - [ ] Status display (address:port, running/stopped)
  - [ ] Environment variables display
  - [ ] Collapsible usage information section

### Phase 4: Integration & Testing (Priority: High)
- [ ] **4.1 Startup Integration**
  - [ ] Implement environment variable-based auto-start
  - [ ] Add port conflict detection and warning
  - [ ] Test startup in both GUI and background modes

- [ ] **4.2 Error Handling**
  - [ ] Comprehensive exception handling
  - [ ] Graceful degradation when GUI unavailable
  - [ ] Connection error recovery

- [ ] **4.3 Testing Framework**
  - [ ] Unit tests for Python API
  - [ ] Integration tests for MCP service
  - [ ] Background mode testing
  - [ ] GUI functionality testing

## Next Steps
1. Begin Phase 1.1 - Set up project structure
2. Implement basic logging system
3. Create configuration handling for environment variables

## Notes
- Implementation plan created in `context/plans/blender-bg-mcp-implementation.md`
- Architecture based on patterns from blender-mcp and blender-echo-plugin references
- All tasks prioritized for systematic implementation approach