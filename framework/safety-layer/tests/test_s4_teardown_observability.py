"""Amendment #26 — teardown observability retrofit (safety-layer).

Verifies SafetyStore.close() surfaces an inner-close failure to the
module logger per tightened CDC 2.
"""

from __future__ import annotations

import logging

from loam.safety_layer import SafetyStore


class _RaisingConn:
    def close(self):
        raise RuntimeError("synthetic close failure — amendment #26 test")


def test_s4_safety_store_close_surfaces_exception(tmp_path, caplog):
    store = SafetyStore(tmp_path / "safety.sqlite")
    store._conn = _RaisingConn()  # type: ignore[assignment]

    with caplog.at_level(logging.DEBUG, logger="loam.safety_layer.store"):
        store.close()

    matching = [
        r for r in caplog.records
        if r.name == "loam.safety_layer.store"
        and r.message == "safety_store_close_failed"
    ]
    assert len(matching) == 1
    assert matching[0].exc_info is not None
    assert matching[0].levelno == logging.DEBUG
