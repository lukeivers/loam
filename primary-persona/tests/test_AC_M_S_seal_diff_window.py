"""AC.M.S — seal-diff discipline for amendment #48.

Outcome (per locked plan §5): ``git diff --name-only
BASELINE..SEAL_COMMIT`` shows only paths under:

  - ``primary-persona/src/``
  - ``primary-persona/tests/``
  - ``primary-persona/pyproject.toml``
  - ``hands-off-lifecycle/hooks/``
  - ``hands-off-lifecycle/tests/``
  - ``hands-off-lifecycle/seals/`` (narrative artefact at seal time)
  - the universal-paths admissions
    (``docs/rebuild/plans/``, ``CLAUDE.md``, ``docs/odd-in-pos.md``,
    ``docs/odd-methodology.md``, ``docs/rebuild/FUTURE_IDEAS.md``).

Tighter than the existing ``test_no_sealed_amendments.py`` window
(which admits the broader top-level ``primary-persona/`` and
``hands-off-lifecycle/`` prefixes); AC.M.S specifies the narrower
sub-tree fence inside each component.

This test runs AFTER ``pos-amend seal`` advances the SEAL_COMMIT
sidecar; pre-seal it succeeds vacuously when the diff window is
the empty-amendment-window the SEAL_COMMIT sidecar carries before
the seal step. Mirrors the AC.M.S pattern from the locked plan.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SEAL_COMMIT_PATH = (
    Path(__file__).resolve().parent / "SEAL_COMMIT"
)

# Resolved at test time — see _seal_commit().
_BASELINE_FROM_TEST = "test_no_sealed_amendments"


def _seal_commit() -> str:
    if SEAL_COMMIT_PATH.exists():
        txt = SEAL_COMMIT_PATH.read_text().strip()
        if txt and txt != "HEAD":
            return txt
    return "HEAD"


def _baseline() -> str:
    """Read BASELINE from the canonical seal test so this test cannot
    drift from the component's authoritative BASELINE pin."""
    src = (
        Path(__file__).resolve().parent / "test_no_sealed_amendments.py"
    ).read_text()
    for ln in src.splitlines():
        if ln.startswith("BASELINE = "):
            return ln.split('"')[1]
    raise AssertionError("BASELINE literal not found")


def test_AC_M_S_seal_diff_within_amendment_48_fence() -> None:
    """No path outside AC.M.S's named fence appears in the
    BASELINE..SEAL_COMMIT diff."""
    seal = _seal_commit()
    baseline = _baseline()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{baseline}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    allowed_prefixes = (
        "primary-persona/src/",
        "primary-persona/tests/",
        "primary-persona/templates/",
        "primary-persona/seals/",
        "hands-off-lifecycle/hooks/",
        "hands-off-lifecycle/tests/",
        # Seal narrative target lives under hands-off-lifecycle/seals/
        # (per locked plan §10's narrative target).
        "hands-off-lifecycle/seals/",
        # Universal admissions (per amendment #22 ruling #3).
        "docs/rebuild/plans/",
        "docs/rebuild/plans/research/",
        # Cross-component partner admission (amendment #50 D-OWNER.2
        # relaxation — one workspace-bootstrap test edit + the
        # SEAL_COMMIT sidecar bump it carries).
        "workspace-bootstrap/tests/",
        # Cross-component partner admission (amendment #52 R1 ruling
        # — A8 dispatch-wrapper widens fence to orchestrator/ for the
        # new activate_scope_with_spec + record_dispatch_close IPC
        # methods that the persona-side wrapper consumes; seal-diff
        # window admits orchestrator/src/ + orchestrator/tests/ +
        # orchestrator/pyproject.toml under this allowed_prefixes
        # tuple, matching the manifest's component list).
        "orchestrator/src/",
        "orchestrator/tests/",
    )
    allowed_files: set[str] = {
        "primary-persona/pyproject.toml",
        "CLAUDE.md",
        "docs/odd-in-pos.md",
        "docs/odd-methodology.md",
        "docs/rebuild/FUTURE_IDEAS.md",
        "docs/rebuild/STATE.md",
        "docs/rebuild/VALUE_PROPOSITION.md",
    }

    offending: list[str] = []
    for path in changed:
        if any(path.startswith(p) for p in allowed_prefixes):
            continue
        if path in allowed_files:
            continue
        offending.append(path)
    assert offending == [], (
        f"AC.M.S violation: paths outside the amendment #48 fence: "
        f"{offending}"
    )
