"""AC.SE.S — structural-enforcement A1 substrate seal-diff invariant.

Per the locked plan-doc §4 AC.SE.S: the seal-diff window for the A1
amendment contains only edits under ``hands-off-lifecycle/``,
``objective-tracker/``, and the universal-paths admissions
(``docs/rebuild/plans/``, ``CLAUDE.md``, ``docs/odd-methodology.md``,
``docs/odd-in-pos.md``, ``docs/rebuild/FUTURE_IDEAS.md``,
``.gitignore``).

Pinned per ODD §10.3 per-invariant BASELINE convention: this test
asserts the window of A1 specifically, not the floating
component-level window the existing
``hands-off-lifecycle/tests/test_cross_cutting.py::test_H19_*``
covers.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = (
    REPO_ROOT
    / "docs"
    / "rebuild"
    / "plans"
    / "structural-enforcement-a1-substrate.manifest.yaml"
)


_ALLOWED_PREFIXES: tuple[str, ...] = (
    "hands-off-lifecycle/",
    "objective-tracker/",
    "docs/rebuild/plans/",
)
_ALLOWED_FILES: frozenset[str] = frozenset(
    {
        "CLAUDE.md",
        "docs/odd-in-pos.md",
        "docs/odd-methodology.md",
        "docs/rebuild/FUTURE_IDEAS.md",
        ".gitignore",
    }
)


def _seal_commit_from_manifest_sibling() -> str | None:
    """Resolve the SEAL_COMMIT for A1 from the existing component
    sidecar that ``pos-amend seal`` advances. Until ``pos-amend seal``
    runs the sidecar holds the apply-time SHA (the BASELINE-pinning
    placeholder); we use whichever value is current and assert the
    window is clean."""
    sidecar = REPO_ROOT / "hands-off-lifecycle" / "tests" / "SEAL_COMMIT"
    if not sidecar.exists():
        return None
    txt = sidecar.read_text().strip()
    if not txt:
        return None
    return txt


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


def test_AC_SE_S_no_path_outside_admitted_prefixes() -> None:
    """Every path touched between BASELINE and SEAL_COMMIT lives
    under an admitted prefix or is one of the universal-files
    admissions.

    Skips if the manifest or sidecar is not yet authored — this is
    a build-time test that becomes load-bearing once ``pos-amend
    apply`` writes both. Pre-apply runs are no-ops (the test is
    informational until A1's window exists)."""
    baseline = _baseline_from_manifest()
    seal = _seal_commit_from_manifest_sibling()
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
        f"AC.SE.S: paths touched outside admitted prefixes: {outside}"
    )
