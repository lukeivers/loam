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

"""AC.LEASE.3 — the admission throttle: with the ceiling at N, N
non-overlapping grants succeed and the (N+1)th is refused with an
admission-control refusal (distinct from an overlap refusal); releasing
one admits a subsequent request.
"""

from __future__ import annotations

from loam.file_lease_registry import Lease, LeaseRefusal, LeaseRegistry


def test_AC_LEASE_3_ceiling_refuses_then_release_admits(tmp_path):
    reg = LeaseRegistry(tmp_path / "leases.json", max_concurrent_leases=2)

    a = reg.grant_or_refuse("d1", ["src/a/**"])
    b = reg.grant_or_refuse("d2", ["src/b/**"])
    assert isinstance(a, Lease) and isinstance(b, Lease)

    # Third grant is non-overlapping but exceeds the ceiling.
    c = reg.grant_or_refuse("d3", ["src/c/**"])
    assert isinstance(c, LeaseRefusal)
    assert c.kind == "admission"
    assert c.holder_dispatch_id is None  # ceiling names no single holder

    # Releasing one active lease admits the pending request.
    assert reg.release("d1") == 1
    c2 = reg.grant_or_refuse("d3", ["src/c/**"])
    assert isinstance(c2, Lease)
    assert c2.dispatch_id == "d3"
