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

"""AC.PSI.OA (outcome-altitude: true) — against the LIVE loam repo
with NO pre-arranged state: the production derivation + surfacing
entry points report REAL plan build-state, and every reported state
matches INDEPENDENT git verification performed by this test (its own
``git log`` probe), not by the module under test.

RE-GROUNDED by plan-state-false-partial-fix (AC.PSTATE.4): the
original premise — "the live repo must carry at least one
partially-sealed plan" — was an artefact of the false-partial defect
(18 fully-sealed legacy-narrative plans mis-reported as partial).
Post-fix the live repo may legitimately carry zero partial plans, so
the outcome verified here is the honest one: NOTHING the surfaces
report as "partially built" is seal-reachable, and the four 2026-06-11
regression fixtures are never so reported.

No fixtures, no injected derivation — the production registry + the
live repo. Skips only when the live loam repo is absent on this host.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from loam.primary_persona.keep_pace.plans_state import (
    query_plan_state,
    render_plans_block,
)

_LIVE_LOAM = Path("/Users/lukeivers/loam")

#: The plan-state-false-partial-fix regression fixtures (AC.PSTATE.4).
_FIXTURE_SLUGS = (
    "claude-p-to-insession-subagent-fanout-slice2-swarm",
    "deep-role-research-provider",
    "egress-consent-core-and-bug-report",
    "dev-pattern-simplifications-1",
)


def _independent_subjects(repo: Path) -> list[str]:
    """The test's OWN git probe — independent of the module under
    test (it shells git directly and never imports plan_state)."""
    proc = subprocess.run(
        ["git", "-C", str(repo), "log", "--format=%s"],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    return proc.stdout.splitlines()


def _newest_evidence_subject(slug: str, subjects: list[str]) -> str:
    for subject in subjects:
        for prefix in ("chore(amend): ", "chore(seals): "):
            candidate = prefix + slug
            if subject == candidate or subject.startswith(candidate + " "):
                return subject
    return ""


@pytest.mark.skipif(
    not (_LIVE_LOAM / "docs" / "plans").is_dir(),
    reason="live loam repo absent on this host; outcome-altitude target unavailable",
)
def test_AC_PSI_OA_live_reported_states_independently_verified() -> None:
    from loam_cli.audit.plan_state import (  # production derivation
        BUILD_STATE_PARTIAL,
        BUILD_STATE_SEALED,
        derive_plan_states,
    )

    derived = derive_plan_states("loam")  # production registry, live repo
    assert derived, "the live loam repo must derive a non-empty plan index"
    by_slug = {p.slug: p for p in derived}
    subjects = _independent_subjects(_LIVE_LOAM)

    # The regression fixtures are sealed, never partial (AC.PSTATE.4).
    for slug in _FIXTURE_SLUGS:
        assert by_slug[slug].build_state == BUILD_STATE_SEALED, (
            f"{slug!r} is seal-reachable and must derive sealed; got "
            f"{by_slug[slug].build_state!r}"
        )

    # INDEPENDENT verification of every reported-partial plan: it is
    # genuinely mid-cycle — slug-named evidence exists, the NEWEST
    # evidence is NOT a completed seal, and no archive narrative exists.
    for plan in derived:
        if plan.build_state != BUILD_STATE_PARTIAL:
            continue
        newest = _newest_evidence_subject(plan.slug, subjects)
        assert newest, (
            f"reported-partial plan {plan.slug!r} has no apply/seal "
            f"commit in the independent git probe"
        )
        assert not newest.startswith("chore(seals): "), (
            f"reported-partial plan {plan.slug!r} has a completed seal "
            f"as its newest evidence — it should have derived as sealed"
        )
        assert not (
            _LIVE_LOAM / "docs" / "plans" / "sealed" / f"{plan.slug}.md"
        ).is_file(), (
            f"reported-partial plan {plan.slug!r} HAS a sealed-archive "
            f"narrative — it should have derived as sealed"
        )
        assert plan.seal_evidence, "partial state must carry its evidence"


@pytest.mark.skipif(
    not (_LIVE_LOAM / "docs" / "plans").is_dir(),
    reason="live loam repo absent on this host; outcome-altitude target unavailable",
)
def test_AC_PSI_OA_live_surfacing_never_reports_sealed_as_partial() -> None:
    """The production SURFACING entry points (the turn block + the
    query), live, no pre-arranged state: no seal-reachable plan is
    ever shown as "partially built" (AC.PSTATE.4); the query reports
    the slice2 regression fixture as sealed with evidence."""
    from loam_cli.audit.plan_state import (
        BUILD_STATE_SEALED,
        derive_plan_states,
    )

    derived = derive_plan_states("loam")
    by_slug = {p.slug: p for p in derived}

    block = render_plans_block()  # production: live derivation, TTL, cap
    # The live repo carries planned-not-built docs, so the block renders.
    assert block.startswith("[plan-state]"), "the live plans block must render"

    # No "partially built" line names a sealed plan (the contributor
    # surface the 2026-06-11 false premises came from).
    sealed_titles = {
        p.title for p in derived if p.build_state == BUILD_STATE_SEALED
    }
    for line in block.splitlines():
        if "partially built" not in line:
            continue
        for title in sealed_titles:
            assert title not in line, (
                f"sealed plan {title!r} reported partially built: {line!r}"
            )

    # The query surface (the claim guard's ground truth) reports the
    # slice2 fixture's REAL state.
    target = by_slug["claude-p-to-insession-subagent-fanout-slice2-swarm"]
    result = query_plan_state(target.slug.replace("-", " "))
    assert any(
        m["slug"] == target.slug
        and m["build_state"] == BUILD_STATE_SEALED
        and m["seal_evidence"]
        for m in result["matches"]
    ), (
        f"the production query must surface {target.slug!r} as sealed "
        f"with evidence; got: {result['matches'][:3]}"
    )
