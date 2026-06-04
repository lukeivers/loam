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

"""Session-start + user-prompt-submit emitters (amendment #46).

This module is the runtime call site for the substrate built across
amendments #32 (D8 composer), #33 (D7 memory consumer), #35 (onboarding
contributor), #40 (tracker context contributor), and #45
(``extra_inner_hooks`` registry on ``hands-off-lifecycle``). Until #46
the substrate existed but was never invoked outside tests; #46 builds
the composer, registers the contributors, and exposes two CLI helpers
that hands-off-lifecycle wires into Claude Code's SessionStart and
UserPromptSubmit hooks.

Public API:

  - :func:`build_session_composer` — constructs a
    ``ComposedContextPayload`` and registers tracker-context, starter-
    pending (when a starter contract is loadable), and memory-retrieval
    (when a memory client is supplied) contributors.
  - :func:`emit_session_start_context` — invokes the composer's
    ``on_session_start`` entry point and returns the rendered
    additionalContext text. Fail-soft on every error path.
  - :func:`emit_user_prompt_submit_context` — invokes
    ``on_user_prompt_submit`` against a freshly-composed session
    payload and returns the rendered turn additionalContext text.
    Fail-soft.
  - :func:`build_persona_session_start_inner_hook` — returns the
    inner-hook dict ``hands-off-lifecycle`` composes into the
    SessionStart envelope via amendment #45's ``extra_inner_hooks``
    parameter.
  - :func:`build_persona_user_prompt_submit_inner_hook` — same shape
    for the UserPromptSubmit envelope (consumed by #46's new
    ``merge_user_prompt_submit`` surface in ``first_run_settings.py``).
  - :func:`cli_session_start` / :func:`cli_user_prompt_submit` — CLI
    entry points. Both return 0 unconditionally (AC46.4 fail-soft —
    a non-zero exit blocks Claude Code's hook fan-out).

Per ODD §2.5 every code path traces back to AC46.1–AC46.S. The fail-
soft branches are explicitly criterion-backed (AC46.4); no defensive
``if`` without an AC anchor.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

from .context_composer import (
    ADDITIONAL_CONTEXT_CAP,
    ComposedContextPayload,
    TriggerKind,
)
from .memory_consumer import (
    MemoryClient,
    register_memory_retrieval,
    resolve_workspace_slug,
)
from .onboarding import build_starter_pending_contributor
from .session_start_gate import compose_session_fields
from .tracker_context import register_tracker_context


# ---- composer construction -----------------------------------------


MemoryClientFactory = Callable[[Path], MemoryClient | None]
"""Callable that returns a MemoryClient for a workspace, or None when
no client is available. The default factory returns None — pre-#47 the
production path has no live MCP client; the memory-retrieval contributor
is simply not registered (graceful empty per AC46.2). Tests inject a
factory returning a FakeMemoryClient to exercise the populated path."""


def _default_memory_client_factory(workspace_root: Path) -> MemoryClient | None:
    """Default production-side memory-client factory.

    **M-FBM (memory-substrate pivot, 2026-05-01).** The runtime
    retrieval path no longer instantiates an MCP-backed client. The
    file-based memory substrate is registered directly inside
    :func:`build_session_composer` via
    :func:`register_file_memory_retrieval`; this factory is preserved
    as a typed surface for tests + M-GMP's future MCP provider but
    returns ``None`` in production at v0.1.0.

    Returning ``None`` here causes :func:`build_session_composer` to
    skip the legacy MCP-client retrieval path; the file-based
    contributor is registered unconditionally via the dedicated
    ``register_file_memory_retrieval`` call. AC.MFBM.5: zero MCP
    instantiation in the runtime path. AC46.2 (graceful-empty when
    no client) remains the structural envelope.
    """
    return None


def build_session_composer(
    workspace_root: Path,
    *,
    memory_client_factory: MemoryClientFactory | None = None,
    loaded_persona: Any | None = None,
    register_tracker: bool = True,
) -> ComposedContextPayload:
    """Construct a ComposedContextPayload and register the persona-
    layer's contributors.

    The returned composer carries (per AC46.1):

      - ``tracker-context`` (TriggerKind.session) when ``register_tracker``
        is True (default). Skipped iff the caller suppresses tracker
        registration (test cases that exercise other contributors in
        isolation).
      - ``starter-pending`` (TriggerKind.session) when ``loaded_persona``
        is supplied OR when the workspace's primary persona loads
        successfully. Skipped on persona-load failure (AC46.4 fail-soft;
        D-build.5).
      - ``memory-retrieval`` (TriggerKind.turn) when
        ``memory_client_factory`` returns a non-None client. Skipped
        otherwise (AC46.2 graceful empty / D-build.4).

    The composer is constructed with the canonical ``compose_session_
    fields`` builder (#32 D8).
    """
    composer = ComposedContextPayload(session_builder=compose_session_fields)

    if register_tracker:
        try:
            register_tracker_context(composer, workspace_root=workspace_root)
        except Exception:  # noqa: BLE001 — AC46.4 fail-soft on registration
            # Tracker registration's lazy-import surface failed (e.g.,
            # objective-tracker not installed in this venv). The
            # contributor is simply not registered; the SessionStart
            # payload omits the tracker-context block. Per AC40.3 the
            # contributor itself is fail-soft on tracker errors at
            # invocation time; this branch covers the rarer
            # registration-time failure (e.g. import-time exception).
            pass

    persona = loaded_persona
    if persona is None:
        persona = _try_load_primary_persona(workspace_root)
    if persona is not None:
        try:
            contributor = build_starter_pending_contributor(persona)
            composer.register(
                name="starter-pending",
                trigger_kind=TriggerKind.session,
                fn=contributor,
            )
        except Exception:  # noqa: BLE001 — AC46.4 fail-soft
            # Contributor build/registration failed (e.g. malformed
            # contract). The SessionStart payload omits the starter-
            # pending block; the session proceeds.
            pass

    factory = memory_client_factory or _default_memory_client_factory
    try:
        client = factory(workspace_root)
    except Exception:  # noqa: BLE001 — AC46.4 fail-soft
        client = None
    if client is not None:
        # Test path (or future M-GMP graphiti provider): inject an
        # MCP-backed client; legacy retrieval contributor wins. Pre-
        # M-FBM this was the production path; post-M-FBM the
        # production factory returns None and the file-based
        # contributor below fires instead. AC.MFBM.5 holds: zero
        # MCP instantiation in production.
        try:
            slug = resolve_workspace_slug(workspace_root)
            register_memory_retrieval(
                composer,
                memory_client=client,
                workspace_slug=slug,
                workspace_root=workspace_root,
            )
        except Exception:  # noqa: BLE001 — AC46.2 graceful empty
            pass
    else:
        # M-FBM production path, CONSOLIDATED (AC-FBM-CON-1): register the
        # GATED keep-pace turn contributor instead of the ungated
        # file-based ``register_file_memory_retrieval``. The gated path runs
        # ``keep_pace.retrieval.retrieve`` — rank-normalize + rule-weight/
        # hard-floor + SALIENCE GATE — and surfaces corpus/rules AND episodes
        # from the SAME live store ``<workspace>/workspace/.loam/memory/...``,
        # junk-gated (task-notification / empty-channel / bare-ack episodes
        # dropped). The contributor keeps the name ``memory-retrieval`` so no
        # downstream consumer keying on the block name changes. The retired
        # ungated ``register_file_memory_retrieval`` / ``build_file_memory_
        # retrieval_contributor`` / ``_render_retrieval`` stay DEFINED and
        # exported (the MCP client branch above + the file-memory tests still
        # use them) — only this LIVE registration is repointed.
        # AC-FBM-CON-2 fail-closed: any boundary error inside the contributor
        # returns an empty string; the turn proceeds. AC46.2 graceful-empty.
        try:
            from .keep_pace.retrieval import (  # noqa: WPS433
                register_keep_pace_turn_contributor,
            )

            slug = resolve_workspace_slug(workspace_root)
            register_keep_pace_turn_contributor(
                composer,
                workspace_root=workspace_root,
                workspace_slug=slug,
            )
        except Exception:  # noqa: BLE001 — AC46.2 graceful empty
            # Slug resolution / contributor registration failed; the turn
            # payload omits the retrieval block. AC46.2 holds.
            pass

        # WORK-STREAMS (Increment 1, AC.WS.SURFACE.1) — register the
        # cross-cutting streams contributor at TriggerKind.turn. This SUBSUMES
        # the Slice-D project-state block (D4 / WMS-D7): the streams block IS
        # the per-turn ground-truth STATE surface, now organized by stream —
        # ONE block, not two (the anti-bloat constraint, F2 #1). For a stream
        # bound to >=1 FBM-registered project (loam->loam, cairn->cairn,
        # litrpg->litrpg) it composes a FRESH ``derive_project_state`` call
        # (Slice C, TTL-cached) — derived live, never stored-stale; an unbound
        # stream surfaces a staleness-based next-action marked "no ground-truth
        # project bound" (never a faked STATE). Honors deep-dive (full + mute
        # others' nudges) / pause (drop + collapse) / collapse-on-overflow
        # within Slice D's hard char-cap. The deviation->#71 fail-soft seam
        # rides inside the surfacer. The bare ``register_project_state_
        # contributor`` stays DEFINED + exported (Slice D tests still use it) —
        # only this LIVE registration is repointed to the streams surfacer.
        # Registered fail-soft (AC46.2 graceful-empty) — a registration-time
        # error simply omits the block.
        try:
            from .keep_pace.work_streams_surface import (  # noqa: WPS433
                register_work_streams_contributor,
            )

            register_work_streams_contributor(composer)
        except Exception:  # noqa: BLE001 — AC46.2 graceful empty
            pass

        # WMS increment 2 (AC.PROJ.* / AC.WMS2.LIVE.1) — register the
        # PROJECTS lens at TriggerKind.turn alongside the streams lens. A
        # SEPARATE named block: the projects + streams lenses are two
        # distinct VIEWS over the ONE work-item store (the architecture's
        # multi-lens-over-one-model insight). The projects lens filters
        # belongs-to-project -> groups -> sorts by priority -> renders a
        # capped block via the Slice-D discipline, deriving live STATE per
        # FBM-bound project (loam/cairn/litrpg) and honestly marking the
        # unbound ones. Registered fail-soft (AC46.2 graceful-empty) — a
        # registration-time error simply omits the block.
        try:
            from .keep_pace.projects import (  # noqa: WPS433
                register_projects_contributor,
            )

            register_projects_contributor(composer)
        except Exception:  # noqa: BLE001 — AC46.2 graceful empty
            pass

        # WMS increment 4 (AC.SURF.* / AC.WMS4.LIVE.1) — register the
        # RELATIONAL lens at TriggerKind.turn alongside the projects +
        # streams lenses. A SEPARATE named block: it turns the inc-2 edge
        # graph + its unblocked_next/waiting_on_other/trace_to_root
        # queries into the answers that make the graph valuable — the
        # PRIORITIZED next-thing + its transparent reason (prioritize.py),
        # what's blocked + on what, what's waiting on ME vs on OTHERS, and
        # the decomposition tree — in ONE concise capped fail-soft block
        # (the Slice-D discipline). The store is CONSUMED via its existing
        # READ API, never modified (D-PRI.1). Registered fail-soft
        # (AC46.2 graceful-empty) — a registration-time error simply omits
        # the block.
        try:
            from .keep_pace.relational import (  # noqa: WPS433
                register_relational_contributor,
            )

            register_relational_contributor(composer)
        except Exception:  # noqa: BLE001 — AC46.2 graceful empty
            pass

    # AC.MSC.2 (Gap A part b) — register the session-start
    # active-thread contributor at TriggerKind.session so a fresh
    # session reconstructs the most-recent active working thread from
    # durably-stored memory WITHOUT any session-end hook. Composed on
    # the existing SessionStart registry (Lens 1 — no new hook
    # machinery). Independent of the turn-level retrieval block above:
    # the active-thread digest is read at session-start, the retrieval
    # block at turn-time. Fail-soft on registration (AC.MSC.5) — a
    # registration failure simply omits the block; the session
    # proceeds.
    try:
        from .active_thread import (  # noqa: WPS433
            build_active_thread_contributor,
        )
        from .file_memory import (  # noqa: WPS433
            FileMemoryStore,
            memory_dir_for_workspace,
        )

        slug = resolve_workspace_slug(workspace_root)
        store = FileMemoryStore(
            memory_dir=memory_dir_for_workspace(workspace_root)
        )
        active_thread_fn = build_active_thread_contributor(
            store,
            workspace_root=workspace_root,
            workspace_slug=slug,
        )
        composer.register(
            name="active-thread",
            trigger_kind=TriggerKind.session,
            fn=active_thread_fn,
        )
    except Exception:  # noqa: BLE001 — AC.MSC.5 fail-soft
        # Slug resolution / store construction / contributor
        # registration failed; the SessionStart payload omits the
        # active-thread block. The session proceeds (defence-in-depth:
        # AC.MSC.3's named-thread corpus path still surfaces the
        # live-thread digest).
        pass

    return composer


def _try_load_primary_persona(workspace_root: Path) -> Any | None:
    """Attempt to load the workspace's primary persona; return None
    on any failure. AC46.4 fail-soft + D-build.5.

    The lazy import keeps the loader off this module's import-time
    surface so test fixtures that don't need a persona don't have to
    pay the loader's import cost.
    """
    try:
        from .loader import (  # noqa: WPS433
            PersonaDirectoryNotFoundError,
            PersonaLoader,
            PersonaValidationError,
        )
    except Exception:  # noqa: BLE001
        return None
    try:
        loader = PersonaLoader(
            workspace_root, enforce_no_personas_in_core=False
        )
        return loader.primary()
    except (PersonaDirectoryNotFoundError, PersonaValidationError):
        return None
    except Exception:  # noqa: BLE001 — AC46.4 fail-soft
        return None


# ---- emit functions -------------------------------------------------


def emit_session_start_context(
    workspace_root: Path,
    *,
    memory_client_factory: MemoryClientFactory | None = None,
    loaded_persona: Any | None = None,
) -> str:
    """Compose the session-level payload and return its rendered
    additionalContext text. Fail-soft per AC46.4.

    Returns the empty string on any failure path (composer
    construction failure, session-builder exception, payload
    validation failure). AC46.3's diagnostic / sentinel emerges
    naturally from ``compose_session_fields`` populating
    ``corpus_gate_state`` + ``missing_paths`` when the baseline corpus
    is incomplete; the ``_serialise_session`` helper renders both into
    the textual payload. AC46.1 is satisfied when the composed payload
    serialises without exception.
    """
    try:
        composer = build_session_composer(
            workspace_root,
            memory_client_factory=memory_client_factory,
            loaded_persona=loaded_persona,
        )
        payload = composer.on_session_start(workspace_root)
        text = payload.additional_context_text
        # Defensive: re-check the cap. The composer's Pydantic
        # validator already refuses an over-cap payload at construction
        # (raising AdditionalContextCapExceededError); this branch
        # never fires in normal operation. Should the structural
        # refusal evolve, the emit-time check ensures Claude Code never
        # sees an over-cap stdout.
        if len(text) > ADDITIONAL_CONTEXT_CAP:
            return ""
        return text
    except Exception:  # noqa: BLE001 — AC46.4 fail-soft
        return ""


def emit_user_prompt_submit_context(
    workspace_root: Path,
    prompt: str,
    *,
    memory_client_factory: MemoryClientFactory | None = None,
    loaded_persona: Any | None = None,
) -> str:
    """Compose the turn-level payload for a user prompt and return
    its rendered additionalContext text. Fail-soft per AC46.4.

    The composer requires a session-level payload before
    ``on_user_prompt_submit`` will compose (D8.3 structural refusal).
    This function builds the composer, runs ``on_session_start``
    once to seed the session payload, then ``on_user_prompt_submit``
    to compose the turn payload. Both calls are wrapped fail-soft.

    AC46.2 graceful-empty when the memory contributor is not
    registered (no factory / factory returns None) or when its
    underlying memory client raises (the contributor itself is fail-
    closed per AC-D7.7).
    """
    try:
        composer = build_session_composer(
            workspace_root,
            memory_client_factory=memory_client_factory,
            loaded_persona=loaded_persona,
        )
        composer.on_session_start(workspace_root)
        turn_payload = composer.on_user_prompt_submit(
            prompt=prompt,
            resolved_component=None,
            memory_client=None,
        )
        text = turn_payload.additional_context_text
        if len(text) > ADDITIONAL_CONTEXT_CAP:
            return ""
        return text
    except Exception:  # noqa: BLE001 — AC46.4 fail-soft
        return ""


# ---- inner-hook builders --------------------------------------------


def build_persona_session_start_inner_hook(loam_root: Path) -> dict:
    """Return the inner-hook dict the SessionStart envelope composes
    against the persona's ``session-start`` CLI subcommand.

    Used by ``hands-off-lifecycle/hooks/first_run_helper.py``'s
    ``_persona_inner_hooks`` (AC46.5). Composed via amendment #45's
    ``extra_inner_hooks`` parameter on ``build_first_run_stanza`` /
    ``build_supervisor_stanza``. Timeout 5s matches the dev-mode
    session-start emit timeout precedent (D-build.7) — the
    session-start work is bounded by
    service probes (~250ms each), filesystem reads, and a single
    SQLite query.
    """
    loam_root = Path(loam_root)
    python = loam_root / ".venv" / "bin" / "python"
    return {
        "type": "command",
        "command": f"{python} -m loam.primary_persona.cli session-start",
        "async": False,
        "timeout": 5,
    }


def build_persona_stop_inner_hook(loam_root: Path) -> dict:
    """Return the inner-hook dict the Stop envelope composes against
    the persona's ``stop`` CLI subcommand.

    Amendment #48 (AC.M.11): used by ``hands-off-lifecycle/hooks/
    first_run_helper.py``'s ``_persona_stop_stanza``. Single-
    contributor for now (plan §9 explicit out-of-scope: multi-
    contributor Stop registry is a future amendment analogous to
    amendment #45's SessionStart generalisation).

    Timeout 5s per D6 — the hook detaches the actual ``add_episode``
    write to a background subprocess and returns in milliseconds;
    5s is the precedent from the dev-mode session-start emit +
    persona session-start + user-prompt-submit timeouts and is
    generous for the work the Stop hook
    itself performs (transcript walk + per-turn-id read/write +
    Popen).
    """
    loam_root = Path(loam_root)
    python = loam_root / ".venv" / "bin" / "python"
    return {
        "type": "command",
        "command": f"{python} -m loam.primary_persona.cli stop",
        "async": False,
        "timeout": 5,
    }


def build_persona_user_prompt_submit_inner_hook(loam_root: Path) -> dict:
    """Return the inner-hook dict the UserPromptSubmit envelope
    composes against the persona's ``user-prompt-submit`` subcommand.

    Used by ``hands-off-lifecycle/hooks/first_run_helper.py``'s
    ``_persona_user_prompt_submit_stanza`` (AC46.5). Single-contributor
    for now (AC46.6 defers multi-contributor generalisation). Timeout
    5s — bounded by the soft-cap on memory-retrieval (5 results, 1600
    char cap) and a single HTTP call to local memory-graphiti.
    """
    loam_root = Path(loam_root)
    python = loam_root / ".venv" / "bin" / "python"
    return {
        "type": "command",
        "command": f"{python} -m loam.primary_persona.cli user-prompt-submit",
        "async": False,
        "timeout": 5,
    }


# ---- CLI helpers ----------------------------------------------------


def cli_session_start(workspace_root: Path | None = None) -> int:
    """Run ``emit_session_start_context`` and print to stdout.

    AC46.4 fail-soft contract: the function returns 0 on every path —
    a non-zero exit would block Claude Code's SessionStart fan-out;
    the empty-payload outcome satisfies "session proceeds".

    Claude Code passes a JSON envelope on stdin to SessionStart hooks
    too (session_id, source, etc.), but the persona emit consumes none
    of those fields — workspace_root is the only input, resolved from
    the CWD (which Claude Code sets to the workspace root before
    firing the hook).
    """
    root = workspace_root if workspace_root is not None else Path.cwd()
    try:
        payload = emit_session_start_context(root)
    except Exception:  # noqa: BLE001 — defensive AC46.4
        payload = ""
    if payload:
        sys.stdout.write(payload)
        if not payload.endswith("\n"):
            sys.stdout.write("\n")
    return 0


def cli_user_prompt_submit(workspace_root: Path | None = None) -> int:
    """Run ``emit_user_prompt_submit_context`` against a prompt read
    from stdin and print the result to stdout.

    AC46.2 + AC46.4 fail-soft. Claude Code's UserPromptSubmit hook
    contract passes a JSON envelope on stdin; the ``prompt`` field
    carries the user's text. D-build.3 confirms the channel.

    The CLI is graceful on every failure mode:

      - stdin is empty / not JSON → empty payload, exit 0.
      - JSON has no ``prompt`` field or the field is empty → empty
        payload, exit 0 (matches AC46.2 graceful-empty when the
        memory contributor produces no output).
      - Composer construction or emit fails → empty payload (handled
        by ``emit_user_prompt_submit_context``), exit 0.
    """
    root = workspace_root if workspace_root is not None else Path.cwd()
    prompt = ""
    try:
        raw = sys.stdin.read()
    except Exception:  # noqa: BLE001 — defensive AC46.4
        raw = ""
    if raw.strip():
        try:
            envelope = json.loads(raw)
            if isinstance(envelope, dict):
                value = envelope.get("prompt", "")
                if isinstance(value, str):
                    prompt = value
        except (ValueError, TypeError):
            # stdin was not JSON; treat as no-prompt and emit empty
            # payload. Per AC46.2 graceful-empty.
            prompt = ""
    if not prompt.strip():
        return 0
    try:
        payload = emit_user_prompt_submit_context(root, prompt)
    except Exception:  # noqa: BLE001 — defensive AC46.4
        payload = ""
    if payload:
        sys.stdout.write(payload)
        if not payload.endswith("\n"):
            sys.stdout.write("\n")
    return 0
