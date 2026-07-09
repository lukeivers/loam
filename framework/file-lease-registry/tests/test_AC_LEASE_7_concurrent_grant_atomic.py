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

"""AC.LEASE.7 — two concurrent grant requests for OVERLAPPING globs
against the same store resolve to exactly one granted lease and one
refusal: the overlap-check-and-write critical section is atomic, so the
"structurally cannot both be granted" guarantee holds under a race.
"""

from __future__ import annotations

import threading

from loam.file_lease_registry import Lease, LeaseRefusal, LeaseRegistry


def test_AC_LEASE_7_concurrent_overlapping_grants_exactly_one_wins(tmp_path):
    reg = LeaseRegistry(tmp_path / "leases.json")

    results: list[Lease | LeaseRefusal] = []
    barrier = threading.Barrier(2)

    def attempt(dispatch_id, glob):
        barrier.wait()  # maximise contention on the critical section
        results.append(reg.grant_or_refuse(dispatch_id, [glob]))

    t1 = threading.Thread(target=attempt, args=("d1", "src/shared/**"))
    t2 = threading.Thread(target=attempt, args=("d2", "src/shared/mod.py"))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    grants = [r for r in results if isinstance(r, Lease)]
    refusals = [r for r in results if isinstance(r, LeaseRefusal)]
    assert len(grants) == 1
    assert len(refusals) == 1
    assert refusals[0].kind == "overlap"
    # exactly one lease persisted
    assert len(reg.active_leases()) == 1
