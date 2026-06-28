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
local-deploy-tier component (P1) + the universal-admitted doc/plan surfaces.
Zero deltas to any sealed component outside the fence — in particular the
sealed deploy-safety-floor and secure-build-baseline are NOT touched (P1
composes on them by reading/naming, never editing — plan §P1 fence,
shared-contract §5.2 D-SC.3).

Sidecar pattern (matching deploy-safety-floor / secure-build-baseline):
SEAL_COMMIT reads the exact seal SHA post-seal; pre-seal it reads HEAD so a
build on an unfinished seal still exercises the test.

BASELINE: the canonical tip immediately preceding this cycle's source-edit
commit (the house HEAD~1 advance pattern). This NEW component's first seal
fences against it.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
BASELINE = "2409dc48d4d964a61ae3b368c36eb057a92b8966"

SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"


def _seal_commit() -> str:
    """Resolve SEAL_COMMIT from the sidecar file, else HEAD."""
    if SEAL_COMMIT_PATH.exists():
        txt = SEAL_COMMIT_PATH.read_text().strip()
        if txt and txt != "HEAD":
            return txt
    return "HEAD"


def test_only_local_deploy_tier_and_partners_changed() -> None:
    """No sealed-component surface outside the declared fence moved at seal."""
    seal = _seal_commit()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    # The fence: the NEW component only. No other framework/ component moves —
    # the floor + secure-build baseline are composed-on, never edited.
    allowed_prefixes = (
        "framework/local-deploy-tier/",
        "docs/plans/",
        "docs/design/",
    )
    allowed_files = {
        "CLAUDE.md",
        "docs/STATE.md",
        "docs/release-roadmap.md",
        "docs/FUTURE_IDEAS_DRAFT.md",
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
