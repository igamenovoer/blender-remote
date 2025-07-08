# MCP Test Procedure for Blender Plugin

This document outlines the testing procedures for the BLD Remote MCP service running inside Blender.

## Prerequisites

- Blender 4.4.3 installed at `/apps/blender-4.4.3-linux-x64/blender`
- BLD Remote MCP plugin installed at `/home/igamenovoer/.config/blender/4.4/scripts/addons/bld_remote_mcp/`
- Python environment with socket and json libraries

## Service Configuration

- **Default Port**: 6688
- **Protocol**: JSON TCP
- **Message Format**: `{"message": "...", "code": "..."}`
- **Environment Variables**:
  - `BLD_REMOTE_MCP_PORT` - Override default port
  - `BLD_REMOTE_MCP_START_NOW` - Auto-start service on Blender launch

## Test Procedures

### 1. Basic Service Startup Test

**Objective**: Verify the MCP service starts correctly in Blender

**Steps**:
1. Kill any existing Blender processes: `pkill -f blender`
2. Start Blender with auto-start MCP:
   ```bash
   export BLD_REMOTE_MCP_START_NOW=1
   export BLD_REMOTE_MCP_PORT=6688
   /apps/blender-4.4.3-linux-x64/blender &
   ```
3. Wait 10 seconds for startup
4. Check if service is running:
   ```bash
   netstat -tlnp | grep 6688
   ps aux | grep blender | grep -v grep
   ```

**Expected Result**: 
- Port 6688 should be listening
- Blender process should be running
- No error messages in console

### 2. Basic Connection Test

**Objective**: Verify TCP connection can be established

**Test Script**:
```python
import socket
import json

def test_basic_connection():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(('127.0.0.1', 6688))
        print("✅ Connection established")
        sock.close()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

test_basic_connection()
```

**Expected Result**: Connection successful without errors

### 3. Basic Message Processing Test

**Objective**: Verify the service can receive and respond to messages

**Test Script**:
```python
import socket
import json

def test_message_processing():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect(('127.0.0.1', 6688))
        
        # Send a simple message
        message = {"message": "Hello from test", "code": "print('Test message received')"}
        sock.sendall(json.dumps(message).encode('utf-8'))
        
        # Receive response
        response = sock.recv(4096).decode('utf-8')
        print(f"Response: {response}")
        
        sock.close()
        return True
    except Exception as e:
        print(f"❌ Message processing failed: {e}")
        return False

test_message_processing()
```

**Expected Result**: Service responds without errors

### 4. Python Code Execution Test

**Objective**: Verify Python code can be executed in Blender context

**Test Script**:
```python
import socket
import json

def test_code_execution():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect(('127.0.0.1', 6688))
        
        # Test basic Python execution
        test_code = """
import bpy
scene_name = bpy.context.scene.name
object_count = len(bpy.context.scene.objects)
result = f"Scene: {scene_name}, Objects: {object_count}"
print(result)
"""
        
        message = {"message": "Execute Python code", "code": test_code}
        sock.sendall(json.dumps(message).encode('utf-8'))
        
        response = sock.recv(4096).decode('utf-8')
        print(f"Execution result: {response}")
        
        sock.close()
        return True
    except Exception as e:
        print(f"❌ Code execution failed: {e}")
        return False

test_code_execution()
```

**Expected Result**: Code executes and returns scene information

### 5. Blender API Access Test

**Objective**: Verify Blender API operations work correctly

**Test Script**:
```python
import socket
import json

def test_blender_api():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect(('127.0.0.1', 6688))
        
        # Test Blender API operations
        api_test_code = """
import bpy

# Create a new cube
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "TestCube"

# Get scene info
scene_info = {
    'scene_name': bpy.context.scene.name,
    'objects': [obj.name for obj in bpy.context.scene.objects],
    'active_object': bpy.context.active_object.name if bpy.context.active_object else None
}

print(f"Scene info: {scene_info}")
"""
        
        message = {"message": "Test Blender API", "code": api_test_code}
        sock.sendall(json.dumps(message).encode('utf-8'))
        
        response = sock.recv(4096).decode('utf-8')
        print(f"API test result: {response}")
        
        sock.close()
        return True
    except Exception as e:
        print(f"❌ Blender API test failed: {e}")
        return False

test_blender_api()
```

**Expected Result**: Cube created and scene information returned

### 6. Error Handling Test

**Objective**: Verify service handles errors gracefully

**Test Script**:
```python
import socket
import json

def test_error_handling():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect(('127.0.0.1', 6688))
        
        # Send invalid Python code
        invalid_code = """
import bpy
# This will cause an error
undefined_variable + 1
"""
        
        message = {"message": "Test error handling", "code": invalid_code}
        sock.sendall(json.dumps(message).encode('utf-8'))
        
        response = sock.recv(4096).decode('utf-8')
        print(f"Error handling result: {response}")
        
        sock.close()
        return True
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

test_error_handling()
```

**Expected Result**: Service returns error information without crashing

### 7. Multiple Connection Test

**Objective**: Verify service can handle multiple concurrent connections

**Test Script**:
```python
import socket
import json
import threading
import time

def single_connection_test(connection_id):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect(('127.0.0.1', 6688))
        
        code = f"print('Connection {connection_id} active')"
        message = {"message": f"Connection {connection_id}", "code": code}
        sock.sendall(json.dumps(message).encode('utf-8'))
        
        response = sock.recv(4096).decode('utf-8')
        print(f"Connection {connection_id} response: {response}")
        
        sock.close()
        return True
    except Exception as e:
        print(f"❌ Connection {connection_id} failed: {e}")
        return False

def test_multiple_connections():
    threads = []
    for i in range(5):
        thread = threading.Thread(target=single_connection_test, args=(i,))
        threads.append(thread)
        thread.start()
        time.sleep(0.1)  # Small delay between connections
    
    for thread in threads:
        thread.join()

test_multiple_connections()
```

**Expected Result**: All connections succeed without interference

### 8. Large Code Block Test

**Objective**: Verify service can handle large code submissions

**Test Script**:
```python
import socket
import json

def test_large_code_block():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(30)
        sock.connect(('127.0.0.1', 6688))
        
        # Generate a large code block
        large_code = """
import bpy
import bmesh

# Create multiple objects and perform operations
for i in range(10):
    # Add cube
    bpy.ops.mesh.primitive_cube_add(location=(i*3, 0, 0))
    cube = bpy.context.active_object
    cube.name = f"Cube_{i}"
    
    # Modify the cube
    bpy.context.view_layer.objects.active = cube
    bpy.ops.object.mode_set(mode='EDIT')
    
    # Use bmesh for modifications
    bm = bmesh.from_mesh(cube.data)
    bmesh.ops.subdivide_edges(bm, 
                             edges=bm.edges,
                             cuts=2,
                             use_grid_fill=True)
    bm.to_mesh(cube.data)
    bm.free()
    
    bpy.ops.object.mode_set(mode='OBJECT')

print(f"Created {len([obj for obj in bpy.context.scene.objects if obj.name.startswith('Cube_')])} cubes")
"""
        
        message = {"message": "Large code block test", "code": large_code}
        sock.sendall(json.dumps(message).encode('utf-8'))
        
        response = sock.recv(8192).decode('utf-8')
        print(f"Large code result: {response}")
        
        sock.close()
        return True
    except Exception as e:
        print(f"❌ Large code block test failed: {e}")
        return False

test_large_code_block()
```

**Expected Result**: Large code block executes successfully

## Comprehensive Test Runner

**Combined Test Script**:
```python
import socket
import json
import threading
import time

class MCPTester:
    def __init__(self, host='127.0.0.1', port=6688):
        self.host = host
        self.port = port
        self.results = {}
    
    def run_test(self, test_name, test_func):
        print(f"\n🔍 Running {test_name}...")
        try:
            result = test_func()
            self.results[test_name] = "✅ PASS" if result else "❌ FAIL"
            print(f"{self.results[test_name]} {test_name}")
        except Exception as e:
            self.results[test_name] = f"❌ ERROR: {e}"
            print(f"{self.results[test_name]}")
    
    def run_all_tests(self):
        print("🚀 Starting MCP Service Test Suite")
        
        # Add all test methods here
        tests = [
            ("Basic Connection", self.test_basic_connection),
            ("Message Processing", self.test_message_processing),
            ("Code Execution", self.test_code_execution),
            ("Blender API", self.test_blender_api),
            ("Error Handling", self.test_error_handling),
            ("Multiple Connections", self.test_multiple_connections),
        ]
        
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
        
        self.print_summary()
    
    def print_summary(self):
        print("\n📊 Test Summary:")
        print("=" * 50)
        for test_name, result in self.results.items():
            print(f"{result} {test_name}")
        
        passed = sum(1 for r in self.results.values() if r == "✅ PASS")
        total = len(self.results)
        print(f"\n{passed}/{total} tests passed")

# Usage
if __name__ == "__main__":
    tester = MCPTester()
    tester.run_all_tests()
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check if Blender is running: `ps aux | grep blender`
   - Check if port is listening: `netstat -tlnp | grep 6688`
   - Restart Blender with environment variables set

2. **Service Not Starting**
   - Check Blender console for error messages
   - Verify plugin is installed correctly
   - Try manual service start: `import bld_remote; bld_remote.start_mcp_service()`

3. **Code Execution Errors**
   - Verify Blender API access in console
   - Check for Python syntax errors
   - Ensure proper Blender context

4. **Port Conflicts**
   - Use different port: `export BLD_REMOTE_MCP_PORT=6689`
   - Check for other services using the port

### Manual Testing Commands

```bash
# Check service status
netstat -tlnp | grep 6688

# Test basic connection
echo '{"message": "test", "code": "print(\"hello\")"}' | nc 127.0.0.1 6688

# Kill Blender if needed
pkill -f blender

# Restart with fresh environment
export BLD_REMOTE_MCP_START_NOW=1
/apps/blender-4.4.3-linux-x64/blender &
```

## Test Environment Cleanup

After testing, clean up the environment:

```bash
# Kill Blender processes
pkill -f blender

# Clear any test objects (if needed, run in Blender console)
# bpy.ops.object.select_all(action='SELECT')
# bpy.ops.object.delete()
```

## Notes

- Tests should be run in a clean Blender environment
- Some tests modify the Blender scene - consider running cleanup between tests
- Service is designed to handle multiple concurrent connections
- Error responses should contain useful debugging information
- GUI mode is recommended for testing (background mode requires special handling)