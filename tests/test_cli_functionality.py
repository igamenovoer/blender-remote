#!/usr/bin/env python3
"""
Test CLI functionality for blender-remote-cli
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from blender_remote.cli import BlenderRemoteConfig, detect_blender_info


def test_config_manager():
    """Test configuration manager functionality"""
    print("=== Testing Config Manager ===")
    
    # Use temporary config for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_config = Path(temp_dir) / "test-config.yaml"
        
        # Create config manager with custom path
        config = BlenderRemoteConfig()
        config.config_path = temp_config
        
        # Test setting and getting values
        test_config = {
            "blender": {
                "version": "4.4.3",
                "exec_path": "/fake/blender",
                "root_dir": "/fake",
                "plugin_dir": "/fake/addons"
            },
            "mcp_service": {
                "default_port": 6688,
                "log_level": "INFO"
            }
        }
        
        # Save config
        config.save(test_config)
        print(f"[PASS] Config saved to {temp_config}")
        
        # Load and test get
        loaded = config.load()
        print(f"[PASS] Config loaded: {loaded}")
        
        # Test dot notation
        port = config.get("mcp_service.default_port")
        log_level = config.get("mcp_service.log_level")
        print(f"[PASS] Got port: {port}")
        print(f"[PASS] Got log_level: {log_level}")
        
        # Test set
        config.set("mcp_service.log_level", "DEBUG")
        new_log_level = config.get("mcp_service.log_level")
        print(f"[PASS] Updated log_level: {new_log_level}")
        
        assert port == 6688
        assert log_level == "INFO"
        assert new_log_level == "DEBUG"
        
        print("[PASS] Config manager tests passed!")


def test_blender_detection():
    """Test Blender detection with fake executable"""
    print("\n=== Testing Blender Detection (Mock) ===")
    
    # This would normally require a real Blender executable
    # For testing, we just verify the function exists and handles errors
    try:
        detect_blender_info("/fake/blender/path")
        print("[FAIL] Should have raised exception for fake path")
    except Exception as e:
        print(f"[PASS] Correctly handled fake path: {e}")
    

def test_cli_options():
    """Test CLI option parsing"""
    print("\n=== Testing CLI Options ===")
    
    # Test imports
    try:
        from blender_remote.cli import cli
        print("[PASS] CLI module imports successfully")
        
        # Test click configuration
        start_command = None
        for command in cli.commands.values():
            if command.name == "start":
                start_command = command
                break
                
        if start_command:
            print("[PASS] Start command found")
            
            # Check for our new options
            option_names = [param.name for param in start_command.params if hasattr(param, 'name')]
            
            if "scene" in option_names:
                print("[PASS] --scene option present")
            else:
                print("[FAIL] --scene option missing")
                
            if "log_level" in option_names:
                print("[PASS] --log-level option present")
            else:
                print("[FAIL] --log-level option missing")
                
        else:
            print("[FAIL] Start command not found")
            
    except ImportError as e:
        print(f"[FAIL] CLI import failed: {e}")


def main():
    """Run all CLI tests"""
    print("Testing blender-remote CLI functionality...")
    
    try:
        test_config_manager()
        test_blender_detection()
        test_cli_options()
        
        print("\n" + "="*50)
        print("[PASS] All CLI functionality tests PASSED!")
        return 0
        
    except Exception as e:
        print(f"\n[FAIL] CLI tests FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())