"""
Blender MCP Client for communication with BLD Remote MCP service.
"""

import json
import socket
import os
import signal
import platform
import base64
from typing import Dict, Any, Optional, cast

from .exceptions import (
    BlenderMCPError,
    BlenderConnectionError,
    BlenderCommandError,
    BlenderTimeoutError,
)


class BlenderMCPClient:
    """
    Client for communicating with BLD Remote MCP service.

    Provides low-level communication with the BLD Remote MCP service running on port 6688.
    Higher-level functionality should use BlenderSceneManager or BlenderAssetManager.

    Parameters
    ----------
    host : str, optional
        Server hostname. Auto-detects Docker environment if None.
    port : int, default 6688
        Server port (BLD Remote MCP default).
    timeout : float, default 30.0
        Command timeout in seconds.

    Attributes
    ----------
    host : str
        Server hostname.
    port : int
        Server port.
    timeout : float
        Command timeout in seconds.
    """

    def __init__(
        self, host: Optional[str] = None, port: int = 6688, timeout: float = 30.0
    ):
        """
        Initialize Blender MCP client.

        Parameters
        ----------
        host : str, optional
            Server hostname or URL. Can be:
            - None (auto-detects environment)
            - hostname (e.g., "localhost")
            - URL with or without http:// prefix (e.g., "http://localhost:6688" or "localhost:6688")
        port : int, default 6688
            Server port (ignored if host contains URL with port).
        timeout : float, default 30.0
            Command timeout in seconds.
        """
        if host is None:
            # Auto-detect environment - check for Docker in a cross-platform way
            in_docker = (
                os.path.exists("/.dockerenv") or  # Linux Docker containers
                os.path.exists("/proc/1/cgroup") and 
                any("docker" in line for line in open("/proc/1/cgroup").readlines() if os.path.exists("/proc/1/cgroup")) or
                os.environ.get("DOCKER_CONTAINER") == "true"  # Cross-platform env var
            )
            self.host = "host.docker.internal" if in_docker else "localhost"
            self.port = port
        else:
            # Check if host looks like a URL (contains : or http://)
            if ":" in host or host.startswith("http://"):
                # Parse as URL
                url_string = host if host.startswith("http://") else "http://" + host
                try:
                    from urllib.parse import urlparse

                    parsed = urlparse(url_string)

                    if not parsed.hostname:
                        raise ValueError("Invalid URL: no hostname found")

                    self.host = parsed.hostname
                    self.port = parsed.port if parsed.port is not None else port

                except Exception as e:
                    raise ValueError(f"Invalid URL format '{host}': {str(e)}")
            else:
                # Treat as simple hostname
                self.host = host
                self.port = port

        self.timeout = timeout

    @classmethod
    def from_url(cls, url_string: str, timeout: float = 30.0) -> "BlenderMCPClient":
        """
        Create BlenderMCPClient from URL string.

        Parameters
        ----------
        url_string : str
            URL string (e.g., "http://localhost:6688" or "localhost:6688").
            If URL doesn't start with "http://", it will be added automatically.
        timeout : float, default 30.0
            Command timeout in seconds.

        Returns
        -------
        BlenderMCPClient
            New BlenderMCPClient instance.

        Raises
        ------
        ValueError
            If URL format is invalid.
        """
        # Add http:// prefix if not present
        if not url_string.startswith("http://"):
            url_string = "http://" + url_string

        try:
            from urllib.parse import urlparse

            parsed = urlparse(url_string)

            if not parsed.hostname:
                raise ValueError("Invalid URL: no hostname found")

            host = parsed.hostname
            port = parsed.port if parsed.port is not None else 6688

            return cls(host=host, port=port, timeout=timeout)

        except Exception as e:
            raise ValueError(f"Invalid URL format '{url_string}': {str(e)}")

    def _receive_full_response(
        self, sock: socket.socket, buffer_size: int = 8192
    ) -> bytes:
        """
        Receive the complete response, potentially in multiple chunks.

        Parameters
        ----------
        sock : socket.socket
            Socket to receive from.
        buffer_size : int, default 8192
            Buffer size for receiving chunks.

        Returns
        -------
        bytes
            Complete response data.

        Raises
        ------
        BlenderConnectionError
            If connection fails or no data received.
        """
        # BLD Remote MCP sends complete JSON responses in a single packet
        # So we can simplify this to just receive once
        try:
            data = sock.recv(buffer_size)
            if not data:
                raise BlenderConnectionError(
                    "Connection closed before receiving any data"
                )

            # Validate that it's valid JSON
            try:
                json.loads(data.decode("utf-8"))
                return data
            except json.JSONDecodeError as e:
                raise BlenderConnectionError(f"Invalid JSON response: {str(e)}")

        except socket.timeout:
            raise BlenderConnectionError("Timeout while receiving response")
        except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
            raise BlenderConnectionError(f"Connection error while receiving: {str(e)}")
        except Exception as e:
            if isinstance(e, BlenderConnectionError):
                raise
            raise BlenderConnectionError(f"Unexpected error while receiving: {str(e)}")

    def execute_command(
        self, command_type: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a command via BLD Remote MCP service.

        Parameters
        ----------
        command_type : str
            MCP command type (e.g., "get_scene_info", "execute_code").
        params : dict, optional
            Command parameters dictionary.

        Returns
        -------
        dict
            Response dictionary from BLD Remote MCP service.

        Raises
        ------
        BlenderMCPError
            If command fails or communication error occurs.
        BlenderTimeoutError
            If command times out.
        BlenderConnectionError
            If connection fails.
        BlenderCommandError
            If command execution fails in Blender.
        """
        if params is None:
            params = {}

        command = {"type": command_type, "params": params}

        sock = None
        try:
            # Create TCP socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)

            try:
                sock.connect((self.host, self.port))
            except socket.timeout:
                raise BlenderTimeoutError(
                    f"Connection timeout after {self.timeout} seconds"
                )
            except socket.error as e:
                raise BlenderConnectionError(
                    f"Failed to connect to {self.host}:{self.port}: {str(e)}"
                )

            # Send command as JSON
            command_json = json.dumps(command).encode("utf-8")
            try:
                sock.sendall(command_json)
            except socket.timeout:
                raise BlenderTimeoutError(f"Send timeout after {self.timeout} seconds")
            except socket.error as e:
                raise BlenderConnectionError(f"Failed to send command: {str(e)}")

            # Receive response
            try:
                response_data = self._receive_full_response(sock)
                response = json.loads(response_data.decode("utf-8"))
            except socket.timeout:
                raise BlenderTimeoutError(
                    f"Receive timeout after {self.timeout} seconds"
                )
            except BlenderConnectionError:
                raise
            except json.JSONDecodeError as e:
                raise BlenderMCPError(f"Invalid JSON response: {str(e)}")

            # Check for errors in response
            if response.get("status") == "error":
                error_msg = response.get("message", "Unknown error")
                raise BlenderCommandError(f"Blender command failed: {error_msg}")

            return cast(Dict[str, Any], response)

        except (
            BlenderTimeoutError,
            BlenderConnectionError,
            BlenderCommandError,
            BlenderMCPError,
        ):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            raise BlenderMCPError(
                f"Unexpected error during command execution: {str(e)}"
            )
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass

    def execute_python(self, code: str, send_as_base64: bool = True, return_as_base64: bool = True) -> str:
        """
        Execute Python code in Blender via BLD Remote MCP service.

        Uses base64 encoding by default for reliable cross-platform transmission.
        Users can disable base64 encoding for compatibility with older systems.

        Parameters
        ----------
        code : str
            Python code string to execute.
        send_as_base64 : bool, default True
            If True, encode the code as base64 before sending to avoid formatting issues.
            Recommended for cross-platform robustness.
        return_as_base64 : bool, default True
            If True, request that the result be returned as base64-encoded.
            Recommended for reliable result transmission.

        Returns
        -------
        str
            Execution result or status message.

        Raises
        ------
        BlenderMCPError
            If execution fails.
        """
        # Prepare the code for transmission
        code_to_send = code
        if send_as_base64:
            # Encode the code as base64 to avoid formatting issues
            code_to_send = base64.b64encode(code.encode('utf-8')).decode('ascii')
        
        # Send with base64 flags
        params = {
            "code": code_to_send,
            "code_is_base64": send_as_base64,
            "return_as_base64": return_as_base64
        }
        
        response = self.execute_command("execute_code", params)
        result_data = response.get("result", {})
        
        # Handle base64 decoding if the result is base64-encoded
        if return_as_base64 and result_data.get("result_is_base64", False):
            try:
                # Decode the base64-encoded result
                encoded_result = result_data.get("result", "")
                if encoded_result:
                    output = base64.b64decode(encoded_result.encode('ascii')).decode('utf-8')
                else:
                    output = ""
            except Exception as e:
                # If decoding fails, return the raw result with error info
                output = result_data.get("result", "") + f" [Base64 decode error: {str(e)}]"
        else:
            # Fallback to original behavior for compatibility
            output = result_data.get("result", "")
            if not output:
                output = result_data.get("output", {}).get("stdout", "")
        
        return cast(str, output)

    def get_scene_info(self) -> Dict[str, Any]:
        """
        Get current scene information from Blender.

        Returns
        -------
        dict
            Dictionary with scene information (objects, materials, etc.).

        Raises
        ------
        BlenderMCPError
            If command fails.
        """
        response = self.execute_command("get_scene_info")
        return cast(Dict[str, Any], response.get("result", {}))

    def get_object_info(self, object_name: str) -> Dict[str, Any]:
        """
        Get information about a specific object in Blender.

        Parameters
        ----------
        object_name : str
            Name of the object to query.

        Returns
        -------
        dict
            Dictionary with object information.

        Raises
        ------
        BlenderMCPError
            If command fails.
        """
        response = self.execute_command("get_object_info", {"name": object_name})
        return cast(Dict[str, Any], response.get("result", {}))

    def take_screenshot(
        self, filepath: str, max_size: int = 1920, format: str = "png"
    ) -> Dict[str, Any]:
        """
        Capture viewport screenshot from Blender.

        Parameters
        ----------
        filepath : str
            Output file path.
        max_size : int, default 1920
            Maximum image dimension in pixels.
        format : str, default "png"
            Image format ("png", "jpg").

        Returns
        -------
        dict
            Dictionary with screenshot info (success, width, height, filepath).

        Raises
        ------
        BlenderMCPError
            If command fails.
        """
        params = {"filepath": filepath, "max_size": max_size, "format": format}
        response = self.execute_command("get_viewport_screenshot", params)
        return cast(Dict[str, Any], response.get("result", {}))

    def test_connection(self) -> bool:
        """
        Test connection to BLD Remote MCP service.

        Returns
        -------
        bool
            True if connection successful, False otherwise.
        """
        try:
            self.get_scene_info()
            return True
        except BlenderMCPError:
            return False

    def get_status(self) -> Dict[str, Any]:
        """
        Get status information from BLD Remote MCP service.

        Returns
        -------
        dict
            Dictionary with service status information.

        Raises
        ------
        BlenderMCPError
            If command fails.
        """
        try:
            # Try to get scene info as a health check
            scene_info = self.get_scene_info()
            return {
                "status": "connected",
                "service": "BLD Remote MCP",
                "host": self.host,
                "port": self.port,
                "timeout": self.timeout,
                "scene_objects": len(scene_info.get("objects", [])),
            }
        except BlenderMCPError as e:
            return {
                "status": "error",
                "service": "BLD Remote MCP",
                "host": self.host,
                "port": self.port,
                "timeout": self.timeout,
                "error": str(e),
            }

    def send_exit_request(self) -> bool:
        """
        Send a request to the BLD_Remote_MCP server to exit gracefully.

        This method sends Python code to raise SystemExit, which will cause
        the MCP server to exit gracefully.

        Returns
        -------
        bool
            True if exit request was sent successfully, False otherwise.

        Raises
        ------
        BlenderMCPError
            If the exit request fails to send.
        """
        try:
            # Send code to raise SystemExit for graceful shutdown
            code = "import sys; sys.exit(0)"
            response = self.execute_command("execute_code", {"code": code})
            return response.get("status") == "success"
        except Exception as e:
            raise BlenderMCPError(f"Failed to send exit request: {str(e)}")

    def get_blender_pid(self) -> int:
        """
        Retrieve the Blender process ID (PID) of the running BLD_Remote_MCP server.

        This is useful for users to know which Blender instance is running the MCP server,
        especially when multiple instances are involved.

        Returns
        -------
        int
            The process ID of the Blender instance running the MCP server.

        Raises
        ------
        BlenderMCPError
            If the PID retrieval fails.
        """
        try:
            # Since BLD Remote MCP doesn't capture print output or return values,
            # we'll write the PID to a temporary file and then read it
            import tempfile
            import time
            
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
            temp_path = temp_file.name
            temp_file.close()
            
            # Use forward slashes for the path in the Python code to ensure cross-platform compatibility
            temp_path_normalized = temp_path.replace('\\', '/')
            
            # Execute code to write PID to temporary file
            code = f"""
import os
import tempfile

# Write PID to temporary file
with open('{temp_path_normalized}', 'w') as f:
    f.write(str(os.getpid()))
"""
            self.execute_command("execute_code", {"code": code})
            
            # Wait a moment for the file to be written
            time.sleep(0.1)
            
            # Read PID from temporary file
            try:
                with open(temp_path, 'r') as f:
                    pid_str = f.read().strip()
                
                # Clean up temporary file
                os.unlink(temp_path)
                
                if pid_str.isdigit():
                    pid = int(pid_str)
                    if pid > 0:
                        return pid
                    else:
                        raise BlenderMCPError(f"Invalid PID value: {pid}")
                else:
                    raise BlenderMCPError(f"Invalid PID format: {pid_str}")
                    
            except FileNotFoundError:
                raise BlenderMCPError("PID file not found - code execution may have failed")
                
        except Exception as e:
            # Clean up temporary file if it exists
            try:
                if 'temp_path' in locals():
                    os.unlink(temp_path)
            except:
                pass
            raise BlenderMCPError(f"Failed to get Blender PID: {str(e)}")

    def kill_blender_process(self) -> bool:
        """
        Kill the Blender process running the BLD_Remote_MCP server.

        This method uses the PID obtained from get_blender_pid() to terminate
        the Blender process, effectively stopping the MCP server. This is a
        forceful way to stop the server and should be used with caution, as
        it does not allow for graceful shutdown procedures.

        Returns
        -------
        bool
            True if the process was killed successfully, False otherwise.

        Raises
        ------
        BlenderMCPError
            If the process termination fails.
        """
        try:
            # Get the Blender PID
            pid = self.get_blender_pid()

            # Try to kill the process - cross-platform approach
            try:
                if platform.system() == "Windows":
                    # Windows doesn't support SIGTERM/SIGKILL, use SIGTERM equivalent
                    os.kill(pid, signal.SIGTERM)  # Windows translates this to TerminateProcess
                else:
                    # Unix-like systems: try graceful termination first
                    os.kill(pid, signal.SIGTERM)
                return True
            except ProcessLookupError:
                # Process already terminated
                return True
            except PermissionError:
                # Try with SIGKILL on Unix systems if SIGTERM fails due to permissions
                if platform.system() != "Windows":
                    try:
                        os.kill(pid, signal.SIGKILL)
                        return True
                    except ProcessLookupError:
                        # Process already terminated
                        return True
                    except Exception as e:
                        raise BlenderMCPError(f"Permission denied and SIGKILL failed: {str(e)}")
                else:
                    # On Windows, if SIGTERM fails with permission error, we can't do much more
                    raise BlenderMCPError(f"Permission denied to terminate process {pid}")
        except Exception as e:
            raise BlenderMCPError(f"Failed to kill Blender process: {str(e)}")
