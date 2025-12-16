# How to Install Python Packages on an Offline Remote System via RPC

This guide covers installing Python packages on a remote Python interpreter accessible via RPC (you can execute Python code remotely and have full filesystem access through that shell, but no SSH or direct file transfer).

**Critical assumption handled**: This guide assumes the remote Python installation may be minimal (bare interpreter only, no pip, possibly missing standard library modules). We provide complete bootstrapping instructions.

## Which Approach Should You Use?

```
┌─────────────────────────────────────┐
│ Does remote have internet access?   │
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┐
       │                │
      YES              NO
       │                │
       ▼                ▼
   Use Quick      Use Full Offline
   Start Guide    Workflow (below)
   (3 steps)      (Complex, 4+ steps)
```

**Check remote internet access**:
```python
# Execute on remote to test
import urllib.request
try:
    urllib.request.urlopen("https://pypi.org", timeout=5)
    print("✓ Remote HAS internet access - use Quick Start")
except:
    print("✗ Remote is OFFLINE - use Full Offline Workflow")
```

---

## Quick Start: If Remote HAS Internet Access

**If your remote Python can access the internet**, the process is dramatically simpler. Skip to this section instead of following the full offline workflow.

### 1. Install pip (if missing)

Execute on remote:

```python
# Option A: Use ensurepip (if available)
import subprocess
import sys
subprocess.check_call([sys.executable, "-m", "ensurepip", "--upgrade"])

# Option B: Download and run get-pip.py
import urllib.request
import sys
import subprocess

url = "https://bootstrap.pypa.io/get-pip.py"
with urllib.request.urlopen(url) as response:
    script = response.read()

with open("/tmp/get-pip.py", "wb") as f:
    f.write(script)

subprocess.check_call([sys.executable, "/tmp/get-pip.py"])
```

### 2. Install packages directly

Execute on remote:

```python
import subprocess
import sys

# Install any package directly from PyPI
subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])

# Install multiple packages
subprocess.check_call([
    sys.executable, "-m", "pip", "install",
    "requests", "numpy", "pandas"
])

# Install specific version
subprocess.check_call([
    sys.executable, "-m", "pip", "install",
    "requests==2.31.0"
])
```

### 3. Verify installation

```python
import requests
print(f"requests version: {requests.__version__}")
```

**That's it!** No wheel downloading, encoding, transferring, or manual installation needed.

---

## Full Offline Workflow

**The rest of this guide is for when the remote is completely offline (air-gapped).** If your remote has internet, use the Quick Start section above instead.

## Overview

The workflow consists of:
0. **Bootstrap pip** (if not present on remote) - Install pip itself first
1. **Discover** remote system information (Python version, platform, architecture)
2. **Download** wheels locally for the target platform with all dependencies
3. **Transfer** wheels to remote filesystem via RPC (using binary encoding)
4. **Install** wheels on remote using pip with local file references

## Step 0: Bootstrap pip on Remote (If Needed)

**CRITICAL**: Many minimal Python installations (embedded systems, custom builds, minimal Docker images) do not include pip. You must install pip itself before installing any packages.

### Check if pip exists

Execute on remote:

```python
import sys
import subprocess

# Method 1: Check if pip module exists
try:
    import pip
    print(f"pip is installed: {pip.__version__}")
except ImportError:
    print("pip is NOT installed")

# Method 2: Try running pip
try:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "--version"],
        capture_output=True,
        text=True
    )
    print(f"pip command works: {result.stdout}")
except Exception as e:
    print(f"pip command failed: {e}")
```

### Option 1: Use ensurepip (Built-in, Recommended)

Python 3.4+ includes `ensurepip` module for bootstrapping pip:

```python
import sys
import subprocess

# Try to install pip using ensurepip
try:
    subprocess.check_call([sys.executable, "-m", "ensurepip", "--upgrade"])
    print("pip installed successfully via ensurepip")
except Exception as e:
    print(f"ensurepip failed: {e}")
    print("ensurepip may not be available in this Python installation")
```

**Caveat**: Some Python distributions (especially embedded/minimal builds) exclude `ensurepip` to save space.

### Option 2: Transfer and Install get-pip.py

If `ensurepip` is not available, use the standalone `get-pip.py` script.

**How it works offline**: The get-pip.py script from bootstrap.pypa.io bundles pip, setuptools, and wheel wheels as base64-encoded data **inside the script itself** (that's why it's 2-3 MB). When executed, it extracts these bundled wheels to a temp directory and installs from there - **no internet required**.

**IMPORTANT**: Always use the official get-pip.py from bootstrap.pypa.io, not older versions that might require internet.

**Local Machine (Internet-Connected):**

```python
import urllib.request
import base64

# Download get-pip.py (contains bundled wheels)
pip_url = "https://bootstrap.pypa.io/get-pip.py"
print(f"Downloading get-pip.py from {pip_url}")

with urllib.request.urlopen(pip_url) as response:
    get_pip_script = response.read()

print(f"Downloaded {len(get_pip_script)} bytes (large because it bundles pip wheels)")

# Encode for transfer
encoded_script = base64.b64encode(get_pip_script).decode("ascii")
print(f"Encoded get-pip.py: {len(encoded_script)} chars")

# Send encoded_script to remote via your RPC mechanism
```

**Remote Machine (Offline):**

```python
import base64
import sys
import subprocess

# Receive encoded_script from local via RPC
# encoded_script = "..." (received from local)

# Decode and save get-pip.py
get_pip_bytes = base64.b64decode(encoded_script)
get_pip_path = "/tmp/get-pip.py"

with open(get_pip_path, "wb") as f:
    f.write(get_pip_bytes)

print(f"Saved get-pip.py to {get_pip_path}")

# Run get-pip.py to install pip
subprocess.check_call([sys.executable, get_pip_path])
print("pip installed successfully")

# Verify
subprocess.check_call([sys.executable, "-m", "pip", "--version"])
```

### Option 3: Manually Install pip from Wheels

If `get-pip.py` fails (e.g., requires internet for dependencies), manually install pip and its dependencies.

**Local Machine (Internet-Connected):**

```python
import subprocess
import sys
import os
import base64

# Download pip and its dependencies as wheels
download_dir = "./pip_bootstrap_wheels"
os.makedirs(download_dir, exist_ok=True)

# Get pip, setuptools, and wheel (core dependencies)
for package in ["pip", "setuptools", "wheel"]:
    subprocess.check_call([
        sys.executable, "-m", "pip", "download",
        "--dest", download_dir,
        "--platform", "manylinux2014_x86_64",  # Adjust for target platform
        "--python-version", "311",  # Adjust for target version
        "--implementation", "cp",
        "--only-binary", ":all:",
        package
    ])

# Encode wheels for transfer
wheels = {}
for filename in os.listdir(download_dir):
    if filename.endswith(".whl"):
        filepath = os.path.join(download_dir, filename)
        with open(filepath, "rb") as f:
            wheel_bytes = f.read()
        wheels[filename] = base64.b64encode(wheel_bytes).decode("ascii")
        print(f"Encoded {filename}")

# Send wheels to remote via RPC
```

**Remote Machine (Offline):**

```python
import base64
import os
import sys
import zipfile
import shutil

def install_wheel_manually(wheel_path):
    """Manually extract and install a wheel file."""
    # Wheels are just ZIP files
    install_dir = None

    # Determine installation directory
    if hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix:
        # In a venv
        install_dir = os.path.join(sys.prefix, "Lib", "site-packages")
    else:
        # System Python - try to get site-packages
        import site
        install_dir = site.getsitepackages()[0] if site.getsitepackages() else None

    if not install_dir:
        raise RuntimeError("Could not determine site-packages directory")

    print(f"Installing to {install_dir}")

    # Extract wheel contents
    with zipfile.ZipFile(wheel_path, "r") as zip_ref:
        # Get list of files
        namelist = zip_ref.namelist()

        # Extract only .py files and package directories (skip .dist-info)
        for name in namelist:
            if not name.endswith("/") and not ".dist-info/" in name:
                # Extract file
                zip_ref.extract(name, install_dir)
                print(f"  Extracted: {name}")

    print(f"Installed {os.path.basename(wheel_path)}")

# Receive encoded wheels from local via RPC
# wheels = {"pip-23.0-py3-none-any.whl": "...", ...}

# Decode and save wheels
wheels_dir = "/tmp/pip_bootstrap"
os.makedirs(wheels_dir, exist_ok=True)

for filename, encoded_data in wheels.items():
    wheel_bytes = base64.b64decode(encoded_data)
    filepath = os.path.join(wheels_dir, filename)
    with open(filepath, "wb") as f:
        f.write(wheel_bytes)
    print(f"Written {filename}")

# Install wheels manually in order: setuptools, wheel, pip
install_order = ["setuptools", "wheel", "pip"]

for package_name in install_order:
    # Find wheel file for this package
    wheel_file = None
    for filename in os.listdir(wheels_dir):
        if filename.startswith(package_name) and filename.endswith(".whl"):
            wheel_file = os.path.join(wheels_dir, filename)
            break

    if wheel_file:
        install_wheel_manually(wheel_file)
    else:
        print(f"Warning: {package_name} wheel not found")

print("\nVerifying pip installation:")
import subprocess
subprocess.check_call([sys.executable, "-m", "pip", "--version"])
```

### Option 4: Pure Python Installation (No Subprocess)

If subprocess is restricted or broken, install pip purely within Python:

```python
import sys
import os
import zipfile
import site

def bootstrap_pip_pure_python(wheel_path):
    """Install pip wheel without using subprocess or pip itself."""

    # Get site-packages directory
    site_packages = site.getsitepackages()[0]
    print(f"Installing to: {site_packages}")

    # Extract wheel (wheels are zip files)
    with zipfile.ZipFile(wheel_path, "r") as whl:
        # Extract all files
        for member in whl.namelist():
            # Skip metadata directories for now
            if ".dist-info/" in member or ".data/" in member:
                continue

            target_path = os.path.join(site_packages, member)

            if member.endswith("/"):
                # Directory
                os.makedirs(target_path, exist_ok=True)
            else:
                # File
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with whl.open(member) as source, open(target_path, "wb") as target:
                    target.write(source.read())

    print(f"Installed {os.path.basename(wheel_path)}")

# Use it
bootstrap_pip_pure_python("/tmp/wheels/pip-23.0-py3-none-any.whl")

# Verify by importing
import pip
print(f"pip version: {pip.__version__}")
```

### Verification After Bootstrap

After installing pip, verify it works:

```python
import subprocess
import sys

# Check pip is available
try:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "--version"],
        capture_output=True,
        text=True,
        check=True
    )
    print(f"SUCCESS: {result.stdout}")
except subprocess.CalledProcessError as e:
    print(f"FAILED: {e}")
    print(f"stderr: {e.stderr}")

# List installed packages
try:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "list"],
        capture_output=True,
        text=True,
        check=True
    )
    print(f"Installed packages:\n{result.stdout}")
except subprocess.CalledProcessError as e:
    print(f"FAILED to list packages: {e}")
```

## Step 1: Discover Remote System Information

First, execute this code on the remote to gather system information:

```python
import sys
import platform
import sysconfig

info = {
    "python_version": sys.version,
    "python_version_tuple": tuple(sys.version_info[:3]),
    "platform": sys.platform,
    "machine": platform.machine(),
    "platform_full": platform.platform(),
    "implementation": platform.python_implementation(),
    "abi": sysconfig.get_config_var("SOABI"),
}
print(info)
```

Example output:
```python
{
    "python_version": "3.11.5 (main, ...)",
    "python_version_tuple": (3, 11, 5),
    "platform": "linux",
    "machine": "x86_64",
    "platform_full": "Linux-5.15.0-91-generic-x86_64-with-glibc2.35",
    "implementation": "CPython",
    "abi": "cpython-311-x86_64-linux-gnu"
}
```

## Step 2: Download Wheels Locally

Use pip to download wheels for the target platform:

```python
import subprocess
import sys
import os

# Remote system info from Step 1
remote_platform = "manylinux2014_x86_64"  # For Linux x86_64
remote_python = "311"  # Python 3.11
remote_impl = "cp"  # CPython

# Package to install
package = "requests"

# Create download directory
download_dir = "./wheels_to_transfer"
os.makedirs(download_dir, exist_ok=True)

# Download wheels for the target platform
subprocess.check_call([
    sys.executable, "-m", "pip", "download",
    "--dest", download_dir,
    "--platform", remote_platform,
    "--python-version", remote_python,
    "--implementation", remote_impl,
    "--only-binary", ":all:",  # Only download wheels, no source
    package
])
```

### Platform Tags Reference

Common platform tags for `--platform`:
- **Linux x86_64**: `manylinux2014_x86_64`, `manylinux_2_17_x86_64`, `linux_x86_64`
- **Linux aarch64**: `manylinux2014_aarch64`, `manylinux_2_17_aarch64`
- **Windows x64**: `win_amd64`
- **Windows x86**: `win32`
- **macOS x86_64**: `macosx_10_9_x86_64`, `macosx_11_0_x86_64`
- **macOS ARM64**: `macosx_11_0_arm64`

For pure Python packages, use `any`:
```python
subprocess.check_call([
    sys.executable, "-m", "pip", "download",
    "--dest", download_dir,
    "--platform", "any",
    "--only-binary", ":all:",
    package
])
```

### Handling Packages with No Wheels

If a package has no pre-built wheels, you must build it locally for the target platform:

```python
# Allow source distributions (will try to build)
subprocess.check_call([
    sys.executable, "-m", "pip", "download",
    "--dest", download_dir,
    "--platform", remote_platform,
    "--python-version", remote_python,
    package
])
```

**Warning**: Building wheels for a different platform requires cross-compilation tools. Consider using Docker to build for the target platform:

```bash
# Example: Build wheels in a Linux container for Linux target
docker run --rm -v $(pwd)/wheels_to_transfer:/wheels python:3.11-slim bash -c "pip download --dest /wheels requests"
```

## Step 3: Transfer Wheels to Remote

Transfer wheel files via RPC using base64 encoding:

### Local: Read and Encode Wheels

```python
import os
import base64

def encode_wheel_for_transfer(wheel_path):
    """Read wheel file and encode as base64 string."""
    with open(wheel_path, "rb") as f:
        wheel_bytes = f.read()
    return base64.b64encode(wheel_bytes).decode("ascii")

def prepare_wheels_for_transfer(wheels_dir):
    """Prepare all wheels in directory for transfer."""
    wheels = {}
    for filename in os.listdir(wheels_dir):
        if filename.endswith(".whl"):
            filepath = os.path.join(wheels_dir, filename)
            encoded = encode_wheel_for_transfer(filepath)
            wheels[filename] = encoded
            print(f"Encoded {filename}: {len(encoded)} chars")
    return wheels

# Prepare wheels
wheels_to_send = prepare_wheels_for_transfer("./wheels_to_transfer")
```

### Remote: Decode and Write Wheels

Execute this on the remote system:

```python
import base64
import os

def write_wheel_from_transfer(filename, encoded_data, dest_dir="/tmp/wheels"):
    """Decode and write wheel file to remote filesystem."""
    os.makedirs(dest_dir, exist_ok=True)
    wheel_bytes = base64.b64decode(encoded_data)
    filepath = os.path.join(dest_dir, filename)
    with open(filepath, "wb") as f:
        f.write(wheel_bytes)
    return filepath

# Receive encoded wheels and write them
# (This data would come from your RPC call)
dest_dir = "/tmp/wheels"
for filename, encoded_data in received_wheels.items():
    path = write_wheel_from_transfer(filename, encoded_data, dest_dir)
    print(f"Written {filename} to {path}")
```

### Handling Large Wheels

For large wheel files, transfer in chunks to avoid memory issues:

```python
# Local: Chunked encoding
def encode_wheel_chunked(wheel_path, chunk_size=1024*1024):
    """Encode wheel in chunks. Yields (chunk_index, encoded_chunk)."""
    with open(wheel_path, "rb") as f:
        chunk_index = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            encoded_chunk = base64.b64encode(chunk).decode("ascii")
            yield chunk_index, encoded_chunk
            chunk_index += 1

# Remote: Chunked decoding
def write_wheel_chunked(filename, chunks, dest_dir="/tmp/wheels"):
    """Write wheel from chunks. chunks is list of (index, encoded_data)."""
    os.makedirs(dest_dir, exist_ok=True)
    filepath = os.path.join(dest_dir, filename)

    # Sort by index
    chunks.sort(key=lambda x: x[0])

    with open(filepath, "wb") as f:
        for _, encoded_chunk in chunks:
            chunk_bytes = base64.b64decode(encoded_chunk)
            f.write(chunk_bytes)
    return filepath
```

## Step 4: Install Wheels on Remote

Execute this on the remote system:

```python
import subprocess
import sys
import os

def install_wheels_from_directory(wheels_dir="/tmp/wheels"):
    """Install all wheels in directory."""
    wheel_files = [
        os.path.join(wheels_dir, f)
        for f in os.listdir(wheels_dir)
        if f.endswith(".whl")
    ]

    if not wheel_files:
        raise ValueError(f"No wheels found in {wheels_dir}")

    # Install all wheels
    subprocess.check_call([
        sys.executable, "-m", "pip", "install",
        "--no-index",  # Don't use PyPI
        "--find-links", wheels_dir,  # Find dependencies in this directory
        *wheel_files
    ])

# Install
install_wheels_from_directory("/tmp/wheels")
```

### Install Specific Package

If you only want to install a specific package (and pip will find its dependencies in the same directory):

```python
import subprocess
import sys

def install_package_from_wheels(package_name, wheels_dir="/tmp/wheels"):
    """Install package using wheels in directory."""
    subprocess.check_call([
        sys.executable, "-m", "pip", "install",
        "--no-index",
        "--find-links", wheels_dir,
        package_name
    ])

install_package_from_wheels("requests", "/tmp/wheels")
```

## Complete End-to-End Example

### Local Machine (Internet-Connected)

```python
import subprocess
import sys
import os
import base64

def download_wheels_for_remote(package, remote_info, download_dir="./wheels"):
    """Download wheels for remote platform."""
    os.makedirs(download_dir, exist_ok=True)

    # Map platform info to pip parameters
    platform_map = {
        "linux": "manylinux2014_x86_64",
        "win32": "win_amd64",
        "darwin": "macosx_11_0_x86_64"
    }

    platform = platform_map.get(remote_info["platform"], "any")
    python_version = f"{remote_info['python_version_tuple'][0]}{remote_info['python_version_tuple'][1]}"

    subprocess.check_call([
        sys.executable, "-m", "pip", "download",
        "--dest", download_dir,
        "--platform", platform,
        "--python-version", python_version,
        "--implementation", "cp",
        "--only-binary", ":all:",
        package
    ])

    print(f"Downloaded wheels to {download_dir}")

def encode_wheels(wheels_dir="./wheels"):
    """Encode all wheels as base64."""
    wheels = {}
    for filename in os.listdir(wheels_dir):
        if filename.endswith(".whl"):
            filepath = os.path.join(wheels_dir, filename)
            with open(filepath, "rb") as f:
                wheel_bytes = f.read()
            encoded = base64.b64encode(wheel_bytes).decode("ascii")
            wheels[filename] = encoded
            print(f"Encoded {filename}: {len(wheel_bytes)} bytes -> {len(encoded)} chars")
    return wheels

# Usage
remote_info = {
    "platform": "linux",
    "python_version_tuple": (3, 11, 5)
}

download_wheels_for_remote("requests", remote_info)
encoded_wheels = encode_wheels("./wheels")

# Now send encoded_wheels to remote via your RPC mechanism
```

### Remote Machine (Offline)

```python
import base64
import os
import subprocess
import sys

def receive_and_install_wheels(encoded_wheels, wheels_dir="/tmp/pip_wheels"):
    """Receive encoded wheels, write to disk, and install."""
    # Create directory
    os.makedirs(wheels_dir, exist_ok=True)

    # Write all wheels
    wheel_paths = []
    for filename, encoded_data in encoded_wheels.items():
        wheel_bytes = base64.b64decode(encoded_data)
        filepath = os.path.join(wheels_dir, filename)
        with open(filepath, "wb") as f:
            f.write(wheel_bytes)
        wheel_paths.append(filepath)
        print(f"Written {filename} ({len(wheel_bytes)} bytes)")

    # Install
    subprocess.check_call([
        sys.executable, "-m", "pip", "install",
        "--no-index",
        "--find-links", wheels_dir,
        *wheel_paths
    ])

    print(f"Successfully installed {len(wheel_paths)} packages")

# Usage (encoded_wheels received from local via RPC)
receive_and_install_wheels(encoded_wheels)
```

## Critical Caveats

### 0. No pip on Remote (CRITICAL)

**Issue**: Remote Python may not include pip at all (minimal installations, embedded Python, custom builds).

```python
# Remote check fails
import pip  # ImportError: No module named 'pip'

# Common in:
# - Embedded Python (python-embed-*.zip on Windows)
# - Minimal Docker images (python:3.11-slim without pip)
# - Custom-built Python with --without-ensurepip
# - Embedded systems (Raspberry Pi, IoT devices)
# - Application-bundled Python (PyInstaller, py2exe)
```

**Solution**: See "Step 0: Bootstrap pip on Remote" for complete bootstrapping guide.

**Quick bootstrap options (in order of preference):**

1. **ensurepip** (if available):
   ```python
   import subprocess, sys
   subprocess.check_call([sys.executable, "-m", "ensurepip", "--upgrade"])
   ```

2. **get-pip.py** (transfer from internet-connected machine):
   ```python
   # Local: Download and encode
   import urllib.request, base64
   script = urllib.request.urlopen("https://bootstrap.pypa.io/get-pip.py").read()
   encoded = base64.b64encode(script).decode("ascii")

   # Remote: Decode and run
   import base64, subprocess, sys
   with open("/tmp/get-pip.py", "wb") as f:
       f.write(base64.b64decode(encoded))
   subprocess.check_call([sys.executable, "/tmp/get-pip.py"])
   ```

3. **Manual wheel installation** (extract pip wheel to site-packages):
   ```python
   # See Option 3 and Option 4 in Step 0
   ```

### 1. Platform Compatibility

**Issue**: Downloaded wheels must exactly match remote platform.

```python
# Bad: Wrong platform
# Local: Windows, Remote: Linux
# Downloads Windows wheels, fails on Linux

# Solution: Always verify remote platform first
import platform
print(f"Remote platform: {platform.platform()}")
```

### 2. Python Version Mismatch

**Issue**: Wheels are Python version-specific (especially with C extensions).

```python
# Bad: Python 3.11 wheels on Python 3.9 remote
# Will fail with "not compatible" error

# Solution: Match major.minor version exactly
remote_version = sys.version_info[:2]  # e.g., (3, 11)
```

### 3. Dependency Resolution

**Issue**: pip download may not get all dependencies if platform differs.

```python
# Problem: Some dependencies are platform-specific
# pip download on Windows may miss Linux-only dependencies

# Solution: Download with --platform to force target platform
subprocess.check_call([
    sys.executable, "-m", "pip", "download",
    "--platform", "manylinux2014_x86_64",
    "--python-version", "311",
    "--implementation", "cp",
    "--only-binary", ":all:",
    "package"
])
```

### 4. Binary vs Source Distributions

**Issue**: Some packages have no wheels, only source distributions (.tar.gz, .zip).

```python
# If no wheel exists, pip download gets source
# Source requires compilation on remote (may lack compiler)

# Solution 1: Build wheel locally for target platform (requires Docker/VM)
# Solution 2: Accept source and ensure remote has build tools
subprocess.check_call([
    sys.executable, "-m", "pip", "download",
    "--dest", download_dir,
    # Remove --only-binary to allow source
    package
])
```

### 5. Large Wheel Files

**Issue**: Some wheels are very large (e.g., PyTorch: 800+ MB).

```python
# Base64 encoding increases size by ~33%
# 800 MB wheel -> 1.06 GB encoded string

# Solution: Use chunked transfer
def transfer_large_wheel_chunked(filename, encoded_chunks):
    """Transfer and reassemble large wheel."""
    filepath = f"/tmp/wheels/{filename}"
    os.makedirs("/tmp/wheels", exist_ok=True)

    with open(filepath, "wb") as f:
        for chunk in encoded_chunks:
            f.write(base64.b64decode(chunk))

    return filepath
```

### 6. Filesystem Permissions

**Issue**: Remote filesystem may have permission restrictions.

```python
# May fail: /usr/local/ not writable
install_wheels("/usr/local/wheels")

# Solution: Use user-writable location
install_wheels("/tmp/wheels")

# Or install to user site-packages
subprocess.check_call([
    sys.executable, "-m", "pip", "install",
    "--user",
    "--no-index",
    "--find-links", wheels_dir,
    package
])
```

### 7. Existing Package Conflicts

**Issue**: Remote may have conflicting package versions.

```python
# Remote has requests==2.25.0
# Trying to install requests==2.31.0 with dependencies

# Solution: Use --force-reinstall or --upgrade
subprocess.check_call([
    sys.executable, "-m", "pip", "install",
    "--force-reinstall",
    "--no-index",
    "--find-links", wheels_dir,
    package
])
```

### 8. ABI Compatibility

**Issue**: Wheels are ABI-specific (especially Linux).

```python
# Problem: manylinux2014 wheel on older glibc system
# May fail with "version GLIBC_2.17 not found"

# Solution: Download oldest compatible manylinux
# manylinux1 (old) < manylinux2010 < manylinux2014 < manylinux_2_17 (new)
subprocess.check_call([
    sys.executable, "-m", "pip", "download",
    "--platform", "manylinux2010_x86_64",  # Older, more compatible
    # ...
])
```

### 9. Transfer Encoding Issues

**Issue**: Base64 encoding may have line breaks or encoding issues.

```python
# Bad: Base64 with line breaks
encoded = base64.b64encode(data).decode("ascii")
# May have \n characters if data is large

# Solution: Ensure no line breaks
encoded = base64.b64encode(data).decode("ascii").replace("\n", "")

# Or use urlsafe encoding
encoded = base64.urlsafe_b64encode(data).decode("ascii")
```

### 10. RPC Size Limits

**Issue**: Your RPC mechanism may have message size limits.

```python
# Problem: 100 MB wheel encoded is 133 MB string
# RPC may reject messages > 10 MB

# Solution: Stream in chunks
CHUNK_SIZE = 5 * 1024 * 1024  # 5 MB chunks

def transfer_wheel_in_chunks(wheel_path, send_chunk_func):
    """Transfer wheel using RPC chunk sender."""
    filename = os.path.basename(wheel_path)
    with open(wheel_path, "rb") as f:
        chunk_index = 0
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            encoded = base64.b64encode(chunk).decode("ascii")
            send_chunk_func(filename, chunk_index, encoded)
            chunk_index += 1
```

### 11. Subprocess Restrictions

**Issue**: Remote environment may restrict subprocess execution (sandboxed environments, security policies).

```python
# Fails in restricted environments
import subprocess
subprocess.check_call([sys.executable, "-m", "pip", "install", "package"])
# Error: subprocess execution not allowed

# Common in:
# - Sandboxed Python interpreters
# - Web-based Python shells (Jupyter kernels, online IDEs)
# - Security-hardened systems
# - Embedded systems with no shell
```

**Solution**: Use pure Python wheel installation (no subprocess):

```python
import zipfile
import sys
import os
import site

def install_wheel_pure_python(wheel_path):
    """Install a wheel without subprocess or pip."""
    # Get installation directory
    site_packages = site.getsitepackages()[0]

    # Extract wheel (wheels are ZIP files)
    with zipfile.ZipFile(wheel_path, "r") as whl:
        for member in whl.namelist():
            # Skip metadata
            if ".dist-info/" in member or ".data/" in member:
                continue

            target = os.path.join(site_packages, member)

            if member.endswith("/"):
                os.makedirs(target, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with whl.open(member) as src:
                    with open(target, "wb") as dst:
                        dst.write(src.read())

    print(f"Installed {os.path.basename(wheel_path)}")

# Install all wheels in directory
wheels_dir = "/tmp/wheels"
for filename in os.listdir(wheels_dir):
    if filename.endswith(".whl"):
        install_wheel_pure_python(os.path.join(wheels_dir, filename))
```

**Caveat**: This approach skips:
- Entry point scripts (command-line tools won't be installed)
- .data directory processing (may miss data files)
- Dependency resolution (install dependencies manually in correct order)

### 12. Standard Library Missing Modules

**Issue**: Minimal Python builds may exclude standard library modules.

```python
# May fail on minimal builds
import zipfile  # ImportError: No module named 'zipfile'
import subprocess  # ImportError: No module named 'subprocess'
import ssl  # ImportError: No module named '_ssl'

# Embedded Python on Windows often excludes:
# - zipfile, gzip, bz2 (compression)
# - ssl, urllib (networking)
# - sqlite3, json (data)
```

**Solution 1**: Transfer missing modules from local Python:

```python
# Local: Find and encode missing module
import sys
import os
import base64

def find_module_file(module_name):
    """Find the .py file for a module."""
    module = __import__(module_name)
    if hasattr(module, "__file__"):
        return module.__file__
    return None

# Find and encode
module_file = find_module_file("zipfile")
with open(module_file, "rb") as f:
    module_bytes = f.read()
encoded = base64.b64encode(module_bytes).decode("ascii")

# Remote: Decode and save to sys.path
import base64
import sys
import os

module_bytes = base64.b64decode(encoded)
dest_path = os.path.join(sys.path[0], "zipfile.py")
with open(dest_path, "wb") as f:
    f.write(module_bytes)

# Now can import
import zipfile
```

**Solution 2**: Use built-in alternatives:

```python
# Instead of subprocess, use os.system (less reliable)
import os
os.system(f"{sys.executable} -m pip install package")

# Instead of zipfile, use tar (if available)
import tarfile

# Instead of json, use eval/ast.literal_eval (UNSAFE for untrusted data)
import ast
data = ast.literal_eval('{"key": "value"}')
```

## Advanced: Building Wheels for Target Platform

If you need to build wheels for a different platform:

### Using Docker

```bash
# Build Linux wheels from any platform
docker run --rm -v $(pwd)/wheels:/wheels python:3.11-slim bash -c "
  pip install build &&
  pip download --dest /wheels --platform manylinux2014_x86_64 requests
"
```

### Using Virtual Machine

```python
# Inside VM matching target platform
import subprocess
import sys

subprocess.check_call([
    sys.executable, "-m", "pip", "wheel",
    "--wheel-dir", "./wheels",
    "package-name"
])
```

## Verification

After installation on remote, verify:

```python
import subprocess
import sys

# Check installed packages
result = subprocess.run(
    [sys.executable, "-m", "pip", "list"],
    capture_output=True,
    text=True
)
print(result.stdout)

# Test import
try:
    import requests
    print(f"requests version: {requests.__version__}")
    print(f"requests location: {requests.__file__}")
except ImportError as e:
    print(f"Failed to import: {e}")
```

## References

- [pip download documentation](https://pip.pypa.io/en/stable/cli/pip_download/)
- [PEP 427 - Wheel Binary Package Format](https://www.python.org/dev/peps/pep-0427/)
- [PEP 425 - Compatibility Tags](https://www.python.org/dev/peps/pep-0425/)
- [PEP 600 - manylinux Platform Tags](https://www.python.org/dev/peps/pep-0600/)
- [Python Packaging User Guide - Platform Compatibility](https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/)
