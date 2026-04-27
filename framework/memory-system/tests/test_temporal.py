"""D8 — temporal filter wrapper tests.

Covers:
- Wrapper produces a Kuzu-compatible filter shape (OR across
  outer-list elements for invalid_at).
- A regression test pins the upstream-bug shape so if upstream
  fixes the compound-inner-list case, the wrapper can be retired.
- `known_at_system_time` matches the OTel-audit use case.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from graphiti_core.driver.driver import GraphProvider
from graphiti_core.search.search_filters import (
    ComparisonOperator,
    edge_search_filter_query_constructor,
)

from src import temporal


def test_active_at_generates_OR_for_invalid_at() -> None:
    t = datetime(2027, 5, 1, tzinfo=timezone.utc)
    sf = temporal.active_at(t)

    # The invalid_at shape must be TWO outer elements (OR), not one
    # element with two DateFilters (AND).
    assert len(sf.invalid_at) == 2
    assert all(len(inner) == 1 for inner in sf.invalid_at)

    ops = [inner[0].comparison_operator for inner in sf.invalid_at]
    assert ComparisonOperator.greater_than in ops
    assert ComparisonOperator.is_null in ops


def test_active_at_cypher_disjunction_is_OR() -> None:
    t = datetime(2027, 5, 1, tzinfo=timezone.utc)
    sf = temporal.active_at(t)
    queries, params = edge_search_filter_query_constructor(sf, GraphProvider.KUZU)
    # The invalid_at clause must contain " OR " (disjunction), not
    # just " AND ".
    invalid_clause = [q for q in queries if "invalid_at" in q]
    assert invalid_clause
    assert " OR " in invalid_clause[0]


def test_known_at_system_time_uses_created_expired_not_valid_invalid() -> None:
    t = datetime(2028, 1, 1, tzinfo=timezone.utc)
    sf = temporal.known_at_system_time(t)
    # Should reference created_at / expired_at and leave valid_at /
    # invalid_at alone.
    assert sf.created_at is not None
    assert sf.expired_at is not None
    assert sf.valid_at is None
    assert sf.invalid_at is None


def test_regression_compound_inner_list_bug_still_exists_upstream() -> None:
    """Pin the upstream-bug shape so we can detect if upstream fixes
    it. If this test fails, D8's wrapper can be retired.
    """
    from graphiti_core.search.search_filters import (
        DateFilter,
        SearchFilters,
    )

    t = datetime(2027, 5, 1, tzinfo=timezone.utc)
    buggy = SearchFilters(
        valid_at=[[DateFilter(date=t, comparison_operator=ComparisonOperator.less_than_equal)]],
        invalid_at=[[
            DateFilter(date=t, comparison_operator=ComparisonOperator.greater_than),
            DateFilter(date=None, comparison_operator=ComparisonOperator.is_null),
        ]],
    )
    queries, _ = edge_search_filter_query_constructor(buggy, GraphProvider.KUZU)
    invalid_clause = [q for q in queries if "invalid_at" in q]
    # Bug: the two inner DateFilters are AND-joined inside one clause.
    # This clause can never be true because `invalid_at > T AND invalid_at IS NULL`.
    assert " AND " in invalid_clause[0]
    # Explicit sanity: the bug shape contains BOTH the > comparison
    # and IS NULL inside ONE outer paren group.
    assert ">" in invalid_clause[0] and "IS NULL" in invalid_clause[0]
