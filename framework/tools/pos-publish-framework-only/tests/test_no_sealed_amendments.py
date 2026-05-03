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

"""AC.FBE.2b.S — sealed-component fence invariant for pos-publish-framework-only.

git diff against the pre-amendment BASELINE shows only paths under
framework/tools/pos-publish-framework-only/ (the sealed component
fence) plus universal-paths admissions (docs/rebuild/plans/, plus
the standard cross-component partner-prefix admissions inherited
from the FBE.5 fence-fifteen baseline shape).

Mirror of the standard sealed-component fence test (cost-governance/
self-correction/loam-init/loam-cli precedent). SEAL_COMMIT_PATH reads
from tests/SEAL_COMMIT; falls back to HEAD when absent/placeholder so
builds on an unfinished seal still exercise the test. Post-seal,
tests/SEAL_COMMIT carries the exact SHA and the diff is
deterministic.

NEW seal anchor established at FBE.2b. Pre-FBE.2b, the manifest-
owner component rode universal-paths admission alone (verified at
FBE.2 + FBE.5 — no `tests/SEAL_COMMIT` or
`test_no_sealed_amendments.py`). FBE.2b is a substantive code edit
(synth.py + cli.py + 3 in-fence test files), so the universal-
paths-only ride is no longer enough; the sidecar lands in the same
amendment as the code edit (mirroring FBE.2's loam-cli pattern).

BASELINE history:
  - 2ac582f (FBE.2b plan-doc commit — pre-amendment tip; the apply
    + seal commits will land via `loam amend apply` per the standard
    sidecar pattern; BASELINE bumps to the source-edit tip at
    apply-time, mirroring FBE.2's 0f75364→80d52ab sequence).
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
BASELINE = "03f261e"

SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"


def _seal_commit() -> str:
    """Resolve SEAL_COMMIT from sidecar file, else HEAD."""
    if SEAL_COMMIT_PATH.exists():
        txt = SEAL_COMMIT_PATH.read_text().strip()
        if txt and txt != "HEAD":
            return txt
    return "HEAD"


def test_AC_FBE_2b_S_only_pos_publish_framework_only_changed() -> None:
    """AC.FBE.2b.S — sealed-component fence invariant.

    The diff window between FBE.2b's BASELINE and SEAL_COMMIT
    contains only paths under framework/tools/pos-publish-framework-only/
    (the sealed component) + universal-paths admissions
    (docs/rebuild/plans/) + standard cross-component partner-prefix
    admissions inherited from the FBE.5 fence-fifteen baseline shape
    (per FBE.4/FBE.5 partner-prefix gap precedent — `loam amend
    apply` derives partner_prefixes assuming `framework/<name>/` for
    every fence component, so admit defensively).
    """
    seal = _seal_commit()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    # `framework/tools/pos-publish-framework-only/` is the sealed-
    # component fence itself (NEW seal anchor established at FBE.2b;
    # sidecar + invariant + substantive code edit all land in the
    # same amendment).
    # `docs/rebuild/plans/` admits the plan-before-code paper trail
    # (FBE.2b sub-plan + manifest YAML + parent plan-doc backfill).
    # The cross-component partner-prefix admissions mirror FBE.2's
    # loam-cli sidecar shape (defensive — the FBE.4/FBE.5
    # partner-prefix gap means apply tool derives partner_prefixes
    # assuming `framework/<name>/`; harmless to admit one anchor's
    # peer prefixes here so a future cross-fence amendment touching
    # this component doesn't trip).
    allowed_prefixes = (
        "framework/tools/pos-publish-framework-only/",
        "docs/rebuild/plans/",
        "cost-governance/",
        "dev-sdlc/",
        "framework/cost-governance/",
        "framework/dev-sdlc/",
        "framework/loam-init/",
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
        "framework/tools/loam/",
        "framework/workspace-bootstrap/",
        "framework/workspace-sync/",
        "loam-init/",
        "objective-tracker/",
        "observability-aggregator/",
        "orchestrator/",
        "plugins/dev-sdlc/",
        "pos-publish-framework-only/",
        "primary-persona/",
        "reversibility-primitive/",
        "safety-layer/",
        "scope-of-work/",
        "self-correction/",
        "self-upgrade/",
        "telegram-interface/",
        "workspace-bootstrap/",
        "workspace-sync/",
    )
    allowed_files: set[str] = {
        "CLAUDE.md",
        "docs/odd-in-loam.md",
        "docs/odd-methodology.md",
        "docs/rebuild/FUTURE_IDEAS.md",
        "docs/rebuild/FUTURE_IDEAS_DRAFT.md",
        "README.md",
        "docs/getting-started.md",
    }

    offending = []
    for path in changed:
        if any(path.startswith(p) for p in allowed_prefixes):
            continue
        if path in allowed_files:
            continue
        offending.append(path)
    assert offending == [], (
        f"Sealed-component paths modified outside "
        f"framework/tools/pos-publish-framework-only/ fence: "
        f"{offending}. Halt-signal condition (AC.FBE.2b.S)."
    )
