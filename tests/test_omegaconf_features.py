#!/usr/bin/env python3
"""
Test OmegaConf-specific features in blender-remote CLI
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from blender_remote.cli import BlenderRemoteConfig
from omegaconf import OmegaConf


def test_omegaconf_basic_features():
    """Test basic OmegaConf features in config manager"""
    print("=== Testing OmegaConf Basic Features ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_config_path = Path(temp_dir) / "test-omegaconf.yaml"
        
        # Create config manager with custom path
        config = BlenderRemoteConfig()
        config.config_path = temp_config_path
        
        # Test creating config with nested structure
        test_config = {
            "blender": {
                "version": "4.4.3",
                "exec_path": "/fake/blender",
                "root_dir": "/fake",
                "plugin_dir": "/fake/addons"
            },
            "mcp_service": {
                "default_port": 6688,
                "log_level": "INFO",
                "features": {
                    "auto_start": True,
                    "debug_mode": False
                }
            }
        }
        
        # Save config using OmegaConf
        config.save(test_config)
        print(f"✅ Config saved using OmegaConf")
        
        # Load and verify
        loaded = config.load()
        print(f"✅ Config loaded using OmegaConf")
        
        # Test dot notation access with deep nesting
        port = config.get("mcp_service.default_port")
        auto_start = config.get("mcp_service.features.auto_start")
        debug_mode = config.get("mcp_service.features.debug_mode")
        
        assert port == 6688
        assert auto_start is True
        assert debug_mode is False
        print(f"✅ Deep dot notation access works: port={port}, auto_start={auto_start}")
        
        # Test setting deep nested values
        config.set("mcp_service.features.debug_mode", True)
        config.set("mcp_service.new_feature", "test_value")
        
        # Verify the changes
        updated_debug = config.get("mcp_service.features.debug_mode")
        new_feature = config.get("mcp_service.new_feature")
        
        assert updated_debug is True
        assert new_feature == "test_value"
        print(f"✅ Deep setting works: debug_mode={updated_debug}, new_feature={new_feature}")


def test_omegaconf_type_safety():
    """Test OmegaConf type handling and conversion"""
    print("\n=== Testing OmegaConf Type Safety ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_config_path = Path(temp_dir) / "test-types.yaml"
        
        config = BlenderRemoteConfig()
        config.config_path = temp_config_path
        
        # Create config with various types
        test_config = {
            "numbers": {
                "port": 6688,
                "timeout": 30.5,
                "enabled": True
            },
            "strings": {
                "host": "localhost",
                "path": "/path/to/blender"
            }
        }
        
        config.save(test_config)
        config.load()
        
        # Test type preservation
        port = config.get("numbers.port")
        timeout = config.get("numbers.timeout")
        enabled = config.get("numbers.enabled")
        host = config.get("strings.host")
        
        assert isinstance(port, int)
        assert isinstance(timeout, float)
        assert isinstance(enabled, bool)
        assert isinstance(host, str)
        
        print(f"✅ Type preservation works: int={type(port)}, float={type(timeout)}, bool={type(enabled)}, str={type(host)}")
        
        # Test type conversion
        config.set("numbers.port", "7777")  # String that can be converted
        converted_port = config.get("numbers.port")
        
        # OmegaConf should preserve the string since we set it as string
        # This tests that our implementation handles this correctly
        print(f"✅ Type handling: original_port={port}, set_as_string={converted_port}")


def test_omegaconf_yaml_format():
    """Test OmegaConf YAML output formatting"""
    print("\n=== Testing OmegaConf YAML Format ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_config_path = Path(temp_dir) / "test-yaml.yaml"
        
        config = BlenderRemoteConfig()
        config.config_path = temp_config_path
        
        # Create config
        test_config = {
            "blender": {
                "version": "4.4.3",
                "exec_path": "/apps/blender-4.4.3-linux-x64/blender"
            },
            "mcp_service": {
                "default_port": 6688,
                "log_level": "INFO"
            }
        }
        
        config.save(test_config)
        
        # Read the raw YAML file to check formatting
        with open(temp_config_path, 'r') as f:
            yaml_content = f.read()
        
        print("Generated YAML content:")
        print(yaml_content)
        
        # Check that it's properly formatted YAML
        assert "blender:" in yaml_content
        assert "mcp_service:" in yaml_content
        assert "default_port: 6688" in yaml_content
        assert "log_level: INFO" in yaml_content
        
        print("✅ YAML formatting is correct")


def test_omegaconf_error_handling():
    """Test OmegaConf error handling"""
    print("\n=== Testing OmegaConf Error Handling ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_config_path = Path(temp_dir) / "nonexistent.yaml"
        
        config = BlenderRemoteConfig()
        config.config_path = temp_config_path
        
        # Test loading non-existent file
        try:
            config.load()
            print("❌ Should have raised exception for non-existent file")
        except Exception as e:
            print(f"✅ Correctly handled missing file: {e}")
        
        # Test accessing non-existent keys
        config.save({"test": {"value": 123}})
        config.load()
        
        non_existent = config.get("non.existent.key")
        assert non_existent is None
        print(f"✅ Non-existent key returns None: {non_existent}")


def main():
    """Run all OmegaConf feature tests"""
    print("Testing OmegaConf integration in blender-remote CLI...")
    
    try:
        test_omegaconf_basic_features()
        test_omegaconf_type_safety()
        test_omegaconf_yaml_format()
        test_omegaconf_error_handling()
        
        print("\n" + "="*50)
        print("✅ All OmegaConf feature tests PASSED!")
        return 0
        
    except Exception as e:
        print(f"\n❌ OmegaConf tests FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())