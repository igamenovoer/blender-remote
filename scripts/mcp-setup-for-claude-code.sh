#!/bin/bash

# MCP Setup Script for Claude Code CLI
# Sets up MCP servers to work with Claude Code

set -e  # Exit on any error

echo "🚀 Setting up MCP servers for Claude Code..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    echo "🔍 Checking prerequisites..."
    
    # Check Claude Code CLI
    if ! command -v claude &> /dev/null; then
        print_error "Claude Code CLI is not installed. Please install it first."
        exit 1
    fi
    print_status "Claude Code CLI found: $(claude --version)"
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install from https://nodejs.org/"
        exit 1
    fi
    print_status "Node.js found: $(node --version)"
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed. Please install Node.js from https://nodejs.org/"
        exit 1
    fi
    print_status "npm found: $(npm --version)"
    
    # Check bunx (part of Bun)
    if ! command -v bunx &> /dev/null; then
        print_error "bunx not found. Please install Bun first:"
        echo ""
        echo "📦 Install Bun (includes bunx):"
        echo "   curl -fsSL https://bun.com/install | bash"
        echo ""
        echo "   Or visit: https://bun.com/docs/installation"
        echo ""
        exit 1
    fi
    print_status "bunx found: $(bunx --version)"
    
    # Check Python and uv/uvx
    if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
        print_error "Python is not installed. Please install Python 3.8+"
        exit 1
    fi
    
    if ! command -v uvx &> /dev/null; then
        print_error "uvx not found. Please install uv first:"
        echo ""
        echo "📦 Install uv (includes uvx):"
        echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
        echo "   source \$HOME/.cargo/env"
        echo ""
        echo "   Or visit: https://docs.astral.sh/uv/"
        echo ""
        exit 1
    fi
    print_status "uvx found"
}

# Install MCP servers
install_mcp_servers() {
    echo "📦 Installing MCP servers..."
    
    # Install Tavily MCP (via bunx)
    print_status "Installing Tavily MCP server..."
    bunx tavily-mcp@latest --help >/dev/null 2>&1 || echo "Tavily MCP will be installed on first use via bunx"
    
    # Context7 uses HTTP transport - no installation needed
    print_status "Context7 MCP uses HTTP transport - no installation required"
    
    # Note: fetch and blender-mcp will be installed via uvx on first use
    print_status "MCP server dependencies checked"
}

# Get API keys
get_api_keys() {
    echo "🔑 Setting up API keys..."
    
    # Tavily API Key - always prompt
    echo "Please enter your Tavily API key:"
    read -r TAVILY_API_KEY
    if [ -z "$TAVILY_API_KEY" ]; then
        print_error "Tavily API key is required"
        exit 1
    fi
    print_status "Tavily API key provided"
}

# Add MCP servers to Claude Code
add_mcp_servers() {
    echo "⚙️ Adding MCP servers to Claude Code..."
    
    # Remove existing servers if they exist (ignore errors)
    claude mcp remove tavily 2>/dev/null || true
    claude mcp remove fetch 2>/dev/null || true
    claude mcp remove blender-mcp 2>/dev/null || true
    claude mcp remove context7 2>/dev/null || true
    
    # Add Tavily MCP server (using bunx)
    print_status "Adding Tavily MCP server..."
    claude mcp add tavily bunx tavily-mcp@latest -e TAVILY_API_KEY="$TAVILY_API_KEY"
    
    # Add Fetch MCP server
    print_status "Adding Fetch MCP server..."
    claude mcp add fetch uvx mcp-server-fetch
    
    # Add Blender MCP server
    print_status "Adding Blender MCP server..."
    claude mcp add blender-mcp uvx blender-mcp
    
    # Add Context7 MCP server (using HTTP transport)
    print_status "Adding Context7 MCP server..."
    claude mcp add --transport http context7 https://mcp.context7.com/mcp
    
    print_status "All MCP servers added to Claude Code"
}

# Test the setup
test_setup() {
    echo "🧪 Testing setup..."
    
    # List configured servers
    print_status "Configured MCP servers:"
    claude mcp list
    
    echo ""
    print_status "Setup validation complete"
}

# Main execution
main() {
    echo "🎯 MCP Setup for Claude Code CLI"
    echo "================================="
    
    check_prerequisites
    install_mcp_servers
    get_api_keys
    add_mcp_servers
    test_setup
    
    echo ""
    echo "🎉 Setup complete!"
    echo ""
    echo "Your MCP servers are now configured for Claude Code:"
    echo "• tavily - Web search capabilities"
    echo "• fetch - Web content fetching"
    echo "• blender-mcp - Blender 3D integration"
    echo "• context7 - Up-to-date documentation"
    echo ""
    echo "You can now use these tools in your Claude Code conversations!"
    echo ""
    echo "Useful commands:"
    echo "• claude mcp list - List all configured servers"
    echo "• claude mcp get <name> - Get details about a server"
    echo "• claude mcp remove <name> - Remove a server"
    echo ""
    echo "Note: You'll need to provide your Tavily API key each time you run this script"
}

# Run main function
main "$@" 