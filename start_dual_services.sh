#!/bin/bash

echo "Starting Blender with dual MCP services..."

# Set environment variables
export BLD_REMOTE_MCP_PORT=6688
export BLD_REMOTE_MCP_START_NOW=1
export BLENDER_AUTO_MCP_SERVICE_PORT=9876
export BLENDER_AUTO_MCP_START_NOW=1

echo "Environment variables set:"
echo "BLD_REMOTE_MCP_PORT=$BLD_REMOTE_MCP_PORT"
echo "BLD_REMOTE_MCP_START_NOW=$BLD_REMOTE_MCP_START_NOW"
echo "BLENDER_AUTO_MCP_SERVICE_PORT=$BLENDER_AUTO_MCP_SERVICE_PORT"
echo "BLENDER_AUTO_MCP_START_NOW=$BLENDER_AUTO_MCP_START_NOW"

echo "Starting Blender..."
/home/igamenovoer/apps/blender-4.4.3-linux-x64/blender > /tmp/blender_dual_output.log 2>&1 &

echo "Blender PID: $!"
echo "Waiting 15 seconds for services to start..."
sleep 15

echo "Checking service ports..."
netstat -tlnp | grep -E "(6688|9876)" || echo "No services detected on expected ports"

echo "Done."