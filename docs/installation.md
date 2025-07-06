# Installation

This guide will help you install and set up Blender Remote in your environment.

## Prerequisites

- **Python 3.8+**: Blender Remote requires Python 3.8 or higher
- **Blender 3.0+**: A compatible version of Blender
- **Network Access**: For remote connections (if controlling Blender on another machine)

## Installation Methods

### Option 1: From PyPI (Recommended)

Install the latest stable version from PyPI:

```bash
pip install blender-remote
```

### Option 2: From Source

For the latest development version or to contribute:

```bash
# Clone the repository
git clone https://github.com/igamenovoer/blender-remote.git
cd blender-remote

# Install in development mode
pip install -e .
```

### Option 3: Using Pixi (For Developers)

If you're contributing to the project:

```bash
# Install pixi (if not already installed)
curl -fsSL https://pixi.sh/install.sh | bash

# Clone and set up development environment
git clone https://github.com/igamenovoer/blender-remote.git
cd blender-remote
pixi install
```

## Blender Add-on Installation

The Blender add-on enables remote control capabilities within Blender.

### Step 1: Download the Add-on

Download the latest add-on from the [releases page](https://github.com/igamenovoer/blender-remote/releases) or use the files from the `blender_addon/` directory.

### Step 2: Install in Blender

1. Open Blender
2. Go to **Edit → Preferences**
3. Select **Add-ons** from the left panel
4. Click **Install...**
5. Navigate to and select the downloaded add-on file
6. Enable the add-on by checking the checkbox next to "Remote Control"

### Step 3: Configure the Add-on

1. In the add-on preferences, configure:
   - **Port**: Default is 5555
   - **Host**: Default is localhost (127.0.0.1)
   - **Auto-start**: Enable to start the service automatically

2. Click **Start Service** to begin listening for remote connections

## Verification

### Test Python Installation

```python
import blender_remote
print(f"Blender Remote version: {blender_remote.__version__}")
```

### Test CLI Installation

```bash
blender-remote --version
```

### Test Connection

With Blender running and the add-on active:

```python
import blender_remote

# Attempt to connect
try:
    client = blender_remote.connect("localhost", 5555)
    print("✅ Successfully connected to Blender!")
    client.disconnect()
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

## Troubleshooting

### Common Issues

#### Connection Refused
```
ConnectionRefusedError: [Errno 61] Connection refused
```
**Solution**: Ensure the Blender add-on is installed, enabled, and the service is started.

#### Port Already in Use
```
OSError: [Errno 48] Address already in use
```
**Solution**: Either stop the conflicting service or configure a different port in the add-on preferences.

#### Import Error
```
ModuleNotFoundError: No module named 'blender_remote'
```
**Solution**: Ensure you've installed the package in the correct Python environment.

### Network Configuration

For remote connections (controlling Blender on another machine):

1. **Firewall**: Ensure the port (default 5555) is open
2. **Network**: Both machines should be on the same network or have network connectivity
3. **Security**: Consider using VPN or SSH tunneling for secure connections

### Development Setup

For contributors and developers:

```bash
# Set up development environment
pixi run dev

# Run tests
pixi run test

# Check code quality
pixi run lint
pixi run format
```

## Next Steps

Once installation is complete:

1. [Getting Started](getting-started.md) - Create your first remote Blender session
2. [API Reference](api-reference.md) - Explore the available commands
3. [CLI Tools](cli.md) - Learn the command-line interface

## Support

If you encounter issues:

1. Check the [troubleshooting section](#troubleshooting) above
2. Search [existing issues](https://github.com/igamenovoer/blender-remote/issues)
3. Create a [new issue](https://github.com/igamenovoer/blender-remote/issues/new) with details