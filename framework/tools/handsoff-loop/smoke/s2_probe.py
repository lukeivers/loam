#!/usr/bin/env python3.13
"""S2 measured-prediction probe (plan: general-build-from-intent §Build path).

Prediction under test: a reconciliation-archetype run yields a
grounding record with >=3 live-resolving citations (the >=1
traceable frozen-gate criterion half is exercised by the S3 probe,
which consumes a real grounding record).

Live web-capable `claude -p` research + real HTTP citation probes.
Results append to smoke/s2_probe_results.json.
Run: python3.13 framework/tools/handsoff-loop/smoke/s2_probe.py
"""

from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(_SRC))

from handsoff_loop.grounding import research_domain  # noqa: E402

OBJECTIVE = (
    "Build a command-line tool that matches a day's payment records "
    "against open invoices, pairs each payment with at most one "
    "invoice on amount and invoice number, and writes the unmatched "
    "items from each side to review files"
)


def main() -> int:
    t0 = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="bfi-s2-probe-") as ws:
        outcome = research_domain(OBJECTIVE, workspace_dir=Path(ws))
        dt = round(time.monotonic() - t0, 1)
        record_body = ""
        if outcome.record_path:
            record_body = Path(outcome.record_path).read_text(
                encoding="utf-8")
        results = {
            "probe": "S2",
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "objective": OBJECTIVE,
            "wall_s": dt,
            "grounded": outcome.grounded,
            "n_live_citations": len(outcome.norms),
            "citations": [
                {"norm_id": n.norm_id, "url": n.source_url,
                 "http_status": n.http_status, "norm": n.norm}
                for n in outcome.norms],
            "expert_gate_flags": outcome.expert_gate_flags,
            "dropped_citations": outcome.dropped_citations,
            "ungrounded_reason": outcome.ungrounded_reason,
            "record_excerpt": record_body[:600],
            "prediction_passed": outcome.grounded
            and len(outcome.norms) >= 3,
        }
    out = Path(__file__).parent / "s2_probe_results.json"
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps({"prediction_passed": results["prediction_passed"],
                      "n_live_citations": results["n_live_citations"],
                      "wall_s": dt, "written": str(out)}))
    return 0 if results["prediction_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
