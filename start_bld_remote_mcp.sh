#!/bin/bash

# Start Blender with BLD_Remote_MCP auto-started on port 9876
# This script configures and launches Blender with the BLD Remote MCP service

set -e  # Exit on any error

# Configuration
BLENDER_PATH="/apps/blender-4.4.3-linux-x64/blender"
BLD_REMOTE_PORT=9876

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "${BLUE}$1${NC}"
}

# Check if Blender exists
if [ ! -f "$BLENDER_PATH" ]; then
    log_error "Blender not found at $BLENDER_PATH"
    exit 1
fi

# Kill any existing Blender processes
log_info "Cleaning up existing Blender processes..."
pkill -f blender 2>/dev/null || true
sleep 2

# Check if port is available
if ! command -v netstat &> /dev/null; then
    log_warn "netstat not available, skipping port check"
else
    if netstat -tlnp 2>/dev/null | grep -q ":$BLD_REMOTE_PORT "; then
        log_error "Port $BLD_REMOTE_PORT is already in use"
        log_info "Use 'netstat -tlnp | grep $BLD_REMOTE_PORT' to check what's using it"
        exit 1
    fi
fi

log_header "=================================================="
log_header "Starting Blender with BLD Remote MCP Service"
log_header "=================================================="
log_info "Blender Path: $BLENDER_PATH"
log_info "BLD Remote MCP Port: $BLD_REMOTE_PORT"
log_info "Auto-start: Enabled"
log_header "=================================================="

# Set environment variables for BLD Remote MCP
export BLD_REMOTE_MCP_PORT=$BLD_REMOTE_PORT
export BLD_REMOTE_MCP_START_NOW=1

log_info "Environment configured:"
log_info "  BLD_REMOTE_MCP_PORT=$BLD_REMOTE_MCP_PORT"
log_info "  BLD_REMOTE_MCP_START_NOW=$BLD_REMOTE_MCP_START_NOW"

# Start Blender
log_info "Starting Blender..."
log_info "Wait approximately 10 seconds for service to initialize"
log_info "Look for: '✅ TCP server started successfully on port $BLD_REMOTE_PORT'"

# Execute Blender with the environment
exec "$BLENDER_PATH"