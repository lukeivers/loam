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
adversarial-review component + its SKILL partner (plugins/loam-skills/) +
the universal-admitted doc/plan surfaces. Zero deltas to any sealed
component outside the fence — in particular the sealed
`framework/tools/loam-spawn-isolation/` surface is NOT touched (the
capability composes on it by importing/naming, never editing — plan §4
fence).

Two-component cycle (adversarial-review NEW + loam-skills EXTEND): the
SKILL lands under `plugins/loam-skills/skills/adversarial-review/`, so
`plugins/loam-skills/` is an admitted partner prefix here; the reverse
seal-fence (loam-skills' own test) admits `framework/adversarial-review/`
in kind.

Sidecar pattern (matching local-deploy-tier / deploy-safety-floor):
SEAL_COMMIT reads the exact seal SHA post-seal; pre-seal it reads HEAD so
a build on an unfinished seal still exercises the test.

BASELINE: the canonical tip at build-dispatch (the release worktree's
starting HEAD == origin/main == local main). This NEW component's first
seal fences against it. `loam amend` rewrites this literal to the
manifest baseline at apply/seal.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
BASELINE = "a4c08928cddb0cb268e779f31ebfdf60620253e6"

SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"


def _seal_commit() -> str:
    """Resolve SEAL_COMMIT from the sidecar file, else HEAD."""
    if SEAL_COMMIT_PATH.exists():
        txt = SEAL_COMMIT_PATH.read_text().strip()
        if txt and txt != "HEAD":
            return txt
    return "HEAD"


def test_only_adversarial_review_and_skill_partner_changed() -> None:
    """No sealed-component surface outside the declared fence moved at seal."""
    seal = _seal_commit()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    # The fence: the NEW component + its SKILL partner. The sealed
    # loam-spawn-isolation surface is composed-on (imported), never edited.
    allowed_prefixes = (
        "framework/adversarial-review/",
        "plugins/loam-skills/",
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
