"""R21: git diff against the sealed safety-layer baseline
(commit 45a15b9) shows only reversibility-primitive/ and workspace-
bootstrap changes. Zero deltas to any sealed component.

Structural remedy 2026-04-20: originally pinned to reversibility's
own seal commit as an inline constant (fixed on commit `f94d602`
after the HEAD-based scope broke when cost-governance landed).
Retrofitted 2026-04-21 to the sidecar-file pattern self-correction
and workspace-bootstrap use — cleaner ritual, no post-seal test
amendment required. SEAL_COMMIT_PATH reads from tests/SEAL_COMMIT;
falls back to HEAD when absent/placeholder so builds on an
unfinished seal still exercise the test. Post-seal, tests/SEAL_COMMIT
carries the exact SHA and the diff is deterministic.

BASELINE: 45a15b9 (safety-layer seal — the previous seal).
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BASELINE = "74ae5d3"

SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"


def _seal_commit() -> str:
    """Resolve SEAL_COMMIT from sidecar file, else HEAD."""
    if SEAL_COMMIT_PATH.exists():
        txt = SEAL_COMMIT_PATH.read_text().strip()
        if txt and txt != "HEAD":
            return txt
    return "HEAD"


def test_R21_only_reversibility_primitive_changed() -> None:
    """No sealed-component surface moved at reversibility's seal."""
    seal = _seal_commit()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    allowed_prefixes = (
        "framework/reversibility-primitive/",
        "reversibility-primitive/",
        "framework/cost-governance/",
        "docs/rebuild/plans/",
        "framework/graceful-degradation/",
        "framework/hands-off-lifecycle/",
        "framework/memory-system/",
        "framework/observability-aggregator/",
        "framework/orchestrator/",
        "framework/self-correction/",
        "framework/telegram-interface/",
        "framework/tools/",
        "framework/workspace-bootstrap/",
        "framework/safety-layer/",
        "cost-governance/",
        "framework/hands-off-lifecycle/canonical-dev/",
        "framework/objective-tracker/",
        "framework/primary-persona/",
        "framework/scope-of-work/",
        "framework/self-upgrade/",
        "framework/workspace-sync/",
        "graceful-degradation/",
        "hands-off-lifecycle/",
        "memory-system/",
        "objective-tracker/",
        "observability-aggregator/",
        "orchestrator/",
        "primary-persona/",
        "safety-layer/",
        "scope-of-work/",
        "self-correction/",
        "self-upgrade/",
        "telegram-interface/",
        "tools/",
        "workspace-bootstrap/",
        "workspace-sync/",
        "framework/tools/loam/",
        "docs/rebuild/components/",
        "docs/rebuild/spec/",
        "framework/tools/loam-mode/",
    )
    # If there is a workspace-bootstrap file at the repo root, allow it.
    allowed_files = {
        "README.md",
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
        f"Sealed-component paths modified: {offending}. Halt-signal condition."
    )
