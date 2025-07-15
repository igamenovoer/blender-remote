#!/usr/bin/env python3
"""
Integration test for blender-remote-cli commands
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from blender_remote.cli import cli


def test_config_commands():
    """Test config get/set commands"""
    print("=== Testing Config Commands ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Override config path for testing
        with patch('blender_remote.cli.CONFIG_FILE', Path(temp_dir) / "test-config.yaml"):
            
            # Create initial config
            from blender_remote.cli import BlenderRemoteConfig
            config = BlenderRemoteConfig()
            config.config_path = Path(temp_dir) / "test-config.yaml"
            
            initial_config = {
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
            config.save(initial_config)
            
            # Test config get all
            try:
                from click.testing import CliRunner
                runner = CliRunner()
                
                # Test get all config
                result = runner.invoke(cli, ['config', 'get'])
                print(f"Get all config result: {result.output}")
                assert result.exit_code == 0
                assert "mcp_service:" in result.output
                assert "log_level: INFO" in result.output
                print("[PASS] Config get all works")
                
                # Test get specific value
                result = runner.invoke(cli, ['config', 'get', 'mcp_service.log_level'])
                print(f"Get log_level result: {result.output}")
                assert result.exit_code == 0
                assert "INFO" in result.output
                print("[PASS] Config get specific value works")
                
                # Test set value
                result = runner.invoke(cli, ['config', 'set', 'mcp_service.log_level=DEBUG'])
                print(f"Set log_level result: {result.output}")
                assert result.exit_code == 0
                print("[PASS] Config set works")
                
                # Verify the set worked
                result = runner.invoke(cli, ['config', 'get', 'mcp_service.log_level'])
                print(f"Get updated log_level result: {result.output}")
                assert result.exit_code == 0
                assert "DEBUG" in result.output
                print("[PASS] Config set verification works")
                
            except ImportError:
                print("[WARNING]  Click testing not available, skipping CLI runner tests")


def test_start_command_syntax():
    """Test start command syntax without actually running Blender"""
    print("\n=== Testing Start Command Syntax ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create fake blender executable
        fake_blender = Path(temp_dir) / "fake_blender"
        fake_blender.write_text("#!/bin/bash\necho 'Blender 4.4.3'\n")
        fake_blender.chmod(0o755)
        
        # Create fake scene file
        fake_scene = Path(temp_dir) / "test_scene.blend"
        fake_scene.write_text("fake blend file")
        
        # Override config for testing
        with patch('blender_remote.cli.CONFIG_FILE', Path(temp_dir) / "test-config.yaml"):
            from blender_remote.cli import BlenderRemoteConfig
            config = BlenderRemoteConfig()
            config.config_path = Path(temp_dir) / "test-config.yaml"
            
            test_config = {
                "blender": {
                    "version": "4.4.3",
                    "exec_path": str(fake_blender),
                    "root_dir": str(temp_dir),
                    "plugin_dir": str(temp_dir)
                },
                "mcp_service": {
                    "default_port": 6688,
                    "log_level": "INFO"
                }
            }
            config.save(test_config)
            
            try:
                from click.testing import CliRunner
                runner = CliRunner()
                
                # Test start command with all options (but don't actually execute)
                # We'll patch subprocess.run to avoid running Blender
                with patch('subprocess.run') as mock_run:
                    mock_run.return_value.returncode = 0
                    
                    result = runner.invoke(cli, [
                        'start', 
                        '--scene', str(fake_scene),
                        '--log-level', 'DEBUG',
                        '--port', '7777',
                        '--background'
                    ])
                    
                    print(f"Start command result: {result.output}")
                    assert result.exit_code == 0
                    assert "Starting Blender with BLD_Remote_MCP on port 7777" in result.output
                    assert f"Opening scene: {fake_scene}" in result.output
                    assert "Log level override: DEBUG" in result.output
                    assert "Background mode: Blender will run headless" in result.output
                    print("[PASS] Start command with all options works")
                    
                    # Verify the subprocess call had correct arguments
                    mock_run.assert_called_once()
                    call_args = mock_run.call_args[0][0]  # First positional argument (the command)
                    
                    # Check command structure
                    assert str(fake_blender) in call_args
                    assert str(fake_scene) in call_args
                    assert "--background" in call_args
                    assert "--python" in call_args
                    print("[PASS] Blender command arguments are correct")
                    
            except ImportError:
                print("[WARNING]  Click testing not available, skipping CLI runner tests")


def main():
    """Run all integration tests"""
    print("Testing blender-remote CLI integration...")
    
    try:
        test_config_commands()
        test_start_command_syntax()
        
        print("\n" + "="*50)
        print("[PASS] All CLI integration tests PASSED!")
        return 0
        
    except Exception as e:
        print(f"\n[FAIL] CLI integration tests FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())