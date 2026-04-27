"""First-run conversational onboarding (amendment #50).

The onboarding module owns the starter-elicitation surface: a
``starter-pending`` SessionStart contributor that points the
loaded persona at its `prompt.md` playbook, plus a structured
write-back surface (``persist_grounding``) that closes the
contract / `prompt.md` / `.claude/agents/<handle>.md` triplet
when the persona has captured enough grounding from the
conversation to commit.

Discovery is conversational (driven by the playbook in
`prompt.md`); the write-back accepts a structured
``GroundingCapture`` payload the persona produces when it
pivots from listening to proposing.

Surface:

- ``STARTER_PENDING_MARKER`` — first-line marker on the
  starter-pending contributor's body. Unchanged.
- ``GroundingCapture`` — structured payload the persona
  builds at the proposal moment.
- ``OnboardingGroundingError`` — raised on a malformed
  ``GroundingCapture``; no file is written.
- ``build_starter_pending_contributor(loaded_persona)`` —
  returns the SessionStart contributor. Body points at the
  playbook in `prompt.md` and at the ``persist_grounding``
  call surface; no question list, no question ids.
- ``persist_grounding(*, loaded_persona, grounding,
  contract_path, workspace_slug=None,
  memory_client_factory=None)`` — write-back that updates
  ``contract.yaml`` from the captured grounding, regenerates
  ``prompt.md`` (with substitution-token rendering) and
  ``.claude/agents/<handle>.md`` (via ``to_agent_md``), and
  optionally writes one ``add_episode`` memory episode tagged
  ``"onboarding-grounding"``.

Read-side dev-intent surface (preserved verbatim from sub-plan A):

- ``dev_intent_storage_path(workspace_root) -> Path``
- ``read_dev_intent(workspace_root) -> Literal["yes", "no", "absent"]``

Per ODD §2.5 every code path traces back to AC.O.1, AC.O.2,
AC.O.3, AC.O.4, AC.O.5, AC.O.6, AC.O.7, or AC.O.8 (locked plan
``primary-persona-conversational-onboarding-and-default-archetype.md``).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable, Literal

from .agent_md import to_agent_md
from .contract import PersonaContract, load_contract
from . import observability as obs


# ---- exceptions ------------------------------------------------------


class OnboardingGroundingError(ValueError):
    """Raised on a malformed ``GroundingCapture`` payload (empty
    required field, invalid dev-intent value, empty captured-summary).
    The disk write-back is **never** attempted on a malformed
    payload — failure is fail-closed at validation time."""


# ---- captured-grounding payload --------------------------------------


@dataclass(frozen=True)
class GroundingCapture:
    """Structured grounding captured by the persona at the proposal
    moment of session-1 conversational onboarding (per the
    conversation playbook in the persona's `prompt.md`).

    Fields are the persona's distillation of what the user said
    during the funnel + reflection phase, not literal user prose.
    Each field is required; ``persist_grounding`` validates shape
    before any file is written.

    - ``user_preferred_name``: how the persona will address the user
      (the persona's translation of "what should I call you?", which
      may be inferred from the conversation rather than asked
      directly).
    - ``persona_given_name``: the persona's own name as the user
      chose it (or kept it).
    - ``single_point_of_contact`` / ``context_holder`` /
      ``escalation_judge``: the persona's distillation of the user's
      day-walkthrough into the three responsibilities-prose fields
      the contract carries.
    - ``dev_intent``: literal ``"yes"`` or ``"no"``, inferred from
      the day-walkthrough's mention (or absence) of pos-v2-dev work.
    - ``captured_summary``: tuple of non-empty bullets — the
      persona's distillation of what it heard, used both as
      observability material and as the body of the optional
      memory episode.
    """

    user_preferred_name: str
    persona_given_name: str
    single_point_of_contact: str
    context_holder: str
    escalation_judge: str
    dev_intent: Literal["yes", "no"]
    captured_summary: tuple[str, ...]


# ---- structurally-detectable marker ----------------------------------

# Preserved from amendment #35; the marker prefix is what the
# session-start hook detects to know the workspace is in starter
# state. The hook surface (D8 composer) is unchanged.
STARTER_PENDING_MARKER = "[primary-persona/onboarding starter-pending]"


# ---- starter-pending contributor (AC.O.2) ----------------------------


def build_starter_pending_contributor(
    loaded_persona: Any,
) -> Callable[[dict[str, Any]], str]:
    """Return the callable registered against
    ``ComposedContextPayload.register(name="starter-pending",
    trigger_kind=TriggerKind.session, fn=<returned callable>)``.

    On every ``on_session_start`` the contributor inspects the
    loaded persona's contract; if ``is_starter`` is True it returns
    a starter-pending block whose:

    - first line is ``STARTER_PENDING_MARKER``;
    - body points the persona at the conversation playbook in
      ``prompt.md``;
    - body names the ``persist_grounding`` write-back surface and
      the resolved contract path;
    - body does **not** carry a numbered question list, and does
      **not** name the prior elicitation question ids
      (``user_name``, ``persona_given_name``, ``domain_focus``,
      ``dev_intent`` as bare ``id=...`` markers — the new shape
      inverts the prior list shape entirely);
    - total length is ≤ 2,000 chars (preserved per-contributor
      budget per AC46.7).

    Under a non-starter contract the contributor returns the empty
    string (the composer's convention for "no contribution this
    turn").

    ``loaded_persona`` is the late-bound persona reference — the
    contributor reads ``loaded_persona.contract`` on each invocation,
    so a contract whose ``is_starter`` was flipped during the
    session (by ``persist_grounding``) is reflected on the next
    session-start without re-registration.
    """

    def contributor(context: dict[str, Any]) -> str:
        contract = loaded_persona.contract
        if not getattr(contract, "is_starter", False):
            return ""

        directory = getattr(loaded_persona, "directory", None)
        if directory is not None:
            contract_path_str = f"{directory}/contract.yaml"
            prompt_path_str = f"{directory}/prompt.md"
        else:
            contract_path_str = "<workspace>/personas/<handle>/contract.yaml"
            prompt_path_str = "<workspace>/personas/<handle>/prompt.md"

        body = (
            f"{STARTER_PENDING_MARKER}\n"
            f"The workspace's persona contract is in starter state. "
            f"{contract.given_name} opens conversational onboarding "
            f"on the next user turn — see the playbook in "
            f"{prompt_path_str}.\n"
            "\n"
            "playbook:\n"
            "  Open with the three seed questions, run a funnel "
            "with two reflections per question, and pivot from "
            "listening to proposing when the 3-of-5 rule fires "
            "(see the Pivot rule section of prompt.md). At the "
            "proposal moment, reflect what was heard, offer 2–3 "
            "concrete deliverables, and close with a question.\n"
            "\n"
            "write-back:\n"
            "  When the user picks a deliverable, build a "
            "GroundingCapture from the conversation and call "
            "primary_persona.onboarding.persist_grounding("
            "loaded_persona=<persona>, grounding=<GroundingCapture>, "
            f"contract_path=Path({contract_path_str!r})). The call "
            "writes the contract, regenerates prompt.md and "
            ".claude/agents/<handle>.md, flips is_starter to False, "
            "and records an onboarding-grounding memory episode "
            "(if the live MCP client is available)."
        )

        # Per-contributor budget guard (AC46.7 inheritance — kept
        # verbatim from the prior shape). The new body is small
        # (~1,000 chars at typical workspace path lengths); the
        # guard is defence-in-depth for unusually long workspace
        # paths. AC.O.2 measures ≤ 2,000.
        _BUDGET = 2000
        if len(body) > _BUDGET:
            body = (
                f"{STARTER_PENDING_MARKER}\n"
                f"{contract.given_name} opens conversational "
                f"onboarding next turn — see playbook at "
                f"{prompt_path_str}; write back via "
                "persist_grounding."
            )
        return body

    return contributor


# ---- captured-grounding write-back (AC.O.3 / AC.O.4 / AC.O.5) -------


def _validate_grounding_payload(grounding: GroundingCapture) -> None:
    """Reject a malformed ``GroundingCapture`` before any file write.

    The fail-closed direction (locked plan §7 constraint 6): on
    any malformed field, raise ``OnboardingGroundingError`` and do
    not write any file. The caller's contract is "if this returns,
    the payload is safe to apply"; if it raises, no on-disk state
    has been mutated.
    """

    def _ensure_nonempty(field: str, value: Any) -> None:
        if not isinstance(value, str) or not value.strip():
            raise OnboardingGroundingError(
                f"GroundingCapture.{field} must be a non-empty "
                f"string; got {value!r}"
            )

    _ensure_nonempty("user_preferred_name", grounding.user_preferred_name)
    _ensure_nonempty("persona_given_name", grounding.persona_given_name)
    _ensure_nonempty("single_point_of_contact", grounding.single_point_of_contact)
    _ensure_nonempty("context_holder", grounding.context_holder)
    _ensure_nonempty("escalation_judge", grounding.escalation_judge)

    if grounding.dev_intent not in ("yes", "no"):
        raise OnboardingGroundingError(
            "GroundingCapture.dev_intent must be 'yes' or 'no'; "
            f"got {grounding.dev_intent!r}"
        )

    if not isinstance(grounding.captured_summary, tuple):
        raise OnboardingGroundingError(
            "GroundingCapture.captured_summary must be a tuple of "
            f"non-empty strings; got {type(grounding.captured_summary).__name__}"
        )
    if len(grounding.captured_summary) == 0:
        raise OnboardingGroundingError(
            "GroundingCapture.captured_summary must be a non-empty "
            "tuple of summary bullets"
        )
    for i, bullet in enumerate(grounding.captured_summary):
        if not isinstance(bullet, str) or not bullet.strip():
            raise OnboardingGroundingError(
                f"GroundingCapture.captured_summary[{i}] must be a "
                f"non-empty string; got {bullet!r}"
            )


def _resolve_template_prompt_body() -> str:
    """Locate the framework-shipped persona-template prompt.md and
    return its body text.

    Walks ``Path(__file__).parents`` for a directory layout
    ``primary-persona/templates/persona-template/prompt.md``. This
    mirrors the resolver used by ``workspace-bootstrap``'s scaffold
    (``_resolve_persona_template_dir``); the persona layer reads
    its own template directly here rather than import from the
    workspace-bootstrap component.

    Raises ``OnboardingGroundingError`` if the template cannot be
    located — a structural failure that surfaces to the caller as a
    grounding-write rejection (the disk write-back cannot proceed
    without a template body). This branch maps to AC.O.4 (template
    body must be readable to substitute names into).
    """
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = (
            parent / "primary-persona" / "templates"
            / "persona-template" / "prompt.md"
        )
        if candidate.is_file():
            return candidate.read_text()
        # The persona-template lives under primary-persona/; if we
        # are inside primary-persona/src/, the template is at
        # ../templates/persona-template/prompt.md.
        sibling = (
            parent / "templates" / "persona-template" / "prompt.md"
        )
        if sibling.is_file():
            return sibling.read_text()
    raise OnboardingGroundingError(
        "framework persona-template prompt.md not found while "
        "rendering onboarding grounding write-back"
    )


def _render_prompt_md(
    template_body: str,
    *,
    user_preferred_name: str,
    persona_given_name: str,
) -> str:
    """Substitute the ``{user_preferred_name}`` and
    ``{persona_given_name}`` tokens in the template body via
    ``str.format``.

    The template author escapes any literal ``{`` / ``}`` outside
    these two tokens as ``{{`` / ``}}`` per Python's str.format
    convention. AC.O.1 verifies the tokens are present in the
    template; AC.O.4 verifies the substituted output carries the
    user-chosen names and no leftover token literal.
    """
    return template_body.format(
        user_preferred_name=user_preferred_name,
        persona_given_name=persona_given_name,
    )


def _build_episode_body(grounding: GroundingCapture) -> str:
    """Compose the body of the onboarding-grounding memory
    episode from the captured grounding.

    Includes the captured-summary bullets and the inferred fields
    so a future retrieval surface (out of scope for this amendment)
    can reconstruct the user's session-1 self-description without
    re-asking. AC.O.5 measures presence of the captured-summary
    text in the emitted episode body.
    """
    summary_block = "\n".join(
        f"- {bullet}" for bullet in grounding.captured_summary
    )
    return (
        f"Onboarding grounding captured during session 1.\n\n"
        f"User preferred name: {grounding.user_preferred_name}\n"
        f"Persona given name: {grounding.persona_given_name}\n"
        f"dev_intent: {grounding.dev_intent}\n\n"
        f"Single point of contact:\n  {grounding.single_point_of_contact}\n\n"
        f"Context holder:\n  {grounding.context_holder}\n\n"
        f"Escalation judge:\n  {grounding.escalation_judge}\n\n"
        f"Captured summary:\n{summary_block}\n"
    )


def persist_grounding(
    *,
    loaded_persona: Any,
    grounding: GroundingCapture,
    contract_path: Path,
    workspace_slug: str | None = None,
    memory_client_factory: Callable[[], Any | None] | None = None,
) -> PersonaContract:
    """Write the captured grounding back across the three persona
    surfaces (contract / prompt.md / .claude/agents/<handle>.md)
    and optionally record one onboarding-grounding memory episode.

    Validation (fail-closed): the ``GroundingCapture`` payload is
    validated first; any malformed field raises
    ``OnboardingGroundingError`` and **no file is written**.

    On a well-formed payload:

    1. Build the new contract from the loaded persona's serialised
       form, applying the captured fields. ``is_starter`` flips to
       False. ``dev_intent`` is set to the captured literal.
    2. Validate via ``PersonaContract.model_validate``; any
       validation failure raises ``OnboardingGroundingError`` (no
       file write).
    3. Write the new contract YAML to ``contract_path``.
    4. Render and write ``<persona_dir>/prompt.md`` from the
       framework template body with substitution-token rendering.
    5. Render and write ``<workspace>/.claude/agents/<handle>.md``
       via ``to_agent_md`` (carrying the rendered prompt body).
    6. If ``memory_client_factory`` is provided and returns a
       non-None client: drive one ``add_episode`` call with
       ``source_description="onboarding-grounding"``. On client
       failure (None factory result, raise during the call), the
       failure is observable via an event but the disk write-back
       is unaffected — the call never raises out of the memory
       step (AC.O.5 fail-soft).

    Returns the new validated ``PersonaContract``.
    """
    _validate_grounding_payload(grounding)

    current = loaded_persona.contract
    handle = current.handle

    # ---- 1+2. Build + validate the new contract --------------
    payload = current.model_dump(mode="json")
    payload["given_name"] = grounding.persona_given_name
    payload["responsibilities"]["single_point_of_contact"] = (
        grounding.single_point_of_contact
    )
    payload["responsibilities"]["context_holder"] = grounding.context_holder
    payload["responsibilities"]["escalation_judge"] = grounding.escalation_judge
    payload["dev_intent"] = grounding.dev_intent
    payload["is_starter"] = False

    try:
        new_contract = PersonaContract.model_validate(payload)
    except Exception as exc:  # noqa: BLE001 — wrap as grounding error
        raise OnboardingGroundingError(
            f"new contract failed validation after applying "
            f"GroundingCapture: {exc}"
        ) from exc

    # ---- 3. Write contract.yaml ------------------------------
    contract_path = Path(contract_path)
    contract_path.write_text(new_contract.to_yaml())

    # ---- 4+5. Render + write prompt.md and agent file --------
    template_body = _resolve_template_prompt_body()
    rendered_prompt = _render_prompt_md(
        template_body,
        user_preferred_name=grounding.user_preferred_name,
        persona_given_name=grounding.persona_given_name,
    )

    persona_dir = contract_path.parent
    prompt_path = persona_dir / "prompt.md"
    prompt_path.write_text(rendered_prompt)

    # D-migration D.2 (amendment #63): personas live under
    # <workspace>/workspace/personas/<handle>/contract.yaml. The
    # contract path's parent is the persona dir, parent.parent is
    # personas/, parent.parent.parent is <workspace>/workspace/, and
    # parent.parent.parent.parent is <workspace>. Per D-Q.A4 lock,
    # .claude/ lives at workspace root (NOT under workspace/), so we
    # walk one more level than pre-D.2.
    from workspace_bootstrap.workspace_paths import claude_dir

    workspace_root = persona_dir.parent.parent.parent
    claude_agents_dir = claude_dir(workspace_root) / "agents"
    claude_agents_dir.mkdir(parents=True, exist_ok=True)
    agent_md_path = claude_agents_dir / f"{handle}.md"
    agent_md_text = to_agent_md(new_contract, prompt_text=rendered_prompt)
    agent_md_path.write_text(agent_md_text)

    # ---- 6. Optional memory episode (AC.O.5) -----------------
    if memory_client_factory is not None:
        _maybe_write_grounding_episode(
            grounding=grounding,
            handle=handle,
            workspace_slug=workspace_slug,
            factory=memory_client_factory,
        )

    # Observability: grounding-persisted event so audit can
    # correlate with the contract write.
    obs.onboarding_grounding_persisted_event(
        handle=handle, workspace_slug=workspace_slug
    )

    # Starter-flag transition is observable on every successful
    # persist_grounding (the only path that flips is_starter to
    # False). Reuse the existing event from amendment #35.
    if current.is_starter and not new_contract.is_starter:
        obs.onboarding_starter_flag_transition_event(
            handle=handle,
            from_value=current.is_starter,
            to_value=new_contract.is_starter,
        )

    return new_contract


def _maybe_write_grounding_episode(
    *,
    grounding: GroundingCapture,
    handle: str,
    workspace_slug: str | None,
    factory: Callable[[], Any | None],
) -> None:
    """Drive one ``add_episode`` call against the memory client the
    factory produces. Fail-soft: on no-client / client-raise the
    function emits an observability event and returns; the caller
    treats this as best-effort.

    The factory is called fresh on every invocation so the live
    MCP client's per-call session lifecycle is honoured (mirrors
    the pattern used by ``cli_memory_write`` in ``stop_emitter.py``).
    """
    try:
        client = factory()
    except Exception as exc:  # noqa: BLE001 — fail-soft per AC.O.5
        obs.onboarding_grounding_episode_failed_event(
            handle=handle,
            workspace_slug=workspace_slug,
            stage="factory",
            error=f"{type(exc).__name__}: {exc}",
        )
        return

    if client is None:
        # Pre-Stop-hook-landing state, or workspace without a live
        # MCP client. The disk write-back has already succeeded;
        # the no-episode path is the documented graceful default.
        return

    body = _build_episode_body(grounding)
    name = f"onboarding-grounding-{handle}"
    reference_time = datetime.now(timezone.utc)
    # ``source`` per amendment #24 / #48 schema — onboarding
    # episodes use the deterministic "message" source per the
    # write-side contract (the persona's distillation is a
    # message-shape episode, not e.g. JSON or code).
    source = "message"
    # ``group_id`` per amendment #24 — the workspace slug isolates
    # episodes per-workspace. Fall back to the handle when the
    # slug is not provided (test fixtures often omit it).
    group_id = workspace_slug or handle

    add = client.add_episode

    try:
        result = add(
            name=name,
            body=body,
            source_description="onboarding-grounding",
            reference_time=reference_time,
            source=source,
            group_id=group_id,
        )
    except Exception as exc:  # noqa: BLE001 — fail-soft per AC.O.5
        obs.onboarding_grounding_episode_failed_event(
            handle=handle,
            workspace_slug=workspace_slug,
            stage="call",
            error=f"{type(exc).__name__}: {exc}",
        )
        return

    # If ``add_episode`` is async (live MCP client uses asyncio),
    # the call returns a coroutine — drive it to completion via
    # ``asyncio.run``. A sync fake client returns a dict directly;
    # both shapes work without isinstance gymnastics on
    # asyncio.iscoroutine.
    if isinstance(result, Awaitable):
        try:
            asyncio.run(result)
        except Exception as exc:  # noqa: BLE001 — fail-soft per AC.O.5
            obs.onboarding_grounding_episode_failed_event(
                handle=handle,
                workspace_slug=workspace_slug,
                stage="await",
                error=f"{type(exc).__name__}: {exc}",
            )


# ---- dev-intent helpers (sub-plan A — preserved verbatim) ------------


def dev_intent_storage_path(workspace_root: Path) -> Path:
    """Return the on-disk location of the workspace's dev-intent
    answer (sub-plan A AC.A.5).

    Per locked owner ruling D-MASTER.1 (a) the dev-intent answer
    lives on the persona contract itself. The workspace's primary
    persona contract is at
    ``<workspace>/personas/<handle>/contract.yaml``. The handle is
    not statically known (workspace-bootstrap chooses it at
    scaffold time), so the resolver returns the *personas*
    directory path that the reader walks to find the primary
    contract.

    Sub-plans E, B, F consume this resolver — not the contract
    directly — so the storage shape is substitutable without
    re-reading those sub-plans.

    D-migration D.2 (amendment #63): personas live under
    ``<workspace>/workspace/personas/`` post-D.2.
    """
    from workspace_bootstrap.workspace_paths import (
        personas_dir as _personas_dir,
    )

    return _personas_dir(workspace_root)


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
    for candidate in candidates:
        try:
            contract = load_contract(candidate)
        except Exception:  # noqa: BLE001 — fail-safe
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
    workspace has no contract yet, when the contract fails to
    load, or when the contract's ``dev_intent`` is the documented
    ``"unanswered"`` sentinel.
    """
    contract_path = _primary_contract_path(workspace_root)
    if contract_path is None:
        return "absent"
    try:
        contract = load_contract(contract_path)
    except Exception:  # noqa: BLE001 — fail-safe
        return "absent"
    answer = getattr(contract, "dev_intent", "unanswered")
    if answer == "yes":
        return "yes"
    if answer == "no":
        return "no"
    return "absent"
