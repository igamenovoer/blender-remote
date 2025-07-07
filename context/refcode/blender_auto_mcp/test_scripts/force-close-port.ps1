# PowerShell script to forcefully close processes using a specified port
# This script requires administrator privileges

param(
    [Parameter(Mandatory=$true, Position=0)]
    [int]$Port,
    [switch]$Force = $false
)

# Check if running as administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "This script requires administrator privileges." -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To run as administrator:" -ForegroundColor Cyan
    Write-Host "1. Right-click on PowerShell and select 'Run as Administrator'" -ForegroundColor White
    Write-Host "2. Or run: Start-Process PowerShell -Verb RunAs" -ForegroundColor White
    Write-Host ""
    Write-Host "Usage: .\force-close-port.ps1 <port> [-Force]" -ForegroundColor White
    Write-Host "Example: .\force-close-port.ps1 10080 -Force" -ForegroundColor White
    exit 1
}

# Validate port number
if ($Port -lt 1 -or $Port -gt 65535) {
    Write-Host "Error: Port number must be between 1 and 65535" -ForegroundColor Red
    exit 1
}

Write-Host "Scanning for processes using port $Port..." -ForegroundColor Cyan

# Find processes using the port
try {
    $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    
    if ($connections.Count -eq 0) {
        Write-Host "No processes found using port $Port" -ForegroundColor Green
        exit 0
    }
    
    Write-Host "Found $($connections.Count) connection(s) using port ${Port}:" -ForegroundColor Yellow
    
    foreach ($conn in $connections) {
        $processId = $conn.OwningProcess
        
        try {
            $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
            if ($process) {
                Write-Host "  PID: $processId - Process: $($process.ProcessName) - Path: $($process.Path)" -ForegroundColor White
                
                if ($Force) {
                    Write-Host "    Forcefully terminating process $processId ($($process.ProcessName))..." -ForegroundColor Red
                    try {
                        Stop-Process -Id $processId -Force
                        Write-Host "    Process $processId terminated successfully" -ForegroundColor Green
                    }
                    catch {
                        Write-Host "    Failed to terminate process ${processId}: $($_.Exception.Message)" -ForegroundColor Red
                    }
                } else {
                    Write-Host "    Use -Force parameter to terminate this process" -ForegroundColor Yellow
                }
            } else {
                Write-Host "  PID: $processId - Process not found (may have already exited)" -ForegroundColor Gray
            }
        }
        catch {
            Write-Host "  PID: $processId - Error getting process info: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    if (-not $Force) {
        Write-Host ""
        Write-Host "To forcefully terminate all processes using port ${Port}, run:" -ForegroundColor Cyan
        Write-Host "  .\force-close-port.ps1 $Port -Force" -ForegroundColor White
        Write-Host ""
        Write-Host "WARNING: This will forcefully terminate processes and may cause data loss!" -ForegroundColor Red
    } else {
        Write-Host ""
        Write-Host "Verifying port $Port is now free..." -ForegroundColor Cyan
        Start-Sleep -Seconds 2
        
        $remainingConnections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
        if ($remainingConnections.Count -eq 0) {
            Write-Host "Port $Port is now free!" -ForegroundColor Green
        } else {
            Write-Host "Warning: Port $Port may still be in use by $($remainingConnections.Count) connection(s)" -ForegroundColor Yellow
        }
    }
}
catch {
    Write-Host "Error checking port ${Port}: $($_.Exception.Message)" -ForegroundColor Red
    
    # Fallback to netstat
    Write-Host "Falling back to netstat..." -ForegroundColor Yellow
    try {
        $netstatOutput = netstat -ano | Select-String ":$Port "
        if ($netstatOutput) {
            Write-Host "Netstat output for port ${Port}:" -ForegroundColor White
            $netstatOutput | ForEach-Object {
                Write-Host "  $_" -ForegroundColor White
                if ($_.Line -match '\s+(\d+)$') {
                    $pid = $Matches[1]
                    $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
                    if ($process) {
                        Write-Host "    PID ${pid}: $($process.ProcessName)" -ForegroundColor Gray
                        if ($Force) {
                            Write-Host "    Terminating PID $pid..." -ForegroundColor Red
                            try {
                                Stop-Process -Id $pid -Force
                                Write-Host "    PID $pid terminated" -ForegroundColor Green
                            }
                            catch {
                                Write-Host "    Failed to terminate PID ${pid}: $($_.Exception.Message)" -ForegroundColor Red
                            }
                        }
                    }
                }
            }
        } else {
            Write-Host "No processes found using port $Port (netstat)" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "Netstat also failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Script completed." -ForegroundColor Cyan