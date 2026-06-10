"""AC.DGR.3 — bounded research, honest under failure (S2).

  * the research budget is NAMED and bounded (one dispatch under a
    named ceiling — the constants exist and the stage performs at most
    one dispatch on every path, success or failure);
  * research unavailability yields an EXPLICITLY-FLAGGED ungrounded
    build the user is told about in plain language — never silent
    fake grounding;
  * invented/unresolvable citations never enter the record: every
    citation failing the in-run probe is DROPPED and LOGGED; zero
    surviving citations degrades to the flagged ungrounded outcome.

Per docs/plans/general-build-from-intent.md §6.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from handsoff_loop import grounding  # noqa: E402
from handsoff_loop.grounding import (  # noqa: E402
    GROUNDING_MAX_DISPATCHES,
    GROUNDING_TIMEOUT_S,
    research_domain,
)


def _norms_payload(urls):
    return {"result": json.dumps({
        "summary": "Some practice summary.",
        "norms": [{"norm": f"norm via {u}", "source_url": u,
                   "source_title": u} for u in urls],
        "expert_gate_flags": [],
    })}


def test_budget_is_named_and_single_dispatch():
    assert GROUNDING_MAX_DISPATCHES == 1
    assert GROUNDING_TIMEOUT_S > 0
    calls = []

    def _counting_llm(prompt, *, model="sonnet", timeout=0):
        calls.append(1)
        raise OSError("network down")

    out = research_domain("do the thing", workspace_dir=Path("/tmp"),
                          llm_json_fn=_counting_llm,
                          url_probe_fn=lambda u: -1)
    # Exactly one dispatch even on failure — no retry path exists.
    assert len(calls) == GROUNDING_MAX_DISPATCHES
    assert out.grounded is False


def test_research_failure_is_flagged_in_plain_language(tmp_path):
    def _failing_llm(prompt, *, model="sonnet", timeout=0):
        raise TimeoutError("research timed out")

    out = research_domain("do the thing", workspace_dir=tmp_path,
                          llm_json_fn=_failing_llm,
                          url_probe_fn=lambda u: -1)
    assert out.grounded is False
    # The user is told, in plain language — never a silent gap.
    assert "research" in out.ungrounded_reason.lower()
    assert "you should know" in out.ungrounded_reason.lower()
    # No record pretends grounding happened.
    assert out.record_path == ""
    assert not (tmp_path / "grounding").exists()


def test_model_declared_failure_degrades_honestly(tmp_path):
    def _declined_llm(prompt, *, model="sonnet", timeout=0):
        return {"result": json.dumps(
            {"research_failed": True, "reason": "no web access here"})}

    out = research_domain("do the thing", workspace_dir=tmp_path,
                          llm_json_fn=_declined_llm,
                          url_probe_fn=lambda u: 200)
    assert out.grounded is False
    assert "no web access here" in out.ungrounded_reason


def test_unresolvable_citations_dropped_and_logged(tmp_path):
    def _llm(prompt, *, model="sonnet", timeout=0):
        return _norms_payload([
            "https://real.example.org/a",
            "https://dead.example.org/b",
            "https://real.example.org/c",
        ])

    def _probe(url):
        return 200 if "real." in url else -1

    out = research_domain("do the thing", workspace_dir=tmp_path,
                          llm_json_fn=_llm, url_probe_fn=_probe)
    assert out.grounded is True
    assert [n.source_url for n in out.norms] == [
        "https://real.example.org/a", "https://real.example.org/c"]
    # The drop is logged, never papered over.
    assert len(out.dropped_citations) == 1
    assert out.dropped_citations[0]["source_url"] == \
        "https://dead.example.org/b"
    body = Path(out.record_path).read_text(encoding="utf-8")
    assert "Citations dropped" in body


def test_zero_verified_citations_is_ungrounded_not_fake(tmp_path):
    def _llm(prompt, *, model="sonnet", timeout=0):
        return _norms_payload(["https://dead.example.org/x"])

    out = research_domain("do the thing", workspace_dir=tmp_path,
                          llm_json_fn=_llm, url_probe_fn=lambda u: -1)
    assert out.grounded is False
    assert out.ungrounded_reason  # told in plain language
    assert out.dropped_citations  # and the drop is on the record
    assert not (tmp_path / "grounding").exists()


def test_expert_gate_flags_carried_in_plain_language(tmp_path):
    def _llm(prompt, *, model="sonnet", timeout=0):
        return {"result": json.dumps({
            "summary": "Practice summary.",
            "norms": [{"norm": "a norm",
                       "source_url": "https://ok.example.org/a",
                       "source_title": "A"}],
            "expert_gate_flags": [
                "Whether partial payments count as matched needs a "
                "bookkeeper's judgment — research did not settle it."],
        })}

    out = research_domain("do the thing", workspace_dir=tmp_path,
                          llm_json_fn=_llm, url_probe_fn=lambda u: 200)
    assert out.grounded is True
    assert len(out.expert_gate_flags) == 1
    body = Path(out.record_path).read_text(encoding="utf-8")
    assert "Where a human expert is needed" in body
    assert "bookkeeper's judgment" in body
