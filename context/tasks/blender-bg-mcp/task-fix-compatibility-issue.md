When `BlenderAutoMCP` is developed, it is intended as a drop-in replacement of the `blender-mcp` plugin (context/refcode/blender-mcp), so that `context/refcode/blender-mcp/src/blender_mcp/server.py` can communicate with the `BlenderAutoMCP` addon ('context/refcode/blender_auto_mcp/__init__.py') directly. In that sense, `BlenderAutoMCP` and `blender-mcp` has the exact same communication protocol that they can be used interchangably.

This is also a requirement for `BLD_Remote_MCP`, we expect LLMs like Gemini or Sonnet who can talk to the `blender-mcp` (`context/refcode/blender-mcp/src/blender_mcp/server.py`) can also directly talk to `BLD_Remote_MCP`, sending and receiving TCP messages from port 9876 via direct socket connection. Note that, we DO NOT need to support functions related to 3rd asset providers (`context/refcode/blender_auto_mcp/asset_providers.py`).

Now when `BLD_Remote_MCP` is running, and I set it to run in port 9876, and try it with LLM, something goes wrong

on the LLM side:
```
Error getting scene info: Connection to Blender lost: [Errno 104] Connection reset by peer
```

on the blender side:
```
[BLD Remote][INFO][23:23:30]    task #0: pending - <Task pending name='Task-4' coro=<BaseSelectorEventLoop._accept_connection2() running at /apps/blender-4.4.3-linux-x64/4.4/python/lib/python3.11/asyncio/selector_events.py:222> wait_for=<Future pending cb=[Task.task_wakeup()]>>
[BLD Remote][INFO][23:23:30]    task #1: pending - <Task pending name='Task-3' coro=<Server.serve_forever() running at /apps/blender-4.4.3-linux-x64/4.4/python/lib/python3.11/asyncio/base_events.py:370> wait_for=<Future pending cb=[Task.task_wakeup()]>>
[BLD Remote][INFO][23:23:30] NEW CLIENT CONNECTION from ('127.0.0.1', 40826) to ('127.0.0.1', 9876)
[BLD Remote][INFO][23:23:30] Transport details: <_SelectorSocketTransport fd=37 read=idle write=<idle, bufsize=0>>
[BLD Remote][INFO][23:23:30] Connection established at 1751988210.4837801
[BLD Remote][INFO][23:23:30] kick_async_loop (call #23651): 2 tasks to process
[BLD Remote][INFO][23:23:30] Processing 2 active tasks...
[BLD Remote][INFO][23:23:30]    task #0: pending - <Task pending name='Task-4' coro=<BaseSelectorEventLoop._accept_connection2() running at /apps/blender-4.4.3-linux-x64/4.4/python/lib/python3.11/asyncio/selector_events.py:222> wait_for=<Future finished result=None>>
[BLD Remote][INFO][23:23:30]    task #1: pending - <Task pending name='Task-3' coro=<Server.serve_forever() running at /apps/blender-4.4.3-linux-x64/4.4/python/lib/python3.11/asyncio/base_events.py:370> wait_for=<Future pending cb=[Task.task_wakeup()]>>
[BLD Remote][INFO][23:23:32] kick_async_loop (call #24001): 1 tasks to process
[BLD Remote][INFO][23:23:32] Processing 1 active tasks...
[BLD Remote][INFO][23:23:32]    task #0: pending - <Task pending name='Task-3' coro=<Server.serve_forever() running at /apps/blender-4.4.3-linux-x64/4.4/python/lib/python3.11/asyncio/base_events.py:370> wait_for=<Future pending cb=[Task.task_wakeup()]>>
[BLD Remote][INFO][23:23:37] kick_async_loop (call #25001): 1 tasks to process
[BLD Remote][INFO][23:23:37] Processing 1 active tasks...
[BLD Remote][INFO][23:23:37]    task #0: pending - <Task pending name='Task-3' coro=<Server.serve_forever() running at /apps/blender-4.4.3-linux-x64/4.4/python/lib/python3.11/asyncio/base_events.py:370> wait_for=<Future pending cb=[Task.task_wakeup()]>>
[BLD Remote][INFO][23:23:43] kick_async_loop (call #26001): 1 tasks to process
[BLD Remote][INFO][23:23:43] Processing 1 active tasks...
[BLD Remote][INFO][23:23:43]    task #0: pending - <Task pending name='Task-3' coro=<Server.serve_forever() running at /apps/blender-4.4.3-linux-x64/4.4/python/lib/python3.11/asyncio/base_events.py:370> wait_for=<Future pending cb=[Task.task_wakeup()]>>
[BLD Remote][INFO][23:23:43] DATA RECEIVED: 46 bytes at 1751988223.530939
[BLD Remote][INFO][23:23:43] Raw data preview: b'{"type": "get_polyhaven_status", "params": {}}'
[BLD Remote][INFO][23:23:43] Attempting to decode data as UTF-8...
[BLD Remote][INFO][23:23:43] Data decoded successfully, length: 46
[BLD Remote][INFO][23:23:43] Attempting to parse JSON...
[BLD Remote][INFO][23:23:43] JSON parsed successfully: <class 'dict'> with keys ['type', 'params']
[BLD Remote][INFO][23:23:43] Calling process_message()...
[BLD Remote][INFO][23:23:43] process_message() called with data keys: ['type', 'params']
[BLD Remote][INFO][23:23:43] Current server_port: 9876
[BLD Remote][INFO][23:23:43] Initial response prepared: {'response': 'OK', 'message': 'Task received', 'source': 'tcp://127.0.0.1:9876'}
[BLD Remote][INFO][23:23:43] Final response: {'response': 'OK', 'message': 'Task received', 'source': 'tcp://127.0.0.1:9876'}
[BLD Remote][INFO][23:23:43] process_message() returned: {'response': 'OK', 'message': 'Task received', 'source': 'tcp://127.0.0.1:9876'}
[BLD Remote][INFO][23:23:43] Encoding response as JSON...
[BLD Remote][INFO][23:23:43] Response encoded: 80 bytes
[BLD Remote][INFO][23:23:43] Sending response to client...
[BLD Remote][INFO][23:23:43] Response sent successfully
[BLD Remote][INFO][23:23:43] Closing client connection...
[BLD Remote][INFO][23:23:43] Client connection closed successfully
[BLD Remote][INFO][23:23:43] CLIENT CONNECTION CLOSED normally (duration: 13.053s)
[BLD Remote][INFO][23:23:43] Connection ended at 1751988223.5366392
[BLD Remote][INFO][23:23:48] kick_async_loop (call #27001): 1 tasks to process
[BLD Remote][INFO][23:23:48] Processing 1 active tasks...
```