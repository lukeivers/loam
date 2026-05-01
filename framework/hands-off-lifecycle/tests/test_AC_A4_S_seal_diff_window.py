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

"""AC.A4.S — structural-enforcement A4 seal-diff invariant.

Per the locked plan-doc §4 AC.A4.S: A4's seal-diff window contains
only edits under ``framework/hands-off-lifecycle/{hooks,tests,seals}/``
and the universal-paths admissions (``docs/rebuild/plans/``,
``CLAUDE.md``, ``docs/odd-methodology.md``, ``docs/odd-in-loam.md``,
``docs/rebuild/FUTURE_IDEAS.md``, ``docs/rebuild/FUTURE_IDEAS_DRAFT.md``).

Pinned per ODD §10.3 per-invariant BASELINE convention. Both
endpoints will be constants once amendment #72 seals; pre-seal the
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
    / "structural-enforcement-a4-bash-and-agent-context-guards.manifest.yaml"
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
        "docs/odd-in-loam.md",
        "docs/odd-methodology.md",
        "docs/rebuild/FUTURE_IDEAS.md",
        "docs/rebuild/FUTURE_IDEAS_DRAFT.md",
    }
)


def _seal_commit_for_a4() -> str | None:
    """Return amendment #72's seal commit SHA.

    Both endpoints are constants per the AC.OBG.S authoring pattern
    (also used by AC.MS-fix.S + AC.TDG.S). The seal SHA isn't knowable
    at amendment-author time; filled by a post-seal corrective commit
    immediately after the amendment's seal commit lands.
    """
    # Amendment #72's seal commit SHA — `chore(seals): structural-
    # enforcement A4 Bash/Agent-context guards ... — hands-off-lifecycle
    # at f1ae42b`.
    return "052c9b72cdd11695568c934331ede86ce5f4dad4"


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


def test_AC_A4_S_no_path_outside_admitted_prefixes() -> None:
    """Every path touched between BASELINE and SEAL_COMMIT lives under
    an admitted prefix or is one of the universal-files admissions.

    Skips (returns informationally) when the SEAL_COMMIT is not yet
    pinned — the window does not exist pre-seal."""
    baseline = _baseline_from_manifest()
    seal = _seal_commit_for_a4()
    if baseline is None or seal is None:
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
        f"AC.A4.S: paths touched outside admitted prefixes: {outside}"
    )
