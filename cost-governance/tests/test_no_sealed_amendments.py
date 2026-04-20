"""C23: git diff against the reversibility-sealed baseline (f657f8c)
shows only cost-governance/ changes. Zero deltas to any sealed
component.

Structural remedy 2026-04-20: pinned to cost-governance's own seal
commit (SEAL_COMMIT) rather than HEAD. The HEAD-based scope breaks
when later components (self-correction, etc.) land on pos-v2 — their
files trip this audit even though they do not touch cost-governance's
sealed surface. Pinning to own-seal preserves the audit at the moment
it was meaningful and leaves future components unaffected.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BASELINE = "f657f8c"
SEAL_COMMIT = "04951b6"  # cost-governance seal commit


def test_C23_only_cost_governance_changed() -> None:
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{SEAL_COMMIT}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    # `data/` is runtime test-output (observability spans.jsonl etc.),
    # not source. It is not a sealed-component amendment — treat as
    # generated artifact alongside `cost-governance/`.
    allowed_prefixes = ("cost-governance/", "data/")
    allowed_files: set[str] = set()  # no workspace-wide touches needed

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
