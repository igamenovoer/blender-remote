# How to Install Blender Add-ons

This guide covers how to install Blender add-ons, offering both a general approach for any add-on and specific instructions for the `bld-remote-mcp` add-on included in this project.

---

## Part 1: General Guide to Installing Blender Add-ons

This section explains the standard methods for installing any Blender add-on from a `.zip` file.

### Method 1: Using the Graphical User Interface (GUI)

This is the most common and straightforward method for installing add-ons.

1.  **Open Blender.**
2.  Go to `Edit > Preferences` from the top menu bar.
3.  In the Preferences window, select the `Add-ons` tab.
4.  Click the `Install...` button. This will open Blender's file browser.
5.  Navigate to and select the `.zip` file for the add-on you want to install.
6.  Click `Install Add-on`.
7.  After installation, the add-on will appear in the list. **Enable it by ticking the checkbox** next to its name.
8.  Your preferences may be configured to save automatically. If not, you can save them manually to ensure the add-on remains enabled for future sessions. In the bottom-left of the Preferences window, click the hamburger menu and select `Save Preferences`.

### Method 2: Using the Command Line Interface (CLI)

For automated setups or users who prefer the terminal, you can install and enable add-ons using a single command, without needing to create any extra script files. This method works for Blender 4.0 and newer.

**Prerequisites:**
*   You must know the path to the add-on's `.zip` file.
*   You must know the add-on's **module name**. This is the name Blender uses to identify the add-on internally. It's typically the name of the main `.py` file or the folder containing the `__init__.py` file. For a zipped add-on, the module name is often the same as the zip file's name (e.g., `my_addon.zip` -> `my_addon`).

For convenience, it's recommended to set the `BLENDER_EXEC_PATH` environment variable to the absolute path of your Blender executable.

#### Command Template

The command uses Blender's `--python-expr` argument to run Python code directly.

**Linux / macOS**
```bash
ADDON_ZIP_PATH="/path/to/your/addon.zip"
ADDON_MODULE_NAME="addon_module_name"

"$BLENDER_EXEC_PATH" --background --python-expr "import bpy; bpy.ops.preferences.addon_install(filepath='$ADDON_ZIP_PATH', overwrite=True); bpy.ops.preferences.addon_enable(module='$ADDON_MODULE_NAME'); bpy.ops.wm.save_userpref()"
```

**Windows (PowerShell)**
```powershell
$env:ADDON_ZIP_PATH = "C:\path\to\your\addon.zip"
$env:ADDON_MODULE_NAME = "addon_module_name"

& $env:BLENDER_EXEC_PATH --background --python-expr "import bpy; bpy.ops.preferences.addon_install(filepath='$env:ADDON_ZIP_PATH', overwrite=True); bpy.ops.preferences.addon_enable(module='$env:ADDON_MODULE_NAME'); bpy.ops.wm.save_userpref()"
```

---

## Part 2: Installing the `bld-remote-mcp` Add-on

Now, let's apply the knowledge from Part 1 to install the add-on from this project.

### Step 1: Prepare the Add-on File

First, you need to create the `bld_remote_mcp.zip` file from the source directory.

```bash
# Navigate to the blender_addon directory from the project root
cd blender_addon

# Create the zip file containing the addon
zip -r bld_remote_mcp.zip bld_remote_mcp/
```
This will create `bld_remote_mcp.zip` inside the `blender_addon` directory. The **module name** for this add-on is `bld_remote_mcp`.

### Step 2: Install the Add-on

#### Using the GUI

Follow the steps in **Part 1, Method 1**. When prompted to select a file, choose the `bld_remote_mcp.zip` file you just created. After installing, search for "BLD Remote MCP" and enable it.

#### Using the CLI

Follow the steps in **Part 1, Method 2**. Use the following paths and names.

**Linux / macOS**
```bash
# Run from the project's root directory
ADDON_ZIP_PATH="blender_addon/bld_remote_mcp.zip"
ADDON_MODULE_NAME="bld_remote_mcp"

"$BLENDER_EXEC_PATH" --background --python-expr "import bpy; bpy.ops.preferences.addon_install(filepath='$ADDON_ZIP_PATH', overwrite=True); bpy.ops.preferences.addon_enable(module='$ADDON_MODULE_NAME'); bpy.ops.wm.save_userpref()"
```

**Windows (PowerShell)**
```powershell
# Run from the project's root directory
$env:ADDON_ZIP_PATH = "blender_addon\bld_remote_mcp.zip"
$env:ADDON_MODULE_NAME = "bld_remote_mcp"

& $env:BLENDER_EXEC_PATH --background --python-expr "import bpy; bpy.ops.preferences.addon_install(filepath='$env:ADDON_ZIP_PATH', overwrite=True); bpy.ops.preferences.addon_enable(module='$env:ADDON_MODULE_NAME'); bpy.ops.wm.save_userpref()"
```

### Step 3: Verify the Installation

This add-on does not have a visible GUI panel. You must verify its installation by checking Blender's system console for specific log messages.

#### How to Open the System Console:

*   **Windows:** Go to `Window > Toggle System Console`.
*   **macOS/Linux:** You need to start Blender from a terminal. The log messages will be printed directly to that terminal window.

#### Key Log Messages to Look For:

When you enable the add-on, you should see the following messages printed in the console. This confirms the add-on has been registered correctly.

```
=== BLD REMOTE MCP ADDON REGISTRATION STARTING ===
🚀 DEV-TEST-UPDATE: BLD Remote MCP v1.0.2 Loading!
...
✅ BLD Remote MCP addon registered successfully
=== BLD REMOTE MCP ADDON REGISTRATION COMPLETED ===
```

If the add-on is configured to start its server automatically, you will also see these lines:

```
✅ Starting server on port 6688
✅ BLD Remote server STARTED successfully on port 6688
Server is now listening for connections on 127.0.0.1:6688
```

If you see these messages, the add-on is installed and running correctly. If not, review the console for any error messages to help diagnose the issue.
