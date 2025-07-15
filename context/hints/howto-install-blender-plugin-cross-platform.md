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
"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe" --background --python "path\to\install_addon.py" -- "path\to\myaddon.zip"
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
