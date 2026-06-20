#!/usr/bin/env bash
# mcp-security-gate: only allow MCP servers declared in mcp.json. Usage: mcp-security-gate.sh <server>
set -uo pipefail
cd "$(dirname "$0")/../.."
SERVER="${1:-}"
[ -z "$SERVER" ] && { echo "no server given" >&2; exit 1; }
if [ ! -f mcp.json ]; then echo "mcp.json missing" >&2; exit 1; fi
if grep -q "\"$SERVER\"" mcp.json; then
  echo "ALLOW: $SERVER is whitelisted in mcp.json"; exit 0
else
  echo "BLOCK: $SERVER not in mcp.json whitelist" >&2; exit 3
fi
