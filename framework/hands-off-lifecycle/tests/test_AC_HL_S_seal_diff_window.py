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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""AC.HL.S — seal-diff window invariant (fence integrity).

Plan: docs/plans/handsoff-loop-real-build.md (§3 AC.HL.S)

Every path touched between BASELINE and the seal commit lives under
a `workspace-bootstrap`-admitted prefix or universal-file admission.
This is the in-component mirror of the workspace-bootstrap seal-test;
it pins THIS amendment's window specifically.

Pre-apply / pre-seal runs are no-ops (the window does not yet exist).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = (
    REPO_ROOT / "docs" / "plans"
    / "handsoff-loop-real-build.manifest.yaml"
)
SIDECAR = (
    REPO_ROOT / "framework" / "workspace-bootstrap" / "tests"
    / "SEAL_COMMIT"
)

# Subset of the workspace-bootstrap LIVE allowed_prefixes this
# amendment actually touches (verified present in
# framework/workspace-bootstrap/tests/test_no_sealed_amendments.py).
_ALLOWED_PREFIXES: tuple[str, ...] = (
    "framework/tools/",
    "plugins/loam-skills/",
    "framework/hands-off-lifecycle/",
    "framework/workspace-bootstrap/",
    "docs/plans/",
    "docs/design/",
    "docs/experiments/",
)
_ALLOWED_FILES: frozenset[str] = frozenset({
    "CLAUDE.md",
    "docs/STATE.md",
    "docs/release-roadmap.md",
    "docs/release-roadmap-dependency-map.md",
    "README.md",
})


def _baseline_from_manifest() -> str | None:
    if not MANIFEST_PATH.is_file():
        return None
    for line in MANIFEST_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("baseline:"):
            return line.split(":", 1)[1].strip().strip('"')
    return None


def _seal_commit() -> str | None:
    if not SIDECAR.is_file():
        return None
    txt = SIDECAR.read_text(encoding="utf-8").strip()
    return txt if txt and txt != "HEAD" else None


def _diff_paths(baseline: str, seal: str) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "diff", "--name-only",
         f"{baseline}..{seal}"],
        capture_output=True, text=True, check=True,
    )
    return [ln.strip() for ln in result.stdout.splitlines() if ln.strip()]


def test_AC_HL_S_no_path_outside_admitted_window() -> None:
    """BASELINE..seal touches only workspace-bootstrap-admitted paths.

    Build-time test: load-bearing once `loam amend apply`/`seal` have
    written the manifest baseline + the sidecar. Pre-apply == no-op.
    """
    baseline = _baseline_from_manifest()
    seal = _seal_commit()
    if baseline is None or seal is None:
        return  # pre-apply / pre-seal — window not yet realised
    # Only assert the SUBSET of the window this amendment introduced:
    # restrict to paths whose first segment is one this amendment
    # owns, so a co-resident sidecar bump from an unrelated component
    # in the shared workspace-bootstrap sidecar history is not
    # mis-attributed.  Conservative: any path NOT under an admitted
    # prefix / file is the violation.
    outside = [
        p for p in _diff_paths(baseline, seal)
        if not (
            any(p.startswith(pref) for pref in _ALLOWED_PREFIXES)
            or p in _ALLOWED_FILES
        )
    ]
    assert not outside, (
        f"AC.HL.S: paths touched outside the admitted window: {outside}"
    )
