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

"""AC.CLP-CUR.S — sealed-component fence invariant for capability-refresh.

FIRST seal of a brand-new component (amendment
claude-leverage-program-s1-currency). The diff window between the
introduction BASELINE and SEAL_COMMIT must contain ONLY paths under
framework/tools/capability-refresh/ (the new component) + the manifest's
universal-paths admissions (docs/plans/ for the plan-doc + manifest,
docs/capability-corpus/ for the corpus fact-fix + sources.yaml + refresh
state, docs/CLAUDE_CAPABILITIES.md for the D-CLP.5 demotion,
docs/STATE.md + docs/release-roadmap.md for bookkeeping) + any
cross-component partner prefixes admitted by ``loam amend apply``.

Mirror of the loam-acceptance-smoke first-seal fence test. The
``allowed_prefixes`` / ``allowed_files`` names are LOAD-BEARING: the
loam-amend seal-diff binding reader parses these identifiers.

SEAL_COMMIT_PATH reads from tests/SEAL_COMMIT; falls back to HEAD when
absent/placeholder so a build on an unfinished seal still exercises the
test. Post-seal, tests/SEAL_COMMIT carries the exact SHA.

BASELINE history:
  - 266aa93c — HEAD of main at sub-plan authoring (the
    programbench-retirement STATE/roadmap backfill tip); the plan +
    manifest commit 6ea2e6b5 is inside the window under docs/plans/.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
BASELINE = "266aa93cc878f422a20e83376a35bfbd660dad8c"

SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"

allowed_prefixes = (
    "framework/tools/capability-refresh/",
    "docs/plans/",
    "docs/capability-corpus/",
)
allowed_files = {
    "docs/CLAUDE_CAPABILITIES.md",
    "docs/STATE.md",
    "docs/release-roadmap.md",
}


def _seal_commit() -> str:
    """Resolve SEAL_COMMIT from sidecar file, else HEAD."""
    if SEAL_COMMIT_PATH.exists():
        txt = SEAL_COMMIT_PATH.read_text().strip()
        if txt and txt != "HEAD":
            return txt
    return "HEAD"


def test_AC_CLP_CUR_S_only_capability_refresh_changed() -> None:
    """AC.CLP-CUR.S — sealed-component fence invariant (first seal)."""
    seal = _seal_commit()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]
    offenders = [
        ln
        for ln in changed
        if not any(ln.startswith(p) for p in allowed_prefixes)
        and ln not in allowed_files
    ]
    assert not offenders, (
        "sealed-component fence breach: the introduction diff touched paths "
        f"outside the capability-refresh component fence: {offenders}"
    )
