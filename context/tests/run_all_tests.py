#!/usr/bin/env python3
"""
Test runner for all blender-remote client tests.

Runs all test scripts and aggregates results.
"""

import sys
import os
import time
import subprocess
from pathlib import Path


def run_test_script(script_path):
    """Run a test script and capture results."""
    print(f"\n{'='*60}")
    print(f"Running: {script_path.name}")
    print(f"{'='*60}")
    
    try:
        # Run the test script
        result = subprocess.run([
            sys.executable, str(script_path)
        ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
        
        # Print output in real-time style
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0, result.stdout, result.stderr
    
    except subprocess.TimeoutExpired:
        print(f"TEST TIMEOUT: {script_path.name}")
        return False, "", "Test timed out after 5 minutes"
    except Exception as e:
        print(f"TEST ERROR: {script_path.name} - {str(e)}")
        return False, "", str(e)


def main():
    """Run all tests and summarize results."""
    print("=== Blender Remote Client Test Suite ===")
    print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Find all test scripts
    test_dir = Path(__file__).parent
    test_scripts = [
        test_dir / "test_fallback_communication.py",  # Run fallback test first
        test_dir / "test_io_handling_focused.py",     # I/O focused tests (core logic assumed working)
        test_dir / "test_with_fallback.py",           # Enhanced test with fallbacks
        test_dir / "test_client_connection.py",
        test_dir / "test_scene_manager_objects.py", 
        test_dir / "test_scene_manager_export.py",
    ]
    
    # Verify test scripts exist
    available_scripts = []
    for script in test_scripts:
        if script.exists():
            available_scripts.append(script)
        else:
            print(f"WARNING: Test script not found: {script}")
    
    if not available_scripts:
        print("ERROR: No test scripts found!")
        return 1
    
    print(f"Found {len(available_scripts)} test scripts")
    
    # Run each test
    results = []
    total_passed = 0
    total_failed = 0
    
    for script in available_scripts:
        success, stdout, stderr = run_test_script(script)
        results.append({
            "script": script.name,
            "success": success,
            "stdout": stdout,
            "stderr": stderr
        })
        
        if success:
            total_passed += 1
        else:
            total_failed += 1
    
    # Final summary
    print(f"\n{'='*60}")
    print("=== TEST SUITE SUMMARY ===")
    print(f"{'='*60}")
    
    for result in results:
        status = "PASS" if result["success"] else "FAIL"
        print(f"[{status}] {result['script']}")
    
    print(f"\nOverall: {total_passed}/{len(available_scripts)} test scripts passed")
    
    if total_failed > 0:
        print(f"\n{total_failed} test script(s) failed. Check individual test logs for details.")
    
    # Save combined results
    log_dir = Path(__file__).parent.parent / "logs" / "tests"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    summary_file = log_dir / f"test_suite_summary_{int(time.time())}.log"
    with open(summary_file, "w") as f:
        f.write(f"Blender Remote Client Test Suite Summary\n")
        f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for result in results:
            status = "PASS" if result["success"] else "FAIL"
            f.write(f"[{status}] {result['script']}\n")
            
            if result["stderr"]:
                f.write(f"  STDERR: {result['stderr']}\n")
        
        f.write(f"\nOverall: {total_passed}/{len(available_scripts)} passed\n")
    
    print(f"\nSummary saved to: {summary_file}")
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())