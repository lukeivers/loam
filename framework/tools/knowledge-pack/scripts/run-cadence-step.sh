#!/bin/zsh
# knowledge-pack cadence STEP — the pack-render step that runs in the SAME
# cadence tick as Slice-1's capability-refresh, AFTER the refresh has
# updated the corpus. This is NOT a scheduler: it owns no cron, no
# launchd agent, no /schedule routine of its own. It is invoked by the
# EXISTING Slice-1 cadence binding (run-cadence.sh / the cloud routine /
# the launchd fallback) as an added step — D-PUSH.4, no second scheduler
# (AC.CLP-PUSH-RENDER.6).
#
# Usage: run-cadence-step.sh            # render into docs/capability-corpus/.pack
#        run-cadence-step.sh <pack-root>
#
# Renders the pack deterministically from the (freshly-refreshed) corpus
# and emits a PENDING curation-gate record. It performs NO public action:
# the pack stages in-repo; the public marketplace repo + first publish are
# S4c ⛔OWNER. It does NOT record a gate pass (a curator does that before
# any publish) and it does NOT commit/push (the cadence binding owns the
# local-commit policy, exactly as it does for the refresh).
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
COMPONENT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$COMPONENT/../../.." && pwd)"
PACK_ROOT="${1:-$REPO_ROOT/docs/capability-corpus/.pack}"

cd "$REPO_ROOT"

PYTHONPATH="$COMPONENT/src${PYTHONPATH:+:$PYTHONPATH}" \
    python3 -m knowledge_pack render --pack-root "$PACK_ROOT"
