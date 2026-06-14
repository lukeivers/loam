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

"""AC.CLP-PUSH-RENDER.6 — the render reuses Slice-1's cadence binding; no
second scheduler (D-PUSH.4).

The component ships an integration STEP (scripts/run-cadence-step.sh +
cadence/INTEGRATION.md) that rides Slice-1's existing binding. It
introduces NO scheduler of its own: no launchd plist, no cron, no
``/schedule`` routine-spec that creates a new routine. The integration
doc points at the EXISTING Slice-1 binding by path.
"""

from __future__ import annotations

from pathlib import Path

COMPONENT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]


def test_AC_CLP_PUSH_RENDER_6_no_second_scheduler_primitive():
    """The component introduces no launchd plist + no cron of its own."""
    plists = list(COMPONENT.rglob("*.plist"))
    assert not plists, f"knowledge-pack must own no launchd agent; found {plists}"
    # No crontab/cron file shipped.
    crons = [p for p in COMPONENT.rglob("*") if p.is_file() and "crontab" in p.name.lower()]
    assert not crons, f"knowledge-pack must own no cron; found {crons}"


def test_AC_CLP_PUSH_RENDER_6_integration_step_present():
    """The cadence STEP + integration doc exist and ride the existing
    binding."""
    step = COMPONENT / "scripts" / "run-cadence-step.sh"
    integ = COMPONENT / "cadence" / "INTEGRATION.md"
    assert step.is_file()
    assert integ.is_file()
    integ_text = integ.read_text(encoding="utf-8")
    # The doc names Slice-1's existing binding by path (reuse, not a new one).
    assert "framework/tools/capability-refresh/cadence" in integ_text
    # The doc explicitly states no second scheduler.
    assert "no second scheduler" in integ_text.lower()


def test_AC_CLP_PUSH_RENDER_6_step_renders_no_public_action():
    """The cadence step script renders + does NOT publish/push (the pack
    stages in-repo; publish is S4c ⛔OWNER)."""
    step_text = (COMPONENT / "scripts" / "run-cadence-step.sh").read_text(encoding="utf-8")
    assert "knowledge_pack render" in step_text
    # No push in the step (the pack stages in-repo; publish is S4c ⛔OWNER).
    assert "git push" not in step_text
    # The step renders only — it invokes no publish subcommand.
    assert "knowledge_pack publish" not in step_text
    # The step does not record a gate pass (curator does that).
    assert "--gate-pass" not in step_text
