# Data persistence in BLD_Remote_MCP in-memory cache

This feature allows data to persist across `execute_command()` calls in the MCP server, enabling stateful operations using multiple commands, also allows delayed result to be returned to the client (client can request for the result later explicitly).

## On BLD_Remote_MCP side
usage pattern (within blender):

```python
import bld_remote

# get data by key
data = bld_remote.persist.get_data(key, default=None)

# put data by key, data can be anything
bld_remote.persist.put_data(key, data)

# remove data
bld_remote.persist.remove_data(key)

# clear all data
bld_remote.persist.clear_data()
```

note that, although `bld_remote.persist` looks like a `dict`, we still make our own `PersistData` class to handle the data persistence, for future extensibility and flexibility.

in the blender addon `__init__.py`, you also need to import other functions to support MCP server call, see below

## On MCP server side
On the MCP server side `src/blender_remote/mcp_server.py`, we will have a these tools for LLM to use:
- `put_persist_data(key, data, ...)`, store or update data with a key, the data will be sent to `BLD_Remote_MCP`.
- `get_persist_data(key, ...)`, retrieve data by key, if not found, return `default` value, this api should has a way to signify that the data is not found.
- `remove_persist_data(key, ...)`, remove data by key, if not found, do nothing.
- note that, fastmcp will handle the data serialization and deserialization

## On Python client side
On the Python client side, `context/refcode/auto_mcp_remote/blender_mcp_client.py`, we will have these python api for human to use:
- `put_persist_data(key, data: Any)`, store or update data (of any type) with a key, the data will be sent to `BLD_Remote_MCP`. Data will be serialized with pickle and base64 encoded before sending.
- `get_persist_data(key, default=None)`, retrieve data by key, if not found, return `default` value. Data will be deserialized from base64 and de-pickle and returned. If the data is not found, it will return `None` by default.
- `remove_persist_data(key) -> True/False`, remove data by key, if not found, do nothing, return `True` if the data is removed, `False` if the data is not found.

## Reference
- `context/hints/blender-kb/howto-persist-data-in-blender.md`, how to persist data in Blender, we prefer using a simple Python pattern. 
  
## Notes
- blender's python environment is pretty barebone, things like `pydantic`, `attrs` are not available, python builtin libraries are ok. Advanced libraries can be used on the MCP server side or python client side.
