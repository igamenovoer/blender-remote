# How to Install Blender Add-ons from the Command Line (Cross-Platform)

This guide provides a reliable, cross-platform method for installing a Blender 4.x add-on from a `.zip` file using the command line. This is particularly useful for automating your development and deployment workflows.

## The Core Concept

The process involves running Blender in background mode (`--background`) and executing a Python script (`--python`). This script uses Blender's `bpy` module to programmatically install and enable the add-on. The main challenge is ensuring the script can correctly identify the add-on's module name after installation, which is required to enable it.

---

## The Installation Script

Here is a robust Python script that handles the installation. Save this as `install_addon.py` in your project's scripts directory.

**`install_addon.py`**
```python
import bpy
import sys
import os
import zipfile
import traceback

def get_addon_module_name(zip_path: str) -> str:
    """
    Intelligently determines the addon's module name from its zip file.
    
    An addon's module name is the name of the folder containing its __init__.py file.
    This may not always match the .zip file's name.

    Parameters
    ----------
    zip_path : str
        Path to the addon's .zip file.

    Returns
    -------
    str
        The determined module name of the addon.
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            # Find all potential module names (directories with an __init__.py)
            possible_names = {member.split('/')[0] for member in z.namelist() if '__init__.py' in member}
            
            if not possible_names:
                raise RuntimeError("No valid module found in the zip file (missing __init__.py).")
            
            # If there's only one, that's our module.
            if len(possible_names) == 1:
                return list(possible_names)[0]

            # If multiple, try to find one that matches the zip file name.
            zip_basename = os.path.basename(zip_path).replace('.zip', '')
            if zip_basename in possible_names:
                return zip_basename
            
            # As a last resort, return the first one found, with a warning.
            print(f"Warning: Multiple potential modules found: {possible_names}. Using '{list(possible_names)[0]}'.")
            return list(possible_names)[0]

    except Exception as e:
        print(f"Error reading zip file to determine module name: {e}")
        # Fallback to the zip file name as a guess.
        fallback_name = os.path.basename(zip_path).replace('.zip', '')
        print(f"Falling back to module name: {fallback_name}")
        return fallback_name


def install_and_enable_addon(addon_path: str):
    """
    Installs and enables a Blender addon from a zip file.

    Parameters
    ----------
    addon_path : str
        The absolute path to the addon .zip file.
    """
    if not os.path.exists(addon_path):
        print(f"Error: Addon path does not exist: {addon_path}")
        sys.exit(1)

    try:
        print(f"Installing addon from: {addon_path}")
        bpy.ops.preferences.addon_install(filepath=addon_path, overwrite=True)
        
        module_name = get_addon_module_name(addon_path)
        
        print(f"Enabling addon module: '{module_name}'")
        bpy.ops.preferences.addon_enable(module=module_name)
        
        print(f"Successfully installed and enabled addon: {module_name}")

    except Exception:
        print(f"An error occurred during addon installation for '{addon_path}'.")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    # Blender's python interpreter gets command line args after '--'
    argv = sys.argv
    try:
        # Get the first argument after '--'
        addon_zip_path_arg = argv[argv.index("--") + 1]
    except (ValueError, IndexError):
        print("Error: Missing addon path argument.")
        print("Usage: blender --background --python install_addon.py -- /path/to/myaddon.zip")
        sys.exit(1)

    # Use an absolute path to avoid issues
    absolute_addon_path = os.path.abspath(addon_zip_path_arg)
    install_and_enable_addon(absolute_addon_path)

    # Exit successfully
    sys.exit(0)
```

---

## How to Run the Script

Open your terminal or command prompt and run one of the following commands, depending on your operating system.

**Important:**
- Replace `path/to/install_addon.py` with the actual path to the script you saved.
- Replace `path/to/myaddon.zip` with the actual path to your add-on's zip file.
- The path to the zip file **must be the last argument**, following the `--` separator.

### Windows

You may need to use the full path to `blender.exe`.

```cmd
"C:\Program Files\Blender Foundation\Blender 4.4\blender.exe" --background --python "path\to\install_addon.py" -- "path\to\myaddon.zip"
```

### macOS

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python path/to/install_addon.py -- /path/to/myaddon.zip
```

### Linux

```sh
blender --background --python path/to/install_addon.py -- /path/to/myaddon.zip
```

After running the command, the script will print its progress to the console. If successful, the add-on will be installed and enabled in Blender, ready for use. If it fails, the script will print an error message and exit.

---

## Getting the Plugin Directory Programmatically

Before installing addons, you might want to know where they will be installed. Here are several ways to get the plugin directory using Blender's command line:

### Quick One-liner

```bash
# Get the main user addon directory
blender --background --python-expr "import bpy; print(bpy.utils.user_resource('SCRIPTS', 'addons'))"

# Get all addon paths
blender --background --python-expr "import bpy; print('\\n'.join(bpy.utils.script_paths(subdir='addons')))"

# For Blender 4.2+: Get the extensions directory
blender --background --python-expr "import bpy; print(bpy.utils.user_resource('EXTENSIONS'))"

# Get Blender version information
blender --background --python-expr "import bpy; print(bpy.app.version_string)"

# Get detailed version info (version tuple, build date, etc.)
blender --background --python-expr "import bpy; print(f'Version: {bpy.app.version_string}, Build: {bpy.app.build_date.decode()}')"
```

### Using a Simple Script

Create `get_plugin_dir.py`:

```python
import bpy
import sys

def main():
    # Show Blender version first
    print(f"Blender Version: {bpy.app.version_string}")
    print(f"Build Date: {bpy.app.build_date.decode('utf-8')}")
    print("-" * 40)
    
    # Get the primary addon directory
    addon_dir = bpy.utils.user_resource('SCRIPTS', 'addons')
    print(f"Primary addon directory: {addon_dir}")
    
    # Get all addon search paths
    all_paths = bpy.utils.script_paths(subdir="addons")
    print("All addon search paths:")
    for path in all_paths:
        print(f"  {path}")
    
    # For Blender 4.2+: Extensions directory
    try:
        ext_dir = bpy.utils.user_resource('EXTENSIONS')
        print(f"Extensions directory: {ext_dir}")
    except:
        print("Extensions directory: Not available")

if __name__ == "__main__":
    main()
    sys.exit(0)
```

Then run:
```bash
blender --background --python get_plugin_dir.py
```

### Getting Blender Version Information

You can also retrieve detailed Blender version information programmatically:

#### Quick Version Check

```bash
# Get just the version string (e.g., "4.2.0")
blender --background --python-expr "import bpy; print(bpy.app.version_string)"

# Get version tuple (major, minor, patch)
blender --background --python-expr "import bpy; print(bpy.app.version)"

# Get build information
blender --background --python-expr "import bpy; print(bpy.app.build_date.decode())"
```

#### Comprehensive Version Script

Create `get_blender_info.py`:

```python
import bpy
import sys
import platform

def main():
    print(f"Blender Version: {bpy.app.version_string}")
    print(f"Version Tuple: {bpy.app.version}")
    print(f"Build Date: {bpy.app.build_date.decode('utf-8')}")
    print(f"Build Time: {bpy.app.build_time.decode('utf-8')}")
    print(f"Build Commit: {bpy.app.build_commit_date.decode('utf-8')}")
    print(f"Build Hash: {bpy.app.build_hash.decode('utf-8')}")
    print(f"Build Branch: {bpy.app.build_branch.decode('utf-8')}")
    print(f"Build Platform: {bpy.app.build_platform.decode('utf-8')}")
    print(f"Build Type: {bpy.app.build_type.decode('utf-8')}")
    print(f"Python Version: {sys.version}")
    print(f"OS: {platform.system()} {platform.release()}")

if __name__ == "__main__":
    main()
    sys.exit(0)
```

Then run:
```bash
blender --background --python get_blender_info.py
```

This will output detailed information like:
```
Blender Version: 4.2.0
Version Tuple: (4, 2, 0)
Build Date: 2024-07-16
Build Time: 16:08:17
Build Commit: 2024-07-15 18:32
Build Hash: a51f293548ad
Build Branch: makepkg
Build Platform: Linux
Build Type: Release
Python Version: 3.11.9 (main, Apr  6 2024, 17:59:24) [GCC 13.2.1 20230801]
OS: Linux 6.9.9-arch1-1
```

### Enhanced Installation Script with Directory Discovery

Here's an enhanced version of the installation script that first discovers and reports the addon directory:

```python
import bpy
import sys
import os
import zipfile
import traceback

def get_addon_directories():
    """Get information about addon directories."""
    info = {
        'user_addons': bpy.utils.user_resource('SCRIPTS', 'addons'),
        'all_paths': bpy.utils.script_paths(subdir="addons")
    }
    
    # Try to get extensions directory (Blender 4.2+)
    try:
        info['extensions'] = bpy.utils.user_resource('EXTENSIONS')
    except:
        info['extensions'] = None
    
    return info

def get_addon_module_name(zip_path: str) -> str:
    """
    Intelligently determines the addon's module name from its zip file.
    
    An addon's module name is the name of the folder containing its __init__.py file.
    This may not always match the .zip file's name.

    Parameters
    ----------
    zip_path : str
        Path to the addon's .zip file.

    Returns
    -------
    str
        The determined module name of the addon.
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            # Find all potential module names (directories with an __init__.py)
            possible_names = {member.split('/')[0] for member in z.namelist() if '__init__.py' in member}
            
            if not possible_names:
                raise RuntimeError("No valid module found in the zip file (missing __init__.py).")
            
            # If there's only one, that's our module.
            if len(possible_names) == 1:
                return list(possible_names)[0]

            # If multiple, try to find one that matches the zip file name.
            zip_basename = os.path.basename(zip_path).replace('.zip', '')
            if zip_basename in possible_names:
                return zip_basename
            
            # As a last resort, return the first one found, with a warning.
            print(f"Warning: Multiple potential modules found: {possible_names}. Using '{list(possible_names)[0]}'.")
            return list(possible_names)[0]

    except Exception as e:
        print(f"Error reading zip file to determine module name: {e}")
        # Fallback to the zip file name as a guess.
        fallback_name = os.path.basename(zip_path).replace('.zip', '')
        print(f"Falling back to module name: {fallback_name}")
        return fallback_name


def install_and_enable_addon(addon_path: str):
    """
    Installs and enables a Blender addon from a zip file.

    Parameters
    ----------
    addon_path : str
        The absolute path to the addon .zip file.
    """
    if not os.path.exists(addon_path):
        print(f"Error: Addon path does not exist: {addon_path}")
        sys.exit(1)

    try:
        print(f"Installing addon from: {addon_path}")
        bpy.ops.preferences.addon_install(filepath=addon_path, overwrite=True)
        
        module_name = get_addon_module_name(addon_path)
        
        print(f"Enabling addon module: '{module_name}'")
        bpy.ops.preferences.addon_enable(module=module_name)
        
        print(f"Successfully installed and enabled addon: {module_name}")

    except Exception:
        print(f"An error occurred during addon installation for '{addon_path}'.")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    # Blender's python interpreter gets command line args after '--'
    argv = sys.argv
    try:
        # Get the first argument after '--'
        addon_zip_path_arg = argv[argv.index("--") + 1]
    except (ValueError, IndexError):
        print("Error: Missing addon path argument.")
        print("Usage: blender --background --python install_addon.py -- /path/to/myaddon.zip")
        sys.exit(1)

    # Use an absolute path to avoid issues
    absolute_addon_path = os.path.abspath(addon_zip_path_arg)
    install_and_enable_addon(absolute_addon_path)

    # Exit successfully
    sys.exit(0)
```

---

## How to Run the Enhanced Script

To run the enhanced script that discovers the addon directory before installation, follow the same steps as before but with the updated script.

### Windows

```cmd
"C:\Program Files\Blender Foundation\Blender 4.4\blender.exe" --background --python "path\to\install_addon.py" -- "path\to\myaddon.zip"
```

### macOS

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python path/to/install_addon.py -- /path/to/myaddon.zip
```

### Linux

```sh
blender --background --python path/to/install_addon.py -- /path/to/myaddon.zip
```

The script will now also print the addon directories used by Blender, providing helpful context during installation.
