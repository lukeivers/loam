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

"""AC.LEASE.4 — a lease whose holder is artifact-probe-dead (judged by
the SHARED ``probe_liveness`` reader, past the startup grace) is reaped,
and a post-reap request for the reaped globs is granted.  A holder with a
FRESH artifact is not reaped.  Uses the real reader against real run dirs.
"""

from __future__ import annotations

import json
import os
import time

from loam.file_lease_registry import Lease, LeaseRegistry


def _age_lease(store_path, dispatch_id, new_granted_at):
    raw = json.loads(store_path.read_text())
    for r in raw["leases"]:
        if r["dispatch_id"] == dispatch_id:
            r["granted_at"] = new_granted_at
    store_path.write_text(json.dumps(raw))


def test_AC_LEASE_4_dead_holder_reaped_and_globs_regrantable(tmp_path):
    store = tmp_path / "leases.json"
    reg = LeaseRegistry(store, startup_grace_s=300.0, stale_after_s=300.0)

    # Dead holder: run dir with a stale artifact (mtime long past).
    dead_dir = tmp_path / "run-dead"
    dead_dir.mkdir()
    art = dead_dir / "run_record.jsonl"
    art.write_text('{"stage": "old"}\n')
    old = time.time() - 10_000
    os.utime(art, (old, old))

    # Live holder: run dir with a fresh artifact.
    live_dir = tmp_path / "run-live"
    live_dir.mkdir()
    (live_dir / "run_record.jsonl").write_text('{"stage": "now"}\n')

    dead = reg.grant_or_refuse("dead-1", ["src/auth/**"], run_dir=dead_dir)
    live = reg.grant_or_refuse("live-1", ["src/pay/**"], run_dir=live_dir)
    assert isinstance(dead, Lease) and isinstance(live, Lease)

    # Age BOTH leases past the startup grace so the probe verdict decides.
    _age_lease(store, "dead-1", time.time() - 10_000)
    _age_lease(store, "live-1", time.time() - 10_000)

    reaped = reg.reap()
    assert [l.dispatch_id for l in reaped] == ["dead-1"]

    remaining = {l.dispatch_id for l in reg.active_leases()}
    assert remaining == {"live-1"}  # the live holder survives

    # The reaped globs are grantable again.
    regrant = reg.grant_or_refuse("dead-2", ["src/auth/login.py"])
    assert isinstance(regrant, Lease)
