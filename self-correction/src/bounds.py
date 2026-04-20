"""Depth + cascade bounds (CR15, CR16).

Both bounds run at trigger intake, before `activate_scope`. On trip,
the controller records the refusal and dispatches a one-on-one channel
notification; no correction scope is opened.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from .config import CorrectionConfig
from .store import CorrectionStore


@dataclass(frozen=True)
class DepthCapTripped:
    reason: str  # "depth_cap"
    depth: int
    cap: int
    parent_correction_id: str | None


@dataclass(frozen=True)
class CascadeTripped:
    reason: str  # "same_class_cascade"
    failure_class: str
    window_count: int
    threshold: int
    window_seconds: int


def compute_depth(
    *,
    parent_correction_id: str | None,
    store: CorrectionStore,
) -> int:
    """Walk `parent_correction_id` chain and return the number of
    ancestor correction episodes (1 = one ancestor, the triggering
    correction).
    """
    depth = 0
    current = parent_correction_id
    seen: set[str] = set()
    while current is not None and current not in seen:
        seen.add(current)
        depth += 1
        ep = store.get_episode(current)
        if ep is None:
            break
        current = ep.parent_correction_id
    return depth


def depth_cap_check(
    *,
    parent_correction_id: str | None,
    store: CorrectionStore,
    config: CorrectionConfig,
) -> DepthCapTripped | None:
    depth = compute_depth(
        parent_correction_id=parent_correction_id, store=store
    )
    # A chain with `config.depth_cap` ancestors means the incoming
    # trigger would open the (depth_cap + 1)th — refuse.
    if depth >= config.depth_cap:
        return DepthCapTripped(
            reason="depth_cap",
            depth=depth,
            cap=config.depth_cap,
            parent_correction_id=parent_correction_id,
        )
    return None


def same_class_cascade_check(
    *,
    failure_class: str,
    store: CorrectionStore,
    config: CorrectionConfig,
    now: float | None = None,
) -> CascadeTripped | None:
    """Count episodes of identical `failure_class` in the window.

    Excludes `refused` rows (they never opened a scope; counting them
    would double-charge the class). Opening this new episode would
    make the count `existing + 1` — trip when that value would meet
    or exceed the threshold.
    """
    now = now if now is not None else time.time()
    since = now - config.cascade_window_seconds
    existing = store.list_episodes_by_class_since(
        failure_class=failure_class, since_unix=since
    )
    # If opening one more would exceed the threshold, refuse.
    if len(existing) + 1 >= config.cascade_threshold:
        return CascadeTripped(
            reason="same_class_cascade",
            failure_class=failure_class,
            window_count=len(existing) + 1,
            threshold=config.cascade_threshold,
            window_seconds=config.cascade_window_seconds,
        )
    return None
