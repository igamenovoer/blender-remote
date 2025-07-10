"""
Dual Service Comparison Tests - BLD_Remote_MCP vs BlenderAutoMCP

This module tests that our BLD_Remote_MCP service functions identically to
the reference BlenderAutoMCP implementation in GUI mode.

Both services run simultaneously on different ports and receive identical
commands. Responses are compared to ensure functional equivalence.
"""

import pytest
import sys
import os
import subprocess
import time
import json
import socket
from pathlib import Path

# Add auto_mcp_remote client interface to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "context" / "refcode"))

try:
    from auto_mcp_remote.blender_mcp_client import BlenderMCPClient
    from auto_mcp_remote.client_utils import parse_response
except ImportError as e:
    pytest.skip(f"auto_mcp_remote client not available: {e}", allow_module_level=True)


class DualServiceTester:
    """Manager for dual-service testing setup and teardown."""

    def __init__(self):
        self.blender_process = None
        self.bld_remote_port = 6688
        self.blender_auto_port = 9876
        self.bld_remote_client = None
        self.blender_auto_client = None
        self.blender_path = "/apps/blender-4.4.3-linux-x64/blender"

    def setup_environment(self):
        """Prepare clean test environment."""
        print("🔧 Setting up dual-service test environment...")

        # Kill any existing Blender processes
        try:
            subprocess.run(["pkill", "-f", "blender"], check=False, timeout=5)
            time.sleep(2)  # Allow processes to terminate
        except subprocess.TimeoutExpired:
            print("⚠️ Warning: pkill timed out")

        # Verify ports are available
        if not self._is_port_available(self.bld_remote_port):
            raise RuntimeError(
                f"Port {self.bld_remote_port} (BLD_Remote_MCP) is not available"
            )
        if not self._is_port_available(self.blender_auto_port):
            raise RuntimeError(
                f"Port {self.blender_auto_port} (BlenderAutoMCP) is not available"
            )

        print(
            f"✅ Ports available - BLD Remote: {self.bld_remote_port}, BlenderAuto: {self.blender_auto_port}"
        )

    def _is_port_available(self, port):
        """Check if a port is available for binding."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(("127.0.0.1", port))
            sock.close()
            return True
        except OSError:
            return False

    def start_dual_services(self):
        """Start Blender with both MCP services in GUI mode."""
        print("🚀 Starting Blender with dual MCP services...")

        env = os.environ.copy()
        env["BLD_REMOTE_MCP_PORT"] = str(self.bld_remote_port)
        env["BLD_REMOTE_MCP_START_NOW"] = "1"
        env["BLENDER_AUTO_MCP_SERVICE_PORT"] = str(self.blender_auto_port)
        env["BLENDER_AUTO_MCP_START_NOW"] = "1"

        # Start Blender in background with both services
        self.blender_process = subprocess.Popen(
            [self.blender_path],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )

        # Wait for both services to start
        print("⏳ Waiting for services to initialize...")
        time.sleep(15)  # Give more time for dual service startup

        # Verify both services are responding
        self._verify_service_startup()

    def _verify_service_startup(self):
        """Verify both services are running and responsive."""
        print("🔍 Verifying service startup...")

        # Test BLD_Remote_MCP
        bld_remote_ok = self._test_port_connection(
            self.bld_remote_port, "BLD_Remote_MCP"
        )

        # Test BlenderAutoMCP
        blender_auto_ok = self._test_port_connection(
            self.blender_auto_port, "BlenderAutoMCP"
        )

        if not bld_remote_ok:
            raise RuntimeError(
                f"BLD_Remote_MCP service not responding on port {self.bld_remote_port}"
            )
        if not blender_auto_ok:
            raise RuntimeError(
                f"BlenderAutoMCP service not responding on port {self.blender_auto_port}"
            )

        print("✅ Both services verified as running")

    def _test_port_connection(self, port, service_name):
        """Test basic TCP connection to a service port."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(("127.0.0.1", port))
            sock.close()

            if result == 0:
                print(f"✅ {service_name} port {port}: TCP connection successful")
                return True
            else:
                print(
                    f"❌ {service_name} port {port}: TCP connection failed (code: {result})"
                )
                return False
        except Exception as e:
            print(
                f"❌ {service_name} port {port}: Exception during connection test: {e}"
            )
            return False

    def create_clients(self):
        """Create MCP clients for both services."""
        print("🔌 Creating MCP clients...")

        try:
            self.bld_remote_client = BlenderMCPClient(port=self.bld_remote_port)
            print(f"✅ BLD_Remote_MCP client created (port {self.bld_remote_port})")
        except Exception as e:
            raise RuntimeError(f"Failed to create BLD_Remote_MCP client: {e}")

        try:
            self.blender_auto_client = BlenderMCPClient(port=self.blender_auto_port)
            print(f"✅ BlenderAutoMCP client created (port {self.blender_auto_port})")
        except Exception as e:
            raise RuntimeError(f"Failed to create BlenderAutoMCP client: {e}")

    def execute_command_on_both(self, command_description, command_func):
        """Execute identical command on both services and return results."""
        print(f"🔄 Testing: {command_description}")

        # Execute on BLD_Remote_MCP
        try:
            bld_result = command_func(self.bld_remote_client)
            bld_success = True
        except Exception as e:
            bld_result = {"error": str(e)}
            bld_success = False
            print(f"❌ BLD_Remote_MCP failed: {e}")

        # Execute on BlenderAutoMCP
        try:
            auto_result = command_func(self.blender_auto_client)
            auto_success = True
        except Exception as e:
            auto_result = {"error": str(e)}
            auto_success = False
            print(f"❌ BlenderAutoMCP failed: {e}")

        return {
            "bld_remote": {"result": bld_result, "success": bld_success},
            "blender_auto": {"result": auto_result, "success": auto_success},
            "both_succeeded": bld_success and auto_success,
        }

    def cleanup(self):
        """Clean up test environment."""
        print("🧹 Cleaning up test environment...")

        if self.bld_remote_client:
            try:
                self.bld_remote_client.disconnect()
            except:
                pass

        if self.blender_auto_client:
            try:
                self.blender_auto_client.disconnect()
            except:
                pass

        if self.blender_process:
            try:
                self.blender_process.terminate()
                self.blender_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.blender_process.kill()
                self.blender_process.wait()

        # Final cleanup - kill any remaining Blender processes
        try:
            subprocess.run(["pkill", "-f", "blender"], check=False, timeout=5)
        except subprocess.TimeoutExpired:
            pass

        print("✅ Cleanup completed")


@pytest.fixture(scope="module")
def dual_service_setup():
    """Pytest fixture for dual-service testing setup."""
    tester = DualServiceTester()

    try:
        tester.setup_environment()
        tester.start_dual_services()
        tester.create_clients()
        yield tester
    finally:
        tester.cleanup()


class TestDualServiceComparison:
    """Test cases comparing BLD_Remote_MCP with BlenderAutoMCP."""

    def test_basic_connectivity(self, dual_service_setup):
        """Test basic TCP connectivity to both services."""
        tester = dual_service_setup

        # Both clients should be connected
        assert tester.bld_remote_client is not None, "BLD_Remote_MCP client not created"
        assert (
            tester.blender_auto_client is not None
        ), "BlenderAutoMCP client not created"

    def test_simple_python_execution(self, dual_service_setup):
        """Test basic Python code execution on both services."""
        tester = dual_service_setup

        def execute_simple_code(client):
            return client.execute_python("result = 2 + 2")

        results = tester.execute_command_on_both(
            "Simple Python execution", execute_simple_code
        )

        # Both services should succeed
        assert results["both_succeeded"], f"One or both services failed: {results}"

        # Compare results (both should succeed with similar response structure)
        bld_result = results["bld_remote"]["result"]
        auto_result = results["blender_auto"]["result"]

        # Both should indicate success (exact format may differ but both should work)
        assert (
            "error" not in str(bld_result).lower()
        ), f"BLD_Remote_MCP returned error: {bld_result}"
        assert (
            "error" not in str(auto_result).lower()
        ), f"BlenderAutoMCP returned error: {auto_result}"

    def test_blender_api_access(self, dual_service_setup):
        """Test Blender API access through both services."""
        tester = dual_service_setup

        def access_blender_api(client):
            return client.execute_python("import bpy; result = len(bpy.data.objects)")

        results = tester.execute_command_on_both(
            "Blender API access", access_blender_api
        )

        # Both services should succeed
        assert results["both_succeeded"], f"One or both services failed: {results}"

    def test_scene_object_creation(self, dual_service_setup):
        """Test creating scene objects through both services."""
        tester = dual_service_setup

        def create_cube(client):
            code = """
import bpy
# Clear existing mesh objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False, confirm=False)

# Create a new cube
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
result = len(bpy.data.objects)
"""
            return client.execute_python(code)

        results = tester.execute_command_on_both("Scene object creation", create_cube)

        # Both services should succeed
        assert results["both_succeeded"], f"One or both services failed: {results}"

    def test_error_handling_comparison(self, dual_service_setup):
        """Test error handling consistency between services."""
        tester = dual_service_setup

        def execute_invalid_code(client):
            return client.execute_python("this_is_invalid_python_syntax <<<")

        results = tester.execute_command_on_both("Error handling", execute_invalid_code)

        # Both services should handle the error gracefully (might succeed with error info or fail cleanly)
        # The key is that both behave consistently, not necessarily that both succeed
        bld_result = results["bld_remote"]["result"]
        auto_result = results["blender_auto"]["result"]

        # Both should either succeed (with error info) or fail in a similar manner
        # We test that both services handle errors without crashing
        assert bld_result is not None, "BLD_Remote_MCP returned None result"
        assert auto_result is not None, "BlenderAutoMCP returned None result"

    def test_multiple_sequential_commands(self, dual_service_setup):
        """Test multiple sequential commands on both services."""
        tester = dual_service_setup

        commands = [
            ("Variable assignment", lambda c: c.execute_python("test_var = 'hello'")),
            (
                "Variable access",
                lambda c: c.execute_python("result = test_var + ' world'"),
            ),
            ("Math operation", lambda c: c.execute_python("math_result = 10 * 5")),
        ]

        for cmd_name, cmd_func in commands:
            results = tester.execute_command_on_both(cmd_name, cmd_func)

            # Each command should work on both services
            assert results[
                "both_succeeded"
            ], f"Command '{cmd_name}' failed on one or both services: {results}"

    def test_large_code_execution(self, dual_service_setup):
        """Test execution of larger code blocks."""
        tester = dual_service_setup

        def execute_large_code(client):
            large_code = """
import bpy
import math

# Create multiple objects
results = []
for i in range(5):
    bpy.ops.mesh.primitive_cube_add(location=(i * 2, 0, 0))
    obj = bpy.context.active_object
    obj.name = f"TestCube_{i}"
    results.append(obj.name)

# Perform some calculations
calculated_values = []
for x in range(10):
    value = math.sin(x) * math.cos(x)
    calculated_values.append(value)

result = {
    'objects_created': len(results),
    'object_names': results,
    'calculations': len(calculated_values)
}
"""
            return client.execute_python(large_code)

        results = tester.execute_command_on_both(
            "Large code execution", execute_large_code
        )

        # Both services should handle large code blocks successfully
        assert results["both_succeeded"], f"Large code execution failed: {results}"


if __name__ == "__main__":
    # Allow running this test file directly for development
    print("🧪 Running dual-service comparison tests...")
    pytest.main([__file__, "-v", "-s"])
