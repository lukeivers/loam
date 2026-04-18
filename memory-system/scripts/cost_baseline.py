"""D4 — extraction cost baseline.

Acceptance per the brief:
- A representative sample of synthetic episodes (drawn from D2 scenarios)
  is ingested through Graphiti.
- Per-episode token usage is measured and broken down by prompt type
  (using TokenUsageTracker).
- A baseline figure and variance estimate are reported.
- A projection to anticipated pOS usage volume is provided with
  assumptions stated.

Method:
1. Build a fresh Graphiti instance (clean Kuzu DB).
2. Ingest episodes one at a time. Snapshot the per-prompt token
   counters before and after each ingest; the delta is that episode's
   cost breakdown.
3. Aggregate: mean, median, stdev, min, max input/output tokens per
   episode, by prompt type.
4. Convert to USD using the configured Anthropic price for
   ANTHROPIC_MODEL (current Haiku 4.5 pricing as of 2026-04-17).
5. Project to anticipated pOS volume — assumption stated.

Output: data/runs/cost_baseline_{ts}.json + summary on stdout.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.factory import load_env, make_graphiti  # noqa: E402

from graphiti_core.nodes import EpisodeType  # noqa: E402


REPO = Path(__file__).resolve().parent.parent
EPISODES_FILE = REPO / "data" / "episodes.json"
RUNS_DIR = REPO / "data" / "runs"


# Anthropic pricing — keep this list small and current. As of 2026-04-17:
# - claude-haiku-4-5: $1.00 / MTok input, $5.00 / MTok output
# - claude-sonnet-4-5: $3.00 / MTok input, $15.00 / MTok output
# - claude-opus-4-5: $15.00 / MTok input, $75.00 / MTok output
# These are the *API* prices, NOT Max-subscription prices. Max bundles
# fixed-rate usage; the cost projection here translates to an equivalent
# API spend so Luke can frame the Max budget conversation.
PRICING_USD_PER_MTOK = {
    "claude-haiku-4-5": (1.00, 5.00),
    "claude-sonnet-4-5": (3.00, 15.00),
    "claude-opus-4-5": (15.00, 75.00),
}


def _wipe_db(db_path: Path) -> None:
    for sibling in db_path.parent.glob(db_path.name + "*"):
        try:
            if sibling.is_file():
                sibling.unlink()
            elif sibling.is_dir():
                shutil.rmtree(sibling, ignore_errors=True)
        except OSError:
            pass


def snapshot(tracker) -> dict[str, dict[str, int]]:
    """Snapshot per-prompt counters as a plain dict."""
    return {
        name: {
            "input": u.total_input_tokens,
            "output": u.total_output_tokens,
            "calls": u.call_count,
        }
        for name, u in tracker.get_usage().items()
    }


def diff(before: dict, after: dict) -> dict[str, dict[str, int]]:
    """Per-prompt delta between two snapshots."""
    keys = set(before) | set(after)
    out: dict[str, dict[str, int]] = {}
    for k in keys:
        b = before.get(k, {"input": 0, "output": 0, "calls": 0})
        a = after.get(k, {"input": 0, "output": 0, "calls": 0})
        out[k] = {
            "input": a["input"] - b["input"],
            "output": a["output"] - b["output"],
            "calls": a["calls"] - b["calls"],
        }
    return {k: v for k, v in out.items() if v["calls"] > 0}


async def main() -> int:
    load_env()
    episodes = json.loads(EPISODES_FILE.read_text())

    db_path = REPO / "data" / "kuzu_db_cost"
    _wipe_db(db_path)

    graphiti = await make_graphiti(db_path=str(db_path))
    await graphiti.build_indices_and_constraints()

    model = graphiti.llm_client.model
    print(f"=== D4 — extraction cost baseline ({model}) ===")
    print(f"Episodes: {len(episodes)} (synthetic, from data/episodes.json)\n")

    per_episode_breakdowns: list[dict[str, Any]] = []
    cumulative_before: dict[str, dict[str, int]] = {}
    for ep in episodes:
        ref_time = datetime.fromisoformat(ep["reference_time"])
        before = snapshot(graphiti.llm_client.token_tracker)
        t0 = time.perf_counter()
        result = await graphiti.add_episode(
            name=ep["name"],
            episode_body=ep["body"],
            source_description=f"D4 baseline — synthetic episode {ep['id']}",
            reference_time=ref_time,
            source=EpisodeType.text,
            group_id=f"d4-cost-{ep['engagement']}",
        )
        wall_seconds = time.perf_counter() - t0
        after = snapshot(graphiti.llm_client.token_tracker)
        d = diff(before, after)
        ep_in = sum(v["input"] for v in d.values())
        ep_out = sum(v["output"] for v in d.values())
        ep_calls = sum(v["calls"] for v in d.values())
        per_episode_breakdowns.append({
            "id": ep["id"],
            "name": ep["name"],
            "body_len_chars": len(ep["body"]),
            "wall_seconds": round(wall_seconds, 2),
            "nodes_extracted": len(result.nodes),
            "edges_extracted": len(result.edges),
            "total_input_tokens": ep_in,
            "total_output_tokens": ep_out,
            "total_calls": ep_calls,
            "by_prompt": d,
        })
        print(
            f"  {ep['id']}  in={ep_in:>5}  out={ep_out:>4}  "
            f"calls={ep_calls:>2}  wall={wall_seconds:>5.1f}s  "
            f"({len(result.nodes)}n {len(result.edges)}e)  {ep['name'][:30]}"
        )

    # Aggregate per prompt across all episodes.
    by_prompt_all: dict[str, dict[str, list[int]]] = {}
    for ep in per_episode_breakdowns:
        for prompt_name, vals in ep["by_prompt"].items():
            slot = by_prompt_all.setdefault(
                prompt_name,
                {"per_ep_input": [], "per_ep_output": [], "per_ep_calls": []},
            )
            slot["per_ep_input"].append(vals["input"])
            slot["per_ep_output"].append(vals["output"])
            slot["per_ep_calls"].append(vals["calls"])

    # Stats helpers.
    def stats(xs: list[int]) -> dict[str, float]:
        if not xs:
            return {}
        return {
            "n": len(xs),
            "mean": round(statistics.mean(xs), 1),
            "median": round(statistics.median(xs), 1),
            "stdev": round(statistics.stdev(xs), 1) if len(xs) >= 2 else 0.0,
            "min": min(xs),
            "max": max(xs),
            "sum": sum(xs),
        }

    by_prompt_stats: dict[str, dict[str, Any]] = {}
    for prompt_name, slot in by_prompt_all.items():
        by_prompt_stats[prompt_name] = {
            "input_tokens": stats(slot["per_ep_input"]),
            "output_tokens": stats(slot["per_ep_output"]),
            "calls": stats(slot["per_ep_calls"]),
        }

    # Per-episode totals.
    ep_totals_in = [e["total_input_tokens"] for e in per_episode_breakdowns]
    ep_totals_out = [e["total_output_tokens"] for e in per_episode_breakdowns]
    ep_totals_calls = [e["total_calls"] for e in per_episode_breakdowns]

    # Cost.
    price_in, price_out = PRICING_USD_PER_MTOK.get(model, (None, None))
    if price_in is None:
        print(f"\n!! no pricing data for model {model}; cost summary skipped")
        cost_per_ep_mean_usd = None
    else:
        mean_in = statistics.mean(ep_totals_in)
        mean_out = statistics.mean(ep_totals_out)
        cost_per_ep_mean_usd = round(
            (mean_in / 1_000_000) * price_in + (mean_out / 1_000_000) * price_out, 6
        )

    summary = {
        "model": model,
        "episodes_total": len(episodes),
        "per_episode": per_episode_breakdowns,
        "by_prompt_stats": by_prompt_stats,
        "totals": {
            "input_tokens_sum": sum(ep_totals_in),
            "output_tokens_sum": sum(ep_totals_out),
            "calls_sum": sum(ep_totals_calls),
            "input_tokens_per_episode": stats(ep_totals_in),
            "output_tokens_per_episode": stats(ep_totals_out),
            "calls_per_episode": stats(ep_totals_calls),
        },
        "pricing": {
            "model": model,
            "input_usd_per_mtok": price_in,
            "output_usd_per_mtok": price_out,
            "estimated_cost_per_episode_usd": cost_per_ep_mean_usd,
        },
    }

    # Projection — assumptions stated alongside.
    if cost_per_ep_mean_usd is not None:
        projections = projection_block(summary)
        summary["projection"] = projections

    RUNS_DIR.mkdir(exist_ok=True, parents=True)
    out_path = RUNS_DIR / f"cost_baseline_{int(time.time())}.json"
    out_path.write_text(json.dumps(summary, indent=2, default=str))
    print(f"\n-> wrote {out_path}")

    print("\n=== PER-PROMPT BREAKDOWN (mean across episodes) ===")
    print(
        f"{'prompt name':<55}  {'in mean':>8}  {'in stdev':>9}  {'out mean':>9}  {'calls/ep':>9}"
    )
    print("-" * 100)
    for name, s in sorted(
        by_prompt_stats.items(),
        key=lambda kv: kv[1]["input_tokens"]["sum"],
        reverse=True,
    ):
        print(
            f"{name:<55}  "
            f"{s['input_tokens']['mean']:>8.0f}  {s['input_tokens']['stdev']:>9.0f}  "
            f"{s['output_tokens']['mean']:>9.0f}  {s['calls']['mean']:>9.2f}"
        )

    print("\n=== PER-EPISODE TOTALS (across all episodes) ===")
    in_stats = summary["totals"]["input_tokens_per_episode"]
    out_stats = summary["totals"]["output_tokens_per_episode"]
    calls_stats = summary["totals"]["calls_per_episode"]
    print(
        f"  input  : mean={in_stats['mean']:.0f}  median={in_stats['median']:.0f}  "
        f"stdev={in_stats['stdev']:.0f}  min={in_stats['min']}  max={in_stats['max']}"
    )
    print(
        f"  output : mean={out_stats['mean']:.0f}  median={out_stats['median']:.0f}  "
        f"stdev={out_stats['stdev']:.0f}  min={out_stats['min']}  max={out_stats['max']}"
    )
    print(
        f"  calls  : mean={calls_stats['mean']:.1f}  median={calls_stats['median']:.0f}  "
        f"min={calls_stats['min']}  max={calls_stats['max']}"
    )
    if cost_per_ep_mean_usd is not None:
        print(
            f"\n  COST   : ${cost_per_ep_mean_usd:.6f} / episode "
            f"(at {model} list pricing)"
        )

    if "projection" in summary:
        print("\n=== PROJECTIONS (with assumptions) ===")
        for label, p in summary["projection"].items():
            print(
                f"  {label:<35} : {p['episodes_per_period']:>6} eps -> "
                f"${p['estimated_usd']:>8.2f}/{p['period']} "
                f"({p['input_tokens']:>10,} in + {p['output_tokens']:>9,} out)"
            )

    await graphiti.close()
    return 0


def projection_block(summary: dict) -> dict[str, dict[str, Any]]:
    """Project the baseline to anticipated pOS volume.

    Assumption (stated explicitly): ~3,000 meaningful events/year per
    research v1 §2.2. The synthetic episodes here are roughly the size
    of "decision events" in pOS (~500-1000 chars). Real pOS will mix
    short telemetry-class messages (filtered out by the ephemerality
    rubric, NOT this brief's scope) and longer summary-class events
    (process-of-arrival captures, ~2000-5000 chars). The projection is
    bracketed accordingly.
    """
    in_mean = summary["totals"]["input_tokens_per_episode"]["mean"]
    out_mean = summary["totals"]["output_tokens_per_episode"]["mean"]
    price_in = summary["pricing"]["input_usd_per_mtok"]
    price_out = summary["pricing"]["output_usd_per_mtok"]
    cost_per_ep = summary["pricing"]["estimated_cost_per_episode_usd"]

    out: dict[str, dict[str, Any]] = {}
    for label, eps_per_period, period in [
        ("daily   (10 events/day)", 10, "day"),
        ("weekly  (60 events/week)", 60, "week"),
        ("monthly (250 ev/month)", 250, "month"),
        ("yearly  (3000 ev/year)", 3000, "year"),
        ("5-year  (15000 ev)", 15_000, "5y"),
    ]:
        in_tok = int(in_mean * eps_per_period)
        out_tok = int(out_mean * eps_per_period)
        usd = round((in_tok / 1_000_000) * price_in + (out_tok / 1_000_000) * price_out, 2)
        out[label] = {
            "episodes_per_period": eps_per_period,
            "period": period,
            "input_tokens": in_tok,
            "output_tokens": out_tok,
            "estimated_usd": usd,
        }
    return out


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
