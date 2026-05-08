# Research Plan — Workspace Bootstrap

**Component:** Workspace Bootstrap — the framework that composes the ten sealed foundational components into a running orchestrator + gate chain, plus the adapter bundle for the foundational ten, plus the extension protocol that future Phase 4+ components use to register themselves without amending bootstrap.
**Status:** DRAFT — awaiting owner's approval before research begins.

**Phase 4 opens on this component.**

---

## Objective this research must serve

Identify the design shape for workspace bootstrap such that:

- A workspace boots by composing the ten sealed foundational components through a framework + adapter bundle pattern, with the three-gate chain wired in correct order (safety outermost, reversibility middle, cost innermost) and the non-wrap components (self-correction, primary-persona, observability aggregator, etc.) registered correctly alongside.
- Future Phase 4+ components register themselves into the running workspace via a published extension protocol — without amending the bootstrap package, without unsealing any foundational component, and without the workspace author having to change bootstrap's code.
- Ordering declarations on contributions (e.g. "wraps safety," "subscribes after cost reconciliation," "runs during session-start phase") are resolved by the framework's ordering engine; unsatisfiable orderings fail-closed at boot with a clear diagnostic.
- The framework's extension surface is the **highest-stakes design decision** in the component — if it is wrong, bootstrap becomes the thing we have to unseal when Phase 4+ components ship. The framework must therefore be over-engineered toward extensibility, under-engineered toward feature count.
- The existing orchestrator `~/.pos/bootstrap.py` primitive is either composed into this component's framework or subsumed cleanly — no regression on the "workspace-authored register(orchestrator)" escape hatch the orchestrator already ships.

## Starting position

- **Ten sealed components on `pos-v2`** at commit `65acb97` (self-correction seal). Each exposes a factored registration entry point:
  - `safety-layer/src/ipc_wiring.py` → `register_safety_ipc(server, ...)`
  - `reversibility-primitive/src/ipc_wiring.py` → `register_reversibility_ipc(server, ...)`
  - `cost-governance/src/ipc_wiring.py` → `register_cost_governance_ipc(server, ...)`
  - `self-correction/src/ipc.py` → self-correction controller + IPC registration
  - `orchestrator/src/bootstrap.py` → already ships the `load_and_register(bootstrap_path, orchestrator)` primitive loading `~/.pos/bootstrap.py`
  - Primary-persona, observability-aggregator, graceful-degradation, objective-tracker, self-upgrade — each contribute config loaders, subscriptions, or IPC methods without a uniform "wiring.py" pattern (they're consumed via their runtimes, not via discrete register-calls).
- **Precedent for sidecar/wrap — quintuple** (objective-tracker, safety, reversibility, cost, self-correction). Bootstrap does not add an activation wrap; it orchestrates the registration of the ones that exist.
- **the owner's architectural ruling 2026-04-20 13:56:** the bootstrap component has two layers — (1) the framework (discovery, ordering, adapter interface, `main()`) and (2) the foundational-ten adapter bundle. Future Phase 4+ components ship their own adapter files in their own packages and register via a published extension protocol. Bootstrap can be sealed; future components add to themselves, not to bootstrap.

## Questions the research must answer

### 1. Discovery protocol — the central design question

1. Where do adapters live?
    - (a) Foundational-ten adapters live in the bootstrap package (inline adapter bundle).
    - (b) Phase 4+ components ship adapters in their own packages (e.g. `onboarding/src/bootstrap_adapter.py`).
    - Is this the right split? Should foundational adapters also live in their own packages for uniformity? (recommendation: no — the ten are sealed and can't grow adapter files without amendment; the bootstrap package owns their adapters.)
2. How does the framework discover contributions from Phase 4+ packages?
    - (a) **Python packaging entry-points** — `pyproject.toml` declares `[project.entry-points."pos.bootstrap"]` entries; framework uses `importlib.metadata.entry_points` (stdlib, Max-first-safe).
    - (b) **YAML manifest in the workspace** — `~/.pos/bootstrap.yaml` lists contributions as `package.module:contribute_fn` paths; framework imports each.
    - (c) **Both** — entry-points for packaged components; YAML manifest for workspace-local adapters (e.g. persona seeders that are workspace content, not a package).
    - recommendation: (c) both. Entry-points for package-level discovery, YAML for workspace-local additions.
3. What is the adapter interface? Candidates:
    - A function `contribute(host: BootstrapHost) -> None` that calls `host.register_ipc(...)`, `host.register_subscription(...)`, `host.after("component-name")`, etc.
    - A class `Contribution` with typed metadata fields (`name`, `after`, `before`, `phase`) and a `run(host)` method.
    - A declarative dict/TOML with known keys (`name`, `ordering`, `module`, `callable`).
    - recommendation: class-based with typed Pydantic metadata — readable, testable, structurally-enforceable.

### 2. Ordering engine

4. How are ordering constraints declared on contributions?
    - (a) Imperative (`host.after("cost-governance")` inside `contribute()`) — simple but hard to inspect before execution.
    - (b) Declarative metadata on the contribution class/object (`name="onboarding"`, `after=("primary-persona",)`, `before=("self-correction",)`) — readable, introspectable, testable.
    - recommendation: (b).
5. What does the ordering engine do? Topological sort with tie-breaking rules (stable alphabetical by `name` when ordering is ambiguous). Cycle detection fails boot with a named-cycle diagnostic.
6. What are the "phases" or scopes of ordering? Candidate: three phases — `before_orchestrator_start`, `wrap_activate_scope`, `after_orchestrator_ready`. Each contribution declares its phase. Within a phase, ordering constraints resolve the order; between phases, the framework executes phase-by-phase. Alternative: single flat ordering space. recommendation: phases — makes the three-wrap-chain natural to declare and makes session-start-time work distinct from boot-time work.
7. What ordering rules does the framework *enforce* vs *trust declarations*? E.g. cost-governance MUST be innermost — should the framework hardcode that, or trust cost's declaration `after=("reversibility",)`? (recommendation: trust declarations; let cost's adapter declare its own ordering. The framework only enforces cycle-absence.)

### 3. The `BootstrapHost` interface

8. What does the host expose to contributions? Candidates:
    - `host.server: IPCServer` — raw IPC server (contribution calls `register_X_ipc` on it).
    - `host.orchestrator: Orchestrator` — constructed orchestrator (for `subscribe_all`, `register_scope_callback`).
    - `host.config: dict[str, Any]` — merged workspace config loaded from `~/.pos/bootstrap.yaml`.
    - `host.register_session_start(callable)` — session-start phase registration.
    - `host.after(name: str) -> None` / `host.declare_ordering(...)` — imperative fallback if needed.
9. Does the host own the construction of shared dependencies (SQLite stores, OTel tracer provider, pyee emitters) or do contributions construct their own? recommendation: host owns the shared *singletons* (IPCServer, Orchestrator, TracerProvider, shared pyee channels); contributions construct their own *component-local* stores (each component's own SQLite lives where the component puts it; bootstrap doesn't manage their schemas).
10. How is the host itself constructed, configured, and wired? Presumably by the framework's `main()`. Does `main()` take a config path parameter, read `~/.pos/bootstrap.yaml`, instantiate the host, run the ordering engine, invoke contributions in order, then start the orchestrator's event loop?

### 4. The foundational-ten adapter bundle

11. What does each of the ten adapters look like? Sketch:
    ```python
    # bootstrap/src/adapters/safety_layer.py
    from pydantic_bootstrap_contract import Contribution

    from safety_layer.ipc_wiring import register_safety_ipc

    class SafetyAdapter(Contribution):
        name = "safety"
        phase = "wrap_activate_scope"
        after = ("reversibility",)      # safety wraps around reversibility

        def run(self, host):
            register_safety_ipc(host.server, host.safety_config)
    ```
    Verify each of the ten has a clean "one function invoked by the adapter" entry point; if any don't (graceful-degradation, objective-tracker, self-upgrade, primary-persona, observability-aggregator, memory-system), the adapter has slightly more code to drive their runtime construction. Research must enumerate the per-component contribution shape.

12. How much config does each adapter need? Config loading is part of the adapter's job (read the component's YAML config file from `~/.pos/<component>/`), or is it part of the framework (host reads a unified config and hands subsets to adapters)? recommendation: each adapter reads its own config file; the host provides the config-directory location as a host attribute. Keeps adapter scope small and avoids a cross-component config schema.

### 5. Composition with the existing `~/.pos/bootstrap.py` primitive

13. The orchestrator already ships `load_and_register(bootstrap_path, orchestrator)` reading `~/.pos/bootstrap.py`. Does the new bootstrap component:
    - (a) Replace that primitive (deprecate the orchestrator's loader, route everything through the new framework)?
    - (b) Compose with it (the new framework's `main()` invokes the orchestrator's loader as one of its contributions)?
    - (c) Leave it as a workspace-customisation escape hatch (workspace authors can still drop a `~/.pos/bootstrap.py` for one-off hooks alongside the contribution ecosystem)?
    - recommendation: (c). The existing primitive is a valid escape hatch for workspace-specific code that doesn't warrant a full contribution. Both mechanisms coexist; the framework calls `load_and_register` as a late-phase contribution.

### 6. Workspace-local contribution surface

14. Where does the workspace declare its contribution set? `~/.pos/bootstrap.yaml` with a shape like:
    ```yaml
    contributions:
      - pos.bootstrap.adapters.orchestrator      # entry-point or dotted path
      - pos.bootstrap.adapters.observability_aggregator
      - pos.bootstrap.adapters.primary_persona
      - pos.bootstrap.adapters.safety
      - pos.bootstrap.adapters.reversibility
      - pos.bootstrap.adapters.cost_governance
      - pos.bootstrap.adapters.self_correction
      - ~/.pos/adapters/my_workspace_personas.py:contribute
    ordering_overrides: {}
    config_dir: ~/.pos/
    ```
15. Does the framework merge entry-point-discovered contributions with manifest-declared ones, or is one authoritative? recommendation: manifest is authoritative for enablement (opt-in), but entry-points are discovered and must be explicitly listed to enable. No auto-enable by presence of an installed package — too surprising.

### 7. Error semantics

16. What happens if a contribution fails to load (import error, missing config file, adapter raises)? Fail-closed at boot with named contribution + diagnostic. The existing `orchestrator/bootstrap.py` is already fail-closed on missing/erroring loaders — inherit that posture.
17. What happens if ordering is unsatisfiable (cycle detected)? Fail-closed at boot with the cycle's edge set logged.
18. What happens if a contribution's config file is missing? Workspace-level decision: contribution-specific default-config fallback vs hard-fail. recommendation: each adapter declares its behaviour (hard-fail for security-critical components like safety; default-config for non-critical like observability retention tuning).

### 8. Testing discipline

19. Integration test matrix — at minimum:
    - All ten foundational adapters contribute; orchestrator starts; `activate_scope` with no special conditions succeeds; gate chain fires in correct order; self-correction's subscriptions fire on a synthetic failed scope; session-start callbacks fire.
    - Synthetic Phase 4 contribution (a mock "onboarding adapter") registers via manifest-declared entry-point; framework discovers and invokes it.
    - Ordering cycle detected and boot fails with named cycle.
    - Missing config file for safety → fail-closed with named diagnostic.
    - Workspace-authored `~/.pos/bootstrap.py` escape hatch runs at the correct late phase.
20. Contract tests for the extension protocol — a mock contribution adheres to the declared `Contribution` Pydantic shape; malformed contributions are refused at discovery time with a clear error.

### 9. Sidecar/wrap sanity (no new sealed-component amendment)

21. Does bootstrap require amendment to any of the ten sealed components? Proposed: **no.** Each existing `register_*_ipc` function is already plugin-compatible. Components lacking a neat registration function (graceful-degradation, objective-tracker, observability-aggregator, primary-persona, self-upgrade, memory-system) are wrapped by thin adapters in the bootstrap package — the adapter code is in *bootstrap*, not in the sealed component. Halt and signal if research finds any case where amendment is required.

22. Does bootstrap require amendment to the orchestrator's existing `bootstrap.py` loader? Proposed: **no** — compose, don't replace (per §5).

### 10. Seal-test pattern

23. Bootstrap's `test_no_sealed_amendments.py` follows the `SEAL_COMMIT` sidecar-file pattern from self-correction (cleaner than the inline-constant pattern cost/reversibility used). Baseline is `65acb97` (self-correction seal).

## Constraints the research must respect

- **Python-native.** Permitted runtime deps as per standard (stdlib, pydantic, pyee, opentelemetry, PyYAML, duckdb). Test-only: pytest, pytest-asyncio.
- **No amendments to sealed components.** Quintuple sidecar/wrap precedent holds.
- **Framework is the high-stakes surface.** Design budget skews toward extension-protocol correctness; adapter bundle for the foundational ten is mechanical once the framework is right.
- **Plugin-hostable from day one.** Future Phase 4+ components add to themselves, not to bootstrap.
- **Fail-closed on boot errors.** Missing/erroring contributions, unsatisfiable ordering, malformed config — all fail-closed with named diagnostics.
- **No monkeypatching.** The framework composes via explicit entry-points / manifest; no magic import-time side effects.
- **Compose with the existing `~/.pos/bootstrap.py` primitive**, don't replace.
- **Max-first.** No LLM inference inside the framework.
- **A1 correction held.** OTel via aggregator's tracer.
- **Seal-test pattern mandatory** — `SEAL_COMMIT` sidecar-file convention from self-correction.
- **Zero carryover from current pOS.**
- **Halt-on-deviation.**

## Deliverable — what the research document must contain

A markdown document at `components/workspace-bootstrap/research.md` with:

1. **Survey of existing patterns** — Python packaging entry-points (pytest, click plugins, Django apps), pluggy (pytest's plugin framework), Zope's component architecture, Java ServiceLoader, npm's module-level hooks. Each for extension-protocol ideas.
2. **Recommended design shape** — for each of the nine question groups, options considered, recommended option, rationale. **The extension protocol recommendation is the document's central claim.**
3. **Clause-by-clause spec coverage** — each acceptance criterion mapped to a design piece.
4. **Extension protocol specification** — Pydantic `Contribution` model, discovery mechanism (entry-points + manifest hybrid), adapter interface, full end-to-end example of a Phase 4 component registering without touching bootstrap.
5. **Ordering engine specification** — declaration format, topological sort with tie-breaking, cycle detection, phase model.
6. **Foundational-ten adapter bundle inventory** — one adapter sketch per component with config file path, ordering declaration, and the function-call it drives. Enumerate the ten and flag any whose registration shape is non-trivial.
7. **`BootstrapHost` interface specification** — the attributes and methods contributions consume; ownership of shared singletons.
8. **Composition with existing `~/.pos/bootstrap.py` primitive** — explicit late-phase contribution that invokes the orchestrator's existing loader.
9. **Error-semantics specification** — fail-closed paths + diagnostics for each error class.
10. **Dependency map** — consumed by: all Phase 4+ components. Depends on: ten sealed components + orchestrator's existing `bootstrap.py` loader.
11. **Complexity estimate** — AI-time calibrated against prior framework-style components (self-upgrade ~25 min, which was similar in shape — framework + plugin surface + clause enforcement). Self-correction ~16 min (pure consumer, no framework). Bootstrap sits between these: framework component, ten adapters, extension surface to design carefully. Anchor **30–45 AI-min wall-clock; red-line 55**. Framework + protocol + ten adapters + integration test suite.
12. **Prototyping priorities** — questions only a prototype can answer (e.g. whether ordering-engine phases + imperative overrides compose cleanly; whether entry-point discovery produces surprises under workspace-installed-but-not-declared packages).

## Execution note

On owner's approval, the plan is passed to a general-purpose Agent. Halt-on-deviation applies. The extension-protocol design is the highest-stakes output — if the researcher produces a protocol that doesn't admit Phase 4+ extensions without bootstrap amendment, halt and re-research rather than accept a weak protocol.

---

## Awaiting owner's approval

- Approve as written → the primary persona dispatches the research agent.
- Approve with changes → the primary persona incorporates and resubmits.
- Reject → the primary persona reworks.
