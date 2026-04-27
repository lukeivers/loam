"""Full-system evaluation using MemoryAPI (D5 + D6 + D7 + D8 + D10).

Same synthetic episodes + test set as scripts/eval_embeddings.py, but
queries go through MemoryAPI — which means:

  - D5 ephemerality filter applies at ingest (a seeded ephemeral
    episode is verified absent from storage).
  - D6 scope attribution tags every episode with its scope_id.
  - D7 observability spans capture every op; token rows get per-prompt
    cost attribution.
  - D8 temporal wrapper applies to all `temporal` questions; temporal
    pass rate should now be non-zero.
  - D10 retention class defaults to `normal`; derived-only episodes
    get their content scrubbed after extraction.

Acceptance check: temporal pass rate > 0, other modes at least match
the prototyping-phase baseline.
"""

from __future__ import annotations

import asyncio
import json
import shutil
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.factory import load_env, make_graphiti, prepare_graphiti  # noqa: E402
from src.memory import MemoryAPI  # noqa: E402
from src.upgrade import run_probe_set, load_probe_set, score_one_probe  # noqa: E402
from src.observability import Emitter, reset_default_emitter  # noqa: E402
from src.scope import MockScopeSource  # noqa: E402


REPO = Path(__file__).resolve().parent.parent
EPISODES_FILE = REPO / "data" / "episodes.json"
TEST_SET_FILE = REPO / "data" / "test_set.json"
RUNS_DIR = REPO / "data" / "runs"


def _wipe_db(db_path: Path) -> None:
    for sibling in db_path.parent.glob(db_path.name + "*"):
        try:
            if sibling.is_file():
                sibling.unlink()
            elif sibling.is_dir():
                shutil.rmtree(sibling, ignore_errors=True)
        except OSError:
            pass


async def main() -> int:
    load_env()

    # Dedicated observability sink for this run.
    obs_dir = REPO / "data" / "observability_fullsystem"
    obs_dir.mkdir(parents=True, exist_ok=True)
    # Clear any prior run's files so per-prompt attribution is clean.
    for f in obs_dir.glob("*.jsonl"):
        f.unlink()
    emitter = Emitter(sink_dir=obs_dir)
    reset_default_emitter(emitter)

    # Fresh DB.
    db_path = REPO / "data" / "kuzu_db_fullsystem"
    _wipe_db(db_path)

    # Dedicated scope registry.
    registry_path = REPO / "data" / "scope_registry_fullsystem.json"
    if registry_path.exists():
        registry_path.unlink()
    scope_source = MockScopeSource(registry_path=registry_path)

    g = await make_graphiti(db_path=str(db_path))
    await prepare_graphiti(g)
    memory = MemoryAPI(g, scope_source=scope_source, emitter=emitter)

    # Register one scope for every distinct engagement + "chaos" catchall.
    episodes = json.loads(EPISODES_FILE.read_text())
    test_set = json.loads(TEST_SET_FILE.read_text())
    questions = test_set["questions"]

    # --- ephemerality smoke: ingest a CPU reading; verify it's discarded ---
    eph_result = await memory.ingest(
        body="cpu usage: 74.2",
        name="telemetry:cpu-reading",
        source="cpu.usage",
        source_description="host telemetry",
        reference_time=datetime(2027, 3, 14, tzinfo=timezone.utc),
        scope_id="telemetry",
    )
    print(f"[D5] ephemeral cpu reading -> {eph_result}")
    assert eph_result.ephemeral is True
    assert eph_result.episode_uuid is None

    # --- ingest the 34 synthetic episodes via MemoryAPI ---
    t0 = time.perf_counter()
    per_ep_secs: list[float] = []
    for ep in episodes:
        # Graphiti group_id restricted to alphanumeric/-/_; use `_` separator.
        scope_id = f"aldermere_{ep['engagement']}"
        ref = datetime.fromisoformat(ep["reference_time"])
        t_start = time.perf_counter()
        res = await memory.ingest(
            body=ep["body"],
            name=ep["name"],
            source_description=f"synthetic episode {ep['id']}",
            reference_time=ref,
            scope_id=scope_id,
            retention_class="normal",
        )
        per_ep_secs.append(time.perf_counter() - t_start)
        print(
            f"  ingested {ep['id']:5} scope={scope_id:24} "
            f"{per_ep_secs[-1]:5.1f}s +{res.nodes_created}n +{res.edges_created}e"
        )

    ingest_elapsed = time.perf_counter() - t0
    print(f"\ningest total: {ingest_elapsed:.1f}s ({len(episodes)} episodes)")

    # --- retention class mix: ingest one derived-only episode ---
    derived_res = await memory.ingest(
        body=(
            "Aldermere's Q1 2029 revenue target is $4.2M; staff costs "
            "remain the largest variable."
        ),
        name="aldermere:q1-2029-target",
        source_description="internal finance note (derived-only retention)",
        reference_time=datetime(2029, 1, 2, tzinfo=timezone.utc),
        scope_id="aldermere_firm-overview",
        retention_class="derived-only",
    )
    print(f"[D10] derived-only ingest -> {derived_res}")

    # Verify the content was scrubbed on the Episodic node.
    rows, _, _ = await g.driver.execute_query(
        "MATCH (ep:Episodic {uuid: $uuid}) RETURN ep.content AS content, ep.retention_class AS cls",
        uuid=derived_res.episode_uuid,
    )
    print(f"    stored content after scrub: {rows[0]['content']!r} cls={rows[0]['cls']!r}")
    assert rows[0]["content"] == ""
    assert rows[0]["cls"] == "derived-only"

    # --- run the probe set ---
    # Use MemoryAPI.search (which hits the D8 temporal wrapper for
    # temporal questions). Do NOT scope-filter the probe queries —
    # the test set is cross-scope; anchor behaviour would otherwise
    # fail.
    print("\n-- running probe set --")
    results = await run_probe_set(memory, probe_set=test_set)

    # Aggregate per mode.
    modes = sorted({q["mode"] for q in questions})
    by_mode: dict[str, dict] = {}
    for mode in modes:
        rows_m = [r for r in results if r.mode == mode]
        if not rows_m:
            continue
        by_mode[mode] = {
            "n": len(rows_m),
            "pass_rate": sum(1 for r in rows_m if r.passed) / len(rows_m),
            "mean_recall": statistics.mean(r.recall for r in rows_m),
            "mean_precision_at_5": statistics.mean(r.precision_at_5 for r in rows_m),
        }

    overall = {
        "n": len(results),
        "pass_rate": sum(1 for r in results if r.passed) / len(results),
        "mean_recall": statistics.mean(r.recall for r in results),
        "mean_precision_at_5": statistics.mean(r.precision_at_5 for r in results),
    }

    # Token usage attribution from the observability sink.
    per_prompt_cost = emitter.per_prompt_cost(
        input_usd_per_mtok=1.0, output_usd_per_mtok=5.0
    )
    total_cost = sum(p["estimated_usd"] for p in per_prompt_cost.values())

    print("\n-- results --")
    print(
        f"overall pass={overall['pass_rate']*100:5.1f}%  "
        f"recall={overall['mean_recall']*100:5.1f}%  "
        f"p@5={overall['mean_precision_at_5']*100:5.1f}%"
    )
    for mode, m in by_mode.items():
        print(
            f"  {mode:13} (n={m['n']:2})  pass={m['pass_rate']*100:5.1f}%  "
            f"recall={m['mean_recall']*100:5.1f}%  p@5={m['mean_precision_at_5']*100:5.1f}%"
        )

    print(f"\ntotal estimated cost (haiku 4.5 pricing): ${total_cost:.4f}")
    for name, pbucket in per_prompt_cost.items():
        print(
            f"  {name:40} calls={pbucket['call_count']:4} "
            f"in={pbucket['input_tokens']:7} out={pbucket['output_tokens']:5} "
            f"${pbucket['estimated_usd']:.4f}"
        )

    # Persist run summary.
    RUNS_DIR.mkdir(exist_ok=True, parents=True)
    out = {
        "at": datetime.now(timezone.utc).isoformat(),
        "wrapper": "D8-temporal-enabled",
        "episodes_ingested": len(episodes),
        "ingest_seconds_total": ingest_elapsed,
        "ingest_seconds_per_episode_mean": statistics.mean(per_ep_secs),
        "overall": overall,
        "by_mode": by_mode,
        "per_prompt_cost": per_prompt_cost,
        "total_cost_estimated_usd": round(total_cost, 6),
        "per_question": [
            {
                "id": r.query_id,
                "mode": r.mode,
                "passed": r.passed,
                "recall": r.recall,
                "precision_at_5": r.precision_at_5,
                "result_count": r.result_count,
                "matched_expected": r.matched_expected,
                "missed_expected": r.missed_expected,
                "negative_hits": r.negative_hits,
                "top_facts_preview": [t[:80] for t in r.top_facts[:3]],
            }
            for r in results
        ],
    }
    out_path = RUNS_DIR / f"full_system_{int(time.time())}.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\n-> wrote {out_path}")

    await g.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
