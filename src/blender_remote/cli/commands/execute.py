from __future__ import annotations

import base64

import click

from ..config import BlenderRemoteConfig
from ..constants import DEFAULT_PORT
from ..transport import connect_and_send_command


@click.command()
@click.argument("code_file", type=click.Path(exists=True), required=False)
@click.option("--code", "-c", help="Python code to execute directly")
@click.option(
    "--use-base64",
    is_flag=True,
    help="Use base64 encoding for code transmission (recommended for complex code)",
)
@click.option(
    "--return-base64",
    is_flag=True,
    help="Request base64-encoded results (recommended for complex output)",
)
@click.option("--port", type=int, help="Override default MCP port")
def execute(
    code_file: str | None,
    code: str | None,
    use_base64: bool,
    return_base64: bool,
    port: int | None,
) -> None:
    """Execute Python code inside Blender via the MCP service.

    Parameters
    ----------
    code_file:
        Optional path to a ``.py`` file whose contents will be executed.
        Mutually exclusive with ``code``.
    code:
        Optional inline Python source string to execute. Mutually exclusive
        with ``code_file``.
    use_base64:
        If ``True``, send the code to Blender as a base64-encoded string to
        avoid quoting/encoding issues for complex scripts.
    return_base64:
        If ``True``, request that Blender return results as a base64-encoded
        string, which will be decoded and printed when possible.
    port:
        Optional override of the MCP TCP port. If omitted, falls back to the
        configured ``mcp_service.default_port`` or ``DEFAULT_PORT``.
    """
    if not code_file and not code:
        raise click.ClickException("Must provide either --code or a code file")

    if code_file and code:
        raise click.ClickException("Cannot use both --code and code file")

    # Read code from file if provided
    if code_file:
        with open(code_file) as f:
            code_to_execute = f.read()
        click.echo(f"[FILE] Executing code from: {code_file}")
    else:
        code_to_execute = code or ""
        click.echo("[CODE] Executing code directly")

    if not code_to_execute.strip():
        raise click.ClickException("Code is empty")

    if use_base64:
        click.echo("[BASE64] Using base64 encoding for code transmission")
    if return_base64:
        click.echo("[BASE64] Requesting base64-encoded results")

    click.echo(f"[LENGTH] Code length: {len(code_to_execute)} characters")

    # Get port configuration
    config = BlenderRemoteConfig()
    mcp_port = port or config.get("mcp_service.default_port") or DEFAULT_PORT

    # Prepare command parameters
    params = {"code": code_to_execute, "code_is_base64": use_base64, "return_as_base64": return_base64}

    # Encode code as base64 if requested
    if use_base64:
        encoded_code = base64.b64encode(code_to_execute.encode("utf-8")).decode("ascii")
        params["code"] = encoded_code
        click.echo(f"[ENCODED] Encoded code length: {len(encoded_code)} characters")

    click.echo(
        f"[CONNECT] Connecting to Blender BLD_Remote_MCP service (port {mcp_port})..."
    )

    # Execute command
    response = connect_and_send_command("execute_code", params, port=mcp_port)

    if response.get("status") == "success":
        result = response.get("result", {})

        click.echo("[SUCCESS] Code execution successful!")

        # Handle execution result
        if result.get("executed", False):
            output = result.get("result", "")

            # Decode base64 result if needed
            if return_base64 and result.get("result_is_base64", False):
                try:
                    decoded_output = base64.b64decode(output.encode("ascii")).decode("utf-8")
                    click.echo("[DECODED] Decoded base64 result:")
                    click.echo(decoded_output)
                except Exception as e:
                    click.echo(f"[ERROR] Failed to decode base64 result: {e}")
                    click.echo(f"Raw result: {output}")
            else:
                if output:
                    click.echo("[OUTPUT] Output:")
                    click.echo(output)
                else:
                    click.echo("[SUCCESS] Code executed successfully (no output)")
        else:
            click.echo("[WARN] Code execution completed but execution status unclear")
            click.echo(f"Response: {result}")
    else:
        error_msg = response.get("message", "Unknown error")
        click.echo(f"[ERROR] Code execution failed: {error_msg}")
        if "connection" in error_msg.lower():
            click.echo("   Make sure Blender is running with BLD_Remote_MCP addon enabled")

