#!/bin/bash
# Shell script to start Blender with Auto MCP plugin in headless mode
# This script configures the environment and starts Blender in background mode
# Usage: ./start-blender-mcp-headless.sh [port]
# Default port: 9876

# Parse command line arguments
PORT=${1:-9876}

# Set environment variables for Auto MCP configuration
export BLENDER_AUTO_MCP_SERVICE_PORT="$PORT"
export BLENDER_AUTO_MCP_START_NOW="1"

# Display configuration
echo -e "\033[32mStarting Blender with Auto MCP plugin (Headless mode)\033[0m"
echo -e "\033[36mPort: $BLENDER_AUTO_MCP_SERVICE_PORT\033[0m"
echo -e "\033[36mAuto-start: $BLENDER_AUTO_MCP_START_NOW\033[0m"

# Function to handle cleanup on script exit
cleanup() {
    echo ""
    echo -e "\033[33mReceived interrupt signal. Stopping Blender...\033[0m"
    if [ ! -z "$blender_pid" ] && kill -0 "$blender_pid" 2>/dev/null; then
        kill "$blender_pid"
        wait "$blender_pid" 2>/dev/null
    fi
    echo -e "\033[32mBlender headless session has been stopped.\033[0m"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

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
echo -e "\033[33mStarting Blender in headless mode...\033[0m"
echo -e "\033[36mThe Auto MCP server will start automatically on port $BLENDER_AUTO_MCP_SERVICE_PORT\033[0m"
echo -e "\033[36mBlender will run in the background and keep the MCP server alive\033[0m"
echo ""
echo -e "\033[33mTo stop the server, use Ctrl+C or send a 'server_shutdown' MCP command\033[0m"
echo ""

# Start Blender in headless mode
echo -e "\033[32mBlender is now running in headless mode...\033[0m"
echo -e "\033[36mMCP server should be available at localhost:$BLENDER_AUTO_MCP_SERVICE_PORT\033[0m"
echo ""
echo -e "\033[33mPress Ctrl+C to stop the server\033[0m"

# Start Blender process in background and capture PID
"$blender_exe" --background &
blender_pid=$!

echo -e "\033[32mBlender process started (PID: $blender_pid)\033[0m"

# Wait for the Blender process to complete
if ! wait "$blender_pid"; then
    echo -e "\033[31mBlender process ended unexpectedly\033[0m"
    exit 1
fi

echo -e "\033[32mBlender headless session has been stopped.\033[0m"