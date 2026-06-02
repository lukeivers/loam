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

"""Seal-fence: the git diff against this slice's BASELINE shows only the
usage-window-guard component + its declared universal-admitted partners.
Zero deltas to any sealed component outside the fence.

Sidecar pattern (matching protection-matrix / state-migration-engine):
SEAL_COMMIT reads the exact seal SHA post-seal; pre-seal it reads HEAD so a
build on an unfinished seal still exercises the test.

BASELINE: a315ed0b — main tip @ plan-authoring on branch
``slice2-insession-subagent-swarm``
(``chore(seals): claude-p-to-insession-subagent-fanout-slice2-swarm``). This
NEW component's first seal fences against it.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
BASELINE = "a315ed0b"

SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"


def _seal_commit() -> str:
    """Resolve SEAL_COMMIT from the sidecar file, else HEAD."""
    if SEAL_COMMIT_PATH.exists():
        txt = SEAL_COMMIT_PATH.read_text().strip()
        if txt and txt != "HEAD":
            return txt
    return "HEAD"


def test_only_usage_window_guard_and_partners_changed() -> None:
    """No sealed-component surface outside the declared fence moved at seal."""
    seal = _seal_commit()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    allowed_prefixes = (
        "framework/usage-window-guard/",
        "docs/plans/",
    )
    allowed_files = {
        "CLAUDE.md",
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
