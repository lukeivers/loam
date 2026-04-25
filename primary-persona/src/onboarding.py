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
from typing import Any, Callable, Literal

from .contract import PersonaContract, load_contract
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


# Canonical question-shape tuple. D-build.2 (amendment #35) selected
# three questions: user_name (the user's preferred address),
# persona_given_name (the persona's own name; default is workspace-
# bootstrap's pick), and domain_focus (one-sentence prose into
# responsibilities.single_point_of_contact). Sub-plan A of the two-
# modes-and-multi-workspace programme adds a fourth question
# (``dev_intent``) that captures whether the operator intends to
# develop pos-v2 itself or use it as a harness only — see AC.A.1.
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
    OnboardingQuestion(
        id="dev_intent",
        prompt=(
            "Are you here to develop pos-v2 itself, or to use it as "
            "a harness for your own work? (yes = developing pos-v2; "
            "no = using it.)"
        ),
        contract_field="dev_intent",
        required=True,
    ),
)


# Accepted dev-intent answer literals. The contract's
# ``Literal["unanswered", "yes", "no"]`` typing rejects anything else
# structurally; this set is the transcript-time sanitiser so a free-
# text user reply normalises to the contract's admissible values
# before the contract validator sees them.
_DEV_INTENT_YES = frozenset({"yes", "y", "develop", "dev", "pos-v2", "true"})
_DEV_INTENT_NO = frozenset({"no", "n", "use", "user", "harness", "false"})


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
        # Question count derived from the canonical tuple per
        # sub-plan A D-A.3 — adding a fifth question in the future
        # never silently drifts the body text.
        question_count = len(ONBOARDING_QUESTIONS)

        # Resolve the contract path so the write-back instructions can
        # name an exact target (AC46.7). The loaded persona carries
        # ``directory`` (loader.LoadedPersona); contract.yaml is the
        # canonical filename. Fall back to a placeholder if the
        # attribute is absent (test fixtures using a stand-in
        # _FakeLoadedPersona without ``directory``).
        directory = getattr(loaded_persona, "directory", None)
        if directory is not None:
            contract_path_str = f"{directory}/contract.yaml"
        else:
            contract_path_str = "<workspace>/personas/<handle>/contract.yaml"

        # AC46.7 — body widening. Preserves AC35.3 (first line is the
        # marker) and AC.A.4 (body contains "{count} questions").
        # Body now includes the question id+prompt list and write-back
        # instructions naming ``persist_elicitation_transcript`` so the
        # loaded persona can conduct the elicitation from
        # additionalContext alone (without persona-prompt customisation).
        lines: list[str] = [
            STARTER_PENDING_MARKER,
            (
                f"The workspace's persona contract is in starter state. "
                f"{contract.given_name} opens elicitation on the next "
                f"user turn ({question_count} questions, ~2 minutes, "
                f"skippable)."
            ),
            "",
            "questions:",
        ]
        for q in ONBOARDING_QUESTIONS:
            lines.append(
                f"  - id={q.id} required={q.required} prompt={q.prompt}"
            )
        lines.extend(
            [
                "",
                "write-back:",
                (
                    "  Call "
                    "primary_persona.onboarding.persist_elicitation_"
                    "transcript(loaded_persona=<persona>, "
                    "transcript={<id>: <answer>, ...}, "
                    f"contract_path=Path({contract_path_str!r})) "
                    "after collecting non-empty answers for every "
                    "required id. The call flips is_starter to False "
                    "on a complete transcript and writes the contract "
                    "yaml back to disk."
                ),
            ]
        )
        body = "\n".join(lines)

        # Per-contributor budget guard (AC46.7): keep the body under
        # 2,000 chars so the SessionStart payload's other contributors
        # fit alongside under the composer's 10,000-char cap. The
        # canonical 4-question tuple produces ~800 chars; defensive
        # truncation kicks in only if a future contract author appends
        # very-long-prompt questions.
        _BUDGET = 2000
        if len(body) > _BUDGET:
            # Hard-trim trailing question prompts; retain the marker,
            # introductory line, every question id (so the persona can
            # still iterate the schema), and the write-back block.
            ellipsis = "  [body trimmed to fit per-contributor budget]"
            head = (
                f"{STARTER_PENDING_MARKER}\n"
                f"The workspace's persona contract is in starter "
                f"state. {contract.given_name} opens elicitation on "
                f"the next user turn ({question_count} questions, ~2 "
                f"minutes, skippable).\n\nquestions:"
            )
            ids_only = "\n".join(
                f"  - id={q.id}" for q in ONBOARDING_QUESTIONS
            )
            tail = lines[-3] + "\n" + lines[-2] + "\n" + lines[-1]
            body = head + "\n" + ids_only + "\n" + ellipsis + "\n" + tail
            if len(body) > _BUDGET:
                # Truly defensive: the static text already exceeds the
                # budget. Preserve the marker + ellipsis only. The
                # elicitation surface degrades; the marker still
                # signals starter-pending so the persona knows to act.
                body = (
                    f"{STARTER_PENDING_MARKER}\n"
                    f"{question_count} questions; body exceeded "
                    f"{_BUDGET}-char budget — see "
                    "primary_persona.onboarding.ONBOARDING_QUESTIONS."
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
        # Sub-plan A AC.A.7 — distinct dev-intent question event so
        # consumers can count it without filtering on question_id.
        if q.id == "dev_intent":
            obs.onboarding_dev_intent_question_event(
                handle=handle, workspace_slug=workspace_slug
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

    # Sub-plan A AC.A.3 — dev-intent write-back. Normalise the user's
    # free-text answer to the contract's Literal admissible values; an
    # unrecognised non-empty answer raises OnboardingTranscriptError
    # (distinct from "incomplete" — the user gave an answer the
    # framework cannot map to yes/no, which is structural).
    dev_intent_raw = transcript.get("dev_intent", "")
    if isinstance(dev_intent_raw, str) and dev_intent_raw.strip():
        normalised = _normalise_dev_intent(dev_intent_raw)
        if normalised is None:
            raise OnboardingTranscriptError(
                f"transcript value for 'dev_intent' must be a yes/no answer, "
                f"got {dev_intent_raw!r}"
            )
        payload["dev_intent"] = normalised
        obs.onboarding_dev_intent_answer_event(
            handle=handle,
            answer=normalised,
            workspace_slug=workspace_slug,
        )

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


# ---- dev-intent helpers (sub-plan A — two-modes-and-multi-workspace) -


def _normalise_dev_intent(raw: str) -> Literal["yes", "no"] | None:
    """Map a free-text answer to the contract's Literal yes/no.

    Returns ``None`` for any non-empty input that is neither a known
    yes-token nor a known no-token; callers translate ``None`` to
    ``OnboardingTranscriptError``. The normaliser is intentionally
    case-insensitive and trims surrounding whitespace.
    """
    token = raw.strip().lower()
    if not token:
        return None
    if token in _DEV_INTENT_YES:
        return "yes"
    if token in _DEV_INTENT_NO:
        return "no"
    return None


def dev_intent_storage_path(workspace_root: Path) -> Path:
    """Return the on-disk location of the workspace's dev-intent
    answer (sub-plan A AC.A.5).

    Per locked owner ruling D-MASTER.1 (a) the dev-intent answer
    lives on the persona contract itself. The workspace's primary
    persona contract is at
    ``<workspace>/personas/<handle>/contract.yaml``. The handle is
    not statically known (workspace-bootstrap chooses it at scaffold
    time), so the resolver returns the *personas* directory path
    that the reader walks to find the primary contract.

    Sub-plans E, B, F consume this resolver — not the contract
    directly — so the storage shape is substitutable without
    re-reading those sub-plans (per AC.A.5 rationale + sub-plan A
    asymmetric observation #2: resolver-as-API).
    """
    return Path(workspace_root) / "personas"


def _primary_contract_path(workspace_root: Path) -> Path | None:
    """Locate the workspace's primary-persona ``contract.yaml``.

    Returns the first ``personas/<handle>/contract.yaml`` whose
    ``is_primary: true`` or — if no contract claims primary — the
    first persona contract found. Returns ``None`` when no contract
    exists yet (fresh workspace, scaffold not run, mid-starter).
    """
    personas_dir = dev_intent_storage_path(workspace_root)
    if not personas_dir.is_dir():
        return None
    candidates: list[Path] = []
    for child in sorted(personas_dir.iterdir()):
        if not child.is_dir():
            continue
        contract_path = child / "contract.yaml"
        if contract_path.is_file():
            candidates.append(contract_path)
    if not candidates:
        return None
    # Prefer a primary-flagged contract; otherwise return the first
    # alphabetical contract (deterministic).
    for candidate in candidates:
        try:
            contract = load_contract(candidate)
        except Exception:  # noqa: BLE001 — fail-safe on malformed contract
            continue
        if getattr(contract, "is_primary", False):
            return candidate
    return candidates[0]


def read_dev_intent(
    workspace_root: Path,
) -> Literal["yes", "no", "absent"]:
    """Return the workspace's dev-intent answer (sub-plan A AC.A.6).

    Returns ``"yes"`` / ``"no"`` when the persona contract carries
    an answered ``dev_intent`` field. Returns ``"absent"`` when the
    workspace has no contract yet, when the contract fails to load,
    or when the contract's ``dev_intent`` is the documented
    ``"unanswered"`` sentinel. Per locked owner ruling D-MASTER.4
    consumers (sub-plan E) treat ``"absent"`` as "no".
    """
    contract_path = _primary_contract_path(workspace_root)
    if contract_path is None:
        return "absent"
    try:
        contract = load_contract(contract_path)
    except Exception:  # noqa: BLE001 — fail-safe on malformed contract
        return "absent"
    answer = getattr(contract, "dev_intent", "unanswered")
    if answer == "yes":
        return "yes"
    if answer == "no":
        return "no"
    return "absent"
