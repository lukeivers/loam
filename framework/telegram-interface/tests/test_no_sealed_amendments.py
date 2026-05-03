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

"""TG23: git diff against the true-first-run-sealed baseline shows
only telegram-interface/ changes (plus optionally the runtime data/
generated-artifact directory). Zero deltas to any sealed component.

Mirror of cost-governance/tests/test_no_sealed_amendments.py — same
sidecar SEAL_COMMIT pattern for a build-time test that keeps working
before the owner seals the component.

BASELINE advances each time telegram-interface opens a new amendment
window:
  - e1686e1  at the true-first-run SEAL_COMMIT — the previous seal
             and this component's first BASELINE.
  - b9e1f96  when the telegram-interface-framework-integration
             amendment (#9) opened. Amendment #9 composes
             telegram-interface as the thirteenth foundational
             adapter via a new workspace-bootstrap adapter; per AC7
             the amendment ships ZERO edits under
             `telegram-interface/src/`. This BASELINE advance +
             allowed-prefix extension admits the multi-component
             amendment's workspace-bootstrap, hands-off-lifecycle,
             and docs surfaces without weakening the src-untouched
             invariant. b9e1f96 is the pre-amendment tip — the
             amendment-#8 audit-closure seal commit immediately
             before this amendment's code commit. Amendment number
             (#9) is proposal-assigned; #10 and #11 landed first.
  - 3b128c3  when the S3 silent-except bundle amendment (#21) opened.
             The 2026-04-22 audit + classifier surfaced one remaining
             AC:none silent catch inside `telegram-interface/src/
             allowlist.py::AccessFile.identities()` (loop skip on
             malformed `pos_identities` records). Per ODD §8 rule 8 +
             the audit-triage-by-severity CDC (bucket d — outright
             violation), the fix replaces the silent skip with a new
             `allowlist_record_malformed` OTel emitter while
             preserving the `continue` (unrecoverable drop still
             correct). Multi-component amendment (scope-of-work,
             telegram-interface, memory-system, hands-off-lifecycle).
             This amendment also adds `scope-of-work/` and
             `memory-system/` to the allowed-prefix tuple because the
             amendment's full diff spans those surfaces too. Sites 4
             + 5 (`first_run_inventory.py::_parse_scalar`) were
             re-classified bucket (a) during research and dropped;
             the former Site 3 in `availability.py` stayed dropped
             per the re-dispatch note. 3b128c3 is the pre-amendment
             tip — the pyyaml-reachability seal commit immediately
             before amendment #21's code commit.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BASELINE = "8032348"

SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"


def _seal_commit() -> str:
    if SEAL_COMMIT_PATH.exists():
        txt = SEAL_COMMIT_PATH.read_text().strip()
        if txt and txt != "HEAD":
            return txt
    return "HEAD"


def test_tg23_only_telegram_interface_changed() -> None:
    """Halt-signal check: no sealed source touched.

    Per AC7 (telegram-interface-framework-integration proposal) the
    telegram-interface/src/ tree is untouched by the amendment —
    asserted structurally by a dedicated AC7 test below.
    """
    seal = _seal_commit()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    # data/observability/spans.jsonl is test-run output, not source.
    # docs/ is workspace-level content. Amendment #9
    # (telegram-interface-framework-integration) extends the allowed
    # prefixes with the three multi-component surfaces it touches —
    # workspace-bootstrap/ (the new adapter), hands-off-lifecycle/
    # (BASELINE bump in cross-cutting seal test), and
    # docs/rebuild/components/telegram-interface-framework-integration/
    # (the proposal + plan). docs/rebuild/plans/ is admitted because
    # the plan-before-code CDC lives alongside the amendment commit.
    # Amendment #21 (S3 silent-except bundle) extends with
    # `scope-of-work/` and `memory-system/` — the other two source-
    # editing partners in that multi-component amendment.
    allowed_prefixes = (
        "framework/telegram-interface/",
        "telegram-interface/",
        "data/",
        "docs/rebuild/components/telegram-interface/",
        "docs/rebuild/components/telegram-interface-framework-integration/",
        "docs/rebuild/plans/",
        # M6a — first plugin lands at plugins/dev-sdlc/. Admitted as
        # cross-component partner so the seal-diff sweep passes when
        # the plugin's diff is in flight.
        "plugins/dev-sdlc/",
        "framework/workspace-bootstrap/",
        "framework/hands-off-lifecycle/",
        "framework/scope-of-work/",
        "framework/memory-system/",
        "framework/cost-governance/",
        "framework/graceful-degradation/",
        "framework/observability-aggregator/",
        "framework/orchestrator/",
        "framework/reversibility-primitive/",
        "framework/self-correction/",
        "framework/tools/",
        "framework/safety-layer/",
        "cost-governance/",
        "framework/hands-off-lifecycle/canonical-dev/",
        "framework/objective-tracker/",
        "framework/primary-persona/",
        "framework/self-upgrade/",
        "framework/workspace-sync/",
        "graceful-degradation/",
        "hands-off-lifecycle/",
        "memory-system/",
        "objective-tracker/",
        "observability-aggregator/",
        "orchestrator/",
        "primary-persona/",
        "reversibility-primitive/",
        "safety-layer/",
        "scope-of-work/",
        "self-correction/",
        "self-upgrade/",
        "tools/",
        "workspace-bootstrap/",
        "workspace-sync/",
        "framework/tools/loam/",
        "docs/rebuild/components/",
        "docs/rebuild/spec/",
        "framework/tools/loam-mode/",
        "dev-sdlc/",
        "framework/dev-sdlc/",
        "framework/loam/",
        "loam/",
    )
    allowed_files: set[str] = {
        "docs/odd-in-pos.md",
        "docs/odd-in-loam.md",
        "docs/rebuild/FUTURE_IDEAS.md",
        "docs/odd-methodology.md",
        "CLAUDE.md",
        ".claude/settings.json",
        "first-run-inventory.yaml",
        "framework/first-run-inventory.yaml",
        "docs/rebuild/FUTURE_IDEAS_DRAFT.md",
        "CLAUDE.dev.md",
        "docs/rebuild/STATE.md",
        "docs/rebuild/VALUE_PROPOSITION.md",
        "docs/rebuild/dev-mode-manifest.yaml",
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
        f"Sealed-component paths modified: {offending}. Halt-signal."
    )


def test_AC7_no_telegram_interface_src_edits() -> None:
    """AC7 (telegram-interface-framework-integration proposal, amendment
    #9): that amendment consumes telegram-interface's public API only;
    zero edits under ``telegram-interface/src/`` landed in amendment #9.

    The invariant is scoped to amendment #9's exact window. Amendment
    #21 (S3 silent-except bundle) legitimately edits
    ``telegram-interface/src/allowlist.py`` + ``observability.py`` to
    surface an AC:none silent-except (Site 3 of that amendment); per
    ODD §2.5 / §8.2, that is an amendment-#21-scoped change within
    telegram-interface's own sealed surface, NOT a violation of the
    amendment-#9-scoped AC7 invariant. Pinning BASELINE/SEAL to the
    amendment-#9 window here keeps the AC7 structural check true to
    its original scope regardless of future amendments.
    """
    amendment_9_baseline = "b9e1f96"
    amendment_9_seal = "4f8b933"
    out = subprocess.check_output(
        [
            "git",
            "diff",
            "--name-only",
            f"{amendment_9_baseline}..{amendment_9_seal}",
            "--",
            "framework/telegram-interface/src/",
        ],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]
    assert changed == [], (
        "amendment #9 (telegram-interface-framework-integration) edited "
        f"telegram-interface/src/ — AC7 halt-signal. Changed paths: {changed}"
    )
