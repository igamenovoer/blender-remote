#!/usr/bin/env python3
"""
Utility functions and classes for BLD Remote MCP examples.

This module provides reusable components for connecting to and controlling
the BLD Remote MCP background service.
"""

import socket
import json
import time
import sys
from typing import Dict, Any, Optional
from contextlib import contextmanager


class BldRemoteClient:
    """Simple client for BLD Remote MCP service."""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 6688, timeout: float = 10.0):
        """
        Initialize client connection parameters.
        
        Args:
            host: Server hostname (default: localhost)
            port: Server port (default: 6688)
            timeout: Connection timeout in seconds
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket = None
    
    def connect(self) -> None:
        """Establish connection to the service."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
        except Exception as e:
            raise ConnectionError(f"Failed to connect to {self.host}:{self.port}: {e}")
    
    def disconnect(self) -> None:
        """Close connection to the service."""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
    
    def send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a command and receive response.
        
        Args:
            command: Command dictionary with 'message' and/or 'code' fields
            
        Returns:
            Response dictionary from the service
            
        Raises:
            ConnectionError: If not connected or communication fails
        """
        if not self.socket:
            raise ConnectionError("Not connected to service")
        
        try:
            # Send command
            message = json.dumps(command).encode('utf-8')
            self.socket.sendall(message)
            
            # Receive response
            response_data = self.socket.recv(4096)
            response = json.loads(response_data.decode('utf-8'))
            
            return response
            
        except Exception as e:
            raise ConnectionError(f"Communication error: {e}")
    
    def execute_code(self, code: str, message: str = "") -> Dict[str, Any]:
        """
        Execute Python code in Blender.
        
        Args:
            code: Python code to execute
            message: Optional description message
            
        Returns:
            Response from service
        """
        command = {"code": code}
        if message:
            command["message"] = message
            
        return self.send_command(command)
    
    def send_message(self, message: str) -> Dict[str, Any]:
        """
        Send a simple message to the service.
        
        Args:
            message: Message to send
            
        Returns:
            Response from service
        """
        return self.send_command({"message": message})
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


@contextmanager
def blender_connection(host: str = '127.0.0.1', port: int = 6688, timeout: float = 10.0):
    """
    Context manager for BLD Remote MCP connections.
    
    Args:
        host: Server hostname
        port: Server port  
        timeout: Connection timeout
        
    Yields:
        BldRemoteClient: Connected client instance
        
    Example:
        with blender_connection() as client:
            client.execute_code("bpy.ops.mesh.primitive_cube_add()")
    """
    client = BldRemoteClient(host, port, timeout)
    try:
        client.connect()
        yield client
    finally:
        client.disconnect()


def check_service_health(host: str = '127.0.0.1', port: int = 6688) -> Dict[str, Any]:
    """
    Check if the BLD Remote MCP service is running and responsive.
    
    Args:
        host: Server hostname
        port: Server port
        
    Returns:
        Health status dictionary
    """
    try:
        with blender_connection(host, port, timeout=5.0) as client:
            # Send a simple test command
            response = client.execute_code(
                "len(bpy.data.objects)", 
                "Health check - count objects"
            )
            
            return {
                "status": "healthy",
                "responsive": True,
                "host": host,
                "port": port,
                "test_response": response
            }
            
    except ConnectionError as e:
        return {
            "status": "unhealthy", 
            "responsive": False,
            "host": host,
            "port": port,
            "error": str(e)
        }
    except Exception as e:
        return {
            "status": "error",
            "responsive": False, 
            "host": host,
            "port": port,
            "error": str(e)
        }


def wait_for_service(host: str = '127.0.0.1', port: int = 6688, 
                    timeout: float = 30.0, check_interval: float = 1.0) -> bool:
    """
    Wait for the service to become available.
    
    Args:
        host: Server hostname
        port: Server port
        timeout: Maximum time to wait
        check_interval: Time between checks
        
    Returns:
        True if service becomes available, False if timeout
    """
    start_time = time.time()
    
    print(f"Waiting for BLD Remote MCP service at {host}:{port}...")
    
    while time.time() - start_time < timeout:
        health = check_service_health(host, port)
        if health["responsive"]:
            print(f"✓ Service is ready!")
            return True
            
        print(f"  Waiting... ({time.time() - start_time:.1f}s)")
        time.sleep(check_interval)
    
    print(f"✗ Service did not become available within {timeout}s")
    return False


def batch_execute(commands: list, host: str = '127.0.0.1', port: int = 6688, 
                 delay: float = 0.1) -> list:
    """
    Execute multiple commands in sequence.
    
    Args:
        commands: List of command dictionaries or code strings
        host: Server hostname
        port: Server port
        delay: Delay between commands
        
    Returns:
        List of responses
    """
    responses = []
    
    with blender_connection(host, port) as client:
        for i, cmd in enumerate(commands):
            try:
                if isinstance(cmd, str):
                    # Convert string to command dict
                    response = client.execute_code(cmd, f"Batch command {i+1}")
                else:
                    # Use command dict directly
                    response = client.send_command(cmd)
                
                responses.append(response)
                
                if delay > 0 and i < len(commands) - 1:
                    time.sleep(delay)
                    
            except Exception as e:
                error_response = {
                    "response": "ERROR",
                    "message": str(e),
                    "command_index": i
                }
                responses.append(error_response)
    
    return responses


def shutdown_service(host: str = '127.0.0.1', port: int = 6688) -> bool:
    """
    Send shutdown command to the service.
    
    Args:
        host: Server hostname
        port: Server port
        
    Returns:
        True if shutdown command sent successfully
    """
    try:
        with blender_connection(host, port, timeout=5.0) as client:
            client.execute_code("quit_blender", "Shutdown command")
        return True
    except:
        # Expected if service shuts down quickly
        return True


def print_status(status: Dict[str, Any]) -> None:
    """Pretty print service status."""
    if status["responsive"]:
        print(f"✓ Service Status: {status['status'].upper()}")
        print(f"  Host: {status['host']}")
        print(f"  Port: {status['port']}")
        if "test_response" in status:
            response = status["test_response"]
            print(f"  Response: {response.get('response', 'N/A')}")
    else:
        print(f"✗ Service Status: {status['status'].upper()}")
        print(f"  Host: {status['host']}")
        print(f"  Port: {status['port']}")
        print(f"  Error: {status.get('error', 'Unknown error')}")


def validate_response(response: Dict[str, Any], expect_ok: bool = True) -> bool:
    """
    Validate service response.
    
    Args:
        response: Response dictionary from service
        expect_ok: Whether to expect 'OK' response
        
    Returns:
        True if response is valid and matches expectation
    """
    if not isinstance(response, dict):
        print(f"Invalid response type: {type(response)}")
        return False
    
    if "response" not in response:
        print("Missing 'response' field in response")
        return False
    
    if expect_ok and response["response"] != "OK":
        print(f"Expected 'OK' response, got: {response['response']}")
        if "message" in response:
            print(f"Message: {response['message']}")
        return False
    
    return True


# Example usage and testing
if __name__ == "__main__":
    print("BLD Remote MCP Utils - Testing basic functionality")
    
    # Check service health
    health = check_service_health()
    print_status(health)
    
    if health["responsive"]:
        print("\nTesting basic operations...")
        
        try:
            with blender_connection() as client:
                # Test message
                response = client.send_message("Hello from utils test!")
                print(f"Message response: {response}")
                
                # Test code execution
                response = client.execute_code(
                    "print(f'Blender version: {bpy.app.version_string}')",
                    "Version check"
                )
                print(f"Code response: {response}")
                
        except Exception as e:
            print(f"Test failed: {e}")
    else:
        print("\nService not available for testing")
        print("Start the service with: python3 start_service.py")