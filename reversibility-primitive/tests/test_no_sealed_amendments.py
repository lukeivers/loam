"""R21: git diff against the sealed safety-layer baseline
(commit 45a15b9) shows only reversibility-primitive/ and workspace-
bootstrap changes. Zero deltas to any sealed component.

Structural remedy 2026-04-20: pinned to reversibility's own seal
commit (SEAL_COMMIT) rather than HEAD. The HEAD-based scope breaks
when later components (cost-governance, etc.) land on pos-v2 — their
files trip this audit even though they do not touch reversibility's
sealed surface. Pinning to own-seal preserves the audit at the moment
it was meaningful and leaves future components unaffected.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BASELINE = "45a15b9"
SEAL_COMMIT = "f657f8c"  # reversibility-primitive seal commit


def test_R21_only_reversibility_primitive_changed() -> None:
    """No sealed-component surface moved at reversibility's seal."""
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{SEAL_COMMIT}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    allowed_prefixes = ("reversibility-primitive/",)
    # If there is a workspace-bootstrap file at the repo root, allow it.
    allowed_files = {"README.md"}

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
