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

"""AC.WS.SHIM.1 (★ WMS-D7) — the register is the streams lens-definition +
attention config, but its project-bindings / backlog are marked the
PRE-L1 SHIM, explicitly re-pointable at the L1 work graph in Increment 2
WITHOUT a register rewrite. The attention / nest-under fields are
lens-config (describe the VIEW, stay); projects / backlog are shim. This
is the one adjustment the work-management-system architecture (§8 /
WMS-D7) names so the foundation is not boxed-in."""

from __future__ import annotations

from loam.primary_persona.keep_pace import work_streams as ws


def test_AC_WS_SHIM_1_projects_and_backlog_are_pre_l1_shim() -> None:
    assert ws.shim_marker("projects") == "pre-l1-shim"
    assert ws.shim_marker("backlog") == "pre-l1-shim"


def test_AC_WS_SHIM_1_attention_and_nest_are_lens_config_not_shim() -> None:
    # attention + nest-under describe the VIEW and STAY (not shim) — WMS-D7.
    assert ws.shim_marker("attention") == "lens-config"
    assert ws.shim_marker("nest-under") == "lens-config"
    assert ws.shim_marker("objective") == "lens-config"


def test_AC_WS_SHIM_1_register_header_marks_the_shim_repointable() -> None:
    # The register header documents the shim + its re-pointability at the
    # L1 work graph in Increment 2 without a register rewrite.
    text = ws.render_register(ws.SEEDED_WORK_STREAMS)
    low = text.lower()
    assert "shim" in low
    assert "re-pointable" in low or "re-point" in low
    assert "increment 2" in low
    assert "work graph" in low or "work-item" in low or "l1" in low


def test_AC_WS_SHIM_1_repoint_binding_without_register_rewrite() -> None:
    # The re-pointability proof: a stream's project binding can be swapped
    # to a work-graph-tag resolver WITHOUT rewriting the register schema —
    # the surfacer reads `projects` through a binding the Increment-2 graph
    # can supply. Here we prove the binding is a plain list the loader
    # round-trips, so Increment 2 can re-point it (a tag query) without a
    # schema change. The register source text is identical before/after a
    # re-point of WHERE the projects come from.
    stream = ws.WorkStream(slug="loam", attention="active", objective="o",
                           detail_path="d", projects=["loam"])
    rendered = ws.render_register([stream])
    reloaded = ws.load_streams(rendered)[0]
    # The binding survives a round-trip as a re-pointable list (Increment 2
    # supplies the same list from a work-graph tag query — no rewrite).
    assert reloaded.projects == ["loam"]
    # And the loader does not bake the binding into an immutable schema
    # field: it is a plain mutable list a re-point can replace.
    reloaded.projects = ["loam", "cairn"]  # an Increment-2 re-point
    assert reloaded.projects == ["loam", "cairn"]
