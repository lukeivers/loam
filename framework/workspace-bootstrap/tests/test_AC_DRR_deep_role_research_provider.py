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

"""AC.DRR.* / AC.DRRSEAM.* / AC.DRRGRACE.* / ★ AC.DRROUT.* — the REAL deep
role-research provider (N3 fast-follow, the slice that fills the sealed seam).

The real provider: given a role + opt-in (both established by the sealed intake),
run a BOUNDED three-axis research pass (claude -p subagent, D-RES-1 (a)) ->
SYNTHESIZE a few person-specific leverage ideas -> return the sealed
``RoleResearchResult`` with ``is_stub=False``, which the intake's
``as_leverage_ideas()`` fold-back consumes UNCHANGED.

Test strategy (the outcome-altitude bound, plan §5/§10.5): the deterministic
variant injects a ResearchSource that runs the REAL provider's dispatch+parse+
budget+synthesis path WITHOUT a live network call (so it runs every pass + is
fast). The inner research function being a deterministic source still exercises
the real provider end-to-end — the provider itself is NOT stubbed (AC.DRROUT.1).
An env-gated live ``claude -p`` variant (``LOAM_AC_DRROUT_LIVE=1``) drives the
real subagent for the real-altitude smoke (per the README_3 / cold-walk
convention; cost + non-determinism gated off the always-run suite).
"""

from __future__ import annotations

import json
import os

import pytest

from loam.workspace_bootstrap.deep_role_research import (
    RoleResearchResult,
    StubResearchProvider,
    default_research_provider,
    register_research_provider,
    reset_research_provider,
)
from loam.workspace_bootstrap.deep_role_research_provider import (
    MAX_LEVERAGE_IDEAS,
    MAX_RESEARCH_ROUNDTRIPS,
    AxisResearch,
    ClaudeSubagentResearchSource,
    RawRoleResearch,
    ResearchUnavailableError,
    RoleResearchProvider,
    _parse_research_envelope,
    make_default_research_provider,
)
from loam.workspace_bootstrap.translate_in_intake import run_translate_in_intake


# --- Test doubles: deterministic research sources that drive the REAL path. ---


def _raw_for(role: str, *, roundtrips_each: int = 1) -> RawRoleResearch:
    """A role-derived RawRoleResearch — role-SPECIFIC content per axis so the
    person-specificity probe distinguishes it from a fixed template."""
    return RawRoleResearch(
        role=role,
        effectiveness=AxisResearch(
            "effectiveness",
            f"A {role} is most effective when they batch the routine parts of "
            f"the {role} workflow and protect deep-focus time.",
            roundtrips_each,
        ),
        promotion_criteria=AxisResearch(
            "promotion_criteria",
            f"A {role} gets promoted by visibly owning outcomes beyond the "
            f"day-to-day {role} duties.",
            roundtrips_each,
        ),
        existing_ai_tools=AxisResearch(
            "existing_ai_tools",
            f"Several AI tools already help a {role}; loam could wrap the best "
            f"and rebuild the {role}-specific glue.",
            roundtrips_each,
        ),
    )


class DeterministicSource:
    """A ResearchSource that returns role-derived research WITHOUT a network
    call — exercises the real provider's dispatch boundary + budget + synthesis
    every pass. Records its calls so the bound is observable."""

    def __init__(self, *, roundtrips_each: int = 1):
        self.calls: list[tuple[str, int]] = []
        self._roundtrips_each = roundtrips_each

    def research(self, role: str, *, max_roundtrips: int) -> RawRoleResearch:
        self.calls.append((role, max_roundtrips))
        return _raw_for(role, roundtrips_each=self._roundtrips_each)


class UnavailableSource:
    """A ResearchSource that always fails (no claude binary / dispatch failure /
    timeout) — drives AC.DRRGRACE.1."""

    def research(self, role: str, *, max_roundtrips: int) -> RawRoleResearch:
        raise ResearchUnavailableError("forced-unavailable for the grace test")


class OverBudgetSource:
    """A ResearchSource that overshoots the budget — drives AC.DRR.2's hard cap."""

    def research(self, role: str, *, max_roundtrips: int) -> RawRoleResearch:
        # Report more round-trips than allowed (the parse clamps per-axis, so
        # build the raw directly with an over-budget total to test the provider's
        # own hard-cap enforcement).
        return _raw_for(role, roundtrips_each=max_roundtrips)  # total = 3 * cap


@pytest.fixture(autouse=True)
def _restore_default_provider():
    """Hygiene: any test that registers a real provider restores the stub."""
    yield
    reset_research_provider()


class ScriptedAnswerer:
    def __init__(self, answers: dict[str, str]):
        self._answers = answers
        self.asked: list[str] = []

    def __call__(self, slug: str, prompt: str) -> str:
        self.asked.append(slug)
        return self._answers.get(slug, "")


# ============================================================================
# AC.DRR.* — the provider researches the three axes + synthesizes.
# ============================================================================


def test_AC_DRR_1_real_provider_returns_three_axes_is_stub_false():
    """AC.DRR.1 — a real provider, given a role, returns a synthesis addressing
    all three axes, is_stub=False, distinguishable from the stub."""
    provider = RoleResearchProvider(research_source=DeterministicSource())
    result = provider.research_role("registered nurse")

    assert isinstance(result, RoleResearchResult)
    assert result.is_stub is False
    # All three named axes carry non-stub, role-derived content.
    assert result.effectiveness and "registered nurse" in result.effectiveness
    assert result.promotion_criteria and "registered nurse" in result.promotion_criteria
    assert result.existing_ai_tools and "registered nurse" in result.existing_ai_tools
    # Distinguishable from the sealed stub (which marks is_stub=True + says
    # "full research lands in the fast-follow slice").
    stub = StubResearchProvider().research_role("registered nurse")
    assert stub.is_stub is True
    assert "fast-follow" in stub.effectiveness
    assert "fast-follow" not in result.effectiveness


def test_AC_DRR_2_research_is_bounded_never_exceeds_the_fixed_budget():
    """AC.DRR.2 — the research runs within the fixed D-RES-2 budget; the
    subagent is told the cap, and the provider observes <= the budget."""
    source = DeterministicSource(roundtrips_each=1)
    provider = RoleResearchProvider(research_source=source)
    provider.research_role("data analyst")

    # The source was told the hard cap.
    assert source.calls == [("data analyst", MAX_RESEARCH_ROUNDTRIPS)]
    # The provider recorded <= the budget round-trips (3 axes * 1 = 3 <= 3).
    assert provider.last_roundtrips is not None
    assert provider.last_roundtrips <= MAX_RESEARCH_ROUNDTRIPS


def test_AC_DRR_2_over_budget_source_is_rejected_to_fallback():
    """AC.DRR.2 (hard cap) — a source that overshoots the budget does NOT get a
    real synthesis; the bound is a HARD over-reach-guard constraint, never
    silently exceeded (halt trigger #4 — degrade rather than honor the overshoot)."""
    provider = RoleResearchProvider(research_source=OverBudgetSource())
    result = provider.research_role("teacher")
    # Over-budget research is treated as unusable -> the clearly-marked fallback.
    assert result.is_stub is True
    assert "teacher" in result.effectiveness


def test_AC_DRR_3_output_is_short_and_person_specific_not_a_dump():
    """★ AC.DRR.3 — the surfaced leverage ideas are a FEW (<= MAX_LEVERAGE_IDEAS)
    and reference the role (person-specific); two roles yield two different
    sets (not a fixed template); the raw research is NOT dumped."""
    provider = RoleResearchProvider(research_source=DeterministicSource())

    nurse = provider.research_role("registered nurse")
    analyst = provider.research_role("data analyst")

    nurse_ideas = nurse.as_leverage_ideas()
    analyst_ideas = analyst.as_leverage_ideas()

    # A FEW ideas, never a long dump.
    assert 1 <= len(nurse_ideas) <= MAX_LEVERAGE_IDEAS
    # Person-specific: each idea references the role.
    assert all("registered nurse" in idea for idea in nurse_ideas)
    assert all("data analyst" in idea for idea in analyst_ideas)
    # Two roles -> two different idea sets (not a fixed template).
    assert nurse_ideas != analyst_ideas


# ============================================================================
# AC.DRRSEAM.* — the real provider satisfies the sealed seam exactly.
# ============================================================================


def test_AC_DRRSEAM_1_real_provider_satisfies_protocol_and_foldback_unchanged():
    """AC.DRRSEAM.1 — the real provider IS a ResearchProvider, and the intake's
    as_leverage_ideas() fold-back + close consume its result with NO change to
    translate_in_intake.py."""
    provider = RoleResearchProvider(research_source=DeterministicSource())
    # Structural Protocol compatibility: it has research_role(role)->Result.
    assert hasattr(provider, "research_role")

    # Drive the REAL intake seam (idea-vacuum + role + opt-in) with the real
    # provider injected — the intake code is untouched.
    result = run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {
                "stop_start": "I'm new and overwhelmed",
                "describe_work": "registered nurse",
                "deep_opt_in": "yes",
            }
        ),
        research_provider=provider,
    )
    assert result.invoked_deep_research is True
    assert result.research_result is not None
    assert result.research_result.is_stub is False
    # The intake folded the provider's ideas into its close.
    assert result.has_leverage_idea
    folded = [li.text for li in result.leverage_ideas]
    assert any("registered nurse" in t for t in folded)


def test_AC_DRRSEAM_2_featherlight_invariant_holds_with_real_provider_registered():
    """★ AC.DRRSEAM.2 — with the REAL provider registered behind
    default_research_provider(), a baseline run STILL never invokes research
    (the sealed AC.ONDEEP.1 invariant is not regressed)."""

    class SpyingRealProvider(RoleResearchProvider):
        def __init__(self):
            super().__init__(research_source=DeterministicSource())
            self.invoked_with: list[str] = []

        def research_role(self, role: str) -> RoleResearchResult:
            self.invoked_with.append(role)
            return super().research_role(role)

    spy = SpyingRealProvider()
    register_research_provider(spy)
    assert default_research_provider() is spy

    # 1. A user who named a stop/start thing directly never reaches research.
    run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {"stop_start": "stop doing the weekly board deck", "confirm_proposal": "yes"}
        )
    )
    # 2. An idea-vacuum user with NO role detail never reaches research.
    run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {"stop_start": "I can't think of anything", "describe_work": "not sure"}
        )
    )
    # 3. An idea-vacuum user who DECLINES the deepening never reaches research.
    run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {"stop_start": "no idea", "describe_work": "product manager", "deep_opt_in": "no"}
        )
    )
    # The real provider was registered as default for all three — yet none of
    # the non-(idea-vacuum + role + opt-in) paths invoked it.
    assert spy.invoked_with == []

    # 4. ONLY the idea-vacuum + role + opt-in path reaches it.
    run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {"stop_start": "overwhelmed", "describe_work": "registered nurse", "deep_opt_in": "yes"}
        )
    )
    assert spy.invoked_with == ["registered nurse"]


# ============================================================================
# AC.DRRGRACE.* — graceful degradation + bound enforcement.
# ============================================================================


def test_AC_DRRGRACE_1_unavailable_primitive_returns_marked_fallback_never_raises():
    """AC.DRRGRACE.1 — when the research primitive is unavailable, the provider
    returns a clearly-marked fallback (never raises / hangs / returns empty),
    and the intake's close still surfaces >=1 leverage idea."""
    provider = RoleResearchProvider(research_source=UnavailableSource())

    # Does not raise.
    result = provider.research_role("teacher")
    assert isinstance(result, RoleResearchResult)
    # Clearly-marked degraded (is_stub=True), all three axes named, role-specific.
    assert result.is_stub is True
    assert "teacher" in result.effectiveness
    assert result.promotion_criteria and result.existing_ai_tools

    # Through the real seam: the opt-in close still surfaces >=1 leverage idea.
    intake = run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {"stop_start": "overwhelmed", "describe_work": "teacher", "deep_opt_in": "yes"}
        ),
        research_provider=provider,
    )
    assert intake.invoked_deep_research is True
    assert intake.has_leverage_idea


def test_AC_DRRGRACE_1_claude_subagent_source_degrades_when_spawn_isolation_absent():
    """AC.DRRGRACE.1 — the production ClaudeSubagentResearchSource degrades (raises
    ResearchUnavailableError, caught -> fallback) when loam_spawn_isolation /
    claude is absent, rather than crashing the intake."""
    source = ClaudeSubagentResearchSource()
    # In the always-run suite loam_spawn_isolation is not installed -> the lazy
    # import raises ImportError -> ResearchUnavailableError. (If it IS installed,
    # the claude binary may still be absent / fail -> same error class.) Either
    # way the provider must surface a fallback, not crash.
    provider = RoleResearchProvider(research_source=source)
    result = provider.research_role("registered nurse")
    # Whether the env has spawn-isolation+claude or not, the provider returns a
    # usable RoleResearchResult (real synthesis OR marked fallback) — never raises.
    assert isinstance(result, RoleResearchResult)
    assert result.effectiveness  # never empty


# ============================================================================
# ★ AC.DRROUT.* — the outcome-altitude AC (real provider through the real seam).
# ============================================================================


def test_AC_DRROUT_1_real_provider_through_real_seam_deterministic():
    """★ AC.DRROUT.1 (outcome-altitude) — a REAL provider on a sample role,
    reached through the REAL seam (default_research_provider() resolving to the
    real provider AND the production intake's idea-vacuum opt-in path), ends with
    the four post-conditions: is_stub=False / three axes / <= count
    person-specific ideas / within budget. Deterministic source variant (runs
    every pass; exercises the real dispatch+parse+budget+synthesis path — the
    provider itself is NOT stubbed)."""
    source = DeterministicSource()
    real = RoleResearchProvider(research_source=source)
    # Register behind the production resolver (the real seam).
    register_research_provider(real)
    assert default_research_provider() is real

    # Reach it through the PRODUCTION intake's idea-vacuum opt-in path on a
    # sample role — no research_provider injected, so it resolves the registered
    # default (the real provider).
    result = run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {
                "stop_start": "I'm new and overwhelmed, no idea where to start",
                "describe_work": "registered nurse",
                "deep_opt_in": "yes",
            }
        )
    )

    # (a) a RoleResearchResult with is_stub=False.
    assert result.research_result is not None
    assert result.research_result.is_stub is False
    # (b) the three axes populated with role-derived content.
    rr = result.research_result
    assert "registered nurse" in rr.effectiveness
    assert "registered nurse" in rr.promotion_criteria
    assert "registered nurse" in rr.existing_ai_tools
    # (c) a FEW person-specific leverage ideas folded into the intake's close.
    research_ideas = [
        li for li in result.leverage_ideas if "registered nurse" in li.text
    ]
    assert 1 <= len(research_ideas) <= MAX_LEVERAGE_IDEAS + 1  # +1: the mine-role idea
    assert result.invoked_deep_research is True
    # (d) the research stayed within the budget.
    assert real.last_roundtrips is not None
    assert real.last_roundtrips <= MAX_RESEARCH_ROUNDTRIPS


@pytest.mark.skipif(
    os.environ.get("LOAM_AC_DRROUT_LIVE") != "1",
    reason=(
        "AC.DRROUT.1 outcome-altitude LIVE smoke is gated behind "
        "LOAM_AC_DRROUT_LIVE=1 (spawns a real bounded claude -p research-subagent; "
        "network + subscription cost + non-deterministic). Run manually at "
        "plan-doc §6 step 3/9 post-seal verification: "
        "LOAM_AC_DRROUT_LIVE=1 pytest "
        "framework/workspace-bootstrap/tests/test_AC_DRR_deep_role_research_provider.py"
        " -k live"
    ),
)
def test_AC_DRROUT_1_real_provider_through_real_seam_live_claude_p():
    """★ AC.DRROUT.1 (outcome-altitude, LIVE) — drives the REAL claude -p
    research-subagent (spawn-isolated, no API key, bounded budget) on a sample
    role through the real seam. Env-gated off the always-run suite (cost +
    non-determinism)."""
    real = make_default_research_provider()  # production source: claude -p subagent
    register_research_provider(real)

    result = run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {
                "stop_start": "I'm new and overwhelmed",
                "describe_work": "registered nurse",
                "deep_opt_in": "yes",
            }
        )
    )
    assert result.invoked_deep_research is True
    assert result.research_result is not None
    rr = result.research_result
    # A real subagent run yields a non-stub synthesis on all three axes; on a
    # genuine unavailable/timeout it returns the marked fallback (is_stub=True) —
    # both are valid live outcomes, but the live smoke asserts a non-empty,
    # bounded, role-touching result reached the close.
    assert rr.effectiveness and rr.promotion_criteria and rr.existing_ai_tools
    assert result.has_leverage_idea
    if not rr.is_stub:
        assert real.last_roundtrips is None or real.last_roundtrips <= MAX_RESEARCH_ROUNDTRIPS


# ============================================================================
# Parse-path unit coverage (the real dispatch's parse boundary).
# ============================================================================


def test_parse_research_envelope_tolerates_json_fence_and_extracts_axes():
    """The real parse path tolerates a ```json fence + extracts the three axes
    + clamps reported round-trips to the budget."""
    fenced = (
        "```json\n"
        + json.dumps(
            {
                "effectiveness": "Batch the routine parts.",
                "promotion_criteria": "Own outcomes visibly.",
                "existing_ai_tools": "Wrap the best AI scheduling tools.",
                "roundtrips_used": 99,  # over-report -> clamped to the budget
            }
        )
        + "\n```"
    )
    raw = _parse_research_envelope("nurse", fenced, MAX_RESEARCH_ROUNDTRIPS)
    assert raw.effectiveness.summary == "Batch the routine parts."
    assert raw.promotion_criteria.summary == "Own outcomes visibly."
    assert raw.existing_ai_tools.summary
    # Clamped: total never exceeds the budget despite the over-report.
    assert raw.total_roundtrips <= MAX_RESEARCH_ROUNDTRIPS


def test_parse_research_envelope_raises_on_missing_axis():
    """A research envelope missing an axis is unusable -> ResearchUnavailableError
    (the provider then returns the AC.DRRGRACE.1 fallback)."""
    bad = json.dumps({"effectiveness": "x", "promotion_criteria": "y"})  # no tools axis
    with pytest.raises(ResearchUnavailableError):
        _parse_research_envelope("nurse", bad, MAX_RESEARCH_ROUNDTRIPS)
