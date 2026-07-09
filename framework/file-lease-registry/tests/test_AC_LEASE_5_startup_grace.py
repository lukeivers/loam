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

"""AC.LEASE.5 — startup grace: a freshly granted lease whose run dir has
no artifacts yet is NOT reaped within the grace window (a live agent
still spinning up keeps its claim).  Only after the grace elapses without
fresh artifacts does the probe-dead judgment make it reapable.
"""

from __future__ import annotations

import json
import time

from loam.file_lease_registry import Lease, LeaseRegistry


def _age_lease(store_path, dispatch_id, new_granted_at):
    raw = json.loads(store_path.read_text())
    for r in raw["leases"]:
        if r["dispatch_id"] == dispatch_id:
            r["granted_at"] = new_granted_at
    store_path.write_text(json.dumps(raw))


def test_AC_LEASE_5_newborn_survives_grace_then_reapable_after(tmp_path):
    store = tmp_path / "leases.json"
    reg = LeaseRegistry(store, startup_grace_s=300.0, stale_after_s=300.0)

    # Newborn: run dir exists but has produced no artifacts yet, so the
    # bare probe would read it as dead — the grace floor must protect it.
    run_dir = tmp_path / "run-newborn"
    run_dir.mkdir()
    lease = reg.grant_or_refuse("newborn", ["src/x/**"], run_dir=run_dir)
    assert isinstance(lease, Lease)

    assert reg.reap() == []
    assert [l.dispatch_id for l in reg.active_leases()] == ["newborn"]

    # Past the grace window, still no artifacts → now reapable.
    _age_lease(store, "newborn", time.time() - 10_000)
    reaped = reg.reap()
    assert [l.dispatch_id for l in reaped] == ["newborn"]
    assert reg.active_leases() == []
