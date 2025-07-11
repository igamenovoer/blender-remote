# Data Persistence Examples

These examples show how to use the data persistence feature to maintain state across multiple commands.

## Prerequisites

1. Start Blender with BLD Remote MCP service:
   ```bash
   export BLD_REMOTE_MCP_START_NOW=1
   blender &
   ```

2. Verify service is running:
   ```bash
   # Test connection
   python -c "
   import socket, json
   s = socket.socket()
   s.connect(('127.0.0.1', 6688))
   s.send(json.dumps({'type': 'get_scene_info'}).encode())
   print('✅ Service is running')
   s.close()
   "
   ```

## Examples

### 01_basic_usage.py
Simple storage and retrieval operations.

### 02_multi_step_workflow.py  
Multi-step animation workflow with state persistence.

### 03_caching_expensive_operations.py
Cache expensive calculations to avoid recomputation.

## Running Examples

```bash
# Run individual examples
python examples/data-persistence/01_basic_usage.py
python examples/data-persistence/02_multi_step_workflow.py
python examples/data-persistence/03_caching_expensive_operations.py
```

## MCP Usage

For LLM integration, use these commands after connecting via MCP:
- `put_persist_data(key="my_data", data={"value": 123})`
- `get_persist_data(key="my_data")`
- `remove_persist_data(key="my_data")`