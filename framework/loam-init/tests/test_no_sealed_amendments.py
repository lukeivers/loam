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

"""AC.FBE.1.S — sealed-component fence invariant for loam-init.

git diff against the pre-amendment BASELINE shows only loam-init/
changes (plus universal-paths admissions + cross-component partners).
Zero deltas to any other sealed component.

Mirror of the standard sealed-component fence test (cost-governance/
self-correction/workspace-bootstrap precedent). SEAL_COMMIT_PATH reads
from tests/SEAL_COMMIT; falls back to HEAD when absent/placeholder so
builds on an unfinished seal still exercise the test. Post-seal,
tests/SEAL_COMMIT carries the exact SHA and the diff is deterministic.

BASELINE history:
  - b111340 (FBE.1 plan-doc commit — pre-amendment tip; the seal
    commit will land at FBE.1's apply + seal commits via `loam amend
    apply` per the standard sidecar pattern).
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BASELINE = "cfc9ed4"

SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"


def _seal_commit() -> str:
    """Resolve SEAL_COMMIT from sidecar file, else HEAD."""
    if SEAL_COMMIT_PATH.exists():
        txt = SEAL_COMMIT_PATH.read_text().strip()
        if txt and txt != "HEAD":
            return txt
    return "HEAD"


def test_AC_FBE_1_S_only_loam_init_changed() -> None:
    """AC.FBE.1.S — sealed-component fence invariant.

    The diff window between FBE.1's BASELINE and SEAL_COMMIT contains
    only paths under framework/loam-init/ (the new component) +
    universal-paths admissions (docs/rebuild/plans/, partition manifest
    file via universal_paths.prefixes) + cross-component partner
    prefixes admitted by `loam amend apply` from the manifest.
    """
    seal = _seal_commit()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    # `docs/rebuild/plans/` admits the plan-before-code paper trail
    # (FBE.1 sub-plan + manifest YAML + parent plan-doc backfill).
    # `framework/tools/pos-publish-framework-only/` admits the single-
    # line partition-manifest edit (universal_paths.prefixes pattern,
    # mirroring M7-partition-fix amendment #98).
    # `framework/loam-init/` is the sealed-component fence itself.
    # Bare-name `loam-init/` retained for back-compat with pre-D.1
    # baselines (matches the pattern used by every other sealed
    # component's fence test).
    allowed_prefixes = (
        "framework/loam-init/",
        "loam-init/",
        "docs/rebuild/plans/",
        "framework/tools/pos-publish-framework-only/",
        "dev-sdlc/",
        "framework/dev-sdlc/",
        "framework/workspace-bootstrap/",
        "workspace-bootstrap/",
    )
    allowed_files: set[str] = {
        "CLAUDE.md",
        "docs/odd-in-loam.md",
        "docs/odd-methodology.md",
        "docs/rebuild/FUTURE_IDEAS.md",
        "docs/rebuild/FUTURE_IDEAS_DRAFT.md",
        "docs/install-from-source.md",
        "install-from-source.txt",
    }

    offending = []
    for path in changed:
        if any(path.startswith(p) for p in allowed_prefixes):
            continue
        if path in allowed_files:
            continue
        offending.append(path)
    assert offending == [], (
        f"Sealed-component paths modified outside loam-init/ fence: "
        f"{offending}. Halt-signal condition (AC.FBE.1.S)."
    )
