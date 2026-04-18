"""D3 — embedding model quality evaluation against the synthetic test set.

For each candidate Ollama embedding model:

1. Spin up a fresh Kuzu DB (separate file per model — embedding dimensions
   differ across models, so they cannot share a graph).
2. Ingest all 34 synthetic episodes from data/episodes.json.
3. Run all 44 questions from data/test_set.json.
4. Score each result against the question's expected_facts /
   expected_episodes / negative_facts.
5. Report per-mode precision/recall/latency and aggregate metrics.

Acceptance per the brief:
- At least two candidate embedding models run (Qwen3 / bge-large per
  the proposal; we substitute nomic-embed-text + bge-large here, with
  Qwen3-embedding pending model availability — see findings.md).
- Precision/recall and latency reported per model.
- Recommendation made with rationale.

The proposal does not name specific precision/recall thresholds; the
research v2 §6.4 sets target precision@5 ≥ 0.8 for recall-style and
≥ 0.9 for entity-lookup. We compute metrics relative to those.

Usage:
    .venv/bin/python scripts/eval_embeddings.py            # both models
    .venv/bin/python scripts/eval_embeddings.py nomic      # one
    .venv/bin/python scripts/eval_embeddings.py bge-large

Writes results to data/runs/eval_{model}_{timestamp}.json plus a
per-model summary printed to stdout.
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
from typing import Any

# Ensure src/ is importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.factory import load_env, make_graphiti  # noqa: E402

from graphiti_core.nodes import EpisodeType  # noqa: E402
from graphiti_core.search.search_filters import (  # noqa: E402
    ComparisonOperator,
    DateFilter,
    SearchFilters,
)


REPO = Path(__file__).resolve().parent.parent
EPISODES_FILE = REPO / "data" / "episodes.json"
TEST_SET_FILE = REPO / "data" / "test_set.json"
RUNS_DIR = REPO / "data" / "runs"

# Models in order of evaluation. Add Qwen3-embedding here once pulled.
DEFAULT_MODELS = ["nomic-embed-text", "bge-large"]


def _wipe_db(db_path: Path) -> None:
    """Remove all Kuzu artifacts at db_path so each run starts clean."""
    for sibling in db_path.parent.glob(db_path.name + "*"):
        try:
            if sibling.is_file():
                sibling.unlink()
            elif sibling.is_dir():
                shutil.rmtree(sibling, ignore_errors=True)
        except OSError:
            pass


async def ingest_all(graphiti, episodes: list[dict]) -> dict[str, Any]:
    """Ingest every synthetic episode; return timing stats."""
    per_episode_seconds: list[float] = []
    nodes_total = 0
    edges_total = 0
    for ep in episodes:
        ref_time = datetime.fromisoformat(ep["reference_time"])
        t0 = time.perf_counter()
        result = await graphiti.add_episode(
            name=ep["name"],
            episode_body=ep["body"],
            source_description=f"synthetic episode {ep['id']}",
            reference_time=ref_time,
            source=EpisodeType.text,
            group_id=f"d3-eval-{ep['engagement']}",
        )
        per_episode_seconds.append(time.perf_counter() - t0)
        nodes_total += len(result.nodes)
        edges_total += len(result.edges)
        print(
            f"    ingested {ep['id']:5} ({ep['name'][:30]:30}) "
            f"{per_episode_seconds[-1]:5.1f}s  +{len(result.nodes)}n +{len(result.edges)}e"
        )
    return {
        "episodes": len(episodes),
        "nodes_total": nodes_total,
        "edges_total": edges_total,
        "ingest_seconds_total": sum(per_episode_seconds),
        "ingest_seconds_per_episode_mean": statistics.mean(per_episode_seconds),
        "ingest_seconds_per_episode_p95": (
            sorted(per_episode_seconds)[int(0.95 * len(per_episode_seconds))]
            if len(per_episode_seconds) >= 5
            else max(per_episode_seconds)
        ),
    }


def score_one(question: dict, edges: list, lookup_engagement_for_edge=None) -> dict[str, Any]:
    """Score a single retrieval result against the question's labels.

    Returns a dict of per-question metrics. Scoring rules:

    - `expected_facts` (list[str]): all substrings must appear across the
      returned edge facts (case-insensitive). Coverage = matched / total.
    - `expected_facts_any` (list[str]): at least one substring must appear
      in some edge fact. Coverage = 1.0 if any matched, else 0.0.
    - `expected_facts_all` (list[str]): synonym for `expected_facts`.
    - `negative_facts` (list[str]): NONE of these substrings should
      appear in the top-5 edges.
    - `expected_episodes` (list[str]): the episode IDs whose body should
      have generated the matched edges. Edges carry a list of source
      episode UUIDs; we map back via the episode's `name` (we registered
      one ingest per episode, so the episode UUID set is known by name).

    For now we only score on facts (the hard signal); episode-level
    scoring requires a UUID map we don't yet keep. Returns precision and
    recall fields normalised to [0, 1].
    """
    # Normalise the fact texts.
    facts_text = " ".join((edge.fact or "").lower() for edge in edges)
    top5_text = " ".join((edge.fact or "").lower() for edge in edges[:5])

    expected_all = (
        question.get("expected_facts")
        or question.get("expected_facts_all")
        or []
    )
    expected_any = question.get("expected_facts_any") or []
    negative = question.get("negative_facts") or []

    matched_all = [e for e in expected_all if e.lower() in facts_text]
    matched_any = [e for e in expected_any if e.lower() in facts_text]
    matched_negatives = [n for n in negative if n.lower() in top5_text]

    # Recall = how many expected facts surfaced.
    if expected_all:
        recall_all = len(matched_all) / len(expected_all)
    elif expected_any:
        recall_all = 1.0 if matched_any else 0.0
    else:
        recall_all = 1.0  # No required facts; trivially satisfied.

    # Precision proxy = top-5 has at least one expected fact AND no
    # negative_facts. This is a coarse signal but matches the spec's
    # "right thing at the right time" framing.
    top5_has_expected = any(
        e.lower() in top5_text for e in (expected_all + expected_any)
    )
    precision_at_5 = (
        1.0
        if top5_has_expected and not matched_negatives
        else (0.5 if top5_has_expected else 0.0)
    )

    # A question PASSES if recall_all >= 1.0 OR (mode == 'context_aware'
    # and precision_at_5 == 1.0). The pass/fail is the headline metric;
    # the recall/precision floats are the diagnostic.
    is_pass = (recall_all >= 1.0) and not matched_negatives
    return {
        "id": question["id"],
        "mode": question["mode"],
        "results_count": len(edges),
        "recall_at_all": recall_all,
        "precision_at_5": precision_at_5,
        "matched_expected": matched_all + matched_any,
        "missed_expected": [
            e for e in expected_all if e.lower() not in facts_text
        ],
        "matched_negatives": matched_negatives,
        "pass": bool(is_pass),
        "top1_fact": edges[0].fact if edges else None,
    }


async def evaluate_model(model: str, episodes: list[dict], questions: list[dict]) -> dict[str, Any]:
    """Run the full ingest + query loop for one embedding model."""
    print(f"\n=== EVAL: {model} ===")
    db_path = REPO / "data" / f"kuzu_db_eval_{model.replace(':', '_').replace('/', '_')}"
    _wipe_db(db_path)

    graphiti = await make_graphiti(embedder_model=model, db_path=str(db_path))
    await graphiti.build_indices_and_constraints()

    print("  -- ingesting --")
    ingest_stats = await ingest_all(graphiti, episodes)
    print(
        f"  ingest done: {ingest_stats['episodes']} episodes, "
        f"{ingest_stats['nodes_total']} nodes, "
        f"{ingest_stats['edges_total']} edges, "
        f"total {ingest_stats['ingest_seconds_total']:.0f}s"
    )

    print("  -- querying --")
    query_results: list[dict] = []
    query_seconds: list[float] = []
    for q in questions:
        anchor_uuid = None
        # Anchor lookup is its own retrieval — find one node UUID matching
        # the anchor entity's name. We do this with a quick semantic
        # search keyed on the anchor name; if it returns no hits, we
        # fall through to anchor-less retrieval.
        if q["mode"] == "context_aware" and q.get("anchor_entity"):
            anchor_results = await graphiti.search(
                query=q["anchor_entity"],
                num_results=3,
            )
            # Best-effort: take the first edge's source node UUID as the
            # anchor proxy. A fuller anchor strategy is full-build work.
            if anchor_results:
                anchor_uuid = anchor_results[0].source_node_uuid

        # Temporal mode: pass a SearchFilters with valid_at <= reference_time
        # AND (invalid_at IS NULL OR invalid_at > reference_time). This is
        # the bitemporal "what was true at T" query — see proposal §5/R5.
        search_filter: SearchFilters | None = None
        if q["mode"] == "temporal" and q.get("reference_time"):
            ref_t = datetime.fromisoformat(q["reference_time"])
            search_filter = SearchFilters(
                valid_at=[
                    [DateFilter(date=ref_t, comparison_operator=ComparisonOperator.less_than_equal)]
                ],
                invalid_at=[
                    [
                        DateFilter(date=ref_t, comparison_operator=ComparisonOperator.greater_than),
                        DateFilter(date=None, comparison_operator=ComparisonOperator.is_null),
                    ]
                ],
            )

        t0 = time.perf_counter()
        edges = await graphiti.search(
            query=q["question"],
            center_node_uuid=anchor_uuid,
            num_results=10,
            search_filter=search_filter,
        )
        dt = time.perf_counter() - t0
        query_seconds.append(dt)
        scored = score_one(q, edges)
        scored["latency_ms"] = round(dt * 1000, 1)
        scored["anchor_used"] = anchor_uuid is not None if q["mode"] == "context_aware" else None
        query_results.append(scored)

        marker = "PASS" if scored["pass"] else "FAIL"
        print(
            f"    {marker} {q['id']:5} ({q['mode']:13}) "
            f"r={scored['recall_at_all']:.2f} p@5={scored['precision_at_5']:.2f} "
            f"{dt*1000:5.0f}ms  top1={(scored['top1_fact'] or '<none>')[:60]}"
        )

    # Aggregate per mode.
    modes = sorted({q["mode"] for q in questions})
    by_mode: dict[str, dict[str, float]] = {}
    for mode in modes:
        rows = [r for r in query_results if r["mode"] == mode]
        if not rows:
            continue
        by_mode[mode] = {
            "n": len(rows),
            "pass_rate": sum(1 for r in rows if r["pass"]) / len(rows),
            "mean_recall": statistics.mean(r["recall_at_all"] for r in rows),
            "mean_precision_at_5": statistics.mean(r["precision_at_5"] for r in rows),
            "mean_latency_ms": statistics.mean(r["latency_ms"] for r in rows),
            "p95_latency_ms": (
                sorted(r["latency_ms"] for r in rows)[int(0.95 * len(rows))]
                if len(rows) >= 5
                else max(r["latency_ms"] for r in rows)
            ),
        }

    overall = {
        "n": len(query_results),
        "pass_rate": sum(1 for r in query_results if r["pass"]) / len(query_results),
        "mean_recall": statistics.mean(r["recall_at_all"] for r in query_results),
        "mean_precision_at_5": statistics.mean(r["precision_at_5"] for r in query_results),
        "mean_latency_ms": statistics.mean(r["latency_ms"] for r in query_results),
        "p95_latency_ms": sorted(r["latency_ms"] for r in query_results)[
            int(0.95 * len(query_results))
        ],
    }

    # Token usage incurred during this eval.
    token_usage = graphiti.llm_client.token_tracker.get_usage()
    total = graphiti.llm_client.token_tracker.get_total_usage()
    token_summary = {
        "by_prompt": {
            name: {
                "input_tokens": u.total_input_tokens,
                "output_tokens": u.total_output_tokens,
                "call_count": u.call_count,
            }
            for name, u in token_usage.items()
        },
        "total_input_tokens": total.input_tokens,
        "total_output_tokens": total.output_tokens,
    }

    await graphiti.close()

    summary = {
        "model": model,
        "ingest": ingest_stats,
        "questions_total": len(questions),
        "by_mode": by_mode,
        "overall": overall,
        "token_usage": token_summary,
        "per_question": query_results,
    }

    RUNS_DIR.mkdir(exist_ok=True, parents=True)
    out_path = RUNS_DIR / f"eval_{model.replace(':', '_').replace('/', '_')}_{int(time.time())}.json"
    out_path.write_text(json.dumps(summary, indent=2, default=str))
    print(f"  -> wrote {out_path}")

    print(f"\n  SUMMARY ({model}):")
    print(
        f"  overall pass={overall['pass_rate']*100:5.1f}%  "
        f"recall={overall['mean_recall']*100:5.1f}%  "
        f"p@5={overall['mean_precision_at_5']*100:5.1f}%  "
        f"mean_latency={overall['mean_latency_ms']:5.0f}ms  "
        f"p95_latency={overall['p95_latency_ms']:5.0f}ms"
    )
    for mode, m in by_mode.items():
        print(
            f"    {mode:13} (n={m['n']:2})  pass={m['pass_rate']*100:5.1f}%  "
            f"recall={m['mean_recall']*100:5.1f}%  p@5={m['mean_precision_at_5']*100:5.1f}%  "
            f"latency={m['mean_latency_ms']:5.0f}ms"
        )
    return summary


async def main(models: list[str]) -> int:
    load_env()
    episodes = json.loads(EPISODES_FILE.read_text())
    test_set = json.loads(TEST_SET_FILE.read_text())
    questions = test_set["questions"]

    summaries: list[dict] = []
    for model in models:
        s = await evaluate_model(model, episodes, questions)
        summaries.append(s)

    if len(summaries) < 2:
        print("\n(only one model evaluated; comparison skipped)")
        return 0

    # Cross-model comparison.
    print("\n=== CROSS-MODEL COMPARISON ===")
    print(f"{'metric':<28} | " + " | ".join(f"{s['model']:<20}" for s in summaries))
    print("-" * (28 + len(summaries) * 23))
    rows = [
        ("overall pass rate %", lambda s: s["overall"]["pass_rate"] * 100),
        ("overall mean recall %", lambda s: s["overall"]["mean_recall"] * 100),
        ("overall p@5 %", lambda s: s["overall"]["mean_precision_at_5"] * 100),
        ("overall mean latency ms", lambda s: s["overall"]["mean_latency_ms"]),
        ("overall p95 latency ms", lambda s: s["overall"]["p95_latency_ms"]),
        ("ingest seconds total", lambda s: s["ingest"]["ingest_seconds_total"]),
    ]
    for label, getter in rows:
        vals = [f"{getter(s):<20.2f}" for s in summaries]
        print(f"{label:<28} | " + " | ".join(vals))

    return 0


if __name__ == "__main__":
    arg_models = sys.argv[1:] or DEFAULT_MODELS
    sys.exit(asyncio.run(main(arg_models)))
