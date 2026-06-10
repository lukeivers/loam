"""AC.DGR.OA (outcome-altitude: true) — live grounding → traceable gate.

On a fresh workspace with NO pre-arranged state, a real archetype ask
produces a grounding record whose citations resolved live in-run, and
the frozen gate text contains >=1 criterion traceable to that record
— or, when live research genuinely failed that run, the build is
explicitly flagged ungrounded (never silent fake grounding; the
honest degrade is asserted, not excused).

Shares the single session live run (conftest.live_bfi_run; env-gated
BFI_REAL_CLAUDE=1).

Per docs/plans/general-build-from-intent.md §6.
"""

from __future__ import annotations

import re
import sys
import urllib.request
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def test_live_citations_and_frozen_gate_traceability(live_bfi_run):
    result = live_bfi_run["result"]
    grounding = result.grounding
    run_dir = Path(result.run_dir)

    if not grounding.grounded:
        # AC.DGR.3's honest degrade: the user was TOLD, in the
        # narration, in plain language — and nothing faked grounding.
        assert grounding.ungrounded_reason
        assert any(grounding.ungrounded_reason in line
                   for line in result.narration)
        return

    # The record exists at the predictable workspace path with
    # in-run-resolved citations.
    record = Path(grounding.record_path)
    assert record.exists()
    assert record.parent == live_bfi_run["workspace"] / "grounding"
    body = record.read_text(encoding="utf-8")
    assert "resolved in-run, HTTP" in body
    assert len(grounding.norms) >= 1

    # Spot-re-resolve one cited URL now (independent of the run's own
    # probe): the citation is a real, live source.
    url = grounding.norms[0].source_url
    req = urllib.request.Request(
        url, method="HEAD", headers={"User-Agent": "bfi-oa-recheck/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            assert resp.status < 500
    except urllib.error.HTTPError as exc:
        assert exc.code < 500  # live host; bot-blocked is still real

    # The FROZEN gate text (the artifact the build was judged by, not
    # a report about it) carries >=1 criterion traceable to the
    # record's norm ids.
    frozen_text = (run_dir / "_frozen" / "bfi-gate.frozen").read_text(
        encoding="utf-8")
    cited = re.findall(r"\[per practitioner norm (N\d+)\]", frozen_text)
    assert cited, "no gate criterion traceable to the grounding record"
    known = {n.norm_id for n in grounding.norms}
    assert set(cited) <= known, (
        f"gate cites norms {set(cited) - known} not in the record")
