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
