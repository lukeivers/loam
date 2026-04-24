"""Memory-consumer wiring for the primary-persona layer (D7).

Amendment #33 registers a turn-level memory-retrieval contributor on
the shared ``ComposedContextPayload`` composer that D8 shipped. It
also dispatches a per-turn aggregated episode write to memory-system
without blocking the interactive channel.

The consumer surface is composed of four collaborating primitives:

- ``MemoryClient``: narrow Protocol bound against amendment #24's
  MCP tool surface (``add_episode``, ``search``). The persona layer
  never imports memory-system source; the Protocol is sufficient.
- ``resolve_workspace_slug(workspace_root)``: pure-function basename
  sanitisation matching the ``workspace-bootstrap`` convention. Used
  both as the ``group_id`` on writes and the ``group_ids`` list
  entry on reads (AC-D7.4).
- ``TurnAggregator``: bundles user message + persona reply into one
  episode per user-turn and fire-and-forget schedules the write via
  ``asyncio.create_task`` (AC-D7.2, AC-D7.3).
- ``build_memory_retrieval_contributor``: factory producing the
  callable that registers against the composer at
  ``TriggerKind.turn``; fires a ``search`` and returns a text
  payload. Fail-closed on every memory-system error (AC-D7.7).

Per amendment plan §3 constraint 5, the write path MUST be
structurally non-blocking. ``asyncio.create_task`` is the cheapest
non-blocking primitive compatible with the plan's "no new
orchestrator / scope-of-work source" fence; the task runs
concurrently with the interactive turn and terminates whenever
``add_episode`` completes (including the empirical 113 s
extraction). Failed writes surface as OTel warnings via the persona
layer's existing D9 observability surface; a subsequent awareness-
block category could pick them up in future work.
"""

from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable, Protocol

from .context_composer import TriggerKind


# ---- exceptions -----------------------------------------------------


class WorkspaceSlugUnrepresentableError(ValueError):
    """Raised when the workspace basename cannot be sanitised to a
    non-empty launchd-safe slug. Mirrors the sibling error in
    ``workspace-bootstrap``; any change to sanitisation semantics
    must keep the two primitives in parity (parity-tested in
    ``tests/test_D7_4_group_id_is_workspace_slug.py``)."""


# ---- MemoryClient protocol ------------------------------------------


class MemoryClient(Protocol):
    """Narrow surface the persona layer calls on memory-system.

    Binds against amendment #24's MCP tool signatures verbatim
    (``memory-system/src/service.py`` ``_impl_add_episode`` /
    ``_impl_search``). The persona never imports memory-system source;
    callers supply a concrete implementation (live MCP client in
    production; FakeMemoryClient in tests).
    """

    async def add_episode(
        self,
        *,
        name: str,
        body: str,
        source_description: str,
        reference_time: datetime,
        source: str,
        group_id: str,
    ) -> dict[str, Any]: ...

    async def search(
        self,
        *,
        query: str,
        group_ids: list[str] | None,
        num_results: int,
        center_node_uuid: str | None,
    ) -> dict[str, Any]: ...


# ---- workspace-slug primitive ---------------------------------------


_SLUG_ALLOWED_RE = re.compile(r"[^a-z0-9-]+")
_SLUG_COLLAPSE_RE = re.compile(r"-+")


def resolve_workspace_slug(workspace_root: Path | str) -> str:
    """Return a stable slug for ``workspace_root`` using the same
    basename-sanitisation convention as
    ``workspace_bootstrap.adapters.first_run_scaffold.workspace_slug``.

    The persona layer already holds ``workspace_root: Path`` as its
    existing workspace-identity primitive. This function derives the
    slug from it via the documented convention — it is not a new
    identity surface; it is reuse of the existing convention. Parity
    with the canonical is verified by an AC-D7.4 test that imports
    ``workspace_bootstrap.adapters.first_run_scaffold.workspace_slug``
    under the test-fixture admission in the governing plan §3
    constraint 2.
    """
    basename = Path(workspace_root).name
    lowered = basename.lower()
    slug = _SLUG_ALLOWED_RE.sub("-", lowered)
    slug = _SLUG_COLLAPSE_RE.sub("-", slug)
    slug = slug.strip("-")
    if not slug:
        raise WorkspaceSlugUnrepresentableError(
            f"workspace-slug-unrepresentable:{basename!r}"
        )
    return slug


# ---- turn aggregation + write dispatch ------------------------------


# Soft cap on the memory-retrieval contribution (characters). Research
# §4.3 set this at 200–400 tokens (~800–1600 chars); we pin at 1600 so
# the combined turn payload (awareness block + retrieval block) stays
# well inside the composer's structural 10 000-char refusal (AC-D7.6).
# The composer's Pydantic ``_cap_guard`` remains the authoritative
# structural refusal; this soft cap is proactive trimming.
MEMORY_RETRIEVAL_CHAR_CAP = 1600


@dataclass
class TurnAggregator:
    """Bundles a user message + the persona reply for one user↔AI
    turn into one aggregated episode (AC-D7.2) and schedules a
    fire-and-forget async write (AC-D7.3).

    Users call ``close_turn`` at turn-close; the aggregator schedules
    ``memory_client.add_episode(group_id=workspace_slug, ...)`` via
    ``asyncio.create_task`` on the caller's running loop. The task
    is returned so tests can await it; production callers discard it.
    """

    memory_client: MemoryClient
    workspace_slug: str
    source_description: str = "primary-persona turn"
    # Track outstanding tasks so tests can await them and the process
    # doesn't orphan them on shutdown. The tuple wrapper is a defensive
    # copy; production code does not inspect this.
    _pending: list[asyncio.Task[Any]] = field(default_factory=list)

    def close_turn(
        self,
        *,
        turn_id: str,
        user_message: str,
        persona_reply: str,
        reference_time: datetime | None = None,
    ) -> asyncio.Task[Any]:
        """Schedule a single aggregated episode write for this turn.

        The returned task is fire-and-forget from the caller's
        perspective (production code does not await it); the task
        runs concurrently with subsequent turns. AC-D7.3 verifies the
        interactive path is not blocked on the write. AC-D7.2 verifies
        exactly one ``add_episode`` call per turn.
        """
        ref = reference_time or datetime.now(timezone.utc)
        body = _compose_episode_body(user_message=user_message, persona_reply=persona_reply)
        coro = self.memory_client.add_episode(
            name=f"turn/{turn_id}",
            body=body,
            source_description=self.source_description,
            reference_time=ref,
            source="message",
            group_id=self.workspace_slug,
        )
        task = asyncio.create_task(coro, name=f"memory-write/{turn_id}")
        self._pending.append(task)
        # Opportunistic cleanup — drop done tasks so _pending doesn't
        # grow unboundedly.
        self._pending = [t for t in self._pending if not t.done()]
        return task

    def pending_tasks(self) -> tuple[asyncio.Task[Any], ...]:
        """Return currently-outstanding write tasks (for tests)."""
        return tuple(t for t in self._pending if not t.done())


def _compose_episode_body(*, user_message: str, persona_reply: str) -> str:
    """Shape a single episode body from one user-turn's contents.

    Plain-text with labelled blocks; graphiti's entity extraction
    tolerates this shape comfortably (amendment #24 research). The
    exact formatting is method, not AC — AC-D7.2 measures structural
    membership (body contains both the user message and the persona
    reply), not exact text.
    """
    return (
        f"[user]\n{user_message.strip()}\n\n"
        f"[persona]\n{persona_reply.strip()}\n"
    )


# ---- memory-retrieval contributor -----------------------------------


@dataclass
class MemoryRetrievalConfig:
    """Per-composer config for the turn-level memory-retrieval
    contributor. Decoupling from the build function simplifies test
    wiring and keeps the contributor callable captureable."""

    memory_client: MemoryClient
    workspace_slug: str
    num_results: int = 5  # research §4.3 recipe
    char_cap: int = MEMORY_RETRIEVAL_CHAR_CAP


def build_memory_retrieval_contributor(
    config: MemoryRetrievalConfig,
) -> Callable[[dict[str, Any]], str]:
    """Return the callable registered on
    ``ComposedContextPayload.register(name="memory-retrieval",
    trigger_kind=TriggerKind.turn, fn=<returned callable>)``.

    On every ``on_user_prompt_submit`` the returned callable issues
    one ``search`` against memory-system with
    ``group_ids=[workspace_slug]`` (AC-D7.4), gathers the top-N
    results, and returns a plain-text rendering under the soft
    character cap (AC-D7.6). On any exception raised by the memory
    boundary, returns an empty string — fail-closed per plan §3
    constraint 8 / AC-D7.7.
    """

    def contributor(context: dict[str, Any]) -> str:
        prompt = str(context.get("prompt", ""))
        if not prompt.strip():
            return ""
        try:
            result = _run_async(
                config.memory_client.search(
                    query=prompt,
                    group_ids=[config.workspace_slug],
                    num_results=config.num_results,
                    center_node_uuid=None,
                )
            )
        except Exception:
            # Fail-closed per AC-D7.7 — any boundary error, regardless
            # of cause (connection refused, HTTP 5xx, timeout, garbage
            # response, etc.), yields an empty retrieval block and the
            # turn proceeds.
            return ""
        return _render_retrieval(result, cap=config.char_cap)

    return contributor


def _run_async(coro: Awaitable[Any]) -> Any:
    """Drive a coroutine to completion from a synchronous call site.

    The composer's contributor callables are synchronous (see
    ``Contributor`` Protocol in ``context_composer.py``). The memory
    client's ``search`` is async (binds against the MCP tool surface).
    We bridge via ``asyncio.new_event_loop()`` when no loop is
    running, or ``asyncio.run_coroutine_threadsafe`` when we are on
    a loop-less thread. Tests exercise the synchronous path.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop — create a temporary one.
        return asyncio.new_event_loop().run_until_complete(coro)
    # There IS a running loop. We must not block it. Run the coroutine
    # on a sub-thread so we don't deadlock. This path is exercised by
    # production (the contributor runs synchronously inside a hook
    # script), but if the harness happens to have a loop active, we
    # defer.
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(asyncio.run, coro)  # type: ignore[arg-type]
        return fut.result()


def _render_retrieval(result: dict[str, Any], *, cap: int) -> str:
    """Plain-text rendering of memory-system's search response.

    Expected shape (amendment #24 ``_impl_search``):
        {"query": str, "results": [{"fact": str, ...}, ...]}

    We render each result's ``fact`` field (the human-readable edge
    summary graphiti returns) as a dashed list, truncated at ``cap``
    characters to keep the contributor's share of the turn envelope
    bounded.
    """
    results = result.get("results") or []
    if not isinstance(results, list) or not results:
        return ""
    lines: list[str] = ["[memory-retrieval]"]
    for item in results:
        if not isinstance(item, dict):
            continue
        fact = item.get("fact")
        if isinstance(fact, str) and fact.strip():
            lines.append(f"- {fact.strip()}")
    text = "\n".join(lines)
    if len(text) > cap:
        # Hard-trim on a line boundary so we don't half-emit a fact.
        out: list[str] = []
        total = 0
        for ln in lines:
            if total + len(ln) + 1 > cap:
                break
            out.append(ln)
            total += len(ln) + 1
        text = "\n".join(out)
    return text


# ---- registration helper --------------------------------------------


def register_memory_retrieval(
    composer: Any,
    *,
    memory_client: MemoryClient,
    workspace_slug: str,
    num_results: int = 5,
    char_cap: int = MEMORY_RETRIEVAL_CHAR_CAP,
    name: str = "memory-retrieval",
) -> Callable[[dict[str, Any]], str]:
    """Register the memory-retrieval contributor against a
    ``ComposedContextPayload`` instance. Convenience wrapper around
    ``composer.register(...)`` for call sites that don't need to
    capture the contributor callable themselves.

    Returns the registered callable so tests can inspect / re-invoke.
    """
    config = MemoryRetrievalConfig(
        memory_client=memory_client,
        workspace_slug=workspace_slug,
        num_results=num_results,
        char_cap=char_cap,
    )
    fn = build_memory_retrieval_contributor(config)
    composer.register(name=name, trigger_kind=TriggerKind.turn, fn=fn)
    return fn
