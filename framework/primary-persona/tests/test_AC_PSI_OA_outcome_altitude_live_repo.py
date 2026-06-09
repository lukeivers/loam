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
entry points report a real plan currently in partial build-state, and
the reported state matches INDEPENDENT git verification performed by
this test (its own ``git log`` probe), not by the module under test.

No fixtures, no injected derivation — the production registry + the
live repo. Skips only when the live loam repo is absent on this host
(environment-specific target, mirroring the AC-FBM-STATE-LIVE-4
precedent); on the build host it runs for real.
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


def _independent_subjects(repo: Path) -> str:
    """The test's OWN git probe — independent of the module under
    test (it shells git directly and never imports plan_state)."""
    proc = subprocess.run(
        ["git", "-C", str(repo), "log", "--format=%s"],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    return proc.stdout


@pytest.mark.skipif(
    not (_LIVE_LOAM / "docs" / "plans").is_dir(),
    reason="live loam repo absent on this host; outcome-altitude target unavailable",
)
def test_AC_PSI_OA_live_partial_plan_reported_and_independently_verified() -> None:
    from loam_cli.audit.plan_state import (  # production derivation
        BUILD_STATE_PARTIAL,
        derive_plan_states,
    )

    derived = derive_plan_states("loam")  # production registry, live repo
    assert derived, "the live loam repo must derive a non-empty plan index"

    partial = [p for p in derived if p.build_state == BUILD_STATE_PARTIAL]
    assert partial, (
        "the live repo must report at least one plan in partial "
        "build-state (apply/seal evidence, no sealed-archive narrative)"
    )

    # INDEPENDENT verification: for every reported-partial plan, the
    # test's own git probe must find an apply/seal subject naming the
    # slug, and the sealed archive must NOT carry its narrative.
    subjects = _independent_subjects(_LIVE_LOAM)
    for plan in partial:
        assert (
            f"chore(amend): {plan.slug}" in subjects
            or f"chore(seals): {plan.slug}" in subjects
        ), (
            f"reported-partial plan {plan.slug!r} has no apply/seal "
            f"commit in the independent git probe"
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
def test_AC_PSI_OA_live_surfacing_and_query_report_the_partial_plan() -> None:
    """The production SURFACING entry points (the turn block + the
    query) report a real partial plan, live, no pre-arranged state."""
    from loam_cli.audit.plan_state import (
        BUILD_STATE_PARTIAL,
        derive_plan_states,
    )

    derived = derive_plan_states("loam")
    partial = [p for p in derived if p.build_state == BUILD_STATE_PARTIAL]
    assert partial

    block = render_plans_block()  # production: live derivation, TTL, cap
    assert block.startswith("[plan-state]"), "the live plans block must render"
    assert "partially built" in block

    # The query surface resolves one real partial plan's topic to its
    # real state (the surface the claim guard consumes).
    target = partial[0]
    result = query_plan_state(target.slug.replace("-", " "))
    assert any(
        m["slug"] == target.slug
        and m["build_state"] == BUILD_STATE_PARTIAL
        and m["seal_evidence"]
        for m in result["matches"]
    ), (
        f"the production query must surface {target.slug!r} as "
        f"partially-sealed with evidence; got: {result['matches'][:3]}"
    )
