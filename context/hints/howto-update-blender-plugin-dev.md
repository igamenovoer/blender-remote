# How to Update Blender Plugins During Development

A comprehensive guide for updating Blender plugins during development, covering hot reload, programmatic updates, and production deployment strategies based on current best practices and community recommendations.

## Overview

When developing Blender plugins, you need efficient ways to update and reload your code without manually restarting Blender every time. This guide outlines proven approaches ranging from hot reload to full Blender restart, with specific considerations for background mode development, VS Code integration, and production deployment.

## Table of Contents

1. [Development Hot Reload Methods](#development-hot-reload-methods)
2. [VS Code Integration](#vs-code-integration)
3. [Programmatic Update Approaches](#programmatic-update-approaches)
4. [Production Deployment Strategies](#production-deployment-strategies)
5. [Best Practices and Troubleshooting](#best-practices-and-troubleshooting)

---

## Development Hot Reload Methods

### 1. Basic Script Reload (Simple Addons)

The simplest approach for single-file addons or quick testing:

```python
# In Blender console or operator
bpy.ops.script.reload()
```

**Keyboard Shortcut Setup:**
- Go to `Edit → Preferences → Keymap → Screen → Screen (Global)`
- Click `Add New` and expand the entry
- Set identifier to `script.reload`
- Assign your preferred key (e.g., F5)

### 2. Multi-File Addon Reloading with importlib

For multi-file addons, implement proper module reloading in your `__init__.py`:

```python
import bpy

# Check if this add-on is being reloaded
if "addon_props" not in locals():
    from . import addon_props, addon_panel, addon_ops
else:
    import importlib
    # Reload modules and reassign to local names
    addon_props = importlib.reload(addon_props)
    addon_panel = importlib.reload(addon_panel)
    addon_ops = importlib.reload(addon_ops)

def register():
    addon_props.register()
    addon_panel.register()
    addon_ops.register()

def unregister():
    addon_ops.unregister()
    addon_panel.unregister()
    addon_props.unregister()
```

**Key Points:**
- Always reassign the return value of `importlib.reload()`
- Check for module existence rather than "bpy" in locals()
- Order matters - unregister in reverse order

### 3. sys.modules Cleanup (Advanced)

For complete module cleanup when `importlib.reload()` isn't sufficient:

```python
import sys

def cleanse_modules():
    """Remove addon modules from sys.modules for clean reload"""
    # Get current addon name
    addon_name = __name__.split('.')[0]
    
    # Find and remove all addon modules
    modules_to_remove = []
    for module_name in sys.modules.keys():
        if module_name.startswith(addon_name):
            modules_to_remove.append(module_name)
    
    # Remove in sorted order to avoid dependency issues
    for module_name in sorted(modules_to_remove, reverse=True):
        del sys.modules[module_name]

def unregister():
    # Standard unregister code
    for module in reversed(modules):
        module.unregister()
    
    # Clean up sys.modules
    cleanse_modules()
```

**Warning:** This approach can cause crashes and test failures. Use only for development.

### 4. Custom Reload Operator with Blender Restart

The most robust approach that combines hot reloading with automatic Blender restart:

```python
class ADDON_OT_reload_addon(bpy.types.Operator):
    """Reload addon with optional Blender restart"""
    bl_idname = "addon.reload_addon"
    bl_label = "Reload Addon"
    bl_options = {'REGISTER'}
    
    restart_blender: bpy.props.BoolProperty(
        name="Restart Blender",
        description="Restart Blender after reloading the addon",
        default=False
    )
    
    def execute(self, context):
        # Stop any services first
        self.cleanup_addon_services()
        
        if self.restart_blender:
            self.restart_blender_with_recovery()
        else:
            self.reload_addon_modules()
            # Re-register addon
            unregister()
            register()
        
        return {'FINISHED'}
    
    def reload_addon_modules(self):
        """Clean sys.modules for hot reload"""
        import sys
        addon_name = __package__ or "your_addon_name"
        
        # Remove all addon modules from sys.modules
        modules_to_reload = [name for name in sys.modules.keys() 
                           if name.startswith(addon_name)]
        
        for module_name in modules_to_reload:
            del sys.modules[module_name]
    
    def restart_blender_with_recovery(self):
        """Restart Blender and recover current session"""
        import subprocess
        blender_exe = bpy.app.binary_path
        
        restart_cmd = [
            blender_exe,
            "--python-expr",
            "import bpy; bpy.ops.wm.recover_last_session()"
        ]
        
        subprocess.Popen(restart_cmd)
        bpy.ops.wm.quit_blender()
    
    def cleanup_addon_services(self):
        """Clean up any background services or timers"""
        # Remove timers
        if bpy.app.timers.is_registered(my_timer):
            bpy.app.timers.unregister(my_timer)
        
        # Remove handlers
        if my_handler in bpy.app.handlers.frame_change_pre:
            bpy.app.handlers.frame_change_pre.remove(my_handler)
```

**Usage:**
```python
# Hot reload without restart
bpy.ops.addon.reload_addon('EXEC_DEFAULT', restart_blender=False)

# Full restart with session recovery
bpy.ops.addon.reload_addon('EXEC_DEFAULT', restart_blender=True)
```

---

## VS Code Integration

### 1. Blender Development Extension

Install the official VS Code extension for seamless development:
- Extension ID: `JacquesLucke.blender-development`
- Features: Auto-reload, debugging, project management

### 2. Setup Steps

1. **Install Extension**
   ```bash
   code --install-extension JacquesLucke.blender-development
   ```

2. **Configure Settings**
   ```json
   {
     "blender.addon.reloadOnSave": true,
     "blender.addon.justMyCode": false,
     "BLENDER_USER_RESOURCES": "./blender_vscode_development"
   }
   ```

3. **Start Blender from VS Code**
   - Use `Ctrl+Shift+P` → "Blender: Start"
   - Or configure custom launch settings

### 3. Auto-Reload Workflow

The extension provides automatic reloading when files are saved:

```python
# In your addon preferences, add VS Code integration
class AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    
    auto_reload: bpy.props.BoolProperty(
        name="Auto Reload",
        description="Automatically reload addon when files change",
        default=True
    )
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "auto_reload")
        
        if self.auto_reload:
            layout.operator("addon.reload_addon", text="Reload Now")
```

### 4. Debugging Setup

1. **Enable Remote Debugging**
   ```python
   import sys
   import os
   
   # Add debugpy to path if available
   debugpy_path = os.path.join(os.path.dirname(__file__), "debugpy")
   if os.path.exists(debugpy_path):
       sys.path.insert(0, debugpy_path)
       
   try:
       import debugpy
       debugpy.listen(5678)
       print("Debugger listening on port 5678")
   except ImportError:
       print("debugpy not available")
   ```

2. **VS Code Debug Configuration**
   ```json
   {
     "name": "Blender Addon Debug",
     "type": "python",
     "request": "attach",
     "connect": {
       "host": "localhost",
       "port": 5678
     },
     "pathMappings": [
       {
         "localRoot": "${workspaceFolder}",
         "remoteRoot": "."
       }
     ]
   }
   ```

---

## Programmatic Update Approaches

### 1. Automatic File Watching

```python
import os
import time
from pathlib import Path

class AddonWatcher:
    def __init__(self, addon_path):
        self.addon_path = Path(addon_path)
        self.last_modified = {}
        self.scan_files()
    
    def scan_files(self):
        """Scan addon files for modifications"""
        for py_file in self.addon_path.rglob("*.py"):
            self.last_modified[py_file] = py_file.stat().st_mtime
    
    def check_for_changes(self):
        """Check if any files have been modified"""
        changed_files = []
        for py_file in self.addon_path.rglob("*.py"):
            current_mtime = py_file.stat().st_mtime
            if py_file not in self.last_modified or current_mtime > self.last_modified[py_file]:
                changed_files.append(py_file)
                self.last_modified[py_file] = current_mtime
        return changed_files
    
    def reload_if_changed(self):
        """Reload addon if files have changed"""
        if self.check_for_changes():
            bpy.ops.script.reload()
            return True
        return False

# Usage in modal operator or timer
def modal_update_timer():
    watcher = AddonWatcher(addon_path)
    watcher.reload_if_changed()
    return 1.0  # Check every second
```

### 2. Smart Reload with State Preservation

```python
class ADDON_OT_smart_reload(bpy.types.Operator):
    bl_idname = "addon.smart_reload"
    bl_label = "Smart Reload"
    bl_description = "Intelligently reload addon with state preservation"
    
    def execute(self, context):
        try:
            # Save current state
            state = self.save_addon_state()
            
            # Perform reload
            bpy.ops.script.reload()
            
            # Restore state
            self.restore_addon_state(state)
            
            self.report({'INFO'}, "Addon reloaded successfully")
            
        except Exception as e:
            self.report({'ERROR'}, f"Reload failed: {str(e)}")
        
        return {'FINISHED'}
    
    def save_addon_state(self):
        """Save addon state before reload"""
        state = {
            'scene_props': {},
            'preferences': {},
            'active_tools': []
        }
        
        # Save scene properties
        for scene in bpy.data.scenes:
            if hasattr(scene, 'addon_props'):
                state['scene_props'][scene.name] = scene.addon_props.to_dict()
        
        return state
    
    def restore_addon_state(self, state):
        """Restore addon state after reload"""
        # Restore scene properties
        for scene_name, props in state['scene_props'].items():
            if scene_name in bpy.data.scenes:
                scene = bpy.data.scenes[scene_name]
                if hasattr(scene, 'addon_props'):
                    scene.addon_props.from_dict(props)
```

### 3. Automatic Reinstall Approach

```python
import zipfile
import tempfile
import shutil

class AddonReinstaller:
    def __init__(self, addon_path, addon_name):
        self.addon_path = Path(addon_path)
        self.addon_name = addon_name
    
    def package_addon(self):
        """Package addon into zip file"""
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
            with zipfile.ZipFile(tmp.name, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file_path in self.addon_path.rglob("*"):
                    if file_path.is_file() and not file_path.name.startswith('.'):
                        # Skip __pycache__ and .pyc files
                        if '__pycache__' in file_path.parts or file_path.suffix == '.pyc':
                            continue
                        
                        arc_path = file_path.relative_to(self.addon_path.parent)
                        zf.write(file_path, arc_path)
            
            return tmp.name
    
    def reinstall_addon(self):
        """Reinstall addon from current source"""
        try:
            # Disable current addon
            bpy.ops.preferences.addon_disable(module=self.addon_name)
            
            # Package current version
            zip_path = self.package_addon()
            
            # Install new version
            bpy.ops.preferences.addon_install(filepath=zip_path)
            bpy.ops.preferences.addon_enable(module=self.addon_name)
            
            # Cleanup
            os.unlink(zip_path)
            
            return True
            
        except Exception as e:
            print(f"Reinstall failed: {e}")
            return False
```

---

## Production Deployment Strategies

### 1. Blender Restart with Session Recovery

For production environments where reliability is crucial:

```python
class ADDON_OT_restart_blender(bpy.types.Operator):
    bl_idname = "addon.restart_blender"
    bl_label = "Restart Blender"
    bl_description = "Restart Blender and recover session"
    
    def execute(self, context):
        import subprocess
        
        # Get Blender executable path
        blender_exe = bpy.app.binary_path
        
        # Start new Blender instance with session recovery
        subprocess.Popen([
            blender_exe, 
            "-con", 
            "--python-expr", 
            "import bpy; bpy.ops.wm.recover_last_session()"
        ])
        
        # Quit current instance
        bpy.ops.wm.quit_blender()
        
        return {'FINISHED'}
```

### 2. Update Management System

```python
class AddonUpdateManager:
    def __init__(self, addon_name, current_version):
        self.addon_name = addon_name
        self.current_version = current_version
        self.backup_dir = Path(bpy.utils.user_resource('SCRIPTS')) / "addons_backup"
        self.backup_dir.mkdir(exist_ok=True)
    
    def backup_current_version(self):
        """Backup current addon version"""
        addon_path = Path(bpy.utils.user_resource('SCRIPTS')) / "addons" / self.addon_name
        if addon_path.exists():
            backup_path = self.backup_dir / f"{self.addon_name}_backup_{int(time.time())}"
            shutil.copytree(addon_path, backup_path)
            return backup_path
        return None
    
    def install_update(self, update_path):
        """Install addon update"""
        try:
            # Backup current version
            backup_path = self.backup_current_version()
            
            # Disable addon
            bpy.ops.preferences.addon_disable(module=self.addon_name)
            
            # Install update
            bpy.ops.preferences.addon_install(filepath=str(update_path))
            bpy.ops.preferences.addon_enable(module=self.addon_name)
            
            return True, backup_path
            
        except Exception as e:
            return False, str(e)
    
    def rollback_update(self, backup_path):
        """Rollback to previous version"""
        if backup_path and backup_path.exists():
            addon_path = Path(bpy.utils.user_resource('SCRIPTS')) / "addons" / self.addon_name
            if addon_path.exists():
                shutil.rmtree(addon_path)
            shutil.copytree(backup_path, addon_path)
            return True
        return False
```

### 3. Remote Update System

```python
import urllib.request
import json
import hashlib

class RemoteUpdateChecker:
    def __init__(self, update_url, current_version):
        self.update_url = update_url
        self.current_version = current_version
    
    def check_remote_version(self):
        """Check remote server for updates"""
        try:
            with urllib.request.urlopen(self.update_url) as response:
                data = json.loads(response.read().decode())
                return data.get('version'), data.get('download_url'), data.get('checksum')
        except Exception as e:
            print(f"Update check failed: {e}")
            return None, None, None
    
    def download_update(self, download_url, expected_checksum=None):
        """Download update from remote server"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
                urllib.request.urlretrieve(download_url, tmp.name)
                
                # Verify checksum if provided
                if expected_checksum:
                    with open(tmp.name, 'rb') as f:
                        actual_checksum = hashlib.sha256(f.read()).hexdigest()
                    if actual_checksum != expected_checksum:
                        os.unlink(tmp.name)
                        raise ValueError("Checksum mismatch")
                
                return tmp.name
        except Exception as e:
            print(f"Download failed: {e}")
            return None
    
    def is_update_available(self):
        """Check if update is available"""
        remote_version, _, _ = self.check_remote_version()
        if remote_version:
            return self.version_compare(remote_version, self.current_version) > 0
        return False
    
    def version_compare(self, version1, version2):
        """Compare two version strings"""
        def normalize_version(v):
            return [int(x) for x in v.split('.')]
        
        v1_parts = normalize_version(version1)
        v2_parts = normalize_version(version2)
        
        # Pad shorter version with zeros
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))
        
        for v1, v2 in zip(v1_parts, v2_parts):
            if v1 > v2:
                return 1
            elif v1 < v2:
                return -1
        
        return 0
```

---

## Best Practices and Troubleshooting

### Development Best Practices

1. **Use Version Control**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   
   # Create development branch
   git checkout -b development
   
   # Use gitignore for Blender files
   echo "__pycache__/" >> .gitignore
   echo "*.pyc" >> .gitignore
   echo ".blend1" >> .gitignore
   ```

2. **Modular Architecture**
   ```python
   # Structure your addon modularly
   addon/
   ├── __init__.py          # Main registration
   ├── properties.py        # Property definitions
   ├── operators.py         # Operators
   ├── panels.py           # UI panels
   ├── utils.py            # Utility functions
   ├── preferences.py      # Addon preferences
   └── handlers.py         # Event handlers
   ```

3. **Error Handling and Logging**
   ```python
   import logging
   
   # Set up logging
   logging.basicConfig(level=logging.DEBUG)
   logger = logging.getLogger(__name__)
   
   def safe_reload():
       try:
           bpy.ops.script.reload()
           logger.info("Reload successful")
           return True
       except Exception as e:
           logger.error(f"Reload failed: {e}")
           return False
   ```

### Common Issues and Solutions

1. **Module Not Reloading**
   ```python
   # Problem: Module changes not reflected
   # Solution: Use proper importlib.reload pattern
   
   if "my_module" in locals():
       import importlib
       my_module = importlib.reload(my_module)
   else:
       from . import my_module
   ```

2. **Circular Import Issues**
   ```python
   # Problem: Circular imports during reload
   # Solution: Use lazy imports or redesign architecture
   
   def get_operator_class():
       from .operators import MyOperator
       return MyOperator
   
   # Or use TYPE_CHECKING
   from typing import TYPE_CHECKING
   if TYPE_CHECKING:
       from .operators import MyOperator
   ```

3. **Property Registration Errors**
   ```python
   # Problem: Properties not updating after reload
   # Solution: Clear and re-register properties
   
   def unregister():
       # Clear properties first
       props_to_clear = ['my_prop', 'another_prop']
       for prop_name in props_to_clear:
           if hasattr(bpy.types.Scene, prop_name):
               delattr(bpy.types.Scene, prop_name)
       
       # Then unregister classes
       for cls in reversed(classes):
           bpy.utils.unregister_class(cls)
   ```

4. **Timer and Handler Persistence**
   ```python
   # Problem: Timers/handlers persist after reload
   # Solution: Clean up in unregister
   
   active_timers = []
   active_handlers = []
   
   def register():
       # Register timer
       timer = bpy.app.timers.register(my_timer_func)
       active_timers.append(timer)
       
       # Register handler
       bpy.app.handlers.frame_change_pre.append(my_handler)
       active_handlers.append(my_handler)
   
   def unregister():
       # Clean up timers
       for timer in active_timers:
           if bpy.app.timers.is_registered(timer):
               bpy.app.timers.unregister(timer)
       active_timers.clear()
       
       # Clean up handlers
       for handler in active_handlers:
           if handler in bpy.app.handlers.frame_change_pre:
               bpy.app.handlers.frame_change_pre.remove(handler)
       active_handlers.clear()
   ```

### Performance Optimization

1. **Lazy Loading**
   ```python
   def register():
       # Register only essential classes initially
       bpy.utils.register_class(MainPanel)
       
       # Load other modules on demand
       bpy.app.timers.register(delayed_registration, first_interval=0.1)
   
   def delayed_registration():
       # Register remaining classes
       for cls in optional_classes:
           bpy.utils.register_class(cls)
   ```

2. **Selective Reloading**
   ```python
   import time
   
   class SelectiveReloader:
       def __init__(self):
           self.file_timestamps = {}
       
       def check_modified_files(self, addon_path):
           modified = []
           for py_file in Path(addon_path).rglob("*.py"):
               mtime = py_file.stat().st_mtime
               if py_file not in self.file_timestamps or mtime > self.file_timestamps[py_file]:
                   modified.append(py_file)
                   self.file_timestamps[py_file] = mtime
           return modified
       
       def reload_specific_modules(self, modified_files):
           for file_path in modified_files:
               module_name = file_path.stem
               if module_name in sys.modules:
                   importlib.reload(sys.modules[module_name])
   ```

### Testing and Validation

1. **Unit Tests**
   ```python
   import unittest
   import tempfile
   
   class TestAddonReload(unittest.TestCase):
       def setUp(self):
           self.addon_name = "test_addon"
           self.temp_dir = tempfile.mkdtemp()
       
       def test_reload_preserves_state(self):
           # Test that reload preserves important state
           original_state = save_addon_state()
           reload_addon()
           restored_state = save_addon_state()
           self.assertEqual(original_state, restored_state)
       
       def test_reload_updates_functionality(self):
           # Test that reload updates functionality
           pass
       
       def tearDown(self):
           shutil.rmtree(self.temp_dir)
   ```

2. **Integration Tests**
   ```python
   def test_full_reload_cycle():
       """Test complete reload cycle"""
       # Save initial state
       initial_state = capture_blender_state()
       
       # Modify addon code
       modify_addon_code()
       
       # Reload addon
       reload_addon()
       
       # Verify changes took effect
       assert functionality_updated()
       
       # Verify state preserved
       current_state = capture_blender_state()
       assert states_compatible(initial_state, current_state)
   ```

### Future-Proofing

1. **Blender Version Compatibility**
   ```python
   import bpy
   
   def version_compatible_reload():
       if bpy.app.version >= (4, 0, 0):
           # Use new extension system
           use_extension_reload()
       elif bpy.app.version >= (3, 0, 0):
           # Use modern addon system
           use_addon_reload()
       else:
           # Use legacy approach
           use_legacy_reload()
   ```

2. **Extension System (Blender 4.2+)**
   ```python
   # For Blender 4.2+ extension system
   def setup_extension_reload():
       # Use proper manifest and extension structure
       manifest = {
           "schema_version": "1.0.0",
           "id": "my_addon",
           "version": "1.0.0",
           "name": "My Addon",
           "permissions": ["files"]
       }
       
       # Extension-specific reload logic
       pass
   ```

3. **Background Mode Considerations**
   ```python
   def background_safe_reload():
       """Reload that works in background mode"""
       if bpy.app.background:
           # Background mode - no UI updates
           reload_logic_only()
       else:
           # Interactive mode - full reload with UI
           full_reload_with_ui()
   ```

---

## Conclusion

Effective Blender addon updating during development requires a combination of proper code structure, appropriate tools, and good practices. Choose the method that best fits your development workflow:

- **For simple addons**: Use basic script reload with proper importlib patterns
- **For complex development**: Use VS Code integration with auto-reload  
- **For production**: Implement proper update management with backup/rollback
- **For teams**: Use version control with standardized reload procedures

Remember that reload mechanisms are development tools - production addons should be properly packaged and distributed through official channels. Always test your reload mechanisms thoroughly and have fallback strategies for when hot reload fails.

### Quick Reference

| Method | Use Case | Pros | Cons |
|--------|----------|------|------|
| `bpy.ops.script.reload()` | Simple addons | Fast, built-in | Limited, doesn't reload all modules |
| `importlib.reload()` | Multi-file addons | Reliable, controlled | Requires manual setup |
| `sys.modules` cleanup | Complex addons | Complete reload | Can cause crashes |
| VS Code integration | Development workflow | Automated, debugging | Requires setup |
| Blender restart | Production/reliability | Guaranteed clean state | Slower |

The key is to start simple and add complexity only when needed. Most development workflows benefit from a combination of these approaches.
    """Clean and reload all addon modules"""
    import sys
    import importlib
    
    addon_name = __package__ or "your_addon_name"
    
    # Collect modules to reload
    modules_to_reload = []
    for module_name in list(sys.modules.keys()):
        if module_name.startswith(addon_name):
            modules_to_reload.append(module_name)
    
    # Remove modules from sys.modules
    for module_name in modules_to_reload:
        del sys.modules[module_name]
    
    # Force reimport of main module
    if addon_name in sys.modules:
        importlib.reload(sys.modules[addon_name])
```

### Process

1. **Stop Services**: Cleanup TCP servers, timers, handlers first
2. **Module Removal**: Remove all addon modules from `sys.modules`
3. **Force Reimport**: Use `importlib.reload()` on main module
4. **Re-register**: Call `unregister()` then `register()`

## 3. **Programmatic Blender Restart**

For cases where hot reload isn't sufficient due to complex dependencies.

### Restart Patterns

#### Basic Restart
```python
import subprocess
blender_exe = bpy.app.binary_path
subprocess.Popen([blender_exe])
bpy.ops.wm.quit_blender()
```

#### Restart with Session Recovery
```python
restart_cmd = [
    blender_exe,
    "--python-expr", 
    "import bpy; bpy.ops.wm.recover_last_session()"
]
subprocess.Popen(restart_cmd)
bpy.ops.wm.quit_blender()
```

#### Restart with Custom Script
```python
restart_cmd = [
    blender_exe,
    "--python", "/path/to/startup_script.py"
]
subprocess.Popen(restart_cmd)
bpy.ops.wm.quit_blender()
```

### Benefits
- Complete environment reset
- Automatic session recovery
- Handles complex module dependencies
- Clears all Python state

## 4. **Source Update with Backup**

For automated development workflow with file synchronization.

### Implementation

```python
class ADDON_OT_update_from_source(bpy.types.Operator):
    """Update addon from source directory"""
    bl_idname = "addon.update_from_source"
    bl_label = "Update from Source"
    bl_options = {'REGISTER'}
    
    source_path = bpy.props.StringProperty(
        name="Source Path",
        description="Path to source directory",
        subtype='DIR_PATH'
    )
    
    backup_current = BoolProperty(
        name="Backup Current",
        default=True
    )
    
    def execute(self, context):
        if self.backup_current:
            self.create_backup()
        
        self.update_addon_files()
        
        # Reload after update
        bpy.ops.addon.reload_addon('EXEC_DEFAULT')
        
        return {'FINISHED'}
    
    def create_backup(self):
        """Create timestamped backup"""
        import shutil
        from datetime import datetime
        
        addon_dir = os.path.dirname(__file__)
        parent_dir = os.path.dirname(addon_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"addon_backup_{timestamp}"
        backup_path = os.path.join(parent_dir, backup_name)
        
        shutil.copytree(addon_dir, backup_path)
    
    def update_addon_files(self):
        """Copy files from source to addon directory"""
        import shutil
        
        source = self.source_path
        addon_dir = os.path.dirname(__file__)
        
        for root, dirs, files in os.walk(source):
            # Skip __pycache__ directories
            dirs[:] = [d for d in dirs if d != '__pycache__']
            
            rel_path = os.path.relpath(root, source)
            target_dir = os.path.join(addon_dir, rel_path) if rel_path != '.' else addon_dir
            
            os.makedirs(target_dir, exist_ok=True)
            
            for file in files:
                if not file.endswith('.pyc'):
                    src_file = os.path.join(root, file)
                    dst_file = os.path.join(target_dir, file)
                    shutil.copy2(src_file, dst_file)
```

## 5. **VS Code Integration (Highly Recommended)**

### Jacques Lucke's Blender Development Extension

The most efficient approach for active development.

#### Features
- **Hot reload**: `Blender: Reload Addons` command (Ctrl+Shift+P)
- **Auto-reload on save**: Enable `blender.addon.reloadOnSave` setting
- **Symlink creation**: Creates permanent soft links to your workspace
- **Full debugging**: Set breakpoints and debug directly in VS Code
- **Blender 4.2+ Extensions support**: Works with both legacy addons and new extensions

#### Setup
1. Install extension: `JacquesLucke.blender-development`
2. Open your addon folder in VS Code
3. Use `Blender: Start` to launch Blender with the extension
4. Use `Blender: Reload Addons` to update after changes

#### Configuration
```json
{
  "blender.addon.reloadOnSave": true,
  "blender.environmentVariables": {
    "BLENDER_USER_RESOURCES": "./blender_vscode_development"
  }
}
```

## 6. **Traditional Blender Reload Methods**

### F8 Key (Reload Scripts)
- Press **F8** in Blender (or F3 → search "Reload Scripts")
- **Limitation**: Only reloads `__init__.py` files, not full addon modules
- **Best for**: Simple addons or quick script changes

### Manual Disable/Enable
- Go to **Preferences → Add-ons**
- Disable your addon, then enable it again
- **Limitation**: Slow workflow for frequent updates

## 7. **API Integration Approach**

Expose programmatic functions for external automation.

### Implementation

```python
def get_addon_updater_functions():
    """Return functions for programmatic addon management"""
    return {
        'reload_addon': lambda restart=False: 
            bpy.ops.addon.reload_addon('EXEC_DEFAULT', restart_blender=restart),
        'update_from_source': lambda source_path, backup=True, restart=True: 
            bpy.ops.addon.update_from_source('EXEC_DEFAULT', 
                source_path=source_path, 
                backup_current=backup, 
                restart_after_update=restart),
        'restart_blender': lambda: 
            bpy.ops.addon.reload_addon('EXEC_DEFAULT', restart_blender=True),
        'hot_reload': lambda: 
            bpy.ops.addon.reload_addon('EXEC_DEFAULT', restart_blender=False)
    }

# Usage from external scripts
import bpy
updater = bpy.ops.addon.get_addon_updater_functions()
updater['hot_reload']()
```

## 8. **Proven Addon Updater Libraries**

### CGCookie Blender Addon Updater

For production addons with version management.

#### Features
- **GitHub Integration**: Automatic updates from releases/tags
- **One-click Updates**: Built-in UI for version management  
- **Backup/Restore**: Automatic backup and rollback capabilities
- **Version Control**: Min/max version constraints

#### Basic Integration
```python
# In your addon's __init__.py
from . import addon_updater_ops

def register():
    addon_updater_ops.register(bl_info)

# In preferences UI
addon_updater_ops.update_settings_ui(self, context)
```

### Hextant Reload Addon

For rapid development iteration.

#### Features
- **Hotkeys**: `Ctrl+Alt+R` for single addon, `Ctrl+Alt+Shift+R` for all scripts
- **Fast Reload**: Optimized for development workflow
- **Submodule Support**: Works with `register_submodule_factory()`

## 9. **Development Workflow Recommendations**

### For Active Development

1. **Primary**: Use VS Code + Blender Development extension with auto-reload
2. **Secondary**: Implement custom reload operators for manual control
3. **Testing**: Use F8 for quick script reloads
4. **Complex Changes**: Use Blender restart for major structural changes

### For Production Deployment

1. **Versioning**: Implement addon updater for user updates
2. **Backup**: Always create backups before updates
3. **Testing**: Test both hot reload and restart scenarios
4. **Environment**: Separate development from production Blender setups

### For Server/Background Mode Development

When developing plugins that run servers or background services:

#### Service State Management
```python
def cleanup_addon_services():
    """Stop all addon services before reload"""
    # Stop TCP servers
    if hasattr(addon_module, 'tcp_server') and addon_module.tcp_server:
        addon_module.tcp_server.close()
        addon_module.tcp_server = None
    
    # Cancel asyncio tasks
    if hasattr(addon_module, 'server_task') and addon_module.server_task:
        addon_module.server_task.cancel()
        addon_module.server_task = None
    
    # Clear global state
    addon_module.server_port = 0
```

#### Background Mode Considerations
- Test restart behavior in background mode
- Handle signal handlers properly during restart
- Ensure external scripts can trigger updates
- Verify service state persistence across reloads

## 10. **Best Practices Summary**

### Development Phase
1. **Use hot reload** for quick iterations (`sys.modules` cleanup)
2. **Stop services** before reload to prevent conflicts
3. **Clean module cache** for complete refresh
4. **Enable auto-reload** in VS Code for seamless workflow

### Testing Phase
1. **Use Blender restart** for complex changes
2. **Test both GUI and background modes**
3. **Verify server state persistence**
4. **Test with clean Blender instances**

### Production Phase
1. **Implement source update** functionality
2. **Create automated backup** system
3. **Add version checking** and rollback
4. **Provide user-friendly update UI**

### Error Handling
1. **Fallback to restart** if hot reload fails
2. **Preserve configuration** across reloads
3. **Log all operations** for debugging
4. **Handle context restrictions** in background mode

## 11. **Implementation Priority**

For immediate implementation:

1. **Start with**: `sys.modules` cleanup + manual restart operators
2. **Add next**: VS Code integration for daily development
3. **Enhance with**: Source update and backup functionality
4. **Consider later**: Integration with existing updater libraries

## 12. **Common Issues and Solutions**

### Module Import Issues
- **Problem**: Modules not reloading properly
- **Solution**: Clean `sys.modules` completely, use absolute imports

### Service Port Conflicts
- **Problem**: TCP server fails to restart on same port
- **Solution**: Always cleanup server before reload, wait for port release

### Context Access in Background Mode
- **Problem**: `'_RestrictContext' object has no attribute 'view_layer'`
- **Solution**: Handle restricted context gracefully, test context availability

### VS Code Extension Issues
- **Problem**: Auto-reload not working
- **Solution**: Ensure Blender started via VS Code, check workspace setup

### Blender Restart Problems
- **Problem**: Session not recovering properly
- **Solution**: Use `--python-expr` with recovery command, save before restart

## 13. **Testing Your Update System**

### Basic Test Script
```python
def test_addon_reload():
    """Test addon reload functionality"""
    import time
    
    # Test hot reload
    print("Testing hot reload...")
    bpy.ops.addon.reload_addon(restart_blender=False)
    time.sleep(2)
    
    # Verify addon still works
    if hasattr(bpy.ops, 'addon'):
        print("✅ Hot reload successful")
    else:
        print("❌ Hot reload failed")
    
    # Test restart (comment out for automated testing)
    # print("Testing restart...")
    # bpy.ops.addon.reload_addon(restart_blender=True)

# Run test
test_addon_reload()
```

### Automated Testing
- Create test scenes before reload
- Verify addon state after reload
- Test service availability and functionality
- Validate UI elements are properly registered

## 14. **Future-Proofing**

### Blender 4.2+ Extensions
- The reload system should work with both legacy addons and new Extensions
- VS Code extension automatically detects the format
- Consider migration path from addons to Extensions

### Python Version Changes
- Test reload system across Python version updates
- Handle module compatibility issues
- Ensure backward compatibility

### Blender API Changes
- Monitor Blender API deprecations
- Test reload system with new Blender versions
- Adapt context handling for API changes

This comprehensive approach gives you maximum flexibility: hot reload for quick development iterations, automatic restart for complex changes, and full automation capabilities for production deployment scenarios.
