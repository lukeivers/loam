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
protection-matrix component + its declared universal-admitted partners. Zero
deltas to any sealed component outside the fence.

Sidecar pattern (matching state-migration-engine / reversibility-primitive /
loam-cli): SEAL_COMMIT reads the exact seal SHA post-seal; pre-seal it reads
HEAD so a build on an unfinished seal still exercises the test.

BASELINE: d9ece972 — the current main tip + merge-base of
``plan/failure-mode-guard-matrix`` (N4 §14 method-decision register backfill).
This NEW component's first seal fences against it.

BASELINE history:
  ec7b666 — the catalogue-track-and-rows follow-on (track the gitignored
            source-of-truth catalogue + the FM.PROCESS-DRIFT / FM.COMMS-PATH-DEAD
            rows + the narration fold).
  949fced9 — the silent-egress-row follow-on (add FM.SILENT-EGRESS). The prior
            BASELINE ec7b666 predated the entire v1.0.0 lockstep release, so the
            stale BASELINE..SEAL_COMMIT window spanned every release-cut
            component and would falsely trip the single-component fence. Advanced
            BASELINE to 949fced9 (the main tip immediately before this
            amendment's source commit — the documented HEAD~1 advance pattern)
            so the window shows only this amendment's protection-matrix +
            docs/plans/ + generated-companion surfaces.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
BASELINE = "949fced9"

SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"


def _seal_commit() -> str:
    """Resolve SEAL_COMMIT from the sidecar file, else HEAD."""
    if SEAL_COMMIT_PATH.exists():
        txt = SEAL_COMMIT_PATH.read_text().strip()
        if txt and txt != "HEAD":
            return txt
    return "HEAD"


def test_only_protection_matrix_and_partners_changed() -> None:
    """No sealed-component surface outside the declared fence moved at seal."""
    seal = _seal_commit()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    # The fence: the new component + the universal-admitted doc/plan surfaces
    # (manifest universal_paths) + the generated companion + the doctrine
    # backfill pointer.
    allowed_prefixes = (
        "framework/protection-matrix/",
        "docs/plans/",
        "docs/state-migrations/",  # the declared no-op migration (plan §9).
    )
    allowed_files = {
        "CLAUDE.md",
        "docs/odd-in-loam.md",
        "docs/odd-methodology.md",
        "docs/STATE.md",
        "docs/release-roadmap.md",
        "docs/design/loam-doctrine.md",
        "docs/design/protection-matrix.md",
        ".gitignore",
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
