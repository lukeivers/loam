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
secure-build-baseline component + its declared partners (the safety-layer
EXTEND for AC.SBB.1 + the universal-admitted doc/plan + protection-matrix
catalogue surfaces). Zero deltas to any sealed component outside the fence.

Sidecar pattern (matching deploy-safety-floor / protection-matrix):
SEAL_COMMIT reads the exact seal SHA post-seal; pre-seal it reads HEAD so a
build on an unfinished seal still exercises the test.

BASELINE: the commit immediately preceding this cycle's source-edit commit
(the house HEAD~1 advance pattern). This NEW component's first seal fences
against it. The safety-layer extension (AC.SBB.1 — additive staged-diff
secret scan) rides as a declared manifest partner; the protection-matrix
catalogue row(s) + regenerated companion ride as universal-path partners
(plan §6: catalogue rows folded into the sub-cycle's fence as a universal
admission, not a second sealed-component entry).
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
BASELINE = "5d66451fbefc5aca9ea1503c8a0a9169a6bd0efb"

SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"


def _seal_commit() -> str:
    """Resolve SEAL_COMMIT from the sidecar file, else HEAD."""
    if SEAL_COMMIT_PATH.exists():
        txt = SEAL_COMMIT_PATH.read_text().strip()
        if txt and txt != "HEAD":
            return txt
    return "HEAD"


def test_only_secure_build_baseline_and_partners_changed() -> None:
    """No sealed-component surface outside the declared fence moved at seal."""
    seal = _seal_commit()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    # The fence: the new component + the safety-layer EXTEND partner
    # (AC.SBB.1, declared in the manifest's components list) + the
    # universal-admitted doc/plan surfaces + the protection-matrix
    # catalogue row & its generated companion (AC.COV.1).
    allowed_prefixes = (
        "framework/secure-build-baseline/",
        "framework/safety-layer/",
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
