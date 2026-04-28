"""AC.OBG.S — structural-enforcement A2 seal-diff invariant.

Per the locked plan-doc §4 AC.OBG.S: A2's seal-diff window contains
only edits under ``framework/hands-off-lifecycle/{hooks,tests,seals}/``
and the universal-paths admissions (``docs/rebuild/plans/``,
``CLAUDE.md``, ``docs/odd-methodology.md``, ``docs/odd-in-pos.md``,
``docs/rebuild/FUTURE_IDEAS.md``).

Pinned per ODD §10.3 per-invariant BASELINE convention. Both
endpoints will be constants once amendment #70 seals; pre-seal the
SEAL_COMMIT constant is None and the test is informational.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = (
    REPO_ROOT
    / "docs"
    / "rebuild"
    / "plans"
    / "structural-enforcement-a2-objective-binding-gate.manifest.yaml"
)


_ALLOWED_PREFIXES: tuple[str, ...] = (
    "framework/hands-off-lifecycle/hooks/",
    "framework/hands-off-lifecycle/tests/",
    "framework/hands-off-lifecycle/seals/",
    "docs/rebuild/plans/",
)
_ALLOWED_FILES: frozenset[str] = frozenset(
    {
        "CLAUDE.md",
        "docs/odd-in-pos.md",
        "docs/odd-methodology.md",
        "docs/rebuild/FUTURE_IDEAS.md",
    }
)


def _seal_commit_for_a2() -> str | None:
    """Return amendment #70's seal commit SHA.

    Both endpoints are constants once the corrective commit lands per
    the AC.MS-fix.S authoring pattern (the seal SHA isn't knowable at
    amendment-author time). Pre-corrective the constant is None and
    the test is informational (the window doesn't yet exist).
    """
    # Filled by post-seal corrective commit.
    return None


def _baseline_from_manifest() -> str | None:
    if not MANIFEST_PATH.is_file():
        return None
    for line in MANIFEST_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("baseline:"):
            return line.split(":", 1)[1].strip()
    return None


def _diff_paths(baseline: str, seal: str) -> list[str]:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(REPO_ROOT),
            "diff",
            "--name-only",
            f"{baseline}..{seal}",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip()
    ]


def test_AC_OBG_S_no_path_outside_admitted_prefixes() -> None:
    """Every path touched between BASELINE and SEAL_COMMIT lives
    under an admitted prefix or is one of the universal-files
    admissions.

    Skips (returns informationally) when the SEAL_COMMIT is not yet
    pinned — the window does not exist pre-seal."""
    baseline = _baseline_from_manifest()
    seal = _seal_commit_for_a2()
    if baseline is None or seal is None:
        # Pre-apply / pre-seal — the window does not yet exist.
        return
    paths = _diff_paths(baseline, seal)
    outside = [
        p
        for p in paths
        if not (
            any(p.startswith(prefix) for prefix in _ALLOWED_PREFIXES)
            or p in _ALLOWED_FILES
        )
    ]
    assert not outside, (
        f"AC.OBG.S: paths touched outside admitted prefixes: {outside}"
    )
