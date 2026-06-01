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

"""AC.ONFIRE.* — onboarding fires on a brand-new instance, idempotently (N3).
Covers: fires through a real entry-point (.1), idempotent / non-destructive on
re-run (.2), and the ★ OUTCOME-ALTITUDE cold-walk (.3 — a genuinely empty
instance run through the REAL entry-point ends with correctly-homed seeded
state, gate-9 GREEN, confidence:prior matrix, confirmed objective).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from loam.workspace_bootstrap.first_run_intake import run_first_run_intake

REPO_ROOT = Path(__file__).resolve().parents[4]
ALLOWLIST_REL = "docs/design/adr/user-state-homes.yaml"


class ScriptedAnswerer:
    def __init__(self, answers: dict[str, str]):
        self._answers = answers
        self.asked: list[str] = []

    def __call__(self, slug: str, prompt: str) -> str:
        self.asked.append(slug)
        return self._answers.get(slug, "")


def _empty_instance(tmp_path: Path):
    """A GENUINELY empty instance — no INTERACTION-MODEL.md, no objective, a
    fresh (non-existent) .loam, an isolated global home, no pre-arranged state."""
    home = tmp_path / "home" / ".claude"
    ws = tmp_path / "workspace"
    ws.mkdir(parents=True)
    assert not home.exists()
    assert not (ws / ".loam").exists()
    return home, ws


# ---- AC.ONFIRE.1 — fires through a real entry-point on first-run. ----


def test_AC_ONFIRE_1_real_entry_point_runs_the_full_flow(tmp_path: Path):
    home, ws = _empty_instance(tmp_path)
    result = run_first_run_intake(
        ws,
        answerer=ScriptedAnswerer(
            {"stop_start": "stop writing the standup notes by hand", "confirm_proposal": "yes"}
        ),
        global_home=home,
        run_capability_ritual=False,
    )
    # The full first-run flow ran: layout established + intake + seed.
    assert (ws / ".loam").is_dir()
    assert result.intake.confirmed is True
    assert result.seed is not None and result.seed.changed


# ---- AC.ONFIRE.2 — idempotent / non-destructive on re-run. ----


def test_AC_ONFIRE_2_rerun_does_not_clobber_existing_seed(tmp_path: Path):
    home, ws = _empty_instance(tmp_path)
    answers = {"stop_start": "stop doing the manual export", "confirm_proposal": "yes"}
    first = run_first_run_intake(
        ws, answerer=ScriptedAnswerer(answers), global_home=home, run_capability_ritual=False
    )
    obj_before = first.seed.objectives_path.read_text()
    im_before = first.seed.interaction_model_path.read_text()

    # A second run on the now-seeded instance: a DIFFERENT scripted answer must
    # NOT overwrite the prior seed (the protection floor).
    second = run_first_run_intake(
        ws,
        answerer=ScriptedAnswerer(
            {"stop_start": "stop something completely different", "confirm_proposal": "yes"}
        ),
        global_home=home,
        run_capability_ritual=False,
    )
    assert second.already_seeded is True
    assert (home / "OBJECTIVES.md").read_text() == obj_before
    assert (home / "INTERACTION-MODEL.md").read_text() == im_before


# ---- ★ AC.ONFIRE.3 — OUTCOME-ALTITUDE cold-walk (outcome-altitude: true). ----


def test_AC_ONFIRE_3_cold_walk_empty_instance_ends_with_homed_seed(tmp_path: Path):
    """outcome-altitude: true — drive the REAL production entry-point
    (run_first_run_intake) on a genuinely-empty instance with a scripted
    answer + confirm, and assert the FOUR post-conditions."""
    home, ws = _empty_instance(tmp_path)

    result = run_first_run_intake(
        ws,
        answerer=ScriptedAnswerer(
            {
                "stop_start": "stop manually triaging my support inbox each morning",
                "confirm_proposal": "yes",
            }
        ),
        global_home=home,
        run_capability_ritual=False,
    )

    # (a) seeded state present in the correct two homes.
    assert (home / "OBJECTIVES.md").exists()
    assert (home / "INTERACTION-MODEL.md").exists()
    assert (ws / ".loam").is_dir()

    # (c) the interaction-model at confidence: prior.
    im = (home / "INTERACTION-MODEL.md").read_text()
    assert "confidence: prior" in im
    assert "confidence: high" not in im

    # (d) the confirmed objective recorded (reflects the confirmed intent).
    obj = (home / "OBJECTIVES.md").read_text()
    assert "triaging" in obj
    assert "status: active" in obj

    # The demonstrate-leverage close fired with a person-specific idea.
    assert result.intake.has_leverage_idea
    assert any("triaging" in i.text for i in result.intake.leverage_ideas)

    # (b) gate 9 GREEN against the resulting tree — no framework-code write of
    # user-state landed outside the two homes (the static scan of framework/).
    from loam_cli.release.gates import check_boundary_respected

    gate = check_boundary_respected(REPO_ROOT, "n3-coldwalk", allowlist_rel=ALLOWLIST_REL)
    assert gate.ok, gate.message


def test_AC_ONFIRE_3_subcommand_entry_point_registered():
    """The real CLI verb is reachable through the registered entry-point (the
    init-intake subcommand the cold-walk's production path is exposed by)."""
    from loam.workspace_bootstrap.first_run_intake_cli import (
        build_init_intake_subcommand,
    )
    import argparse

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    build_init_intake_subcommand(sub)
    args = parser.parse_args(["init-intake", "/tmp/somewhere"])
    assert hasattr(args, "func")
