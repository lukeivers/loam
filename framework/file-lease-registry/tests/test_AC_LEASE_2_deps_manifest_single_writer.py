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

"""AC.LEASE.2 — the dependency-manifest set is one exclusive lease: a
second deps-touching grant is refused while the first is held, and
admitted after release.  The two grants' non-deps globs are disjoint, so
only the deps single-writer rule can cause the refusal.
"""

from __future__ import annotations

from loam.file_lease_registry import (
    DEPS_MANIFEST_KEY,
    Lease,
    LeaseRefusal,
    LeaseRegistry,
)


def test_AC_LEASE_2_second_deps_touch_refused_until_release(tmp_path):
    reg = LeaseRegistry(tmp_path / "leases.json")

    first = reg.grant_or_refuse("d1", ["src/pkg-a/**", "package.json"])
    assert isinstance(first, Lease)
    assert first.deps_manifest is True

    # Disjoint code globs, but both touch the deps set → refused.
    second = reg.grant_or_refuse("d2", ["src/pkg-b/**", "poetry.lock"])
    assert isinstance(second, LeaseRefusal)
    assert second.kind == "deps_manifest"
    assert second.holder_dispatch_id == "d1"
    assert DEPS_MANIFEST_KEY in second.message

    # After the first releases, the second is admitted.
    assert reg.release("d1") == 1
    retry = reg.grant_or_refuse("d2", ["src/pkg-b/**", "poetry.lock"])
    assert isinstance(retry, Lease)
    assert retry.deps_manifest is True


def test_AC_LEASE_2_non_deps_grant_not_blocked_by_held_deps(tmp_path):
    # A grant that does NOT touch the deps set is unaffected by a held
    # deps lease (the exclusivity is scoped to the deps set only).
    reg = LeaseRegistry(tmp_path / "leases.json")
    assert isinstance(reg.grant_or_refuse("d1", ["package.json"]), Lease)
    ok = reg.grant_or_refuse("d2", ["src/ui/**"])
    assert isinstance(ok, Lease)
    assert ok.deps_manifest is False
