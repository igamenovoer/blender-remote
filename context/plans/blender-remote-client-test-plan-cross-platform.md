# Cross-Platform Blender Remote Client Test Plan

## Overview

This is a revised test plan for the blender-remote Python API classes with enhanced cross-platform considerations:
- `BlenderMCPClient` (src/blender_remote/client.py)
- `BlenderSceneManager` (src/blender_remote/scene_manager.py)

## Cross-Platform Testing Focus Areas

### 1. Path Handling (Critical)
- **File Path Separators**: Windows `\` vs Unix `/`
- **Temporary File Locations**: 
  - Windows: `%TEMP%` or `%TMP%`
  - Unix: `/tmp` or `$TMPDIR`
- **User Configuration Paths**:
  - Windows: `%APPDATA%\blender-remote\`
  - macOS: `~/Library/Application Support/blender-remote/`
  - Linux: `~/.config/blender-remote/`
- **Screenshot Output Paths**: Cross-platform path construction
- **GLB Export Paths**: Binary file handling with correct paths

### 2. Process Management (Platform-Specific)
- **PID Handling**: Different process APIs on Windows vs Unix
- **Process Termination**: 
  - Windows: `taskkill /F /IM blender.exe`
  - Unix: `pkill -f blender`
- **Signal Handling**: Windows vs Unix signal differences
- **Process Detection**: Docker environment detection cross-platform

### 3. File Operations (Critical)
- **Text Encoding**: UTF-8 handling across platforms
- **Binary File Handling**: GLB exports with correct binary mode
- **File Permissions**: Unix permissions vs Windows ACLs
- **Path Resolution**: Relative vs absolute paths

### 4. Network Communication (Platform-Agnostic)
- **Socket Operations**: Should work identically
- **Timeout Handling**: Platform-specific socket behavior
- **Connection Management**: Error handling differences

## Cross-Platform Test Environment Setup

### Required Tools
```bash
# Install platformdirs for proper path handling
pixi add platformdirs

# Cross-platform process management
# Windows: tasklist, taskkill
# Unix: ps, pkill

# File operations
# Windows: dir, type, copy
# Unix: ls, cat, cp
```

### Test Data Structure
```
tmp/
├── blender-client-tests/
│   ├── screenshots/           # Platform-specific paths
│   ├── glb-exports/          # Binary file handling
│   ├── temp-files/           # Temporary file cleanup
│   └── logs/                 # Cross-platform log paths
```

## Revised Test Categories

### 0. Cross-Platform Path Handling Tests (New Priority)

#### 0.1 Path Construction and Resolution
- **Test**: `test_cross_platform_paths.py`
- **Coverage**:
  - ✅ Temporary file path creation using `pathlib.Path`
  - ✅ Screenshot path construction with proper separators
  - ✅ GLB export path handling with binary mode
  - ✅ Configuration directory detection using `platformdirs`
  - ✅ Path validation and sanitization
  - ✅ Cross-platform path normalization

#### 0.2 File Operations Cross-Platform
- **Test**: `test_file_operations_cross_platform.py`
- **Coverage**:
  - File creation/deletion with proper permissions
  - Binary file handling (GLB exports)
  - Text file encoding (UTF-8 consistency)
  - Temporary file cleanup
  - Directory creation with `parents=True, exist_ok=True`

### 1. Enhanced BlenderMCPClient Tests (Cross-Platform)

#### 1.1 Connection Management (Platform-Aware)
- **Test**: `test_client_connection_cross_platform.py`
- **Coverage**:
  - Docker detection on Windows/Unix
  - URL parsing with platform-specific hosts
  - Socket timeout behavior differences
  - Connection error handling per platform

#### 1.2 Process Management (Platform-Specific)
- **Test**: `test_client_process_cross_platform.py`
- **Coverage**:
  - PID retrieval using platform-appropriate methods
  - Process termination with correct commands
  - Signal handling differences
  - Process status detection

#### 1.3 Screenshot Functionality (Path-Aware)
- **Test**: `test_client_screenshot_cross_platform.py`
- **Coverage**:
  - Screenshot path construction with `pathlib.Path`
  - Directory creation with proper permissions
  - File format handling (PNG, JPG) with binary mode
  - Path validation and sanitization

### 2. Enhanced BlenderSceneManager Tests (Cross-Platform)

#### 2.1 Asset Export (GLB) - Cross-Platform
- **Test**: `test_scene_manager_export_cross_platform.py`
- **Coverage**:
  - GLB binary file creation with correct paths
  - Temporary file handling using `tempfile` module
  - Path construction using `pathlib.Path`
  - Binary data integrity across platforms
  - File cleanup after export

#### 2.2 File I/O Operations
- **Test**: `test_scene_manager_file_io.py`
- **Coverage**:
  - Text file operations with UTF-8 encoding
  - Binary file operations (GLB, images)
  - Path resolution and validation
  - Error handling for invalid paths

## Cross-Platform Test Implementation Strategy

### Phase 1: Path Handling Foundation
```python
import pathlib
import tempfile
import platformdirs
import os

# Use platformdirs for user directories
def get_test_config_dir():
    return pathlib.Path(platformdirs.user_config_dir("blender-remote-test"))

# Use tempfile for temporary files
def get_temp_file(suffix=".tmp"):
    return tempfile.NamedTemporaryFile(suffix=suffix, delete=False)

# Use pathlib for all path operations
def construct_screenshot_path(filename):
    base_dir = pathlib.Path("tmp/blender-client-tests/screenshots")
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir / filename
```

### Phase 2: Process Management Abstraction
```python
import platform
import subprocess
import signal

def kill_blender_process():
    if platform.system() == "Windows":
        subprocess.run(["taskkill", "/F", "/IM", "blender.exe"], check=False)
    else:
        subprocess.run(["pkill", "-f", "blender"], check=False)

def get_blender_executable():
    if platform.system() == "Windows":
        return "C:\\Program Files\\Blender Foundation\\Blender 4.4\\blender.exe"
    else:
        return "/apps/blender-4.4.3-linux-x64/blender"
```

### Phase 3: File Operations with Error Handling
```python
import pathlib
import os

def safe_file_write(path, content, mode="w", encoding="utf-8"):
    """Write file with proper error handling and encoding."""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(path, mode, encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error writing file {path}: {e}")
        return False

def safe_binary_write(path, data):
    """Write binary file with proper error handling."""
    return safe_file_write(path, data, mode="wb", encoding=None)
```

## Cross-Platform Test Execution

### Environment Setup
```bash
# Windows
set BLENDER_REMOTE_TEST_PLATFORM=windows
set BLENDER_EXECUTABLE=C:\Program Files\Blender Foundation\Blender 4.4\blender.exe

# Unix (Linux/macOS)
export BLENDER_REMOTE_TEST_PLATFORM=unix
export BLENDER_EXECUTABLE=/apps/blender-4.4.3-linux-x64/blender
```

### Test Commands
```bash
# Run cross-platform tests
pixi run python context/tests/test_cross_platform_paths.py
pixi run python context/tests/test_client_connection_cross_platform.py
pixi run python context/tests/test_scene_manager_export_cross_platform.py

# Platform-specific tests
pixi run python context/tests/test_client_process_cross_platform.py
```

## Cross-Platform Success Criteria

### Path Handling Requirements
- [ ] All file operations use `pathlib.Path`
- [ ] Temporary files use `tempfile` module
- [ ] Configuration paths use `platformdirs`
- [ ] No hardcoded path separators (`/` or `\`)
- [ ] Proper binary vs text file handling

### Process Management Requirements
- [ ] Process operations work on Windows and Unix
- [ ] PID handling is platform-appropriate
- [ ] Process termination uses correct commands
- [ ] Error handling for platform-specific failures

### File Operations Requirements
- [ ] UTF-8 encoding for text files
- [ ] Binary mode for GLB/image files
- [ ] Proper file permissions handling
- [ ] Cleanup works on all platforms

## Risk Mitigation

### High-Risk Areas
1. **Windows Path Handling**: Backslash vs forward slash
2. **Process Management**: Different APIs on Windows vs Unix
3. **File Permissions**: Unix permissions vs Windows ACLs
4. **Temporary Files**: Different temp directory locations

### Mitigation Strategies
1. **Use Standard Libraries**: `pathlib`, `tempfile`, `platformdirs`
2. **Platform Detection**: Use `platform.system()` for conditional logic
3. **Error Handling**: Comprehensive exception handling per platform
4. **Testing**: Run tests on multiple platforms before deployment

## Implementation Notes

- Always use `pathlib.Path` for path operations
- Use `tempfile` module for temporary files
- Use `platformdirs` for user configuration paths
- Test on Windows, Linux, and macOS if possible
- Handle encoding explicitly (UTF-8 for text, binary for images/GLB)
- Use `subprocess` with proper error handling for process management