"""Trace exactly the Kuzu cypher and parameters emitted for the compound
valid_at + invalid_at SearchFilter.

This pinpoints the upstream bug so D8's wrapper can re-translate the
filter into Kuzu-compatible form.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from graphiti_core.driver.driver import GraphProvider
from graphiti_core.search.search_filters import (
    ComparisonOperator,
    DateFilter,
    SearchFilters,
    edge_search_filter_query_constructor,
)


def main() -> int:
    ref_t = datetime(2027, 5, 1, tzinfo=timezone.utc)

    print("=== simple valid_at <= T ===")
    sf = SearchFilters(
        valid_at=[[DateFilter(date=ref_t, comparison_operator=ComparisonOperator.less_than_equal)]],
    )
    queries, params = edge_search_filter_query_constructor(sf, GraphProvider.KUZU)
    print("  filter clauses:", queries)
    print("  filter params :", {k: str(v) for k, v in params.items()})

    print()
    print("=== compound valid_at + invalid_at ===")
    sf_c = SearchFilters(
        valid_at=[[DateFilter(date=ref_t, comparison_operator=ComparisonOperator.less_than_equal)]],
        invalid_at=[[
            DateFilter(date=ref_t, comparison_operator=ComparisonOperator.greater_than),
            DateFilter(date=None, comparison_operator=ComparisonOperator.is_null),
        ]],
    )
    queries, params = edge_search_filter_query_constructor(sf_c, GraphProvider.KUZU)
    print("  filter clauses:", queries)
    print("  filter params :", {k: str(v) for k, v in params.items()})

    print()
    print("=== OR of two DateFilter lists ===")
    sf_or = SearchFilters(
        invalid_at=[
            [DateFilter(date=ref_t, comparison_operator=ComparisonOperator.greater_than)],
            [DateFilter(date=None, comparison_operator=ComparisonOperator.is_null)],
        ],
    )
    queries, params = edge_search_filter_query_constructor(sf_or, GraphProvider.KUZU)
    print("  filter clauses:", queries)
    print("  filter params :", {k: str(v) for k, v in params.items()})

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
