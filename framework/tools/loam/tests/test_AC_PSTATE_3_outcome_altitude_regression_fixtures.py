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

"""AC.PSTATE.3 (outcome-altitude: true) — the four 2026-06-11
false-positive plans derive ``sealed`` against the LIVE loam repo
(plan-state-false-partial-fix regression fixtures).

The production entry point (``derive_plan_states("loam")``, production
registry, no pre-arranged state) must report the four plans that fed
false build-dispatch premises on 2026-06-11 as ``sealed``; INDEPENDENT
git verification (this test's own ``git log`` probe — never the module
under test) confirms each fixture's newest slug-named evidence is a
completed ``chore(seals):`` subject AND its doc is absent from the
sealed archive — proving the seal-reachability predicate (not archive
presence) produced the verdict. Skips only when the live loam repo is
absent on this host (the AC.PSI.OA precedent).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

_LIVE_LOAM = Path("/Users/lukeivers/loam")

#: The dispatch-named regression fixtures (FIDRAFT
#: F-PLANSTATE-FALSE-PARTIAL; slice2 the minimum, all four named).
_FIXTURE_SLUGS = (
    "claude-p-to-insession-subagent-fanout-slice2-swarm",
    "deep-role-research-provider",
    "egress-consent-core-and-bug-report",
    "dev-pattern-simplifications-1",
)


def _independent_subjects(repo: Path) -> list[str]:
    """The test's OWN git probe, newest first — independent of the
    module under test."""
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
def test_AC_PSTATE_3_live_regression_fixtures_derive_sealed() -> None:
    from loam_cli.audit.plan_state import (  # production derivation
        BUILD_STATE_SEALED,
        derive_plan_states,
    )

    derived = derive_plan_states("loam")  # production registry, live repo
    assert derived, "the live loam repo must derive a non-empty plan index"
    by_slug = {p.slug: p for p in derived}

    subjects = _independent_subjects(_LIVE_LOAM)
    for slug in _FIXTURE_SLUGS:
        assert slug in by_slug, f"regression fixture {slug!r} not derived"
        plan = by_slug[slug]
        assert plan.build_state == BUILD_STATE_SEALED, (
            f"{slug!r} must derive sealed (the 2026-06-11 false positive); "
            f"got {plan.build_state!r}"
        )
        assert plan.seal_evidence, "the sealed verdict must carry its evidence"

        # INDEPENDENT verification that the NEW predicate (not archive
        # presence) produced the verdict: newest slug evidence is a
        # completed seal subject; no sealed-archive narrative exists.
        newest = _newest_evidence_subject(slug, subjects)
        assert newest.startswith("chore(seals): "), (
            f"{slug!r}: independent probe expected a completed seal as the "
            f"newest evidence; got {newest!r}"
        )
        assert not (
            _LIVE_LOAM / "docs" / "plans" / "sealed" / f"{slug}.md"
        ).is_file(), (
            f"{slug!r} has a sealed-archive narrative — this fixture no "
            f"longer exercises the seal-reachability arm; pick a "
            f"legacy-narrative fixture"
        )
