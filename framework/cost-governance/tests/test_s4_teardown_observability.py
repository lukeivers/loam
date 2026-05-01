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

"""Amendment #26 — teardown observability retrofit.

Verifies CostStore.close() surfaces an inner-close failure to the
module logger per tightened CDC 2 at ``9559ca7``. Bare pass inside a
teardown broad-catch is no longer ODD-legit; the emission is the
forensic-trail guarantee.
"""

from __future__ import annotations

import logging

import pytest

from loam.cost_governance import CostStore


def _raising_close():
    raise RuntimeError("synthetic close failure — amendment #26 test")


class _RaisingConn:
    def close(self):
        raise RuntimeError("synthetic close failure — amendment #26 test")


def test_s4_cost_store_close_surfaces_exception(tmp_path, caplog):
    """CostStore.close() swallows the inner close exception but emits
    a DEBUG-level log record with the exception info — never silent."""
    store_path = tmp_path / "cost.sqlite"
    store = CostStore(store_path)
    # Replace the inner connection with a stub whose close raises.
    store._conn = _RaisingConn()  # type: ignore[assignment]

    with caplog.at_level(logging.DEBUG, logger="loam.cost_governance.store"):
        # Must not raise.
        store.close()

    # Emission shape: named "cost_store_close_failed" at DEBUG with
    # exc_info attached.
    matching = [
        r for r in caplog.records
        if r.name == "loam.cost_governance.store"
        and r.message == "cost_store_close_failed"
    ]
    assert len(matching) == 1, (
        f"expected exactly one teardown emission; got {len(matching)} "
        f"from records {[r.message for r in caplog.records]}"
    )
    assert matching[0].exc_info is not None
    assert matching[0].levelno == logging.DEBUG
