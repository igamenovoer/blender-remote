# PowerShell script to start Blender with Auto MCP plugin in headless mode
# This script configures the environment and starts Blender in background mode
# Usage: .\start-blender-mcp-headless.ps1 [port]
# Default port: 9876

param(
    [int]$Port = 9876
)

# Set environment variables for Auto MCP configuration
$env:BLENDER_AUTO_MCP_SERVICE_PORT = $Port.ToString()
$env:BLENDER_AUTO_MCP_START_NOW = "1"

# Display configuration
Write-Host "Starting Blender with Auto MCP plugin (Headless mode)" -ForegroundColor Green
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
Write-Host "Starting Blender in headless mode..." -ForegroundColor Yellow
Write-Host "The Auto MCP server will start automatically on port $env:BLENDER_AUTO_MCP_SERVICE_PORT" -ForegroundColor Cyan
Write-Host "Blender will run in the background and keep the MCP server alive" -ForegroundColor Cyan
Write-Host ""
Write-Host "To stop the server, use Ctrl+C or send a 'server_shutdown' MCP command" -ForegroundColor Yellow
Write-Host ""

# Start Blender in headless mode
try {
    # Use & operator to run Blender and capture output
    Write-Host "Blender is now running in headless mode..." -ForegroundColor Green
    Write-Host "MCP server should be available at localhost:$env:BLENDER_AUTO_MCP_SERVICE_PORT" -ForegroundColor Cyan
    Write-Host ""
    
    # Start Blender process and wait for it
    $blenderProcess = Start-Process -FilePath $blenderExe -ArgumentList "--background" -PassThru -NoNewWindow
    
    Write-Host "Blender process started (PID: $($blenderProcess.Id))" -ForegroundColor Green
    Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
    
    # Wait for the process to complete
    $blenderProcess.WaitForExit()
    
    Write-Host ""
    Write-Host "Blender process has ended." -ForegroundColor Green
    
} catch {
    Write-Host "Error starting Blender: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Blender headless session has been stopped." -ForegroundColor Green