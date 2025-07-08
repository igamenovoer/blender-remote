"""
PyTest configuration and shared fixtures for blender-remote tests.

This module provides common test fixtures, utilities, and configuration
for testing the blender-remote project, including MCP service testing.
"""

import pytest
import sys
import os
import subprocess
import time
import socket
from pathlib import Path

# Add project paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "context" / "refcode"))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Test configuration
BLENDER_PATH = "/apps/blender-4.4.3-linux-x64/blender"
BLD_REMOTE_PORT = 6688
BLENDER_AUTO_PORT = 9876
SERVICE_STARTUP_TIMEOUT = 20  # seconds


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "blender_required: marks tests that require Blender to be running"
    )
    config.addinivalue_line(
        "markers", "dual_service: marks tests that require both MCP services"
    )


def is_port_available(port):
    """Check if a port is available for binding."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', port))
        sock.close()
        return True
    except OSError:
        return False


def kill_blender_processes():
    """Kill any existing Blender processes."""
    try:
        subprocess.run(['pkill', '-f', 'blender'], check=False, timeout=5)
        time.sleep(2)  # Allow processes to terminate
        return True
    except subprocess.TimeoutExpired:
        print("Warning: pkill timed out")
        return False
    except Exception as e:
        print(f"Error killing Blender processes: {e}")
        return False


def wait_for_port(port, timeout=10, service_name="service"):
    """Wait for a service to start listening on a port."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if not is_port_available(port):  # Port is in use = service is running
            print(f"✅ {service_name} is listening on port {port}")
            return True
        time.sleep(0.5)
    
    print(f"❌ {service_name} failed to start on port {port} within {timeout}s")
    return False


@pytest.fixture(scope="session")
def clean_environment():
    """Ensure clean test environment at session start."""
    print("🔧 Setting up clean test environment...")
    kill_blender_processes()
    
    # Verify required ports are available
    if not is_port_available(BLD_REMOTE_PORT):
        pytest.skip(f"Port {BLD_REMOTE_PORT} not available for BLD_Remote_MCP testing")
    if not is_port_available(BLENDER_AUTO_PORT):
        pytest.skip(f"Port {BLENDER_AUTO_PORT} not available for BlenderAutoMCP testing")
    
    yield
    
    # Cleanup after all tests
    print("🧹 Final test environment cleanup...")
    kill_blender_processes()


@pytest.fixture
def blender_path():
    """Provide Blender executable path."""
    if not os.path.exists(BLENDER_PATH):
        pytest.skip(f"Blender not found at {BLENDER_PATH}")
    return BLENDER_PATH


@pytest.fixture
def bld_remote_port():
    """Provide BLD_Remote_MCP port number."""
    return BLD_REMOTE_PORT


@pytest.fixture
def blender_auto_port():
    """Provide BlenderAutoMCP port number."""
    return BLENDER_AUTO_PORT


class ServiceManager:
    """Helper class for managing Blender MCP services during tests."""
    
    def __init__(self, blender_path, bld_remote_port, blender_auto_port):
        self.blender_path = blender_path
        self.bld_remote_port = bld_remote_port
        self.blender_auto_port = blender_auto_port
        self.process = None
        
    def start_single_service(self, service="bld_remote"):
        """Start Blender with single MCP service."""
        env = os.environ.copy()
        
        if service == "bld_remote":
            env['BLD_REMOTE_MCP_PORT'] = str(self.bld_remote_port)
            env['BLD_REMOTE_MCP_START_NOW'] = '1'
            port_to_wait = self.bld_remote_port
            service_name = "BLD_Remote_MCP"
        elif service == "blender_auto":
            env['BLENDER_AUTO_MCP_SERVICE_PORT'] = str(self.blender_auto_port)
            env['BLENDER_AUTO_MCP_START_NOW'] = '1'
            port_to_wait = self.blender_auto_port
            service_name = "BlenderAutoMCP"
        else:
            raise ValueError(f"Unknown service: {service}")
        
        self.process = subprocess.Popen(
            [self.blender_path],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Wait for service to start
        if not wait_for_port(port_to_wait, SERVICE_STARTUP_TIMEOUT, service_name):
            self.cleanup()
            pytest.fail(f"Failed to start {service_name}")
            
        return self.process
        
    def start_dual_services(self):
        """Start Blender with both MCP services."""
        env = os.environ.copy()
        env['BLD_REMOTE_MCP_PORT'] = str(self.bld_remote_port)
        env['BLD_REMOTE_MCP_START_NOW'] = '1'
        env['BLENDER_AUTO_MCP_SERVICE_PORT'] = str(self.blender_auto_port)
        env['BLENDER_AUTO_MCP_START_NOW'] = '1'
        
        self.process = subprocess.Popen(
            [self.blender_path],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Wait for both services to start
        bld_remote_ok = wait_for_port(self.bld_remote_port, SERVICE_STARTUP_TIMEOUT, "BLD_Remote_MCP")
        blender_auto_ok = wait_for_port(self.blender_auto_port, SERVICE_STARTUP_TIMEOUT, "BlenderAutoMCP")
        
        if not bld_remote_ok or not blender_auto_ok:
            self.cleanup()
            pytest.fail("Failed to start one or both MCP services")
            
        return self.process
        
    def cleanup(self):
        """Clean up the Blender process."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        kill_blender_processes()


@pytest.fixture
def service_manager(clean_environment, blender_path, bld_remote_port, blender_auto_port):
    """Provide ServiceManager instance for test use."""
    manager = ServiceManager(blender_path, bld_remote_port, blender_auto_port)
    yield manager
    manager.cleanup()


@pytest.fixture
@pytest.mark.blender_required
def bld_remote_service(service_manager):
    """Start and provide BLD_Remote_MCP service."""
    service_manager.start_single_service("bld_remote")
    yield service_manager.bld_remote_port
    # Cleanup handled by service_manager fixture


@pytest.fixture  
@pytest.mark.blender_required
def blender_auto_service(service_manager):
    """Start and provide BlenderAutoMCP service."""
    service_manager.start_single_service("blender_auto")
    yield service_manager.blender_auto_port
    # Cleanup handled by service_manager fixture


@pytest.fixture
@pytest.mark.dual_service
def dual_services(service_manager):
    """Start and provide both MCP services."""
    service_manager.start_dual_services()
    yield {
        'bld_remote_port': service_manager.bld_remote_port,
        'blender_auto_port': service_manager.blender_auto_port
    }
    # Cleanup handled by service_manager fixture


# Test utilities
def create_mcp_client(port):
    """Create MCP client for given port."""
    try:
        from auto_mcp_remote.blender_mcp_client import BlenderMCPClient
        return BlenderMCPClient(port=port)
    except ImportError:
        pytest.skip("auto_mcp_remote client not available")


def compare_responses(response1, response2, tolerance=0.001):
    """Compare two MCP responses for functional equivalence."""
    # Basic type comparison
    if type(response1) != type(response2):
        return False, f"Type mismatch: {type(response1)} vs {type(response2)}"
    
    # If both are strings, compare directly
    if isinstance(response1, str) and isinstance(response2, str):
        return response1 == response2, "String responses differ"
    
    # If both are numbers, use tolerance
    if isinstance(response1, (int, float)) and isinstance(response2, (int, float)):
        diff = abs(response1 - response2)
        return diff <= tolerance, f"Numeric difference {diff} exceeds tolerance {tolerance}"
    
    # For other types, use basic equality
    try:
        equal = response1 == response2
        return equal, "Responses differ" if not equal else "Responses match"
    except:
        return False, "Cannot compare responses"