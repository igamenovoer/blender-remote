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


def submit_code_job(
    code: str,
    *,
    code_is_base64: bool = False,
    return_as_base64: bool = False,
    job_timeout_seconds: float | None = None,
    host: str = "127.0.0.1",
    port: int = DEFAULT_PORT,
    timeout: float = SOCKET_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Submit a Blender Python job and return its remote job metadata."""
    params: dict[str, Any] = {
        "code": code,
        "code_is_base64": code_is_base64,
        "return_as_base64": return_as_base64,
    }
    if job_timeout_seconds is not None:
        params["job_timeout_seconds"] = job_timeout_seconds
    return connect_and_send_command(
        "submit_code_job",
        params,
        host=host,
        port=port,
        timeout=timeout,
    )


def get_job_status(
    job_id: str,
    *,
    host: str = "127.0.0.1",
    port: int = DEFAULT_PORT,
    timeout: float = SOCKET_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Inspect the status of a submitted Blender job."""
    return connect_and_send_command(
        "get_job_status",
        {"job_id": job_id},
        host=host,
        port=port,
        timeout=timeout,
    )


def get_job_result(
    job_id: str,
    *,
    host: str = "127.0.0.1",
    port: int = DEFAULT_PORT,
    timeout: float = SOCKET_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Retrieve the stored terminal result for a submitted Blender job."""
    return connect_and_send_command(
        "get_job_result",
        {"job_id": job_id},
        host=host,
        port=port,
        timeout=timeout,
    )


def cancel_job(
    job_id: str,
    *,
    reason: str | None = None,
    host: str = "127.0.0.1",
    port: int = DEFAULT_PORT,
    timeout: float = SOCKET_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Request cooperative cancellation for a submitted Blender job."""
    params: dict[str, Any] = {"job_id": job_id}
    if reason is not None:
        params["reason"] = reason
    return connect_and_send_command(
        "cancel_job",
        params,
        host=host,
        port=port,
        timeout=timeout,
    )


def execute_code(
    code: str,
    *,
    code_is_base64: bool = False,
    return_as_base64: bool = False,
    wait_timeout_seconds: float | None = None,
    job_timeout_seconds: float | None = None,
    detach_on_wait_timeout: bool = False,
    host: str = "127.0.0.1",
    port: int = DEFAULT_PORT,
    timeout: float = SOCKET_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Execute Blender Python through the synchronous job facade."""
    params: dict[str, Any] = {
        "code": code,
        "code_is_base64": code_is_base64,
        "return_as_base64": return_as_base64,
        "detach_on_wait_timeout": detach_on_wait_timeout,
    }
    if wait_timeout_seconds is not None:
        params["wait_timeout_seconds"] = wait_timeout_seconds
    if job_timeout_seconds is not None:
        params["job_timeout_seconds"] = job_timeout_seconds
    return connect_and_send_command(
        "execute_code",
        params,
        host=host,
        port=port,
        timeout=timeout,
    )
