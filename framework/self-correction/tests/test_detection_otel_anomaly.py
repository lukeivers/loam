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

"""CR3 — OTel anomaly detection via aggregator poll (ruling #2).

Anomaly predicate: `status == "ERROR"` AND `retention_class == NORMAL`.

CHALLENGE: the ruling text says `retention_class == "high"` but the
aggregator's enum has no `high` value. The correct mapping is
`RetentionClass.NORMAL` — full-fidelity (non-sampled) spans worth
investigating. Documented in return summary.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from loam.observability_aggregator.api import QueryAPI
from loam.observability_aggregator.config import AggregatorConfig
from loam.observability_aggregator.schema import RetentionClass, SpanRecord
from loam.observability_aggregator.store import Store

from loam.self_correction import OTelAnomalyPoller, TriggerSource
from loam.self_correction.triggers import build_trigger_from_span


def _make_span(
    *,
    name: str,
    status: str,
    retention_class: RetentionClass,
    span_id: str = "sp-1",
    trace_id: str = "tr-abc",
) -> SpanRecord:
    now_ns = int(datetime.now(timezone.utc).timestamp() * 1e9)
    return SpanRecord(
        trace_id=trace_id,
        span_id=span_id,
        parent_span_id=None,
        name=name,
        tracer_name="loam.test",
        component="other",
        kind="INTERNAL",
        start_time_unix_nano=now_ns,
        end_time_unix_nano=now_ns + 1_000_000,
        status=status,
        status_message="boom" if status == "ERROR" else None,
        attributes={"loam.scope.id": "scope-xyz"},
        retention_class=retention_class,
    )


@pytest.fixture
def api(tmp_path: Path) -> QueryAPI:
    cfg = AggregatorConfig(
        base_dir=str(tmp_path),
        substrate="sqlite",
        db_path=str(tmp_path / "obs.sqlite"),
    )
    store = Store(cfg)
    return QueryAPI(store)


async def test_CR3_error_normal_span_fires_trigger(api: QueryAPI) -> None:
    api.store.insert_span(
        _make_span(
            name="loam.cost.activation_refused",
            status="ERROR",
            retention_class=RetentionClass.NORMAL,
        )
    )

    seen: list = []

    async def handler(trigger):
        seen.append(trigger)

    poller = OTelAnomalyPoller(
        query_api=api, handler=handler, poll_interval_seconds=30
    )
    dispatched = await poller.run_once()

    assert dispatched == 1
    assert len(seen) == 1
    assert seen[0].source == TriggerSource.otel_anomaly
    assert seen[0].scope_id == "scope-xyz"


async def test_CR3_error_without_normal_retention_does_not_fire(
    api: QueryAPI,
) -> None:
    # DERIVED_ONLY spans are sampled/reduced — anomaly poll skips them.
    api.store.insert_span(
        _make_span(
            name="loam.other.failure",
            status="ERROR",
            retention_class=RetentionClass.DERIVED_ONLY,
            span_id="sp-derived",
        )
    )

    seen: list = []

    async def handler(trigger):
        seen.append(trigger)

    poller = OTelAnomalyPoller(
        query_api=api, handler=handler, poll_interval_seconds=30
    )
    dispatched = await poller.run_once()
    assert dispatched == 0
    assert seen == []


async def test_CR3_ok_status_never_fires(api: QueryAPI) -> None:
    api.store.insert_span(
        _make_span(
            name="loam.scope.ok",
            status="OK",
            retention_class=RetentionClass.NORMAL,
            span_id="sp-ok",
        )
    )

    seen: list = []

    async def handler(trigger):
        seen.append(trigger)

    poller = OTelAnomalyPoller(
        query_api=api, handler=handler, poll_interval_seconds=30
    )
    assert await poller.run_once() == 0
    assert seen == []


async def test_CR3_poller_dedups_seen_span_ids(api: QueryAPI) -> None:
    api.store.insert_span(
        _make_span(
            name="loam.cost.activation_refused",
            status="ERROR",
            retention_class=RetentionClass.NORMAL,
            span_id="sp-once",
        )
    )

    seen: list = []

    async def handler(trigger):
        seen.append(trigger)

    poller = OTelAnomalyPoller(
        query_api=api, handler=handler, poll_interval_seconds=30
    )
    assert await poller.run_once() == 1
    # Second pass — same span already seen by the poller; does not
    # re-fire. (Additional trigger-level dedup via SHA-256 happens in
    # the controller.)
    assert await poller.run_once() == 0


def test_build_trigger_from_span_shape() -> None:
    sp = _make_span(
        name="loam.test.failure",
        status="ERROR",
        retention_class=RetentionClass.NORMAL,
    )
    tr = build_trigger_from_span(span=sp)
    assert tr.source == TriggerSource.otel_anomaly
    assert tr.trace_id == "tr-abc"
    assert tr.scope_id == "scope-xyz"
    assert tr.raw_payload["retention_class"] == "normal"
