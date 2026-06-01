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

"""AC.INTENT.5 — the LLM extractor is the PRODUCTION default, fail-soft retained.

The real ``ClaudeIntentExtractor`` is the default the PRODUCTION orchestrator
resolves (replacing the built-but-off ``DisabledIntentExtractor`` as the
production reader), so the four-step loop is LIVE in production, not only when a
consumer registers it. The fail-soft regex fallback is RETAINED: a forced
extractor failure still completes the intake via the regex distillation, so
onboarding never breaks.

The LIBRARY seam default stays disabled/pure-regex — that's asserted by
AC.INTENT.2 and is a DIFFERENT default (the featherlight library boundary); this
AC pins the PRODUCTION front-door default.
"""

from __future__ import annotations

from pathlib import Path

from loam.workspace_bootstrap.first_run_intake import (
    production_intent_extractor,
    run_first_run_intake,
)
from loam.workspace_bootstrap.intent_extract import (
    ClaudeIntentExtractor,
    IntentExtractUnavailableError,
)


class ScriptedAnswerer:
    def __init__(self, answers: dict[str, str]):
        self._answers = answers

    def __call__(self, slug: str, prompt: str) -> str:
        return self._answers.get(slug, "")


def _empty_instance(tmp_path: Path):
    home = tmp_path / "home" / ".claude"
    ws = tmp_path / "workspace"
    ws.mkdir(parents=True)
    return home, ws


def test_AC_INTENT_5_production_default_is_the_real_claude_extractor():
    """The PRODUCTION default extractor is the real ClaudeIntentExtractor (the LLM
    seam is LIVE in production by default), not the disabled baseline."""
    extractor = production_intent_extractor()
    assert isinstance(extractor, ClaudeIntentExtractor)


def test_AC_INTENT_5_orchestrator_uses_production_default_when_none_injected(
    monkeypatch, tmp_path: Path
):
    """With NO extractor injected, the orchestrator resolves the PRODUCTION default
    (the real extractor) — proven by recording which extractor the intake saw."""
    seen = {}

    import loam.workspace_bootstrap.first_run_intake as fri

    real = fri.production_intent_extractor()

    def _record():
        seen["extractor"] = real
        return real

    monkeypatch.setattr(fri, "production_intent_extractor", _record)
    home, ws = _empty_instance(tmp_path)
    run_first_run_intake(
        ws,
        answerer=ScriptedAnswerer(
            {"stop_start": "stop writing the standup notes by hand", "confirm_proposal": "yes"}
        ),
        global_home=home,
        run_capability_ritual=False,
    )
    assert isinstance(seen.get("extractor"), ClaudeIntentExtractor)


def test_AC_INTENT_5_failsoft_completes_via_regex_when_production_call_fails(
    monkeypatch, tmp_path: Path
):
    """FAIL-SOFT retained: when the production extractor's bounded call FAILS, the
    intake still completes — the close lands on the regex distillation, onboarding
    never breaks."""

    class AlwaysFailingClaudeExtractor(ClaudeIntentExtractor):
        def extract(self, raw_reply: str, *, prior_proposal: str = ""):
            raise IntentExtractUnavailableError("forced failure (no live spawn)")

        def extract_adjustment(self, confirm_reply: str, *, item: str, proposal: str = ""):
            raise IntentExtractUnavailableError("forced failure (no live spawn)")

    import loam.workspace_bootstrap.first_run_intake as fri

    monkeypatch.setattr(
        fri, "production_intent_extractor", lambda: AlwaysFailingClaudeExtractor()
    )
    home, ws = _empty_instance(tmp_path)
    result = run_first_run_intake(
        ws,
        answerer=ScriptedAnswerer(
            {
                "stop_start": "stop writing listing descriptions for properties by hand",
                "confirm_proposal": "yes",
            }
        ),
        global_home=home,
        run_capability_ritual=False,
    )
    # The intake completed despite the extractor failing — the regex fallback ran.
    assert result.intake.confirmed is True
    assert result.intake.has_leverage_idea
    assert any(
        "listing descriptions" in i.text for i in result.intake.leverage_ideas
    )
