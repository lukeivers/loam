"""Amendment #26 — teardown observability retrofit (reversibility).

Verifies ReversibilityStore.close() surfaces an inner-close failure to
the module logger per tightened CDC 2.
"""

from __future__ import annotations

import logging

from reversibility_primitive import ReversibilityStore


class _RaisingConn:
    def close(self):
        raise RuntimeError("synthetic close failure — amendment #26 test")


def test_s4_reversibility_store_close_surfaces_exception(tmp_path, caplog):
    store = ReversibilityStore(tmp_path / "reversibility.sqlite")
    store._conn = _RaisingConn()  # type: ignore[assignment]

    with caplog.at_level(
        logging.DEBUG, logger="reversibility_primitive.store"
    ):
        store.close()

    matching = [
        r for r in caplog.records
        if r.name == "reversibility_primitive.store"
        and r.message == "reversibility_store_close_failed"
    ]
    assert len(matching) == 1
    assert matching[0].exc_info is not None
    assert matching[0].levelno == logging.DEBUG
