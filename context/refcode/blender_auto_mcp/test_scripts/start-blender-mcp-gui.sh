#!/bin/bash
# Shell script to start Blender with Auto MCP plugin in GUI mode
# This script configures the environment and starts Blender normally with GUI
# Usage: ./start-blender-mcp-gui.sh [port]
# Default port: 9876

# Parse command line arguments
PORT=${1:-9876}

# Set environment variables for Auto MCP configuration
export BLENDER_AUTO_MCP_SERVICE_PORT="$PORT"
export BLENDER_AUTO_MCP_START_NOW="1"

# Display configuration
echo -e "\033[32mStarting Blender with Auto MCP plugin (GUI mode)\033[0m"
echo -e "\033[36mPort: $BLENDER_AUTO_MCP_SERVICE_PORT\033[0m"
echo -e "\033[36mAuto-start: $BLENDER_AUTO_MCP_START_NOW\033[0m"

# Find Blender executable
if [ -n "$BLENDER_EXEC_PATH" ] && [ -x "$BLENDER_EXEC_PATH" ]; then
    blender_exe="$BLENDER_EXEC_PATH"
    echo -e "\033[32mUsing Blender from BLENDER_EXEC_PATH: $blender_exe\033[0m"
else
    # Fall back to assuming blender is in PATH
    blender_exe="blender"
    echo -e "\033[33mBLENDER_EXEC_PATH not set or invalid, using 'blender' from PATH\033[0m"
fi

echo -e "\033[32mFound Blender at: $blender_exe\033[0m"
echo ""
echo -e "\033[33mStarting Blender...\033[0m"
echo -e "\033[36mThe Auto MCP server will start automatically on port $BLENDER_AUTO_MCP_SERVICE_PORT\033[0m"
echo -e "\033[36mCheck the Blender console for startup messages\033[0m"
echo ""

# Start Blender with GUI
if ! "$blender_exe"; then
    echo -e "\033[31mError starting Blender\033[0m"
    exit 1
fi

echo -e "\033[32mBlender has been closed.\033[0m"