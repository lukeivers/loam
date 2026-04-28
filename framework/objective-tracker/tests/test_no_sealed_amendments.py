"""AC38.S — objective-tracker seal-diff test (amendment #38).

Objective-tracker historically shipped without a ``SEAL_COMMIT`` sidecar
surface; amendment #38 (schema widening — `lifted_from` provenance +
`query_projection_view` API) lands the surface alongside the first
behaviour change to establish sealed-component discipline on the
objective-tracker layer. Mirrors the precedent set in amendment #32 for
primary-persona — a sealed component's first behaviour-change amendment
introduces the seal-diff test + SEAL_COMMIT sidecar in the same fence.

Seal-test pattern (B23 from primary-persona): BASELINE names the
pre-amendment tip; SEAL_COMMIT is read from the sidecar sibling file so
the diff runs ``BASELINE..SEAL_COMMIT`` — NOT ``..HEAD``. The HEAD-based
variant was the ``f94d602`` defect patched across the other sealed
components; it must not be reintroduced.

BASELINE advances when a new amendment opens this sealed surface.
Initial value ``5ad573d`` — the pre-amendment tip (the commit
``docs(plans): record amendment #37 commit SHAs in method-decision
register`` immediately preceding amendment #38's first touch of the
objective-tracker sealed surface).
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
# BASELINE history:
#   - 5ad573d  at amendment #38 (objective-tracker schema widening).
#              First time the objective-tracker component carries a
#              seal-diff test + SEAL_COMMIT sidecar; BASELINE pins at
#              the pre-amendment tip (HEAD~1 of the amendment commit,
#              mirroring amendments #34 / #35 / #36 / #37).
BASELINE = "1ca6f62aed91ea066d10c26e84ee210029b8399c"

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


def test_AC38_S_only_objective_tracker_surfaces_changed() -> None:
    """``git diff --name-only BASELINE..SEAL_COMMIT`` produces only
    paths under the allowed amendment surfaces.

    Amendment #38 (schema widening) targets ``objective-tracker/``
    (primary surface — the new `lifted_from` field on `ObjectiveSpec`,
    the `query_projection_view` API on `ObjectiveTracker`, the
    `ObjectiveFilter` Pydantic model, the AC tests, and the new
    seal-diff sidecar surface) plus the amendment's own plan /
    research / manifest artefacts under ``docs/rebuild/plans/``.
    Universal-file admissions (CLAUDE.md, docs/odd-*.md,
    docs/rebuild/FUTURE_IDEAS.md) are admitted per amendment #22
    ruling #3.
    """
    seal = _seal_commit()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    allowed_prefixes = (
        "framework/objective-tracker/",
        "objective-tracker/",
        # plan-before-code CDC paper trail: this amendment's plan +
        # research + manifest live under docs/rebuild/plans/.
        "docs/rebuild/plans/",
        "framework/hands-off-lifecycle/",
        "cost-governance/",
        "framework/cost-governance/",
        "framework/graceful-degradation/",
        "framework/hands-off-lifecycle/canonical-dev/",
        "framework/memory-system/",
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
        "framework/workspace-sync/",
        "graceful-degradation/",
        "hands-off-lifecycle/",
        "memory-system/",
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
        "workspace-sync/",
    )
    # Universal-file admissions per amendment #22 ruling #3. Written
    # by ``pos-amend apply``; kept stable across amendments.
    allowed_files: set[str] = {
        "CLAUDE.md",
        "docs/odd-in-pos.md",
        "docs/odd-methodology.md",
        "docs/rebuild/FUTURE_IDEAS.md",
        ".gitignore",
        ".claude/settings.json",
        "first-run-inventory.yaml",
        "framework/first-run-inventory.yaml",
        "docs/rebuild/FUTURE_IDEAS_DRAFT.md",
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
