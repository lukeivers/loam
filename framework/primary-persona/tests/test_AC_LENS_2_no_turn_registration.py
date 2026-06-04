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

"""AC.LENS.2 — no new always-on per-turn block (D-WMS5.4 no-bloat).

Plan §6 AC.LENS.2. Outcome: none of the three lenses is registered as a
``TriggerKind.turn`` contributor — the per-turn surface gains ZERO new
always-on blocks. Verifiable: the three lenses expose on-demand
``render_*_block`` entry points only (no ``register_*_contributor`` /
``build_*_contributor``), and the session-start emitter registers no new
lens contributor.
"""

from __future__ import annotations

import inspect

from loam.primary_persona import session_start_emitter
from loam.primary_persona.keep_pace import goals, plate, waiting_on


def test_AC_LENS_2_on_demand_entry_points_exist() -> None:
    # Each lens exposes its on-demand render entry point.
    assert callable(goals.render_goals_block)
    assert callable(plate.render_plate_block)
    assert callable(waiting_on.render_waiting_on_block)


def test_AC_LENS_2_no_lens_exposes_a_turn_contributor() -> None:
    # None of the three lenses exposes a turn-contributor registrar or
    # builder — they are on-demand only (no always-on per-turn seat).
    for mod in (goals, plate, waiting_on):
        names = set(dir(mod))
        offenders = {
            n
            for n in names
            if n.startswith("register_") or n.startswith("build_")
            and n.endswith("_contributor")
        }
        # No register_*/build_* contributor surface at all.
        assert not any(
            n.startswith("register_") or n.endswith("_contributor")
            for n in names
        ), (
            f"{mod.__name__} must NOT expose a turn-contributor surface "
            f"(on-demand only — AC.LENS.2); found {offenders or names}"
        )


def test_AC_LENS_2_emitter_registers_no_new_lens_contributor() -> None:
    # The session-start emitter registers exactly the inc-4 set of lens
    # turn-contributors (streams / projects / relational + retrieval) — it
    # does NOT register goals / plate / waiting-on as turn contributors.
    src = inspect.getsource(session_start_emitter)
    assert "register_goals_contributor" not in src
    assert "register_plate_contributor" not in src
    assert "register_waiting_on_contributor" not in src
    # And the on-demand render entry points are not wired as turn blocks.
    assert "register_relational_contributor" in src, (
        "the inc-4 relational turn registration must remain (unchanged)"
    )
