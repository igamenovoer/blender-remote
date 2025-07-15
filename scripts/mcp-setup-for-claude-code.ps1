#!/usr/bin/env pwsh

# MCP Setup Script for Claude Code CLI (PowerShell)
# Sets up MCP servers to work with Claude Code

param(
    [string]$TavilyApiKey = ""
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Colors for output
$Colors = @{
    Green  = "Green"
    Yellow = "Yellow"
    Red    = "Red"
    White  = "White"
}

function Write-Status {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor $Colors.Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor $Colors.Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor $Colors.Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "$Message" -ForegroundColor $Colors.White
}

# Check prerequisites
function Test-Prerequisites {
    Write-Info "🔍 Checking prerequisites..."
    
    # Check Claude Code CLI
    try {
        $claudeVersion = claude --version
        Write-Status "Claude Code CLI found: $claudeVersion"
    }
    catch {
        Write-Error "Claude Code CLI is not installed. Please install it first."
        exit 1
    }
    
    # Check Node.js
    try {
        $nodeVersion = node --version
        Write-Status "Node.js found: $nodeVersion"
    }
    catch {
        Write-Error "Node.js is not installed. Please install from https://nodejs.org/"
        exit 1
    }
    
    # Check npm
    try {
        $npmVersion = npm --version
        Write-Status "npm found: $npmVersion"
    }
    catch {
        Write-Error "npm is not installed. Please install Node.js from https://nodejs.org/"
        exit 1
    }
    
    # Check bunx (part of Bun)
    try {
        $null = bunx --version
        Write-Status "bunx found: $(bunx --version)"
    }
    catch {
        Write-Error "bunx not found. Please install Bun first:"
        Write-Host ""
        Write-Host "📦 Install Bun (includes bunx):" -ForegroundColor Cyan
        Write-Host "   powershell -c `"irm bun.sh/install.ps1|iex`"" -ForegroundColor Green
        Write-Host ""
        Write-Host "   Or visit: https://bun.com/docs/installation" -ForegroundColor Yellow
        Write-Host ""
        exit 1
    }
    
    # Check Python
    $pythonCmd = $null
    foreach ($cmd in @("python", "python3", "py")) {
        try {
            $null = & $cmd --version
            $pythonCmd = $cmd
            break
        }
        catch {
            continue
        }
    }
    
    if (-not $pythonCmd) {
        Write-Error "Python is not installed. Please install Python 3.8+"
        exit 1
    }
    
    # Check uvx
    try {
        $null = uvx --version
        Write-Status "uvx found"
    }
    catch {
        Write-Error "uvx not found. Please install uv first:"
        Write-Host ""
        Write-Host "📦 Install uv (includes uvx):" -ForegroundColor Cyan
        Write-Host "   powershell -c `"irm https://astral.sh/uv/install.ps1 | iex`"" -ForegroundColor Green
        Write-Host ""
        Write-Host "   Or visit: https://docs.astral.sh/uv/" -ForegroundColor Yellow
        Write-Host ""
        exit 1
    }
}

# Install MCP servers
function Install-McpServers {
    Write-Info "📦 Installing MCP servers..."
    
    # Install Tavily MCP (via bunx)
    Write-Status "Checking Tavily MCP server..."
    try {
        $null = bunx tavily-mcp@latest --help
        Write-Status "Tavily MCP available via bunx"
    }
    catch {
        Write-Status "Tavily MCP will be installed on first use via bunx"
    }
    
    # Context7 uses HTTP transport - no installation needed
    Write-Status "Context7 MCP uses HTTP transport - no installation required"
    
    # Note: fetch and blender-mcp will be installed via uvx on first use
    Write-Status "MCP server packages installed"
}

# Get API keys
function Get-ApiKeys {
    Write-Info "🔑 Setting up API keys..."
    
    # Tavily API Key - always prompt if not provided
    if (-not $TavilyApiKey) {
        $TavilyApiKey = Read-Host "Please enter your Tavily API key"
    }
    
    if (-not $TavilyApiKey) {
        Write-Error "Tavily API key is required"
        exit 1
    }
    
    Write-Status "Tavily API key provided"
    return $TavilyApiKey
}

# Add MCP servers to Claude Code
function Add-McpServers {
    param([string]$ApiKey)
    
    Write-Info "⚙️ Adding MCP servers to Claude Code..."
    
    # Remove existing servers if they exist (ignore errors)
    try { claude mcp remove tavily } catch { }
    try { claude mcp remove fetch } catch { }
    try { claude mcp remove blender-mcp } catch { }
    try { claude mcp remove context7 } catch { }
    
    # Add Tavily MCP server (using bunx)
    Write-Status "Adding Tavily MCP server..."
    claude mcp add tavily bunx tavily-mcp@latest -e TAVILY_API_KEY="$ApiKey"
    
    # Add Fetch MCP server
    Write-Status "Adding Fetch MCP server..."
    claude mcp add fetch uvx mcp-server-fetch
    
    # Add Blender MCP server
    Write-Status "Adding Blender MCP server..."
    claude mcp add blender-mcp uvx blender-mcp
    
    # Add Context7 MCP server (using HTTP transport)
    Write-Status "Adding Context7 MCP server..."
    claude mcp add --transport http context7 https://mcp.context7.com/mcp
    
    Write-Status "All MCP servers added to Claude Code"
}

# Test the setup
function Test-Setup {
    Write-Info "🧪 Testing setup..."
    
    # List configured servers
    Write-Status "Configured MCP servers:"
    claude mcp list
    
    Write-Info ""
    Write-Status "Setup validation complete"
}

# Main execution
function Main {
    Write-Info "🎯 MCP Setup for Claude Code CLI"
    Write-Info "=================================="
    
    try {
        Test-Prerequisites
        Install-McpServers
        $apiKey = Get-ApiKeys
        Add-McpServers -ApiKey $apiKey
        Test-Setup
        
        Write-Info ""
        Write-Info "🎉 Setup complete!" -ForegroundColor Green
        Write-Info ""
        Write-Info "Your MCP servers are now configured for Claude Code:"
        Write-Info "• tavily - Web search capabilities"
        Write-Info "• fetch - Web content fetching"
        Write-Info "• blender-mcp - Blender 3D integration"
        Write-Info "• context7 - Up-to-date documentation"
        Write-Info ""
        Write-Info "You can now use these tools in your Claude Code conversations!"
        Write-Info ""
        Write-Info "Useful commands:"
        Write-Info "• claude mcp list - List all configured servers"
        Write-Info "• claude mcp get <name> - Get details about a server"
        Write-Info "• claude mcp remove <name> - Remove a server"
        Write-Info ""
        Write-Info "Note: You'll need to provide your Tavily API key each time you run this script"
    }
    catch {
        Write-Error "Setup failed: $_"
        exit 1
    }
}

# Run main function
Main 