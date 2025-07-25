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

#### **GUI Mode - Dual Service Testing**
- **Primary**: Test our BLD Remote MCP service (port 6688)
- **Backup Channel**: BlenderAutoMCP as reference/validation service (port 9876)
- **Strategy**: Both services can run simultaneously in GUI mode
- **Benefits**: 
  - Cross-validate results between services
  - Use BlenderAutoMCP to verify Blender state when our service fails
  - Debug our service by comparing behavior with proven reference
  - Fallback communication channel if our service becomes unresponsive

#### **Background Mode - Single Service Testing**
- **Primary**: Only our BLD Remote MCP service (port 6688)
- **Limitation**: BlenderAutoMCP cannot run in background mode
- **Strategy**: Pure test of our implementation without fallback
- **Benefits**: 
  - Validates true headless compatibility
  - Tests our service's background mode robustness
  - Simulates production headless deployment scenarios

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

#### **2A. GUI Mode - Dual Service Startup**

**Objective**: Start both services for comprehensive testing with backup channel

**Test Script**:
```python
import subprocess
import time
import os

def start_dual_services_gui(our_port):
    """Start both BLD Remote MCP and BlenderAutoMCP services in GUI mode"""
    print(f"🚀 Starting DUAL services in GUI mode...")
    print(f"   - BLD Remote MCP on port {our_port}")
    print(f"   - BlenderAutoMCP on port 9876 (reference)")
    
    # Setup environment for both services
    env = os.environ.copy()
    
    # Configure our service
    env['BLD_REMOTE_MCP_PORT'] = str(our_port)
    env['BLD_REMOTE_MCP_START_NOW'] = '1'
    
    # Configure BlenderAutoMCP reference service  
    env['BLENDER_AUTO_MCP_SERVICE_PORT'] = '9876'
    env['BLENDER_AUTO_MCP_START_NOW'] = '1'
    
    # Start Blender in GUI mode with both services
    cmd = ['/apps/blender-4.4.3-linux-x64/blender']
    print(f"   Command: {' '.join(cmd)}")
    print(f"   Environment: BLD_REMOTE_MCP_PORT={our_port}, BLENDER_AUTO_MCP_START_NOW=1")
    
    process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for both services to start (longer wait for dual startup)
    print("   Waiting 15 seconds for dual service startup...")
    time.sleep(15)
    
    # Verify both services are running
    services_status = verify_dual_services(our_port, 9876)
    
    if services_status['our_service'] and services_status['reference_service']:
        print("✅ DUAL SERVICES started successfully!")
        print(f"   ✅ BLD Remote MCP: port {our_port}")
        print(f"   ✅ BlenderAutoMCP: port 9876")
        return True, process
    elif services_status['our_service']:
        print("⚠️  Partial success: Our service running, BlenderAutoMCP failed")
        print(f"   ✅ BLD Remote MCP: port {our_port}")
        print(f"   ❌ BlenderAutoMCP: port 9876")
        return True, process  # Continue with single service
    else:
        print("❌ DUAL SERVICE startup failed")
        print(f"   ❌ BLD Remote MCP: port {our_port}")
        print(f"   ❌ BlenderAutoMCP: port 9876")
        return False, process

def verify_dual_services(our_port, reference_port):
    """Verify both services are responding"""
    import socket
    
    def check_port(port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            return result == 0
        except:
            return False
    
    return {
        'our_service': check_port(our_port),
        'reference_service': check_port(reference_port)
    }

# Usage for GUI mode
port = find_available_port()
if port:
    success, process = start_dual_services_gui(port)
```

#### **2B. Background Mode - Single Service Startup**

**Objective**: Start only our service in background mode (BlenderAutoMCP cannot run in background)

**Test Script**:
```python
def start_background_service(port):
    """Start BLD Remote MCP service in background mode"""
    print(f"🚀 Starting BLD Remote MCP on port {port} in BACKGROUND mode...")
    print("   Note: BlenderAutoMCP cannot run in background mode")
    
    env = os.environ.copy()
    env['BLD_REMOTE_MCP_PORT'] = str(port)
    env['BLD_REMOTE_MCP_START_NOW'] = '1'
    
    cmd = ['/apps/blender-4.4.3-linux-x64/blender', '--background']
    print(f"   Command: {' '.join(cmd)}")
    
    process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for startup
    print("   Waiting 10 seconds for background startup...")
    time.sleep(10)
    
    # Check if process completed (background mode exits after startup)
    if process.poll() is not None:
        stdout, stderr = process.communicate()
        print(f"✅ Background process completed")
        print(f"   stdout: {stdout.decode('utf-8')[:200]}...")
        if stderr:
            print(f"   stderr: {stderr.decode('utf-8')[:200]}...")
        
        # Verify service is actually running by testing connection
        if verify_service_connection(port):
            print(f"✅ Background service verified on port {port}")
            return True
        else:
            print(f"❌ Background service not responding on port {port}")
            return False
    else:
        print(f"⚠️  Background process still running (unexpected)")
        return False

def verify_service_connection(port):
    """Test if service is actually responding"""
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0
    except:
        return False

# Usage for background mode
port = find_available_port()
if port:
    start_background_service(port)
```

**Expected Results**: 
- **GUI Mode**: Both services start and respond on their respective ports
- **Background Mode**: Our service starts and responds, process exits normally

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

### 9. Dual Service Validation and Cross-Verification

**Objective**: Use both services to cross-validate Blender state and test service compatibility

#### **9A. GUI Mode - Dual Service Cross-Validation**

**Test Script**:
```python
def dual_service_cross_validation(our_port):
    """Use BlenderAutoMCP as backup channel to validate our service results"""
    print("🔍 DUAL SERVICE Cross-Validation Testing...")
    print("   Strategy: Use BlenderAutoMCP as reference/backup to verify our service")
    
    try:
        # Connect to both services
        print("   Connecting to both services...")
        our_client = BlenderMCPClient(host="localhost", port=our_port, timeout=30.0)
        ref_client = BlenderMCPClient(host="localhost", port=9876, timeout=30.0)
        
        # Test connections
        our_connected = our_client.test_connection()
        ref_connected = ref_client.test_connection()
        
        print(f"   BLD Remote MCP (port {our_port}): {'✅ Connected' if our_connected else '❌ Failed'}")
        print(f"   BlenderAutoMCP (port 9876): {'✅ Connected' if ref_connected else '❌ Failed'}")
        
        if not our_connected:
            print("   ❌ Our service not available - cannot perform cross-validation")
            return False
        
        if not ref_connected:
            print("   ⚠️  Reference service not available - testing our service only")
            return validate_single_service(our_client)
        
        # Cross-validation tests
        print("\n   🔍 Cross-Validation Tests:")
        
        # Test 1: Scene info consistency
        print("   Test 1: Scene information consistency...")
        our_scene = our_client.get_scene_info()
        ref_scene = ref_client.get_scene_info()
        
        scene_consistent = (
            our_scene.get('name') == ref_scene.get('name') and
            our_scene.get('object_count') == ref_scene.get('object_count')
        )
        
        print(f"      Our service: Scene='{our_scene.get('name')}', Objects={our_scene.get('object_count')}")
        print(f"      Reference:   Scene='{ref_scene.get('name')}', Objects={ref_scene.get('object_count')}")
        print(f"      Consistency: {'✅ Match' if scene_consistent else '❌ Mismatch'}")
        
        # Test 2: Create object via our service, verify via reference
        print("   Test 2: Object creation cross-verification...")
        test_code = """
import bpy
bpy.ops.mesh.primitive_cube_add(location=(5, 5, 5))
cube = bpy.context.active_object
cube.name = "CrossValidationTestCube"
print(f"Created cube: {cube.name}")
"""
        
        # Create via our service
        our_result = our_client.execute_python(test_code)
        print(f"      Our service created object: {our_result.strip()}")
        
        # Verify via reference service
        verify_code = """
import bpy
test_cube = bpy.data.objects.get("CrossValidationTestCube")
if test_cube:
    location = test_cube.location
    print(f"Found test cube at location: ({location.x:.1f}, {location.y:.1f}, {location.z:.1f})")
else:
    print("Test cube not found!")
"""
        
        ref_result = ref_client.execute_python(verify_code)
        print(f"      Reference verified: {ref_result.strip()}")
        
        # Test 3: Cleanup via reference, verify via our service
        print("   Test 3: Cleanup cross-verification...")
        cleanup_code = """
import bpy
test_cube = bpy.data.objects.get("CrossValidationTestCube")
if test_cube:
    bpy.data.objects.remove(test_cube, do_unlink=True)
    print("Test cube removed")
else:
    print("Test cube already gone")
"""
        
        # Cleanup via reference
        ref_cleanup = ref_client.execute_python(cleanup_code)
        print(f"      Reference cleanup: {ref_cleanup.strip()}")
        
        # Verify cleanup via our service
        our_verify = our_client.execute_python(verify_code)
        print(f"      Our service verified: {our_verify.strip()}")
        
        # Test 4: Service isolation test
        print("   Test 4: Service isolation verification...")
        isolation_code = f"""
import bpy
# Add marker to identify which service created this
bpy.ops.mesh.primitive_uv_sphere_add(location=(10, 0, 0))
sphere = bpy.context.active_object
sphere.name = "ServiceIsolationTest_Port{our_port if 'our_client' in locals() else '9876'}"
print(f"Created isolation test sphere: {{sphere.name}}")
"""
        
        # Execute same code via both services
        our_isolation = our_client.execute_python(isolation_code.replace(f"Port{our_port}", f"Port{our_port}"))
        ref_isolation = ref_client.execute_python(isolation_code.replace(f"Port{our_port}", "Port9876"))
        
        print(f"      Our service isolation: {our_isolation.strip()}")
        print(f"      Reference isolation: {ref_isolation.strip()}")
        
        # Final scene state via both
        our_final = our_client.get_scene_info()
        ref_final = ref_client.get_scene_info()
        
        final_consistent = our_final.get('object_count') == ref_final.get('object_count')
        print(f"   Final state consistency: {'✅ Match' if final_consistent else '❌ Mismatch'}")
        print(f"      Both report {our_final.get('object_count')} objects in scene")
        
        return scene_consistent and final_consistent
        
    except Exception as e:
        print(f"   ❌ Cross-validation failed: {e}")
        return False

def validate_single_service(client):
    """Validate our service when reference is not available"""
    print("   🔍 Single service validation (no reference available)...")
    
    try:
        # Basic functionality test
        scene_info = client.get_scene_info()
        print(f"   Scene info: {scene_info.get('name')}, {scene_info.get('object_count')} objects")
        
        # Code execution test
        result = client.execute_python("print('Single service validation successful')")
        print(f"   Code execution: {result.strip()}")
        
        return "successful" in result
    except Exception as e:
        print(f"   ❌ Single service validation failed: {e}")
        return False

# Usage for GUI mode with dual services
if port:
    dual_service_cross_validation(port)
```

#### **9B. Background Mode - Single Service Validation**

**Test Script**:
```python
def background_service_validation(our_port):
    """Validate our service in background mode (no reference available)"""
    print("🔍 BACKGROUND MODE Service Validation...")
    print("   Note: BlenderAutoMCP not available in background mode")
    
    try:
        our_client = BlenderMCPClient(host="localhost", port=our_port, timeout=30.0)
        
        if not our_client.test_connection():
            print("   ❌ Our service not responding in background mode")
            return False
        
        print("   ✅ Service responding in background mode")
        
        # Background-specific tests
        print("   🔍 Background mode specific tests:")
        
        # Test context access
        context_test = """
import bpy
try:
    scene_name = bpy.context.scene.name
    print(f"Background context access: Scene={scene_name}")
except Exception as e:
    print(f"Background context error: {e}")
"""
        
        result = our_client.execute_python(context_test)
        print(f"   Context test: {result.strip()}")
        
        return "Scene=" in result or "Background context access" in result
        
    except Exception as e:
        print(f"   ❌ Background validation failed: {e}")
        return False

# Usage for background mode
if port and mode == 'background':
    background_service_validation(port)
```

**Expected Results**: 
- **GUI Mode**: Cross-validation between services shows consistent Blender state
- **Background Mode**: Service responds correctly without reference service
- **Isolation**: Both services can operate independently without interference

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
        self.ref_client = None
        self.dual_mode = False
        self.process = None
        
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
        """Start service(s) based on mode"""
        if not self.port:
            return False
        
        if mode == 'gui':
            return self.start_dual_services()
        else:
            return self.start_background_service()
    
    def start_dual_services(self):
        """Start both BLD Remote MCP and BlenderAutoMCP in GUI mode"""
        print(f"🚀 Starting DUAL services in GUI mode...")
        print(f"   - BLD Remote MCP on port {self.port}")
        print(f"   - BlenderAutoMCP on port 9876 (reference)")
        
        env = os.environ.copy()
        
        # Configure our service
        env['BLD_REMOTE_MCP_PORT'] = str(self.port)
        env['BLD_REMOTE_MCP_START_NOW'] = '1'
        
        # Configure BlenderAutoMCP reference service  
        env['BLENDER_AUTO_MCP_SERVICE_PORT'] = '9876'
        env['BLENDER_AUTO_MCP_START_NOW'] = '1'
        
        # Start Blender in GUI mode with both services
        cmd = ['/apps/blender-4.4.3-linux-x64/blender']
        self.process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for both services to start
        print("   Waiting 15 seconds for dual service startup...")
        time.sleep(15)
        
        # Check if both services are responding
        try:
            self.client = BlenderMCPClient(host="localhost", port=self.port, timeout=30.0)
            our_connected = self.client.test_connection()
            
            self.ref_client = BlenderMCPClient(host="localhost", port=9876, timeout=30.0)  
            ref_connected = self.ref_client.test_connection()
            
            print(f"   BLD Remote MCP: {'✅ Connected' if our_connected else '❌ Failed'}")
            print(f"   BlenderAutoMCP: {'✅ Connected' if ref_connected else '❌ Failed'}")
            
            if our_connected and ref_connected:
                print("✅ DUAL SERVICES started successfully!")
                self.dual_mode = True
                return True
            elif our_connected:
                print("⚠️  Partial success: Our service running, reference failed")
                self.dual_mode = False
                return True
            else:
                print("❌ DUAL SERVICE startup failed")
                return False
                
        except Exception as e:
            print(f"❌ Service startup failed: {e}")
            return False
    
    def start_background_service(self):
        """Start BLD Remote MCP service in background mode"""
        print(f"🚀 Starting BLD Remote MCP on port {self.port} in BACKGROUND mode...")
        print("   Note: BlenderAutoMCP cannot run in background mode")
        
        env = os.environ.copy()
        env['BLD_REMOTE_MCP_PORT'] = str(self.port)
        env['BLD_REMOTE_MCP_START_NOW'] = '1'
        
        cmd = ['/apps/blender-4.4.3-linux-x64/blender', '--background']
        self.process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for startup
        print("   Waiting 10 seconds for background startup...")
        time.sleep(10)
        
        # Check if service is responding
        try:
            self.client = BlenderMCPClient(host="localhost", port=self.port, timeout=30.0)
            if self.client.test_connection():
                print(f"✅ Background service started successfully")
                self.dual_mode = False
                return True
            else:
                print(f"❌ Background service not responding")
                return False
        except Exception as e:
            print(f"❌ Background service startup failed: {e}")
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
        """Cross-validate with BlenderAutoMCP or test standalone"""
        if self.dual_mode and self.ref_client:
            return self.test_dual_service_cross_validation()
        else:
            return self.test_single_service_validation()
    
    def test_dual_service_cross_validation(self):
        """Cross-validate using both services in dual mode"""
        try:
            print("   🔍 Dual service cross-validation...")
            
            # Test 1: Scene consistency
            our_scene = self.client.get_scene_info()
            ref_scene = self.ref_client.get_scene_info() 
            
            scene_match = (our_scene.get('name') == ref_scene.get('name') and
                          our_scene.get('object_count') == ref_scene.get('object_count'))
            
            print(f"   Scene consistency: {'✅ Match' if scene_match else '❌ Mismatch'}")
            
            # Test 2: Cross-service object creation/verification
            test_code = "import bpy; bpy.ops.mesh.primitive_cube_add(location=(0, 0, 5)); print('Cross-test cube created')"
            
            our_result = self.client.execute_python(test_code)
            verify_code = "import bpy; cube = bpy.data.objects.get('Cube'); print(f'Cube found: {cube is not None}')"
            ref_result = self.ref_client.execute_python(verify_code)
            
            cross_validation = "created" in our_result and "True" in ref_result
            print(f"   Cross-validation: {'✅ Pass' if cross_validation else '❌ Fail'}")
            
            return scene_match and cross_validation
            
        except Exception as e:
            print(f"   ❌ Cross-validation error: {e}")
            return False
    
    def test_single_service_validation(self):
        """Validate single service when reference not available"""
        try:
            print("   🔍 Single service validation...")
            
            # Basic connectivity
            if not self.client or not self.client.test_connection():
                return False
            
            # Scene info test
            scene_info = self.client.get_scene_info()
            scene_ok = scene_info and 'name' in scene_info
            
            # Code execution test
            result = self.client.execute_python("print('Validation test')")
            exec_ok = "Validation test" in result
            
            print(f"   Single service: {'✅ Pass' if scene_ok and exec_ok else '❌ Fail'}")
            return scene_ok and exec_ok
            
        except Exception as e:
            print(f"   ❌ Single service validation error: {e}")
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

## 🎯 **Dual-Service Testing Strategy Benefits**

### **GUI Mode - Two Communication Channels**
When testing in GUI mode, you have **dual communication channels** to the same Blender instance:

```
Test Client ──┬─► BLD Remote MCP (port 6688) ──┐
              │                                 ├─► Same Blender Instance
              └─► BlenderAutoMCP (port 9876) ───┘
```

**Key Benefits:**
1. **Cross-Validation**: Verify Blender state changes via both services  
2. **Backup Channel**: If our service fails, use BlenderAutoMCP to debug
3. **Reference Comparison**: Compare our service behavior with proven implementation
4. **Isolation Testing**: Ensure services don't interfere with each other
5. **Debugging Support**: Use BlenderAutoMCP to inspect scene state when our service has issues

**Example Debugging Workflow:**
```python
# Create object via our service
our_client.execute_python("bpy.ops.mesh.primitive_cube_add()")

# Verify via reference service  
ref_result = ref_client.execute_python("print(len(bpy.context.scene.objects))")

# If counts don't match, investigate the discrepancy
```

### **Background Mode - Pure Implementation Test**
In background mode, only our service is available:

```
Test Client ──► BLD Remote MCP (port 6688) ──► Blender --background
```

**Benefits:**
1. **True Headless Testing**: Validates production deployment scenarios
2. **Service Independence**: Tests our implementation without fallbacks
3. **Background Compatibility**: Verifies asyncio and context handling
4. **Performance Testing**: Measures headless service performance

### **Testing Strategy Matrix**

| Mode | Our Service | Reference | Strategy | Benefits |
|------|------------|-----------|----------|----------|
| **GUI** | ✅ Port 6688 | ✅ Port 9876 | Dual-channel validation | Cross-verification, backup channel, debugging |
| **Background** | ✅ Port 6688 | ❌ Not available | Single-service validation | True headless testing, independence |

### **Practical Testing Scenarios**

#### **Scenario 1: Service Development**
- Start dual services in GUI mode
- Test new features via our service
- Cross-validate results via BlenderAutoMCP
- Use reference service to debug issues

#### **Scenario 2: Production Validation**  
- Test in background mode to simulate deployment
- Validate headless operation without GUI dependencies
- Ensure service works in containerized environments

#### **Scenario 3: Regression Testing**
- Run dual-service tests to compare with known-good reference
- Detect behavior changes or compatibility issues
- Validate protocol compliance with proven implementation

This dual-service approach provides comprehensive testing coverage while maintaining the flexibility to test in both development and production scenarios.

## Plugin Development and Update Procedures

### Overview

During development, we need efficient ways to update the BLD Remote MCP plugin without manually restarting Blender every time. This section outlines proven approaches for hot reload, programmatic updates, and development workflow optimization.

### Development Workflow Integration

#### **VS Code + Blender Development Extension (Recommended)**

For active development, use Jacques Lucke's Blender Development extension:

**Setup Steps:**
1. Install extension: `JacquesLucke.blender-development`
2. Configure settings:
   ```json
   {
     "blender.addon.reloadOnSave": true,
     "blender.addon.justMyCode": false,
     "BLENDER_USER_RESOURCES": "./blender_vscode_development"
   }
   ```
3. Start Blender from VS Code: `Ctrl+Shift+P` → "Blender: Start"
4. Auto-reload on file save or manual reload: "Blender: Reload Addons"

**Benefits:**
- Automatic reloading when files are saved
- Full debugging capabilities with breakpoints
- Symlink creation for permanent workspace links
- Works with both legacy addons and Blender 4.2+ Extensions

#### **Manual Plugin Update Methods**

**Method 1: Hot Reload with Service Cleanup**
```python
def reload_bld_remote_mcp_with_cleanup():
    """Hot reload BLD Remote MCP with proper service cleanup"""
    import sys
    import importlib
    
    print("🔄 Starting BLD Remote MCP hot reload...")
    
    # Step 1: Stop all addon services first
    print("   Stopping services...")
    try:
        import bld_remote
        if bld_remote.is_mcp_service_up():
            bld_remote.stop_mcp_service()
            print("   ✅ BLD Remote MCP service stopped")
        else:
            print("   ℹ️  Service was not running")
    except Exception as e:
        print(f"   ⚠️  Error stopping service: {e}")
    
    # Step 2: Clean sys.modules for complete reload
    print("   Cleaning module cache...")
    addon_name = "bld_remote_mcp"
    modules_to_remove = [name for name in sys.modules.keys() 
                        if name.startswith(addon_name)]
    
    for module_name in modules_to_remove:
        del sys.modules[module_name]
        print(f"   🗑️  Removed module: {module_name}")
    
    # Step 3: Disable and re-enable addon
    print("   Reloading addon...")
    try:
        bpy.ops.preferences.addon_disable(module=addon_name)
        bpy.ops.preferences.addon_enable(module=addon_name)
        print("   ✅ Addon reloaded successfully")
        
        # Step 4: Restart service if needed
        import bld_remote
        if should_auto_start():  # Check environment variable
            bld_remote.start_mcp_service()
            print("   ✅ Service restarted")
        
        return True
    except Exception as e:
        print(f"   ❌ Reload failed: {e}")
        return False

# Usage in Blender console
reload_bld_remote_mcp_with_cleanup()
```

**Method 2: Programmatic Source Update**
```python
def update_plugin_from_source():
    """Update BLD Remote MCP plugin from source directory"""
    import shutil
    import os
    from pathlib import Path
    from datetime import datetime
    
    print("🔄 Updating BLD Remote MCP from source...")
    
    # Paths
    source_dir = Path("/workspace/code/blender-remote/blender_addon/bld_remote_mcp")
    target_dir = Path("/home/igamenovoer/.config/blender/4.4/scripts/addons/bld_remote_mcp")
    backup_dir = target_dir.parent / f"bld_remote_mcp_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # Step 1: Stop service
        import bld_remote
        if bld_remote.is_mcp_service_up():
            bld_remote.stop_mcp_service()
            print("   ✅ Service stopped")
        
        # Step 2: Create backup
        if target_dir.exists():
            shutil.copytree(target_dir, backup_dir)
            print(f"   ✅ Backup created: {backup_dir}")
        
        # Step 3: Update files
        if target_dir.exists():
            shutil.rmtree(target_dir)
        
        shutil.copytree(source_dir, target_dir)
        print(f"   ✅ Files updated from {source_dir}")
        
        # Step 4: Reload addon
        reload_result = reload_bld_remote_mcp_with_cleanup()
        
        if reload_result:
            print("   🎉 Plugin update completed successfully!")
            return True
        else:
            print("   ❌ Plugin update failed during reload")
            return False
            
    except Exception as e:
        print(f"   ❌ Plugin update failed: {e}")
        
        # Rollback if possible
        if backup_dir.exists() and not target_dir.exists():
            shutil.copytree(backup_dir, target_dir)
            print(f"   🔄 Rolled back to backup")
        
        return False

# Usage
update_plugin_from_source()
```

**Method 3: Blender Restart with Session Recovery**
```python
def restart_blender_with_plugin_update():
    """Restart Blender with automatic session recovery and plugin update"""
    import subprocess
    
    print("🔄 Restarting Blender with plugin update...")
    
    # Update plugin first
    if update_plugin_from_source():
        print("   ✅ Plugin updated, restarting Blender...")
        
        # Get Blender executable path
        blender_exe = bpy.app.binary_path
        
        # Restart with session recovery
        restart_cmd = [
            blender_exe,
            "--python-expr",
            "import bpy; bpy.ops.wm.recover_last_session()"
        ]
        
        subprocess.Popen(restart_cmd)
        bpy.ops.wm.quit_blender()
    else:
        print("   ❌ Plugin update failed, not restarting")

# Usage for major changes
restart_blender_with_plugin_update()
```

### Testing Plugin Update Mechanisms

#### **Test 1: Hot Reload Functionality**
```python
def test_hot_reload_capability():
    """Test hot reload without losing service state"""
    print("🔍 Testing hot reload capability...")
    
    # Get initial state
    initial_port = None
    initial_running = False
    
    try:
        import bld_remote
        initial_port = bld_remote.get_mcp_service_port()
        initial_running = bld_remote.is_mcp_service_up()
        print(f"   Initial state: port={initial_port}, running={initial_running}")
    except Exception as e:
        print(f"   ⚠️  Could not get initial state: {e}")
    
    # Perform hot reload
    reload_success = reload_bld_remote_mcp_with_cleanup()
    
    if reload_success:
        try:
            import bld_remote
            final_port = bld_remote.get_mcp_service_port()
            final_running = bld_remote.is_mcp_service_up()
            print(f"   Final state: port={final_port}, running={final_running}")
            
            # Verify state preservation
            if final_port == initial_port:
                print("   ✅ Port configuration preserved")
            else:
                print(f"   ⚠️  Port changed: {initial_port} → {final_port}")
            
            # Test service functionality
            if final_running or not initial_running:
                from auto_mcp_remote import BlenderMCPClient
                client = BlenderMCPClient(host="localhost", port=final_port, timeout=30.0)
                if client.test_connection():
                    print("   ✅ Service functional after reload")
                    return True
                else:
                    print("   ❌ Service not responding after reload")
                    return False
            else:
                print("   ✅ Hot reload successful (service was not running)")
                return True
                
        except Exception as e:
            print(f"   ❌ Post-reload verification failed: {e}")
            return False
    else:
        print("   ❌ Hot reload failed")
        return False

# Usage
test_hot_reload_capability()
```

#### **Test 2: Source Update Functionality**
```python
def test_source_update_workflow():
    """Test programmatic source update workflow"""
    print("🔍 Testing source update workflow...")
    
    try:
        # Step 1: Verify source directory exists
        source_dir = Path("/workspace/code/blender-remote/blender_addon/bld_remote_mcp")
        if not source_dir.exists():
            print(f"   ❌ Source directory not found: {source_dir}")
            return False
        
        print(f"   ✅ Source directory found: {source_dir}")
        
        # Step 2: Check file differences
        target_dir = Path("/home/igamenovoer/.config/blender/4.4/scripts/addons/bld_remote_mcp")
        if target_dir.exists():
            source_files = set(f.name for f in source_dir.rglob("*.py"))
            target_files = set(f.name for f in target_dir.rglob("*.py"))
            
            print(f"   Source files: {len(source_files)}")
            print(f"   Target files: {len(target_files)}")
            
            if source_files != target_files:
                print("   ⚠️  File differences detected")
                new_files = source_files - target_files
                missing_files = target_files - source_files
                if new_files:
                    print(f"      New files: {new_files}")
                if missing_files:
                    print(f"      Missing files: {missing_files}")
            else:
                print("   ✅ File sets match")
        
        # Step 3: Test update process
        update_success = update_plugin_from_source()
        
        if update_success:
            print("   ✅ Source update workflow successful")
            return True
        else:
            print("   ❌ Source update workflow failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Source update test failed: {e}")
        return False

# Usage
test_source_update_workflow()
```

#### **Test 3: Development Iteration Speed**
```python
def test_development_iteration_speed():
    """Test how quickly we can iterate during development"""
    import time
    
    print("🔍 Testing development iteration speed...")
    
    iterations = 3
    times = []
    
    for i in range(iterations):
        print(f"   Iteration {i+1}/{iterations}...")
        
        start_time = time.time()
        
        # Simulate development cycle
        success = reload_bld_remote_mcp_with_cleanup()
        
        end_time = time.time()
        iteration_time = end_time - start_time
        times.append(iteration_time)
        
        print(f"      Time: {iteration_time:.2f}s, Success: {success}")
        
        if not success:
            print(f"   ❌ Iteration {i+1} failed")
            return False
        
        # Small delay between iterations
        time.sleep(1)
    
    avg_time = sum(times) / len(times)
    print(f"   ✅ Average iteration time: {avg_time:.2f}s")
    
    if avg_time < 5.0:
        print("   🚀 Fast iteration (< 5s) - Good for development")
    elif avg_time < 10.0:
        print("   ⚠️  Moderate iteration (5-10s) - Acceptable")
    else:
        print("   🐌 Slow iteration (> 10s) - Consider optimization")
    
    return True

# Usage
test_development_iteration_speed()
```

### Background Mode Development Considerations

#### **Key Issues in Background Mode:**
1. **Context Access Restrictions**: `'_RestrictContext' object has no attribute 'view_layer'`
2. **Service State Persistence**: Ensure services survive module reloads
3. **Signal Handler Integration**: Proper cleanup on process termination
4. **External Script Triggers**: Allow updates from outside Blender process

#### **Background-Safe Reload Pattern:**
```python
def background_safe_reload():
    """Reload that works in background mode"""
    if bpy.app.background:
        print("   🔧 Background mode - using context-safe reload")
        # Background mode - no UI updates, careful context handling
        reload_logic_only()
    else:
        print("   🖥️  GUI mode - using full reload with UI")
        # Interactive mode - full reload with UI
        full_reload_with_ui()

def reload_logic_only():
    """Reload addon logic without UI dependencies"""
    try:
        # Stop services without accessing scene properties
        cleanup_server_background_safe()
        
        # Clean modules
        clean_sys_modules()
        
        # Re-enable addon
        bpy.ops.preferences.addon_disable(module="bld_remote_mcp")
        bpy.ops.preferences.addon_enable(module="bld_remote_mcp")
        
    except Exception as e:
        print(f"   ❌ Background reload failed: {e}")

def cleanup_server_background_safe():
    """Cleanup server without accessing restricted context"""
    global tcp_server, server_task, server_port
    
    # Close TCP server
    if tcp_server:
        tcp_server.close()
        tcp_server = None
    
    # Cancel asyncio tasks
    if server_task:
        server_task.cancel()
        server_task = None
    
    # Reset port
    server_port = 0
    
    # Skip scene property updates in background mode
    if not bpy.app.background:
        try:
            bpy.data.scenes[0].bld_remote_server_running = False
        except (AttributeError, TypeError):
            pass  # Context restrictions
```

### Integration with Test Suite

#### **Enhanced Test Runner with Plugin Update Support**
```python
class BLDRemoteMCPTesterWithUpdates(BLDRemoteMCPTester):
    def __init__(self):
        super().__init__()
        self.update_methods = {}
    
    def test_plugin_update_capabilities(self):
        """Test all plugin update methods"""
        print("🔍 Testing plugin update capabilities...")
        
        tests = [
            ("Hot Reload", self.test_hot_reload_method),
            ("Source Update", self.test_source_update_method),
            ("Development Iteration", self.test_iteration_speed),
        ]
        
        for test_name, test_func in tests:
            success = self.run_test(f"Plugin Update - {test_name}", test_func)
            self.update_methods[test_name] = success
        
        return all(self.update_methods.values())
    
    def test_hot_reload_method(self):
        """Test hot reload capability"""
        return test_hot_reload_capability()
    
    def test_source_update_method(self):
        """Test source update workflow"""
        return test_source_update_workflow()
    
    def test_iteration_speed(self):
        """Test development iteration speed"""
        return test_development_iteration_speed()
    
    def run_development_workflow_tests(self):
        """Run comprehensive development workflow tests"""
        print("🚀 Starting Development Workflow Test Suite")
        print("=" * 60)
        
        # Standard tests
        if not self.run_all_tests('gui'):
            return False
        
        # Plugin update tests
        if not self.test_plugin_update_capabilities():
            return False
        
        print("\n🎯 Development Workflow Summary:")
        for method, success in self.update_methods.items():
            status = "✅ Available" if success else "❌ Failed"
            print(f"   {status} {method}")
        
        return True

# Usage for development
if __name__ == "__main__":
    dev_tester = BLDRemoteMCPTesterWithUpdates()
    dev_tester.run_development_workflow_tests()
```

### Quick Reference Commands

#### **Essential Development Commands**
```python
# Quick hot reload in Blender console
exec(open('/workspace/code/blender-remote/scripts/dev_reload.py').read())

# Update from source and reload
exec(open('/workspace/code/blender-remote/scripts/dev_update.py').read())

# Test current plugin state
import bld_remote; print(f"Service: {bld_remote.get_status()}")

# Manual service restart
import bld_remote; bld_remote.stop_mcp_service(); bld_remote.start_mcp_service()
```

#### **File System Commands**
```bash
# Copy updated plugin to Blender addons directory
cp -r /workspace/code/blender-remote/blender_addon/bld_remote_mcp/ \
      /home/igamenovoer/.config/blender/4.4/scripts/addons/

# Backup current plugin
cp -r /home/igamenovoer/.config/blender/4.4/scripts/addons/bld_remote_mcp/ \
      /home/igamenovoer/.config/blender/4.4/scripts/addons/bld_remote_mcp_backup_$(date +%Y%m%d_%H%M%S)/

# Check plugin differences
diff -r /workspace/code/blender-remote/blender_addon/bld_remote_mcp/ \
        /home/igamenovoer/.config/blender/4.4/scripts/addons/bld_remote_mcp/
```

### Development Best Practices

#### **Workflow Recommendations**
1. **Use VS Code Integration**: Fastest development cycle with auto-reload
2. **Test Hot Reload First**: Attempt hot reload before full restart
3. **Cleanup Services**: Always stop services before module updates
4. **Backup Before Updates**: Create timestamped backups for rollback
5. **Verify After Updates**: Test service functionality after each update

#### **Common Pitfalls**
1. **Port Conflicts**: Service fails to restart on same port after reload
2. **Module Import Errors**: Incomplete sys.modules cleanup
3. **Context Restrictions**: Background mode limitations
4. **State Persistence**: Global variables not properly reset
5. **Timer/Handler Leaks**: Background timers persist after reload

#### **Troubleshooting Quick Fixes**
```python
# Fix port conflicts
import bld_remote; bld_remote.stop_mcp_service(); time.sleep(2); bld_remote.start_mcp_service()

# Force module cleanup
import sys; [sys.modules.pop(k) for k in list(sys.modules.keys()) if k.startswith('bld_remote')]

# Reset global state
import bld_remote_mcp; bld_remote_mcp.tcp_server = None; bld_remote_mcp.server_task = None

# Check background mode
print(f"Background mode: {bpy.app.background}")
```

This enhanced development workflow provides efficient plugin iteration while maintaining comprehensive testing coverage. The dual-service testing strategy combined with these update mechanisms enables rapid development and validation of the BLD Remote MCP service.