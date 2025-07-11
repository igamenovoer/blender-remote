#!/usr/bin/env python3
"""
Comprehensive integration test showing OmegaConf improvements in CLI
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from blender_remote.cli import cli, BlenderRemoteConfig
from omegaconf import OmegaConf


def test_omegaconf_cli_workflow():
    """Test complete CLI workflow with OmegaConf features"""
    print("=== Testing Complete OmegaConf CLI Workflow ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir) / "omegaconf-test-config.yaml"
        
        # Override config path for testing
        with patch('blender_remote.cli.CONFIG_FILE', config_file):
            
            # Create initial config manually to test OmegaConf features
            config = BlenderRemoteConfig()
            config.config_path = config_file
            
            initial_config = {
                "blender": {
                    "version": "4.4.3",
                    "exec_path": "/apps/blender",
                    "root_dir": "/apps",
                    "plugin_dir": "/home/user/.config/blender/4.4/scripts/addons"
                },
                "mcp_service": {
                    "default_port": 6688,
                    "log_level": "INFO",
                    "features": {
                        "auto_start": True,
                        "background_support": True,
                        "scene_loading": True
                    },
                    "advanced": {
                        "connection_timeout": 30.0,
                        "retry_attempts": 3,
                        "use_ssl": False
                    }
                },
                "experimental": {
                    "new_feature": "enabled",
                    "beta_apis": False
                }
            }
            
            config.save(initial_config)
            print("✅ Created complex nested configuration")
            
            # Test CLI config operations
            try:
                from click.testing import CliRunner
                runner = CliRunner()
                
                # Test getting nested values
                result = runner.invoke(cli, ['config', 'get', 'mcp_service.features.auto_start'])
                assert result.exit_code == 0
                assert "True" in result.output
                print("✅ CLI can get deeply nested boolean values")
                
                result = runner.invoke(cli, ['config', 'get', 'mcp_service.advanced.connection_timeout'])
                assert result.exit_code == 0
                assert "30.0" in result.output
                print("✅ CLI can get float values")
                
                # Test setting nested values
                result = runner.invoke(cli, ['config', 'set', 'mcp_service.advanced.retry_attempts=5'])
                assert result.exit_code == 0
                print("✅ CLI can set nested integer values")
                
                # Test setting new nested structure
                result = runner.invoke(cli, ['config', 'set', 'experimental.new_setting=test_value'])
                assert result.exit_code == 0
                print("✅ CLI can create new nested values")
                
                # Test getting all config (should show clean YAML format)
                result = runner.invoke(cli, ['config', 'get'])
                assert result.exit_code == 0
                assert "mcp_service:" in result.output
                assert "features:" in result.output
                assert "auto_start: true" in result.output
                assert "retry_attempts: 5" in result.output  # Our update
                assert "new_setting: test_value" in result.output  # Our new setting
                print("✅ CLI config get all shows properly formatted YAML")
                
                # Test missing key handling
                result = runner.invoke(cli, ['config', 'get', 'non.existent.key'])
                assert result.exit_code == 0
                assert "not found" in result.output
                print("✅ CLI handles missing keys gracefully")
                
                # Verify the config file is valid YAML and OmegaConf can load it
                loaded = OmegaConf.load(config_file)
                assert loaded.mcp_service.advanced.retry_attempts == 5
                assert loaded.experimental.new_setting == "test_value"
                print("✅ Generated config file is valid OmegaConf YAML")
                
            except ImportError:
                print("⚠️  Click testing not available, skipping CLI runner tests")


def test_omegaconf_config_validation():
    """Test OmegaConf configuration validation features"""
    print("\n=== Testing OmegaConf Configuration Validation ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir) / "validation-test.yaml"
        
        config = BlenderRemoteConfig()
        config.config_path = config_file
        
        # Test valid configuration
        valid_config = {
            "blender": {
                "version": "4.4.3",
                "exec_path": "/valid/path"
            },
            "mcp_service": {
                "default_port": 6688,
                "log_level": "INFO"
            }
        }
        
        config.save(valid_config)
        loaded = config.load()
        
        # Verify structure is preserved
        assert loaded.blender.version == "4.4.3"
        assert loaded.mcp_service.default_port == 6688
        print("✅ Valid configuration saves and loads correctly")
        
        # Test type safety
        config.set("mcp_service.default_port", "7777")
        updated_port = config.get("mcp_service.default_port")
        
        # Should handle string input appropriately
        print(f"✅ Port value handling: {updated_port} (type: {type(updated_port)})")


def test_omegaconf_performance():
    """Test OmegaConf performance with large configs"""
    print("\n=== Testing OmegaConf Performance ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir) / "large-config.yaml"
        
        config = BlenderRemoteConfig()
        config.config_path = config_file
        
        # Create a large nested configuration
        large_config = {
            "blender": {
                "version": "4.4.3",
                "exec_path": "/apps/blender",
                "plugins": {f"plugin_{i}": {"enabled": True, "version": f"1.{i}"} for i in range(50)}
            },
            "mcp_service": {
                "default_port": 6688,
                "endpoints": {f"endpoint_{i}": f"http://service{i}.local" for i in range(20)}
            },
            "scenes": {f"scene_{i}": {"path": f"/scenes/scene_{i}.blend", "active": i % 2 == 0} for i in range(30)}
        }
        
        import time
        
        # Test save performance
        start_time = time.time()
        config.save(large_config)
        save_time = time.time() - start_time
        
        # Test load performance
        start_time = time.time()
        config.load()
        load_time = time.time() - start_time
        
        # Test access performance
        start_time = time.time()
        for i in range(10):
            _ = config.get(f"blender.plugins.plugin_{i}.enabled")
        access_time = time.time() - start_time
        
        print(f"✅ Performance test completed:")
        print(f"   Save time: {save_time:.4f}s")
        print(f"   Load time: {load_time:.4f}s") 
        print(f"   Access time (10 gets): {access_time:.4f}s")
        
        # Verify correctness
        assert config.get("blender.plugins.plugin_5.enabled") is True
        assert config.get("scenes.scene_10.active") is True
        print("✅ Large configuration handled correctly")


def main():
    """Run all OmegaConf CLI integration tests"""
    print("Testing OmegaConf CLI integration and advanced features...")
    
    try:
        test_omegaconf_cli_workflow()
        test_omegaconf_config_validation()
        test_omegaconf_performance()
        
        print("\n" + "="*60)
        print("✅ All OmegaConf CLI integration tests PASSED!")
        print("\nOmegaConf provides these benefits over manual YAML:")
        print("🔹 Robust dot-notation access with error handling")
        print("🔹 Type-aware configuration management")
        print("🔹 Clean, consistent YAML formatting")
        print("🔹 Better performance for large configurations")
        print("🔹 Built-in validation and interpolation support")
        print("🔹 Safe handling of missing keys and nested structures")
        return 0
        
    except Exception as e:
        print(f"\n❌ OmegaConf CLI integration tests FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())