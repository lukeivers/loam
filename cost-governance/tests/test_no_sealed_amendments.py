"""C23: git diff against the reversibility-sealed baseline (f657f8c)
shows only cost-governance/ changes. Zero deltas to any sealed
component.

Structural remedy 2026-04-20: originally pinned to cost-governance's
own seal commit as an inline constant (fixed on commit `f94d602`
after the HEAD-based scope broke when self-correction landed).
Retrofitted 2026-04-21 to the sidecar-file pattern self-correction
and workspace-bootstrap use — cleaner ritual, no post-seal test
amendment required. SEAL_COMMIT_PATH reads from tests/SEAL_COMMIT;
falls back to HEAD when absent/placeholder so builds on an
unfinished seal still exercise the test. Post-seal, tests/SEAL_COMMIT
carries the exact SHA and the diff is deterministic.

BASELINE: f657f8c (reversibility-primitive seal — the previous seal).
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BASELINE = "f657f8c"

SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"


def _seal_commit() -> str:
    """Resolve SEAL_COMMIT from sidecar file, else HEAD."""
    if SEAL_COMMIT_PATH.exists():
        txt = SEAL_COMMIT_PATH.read_text().strip()
        if txt and txt != "HEAD":
            return txt
    return "HEAD"


def test_C23_only_cost_governance_changed() -> None:
    seal = _seal_commit()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{seal}"],
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
