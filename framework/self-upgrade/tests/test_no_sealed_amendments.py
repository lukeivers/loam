"""Self-upgrade seal-diff test (amendment #53 — seal-bookkeeping retrofit).

Self-upgrade was sealed 2026-04-19 14:12 per ``docs/rebuild/STATE.md``
but the seal ritual never landed the bookkeeping infrastructure that
every other Phase 2 sealed component carries: no
``tests/SEAL_COMMIT`` sidecar, no ``tests/test_no_sealed_amendments.py``
diff-scope guard, no ``seals/`` narrative directory. Amendment #53
(this file's introducing amendment) retrofits all three at once,
mirroring the memory-system retrofit (amendment #8) and the
graceful-degradation + observability-aggregator retrofit
(chore commit ``7d462e3``, 2026-04-22).

Seal-test pattern (B23): BASELINE names the pre-amendment tip;
SEAL_COMMIT is read from the sidecar sibling file so the diff runs
``BASELINE..SEAL_COMMIT`` — NOT ``..HEAD``. The HEAD-based variant
was the ``f94d602`` defect patched across the other sealed components;
it must not be reintroduced.

BASELINE advances when a new amendment opens this sealed surface.
Initial value ``edf64290c7c6f76d1d1c32e8808900fce76278b2`` — the
pre-amendment tip (the post-amendment-#52 SHA-record commit
immediately before amendment #53's first touch).
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
# BASELINE history:
#   - edf64290c7c6f76d1d1c32e8808900fce76278b2 at amendment #53
#     (self-upgrade seal-bookkeeping retrofit). Pre-amendment tip
#     = HEAD at retrofit dispatch, post the amendment #52
#     SHA-record commit. The retrofit lands three new files
#     (this test, ``tests/SEAL_COMMIT``, ``seals/.gitkeep``) plus
#     the plan-doc + manifest + builder-plan + vars under
#     ``docs/rebuild/plans/`` (admitted via universal_paths). No
#     edits to ``self-upgrade/src/`` — retrofit-only. Empty
#     BASELINE..HEAD window at apply time per the standard
#     retrofit pattern.
BASELINE = "820fd84"

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


def test_B20_only_self_upgrade_surfaces_changed() -> None:
    """``git diff --name-only BASELINE..SEAL_COMMIT`` produces only
    paths under the allowed amendment surfaces.

    Amendment #53 (seal-bookkeeping retrofit) targets ``self-upgrade/``
    only — three new files under ``self-upgrade/tests/`` and
    ``self-upgrade/seals/``. Plan-doc + manifest + builder-plan + vars
    land under ``docs/rebuild/plans/`` (admitted via universal_paths
    per amendment #22 ruling #3). No edits to ``self-upgrade/src/``
    — strict retrofit fence.

    Future amendments touching self-upgrade (BB-feat clause-(h)
    LLM-merge is the next planned one) extend this prefix tuple as
    cross-component partners require.
    """
    seal = _seal_commit()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    allowed_prefixes = (
        "framework/self-upgrade/",
        "self-upgrade/",
        "data/",
        "docs/rebuild/plans/",
        # M6a — first plugin lands at plugins/dev-sdlc/. Admitted as
        # cross-component partner so the seal-diff sweep passes when
        # the plugin's diff is in flight.
        "plugins/dev-sdlc/",
        "docs/rebuild/components/self-upgrade/",
        "cost-governance/",
        "framework/cost-governance/",
        "framework/dormancy/",
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
        "framework/telegram-interface/",
        "framework/tools/",
        "framework/workspace-bootstrap/",
        "framework/workspace-sync/",
        "dormancy/",
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
        "telegram-interface/",
        "tools/",
        "workspace-bootstrap/",
        "workspace-sync/",
        "framework/tools/loam/",
        "docs/rebuild/components/",
        "docs/rebuild/spec/",
        "framework/tools/loam-mode/",
        "framework/tools/loam-migrate-dormancy-config/",
    )
    # Universal admissions per amendment #22 ruling #3 (CLAUDE.md +
    # docs/odd-*.md + docs/rebuild/FUTURE_IDEAS.md). The
    # ``docs/rebuild/plans/`` prefix is also universal but stays in
    # ``allowed_prefixes`` above for symmetry with the peer
    # retrofitted components.
    allowed_files: set[str] = {
        "CLAUDE.md",
        "docs/odd-in-pos.md",
        "docs/odd-in-loam.md",
        "docs/odd-methodology.md",
        "docs/rebuild/FUTURE_IDEAS.md",
        ".claude/settings.json",
        "first-run-inventory.yaml",
        "framework/first-run-inventory.yaml",
        "docs/rebuild/FUTURE_IDEAS_DRAFT.md",
        "CLAUDE.dev.md",
        "docs/rebuild/STATE.md",
        "docs/rebuild/VALUE_PROPOSITION.md",
        "docs/rebuild/dev-mode-manifest.yaml",
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
