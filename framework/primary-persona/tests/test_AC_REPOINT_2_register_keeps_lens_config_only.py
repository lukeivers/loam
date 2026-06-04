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

"""AC.REPOINT.2 — after the re-point, the register carries ONLY
lens-presentation config (attention + nest-under); a stream's
project-binding and backlog are no longer a register-owned parallel
list. Re-pointing required NO rewrite of the register's attention/nest
config.

Plan §6 AC.REPOINT.2 (the shim dissolved, not duplicated). Method: the
field-class machinery already marks attention/nest as lens-config and
projects/backlog as the shim; the re-point makes the graph the
membership source while the register's attention/nest config stays
byte-identical (no rewrite).
"""

from __future__ import annotations

from loam.primary_persona.keep_pace import work_streams as ws


def test_AC_REPOINT_2_attention_and_nest_are_lens_config() -> None:
    # The lens-presentation config the register legitimately keeps.
    assert ws.shim_marker("attention") == "lens-config"
    assert ws.shim_marker("nest-under") == "lens-config"


def test_AC_REPOINT_2_projects_and_backlog_are_the_dissolved_shim() -> None:
    # The register-local membership lists are the pre-L1 shim; the
    # re-point resolves membership from the graph instead.
    assert ws.shim_marker("projects") == "pre-l1-shim"
    assert ws.shim_marker("backlog") == "pre-l1-shim"
    assert ws.SHIM_FIELDS == frozenset({"projects", "backlog"})


def test_AC_REPOINT_2_attention_remains_owner_gated_unchanged() -> None:
    # The owner-gated attention field-class is unchanged by the re-point.
    assert ws.field_class("attention") == "owner-gated"
    assert ws.OWNER_GATED_FIELDS == frozenset({"attention"})


def test_AC_REPOINT_2_repoint_needs_no_register_rewrite() -> None:
    """The graph-backed membership resolver reads work-item tags; it does
    NOT consult the register's projects/backlog and does NOT mutate the
    register. A round-trip of the seeded register's attention/nest config
    through render+load is byte-stable (no rewrite)."""
    streams = list(ws.SEEDED_WORK_STREAMS)
    rendered = ws.render_register(streams)
    reloaded = ws.load_streams(rendered)
    # attention + nest-under survive the round-trip unchanged.
    by_slug = {s.slug: s for s in reloaded}
    for original in streams:
        got = by_slug[original.slug]
        assert got.attention == original.attention
        assert got.nest_under == original.nest_under
