#!/usr/bin/env python3
"""
Test logging control for BLD Remote MCP utils
"""

import os
import sys
import subprocess

def test_log_level(level, expected_outputs):
    """Test logging at a specific level"""
    print(f"\n=== Testing BLD_REMOTE_LOG_LEVEL={level} ===")
    
    # Create a test script that imports utils and logs at all levels
    test_script = f"""
import sys
sys.path.insert(0, '/workspace/code/blender-remote/blender_addon/bld_remote_mcp')

from utils import log_debug, log_info, log_warning, log_error, log_critical

print("Testing log levels with BLD_REMOTE_LOG_LEVEL={level}")
log_debug("This is a DEBUG message")
log_info("This is an INFO message") 
log_warning("This is a WARNING message")
log_error("This is an ERROR message")
log_critical("This is a CRITICAL message")
"""
    
    # Run the test script with the specified log level
    env = os.environ.copy()
    env['BLD_REMOTE_LOG_LEVEL'] = level
    
    result = subprocess.run([
        sys.executable, '-c', test_script
    ], env=env, capture_output=True, text=True)
    
    output = result.stdout
    print("Output:")
    print(output)
    
    # Check expected outputs
    success = True
    for expected in expected_outputs:
        if expected not in output:
            print(f"❌ Expected to see: {expected}")
            success = False
        else:
            print(f"✅ Found expected: {expected}")
    
    # Check unexpected outputs
    all_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    for level_name in all_levels:
        if level_name not in expected_outputs:
            if f"[{level_name}]" in output:
                print(f"❌ Should NOT see {level_name} messages")
                success = False
    
    return success

def main():
    """Test all log levels"""
    print("Testing BLD Remote MCP logging control...")
    
    tests = [
        ("DEBUG", ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
        ("INFO", ["INFO", "WARNING", "ERROR", "CRITICAL"]),
        ("WARNING", ["WARNING", "ERROR", "CRITICAL"]),
        ("ERROR", ["ERROR", "CRITICAL"]),
        ("CRITICAL", ["CRITICAL"]),
        ("", ["INFO", "WARNING", "ERROR", "CRITICAL"]),  # Default to INFO
        ("invalid", ["INFO", "WARNING", "ERROR", "CRITICAL"]),  # Invalid defaults to INFO
    ]
    
    all_passed = True
    for level, expected in tests:
        success = test_log_level(level, expected)
        if not success:
            all_passed = False
    
    print(f"\n{'='*50}")
    if all_passed:
        print("✅ All logging control tests PASSED!")
    else:
        print("❌ Some logging control tests FAILED!")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())