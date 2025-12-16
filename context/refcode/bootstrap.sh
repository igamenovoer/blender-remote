#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REFCODE_DIR="${SCRIPT_DIR}"

require_cmd() {
  for c in "$@"; do
    if ! command -v "$c" >/dev/null 2>&1; then
      echo "missing required command: $c" >&2
      exit 127
    fi
  done
}

require_cmd git

BLENDER_MCP_DIR="${REFCODE_DIR}/blender-mcp"
MCP_SPEC_DIR="${REFCODE_DIR}/modelcontextprotocol"
MCP_SDK_DIR="${REFCODE_DIR}/mcp-sdk"

echo "Bootstrapping external reference code in ${REFCODE_DIR} ..."

# Clone blender-mcp
if [[ -d "${BLENDER_MCP_DIR}/.git" ]]; then
  echo "  - blender-mcp already present; leaving as-is."
else
  echo "  - cloning blender-mcp (shallow) ..."
  rm -rf "${BLENDER_MCP_DIR}"
  git clone --depth 1 https://github.com/ahujasid/blender-mcp.git "${BLENDER_MCP_DIR}"
fi

# Clone modelcontextprotocol
if [[ -d "${MCP_SPEC_DIR}/.git" ]]; then
  echo "  - modelcontextprotocol already present; leaving as-is."
else
  echo "  - cloning modelcontextprotocol (shallow) ..."
  rm -rf "${MCP_SPEC_DIR}"
  git clone --depth 1 https://github.com/modelcontextprotocol/modelcontextprotocol.git "${MCP_SPEC_DIR}"
fi

# Clone mcp-sdk (python-sdk)
if [[ -d "${MCP_SDK_DIR}/.git" ]]; then
  echo "  - mcp-sdk already present; leaving as-is."
else
  echo "  - cloning mcp-sdk (shallow) ..."
  rm -rf "${MCP_SDK_DIR}"
  git clone --depth 1 https://github.com/modelcontextprotocol/python-sdk.git "${MCP_SDK_DIR}"
fi

echo "Done."
