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

"""AC.SE.S — structural-enforcement A1 substrate seal-diff invariant.

Per the locked plan-doc §4 AC.SE.S: the seal-diff window for the A1
amendment contains only edits under ``hands-off-lifecycle/``,
``objective-tracker/``, and the universal-paths admissions
(``docs/rebuild/plans/``, ``CLAUDE.md``, ``docs/odd-methodology.md``,
``docs/odd-in-loam.md``, ``docs/rebuild/FUTURE_IDEAS.md``,
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


REPO_ROOT = Path(__file__).resolve().parents[3]
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
        "docs/odd-in-loam.md",
        "docs/odd-methodology.md",
        "docs/rebuild/FUTURE_IDEAS.md",
        ".gitignore",
    }
)


def _seal_commit_from_manifest_sibling() -> str | None:
    """Return A1's historical seal commit SHA.

    Originally this read the live SEAL_COMMIT sidecar — but that
    sidecar is shared across every hands-off-lifecycle amendment and
    advances with each loam amend seal. The test's intent is "A1's
    amendment window stayed clean" — a HISTORICAL fact about a single
    amendment, not a live property. Tighten the AC per ODD §4 / the
    loose-AC-text-fix convention by hardcoding A1's seal SHA. Pre-D.1
    this test passed because the live sidecar happened to still equal
    A1's seal (no intervening hands-off-lifecycle amendments had
    bumped it). D.1 is the first such bump; the brittle live-read
    pattern surfaces and is replaced.
    """
    # A1's seal commit — `chore(seals): structural-enforcement A1
    # substrate ... at 97f7829` (commit d4dcfa9; sealed value 97f7829).
    return "97f78290f6a810957dc0bd0c8a6a1d4b96524f65"


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
    a build-time test that becomes load-bearing once ``loam amend
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
