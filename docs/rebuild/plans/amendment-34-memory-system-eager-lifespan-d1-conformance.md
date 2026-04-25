# Plan — Amendment #34: memory-system eager lifespan / D1 health-check conformance

**Status:** authored 2026-04-25, awaiting owner ruling on the named decisions in §3 before brief-dispatch.
**Pre-amendment tip:** captured at brief-dispatch time.
**Amendment number:** `#34` placeholder; renumbered at dispatch per the convention amendments #29–#33 followed.
**Filename:** family-named (`memory-system-eager-lifespan-d1-conformance`) so the path survives renumbering.
**Companion research:** none authored separately — research findings inlined in §2 because the bug is mechanically traceable to a single FastMCP lifespan-routing fact, and the empirical confirmation is one read of the installed package + one read of `memory-system/src/service.py`. The CDC research-before-plan gate is satisfied by §2's findings; an external research artefact would be ceremony, not signal.

---

## 1. Summary / TLDR

Amendment #24 (FastAPI → FastMCP transport swap, 2026-04-22) silently regressed the D1 acceptance criterion **"the service auto-starts with the system, restarts on failure, exposes a health check, and is queryable through the MCP interface."** Under the new transport, the user lifespan that builds the Graphiti instance is no longer invoked at process startup — FastMCP routes it to the lower-level `MCPServer.run`, which is invoked **per MCP session** by `StreamableHTTPSessionManager`. Until a client opens an MCP session, the module-level `_graphiti` stays `None` and the `GET /health` Starlette `custom_route` returns `503 {"status":"initialising"}`.

That defeats hands-off-lifecycle's phase-4b probe (it polls `/health` for 60s without ever opening an MCP session) and — independently of phase-4b — fails the spec-level D1 clause "exposes a health check," because a route that never returns healthy is not exposing a health check in any meaningful sense. The bug is a D1-conformance defect in the memory-system component, not a workspace-identity / Idea-9 follow-on.

Recommendation: **eager-init memory-system's Graphiti instance in a Starlette `on_startup` callback (or equivalent process-startup hook owned by memory-system itself), under a single new acceptance criterion AC34.1 ("/health returns 200 within a bounded budget after `python -m src.service` enters its serve loop, without any MCP session being opened"), as a sealed-component amendment to memory-system. No hands-off-lifecycle or workspace-bootstrap surface change is required.**

The amendment composes additively with amendment #29's identity-aware probe (AC29.5): once `_graphiti` is populated eagerly, the `/health` route already returns the `workspace_root` field amendment #29 added, and the probe path keeps working.

---

## 2. Research findings (inlined per CDC)

### 2.1 The bug

**File:** `memory-system/src/service.py` lines 51, 66–86, 99–104, 288–307, 313, 316–328.

The module global `_graphiti: Any = None` (line 51) is populated only by the `lifespan` async context manager (line 67). `_build_mcp` (line 88) constructs the `FastMCP` instance with `lifespan=lifespan` (line 101). `_register_custom_routes` (line 288) attaches a `GET /health` Starlette route via `@server.custom_route` — that route reads `_graphiti` at request time (line 301) and returns `503 {"status":"initialising"}` whenever `_graphiti is None`.

`run()` (line 316) calls `mcp.run_streamable_http_async()`.

### 2.2 What FastMCP actually does with the user lifespan

**Source:** `mcp/server/fastmcp/server.py` from `mcp>=1.27` (the version pinned in `memory-system/requirements.txt` per amendment #24).

- Line 132–143: `lifespan_wrapper(app, lifespan)` wraps the user lifespan and re-types it for the lower-level Server.
- Line 212: the wrapped lifespan is passed to `MCPServer.__init__(lifespan=...)` (the lower-level `mcp.server.lowlevel.Server`).
- Line 1044: `streamable_http_app()` returns a `Starlette` whose `lifespan=lambda app: self.session_manager.run()`.
- Line 950–963: `streamable_http_app()` creates a `StreamableHTTPSessionManager` and the Starlette app's lifespan is **only** that session-manager's `run()`.
- `StreamableHTTPSessionManager.run` (`mcp/server/streamable_http_manager.py` line 99–137) sets up an anyio task group; **it does not call the user lifespan**.
- The user lifespan (now living inside `MCPServer.lifespan`) is entered by `MCPServer.run` (`mcp/server/lowlevel/server.py` line 640, 657: `lifespan_context = await stack.enter_async_context(self.lifespan(self))`).
- `MCPServer.run` is invoked by `StreamableHTTPSessionManager._handle_stateless_request` (line 193) and `_handle_stateful_request` (line 273) — i.e., **per HTTP request that opens an MCP session**, not at server startup.

**Consequence:** the user lifespan body (`load_env`, `make_graphiti`, `build_indices_and_constraints`, populate `_graphiti`) runs the first time a client opens an MCP session, not at process start. The Starlette `custom_route` for `/health` is registered at the Starlette layer, not the MCP layer, and bypasses the session creation path entirely. So a `/health` GET from launchd / hands-off-lifecycle / `curl` never opens a session and never causes `_graphiti` to be populated.

### 2.3 What the prior FastAPI shape did (pre-#24)

`git show 53a4b88 -- memory-system/src/service.py` shows the diff:

- Pre-#24: `app = FastAPI(..., lifespan=lifespan)`. FastAPI's Starlette parent calls the user lifespan exactly once at app startup, before any request is served. So `/health` returned 200 immediately because `_graphiti` was populated at startup.
- Post-#24: the same `lifespan` callable is now passed to `FastMCP`, which re-routes it to the per-session path described in §2.2.

The transport swap was authored as "preserves the Graphiti lifespan (construct-on-start / close-on-shutdown)" (amendment #24 commit message), and the `lifespan` callable's body did indeed go in unchanged. What the author didn't notice — and what amendment #24's AC24.1 didn't catch — is that the **caller** changed. AC24.1 directly invokes `service.lifespan(service.mcp)` as an async context manager (`memory-system/tests/test_service.py:172`), which proves the lifespan body works when entered, but says nothing about whether the framework actually enters it at process start. That gap is the §2.5-style violation the present amendment closes by adding an outcome-shaped criterion.

### 2.4 When did this regress?

**The 2026-04-23 first-run that "passed" phase-4b was post-#24 already** (amendment #24 sealed 2026-04-23 12:54 CDT; first-run was later that day). The lifespan-laziness was present then. Two plausible explanations for the apparent pass:

1. The phase-4b probe is `_probe_http(status == 200)` pre-#29 and identity-aware post-#29. Pre-#29's lenient probe could have been satisfied by an **already-running sidecar from a prior invocation** that had been hit by an MCP session at any time — its `_graphiti` was populated, `/health` returned 200, and phase-4b passed without amendment #34's eager-init being needed. Pre-#29 had no port-namespacing, so all workspaces shared port 8765, and any prior sidecar could satisfy any later phase-4b.
2. Or phase-4b's polling budget happened to land within a window where some other path exercised the MCP session. (Less likely; nothing in the first-run flow opens an MCP session before phase-4b.)

Post-#29's per-workspace port + identity-aware probe closes both escape hatches: the workspace's own freshly-spawned sidecar must respond healthy with the matching `workspace_root`, and that sidecar's `_graphiti` is unpopulated until a session opens. Phase-4b's 60-second budget elapses before any session is opened (because nothing in the first-run flow opens one), so the probe times out.

So #29 didn't introduce the bug; it surfaced it by removing the cross-workspace masking. The bug class is "transport-swap regressed an objective the AC didn't outcome-shape," dating to #24.

### 2.5 What "exposing a health check" requires

D1's spec text (per `memory-system/proposal.md:71`): *"the service auto-starts with the system, restarts on failure, exposes a health check, and is queryable through the MCP interface."*

A health check route that returns 503 forever (under the actually-deployed configuration) does not satisfy "exposes a health check." The objective is outcome-shaped — there must be a check the rest of the system can use to know the service is healthy — and the current implementation fails that outcome.

This locates the fix at the spec-objective layer, not the dev-discipline layer per CLAUDE.md's §2.5 "operational cautions":

> §2.5 applies to proposals I author, not only to code I review. Before scoping anything as a sealed-component amendment, name the specific spec objective (v1.0/v1.1/v1.2) the code will satisfy. If I can't name one, the work is dev-discipline. … not a sealed-component cycle.

D1 is the named spec objective. Sealed-component amendment is the correct framing.

---

## 3. Decisions for owner to rule on (recommendations stated)

Six named decisions. Each names a recommendation; each recommendation is defensible from the research; no punt to "owner ruling" without a stated lean.

### D1. Spec-objective placement: D1 (memory-system v1.0) vs Idea 9 family

**Question:** is this a D1 conformance fix in the memory-system component, or a workspace-identity follow-on under FUTURE_IDEAS Idea 9 (where amendments #6, #28, #29 ride)?

**Recommendation: D1.** The bug is "the health route does not actually expose health" — a clean miss against the spec text. Idea 9 amendments fix workspace-identity hazards (slug collisions, host-global state-file collisions, shared-port collisions, identity-confused probes); this fix is single-workspace and would be wrong on a single-workspace machine the same way it's wrong now. The bug is orthogonal to identity. D1 is the correct objective, and memory-system is the sole sealed component that owns D1.

**Alternative considered:** scope as Idea-9 because amendment #29 is fresh and the failure surfaces in the same probe. Rejected — the workspace-identity machinery in #29 is correct; the bug is upstream of it.

### D2. Remedy class: eager init at startup (a) vs probe-side change (b) vs first-call init (c) vs combination (d)

**Question:** where does the fix live?

**Recommendation: (a) eager init at process startup, owned by memory-system.** Specifically: register an `on_startup` hook on the Starlette app returned by `FastMCP.streamable_http_app`, or override `run()` to construct Graphiti before entering `mcp.run_streamable_http_async`, such that `_graphiti` is populated before the uvicorn server begins accepting requests. The lifespan wrapper continues to exist for shutdown semantics (graceful close on process termination), but the construction path moves to startup.

**Why (a) over the alternatives:**

- **(b) Probe-side change** (treat 503 `initialising` as a different state, or have the probe send an MCP request to trigger init): defeats AC29.5's identity-aware probe (a 503 carries no body the probe can match against `workspace_root`); shifts complexity from the service that should expose the health check to every consumer of it; is inconsistent with the spec text — "exposes a health check" places the burden on the service.
- **(c) First-call init** (have the `/health` route trigger `make_graphiti` if `_graphiti is None`): introduces a thundering-herd race (phase-4b polls every 0.5s; a slow `make_graphiti` could be re-entered before the first call completes); defeats the original lifespan's "construct once" property; requires synchronisation primitives the current design avoids.
- **(d) Combination**: more surface than the bug warrants. The eager-init shape is sufficient.

**Risk on (a):** the `on_startup` callback's exception handling needs to be deliberate — if `make_graphiti` fails (e.g., Ollama unreachable, Kuzu DB locked), the process should exit with a diagnostic, not silently degrade to the current 503-forever state. The current lazy-init at least surfaces the failure on the first MCP call; eager-init must surface it at uvicorn startup. Builder's call on the exact error-surfacing pattern, but the AC names the outcome.

### D3. Component scope: memory-system only vs multi-component

**Question:** does the fix touch memory-system only, or also hands-off-lifecycle / workspace-bootstrap?

**Recommendation: memory-system only.** Single sealed component. No surface change to hands-off-lifecycle (the probe is correct; it polls for 60s expecting a 200) or workspace-bootstrap (the launchd plist invocation contract is unchanged). The fix is internal to memory-system's service.py.

This contrasts with #29's three-component amendment — #29 had to coordinate port emission (workspace-bootstrap), port consumption (memory-system), and identity-aware probing (hands-off-lifecycle). #34 has no coordination surface; it's a one-component bugfix.

### D4. Test strategy: how to empirically distinguish "lifespan ran at startup" from "lifespan ran on first /health hit"

**Question:** what shape does the AC's test take, given that the bug is precisely about *when* an existing-and-correct lifespan body runs?

**Recommendation: spawn a real subprocess of `python -m src.service` (with `make_graphiti` monkeypatched to a FakeGraphiti via an env-var seam, so no real Ollama / Claude / Kuzu fires), poll `127.0.0.1:<port>/health` over HTTP from the test, and assert 200 + `workspace_root` field within a bounded budget (suggested 5s — generous for the FakeGraphiti path) without ever opening an MCP session.** The test is structurally identical to AC29.4's subprocess-bind-only pattern (already on the seal surface) but asserts payload-shape rather than only port-bind.

The "without opening an MCP session" clause is enforced by construction (the test only issues plain HTTP GETs to `/health`); no negative assertion is needed.

This shape distinguishes (a) from the prior state because the prior state's `/health` returns 503 within the 5s budget; the post-fix state returns 200. Deterministic, CI-friendly, no external surfaces.

**Alternative considered:** unit-test the new on_startup callback in isolation. Rejected — that tests method, not outcome (per ODD §8.2.10 "tests that test method"). The outcome is "/health returns 200 after process start"; the test must assert that outcome.

**Builder-flagged inference:** the test fixture must inject a FakeGraphiti via a seam memory-system already exposes (`make_graphiti` lives in `factory.py`; an env-var-controlled monkeypatch or a test-only `MEMORY_SYSTEM_FAKE_GRAPHITI=1` flag is the cheapest surface). Builder's call on the exact mechanism — the AC's outcome only requires that `/health` returns 200 within budget under a controlled init.

### D5. Backwards-compat: does the fix risk breaking the live MCP-tool-call path?

**Question:** the per-session lifespan currently *is* the only init point. If we move construction to startup, do we break the per-session path?

**Recommendation: minimally invasive change — keep the lifespan callable wired to the FastMCP instance for shutdown semantics, but populate `_graphiti` before the FastMCP-wrapped Starlette app starts serving.** Two compatible shapes:

1. **Pre-build before serve:** in `run()`, call `await _ensure_graphiti()` (a new coroutine that does what the lifespan body does, idempotent on re-entry) before `await mcp.run_streamable_http_async()`. The existing lifespan body becomes a no-op when `_graphiti` is already populated (idempotency check), and only does the close-on-exit work. Per-session enters of the lifespan still work; they just observe `_graphiti` already populated and skip rebuild.
2. **Starlette `on_startup` hook:** use FastMCP's `custom_route` mechanism (or directly add to `streamable_http_app().router.on_startup`) to register the same coroutine. Same effect; less direct entanglement with `run()`.

Both preserve the per-session `app.run` path (it still enters its lifespan; the wrapped lifespan body is now a no-op on the build side and runs close on process exit only). No tool-call regression because the tools call `_require_graphiti()` which observes the eagerly-populated `_graphiti`.

**The shape choice is method (builder's call).** The AC bounds the outcome.

**Risk:** if `make_graphiti` is invoked twice (once at startup, once per session), and is not idempotent, we double-construct. Mitigation: idempotency check in the new `_ensure_graphiti()` or `on_startup`. The current lifespan body is `_graphiti = await make_graphiti(); await _graphiti.build_indices_and_constraints()` — with an `if _graphiti is None:` guard, idempotent by construction. This is method-level mitigation; the builder owns it.

### D6. Audit-trail framing for amendment #24's regression

**Question:** how does this amendment characterise its relationship to amendment #24 — as a "missing AC" re-extension (ODD §4) or as a defect fix?

**Recommendation: re-extension under ODD §4.** Amendment #24's AC24.1 tested the lifespan body but not the lifespan invocation timing. The proper §4 framing is: a behaviour the proposal promised ("auto-starts," "exposes a health check") was not testable by AC24.1 because AC24.1 was scoped to lifespan body, not to process-startup outcome. AC34.1 promotes the outcome-shaped behaviour to a named criterion. The amendment commit message names this re-extension explicitly, the seal narrative records the lineage to #24, and amendment #24's seal stays untouched (no retroactive change to its AC list).

This matches the safety-layer A20 precedent: a behaviour the proposal promised, not testable by the existing criteria, gets re-extended as a new positive criterion in a follow-on amendment.

---

## 4. Family + spec-objective rationale (per CLAUDE.md §2.5 operational caution)

**Spec objective:** memory-system component, proposal §3.4 D1 (v1.0): *"the service auto-starts with the system, restarts on failure, **exposes a health check**, and is queryable through the MCP interface."*

The bug is a clean miss against the **"exposes a health check"** clause. The current behaviour ("`/health` returns 503 indefinitely under the deployed configuration") does not satisfy the outcome the proposal promised. This is sealed-component-amendment territory — the named spec objective exists, the work is to ship a test that asserts the outcome and code that satisfies it.

This is **not** dev-discipline (CLAUDE.md, tools/, docs/). The fix touches `memory-system/src/service.py` and `memory-system/tests/`. It is a sealed-component amendment by every property the operational caution lists: named spec objective, sealed component, code change.

**Component family:** memory-system, single component. Not part of Idea 9's workspace-identity family (per D1 in §3 above).

---

## 5. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude-leverage

What Claude capability does this lean on or extend? **None directly.** This is an internal-implementation defect inside a memory-sidecar process; it does not leverage or extend any Claude-Code primitive. The harness layer above (hands-off-lifecycle's launchd plist + phase-4b probe) consumes the service via a plain HTTP GET; the fix doesn't change that consumption shape.

This is consistent with CLAUDE.md's framing: lenses apply to *features*, and this is a sealed-component bugfix, not a feature. The lens 1 question is answerable as "N/A — internal bugfix"; the amendment is not a vehicle for adding Claude-native composition because there's no end-user surface change to compose with.

### Lens 2 — Harness + primary-persona value

**Primary-persona test** (does this reduce translation burden?): yes, indirectly. The current bug forces every fresh-clone first-run to fail phase-4b, which forces the user (or the primary persona on the user's behalf) to triage a confusing diagnostic ("service-health-timeout: pos.<slug>.memory") that points at memory-system but whose root cause is one layer below the visible failure. Fixing the bug removes a translation burden the persona was previously carrying — "the sidecar is unhealthy" → "actually no, it's fine, it just hasn't been pinged correctly" is exactly the kind of mechanism-detail the user should not have to learn.

**Harness test** (does this add to the toolkit?): no — it restores a toolkit capability (a working memory-sidecar after first-run) that the spec already promised but was silently missing. Net: harness test is "restores rather than expands," which is the correct shape for a defect fix.

### Lens 3 — ODD authoring

The plan authors a single new acceptance criterion (AC34.1) outcome-shaped against the spec text:

> **AC34.1.** A `python -m src.service` subprocess started under a controlled `make_graphiti` (FakeGraphiti) returns `200 OK` with a JSON body containing `workspace_root` from `GET /health` within 5 seconds of the subprocess entering its serve loop, without any MCP session being opened against the subprocess.

Outcome-shaped: "200 within 5s, no MCP session opened." Deterministic: subprocess + HTTP GET + assertion. No method-in-acceptance: doesn't say `on_startup`, doesn't say "register a Starlette hook," doesn't name a coroutine. The builder picks the mechanism; the test asserts the outcome.

ODD §2.5 reverse-direction check: the amendment introduces one new code path (the eager-init, whatever shape the builder picks) plus one new test. Both map back to AC34.1. No platform branches, no configuration options, no "might be useful later" surface.

---

## 6. Acceptance criteria

### AC34.1 — `/health` returns 200 with `workspace_root` after process start, without an MCP session

**Test file:** `memory-system/tests/test_AC34_eager_health_after_startup.py`
**Test function:** `test_AC34_1_health_returns_200_after_subprocess_serve_loop_entry`

A `python -m memory_system.service` (or `python -m src.service`, matching the launchd plist invocation contract — builder confirms the actual module path) subprocess started with:
- `GRAPHITI_SERVICE_HOST=127.0.0.1`
- `GRAPHITI_SERVICE_PORT=<test-allocated free port>`
- `POS_V2_WORKSPACE_ROOT=<test-fixture path>`
- A test-only seam that injects a FakeGraphiti in place of `make_graphiti` (env-var-controlled or import-shim — builder's call)

Returns `200 OK` from `GET http://127.0.0.1:<port>/health` within 5 seconds wall-clock of the subprocess being spawned, with a JSON response body containing `"workspace_root": "<test-fixture path>"`. The test issues only HTTP GET requests; no MCP `initialize` or other session-opening request is made.

**Maps to:**
- D1 spec clause "exposes a health check" (memory-system proposal §3.4)
- ODD §4 re-extension of amendment #24's missing outcome AC

**Code path satisfying it:** memory-system's service module (`memory-system/src/service.py`) gains an eager-init mechanism — Starlette `on_startup`, pre-`run_streamable_http_async` await, or equivalent process-startup construction of `_graphiti`. Method is the builder's call.

### AC34.2 — no regression on AC24.1–AC24.7, AC29.4, AC29.5

**Test file:** existing `memory-system/tests/test_service.py`, `memory-system/tests/test_AC29_service_port_binding.py`, `memory-system/tests/test_AC29_health_workspace_identity.py`
**Test function:** all existing AC24.* and AC29.* tests pass unchanged after the eager-init lands.

Specifically:
- AC24.1 (lifespan constructs and closes Graphiti): the lifespan body must remain re-entrant-safe / idempotent. If the fix shape is "make the lifespan body a no-op when `_graphiti` already populated," the existing test still passes because it operates on a freshly-imported module with `_graphiti = None` initially.
- AC24.6 (run launches streamable_http transport): still passes; the entry point shape doesn't change.
- AC29.4 (two subprocesses bind distinct ports): still passes; the fix doesn't touch port binding.
- AC29.5 (`/health` carries `workspace_root`, identity-aware probe verifies match): still passes; AC34.1's eager init makes AC29.5's probe actually-exercisable in CI (it currently only works for tests that bypass the launchd path and directly enter the lifespan).

**Maps to:** the no-regression guarantee implicit in any sealed-component amendment.

### AC34.3 — no sealed-component surface outside memory-system is modified

**Test file:** `memory-system/tests/test_no_sealed_amendments.py` (existing seal-diff test)
**Test:** the seal-diff invariant holds — `git diff --name-only BASELINE..SEAL_COMMIT` for memory-system shows changes only under `memory-system/` plus universal-paths (`docs/rebuild/plans/`).

Specifically: no edits to `hands-off-lifecycle/`, `workspace-bootstrap/`, or any other sealed component's source or tests.

**Maps to:** the per-amendment contamination invariant from amendment #6's seal-diff convention; D3 above.

---

## 7. Implementation order (suggested — builder's call to refine)

Per the scope-only-dispatch CDC, this section is advisory; the builder authors the actual order in their builder-plan.

1. Read session-start corpus: `docs/odd-methodology.md`, `docs/odd-in-pos.md`, `docs/rebuild/VALUE_PROPOSITION.md`, `docs/rebuild/STATE.md`, `docs/rebuild/FUTURE_IDEAS.md`, this plan, `memory-system/proposal.md` §3.4 D1, amendment-24 plan, amendment-29 plan.
2. Write builder-plan to `docs/rebuild/plans/amendment-34-memory-system-eager-lifespan-d1-conformance.builder-plan.md` naming the specific files + symbols expected to be touched.
3. Empirically reproduce the bug locally: build a memory-system venv, spawn `python -m src.service`, `curl /health`, observe 503.
4. Implement the eager-init shape the builder chose. Confirm 200 locally.
5. Author AC34.1 test using the test-only FakeGraphiti seam.
6. Run AC34.1 + full memory-system test suite. Both green.
7. Run hands-off-lifecycle and workspace-bootstrap seal-diff tests. Green (no changes there).
8. Skip pre-seal full rerun per the dispatch-speedups CDC.
9. Amendment commit (descriptive, not prescribed here).
10. `pos-amend apply --dry-run` green gate.
11. Seal commit via `pos-amend seal`; sidecar bump + narrative append.
12. Post-seal: seal-diff-only across all sealed components.

## 8. Out of scope

- No changes to the workspace-identity machinery from amendments #6, #28, #29.
- No changes to graphiti-core, kuzu-driver, the BGE reranker, the LLM client, or the embedder.
- No changes to the MCP transport shape, tool surface, or `streamable_http_path` setting.
- No changes to hands-off-lifecycle's phase-4b probe (its 60s budget, polling interval, identity-aware logic all stay).
- No changes to workspace-bootstrap's launchd plist template or scaffold flow.
- No new launchd-level health check (`KeepAlive { OtherJobEnabled }`, etc.) — out of scope; the fix lives at the application layer.
- No spec v1.x amendment. D1 is unchanged; this is a conformance fix.

## 9. Risks

### R1. Eager-init failure mode change

Currently: if `make_graphiti` fails (Ollama unreachable, Kuzu locked, Claude unauthed), the failure surfaces on the first MCP tool call. Post-fix: the failure surfaces at uvicorn startup; the process exits, launchd restarts it, and the cycle repeats inside `KeepAlive`'s back-off.

**Mitigation:** the AC bounds outcome (200 within 5s under FakeGraphiti). The real-world startup-failure path is operational, not test-time. Builder's call on whether to add a separate explicit error-surfacing mechanism (logging, structured exit code). Recommend keeping it minimal — uvicorn already logs the exception; launchd handles restart. The user-facing diagnostic at phase-4b is `service-health-timeout`, which is at least as actionable post-fix as pre-fix.

### R2. Idempotency-bug if the lifespan body runs twice

If the builder picks shape D5(1) (eager pre-build + leave lifespan body intact), `_ensure_graphiti()` and the lifespan body could both attempt to construct Graphiti. Mitigation: idempotency check in the new path (`if _graphiti is None: ...`).

If the builder picks D5(2) (Starlette `on_startup`), the lifespan body still runs per-session, and the same idempotency guard applies.

The existing AC24.1 test enters the lifespan once; it does not exercise the double-entry path. Builder may add a test for idempotency, or rely on the structural guard. Recommend the structural guard — `_graphiti is not None` is checkable in one line and matches the existing `_require_graphiti` pattern at line 61.

### R3. Live MCP tool path regression

Tools (add_episode, search, health, token_usage) call `_require_graphiti()` which raises if `_graphiti is None`. Post-fix, `_graphiti` is populated by the time uvicorn accepts requests, so the tool path works the same way it did pre-fix on a "warm" sidecar. Cold-path semantics improve (no first-call latency for `make_graphiti`).

The per-session lifespan still runs in the FastMCP framework — that's a framework property the fix doesn't change. As long as the lifespan body is idempotent on a populated `_graphiti`, the tool path stays green. AC24.1 + AC24.2 + AC24.3 cover the tool path; AC34.2 asserts they stay green.

### R4. Subprocess test flakiness

AC34.1 spawns a subprocess and polls a port. The 5s budget is generous for FakeGraphiti, but CI environments vary. Mitigation: AC29.4 already establishes the subprocess-bind-test pattern in this component; AC34.1 follows the same shape with one extra GET at the end. The test fixture chooses a free port via the standard "bind to 0, read assigned port" pattern (or whatever AC29.4 uses).

### R5. Hidden coupling to MCP-session-lifespan ordering

If any code currently relies on Graphiti being unconstructed until the first MCP session opens (e.g., a deferred-login pattern in the LLM client), eager-init breaks it. Audit: `make_graphiti` builds the LLM client (`ClaudePrintLLMClient`), embedder (Ollama), reranker (BGE-lazy), and Kuzu driver. None of those have known session-coupling — `ClaudePrintLLMClient` per amendment #8 spawns `claude -p` per call (not per session). `LazyBGERerankerClient` defers model load to first `rank()` call (per the proposal §1 explicit-wiring note). Ollama and Kuzu are local connections established at construction.

**Conclusion:** no known coupling. Builder confirms during implementation.

## 10. Halt triggers (builder halts + signals owner)

1. **Eager-init breaks AC24.1 in a way that can't be resolved by idempotency guards.** Halt; the design is wrong.
2. **An ODD-violating shape becomes strongly required** (e.g., the only working eager-init introduces a method-in-AC test or a non-objective code path). Halt; owner rules.
3. **`/health` cannot return `workspace_root` after eager-init for a reason that wasn't surfaced in §2.** Halt; the research has a gap.
4. **The fix requires a workspace-bootstrap or hands-off-lifecycle source change** (i.e., D3 was wrong). Halt; owner rules on whether to scope-expand or split into two amendments.
5. **Amendment-dispatch wall-time exceeds 60 minutes.** Halt with current state. Owner rules on split vs push-through.

## 11. Bookkeeping (`pos-amend` manifest)

Single component:

- **memory-system** — seal_test `memory-system/tests/test_no_sealed_amendments.py`, sidecar `memory-system/tests/SEAL_COMMIT`, `frozen_baseline: false`.

Universal paths: `docs/rebuild/plans/` (prefix); `CLAUDE.md` and `docs/odd-*.md` only if methodology shifts (this amendment doesn't shift methodology).

Narrative target: `memory-system/seals/SEAL_COMMIT.eager-lifespan-d1-conformance` (or equivalent, matching the existing narrative-naming convention). Body describes the D1 conformance lineage to amendment #24, names AC34.1 as the re-extended outcome criterion, cross-references amendment #29's AC29.5 (which AC34.1 makes actually-CI-exercisable).

## 12. Open questions for owner

- **Q1.** Plan recommends framing as D1-conformance defect (D1, D6 above). Confirm — or rule that the fix should ride Idea 9 instead.
- **Q2.** Plan recommends single-component amendment (D3). Confirm — or rule that hands-off-lifecycle should also gain a defensive AC (e.g., probe surfaces "503 initialising" diagnostically separate from "connection refused / 200 + identity mismatch"). Plan's lean: no — the fix is upstream of the probe; defensive ACs in the probe propagate the bug rather than fix it.
- **Q3.** Plan recommends the test-only FakeGraphiti seam be method (D4 builder-call). Confirm — or rule that the seam itself needs an explicit AC (e.g., "the service module exposes a documented test-only seam for substituting `make_graphiti`"). Plan's lean: no — the seam is internal-to-test scaffolding, not a runtime contract; an AC for it would be method-in-AC.

## 13. Dispatch-time additions (brief-phase material, not plan surface)

When the brief is drafted for the build dispatch, it will carry these CDC + ODD enforcement requirements verbatim:

- Working directory: `/Users/lukeivers/ivers-corp-pos-v2/`. No cd-out.
- Session-start corpus read mandatory before any code edit.
- Plan-before-code: builder writes its own builder-plan to disk before touching source.
- ODD §2.4 + §2.5: no method-in-acceptance, no non-objective-backed code.
- Strong-ODD-adherence: halt if the builder believes an ODD break is strongly required — do not silently apply.
- Scope-only downstream dispatches: if the builder spawns sub-agents, the brief is scope, not method.
- No `git commit --amend`.
- Amendment-dispatch speedups: narrow test scope to memory-system + seal-diff on others; skip pre-seal full rerun; methodology snippets inlined.

---

## 14. Method-decision record (builder, post-build)

The plan §3 left D4 (test shape) and D5 (eager-init shape) to the
builder. This section records the choices made and the rationale.

### D4 — test shape: subprocess-spawn + plain HTTP GET

Followed the §3 D4 recommendation verbatim. Subprocess script swaps
`service.make_graphiti` and `service.load_env` for fakes, calls
`service.run()`, and the parent test polls `127.0.0.1:<port>/health`
over plain HTTP. Test file:
`memory-system/tests/test_AC34_eager_health_after_startup.py`.

**Rationale:** AC29.4 already establishes the subprocess-bind-only
pattern in this component (no new framework introduced); the outcome
under test ("/health returns 200 within 5s without an MCP session")
is exactly what a plain HTTP GET measures. Unit-testing the eager-
init coroutine in isolation would test method, not outcome — rejected
per ODD §8.2.10.

### D5 — eager-init shape: option (1) pre-build before serve

`run()` awaits a new idempotent coroutine `_ensure_graphiti()` before
entering `mcp.run_streamable_http_async()`. Both run inside a single
`asyncio.run` call so the event loop is shared. The existing
`lifespan` body's construct half delegates to `_ensure_graphiti()`,
making per-MCP-session enters no-ops on the construct side; the
yield/finally close-on-exit half preserves verbatim. Idempotency
guard: `if _graphiti is not None: return`.

**Rationale:** option (2) (Starlette `on_startup`) was rejected after
empirical verification that the FastMCP-returned Starlette app's
modern `Router` exposes no post-hoc `add_event_handler` /
`on_startup` (verified — `app.router.on_startup` raises
`AttributeError`). Option (1) is a one-coroutine + one-`run()`-edit
change. The idempotency guard mirrors the existing
`_require_graphiti()` pattern at service.py line 61.

### Test results

- AC34.1 + AC34.2 + AC34.3: 3/3 green.
- AC24.1–AC24.7: 9/9 green (no regression).
- AC29.1, AC29.4, AC29.5: 3/3 green (no regression).
- Full memory-system suite: 90 passed, 1 skipped (the slow chaos test
  excluded by default), 0 failed.
- Cross-component seal-diff tests: 11/11 sealed components green.
- `pos-amend apply --dry-run`: green.

### Commit SHAs

- Amendment commit: `135398d372bb6398d2d78eec0e14406cc031d18e` —
  `fix(memory-system): eager lifespan / D1 health-check conformance — amendment #34`
- Seal commit: `ee52a15a0d3ef115945b00df7509f13a062f020e` —
  `chore(seals): memory-system-eager-lifespan-d1-conformance seal — memory-system at 135398d`
