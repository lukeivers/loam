#!/bin/zsh
# capability-refresh cadence runner — the exact command both cadence
# bindings (cloud routine / launchd fallback) execute per tick.
#
# Usage: run-cadence.sh <high-velocity|long-form|on-merge|all>
#
# Runs the deterministic refresh for one cadence class from the repo
# root, then commits any corpus changes LOCALLY. No push: distribution
# of refresh commits is the cadence binding's policy surface (the cloud
# routine pushes to a claude/-prefixed branch via the owner's GitHub
# connection; the launchd fallback leaves commits local for the next
# interactive session to surface).
set -euo pipefail

CLASS="${1:?usage: run-cadence.sh <high-velocity|long-form|on-merge|all>}"
SCRIPT_DIR="${0:A:h}"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
COMPONENT="$REPO_ROOT/framework/tools/capability-refresh"

cd "$REPO_ROOT"

PYTHONPATH="$COMPONENT/src${PYTHONPATH:+:$PYTHONPATH}" \
    python3 -m capability_refresh --cadence-class "$CLASS"
status=$?
if [[ $status -ne 0 ]]; then
    echo "capability-refresh exited $status — not committing" >&2
    exit $status
fi

if ! git diff --quiet -- docs/capability-corpus/; then
    git add docs/capability-corpus/
    git commit -m "chore(corpus): scheduled capability refresh ($CLASS)" \
        -m "Deterministic projection run — auto-land/review partition per D-CUR.4; see docs/capability-corpus/.refresh/last-run.json"
    echo "refresh changes committed (local only)"
else
    echo "no corpus changes this cycle"
fi
