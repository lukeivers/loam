"""B20, B23 — git diff against baseline shows only workspace-bootstrap
changes. Zero deltas to any sealed component.

Seal-test pattern (B23 / proposal §3.5): this file defines a BASELINE
constant and reads SEAL_COMMIT from a sidecar file, diffing
`BASELINE..SEAL_COMMIT` — NOT `..HEAD`. The HEAD-based variant is the
defect fixed on `f94d602`; it must not be reintroduced.

BASELINE: the commit immediately preceding the most recent amendment
    window for workspace-bootstrap. Originally ac48a7b at first seal;
    updated to 3780603 when Amendment 4 (hands-off-lifecycle
    first_run_scaffold phase) opened. Each new amendment that opens
    this sealed surface updates BASELINE to the pre-amendment tip so
    the diff scope reflects the amendment, not the full rebuild
    history.
SEAL_COMMIT: populated at seal time. During build, falls back to HEAD.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
# BASELINE advances when workspace-bootstrap opens a new amendment
# window:
#   - ac48a7b  at first seal
#   - 3780603  when Amendment 4 (first_run_scaffold phase) opened
#   - 63b7cb8  when the session-start-detachment amendment opened
#              (run_first_run_scaffold gains a partial_recovery=True
#              path so the detached worker can complete a scaffold
#              that crashed mid-flight, closing the H4 "retry next
#              session" terminal user surface). 63b7cb8 is the tip
#              immediately before this amendment's commit, so the
#              diff scope captures only this amendment's work even
#              though unrelated commits landed between the prior
#              workspace-bootstrap seal (1a55969) and this one.
#   - 9f35979  when the namespaced-labels-and-bootout amendment (#6)
#              opened. Per-workspace service-label namespacing
#              (`com.pos-v2.<slug>.<kind>`) + launchctl bootout-before-
#              bootstrap so multiple pos-v2 workspaces coexist on one
#              host and stale launchd cache is replaced rather than
#              no-op'd (closes the pos3 first-run regression 2026-04-22).
#              Multi-component amendment with hands-off-lifecycle in
#              lockstep. 9f35979 is the pre-amendment tip — the docs-
#              migration chore commit immediately before the amendment
#              code commit.
#   - a5dbf8f  when the orchestrator-bootstrap-unification amendment
#              (#7) opened. Orchestrator no longer self-loads
#              `bootstrap.py`; the workspace-bootstrap framework's
#              `WorkspaceBootstrapPyContribution` adapter is the sole
#              loader, and missing `~/.pos/bootstrap.yaml` is the new
#              fail-closed trigger (MissingConfigError, -32080). Adapter
#              + integration-test edits land on this side because the
#              removed `OrchestratorConfig.require_bootstrap` field was
#              referenced here; the amendment's primary surface is
#              orchestrator/. a5dbf8f is the pre-amendment tip — the
#              amendment-#6 seal commit immediately before this
#              amendment's code commit.
#   - 7d462e3  when the linux-removal amendment (#10) opened. Per
#              docs/odd-methodology.md §2.5, Linux was never a named
#              supported-platform objective; `_SYSTEMD_TEMPLATES`, the
#              linux branches in `detect_platform` / `_install_service_
#              manager_files` / `ServiceManagerRunner.bootstrap`, and
#              the `test_H1_linux_writes_systemd_units` +
#              `test_AC4_linux_stop_then_reload_then_start` tests are
#              removed. Multi-component amendment touching workspace-
#              bootstrap, orchestrator, self-upgrade, hands-off-
#              lifecycle, first-run-inventory.yaml, and amendment-#6's
#              proposal (historical superseded-by marker). 7d462e3 is
#              the pre-amendment tip — the graceful-degradation +
#              observability-aggregator retrofit chore commit
#              immediately before this amendment's code commit.
BASELINE = "7d462e3"

SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"


def _seal_commit() -> str:
    """Resolve SEAL_COMMIT from the sidecar file, else HEAD.

    Once sealed, tests/SEAL_COMMIT holds the exact SHA and the diff
    runs against that — the HEAD defect cannot recur."""
    if SEAL_COMMIT_PATH.exists():
        txt = SEAL_COMMIT_PATH.read_text().strip()
        if txt and txt != "HEAD":
            return txt
    return "HEAD"


def test_B23_seal_commit_pinning_pattern() -> None:
    """The test file exposes SEAL_COMMIT_PATH and names BASELINE; the
    diff call routes through _seal_commit() (not a hardcoded HEAD)."""
    source = Path(__file__).read_text()
    assert "BASELINE = " in source
    assert "SEAL_COMMIT_PATH" in source
    assert "{BASELINE}..{seal}" in source, (
        "the diff call must route through _seal_commit()"
    )


def test_B20_only_workspace_bootstrap_changed() -> None:
    seal = _seal_commit()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    # `data/` is runtime test-output (aggregator spool, cost sqlite).
    # `hands-off-lifecycle/` is the amendment counterpart in the
    # 2026-04-22 session-start-detachment multi-component amendment —
    # run_first_run_scaffold gained a partial_recovery=True path here,
    # and the detached worker that consumes it lives in
    # hands-off-lifecycle. Both components' tests re-seal in lockstep.
    # Amendment #6 (namespaced-labels-and-bootout) additions:
    #   - `docs/rebuild/components/namespaced-labels-and-bootout/` —
    #     the proposal + brief living with the amendment.
    #   - `first-run-inventory.yaml` — workspace-level manifest; the
    #     amendment templates service labels with `{slug}` so the
    #     inventory is workspace-agnostic.
    # Amendment #7 (orchestrator-bootstrap-unification) additions:
    #   - `orchestrator/` — primary surface for the amendment (this
    #     multi-component amendment's main edits land in orchestrator/
    #     with counterpart edits on this side for the removed
    #     `require_bootstrap` field's upstream callers).
    #   - `docs/rebuild/components/orchestrator-bootstrap-unification/`
    #     — the proposal living with the amendment.
    # Amendment #10 (linux-removal) additions:
    #   - `self-upgrade/` — dead `systemd_user_restart` removed.
    #   - `memory-system/` — orphan `memory-system/systemd/` directory
    #     removed (unit template was never read by runtime code).
    #   - `docs/rebuild/components/namespaced-labels-and-bootout/` —
    #     already in the allowed list for amendment #6; the #10 edit is
    #     the superseded-by marker on AC3.
    #   - `docs/rebuild/plans/` — the amendment's own plan file.
    allowed_prefixes = (
        "workspace-bootstrap/",
        "data/",
        "hands-off-lifecycle/",
        "orchestrator/",
        "self-upgrade/",
        "memory-system/",
        "docs/rebuild/components/namespaced-labels-and-bootout/",
        "docs/rebuild/components/orchestrator-bootstrap-unification/",
        "docs/rebuild/plans/",
    )
    allowed_files: set[str] = {"first-run-inventory.yaml"}

    offending = []
    for path in changed:
        if any(path.startswith(p) for p in allowed_prefixes):
            continue
        if path in allowed_files:
            continue
        offending.append(path)
    assert offending == [], (
        f"Sealed-component paths modified: {offending}. "
        "Halt-signal condition."
    )
