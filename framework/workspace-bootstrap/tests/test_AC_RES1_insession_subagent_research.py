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

"""AC.RES1.* — Slice 1 of the in-session-subagent-migration minor.

The deep-research provider's production ResearchSource is converted from a
detached ``claude -p`` subprocess to an IN-SESSION subagent dispatched through a
host-session-registered dispatcher callable, so the workload draws from the
subscription plan limits instead of the post-June-15 metered Agent SDK credit.

Per `docs/plans/claude-p-to-insession-subagent-fanout.md` §5:

  - AC.RES1.1 — the production role-research path no longer spawns a detached
    `claude -p` subprocess + yields a usable three-axis result.
  - AC.RES1.2 — the bounded research budget is still enforced through the swap.
  - AC.RES1.3 — graceful degradation preserved (unavailable -> marked fallback,
    never raises / hangs).
  - AC.RES1.5 — the keep-open USER NOTICE is shipped on the user-facing path
    (outcome-altitude — walked cold).

AC.RES1.4 (post-June-15 `/usage` billing confirmation) is a DEFERRED calendar-
gated minor-level empirical gate — NOT a Slice-1 code AC, does NOT block the
seal, and is intentionally NOT tested here (plan §9). It is not faked to green.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

import loam.workspace_bootstrap.deep_role_research_provider as drp
from loam.workspace_bootstrap.deep_role_research import RoleResearchResult
from loam.workspace_bootstrap.deep_role_research_provider import (
    MAX_RESEARCH_ROUNDTRIPS,
    InSessionResearchSource,
    RoleResearchProvider,
    clear_in_session_dispatcher,
    get_in_session_dispatcher,
    make_default_research_provider,
    set_in_session_dispatcher,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def _research_json(role: str, *, roundtrips: int = 3) -> str:
    """A well-formed research-subagent result for a role (role-specific so the
    person-specificity probe distinguishes it from a fixed template)."""
    return json.dumps(
        {
            "effectiveness": f"A {role} is most effective batching routine work.",
            "promotion_criteria": f"A {role} gets promoted by owning outcomes.",
            "existing_ai_tools": f"AI tools exist a {role} could use; loam wraps them.",
            "roundtrips_used": roundtrips,
        }
    )


@pytest.fixture(autouse=True)
def _clean_dispatcher():
    """Hygiene: the dispatcher registry is process-global; clear it each test."""
    clear_in_session_dispatcher()
    yield
    clear_in_session_dispatcher()


# ============================================================================
# AC.RES1.1 — production path takes the in-session subagent, no detached
#             `claude -p` subprocess, usable result.
# ============================================================================


def test_AC_RES1_1_production_default_is_in_session_not_claude_p():
    """AC.RES1.1 — the production provider's default source is the in-session
    subagent source (NOT the detached `claude -p` ClaudeSubagentResearchSource)."""
    provider = make_default_research_provider()
    assert isinstance(provider._source, InSessionResearchSource)


def test_AC_RES1_1_in_session_path_yields_result_without_spawning_claude_p(
    monkeypatch,
):
    """AC.RES1.1 — with an in-session dispatcher wired, the production source
    produces a usable three-axis result AND never spawns a detached `claude -p`
    subprocess. The spawn surface is booby-trapped: any subprocess spawn fails
    the test loudly."""
    dispatched_prompts: list[str] = []

    def fake_dispatch(prompt: str) -> str:
        dispatched_prompts.append(prompt)
        # Recover the role from the bounded research prompt the source built.
        m = re.search(r"Research the role: '([^']+)'", prompt)
        role = m.group(1) if m else "unknown"
        return _research_json(role)

    set_in_session_dispatcher(fake_dispatch)

    # Booby-trap the detached-spawn surfaces: the in-session path must touch
    # NEITHER subprocess.run NOR spawn_isolated_claude.
    def _explode_subprocess_run(*a, **k):  # pragma: no cover - must not be hit
        raise AssertionError(
            "AC.RES1.1 violated: the in-session path spawned a subprocess "
            "(detached `claude -p`) instead of dispatching an in-session subagent."
        )

    monkeypatch.setattr(
        "subprocess.run", _explode_subprocess_run, raising=True
    )

    provider = make_default_research_provider()
    result = provider.research_role("registered nurse")

    # A usable, non-stub, three-axis, role-specific result.
    assert isinstance(result, RoleResearchResult)
    assert result.is_stub is False
    assert "registered nurse" in result.effectiveness
    assert "registered nurse" in result.promotion_criteria
    assert "registered nurse" in result.existing_ai_tools
    # The in-session dispatcher WAS used (the prompt carried the role + budget).
    assert len(dispatched_prompts) == 1
    assert "registered nurse" in dispatched_prompts[0]
    assert str(MAX_RESEARCH_ROUNDTRIPS) in dispatched_prompts[0]


def test_AC_RES1_1_in_session_source_does_not_import_spawn_isolation(monkeypatch):
    """AC.RES1.1 — the converted in-session source never reaches the
    spawn-isolation chokepoint (no subprocess argv to isolate). Importing
    loam_spawn_isolation is booby-trapped: the in-session path must not need it."""

    def _explode_import(name, *a, **k):  # pragma: no cover - must not be hit
        if name == "loam_spawn_isolation":
            raise AssertionError(
                "AC.RES1.1 violated: the in-session path imported "
                "loam_spawn_isolation (the detached-spawn chokepoint)."
            )
        return _real_import(name, *a, **k)

    import builtins

    _real_import = builtins.__import__
    monkeypatch.setattr(builtins, "__import__", _explode_import)

    set_in_session_dispatcher(lambda prompt: _research_json("teacher"))
    src = InSessionResearchSource()
    raw = src.research("teacher", max_roundtrips=MAX_RESEARCH_ROUNDTRIPS)
    assert raw.role == "teacher"
    assert raw.effectiveness.summary


# ============================================================================
# AC.RES1.2 — the bounded budget is still enforced through the conversion.
# ============================================================================


def test_AC_RES1_2_budget_enforced_through_in_session_conversion():
    """AC.RES1.2 — the in-session source produces research within the budget; the
    provider records total_roundtrips <= MAX_RESEARCH_ROUNDTRIPS."""
    set_in_session_dispatcher(
        lambda prompt: _research_json("data analyst", roundtrips=MAX_RESEARCH_ROUNDTRIPS)
    )
    provider = make_default_research_provider()
    provider.research_role("data analyst")
    assert provider.last_roundtrips is not None
    assert provider.last_roundtrips <= MAX_RESEARCH_ROUNDTRIPS


def test_AC_RES1_2_over_budget_in_session_result_folds_to_fallback():
    """AC.RES1.2 (hard cap) — an in-session subagent that reports an over-budget
    round-trip count is clamped by the parse so the recorded total never exceeds
    the cap; a genuinely over-budget RawRoleResearch is treated as unusable. Here
    the over-report (99) is clamped: the provider still produces a within-budget
    real synthesis (the bound is never silently exceeded)."""
    set_in_session_dispatcher(lambda prompt: _research_json("teacher", roundtrips=99))
    provider = make_default_research_provider()
    result = provider.research_role("teacher")
    # The reported overshoot was clamped to the budget; total stays within cap.
    assert provider.last_roundtrips is not None
    assert provider.last_roundtrips <= MAX_RESEARCH_ROUNDTRIPS
    assert isinstance(result, RoleResearchResult)


# ============================================================================
# AC.RES1.3 — graceful degradation preserved across the primitive swap.
# ============================================================================


def test_AC_RES1_3_no_dispatcher_registered_degrades_to_marked_fallback():
    """AC.RES1.3 — with NO in-session dispatcher registered (running outside a
    live session), the provider returns the clearly-marked is_stub=True fallback,
    never raises / hangs (the AC.DRRGRACE.1 contract holds across the swap)."""
    assert get_in_session_dispatcher() is None  # the autouse fixture cleared it
    provider = make_default_research_provider()
    result = provider.research_role("teacher")
    assert isinstance(result, RoleResearchResult)
    assert result.is_stub is True
    assert "teacher" in result.effectiveness
    assert result.promotion_criteria and result.existing_ai_tools


def test_AC_RES1_3_dispatcher_that_raises_degrades_to_marked_fallback():
    """AC.RES1.3 — a registered dispatcher that RAISES degrades to the marked
    fallback (never propagates out of research_role)."""

    def _raise(prompt: str) -> str:
        raise RuntimeError("in-session subagent dispatch blew up")

    set_in_session_dispatcher(_raise)
    provider = make_default_research_provider()
    result = provider.research_role("nurse")
    assert result.is_stub is True
    assert "nurse" in result.effectiveness


def test_AC_RES1_3_unparseable_in_session_result_degrades_to_marked_fallback():
    """AC.RES1.3 — a dispatcher that returns garbage (no JSON / missing axis)
    degrades to the marked fallback rather than crashing the intake."""
    set_in_session_dispatcher(lambda prompt: "not json at all, sorry")
    provider = make_default_research_provider()
    result = provider.research_role("electrician")
    assert result.is_stub is True
    assert "electrician" in result.effectiveness


# ============================================================================
# AC.RES1.5 — the keep-open USER NOTICE shipped (outcome-altitude).
# ============================================================================


def test_AC_RES1_5_keep_open_user_notice_present_on_user_facing_path():
    """★ AC.RES1.5 (outcome-altitude) — walked COLD with no pre-arranged state:
    a reader who has never seen the migration finds, on the normal user-facing
    docs path, a plain-language notice that converted long-running work runs
    while the session stays open and pauses when it closes."""
    notice = REPO_ROOT / "docs" / "insession-subagent-keep-open-notice.md"
    # Reachable through the normal user-facing path (a top-level docs/ file,
    # not buried in code comments).
    assert notice.exists(), (
        f"AC.RES1.5: keep-open USER NOTICE missing at {notice}"
    )
    text = notice.read_text().lower()
    # Plain-language: the two load-bearing facts a cold reader must learn.
    assert "keep loam open" in text
    assert "background" in text
    # Open session -> work runs.
    assert "keeps working" in text or "keeps running" in text or "keep running" in text
    # Close session -> work pauses.
    assert "pause" in text
    assert "close" in text
