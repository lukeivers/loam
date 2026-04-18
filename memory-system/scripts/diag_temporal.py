"""Investigate why temporal SearchFilter returns zero results in eval.

Hypothesis paths:
1. Graphiti's edges have valid_at NULL for our text-source episodes
   (only message-source episodes get reference_time propagated).
2. Kuzu's filter shape doesn't match what node_search_filter_query_constructor
   produces — need to inspect the cypher.

Run after the main eval finishes; uses a fresh small DB.
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.factory import load_env, make_graphiti  # noqa: E402

from graphiti_core.nodes import EpisodeType  # noqa: E402
from graphiti_core.search.search_filters import (  # noqa: E402
    ComparisonOperator, DateFilter, SearchFilters,
)


async def main() -> int:
    load_env()
    db_path = Path(__file__).resolve().parent.parent / "data" / "kuzu_db_diag"
    # Wipe.
    for f in db_path.parent.glob(db_path.name + "*"):
        if f.is_file(): f.unlink()
    g = await make_graphiti(db_path=str(db_path))
    await g.build_indices_and_constraints()

    # Three episodes spanning dates in 2027.
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

    # Inspect edges directly via Kuzu.
    res = await g.driver.execute_query(
        "MATCH (n:RelatesToNode_) RETURN n.name AS name, n.fact AS fact, n.valid_at AS valid_at, n.invalid_at AS invalid_at LIMIT 20"
    )
    rows, _, _ = res
    print(f"\nEdges in DB (n={len(rows)}):")
    for r in rows:
        print(f"  name={r['name']!s:<30} valid_at={r['valid_at']!s:<25} invalid={r['invalid_at']!s:<25} fact={(r['fact'] or '')[:60]}")

    # Now try a search WITHOUT filter, to confirm baseline.
    print("\nSearch (no filter): 'Frostvault decision'")
    edges = await g.search(query="Frostvault decision", group_ids=["diag"], num_results=10)
    print(f"  -> {len(edges)} results; first: {(edges[0].fact if edges else None)}")

    # Search with valid_at <= 1 May 2027 — should EXCLUDE the July board decision.
    ref_t = datetime(2027, 5, 1, tzinfo=timezone.utc)
    sf_simple = SearchFilters(
        valid_at=[[DateFilter(date=ref_t, comparison_operator=ComparisonOperator.less_than_equal)]],
    )
    print(f"\nSearch (valid_at <= 2027-05-01): 'Frostvault decision'")
    edges = await g.search(query="Frostvault decision", group_ids=["diag"], num_results=10, search_filter=sf_simple)
    print(f"  -> {len(edges)} results")
    for e in edges:
        print(f"     valid_at={e.valid_at}  fact={e.fact[:80]}")

    # Search with the original eval shape (compound, list-of-list with multiple alternatives).
    sf_compound = SearchFilters(
        valid_at=[[DateFilter(date=ref_t, comparison_operator=ComparisonOperator.less_than_equal)]],
        invalid_at=[[
            DateFilter(date=ref_t, comparison_operator=ComparisonOperator.greater_than),
            DateFilter(date=None, comparison_operator=ComparisonOperator.is_null),
        ]],
    )
    print(f"\nSearch (compound valid+invalid filter): 'Frostvault decision'")
    edges = await g.search(query="Frostvault decision", group_ids=["diag"], num_results=10, search_filter=sf_compound)
    print(f"  -> {len(edges)} results")
    for e in edges:
        print(f"     valid_at={e.valid_at}  invalid_at={e.invalid_at}  fact={e.fact[:80]}")

    await g.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
