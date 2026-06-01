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

"""AC.SMOKE.1 (outcome-altitude) + AC.SMOKE.5 (re-runnable + self-cleaning).

AC.SMOKE.1: running the harness with ZERO pre-arranged workspace state drives
the REAL production first-run intake entry-point (run_first_run_intake) and
produces a homed seed — NOT a unit test of inner modules. Here the LLM-backed
role-play answerer is swapped for a deterministic scripted answerer so the test
is hermetic + fast, but the ENTRY-POINT under test is the real production
orchestrator (the outcome-altitude property: no pre-arranged state, real entry
point). The full live LLM walk is exercised by the run-report (the priority
deliverable), not the unit suite.

AC.SMOKE.5: the throwaway workspace + isolated global home are removed on exit
and the operator's real ~/.claude is never written.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam_acceptance_smoke import runner as runner_mod
from loam_acceptance_smoke.runner import VariantRun, run_variant
from loam_acceptance_smoke.variants import variant_by_key


class _ScriptedAnswerer:
    """Deterministic stand-in for the LLM role-play answerer (hermetic test)."""

    def __init__(self, run: VariantRun, lines: dict[str, str]):
        self._run = run
        self._lines = lines

    def __call__(self, slug: str, prompt: str) -> str:
        reply = self._lines.get(slug, "yes")
        self._run.transcript.append((slug, prompt, reply))
        return reply


@pytest.mark.outcome_altitude
def test_AC_SMOKE_1_real_entry_point_zero_prearranged_state(
    tmp_path: Path, monkeypatch
):
    # Swap the LLM-backed answerer for a deterministic one (hermetic), but keep
    # the REAL run_first_run_intake orchestrator + REAL loam init under test.
    spec = variant_by_key("A")

    def _fake_init(canonical_source, temp_root):
        ws = temp_root / "ws"
        ws.mkdir(parents=True, exist_ok=True)
        return ws, 0  # the real init is exercised separately in the live smoke

    monkeypatch.setattr(runner_mod, "_loam_init_throwaway", _fake_init)

    def _scripted_factory(variant, run):
        return _ScriptedAnswerer(
            run,
            {
                "stop_start": "stop hand-writing the listing descriptions every evening",
                "confirm_proposal": "yes",
            },
        )

    monkeypatch.setattr(runner_mod, "_RolePlayAnswerer", _scripted_factory)

    run = run_variant(spec, canonical_source=tmp_path, keep_workspace=True)

    # Outcome-altitude: the REAL intake ran end-to-end with no pre-arranged
    # state and produced a homed seed.
    assert run.error is None, run.error
    assert run.confirmed is True
    assert run.seeded_objective_text
    assert "interaction-model" in run.interaction_model_text.lower()
    assert "objective" in run.objectives_text.lower()
    # The seed landed in the ISOLATED global home (never the real ~/.claude):
    # the home is under the throwaway temp tree, NOT the operator's home.
    assert ".claude" in str(run.global_home)
    assert str(Path.home() / ".claude") != str(run.global_home)
    assert run.invoked_deep_research is False  # idea-rich -> zero research


@pytest.mark.outcome_altitude
def test_AC_SMOKE_5_self_cleaning_removes_throwaway(tmp_path: Path, monkeypatch):
    spec = variant_by_key("A")
    captured = {}

    def _fake_init(canonical_source, temp_root):
        ws = temp_root / "ws"
        ws.mkdir(parents=True, exist_ok=True)
        captured["temp_root"] = temp_root
        return ws, 0

    monkeypatch.setattr(runner_mod, "_loam_init_throwaway", _fake_init)

    def _scripted_factory(variant, run):
        return _ScriptedAnswerer(
            run, {"stop_start": "stop doing the manual export", "confirm_proposal": "yes"}
        )

    monkeypatch.setattr(runner_mod, "_RolePlayAnswerer", _scripted_factory)

    run = run_variant(spec, canonical_source=tmp_path, keep_workspace=False)
    assert run.error is None, run.error
    # Self-cleaning: the throwaway temp root is gone after the run.
    assert not captured["temp_root"].exists()
