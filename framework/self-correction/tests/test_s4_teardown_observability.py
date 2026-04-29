"""Amendment #26 — teardown observability retrofit (self-correction).

Verifies CorrectionStore.close() surfaces an inner-close failure to
the module logger per tightened CDC 2.
"""

from __future__ import annotations

import logging

from loam.self_correction import CorrectionStore


class _RaisingConn:
    def close(self):
        raise RuntimeError("synthetic close failure — amendment #26 test")


def test_s4_correction_store_close_surfaces_exception(tmp_path, caplog):
    store_path = tmp_path / "correction.sqlite"
    store = CorrectionStore(store_path)
    store._conn = _RaisingConn()  # type: ignore[assignment]

    with caplog.at_level(logging.DEBUG, logger="loam.self_correction.store"):
        store.close()

    matching = [
        r for r in caplog.records
        if r.name == "loam.self_correction.store"
        and r.message == "self_correction_store_close_failed"
    ]
    assert len(matching) == 1
    assert matching[0].exc_info is not None
    assert matching[0].levelno == logging.DEBUG
