# install_addon.py
import bpy
import sys
import os

def get_addon_name_from_zip(zip_path):
    """
    A simple way to guess the addon module name from its zip file name.
    e.g., 'bld_remote_mcp.zip' -> 'bld_remote_mcp'
    """
    return os.path.basename(zip_path).replace(".zip", "")

def install_and_enable_addon(addon_zip_path):
    """
    Installs and enables a Blender add-on from a .zip file.
    """
    if not os.path.exists(addon_zip_path):
        print(f"Error: Add-on file not found at '{addon_zip_path}'")
        sys.exit(1)

    addon_module_name = get_addon_name_from_zip(addon_zip_path)
    try:
        print(f"Installing addon from: {addon_zip_path}")
        bpy.ops.preferences.addon_install(filepath=addon_zip_path, overwrite=True)
        
        # Determine the module name from the zip file name
        
        print(f"Enabling addon: {addon_module_name}")
        bpy.ops.preferences.addon_enable(module=addon_module_name)
        
        print(f"Add-on '{addon_module_name}' installed and enabled successfully.")
        
        # Save preferences so the add-on remains enabled
        bpy.ops.wm.save_userpref()
        print("User preferences saved.")

    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        # Attempt to provide more context for common errors
        if "module" in str(e) and "not found" in str(e):
            print("This might mean the addon's module name inside the script differs from the zip file name.", file=sys.stderr)
            print(f"Guessed module name was: '{addon_module_name}'. Please check the add-on's `__init__.py` for the correct name.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    # Blender's Python interpreter passes command-line arguments after '--'
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    if not argv:
        print("Usage: blender --background --python install_addon.py -- <path_to_addon.zip>", file=sys.stderr)
        sys.exit(1)
        
    addon_path = argv[0]
    install_and_enable_addon(addon_path)

    # Exit blender
    bpy.ops.wm.quit_blender()
