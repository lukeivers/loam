"""Amendment #26 — teardown observability retrofit (aggregator).

Verifies observability-aggregator's Store.close() surfaces an inner-
close failure to the module logger per tightened CDC 2.

The aggregator's store holds its own substrate; the logger name
follows the aggregator's existing `loam.aggregator.*` convention
(ingest.py:59).
"""

from __future__ import annotations

import logging

from loam.observability_aggregator import AggregatorConfig, open_store
from loam.observability_aggregator.config import IngestConfig, RetentionConfig


class _RaisingConn:
    def close(self):
        raise RuntimeError("synthetic close failure — amendment #26 test")


def _make_store(tmp_path):
    cfg = AggregatorConfig(
        db_path=tmp_path / "aggregator.sqlite",
        substrate="sqlite",
        ingest=IngestConfig(),
        retention=RetentionConfig(),
    )
    return open_store(cfg)


def test_s4_aggregator_store_close_surfaces_exception(tmp_path, caplog):
    store = _make_store(tmp_path)
    store._conn = _RaisingConn()  # type: ignore[assignment]

    with caplog.at_level(logging.DEBUG, logger="loam.aggregator.store"):
        store.close()

    matching = [
        r for r in caplog.records
        if r.name == "loam.aggregator.store"
        and r.message == "aggregator_store_close_failed"
    ]
    assert len(matching) == 1
    assert matching[0].exc_info is not None
    assert matching[0].levelno == logging.DEBUG
