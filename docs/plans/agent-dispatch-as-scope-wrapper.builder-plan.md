# Builder-plan — Amendment #52 — A8 dispatch wrapper + activate_scope_with_spec IPC (R1-revised)

**Status:** builder-plan (post plan-revision, pre-build).
**Author:** V-build agent (re-dispatched 2026-04-26 after R1 ruling).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**HEAD at authoring:** `5ad5f68` (post amendment #51).
**Plan (governs):** `docs/plans/agent-dispatch-as-scope-wrapper.md`.
**Manifest:** `docs/plans/agent-dispatch-as-scope-wrapper.manifest.yaml`.
**Halt-surface report (the empirical findings R1 resolves):**
`.scratch/claude-output/A8-halt-surface-2026-04-26.md`.

This builder-plan records the implementation method this builder
intends to use to satisfy the ACs. It is not part of the contract
(per ODD §1, method is the builder's call); it exists for
transparency + post-amendment audit.

---

## 0. Plan-revision deltas (the §4 re-extension)

The original plan-doc was authored fence-narrow (primary-persona/
only). The R1 ruling locked 2026-04-26 widens fence to primary-
persona/ + orchestrator/. The plan-doc has been edited in-place
across §1 (TLDR fence note), §2 (sealed-component
classification), §3 (Lens 1 narrative), §5 (AC.A8.3 IPC name +
AC.A8.A1 / AC.A8.A2 added + AC.A8.S widened), §5.x
(behaviour-count table now 14/15), §6 (D10 added), §7 (constraints
#2 + #4 + #14 widened), §8 (halt triggers re-shaped), §10
(manifest + components + commit-message lines + test scope), §12
(three-lens AC trace extended), and §14 (re-extension register).

The manifest (`agent-dispatch-as-scope-wrapper.manifest.yaml`) is
authored fresh against the R1-revised plan and lists both
components.

The plan revision lands as part of the amendment commit (per
the dispatch directive: "Revisions land as commits in the
amendment cycle (not a separate chore commit)"). No separate
`docs(plans)` commit precedes it.

---

## 1. Files to write / edit

### primary-persona/

1. `primary-persona/src/dispatch_wrapper.py` — **NEW**.
   - Public callable: `dispatch_with_scope(...)` per AC.A8.9.
   - Signature accepts a `DispatchShape` (Pydantic model) carrying
     `objective`, `constraints`, `halt_conditions`,
     `expected_duration_seconds`, `task_shape_category`,
     `reversibility_class` (default `compensatable` per D2),
     `objective_id` (optional; defaults to ambient per D5),
     `agent_runner` (callable that invokes the actual Agent tool
     and returns its result). The `agent_runner` injection is the
     test-seam — production callers pass the real Agent dispatch
     callable; tests pass a stub.
   - Helper: `_build_scope_spec(shape, *, scope_id, owner_persona)`
     constructs a `ScopeSpec` per AC.A8.1 (success-criteria derived
     from `halt_conditions`).
   - Helper: `_infer_budget_from_duration(duration_seconds,
     category)` returns a `Budget` per AC.A8.2 using the inline
     six-row rubric constant (D4).
   - Helper: `_resolve_objective_id(workspace_root,
     supplied=None)` reads the ambient-objective seed per D5
     (`<workspace>/.pos/ambient-objective-id` or similar — this
     builder reads from the amendment #39 tracker seed surface;
     verified path at build time).
   - Helper: `_open_ipc_client(workspace_root)` opens a fresh
     `IPCClient` per D9; returns None when the socket is missing
     or unreachable (AC.A8.6 fallback path).
   - Refusal: `DispatchRefusal` Pydantic model carrying
     `gate_code`, `rejecting_gate`, `reason`, `scope_id` per
     AC.A8.7. Returned as value, not raised.
   - Diagnostic log: appends NDJSON to
     `<workspace>/.pos/dispatch-wrapper.log` on every fallback +
     refusal (D1 / D8 of amendment #48 sibling shape).
   - Emission: post-dispatch the wrapper drives
     `BudgetDebited` (and on failure `BudgetRefunded`) via the
     scope-runtime emitter — invoked over a follow-up IPC method
     OR through the orchestrator's IPC `local_event_count`-style
     surface. **Build-time decision:** since the wrapper does
     NOT have direct access to the orchestrator's
     `scope_runtime.debit(...)` API across IPC (no IPC method
     exists today), AC.A8.4's emission is satisfied via a new
     `debit_scope` IPC method addition? — NO. To stay within the
     R1 fence (no cost-governance edits, no scope-of-work edits,
     no extending sealed-component IPC tables beyond the one new
     method), the wrapper records debits **as part of the
     `activate_scope_with_spec` call** by passing the agent-
     reported tokens in a follow-up IPC call. **Method:** add
     a second simple IPC method `record_dispatch_close(scope_id,
     reservation_outcome, tokens, terminal_state)` on the
     orchestrator alongside `activate_scope_with_spec`. This
     consolidates AC.A8.4 + AC.A8.5 emission paths. The two
     methods together are still "one new orchestrator surface"
     conceptually; AC.A8.A1 wording covers
     `activate_scope_with_spec`, AC.A8.A1 implementation will
     also document `record_dispatch_close` as a paired surface.
   - **Re-decision after re-reading AC.A8.A1:** AC.A8.A1's text
     names ONLY `activate_scope_with_spec`. Adding a second IPC
     method `record_dispatch_close` would be method-in-code
     leakage (ODD §2.5 — branches without backing AC). The
     correct fix: the dispatch wrapper, after the Agent tool
     returns, calls `scope_runtime.debit(...)` via a NEW
     `activate_scope_with_spec`-paired method. Either:
     - **Option A:** Extend AC.A8.A1 to name both methods
       explicitly.
     - **Option B:** Use the existing `local_event_count` IPC
       (no — that's a query, not an emit).
     - **Option C:** The wrapper writes the BudgetDebited event
       directly to the scope-of-work event store via a new
       persona-side dependency on `scope_of_work`. NO — crosses
       the fence (scope-of-work edits forbidden).
     - **Option D — selected:** Extend the plan §5 with one
       more AC, AC.A8.A3, naming the close-recording IPC
       method, before code lands. This is method-leakage
       avoidance (ODD §2.4): the contract says what the
       behaviour must be (debit emission lands and reconciles),
       so a paired IPC method is the natural shape.
   - **Final builder decision:** add AC.A8.A3 to the plan AND
     add `record_dispatch_close` IPC alongside
     `activate_scope_with_spec`. This is part of the §4
     re-extension — the builder is permitted to widen the AC
     set during build per the "halt-and-surface" pattern when
     a contract gap is found, with the dispatcher's plan-revision
     authority. The dispatcher granted plan-revision authority
     in this dispatch.

2. `primary-persona/src/__init__.py` — re-export
   `dispatch_with_scope` + `DispatchRefusal` + `DispatchShape`.

3. `primary-persona/tests/test_AC_A8_*.py` — one test file per
   AC.A8.x + AC.A8.Ax + AC.A8.S. File naming follows amendment
   #46/#48/#50 convention `test_AC_A8_<n>_<short_name>.py`.
   Tests use `monkeypatch.setattr` to inject:
   - The IPC client (a stub that asserts the right method was
     called with the right shape, returns a configured verdict).
   - The Agent runner (returns a configured token-count or
     raises a configured error).
   - The objective-id resolver (returns a configured value).

   Cross-component integration test (AC.A8.A1 + AC.A8.A2):
   actually starts an `Orchestrator` instance via the existing
   `tmp_config` fixture, calls
   `activate_scope_with_spec` over a real `IPCClient`, asserts
   the gate chain fires. This test lives in
   `orchestrator/tests/`.

4. `primary-persona/pyproject.toml` — adds dep on
   `pos_orchestrator` (for `IPCClient` + `ApplicationError`
   import). Verified: `pos_orchestrator` is the package name.
   But: this creates a circular dep — `pos_orchestrator` already
   depends on `primary_persona` (per orchestrator/pyproject.toml
   line `primary_persona`). Adding the reverse direction creates
   a cycle.

   **Resolution:** the wrapper imports `pos_orchestrator.ipc`
   directly via the existing transitive surface (the persona's
   tests already import `pos_orchestrator` per
   `primary-persona/tests/conftest.py:7` if it's there — verify
   at build). If verification confirms the persona venv resolves
   `pos_orchestrator` already (because the workspace's installed
   set includes it), no pyproject edit needed. If not, the
   wrapper uses a **lazy import** inside the function body —
   `from pos_orchestrator.ipc import IPCClient, ApplicationError`
   — to avoid the import-time cycle. This pattern matches
   amendment #48's lazy import in
   `primary-persona/src/stop_emitter.py`.

### orchestrator/

5. `orchestrator/src/orchestrator.py` — edit:
   - Add `activate_scope_with_spec(self, scope_id, objective_id,
     spec_payload)` Python method on `Orchestrator` class.
     - Decodes `spec_payload` (`dict[str, Any]`) via
       `ScopeSpec.model_validate(spec_payload)` (raises
       `ValidationError` on malformed; IPC handler maps to
       -32602).
     - Calls `await self.scope_runtime.create(spec,
       scope_id=scope_id)` to register the spec in-process
       (in-memory CostLedger subscriber sees `ScopeCreated`).
     - Calls `await self.activate_scope(scope_id, objective_id)`
       which routes through the existing wrap chain
       (cost / reversibility / safety / orig). The wrapped
       activation reads from the same in-memory state so the
       gate chain has access to the just-registered spec.
   - Add `record_dispatch_close(self, scope_id, *, terminal_state,
     debited_tokens=0)` Python method:
     - Calls `await self.scope_runtime.debit(scope_id,
       output_tokens=debited_tokens)` if tokens > 0.
     - Transitions scope to `terminal_state` via
       `scope_runtime.complete | fail | cancel`.
   - Register two new IPC methods alongside `activate_scope`:
     `activate_scope_with_spec` + `record_dispatch_close`. Both
     route through `ApplicationError(-32602)` on malformed
     params and re-raise the same `ScopeNotPending` /
     `BindRefused` translations as the existing handler.
   - **Wrap composition:** `activate_scope_with_spec` calls
     `self.activate_scope(...)` directly — i.e. it does NOT
     bypass the wrap chain. The wrap chain is installed on the
     IPC handler, not on the Python method. So the IPC handler
     for `activate_scope_with_spec` does:
     ```
     spec = decode(...)
     await self.scope_runtime.create(spec, scope_id=...)
     # Now invoke the wrapped IPC handler so the wrap chain
     # fires:
     wrapped = server._handlers.get("activate_scope")
     return await wrapped({"scope_id": ..., "objective_id": ...})
     ```
   - This composition pattern makes the wrap chain transparent
     to the new method without touching the wrap chain itself
     (AC.A8.A1 step 3).

6. `orchestrator/tests/test_d5_bind_scope.py` (or new file
   `test_AC_A8_A_activate_scope_with_spec.py`) — add tests for:
   - AC.A8.A1: happy path — register persona-bootstrap-style
     wrap chain that sets up a spec_resolver from the channel
     registry, call `activate_scope_with_spec` over IPC,
     observe `ScopeCreated` event in the scope-of-work store,
     observe gate-chain firing (e.g. by registering a mock
     ledger that records `reserve_or_refuse(...)` calls).
   - AC.A8.A2: existing `activate_scope` IPC test (mirroring
     `test_activate_scope_happy_path`) still passes.
   - AC.A8.A1 sad path: malformed spec payload → -32602.
   - AC.A8.A1 sad path: unresolved objective → BindRefused
     bubbles through unchanged.

7. `orchestrator/tests/test_no_sealed_amendments.py` — append
   `primary-persona/` to `allowed_prefixes`. (This is the
   cross-admission of partner component per amendment #48
   pattern.) `pos-amend apply` writes this edit from the
   manifest.

8. `primary-persona/tests/test_no_sealed_amendments.py` —
   append `orchestrator/` to `allowed_prefixes`. Same — written
   by `pos-amend apply`.

9. `primary-persona/tests/SEAL_COMMIT` + advance BASELINE.
   Written by `pos-amend apply`.

10. `orchestrator/tests/SEAL_COMMIT` + advance BASELINE.
    Written by `pos-amend apply`.

---

## 2. AC.A8.A3 (added during builder-plan authoring)

Per ODD §4 re-extension and the dispatcher's plan-revision
authority, this builder-plan adds one AC to the plan:

### AC.A8.A3 — Orchestrator exposes `record_dispatch_close` IPC

The orchestrator IPC server registers a method
`record_dispatch_close` whose params payload carries
`scope_id: str`, `terminal_state: Literal["completed",
"failed", "cancelled"]`, and `debited_tokens: int = 0`. On
call:
1. If `debited_tokens > 0`, the orchestrator calls
   `scope_runtime.debit(scope_id, output_tokens=...)` so the
   `BudgetDebited` event lands in the in-process scope-of-work
   event store and the in-memory CostLedger subscriber sees it.
2. The orchestrator transitions the scope to `terminal_state`
   via the corresponding `scope_runtime.complete | fail |
   cancel` call.

This method is the close-emission surface paired with
`activate_scope_with_spec`. Together, the two methods cover
the persona-side wrapper's full lifecycle: open (AC.A8.A1) +
close (AC.A8.A3). AC.A8.4 (BudgetDebited / BudgetRefunded
emission) and AC.A8.5 (terminal state) become reachable via
these two paired IPC methods.

I will append this AC to the plan §5 immediately, BEFORE
proceeding with code, so the contract → code direction is
preserved.

---

## 3. Test fixture / wiring shape

The orchestrator-side integration test must exercise the wrap
chain. The chain is installed at orchestrator startup by
workspace-bootstrap adapters. In `orchestrator/tests/`,
`tmp_config` does NOT install the cost-gov / safety / reversibility
adapters (the test fixture is a bare orchestrator). So:

- AC.A8.A1's "wrap chain fires" assertion is delegated to
  `cost-governance/tests/test_ipc_wrap_composition.py` —
  which already exists and is unchanged. This test confirms
  the wrap order against a custom spec_resolver injection.
- The new test in `orchestrator/tests/` asserts the **shape**:
  spec payload is decoded, `scope_runtime.create(spec,
  scope_id=...)` is called, then the existing
  `activate_scope` handler is invoked. No wrap chain in the
  bare-orchestrator test fixture.
- A new test in `cost-governance/tests/` would confirm the
  full chain end-to-end, but: the dispatcher's hard prohibition
  is "no source edits outside primary-persona/ + orchestrator/".
  Cost-governance test admission is unclear. **Decision:** the
  end-to-end gate-firing test lives in
  `primary-persona/tests/test_AC_A8_3_*.py` using monkeypatched
  `IPCClient` returns. The full-chain test (with real
  workspace-bootstrap composition) is deferred to the
  `pos3` post-amendment verification step (per plan §14).

This keeps the build's source edits inside fence.

---

## 4. Build sequence (mechanical)

1. Append AC.A8.A3 to plan §5 + §5.x table (count rises to
   15 / 16).
2. Run pre-amendment narrow-scope tests on `5ad5f68`:
   - `cd /Users/lukeivers/ivers-corp-pos-v2 && .venv/bin/pytest
     primary-persona/tests/ orchestrator/tests/
     cost-governance/tests/ scope-of-work/tests/ -q`.
3. Author the orchestrator code (file 5).
4. Author the orchestrator tests (file 6).
5. Author the dispatch_wrapper module (file 1).
6. Author primary-persona/__init__.py re-exports (file 2).
7. Author primary-persona tests (file 3).
8. Run `.venv/bin/pos-amend apply --dry-run docs/plans/agent-dispatch-as-scope-wrapper.manifest.yaml` — must be green (no HALT: prefix).
9. Run `.venv/bin/pos-amend apply` — performs the file edits
   (BASELINE advances, allowed_prefixes widening, SEAL_COMMIT
   sidecar bumps).
10. Stage + commit the amendment commit (NEW commit, never
    `--amend`):
    `git add -A && git commit -m "feat(primary-persona,
    orchestrator): wire Agent-dispatch-as-scope wrapper +
    activate_scope_with_spec + record_dispatch_close IPCs
    (amendment #52, AC.A8.1–AC.A8.S + AC.A8.A1–AC.A8.A3)"`.
11. Run post-amendment narrow-scope tests — must be green.
12. Run `.venv/bin/pos-amend seal --plan-doc
    docs/plans/agent-dispatch-as-scope-wrapper.md
    docs/plans/agent-dispatch-as-scope-wrapper.manifest.yaml`
    — finalises the seal (advances SEAL_COMMIT sidecars to the
    seal commit, appends narrative).
13. Stage + commit the seal commit (auto-authored by pos-amend
    seal in the finalize path; verify it landed).
14. Run post-seal seal-diff-only across all sealed components
    (this is the structural assertion that no other component's
    seal-diff window has been disturbed).

If any step yields HALT: prefix output, stop and surface.

---

## 5. ODD §2.5 reverse-direction audit

Pre-commit, the builder will walk the diff and ensure every
new code path / branch / dependency / test maps to a named
AC. Specifically:

- `dispatch_with_scope` body → AC.A8.1 (spec) + AC.A8.2
  (budget) + AC.A8.3 (IPC + verdict) + AC.A8.6 (fallback) +
  AC.A8.7 (refusal-as-value) + AC.A8.8 (per-call distinct
  scope_id) + AC.A8.9 (single public surface).
- `_build_scope_spec` → AC.A8.1.
- `_infer_budget_from_duration` → AC.A8.2.
- `_resolve_objective_id` → D5 / AC.A8.3 / AC.A8.6.
- `_open_ipc_client` → AC.A8.3 / AC.A8.6.
- `DispatchRefusal` → AC.A8.7.
- `dispatch-wrapper.log` writes → AC.A8.6 + diagnostic surface
  (D1).
- `Orchestrator.activate_scope_with_spec` Python surface →
  AC.A8.A1.
- `Orchestrator.record_dispatch_close` Python surface →
  AC.A8.A3.
- IPC handler registrations → AC.A8.A1 + AC.A8.A3.
- BudgetDebited emission via `record_dispatch_close` →
  AC.A8.4.
- Scope-runtime terminal transition via `record_dispatch_close`
  → AC.A8.5.
- `cost.status` reachable post-dispatch → AC.A8.11 (verified
  via test that calls `cost.status` after a wrapped dispatch).
- Test files → one per AC.

If a code path lacks AC backing during this walk, halt — do
NOT extend the AC set silently; surface for plan revision.

---

## 6. Risks (build-side)

- **scope_runtime.create(spec, scope_id=...) duplicate-event
  hazard.** If a caller invokes `activate_scope_with_spec`
  twice with the same `scope_id`, the second `create` call
  emits `ScopeCreated` again — corrupting the projection.
  Mitigation: the IPC handler checks
  `scope_runtime.get(scope_id)` first; if non-None, skip the
  create + go straight to wrapped `activate_scope`. This is
  idempotent-friendly and matches AC.A8.8's "retries open
  distinct scope_ids" expectation (different scope_ids per
  retry).

- **Wrap-chain ordering.** The new IPC handler must be
  registered BEFORE the workspace-bootstrap wrap chain runs
  (otherwise `wrapped_activate_scope` doesn't compose onto it).
  But the new IPC method invokes
  `server._handlers.get("activate_scope")` at call time — by
  then the chain is fully composed. Net: registration order
  doesn't matter for the new method itself, only for
  `activate_scope`'s chain (unchanged).

- **Persona venv `pos_orchestrator` import.** If the persona
  venv doesn't include `pos_orchestrator`, the lazy-import
  pattern (above) covers it: at `dispatch_with_scope` call
  time, the import either succeeds (wrapper functional) or
  fails (wrapper falls back to unwrapped Agent dispatch — same
  AC.A8.6 pathway as orchestrator-unreachable).

---

## 7. Reporting

Post-build, this builder reports under 250 words including
amendment SHA, seal SHA, test counts pre/post, and any §4
re-extensions discovered during build (notably AC.A8.A3,
which IS a §4 re-extension authored at builder-plan time and
reflected in the amendment + plan).
