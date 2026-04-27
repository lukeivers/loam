"""D1 smoke test — round-trip an episode through Graphiti and retrieve it.

Acceptance criterion: a test Python call reaches Graphiti, submits an
episode, retrieves it via query — round-trip succeeds.

This script intentionally uses one fabricated episode unrelated to any
ivers-corp content (synthetic-only constraint per the brief).

Usage:
    .venv/bin/python scripts/smoke_test.py

Exit code 0 = round-trip passed; non-zero otherwise.
"""

from __future__ import annotations

import asyncio
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Ensure src/ is importable when running as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.factory import load_env, make_graphiti  # noqa: E402

from graphiti_core.nodes import EpisodeType  # noqa: E402


# Synthetic episode — invented characters in an invented company. Zero
# overlap with current ivers-corp content (Luke / Eve / Mara / etc.).
SYNTHETIC_EPISODE = """
On 2027-03-14, Mira Adelyn (CEO of Halcyon Cartography) confirmed in a
team standup that the Tideglass project had passed its second internal
review. Renji Okamoto (head of platform) noted that the storage layer
would migrate from Frostvault to a new substrate codenamed Aldermere by
end of Q2. Halcyon's board chair, Iva Petranek, approved the migration
budget of 84,000 GBP.
"""

SMOKE_DB_PATH = "./data/kuzu_db_smoke"


async def main() -> int:
    load_env()

    # Use a dedicated DB path for the smoke test so a wedged main DB
    # doesn't block this from running.
    smoke_db = Path(__file__).resolve().parent.parent / "data" / "kuzu_db_smoke"
    if smoke_db.exists():
        # Clean slate every run so the round-trip is a real round-trip,
        # not a "we already had it cached" pass. Kuzu writes a single
        # file here (newer Kuzu versions sometimes use a directory; cope
        # with either shape).
        import shutil
        if smoke_db.is_dir():
            shutil.rmtree(smoke_db, ignore_errors=True)
        else:
            smoke_db.unlink()
    # Also remove the WAL companion file if present.
    for sibling in smoke_db.parent.glob("kuzu_db_smoke*"):
        try:
            if sibling.is_file():
                sibling.unlink()
        except OSError:
            pass

    graphiti = await make_graphiti(db_path=str(smoke_db))

    print(f"[smoke] graphiti instance built ({type(graphiti).__name__})")
    print(f"[smoke] LLM model: {graphiti.llm_client.model}")
    print(f"[smoke] embedder dim: {graphiti.embedder.config.embedding_dim}")

    print("[smoke] building Kuzu indices and constraints...")
    t0 = time.perf_counter()
    await graphiti.build_indices_and_constraints()
    print(f"[smoke] indices built in {time.perf_counter() - t0:.1f}s")

    print("[smoke] ingesting one synthetic episode...")
    t0 = time.perf_counter()
    add_result = await graphiti.add_episode(
        name="smoke-tideglass-confirm",
        episode_body=SYNTHETIC_EPISODE,
        source_description="synthetic D1 round-trip probe",
        reference_time=datetime(2027, 3, 14, 9, 0, tzinfo=timezone.utc),
        source=EpisodeType.text,
        group_id="d1-smoke",
    )
    ingest_seconds = time.perf_counter() - t0
    print(
        f"[smoke] episode ingested in {ingest_seconds:.1f}s — "
        f"{len(add_result.nodes)} nodes, {len(add_result.edges)} edges"
    )

    # Probe queries — expect to find facts about the invented entities.
    queries = [
        ("Mira Adelyn", "should hit CEO entity"),
        ("Tideglass project review", "should hit project + status"),
        ("Aldermere migration budget", "should hit budget edge"),
    ]

    all_passed = True
    print("\n[smoke] running probe queries...")
    for q, why in queries:
        t0 = time.perf_counter()
        results = await graphiti.search(query=q, group_ids=["d1-smoke"], num_results=5)
        dt = time.perf_counter() - t0
        ok = len(results) > 0
        all_passed &= ok
        marker = "PASS" if ok else "FAIL"
        print(f"[smoke] {marker} q={q!r} -> {len(results)} edges in {dt*1000:.0f}ms ({why})")
        for edge in results[:3]:
            print(f"        - {edge.fact[:120]}")

    # Token-usage breakdown — same source D4 will use, exposed here as a
    # quick sanity check.
    print("\n[smoke] token usage by prompt (D4 will use the same path):")
    usage_by_prompt = graphiti.llm_client.token_tracker.get_usage()
    total = graphiti.llm_client.token_tracker.get_total_usage()
    for prompt_name, u in sorted(usage_by_prompt.items()):
        print(
            f"        {prompt_name:<60} in={u.total_input_tokens:>6}  "
            f"out={u.total_output_tokens:>5}  calls={u.call_count}"
        )
    print(
        f"        {'TOTAL':<60} in={total.input_tokens:>6}  out={total.output_tokens:>5}"
    )

    await graphiti.close()
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
