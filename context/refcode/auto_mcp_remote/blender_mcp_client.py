"""
Raw Blender MCP Client for low-level communication with Blender MCP server.
"""

import json
import socket
import os
from typing import Dict, Any
from .data_types import BlenderMCPError


class BlenderMCPClient:
    """
    Raw Blender MCP client for sending commands to the MCP server.
    
    Provides low-level communication with the Blender MCP server running on port 9876.
    Higher-level functionality should use BlenderAssetManager or BlenderSceneManager.
    
    Parameters
    ----------
    host : str, optional
        Server hostname. Auto-detects Docker environment if None.
    port : int, default 9876
        Server port.
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
    
    def __init__(self, host: str = None, port: int = 9876, timeout: float = 30.0):
        """
        Initialize Blender MCP client.
        
        Parameters
        ----------
        host : str, optional
            Server hostname or URL. Can be:
            - None (auto-detects environment)
            - hostname (e.g., "localhost")
            - URL with or without http:// prefix (e.g., "http://localhost:9876" or "localhost:9876")
        port : int, default 9876
            Server port (ignored if host contains URL with port).
        timeout : float, default 30.0
            Command timeout in seconds.
        """
        if host is None:
            # Auto-detect environment
            self.host = "host.docker.internal" if os.path.exists("/.dockerenv") else "localhost"
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
    def from_url(cls, url_string: str, timeout: float = 30.0) -> 'BlenderMCPClient':
        """
        Create BlenderMCPClient from URL string.
        
        Parameters
        ----------
        url_string : str
            URL string (e.g., "http://localhost:9876" or "localhost:9876").
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
            port = parsed.port if parsed.port is not None else 9876
            
            return cls(host=host, port=port, timeout=timeout)
            
        except Exception as e:
            raise ValueError(f"Invalid URL format '{url_string}': {str(e)}")
    
    def _receive_full_response(self, sock: socket.socket, buffer_size: int = 8192) -> bytes:
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
        """
        chunks = []
        
        try:
            while True:
                try:
                    chunk = sock.recv(buffer_size)
                    if not chunk:
                        # Connection closed, check if we have data
                        if not chunks:
                            raise Exception("Connection closed before receiving any data")
                        break
                    
                    chunks.append(chunk)
                    
                    # Check if we've received a complete JSON object
                    try:
                        data = b''.join(chunks)
                        json.loads(data.decode('utf-8'))
                        # If we get here, JSON is complete
                        return data
                    except json.JSONDecodeError:
                        # Incomplete JSON, continue receiving
                        continue
                        
                except socket.timeout:
                    # If we hit timeout during receiving, try to use what we have
                    break
                except (ConnectionError, BrokenPipeError, ConnectionResetError):
                    # Connection issues, break and try to use what we have
                    break
                    
        except Exception:
            # Any other error, try to use what we have
            pass
            
        # Try to use accumulated data
        if chunks:
            data = b''.join(chunks)
            try:
                # Validate that it's complete JSON
                json.loads(data.decode('utf-8'))
                return data
            except json.JSONDecodeError:
                raise Exception("Incomplete JSON response received")
        else:
            raise Exception("No data received")
        
    def execute_command(self, command_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a raw MCP command using direct socket communication.
        
        Parameters
        ----------
        command_type : str
            MCP command type (e.g., "get_scene_info", "execute_code").
        params : dict, optional
            Command parameters dictionary.
            
        Returns
        -------
        dict
            Response dictionary from Blender MCP server.
            
        Raises
        ------
        BlenderMCPError
            If command fails or times out.
        """
        if params is None:
            params = {}
            
        command = {
            "type": command_type,
            "params": params
        }
        
        sock = None
        try:
            # Create TCP socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.host, self.port))
            
            # Send command as JSON
            command_json = json.dumps(command).encode('utf-8')
            sock.sendall(command_json)
            
            # Receive response in chunks (like MCP server does)
            response_data = self._receive_full_response(sock)
            response = json.loads(response_data.decode('utf-8'))
            
            if response.get("status") == "error":
                raise BlenderMCPError(f"Blender error: {response.get('message', 'Unknown error')}")
                
            return response
            
        except socket.timeout:
            raise BlenderMCPError(f"Socket timeout after {self.timeout} seconds")
        except socket.error as e:
            raise BlenderMCPError(f"Socket error: {str(e)}")
        except json.JSONDecodeError as e:
            raise BlenderMCPError(f"Invalid JSON response: {str(e)}")
        except Exception as e:
            raise BlenderMCPError(f"Communication error: {str(e)}")
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass
    
    def execute_python(self, code: str) -> str:
        """
        Execute Python code in Blender.
        
        Parameters
        ----------
        code : str
            Python code string to execute.
            
        Returns
        -------
        str
            Execution result string.
            
        Raises
        ------
        BlenderMCPError
            If execution fails.
        """
        response = self.execute_command("execute_code", {"code": code})
        return response.get("result", {}).get("result", "")
    
    def get_scene_info(self) -> Dict[str, Any]:
        """
        Get current scene information.
        
        Returns
        -------
        dict
            Dictionary with scene information (objects, materials, etc.).
        """
        response = self.execute_command("get_scene_info")
        return response.get("result", {})
    
    def get_object_info(self, object_name: str) -> Dict[str, Any]:
        """
        Get information about a specific object.
        
        Parameters
        ----------
        object_name : str
            Name of the object to query.
            
        Returns
        -------
        dict
            Dictionary with object information.
        """
        response = self.execute_command("get_object_info", {"name": object_name})
        return response.get("result", {})
    
    def take_screenshot(self, filepath: str, max_size: int = 1920, format: str = "png") -> Dict[str, Any]:
        """
        Capture viewport screenshot.
        
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
        """
        params = {
            "filepath": filepath,
            "max_size": max_size,
            "format": format
        }
        response = self.execute_command("get_viewport_screenshot", params)
        return response.get("result", {})
    
    def test_connection(self) -> bool:
        """
        Test connection to Blender MCP server.
        
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