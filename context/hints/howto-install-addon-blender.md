# How to Install and Verify the Blender Add-on

This guide explains how to install the `bld_remote_mcp` add-on using Blender's GUI and verify its successful installation by checking the system console for log messages.

## 1. Preparing the Add-on

First, you need to create a `.zip` file from the add-on's source directory.

```bash
# Navigate to the blender_addon directory from the project root
cd blender_addon

# Create the zip file containing the addon
zip -r bld_remote_mcp.zip bld_remote_mcp/
```

This will create `bld_remote_mcp.zip` inside the `blender_addon` directory, which you will use for installation.

## 2. Installing the Add-on via Blender GUI

1.  **Open Blender.**
2.  Go to `Edit > Preferences` from the top menu bar.
3.  In the Preferences window, select the `Add-ons` tab.
4.  Click the `Install...` button. This will open Blender's file browser.
5.  Navigate to the `blender_addon` directory within this project and select the `bld_remote_mcp.zip` file you created.
6.  Click `Install Add-on`.
7.  After installation, search for "BLD Remote MCP" in the add-on list and **enable it by ticking the checkbox** next to its name.

## 3. Verifying the Installation

This add-on does not have a visible GUI panel. You must verify its installation by checking Blender's system console for specific log messages.

### How to Open the System Console:

*   **Windows:** Go to `Window > Toggle System Console`.
*   **macOS/Linux:** You need to start Blender from a terminal. The log messages will be printed directly to that terminal window.

### Key Log Messages to Look For:

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
