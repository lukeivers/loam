# Plan — Amendment #29: per-workspace memory-sidecar port + workspace-identity health probe

**Status:** authored 2026-04-24. **Owner rulings:** D1 (re-extend under Idea 9, no spec v1.x amendment), D2 (multi-component), D3 (S1 — per-workspace port via memory.yaml seam), D6 (folded as AC29.5). Approved via Luke's "good on bandwidth" (2026-04-23). **Research:** `docs/rebuild/plans/research/memory-sidecar-port-workspace-scoping.md` (905 lines).

**Pre-amendment tip:** to be captured at brief-dispatch time. **Amendment number:** assigned sequentially at build-dispatch time per owner ruling 2026-04-24 — the filename's `#29` is a placeholder used for authoring; the actual number is whatever the next one is at the moment the build agent starts. Rename the file and update the plan's references accordingly at dispatch.

---

## 1. Objective

Close the workspace-identity leak in the memory-sidecar's port binding and its health-probe contract, so that two pos-v2 workspaces on one host can run memory sidecars concurrently without port collision and so that a workspace's health probe cannot be satisfied by another workspace's (or an orphan's) service.

## 2. Hard constraints

1. **Multi-component, three sealed surfaces only.** memory-system, workspace-bootstrap, hands-off-lifecycle. If a fourth sealed component needs touching → halt and signal.
2. **Re-extend under `FUTURE_IDEAS.md` Idea 9.** No spec v1.0/v1.1/v1.2 amendment. Precedent: amendments #6 (namespaced labels) and #28 (workspace-identity-routed first-run state) landed via the same pattern.
3. **No amend.** Corrective commits only if something misses.
4. **No retroactive changes to other sealed components' surfaces.** The amendment touches only the port-binding and probe-path surfaces it names.
5. **`pos-amend` manifest is the bookkeeping interface.** No hand-edits to BASELINE literals or sidecars. `pos-amend apply --dry-run` must exit 0 before the amendment commit lands.
6. **Amendment-dispatch speedups apply** (per `feedback_amendment_dispatch_speedups.md`): narrow test scope to touched components + seal-diff on untouched; skip pre-seal full-rerun; methodology snippets inlined.
7. **The research doc's S1 shape is the binding ruling.** Method at the code level (exact field names, file layouts, config-key names) is the builder's call in the eventual plan, not prescribed here.

## 3. Acceptance criteria (AC29.x)

Each AC maps to at least one test function named `test_AC29_<n>_<slug>` in the appropriate sealed component's test tree.

### AC29.1 — memory-system binds to the port it is told to bind to

The memory-system service resolves its listen port from the existing `GRAPHITI_SERVICE_PORT` env var (or its replacement seam, builder's call) with no host-global default that collides across workspaces. A test constructs the FastMCP server under two different port values and asserts the server's configured port reflects the value passed, not a hardcoded constant.

### AC29.2 — workspace-bootstrap scaffold emits a per-workspace port

The `workspace-bootstrap` first-run scaffold resolves a port value from the workspace's `memory.yaml` (or the equivalent workspace-local config) and propagates it to:
- the launchd plist's `EnvironmentVariables` (so `GRAPHITI_SERVICE_PORT` reaches the service),
- the first-run inventory's `services[].health.port` entry (so the health probe aims at the right port).

Two scaffold invocations with distinct workspace-roots produce plists + inventories with distinct port values. Test covers the propagation from config → plist and config → inventory.

### AC29.3 — port source is workspace-local, not host-global

The port value written by the scaffold is derived from the workspace's own config (e.g., `memory.yaml` under the workspace root), not from a host-global source. Two workspaces on the same host whose `memory.yaml` files name different ports produce different plists without any shared state. Test: mutating one workspace's config does not affect the other's scaffold output.

### AC29.4 — two memory-system subprocess instances bind distinct ports without EADDRINUSE

**Owner ruling (2026-04-24):** subprocess-bind-only shape. No full graphiti init, no Ollama, no `claude -p`.

A CI-friendly subprocess-spawn test starts two memory-system subprocess instances concurrently with distinct `GRAPHITI_SERVICE_PORT` values on `127.0.0.1` and asserts both bind their declared ports without either raising `EADDRINUSE`. This test proves the port-bind regression class without requiring real external surfaces (launchd/keychain/Ollama/claude CLI).

Full-stack coexistence (claude-authed + Ollama-reachable + both `/health` → 200 concurrently) is covered by a documented manual-repro script at `memory-system/tests/integration/coexistence.sh` — operators run it by hand post-amendment to verify. NOT a CI gate. Keeping heavy-apparatus integration testing out of the seal surface avoids the POST_FIRST_RUN_REVIEW entry #3 anti-pattern (AC tests that mock too close to the boundary).

### AC29.5 — /health response carries workspace identity; probe verifies match (D6 fold-in)

The memory-system's `/health` response body includes a `workspace_root` (or `workspace_slug`, builder's call on naming) field identifying the workspace whose sidecar is responding. The first-run phase-4b health probe in `hands-off-lifecycle` verifies the response body's workspace identity matches the probing workspace's own identity. A test constructs a stub HTTP server on the probed port that returns 200 with a mismatched workspace identity → the probe fails with a diagnostic naming the mismatch. A second test with matching identity → the probe succeeds.

### AC29.6 — no sealed-component surface outside the three named components is modified

`git diff --name-only BASELINE..SEAL_COMMIT` shows changes only under `memory-system/`, `workspace-bootstrap/`, `hands-off-lifecycle/`, and universal-paths (`docs/rebuild/plans/`, `CLAUDE.md` if methodology shifted, `docs/odd-*.md` if methodology shifted). No orchestrator, primary-persona, scope-of-work, objective-tracker, observability-aggregator, self-upgrade, safety-layer, reversibility-primitive, cost-governance, self-correction, or telegram-interface source or test changes.

### AC29.7 — no regression on amendments #6, #24, #28

Seal-diff tests on hands-off-lifecycle, memory-system, and workspace-bootstrap all exit green after the seal commit. Specifically: amendment #28's workspace-identity-routed first-run state remains workspace-local; amendment #6's namespaced labels remain slug-scoped; amendment #24's MCP transport surface remains the four-tool set (`add_episode`, `search`, `health`, `token_usage`).

## 4. Implementation order (suggested — builder's call to refine)

1. Build-agent reads session-start corpus: `docs/odd-methodology.md`, `docs/odd-in-pos.md`, `docs/rebuild/VALUE_PROPOSITION.md`, `docs/rebuild/STATE.md`, `docs/rebuild/FUTURE_IDEAS.md`, this plan, and the research doc.
2. Build-agent writes its own **build plan** to `docs/rebuild/plans/amendment-29-per-workspace-memory-sidecar-port.builder-plan.md` naming the specific files + symbols it expects to touch, before any code edit. (per plan-before-code CDC)
3. Pre-amendment test runs: full suite on the three touched components; seal-diff-only on the other eight.
4. Land the three-component changes in the amendment commit.
5. `pos-amend apply --dry-run` green gate.
6. Amendment commit (descriptive, not prescribed here).
7. Seal commit via `pos-amend seal`; sidecar bumps + narrative append.
8. Post-seal: seal-diff-only across all sealed components.

## 5. Out of scope

- No changes to graphiti-core, kuzu-driver, or the BGE reranker surface. The LLM/embedder/reranker paths are untouched.
- No changes to the MCP transport shape or tool surface. Amendment #24 is fresh and stable.
- No consumer-wiring work. That's D7, a separate research cycle.
- No Idea-8 context-load-gate work. That's D8, a separate research cycle.
- No D4/D5 env-scrubber or plist-env work. Those are independent amendments running in parallel.
- No orphan-plist cleanup tooling. That's D9, deferred.
- No spec v1.x amendment. Re-extension under Idea 9 per D1.

## 6. Halt triggers (builder halts + signals owner)

1. **Fourth sealed component turns out to require changes.** Halt and signal; do not expand scope silently.
2. **An AC requires a method-in-acceptance shape** (e.g., test cannot be authored outcome-first without prescribing an implementation detail). Halt, signal, author as §4 re-extension up the objective chain — don't bury as a method-coupled test.
3. **ODD break detected as strongly required.** If the builder believes an ODD-violating code path is unavoidable (silent exception, method-in-AC, non-objective-backed code), halt and signal with the specific conflict named. Owner rules.
4. **Spec objective gap surfaces.** If research or implementation reveals that a spec v1.x objective IS needed (the re-extension path is no longer viable), halt and signal. Owner rules on spec-amendment vs scope-reduction.
5. **Amendment-dispatch budget overrun.** If the amendment trends >90 minutes of background-agent wall-time, halt and signal with the current state. Owner rules on split vs push-through.

## 7. Bookkeeping (pos-amend manifest)

Three manifest components:

- **memory-system** — seal_test `memory-system/tests/test_no_sealed_amendments.py`, sidecar `memory-system/tests/SEAL_COMMIT`, `frozen_baseline: false`.
- **workspace-bootstrap** — seal_test `workspace-bootstrap/tests/test_no_sealed_amendments.py`, sidecar per existing convention, `frozen_baseline: false`.
- **hands-off-lifecycle** — seal_test `hands-off-lifecycle/tests/test_cross_cutting.py`, sidecar per existing convention, `frozen_baseline: true` (H19 pinned at project-start per amendment #23).

Universal paths: `docs/rebuild/plans/` (prefix), `CLAUDE.md`, `docs/odd-in-pos.md`, `docs/odd-methodology.md`, `docs/rebuild/FUTURE_IDEAS.md` (files).

Narrative target: `hands-off-lifecycle/seals/SEAL_COMMIT.per-workspace-memory-port` (or equivalent). Narrative body describes D1/D2/D3/D6 rulings, S1 shape rationale, multi-component boundary, AC29.5 folded from D6.

## 8. Dispatch-time additions (brief-phase material, not plan surface)

When the brief is drafted for the build dispatch, it will carry these CDC + ODD enforcement requirements verbatim (reproduced here for visibility, not prescribed here as method):

- Working directory: `/Users/lukeivers/ivers-corp-pos-v2/`. No cd-out.
- Session-start corpus read mandatory before any code edit.
- Plan-before-code: builder writes its own build plan to disk before touching source.
- ODD §2.4 + §2.5: no method-in-acceptance, no non-objective-backed code.
- Strong-ODD-adherence: halt if the builder believes an ODD break is strongly required — do not silently apply.
- Scope-only downstream dispatches: if the builder spawns sub-agents, the brief is scope, not method.
- No `git commit --amend`.
