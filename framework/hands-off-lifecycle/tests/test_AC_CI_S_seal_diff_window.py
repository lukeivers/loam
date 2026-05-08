# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""AC.CI.S — corpus-inlining-session-start-hook seal-diff invariant.

Per the locked plan-doc §4 AC.CI.S: the seal-diff window for this
amendment contains only edits under
``framework/hands-off-lifecycle/{hooks,tests,seals}/`` plus the
universal-paths admissions
(``docs/plans/``, ``CLAUDE.md``, ``docs/odd-methodology.md``,
``docs/odd-in-loam.md``, ``docs/FUTURE_IDEAS.md``,
``docs/FUTURE_IDEAS_DRAFT.md``).

Pinned per ODD §10.3 per-invariant BASELINE convention: this test
asserts the window of THIS amendment specifically, not the floating
component-level window the existing
``hands-off-lifecycle/tests/test_cross_cutting.py::test_H19_*``
covers.

The test reads the amendment's manifest's ``baseline:`` literal and
the seal-diff sidecar at
``framework/hands-off-lifecycle/seals/SEAL_COMMIT.<slug>``; the
sidecar is written/advanced by ``loam amend seal``. Pre-apply / pre-
seal runs are no-ops (the sidecar / SHA do not yet exist).
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = (
    REPO_ROOT
    / "docs"
    / "plans"
    / "corpus-inlining-session-start-hook.manifest.yaml"
)
SIDECAR_PATH = (
    REPO_ROOT
    / "framework"
    / "hands-off-lifecycle"
    / "seals"
    / "SEAL_COMMIT.corpus-inlining-session-start-hook"
)


_ALLOWED_PREFIXES: tuple[str, ...] = (
    "framework/hands-off-lifecycle/hooks/",
    "framework/hands-off-lifecycle/tests/",
    "framework/hands-off-lifecycle/seals/",
    "docs/plans/",
    "docs/rebuild/plans/",  # historical pre-v0.3.0-C1 path retained for diff-window check
)
_ALLOWED_FILES: frozenset[str] = frozenset(
    {
        "CLAUDE.md",
        "docs/odd-in-loam.md",
        "docs/odd-methodology.md",
        "docs/FUTURE_IDEAS.md",
        "docs/FUTURE_IDEAS_DRAFT.md",
    }
)


def _baseline_from_manifest() -> str | None:
    if not MANIFEST_PATH.is_file():
        return None
    for line in MANIFEST_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("baseline:"):
            return line.split(":", 1)[1].strip()
    return None


def _seal_commit_sha() -> str | None:
    if not SIDECAR_PATH.is_file():
        return None
    text = SIDECAR_PATH.read_text(encoding="utf-8").strip()
    # The sidecar may contain commentary + the SHA on its own line.
    # The loam amend convention is the SHA on the first line; if the
    # file is the narrative-then-SHA shape, we accept either.
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for ln in lines:
        if len(ln) == 40 and all(c in "0123456789abcdef" for c in ln):
            return ln
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


def test_AC_CI_S_no_path_outside_admitted_prefixes() -> None:
    """Every path touched between BASELINE and SEAL_COMMIT lives
    under an admitted prefix or is one of the universal-files
    admissions.

    Skips if the manifest or sidecar is not yet authored — this is
    a build-time test that becomes load-bearing once ``loam amend
    apply`` writes both. Pre-apply runs are no-ops (the test is
    informational until this amendment's window exists)."""
    baseline = _baseline_from_manifest()
    seal = _seal_commit_sha()
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
        f"AC.CI.S: paths touched outside admitted prefixes: {outside}"
    )
