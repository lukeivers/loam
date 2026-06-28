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

"""Seal-fence: the git diff against this cycle's BASELINE shows only the
deploy-safety-floor component + its declared universal-admitted partners.
Zero deltas to any sealed component outside the fence.

Sidecar pattern (matching deliberate-reasoning / protection-matrix):
SEAL_COMMIT reads the exact seal SHA post-seal; pre-seal it reads HEAD so a
build on an unfinished seal still exercises the test.

BASELINE: the plan-doc commit — the commit immediately preceding this
cycle's source-edit commit (the house HEAD~1 advance pattern). Advanced for
the fail-policy-adoption micro-cycle (e0e9a258) so the diff window carries
only this cycle's de-dup changes; leaving it at Sub-cycle A's f27bbd66 would
pull intervening safety-layer edits into the window. The protection-matrix
catalogue row + regenerated companion remain admitted as universal-path
partners (they do not move in this de-dup cycle).
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
BASELINE = "e0e9a258f12231fa22785d90d791d4729562e434"

SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"


def _seal_commit() -> str:
    """Resolve SEAL_COMMIT from the sidecar file, else HEAD."""
    if SEAL_COMMIT_PATH.exists():
        txt = SEAL_COMMIT_PATH.read_text().strip()
        if txt and txt != "HEAD":
            return txt
    return "HEAD"


def test_only_deploy_safety_floor_and_partners_changed() -> None:
    """No sealed-component surface outside the declared fence moved at seal."""
    seal = _seal_commit()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    # The fence: the new component + the universal-admitted doc/plan surfaces
    # + the protection-matrix catalogue row & its generated companion
    # (AC.COV.1, admitted per plan §6).
    allowed_prefixes = (
        "framework/deploy-safety-floor/",
        "docs/plans/",
    )
    allowed_files = {
        "CLAUDE.md",
        "docs/STATE.md",
        "docs/FUTURE_IDEAS_DRAFT.md",
        "docs/design/protection-matrix.md",
        "framework/protection-matrix/data/failure-mode-guard-matrix.yaml",
    }

    offending = []
    for path in changed:
        if any(path.startswith(p) for p in allowed_prefixes):
            continue
        if path in allowed_files:
            continue
        offending.append(path)
    assert offending == [], (
        f"Sealed-component paths modified outside the fence: {offending}. "
        f"Halt-signal condition."
    )
