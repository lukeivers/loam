# Research — Amendment #24: memory-system MCP migration

**Author:** amendment builder, 2026-04-22 (working dir
`/Users/lukeivers/ivers-corp-pos-v2/`, pre-amendment tip `494a5ef`).
**Status:** research artefact backing the amendment plan at
`docs/plans/amendment-24-memory-system-mcp-migration.md`.
**Scope:** survey the python-mcp-sdk + graphiti reference
implementation to ground the transport-layer rewrite (FastAPI +
uvicorn → MCP server) for `memory-system/src/service.py`.

---

## 1. What's landed today

`memory-system/src/service.py` is a **FastAPI app** mounted with a
`lifespan` async context manager that constructs one Graphiti
instance on startup, calls `build_indices_and_constraints()`, yields
the app, and calls `graphiti.close()` on shutdown. Four HTTP routes:

| Method + Path | Purpose | Request model | Response model |
|---|---|---|---|
| `GET /health` | Liveness probe + config sniff | — | `HealthResponse` (status, llm_model, embedder_dim, db_path) |
| `POST /ingest` | Add an episode via `graphiti.add_episode` | `IngestRequest` (name, body, source_description, reference_time, source, group_id) | `IngestResponse` (episode_uuid, nodes_extracted, edges_extracted) |
| `POST /search` | Fact-edge search via `graphiti.search` | `SearchRequest` (query, group_ids, num_results, center_node_uuid) | `SearchResponse` (query, results[]) |
| `GET /token-usage` | Per-prompt + total token usage from the LLM client's tracker | — | `dict[str, Any]` (by_prompt, total) |

Entry point: `python -m src.service` invokes `run()` → `uvicorn.run` on
`127.0.0.1:8765` (overridable via `GRAPHITI_SERVICE_HOST` /
`GRAPHITI_SERVICE_PORT`).

**No tests currently exercise `service.py`.** The `memory-system/tests/`
directory covers every other module (drain, staging, temporal,
retention, ephemerality, scope, upgrade, observability, claude-print,
D11 process-of-arrival, D12 chaos-durability, S3 silent-excepts) but
`test_service.py` is absent. The amendment adds it, per the brief's
"same assertion shape" direction.

## 2. python-mcp-sdk survey (PyPI `mcp`, version 1.27.0 as of 2026-04-02)

Install: `pip install mcp`. Python ≥ 3.10 required.

**Core deps pulled in:** `anyio`, `httpx`, `httpx-sse`, `sse-starlette`,
`starlette`, `uvicorn`, `pydantic`, `pydantic-settings`, `jsonschema`
(+ `jsonschema-specifications`, `referencing`, `rpds-py`),
`python-dotenv`, `python-multipart`, `PyJWT`, `cryptography`, `click`,
`h11`, `httpcore`, `certifi`, `idna`, `attrs`, `cffi`, `pycparser`,
`typing-extensions`, `typing-inspection`, `annotated-types`.

**Compared to current FastAPI + uvicorn footprint in memory-system's
venv today:** `fastapi`, `uvicorn`, `starlette`, `pydantic`,
`pydantic-core`, `anyio`, `click`, `h11`, `httpx`, `python-dotenv`
all already present. Net additions post-migration: `mcp`, `httpx-sse`,
`sse-starlette`, `jsonschema` + 3 transitives, `pydantic-settings`,
`python-multipart`, `PyJWT`, `cryptography`, `cffi`, `pycparser`,
`attrs`, `httpcore`, `certifi`, `idna`, `typing-inspection`,
`annotated-types` — mostly small. Net removal: `fastapi` only (uvicorn
stays because `mcp` depends on it transitively via its HTTP transport).
**Footprint growth is not significant** — halt trigger "dependency
footprint grows significantly" is cleared.

### 2.1 Three transports

| Transport | `FastMCP.run_*_async()` | Suits which shape? |
|---|---|---|
| `stdio` | `run_stdio_async` | Spawned per client session. Parent MCP client owns the subprocess. Not compatible with launchd+KeepAlive (no parent to attach to). |
| `sse` (deprecated March 2025) | `run_sse_async` | Long-lived HTTP server with SSE streams. Works with launchd. Deprecated in favour of streamable HTTP. |
| `http` (streamable HTTP) | `run_streamable_http_async` | Long-lived HTTP server, stateless option for scaling. **Recommended for production** per the spec and the reference implementation. Works with launchd. |

**Transport choice: streamable HTTP.** Rationale:

1. launchd's `KeepAlive=true` + `RunAtLoad=true` requires the service
   to be a long-lived process that can be started without a parent
   client — stdio is out.
2. SSE is deprecated upstream; starting on it would be tech-debt on
   day one.
3. Streamable HTTP is the same shape as the current FastAPI service
   (long-lived, listens on a port, holds the Graphiti connection
   across requests). Same invocation pattern via `python -m
   src.service`; same `GRAPHITI_SERVICE_HOST` / `GRAPHITI_SERVICE_PORT`
   env var semantics preserved.
4. Per-session spawn halt trigger is cleared — streamable HTTP is
   explicitly NOT per-session.

### 2.2 Lifespan pattern

FastMCP accepts a `lifespan=` kwarg in its constructor:

```python
from contextlib import asynccontextmanager
from mcp.server.fastmcp import FastMCP

@asynccontextmanager
async def lifespan(server: FastMCP):
    graphiti = await make_graphiti()
    await graphiti.build_indices_and_constraints()
    try:
        yield {"graphiti": graphiti}
    finally:
        await graphiti.close()

mcp = FastMCP("pOS v2 memory-system", lifespan=lifespan)
```

Tools access the lifespan-yielded context via `ctx.request_context.
lifespan_context["graphiti"]` with a `Context` type-annotated
parameter. This preserves the current construct-once / close-on-
shutdown discipline — halt trigger "structural incompatibility with
Graphiti's async lifecycle" is cleared.

### 2.3 Tool definitions

FastMCP tools are decorated async functions:

```python
@mcp.tool()
async def add_episode(
    name: str,
    body: str,
    source_description: str = "synthetic episode",
    reference_time: str | None = None,
    source: str = "text",
    group_id: str = "default",
    ctx: Context | None = None,
) -> dict[str, Any]:
    """..."""
```

MCP tool-name convention is snake_case — matches the reference
implementation (`add_memory`, `search_nodes`, `search_memory_facts`,
`delete_entity_edge`, `delete_episode`, `clear_graph`, `get_status`).

### 2.4 Health-probe idiom

The graphiti reference implementation uses `@mcp.custom_route(
"/health", methods=["GET"])` for a Docker/load-balancer-friendly HTTP
health check that sits alongside the MCP surface on the streamable-
HTTP transport. We mirror that — it preserves the existing D1
"exposes a health check" acceptance criterion without requiring a
special MCP client to probe liveness. A parallel `health` MCP **tool**
ALSO ships so the health check is reachable from an MCP client.

## 3. Reference: graphiti's own MCP server

`github.com/getzep/graphiti/blob/main/mcp_server/src/graphiti_mcp_
server.py` ships its MCP server with these tools:

- `add_memory` → takes `name`, `episode_body`, `group_id`, `source`,
  `source_description`, `uuid`. Maps to `Graphiti.add_episode`.
- `search_nodes` → takes `query`, `group_ids`, `max_nodes`,
  `entity_types`.
- `search_memory_facts` → takes `query`, `group_ids`, `max_facts`,
  `center_node_uuid`. Maps to `Graphiti.search`.
- `delete_entity_edge`, `delete_episode`, `get_entity_edge`,
  `get_episodes`, `clear_graph`, `get_status`.

Our amendment is a narrower slice — just the four current-FastAPI
endpoints. Tool-name mapping:

| FastAPI (before) | MCP tool (after) |
|---|---|
| `GET /health` | `health` tool + `GET /health` custom_route |
| `POST /ingest` | `add_episode` |
| `POST /search` | `search` |
| `GET /token-usage` | `token_usage` |

(Brief prescribes these names. I preserve them.) The graphiti upstream
uses `add_memory` / `search_memory_facts`; we use `add_episode` /
`search` because (a) the brief asks for it, (b) `episode` is the
primitive the graphiti-core API already exposes at `add_episode()`,
keeping the pOS tool name aligned with the underlying call, (c) the
broader `search_memory_facts` doesn't match our current slice — we
search fact edges only, not the full graphiti search-nodes surface.
Any future fan-out to node search or deletion tools is a separate
amendment.

## 4. launchd plist: no change required

The plist template lives in **`workspace-bootstrap`** (amendment #4
made it the canonical plist generator per
`docs/archive/component-research/true-first-run/research.md` §10), not in
hands-off-lifecycle as the brief phrases it. The template invokes the
service as:

```
{workspace}/memory-system/.venv/bin/python -m src.service
```

Swapping only what `src/service.py` does internally (FastAPI →
FastMCP with streamable-HTTP transport on the same host+port) keeps
the plist invocation identical. **No plist template change required.**
The legacy standalone `memory-system/launchd/com.pos-v2.memory-
graphiti.plist` (predates the scaffold, effectively dead docs) also
does not need a change — same `python -m src.service` invocation.

This means **workspace-bootstrap is NOT a third touched sealed
component.** The halt trigger ("If a 3rd needs touching → HALT") is
cleared.

## 5. hands-off-lifecycle: scope footprint re-evaluated

The brief says both memory-system and hands-off-lifecycle BASELINE
advance. Re-reading: hands-off-lifecycle's cross-cutting checks are
`test_cross_cutting.py`:

- H19 top-level admission — `memory-system` is already in the allowed
  bucket set (and BASELINE is frozen at `3780603` per amendment #23
  so no per-amendment bump).
- H20 smoke test — asserts per-component dir is present; not a
  count-based check.
- SEAL_COMMIT sidecar presence tests — memory-system's sidecar
  changes, hands-off-lifecycle's own sidecar bookkeeping stays the
  same shape.

Hands-off-lifecycle's own seal narrative ships at
`hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run` and is the
canonical target for amendment narratives per the pos-amend manifest
convention. **We append a block there describing amendment #24.**
That touches hands-off-lifecycle under its sidecar + narrative — no
source edits. The pos-amend manifest lists hands-off-lifecycle with
`frozen_baseline: true` so H19's BASELINE literal is NOT bumped.

## 6. Test strategy — new MCP-based service tests

Since `test_service.py` didn't exist pre-amendment, the "rewrite"
direction translates to **add coverage that mirrors the HTTP-shape
assertion the FastAPI build implied but never tested**. Assertion
shape from the brief: construct → health → ingest → search →
token-usage.

**Determinism under mocks.** The halt trigger rules out real-LLM /
network tests. Graphiti requires an LLM client and an embedder; at
test time we inject a `FakeGraphiti` stand-in that implements the
four methods our MCP tools call: `add_episode`, `search`,
`build_indices_and_constraints`, `close`, plus the `llm_client.
token_tracker` surface. Tests call the MCP tool functions directly
(the `FastMCP` surface; no subprocess, no network loopback). This
mirrors how `test_claude_print_client.py` mocks `claude -p` — same
discipline.

**MCP-client round-trip is NOT in scope.** A true end-to-end
streamable-HTTP test would require spawning the server and running
an in-process client against it; that adds transport flake and
slows the suite. The contract we check is: tool registered with
FastMCP, tool function invoked with the right args, tool dispatches
to Graphiti's method with the right args, tool returns the right
shape. The transport layer itself is upstream-maintained by the
`mcp` package and covered by its own tests.

## 7. Proposal edits

`docs/archive/component-research/memory-system/proposal.md`:

- §Direction already says "self-hosted as a local MCP service" —
  this text is correct; flag amendment #24 as the landing
  confirmation.
- §Non-goals already says "Not a specification of code structure" —
  no edit.
- §Adaptation #4 "Graphiti MCP hosting" — acceptance criterion "is
  queryable through the MCP interface" now passes. Add a one-line
  landed-transport note (streamable HTTP, FastMCP, amendment #24).
- No other §0.1 exists. The brief's §0.1 / §3.2 reference is a
  placeholder; the proposal doc numbers adaptation layers 1-9 rather
  than sectioning.
- No FastAPI references to remove.

## 8. Halt triggers cleared

1. **python-mcp-sdk structural incompat with Graphiti's async
   lifecycle** — cleared, FastMCP's `lifespan=` kwarg is the exact
   same shape as FastAPI's (`@asynccontextmanager` → yield; the
   current `service.py` lifespan moves across verbatim).
2. **Test requires real LLM / Claude / network** — cleared via
   injected `FakeGraphiti` stand-in.
3. **Per-session spawn** — cleared by choosing streamable-HTTP
   transport; one persistent process.
4. **Removing FastAPI/uvicorn breaks a non-test consumer** — cleared.
   No non-test HTTP consumer uses `/ingest`, `/search`,
   `/token-usage`, `/health`. The orchestrator only references the
   launchd label (`com.pos-v2.<slug>.memory-graphiti`), not the HTTP
   API. Uvicorn stays (transitive `mcp` dep); only `fastapi` is
   removed from `requirements.txt`.
5. **Primary-persona component integration changes** — out of scope;
   no primary-persona code touches the service. Cleared.
6. **Dependency footprint grows significantly** — cleared. ~15 small
   transitive deps added, `fastapi` removed.

## 9. Surface edits (authoritative)

- `memory-system/src/service.py` — rewrite module body. Keep the
  `run()` entry point signature (`python -m src.service`) so the
  plist template needs no change. Host/port env-var names preserved.
- `memory-system/requirements.txt` — drop `fastapi`, add `mcp`.
  Keep `uvicorn` (MCP transitive dep; drop the explicit pin if the
  upstream pulls the same range).
- `memory-system/tests/test_service.py` — new. 5+ outcome-shaped
  tests against a `FakeGraphiti` fixture.
- `memory-system/tests/test_no_sealed_amendments.py` — BASELINE bump
  handled by pos-amend. No manual edit.
- `memory-system/tests/SEAL_COMMIT` — sidecar advance handled by
  pos-amend.
- `hands-off-lifecycle/tests/SEAL_COMMIT` — sidecar advance handled
  by pos-amend (no BASELINE bump; `frozen_baseline: true`).
- `hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run` — narrative
  append handled by pos-amend.
- `docs/archive/component-research/memory-system/proposal.md` — one-line
  landed-transport note under §Adaptation #4.
- `docs/plans/amendment-24-memory-system-mcp-migration.md` —
  plan.
- `docs/plans/amendment-24-memory-system-mcp-migration.manifest.yaml` —
  pos-amend manifest.
- `docs/plans/research/amendment-24-memory-system-mcp-migration-research.md` —
  this doc.
