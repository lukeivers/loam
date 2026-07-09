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

"""AC.LEASE.1 (outcome-altitude) — grant / conservative-overlap-refuse /
disjoint-grant, through the production entry point against a real
on-disk store with no pre-set state.
"""

from __future__ import annotations

from loam.file_lease_registry import Lease, LeaseRefusal, LeaseRegistry


def test_AC_LEASE_1_grant_then_overlap_refuse_then_disjoint_grant(tmp_path):
    reg = LeaseRegistry(tmp_path / "leases.json")

    # (a) grant src/auth/** to dispatch-1
    a = reg.grant_or_refuse("dispatch-1", ["src/auth/**"])
    assert isinstance(a, Lease)
    assert a.globs == ("src/auth/**",)

    # (b) a descendant path overlaps → refused, naming the holder
    b = reg.grant_or_refuse("dispatch-2", ["src/auth/login.py"])
    assert isinstance(b, LeaseRefusal)
    assert b.kind == "overlap"
    assert b.holder_dispatch_id == "dispatch-1"
    assert "dispatch-1" in b.message

    # (c) a disjoint subtree is granted
    c = reg.grant_or_refuse("dispatch-2", ["src/billing/**"])
    assert isinstance(c, Lease)
    assert c.globs == ("src/billing/**",)

    # only two live leases exist (the refused one did not land)
    held = {l.dispatch_id for l in reg.active_leases()}
    assert held == {"dispatch-1", "dispatch-2"}


def test_AC_LEASE_1_ancestor_request_also_conflicts(tmp_path):
    # Conservative: a request that is an ANCESTOR of a held glob conflicts
    # too (not only descendants), so overlap is symmetric.
    reg = LeaseRegistry(tmp_path / "leases.json")
    assert isinstance(reg.grant_or_refuse("d1", ["src/auth/login.py"]), Lease)
    r = reg.grant_or_refuse("d2", ["src/auth/**"])
    assert isinstance(r, LeaseRefusal)
    assert r.kind == "overlap"
    assert r.holder_dispatch_id == "d1"
