from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

import click

from ..config import BlenderRemoteConfig
from ..constants import DEFAULT_PORT
from .. import transport


def _resolve_port(port: int | None) -> int:
    if port is not None:
        return port
    config = BlenderRemoteConfig()
    return int(config.get("mcp_service.default_port") or DEFAULT_PORT)


def _print_response(response: dict[str, Any]) -> None:
    click.echo(json.dumps(response, indent=2, sort_keys=True))


@click.group()
def job() -> None:
    """Submit and inspect Blender remote jobs."""


@job.command("submit")
@click.argument("code_file", type=click.Path(exists=True), required=False)
@click.option("--code", "-c", help="Python code to submit directly")
@click.option("--use-base64", is_flag=True, help="Base64-encode code before sending")
@click.option("--return-base64", is_flag=True, help="Request base64-encoded job output")
@click.option("--job-timeout", type=float, help="Cooperative job timeout in seconds")
@click.option("--port", type=int, help="Override default MCP port")
def submit(
    code_file: str | None,
    code: str | None,
    use_base64: bool,
    return_base64: bool,
    job_timeout: float | None,
    port: int | None,
) -> None:
    """Submit Python code as a queued asynchronous user job."""
    if not code_file and not code:
        raise click.ClickException("Must provide either --code or a code file")
    if code_file and code:
        raise click.ClickException("Cannot use both --code and code file")

    code_to_submit = Path(code_file).read_text() if code_file else code or ""
    if not code_to_submit.strip():
        raise click.ClickException("Code is empty")

    if use_base64:
        code_to_submit = base64.b64encode(code_to_submit.encode("utf-8")).decode("ascii")

    response = transport.submit_code_job(
        code_to_submit,
        code_is_base64=use_base64,
        return_as_base64=return_base64,
        job_timeout_seconds=job_timeout,
        port=_resolve_port(port),
    )
    _print_response(response)


@job.command("status")
@click.argument("job_id")
@click.option("--port", type=int, help="Override default MCP port")
def status(job_id: str, port: int | None) -> None:
    """Inspect one queued, running, or terminal job."""
    _print_response(transport.get_job_status(job_id, port=_resolve_port(port)))


@job.command("result")
@click.argument("job_id")
@click.option("--port", type=int, help="Override default MCP port")
def result(job_id: str, port: int | None) -> None:
    """Retrieve the stored result for one job."""
    _print_response(transport.get_job_result(job_id, port=_resolve_port(port)))


@job.command("cancel")
@click.argument("job_id")
@click.option("--reason", help="Optional cancellation reason")
@click.option("--port", type=int, help="Override default MCP port")
def cancel(job_id: str, reason: str | None, port: int | None) -> None:
    """Request cooperative cancellation for a queued or running job."""
    _print_response(
        transport.cancel_job(job_id, reason=reason, port=_resolve_port(port))
    )


@job.command("queue")
@click.option("--port", type=int, help="Override default MCP port")
def queue_status(port: int | None) -> None:
    """Inspect active work, pending queues, and capacity metadata."""
    _print_response(transport.get_queue_status(port=_resolve_port(port)))


@job.command("active")
@click.option("--port", type=int, help="Override default MCP port")
def active(port: int | None) -> None:
    """Inspect the active main-thread item."""
    _print_response(transport.get_active_item(port=_resolve_port(port)))


@job.command("list")
@click.option("--status", "job_status", help="Filter by job status")
@click.option("--include-terminal/--exclude-terminal", default=True)
@click.option("--include-result", is_flag=True, help="Include stored result payloads")
@click.option("--limit", type=int, default=100, show_default=True)
@click.option("--port", type=int, help="Override default MCP port")
def list_jobs(
    job_status: str | None,
    include_terminal: bool,
    include_result: bool,
    limit: int,
    port: int | None,
) -> None:
    """List known jobs in the Blender job registry."""
    _print_response(
        transport.list_jobs(
            status=job_status,
            include_terminal=include_terminal,
            include_result=include_result,
            limit=limit,
            port=_resolve_port(port),
        )
    )
