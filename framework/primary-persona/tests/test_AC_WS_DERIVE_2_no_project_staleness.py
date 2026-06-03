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

"""AC.WS.DERIVE.2 — a stream bound to NO registered project (e.g. Money)
surfaces a next-action from its detail-path / cadence staleness AND is
explicitly marked "no ground-truth project bound"; it NEVER fabricates a
derived build-STATE (D3's honest gap)."""

from __future__ import annotations

from loam.primary_persona.keep_pace import work_streams as ws
from loam.primary_persona.keep_pace import work_streams_surface as wss


def test_AC_WS_DERIVE_2_unbound_stream_marked_no_ground_truth() -> None:
    stream = ws.WorkStream(
        slug="money", attention="active", objective="o", detail_path="d",
        projects=[], cadence="weekly", last_touched="2026-05-28",
    )

    def derive(name):  # would be a real STATE for a bound stream
        raise AssertionError("derive must NOT be called for an unbound stream")

    line = wss.render_stream_line(stream, derive=derive)
    assert "no ground-truth project bound" in line, (
        "an unbound stream must be explicitly marked — never a faked STATE"
    )
    assert "money" in line


def test_AC_WS_DERIVE_2_unbound_line_carries_staleness_anchor() -> None:
    stream = ws.WorkStream(
        slug="personal-home", attention="active", objective="o",
        detail_path="d", projects=[], cadence="weekly",
        last_touched="2026-05-20",
    )
    line = wss.render_stream_line(stream, derive=lambda n: None)
    # The next-action anchor is the cadence / last-touched staleness.
    assert "cadence weekly" in line
    assert "last touched 2026-05-20" in line


def test_AC_WS_DERIVE_2_never_fabricates_build_state() -> None:
    # An unbound stream's line must NOT carry build-status vocabulary
    # (merged/sealed/built) — that would be a faked derived STATE.
    stream = ws.WorkStream(
        slug="money", attention="active", objective="o", detail_path="d",
        projects=[], cadence="weekly", last_touched="2026-05-28",
    )
    line = wss.render_stream_line(stream, derive=lambda n: None).lower()
    assert "merged" not in line
    assert "sealed" not in line
    assert "built (" not in line
