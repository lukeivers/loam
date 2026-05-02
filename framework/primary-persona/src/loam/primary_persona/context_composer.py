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

"""ComposedContextPayload — the shared additionalContext composer (D8).

This primitive is the session-start context-load gate's structural
surface. It exposes two entry points:

- ``on_session_start(workspace_root)`` returns a ``SessionPayload``
  carrying the workspace-baseline corpus paths, session-level state,
  and a ``corpus_gate_state`` sentinel (loaded / partial / missing).
  Session-level contributors registered on the composer contribute
  to this payload.

- ``on_user_prompt_submit(prompt, resolved_component, memory_client)``
  returns a ``TurnPayload`` carrying the session-level sentinel and a
  registered-contributor collection. Calling this entry point on a
  composer whose session-level payload was never composed is
  structurally refused at construction (``SessionPayloadMissingError``)
  — a sibling amendment (D7) binds a turn-level contributor against
  this surface; D8 itself registers no turn-level contributor.

The 10,000-char additionalContext cap is enforced STRUCTURALLY at
payload construction via a Pydantic ``model_validator`` — exceeding
the cap raises ``AdditionalContextCapExceededError`` before the hook
script can emit. Per the amendment plan §3 constraint 4 + the
research doc §6.1 explicit "invalid payloads cannot reach the hook
script's stdout" requirement.

Shape follows research §6.2's D7/D8 co-ownership contract: a single
contributor registry accepts both turn-level and session-level
contributors; each contributor declares its trigger kind and produces
a text payload on trigger-fire. This module ships the registry + both
entry points; D8's session-level contributor (the corpus-load gate)
lives in ``session_start_gate.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator


ADDITIONAL_CONTEXT_CAP = 10_000
"""Claude Code's documented additionalContext size cap (chars)."""


class TriggerKind(str, Enum):
    """Which hook event a contributor runs on."""

    session = "session"
    turn = "turn"


class CorpusGateState(str, Enum):
    """Session-start corpus-load sentinel.

    - ``loaded``: every baseline path present.
    - ``partial``: at least one baseline path present AND at least
      one missing.
    - ``missing``: zero baseline paths present.
    """

    loaded = "loaded"
    partial = "partial"
    missing = "missing"


# ---- errors ---------------------------------------------------------


class AdditionalContextCapExceededError(ValueError):
    """Raised at payload construction when the serialised payload
    would exceed ``ADDITIONAL_CONTEXT_CAP`` chars. Structural refusal
    per plan §3 constraint 4."""


class SessionPayloadMissingError(RuntimeError):
    """Raised when ``on_user_prompt_submit`` is invoked on a composer
    whose ``on_session_start`` was not called. Per plan AC D8.3:
    invoking the turn entry point without a session-level payload is
    not representable."""


class ContributorRegistrationError(ValueError):
    """Raised on invalid contributor registration (duplicate name,
    missing trigger-kind, etc.)."""


# ---- contributor surface --------------------------------------------


class Contributor(Protocol):
    """A contributor to the ComposedContextPayload output.

    A contributor is any callable that, given a context dict, returns
    a text block suitable for inclusion in ``additionalContext``.
    Session-level contributors run on ``on_session_start``; turn-level
    contributors run on ``on_user_prompt_submit``.

    The dict argument carries trigger-specific inputs (see the entry
    points for shape). Contributors must return a plain string.
    """

    def __call__(self, context: dict[str, Any]) -> str: ...


@dataclass(frozen=True)
class RegisteredContributor:
    """A contributor bound to the registry with a name + trigger kind."""

    name: str
    trigger_kind: TriggerKind
    fn: Callable[[dict[str, Any]], str]


# ---- payloads -------------------------------------------------------


class SessionPayload(BaseModel):
    """The session-level payload emitted on ``SessionStart``.

    Construction enforces the 10,000-char cap structurally — the
    ``_cap_guard`` validator raises
    ``AdditionalContextCapExceededError`` if the serialised
    ``additional_context_text`` exceeds the cap. Per plan §3 constraint
    4 + AC D8.5.
    """

    model_config = ConfigDict(frozen=True)

    # Baseline-corpus + session-state fields (AC D8.1).
    corpus_paths: tuple[tuple[str, bool], ...] = Field(
        default=(),
        description=(
            "Tuple of (path, present) pairs for every baseline corpus "
            "path listed in CLAUDE.md's session-start-discipline "
            "section. ``present`` is True when the path resolves to an "
            "existing file in the workspace."
        ),
    )
    amendments_in_flight: tuple[str, ...] = Field(
        default=(),
        description=(
            "Paths to in-flight amendment-*.md files in the "
            "workspace's plan directory. Empty tuple when none are "
            "in flight."
        ),
    )
    service_state: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Service-state fields for the memory sidecar, orchestrator, "
            "and any other session-level services. Values are short "
            "status strings — 'up', 'down', 'timeout', 'unknown'."
        ),
    )
    cost_headroom: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Cost-governance month-to-date spend + ceiling headroom. "
            "Empty dict when the cost-governance readout is unavailable."
        ),
    )
    corpus_gate_state: CorpusGateState = Field(
        default=CorpusGateState.loaded,
        description=(
            "Sentinel of the baseline-corpus load status. UserPromptSubmit "
            "and any turn-level contributor may observe this via the "
            "shared composer; D8 itself does not structurally refuse "
            "the session on missing corpus (graceful degradation per "
            "owner ruling D-2)."
        ),
    )
    first_run_completion: str | None = Field(
        default=None,
        description=(
            "Recent first-run completion timestamp (ISO8601) or None "
            "when no recent first-run event is recorded."
        ),
    )
    generation_marker: str = Field(
        default="session-start/1",
        description=(
            "Generation marker naming this composer's surface + "
            "schema version. Lets downstream consumers discriminate "
            "payload shapes across future amendments."
        ),
    )
    missing_paths: tuple[str, ...] = Field(
        default=(),
        description=(
            "Structured-diagnostic enumeration of baseline paths that "
            "were expected but absent. Populated iff corpus_gate_state "
            "is partial or missing (AC D8.2)."
        ),
    )
    contributor_outputs: tuple[tuple[str, str], ...] = Field(
        default=(),
        description=(
            "Session-level contributor outputs as (name, text) tuples. "
            "Order is registration order."
        ),
    )
    additional_context_text: str = Field(
        default="",
        description=(
            "Serialised form of the payload — the exact string the "
            "hook script emits as additionalContext. Validated against "
            "ADDITIONAL_CONTEXT_CAP at construction."
        ),
    )

    @model_validator(mode="after")
    def _cap_guard(self) -> "SessionPayload":
        if len(self.additional_context_text) > ADDITIONAL_CONTEXT_CAP:
            raise AdditionalContextCapExceededError(
                f"session additionalContext length "
                f"{len(self.additional_context_text)} exceeds cap "
                f"{ADDITIONAL_CONTEXT_CAP}"
            )
        return self


class TurnPayload(BaseModel):
    """The turn-level payload emitted on ``UserPromptSubmit``.

    Carries the session-level sentinel (visible to any turn-level
    contributor; D7's memory-retrieval contributor observes it) plus
    the registered-contributor outputs. D8 registers no turn-level
    contributor; the turn-payload surface exists for D7's use.

    Construction enforces the same 10,000-char cap via the ``_cap_guard``
    model_validator (AC D8.5).
    """

    model_config = ConfigDict(frozen=True)

    corpus_gate_state: CorpusGateState = Field(
        default=CorpusGateState.loaded,
        description=(
            "Sentinel inherited from the session-level payload. "
            "Contributors may branch on this value without the turn "
            "itself refusing — graceful degradation per owner ruling "
            "D-2."
        ),
    )
    missing_paths: tuple[str, ...] = Field(
        default=(),
        description=(
            "Inherited from the session-level diagnostic. Empty when "
            "corpus_gate_state == loaded."
        ),
    )
    prompt: str = Field(default="")
    resolved_component: str | None = Field(default=None)
    contributor_outputs: tuple[tuple[str, str], ...] = Field(
        default=(),
        description=(
            "Turn-level contributor outputs as (name, text) tuples. "
            "Each tuple is one registered contributor's on-turn output."
        ),
    )
    additional_context_text: str = Field(default="")

    @model_validator(mode="after")
    def _cap_guard(self) -> "TurnPayload":
        if len(self.additional_context_text) > ADDITIONAL_CONTEXT_CAP:
            raise AdditionalContextCapExceededError(
                f"turn additionalContext length "
                f"{len(self.additional_context_text)} exceeds cap "
                f"{ADDITIONAL_CONTEXT_CAP}"
            )
        return self


# ---- composer -------------------------------------------------------


SessionBuilder = Callable[[Path], dict[str, Any]]
"""Callable that produces the baseline SessionPayload field dict for a
given workspace root. Pluggable so tests can substitute a fixed shape
without spinning up the live probes. The default binding lives in
``session_start_gate.compose_session_fields``."""


@dataclass
class ComposedContextPayload:
    """The shared additionalContext composer for the primary-persona
    layer. One instance lives for one session's lifetime.

    Usage:

        composer = ComposedContextPayload(session_builder=...)
        session_payload = composer.on_session_start(workspace_root)
        # ... later, on a user prompt:
        turn_payload = composer.on_user_prompt_submit(
            prompt="...", resolved_component=None, memory_client=None
        )

    ``on_user_prompt_submit`` raises ``SessionPayloadMissingError`` if
    called before ``on_session_start`` — structural representation
    of the "invoke on never-composed session is not representable"
    constraint (AC D8.3).
    """

    session_builder: SessionBuilder
    _contributors: list[RegisteredContributor] = field(default_factory=list)
    _session_payload: SessionPayload | None = None

    # ---- registry surface -----------------------------------------

    def register(
        self,
        name: str,
        trigger_kind: TriggerKind,
        fn: Callable[[dict[str, Any]], str],
    ) -> None:
        """Register a contributor under ``name`` for ``trigger_kind``.

        Per research §6.2: a single registry accepts both turn- and
        session-level contributors. D7's memory-retrieval contributor
        will register here with ``TriggerKind.turn``; future
        amendments (cost-governance, etc.) may register session-level
        contributors alongside D8's own.

        Raises ``ContributorRegistrationError`` on duplicate name.
        """
        for existing in self._contributors:
            if existing.name == name:
                raise ContributorRegistrationError(
                    f"contributor already registered under name={name!r}"
                )
        self._contributors.append(
            RegisteredContributor(name=name, trigger_kind=trigger_kind, fn=fn)
        )

    def contributors(
        self, trigger_kind: TriggerKind | None = None
    ) -> tuple[RegisteredContributor, ...]:
        """Return the registered contributors (optionally filtered)."""
        if trigger_kind is None:
            return tuple(self._contributors)
        return tuple(c for c in self._contributors if c.trigger_kind == trigger_kind)

    # ---- entry points ---------------------------------------------

    def on_session_start(self, workspace_root: Path) -> SessionPayload:
        """Compose the session-level payload.

        Invokes the session-builder to produce the baseline field dict
        (corpus paths, amendments in flight, service state, cost
        headroom, sentinel, diagnostics). Then invokes every
        session-level contributor and folds their outputs into the
        ``contributor_outputs`` tuple. Serialises the full payload to
        ``additional_context_text`` and constructs a validated
        ``SessionPayload`` — the Pydantic validator enforces the cap.

        Caches the payload on the composer so the turn entry point
        can inherit the session-level sentinel (AC D8.3).
        """
        fields = self.session_builder(workspace_root)
        contributor_outputs: list[tuple[str, str]] = []
        for c in self._contributors:
            if c.trigger_kind != TriggerKind.session:
                continue
            try:
                out = c.fn(dict(fields))
            except Exception as exc:  # noqa: BLE001 — contributor sandbox
                out = f"[contributor {c.name} raised: {type(exc).__name__}]"
            contributor_outputs.append((c.name, out))

        text = _serialise_session(fields, contributor_outputs)
        payload = SessionPayload(
            **fields,
            contributor_outputs=tuple(contributor_outputs),
            additional_context_text=text,
        )
        self._session_payload = payload
        return payload

    def on_user_prompt_submit(
        self,
        prompt: str,
        resolved_component: str | None = None,
        memory_client: Any = None,
    ) -> TurnPayload:
        """Compose the turn-level payload.

        Refuses (``SessionPayloadMissingError``) if ``on_session_start``
        has not been called on this composer instance. Otherwise walks
        the turn-level contributor set, folds their outputs into the
        returned ``TurnPayload``, and serialises to
        ``additional_context_text`` under the 10 k-char cap.

        The session-level sentinel + diagnostic are propagated into
        the turn payload so contributors (and downstream consumers)
        observe corpus-load state per-turn without needing a separate
        channel. Per plan AC D8.2: "a subsequent on_user_prompt_submit
        invocation on the same session observes the missing / partial
        sentinel via the shared composer".
        """
        if self._session_payload is None:
            raise SessionPayloadMissingError(
                "on_user_prompt_submit invoked before on_session_start; "
                "the shared composer refuses to construct a turn "
                "payload without a session-level payload in scope."
            )

        context: dict[str, Any] = {
            "prompt": prompt,
            "resolved_component": resolved_component,
            "memory_client": memory_client,
            "session_payload": self._session_payload,
        }
        contributor_outputs: list[tuple[str, str]] = []
        for c in self._contributors:
            if c.trigger_kind != TriggerKind.turn:
                continue
            try:
                out = c.fn(dict(context))
            except Exception as exc:  # noqa: BLE001 — contributor sandbox
                out = f"[contributor {c.name} raised: {type(exc).__name__}]"
            contributor_outputs.append((c.name, out))

        text = _serialise_turn(
            prompt=prompt,
            resolved_component=resolved_component,
            corpus_gate_state=self._session_payload.corpus_gate_state,
            missing_paths=self._session_payload.missing_paths,
            contributor_outputs=contributor_outputs,
        )
        return TurnPayload(
            corpus_gate_state=self._session_payload.corpus_gate_state,
            missing_paths=self._session_payload.missing_paths,
            prompt=prompt,
            resolved_component=resolved_component,
            contributor_outputs=tuple(contributor_outputs),
            additional_context_text=text,
        )

    # ---- introspection ---------------------------------------------

    @property
    def session_payload(self) -> SessionPayload | None:
        """The last session-level payload composed on this instance,
        or None if ``on_session_start`` has not been called yet."""
        return self._session_payload


# ---- serialisation --------------------------------------------------


def _serialise_session(
    fields: dict[str, Any], contributor_outputs: list[tuple[str, str]]
) -> str:
    """Produce the text emitted as SessionStart additionalContext.

    Format is plain text with labelled sections — matches Claude Code's
    text-shaped hook contract (research doc §5.1). The exact shape is
    stable but not load-bearing for any AC; ACs check structural
    membership (fields present / paths listed / sentinel value /
    length under cap), not textual equality.
    """
    lines: list[str] = []
    lines.append(f"[pos-v2 session-start / {fields.get('generation_marker', '?')}]")
    gate = fields.get("corpus_gate_state", "?")
    gate_str = gate.value if isinstance(gate, CorpusGateState) else str(gate)
    lines.append(f"corpus_gate_state: {gate_str}")

    corpus_paths = fields.get("corpus_paths", ())
    if corpus_paths:
        lines.append("corpus_paths:")
        for path, present in corpus_paths:
            marker = "present" if present else "MISSING"
            lines.append(f"  - [{marker}] {path}")

    missing = fields.get("missing_paths", ())
    if missing:
        lines.append("missing_corpus_paths (diagnostic):")
        for p in missing:
            lines.append(f"  - {p}")

    amendments = fields.get("amendments_in_flight", ())
    if amendments:
        lines.append("amendments_in_flight:")
        for a in amendments:
            lines.append(f"  - {a}")

    service_state = fields.get("service_state", {})
    if service_state:
        lines.append("service_state:")
        for k in sorted(service_state.keys()):
            lines.append(f"  - {k}: {service_state[k]}")

    cost_headroom = fields.get("cost_headroom", {})
    if cost_headroom:
        lines.append("cost_headroom:")
        for k in sorted(cost_headroom.keys()):
            lines.append(f"  - {k}: {cost_headroom[k]}")

    first_run = fields.get("first_run_completion")
    if first_run is not None:
        lines.append(f"first_run_completion: {first_run}")

    if contributor_outputs:
        lines.append("contributor_outputs:")
        for name, text in contributor_outputs:
            # Guard: prefix each contributor's block with its name so
            # consumers can discriminate without parsing the text back.
            lines.append(f"  [{name}]")
            for ln in text.splitlines() or [""]:
                lines.append(f"    {ln}")

    return "\n".join(lines)


def _serialise_turn(
    *,
    prompt: str,
    resolved_component: str | None,
    corpus_gate_state: CorpusGateState,
    missing_paths: tuple[str, ...],
    contributor_outputs: list[tuple[str, str]],
) -> str:
    """Produce the text emitted as UserPromptSubmit additionalContext.

    Includes the session-level sentinel (so every turn carries a
    visible corpus-gate state) plus registered contributor outputs in
    registration order.
    """
    lines: list[str] = []
    lines.append("[pos-v2 user-prompt-submit]")
    lines.append(f"corpus_gate_state: {corpus_gate_state.value}")
    if resolved_component:
        lines.append(f"resolved_component: {resolved_component}")
    if missing_paths:
        lines.append("missing_corpus_paths (diagnostic):")
        for p in missing_paths:
            lines.append(f"  - {p}")
    # AC.MPF.4 (amendment #95): skip contributors whose text is
    # empty (or whitespace-only) so the UPS hook attachment doesn't
    # carry whitespace-padded contributor headers. Symmetric with
    # the ``if missing_paths:`` and ``if resolved_component:``
    # guards above. The ``contributor_outputs:`` header itself is
    # also skipped when no contributor produced text — pre-amendment
    # this rendered an empty header followed by indent-only lines.
    if contributor_outputs:
        rendered_any = False
        for name, text in contributor_outputs:
            if not text.strip():
                continue
            if not rendered_any:
                lines.append("contributor_outputs:")
                rendered_any = True
            lines.append(f"  [{name}]")
            for ln in text.splitlines():
                lines.append(f"    {ln}")
    return "\n".join(lines)
