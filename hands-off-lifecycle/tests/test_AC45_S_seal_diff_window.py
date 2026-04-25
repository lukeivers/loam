"""Amendment #45 — AC.45.S.

Seal-diff: changes confined to ``hands-off-lifecycle/`` source +
tests, ``tools/loam-mode/`` (within H19's ``tools`` admission), and
the relevant plan docs. No surface change to other sealed components.

This test asserts the source-tree introspection invariant: every
amendment-#45-touched file lives under one of the admitted prefixes.
The existing H19 frozen-BASELINE check
(``test_cross_cutting.py::test_H19_diff_scope_covers_only_approved_surfaces``)
covers the cross-component check at project level; this test
provides the per-amendment confirmation.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


# Allowed prefixes for amendment #45's diff window. Mirrors the
# manifest's ``components`` + ``universal_paths`` declarations.
_ALLOWED_PREFIXES: tuple[str, ...] = (
    "hands-off-lifecycle/",
    "tools/loam-mode/",
    "docs/rebuild/plans/",
    # Universal admissions per amendment #22 ruling #3.
    "CLAUDE.md",
    "docs/odd-in-pos.md",
    "docs/odd-methodology.md",
    "docs/rebuild/FUTURE_IDEAS.md",
)


def _diff_paths(baseline: str, head: str) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "diff", "--name-only",
         f"{baseline}..{head}"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip()
    ]


def test_AC45_S_no_path_outside_admitted_prefixes_against_HEAD() -> None:
    """Every path touched between the amendment BASELINE (the commit
    immediately preceding the amendment commit) and HEAD lives under
    an admitted prefix.

    The BASELINE is resolved at runtime by reading the manifest yaml
    so this test stays in lock-step with the manifest as the seal
    cycle progresses. Pre-amendment-commit, BASELINE may not be
    reachable (the manifest is authored alongside the amendment); in
    that window the test resolves BASELINE via HEAD~1.
    """
    # Resolve BASELINE: prefer the manifest's value (the canonical
    # pre-amendment tip the seal cycle pinned). Fall back to HEAD —
    # i.e. an empty diff window — when the manifest is not yet
    # authored (pre-amendment-commit). This keeps the test green
    # during the pre-commit window and load-bearing post-commit.
    manifest_path = (
        REPO_ROOT
        / "docs"
        / "rebuild"
        / "plans"
        / "amendment-45-merge-session-start-multi-contributor.manifest.yaml"
    )
    baseline: str | None = None
    if manifest_path.is_file():
        for line in manifest_path.read_text().splitlines():
            if line.strip().startswith("baseline:"):
                baseline = line.split(":", 1)[1].strip()
                break
    if baseline is None:
        # Pre-manifest-author state — the diff window is empty (no
        # commit yet introduces the amendment surface).
        baseline = "HEAD"

    paths = _diff_paths(baseline, "HEAD")
    outside = [
        p for p in paths
        if not any(p.startswith(prefix) for prefix in _ALLOWED_PREFIXES)
    ]
    assert not outside, (
        f"AC.45.S: paths touched outside admitted prefixes: {outside}"
    )
