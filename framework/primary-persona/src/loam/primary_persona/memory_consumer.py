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

**Group-ID convention (amendment #95 / AC.MPF.5).** The persona's
write path uses ``group_id=workspace_slug``; the read path queries
with ``group_ids=[workspace_slug]``. The two paths agree by
construction. Verification-write paths that bypass the persona
(e.g. memory-system internal ingest under ``default_scope_id``,
test harnesses) write under DIFFERENT group_ids and are NOT
retrievable via the persona's read path. If a future agent /
harness wants persona-retrievable data, it must write under the
persona's slug convention. Per-source isolation is the current
convention; a "shared workspace group_id" surface is deferred to
FUTURE_IDEAS_DRAFT (HSF#4 in plan §16).
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable, Protocol

from .context_composer import TriggerKind


# Diagnostic log filename (sibling to write-side ``memory-writes.log``)
# used by ``_append_diag`` to surface read-side boundary errors per
# AC.MPF.3 / M6c graceful-fallthrough-with-detection CDC. The log lives
# at ``<workspace_root>/.pos/<MEMORY_READS_LOG_NAME>``; the directory
# is created by ``workspace-bootstrap`` and SHOULD exist by the time
# the contributor fires. ``_append_diag`` is fail-soft if it doesn't.
MEMORY_READS_LOG_NAME = "memory-reads.log"


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
    ) -> dict[str, Any]:
        """Issue ``search`` against memory-system.

        Post-fastmcp-group-ids-filter-fix (amendment #96): the
        documented return shape is
        ``{"query", "results", "nodes", "episodes"}`` — strict
        superset of the pre-#96 ``{"query", "results"}`` shape.
        ``results`` continues to carry edges (facts). ``nodes``
        and ``episodes`` are new keys; consumers that read
        ``out["query"]`` / ``out["results"]`` only see no
        behavioural change.
        """
        ...


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
    *,
    workspace_root: Path | str | None = None,
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

    Per AC.MPF.3 (amendment #95), boundary exceptions are now
    additionally surfaced to ``<workspace>/.pos/memory-reads.log``
    via ``_append_diag`` so an operator inspecting read-side
    observability can distinguish "no relevant results" from
    "memory boundary failed" from "group_id mismatch". The
    contributor still returns ``""`` on exception (fail-closed
    contract preserved). When ``workspace_root`` is None, the
    diagnostic log is skipped (degrades gracefully — used by tests
    that don't provide a workspace path).
    """

    ws_root_resolved: Path | None = (
        Path(workspace_root) if workspace_root is not None else None
    )

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
        except Exception as exc:
            # Fail-closed per AC-D7.7 — any boundary error, regardless
            # of cause (connection refused, HTTP 5xx, timeout, garbage
            # response, etc.), yields an empty retrieval block and the
            # turn proceeds.
            #
            # AC.MPF.3 / M6c: surface the exception to memory-reads.log
            # before swallowing it, so the read-side fallthrough is
            # detectable from outside the hook channel.
            if ws_root_resolved is not None:
                _append_diag(
                    workspace_root=ws_root_resolved,
                    exception=exc,
                    workspace_slug=config.workspace_slug,
                    query=prompt,
                )
            return ""
        return _render_retrieval(result, cap=config.char_cap)

    return contributor


def _append_diag(
    *,
    workspace_root: Path,
    exception: BaseException,
    workspace_slug: str,
    query: str,
) -> None:
    """Append one NDJSON line to ``<workspace>/.pos/memory-reads.log``.

    Mirror of the write-side ``memory-writes.log`` diagnostic surface.
    Fail-soft: any OSError on directory or file open swallows
    silently — the read-side fail-closed envelope is the load-bearing
    contract; this log is best-effort observability only (AC.MPF.3).

    NDJSON line shape:
        {"timestamp": "<ISO-8601-utc>",
         "exception_type": "<ClassName>",
         "exception_message": "<str(exc)>",
         "workspace_slug": "<slug>",
         "query_preview": "<first 80 chars of query>"}
    """
    try:
        diag_dir = Path(workspace_root) / ".pos"
        diag_dir.mkdir(parents=True, exist_ok=True)
        log_path = diag_dir / MEMORY_READS_LOG_NAME
        line = json.dumps(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "exception_type": type(exception).__name__,
                "exception_message": str(exception),
                "workspace_slug": workspace_slug,
                "query_preview": query[:80],
            },
            ensure_ascii=False,
        )
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        # Best-effort observability; never propagate.
        return


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

    Expected shape (post-fastmcp-group-ids-filter-fix /
    amendment #96 ``_impl_search``):
        {"query": str,
         "results":  [{"fact": str, ...}, ...],   # edges (facts)
         "nodes":    [{"node_uuid", "name", "summary", "group_id"}, ...],
         "episodes": [{"episode_uuid", "name", "content",
                       "group_id", "valid_at"}, ...]}

    Pre-amendment-#96 shape was ``{"query", "results"}`` (results =
    edges). The persona consumer is back-compat by construction —
    when the boundary returns the old shape, ``nodes`` and
    ``episodes`` default to ``[]`` and the rendering is identical.

    Rendering strategy (amendment #96 D2):

    1. If ``results`` (edges) is non-empty: render each edge's
       ``fact`` field as a dashed list — same shape as pre-#96.
       Edges are graphiti's reranked, fact-summarised relations and
       are the highest-signal retrieval surface.
    2. Else if ``episodes`` is non-empty: render each episode's
       name + content preview as ``[episode] {name}: {preview}``.
       This is the fall-through that fixes the
       fastmcp-group-ids-filter-fix observable: write under
       ``group_id=X`` with a body too sparse for graphiti's LLM-
       extractor to derive edges, search with ``group_ids=[X]`` —
       the episode is now retrievable via this branch.
    3. Else (both empty): preserve AC.MPF.2's empty-state diagnostic
       (``[memory-retrieval]\\n  (no results for this query)``).

    ``nodes`` is currently omitted from the rendering — entities
    without their relating edges or episodes are typically lower
    signal-density than episodes, and surfacing them risks bloating
    the contributor envelope without proportional retrieval value.
    Captured as a future-improvement (FUTURE_IDEAS_DRAFT) — not a
    fix-blocker. The MCP tool still returns ``nodes`` so other
    consumers (e.g. an explicit graph-explorer) can use it.

    The ``cap`` truncation is line-boundary aware: we never emit a
    half-line. When the cap forces truncation mid-list, the
    remaining items are dropped (no ellipsis marker needed; the
    line-count is the only signal of completeness).
    """
    edges = result.get("results") or []
    episodes = result.get("episodes") or []

    if isinstance(edges, list) and edges:
        lines: list[str] = ["[memory-retrieval]"]
        for item in edges:
            if not isinstance(item, dict):
                continue
            fact = item.get("fact")
            if isinstance(fact, str) and fact.strip():
                lines.append(f"- {fact.strip()}")
    elif isinstance(episodes, list) and episodes:
        lines = ["[memory-retrieval]"]
        for item in episodes:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            content = item.get("content")
            if not isinstance(name, str) or not name.strip():
                continue
            if not isinstance(content, str):
                content = ""
            content_preview = content.strip().replace("\n", " ")
            # Per-episode line cap: keep the preview compact so a
            # single dense episode doesn't exhaust the contributor
            # cap. The line-level cap below still applies.
            if len(content_preview) > 200:
                content_preview = content_preview[:200].rstrip() + "…"
            if content_preview:
                lines.append(
                    f"- [episode] {name.strip()}: {content_preview}"
                )
            else:
                lines.append(f"- [episode] {name.strip()}")
    else:
        return "[memory-retrieval]\n  (no results for this query)"

    text = "\n".join(lines)
    if len(text) > cap:
        # Hard-trim on a line boundary so we don't half-emit an entry.
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
    workspace_root: Path | str | None = None,
) -> Callable[[dict[str, Any]], str]:
    """Register the memory-retrieval contributor against a
    ``ComposedContextPayload`` instance. Convenience wrapper around
    ``composer.register(...)`` for call sites that don't need to
    capture the contributor callable themselves.

    Returns the registered callable so tests can inspect / re-invoke.

    ``workspace_root`` (AC.MPF.3, amendment #95) is forwarded to
    ``build_memory_retrieval_contributor`` so boundary exceptions
    surface to ``<workspace>/.pos/memory-reads.log``. When None,
    the diagnostic log is skipped.
    """
    config = MemoryRetrievalConfig(
        memory_client=memory_client,
        workspace_slug=workspace_slug,
        num_results=num_results,
        char_cap=char_cap,
    )
    fn = build_memory_retrieval_contributor(
        config,
        workspace_root=workspace_root,
    )
    composer.register(name=name, trigger_kind=TriggerKind.turn, fn=fn)
    return fn
