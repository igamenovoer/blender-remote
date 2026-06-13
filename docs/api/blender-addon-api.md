# Blender Addon API Reference

The `BLD_Remote_MCP` addon runs a TCP server inside Blender, allowing external applications to send commands and execute Python code. It also provides a Python module, `bld_remote`, for direct use in Blender scripts.

**File:** `src/blender_remote/addon/bld_remote_mcp/__init__.py`

## `bld_remote` Python Module

When the addon is enabled, it registers a module named `bld_remote` that can be imported directly in Blender's Python environment. This is the primary way to control the MCP service from other scripts within Blender.

```python
import bld_remote

# Check if the server is running
status = bld_remote.get_status()
print(f"Server running: {status['running']} on port {status['port']}")

# Start the service if it's not running
if not status['running']:
    bld_remote.start_mcp_service()
```

### Module Functions

#### `get_status()`
Returns a dictionary with the current status of the MCP service.

- **Returns (dict):** A dictionary containing `running` (bool), `port` (int), and other status info.

#### `start_mcp_service()`
Starts the TCP server. If the server is already running, this function does nothing. It will raise a `RuntimeError` if it fails to start (e.g., if the port is already in use).

#### `stop_mcp_service()`
Stops the TCP server and disconnects all clients.

#### `is_mcp_service_up()`
A quick check to see if the service is running.

- **Returns (bool):** `True` if the server is active, `False` otherwise.

#### `get_mcp_service_port()`
Gets the port number the server is configured to run on.

- **Returns (int):** The port number.

#### `set_mcp_service_port(port_number)`
Sets the port for the MCP service. This can only be called when the service is stopped.

- **`port_number` (int):** The new port to use.

#### `step()`
When running in **background mode**, this function must be called repeatedly in your script's main loop. It pumps the Blender job scheduler and processes any pending legacy main-thread commands from the queue. In GUI mode, the same scheduler is pumped automatically by a Blender timer so asynchronous user jobs, priority main-thread system operations, cooperative cancellation checkpoints, and terminal result recording continue while Blender owns the event loop.

**Example for background mode:**
```python
# From tests/mcp-server/test_background_screenshot.py
import bld_remote
import time
import sys

# Start the service
bld_remote.start_mcp_service()
print("Service started, waiting for connections...")

# Keep the script running
while True:
    try:
        bld_remote.step()  # Process pending commands
        time.sleep(0.01)   # Small delay to prevent CPU spinning
    except KeyboardInterrupt:
        bld_remote.stop_mcp_service()
        sys.exit(0)
```

#### `is_background_mode()`
Checks if Blender is running in headless (background) mode.

- **Returns (bool):** `True` if in background mode.

#### `get_startup_options()`
Gets the startup configuration options for the MCP service.

- **Returns (dict):** A dictionary containing startup options including port, host, and auto-start settings.

#### `get_command_queue_size()`
Gets the current size of the command queue (background mode only).

- **Returns (int):** The number of commands in the queue, or -1 if the queue is not available.

#### `persist`
The `bld_remote.persist` object provides a simple key-value store for persisting data across different commands or sessions.

- **`bld_remote.persist.put_data(key, data)`:** Stores a value.
- **`bld_remote.persist.get_data(key, default=None)`:** Retrieves a value.
- **`bld_remote.persist.remove_data(key)`:** Deletes a value.
- **`bld_remote.persist.get_keys()`:** Returns a list of all stored keys.

**Example:**
```python
import bld_remote

# Store some data
bld_remote.persist.put_data("my_key", {"value": 42})

# Retrieve data
data = bld_remote.persist.get_data("my_key")
print(f"Retrieved: {data}")

# List all keys
keys = bld_remote.persist.get_keys()
print(f"All keys: {keys}")
```

## Server Commands

The TCP server listens for JSON commands. These are the commands that the `BlenderMCPClient` sends.

### Scheduling model

`blender-remote` serializes all Blender main-thread work in one process. Asynchronous job submission means "accepted into a queue and inspectable by job id"; it does not mean multiple caller Python jobs run in parallel inside Blender. The scheduler has one active main-thread item, a normal FIFO lane for user jobs created by `submit_code_job` and synchronous `execute_code`, and a priority FIFO lane for fixed server-defined system operations such as scene/object inspection. A priority system operation accepted while another item is running starts after the active item and before already queued user jobs. Immediate control commands such as `get_job_status`, `get_job_result`, `cancel_job`, `get_queue_status`, `get_active_item`, and `list_jobs` only inspect or mutate scheduler/registry metadata and answer without entering the Blender main-thread executor.

Caller-provided Python is never accepted as a priority system operation. Any API that runs arbitrary code is classified as a normal user job and observes FIFO order behind earlier user jobs, even when the caller uses synchronous `execute_code`.

### `get_scene_info`
Retrieves a summary of the current scene. This is a server-defined main-thread system operation: it touches Blender state, so it is enqueued in the priority system-operation lane rather than answered from the socket thread.

- **Params:** None
- **Returns:** A dictionary with scene statistics, including object count and a list of the first 10 objects.

### `get_object_info`
Gets detailed information about a specific object.

- **Params:** `{"name": "ObjectName"}`
- **Returns:** A dictionary with the object's properties (location, rotation, materials, etc.).

### `execute_code`
Executes a string of Python code in Blender's global context and waits for the terminal result. This command is implemented as a synchronous facade over the Blender-side FIFO user-job queue: it creates an internal user job, waits for that job's terminal state, and returns the same successful result shape expected by existing MCP callers. It does not bypass earlier queued user jobs.

- **Params:**
    - `code` (str): The code to run.
    - `code_is_base64` (bool): Set to `True` if the code is base64 encoded.
    - `return_as_base64` (bool): Set to `True` to receive the result as a base64 encoded string.
    - `wait_timeout_seconds` (float, optional): Maximum time for this caller to wait for a response.
    - `job_timeout_seconds` (float, optional): Maximum time the Blender job itself is allowed to run before timeout cancellation is requested.
    - `detach_on_wait_timeout` (bool, optional): If `True`, a wait timeout can return a still-running job id instead of requesting cooperative cancellation.
- **Returns:** The result of the execution, typically the standard output, or a structured terminal status such as `cancelled` or `timed_out`.

### `submit_code_job`
Submits a string of Python code as an asynchronous Blender job and returns immediately with a job id. The job is still executed on Blender's main thread by the shared scheduler; asynchronous submission changes caller waiting behavior, not Blender concurrency. Multiple accepted jobs are appended to the normal user-job FIFO and run one at a time.

- **Params:**
    - `code` (str): The code to run.
    - `code_is_base64` (bool): Set to `True` if the code is base64 encoded.
    - `return_as_base64` (bool): Set to `True` to store the result as a base64 encoded string.
    - `job_timeout_seconds` (float, optional): Maximum time the Blender job itself is allowed to run before timeout cancellation is requested.
- **Returns:** A job snapshot containing `job_id`, `status`, timestamps, cancellation metadata, queue metadata such as `queue_position` when queued, and `terminal=false`.

### `get_job_status`
Returns lightweight status for a known Blender job id without waiting behind queued or running Blender work.

- **Params:** `{"job_id": "bld-job-..."}`
- **Returns:** A job snapshot without the terminal result payload, plus `found=true`; unknown jobs return `found=false`. Queued jobs include `queue_position`; the active job includes `active=true`.

### `get_job_result`
Returns the stored result or structured error for a known Blender job id. This command never re-runs code.

- **Params:** `{"job_id": "bld-job-..."}`
- **Returns:** A job snapshot including terminal result/error payloads when available; non-terminal jobs include a message that the job has not reached a terminal state.

### `cancel_job`
Requests cooperative cancellation for a known Blender job id and returns immediately. `cancel_job`, `get_job_status`, `get_job_result`, `get_queue_status`, `get_active_item`, and `list_jobs` are immediate control commands: they update or inspect the registry/scheduler directly and do not enter the main-thread Blender command queue.

- **Params:** `{"job_id": "bld-job-...", "reason": "optional reason"}`
- **Returns:** A job snapshot with `cancel_requested=true` and status usually `cancelling` for active jobs; terminal jobs keep their terminal status; unknown jobs return `found=false`.

Executing job code receives cooperative cancellation helpers in its global scope: `ctx`, `job_context`, `__bld_remote_job_context`, and `check_cancelled`. Long jobs should call `check_cancelled()` between expensive phases. This first implementation is checkpoint-bounded; it does not forcibly interrupt arbitrary Python or a blocking Blender C-level operation that never returns to Python.

### `get_queue_status`
Returns current scheduler state without entering the Blender main-thread executor.

- **Params:** None
- **Returns:** Active item metadata when present, queued user-job count and ids, queued system-operation count and ids, and configured capacity metadata.

### `get_active_item`
Returns the currently active main-thread item without entering the Blender main-thread executor.

- **Params:** None
- **Returns:** `{"active_item": null}` when idle, or an object with `kind`, `item_id`, `job_id` or `operation_id`, `command_type` when applicable, and `started_at`.

### `list_jobs`
Lists known job registry records without entering the Blender main-thread executor.

- **Params:** Optional `status`, `include_terminal`, `include_result`, and `limit`.
- **Returns:** A dictionary with `jobs`, `count`, and `limit`.

### `get_viewport_screenshot`
Captures a screenshot of the 3D viewport. This command only works when Blender is running in GUI mode.

- **Params:**
    - `max_size` (int): The maximum dimension for the image.
    - `filepath` (str): A path to save the file to. If not provided, a temporary file is created.
    - `format` (str): Image format (`"png"` or `"jpg"`).
- **Returns:** A dictionary with the `width`, `height`, and `filepath` of the saved image.

### `server_shutdown`
Gracefully shuts down the MCP server.

- **Params:** None
- **Returns:** A success message confirming shutdown.

### `get_polyhaven_status`
Gets the status of the Polyhaven addon integration.

- **Params:** None  
- **Returns:** A dictionary with the Polyhaven addon status.

### Data Persistence Commands

- **`put_persist_data`**: Stores data.
  - **Params:** `{"key": "my_key", "data": "my_data"}`
  - **Returns:** Confirmation of data storage.
- **`get_persist_data`**: Retrieves data.
  - **Params:** `{"key": "my_key", "default": "default_value"}`
  - **Returns:** The stored data or default value.
- **`remove_persist_data`**: Deletes data.
  - **Params:** `{"key": "my_key"}`
  - **Returns:** Confirmation of data removal.
