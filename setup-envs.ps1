# PowerShell environment setup script
# Usage: . .\setup-envs.ps1 [--proxy <proxy_addr|auto|none>]
# Note: Source this script with ". .\setup-envs.ps1" to set variables in current session

[CmdletBinding()]
param(
    [Parameter(Position=0)]
    [string]$Proxy = "auto",
    
    [switch]$Help
)

# Check if long paths are enabled on Windows
function Test-LongPathEnabled {
    try {
        $longPathEnabled = Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -ErrorAction SilentlyContinue
        if ($null -eq $longPathEnabled -or $longPathEnabled.LongPathsEnabled -ne 1) {
            Write-Host ""
            Write-Host "WARNING: Windows Long Path support is NOT enabled!" -ForegroundColor Yellow
            Write-Host "This may cause issues with packages that have deep directory structures." -ForegroundColor Yellow
            Write-Host ""
            Write-Host "To enable long paths, run PowerShell as Administrator and execute:" -ForegroundColor Cyan
            Write-Host '  New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force' -ForegroundColor White
            Write-Host ""
            Write-Host "Then restart your terminal or reboot your computer." -ForegroundColor Cyan
            Write-Host ""
        }
    }
    catch {
        # Silently ignore errors (e.g., on non-Windows systems)
    }
}

# Run long path check at startup
Test-LongPathEnabled

function Show-Usage {
    Write-Host @"
Usage: . .\setup-envs.ps1 [-Proxy <proxy_addr|auto|none>] [-Help]

Options:
    -Proxy     Explicit proxy address, or one of:
               auto (default) - detect proxy at http://127.0.0.1:7890
               none           - do not configure any proxy

    Notes:
    - When running inside Docker, detection also probes host.docker.internal:7890
      (HTTP) in addition to 127.0.0.1.
    -Help      Show this help message and exit
"@
}

if ($Help) {
    Show-Usage
    return
}

# Get script directory and set CODEX_HOME
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$CodexHome = Join-Path $ScriptDir ".codex"
$env:CODEX_HOME = $CodexHome

function Clear-ProxyVars {
    Remove-Item Env:\HTTP_PROXY -ErrorAction SilentlyContinue
    Remove-Item Env:\HTTPS_PROXY -ErrorAction SilentlyContinue
    Remove-Item Env:\http_proxy -ErrorAction SilentlyContinue
    Remove-Item Env:\https_proxy -ErrorAction SilentlyContinue
}

function Set-ProxyVars {
    param([string]$ProxyAddress)
    
    $env:HTTP_PROXY = $ProxyAddress
    $env:HTTPS_PROXY = $ProxyAddress
    $env:http_proxy = $ProxyAddress
    $env:https_proxy = $ProxyAddress
}

function Test-InDocker {
    # Check for common Docker indicators
    if (Test-Path "/.dockerenv") {
        return $true
    }
    
    if ($env:container -eq "docker") {
        return $true
    }
    
    # Windows containers might set different indicators
    if ($env:DOTNET_RUNNING_IN_CONTAINER -eq "true") {
        return $true
    }
    
    return $false
}

function Detect-LocalProxy {
    $debug = $env:DEBUG_PROXY -eq "true"
    
    # Determine if we're inside a Docker/containerized environment
    $inDocker = Test-InDocker
    if ($debug) {
        Write-Host "Debug: inDocker=$inDocker" -ForegroundColor Yellow
    }
    
    # Build candidate hosts list
    $candidateHosts = @("127.0.0.1")
    if ($inDocker) {
        $candidateHosts += "host.docker.internal"
    }
    
    # Use fast, reliable test URLs that don't redirect
    $testUrls = @(
        "http://www.google.com/generate_204",
        "http://captive.apple.com/hotspot-detect.txt",
        "http://connectivitycheck.gstatic.com/generate_204"
    )
    
    # Try HTTP proxy protocol for each candidate host
    foreach ($candidateHost in $candidateHosts) {
        $httpProxyCandidate = "http://$($candidateHost):7890"
        foreach ($url in $testUrls) {
            if ($debug) {
                Write-Host "Debug: Testing HTTP proxy $httpProxyCandidate with $url" -ForegroundColor Yellow
            }
            
            try {
                $response = Invoke-WebRequest -Uri $url -Proxy $httpProxyCandidate -TimeoutSec 8 -UseBasicParsing -ErrorAction Stop
                if ($debug) {
                    Write-Host "Debug: HTTP proxy successful via $httpProxyCandidate" -ForegroundColor Green
                }
                return $httpProxyCandidate
            }
            catch {
                # Continue to next attempt
            }
        }
    }
    
    if ($debug) {
        Write-Host "Debug: HTTP proxy detection failed" -ForegroundColor Red
    }
    return $null
}

# Handle proxy configuration
$proxyStatus = ""

switch ($Proxy.ToLower()) {
    "auto" {
        # Respect existing proxy configuration
        if ($env:HTTP_PROXY -or $env:HTTPS_PROXY -or $env:http_proxy -or $env:https_proxy) {
            $proxyStatus = "kept (pre-existing)"
        }
        else {
            $proxyAddr = Detect-LocalProxy
            if ($proxyAddr) {
                Set-ProxyVars -ProxyAddress $proxyAddr
                $proxyStatus = "detected and set to $proxyAddr"
            }
            else {
                Clear-ProxyVars
                $proxyStatus = "not set (no proxy detected)"
            }
        }
    }
    "none" {
        Clear-ProxyVars
        $proxyStatus = "disabled (cleared)"
    }
    default {
        Set-ProxyVars -ProxyAddress $Proxy
        $proxyStatus = "explicitly set to $Proxy"
    }
}

# Print all environment variables set by this script
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Environment variables configured:" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "CODEX_HOME = $env:CODEX_HOME"
Write-Host ""
Write-Host "Proxy status: $proxyStatus"

if ($env:HTTP_PROXY -or $env:HTTPS_PROXY -or $env:http_proxy -or $env:https_proxy) {
    Write-Host "  HTTP_PROXY  = $(if ($env:HTTP_PROXY) { $env:HTTP_PROXY } else { '<not set>' })"
    Write-Host "  HTTPS_PROXY = $(if ($env:HTTPS_PROXY) { $env:HTTPS_PROXY } else { '<not set>' })"
    Write-Host "  http_proxy  = $(if ($env:http_proxy) { $env:http_proxy } else { '<not set>' })"
    Write-Host "  https_proxy = $(if ($env:https_proxy) { $env:https_proxy } else { '<not set>' })"
}
else {
    Write-Host "  (no proxy variables set)"
}

Write-Host "=========================================" -ForegroundColor Cyan

# Start SSH agent and add keys
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "SSH Agent Configuration:" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

try {
    # Check if ssh-agent service exists
    $sshAgentService = Get-Service ssh-agent -ErrorAction SilentlyContinue
    
    if ($null -eq $sshAgentService) {
        Write-Host "SSH Agent service not found. OpenSSH may not be installed." -ForegroundColor Yellow
    }
    else {
        # Start the service if it's not running
        if ($sshAgentService.Status -ne 'Running') {
            Write-Host "Starting SSH Agent service..." -ForegroundColor Yellow
            Start-Service ssh-agent -ErrorAction Stop
            Write-Host "SSH Agent started successfully." -ForegroundColor Green
        }
        else {
            Write-Host "SSH Agent is already running." -ForegroundColor Green
        }
        
        # Add SSH keys
        Write-Host "Adding SSH keys..." -ForegroundColor Yellow
        $sshAddOutput = & ssh-add 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "SSH keys added successfully:" -ForegroundColor Green
            $sshAddOutput | ForEach-Object { Write-Host "  $_" }
        }
        else {
            Write-Host "Note: $sshAddOutput" -ForegroundColor Yellow
        }
    }
}
catch {
    Write-Host "Error configuring SSH Agent: $_" -ForegroundColor Red
}

Write-Host "=========================================" -ForegroundColor Cyan
