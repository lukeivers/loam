"""Ordering engine — per-phase topological sort with deterministic
tie-breaking.

Contract:

  - Input: a list of `(name, after, before)` triples for contributions
    within a single phase.
  - Output: an ordered list of `name` values such that every `after`
    edge (A before B ↔ B.after includes A) is respected. Tie-breaking
    is alphabetical on `name`.
  - Cycles: raise `OrderingCycleError` listing the edge set involved.
  - Unknown references: raise `UnknownReferenceError` naming the
    offending `(contribution, referenced_name)` pair.

Algorithm: Kahn's topological sort on a DAG built from `after` +
reversed `before` edges, using a heapq ordered by name to make
dependency-free pops deterministic.
"""

from __future__ import annotations

import heapq
from collections import defaultdict
from typing import Iterable

from .errors import OrderingCycleError, UnknownReferenceError


def topological_order(
    triples: Iterable[tuple[str, tuple[str, ...], tuple[str, ...]]],
    *,
    phase_label: str,
) -> list[str]:
    """Return a deterministic topological order for the given triples.

    Parameters
    ----------
    triples: iterable of `(name, after, before)` per contribution.
        `after = (a, b, ...)` means `name` runs after `a`, `b`, ...
        `before = (c, d, ...)` means `name` runs before `c`, `d`, ...
    phase_label: string used in error diagnostics.
    """
    # Freeze input.
    items = list(triples)
    names = {n for n, _, _ in items}

    # Build `edges[u] = {v, ...}` meaning "u must precede v".
    edges: dict[str, set[str]] = defaultdict(set)
    indegree: dict[str, int] = {n: 0 for n in names}

    for name, after, before in items:
        # `name.after = (a,)` → a must precede name → edge a → name.
        for a in after:
            if a not in names:
                raise UnknownReferenceError(
                    f"{phase_label}: contribution {name!r} declares "
                    f"after={a!r} but {a!r} is not in the phase set",
                    data={"contribution": name, "reference": a, "kind": "after"},
                )
            if name not in edges[a]:
                edges[a].add(name)
                indegree[name] += 1
        # `name.before = (c,)` → name must precede c → edge name → c.
        for b in before:
            if b not in names:
                raise UnknownReferenceError(
                    f"{phase_label}: contribution {name!r} declares "
                    f"before={b!r} but {b!r} is not in the phase set",
                    data={"contribution": name, "reference": b, "kind": "before"},
                )
            if b not in edges[name]:
                edges[name].add(b)
                indegree[b] += 1

    # Kahn's with alphabetical tie-breaking (heapq of names).
    ready: list[str] = [n for n, d in indegree.items() if d == 0]
    heapq.heapify(ready)
    ordered: list[str] = []
    while ready:
        n = heapq.heappop(ready)
        ordered.append(n)
        for m in sorted(edges.get(n, ())):
            indegree[m] -= 1
            if indegree[m] == 0:
                heapq.heappush(ready, m)

    if len(ordered) != len(names):
        # Cycle exists somewhere in the remaining nodes.
        remaining = [n for n in names if n not in ordered]
        cycle_edges = []
        for u in remaining:
            for v in edges.get(u, ()):
                if v in remaining:
                    cycle_edges.append((u, v))
        raise OrderingCycleError(
            f"{phase_label}: ordering cycle detected among "
            f"{sorted(remaining)!r}; edges: {cycle_edges!r}",
            data={
                "phase": phase_label,
                "nodes": sorted(remaining),
                "edges": [list(e) for e in cycle_edges],
            },
        )

    return ordered
