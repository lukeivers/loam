# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Decaying retention with v1.1 R10 retention-class handling.

Per Luke's brief decisions:
  - 0–7 days: full fidelity.
  - 7–30 days: daily rollup + top-N longest spans kept raw.
  - 30–365 days: monthly rollup.
  - 365+ days: yearly rollup, or audit-only at a workspace-set cutoff.

All boundaries workspace-tunable in `AggregatorConfig.retention`.

The job is idempotent: re-running it produces the same rollup tables
and prunes nothing that wasn't already eligible. The job does not
delete `derived-only` or `ephemeral` records' structural metadata —
those records are already shape-reduced at ingest, and removing them
on aggregation would lose audit-of-existence facts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .config import AggregatorConfig
from .store import Store


@dataclass
class RetentionRunResult:
    daily_rollups_written: int
    monthly_rollups_written: int
    yearly_rollups_written: int
    raw_spans_pruned_full_to_daily: int
    raw_spans_pruned_daily_to_monthly: int
    raw_spans_pruned_monthly_to_yearly: int
    audit_pruned: int


class RetentionJob:
    """Runs the rollup/prune passes once per call.

    Schedule with `asyncio.create_task(periodic_rollup(...))` from a
    long-lived process, or invoke from the orchestrator's heartbeat.
    """

    def __init__(self, store: Store, config: AggregatorConfig) -> None:
        self.store = store
        self.config = config
        self.r = config.retention

    def run_once(self, now: datetime | None = None) -> RetentionRunResult:
        now = now or datetime.now(timezone.utc)
        # Boundary timestamps in nanoseconds.
        full_end = self._ns(now - timedelta(days=self.r.full_fidelity_days))
        daily_end = self._ns(now - timedelta(days=self.r.daily_rollup_end_days))
        monthly_end = self._ns(now - timedelta(days=self.r.monthly_rollup_end_days))

        d_written = self._daily_rollup(full_end, daily_end)
        m_written = self._monthly_rollup(daily_end, monthly_end)
        y_written = self._yearly_rollup(monthly_end)

        # Prune raw spans crossing the next-tier boundary, but keep
        # the top-N longest per day in the daily-rollup window.
        d_pruned = self._prune_full_to_daily(full_end, daily_end)
        dm_pruned = self._prune_daily_to_monthly(daily_end, monthly_end)
        my_pruned = self._prune_monthly_to_yearly(monthly_end)

        audit_pruned = 0
        if self.r.audit_cutoff_days is not None:
            cutoff = now - timedelta(days=self.r.audit_cutoff_days)
            audit_pruned = self._prune_audit(cutoff)

        return RetentionRunResult(
            daily_rollups_written=d_written,
            monthly_rollups_written=m_written,
            yearly_rollups_written=y_written,
            raw_spans_pruned_full_to_daily=d_pruned,
            raw_spans_pruned_daily_to_monthly=dm_pruned,
            raw_spans_pruned_monthly_to_yearly=my_pruned,
            audit_pruned=audit_pruned,
        )

    # ---- rollup writers ----

    def _daily_rollup(self, full_end_ns: int, daily_end_ns: int) -> int:
        """Aggregate spans in (daily_end_ns, full_end_ns] into daily_rollup."""
        # Pull spans in the window grouped by day/component/name/retention.
        rows = self.store.fetch(
            """
            SELECT start_time_unix_nano, component, name, status, duration_ns, retention_class
            FROM spans
            WHERE start_time_unix_nano > ? AND start_time_unix_nano <= ?
            """,
            (daily_end_ns, full_end_ns),
        )
        agg: dict[tuple[str, str, str, str], dict[str, int]] = {}
        for start_ns, component, name, status, dur, rclass in rows:
            day = datetime.fromtimestamp(start_ns / 1e9, tz=timezone.utc).date().isoformat()
            key = (day, component, name, rclass)
            bucket = agg.setdefault(
                key, {"span_count": 0, "total_duration_ns": 0, "error_count": 0}
            )
            bucket["span_count"] += 1
            bucket["total_duration_ns"] += int(dur or 0)
            if status == "ERROR":
                bucket["error_count"] += 1
        for (day, component, name, rclass), b in agg.items():
            self._upsert_daily(day, component, name, rclass, b)
        return len(agg)

    def _monthly_rollup(self, daily_end_ns: int, monthly_end_ns: int) -> int:
        rows = self.store.fetch(
            """
            SELECT start_time_unix_nano, component, name, status, duration_ns
            FROM spans
            WHERE start_time_unix_nano > ? AND start_time_unix_nano <= ?
            """,
            (monthly_end_ns, daily_end_ns),
        )
        agg: dict[tuple[str, str, str], dict[str, int]] = {}
        for start_ns, component, name, status, dur in rows:
            d = datetime.fromtimestamp(start_ns / 1e9, tz=timezone.utc)
            ym = f"{d.year:04d}-{d.month:02d}"
            key = (ym, component, name)
            bucket = agg.setdefault(
                key, {"span_count": 0, "total_duration_ns": 0, "error_count": 0}
            )
            bucket["span_count"] += 1
            bucket["total_duration_ns"] += int(dur or 0)
            if status == "ERROR":
                bucket["error_count"] += 1
        for (ym, component, name), b in agg.items():
            self._upsert_monthly(ym, component, name, b)
        return len(agg)

    def _yearly_rollup(self, monthly_end_ns: int) -> int:
        rows = self.store.fetch(
            """
            SELECT start_time_unix_nano, component, name, status, duration_ns
            FROM spans
            WHERE start_time_unix_nano <= ?
            """,
            (monthly_end_ns,),
        )
        agg: dict[tuple[int, str, str], dict[str, int]] = {}
        for start_ns, component, name, status, dur in rows:
            year = datetime.fromtimestamp(start_ns / 1e9, tz=timezone.utc).year
            key = (year, component, name)
            bucket = agg.setdefault(
                key, {"span_count": 0, "total_duration_ns": 0, "error_count": 0}
            )
            bucket["span_count"] += 1
            bucket["total_duration_ns"] += int(dur or 0)
            if status == "ERROR":
                bucket["error_count"] += 1
        for (year, component, name), b in agg.items():
            self._upsert_yearly(year, component, name, b)
        return len(agg)

    def _upsert_daily(self, day, component, name, rclass, b):
        # Try update; if no row, insert. Cross-substrate compatible.
        existing = self.store.fetch(
            "SELECT span_count FROM daily_rollup WHERE day = ? AND component = ? AND span_name = ? AND retention_class = ?",
            (day, component, name, rclass),
        )
        if existing:
            self.store.execute(
                "UPDATE daily_rollup SET span_count = ?, total_duration_ns = ?, error_count = ? "
                "WHERE day = ? AND component = ? AND span_name = ? AND retention_class = ?",
                (b["span_count"], b["total_duration_ns"], b["error_count"], day, component, name, rclass),
            )
        else:
            self.store.execute(
                "INSERT INTO daily_rollup (day, component, span_name, span_count, total_duration_ns, error_count, retention_class) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (day, component, name, b["span_count"], b["total_duration_ns"], b["error_count"], rclass),
            )

    def _upsert_monthly(self, ym, component, name, b):
        existing = self.store.fetch(
            "SELECT span_count FROM monthly_rollup WHERE year_month = ? AND component = ? AND span_name = ?",
            (ym, component, name),
        )
        if existing:
            self.store.execute(
                "UPDATE monthly_rollup SET span_count = ?, total_duration_ns = ?, error_count = ? "
                "WHERE year_month = ? AND component = ? AND span_name = ?",
                (b["span_count"], b["total_duration_ns"], b["error_count"], ym, component, name),
            )
        else:
            self.store.execute(
                "INSERT INTO monthly_rollup (year_month, component, span_name, span_count, total_duration_ns, error_count) VALUES (?, ?, ?, ?, ?, ?)",
                (ym, component, name, b["span_count"], b["total_duration_ns"], b["error_count"]),
            )

    def _upsert_yearly(self, year, component, name, b):
        existing = self.store.fetch(
            "SELECT span_count FROM yearly_rollup WHERE year = ? AND component = ? AND span_name = ?",
            (year, component, name),
        )
        if existing:
            self.store.execute(
                "UPDATE yearly_rollup SET span_count = ?, total_duration_ns = ?, error_count = ? "
                "WHERE year = ? AND component = ? AND span_name = ?",
                (b["span_count"], b["total_duration_ns"], b["error_count"], year, component, name),
            )
        else:
            self.store.execute(
                "INSERT INTO yearly_rollup (year, component, span_name, span_count, total_duration_ns, error_count) VALUES (?, ?, ?, ?, ?, ?)",
                (year, component, name, b["span_count"], b["total_duration_ns"], b["error_count"]),
            )

    # ---- pruners (raw spans removed once aggregated, top-N preserved in 7-30 window) ----

    def _prune_full_to_daily(self, full_end_ns: int, daily_end_ns: int) -> int:
        """Prune raw spans aged 7-30 days (configurable), keeping top-N longest per day."""
        # Pull all spans in the window, group by day, identify top-N to keep.
        rows = self.store.fetch(
            """
            SELECT span_id, start_time_unix_nano, duration_ns
            FROM spans
            WHERE start_time_unix_nano > ? AND start_time_unix_nano <= ?
            """,
            (daily_end_ns, full_end_ns),
        )
        if not rows:
            return 0
        per_day: dict[str, list[tuple[str, int]]] = {}
        for span_id, start_ns, dur in rows:
            day = datetime.fromtimestamp(start_ns / 1e9, tz=timezone.utc).date().isoformat()
            per_day.setdefault(day, []).append((span_id, int(dur or 0)))
        keep_ids: set[str] = set()
        for day, items in per_day.items():
            items.sort(key=lambda t: t[1], reverse=True)
            for sid, _ in items[: self.r.top_n_raw_per_day]:
                keep_ids.add(sid)
        # Delete spans in window not in keep_ids.
        delete_ids = [sid for (sid, _, _) in rows if sid not in keep_ids]
        return self._delete_span_ids(delete_ids)

    def _prune_daily_to_monthly(self, daily_end_ns: int, monthly_end_ns: int) -> int:
        rows = self.store.fetch(
            """
            SELECT span_id FROM spans
            WHERE start_time_unix_nano > ? AND start_time_unix_nano <= ?
            """,
            (monthly_end_ns, daily_end_ns),
        )
        return self._delete_span_ids([r[0] for r in rows])

    def _prune_monthly_to_yearly(self, monthly_end_ns: int) -> int:
        rows = self.store.fetch(
            "SELECT span_id FROM spans WHERE start_time_unix_nano <= ?",
            (monthly_end_ns,),
        )
        return self._delete_span_ids([r[0] for r in rows])

    def _delete_span_ids(self, span_ids: list[str]) -> int:
        if not span_ids:
            return 0
        # Batch DELETE; chunk to avoid huge IN clauses.
        deleted = 0
        chunk = 500
        for i in range(0, len(span_ids), chunk):
            batch = span_ids[i:i + chunk]
            placeholders = ", ".join("?" for _ in batch)
            self.store.execute(
                f"DELETE FROM span_events WHERE span_id IN ({placeholders})",
                batch,
            )
            self.store.execute(
                f"DELETE FROM spans WHERE span_id IN ({placeholders})",
                batch,
            )
            deleted += len(batch)
        return deleted

    def _prune_audit(self, cutoff: datetime) -> int:
        cutoff_iso = self.store._iso(cutoff)
        before = self.store.fetch("SELECT COUNT(*) FROM audit WHERE at_time < ?", (cutoff_iso,))
        count = int(before[0][0]) if before else 0
        self.store.execute("DELETE FROM audit WHERE at_time < ?", (cutoff_iso,))
        return count

    @staticmethod
    def _ns(dt: datetime) -> int:
        return int(dt.timestamp() * 1e9)
