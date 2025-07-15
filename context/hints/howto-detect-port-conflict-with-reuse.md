# How to Detect Port Conflicts with SO_REUSEADDR

## Overview

This guide explains how to reliably detect port conflicts when using Python sockets, particularly when dealing with `SO_REUSEADDR` across different platforms. This is crucial for server applications that need to restart or detect if another instance is already running.

## The Problem with SO_REUSEADDR

### What SO_REUSEADDR Does

- **Primary Purpose**: Allows reusing a socket address that's in `TIME_WAIT` state
- **Side Effect**: On some platforms, it can allow binding to ports actively used by other applications
- **Platform Differences**: Behavior varies significantly between operating systems

### Platform-Specific Behavior

#### Linux/Unix Systems
```python
# SO_REUSEADDR on Linux mainly allows:
# 1. Reuse of ports in TIME_WAIT state
# 2. Multiple sockets binding to same port with different interfaces
# 3. Generally safer behavior - less likely to bind to active ports
```

#### Windows Systems
```python
# SO_REUSEADDR on Windows is more permissive:
# 1. Can bind to ports actively used by other applications
# 2. Allows "hijacking" of existing connections
# 3. Less reliable for port conflict detection
```

#### macOS Systems
```python
# SO_REUSEADDR on macOS:
# 1. Similar to Linux but with some variations
# 2. Generally safer than Windows
# 3. Respects active connections better than Windows
```

## Detection Methods

### Method 1: Avoid SO_REUSEADDR (Recommended)

**Most Reliable Approach**

```python
def start_server_safe(host, port):
    """Start server without SO_REUSEADDR for reliable port conflict detection."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # DO NOT set SO_REUSEADDR
        sock.bind((host, port))
        sock.listen(5)
        return sock
    except OSError as e:
        if e.errno == errno.EADDRINUSE:
            raise RuntimeError(f"Port {port} is already in use")
        raise
```

**Pros:**
- ✅ Cross-platform consistent behavior
- ✅ Reliable port conflict detection
- ✅ Clear error messages
- ✅ No false positives

**Cons:**
- ❌ Cannot restart quickly (TIME_WAIT delay)
- ❌ May fail on rapid restart scenarios

### Method 2: Pre-check Before Using SO_REUSEADDR

**For Rapid Restart Scenarios**

```python
import socket
import errno

def is_port_actually_in_use(host, port, timeout=1):
    """
    Check if port is actually in use by another application.
    Returns True if port is in use, False if available.
    """
    
    # Method 1: Try to connect to the port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        result = sock.connect_ex((host, port))
        if result == 0:
            return True  # Connection successful = port in use
    except socket.error:
        pass
    finally:
        sock.close()
    
    # Method 2: Try to bind without SO_REUSEADDR
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((host, port))
        return False  # Bind successful = port available
    except OSError as e:
        if e.errno == errno.EADDRINUSE:
            return True  # Port is in use
        return False  # Other error, assume available
    finally:
        sock.close()

def start_server_with_reuse_check(host, port):
    """Start server with SO_REUSEADDR after checking for conflicts."""
    
    # First check if port is actually in use
    if is_port_actually_in_use(host, port):
        raise RuntimeError(f"Port {port} is already in use by another application")
    
    # Now create socket with SO_REUSEADDR
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        sock.bind((host, port))
        sock.listen(5)
        return sock
    except OSError as e:
        if e.errno == errno.EADDRINUSE:
            raise RuntimeError(f"Port {port} is already in use")
        raise
```

### Method 3: Platform-Specific Detection

```python
import platform

def detect_port_conflict_platform_aware(host, port):
    """Platform-aware port conflict detection."""
    
    system = platform.system().lower()
    
    if system == "windows":
        # Windows: More aggressive checking needed
        return _check_port_windows(host, port)
    elif system in ["linux", "darwin"]:
        # Linux/macOS: Standard approach works well
        return _check_port_unix(host, port)
    else:
        # Other systems: Use conservative approach
        return _check_port_conservative(host, port)

def _check_port_windows(host, port):
    """Windows-specific port checking."""
    # Try connection first (more reliable on Windows)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        result = sock.connect_ex((host, port))
        return result == 0
    finally:
        sock.close()

def _check_port_unix(host, port):
    """Unix/Linux/macOS port checking."""
    # Bind test works reliably
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((host, port))
        return False
    except OSError as e:
        return e.errno == errno.EADDRINUSE
    finally:
        sock.close()

def _check_port_conservative(host, port):
    """Conservative approach for unknown systems."""
    # Use both methods for maximum reliability
    return (_check_port_windows(host, port) or 
            _check_port_unix(host, port))
```

## Server Restart Scenarios

### Scenario 1: Graceful Restart

```python
class RestartableServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None
        self.use_reuse_addr = False
    
    def start(self, allow_reuse=False):
        """Start server with optional SO_REUSEADDR for restarts."""
        
        if not allow_reuse:
            # First attempt: No SO_REUSEADDR (most reliable)
            try:
                self.sock = self._create_socket(use_reuse=False)
                self.use_reuse_addr = False
                return True
            except RuntimeError as e:
                if "already in use" in str(e):
                    print(f"Port {self.port} in use, checking if it's our old instance...")
                    # Could be our old instance in TIME_WAIT
                    if allow_reuse:
                        # Try with SO_REUSEADDR after verification
                        return self._try_reuse_start()
                raise
        else:
            return self._try_reuse_start()
    
    def _try_reuse_start(self):
        """Try starting with SO_REUSEADDR after verification."""
        
        # Check if port is actually in use by another app
        if is_port_actually_in_use(self.host, self.port):
            raise RuntimeError(
                f"Port {self.port} is actively used by another application"
            )
        
        # Safe to use SO_REUSEADDR
        try:
            self.sock = self._create_socket(use_reuse=True)
            self.use_reuse_addr = True
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to start with SO_REUSEADDR: {e}")
    
    def _create_socket(self, use_reuse=False):
        """Create and bind socket."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        if use_reuse:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            sock.bind((self.host, self.port))
            sock.listen(5)
            return sock
        except OSError as e:
            sock.close()
            if e.errno == errno.EADDRINUSE:
                raise RuntimeError(f"Port {self.port} is already in use")
            raise
    
    def stop(self):
        """Stop server cleanly."""
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except:
                pass
            self.sock.close()
            self.sock = None
    
    def restart(self):
        """Restart server with automatic conflict handling."""
        self.stop()
        
        # Wait a moment for cleanup
        time.sleep(0.1)
        
        # Try without SO_REUSEADDR first
        try:
            return self.start(allow_reuse=False)
        except RuntimeError:
            # If that fails, try with SO_REUSEADDR
            print("Retrying with SO_REUSEADDR...")
            return self.start(allow_reuse=True)
```

### Scenario 2: Development/Testing Rapid Restart

```python
def start_dev_server(host, port, max_retries=3):
    """Start server for development with rapid restart capability."""
    
    for attempt in range(max_retries):
        try:
            if attempt == 0:
                # First attempt: Clean start without SO_REUSEADDR
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind((host, port))
                sock.listen(5)
                print(f"Server started on {host}:{port} (clean start)")
                return sock
            else:
                # Subsequent attempts: Check and use SO_REUSEADDR
                if is_port_actually_in_use(host, port):
                    print(f"Port {port} is in use by another app, waiting...")
                    time.sleep(1)
                    continue
                
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind((host, port))
                sock.listen(5)
                print(f"Server started on {host}:{port} (with SO_REUSEADDR)")
                return sock
                
        except OSError as e:
            if e.errno == errno.EADDRINUSE:
                print(f"Attempt {attempt + 1}: Port {port} in use, retrying...")
                time.sleep(1)
                continue
            raise
    
    raise RuntimeError(f"Failed to start server after {max_retries} attempts")
```

## Best Practices

### 1. Choose the Right Approach for Your Use Case

```python
# Production servers (reliability first)
def production_server():
    # Don't use SO_REUSEADDR - clear error messages
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, port))  # Will fail cleanly if port in use
    return sock

# Development servers (convenience first)
def development_server():
    # Use SO_REUSEADDR with pre-checking
    if is_port_actually_in_use(host, port):
        raise RuntimeError("Port in use by another app")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    return sock
```

### 2. Handle Platform Differences

```python
def create_server_socket(host, port, allow_reuse=None):
    """Create server socket with platform-appropriate settings."""
    
    if allow_reuse is None:
        # Auto-detect based on platform
        system = platform.system().lower()
        allow_reuse = system in ["linux", "darwin"]  # Safer on Unix
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    if allow_reuse:
        # Pre-check on Windows for safety
        if platform.system().lower() == "windows":
            if is_port_actually_in_use(host, port):
                sock.close()
                raise RuntimeError(f"Port {port} in use")
        
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    sock.bind((host, port))
    sock.listen(5)
    return sock
```

### 3. Comprehensive Error Handling

```python
def robust_server_start(host, port):
    """Robust server startup with comprehensive error handling."""
    
    try:
        # Method 1: Clean start (most reliable)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((host, port))
        sock.listen(5)
        return sock, "clean_start"
        
    except OSError as e:
        if e.errno != errno.EADDRINUSE:
            raise  # Other error, re-raise
        
        # Port in use - investigate further
        print(f"Port {port} appears to be in use, investigating...")
        
        # Check if it's actually in use
        if is_port_actually_in_use(host, port):
            # Find out what's using it (platform-specific)
            process_info = get_port_process_info(port)
            raise RuntimeError(
                f"Port {port} is actively used by: {process_info}"
            )
        
        # Might be TIME_WAIT - try with SO_REUSEADDR
        print("Port might be in TIME_WAIT state, trying SO_REUSEADDR...")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((host, port))
            sock.listen(5)
            return sock, "reuse_addr"
        except OSError:
            raise RuntimeError(f"Could not bind to port {port}")

def get_port_process_info(port):
    """Get information about process using a port (platform-specific)."""
    import subprocess
    
    system = platform.system().lower()
    
    try:
        if system == "windows":
            result = subprocess.run(
                ["netstat", "-ano", "-p", "TCP"], 
                capture_output=True, text=True
            )
            # Parse netstat output for port
            for line in result.stdout.split('\n'):
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        return f"PID {parts[-1]}"
        
        elif system in ["linux", "darwin"]:
            result = subprocess.run(
                ["lsof", "-i", f":{port}"], 
                capture_output=True, text=True
            )
            if result.stdout:
                lines = result.stdout.split('\n')
                if len(lines) > 1:
                    return lines[1].split()[0]  # Process name
        
    except Exception:
        pass
    
    return "unknown process"
```

## Current Implementation Analysis

Your current implementation in `BldRemoteMCPServer.start()` is **optimal** for production use:

```python
# Your current approach (RECOMMENDED)
self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Note: Removed SO_REUSEADDR to ensure proper port conflict detection
# Multiple instances should fail when trying to bind to the same port
self.server_socket.bind((self.host, self.port))
```

**Why this is correct:**
- ✅ Reliable cross-platform port conflict detection
- ✅ Clear error messages when port is in use
- ✅ No false positives from SO_REUSEADDR behavior
- ✅ Prevents accidental multiple instances

## Recommendations

1. **Keep your current implementation** for production reliability
2. **Add a development mode** that uses SO_REUSEADDR with pre-checking
3. **Consider adding restart logic** for server management
4. **Document platform differences** for your team

```python
# Example addition to your config
class BldRemoteMCPConfig:
    # ... existing config ...
    
    # Development mode settings
    DEVELOPMENT_MODE = os.getenv('BLD_REMOTE_DEV_MODE', 'false').lower() == 'true'
    ALLOW_RAPID_RESTART = DEVELOPMENT_MODE
    
    # Platform-specific settings
    PLATFORM_SYSTEM = platform.system().lower()
    USE_AGGRESSIVE_PORT_CHECK = PLATFORM_SYSTEM == "windows"
```

This approach gives you the best of both worlds: reliability in production and convenience in development.
