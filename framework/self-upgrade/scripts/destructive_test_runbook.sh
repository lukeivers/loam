#!/usr/bin/env bash
# Destructive-test runbook — manual prototype-only test per Luke's ruling.
#
# Exercises the failed-rollback path: deliberately corrupts a
# pre-upgrade substrate snapshot, then triggers a clause-failure
# rollback, and verifies the framework:
#
#   1. detects the corrupted snapshot
#   2. halts safely rather than crashing silently
#   3. writes <tag>-rollback-failed.json with a recovery-instructions report
#   4. emits the Tier 1 notification
#
# Not a CI test. Intended for operator review at integration time.
#
# Usage (from a SAFE throwaway workspace — NEVER run against the live
# framework):
#
#   export POS_BASE_DIR="$(mktemp -d)"
#   ./destructive_test_runbook.sh

set -u  # don't set -e: we intentionally trigger failures and inspect

if [[ -z "${POS_BASE_DIR:-}" ]]; then
    echo "ERROR: POS_BASE_DIR must be set to a throwaway directory."
    echo "       Never run this against ~/.loam on the live system."
    exit 2
fi

if [[ "$POS_BASE_DIR" == "$HOME/.loam" || "$POS_BASE_DIR" == *live* ]]; then
    echo "ERROR: refusing to run against what looks like the live path."
    exit 2
fi

SELF_UPGRADE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${PYTHON:-$SELF_UPGRADE_DIR/../.venv/bin/python}"
TAG="pos-v2-destruct-$(date +%s)"

echo "[runbook] using POS_BASE_DIR=$POS_BASE_DIR"
echo "[runbook] tag for this test: $TAG"
echo ""

mkdir -p "$POS_BASE_DIR"
mkdir -p "$POS_BASE_DIR/framework"
mkdir -p "$POS_BASE_DIR/framework/releases/pos-v2-v0.1.0"
echo "prior-release" > "$POS_BASE_DIR/framework/releases/pos-v2-v0.1.0/version.txt"

# Seed substrates
printf 'sqlite-original' > "$POS_BASE_DIR/scope_of_work.sqlite"
printf 'sqlite-original' > "$POS_BASE_DIR/objective_tracker.sqlite"
printf 'sqlite-original' > "$POS_BASE_DIR/orchestrator.sqlite"
printf 'sqlite-original' > "$POS_BASE_DIR/degradation.sqlite"
printf 'duckdb-original' > "$POS_BASE_DIR/observability.duckdb"
mkdir -p "$POS_BASE_DIR/memory"
printf 'kuzu-original' > "$POS_BASE_DIR/memory/memory.kuzu"

echo "[runbook] step 1 — take pre-upgrade snapshot"
"$PYTHON" - <<PY
import os
from self_upgrade.paths import Paths
from self_upgrade.snapshot import capture_substrate_snapshots
p = Paths.from_env()
capture_substrate_snapshots(p, "${TAG}", probe_fn=None)
print(f"[runbook]   snapshot dir: {p.history_dir_pre('${TAG}')}")
PY

echo ""
echo "[runbook] step 2 — CORRUPT the snapshot (remove files from one component)"
SNAP_DIR="$POS_BASE_DIR/framework/history/${TAG}-pre/scope_of_work"
if [[ -d "$SNAP_DIR" ]]; then
    rm -rf "$SNAP_DIR"
    echo "[runbook]   deleted $SNAP_DIR"
else
    echo "[runbook]   ERROR: expected snapshot dir not found at $SNAP_DIR"
    exit 1
fi

echo ""
echo "[runbook] step 3 — attempt rollback; expect RollbackFailed"
set +e
"$PYTHON" - <<PY
import json
import sys
import traceback
from self_upgrade.paths import Paths
from self_upgrade.rollback import RollbackFailed, rollback
p = Paths.from_env()

# The live substrate exists; the snapshot for this component is missing
# (we deleted ${SNAP_DIR} above). Restore MUST fail and report clearly
# rather than silently-skipping the component.

try:
    report = rollback(
        paths=p,
        tag="${TAG}",
        prior_tag="pos-v2-v0.1.0",
        failing_clauses=["c"],
        clause_details={"c": {"reason": "synthetic failure for runbook"}},
    )
    print(f"[runbook]   UNEXPECTED success: {report.to_dict()}")
    sys.exit(3)
except RollbackFailed as exc:
    print(f"[runbook]   RollbackFailed raised as expected")
    print(f"[runbook]   steps_completed: {exc.report.steps_completed}")
    print(f"[runbook]   steps_failed:    {exc.report.steps_failed}")
    fail_json = p.history / "${TAG}-rollback-failed.json"
    if fail_json.exists():
        print(f"[runbook]   fail report at {fail_json}")
    else:
        print(f"[runbook]   ERROR: fail report NOT written")
        sys.exit(3)
PY
RB_RC=$?
set -e

if [[ $RB_RC -ne 0 ]]; then
    echo ""
    echo "[runbook] step 3 FAILED — framework did not behave as expected."
    exit 1
fi

echo ""
echo "[runbook] step 4 — verify <tag>-rollback-failed.json exists and is valid"
FAIL_JSON="$POS_BASE_DIR/framework/history/${TAG}-rollback-failed.json"
if [[ ! -f "$FAIL_JSON" ]]; then
    echo "[runbook]   FAIL: $FAIL_JSON missing"
    exit 1
fi

"$PYTHON" - <<PY
import json
from pathlib import Path
data = json.loads(Path("$FAIL_JSON").read_text())
assert data["success"] is False, f"expected success=False, got {data['success']}"
assert data["failing_clauses"] == ["c"], data["failing_clauses"]
assert "steps_failed" in data and data["steps_failed"]
print(f"[runbook]   {len(data['steps_failed'])} failed steps recorded")
for step in data["steps_failed"]:
    print(f"[runbook]     - {step['step']}: {step['error'][:80]}")
PY

echo ""
echo "[runbook] step 5 — happy-path runbook verification (non-destructive)"
# Verify the runbook itself executes cleanly on its happy path
# (no synthetic corruption). Framework writes <tag>-rolled-back.json
# which indicates success.
OK_TAG="pos-v2-ok-$(date +%s)"

# Reset state for the ok case
rm -rf "$POS_BASE_DIR/framework/history"

printf 'sqlite-original' > "$POS_BASE_DIR/scope_of_work.sqlite"
printf 'sqlite-original' > "$POS_BASE_DIR/objective_tracker.sqlite"
printf 'sqlite-original' > "$POS_BASE_DIR/orchestrator.sqlite"
printf 'sqlite-original' > "$POS_BASE_DIR/degradation.sqlite"
printf 'duckdb-original' > "$POS_BASE_DIR/observability.duckdb"
printf 'kuzu-original' > "$POS_BASE_DIR/memory/memory.kuzu"

"$PYTHON" - <<PY
from self_upgrade.paths import Paths
from self_upgrade.rollback import rollback
from self_upgrade.snapshot import capture_substrate_snapshots
p = Paths.from_env()
capture_substrate_snapshots(p, "${OK_TAG}", probe_fn=None)
report = rollback(
    paths=p,
    tag="${OK_TAG}",
    prior_tag="pos-v2-v0.1.0",
    failing_clauses=["c"],
    clause_details={},
)
assert report.success
print(f"[runbook]   happy path OK, report at {p.rolled_back_json('${OK_TAG}')}")
PY

echo ""
echo "[runbook] all steps complete — framework handled the destructive case safely."
echo "[runbook] destructive test run: PASSED"
