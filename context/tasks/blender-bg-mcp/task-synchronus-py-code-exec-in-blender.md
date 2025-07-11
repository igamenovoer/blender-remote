# Task: Synchronous Python Code Execution in BLD_Remote_MCP

**Created:** 2025-07-11  
**Priority:** High  
**Complexity:** Very High  
**Status:** Planning  

## Overview

Rewrite the core execution engine of BLD_Remote_MCP to provide synchronous Python code execution with immediate result return, while maintaining the existing asynchronous version as a fallback option.

## Current State Analysis

### Existing Architecture (BLD_Remote_MCP_Async)
- **Current Name**: `bld_remote_mcp` addon
- **Future Name**: `bld_remote_mcp_async` (renamed)
- **Future Reference**: `BLD_Remote_MCP_Async`
- **Execution Model**: Asynchronous via Blender timer system
- **Response Pattern**: `{"response": "OK", "message": "Code execution scheduled"}`
- **Output Location**: Blender console (not captured in response)
- **Advantages**: Non-blocking, handles complex operations, stable
- **Disadvantages**: No direct result capture, debugging difficulties

### Reference Implementation (BlenderAutoMCP)
- **Location**: `context/refcode/blender_auto_mcp/server.py`
- **Execution Model**: **Synchronous execution in Blender**
- **Key Reference**: BlenderAutoMCP already implements synchronous Python execution
- **Response Pattern**: Direct result return with captured output
- **Architecture**: Proven synchronous execution pattern in production
- **Status**: ✅ **CRITICAL REFERENCE** - Use this as primary implementation guide

### Target Architecture (BLD_Remote_MCP_Sync)
- **Name**: `BLD_Remote_MCP` (new default)
- **Execution Model**: Synchronous with immediate execution
- **Threading Model**: **Threading-based** (not asyncio) for request handling and data transmission
- **Keep-alive Strategy**: **Non-stop loop** in addon, external script handles Blender background keep-alive
- **Response Pattern**: `{"status": "success", "result": {...}, "output": "..."}`
- **Output Location**: Captured and returned in TCP response
- **Exit Strategy**: SystemExit exception (breaks loop in background, shuts down in GUI)
- **Advantages**: Direct result access, better debugging, API completeness, simplified architecture
- **Challenges**: Threading constraints, blocking concerns, output capture

## Technical Challenges

### 1. **Blender Threading Constraints**
- **Issue**: Blender's API is not thread-safe
- **Constraint**: All bpy operations must run on main thread
- **Challenge**: TCP server runs in asyncio context, needs main thread access
- **Complexity**: High

### 2. **Output Capture Mechanism**
- **Current**: `print()` statements go to console
- **Target**: Capture all output (stdout, stderr, Blender logs)
- **Requirements**:
  - Capture `print()` statements
  - Capture `bpy.ops` feedback
  - Capture error tracebacks
  - Capture custom logging output
- **Implementation**: Context managers, IO redirection, custom handlers
- **Complexity**: Very High

### 3. **Result Value Extraction**
- **Challenge**: Python `exec()` doesn't return values directly
- **Solutions**:
  - Globals/locals inspection for result variables
  - Custom result assignment conventions
  - Expression evaluation vs statement execution
  - JSON serialization of complex objects
- **Complexity**: High

### 4. **Error Handling and Recovery**
- **Current**: Errors logged, service continues
- **Target**: Structured error responses with full context
- **Requirements**:
  - Exception capture with full traceback
  - Blender state recovery after errors
  - Timeout handling for infinite loops
  - Memory cleanup after failed operations
- **Complexity**: Very High

### 5. **Performance and Blocking**
- **Issue**: Synchronous execution can block TCP server
- **Mitigation Strategies**:
  - Execution timeouts
  - Interruptible execution patterns
  - Resource monitoring
  - Client connection management
- **Trade-offs**: Responsiveness vs completeness
- **Complexity**: High

## Core Implementation Strategy

### 1. **Threading-Based Architecture (Not Asyncio)**
- **Design Decision**: Use Python `threading` module instead of `asyncio` for the synchronous version
- **Request Handling**: Each client connection handled by dedicated thread
- **Data Transmission**: Synchronous socket operations with thread-safe data structures
- **Server Loop**: Non-stop `while True` loop in main thread for server socket acceptance
- **Rationale**: Simplifies synchronous execution, eliminates asyncio complexity
- **Implementation Pattern**:
  ```python
  # Main server thread
  while self.running:
      client_socket, address = server_socket.accept()
      client_thread = threading.Thread(target=self._handle_client, args=(client_socket,))
      client_thread.start()
  ```

### 2. **Simplified Background Mode Keep-Alive**
- **Key Insight**: **BLD_Remote_MCP addon is NOT responsible for keeping Blender alive**
- **Background Mode Strategy**: External startup script (`blender --background --python script.py`) handles keep-alive
- **Existing Implementation**: **REFERENCE** `src/blender_remote/cli.py` - `blender-remote-cli start --background`
- **Proven Pattern**: CLI already creates startup scripts for background mode keep-alive
- **Addon Responsibility**: Only manage TCP server and client connections
- **No Modal Operators**: Eliminate complex Blender modal operator keep-alive mechanisms
- **Simplified Logic**: Addon can focus solely on TCP service, not Blender process management
- **Architecture Benefit**: Cleaner separation of concerns, easier testing and debugging
- **Existing CLI Pattern** (from `cli.py`):
  ```python
  # Current async version in cli.py (lines 435-501)
  import time, signal, sys
  _keep_running = True
  
  def signal_handler(signum, frame):
      global _keep_running
      _keep_running = False
      # Cleanup MCP service
      sys.exit(0)
  
  signal.signal(signal.SIGINT, signal_handler)
  signal.signal(signal.SIGTERM, signal_handler)
  
  # Current: drives async_loop.kick_async_loop()
  while _keep_running:
      if async_loop.kick_async_loop():
          break
      time.sleep(0.05)
  ```
- **Synchronous Version Pattern**:
  ```python
  # Simplified for threading-based sync version
  import bld_remote
  bld_remote.start_mcp_service()  # Start sync service
  while _keep_running:
      time.sleep(1)  # Simple keep-alive, no async loop
  ```

### 3. **SystemExit Exception Strategy**
- **Exit Mechanism**: Continue using `SystemExit` exception for shutdown requests
- **Background Mode Behavior**: SystemExit breaks out of outermost keep-alive loop in external script
- **GUI Mode Behavior**: SystemExit directly shuts down Blender application  
- **Implementation**: No changes needed to exit handling logic
- **Thread Safety**: SystemExit in client thread triggers graceful server shutdown
- **Cleanup Process**:
  ```python
  # In client handler thread
  if "quit_blender" in code:
      self._cleanup_connections()
      raise SystemExit("Shutdown requested")
  ```

## Implementation Strategy

### Phase 0: Reference Study (CRITICAL)
1. **Analyze BlenderAutoMCP Implementation**: 
   - **PRIMARY REFERENCE**: `context/refcode/blender_auto_mcp/server.py`
   - Study synchronous execution patterns
   - Understand output capture mechanisms
   - Analyze error handling strategies
   - Extract threading and blocking solutions
2. **Document Key Patterns**: How BlenderAutoMCP achieves synchronous execution
3. **Identify Reusable Components**: Code patterns that can be adapted

### Phase 1: Architecture Preparation
1. **Rename existing addon**: `bld_remote_mcp` → `async_bld_remote_mcp`
2. **Update references**: All documentation and code to use `BLD_Remote_MCP_Async`
3. **Create new addon structure**: `bld_remote_mcp_sync` → `bld_remote_mcp`
4. **Dual compatibility**: Both versions available during transition
5. **BlenderAutoMCP Pattern Analysis**: Extract synchronous execution architecture
6. **CLI Keep-Alive Adaptation**: Modify `src/blender_remote/cli.py` background startup script for sync version

### Phase 2: Core Execution Engine (Threading-Based, BlenderAutoMCP Pattern)
1. **Threading-Based TCP Server**:
   ```python
   class BldRemoteMCPServer:
       def __init__(self, port=6688):
           self.port = port
           self.running = False
           self.server_socket = None
           self.client_threads = []
           
       def start(self):
           self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
           self.server_socket.bind(('127.0.0.1', self.port))
           self.server_socket.listen(5)
           self.running = True
           
           # Main server loop (non-stop, no asyncio)
           while self.running:
               client_socket, address = self.server_socket.accept()
               client_thread = threading.Thread(target=self._handle_client, args=(client_socket,))
               client_thread.start()
               self.client_threads.append(client_thread)
   ```

2. **Output Capture System** (Adapt from BlenderAutoMCP):
   ```python
   class OutputCapture:
       def __enter__(self):
           # Redirect stdout, stderr, Blender logs
           # REFERENCE: BlenderAutoMCP's output capture mechanism
       def __exit__(self):
           # Restore original streams, return captured output
           # REFERENCE: BlenderAutoMCP's stream restoration
   ```

3. **Synchronous Executor** (BlenderAutoMCP Pattern, Thread-Safe):
   ```python
   def execute_code_sync(code: str, timeout: float = 30.0) -> ExecutionResult:
       # REFERENCE: BlenderAutoMCP's synchronous execution approach
       # Executed in client thread, synchronous response
       with OutputCapture() as capture:
           with TimeoutContext(timeout):
               exec_globals = {...}
               exec(code, exec_globals, exec_globals)
               return ExecutionResult(
                   success=True,
                   output=capture.get_output(),
                   result=extract_result(exec_globals),
                   duration=capture.duration
               )
   ```

4. **Result Extraction Logic** (BlenderAutoMCP Method):
   - **REFERENCE**: Study how BlenderAutoMCP returns execution results
   - Convention: `_result` variable for return values
   - Automatic JSON serialization
   - Fallback to last expression value
   - Type-specific handlers (bpy objects, numpy arrays)

### Phase 3: Protocol Enhancement
1. **Enhanced Response Format**:
   ```json
   {
     "status": "success|error|timeout",
     "result": {...},
     "output": "captured stdout/stderr",
     "logs": ["blender log entries"],
     "duration": 1.234,
     "metadata": {
       "objects_created": ["Cube.001"],
       "scene_changes": true,
       "memory_usage": {...}
     }
   }
   ```

2. **Backward Compatibility**:
   - Support both sync and async modes
   - Client can specify execution mode
   - Graceful fallback to async for complex operations

### Phase 4: Advanced Features
1. **Execution Context Management**:
   - Isolated namespaces per connection
   - Persistent variables between calls
   - Context cleanup and reset

2. **Performance Monitoring**:
   - Execution time tracking
   - Memory usage monitoring
   - Resource utilization metrics

3. **Safety Features**:
   - Code validation and sandboxing
   - Resource limits (memory, time, file access)
   - Dangerous operation detection

## Technical Specifications

### Output Capture Implementation
```python
import sys
import io
import contextlib
from typing import Dict, Any, Optional

class BlenderOutputCapture:
    """Comprehensive output capture for Blender operations"""
    
    def __init__(self):
        self.stdout_buffer = io.StringIO()
        self.stderr_buffer = io.StringIO()
        self.blender_logs = []
        self.original_stdout = None
        self.original_stderr = None
        
    def __enter__(self):
        # Capture standard streams
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = self.stdout_buffer
        sys.stderr = self.stderr_buffer
        
        # Hook into Blender's logging system
        self._setup_blender_log_capture()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore streams
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        
        # Cleanup Blender hooks
        self._cleanup_blender_log_capture()
        
    def get_output(self) -> Dict[str, Any]:
        return {
            "stdout": self.stdout_buffer.getvalue(),
            "stderr": self.stderr_buffer.getvalue(), 
            "blender_logs": self.blender_logs
        }
```

### Execution Result Data Structure
```python
@dataclass
class ExecutionResult:
    success: bool
    output: Dict[str, str]  # stdout, stderr, logs
    result: Optional[Any]   # Extracted result value
    duration: float         # Execution time in seconds
    error: Optional[str]    # Error message if failed
    traceback: Optional[str] # Full traceback if failed
    metadata: Dict[str, Any] # Scene changes, objects created, etc.
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON-serializable format"""
        return {
            "status": "success" if self.success else "error",
            "result": self._serialize_result(),
            "output": self.output,
            "duration": self.duration,
            "error": self.error,
            "traceback": self.traceback,
            "metadata": self.metadata
        }
```

## Migration Path

### 1. **Gradual Transition**
- Keep `BLD_Remote_MCP_Async` as stable fallback
- Introduce `BLD_Remote_MCP_Sync` as experimental
- Client-side configuration for execution mode choice
- Performance comparison and validation

### 2. **Compatibility Layer**
```python
# Client can request execution mode
{
    "type": "execute_code",
    "params": {
        "code": "import bpy; print('test')",
        "execution_mode": "sync|async",  # Default: sync
        "timeout": 30.0,
        "capture_output": True
    }
}
```

### 3. **Testing Strategy**
- Comprehensive test suite for both modes
- Performance benchmarking
- Memory usage analysis
- Stability testing under load
- Error handling validation

## Risk Assessment

### High Risk Areas
1. **Thread Safety**: Blender API threading constraints
2. **Performance**: Blocking vs responsiveness trade-offs
3. **Stability**: Complex output capture and error handling
4. **Compatibility**: Breaking changes to existing workflows

### Mitigation Strategies
1. **Extensive Testing**: Automated test suites for edge cases
2. **Gradual Rollout**: Optional feature with fallback
3. **Performance Monitoring**: Real-time metrics and alerts
4. **Documentation**: Clear migration guides and examples

## Success Criteria

### Functional Requirements
- ✅ Immediate execution results returned in TCP response
- ✅ Complete output capture (stdout, stderr, Blender logs)
- ✅ Structured error handling with full context
- ✅ Backward compatibility with existing clients
- ✅ Performance acceptable for typical operations

### Quality Requirements
- ✅ No regression in stability compared to async version
- ✅ Memory usage remains within acceptable bounds
- ✅ Comprehensive test coverage (>90%)
- ✅ Documentation and examples for both modes

### Performance Targets
- **Simple operations**: <100ms execution time
- **Complex geometry**: <5s execution time
- **Memory overhead**: <50MB additional usage
- **Concurrent clients**: Support 5+ simultaneous connections

## Dependencies

### Code Dependencies
- **Existing**: `async_bld_remote_mcp` (renamed current version)
- **New**: `bld_remote_mcp` (synchronous version)
- **Shared**: `persist.py`, `utils.py`, `config.py`
- **CRITICAL REFERENCE**: `context/refcode/blender_auto_mcp/server.py`
- **BACKGROUND KEEP-ALIVE REFERENCE**: `src/blender_remote/cli.py` (lines 435-501)

### External Dependencies
- **Blender API**: Thread-safe operation patterns
- **Python threading**: Multi-threaded client handling (NOT asyncio)
- **Python socket**: Synchronous TCP server operations
- **JSON serialization**: Complex object handling

### Reference Implementation Dependencies
- **BlenderAutoMCP**: Primary architectural reference for synchronous execution
- **BlenderAutoMCP Patterns**: Output capture, error handling, threading solutions

### Architecture Simplifications
- **No asyncio**: Threading-based approach eliminates asyncio complexity
- **No modal operators**: External script handles background keep-alive
- **No complex event loops**: Simple `while True` server loop
- **Simplified exit handling**: SystemExit works in both GUI and background modes

## Timeline Estimate

- **Phase 0** (BlenderAutoMCP Study): 1-2 days
- **Phase 1** (Architecture): 2-3 days
- **Phase 2** (Core Engine): 5-7 days  
- **Phase 3** (Protocol): 2-3 days
- **Phase 4** (Advanced Features): 3-5 days
- **Testing & Documentation**: 3-4 days

**Total Estimate**: 16-24 development days

## Notes

This is a **fundamental architectural change** that affects the core execution model of the entire BLD_Remote_MCP system. The complexity is very high due to:

1. **Blender's Threading Model**: Requires careful coordination with main thread
2. **Output Capture Complexity**: Multiple output streams and logging systems
3. **Error Handling**: Robust recovery from arbitrary Python code execution
4. **Performance Trade-offs**: Balancing immediacy with responsiveness

The implementation should proceed cautiously with extensive testing at each phase to ensure system stability and performance.

## Key Architectural Benefits

### **Simplified Threading Architecture**
- **No asyncio complexity**: Eliminates event loop management and async/await patterns
- **Standard threading**: Uses familiar Python threading patterns for multi-client handling
- **Synchronous execution**: Direct execution in client threads with immediate results
- **Easier debugging**: Standard thread debugging tools and patterns apply

### **Clean Separation of Concerns**  
- **Addon responsibility**: Only TCP server and client connection management
- **External script responsibility**: Blender process keep-alive in background mode
- **No modal operators**: Eliminates complex Blender-specific keep-alive mechanisms
- **Clear exit strategy**: SystemExit works consistently across GUI and background modes

### **BlenderAutoMCP Proven Patterns**
- **Reference implementation**: Working synchronous execution already exists
- **Output capture**: Proven mechanisms for capturing execution results
- **Error handling**: Tested patterns for robust error recovery
- **Threading solutions**: Working solutions for Blender API thread constraints

### **Existing CLI Keep-Alive Infrastructure**
- **Proven background mode**: `blender-remote-cli start --background` already works
- **Startup script generation**: CLI creates temporary Python scripts for background keep-alive
- **Signal handling**: SIGINT/SIGTERM handlers already implemented
- **Process management**: Temporary file cleanup and graceful shutdown already working
- **Simple adaptation**: Only need to replace `async_loop.kick_async_loop()` with simple `time.sleep(1)`

This simplified approach significantly reduces implementation complexity while leveraging proven patterns from both BlenderAutoMCP's successful synchronous execution model AND the existing CLI's background mode infrastructure.