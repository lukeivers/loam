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

"""Onboarding ritual orchestrator.

Per v0.2.1 Cycle 1 plan-doc §3 + master plan §3 Cycle 1: hosts the
six-question one-at-a-time install-time ritual that polishes the
first 5–10 minutes of Eric's install. Composes on:

  - :mod:`loam.workspace_bootstrap.language_detection` (AC.ONBOARD.2)
  - :mod:`loam.workspace_bootstrap.survey_parser` (AC.ONBOARD.15)
  - :mod:`loam.workspace_bootstrap.onboarding_audit` (AC.ONBOARD.11)
  - :mod:`loam.workspace_bootstrap.onboarding_activations` (.4/.6/.7)
  - :mod:`loam.workspace_bootstrap.manifest` (write_onboarding_fields)
  - :mod:`framework.per_project_pm.PMRuntime` (read-only consumer of
    ``enqueue_decision`` + ``surface_next_questions_batch(n=1)`` +
    ``record_response``) per AC.ONBOARD.3 + Decision Q.

The orchestrator is sync. The CLI driver (``onboarding_cli.py``)
uses stdin for the user's answers; tests inject a pre-scripted
:class:`Answerer` to drive the loop deterministically.

LOAM_ONBOARDING_SKIP=1 short-circuits the ritual entirely (returns
immediately with no audit-log entries) per AC.ONBOARD.1.
"""

from __future__ import annotations

import datetime as _dt
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from .language_detection import (
    LanguageDetection,
    detect_language,
)
from .manifest import write_onboarding_fields
from .onboarding_activations import (
    ActivationResult,
    activate_channel_telegram,
    activate_extractor,
    activate_watch_pointer,
)
from .onboarding_audit import (
    audit_log_path,
    emit_audit_entry,
)
from .survey_parser import (
    SurveyDefaults,
    parse_survey_file,
    resolve_survey_path,
)


SKIP_ENV_VAR = "LOAM_ONBOARDING_SKIP"


# AC.ONBOARD.1 — six install-time question slugs in order.
QUESTION_SLUGS: tuple[str, ...] = (
    "language",
    "channel",
    "safety_profile",
    "extractor",
    "watch",
    "auto_skill_capture",
)


class Answerer(Protocol):
    """Callable that asks the user one question and returns the answer.

    Tests inject a pre-scripted instance; the CLI implements via
    stdin. The ritual calls ``answerer(slug, prompt)`` once per
    question; the response is the raw user input (string).
    """

    def __call__(self, slug: str, prompt: str) -> str:  # pragma: no cover
        ...


@dataclass
class OnboardingResult:
    """Terminal state of a completed onboarding ritual.

    Used by the CLI to render the completion summary + by integration
    tests to assert end-to-end behaviour.
    """

    workspace_root: Path
    language_detection: LanguageDetection
    answers: dict[str, str] = field(default_factory=dict)
    activations: list[ActivationResult] = field(default_factory=list)
    completion_summary_path: Path | None = None
    audit_log_path: Path | None = None
    completed_at: str | None = None
    skipped: bool = False
    survey_defaults: SurveyDefaults | None = None
    production_stake_force_flip: bool = False


def run_onboarding(
    workspace_root: Path,
    *,
    answerer: Answerer,
    pm_runtime: Any | None = None,
    survey_path: Path | None = None,
    extractor_cmd: list[str] | None = None,
    today: str | None = None,
) -> OnboardingResult:
    """Run the six-question onboarding ritual end-to-end.

    Per AC.ONBOARD.1 / .2 / .3 / .9 / .10 / .11 / .15.

    Arguments:
        workspace_root: Path to the freshly-bootstrapped workspace
            (the root that contains ``bootstrap.yaml``).
        answerer: Callable used to ask the user each question.
        pm_runtime: Optional :class:`PMRuntime` for one-at-a-time
            question sequencing per AC.ONBOARD.3. When None, the
            ritual still asks one-at-a-time via ``answerer`` (the PM
            integration is structural for production; tests may omit
            it). Per Decision Q the production CLI always passes a
            real PMRuntime.
        survey_path: Optional override for the survey-file path
            (tests pin this; production reads via env-var +
            conventional path per :func:`resolve_survey_path`).
        extractor_cmd: Optional override for the extractor subprocess
            command (tests inject a no-op; production uses the
            default ``loam odd-extract <root>``).
        today: Optional date override for audit-log filename
            (tests pin determinism; production uses real UTC date).

    Returns:
        :class:`OnboardingResult` carrying the answers + activations
        + audit-log path + completion-summary path.
    """
    if os.environ.get(SKIP_ENV_VAR) == "1":
        # AC.ONBOARD.1 SKIP path — return immediately; no audit-log.
        return OnboardingResult(
            workspace_root=workspace_root,
            language_detection=LanguageDetection(
                primary="unknown", signals=()
            ),
            skipped=True,
        )

    # AC.ONBOARD.11 — emit the start entry.
    emit_audit_entry(
        workspace_root,
        event_kind="onboarding_started",
        notes=f"workspace_root={workspace_root!s}",
        today=today,
    )

    # AC.ONBOARD.2 — auto-detect.
    detection = detect_language(workspace_root)

    # AC.ONBOARD.15 — survey-as-default-source. Resolve path: explicit
    # override > env-var > conventional default. None when no survey
    # is present (fresh workspace; ritual asks fresh).
    survey: SurveyDefaults | None = None
    resolved_path = survey_path or resolve_survey_path()
    if resolved_path is not None:
        survey = parse_survey_file(resolved_path)

    answers: dict[str, str] = {}
    activations: list[ActivationResult] = []
    production_stake_force_flip = False

    for slug in QUESTION_SLUGS:
        prompt = _compose_prompt(slug, detection, survey, answers)
        # AC.ONBOARD.3 — enqueue + surface via PM batch API n=1 when
        # PM is wired. Best-effort: PMRuntime mocks in tests record the
        # call; production verifies against the real PM.
        if pm_runtime is not None:
            try:
                pm_runtime.enqueue_decision(
                    prompt, provenance=f"onboarding:Q{slug}"
                )
                pm_runtime.surface_next_questions_batch(n=1)
            except Exception:  # noqa: BLE001 — PM mock errors are OK
                pass
        emit_audit_entry(
            workspace_root,
            event_kind="onboarding_question_asked",
            notes=f"slug={slug}",
            today=today,
        )

        raw = answerer(slug, prompt)
        normalised = _normalise_answer(slug, raw, detection)
        answers[slug] = normalised
        emit_audit_entry(
            workspace_root,
            event_kind="onboarding_response_recorded",
            notes=f"slug={slug} answer={normalised}",
            today=today,
        )

        # AC.ONBOARD.10 — production-stake force-flip on
        # auto-skill-capture (fires before activation dispatch so the
        # activation-side Y → forced-False is logged).
        if (
            slug == "auto_skill_capture"
            and answers.get("safety_profile") == "production-stake"
            and normalised == "yes"
        ):
            answers["auto_skill_capture"] = "no"
            production_stake_force_flip = True
            emit_audit_entry(
                workspace_root,
                event_kind="onboarding_default_flip",
                notes=(
                    "production-stake mode forced auto-skill-capture to no "
                    "(SOC-2 floor); user-submitted answer was yes"
                ),
                today=today,
            )

        # Per-question activation dispatch. Channel-telegram fires on
        # Q2 yes; extractor on Q4 yes; watch on Q5 yes.
        result = _dispatch_activation(
            slug, normalised, workspace_root, detection,
            extractor_cmd=extractor_cmd,
        )
        if result is not None:
            activations.append(result)
            emit_audit_entry(
                workspace_root,
                event_kind="onboarding_capability_activated",
                notes=f"kind={result.kind} status={result.status}",
                artefact_path=result.artefact_path,
                today=today,
            )

    # AC.ONBOARD.5 + .8 — write the manifest fields. `safety_profile`
    # + `enable_auto_skill_capture` use existing v0.1.6 / v0.2.0
    # fields; channel/extractor/watch/language use the new v0.2.1
    # fields.
    completed_at = _dt.datetime.now(_dt.timezone.utc).isoformat()
    bootstrap_yaml = workspace_root / "bootstrap.yaml"
    if bootstrap_yaml.exists():
        # v0.7.0 AC.NTU.2 (a) — derive primary_channel from the same Q2
        # answer (per D-NTU.2.b default: extend existing question to
        # cover primary_channel semantics). Telegram → telegram;
        # cli/anything else explicit → terminal; deferred → None
        # (caller defaults to terminal at runtime, preserving current
        # behavior).
        primary_channel = _channel_to_primary_channel(answers["channel"])
        write_onboarding_fields(
            bootstrap_yaml,
            safety_profile=answers["safety_profile"],
            enable_auto_skill_capture=(
                answers["auto_skill_capture"] == "yes"
            ),
            channel_preference=_channel_to_field(answers["channel"]),
            extractor_opt_in=answers["extractor"],
            watch_opt_in=answers["watch"],
            language_primary=answers["language"],
            onboarding_completed_at=completed_at,
            primary_channel=primary_channel,
        )

    # AC.ONBOARD.9 — completion summary.
    summary_path = _write_completion_summary(
        workspace_root,
        answers=answers,
        activations=activations,
        audit_path=audit_log_path(workspace_root, today=today),
        production_stake_force_flip=production_stake_force_flip,
    )

    emit_audit_entry(
        workspace_root,
        event_kind="onboarding_completed",
        notes=(
            f"summary_path={summary_path!s} "
            f"production_stake_force_flip={production_stake_force_flip}"
        ),
        artefact_path=str(summary_path),
        today=today,
    )

    return OnboardingResult(
        workspace_root=workspace_root,
        language_detection=detection,
        answers=answers,
        activations=activations,
        completion_summary_path=summary_path,
        audit_log_path=audit_log_path(workspace_root, today=today),
        completed_at=completed_at,
        survey_defaults=survey,
        production_stake_force_flip=production_stake_force_flip,
    )


# ---- prompt composition + answer normalisation -----------------------


def _compose_prompt(
    slug: str,
    detection: LanguageDetection,
    survey: SurveyDefaults | None,
    prior_answers: dict[str, str],
) -> str:
    """Build the user-facing question text for ``slug``.

    AC.ONBOARD.2 / .4 / .5 / .6 / .7 / .8 / .15 — each slug has its
    own prompt shape; survey pre-fill switches to confirm-or-adjust
    when a default is available.
    """
    survey_default = _survey_default_for(slug, survey)
    if slug == "language":
        if survey_default:
            return (
                f"Q1: From your survey: {survey_default}. "
                f"Confirm? (1) Yes (2) Adjust to: <free-form>"
            )
        primary = detection.primary
        if primary == "rails":
            return "Q1: I detected this is rails. Continue? (1) Yes (2) No, it's: <free-form>"
        if primary == "ruby":
            return "Q1: I detected this is ruby. Continue? (1) Yes (2) No, it's: <free-form>"
        if primary == "ts":
            return "Q1: I detected this is ts. Continue? (1) Yes (2) No, it's: <free-form>"
        if primary == "js":
            return "Q1: I detected this is js. Continue? (1) Yes (2) No, it's: <free-form>"
        if primary == "mixed":
            return (
                "Q1: I detected both Ruby and JS/TS. Which is primary? "
                "(1) Ruby (2) JS/TS (3) other"
            )
        return "Q1: I couldn't auto-detect. What language is this? (free-form)"
    if slug == "channel":
        if survey_default:
            return (
                f"Q2: From your survey: {survey_default}. Confirm? "
                f"(1) Yes (2) Adjust"
            )
        return (
            "Q2: Where do you want async pings when work completes? "
            "(1) Telegram (2) CLI-only (3) Skip for now"
        )
    if slug == "safety_profile":
        # AC.ONBOARD.5 — default-highlight production-stake when language=rails.
        rails = (
            detection.primary == "rails"
            or prior_answers.get("language") == "rails"
        )
        if survey_default:
            return (
                f"Q3: From your survey: {survey_default}. Confirm? "
                f"(1) Yes (2) Adjust"
            )
        if rails:
            return (
                "Q3: Safety profile? (1) production-stake [recommended for "
                "Rails apps] (2) dev (3) research"
            )
        return "Q3: Safety profile? (1) production-stake (2) dev (3) research"
    if slug == "extractor":
        if survey_default:
            return (
                f"Q4: From your survey: {survey_default}. Confirm? "
                f"(1) Yes (2) Adjust"
            )
        # v0.7.0 AC.NTU.6 — vocabulary scrub: "ODD extractor" was
        # substrate-name leaking into the user-facing Q4 question text.
        # The user-facing concept is "scan this codebase for design
        # patterns" — a code-pattern scanner. Substrate command name
        # `loam odd-extract` is preserved for the dev-mode CLI surface
        # (operators know what it does); the user-facing question
        # avoids the substrate term. Deeper F-DESIGN (Q4 should be
        # conditional on dev-intent detection — non-tech-user
        # workspaces shouldn't surface this question at all) deferred
        # to a follow-on amendment per the v0.7.0 build report.
        return (
            "Q4: Scan this codebase for design patterns now? "
            "(the scanner reads your source files + drafts a design "
            "summary; useful for software-development workspaces) "
            "(1) Yes — scan now (2) Defer — I'll run the scan later "
            "(3) Never — disable the scanner for this workspace"
        )
    if slug == "watch":
        if survey_default:
            return (
                f"Q5: From your survey: {survey_default}. Confirm? "
                f"(1) Yes (2) Adjust"
            )
        # AC.ONBOARD.7 — Defer is the default for fresh-user low-context.
        return (
            "Q5: Enable continuous codebase-watch (auto re-extract when "
            "commits land)? (1) Yes (2) Defer [default] (3) No"
        )
    if slug == "auto_skill_capture":
        if survey_default:
            return (
                f"Q6: From your survey: {survey_default}. Confirm? "
                f"(1) Yes (2) Adjust"
            )
        # AC.ONBOARD.8 — N is the default per layered-skills §3.6 Decision E.
        return (
            "Q6: Enable auto-skill-capture (persona drafts SKILL.md when "
            "patterns repeat; you ratify each)? (1) Yes (2) No [default]"
        )
    return f"Question for slug={slug}"  # defensive (should not reach)


def _survey_default_for(
    slug: str, survey: SurveyDefaults | None
) -> str | None:
    if survey is None:
        return None
    return getattr(survey, slug, None)


def _normalise_answer(
    slug: str, raw: str, detection: LanguageDetection
) -> str:
    """Map raw user input to the canonical value written to manifest.

    Per the LEGAL_* frozen sets in :mod:`manifest`. Tolerates "1" /
    "yes" / "y" / "Yes" shapes per AC.ONBOARD test convention.
    """
    text = raw.strip().lower()
    if slug == "language":
        # Confirm-detection branch: "1" / "y" / "yes" preserves detection.
        if text in {"1", "y", "yes"}:
            return detection.primary if detection.primary != "mixed" else "ruby"
        # Mixed Q1 (1=Ruby / 2=JS/TS / 3=other).
        if detection.primary == "mixed":
            if text == "1":
                return "ruby"
            if text == "2":
                return "ts"
            if text == "3":
                return "other"
        # Free-form override.
        for legal in ("rails", "ruby", "ts", "js", "mixed", "other", "unknown"):
            if legal in text:
                return legal
        return "unknown"
    if slug == "channel":
        if text in {"1", "telegram", "yes", "y"}:
            return "telegram"
        if text in {"2", "cli", "cli-only"}:
            return "cli"
        if text in {"3", "skip", "deferred", "defer"}:
            return "deferred"
        return "deferred"
    if slug == "safety_profile":
        if text in {"1", "production-stake", "production"}:
            return "production-stake"
        if text in {"2", "dev"}:
            return "dev"
        if text in {"3", "research"}:
            return "research"
        return "dev"
    if slug == "extractor":
        if text in {"1", "yes", "y", "now"}:
            return "yes"
        if text in {"2", "defer", "deferred", "later"}:
            return "deferred"
        if text in {"3", "never", "no"}:
            return "never"
        return "deferred"
    if slug == "watch":
        if text in {"1", "yes", "y"}:
            return "yes"
        if text in {"3", "no", "n"}:
            return "no"
        # Default-defer per AC.ONBOARD.7.
        return "deferred"
    if slug == "auto_skill_capture":
        if text in {"1", "yes", "y"}:
            return "yes"
        # Default-no per AC.ONBOARD.8.
        return "no"
    return text


def _channel_to_field(channel: str) -> str:
    """Map normalised channel answer to manifest field value."""
    if channel == "telegram":
        return "telegram"
    if channel == "cli":
        return "cli"
    return "deferred"


def _channel_to_primary_channel(channel: str) -> str | None:
    """Map normalised channel answer to v0.7.0 ``primary_channel``
    runtime-routing slot (AC.NTU.2).

    Per D-NTU.2.b: the same Q2 answer drives both the legacy
    ``channel_preference`` field and the new ``primary_channel`` field.
    Telegram → telegram; CLI-only → terminal; Skip-for-now → None
    (loader/runtime treats None as terminal-equivalent for behavior
    preservation, matching pre-v0.7.0 behaviour).
    """
    if channel == "telegram":
        return "telegram"
    if channel == "cli":
        return "terminal"
    # "deferred" or anything else: leave unset (None).
    return None


# ---- activation dispatch --------------------------------------------


def _dispatch_activation(
    slug: str,
    normalised: str,
    workspace_root: Path,
    detection: LanguageDetection,
    *,
    extractor_cmd: list[str] | None,
) -> ActivationResult | None:
    """Fire the activation matching the user's Y answer (if any)."""
    if slug == "channel" and normalised == "telegram":
        return activate_channel_telegram(workspace_root)
    if slug == "extractor" and normalised == "yes":
        return activate_extractor(
            workspace_root,
            language=detection.primary,
            extractor_cmd=extractor_cmd,
        )
    if slug == "watch" and normalised == "yes":
        return activate_watch_pointer(workspace_root)
    return None


# ---- completion summary ---------------------------------------------


def _write_completion_summary(
    workspace_root: Path,
    *,
    answers: dict[str, str],
    activations: list[ActivationResult],
    audit_path: Path,
    production_stake_force_flip: bool,
) -> Path:
    """Write the AC.ONBOARD.9 completion summary."""
    next_action = _next_action(answers, activations)
    flip_note = ""
    if production_stake_force_flip:
        flip_note = (
            "\n**Production-stake mode disables auto-skill-capture "
            "(SOC-2 floor); your Y on Q6 is overridden to N.**\n"
        )
    capabilities = (
        f"- Language: {answers.get('language', 'unknown')}\n"
        f"- Channel: {answers.get('channel', 'deferred')}\n"
        f"- Safety profile: {answers.get('safety_profile', 'dev')}\n"
        f"- Extractor: {answers.get('extractor', 'deferred')}\n"
        f"- Continuous-watch: {answers.get('watch', 'deferred')}\n"
        f"- Auto-skill-capture: {answers.get('auto_skill_capture', 'no')}\n"
    )
    body = (
        f"# loam onboarding completion summary\n"
        f"\n"
        f"## Capabilities active\n"
        f"\n"
        f"{capabilities}"
        f"{flip_note}"
        f"\n"
        f"## Next action\n"
        f"\n"
        f"{next_action}\n"
        f"\n"
        f"## Audit-log\n"
        f"\n"
        f"`{audit_path!s}`\n"
    )
    pointer_dir = workspace_root / ".loam"
    pointer_dir.mkdir(parents=True, exist_ok=True)
    summary_path = pointer_dir / "onboarding-summary.md"
    summary_path.write_text(body, encoding="utf-8")
    return summary_path


def _next_action(
    answers: dict[str, str],
    activations: list[ActivationResult],
) -> str:
    """Compose the AC.ONBOARD.9 single-next-action prose."""
    channel = answers.get("channel", "deferred")
    extractor = answers.get("extractor", "deferred")
    if channel == "telegram":
        return (
            "Open a Telegram chat with your bot — the setup-walkthrough "
            "will resume from step 1 in your next session."
        )
    if extractor == "deferred":
        return "Run `loam odd-extract <repo>` when you're ready to extract."
    if extractor == "yes":
        return (
            "The extractor fired against your codebase; review the contract "
            "draft at `<workspace>/.loam/extractions/`."
        )
    return "You're set up. Try a turn in Claude Code in this workspace."
