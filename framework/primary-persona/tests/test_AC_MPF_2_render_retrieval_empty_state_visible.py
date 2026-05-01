"""AC.MPF.2 — retrieval empty-state path is visible.

Outcome (per locked plan §4 AC.MPF.2): ``_render_retrieval`` returns a
structured diagnostic string when ``result["results"]`` is empty,
instead of the pre-amendment-#95 ``""`` (which the composer rendered
as a whitespace-only ``[memory-retrieval]`` block).

Pre-amendment-#95 the empty-state path returned ``""``; the composer's
``_serialise_turn`` rendered ``[memory-retrieval]\\n    \\n`` —
indistinguishable from "search exception" or "group_id mismatch"
without log inspection.

Post-amendment-#95 the empty-state path returns
``"[memory-retrieval]\\n  (no results for this query)"`` so the
absence is observable in UPS hook stdout per M6c graceful-fallthrough-
with-detection CDC.
"""

from __future__ import annotations

from loam.primary_persona.memory_consumer import _render_retrieval


def test_AC_MPF_2_empty_results_yields_visible_diagnostic_string() -> None:
    """Outcome: empty results render as the visible "(no results...)"
    diagnostic, not as an empty string.
    """
    out = _render_retrieval({"query": "anything", "results": []}, cap=1600)
    assert out == "[memory-retrieval]\n  (no results for this query)"


def test_AC_MPF_2_missing_results_key_yields_visible_diagnostic_string() -> None:
    """Defensive: a malformed search response (missing ``results`` key
    entirely, or carrying ``None``) also renders the empty-state
    diagnostic — same fallthrough surface.
    """
    out_missing = _render_retrieval({"query": "x"}, cap=1600)
    out_none = _render_retrieval({"results": None}, cap=1600)
    assert out_missing == "[memory-retrieval]\n  (no results for this query)"
    assert out_none == "[memory-retrieval]\n  (no results for this query)"


def test_AC_MPF_2_non_list_results_yields_visible_diagnostic_string() -> None:
    """Defensive: ``results`` of an unexpected non-list shape (dict,
    string, int) routes through the same fallthrough."""
    for bogus in ({"k": "v"}, "garbage", 42):
        out = _render_retrieval({"results": bogus}, cap=1600)
        assert out == "[memory-retrieval]\n  (no results for this query)"


def test_AC_MPF_2_non_empty_results_unchanged() -> None:
    """Backwards-compat: when results are present, rendering still
    produces the dashed-list shape from amendment #33's surface.
    """
    out = _render_retrieval(
        {
            "query": "t",
            "results": [
                {"fact": "alpha relates to beta"},
                {"fact": "gamma relates to delta"},
            ],
        },
        cap=1600,
    )
    assert "[memory-retrieval]" in out
    assert "- alpha relates to beta" in out
    assert "- gamma relates to delta" in out
    # Header + 2 facts — no diagnostic string.
    assert "(no results for this query)" not in out
