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

"""AC.SMOKE.S — sealed-component fence invariant for loam-acceptance-smoke.

This is the FIRST seal of a brand-new component. The diff window between the
introduction BASELINE and SEAL_COMMIT must contain ONLY paths under
framework/tools/loam-acceptance-smoke/ (the new component) +
universal-paths admissions (docs/plans/, docs/experiments/ for the run-report)
+ any cross-component partner prefixes admitted by `loam amend apply` from the
manifest.

Mirror of the standard sealed-component fence test (loam-init / workspace-
bootstrap precedent). SEAL_COMMIT_PATH reads from tests/SEAL_COMMIT; falls back
to HEAD when absent/placeholder so a build on an unfinished seal still
exercises the test. Post-seal, tests/SEAL_COMMIT carries the exact SHA and the
diff is deterministic.

BASELINE history:
  - f614d5af (the foundation-polish tip the smoke was dispatched off — the
    pre-introduction tip; the apply + seal commits land the new component).
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
BASELINE = "625303cf"

SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"

# The component's own prefix + the universal admissions a first-seal of an
# acceptance-test component legitimately touches (the plan-doc + manifest that
# introduce it, and the run-report experiment doc the smoke produces).
_ALLOWED_PREFIXES = (
    "framework/tools/loam-acceptance-smoke/",
    "docs/plans/",
    "docs/experiments/",
)


def _seal_commit() -> str:
    """Resolve SEAL_COMMIT from sidecar file, else HEAD."""
    if SEAL_COMMIT_PATH.exists():
        txt = SEAL_COMMIT_PATH.read_text().strip()
        if txt and txt != "HEAD":
            return txt
    return "HEAD"


def test_AC_SMOKE_S_only_acceptance_smoke_changed() -> None:
    """AC.SMOKE.S — sealed-component fence invariant (first seal).

    The diff window between the introduction BASELINE and SEAL_COMMIT contains
    only paths under framework/tools/loam-acceptance-smoke/ (the new component)
    + the universal admissions (plan-doc + manifest + the run-report).
    """
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
        if not any(ln.startswith(p) for p in _ALLOWED_PREFIXES)
    ]
    assert not offenders, (
        "sealed-component fence breach: the introduction diff touched paths "
        f"outside the loam-acceptance-smoke component fence: {offenders}"
    )
