# How to Find Blender and Its Components on macOS

This guide provides comprehensive methods for locating Blender installations, addon directories, and other important paths on macOS systems.

## Table of Contents
- [Quick Reference](#quick-reference)
- [Finding Blender Executable](#finding-blender-executable)
- [Understanding macOS App Bundle Structure](#understanding-macos-app-bundle-structure)
- [Finding Addon/Plugin Directories](#finding-addonplugin-directories)
- [Using Blender's Python API](#using-blenders-python-api)
- [Programmatic Discovery](#programmatic-discovery)
- [Version Detection](#version-detection)
- [Troubleshooting](#troubleshooting)

## Quick Reference

### Default Locations
```bash
# Blender executable (default installation)
/Applications/Blender.app/Contents/MacOS/Blender

# User addon directory (Blender 4.x)
~/Library/Application Support/Blender/4.4/scripts/addons

# System addon directory (core addons)
/Applications/Blender.app/Contents/Resources/4.4/scripts/addons_core
```

### Essential One-Liners
```bash
# Find Blender using Spotlight
mdfind -name "Blender.app"

# Get addon directory using Blender
/Applications/Blender.app/Contents/MacOS/Blender --background --python-expr "import bpy; print(bpy.utils.user_resource('SCRIPTS') + '/addons')"

# Get Blender version
/Applications/Blender.app/Contents/MacOS/Blender --version
```

## Finding Blender Executable

### Method 1: Check Default Locations
```bash
# Primary location (most common)
ls -la /Applications/Blender.app/Contents/MacOS/Blender

# Alternative location (some installations)
ls -la /Applications/Blender/Blender.app/Contents/MacOS/Blender

# User-specific installation
ls -la ~/Applications/Blender.app/Contents/MacOS/Blender
```

### Method 2: Use Spotlight Search (mdfind)
```bash
# Find all Blender.app installations
mdfind -name "Blender.app"

# Find with more specific criteria
mdfind "kMDItemDisplayName == 'Blender.app' && kMDItemContentType == 'com.apple.application-bundle'"

# Get just the first result
mdfind -name "Blender.app" | head -1
```

### Method 3: Use System Profiler
```bash
# List all applications (grep for Blender)
system_profiler SPApplicationsDataType | grep -A 5 "Blender"
```

### Method 4: Check Running Processes
```bash
# If Blender is running
ps aux | grep -i blender | grep -v grep
```

## Understanding macOS App Bundle Structure

Blender on macOS is packaged as an app bundle. Here's the structure:

```
Blender.app/
├── Contents/
│   ├── MacOS/
│   │   └── Blender              # Main executable
│   ├── Resources/
│   │   ├── 4.4/                 # Version-specific resources
│   │   │   ├── scripts/         # Built-in scripts
│   │   │   │   ├── addons_core/ # Core addons
│   │   │   │   ├── modules/     # Python modules
│   │   │   │   └── startup/     # Startup scripts
│   │   │   ├── python/          # Bundled Python
│   │   │   └── datafiles/       # Icons, fonts, etc.
│   │   └── [icons, cursors...]  # UI resources
│   └── Info.plist               # App metadata
```

### Accessing Bundle Contents via CLI
```bash
# Navigate to executable
cd /Applications/Blender.app/Contents/MacOS/

# List Resources
ls -la /Applications/Blender.app/Contents/Resources/

# Find version-specific directory
ls -la /Applications/Blender.app/Contents/Resources/ | grep -E '^d.*[0-9]\.[0-9]'
```

## Finding Addon/Plugin Directories

### User Addon Directory (Where You Install Custom Addons)
```bash
# General pattern
~/Library/Application Support/Blender/{VERSION}/scripts/addons

# For Blender 4.4
~/Library/Application Support/Blender/4.4/scripts/addons

# Create if it doesn't exist
mkdir -p ~/Library/Application\ Support/Blender/4.4/scripts/addons
```

### System Addon Directories
```bash
# Core addons (bundled with Blender)
/Applications/Blender.app/Contents/Resources/4.4/scripts/addons_core

# Check what's there
ls -la /Applications/Blender.app/Contents/Resources/4.4/scripts/
```

### Extensions Directory (Blender 4.2+)
```bash
# New extensions system location
~/Library/Application Support/Blender/4.4/extensions
```

### Finding All Addon Paths Programmatically
```bash
# Get all addon search paths
/Applications/Blender.app/Contents/MacOS/Blender --background --python-expr \
  "import bpy; print('\n'.join(bpy.utils.script_paths(subdir='addons')))"
```

## Using Blender's Python API

### Get Comprehensive Path Information
```bash
# Create a temporary Python script
cat > /tmp/blender_paths.py << 'EOF'
import bpy
import sys
import os

print("=== BLENDER PATHS ===")
print(f"Blender Version: {bpy.app.version_string}")
print(f"Python Version: {sys.version.split()[0]}")

print("\n=== USER DIRECTORIES ===")
print(f"Scripts: {bpy.utils.user_resource('SCRIPTS')}")
print(f"Config: {bpy.utils.user_resource('CONFIG')}")
print(f"Datafiles: {bpy.utils.user_resource('DATAFILES')}")

try:
    print(f"Extensions: {bpy.utils.user_resource('EXTENSIONS')}")
except:
    print("Extensions: Not available (Blender < 4.2)")

print("\n=== SYSTEM DIRECTORIES ===")
print(f"Scripts: {bpy.utils.system_resource('SCRIPTS')}")
print(f"Datafiles: {bpy.utils.system_resource('DATAFILES')}")

print("\n=== ADDON PATHS ===")
for i, path in enumerate(bpy.utils.script_paths(subdir="addons"), 1):
    print(f"{i}. {path}")

print("\n=== PYTHON PATHS ===")
print(f"Executable: {sys.executable}")
print("Site packages:")
for path in sys.path:
    if "site-packages" in path:
        print(f"  - {path}")
EOF

# Run it
/Applications/Blender.app/Contents/MacOS/Blender --background --python /tmp/blender_paths.py
```

### Quick One-Liners for Specific Information
```bash
# Get user scripts directory
/Applications/Blender.app/Contents/MacOS/Blender --background --python-expr \
  "import bpy; print(bpy.utils.user_resource('SCRIPTS'))"

# Get bundled Python version
/Applications/Blender.app/Contents/MacOS/Blender --background --python-expr \
  "import sys; print(sys.version)"

# Check if specific addon is installed
/Applications/Blender.app/Contents/MacOS/Blender --background --python-expr \
  "import addon_utils; print('bld_remote_mcp' in [a.module for a in addon_utils.modules()])"
```

## Programmatic Discovery

### Python Script for Finding Blender
```python
#!/usr/bin/env python3
"""Find Blender installation on macOS"""

import subprocess
from pathlib import Path

def find_blender_executable():
    """Find Blender executable using multiple methods"""
    
    # Method 1: Check common locations
    common_paths = [
        "/Applications/Blender.app/Contents/MacOS/Blender",
        "/Applications/Blender/Blender.app/Contents/MacOS/Blender",
        Path.home() / "Applications/Blender.app/Contents/MacOS/Blender",
    ]
    
    for path in common_paths:
        if Path(path).exists():
            return str(path)
    
    # Method 2: Use mdfind (Spotlight)
    try:
        result = subprocess.run(
            ["mdfind", "-name", "Blender.app"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            app_path = result.stdout.strip().split('\n')[0]
            exe_path = Path(app_path) / "Contents/MacOS/Blender"
            if exe_path.exists():
                return str(exe_path)
    except:
        pass
    
    return None

# Usage
blender_path = find_blender_executable()
if blender_path:
    print(f"Found Blender: {blender_path}")
else:
    print("Blender not found")
```

### Shell Script for Complete Discovery
```bash
#!/bin/bash
# find_blender_info.sh - Comprehensive Blender discovery script

echo "🔍 Searching for Blender on macOS..."

# Find Blender.app
BLENDER_APP=$(mdfind -name "Blender.app" | head -1)

if [ -z "$BLENDER_APP" ]; then
    echo "❌ Blender.app not found using Spotlight"
    # Check default location
    if [ -d "/Applications/Blender.app" ]; then
        BLENDER_APP="/Applications/Blender.app"
    else
        echo "❌ Blender not found in /Applications"
        exit 1
    fi
fi

echo "✅ Found Blender.app: $BLENDER_APP"

# Get executable path
BLENDER_EXE="$BLENDER_APP/Contents/MacOS/Blender"
echo "📍 Executable: $BLENDER_EXE"

# Get version
VERSION=$("$BLENDER_EXE" --version 2>&1 | grep "Blender" | head -1 | awk '{print $2}')
echo "📌 Version: $VERSION"

# Extract major.minor version
VERSION_SHORT=$(echo $VERSION | cut -d. -f1,2)
echo "📌 Version (short): $VERSION_SHORT"

# User directories
USER_SCRIPTS="$HOME/Library/Application Support/Blender/$VERSION_SHORT/scripts"
USER_ADDONS="$USER_SCRIPTS/addons"
echo "📁 User addons: $USER_ADDONS"

# System directories
SYSTEM_RESOURCES="$BLENDER_APP/Contents/Resources/$VERSION_SHORT"
echo "📁 System resources: $SYSTEM_RESOURCES"

# Check if directories exist
[ -d "$USER_ADDONS" ] && echo "✅ User addons directory exists" || echo "⚠️  User addons directory not found"
[ -d "$SYSTEM_RESOURCES" ] && echo "✅ System resources directory exists" || echo "⚠️  System resources directory not found"
```

## Version Detection

### Get Version Information
```bash
# Basic version
/Applications/Blender.app/Contents/MacOS/Blender --version

# Detailed version info using Python
/Applications/Blender.app/Contents/MacOS/Blender --background --python-expr \
  "import bpy; v=bpy.app; print(f'Version: {v.version_string}\\nBuild: {v.build_date.decode()} {v.build_time.decode()}\\nHash: {v.build_hash.decode()}')"

# Just version number
/Applications/Blender.app/Contents/MacOS/Blender --version | grep "Blender" | awk '{print $2}'
```

### Check App Bundle Version
```bash
# Read from Info.plist
defaults read /Applications/Blender.app/Contents/Info.plist CFBundleShortVersionString

# Using PlistBuddy
/usr/libexec/PlistBuddy -c "Print :CFBundleShortVersionString" /Applications/Blender.app/Contents/Info.plist
```

## Troubleshooting

### Common Issues and Solutions

#### Blender Not Found
```bash
# Rebuild Spotlight index
sudo mdutil -E /Applications

# Check if Blender is in a custom location
find /Applications -name "Blender.app" -type d 2>/dev/null
find ~/Applications -name "Blender.app" -type d 2>/dev/null
```

#### Permission Issues
```bash
# Fix addon directory permissions
chmod -R u+rwX ~/Library/Application\ Support/Blender/

# Create addon directory with proper permissions
mkdir -p ~/Library/Application\ Support/Blender/4.4/scripts/addons
chmod 755 ~/Library/Application\ Support/Blender/4.4/scripts/addons
```

#### Multiple Blender Versions
```bash
# Find all Blender installations
mdfind -name "Blender.app" | while read -r app; do
    exe="$app/Contents/MacOS/Blender"
    if [ -x "$exe" ]; then
        version=$("$exe" --version 2>&1 | grep "Blender" | awk '{print $2}')
        echo "$version: $exe"
    fi
done
```

### Verification Commands
```bash
# Verify Blender executable
file /Applications/Blender.app/Contents/MacOS/Blender

# Check if it's a valid Mach-O executable
otool -h /Applications/Blender.app/Contents/MacOS/Blender

# List dynamic libraries
otool -L /Applications/Blender.app/Contents/MacOS/Blender | head -10
```

## Advanced Tips

### Environment Variables
```bash
# Set BLENDER_USER_SCRIPTS to use custom script directory
export BLENDER_USER_SCRIPTS="$HOME/my-blender-scripts"

# Set BLENDER_SYSTEM_SCRIPTS for testing
export BLENDER_SYSTEM_SCRIPTS="/path/to/test/scripts"
```

### Creating Aliases
```bash
# Add to ~/.zshrc or ~/.bash_profile
alias blender="/Applications/Blender.app/Contents/MacOS/Blender"
alias blender-bg="/Applications/Blender.app/Contents/MacOS/Blender --background"
alias blender-version="/Applications/Blender.app/Contents/MacOS/Blender --version | head -1"
```

### JSON Output for Scripts
```bash
# Get all paths as JSON
/Applications/Blender.app/Contents/MacOS/Blender --background --python-expr "
import bpy, json, sys
paths = {
    'executable': sys.executable,
    'version': bpy.app.version_string,
    'user_scripts': bpy.utils.user_resource('SCRIPTS'),
    'user_config': bpy.utils.user_resource('CONFIG'),
    'addon_paths': bpy.utils.script_paths(subdir='addons')
}
print(json.dumps(paths, indent=2))"
```

This comprehensive guide should help you locate any Blender installation and its components on macOS systems.