"""AC.FGF.4 — ``_render_retrieval`` prefers edges (results) over
episodes when both are present.

Outcome (per fastmcp-group-ids-filter-fix plan §4 AC.FGF.4): when the
search response carries BOTH a non-empty ``results`` (edges) list
AND a non-empty ``episodes`` list, the contributor renders the
edges only — episodes are NOT appended.

Rationale (plan §3 D2): edges are graphiti's reranked, fact-
summarised relations. They are higher signal-density than raw
episode content and match the M9 substitution-pass invariant for
the persona-facing memory shape. The episodes-fallthrough branch
only fires when no edges matched (AC.FGF.3); when both arms produce
results, the edges arm is the presentation surface.
"""

from __future__ import annotations

from loam.primary_persona.memory_consumer import _render_retrieval


def test_AC_FGF_4_edges_preferred_when_both_present() -> None:
    """Outcome: edges are rendered, episodes are NOT appended when
    both arms carry matches."""
    out = _render_retrieval(
        {
            "query": "Luke",
            "results": [
                {"fact": "Luke Ivers is the operator of pos3"},
                {"fact": "Luke Ivers uses Claude as the primary persona"},
            ],
            "nodes": [],
            "episodes": [
                {
                    "episode_uuid": "ep-A",
                    "name": "should-not-render",
                    "content": "this episode should not appear",
                    "group_id": "pos3",
                    "valid_at": None,
                },
            ],
        },
        cap=1600,
    )
    # Edges rendered.
    assert "- Luke Ivers is the operator of pos3" in out
    assert "- Luke Ivers uses Claude as the primary persona" in out
    # Episodes NOT rendered.
    assert "[episode]" not in out
    assert "should-not-render" not in out
    assert "this episode should not appear" not in out


def test_AC_FGF_4_edges_preferred_even_with_one_edge_and_many_episodes() -> None:
    """Even a single edge wins over many episodes: cardinality does
    not influence the preference."""
    out = _render_retrieval(
        {
            "query": "x",
            "results": [{"fact": "single fact"}],
            "episodes": [
                {
                    "episode_uuid": f"ep-{i}",
                    "name": f"episode-{i}",
                    "content": f"content-{i}",
                    "group_id": "g",
                    "valid_at": None,
                }
                for i in range(5)
            ],
        },
        cap=1600,
    )
    assert "- single fact" in out
    assert "[episode]" not in out
