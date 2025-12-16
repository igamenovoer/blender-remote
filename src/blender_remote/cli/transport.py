"""TCP transport helpers for talking to the Blender addon."""

from __future__ import annotations

import json
import socket
from typing import Any, cast

from .constants import (
    DEFAULT_PORT,
    SOCKET_MAX_RESPONSE_SIZE,
    SOCKET_RECV_CHUNK_SIZE,
    SOCKET_TIMEOUT_SECONDS,
)


def connect_and_send_command(
    command_type: str,
    params: dict[str, Any] | None = None,
    host: str = "127.0.0.1",
    port: int = DEFAULT_PORT,
    timeout: float = SOCKET_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Connect to BLD_Remote_MCP and send a command with optimized socket handling."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))

        command = {"type": command_type, "params": params or {}}

        # Send command
        command_json = json.dumps(command)
        sock.sendall(command_json.encode("utf-8"))

        # Optimized response handling with accumulation (matches MCP server approach)
        response_data = b""

        while len(response_data) < SOCKET_MAX_RESPONSE_SIZE:
            try:
                chunk = sock.recv(SOCKET_RECV_CHUNK_SIZE)
                if not chunk:
                    break
                response_data += chunk

                # Quick check if we might have complete JSON by looking for balanced braces
                try:
                    decoded = response_data.decode("utf-8")
                    if decoded.count("{") > 0 and decoded.count("{") == decoded.count("}"):
                        # Likely complete JSON, try parsing
                        response = json.loads(decoded)
                        sock.close()
                        return cast(dict[str, Any], response)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    # Not ready yet, continue reading
                    continue

            except TimeoutError:
                # Short timeout means likely no more data for LAN/localhost
                break
            except Exception as e:
                if "timeout" in str(e).lower():
                    break
                raise

        if not response_data:
            sock.close()
            return {"status": "error", "message": "Connection closed by Blender"}

        # Final parse attempt
        response = json.loads(response_data.decode("utf-8"))
        sock.close()
        return cast(dict[str, Any], response)

    except Exception as e:
        return {"status": "error", "message": f"Connection failed: {e}"}

