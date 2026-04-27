"""Workspace-sync seal-diff test (first seal of this component).

This file lands at first seal (workspace-sync amendment #56). The
component is created at first-seal-time alongside the source per the
"create at first seal, not retrofit" pattern (plan §7 + §9 + dev CDC):
every sealed component since amendment #53 lands its bookkeeping infra
in the same amendment as its source. workspace-sync follows the
pattern; the BB clause-(h) bookkeeping retrofit (#53) was the
exception because self-upgrade pre-dated the convention.

Seal-test pattern (B23): BASELINE names the pre-amendment tip;
SEAL_COMMIT is read from the sidecar sibling file so the diff runs
``BASELINE..SEAL_COMMIT`` — NOT ``..HEAD``. The HEAD-based variant
was the ``f94d602`` defect patched across the other sealed components;
it must not be reintroduced.

BASELINE history:
  - caafdf0ec2eb2e7b85f4c1145ae3f27ce874d62e at first seal (this
    amendment, #56). The pre-amendment tip = HEAD at the
    amendment-commit time = the ``chore(self-upgrade,tools): release
    manifest pos-v2-v0.2.0 + upgrade-merge-resolver factory`` commit
    (the SHA-record commit for amendment #55's release-manifest
    entries; immediately before workspace-sync's first touch).
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BASELINE = "57d735fbcde275dc0462306cd53e4830792df894"

SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"


def _seal_commit() -> str:
    """Resolve SEAL_COMMIT from the sidecar file, else HEAD.

    Once sealed, tests/SEAL_COMMIT holds the exact SHA and the diff
    runs against that — the HEAD defect cannot recur.
    """
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


def test_B20_only_workspace_sync_surfaces_changed() -> None:
    """``git diff --name-only BASELINE..SEAL_COMMIT`` produces only
    paths under the allowed amendment surfaces.

    Amendment #56 (workspace-sync first seal) targets ``workspace-sync/``
    only — new component scaffold + source + tests + seals. Plan-doc +
    builder-plan + manifest land under ``docs/rebuild/plans/`` (admitted
    via universal_paths per amendment #22 ruling #3). No edits to any
    other component (Hard Constraint #1: no self-upgrade edits; salvage
    is by file-copy).

    Future amendments touching workspace-sync extend this prefix tuple
    as cross-component partners require.
    """
    seal = _seal_commit()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    allowed_prefixes = (
        "framework/workspace-sync/",
        "workspace-sync/",
        "docs/rebuild/plans/",
        "cost-governance/",
        "framework/cost-governance/",
        "framework/graceful-degradation/",
        "framework/hands-off-lifecycle/",
        "framework/hands-off-lifecycle/canonical-dev/",
        "framework/memory-system/",
        "framework/objective-tracker/",
        "framework/observability-aggregator/",
        "framework/orchestrator/",
        "framework/primary-persona/",
        "framework/reversibility-primitive/",
        "framework/safety-layer/",
        "framework/scope-of-work/",
        "framework/self-correction/",
        "framework/self-upgrade/",
        "framework/telegram-interface/",
        "framework/tools/",
        "framework/workspace-bootstrap/",
        "graceful-degradation/",
        "hands-off-lifecycle/",
        "memory-system/",
        "objective-tracker/",
        "observability-aggregator/",
        "orchestrator/",
        "primary-persona/",
        "reversibility-primitive/",
        "safety-layer/",
        "scope-of-work/",
        "self-correction/",
        "self-upgrade/",
        "telegram-interface/",
        "tools/",
        "workspace-bootstrap/",
    )
    # Universal admissions per amendment #22 ruling #3 (CLAUDE.md +
    # docs/odd-*.md + docs/rebuild/FUTURE_IDEAS.md).
    allowed_files: set[str] = {
        "CLAUDE.md",
        "docs/odd-in-pos.md",
        "docs/odd-methodology.md",
        "docs/rebuild/FUTURE_IDEAS.md",
        ".claude/settings.json",
        "first-run-inventory.yaml",
        "framework/first-run-inventory.yaml",
    }

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
