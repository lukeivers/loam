# Plan — Amendment #24: memory-system MCP migration

**Status:** authored 2026-04-22. Dispatch brief:
`.scratch/dispatch-drafts/amendment-24-mcp-migration.md`. Pre-amendment
tip `494a5ef`. Research:
`docs/plans/research/amendment-24-memory-system-mcp-migration-research.md`.

Transport-layer rewrite of `memory-system/src/service.py`: FastAPI +
uvicorn → FastMCP (streamable-HTTP transport). Per Luke's R5 ruling
(2026-04-23) and the component's proposal §Direction ("self-hosted as
a local MCP service").

---

## 1. Objective

Close the D1 acceptance criterion's "queryable through the MCP
interface" clause on the memory-graphiti service. Ingest/search
semantics, Graphiti lifecycle, launchd invocation, and host/port
env-var contracts are preserved. Dependency footprint shifts from
FastAPI+uvicorn to `mcp`+uvicorn (net ~15 small transitive deps
added, `fastapi` removed).

## 2. Hard constraints

1. No `--amend`. Corrective commits only if something misses.
2. Scope strictly memory-system source + tests + proposal note +
   hands-off-lifecycle bookkeeping (sidecar + narrative). **Two sealed
   components only.** If a third needs touching → halt.
3. The plist template at `workspace-bootstrap/src/workspace_bootstrap/
   adapters/first_run_scaffold.py` is NOT touched. `python -m
   src.service` stays the entrypoint; the transport swap is internal
   to `src/service.py`.
4. No real LLM / Claude / network calls from tests. Mock at the
   Graphiti boundary via a `FakeGraphiti` fixture.
5. graphiti-core stays pinned at `0.28.2` (the factory-level Kuzu
   patches remain the load-bearing reason).
6. Tool names match the brief: `add_episode`, `search`, `health`,
   `token_usage`. Snake-case per MCP convention.
7. pos-amend manifest is the bookkeeping interface. No hand-edits to
   BASELINE literals or sidecars.

## 3. Acceptance criteria (AC24.x)

Each AC maps to one or more test functions in
`memory-system/tests/test_service.py`, named `test_AC24_<n>_<slug>`.

### AC24.1 — FastMCP server instantiates with Graphiti lifespan

The module exposes an `mcp` FastMCP instance whose `lifespan`
constructs a Graphiti via the existing `make_graphiti()` factory,
calls `build_indices_and_constraints()`, yields the app, and calls
`graphiti.close()` on shutdown. Test injects a `FakeGraphiti` via
monkeypatch on the factory; asserts construct called exactly once;
asserts `close()` called exactly once on context exit.

### AC24.2 — `add_episode` tool dispatches to Graphiti.add_episode

The `add_episode` MCP tool accepts (name, body,
source_description="synthetic episode", reference_time=None,
source="text", group_id="default"). On invocation, calls
`graphiti.add_episode()` with the translated args, timezone-normalises
a naive `reference_time` to UTC (preserving current behaviour), maps
the `source` string to a `graphiti_core.nodes.EpisodeType`, and
returns a dict with `episode_uuid`, `nodes_extracted`,
`edges_extracted` keys.

### AC24.3 — `search` tool dispatches to Graphiti.search

The `search` MCP tool accepts (query, group_ids=None, num_results=10,
center_node_uuid=None). On invocation, calls `graphiti.search()` with
the translated args and returns a dict with `query` and `results[]`
keys. Each result item has `fact`, `edge_uuid`, `valid_at`,
`invalid_at`, `source_node_uuid`, `target_node_uuid` — same shape as
the current FastAPI `SearchResultItem`.

### AC24.4 — `health` tool returns ok + config sniff

The `health` MCP tool returns a dict with `status="ok"`, `llm_model`
(from `graphiti.llm_client.model`), `embedder_dim` (from
`graphiti.embedder.config.embedding_dim`), `db_path` (from
`KUZU_DB_PATH` env or the default `./data/kuzu_db`). Same shape as
the current FastAPI `HealthResponse`.

### AC24.5 — `token_usage` tool returns by-prompt + total

The `token_usage` MCP tool returns a dict with `by_prompt` (keyed by
prompt name → dict of `input_tokens`, `output_tokens`, `call_count`)
and `total` (dict of `input_tokens`, `output_tokens`). Same shape as
the current FastAPI `GET /token-usage` response.

### AC24.6 — `run()` launches the streamable-HTTP transport

`run()` invokes FastMCP's streamable-HTTP transport (binding
`GRAPHITI_SERVICE_HOST` / `GRAPHITI_SERVICE_PORT`, defaults preserved
at `127.0.0.1` / `8765`). Tested via a `monkeypatch` on the MCP
transport entry point — asserts the call site reads the env vars
and invokes the streamable-HTTP run function with a host+port
consistent with the FastMCP settings configured on the mcp instance.

### AC24.7 — `fastapi` removed from requirements.txt; `mcp` added

Regression test asserts `fastapi` is absent from
`memory-system/requirements.txt` and `mcp>=1.27` is present.
`uvicorn` stays (MCP transitive). Keeps the invariant that the
amendment fully removes the old transport's direct pin.

## 4. Implementation order

1. Research doc (done):
   `docs/plans/research/amendment-24-memory-system-mcp-migration-research.md`
2. This plan (done):
   `docs/plans/amendment-24-memory-system-mcp-migration.md`
3. Manifest (next):
   `docs/plans/amendment-24-memory-system-mcp-migration.manifest.yaml`
4. **Pre-amendment test runs:**
   a. `memory-system/` full suite — capture PASS count as pre-touch
      BASELINE.
   b. `hands-off-lifecycle/` full suite — capture PASS count.
   c. Seal-diff-only tests for the 8 untouched sealed components:
      `cost-governance`, `graceful-degradation`,
      `observability-aggregator`, `orchestrator`,
      `reversibility-primitive`, `self-correction`, `telegram-
      interface`, `workspace-bootstrap`.
5. Install `mcp` into the memory-system venv.
6. Rewrite `memory-system/src/service.py` against the AC spec above.
7. Update `memory-system/requirements.txt` — drop `fastapi`, add
   `mcp>=1.27`.
8. Add `memory-system/tests/test_service.py` with seven
   `test_AC24_*_*` tests covering AC24.1–AC24.7.
9. Update `docs/archive/component-research/memory-system/proposal.md` §
   Adaptation #4 (Graphiti MCP hosting) with a one-line landed-
   transport note.
10. Run `pos-amend validate` + `pos-amend apply` against the manifest.
11. Run `pos-amend apply --dry-run` as the green-gate.
12. **Post-apply test runs:**
    a. `memory-system/` full suite — must still PASS, delta =
       pre-touch + 7 new AC24 tests.
    b. `hands-off-lifecycle/` full suite — must still PASS with no
       delta.
13. Amendment commit: `fix(memory-system, hands-off-lifecycle):
    migrate memory-system transport FastAPI → MCP (amendment #24)`.
14. Run `pos-amend seal` to advance sidecars + append narrative.
15. Seal commit: `chore(seals): memory-system-mcp-migration seal —
    memory-system + hands-off-lifecycle at <amendment-sha>`.
16. **Post-seal test runs:** seal-diff-only tests across all 10
    sealed components to confirm no unadmitted surfaces.

## 5. Out of scope

- No changes to Graphiti-core pins or patches.
- No changes to factory, claude_print_client, temporal, retention,
  ephemerality, scope, drain, staging, upgrade, observability,
  process_of_arrival.
- No plist template changes (workspace-bootstrap untouched).
- No changes to the orchestrator's service-label reference.
- No new node-search / node-delete / edge-delete tools — only the
  four brief-specified tools. Future expansion is a separate
  amendment.
- No MCP-client-side integration into any pOS consumer (primary-
  persona etc.). That's downstream work.
- No change to the launchd invocation semantics (KeepAlive, stdout
  path, env vars).

## 6. Risks + mitigations

| Risk | Mitigation |
|---|---|
| FastMCP streamable-HTTP transport binding API differs in the installed `mcp` version vs the docs | Test AC24.6 directly against the concrete API after install; halt if the binding surface is materially different. |
| Graphiti's lifespan-context-injection pattern breaks under FastMCP | AC24.1 tests the lifecycle in isolation; halt if FakeGraphiti construct/close counts are off. |
| Dependency resolution conflict (mcp's pydantic-settings or similar clashing with existing pins) | Install in isolation first, read `pip install` output, halt if a resolver conflict surfaces. |
| Port 8765 semantics differ under streamable-HTTP | Preserve host/port env-var contract; test AC24.6 asserts they're read. |

## 7. Bookkeeping surface

**Two manifest components only:**

- `memory-system` — `seal_test: memory-system/tests/
  test_no_sealed_amendments.py`, `sidecar: memory-system/tests/
  SEAL_COMMIT`, `frozen_baseline: false` (normal floating BASELINE
  advance).
- `hands-off-lifecycle` — `seal_test: hands-off-lifecycle/tests/
  test_cross_cutting.py`, `sidecar: hands-off-lifecycle/tests/
  SEAL_COMMIT`, `frozen_baseline: true` (H19 pinned at project-start
  per amendment #23).

`universal_paths.prefixes`: `docs/plans/` (universal).
`universal_paths.files`: `CLAUDE.md`, `docs/odd-in-pos.md`,
`docs/odd-methodology.md`, `docs/FUTURE_IDEAS.md` (universal).

`narrative.target`: `hands-off-lifecycle/seals/
SEAL_COMMIT.true-first-run`. Narrative body describes R5 ruling,
transport choice rationale, tool-name mapping, and dependency delta.
