"""Verify D8 wrapper produces correct results on the diag world.

Should return: Mira's review edge (active) and Tobi's 'decided to retain'
edge (active at 2027-05-01) — but NOT the board reversal (that happens
2027-07-02 and is after the query time).
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.factory import load_env, make_graphiti  # noqa: E402
from src import temporal  # noqa: E402

from graphiti_core.nodes import EpisodeType  # noqa: E402


async def main() -> int:
    load_env()
    db_path = Path(__file__).resolve().parent.parent / "data" / "kuzu_db_diag"
    for f in db_path.parent.glob(db_path.name + "*"):
        if f.is_file(): f.unlink()
    g = await make_graphiti(db_path=str(db_path))
    await g.build_indices_and_constraints()

    eps = [
        ("e1", "On 14 March 2027, Mira Adelyn confirmed Tideglass passed review.", datetime(2027, 3, 14, tzinfo=timezone.utc)),
        ("e2", "On 22 April 2027, Tobi Imari decided to retain Frostvault.", datetime(2027, 4, 22, tzinfo=timezone.utc)),
        ("e3", "On 2 July 2027, the board reversed the Frostvault decision.", datetime(2027, 7, 2, tzinfo=timezone.utc)),
    ]
    for name, body, ref in eps:
        await g.add_episode(
            name=name, episode_body=body,
            source_description="diagnostic",
            reference_time=ref, source=EpisodeType.text,
            group_id="diag",
        )

    ref_t = datetime(2027, 5, 1, tzinfo=timezone.utc)

    print("\n=== D8 wrapper: active_at(2027-05-01) ===")
    sf = temporal.active_at(ref_t)
    edges = await g.search(query="Frostvault decision", group_ids=["diag"], num_results=10, search_filter=sf)
    print(f"  -> {len(edges)} results")
    for e in edges:
        print(f"     valid={e.valid_at!s:<25} invalid={e.invalid_at!s:<25} fact={(e.fact or '')[:60]}")

    await g.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
