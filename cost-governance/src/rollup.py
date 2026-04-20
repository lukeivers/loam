"""Rolling-window interval-closure + retention.

Idempotent under double-run and clock skew (C17). Scheduled interval
is `min(window.duration_seconds) / 10` in production (6 minutes for
the default daily+hourly config); tests drive the task directly.

The closure algorithm: for each configured rolling window, compute
the "bucket" boundaries keyed on unix wall-time. A bucket closes
once wall-time has moved past its `interval_end_unix`. The PRIMARY
KEY on `(window_kind, interval_end_unix)` in `rolling_rollups`
provides idempotence; a second closure attempt silently no-ops.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from . import observability as obs
from .config import CostConfig, RollingCeiling
from .spec import RollingRollup, iso_now, unix_now
from .store import CostStore


@dataclass
class RollupRunResult:
    intervals_closed: int
    reservations_pruned: int
    sessions_pruned: int


class RollupTask:
    """Per-call rolling-window closer + retention pass."""

    def __init__(
        self,
        *,
        store: CostStore,
        config: CostConfig,
        reservation_retention_days: int = 30,
        session_retention_days: int = 365,
    ) -> None:
        self.store = store
        self.config = config
        self.reservation_retention_days = reservation_retention_days
        self.session_retention_days = session_retention_days

    # -- closure -----------------------------------------------------

    def run_once(self, now: float | None = None) -> RollupRunResult:
        now = now if now is not None else unix_now()
        intervals_closed = 0
        for rc in self.config.rolling:
            intervals_closed += self._close_window(rc, now=now)

        res_pruned = self._prune_reservations(now=now)
        sess_pruned = self._prune_sessions(now=now)
        obs.retention_pruned(
            reservations_pruned=res_pruned, sessions_pruned=sess_pruned
        )
        return RollupRunResult(
            intervals_closed=intervals_closed,
            reservations_pruned=res_pruned,
            sessions_pruned=sess_pruned,
        )

    def _close_window(self, rc: RollingCeiling, *, now: float) -> int:
        """Close any fully-elapsed intervals for this window.

        Buckets align on unix-time modulo `duration_seconds`. The
        algorithm finds every bucket whose `end <= now` that has not
        yet been closed, sums the session rollups that ended inside
        the bucket (plus reconciled reservations that closed inside
        the bucket) and writes a `rolling_rollups` row. Idempotent
        via the PRIMARY KEY conflict.

        Under clock skew (e.g. suspend/resume), `now` jumps forward;
        the loop walks every skipped bucket and closes each — C17.
        """
        duration = rc.duration_seconds
        latest_end = self._latest_closed_end_unix(rc.window_kind)
        # If no prior close, start from the bucket immediately before
        # the earliest reconciled reservation — or `now - 2 * duration`
        # as a safe backfill anchor.
        if latest_end is None:
            start_from = now - 2.0 * duration
        else:
            start_from = latest_end

        closed = 0
        # Walk forward in bucket-size steps until the next interval
        # would extend beyond `now`. `_next_bucket_end` aligns the
        # boundary.
        cursor = self._next_bucket_end(start_from, duration)
        # Cap the walk to avoid pathological unbounded loops on
        # suspended-forever clocks — 10,000 buckets is ~14 years of
        # hourly, far more than any realistic skew.
        max_iter = 10000
        while cursor <= now and max_iter > 0:
            interval_end = cursor
            interval_start = interval_end - duration
            totals = self._sum_interval(
                interval_start=interval_start,
                interval_end=interval_end,
            )
            rollup = RollingRollup(
                window_kind=rc.window_kind,
                interval_start_unix=interval_start,
                interval_end_unix=interval_end,
                total_time_seconds=totals[0],
                total_tokens=totals[1],
                total_money_cents=totals[2],
                closed_at=iso_now(),
            )
            inserted = self.store.upsert_rolling_rollup(rollup)
            if inserted:
                closed += 1
                obs.rollup_closed(
                    window_kind=rc.window_kind,
                    interval_end_unix=interval_end,
                    total_money_cents=totals[2],
                )
            cursor += duration
            max_iter -= 1
        return closed

    def _latest_closed_end_unix(self, window_kind: str) -> float | None:
        rows = self.store.list_rolling_rollups(window_kind=window_kind)
        if not rows:
            return None
        return max(r.interval_end_unix for r in rows)

    @staticmethod
    def _next_bucket_end(start_from: float, duration: int) -> float:
        """Align forward: the next bucket boundary after `start_from`."""
        # Compute the next multiple-of-duration that is strictly > start_from.
        n = math.floor(start_from / duration) + 1
        return float(n * duration)

    def _sum_interval(
        self, *, interval_start: float, interval_end: float
    ) -> tuple[int, int, int]:
        """Aggregate spend inside [start, end].

        The rolling-rollup represents the spend that closed (reconciled)
        inside the interval. For the v1.0 ledger that means:
          - reconciled reservations with reconciled_at in the interval
          - plus any in-flight debits on currently-active reservations?
            No — in-flight is captured as "live" in the session rollup;
            the closed-interval total reflects terminal outcomes only.

        This gives clean audit semantics: each rolling-rollup row is
        "what spent between T and T+d" without needing to re-read
        ephemeral debit streams.
        """
        start_iso = datetime.fromtimestamp(interval_start, tz=timezone.utc).isoformat()
        end_iso = datetime.fromtimestamp(interval_end, tz=timezone.utc).isoformat()
        all_reservations = self.store.list_all_reservations()
        t = k = m = 0
        for r in all_reservations:
            if r.reconciled_at is None:
                continue
            if start_iso <= r.reconciled_at < end_iso:
                t += r.actual_time_seconds
                k += r.actual_tokens
                m += r.actual_money_cents
        return t, k, m

    # -- retention ---------------------------------------------------

    def _prune_reservations(self, *, now: float) -> int:
        cutoff = datetime.fromtimestamp(now, tz=timezone.utc) - timedelta(
            days=self.reservation_retention_days
        )
        return self.store.prune_reconciled_before(iso_cutoff=cutoff.isoformat())

    def _prune_sessions(self, *, now: float) -> int:
        cutoff = datetime.fromtimestamp(now, tz=timezone.utc) - timedelta(
            days=self.session_retention_days
        )
        return self.store.prune_sessions_before(iso_cutoff=cutoff.isoformat())
