"""FastMCP wrapper around Graphiti — the 'managed local service' shape.

Amendment #24 (2026-04-22) swapped the transport layer from FastAPI +
uvicorn (HTTP REST) to FastMCP (streamable-HTTP MCP) per Luke's R5
ruling (2026-04-23). Rationale in the amendment plan
(``docs/rebuild/plans/amendment-24-memory-system-mcp-migration.md``):
the proposal's §Direction always called for "self-hosted as a local
MCP service"; the initial FastAPI shape was a prototyping stand-in.
Amendment #24 lands the intended transport.

Why a long-lived service rather than library-only? Proposal D1's
acceptance criterion calls for 'the service auto-starts with the
system, restarts on failure, exposes a health check, and is queryable
through the MCP interface.' A long-lived process holding the Kuzu
connection (a) makes auto-start meaningful (launchd KeepAlive), (b)
gives the survives-a-restart property a concrete test (kill, relaunch,
query the prior episode), and (c) matches the proposal's adaptation #4
(Graphiti MCP hosting) shape directly.

Transport choice: streamable HTTP. Stdio would require a parent MCP
client to own the subprocess — incompatible with launchd's KeepAlive.
SSE was deprecated upstream (March 2025). Streamable HTTP is the
same long-lived shape as the outgoing FastAPI service.

The four MCP tools (``add_episode``, ``search``, ``health``,
``token_usage``) cover the same surface as the outgoing
``/ingest``, ``/search``, ``/health``, ``/token-usage`` endpoints —
one-to-one. Tool names are snake_case per MCP convention.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from graphiti_core.nodes import EpisodeType
from mcp.server.fastmcp import FastMCP

from .factory import load_env, make_graphiti


# Module-level handle to the Graphiti instance, populated by the
# lifespan context manager on server start and cleared on shutdown.
# Tool implementations read it via ``_require_graphiti()`` which raises
# a descriptive error if the lifespan hasn't entered. Kept as a
# module-level attribute (rather than only inside the lifespan context
# dict) so the tool functions can be unit-tested by monkeypatching
# this single name — the same pattern the outgoing FastAPI module used.
_graphiti: Any = None


def _require_graphiti() -> Any:
    """Return the Graphiti instance or raise if uninitialised.

    Pre-amendment (FastAPI) raised ``HTTPException(503)``; under MCP
    the equivalent surfacing is a ``RuntimeError`` whose message the
    MCP framework relays to the client as a tool-call error.
    """
    if _graphiti is None:
        raise RuntimeError("graphiti not initialised (lifespan not entered)")
    return _graphiti


async def _ensure_graphiti() -> Any:
    """Construct ``_graphiti`` once; idempotent on re-entry.

    Amendment #34 (AC34.1): the FastMCP-wrapped Starlette app routes
    the user lifespan to the lower-level ``MCPServer.run`` path, which
    is invoked per MCP session by ``StreamableHTTPSessionManager``.
    That means the lifespan's construct half does not run at process
    start — it runs the first time a client opens an MCP session. The
    ``GET /health`` Starlette ``custom_route`` reads ``_graphiti`` at
    request time and returns 503 ``{"status":"initialising"}`` when
    ``_graphiti is None``, so launchd / hands-off-lifecycle's phase-4b
    probe (which never opens an MCP session) sees 503 forever.

    The fix moves construction to a coroutine the entry point awaits
    before ``mcp.run_streamable_http_async()`` enters its serve loop.
    The lifespan's construct half now delegates to this coroutine; the
    ``if _graphiti is not None: return`` guard makes per-session enters
    no-ops on the construct side, while the lifespan's
    yield/finally close-on-exit half preserves verbatim.
    """
    global _graphiti
    if _graphiti is not None:
        return _graphiti
    load_env()
    _graphiti = await make_graphiti()
    await _graphiti.build_indices_and_constraints()
    return _graphiti


@asynccontextmanager
async def lifespan(server: FastMCP):
    """Build Graphiti once (idempotent); close on shutdown.

    Construct half delegates to ``_ensure_graphiti()`` — when the
    process-startup path has already populated ``_graphiti`` (the
    amendment #34 path), this is a no-op. When entered cold (e.g. by
    AC24.1's direct test invocation), ``_ensure_graphiti()`` does the
    first-time construction. Either way the body's contract is
    "``_graphiti`` is populated on yield, closed on exit."
    """
    global _graphiti
    await _ensure_graphiti()
    try:
        yield {"graphiti": _graphiti}
    finally:
        if _graphiti is not None:
            try:
                await _graphiti.close()
            finally:
                _graphiti = None


def _build_mcp() -> FastMCP:
    """Construct the FastMCP instance and register tools.

    Factored out so tests can reconstruct a fresh instance under a
    fake-Graphiti monkeypatch without leaking state from earlier
    tests. The module-level ``mcp`` binding is the one the
    streamable-HTTP server runs against.
    """
    host = os.environ.get("GRAPHITI_SERVICE_HOST", "127.0.0.1")
    port = int(os.environ.get("GRAPHITI_SERVICE_PORT", "8765"))

    server = FastMCP(
        "pOS v2 memory-system",
        lifespan=lifespan,
        host=host,
        port=port,
    )

    _register_tools(server)
    _register_custom_routes(server)
    return server


# ---- Tool implementations (pure, test-friendly) ---------------------
#
# The implementations take a Graphiti handle as their first argument
# so they're trivially unit-testable with a fake. The MCP-decorated
# wrappers below call through to these functions with the live
# Graphiti instance resolved from the module global.


_EPISODE_TYPES = {t.value: t for t in EpisodeType}


async def _impl_add_episode(
    graphiti: Any,
    *,
    name: str,
    body: str,
    source_description: str = "synthetic episode",
    reference_time: datetime | None = None,
    source: str = "text",
    group_id: str = "default",
) -> dict[str, Any]:
    """``add_episode`` tool implementation."""
    episode_source = _EPISODE_TYPES.get(source, EpisodeType.text)
    ref_time = reference_time or datetime.now(timezone.utc)
    if ref_time.tzinfo is None:
        ref_time = ref_time.replace(tzinfo=timezone.utc)
    result = await graphiti.add_episode(
        name=name,
        episode_body=body,
        source_description=source_description,
        reference_time=ref_time,
        source=episode_source,
        group_id=group_id,
    )
    return {
        "episode_uuid": result.episode.uuid,
        "nodes_extracted": len(result.nodes),
        "edges_extracted": len(result.edges),
    }


async def _impl_search(
    graphiti: Any,
    *,
    query: str,
    group_ids: list[str] | None = None,
    num_results: int = 10,
    center_node_uuid: str | None = None,
) -> dict[str, Any]:
    """``search`` tool implementation."""
    edges = await graphiti.search(
        query=query,
        center_node_uuid=center_node_uuid,
        group_ids=group_ids,
        num_results=num_results,
    )
    items = [
        {
            "fact": edge.fact,
            "edge_uuid": edge.uuid,
            "valid_at": edge.valid_at.isoformat() if edge.valid_at else None,
            "invalid_at": edge.invalid_at.isoformat() if edge.invalid_at else None,
            "source_node_uuid": edge.source_node_uuid,
            "target_node_uuid": edge.target_node_uuid,
        }
        for edge in edges
    ]
    return {"query": query, "results": items}


async def _impl_health(graphiti: Any) -> dict[str, Any]:
    """``health`` tool implementation.

    Amendment #29 (AC29.5): the response carries a ``workspace_root``
    field so consumers (hands-off-lifecycle's phase-4b probe) can
    verify the responding sidecar belongs to the workspace they
    dispatched from. Value comes from ``LOAM_WORKSPACE_ROOT`` in
    the process env, which the workspace-bootstrap first-run scaffold
    injects via the launchd plist's ``EnvironmentVariables`` dict.
    Empty string is the explicit "workspace identity not configured"
    value — probes treat that as mismatch.
    """
    return {
        "status": "ok",
        "llm_model": graphiti.llm_client.model,
        "embedder_dim": graphiti.embedder.config.embedding_dim,
        "db_path": os.environ.get("KUZU_DB_PATH", "./data/kuzu_db"),
        "workspace_root": os.environ.get("LOAM_WORKSPACE_ROOT", ""),
    }


async def _impl_token_usage(graphiti: Any) -> dict[str, Any]:
    """``token_usage`` tool implementation."""
    by_prompt = graphiti.llm_client.token_tracker.get_usage()
    total = graphiti.llm_client.token_tracker.get_total_usage()
    return {
        "by_prompt": {
            name: {
                "input_tokens": u.total_input_tokens,
                "output_tokens": u.total_output_tokens,
                "call_count": u.call_count,
            }
            for name, u in by_prompt.items()
        },
        "total": {
            "input_tokens": total.input_tokens,
            "output_tokens": total.output_tokens,
        },
    }


# ---- MCP registration -----------------------------------------------


def _register_tools(server: FastMCP) -> None:
    """Register the four MCP tools on the server instance.

    Each tool wraps the corresponding ``_impl_*`` function, resolving
    the live Graphiti instance via ``_require_graphiti()``.
    """

    @server.tool()
    async def add_episode(
        name: str,
        body: str,
        source_description: str = "synthetic episode",
        reference_time: str | None = None,
        source: str = "text",
        group_id: str = "default",
    ) -> dict[str, Any]:
        """Add an episode to the Graphiti knowledge graph.

        ``reference_time`` accepts an ISO-8601 string or ``None``
        (defaults to now). ``source`` is one of graphiti-core's
        ``EpisodeType`` string values (``text``, ``message``,
        ``json``); unknown values fall back to ``text``.
        """
        ref_dt: datetime | None = None
        if reference_time is not None:
            ref_dt = datetime.fromisoformat(reference_time)
        return await _impl_add_episode(
            _require_graphiti(),
            name=name,
            body=body,
            source_description=source_description,
            reference_time=ref_dt,
            source=source,
            group_id=group_id,
        )

    @server.tool()
    async def search(
        query: str,
        group_ids: list[str] | None = None,
        num_results: int = 10,
        center_node_uuid: str | None = None,
    ) -> dict[str, Any]:
        """Search Graphiti's fact edges for edges matching the query."""
        return await _impl_search(
            _require_graphiti(),
            query=query,
            group_ids=group_ids,
            num_results=num_results,
            center_node_uuid=center_node_uuid,
        )

    @server.tool()
    async def health() -> dict[str, Any]:
        """Return service health + current LLM/embedder/DB config."""
        return await _impl_health(_require_graphiti())

    @server.tool()
    async def token_usage() -> dict[str, Any]:
        """Return per-prompt and total LLM token usage counters."""
        return await _impl_token_usage(_require_graphiti())


def _register_custom_routes(server: FastMCP) -> None:
    """Register a ``GET /health`` Starlette route alongside the MCP
    surface.

    Mirrors the graphiti-upstream MCP server's health-route pattern:
    exposes a plain HTTP probe that launchd / load-balancers / smoke
    tests can hit without speaking MCP. The same liveness data the
    ``health`` MCP tool returns.
    """
    from starlette.responses import JSONResponse

    @server.custom_route("/health", methods=["GET"])
    async def health_route(request):  # type: ignore[no-untyped-def]
        if _graphiti is None:
            return JSONResponse(
                {"status": "initialising"},
                status_code=503,
            )
        body = await _impl_health(_graphiti)
        return JSONResponse(body)


# ---- Module bindings + entry point ----------------------------------


mcp = _build_mcp()


def run() -> None:
    """Entry point for ``python -m src.service``.

    Launches the FastMCP streamable-HTTP transport bound to
    ``GRAPHITI_SERVICE_HOST`` / ``GRAPHITI_SERVICE_PORT``. Same
    invocation contract the outgoing FastAPI service honoured so the
    launchd plist template (``workspace-bootstrap`` scaffold) needs
    no change.

    Amendment #34 (AC34.1): awaits ``_ensure_graphiti()`` BEFORE
    entering ``mcp.run_streamable_http_async()`` so ``_graphiti`` is
    populated before uvicorn begins accepting requests. This is what
    makes ``GET /health`` return 200 from the first probe onwards
    (rather than 503 until the first MCP session opens). Both
    awaitables share the same event loop via a single
    ``asyncio.run`` call.
    """
    import asyncio

    async def _serve() -> None:
        await _ensure_graphiti()
        await mcp.run_streamable_http_async()

    asyncio.run(_serve())


if __name__ == "__main__":
    run()
