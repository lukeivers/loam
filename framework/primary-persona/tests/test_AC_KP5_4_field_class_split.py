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

"""AC.KP5.4 — ``status`` is owner-gated-write; ``last-touched`` /
``cadence`` are soft-auto-write. The loader exposes the field-class
distinction (encodes Surface #3's PROPOSE-AND-SURFACE ruling at the
schema level)."""

from __future__ import annotations

from loam.primary_persona.keep_pace import objectives as obj


def test_AC_KP5_4_status_is_owner_gated() -> None:
    assert obj.field_class("status") == "owner-gated"
    assert "status" in obj.OWNER_GATED_FIELDS


def test_AC_KP5_4_bookkeeping_fields_are_soft_auto() -> None:
    assert obj.field_class("last-touched") == "soft-auto"
    assert obj.field_class("cadence") == "soft-auto"
    assert obj.SOFT_AUTO_FIELDS == {"last-touched", "cadence"}


def test_AC_KP5_4_other_fields_are_static() -> None:
    for f in ("objective", "completion", "detail-path", "slug", "subgoals"):
        assert obj.field_class(f) == "static"


def test_AC_KP5_4_status_and_bookkeeping_are_disjoint_classes() -> None:
    # The owner-gated and soft-auto classes must not overlap — a field
    # cannot be both auto-writable AND owner-gated.
    assert obj.OWNER_GATED_FIELDS.isdisjoint(obj.SOFT_AUTO_FIELDS)
