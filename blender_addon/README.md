# Blender Add-ons

This directory contains Blender add-ons (plugins) that are installed directly into Blender.

## Purpose

These add-ons create non-stop services inside Blender that:
- Listen for incoming commands from the remote control library
- Execute commands using Blender's Python API
- Send responses back to the remote controller
- Maintain persistent connections for real-time control

## Structure

Each add-on should be in its own subdirectory with:
- `__init__.py` - Add-on metadata and registration
- Service implementation for receiving and executing commands
- Blender operator definitions for various operations

## Installation

### Creating the Add-on Zip File

The `bld_remote_mcp.zip` file is not included in the repository and must be created from the source:

```bash
# From the blender_addon/ directory
cd blender_addon/
zip -r bld_remote_mcp.zip bld_remote_mcp/
```

### Installing in Blender

#### Method 1: GUI Installation (Recommended)

1. **Open Blender**
2. Go to `Edit > Preferences` from the top menu bar
3. In the Preferences window, select the `Add-ons` tab
4. Click the `Install...` button (this opens Blender's file browser)
5. Navigate to your `blender_addon/` directory and select the `bld_remote_mcp.zip` file you created
6. Click `Install Add-on`
7. **Important**: Search for "BLD Remote MCP" in the add-on list and **enable it by ticking the checkbox**

#### Method 2: Manual Directory Copy

Alternatively, copy the `bld_remote_mcp/` directory directly to your Blender addons folder:
```bash
mkdir -p ~/.config/blender/4.4/scripts/addons/
cp -r bld_remote_mcp/ ~/.config/blender/4.4/scripts/addons/
# Then restart Blender and enable the addon in Preferences > Add-ons
```

### Verifying Installation

**Critical**: The BLD Remote MCP add-on has **no visible GUI panel**. You must verify its installation through Blender's system console.

#### How to Access System Console:

- **Windows**: Go to `Window > Toggle System Console` in Blender's menu
- **macOS/Linux**: Start Blender from a terminal window - log messages will appear in that terminal

#### Expected Log Messages:

When you enable the add-on, you should see these registration messages in the console:

```
=== BLD REMOTE MCP ADDON REGISTRATION STARTING ===
🚀 DEV-TEST-UPDATE: BLD Remote MCP v1.0.2 Loading!
...
✅ BLD Remote MCP addon registered successfully
=== BLD REMOTE MCP ADDON REGISTRATION COMPLETED ===
```

If the add-on is configured to auto-start its server (via environment variables), you'll also see:

```
✅ Starting server on port 6688
✅ BLD Remote server STARTED successfully on port 6688
Server is now listening for connections on 127.0.0.1:6688
```

#### Troubleshooting Installation:

- **No registration messages**: The add-on failed to load. Check for error messages in the console.
- **Add-on not found in preferences**: Ensure the zip file was created correctly and contains the `bld_remote_mcp/` directory.
- **Server won't start**: Check environment variables and port availability.

If you see the registration messages, the add-on is installed and ready to use!

## Development

When developing add-ons:
- Follow Blender's add-on conventions and best practices
- Ensure compatibility with Blender's Python API version
- Test thoroughly within Blender's environment
- Handle errors gracefully to avoid crashing Blender