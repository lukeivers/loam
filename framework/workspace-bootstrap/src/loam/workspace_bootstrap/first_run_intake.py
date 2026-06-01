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

"""N3 first-run intake ORCHESTRATOR — the real production entry-point the
``loam init-intake`` verb drives (slice N3 / AC.ONFIRE.*).

This is the D-4 (a) orchestration (RATIFIED): the single front door that runs
the four first-run phases for a brand-new instance:

  1. scaffold        — ``establish_loam_layout`` (composed; exists, P1.2)
  2. capability-ritual — the existing ``run_onboarding`` six-question ritual
                       (COMPOSED, not extended — §10.1: it activates
                       capabilities; it does NOT infer end-intent). Optional /
                       best-effort: a capability-ritual failure must not abort
                       the intake (the intake is the load-bearing N3 phase).
  3. translate-in intake — the NEW operating-loop intake (infer -> propose ->
                       verify -> learn) that leads the user to ONE stop/start
                       thing + ends on a person-specific leverage idea.
  4. seed            — the NEW seed-writer: the D-2 minimum prior into the two
                       homes (objective + openness-biased AIM matrix), gate-9
                       clean, idempotent / non-destructive.

**The `loam init` name-collision (resolved — see plan §11).** ``loam init``
already exists as a separate sealed component (``framework/loam-init/``) that
bootstraps a fresh workspace TREE + fires the capability ritual. To keep this
build single-component (the plan's §2 home = ``workspace-bootstrap``) and avoid
editing the sealed ``loam-init/``, this orchestrator is exposed as the
NON-colliding verb ``loam init-intake``. The outcome-altitude AC (AC.ONFIRE.3)
drives ``run_first_run_intake`` — a REAL production entry-point — on an empty
instance. Folding it into the literal ``loam init`` verb is a one-line callout
amend to the sealed ``loam-init/`` (a clean fast-follow, surfaced in §11).

**Idempotent / non-destructive (AC.ONFIRE.2 — the protection floor).** A re-run
on an already-seeded instance leaves the prior seed intact (the seed-writer's
additive/never-clobber guarantee). The orchestrator detects an already-seeded
home and can short-circuit the intake (the seed exists; re-running is a no-op
on the seeded files).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .deep_role_research import ResearchProvider
from .intent_extract import ClaudeIntentExtractor, IntentExtractor
from .seed_writer import SeedResult, default_global_home, seed_user_state
from .translate_in_intake import Answerer, IntakeResult, run_translate_in_intake


def production_intent_extractor() -> IntentExtractor:
    """The PRODUCTION-default intent extractor (AC.INTENT.5).

    The library seam default (``translate_in_intake.default_intent_extractor`` ->
    ``DisabledIntentExtractor``) stays pure-regex so the baseline distillation suite
    is byte-identical and the featherlight path takes no spawn. The PRODUCTION
    front door — ``loam init-intake`` (and the acceptance smoke, which drives the
    same orchestrator) — activates the REAL ``ClaudeIntentExtractor`` so the
    four-step loop is LIVE in production, not only when a consumer registers it.
    Fail-soft is unchanged: ``run_translate_in_intake`` still catches
    ``IntentExtractUnavailableError`` and degrades to the regex distillation, so
    onboarding NEVER breaks if the bounded ``claude -p`` call fails
    (``feedback_no_anthropic_api_key`` — subscription-only, no SDK)."""
    return ClaudeIntentExtractor()


@dataclass
class FirstRunIntakeResult:
    """Terminal state of a ``loam init-intake`` run (AC.ONFIRE.*).

    Carries the intake outcome + the seed outcome so a test (and the CLI) can
    assert the four cold-walk post-conditions: homed seed / gate-9 GREEN /
    ``confidence: prior`` matrix / confirmed objective recorded.
    """

    workspace_root: Path
    global_home: Path
    intake: IntakeResult
    seed: SeedResult | None = None
    capability_ritual_ran: bool = False
    capability_ritual_error: str | None = None
    already_seeded: bool = False

    @property
    def seeded(self) -> bool:
        return self.seed is not None and self.seed.changed or self.already_seeded


def _is_already_seeded(global_home: Path) -> bool:
    """A home with BOTH seed files present is already onboarded (AC.ONFIRE.2)."""
    return (
        (global_home / "OBJECTIVES.md").exists()
        and (global_home / "INTERACTION-MODEL.md").exists()
    )


def run_first_run_intake(
    workspace_root: Path,
    *,
    answerer: Answerer,
    global_home: Path | None = None,
    research_provider: ResearchProvider | None = None,
    intent_extractor: IntentExtractor | None = None,
    run_capability_ritual: bool = True,
    capability_answerer: Any | None = None,
) -> FirstRunIntakeResult:
    """Orchestrate the four first-run phases; return the seeded outcome.

    Arguments:
        workspace_root: the workspace whose ``.loam/`` is composed.
        answerer: the intake answerer (scripted in tests; stdin in production).
        global_home: the ``~/.claude`` home (default: real home). Tests pass an
            isolated fixture dir so the cold-walk never touches the real home.
        research_provider: the deep-role-research provider (default: the
            featherlight stub — the baseline degrades gracefully, AC.ONDEEP.1).
        intent_extractor: the LLM intent-extraction seam (default: the disabled
            extractor — the baseline distillation stays pure-regex, AC.INTENT.2;
            the smoke / production CLI register the real ClaudeIntentExtractor).
        run_capability_ritual: when True (default), compose the existing
            capability-activation ritual (phase 2). Best-effort — its failure
            does NOT abort the intake.
        capability_answerer: optional answerer for the capability ritual (tests
            may pin a no-op; production uses the stdin answerer).

    Returns a :class:`FirstRunIntakeResult`.
    """
    from .translate_in_intake import IdeaRichness

    home = global_home if global_home is not None else default_global_home()
    workspace_root = Path(workspace_root)

    # --- AC.ONFIRE.2: idempotent / non-destructive short-circuit. ---
    if _is_already_seeded(home):
        # An already-onboarded instance has its seed; re-running must not
        # clobber it. Surface the prior state + stop (the protection floor).
        # The intake conversation is NOT re-run.
        return FirstRunIntakeResult(
            workspace_root=workspace_root,
            global_home=home,
            intake=IntakeResult(richness=IdeaRichness.CLEAR),
            already_seeded=True,
        )

    result = FirstRunIntakeResult(
        workspace_root=workspace_root,
        global_home=home,
        intake=IntakeResult(richness=IdeaRichness.EMPTY),
    )

    # --- Phase 1: scaffold (composed; idempotent). ---
    from .loam_layout import establish_loam_layout

    establish_loam_layout(workspace_root)

    # --- Phase 2: capability-activation ritual (COMPOSED, best-effort). ---
    if run_capability_ritual:
        try:
            from .onboarding import run_onboarding

            if capability_answerer is not None:
                run_onboarding(workspace_root, answerer=capability_answerer)
                result.capability_ritual_ran = True
        except Exception as exc:  # noqa: BLE001 — ritual is value-add, not load-bearing
            result.capability_ritual_error = str(exc)

    # --- Phase 3: the translate-in intake (the load-bearing N3 phase). ---
    # AC.INTENT.5: production activates the REAL extractor by default (the library
    # seam stays disabled/pure-regex). An explicit injection (tests) still wins.
    # Fail-soft is retained — the intake degrades to the regex distillation on any
    # extractor failure, so onboarding never breaks.
    effective_extractor = (
        intent_extractor
        if intent_extractor is not None
        else production_intent_extractor()
    )
    intake = run_translate_in_intake(
        answerer=answerer,
        research_provider=research_provider,
        intent_extractor=effective_extractor,
    )
    result.intake = intake

    # --- Phase 4: seed the D-2 minimum prior (ONLY on a confirmed intent). ---
    # The seed is gated on the verify-gate (AC.ONINTAKE.3): no confirmed
    # end-intent -> nothing is seeded as the objective (but the AIM matrix +
    # layout still seed, so the next session has the openness-biased prior).
    if intake.confirmed and intake.seeded_objective_text:
        result.seed = seed_user_state(
            objective_slug=intake.seeded_objective_slug or "first-objective",
            objective_text=intake.seeded_objective_text,
            workspace_root=workspace_root,
            global_home=home,
        )
    else:
        # No confirmed objective — still seed the openness-biased AIM matrix +
        # layout so the instance has its prior (the objective lands later).
        result.seed = seed_user_state(
            objective_slug="getting-started",
            objective_text=(
                "Getting started — the user has not yet named a confirmed "
                "end-intent; loam keeps learning from evidence (N4)."
            ),
            workspace_root=workspace_root,
            global_home=home,
        )

    return result
