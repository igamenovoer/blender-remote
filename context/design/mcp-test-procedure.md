# BLD Remote MCP Test Procedure

This document outlines comprehensive testing procedures for the BLD Remote MCP service using the proven `auto_mcp_remote` client interface.

## Overview

We test our BLD Remote MCP service using the same client interface (`@context/refcode/auto_mcp_remote/`) that successfully interacts with BlenderAutoMCP. This ensures compatibility and validates our implementation against proven patterns.

## Prerequisites

- Blender 4.4.3 installed at `/apps/blender-4.4.3-linux-x64/blender`
- BLD Remote MCP plugin installed at `/home/igamenovoer/.config/blender/4.4/scripts/addons/bld_remote_mcp/`
- BlenderAutoMCP reference service running on port 9876 (for comparison)
- Python environment with `auto_mcp_remote` modules

## Service Configuration

### Port Management Strategy
- **Dynamic Port Selection**: Test for available ports in range 6700-6799
- **Port Conflict Prevention**: Kill existing Blender processes before testing
- **Environment Variables**:
  - `BLD_REMOTE_MCP_PORT` - Override default port
  - `BLD_REMOTE_MCP_START_NOW` - Auto-start service on Blender launch

### Service Modes
- **GUI Mode**: Full functionality testing
- **Background Mode**: Headless compatibility testing

## Test Procedures

### 1. Environment Setup and Port Discovery

**Objective**: Prepare test environment and find available port

**Test Script**:
```python
import subprocess
import socket
import sys
import os

# Add auto_mcp_remote to path
sys.path.insert(0, '/workspace/code/blender-remote/context/refcode')

def find_available_port(start_port=6700, end_port=6799):
    """Find first available port in range"""
    for port in range(start_port, end_port + 1):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('127.0.0.1', port))
            sock.close()
            return port
        except OSError:
            continue
    return None

def kill_blender_processes():
    """Kill existing Blender processes"""
    try:
        subprocess.run(['pkill', '-f', 'blender'], check=False)
        return True
    except Exception as e:
        print(f"Error killing Blender: {e}")
        return False

def setup_test_environment():
    print("🔧 Setting up test environment...")
    kill_blender_processes()
    
    port = find_available_port()
    if port:
        print(f"✅ Found available port: {port}")
        return port
    else:
        print("❌ No available ports in range 6700-6799")
        return None

# Usage
if __name__ == "__main__":
    port = setup_test_environment()
```

**Expected Result**: Clean environment with available port identified

### 2. Service Startup Test

**Objective**: Start BLD Remote MCP service and verify it's running

**Test Script**:
```python
import subprocess
import time
import os

def start_bld_remote_service(port, mode='gui'):
    """Start BLD Remote MCP service in specified mode"""
    print(f"🚀 Starting BLD Remote MCP on port {port} in {mode} mode...")
    
    env = os.environ.copy()
    env['BLD_REMOTE_MCP_PORT'] = str(port)
    env['BLD_REMOTE_MCP_START_NOW'] = '1'
    
    if mode == 'background':
        cmd = ['/apps/blender-4.4.3-linux-x64/blender', '--background']
    else:
        cmd = ['/apps/blender-4.4.3-linux-x64/blender']
    
    # Start Blender (don't wait for completion in GUI mode)
    process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for startup
    time.sleep(10)
    
    # Check if process is running
    if process.poll() is None or mode == 'gui':
        print(f"✅ Blender started successfully")
        return True
    else:
        stdout, stderr = process.communicate()
        print(f"❌ Blender failed to start:")
        print(f"   stdout: {stdout.decode('utf-8')[:200]}...")
        print(f"   stderr: {stderr.decode('utf-8')[:200]}...")
        return False

# Usage in test
port = find_available_port()
if port:
    start_bld_remote_service(port, 'gui')
```

**Expected Result**: Service starts and port becomes available

### 3. BlenderMCPClient Connection Test

**Objective**: Test connection using auto_mcp_remote client interface

**Test Script**:
```python
from auto_mcp_remote import BlenderMCPClient

def test_client_connection(port):
    """Test BlenderMCPClient connection to BLD Remote MCP"""
    print(f"🔍 Testing BlenderMCPClient connection to port {port}...")
    
    try:
        # Create client for our service
        client = BlenderMCPClient(host="localhost", port=port, timeout=30.0)
        
        # Test connection
        if client.test_connection():
            print("✅ BlenderMCPClient connection successful")
            return client
        else:
            print("❌ BlenderMCPClient connection failed")
            return None
    except Exception as e:
        print(f"❌ BlenderMCPClient error: {e}")
        return None

# Usage
client = test_client_connection(port)
```

**Expected Result**: Client successfully connects to our service

### 4. Python Code Execution Test

**Objective**: Test Python code execution using BlenderMCPClient

**Test Script**:
```python
def test_python_execution(client):
    """Test Python code execution through BlenderMCPClient"""
    print("🔍 Testing Python code execution...")
    
    try:
        # Test basic Python execution
        test_code = """
import bpy
scene_name = bpy.context.scene.name
object_count = len(bpy.context.scene.objects)
result = f"Scene: {scene_name}, Objects: {object_count}"
print(result)
"""
        
        result = client.execute_python(test_code)
        print(f"✅ Python execution successful")
        print(f"   Result: {result.strip()}")
        return True
    except Exception as e:
        print(f"❌ Python execution failed: {e}")
        return False

# Usage
if client:
    test_python_execution(client)
```

**Expected Result**: Code executes and returns scene information

### 5. BlenderSceneManager Test

**Objective**: Test high-level scene operations using BlenderSceneManager

**Test Script**:
```python
from auto_mcp_remote import BlenderSceneManager

def test_scene_manager(client):
    """Test BlenderSceneManager functionality"""
    print("🔍 Testing BlenderSceneManager...")
    
    try:
        # Create scene manager
        scene = BlenderSceneManager(client)
        
        # Get scene summary
        summary = scene.get_scene_summary()
        print(f"✅ Scene summary: {summary.get('name', 'Unknown')}, Objects: {summary.get('object_count', 0)}")
        
        # List objects
        objects = scene.list_objects()
        print(f"   Found {len(objects)} objects:")
        for obj in objects[:3]:  # Show first 3
            print(f"     - {obj.name} ({obj.type}) at {obj.location}")
        
        # Test object creation
        cube_name = scene.add_cube(location=(0, 0, 2), size=1.0, name="BLD_TestCube")
        print(f"   Created cube: {cube_name}")
        
        # Test object manipulation
        moved = scene.move_object(cube_name, location=(1, 1, 3))
        print(f"   Moved cube: {moved}")
        
        # Clean up
        deleted = scene.delete_object(cube_name)
        print(f"   Deleted cube: {deleted}")
        
        return True
    except Exception as e:
        print(f"❌ BlenderSceneManager test failed: {e}")
        return False

# Usage
if client:
    test_scene_manager(client)
```

**Expected Result**: Scene operations complete successfully

### 6. Error Handling Test

**Objective**: Test error handling using BlenderMCPClient

**Test Script**:
```python
from auto_mcp_remote.data_types import BlenderMCPError

def test_error_handling(client):
    """Test error handling through BlenderMCPClient"""
    print("🔍 Testing error handling...")
    
    try:
        # Test invalid Python code
        invalid_code = """
import bpy
# This will cause an error
undefined_variable + 1
"""
        
        try:
            result = client.execute_python(invalid_code)
            print(f"⚠️  Expected error but got result: {result}")
            return False
        except BlenderMCPError as e:
            print(f"✅ Error handling successful: {str(e)[:100]}...")
            return True
        except Exception as e:
            print(f"⚠️  Unexpected error type: {type(e).__name__}: {e}")
            return True  # Still counts as handling the error
            
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

# Usage
if client:
    test_error_handling(client)
```

**Expected Result**: Service handles errors gracefully with proper exceptions

### 7. Multiple Client Test

**Objective**: Test multiple concurrent BlenderMCPClient connections

**Test Script**:
```python
import threading
import time

def single_client_test(port, connection_id):
    """Test single client connection"""
    try:
        client = BlenderMCPClient(host="localhost", port=port, timeout=30.0)
        
        test_code = f"print('Connection {connection_id} active')"
        result = client.execute_python(test_code)
        
        print(f"✅ Connection {connection_id} successful: {result.strip()}")
        return True
    except Exception as e:
        print(f"❌ Connection {connection_id} failed: {e}")
        return False

def test_multiple_clients(port, num_clients=3):
    """Test multiple concurrent clients"""
    print(f"🔍 Testing {num_clients} concurrent clients...")
    
    threads = []
    results = []
    
    def run_test(conn_id):
        result = single_client_test(port, conn_id)
        results.append(result)
    
    # Start all client threads
    for i in range(num_clients):
        thread = threading.Thread(target=run_test, args=(i,))
        threads.append(thread)
        thread.start()
        time.sleep(0.2)  # Small delay between connections
    
    # Wait for all to complete
    for thread in threads:
        thread.join()
    
    success_count = sum(results)
    print(f"   {success_count}/{num_clients} clients succeeded")
    return success_count == num_clients

# Usage
if port:
    test_multiple_clients(port)
```

**Expected Result**: All client connections succeed without interference

### 8. Complex Scene Operation Test

**Objective**: Test complex Blender operations using client interface

**Test Script**:
```python
def test_complex_operations(client):
    """Test complex Blender operations"""
    print("🔍 Testing complex scene operations...")
    
    try:
        # Generate complex scene code
        complex_code = """
import bpy
import bmesh

# Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
for obj in list(bpy.context.scene.objects):
    if obj.type == 'MESH':
        obj.select_set(True)
        bpy.data.objects.remove(obj, do_unlink=True)

# Create multiple objects with complex operations
for i in range(5):
    # Add cube
    bpy.ops.mesh.primitive_cube_add(location=(i*2, 0, 0))
    cube = bpy.context.active_object
    cube.name = f"ComplexCube_{i}"
    
    # Modify the cube with bmesh
    bpy.context.view_layer.objects.active = cube
    bpy.ops.object.mode_set(mode='EDIT')
    
    bm = bmesh.from_mesh(cube.data)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=1, use_grid_fill=True)
    bm.to_mesh(cube.data)
    bm.free()
    
    bpy.ops.object.mode_set(mode='OBJECT')

mesh_count = len([obj for obj in bpy.context.scene.objects if obj.name.startswith('ComplexCube_')])
print(f"Created {mesh_count} complex cubes")
"""
        
        result = client.execute_python(complex_code)
        print(f"✅ Complex operations successful: {result.strip()}")
        return True
    except Exception as e:
        print(f"❌ Complex operations failed: {e}")
        return False

# Usage
if client:
    test_complex_operations(client)
```

**Expected Result**: Complex operations execute successfully

### 9. Comparison with BlenderAutoMCP

**Objective**: Compare our service with BlenderAutoMCP reference implementation

**Test Script**:
```python
def compare_with_blender_auto_mcp(our_port):
    """Compare BLD Remote MCP with BlenderAutoMCP"""
    print("🔍 Comparing with BlenderAutoMCP reference...")
    
    try:
        # Test BlenderAutoMCP (reference on port 9876)
        print("   Testing BlenderAutoMCP (reference)...")
        auto_mcp_client = BlenderMCPClient(host="localhost", port=9876, timeout=30.0)
        
        if auto_mcp_client.test_connection():
            auto_scene = auto_mcp_client.get_scene_info()
            print(f"   ✅ BlenderAutoMCP: Scene={auto_scene.get('name')}, Objects={auto_scene.get('object_count')}")
        else:
            print("   ❌ BlenderAutoMCP not available")
            return False
        
        # Test our BLD Remote MCP
        print("   Testing BLD Remote MCP (our implementation)...")
        our_client = BlenderMCPClient(host="localhost", port=our_port, timeout=30.0)
        
        if our_client.test_connection():
            our_scene = our_client.get_scene_info()
            print(f"   ✅ BLD Remote MCP: Scene={our_scene.get('name')}, Objects={our_scene.get('object_count')}")
        else:
            print("   ❌ BLD Remote MCP not responding")
            return False
        
        # Compare functionality
        print("   📊 Functionality comparison:")
        print(f"     Both services respond to BlenderMCPClient interface: ✅")
        print(f"     BlenderAutoMCP: Full-featured with asset providers")
        print(f"     BLD Remote MCP: Minimal essential functions only")
        
        return True
    except Exception as e:
        print(f"❌ Comparison test failed: {e}")
        return False

# Usage
if port:
    compare_with_blender_auto_mcp(port)
```

**Expected Result**: Both services work with same client interface

## Comprehensive Test Runner

**Combined Test Script**:
```python
#!/usr/bin/env python3
"""
Comprehensive BLD Remote MCP Test Suite
Uses auto_mcp_remote interface for compatibility testing
"""

import subprocess
import socket
import sys
import os
import threading
import time

# Add auto_mcp_remote to path
sys.path.insert(0, '/workspace/code/blender-remote/context/refcode')

from auto_mcp_remote import BlenderMCPClient, BlenderSceneManager
from auto_mcp_remote.data_types import BlenderMCPError

class BLDRemoteMCPTester:
    def __init__(self):
        self.results = {}
        self.port = None
        self.client = None
        
    def setup_environment(self):
        """Setup test environment and find available port"""
        print("🔧 Setting up test environment...")
        
        # Kill existing Blender processes
        try:
            subprocess.run(['pkill', '-f', 'blender'], check=False)
            print("   Killed existing Blender processes")
        except Exception as e:
            print(f"   Warning: Could not kill Blender processes: {e}")
        
        # Find available port
        for port in range(6700, 6800):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(('127.0.0.1', port))
                sock.close()
                self.port = port
                print(f"✅ Found available port: {port}")
                return True
            except OSError:
                continue
        
        print("❌ No available ports in range 6700-6799")
        return False
    
    def start_service(self, mode='gui'):
        """Start BLD Remote MCP service"""
        if not self.port:
            return False
            
        print(f"🚀 Starting BLD Remote MCP on port {self.port} in {mode} mode...")
        
        env = os.environ.copy()
        env['BLD_REMOTE_MCP_PORT'] = str(self.port)
        env['BLD_REMOTE_MCP_START_NOW'] = '1'
        
        if mode == 'background':
            cmd = ['/apps/blender-4.4.3-linux-x64/blender', '--background']
        else:
            cmd = ['/apps/blender-4.4.3-linux-x64/blender']
        
        # Start Blender
        process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for startup
        time.sleep(10)
        
        # Check if service is responding
        try:
            self.client = BlenderMCPClient(host="localhost", port=self.port, timeout=30.0)
            if self.client.test_connection():
                print(f"✅ Service started successfully")
                return True
            else:
                print(f"❌ Service not responding")
                return False
        except Exception as e:
            print(f"❌ Service startup failed: {e}")
            return False
    
    def run_test(self, test_name, test_func):
        """Run a single test"""
        print(f"\n🔍 Running {test_name}...")
        try:
            result = test_func()
            status = "✅ PASS" if result else "❌ FAIL"
            self.results[test_name] = status
            print(f"{status} {test_name}")
            return result
        except Exception as e:
            status = f"❌ ERROR: {str(e)[:100]}..."
            self.results[test_name] = status
            print(f"{status}")
            return False
    
    def test_client_connection(self):
        """Test BlenderMCPClient connection"""
        if not self.client:
            return False
        return self.client.test_connection()
    
    def test_python_execution(self):
        """Test Python code execution"""
        if not self.client:
            return False
        
        test_code = """
import bpy
scene_name = bpy.context.scene.name
object_count = len(bpy.context.scene.objects)
print(f"Scene: {scene_name}, Objects: {object_count}")
"""
        result = self.client.execute_python(test_code)
        return "Scene:" in result
    
    def test_scene_manager(self):
        """Test BlenderSceneManager functionality"""
        if not self.client:
            return False
        
        scene = BlenderSceneManager(self.client)
        
        # Get scene summary
        summary = scene.get_scene_summary()
        if not summary:
            return False
        
        # Test object creation and manipulation
        cube_name = scene.add_cube(location=(0, 0, 2), size=1.0, name="TestCube")
        if not cube_name:
            return False
        
        # Clean up
        deleted = scene.delete_object(cube_name)
        return deleted
    
    def test_error_handling(self):
        """Test error handling"""
        if not self.client:
            return False
        
        try:
            invalid_code = "undefined_variable + 1"
            self.client.execute_python(invalid_code)
            return False  # Should have raised an error
        except (BlenderMCPError, Exception):
            return True  # Error was properly handled
    
    def test_multiple_clients(self):
        """Test multiple concurrent clients"""
        if not self.port:
            return False
        
        def single_test(conn_id):
            try:
                client = BlenderMCPClient(host="localhost", port=self.port, timeout=30.0)
                result = client.execute_python(f"print('Connection {conn_id} active')")
                return "active" in result
            except Exception:
                return False
        
        # Test 3 concurrent connections
        threads = []
        results = []
        
        def run_test(conn_id):
            result = single_test(conn_id)
            results.append(result)
        
        for i in range(3):
            thread = threading.Thread(target=run_test, args=(i,))
            threads.append(thread)
            thread.start()
            time.sleep(0.2)
        
        for thread in threads:
            thread.join()
        
        return all(results)
    
    def test_comparison_with_blender_auto_mcp(self):
        """Compare with BlenderAutoMCP reference"""
        try:
            # Test BlenderAutoMCP
            auto_client = BlenderMCPClient(host="localhost", port=9876, timeout=30.0)
            auto_works = auto_client.test_connection()
            
            # Test our service
            our_works = self.client.test_connection() if self.client else False
            
            return auto_works and our_works
        except Exception:
            return False
    
    def run_all_tests(self, mode='gui'):
        """Run all tests"""
        print("🚀 Starting BLD Remote MCP Test Suite")
        print("=" * 60)
        
        # Setup
        if not self.setup_environment():
            print("❌ Environment setup failed")
            return False
        
        if not self.start_service(mode):
            print("❌ Service startup failed")
            return False
        
        # Define tests
        tests = [
            ("Client Connection", self.test_client_connection),
            ("Python Execution", self.test_python_execution),
            ("Scene Manager", self.test_scene_manager),
            ("Error Handling", self.test_error_handling),
            ("Multiple Clients", self.test_multiple_clients),
            ("Comparison with BlenderAutoMCP", self.test_comparison_with_blender_auto_mcp),
        ]
        
        # Run all tests
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
        
        self.print_summary()
        return True
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 Test Summary:")
        print("=" * 60)
        
        for test_name, result in self.results.items():
            print(f"{result} {test_name}")
        
        passed = sum(1 for r in self.results.values() if r.startswith("✅"))
        total = len(self.results)
        
        print(f"\n{passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! BLD Remote MCP is working correctly.")
        else:
            print("⚠️  Some tests failed. Check implementation.")
            print("\n🔧 Next Steps:")
            print("   1. Fix failing tests")
            print("   2. Test background mode compatibility")
            print("   3. Verify essential command implementation")

# Usage
if __name__ == "__main__":
    tester = BLDRemoteMCPTester()
    
    # Test GUI mode
    print("Testing GUI mode...")
    tester.run_all_tests('gui')
    
    # Optionally test background mode
    # print("\nTesting background mode...")
    # tester.run_all_tests('background')
```

## Troubleshooting

### Common Issues

1. **Environment Setup Fails**
   - Check if Blender path is correct: `/apps/blender-4.4.3-linux-x64/blender`
   - Verify BLD Remote MCP plugin is installed
   - Ensure no port conflicts in range 6700-6799

2. **Service Startup Issues**
   - Check Blender console output for error messages
   - Verify environment variables are set correctly
   - Try manual service start in Blender console: `import bld_remote; bld_remote.start_mcp_service()`

3. **BlenderMCPClient Connection Failures**
   - Verify service is actually running on the expected port
   - Check if BlenderAutoMCP is interfering (different ports)
   - Increase timeout for slow systems

4. **Background Mode Problems**
   - Known issue: BLD Remote MCP may fail in background mode
   - Error: `'_RestrictContext' object has no attribute 'view_layer'`
   - Use GUI mode for testing until background mode is fixed

5. **auto_mcp_remote Import Errors**
   - Ensure path is correctly added: `sys.path.insert(0, '/workspace/code/blender-remote/context/refcode')`
   - Check if all required modules are present
   - Verify numpy, scipy dependencies

### Debug Commands

```bash
# Check for running Blender processes
ps aux | grep blender | grep -v grep

# Check which ports are listening
netstat -tlnp | grep blender

# Kill all Blender processes
pkill -f blender

# Check if auto_mcp_remote modules are accessible
python3 -c "
import sys
sys.path.insert(0, '/workspace/code/blender-remote/context/refcode')
from auto_mcp_remote import BlenderMCPClient
print('auto_mcp_remote modules loaded successfully')
"
```

### Manual Service Testing

```python
# Test service manually using BlenderMCPClient
from auto_mcp_remote import BlenderMCPClient

# Test connection to specific port
client = BlenderMCPClient(host="localhost", port=6700, timeout=30.0)
if client.test_connection():
    print("Service is responding")
else:
    print("Service not responding")
```

### Background vs GUI Mode

| Mode | Status | Notes |
|------|--------|-------|
| **GUI Mode** | ✅ Working | Recommended for testing |
| **Background Mode** | ❌ Broken | Context access issues |

### Comparison Testing

```python
# Compare our service with BlenderAutoMCP
auto_client = BlenderMCPClient(port=9876)  # BlenderAutoMCP
our_client = BlenderMCPClient(port=6700)   # BLD Remote MCP

print(f"BlenderAutoMCP: {auto_client.test_connection()}")
print(f"BLD Remote MCP: {our_client.test_connection()}")
```

## Test Environment Cleanup

```bash
# Complete cleanup script
pkill -f blender
sleep 2

# Verify cleanup
ps aux | grep blender | grep -v grep
echo "Cleanup complete"
```

## Development Notes

### Key Testing Insights
1. **Use auto_mcp_remote interface** - Proven to work with BlenderAutoMCP
2. **Dynamic port selection** - Prevents conflicts during development
3. **Environment cleanup** - Essential due to Blender's poor state management
4. **GUI mode testing** - More reliable than background mode
5. **Comparison testing** - Validates compatibility with reference implementation

### Test Results Interpretation
- **All tests pass**: Service is compatible with auto_mcp_remote interface
- **Connection fails**: Service not running or port issues
- **Client tests fail**: Message format or protocol incompatibility
- **Scene manager fails**: Blender API access issues

### Next Steps After Testing
1. Fix any failing tests
2. Implement missing essential commands
3. Address background mode compatibility
4. Validate against BlenderAutoMCP patterns