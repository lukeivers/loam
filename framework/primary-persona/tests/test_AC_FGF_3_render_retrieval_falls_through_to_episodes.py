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

"""AC.FGF.3 — ``_render_retrieval`` falls through to ``episodes``
when ``results`` (edges) is empty.

Outcome (per fastmcp-group-ids-filter-fix plan §4 AC.FGF.3): when
the memory-system search response carries an empty ``results`` list
(i.e. graphiti returned no edges for this query under this
group_ids filter) but a non-empty ``episodes`` list (graphiti
returned matching Episodic nodes — the raw memory layer), the
contributor renders the episodes instead of the
``"(no results for this query)"`` fallthrough.

This closes the read-side observable that the predecessor diagnostic
mis-named "FastMCP group_ids filter broken": episodes whose body is
too sparse for graphiti's LLM-extractor to derive RelatesToNode_
were unreachable on edge-search even with the correct group_id.
With ``_impl_search`` now surfacing episodes (amendment #96), the
persona's contributor must consume them — this test verifies the
consumption.
"""

from __future__ import annotations

from loam.primary_persona.memory_consumer import _render_retrieval


def test_AC_FGF_3_empty_results_with_populated_episodes_renders_episodes() -> None:
    """Outcome: when ``results`` is empty but ``episodes`` carries
    matches, the contributor renders an ``[episode]`` line per
    episode, NOT the empty-state diagnostic.
    """
    out = _render_retrieval(
        {
            "query": "diagnostic",
            "results": [],
            "nodes": [],
            "episodes": [
                {
                    "episode_uuid": "ep-A",
                    "name": "diagnostic-test-2026-04-29",
                    "content": (
                        "Memory sidecar diagnostic test episode. The "
                        "graphiti service was restarted via launchctl "
                        "after lifespan-init failure."
                    ),
                    "group_id": "pos-v2_default",
                    "valid_at": None,
                },
            ],
        },
        cap=1600,
    )
    assert "[memory-retrieval]" in out
    assert "[episode] diagnostic-test-2026-04-29" in out
    assert "Memory sidecar diagnostic test episode" in out
    # The empty-state fall-through must NOT fire.
    assert "(no results for this query)" not in out


def test_AC_FGF_3_multiple_episodes_render_as_dashed_list() -> None:
    """Multiple episodes each get their own ``- [episode]`` line."""
    out = _render_retrieval(
        {
            "query": "x",
            "results": [],
            "episodes": [
                {
                    "episode_uuid": "ep-A",
                    "name": "first-episode",
                    "content": "alpha content",
                    "group_id": "g",
                    "valid_at": None,
                },
                {
                    "episode_uuid": "ep-B",
                    "name": "second-episode",
                    "content": "beta content",
                    "group_id": "g",
                    "valid_at": None,
                },
            ],
        },
        cap=1600,
    )
    assert "- [episode] first-episode: alpha content" in out
    assert "- [episode] second-episode: beta content" in out


def test_AC_FGF_3_episode_with_empty_content_renders_name_only() -> None:
    """Defensive: when an episode has empty content (rare but
    possible — Episodic.content is a STRING column, can hold ``""``),
    we render just the name line. No silent drop, no half-broken
    ``[episode] name: `` trailing-colon line."""
    out = _render_retrieval(
        {
            "query": "x",
            "results": [],
            "episodes": [
                {
                    "episode_uuid": "ep-X",
                    "name": "name-only-episode",
                    "content": "",
                    "group_id": "g",
                    "valid_at": None,
                },
            ],
        },
        cap=1600,
    )
    assert "- [episode] name-only-episode" in out
    # No trailing-colon variant.
    assert "- [episode] name-only-episode: " not in out


def test_AC_FGF_3_long_content_truncated_with_ellipsis() -> None:
    """Per-episode content preview is truncated at 200 chars with
    a trailing ellipsis to keep a single dense episode from
    exhausting the whole cap."""
    long = "x" * 500
    out = _render_retrieval(
        {
            "query": "x",
            "results": [],
            "episodes": [
                {
                    "episode_uuid": "ep-X",
                    "name": "long-content-ep",
                    "content": long,
                    "group_id": "g",
                    "valid_at": None,
                },
            ],
        },
        cap=1600,
    )
    # The ellipsis marker should be present; the rendered line should
    # carry roughly 200 chars of content (not the full 500).
    assert "…" in out
    rendered_line = next(
        ln for ln in out.splitlines() if ln.startswith("- [episode]")
    )
    # Sanity: the rendered preview is bounded — not the full 500 chars.
    assert len(rendered_line) < 250


def test_AC_FGF_3_empty_results_and_empty_episodes_keeps_mpf_fallthrough() -> None:
    """Regression: when BOTH ``results`` and ``episodes`` are empty,
    the AC.MPF.2 empty-state diagnostic is preserved verbatim.
    """
    out = _render_retrieval(
        {
            "query": "nothing-matches",
            "results": [],
            "nodes": [],
            "episodes": [],
        },
        cap=1600,
    )
    assert out == "[memory-retrieval]\n  (no results for this query)"


def test_AC_FGF_3_old_shape_response_still_renders_mpf_empty_state() -> None:
    """Backwards-compat: a memory-system response that pre-dates the
    fastmcp-group-ids-filter-fix shape (no ``episodes`` key at all)
    still falls through to the AC.MPF.2 empty-state diagnostic when
    ``results`` is empty. This shouldn't happen in production once
    amendment #96 is deployed, but the persona consumer is the
    boundary-tolerant side."""
    out = _render_retrieval({"query": "x", "results": []}, cap=1600)
    assert out == "[memory-retrieval]\n  (no results for this query)"
