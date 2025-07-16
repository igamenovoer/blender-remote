# How to Install and Enable a Blender Addon via Python Script

This guide explains how to install and enable a Blender addon from a `.zip` file using a Python script. This script can be executed from the command line with `blender --background`.

## Key Blender Python Commands

The core of the process involves three `bpy.ops` commands:

1.  `bpy.ops.preferences.addon_install(filepath, overwrite=True)`: This command installs an addon from the given `filepath`.
    *   `filepath`: The absolute path to the addon's `.zip` or `.py` file.
    *   `overwrite=True`: This is crucial for ensuring that if the addon is already installed, it will be replaced with the new version.
2.  `bpy.ops.preferences.addon_enable(module)`: This command enables the addon.
    *   `module`: The module name of the addon (usually the name of the main `.py` file or the folder name within the zip).
3.  `bpy.ops.wm.save_userpref()`: This command saves the user preferences, making the installation and enabling persistent across Blender sessions. Without this, the changes will be lost when Blender closes.

## Example Python Script

Here is a Python script that demonstrates how to install and enable an addon.

```python
import bpy
import sys
import os

def install_and_enable_addon(addon_zip_path, addon_module_name):
    """
    Installs and enables a Blender addon.

    :param addon_zip_path: Absolute path to the addon's .zip file.
    :param addon_module_name: The module name of the addon to enable.
    """
    if not os.path.exists(addon_zip_path):
        print(f"Error: Addon file not found at '{addon_zip_path}'")
        sys.exit(1)

    try:
        print(f"Installing addon from: {addon_zip_path}")
        bpy.ops.preferences.addon_install(filepath=addon_zip_path, overwrite=True)
        
        print(f"Enabling addon: {addon_module_name}")
        bpy.ops.preferences.addon_enable(module=addon_module_name)
        
        print("Saving user preferences...")
        bpy.ops.wm.save_userpref()
        
        print(f"Addon '{addon_module_name}' installed and enabled successfully.")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        # Attempt to get more details from the exception if possible
        if hasattr(e, 'args') and e.args:
            print("Details:", e.args[0])
        sys.exit(1)

if __name__ == "__main__":
    # It's recommended to pass the addon path and module name as arguments
    # to the script, but for simplicity, we hardcode them here.
    
    # On Windows, use raw string or double backslashes for paths
    # addon_path = r"C:\\path\\to\\your\\addon.zip" 
    
    # On macOS/Linux
    # addon_path = "/path/to/your/addon.zip"
    
    # Example:
    addon_path = "/path/to/your/addon.zip" # REPLACE WITH ACTUAL PATH
    addon_name = "your_addon_module_name" # REPLACE WITH ACTUAL MODULE NAME

    # You can get these from command line arguments for more flexibility
    if len(sys.argv) > 4:
        script_args_start = sys.argv.index("--") + 1 if "--" in sys.argv else 4
        custom_args = sys.argv[script_args_start:]
        if len(custom_args) >= 2:
            addon_path = custom_args[0]
            addon_name = custom_args[1]

    install_and_enable_addon(addon_path, addon_name)

```

## How to Execute from Command Line

You can run this script using Blender in background mode.

```bash
blender --background --python /path/to/your/install_script.py
```

To pass the addon path and name from the command line:
```bash
blender --background --python /path/to/your/install_script.py -- /path/to/addon.zip addon_module_name
```
The `--` is important to separate Blender's arguments from the script's arguments.

This approach is used in the `blender-remote` CLI to install the `bld_remote_mcp` addon.
