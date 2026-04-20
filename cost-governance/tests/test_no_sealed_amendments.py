"""C23: git diff against the reversibility-sealed baseline (f657f8c)
shows only cost-governance/ changes. Zero deltas to any sealed
component.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BASELINE = "f657f8c"


def test_C23_only_cost_governance_changed() -> None:
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..HEAD"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]
    # Also include working-tree changes in case commits haven't landed
    # yet — the test is more useful during build.
    out_working = subprocess.check_output(
        ["git", "status", "--porcelain"],
        cwd=REPO_ROOT,
        text=True,
    )
    for line in out_working.splitlines():
        line = line.strip()
        if not line:
            continue
        # Format: "XY path" or "XY orig -> new"
        parts = line.split()
        path = parts[-1]
        if path not in changed:
            changed.append(path)

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
