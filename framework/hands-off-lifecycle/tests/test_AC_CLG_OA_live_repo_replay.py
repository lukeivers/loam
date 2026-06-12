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

"""AC.CLG.OA (outcome-altitude: true) — the literal 2026-06-09 failure
replayed against PRODUCTION machinery and caught: against the LIVE
repo with NO pre-arranged state, through the production gate entry
point,

  (a) a draft asserting that a real, evidence-backed plan "isn't
      planned / doesn't exist" produces a steer citing that plan's
      real evidence + REAL build-state;
  (b) a draft asserting a genuinely-sealed item is sealed produces NO
      steer.

RE-GROUNDED by plan-state-false-partial-fix (AC.PSTATE.5): the replay
no longer requires the live repo to carry a partially-sealed plan —
that requirement was an artefact of the false-partial defect (the
seal-reachability verdict flips the legacy-narrative plans to sealed,
and the live repo may legitimately have zero partials). The 06-09
failure shape (denying work that exists) is steered for ANY
evidence-backed plan, sealed or partial; the steer carries whichever
build-state is real.

No fixtures, no injected query — the gate reaches the live Slice-1
plan-state surface, which derives from the live git ref graph. Skips
only when the live loam repo is absent on this host.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
KEEP_PACE_DIR = (
    REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks" / "keep_pace"
)
sys.path.insert(0, str(KEEP_PACE_DIR))

from draft_gate import Verdict, gate  # noqa: E402

_LIVE_LOAM = Path("/Users/lukeivers/loam")

# Words that would trip the gate's Layer-1 jargon lint or its seeded
# constraint topics — the OA drafts are authored from a plan's slug
# words and must isolate the CLAIM-GUARD behaviour, so plans whose
# identity collides with other layers' vocabulary are skipped as draft
# sources (plenty of others exist).
_NOISY_WORDS = frozenset(
    {
        "amendment", "manifest", "commit", "component", "cycle",
        "pytest", "seal", "seals", "sealed", "odd", "claude", "api",
        "anthropic", "model", "llm", "aaron", "pod",
    }
)


def _clean_slug_words(slug: str) -> str:
    words = [w for w in slug.split("-") if w and w.lower() not in _NOISY_WORDS]
    return " ".join(words).lower()


def _pick(plans, state: str) -> tuple:
    """A (plan, topic) pair whose slug words are layer-clean and
    distinctive enough to resolve."""
    for plan in plans:
        if plan.build_state != state:
            continue
        topic = _clean_slug_words(plan.slug)
        if len(topic.split()) >= 3:
            return plan, topic
    return None, ""


def _pick_evidence_backed(plans) -> tuple:
    """A (plan, topic) pair with REAL build evidence (sealed or
    partial — AC.PSTATE.5: the 06-09 replay must not depend on the
    live repo carrying a partial plan)."""
    for plan in plans:
        if not plan.seal_evidence:
            continue
        topic = _clean_slug_words(plan.slug)
        if len(topic.split()) >= 3:
            return plan, topic
    return None, ""


@pytest.mark.skipif(
    not (_LIVE_LOAM / "docs" / "plans").is_dir(),
    reason="live loam repo absent on this host; outcome-altitude target unavailable",
)
def test_AC_CLG_OA_the_0609_failure_is_caught_live() -> None:
    """(a) — the false negative about a real evidence-backed plan is
    steered with that plan's real evidence + real build-state,
    through gate()."""
    from loam_cli.audit.plan_state import derive_plan_states

    plans = derive_plan_states("loam")
    assert plans
    target, topic = _pick_evidence_backed(plans)
    assert target is not None, "the live repo must carry an evidence-backed plan"

    draft = f"As far as I can tell, the {topic} work isn't planned and doesn't exist."
    result = gate(draft)  # the production entry point, live ground truth

    cg = [r for r in result.reasons if r.layer == "CG"]
    assert cg, (
        f"the live replay of the 06-09 failure must be caught; draft was "
        f"{draft!r}, verdict {result.verdict}"
    )
    assert result.verdict == Verdict.FLAG, (
        "the catch is a steer (FLAG), never a blocked send (D2)"
    )
    details = " ".join(r.detail for r in cg)
    assert (
        target.slug in details or target.title in details
    ), f"the steer must cite the real plan's evidence; got: {details}"
    assert target.build_state in details, (
        f"the steer must carry the REAL build-state "
        f"({target.build_state!r}); got: {details}"
    )


@pytest.mark.skipif(
    not (_LIVE_LOAM / "docs" / "plans").is_dir(),
    reason="live loam repo absent on this host; outcome-altitude target unavailable",
)
def test_AC_CLG_OA_true_sealed_claim_passes_live() -> None:
    """(b) — a true claim about a genuinely-sealed item passes with no
    claim-guard steer, live."""
    from loam_cli.audit.plan_state import derive_plan_states

    plans = derive_plan_states("loam")
    target, topic = _pick(plans, "sealed")
    assert target is not None, "the live repo must carry sealed plans"

    draft = f"The {topic} work is already shipped."
    result = gate(draft)
    cg = [r for r in result.reasons if r.layer == "CG"]
    assert cg == [], (
        f"a ground-truth-confirmed claim must pass un-steered; draft "
        f"{draft!r} got: {[r.detail for r in cg]}"
    )
