"""D8 — Temporal-filter wrapper.

Graphiti's compound `valid_at + invalid_at` SearchFilter shape does
not translate correctly to Kuzu Cypher: when the user asks "is this
edge active at T?" — semantically

    valid_at <= T AND (invalid_at > T OR invalid_at IS NULL)

— and builds the filter as

    SearchFilters(
        valid_at=[[DateFilter(<=, T)]],
        invalid_at=[[
            DateFilter(>, T),
            DateFilter(IS NULL, None),
        ]],
    )

…the constructor in `graphiti_core.search.search_filters` concatenates
the two DateFilters inside one inner list using `AND`, producing

    (e.invalid_at > T) AND (e.invalid_at IS NULL)

— which is always false. The correct inner shape is an OR across the
two conditions, achieved by putting each in its own inner list:

    invalid_at=[[DateFilter(>, T)], [DateFilter(IS NULL, None)]]

This wrapper produces the CORRECT shape, so callers can express the
intent declaratively (`active_at(T)`) without having to remember the
per-list semantics of the underlying Pydantic model.

Diagnosed in `scripts/diag_temporal2.py`. A regression test
(`tests/test_temporal.py`) pins the bug shape so the wrapper stays
correct if the upstream constructor ever changes.

Wrapper interface is transparent to callers: they still get a
`SearchFilters` back and pass it to `graphiti.search()` exactly as
before. The wrapper just knows how to construct the filter correctly.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from graphiti_core.search.search_filters import (
    ComparisonOperator,
    DateFilter,
    SearchFilters,
)

from .config import section


def active_at(reference_time: datetime) -> SearchFilters:
    """Build a SearchFilters that matches edges active at `reference_time`.

    The semantic contract: an edge is active at T iff its valid interval
    contains T, i.e.

        valid_at <= T AND (invalid_at > T OR invalid_at IS NULL)

    Returns a SearchFilters shaped correctly for Kuzu Cypher
    (distinct outer-list elements for the OR disjunction on invalid_at).
    """
    if not section("temporal").get("enabled", True):
        # Safety valve: if a workspace disables the wrapper (because
        # upstream fixed it), fall through to the naive compound shape
        # so behaviour degrades back to the upstream state.
        return _naive_compound(reference_time)

    return SearchFilters(
        valid_at=[
            [DateFilter(
                date=reference_time,
                comparison_operator=ComparisonOperator.less_than_equal,
            )]
        ],
        invalid_at=[
            [DateFilter(
                date=reference_time,
                comparison_operator=ComparisonOperator.greater_than,
            )],
            [DateFilter(
                date=None,
                comparison_operator=ComparisonOperator.is_null,
            )],
        ],
    )


def valid_at_or_before(reference_time: datetime) -> SearchFilters:
    """Match edges whose `valid_at <= reference_time`.

    Useful for "what did we know up to T," independent of invalidation.
    This is the simple-filter case the upstream already handles; kept
    here so the temporal API lives in one place.
    """
    return SearchFilters(
        valid_at=[
            [DateFilter(
                date=reference_time,
                comparison_operator=ComparisonOperator.less_than_equal,
            )]
        ],
    )


def known_at_system_time(system_time: datetime) -> SearchFilters:
    """Match edges as the system knew them at `system_time`.

    Spec v1.1 R5: audit queries operate on system-time (created_at),
    distinct from valid-time (valid_at). The system knew edge E at T
    iff E.created_at <= T AND (E.expired_at > T OR E.expired_at IS NULL).
    """
    return SearchFilters(
        created_at=[
            [DateFilter(
                date=system_time,
                comparison_operator=ComparisonOperator.less_than_equal,
            )]
        ],
        expired_at=[
            [DateFilter(
                date=system_time,
                comparison_operator=ComparisonOperator.greater_than,
            )],
            [DateFilter(
                date=None,
                comparison_operator=ComparisonOperator.is_null,
            )],
        ],
    )


def _naive_compound(reference_time: datetime) -> SearchFilters:
    """The upstream-bug shape, produced only when the wrapper is disabled.

    Present so a regression test (`tests/test_temporal.py`) can verify
    the bug still exists upstream — if this shape ever starts returning
    the correct results, we can drop the wrapper.
    """
    return SearchFilters(
        valid_at=[
            [DateFilter(
                date=reference_time,
                comparison_operator=ComparisonOperator.less_than_equal,
            )]
        ],
        invalid_at=[[
            DateFilter(
                date=reference_time,
                comparison_operator=ComparisonOperator.greater_than,
            ),
            DateFilter(
                date=None,
                comparison_operator=ComparisonOperator.is_null,
            ),
        ]],
    )


def describe_wrapper() -> dict[str, Any]:
    """Self-describe for /health and docs."""
    return {
        "enabled": section("temporal").get("enabled", True),
        "purpose": "Kuzu-compatible temporal SearchFilter for active-at/known-at queries",
        "diagnosed_bug": (
            "graphiti-core 0.28.2 compound DateFilter in one inner list "
            "ANDs conditions; correct shape is OR across outer lists."
        ),
    }
