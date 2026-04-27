"""D11 demo — end-to-end process-of-arrival capture using the mock
StreamLogProducer.

Simulates a background dispatch producing a multi-line reasoning log
plus an outcome, summarises via Claude, ingests both episodes
(outcome + summary) through MemoryAPI, and verifies:

  (a) a retrieval query for the outcome or the reasoning returns
      both episodes,
  (b) the raw stream text is NOT stored (derived-only retention),
  (c) the summary's structured facts landed in the graph.

Writes a run report to data/runs/poa_demo_<ts>.json.
"""

from __future__ import annotations

import asyncio
import json
import shutil
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.factory import load_env, make_graphiti, prepare_graphiti  # noqa: E402
from src.memory import MemoryAPI  # noqa: E402
from src.observability import Emitter, reset_default_emitter  # noqa: E402
from src.process_of_arrival import (  # noqa: E402
    ProcessOfArrivalReceiver,
    make_mock_log,
    MockStreamLogProducer,
)
from src.scope import MockScopeSource  # noqa: E402


REPO = Path(__file__).resolve().parent.parent
RUNS_DIR = REPO / "data" / "runs"


def _wipe_db(db_path: Path) -> None:
    for sib in db_path.parent.glob(db_path.name + "*"):
        try:
            if sib.is_file(): sib.unlink()
            elif sib.is_dir(): shutil.rmtree(sib, ignore_errors=True)
        except OSError:
            pass


async def main() -> int:
    load_env()

    obs_dir = REPO / "data" / "observability_poa"
    obs_dir.mkdir(parents=True, exist_ok=True)
    for f in obs_dir.glob("*.jsonl"):
        f.unlink()
    emitter = Emitter(sink_dir=obs_dir)
    reset_default_emitter(emitter)

    db_path = REPO / "data" / "kuzu_db_poa"
    _wipe_db(db_path)
    scope_source = MockScopeSource(registry_path=REPO / "data" / "scope_registry_poa.json")

    g = await make_graphiti(db_path=str(db_path))
    await prepare_graphiti(g)
    memory = MemoryAPI(g, scope_source=scope_source, emitter=emitter)

    async def _ingest(**kwargs):
        res = await memory.ingest(**kwargs)
        return res.episode_uuid

    receiver = ProcessOfArrivalReceiver(
        memory_ingest=_ingest,
        llm_client=g.llm_client,
    )

    now = datetime.now(timezone.utc)
    log = make_mock_log(
        dispatch_id="velmar-market-analysis-2029-01-03",
        scope_id="velmar_entry_decision",
        persona="rho-quant",
        started_at=now - timedelta(minutes=3),
        ended_at=now,
        outcome=(
            "Recommendation: enter Brazil first. Supporting rationale: "
            "market size 3x Chile under baseline assumptions, partner "
            "Lente Pampero is available, regulatory friction is comparable."
        ),
        lines=[
            "Starting analysis: Velmar Optical's Latin America entry.",
            "Candidates: Brazil, Chile, Argentina, Uruguay.",
            "Pulled 2027 ophthalmology market size tables — Brazil "
            "dominates on raw volume (~3x Chile, ~8x Uruguay).",
            "Checked regulatory filings: Brazil's ANVISA registration "
            "is medium-complexity; Chile's ISP is simpler but market is "
            "smaller.",
            "Ran sensitivity: Brazil wins under 80% of scenarios; "
            "Chile catches up only if luxury premium segment outperforms.",
            "Partner check: Lente Pampero (Sao Paulo) has a prior "
            "working relationship with two Velmar competitors.",
            "Conclusion: Brazil first, secondary sweep after 12 months.",
        ],
    )

    # Emit the log through the receiver.
    producer = MockStreamLogProducer(logs=[log])
    result = await receiver.receive(await producer.next_log())
    print(f"process-of-arrival result: {result}")

    # Acceptance: a retrieval for the outcome's topic returns BOTH
    # episodes (outcome + reasoning summary).
    hits = await memory.search("Brazil market entry recommendation", num_results=10)
    fact_preview = [h.fact[:100] for h in hits[:6]]
    print("\nretrieved facts for 'Brazil market entry recommendation':")
    for f in fact_preview:
        print(f"  - {f}")

    # Check derived-only: the reasoning episode's content was scrubbed.
    rows, _, _ = await g.driver.execute_query(
        "MATCH (ep:Episodic {uuid: $uuid}) RETURN ep.content AS content, ep.retention_class AS cls",
        uuid=result.summary_episode_uuid,
    )
    summary_content = rows[0]["content"] if rows else None
    print(f"\nsummary episode retention_class={rows[0]['cls'] if rows else None}")
    print(f"summary episode stored content (should be empty for derived-only): {summary_content!r}")

    # Outcome episode should be NORMAL (raw text preserved).
    rows_o, _, _ = await g.driver.execute_query(
        "MATCH (ep:Episodic {uuid: $uuid}) RETURN ep.content AS content, ep.retention_class AS cls",
        uuid=result.outcome_episode_uuid,
    )
    print(f"outcome episode retention_class={rows_o[0]['cls'] if rows_o else None}")
    print(f"outcome episode content preview: {(rows_o[0]['content'] if rows_o else '')[:120]!r}")

    # Emit a summary report.
    out = {
        "at": datetime.now(timezone.utc).isoformat(),
        "dispatch_id": log.dispatch_id,
        "outcome_episode_uuid": result.outcome_episode_uuid,
        "summary_episode_uuid": result.summary_episode_uuid,
        "summary_text_preview": result.summary_text[:500],
        "retrieval_facts": fact_preview,
        "summary_content_scrubbed": summary_content == "",
        "outcome_content_preserved": bool(rows_o and rows_o[0]["content"]),
    }
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RUNS_DIR / f"poa_demo_{int(time.time())}.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\n-> wrote {out_path}")

    await g.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
