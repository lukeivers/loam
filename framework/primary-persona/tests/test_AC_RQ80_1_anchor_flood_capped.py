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

"""AC.RQ80.1 (#80 anchor-flood de-flood) — ``WorkAnchor.query_tokens()`` caps the
ANCHOR (objective + subgoal) contribution prompt-relative: ALL prompt tokens are
present, and the anchor adds at most ``max(MIN_ANCHOR_FLOOR, MAX_QUERY_TOKENS -
prompt_token_count)`` tokens, so a short topical prompt no longer becomes an
80-token objective-flooded query.

Plan: docs/plans/fbm-retrieval-quality-anchor-cap-omnibus-norm.md §Lever 1.
"""

from __future__ import annotations

from loam.primary_persona.keep_pace.work_anchor import (
    MAX_QUERY_TOKENS,
    MIN_ANCHOR_FLOOR,
    WorkAnchor,
    tokenize,
)


# A long objective text whose token count (well over the cap) is what used to
# flood the query — the same shape as the live financial/litrpg objectives.
_LONG_OBJECTIVE = (
    "Build durable robust financial independence weighted toward passive income "
    "target 250k per year active consulting bootstrap engine convert into assets "
    "investing real estate ip catalog ai operated bought businesses until work "
    "optional"
)
_SECOND_OBJECTIVE = (
    "Produce the LitRPG series Patch Notes for Reality seven books via the "
    "autonomous Layer 4 production pipeline quality bar canon consistency"
)


def test_AC_RQ80_1_rich_prompt_caps_anchor_flood() -> None:
    """A rich topical prompt + long objectives: every prompt token is present,
    and the anchor adds only the prompt-relative cap (NOT the full flood)."""
    prompt = "can we use the Anthropic API key for an LLM call"
    anchor = WorkAnchor(
        prompt=prompt,
        objective_texts=[_LONG_OBJECTIVE, _SECOND_OBJECTIVE],
    )
    tokens = anchor.query_tokens()

    prompt_tokens = tokenize(prompt)
    # Every prompt token is present in full (the topical signal is never capped).
    for pt in prompt_tokens:
        assert pt in tokens, f"prompt token {pt!r} must be in the query"

    # The anchor contributed only the prompt-relative cap, not the full flood.
    expected_anchor_cap = max(
        MIN_ANCHOR_FLOOR, MAX_QUERY_TOKENS - len(prompt_tokens)
    )
    anchor_token_count = len(tokens) - len(prompt_tokens)
    assert anchor_token_count <= expected_anchor_cap, (
        f"anchor flood not capped: {anchor_token_count} anchor tokens added, "
        f"cap is {expected_anchor_cap}; full query={tokens!r}"
    )

    # Concretely: the pre-fix flood was ~72 anchor tokens (80-token query); the
    # capped query is dramatically smaller.
    total_anchor_available = len(
        set(tokenize(_LONG_OBJECTIVE)) | set(tokenize(_SECOND_OBJECTIVE))
    )
    assert anchor_token_count < total_anchor_available, (
        "the cap must admit strictly fewer anchor tokens than the full "
        "objective text would (the flood is bounded)"
    )


def test_AC_RQ80_1_vague_prompt_gets_larger_anchor_budget() -> None:
    """A VAGUE prompt leaves a LARGER anchor budget (the anchor is the only
    retrieval signal) — the prompt-relative cap, not a fixed small cap."""
    vague = WorkAnchor(
        prompt="continue",  # 1 content token
        objective_texts=[_LONG_OBJECTIVE, _SECOND_OBJECTIVE],
    )
    rich = WorkAnchor(
        prompt="can we use the Anthropic API key for an LLM call",
        objective_texts=[_LONG_OBJECTIVE, _SECOND_OBJECTIVE],
    )
    vague_anchor = len(vague.query_tokens()) - len(tokenize("continue"))
    rich_anchor = len(rich.query_tokens()) - len(
        tokenize("can we use the Anthropic API key for an LLM call")
    )
    # The vague prompt's anchor budget is strictly larger than the rich
    # prompt's — the cap tracks prompt strength (the AC.KP1.6 rescue needs it).
    assert vague_anchor > rich_anchor, (
        f"vague-prompt anchor budget ({vague_anchor}) must exceed rich-prompt "
        f"anchor budget ({rich_anchor})"
    )
