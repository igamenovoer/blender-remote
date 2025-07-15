# Cross-Platform Path Handling

This document explains how blender-remote handles file paths, configuration storage, and directory detection across Windows, Linux, and macOS platforms.

## Overview

blender-remote uses industry-standard approaches for cross-platform path handling:

- **Configuration**: Uses `platformdirs` library for OS-appropriate config directories
- **Blender Detection**: Platform-specific addon directory discovery
- **Temporary Files**: Cross-platform temp directory handling
- **Path Normalization**: Consistent path separators for all platforms

## Configuration Storage

### Location by Platform

blender-remote stores its configuration file (`bld-remote-config.yaml`) in platform-appropriate directories:

| Platform | Configuration Directory | Example Path |
|----------|------------------------|--------------|
| **Windows** | `%APPDATA%\blender-remote\` | `C:\Users\Alice\AppData\Roaming\blender-remote\` |
| **Linux** | `~/.config/blender-remote/` | `/home/alice/.config/blender-remote/` |
| **macOS** | `~/Library/Application Support/blender-remote/` | `/Users/alice/Library/Application Support/blender-remote/` |

### Implementation

The configuration directory is determined using the `platformdirs` library:

```python
import platformdirs
from pathlib import Path

CONFIG_DIR = Path(platformdirs.user_config_dir(
    appname="blender-remote", 
    appauthor="blender-remote"
))
CONFIG_FILE = CONFIG_DIR / "bld-remote-config.yaml"
```

### Configuration File Structure

```yaml
blender:
  version: "4.4.3"
  exec_path: "/path/to/blender"
  root_dir: "/path/to/blender/directory"
  plugin_dir: "/path/to/blender/addons"
mcp_service:
  default_port: 6688
  log_level: "INFO"
```

## Blender Addon Directory Detection

### Detection Strategy

blender-remote automatically detects Blender addon directories using platform-specific search patterns:

#### Windows
1. **User Directory**: `%APPDATA%\Blender Foundation\Blender\{version}\scripts\addons\`
2. **System Directory**: `{blender_root}\{version}\scripts\addons\`

#### macOS  
1. **User Directory**: `~/Library/Application Support/Blender/{version}/scripts/addons/`
2. **System Directory**: `{blender_root}/{version}/scripts/addons/`

#### Linux
1. **XDG Config**: `$XDG_CONFIG_HOME/blender/{version}/scripts/addons/` (falls back to `~/.config/`)
2. **System Directory**: `{blender_root}/{version}/scripts/addons/`

### Implementation Details

```python
def detect_blender_addon_dir(blender_version):
    if platform.system() == "Windows":
        # Use platformdirs for Windows AppData
        appdata = Path(platformdirs.user_data_dir(appname="", appauthor="")).parent
        user_path = appdata / "Blender Foundation" / "Blender" / blender_version / "scripts" / "addons"
    elif platform.system() == "darwin":  # macOS
        user_path = Path.home() / "Library" / "Application Support" / "Blender" / blender_version / "scripts" / "addons"
    else:  # Linux and other Unix-like
        xdg_config = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        user_path = xdg_config / "blender" / blender_version / "scripts" / "addons"
    
    return user_path if user_path.exists() else system_fallback_path
```

### Manual Override

If automatic detection fails, users can manually specify the addon directory:

```bash
blender-remote-cli init /path/to/blender
# CLI will prompt for addon directory if not found
```

## Temporary File Handling

### Temporary Directory Usage

blender-remote uses temporary files for:

- **GLB Exports**: Binary mesh data transfer from Blender
- **Debug Logs**: Cross-platform logging in background mode  
- **Screenshots**: Image capture before base64 encoding
- **Process Communication**: PID files for process management

### Platform-Agnostic Implementation

```python
import tempfile
import os

# Get cross-platform temp directory
temp_dir = tempfile.gettempdir()

# Examples by platform:
# Windows: C:\Users\Alice\AppData\Local\Temp\
# Linux:   /tmp/
# macOS:   /var/folders/xy/abc123/T/
```

### GLB Export Example

```python
# Generate unique temporary file path
temp_filepath = os.path.join(
    tempfile.gettempdir(), 
    f"temp_{object_name.replace(' ', '_')}_{int(time.time())}.glb"
)

# Export GLB file
bpy.ops.export_scene.gltf(filepath=temp_filepath, ...)

# Read and cleanup
with open(temp_filepath, 'rb') as f:
    glb_data = f.read()
os.remove(temp_filepath)  # Cross-platform cleanup
```

## Path Normalization

### Forward Slash Consistency

For Python code execution in Blender, paths are normalized to use forward slashes:

```python
# Windows path: C:\Users\Alice\temp\file.txt
temp_path_normalized = temp_path.replace('\\', '/')
# Result: C:/Users/Alice/temp/file.txt

# This ensures Python code works consistently across platforms
python_code = f"with open('{temp_path_normalized}', 'w') as f: ..."
```

### Subprocess Path Handling

When passing file paths to subprocess commands (like Blender CLI), use `.as_posix()`:

```python
addon_zip_path = Path("/path/to/addon.zip")
addon_zip_posix = addon_zip_path.as_posix()  # Always forward slashes

# Safe for all platforms in subprocess calls
subprocess.run([blender_path, "--python-expr", f"import_addon('{addon_zip_posix}')"])
```

## Asset Library Paths

### Library Detection

Asset libraries are detected through Blender's preferences:

```python
# Blender Python code for library discovery
prefs = bpy.context.preferences
asset_libs = prefs.filepaths.asset_libraries

for lib in asset_libs:
    library_path = lib.path  # Platform-specific path
    # Windows: C:\Users\Alice\Documents\Blender\Assets\
    # Linux:   /home/alice/Documents/Blender/Assets/
    # macOS:   /Users/alice/Documents/Blender/Assets/
```

### Path Validation

```python
def validate_library_path(path_str):
    """Cross-platform library path validation."""
    library_path = Path(path_str)
    return library_path.exists() and library_path.is_dir()
```

## Docker Environment Detection

### Cross-Platform Docker Detection

blender-remote detects Docker environments across platforms:

```python
def detect_docker_environment():
    """Detect if running inside Docker container."""
    return (
        os.path.exists("/.dockerenv") or  # Linux containers
        (os.path.exists("/proc/1/cgroup") and 
         any("docker" in line for line in open("/proc/1/cgroup").readlines())) or
        os.environ.get("DOCKER_CONTAINER") == "true"  # Cross-platform env var
    )

# Adjust host accordingly
host = "host.docker.internal" if in_docker else "localhost"
```

## Signal Handling

### Platform-Specific Signals

Different platforms support different process signals:

```python
import signal
import platform

def terminate_process(pid):
    """Cross-platform process termination."""
    if platform.system() == "Windows":
        # Windows: SIGTERM is translated to TerminateProcess
        os.kill(pid, signal.SIGTERM)
    else:
        # Unix-like: Try graceful SIGTERM first, then SIGKILL
        try:
            os.kill(pid, signal.SIGTERM)
        except PermissionError:
            os.kill(pid, signal.SIGKILL)  # Force termination
```

## Best Practices

### 1. Use Standard Libraries

- **`platformdirs`**: For configuration directories
- **`tempfile`**: For temporary file handling  
- **`pathlib.Path`**: For path manipulation
- **`os.path.join()`**: For safe path concatenation

### 2. Path Validation

Always validate paths before use:

```python
from pathlib import Path

def safe_path_access(path_str):
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(f"Path not found: {path}")
    if not path.is_file() and not path.is_dir():
        raise ValueError(f"Invalid path type: {path}")
    return path
```

### 3. Error Handling

Provide informative error messages for path-related issues:

```python
try:
    blender_info = detect_blender_info(blender_path)
except Exception as e:
    if "not found" in str(e).lower():
        print("Tip: Make sure Blender is installed and the path is correct")
        print("Windows: Usually in C:\\Program Files\\Blender Foundation\\")
        print("Linux: Try /usr/bin/blender or /opt/blender/")  
        print("macOS: Try /Applications/Blender.app/Contents/MacOS/Blender")
    raise
```

### 4. Documentation

Always document platform-specific behavior:

```python
def get_blender_executable_name():
    """Get platform-specific Blender executable name.
    
    Returns:
        str: Executable name
            - Windows: "blender.exe"
            - Linux/macOS: "blender"
    """
    return "blender.exe" if platform.system() == "Windows" else "blender"
```

## Troubleshooting

### Common Path Issues

1. **Config Not Found**
   ```bash
   # Initialize configuration
   blender-remote-cli init /path/to/blender
   ```

2. **Addon Directory Not Detected**
   ```bash
   # Manual specification during init
   blender-remote-cli init
   # Enter addon path when prompted
   ```

3. **Permission Errors**
   ```bash
   # Check directory permissions
   ls -la ~/.config/blender-remote/  # Linux/macOS
   dir "%APPDATA%\blender-remote\"   # Windows
   ```

4. **Temp Directory Issues**
   ```python
   # Verify temp directory
   import tempfile
   print(f"Temp directory: {tempfile.gettempdir()}")
   ```

### Platform-Specific Debug

Enable verbose logging to see path resolution:

```bash
blender-remote-cli start --log-level DEBUG
```

This will show:
- Configuration file paths
- Blender addon directory detection
- Temporary file creation
- Path normalization steps

## Migration Notes

### From Manual Path Handling to platformdirs

If you're upgrading from older versions that used manual platform detection:

**Old approach:**
```python
if platform.system() == "Windows":
    config_dir = Path(os.environ.get("APPDATA")) / "blender-remote"
else:
    config_dir = Path.home() / ".config" / "blender-remote"
```

**New approach:**
```python
import platformdirs
config_dir = Path(platformdirs.user_config_dir(
    appname="blender-remote", 
    appauthor="blender-remote"
))
```

The new approach:
- ✅ Handles edge cases automatically
- ✅ Follows OS conventions precisely  
- ✅ Supports all three platforms consistently
- ✅ Maintained by the Python community