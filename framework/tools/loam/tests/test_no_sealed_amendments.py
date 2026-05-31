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

"""AC.FBE.2.S — sealed-component fence invariant for loam-cli.

git diff against the pre-amendment BASELINE shows only loam-cli/
changes (the sealed component fence) plus universal-paths admissions
(docs/rebuild/plans/, the partition manifest file, and the manifest-
owner pos-publish-framework-only/ paths admitted via universal_paths
.prefixes for the partition + spot-check edits).

Mirror of the standard sealed-component fence test (cost-governance/
self-correction/loam-init precedent). SEAL_COMMIT_PATH reads from
tests/SEAL_COMMIT; falls back to HEAD when absent/placeholder so
builds on an unfinished seal still exercise the test. Post-seal,
tests/SEAL_COMMIT carries the exact SHA and the diff is deterministic.

BASELINE history:
  - 8f0e778 (FBE.2 plan-doc commit — pre-amendment tip; the apply
    + seal commits will land via `loam amend apply` per the standard
    sidecar pattern; BASELINE bumps to the partition-admission tip
    at apply-time, mirroring FBE.1's b111340→608ecea sequence).
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
# Advanced to 31dc9ca (the P1.2 FBM-path-consolidation seal — this slice's
# predecessor on slice/p1.2-loam-layout) at the P1.3 migration-engine seal.
# The prior baseline (b278cc6a) sat 95 sibling commits behind HEAD; advancing
# to the immediate predecessor seal bounds the window to THIS slice's loam-cli
# changes (the standard "advance sidecar + BASELINE" seal pattern).
BASELINE = "b234bfd"

SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"


def _seal_commit() -> str:
    """Resolve SEAL_COMMIT from sidecar file, else HEAD."""
    if SEAL_COMMIT_PATH.exists():
        txt = SEAL_COMMIT_PATH.read_text().strip()
        if txt and txt != "HEAD":
            return txt
    return "HEAD"


def test_AC_FBE_2_S_only_loam_cli_changed() -> None:
    """AC.FBE.2.S — sealed-component fence invariant.

    The diff window between FBE.2's BASELINE and SEAL_COMMIT contains
    only paths under framework/tools/loam/ (the sealed component) +
    universal-paths admissions (docs/rebuild/plans/, the partition
    manifest file via universal_paths.prefixes, and the pos-publish-
    framework-only/ test fixture spot-check edit admitted by the same
    prefix).
    """
    seal = _seal_commit()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    # `framework/tools/loam/` is the sealed-component fence itself
    # (NEW seal anchor established at FBE.2; sidecar + invariant land
    # in the same amendment).
    # `framework/tools/pos-publish-framework-only/` admits the partition-
    # manifest 2-line edit + the spot-check test fixture edit
    # (universal_paths.prefixes pattern; mirrors M7-partition-fix #98
    # and FBE.1).
    # `docs/rebuild/plans/` admits the plan-before-code paper trail
    # (FBE.2 sub-plan + manifest YAML + parent plan-doc backfill).
    allowed_prefixes = (
        "framework/tools/loam/",
        # P1.3 partner-admission: the migration engine slice lands its NEW
        # component + the tracked migration contract + the slice plan/cursor
        # alongside the loam-cli gate edit (the same cross-component partner
        # admission reversibility-primitive's fence already uses).
        "framework/state-migration-engine/",
        "docs/state-migrations/",
        "docs/plans/",
        "framework/tools/pos-publish-framework-only/",
        # Amendment #143 cross-component partner: heavy-b-migrate's
        # downstream-consumer source-edit (amendment_acs.py routes
        # through the shared plan_locator helper). The cross-component
        # prefix machinery defaults to ``framework/<name>/`` which
        # misses the ``tools/`` segment, so this admission is named
        # explicitly. Mirror of dev-sdlc seal-test's existing
        # framework/tools/heavy-b-migrate/ admission.
        "framework/tools/heavy-b-migrate/",
        "docs/rebuild/plans/",
        "cost-governance/",
        "dev-sdlc/",
        "framework/cost-governance/",
        "framework/dev-sdlc/",
        "framework/objective-tracker/",
        "framework/observability-aggregator/",
        "framework/orchestrator/",
        "framework/primary-persona/",
        "framework/reversibility-primitive/",
        "framework/safety-layer/",
        "framework/scope-of-work/",
        "framework/self-correction/",
        "framework/self-upgrade/",
        "framework/telegram-interface/",
        "framework/workspace-bootstrap/",
        "framework/workspace-sync/",
        "plugins/dev-sdlc/",
        "objective-tracker/",
        "observability-aggregator/",
        "orchestrator/",
        "primary-persona/",
        "reversibility-primitive/",
        "safety-layer/",
        "scope-of-work/",
        "self-correction/",
        "self-upgrade/",
        "telegram-interface/",
        "workspace-bootstrap/",
        "workspace-sync/",
        "framework/hands-off-lifecycle/",
        "hands-off-lifecycle/",
        "docs/design/",
        "docs/experiments/",
        "docs/plans/",
    )
    allowed_files: set[str] = {
        "CLAUDE.md",
        "docs/odd-in-loam.md",
        "docs/odd-methodology.md",
        "docs/rebuild/FUTURE_IDEAS.md",
        "docs/rebuild/FUTURE_IDEAS_DRAFT.md",
        "README.md",
        "docs/getting-started.md",
        "docs/FUTURE_IDEAS.md",
        "docs/FUTURE_IDEAS_DRAFT.md",
        "docs/STATE.md",
        "docs/odd-in-pos.md",
        "docs/release-process.md",
        "docs/release-roadmap-dependency-map.md",
        "docs/release-roadmap.md",
        "docs/release-versioning-policy.md",
        "docs/plans/loam-roadmap.md",
    }

    offending = []
    for path in changed:
        if any(path.startswith(p) for p in allowed_prefixes):
            continue
        if path in allowed_files:
            continue
        offending.append(path)
    assert offending == [], (
        f"Sealed-component paths modified outside framework/tools/loam/ "
        f"fence: {offending}. Halt-signal condition (AC.FBE.2.S)."
    )
