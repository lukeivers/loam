"""D7 — Decaying retention + retention-class handling."""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

from pos_observability_aggregator.api import QueryAPI, SpanFilter
from pos_observability_aggregator.config import RetentionConfig
from pos_observability_aggregator.retention import RetentionJob
from pos_observability_aggregator.schema import RetentionClass, SpanRecord


def _span_at(ts: datetime, span_id: str, name: str = "op", duration_ns: int = 1_000_000, status="OK", attrs=None):
    ns = int(ts.timestamp() * 1e9)
    return SpanRecord(
        trace_id="t" * 32, span_id=span_id, name=name,
        tracer_name="loam.scope_of_work", component="scope_of_work",
        start_time_unix_nano=ns, end_time_unix_nano=ns + duration_ns,
        status=status, attributes=attrs or {},
    )


def test_full_fidelity_window_preserves_all_spans(store, tmp_config):
    now = datetime.now(timezone.utc)
    for i in range(3):
        store.insert_span(_span_at(now - timedelta(days=i), f"{i:016x}"))
    job = RetentionJob(store, tmp_config)
    job.run_once(now=now)
    api = QueryAPI(store)
    spans = api.find_spans(SpanFilter(components=["scope_of_work"]), limit=100)
    assert len(spans) == 3  # all within 7-day full fidelity


def test_daily_rollup_in_7_to_30_day_window(store, tmp_config):
    now = datetime.now(timezone.utc)
    # Insert 5 spans aged 14 days (in the 7-30 daily-rollup window).
    for i in range(5):
        store.insert_span(_span_at(now - timedelta(days=14), f"{i:016x}", name="aged_op"))
    job = RetentionJob(store, tmp_config)
    res = job.run_once(now=now)
    assert res.daily_rollups_written >= 1
    rows = store.fetch("SELECT span_count FROM daily_rollup")
    assert sum(int(r[0]) for r in rows) == 5


def test_top_n_raw_spans_kept_in_daily_window(tmp_path, tmp_config):
    """Top-N longest spans within the daily-rollup window are kept raw."""
    from pos_observability_aggregator import open_store
    cfg = tmp_config
    cfg.retention = RetentionConfig(top_n_raw_per_day=2)
    store = open_store(cfg)
    try:
        now = datetime.now(timezone.utc)
        # 5 spans on the same day, durations 1, 2, 3, 4, 5 seconds.
        target_day = now - timedelta(days=14)
        for i, dur_s in enumerate([1, 2, 3, 4, 5]):
            store.insert_span(_span_at(
                target_day, f"{i:016x}", name="contender", duration_ns=int(dur_s * 1e9)
            ))
        job = RetentionJob(store, cfg)
        job.run_once(now=now)
        api = QueryAPI(store)
        # After run, 2 longest spans (durations 5s, 4s) should remain raw.
        remaining = api.find_spans(SpanFilter(name_exact="contender"), limit=10)
        assert len(remaining) == 2
        # Both should be the longest two.
        durations = sorted([s.duration_ns for s in remaining])
        assert durations == [int(4e9), int(5e9)]
    finally:
        store.close()


def test_monthly_rollup_in_30_to_365_day_window(store, tmp_config):
    now = datetime.now(timezone.utc)
    # 3 spans aged 100 days.
    for i in range(3):
        store.insert_span(_span_at(now - timedelta(days=100), f"{i:016x}", name="monthly_op"))
    job = RetentionJob(store, tmp_config)
    res = job.run_once(now=now)
    assert res.monthly_rollups_written >= 1
    rows = store.fetch("SELECT span_count FROM monthly_rollup")
    assert sum(int(r[0]) for r in rows) == 3


def test_yearly_rollup_after_365_days(store, tmp_config):
    now = datetime.now(timezone.utc)
    # 2 spans aged 400 days.
    for i in range(2):
        store.insert_span(_span_at(now - timedelta(days=400), f"{i:016x}", name="yearly_op"))
    job = RetentionJob(store, tmp_config)
    res = job.run_once(now=now)
    assert res.yearly_rollups_written >= 1
    rows = store.fetch("SELECT span_count FROM yearly_rollup")
    assert sum(int(r[0]) for r in rows) == 2


def test_retention_class_normal_stored_fully(store):
    s = SpanRecord(
        trace_id="t" * 32, span_id="0" * 16, name="op",
        tracer_name="loam.memory", component="memory_system",
        start_time_unix_nano=1000, end_time_unix_nano=2000,
        attributes={"inputs": "raw text", "k": "v"},
        retention_class=RetentionClass.NORMAL,
    )
    store.insert_span(s)
    api = QueryAPI(store)
    out = api.find_spans(SpanFilter(name_exact="op"))[0]
    assert out.attributes.get("inputs") == "raw text"


def test_retention_class_derived_only_drops_payload(store):
    s = SpanRecord(
        trace_id="t" * 32, span_id="0" * 16, name="op",
        tracer_name="loam.memory", component="memory_system",
        start_time_unix_nano=1000, end_time_unix_nano=2000,
        attributes={"inputs": "raw text", "outputs": "raw out", "kept": "yes"},
        retention_class=RetentionClass.DERIVED_ONLY,
    )
    store.insert_span(s)
    api = QueryAPI(store)
    out = api.find_spans(SpanFilter(name_exact="op"))[0]
    assert "inputs" not in out.attributes
    assert "outputs" not in out.attributes
    assert out.attributes.get("kept") == "yes"


def test_retention_class_ephemeral_keeps_only_stub(store):
    s = SpanRecord(
        trace_id="t" * 32, span_id="0" * 16, name="op",
        tracer_name="loam.memory", component="memory_system",
        start_time_unix_nano=1000, end_time_unix_nano=2000,
        attributes={"inputs": "raw text", "any_key": "value"},
        retention_class=RetentionClass.EPHEMERAL,
    )
    store.insert_span(s)
    api = QueryAPI(store)
    out = api.find_spans(SpanFilter(name_exact="op"))[0]
    # No payload of any kind preserved.
    assert "inputs" not in out.attributes
    assert "any_key" not in out.attributes


def test_retention_class_is_queryable(store):
    """Users can audit what's been dropped via filter on retention_class."""
    classes = [RetentionClass.NORMAL, RetentionClass.DERIVED_ONLY, RetentionClass.EPHEMERAL]
    for i, rc in enumerate(classes):
        store.insert_span(SpanRecord(
            trace_id="t" * 32, span_id=f"{i:016x}", name=f"op_{rc.value}",
            tracer_name="loam.memory", component="memory_system",
            start_time_unix_nano=1000 + i, end_time_unix_nano=2000 + i,
            attributes={},
            retention_class=rc,
        ))
    api = QueryAPI(store)
    for rc in classes:
        out = api.find_spans(SpanFilter(retention_class=rc))
        assert len(out) == 1
        assert out[0].retention_class is rc


def test_rollup_idempotent(store, tmp_config):
    now = datetime.now(timezone.utc)
    for i in range(3):
        store.insert_span(_span_at(now - timedelta(days=14), f"{i:016x}", name="repeat_op"))
    job = RetentionJob(store, tmp_config)
    job.run_once(now=now)
    rows1 = store.fetch("SELECT day, span_count FROM daily_rollup ORDER BY day")
    job.run_once(now=now)
    rows2 = store.fetch("SELECT day, span_count FROM daily_rollup ORDER BY day")
    assert rows1 == rows2
