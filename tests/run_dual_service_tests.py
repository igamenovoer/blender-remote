#!/usr/bin/env python3
"""
Test Runner for BLD_Remote_MCP vs BlenderAutoMCP Comparison

This script provides an easy way to run comprehensive comparison tests
between our BLD_Remote_MCP service and the reference BlenderAutoMCP
implementation.
"""

import sys
import os
import subprocess
import argparse
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def run_command(cmd, description, timeout=60):
    """Run a command with timeout and error handling."""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}")
    print("")

    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            timeout=timeout,
            capture_output=False,  # Let output stream directly
            check=False,
        )

        if result.returncode == 0:
            print(f"\n✅ {description} - PASSED")
            return True
        else:
            print(f"\n❌ {description} - FAILED (exit code: {result.returncode})")
            return False

    except subprocess.TimeoutExpired:
        print(f"\n⏰ {description} - TIMEOUT ({timeout}s)")
        return False
    except Exception as e:
        print(f"\n💥 {description} - ERROR: {e}")
        return False


def check_prerequisites():
    """Check if all prerequisites are available."""
    print("🔍 Checking prerequisites...")

    issues = []

    # Check Blender
    blender_path = "/apps/blender-4.4.3-linux-x64/blender"
    if not os.path.exists(blender_path):
        issues.append(f"Blender not found at {blender_path}")
    else:
        print(f"✅ Blender found at {blender_path}")

    # Check addon directory
    addon_dir = Path.home() / ".config/blender/4.4/scripts/addons/bld_remote_mcp"
    if not addon_dir.exists():
        issues.append(f"BLD_Remote_MCP addon not found at {addon_dir}")
    else:
        print(f"✅ BLD_Remote_MCP addon found at {addon_dir}")

    # Check auto_mcp_remote
    auto_mcp_path = PROJECT_ROOT / "context/refcode/auto_mcp_remote"
    if not auto_mcp_path.exists():
        issues.append(f"auto_mcp_remote not found at {auto_mcp_path}")
    else:
        print(f"✅ auto_mcp_remote found at {auto_mcp_path}")

    # Check pytest
    try:
        subprocess.run(
            ["python", "-m", "pytest", "--version"], capture_output=True, check=True
        )
        print("✅ pytest available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        issues.append("pytest not available - install with 'pip install pytest'")

    if issues:
        print(f"\n❌ Prerequisites check failed:")
        for issue in issues:
            print(f"  - {issue}")
        return False

    print("✅ All prerequisites satisfied")
    return True


def kill_blender_processes():
    """Kill any existing Blender processes."""
    print("🔄 Cleaning up any existing Blender processes...")
    try:
        subprocess.run(["pkill", "-f", "blender"], check=False, timeout=10)
        time.sleep(2)
        print("✅ Blender processes cleaned up")
    except subprocess.TimeoutExpired:
        print("⚠️ Warning: pkill timed out")
    except Exception as e:
        print(f"⚠️ Warning: Error during cleanup: {e}")


def main():
    parser = argparse.ArgumentParser(description="Run BLD_Remote_MCP comparison tests")

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick tests only (no performance tests)",
    )
    parser.add_argument(
        "--performance", action="store_true", help="Run performance tests only"
    )
    parser.add_argument(
        "--unit", action="store_true", help="Run unit tests only (single service)"
    )
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run integration tests only (dual service)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Test timeout in seconds (default: 300)",
    )

    args = parser.parse_args()

    print("🧪 BLD_Remote_MCP Dual Service Test Runner")
    print("=" * 60)

    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)

    # Clean environment
    kill_blender_processes()

    # Determine which tests to run
    test_suites = []

    if args.unit:
        test_suites.append(
            ("Unit Tests", ["python", "-m", "pytest", "tests/test_bld_remote_mcp.py"])
        )
    elif args.integration:
        test_suites.append(
            ("Integration Tests", ["python", "-m", "pytest", "tests/integration/"])
        )
    elif args.performance:
        test_suites.append(
            (
                "Performance Tests",
                [
                    "python",
                    "-m",
                    "pytest",
                    "tests/integration/test_performance_comparison.py",
                    "-m",
                    "slow",
                ],
            )
        )
    elif args.quick:
        test_suites.extend(
            [
                (
                    "Unit Tests",
                    ["python", "-m", "pytest", "tests/test_bld_remote_mcp.py"],
                ),
                (
                    "Basic Integration",
                    [
                        "python",
                        "-m",
                        "pytest",
                        "tests/integration/test_dual_service_comparison.py",
                        "-m",
                        "not slow",
                    ],
                ),
            ]
        )
    else:
        # Run all tests
        test_suites.extend(
            [
                (
                    "Unit Tests",
                    ["python", "-m", "pytest", "tests/test_bld_remote_mcp.py"],
                ),
                (
                    "Integration Tests",
                    [
                        "python",
                        "-m",
                        "pytest",
                        "tests/integration/test_dual_service_comparison.py",
                    ],
                ),
                (
                    "Performance Tests",
                    [
                        "python",
                        "-m",
                        "pytest",
                        "tests/integration/test_performance_comparison.py",
                    ],
                ),
            ]
        )

    # Add common pytest flags
    for suite_name, cmd in test_suites:
        if args.verbose:
            cmd.extend(["-v", "-s"])
        cmd.extend(["--tb=short", "--timeout", str(args.timeout)])

    # Run test suites
    results = []
    total_start_time = time.time()

    for suite_name, cmd in test_suites:
        start_time = time.time()
        success = run_command(cmd, suite_name, args.timeout)
        end_time = time.time()

        results.append(
            {"name": suite_name, "success": success, "duration": end_time - start_time}
        )

        # Clean up between test suites
        kill_blender_processes()
        time.sleep(3)

    total_end_time = time.time()
    total_duration = total_end_time - total_start_time

    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)

    passed = 0
    failed = 0

    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        duration = result["duration"]
        print(f"{result['name']:25} {status:10} ({duration:.1f}s)")

        if result["success"]:
            passed += 1
        else:
            failed += 1

    print("-" * 60)
    print(f"Total: {passed + failed} tests, {passed} passed, {failed} failed")
    print(f"Total duration: {total_duration:.1f}s")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print(
            "✅ BLD_Remote_MCP appears to be functionally equivalent to BlenderAutoMCP"
        )
        exit_code = 0
    else:
        print(f"\n💥 {failed} TEST SUITE(S) FAILED")
        print("❌ BLD_Remote_MCP has functional differences or issues")
        exit_code = 1

    # Final cleanup
    kill_blender_processes()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
