"""AC.DGR.1 — the in-pipeline domain-grounding record (S2).

Between intent confirmation and gate-freeze, the pipeline produces a
domain-grounding record — practitioner norms with citations — written
as a durable record at a predictable workspace path, with every
citation carrying IN-RUN resolution evidence (the live-fetch half is
the env-gated S2 probe + AC.DGR.OA; here the structural contract is
pinned deterministically through the injectable seams).

Per docs/plans/general-build-from-intent.md §6.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from handsoff_loop.grounding import research_domain  # noqa: E402


def _researching_llm(prompt, *, model="sonnet", timeout=0):
    # The objective reaches the research dispatch verbatim (the
    # research is about THIS run's objective, not a template).
    assert "match the day's payments" in prompt
    return {"result": json.dumps({
        "summary": "Practitioners reconcile in a standard way.",
        "norms": [
            {"norm": "Every unmatched item is listed, never dropped.",
             "source_url": "https://example.org/recon-guide",
             "source_title": "Reconciliation Guide"},
            {"norm": "Matched pairs reference both source rows.",
             "source_url": "https://example.org/matching",
             "source_title": "Matching Practices"},
            {"norm": "Totals are shown for both sides.",
             "source_url": "https://example.org/totals",
             "source_title": "Totals Standard"},
        ],
        "expert_gate_flags": [],
    })}


def test_grounded_record_written_at_predictable_path(tmp_path):
    outcome = research_domain(
        "match the day's payments against open invoices",
        workspace_dir=tmp_path,
        llm_json_fn=_researching_llm,
        url_probe_fn=lambda url: 200,
    )
    assert outcome.grounded is True
    assert len(outcome.norms) == 3
    # Predictable workspace path: <workspace>/grounding/*-grounding.md
    rec = Path(outcome.record_path)
    assert rec.parent == tmp_path / "grounding"
    assert rec.name.endswith("-grounding.md")
    body = rec.read_text(encoding="utf-8")
    # Durable, indexable: YAML frontmatter names the record kind.
    assert body.startswith("---\n")
    assert "kind: domain-grounding-record" in body
    # Every citation carries its in-run resolution evidence.
    assert body.count("resolved in-run, HTTP 200") == 3
    # Norm ids are the gate-traceability keys (consumed by S3).
    assert "**N1**" in body and "**N3**" in body


def test_norm_ids_are_stable_traceability_keys(tmp_path):
    outcome = research_domain(
        "match the day's payments against open invoices",
        workspace_dir=tmp_path,
        llm_json_fn=_researching_llm,
        url_probe_fn=lambda url: 200,
    )
    assert [n.norm_id for n in outcome.norms] == ["N1", "N2", "N3"]
    assert all(n.http_status == 200 for n in outcome.norms)
