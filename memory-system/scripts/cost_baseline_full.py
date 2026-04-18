"""Refreshed cost baseline from full-system usage.

Reads the most recent full_system_*.json run (produced by
scripts/eval_full_system.py) and the most recent poa_demo_*.json plus
the observability token sink to produce a realistic projection of
cost at various user workloads.

Unlike D4's prototyping cost baseline (synthetic ingest only), this
baseline reflects the entire memory-system pipeline:

  - 34 synthetic episodes ingested through MemoryAPI
  - 1 derived-only retention episode
  - 1 ephemeral (rejected) ingest — no cost
  - Probe set (44 questions) run — embedding cost on Ollama (local,
    zero marginal dollars)
  - Process-of-arrival: 2 additional episodes (outcome + summary)

Writes: data/runs/cost_baseline_full_<ts>.json and prints a table.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


REPO = Path(__file__).resolve().parent.parent
RUNS_DIR = REPO / "data" / "runs"


# Anthropic Haiku 4.5 public pricing (same as D4).
INPUT_USD_PER_MTOK = 1.00
OUTPUT_USD_PER_MTOK = 5.00


def latest(glob: str) -> Path | None:
    candidates = sorted(RUNS_DIR.glob(glob), key=lambda p: p.stat().st_mtime)
    return candidates[-1] if candidates else None


def main() -> int:
    full_run_path = latest("full_system_*.json")
    if full_run_path is None:
        print("no full_system_*.json run found; run scripts/eval_full_system.py first")
        return 1
    run = json.loads(full_run_path.read_text())

    by_prompt = run["per_prompt_cost"]
    episodes_ingested = run["episodes_ingested"]
    ingest_total_s = run["ingest_seconds_total"]

    # Per-episode means. Note: the probe set's embedding cost is
    # zero-dollar (local Ollama) so it's not in the by_prompt totals.
    per_episode_input = sum(p["input_tokens"] for p in by_prompt.values()) / episodes_ingested
    per_episode_output = sum(p["output_tokens"] for p in by_prompt.values()) / episodes_ingested
    per_episode_calls = sum(p["call_count"] for p in by_prompt.values()) / episodes_ingested
    per_episode_usd = (
        (per_episode_input / 1_000_000) * INPUT_USD_PER_MTOK
        + (per_episode_output / 1_000_000) * OUTPUT_USD_PER_MTOK
    )

    projections = {}
    for label, n_per_period, period in [
        ("daily (10 events/day)", 10, "day"),
        ("weekly (60 events/week)", 60, "week"),
        ("monthly (250 events/month)", 250, "month"),
        ("yearly (3000 events/year)", 3000, "year"),
        ("5-year (15000 events)", 15000, "5y"),
    ]:
        projections[label] = {
            "events": n_per_period,
            "period": period,
            "input_tokens": round(per_episode_input * n_per_period),
            "output_tokens": round(per_episode_output * n_per_period),
            "llm_calls": round(per_episode_calls * n_per_period),
            "estimated_usd": round(per_episode_usd * n_per_period, 2),
        }

    # Post-hoc check: include the D11 process-of-arrival overhead.
    # Each dispatch produces ONE additional summary episode plus one
    # Claude summarisation call (~500 tokens out on 4-8k in). The
    # summary episode itself is ingested — another ~7 LLM calls and
    # ~12k input / 1.3k output tokens. Add this as a separate line.
    poa_per_dispatch = {
        "summarise_input": 1500,      # stream excerpt + prompt
        "summarise_output": 400,
        "summary_ingest_input": per_episode_input,
        "summary_ingest_output": per_episode_output,
    }
    poa_usd_per_dispatch = (
        (poa_per_dispatch["summarise_input"] + poa_per_dispatch["summary_ingest_input"]) / 1_000_000 * INPUT_USD_PER_MTOK
        + (poa_per_dispatch["summarise_output"] + poa_per_dispatch["summary_ingest_output"]) / 1_000_000 * OUTPUT_USD_PER_MTOK
    )

    out = {
        "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_run": str(full_run_path.name),
        "model": "claude-haiku-4-5",
        "pricing": {
            "input_usd_per_mtok": INPUT_USD_PER_MTOK,
            "output_usd_per_mtok": OUTPUT_USD_PER_MTOK,
        },
        "per_episode": {
            "input_tokens_mean": round(per_episode_input, 1),
            "output_tokens_mean": round(per_episode_output, 1),
            "llm_calls_mean": round(per_episode_calls, 2),
            "estimated_usd": round(per_episode_usd, 5),
            "ingest_seconds_mean": round(ingest_total_s / episodes_ingested, 2),
        },
        "per_prompt": by_prompt,
        "projections": projections,
        "process_of_arrival_overhead_per_dispatch": {
            **poa_per_dispatch,
            "estimated_usd": round(poa_usd_per_dispatch, 5),
        },
        "notes": [
            "Ollama embedding cost is zero-dollar (local inference).",
            "Token counts reflect the MemoryAPI pipeline: ephemerality "
            "filter rejections cost nothing, derived-only retention "
            "costs the same as normal (extraction still runs).",
            "Process-of-arrival adds roughly one extra episode's cost "
            "plus a ~1500+400 summarisation call per dispatch.",
        ],
    }

    out_path = RUNS_DIR / f"cost_baseline_full_{int(time.time())}.json"
    out_path.write_text(json.dumps(out, indent=2))

    # Print readable table.
    print("=== refreshed cost baseline (full-system) ===\n")
    print(f"source run: {full_run_path.name}")
    print(f"model: claude-haiku-4-5")
    print()
    print("per-episode means:")
    print(f"  input tokens:  {out['per_episode']['input_tokens_mean']:9.1f}")
    print(f"  output tokens: {out['per_episode']['output_tokens_mean']:9.1f}")
    print(f"  llm calls:     {out['per_episode']['llm_calls_mean']:9.2f}")
    print(f"  est. cost:    ${out['per_episode']['estimated_usd']:9.5f}")
    print(f"  ingest wall:   {out['per_episode']['ingest_seconds_mean']:9.2f} s")
    print()
    print("per-prompt breakdown:")
    for name, b in by_prompt.items():
        print(
            f"  {name:42} calls={b['call_count']:4} "
            f"in={b['input_tokens']:>7} out={b['output_tokens']:>6} "
            f"${b['estimated_usd']:.4f}"
        )
    print()
    print("projections:")
    for label, p in projections.items():
        print(
            f"  {label:30}  {p['input_tokens']:>10} in  "
            f"{p['output_tokens']:>9} out  {p['llm_calls']:>6} calls  "
            f"${p['estimated_usd']:.2f}"
        )
    print()
    print("process-of-arrival overhead (per dispatch):")
    poa = out["process_of_arrival_overhead_per_dispatch"]
    print(
        f"  summary: in={poa['summarise_input']} out={poa['summarise_output']}  "
        f"summary-ingest: in={poa['summary_ingest_input']} out={poa['summary_ingest_output']}  "
        f"~${poa['estimated_usd']:.5f}/dispatch"
    )
    print(f"\n-> wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
