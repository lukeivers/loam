#!/usr/bin/env bash
#
# Amendment #29 AC29.4 manual-repro script — full-stack coexistence.
#
# Verifies that two pos-v2 workspaces on one macOS host can run their
# memory sidecars concurrently (distinct ports, both /health → 200,
# each workspace's probe only matches its own sidecar's identity).
# This is NOT a CI gate — it requires real claude auth, real Ollama,
# real launchd, and two installed workspace clones. Operators run it
# by hand post-amendment.
#
# Usage:
#   bash memory-system/tests/integration/coexistence.sh \
#       /path/to/workspace-a /path/to/workspace-b
#
# Pre-req: both workspaces have completed first-run; both have
# ``~/.pos/memory.yaml`` with distinct ``port`` values; both plists
# are loaded under launchctl with workspace-namespaced labels per
# amendment #6.
#
# Expected outcome:
#   * Both launchctl print targets report Running.
#   * ``curl /health`` on each port returns 200 with a
#     ``workspace_root`` field naming the responding workspace.
#   * The workspace_root fields are distinct between the two probes.

set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo "usage: $0 <workspace-a-root> <workspace-b-root>" >&2
    exit 2
fi

ws_a="$1"
ws_b="$2"

read_port() {
    local ws_root="$1"
    python3 -c "
import sys, yaml
cfg = yaml.safe_load(open('$ws_root/.pos/memory.yaml')) or {}
print(int(cfg.get('port', 8765)))
"
}

port_a="$(read_port "$ws_a")"
port_b="$(read_port "$ws_b")"

echo "workspace A: $ws_a (port $port_a)"
echo "workspace B: $ws_b (port $port_b)"

if [[ "$port_a" == "$port_b" ]]; then
    echo "ERROR: both workspaces declare port $port_a — edit one's memory.yaml and retry." >&2
    exit 1
fi

probe_one() {
    local port="$1"
    local expected_ws="$2"
    local body
    body="$(curl -sf "http://127.0.0.1:$port/health")"
    echo "  port $port → $body"
    echo "$body" | python3 -c "
import json, sys
payload = json.load(sys.stdin)
assert payload.get('status') == 'ok', payload
assert payload.get('workspace_root') == '$expected_ws', (
    'workspace_root mismatch: expected $expected_ws, got ' + repr(payload.get('workspace_root'))
)
"
}

echo "probing workspace A /health..."
probe_one "$port_a" "$ws_a"
echo "probing workspace B /health..."
probe_one "$port_b" "$ws_b"

echo "OK — both sidecars reachable on distinct ports with matching workspace identity."
