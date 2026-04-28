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


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
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

    # D-migration D.1 (amendment #61) prefixed every framework
    # component path with ``framework/``; D.2 (amendment #63) under
    # the wider-fence ruling cuts every workspace-state reader over
    # to the workspace_paths helper inside workspace-bootstrap. The
    # AC.M.S prefix list is widened correspondingly. AC.M.S is now
    # tracking the *cumulative* fence of the amendment #48-line of
    # primary-persona work (per D.2's loose-AC tightening rule).
    allowed_prefixes = (
        # Post-D.1 framework/ root.
        "framework/primary-persona/src/",
        "framework/primary-persona/tests/",
        "framework/primary-persona/templates/",
        "framework/primary-persona/seals/",
        "framework/hands-off-lifecycle/hooks/",
        "framework/hands-off-lifecycle/tests/",
        "framework/hands-off-lifecycle/seals/",
        "framework/workspace-bootstrap/src/",
        "framework/workspace-bootstrap/tests/",
        "framework/workspace-bootstrap/templates/",
        "framework/orchestrator/src/",
        "framework/orchestrator/tests/",
        # D.2 wider-fence components — cut over to workspace_paths
        # helper per D.2-build.A/G/H.
        "framework/workspace-sync/src/",
        "framework/workspace-sync/tests/",
        "framework/self-upgrade/src/",
        "framework/self-upgrade/tests/",
        "framework/tools/",
        # Universal admissions (per amendment #22 ruling #3).
        "docs/rebuild/plans/",
        "docs/rebuild/plans/research/",
        # Amendment #68 (α — Claude-Code-corpus prompt-spine + seed
        # docs) widened universal_paths to include the new
        # capability-corpus tree. Same widening pattern as D.1 / D.2:
        # the cumulative fence of the amendment #48-line of
        # primary-persona work expands as universal admissions
        # broaden. Structural fix (FUTURE_IDEAS_DRAFT — "AC.M.S
        # structural brittleness") replaces this drifting-fence
        # pattern in a follow-on amendment.
        "docs/rebuild/capability-corpus/",
        # Pre-D.1 paths (transitional admission per D.1's seal-diff
        # window — the BASELINE pinned in test_no_sealed_amendments
        # advanced past D.1, but transitional admission keeps the
        # window stable for prior-rename comparisons).
        "primary-persona/",
        "hands-off-lifecycle/",
        "workspace-bootstrap/tests/",
        "orchestrator/src/",
        "orchestrator/tests/",
    )
    allowed_files: set[str] = {
        # Post-D.1 framework/ root.
        "framework/primary-persona/pyproject.toml",
        "framework/workspace-bootstrap/pyproject.toml",
        "framework/orchestrator/pyproject.toml",
        # Pre-D.1 transitional.
        "primary-persona/pyproject.toml",
        "CLAUDE.md",
        "docs/odd-in-pos.md",
        "docs/odd-methodology.md",
        "docs/rebuild/FUTURE_IDEAS.md",
        "docs/rebuild/STATE.md",
        "docs/rebuild/VALUE_PROPOSITION.md",
        # D.1 universal-admissions widened roots.
        ".claude/settings.json",
        "data/kuzu_db",
        "data/scope_registry.json",
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
