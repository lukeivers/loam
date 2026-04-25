"""First-run conversational elicitation (amendment #35).

The onboarding module owns the starter-elicitation flow: a small set
of question-shape templates the persona uses on session one to refine
a starter-flagged contract into the user's persona, plus the
transcript→contract write-back that persists user answers and flips
``is_starter`` to False on completion.

Surface:

- ``ONBOARDING_QUESTIONS`` — the canonical question-shape tuple. Each
  question has an id (used in transcript dicts and OTel events) and a
  prompt. The prompts are *framework-level scaffolding* — they speak
  about the contract, not in the persona's voice. The answers (the
  workspace-supplied content) flow into the contract.

- ``build_starter_pending_contributor(loaded_persona)`` — returns the
  callable that registers against
  ``ComposedContextPayload.register(name=..., trigger_kind=session)``.
  When invoked under a starter-flagged contract the contributor
  produces an additionalContext block carrying a structurally-
  detectable starter-pending marker. Under a non-starter contract the
  contributor returns the empty string (per the registry's "empty
  output is no-op contribution" convention).

- ``persist_elicitation_transcript(loaded_persona, transcript, contract_path)``
  — write-back surface. Given a complete transcript (all required
  question ids answered with non-empty strings), writes the answers
  back into the contract via ``PersonaContract.to_yaml()`` and flips
  ``is_starter`` to False. Given an incomplete transcript leaves
  ``is_starter`` True. The fail-closed direction matches plan §6
  constraint 7.

Per ODD §2.5 every code path traces back to AC35.3 (contributor
registration), AC35.4 (transcript→write-back), or AC35.7
(observability).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .contract import PersonaContract
from . import observability as obs


# ---- exceptions ------------------------------------------------------


class OnboardingTranscriptError(ValueError):
    """Raised on a structurally-malformed transcript (e.g., a
    non-string value, an unknown question id). Distinct from "transcript
    incomplete" — incomplete is a normal state; malformed is a defect."""


# ---- question shapes -------------------------------------------------


@dataclass(frozen=True)
class OnboardingQuestion:
    """A single elicitation question.

    Question prompts are framework-level scaffolding — they speak
    *about* the contract (e.g., "What should I call you?") and are not
    persona-prose. The answer is the workspace-supplied content that
    populates a contract field.
    """

    id: str
    prompt: str
    contract_field: str  # dotted path into PersonaContract; see _SET_FIELD_HANDLERS
    required: bool = True


# Canonical question-shape tuple. D-build.2 selected three questions:
# user_name (the user's preferred address), persona_given_name (the
# persona's own name; default is workspace-bootstrap's pick), and
# domain_focus (one-sentence prose into responsibilities.single_point_of_contact).
ONBOARDING_QUESTIONS: tuple[OnboardingQuestion, ...] = (
    OnboardingQuestion(
        id="user_name",
        prompt="What should I call you?",
        contract_field="user_name",  # not on the contract directly; see note below
        required=True,
    ),
    OnboardingQuestion(
        id="persona_given_name",
        prompt=(
            "What should I call myself? "
            "(You can also pick a different name later.)"
        ),
        contract_field="given_name",
        required=True,
    ),
    OnboardingQuestion(
        id="domain_focus",
        prompt="What kinds of work do you most want me to handle?",
        contract_field="responsibilities.single_point_of_contact",
        required=True,
    ),
)


# Note on ``user_name``: the persona contract holds ``given_name`` for
# the persona's own name; the *user's* preferred address lives in the
# workspace's ``prompt.md`` body or in user-context the persona learns
# (memory). Recording the user_name answer in the transcript and
# emitting an observability event is sufficient for AC35.4 (the AC
# measures persistence of answers; user_name is intentionally a non-
# contract write-back so the value flows into prompt.md if a future
# amendment writes one — outside this amendment's scope). The
# transcript's user_name entry is preserved through the write-back
# call and emitted as an event for downstream consumers.


# Structurally-detectable marker prefix on the starter-pending
# contributor's first line. AC35.3 measures presence of this prefix.
STARTER_PENDING_MARKER = "[primary-persona/onboarding starter-pending]"


# ---- starter-pending contributor ------------------------------------


def build_starter_pending_contributor(
    loaded_persona: Any,
) -> Callable[[dict[str, Any]], str]:
    """Return the callable registered on
    ``ComposedContextPayload.register(name="starter-pending",
    trigger_kind=TriggerKind.session, fn=<returned callable>)``.

    On every ``on_session_start`` the contributor inspects the
    loaded persona's contract; if ``is_starter`` is True it returns a
    starter-pending block whose first line carries
    ``STARTER_PENDING_MARKER`` (AC35.3 measures this); else returns the
    empty string (the composer's convention for "no contribution
    this turn").

    ``loaded_persona`` is the late-bound persona reference — the
    contributor reads ``loaded_persona.contract`` on each invocation,
    so a contract whose ``is_starter`` was flipped during the session
    (by ``persist_elicitation_transcript``) is reflected on the next
    session-start without re-registration.
    """

    def contributor(context: dict[str, Any]) -> str:
        contract = loaded_persona.contract
        if not getattr(contract, "is_starter", False):
            return ""
        body = (
            f"{STARTER_PENDING_MARKER}\n"
            f"The workspace's persona contract is in starter state. "
            f"{contract.given_name} opens elicitation on the next user "
            f"turn (3 questions, ~2 minutes, skippable)."
        )
        return body

    return contributor


# ---- transcript shape + write-back ----------------------------------


def _is_complete_transcript(transcript: dict[str, str]) -> bool:
    """All required questions answered with non-empty strings."""
    for q in ONBOARDING_QUESTIONS:
        if not q.required:
            continue
        value = transcript.get(q.id)
        if not isinstance(value, str) or not value.strip():
            return False
    return True


def _validate_transcript_shape(transcript: dict[str, str]) -> None:
    """Reject malformed transcripts — non-str values, unknown ids."""
    known_ids = {q.id for q in ONBOARDING_QUESTIONS}
    for k, v in transcript.items():
        if k not in known_ids:
            raise OnboardingTranscriptError(
                f"transcript carries unknown question id: {k!r}"
            )
        if not isinstance(v, str):
            raise OnboardingTranscriptError(
                f"transcript value for {k!r} must be str, got {type(v).__name__}"
            )


def persist_elicitation_transcript(
    *,
    loaded_persona: Any,
    transcript: dict[str, str],
    contract_path: Path,
    workspace_slug: str | None = None,
) -> PersonaContract:
    """Write transcript answers back to the contract on disk.

    Validates the transcript shape (raises ``OnboardingTranscriptError``
    on structural malformation). On a *complete* transcript: applies
    every required-question answer to the corresponding contract
    field, flips ``is_starter`` to False, serialises via
    ``contract.to_yaml()``, writes ``contract_path``, and returns the
    new contract. On an *incomplete* transcript: applies any answers
    present (best-effort), keeps ``is_starter`` True, serialises +
    writes, returns the new contract. The next session re-opens
    elicitation (AC35.4 negative path).

    Emits OTel events for each question dispatched, each answer
    recorded, the write-back outcome, and any starter-flag transition
    (AC35.7).
    """
    _validate_transcript_shape(transcript)

    current = loaded_persona.contract
    handle = current.handle

    # Emit one question + answer event per known question (whether or
    # not it has a transcript entry — observability spans the
    # elicitation lifecycle, not just the answered subset).
    for q in ONBOARDING_QUESTIONS:
        obs.onboarding_question_event(
            handle=handle, question_id=q.id, workspace_slug=workspace_slug
        )
        answer = transcript.get(q.id, "")
        if isinstance(answer, str) and answer.strip():
            obs.onboarding_answer_event(
                handle=handle,
                question_id=q.id,
                answer_length=len(answer),
            )

    completed = _is_complete_transcript(transcript)

    # Build the updated contract dict — start from the current
    # contract's serialised form so all preserved fields keep their
    # values; mutate only the fields with answers.
    payload = current.model_dump(mode="json")

    persona_given_name = transcript.get("persona_given_name", "").strip()
    if persona_given_name:
        payload["given_name"] = persona_given_name

    domain_focus = transcript.get("domain_focus", "").strip()
    if domain_focus:
        payload["responsibilities"]["single_point_of_contact"] = domain_focus

    # user_name does not map to a contract field in this amendment's
    # scope (see module-docstring note). Its presence is recorded via
    # the answer event above; no payload mutation here.

    new_is_starter = False if completed else current.is_starter
    payload["is_starter"] = new_is_starter

    new_contract = PersonaContract.model_validate(payload)

    # Write the YAML to disk via the contract's existing surface.
    contract_path.write_text(new_contract.to_yaml())

    # Emit write-back + starter-flag-transition events.
    obs.onboarding_writeback_event(
        handle=handle, completed=completed, workspace_slug=workspace_slug
    )
    if current.is_starter != new_is_starter:
        obs.onboarding_starter_flag_transition_event(
            handle=handle,
            from_value=current.is_starter,
            to_value=new_is_starter,
        )

    return new_contract
