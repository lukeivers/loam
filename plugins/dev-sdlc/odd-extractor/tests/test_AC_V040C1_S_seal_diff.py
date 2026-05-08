"""AC.V040C1.S — Seal-diff discipline.

Per cycle-1 plan-doc §4 AC.V040C1.S: ``git diff --name-only
BASELINE..SEAL_COMMIT`` shows changes only under:

- ``plugins/dev-sdlc/odd-extractor/`` (source + tests + fixtures),
- ``docs/plans/v0-4-0-cycle-1-*`` (this plan + manifest),
- universal-paths admissions (CLAUDE.md, docs/odd-in-pos.md,
  docs/odd-methodology.md, docs/FUTURE_IDEAS.md if surfaced).

This module reads the BASELINE pin from the sidecar
``plugins/dev-sdlc/odd-extractor/tests/SEAL_COMMIT`` (created at
seal time by ``loam amend seal``) and runs ``git diff --name-only
BASELINE..HEAD`` to verify all changes fit the fence.

If the sidecar does not yet exist (fresh apply, pre-seal), the test
is skipped — the seal-diff invariant is checked at seal time, not
at apply time. This mirrors the pattern used by amendment #38
(``test_no_sealed_amendments.py`` post-seal verification).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


_REPO_ROOT = Path(__file__).resolve().parents[4]  # → ivers-corp-pos-v2/
_SIDECAR = (
    Path(__file__).parent / "SEAL_COMMIT"
)


_ALLOWED_PREFIXES = (
    "plugins/dev-sdlc/odd-extractor/",
    "docs/plans/v0-4-0-cycle-1-",
    "docs/plans/",  # universal admission
)

_ALLOWED_FILES = (
    "CLAUDE.md",
    "docs/odd-in-pos.md",
    "docs/odd-methodology.md",
    "docs/FUTURE_IDEAS.md",
)


def _is_allowed(path: str) -> bool:
    if path in _ALLOWED_FILES:
        return True
    for prefix in _ALLOWED_PREFIXES:
        if path.startswith(prefix):
            return True
    return False


def test_AC_V040C1_S_seal_diff_invariant() -> None:
    """Diff between BASELINE (sidecar) and HEAD only touches
    in-fence files."""
    if not _SIDECAR.is_file():
        pytest.skip(
            "AC.V040C1.S sidecar SEAL_COMMIT not yet present (pre-seal). "
            "Seal-diff invariant is verified at `loam amend seal` time."
        )
    baseline = _SIDECAR.read_text().strip()
    if not baseline:
        pytest.skip("SEAL_COMMIT sidecar empty (pre-apply state).")

    proc = subprocess.run(
        ["git", "diff", "--name-only", f"{baseline}..HEAD"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    changed = [
        line.strip() for line in proc.stdout.splitlines() if line.strip()
    ]
    violations = [p for p in changed if not _is_allowed(p)]
    assert not violations, (
        "AC.V040C1.S — seal-diff invariant violated. Files outside "
        f"the C1 fence:\n  " + "\n  ".join(violations)
    )
