#!/usr/bin/env python3
"""
Development script to run the MCP server locally.
This simulates what `uvx blender-remote` will do after publication.
"""
import sys
import os
import subprocess

# Use pixi run to ensure correct environment
if __name__ == "__main__":
    print("🚀 Starting Blender Remote MCP Server (development mode)")
    print("📡 This simulates what 'uvx blender-remote' will do after PyPI publication")
    print("🔗 Connecting to BLD_Remote_MCP service on port 6688...")

    # Run using pixi environment
    result = subprocess.run(
        [".pixi/envs/default/bin/python", "-m", "blender_remote.mcp_server"],
        cwd=os.path.dirname(__file__),
        env={
            **os.environ,
            "PYTHONPATH": os.path.join(os.path.dirname(__file__), "src"),
        },
    )
    sys.exit(result.returncode)
