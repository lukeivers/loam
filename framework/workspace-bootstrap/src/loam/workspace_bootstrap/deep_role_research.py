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

"""N3 deep-role-research SEAM (slice N3 baseline / AC.ONDEEP.1).

**D-5 (a) — RATIFIED.** The deep role-research PASS itself (a per-user
web-research + three-axis synthesis: what makes someone effective at a role /
what gets them promoted / which existing AI solutions loam could wrap or
rebuild) is its OWN fast-follow slice (AC.ONDEEP.2). N3 baseline ships ONLY:

  - the clean INTERFACE the baseline intake composes on (``ResearchProvider``);
  - the opt-in OFFER + the gate that keeps it OFF the baseline first-touch path;
  - a featherlight stub provider so the baseline DEGRADES GRACEFULLY when the
    real research pass is absent (the no-interrogation-by-weight backstop).

The featherlight invariant (AC.ONDEEP.1): the research interface is reached
ONLY from the bottom of the idea-quality continuum (an idea-vacuum user who
gave real role detail AND opted in). A user who names a stop/start thing
directly, OR gives no role detail, OR declines the deepening NEVER reaches it.
The intake (``translate_in_intake``) owns that gate; this module owns the
interface + the graceful-degradation stub.

The real pass (the fast-follow) composes the Claude-native
forked-context-research-subagent primitive (``WebSearch`` + ``WebFetch`` in an
isolated subagent) and registers a real ``ResearchProvider``; this baseline
ships the seam so the fast-follow has somewhere to land with no retrofit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class RoleResearchResult:
    """A deep-role-research synthesis on the three named axes (AC.ONDEEP.2).

    The baseline stub fills these with a featherlight placeholder; the
    fast-follow slice fills them with a real web-research synthesis.
    """

    role: str
    effectiveness: str
    promotion_criteria: str
    existing_ai_tools: str
    is_stub: bool = False

    def as_leverage_ideas(self) -> list[str]:
        """Fold the synthesis back into surfaced leverage ideas the intake can
        present at its demonstrate-leverage close (AC.ONINTAKE.6)."""
        return [
            f"For your role ({self.role}): {self.existing_ai_tools}",
            f"A path to greater effectiveness: {self.effectiveness}",
        ]


class ResearchProvider(Protocol):
    """The clean interface the baseline intake composes on (AC.ONDEEP.2).

    Input: a user's stated role. Output: the three-axis synthesis. The
    fast-follow slice registers a real provider (web-research subagent); the
    baseline ships ``StubResearchProvider`` so it degrades gracefully when the
    real pass is absent.
    """

    def research_role(self, role: str) -> RoleResearchResult:  # pragma: no cover
        ...


class StubResearchProvider:
    """The featherlight baseline provider — a graceful-degradation placeholder.

    It returns a clearly-marked stub synthesis (``is_stub=True``) naming the
    three axes so the baseline intake can offer the deepening + degrade cleanly
    when the real fast-follow pass is not installed. It does NO web research —
    the baseline first-touch stays featherlight (AC.ONDEEP.1)."""

    def research_role(self, role: str) -> RoleResearchResult:
        return RoleResearchResult(
            role=role,
            effectiveness=(
                f"the habits + skills that make a {role} effective "
                "(full research lands in the deep-role-research fast-follow slice)"
            ),
            promotion_criteria=(
                f"what gets a {role} promoted to the next level "
                "(full research lands in the fast-follow slice)"
            ),
            existing_ai_tools=(
                f"AI tools loam could wrap or rebuild for a {role} "
                "(full research lands in the fast-follow slice)"
            ),
            is_stub=True,
        )


# The default provider the baseline intake uses when no real research provider
# is registered. The fast-follow slice swaps this for a web-research provider.
_DEFAULT_PROVIDER: ResearchProvider = StubResearchProvider()


def default_research_provider() -> ResearchProvider:
    """The provider the baseline intake composes on. Resolved at call time so
    the fast-follow slice can register a real provider without the baseline
    importing it (graceful degradation — the seam is present, the pass is not).
    """
    return _DEFAULT_PROVIDER


def register_research_provider(provider: ResearchProvider) -> None:
    """Swap the default provider the baseline intake resolves at call time.

    The registration seam the fast-follow slice fills (AC.DRRSEAM.*): it swaps
    the featherlight ``StubResearchProvider`` for a real web-research provider
    WITHOUT the baseline importing it and WITHOUT touching the intake's gating
    logic. The featherlight invariant (AC.ONDEEP.1) is unaffected — only the
    idea-vacuum + role + opt-in path ever reaches the provider at all, regardless
    of which provider is registered here.
    """
    global _DEFAULT_PROVIDER
    _DEFAULT_PROVIDER = provider


def reset_research_provider() -> None:
    """Restore the baseline featherlight stub provider (test-hygiene seam so a
    test that registers a real provider can undo it without leaking module
    state across the suite)."""
    global _DEFAULT_PROVIDER
    _DEFAULT_PROVIDER = StubResearchProvider()
