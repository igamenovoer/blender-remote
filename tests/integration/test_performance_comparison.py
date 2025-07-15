"""
Performance Comparison Tests - BLD_Remote_MCP vs BlenderAutoMCP

This module compares performance characteristics between our BLD_Remote_MCP
service and the reference BlenderAutoMCP implementation to ensure we don't
have significant performance regressions.
"""

import pytest
import time
import statistics
import sys
from pathlib import Path

# Add auto_mcp_remote client interface to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "context" / "refcode"))

try:
    from auto_mcp_remote.blender_mcp_client import BlenderMCPClient
except ImportError as e:
    pytest.skip(f"auto_mcp_remote client not available: {e}", allow_module_level=True)


class PerformanceTester:
    """Manages performance testing between both MCP services."""

    def __init__(self, bld_remote_port, blender_auto_port):
        self.bld_remote_port = bld_remote_port
        self.blender_auto_port = blender_auto_port
        self.bld_remote_client = None
        self.blender_auto_client = None

    def setup_clients(self):
        """Create clients for both services."""
        self.bld_remote_client = BlenderMCPClient(port=self.bld_remote_port)
        self.blender_auto_client = BlenderMCPClient(port=self.blender_auto_port)

    def measure_execution_time(self, client, command_func, iterations=5):
        """Measure execution time for a command over multiple iterations."""
        times = []

        for i in range(iterations):
            start_time = time.perf_counter()
            try:
                result = command_func(client)
                end_time = time.perf_counter()
                execution_time = end_time - start_time
                times.append(execution_time)
            except Exception as e:
                # Record failure but don't include in timing
                print(f"Iteration {i+1} failed: {e}")
                continue

        if not times:
            return None, "All iterations failed"

        return {
            "times": times,
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "min": min(times),
            "max": max(times),
            "stdev": statistics.stdev(times) if len(times) > 1 else 0,
            "iterations": len(times),
        }, None

    def compare_performance(
        self, command_description, command_func, iterations=5, tolerance_factor=2.0
    ):
        """Compare performance between both services."""
        print(f"[TIME] Performance test: {command_description}")

        # Measure BLD_Remote_MCP
        bld_stats, bld_error = self.measure_execution_time(
            self.bld_remote_client, command_func, iterations
        )

        # Measure BlenderAutoMCP
        auto_stats, auto_error = self.measure_execution_time(
            self.blender_auto_client, command_func, iterations
        )

        result = {
            "command": command_description,
            "bld_remote": bld_stats,
            "blender_auto": auto_stats,
            "bld_error": bld_error,
            "auto_error": auto_error,
        }

        # Calculate performance ratio if both succeeded
        if bld_stats and auto_stats:
            ratio = bld_stats["mean"] / auto_stats["mean"]
            result["performance_ratio"] = ratio
            result["performance_acceptable"] = ratio <= tolerance_factor

            print(
                f"  BLD_Remote_MCP: {bld_stats['mean']:.4f}s (±{bld_stats['stdev']:.4f}s)"
            )
            print(
                f"  BlenderAutoMCP: {auto_stats['mean']:.4f}s (±{auto_stats['stdev']:.4f}s)"
            )
            print(
                f"  Performance ratio: {ratio:.2f}x ({'[PASS] PASS' if ratio <= tolerance_factor else '[FAIL] FAIL'})"
            )
        else:
            result["performance_ratio"] = None
            result["performance_acceptable"] = False
            print(
                f"  Performance comparison failed - BLD error: {bld_error}, Auto error: {auto_error}"
            )

        return result

    def cleanup(self):
        """Clean up client connections."""
        try:
            if self.bld_remote_client:
                self.bld_remote_client.disconnect()
        except:
            pass
        try:
            if self.blender_auto_client:
                self.blender_auto_client.disconnect()
        except:
            pass


@pytest.fixture
def performance_tester(dual_services):
    """Create performance tester with both services running."""
    tester = PerformanceTester(
        dual_services["bld_remote_port"], dual_services["blender_auto_port"]
    )
    tester.setup_clients()
    yield tester
    tester.cleanup()


@pytest.mark.slow
@pytest.mark.dual_service
class TestPerformanceComparison:
    """Performance comparison test cases."""

    def test_simple_command_performance(self, performance_tester):
        """Test performance of simple Python commands."""

        def simple_command(client):
            return client.execute_python("result = 2 + 2")

        result = performance_tester.compare_performance(
            "Simple arithmetic", simple_command, iterations=10
        )

        # Our service should not be more than 2x slower than reference
        assert result[
            "performance_acceptable"
        ], f"Performance regression: {result['performance_ratio']:.2f}x slower than BlenderAutoMCP"

    def test_blender_api_performance(self, performance_tester):
        """Test performance of Blender API access."""

        def blender_api_command(client):
            return client.execute_python("import bpy; result = len(bpy.data.objects)")

        result = performance_tester.compare_performance(
            "Blender API access", blender_api_command, iterations=10
        )

        assert result[
            "performance_acceptable"
        ], f"Blender API performance regression: {result['performance_ratio']:.2f}x slower"

    def test_object_creation_performance(self, performance_tester):
        """Test performance of object creation operations."""

        def object_creation_command(client):
            code = """
import bpy
# Create a cube
bpy.ops.mesh.primitive_cube_add()
result = "cube_created"
"""
            return client.execute_python(code)

        result = performance_tester.compare_performance(
            "Object creation", object_creation_command, iterations=5
        )

        assert result[
            "performance_acceptable"
        ], f"Object creation performance regression: {result['performance_ratio']:.2f}x slower"

    def test_large_code_performance(self, performance_tester):
        """Test performance with larger code blocks."""

        def large_code_command(client):
            large_code = """
import bpy
import math

# Create multiple objects and perform calculations
objects_created = []
for i in range(10):
    bpy.ops.mesh.primitive_cube_add(location=(i, 0, 0))
    obj = bpy.context.active_object
    obj.name = f"PerfTest_{i}"
    objects_created.append(obj.name)

# Perform calculations
calculations = []
for x in range(100):
    value = math.sin(x) * math.cos(x) * math.tan(x / 10)
    calculations.append(value)

result = {
    'objects': len(objects_created),
    'calculations': len(calculations),
    'total_time': 'measured_externally'
}
"""
            return client.execute_python(large_code)

        result = performance_tester.compare_performance(
            "Large code execution", large_code_command, iterations=3
        )

        # Allow more tolerance for complex operations
        assert (
            result["performance_ratio"] is None or result["performance_ratio"] <= 3.0
        ), f"Large code performance regression: {result['performance_ratio']:.2f}x slower"

    def test_connection_overhead(self, performance_tester):
        """Test connection establishment overhead."""

        def quick_connection_test(client):
            # Test multiple quick commands to measure connection overhead
            return client.execute_python("x = 1")

        # Test many quick commands
        result = performance_tester.compare_performance(
            "Connection overhead", quick_connection_test, iterations=20
        )

        assert result[
            "performance_acceptable"
        ], f"Connection overhead regression: {result['performance_ratio']:.2f}x slower"

    def test_concurrent_operation_handling(self, performance_tester):
        """Test how well services handle rapid sequential operations."""

        def rapid_sequential_commands(client):
            # Execute multiple commands in sequence
            for i in range(5):
                client.execute_python(f"var_{i} = {i} * 2")
            return client.execute_python(
                "result = sum([var_0, var_1, var_2, var_3, var_4])"
            )

        result = performance_tester.compare_performance(
            "Sequential operations", rapid_sequential_commands, iterations=5
        )

        assert result[
            "performance_acceptable"
        ], f"Sequential operations performance regression: {result['performance_ratio']:.2f}x slower"


@pytest.mark.slow
@pytest.mark.dual_service
def test_performance_summary(dual_services):
    """Generate a comprehensive performance summary."""
    print("\n" + "=" * 60)
    print("PERFORMANCE SUMMARY")
    print("=" * 60)

    tester = PerformanceTester(
        dual_services["bld_remote_port"], dual_services["blender_auto_port"]
    )
    tester.setup_clients()

    try:
        test_cases = [
            ("Basic arithmetic", lambda c: c.execute_python("result = 42")),
            (
                "Import statement",
                lambda c: c.execute_python("import math; result = math.pi"),
            ),
            (
                "Blender API call",
                lambda c: c.execute_python(
                    "import bpy; result = bpy.app.version_string"
                ),
            ),
            ("Simple loop", lambda c: c.execute_python("result = sum(range(100))")),
        ]

        results = []
        for name, func in test_cases:
            result = tester.compare_performance(name, func, iterations=10)
            results.append(result)

        # Print summary
        print("\nPerformance Results:")
        print("-" * 40)
        total_acceptable = 0
        for result in results:
            if result["performance_ratio"] is not None:
                status = "[PASS] PASS" if result["performance_acceptable"] else "[FAIL] FAIL"
                print(
                    f"{result['command']:20} {result['performance_ratio']:6.2f}x {status}"
                )
                if result["performance_acceptable"]:
                    total_acceptable += 1
            else:
                print(f"{result['command']:20} ERROR")

        print(
            f"\nSummary: {total_acceptable}/{len(results)} tests passed performance criteria"
        )
        print("=" * 60)

    finally:
        tester.cleanup()


if __name__ == "__main__":
    # Allow running this test file directly
    pytest.main([__file__, "-v", "-s", "--tb=short"])
