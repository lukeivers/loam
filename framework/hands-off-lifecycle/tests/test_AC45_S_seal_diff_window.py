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

Amendment #46 §2.5 fix: the original v1 of this test diffed
``BASELINE..HEAD`` rather than ``BASELINE..SEAL_COMMIT``. That made
the diff window expand monotonically as later amendments landed —
intervening commits (#38–#44 and the heavy-b-migrate / pos-amend
extensions that landed after #45's seal) naturally fell outside #45's
admission set, breaking the test on every later seal cycle. Per
``test_no_sealed_amendments.py``'s ``_seal_commit()`` pattern (the
project-wide convention every other sealed-component seal-diff test
uses), the upper bound of an amendment-window diff is the amendment's
SEAL_COMMIT, not HEAD. Per ODD §2.5 + the dispatcher-side "halt and
surface §2.5 violations in surrounding code" CDC, amendment #46
repairs this rather than silently extending the broken assertion.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


# Allowed prefixes for amendment #45's diff window. Mirrors the
# manifest's ``components`` + ``universal_paths`` declarations.
_ALLOWED_PREFIXES: tuple[str, ...] = (
    "hands-off-lifecycle/",
    "tools/loam-mode/",
    "docs/rebuild/plans/",
    # Universal admissions per amendment #22 ruling #3.
    "CLAUDE.md",
    "docs/odd-in-loam.md",
    "docs/odd-methodology.md",
    "docs/rebuild/FUTURE_IDEAS.md",
)


# Amendment-#45-specific upper bound: the test asserts amendment #45's
# diff window was clean. That window is by construction
# ``c046f78..0702d25`` (#45's pre-amendment tip → #45's seal commit).
# Both endpoints are constants after #45 sealed; the test must NOT
# float either endpoint with subsequent amendment cycles, otherwise
# the assertion drifts away from its declared invariant. The
# component-wide ``hands-off-lifecycle/tests/SEAL_COMMIT`` sidecar
# legitimately advances on every later amendment (#46 advances it),
# but that sidecar tracks the LATEST seal — not #45's.
#
# Per ODD §2.5 the AC's intent maps to a constant range. The fix
# matches the per-invariant-BASELINE pattern documented in
# ``docs/odd-in-loam.md`` §10 (extended here to cover the upper bound
# of an amendment-specific window).
_AMENDMENT_45_SEAL_COMMIT = "0702d25ee97927aa6035e6dcff0a7490ec5cb5fd"


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
    """Every path touched between the amendment BASELINE and the
    amendment's SEAL_COMMIT lives under an admitted prefix.

    Test name retains the historical ``_against_HEAD`` suffix for
    test-discovery stability across amendment #46's §2.5 repair; the
    upper bound now resolves through ``_seal_commit()`` per the
    project-wide convention.
    """
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

    paths = _diff_paths(baseline, _AMENDMENT_45_SEAL_COMMIT)
    outside = [
        p for p in paths
        if not any(p.startswith(prefix) for prefix in _ALLOWED_PREFIXES)
    ]
    assert not outside, (
        f"AC.45.S: paths touched outside admitted prefixes: {outside}"
    )
