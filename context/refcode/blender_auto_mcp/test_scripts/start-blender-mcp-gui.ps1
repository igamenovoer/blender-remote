# PowerShell script to start Blender with Auto MCP plugin in GUI mode
# This script configures the environment and starts Blender normally with GUI
# Usage: .\start-blender-mcp-gui.ps1 [port]
# Default port: 9876

param(
    [int]$Port = 9876
)

# Set environment variables for Auto MCP configuration
$env:BLENDER_AUTO_MCP_SERVICE_PORT = $Port.ToString()
$env:BLENDER_AUTO_MCP_START_NOW = "1"

# Display configuration
Write-Host "Starting Blender with Auto MCP plugin (GUI mode)" -ForegroundColor Green
Write-Host "Port: $env:BLENDER_AUTO_MCP_SERVICE_PORT" -ForegroundColor Cyan
Write-Host "Auto-start: $env:BLENDER_AUTO_MCP_START_NOW" -ForegroundColor Cyan

# Find Blender executable
$blenderExe = $null

# First check BLENDER_EXEC_PATH environment variable
if ($env:BLENDER_EXEC_PATH -and (Test-Path $env:BLENDER_EXEC_PATH)) {
    $blenderExe = $env:BLENDER_EXEC_PATH
    Write-Host "Using Blender from BLENDER_EXEC_PATH: $blenderExe" -ForegroundColor Green
} else {
    # Fall back to assuming blender is in PATH
    $blenderExe = "blender"
    Write-Host "BLENDER_EXEC_PATH not set or invalid, using 'blender' from PATH" -ForegroundColor Yellow
}

Write-Host "Found Blender at: $blenderExe" -ForegroundColor Green
Write-Host ""
Write-Host "Starting Blender..." -ForegroundColor Yellow
Write-Host "The Auto MCP server will start automatically on port $env:BLENDER_AUTO_MCP_SERVICE_PORT" -ForegroundColor Cyan
Write-Host "Check the Blender console for startup messages" -ForegroundColor Cyan
Write-Host ""

# Start Blender with GUI
try {
    Start-Process -FilePath $blenderExe -Wait
} catch {
    Write-Host "Error starting Blender: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Blender has been closed." -ForegroundColor Green