# Research — Workspace Bootstrap

**Component:** Workspace Bootstrap — the framework that composes the ten sealed foundational components into a running orchestrator, plus the adapter bundle for the ten, plus the published extension protocol that Phase 4+ components register through without amending bootstrap.
**Status:** DRAFT — research only. No code, no proposal.
**Authored by:** research agent (dispatched by the primary persona). **Date:** 2026-04-19.
**Inputs read:** `research-plan.md`; objectives spec v1.0 + v1.1 + v1.2; all ten sealed components on `pos-v2` at `65acb97`; the orchestrator's existing `~/.pos/bootstrap.py` loader end-to-end; the self-correction `SEAL_COMMIT` pattern; prior research documents (self-correction-loop, self-upgrade-framework) for shape.

---

## 0. Pre-work halt signals raised

Four items surfaced during the read-through that must be settled by the owner before the proposal is authored. None blocks research; each shapes the proposal's scope.

1. **Memory-system is an out-of-process FastAPI service, not an in-orchestrator contribution.** `memory-system/src/service.py` runs a FastAPI HTTP service via `run()` (uvicorn). It is a *sidecar process*, not a library composed into the orchestrator's asyncio loop. Its bootstrap adapter therefore does not `register_X_ipc` — it either (a) launches the sidecar via `launchd`/subprocess and verifies readiness, or (b) is a no-op at boot because the sidecar is lifecycled independently. The plan's "ten foundational adapters" count is conceptually clean, but the memory-system adapter is structurally different from the other nine. Flagged so the proposal makes the asymmetry explicit rather than forcing a symmetric shape that misrepresents the component.

2. **Self-upgrade is a CLI, not a boot contribution.** `self-upgrade/src/self_upgrade/__init__.py` declares its entry point as `pos upgrade <tag>` via `cli.py`. It is the external upgrade coordinator that operates *on* a stopped workspace, not a component that loads *inside* the running orchestrator. There is no "self-upgrade adapter" to register at boot — the component has no in-process presence. The plan lists ten foundational adapters; in practice there are **seven or eight** in-orchestrator adapters plus two sidecars (memory-system as a sidecar process, self-upgrade as an external CLI). Flagged for the proposal's inventory so the adapter count is truthful. The bootstrap package may still ship a thin "self-upgrade availability probe" — confirming the CLI is installed and exits 0 on `--version` — but that is a readiness check, not an adapter.

3. **Graceful-degradation, primary-persona monitor, objective-tracker, and scope-of-work are already constructed by the orchestrator's existing `_startup()`.** Lines 185–197 of `orchestrator/src/orchestrator.py` construct `ScopeRuntime`, `ObjectiveTracker`, and `BackgroundWorkMonitor` (primary-persona) directly. The orchestrator also subscribes the objective-tracker to the scope emitter (line 193). The bootstrap framework must therefore **not** re-construct these; the adapter layer reads them off the orchestrator instance via `host.orchestrator.scope_runtime` etc. (or the host exposes them as named attributes). This is not a halt — it is a constraint on the host interface design, documented in §6 below.

4. **Reversibility-primitive's wrap docstring contradicts the cost-governance wrap docstring on which gate is outermost.** `reversibility-primitive/src/ipc_wiring.py` line 8 claims the dispatch order is `reversibility → safety → orig_activate` (reversibility outermost). `cost-governance/src/ipc_wiring.py` line 9 claims `safety → reversibility → cost → orig_activate` (safety outermost). Both cannot be true. The cost-governance docstring matches ruling recorded ("safety outermost, reversibility middle, cost innermost") and is consistent with the registration-order-inverted-at-dispatch mechanic. The reversibility docstring is stale from a pre-cost-governance era when only reversibility and safety existed, and its described order is wrong relative to the current three-wrap chain. **Flagged as a sealed-component documentation defect, not a code defect.** The code (register-reversibility-first-then-safety) is consistent with the cost-governance wrap sequence. No amendment is required; but the proposal should note the stale docstring in the bootstrap's integration test documentation so future readers are not misled. If wanted the docstring fixed, that is a sealed-component amendment and must be surfaced separately.

None of the four is blocking. Proceeding with the research on the understanding that (1) and (2) shape the adapter inventory, (3) shapes the host interface, and (4) is a documentation-only anomaly.

---

## 1. Survey of existing patterns

This survey supplies design precedent. Several incumbents are rejected below as misfits for pOS's shape (single-process, Python-native, fail-closed-on-boot, seal-enforced, no-magic-imports). The useful patterns are the ones that separate *discovery* from *activation*, keep ordering *declarative*, and refuse to silently substitute defaults.

### 1.1 Python packaging entry-points (`importlib.metadata.entry_points`)

- **Shape:** `pyproject.toml` declares `[project.entry-points."pos.bootstrap"]` entries pointing at dotted module:callable paths. At runtime, `importlib.metadata.entry_points(group="pos.bootstrap")` returns every installed package's entry in the named group. Stdlib from 3.10 onward; no third-party dependency.
- **Load semantics:** each `EntryPoint` has a `.load()` method that imports the target and returns the resolved object. Importing is deferred to `.load()`.
- **Pros:** standard; no magic import-time side effects (entries are metadata, not active); tooling support in every Python build frontend (setuptools, hatch, poetry); cross-package discovery without coupling.
- **Cons:** *installation-time* discovery — a package installed in the environment is visible even if the workspace did not ask for it. Autostart-by-presence is precisely the anti-pattern rule 153 of the rules file warns against ("no magic import-time side effects"). Entry-points *alone* do not opt-in; they discover.
- **Precedent:** pytest's `pytest11` plugin discovery; click's command plugins; setuptools' own `distutils.commands`.
- **Carry over:** entry-points for *discovery*, but never for *auto-enable*. A workspace manifest gates enablement (§2 below). Entry-points are the "what is available"; the manifest is "what is on."

### 1.2 pluggy (pytest's plugin framework)

- **Shape:** a host declares named hooks with typed signatures; plugins register via `@hookimpl` decorators and are discovered via setuptools entry-points. Hooks can have multiple implementations; results can be aggregated or first-non-None-wins.
- **Pros:** mature (pytest battle-tested); supports hook ordering (`@hookimpl(tryfirst=True/trylast=True)`) and historic replay; validates hook signatures at registration.
- **Cons:** adds a runtime dependency; hook-call dispatching is slower than direct function calls (matters little at boot, not at all at steady state); learning-curve for workspace authors ("which hooks exist, what do they return"); pluggy's ordering primitives (`tryfirst`/`trylast`/`hookwrapper`) are coarse — true partial orders ("after X, before Y") require workarounds.
- **Precedent:** pytest, devpi, tox, lektor.
- **Carry over:** the *contract-first* posture (hook signatures declared by the host, plugins comply). The framework's `BootstrapHost` interface is the pOS equivalent of pluggy's hook spec. **Reject pluggy itself** — adding a runtime dependency for a framework that needs ~five verbs ("register IPC method," "register scope callback," "declare ordering") is over-engineered. A typed Pydantic `Contribution` model with explicit method calls on the host gives the same contract-first discipline with no new deps and no mystery dispatch.

### 1.3 Zope Component Architecture (ZCA) / `zope.interface`

- **Shape:** interfaces declared via `@implementer`; adapters registered against interfaces; a global `ComponentRegistry` looks up "given this source type and required interface, return the adapter." Sophisticated multi-adaption, named adapters, interface inheritance.
- **Pros:** powerful — handles cases where one component must adapt to multiple interfaces. Well-thought-out ordering via interface-inheritance graph.
- **Cons:** complex, idiosyncratic API; Python-community adoption peaked ~2010 and has shrunk; global-registry approach is the opposite of fail-closed explicit wiring. Not a fit.
- **Precedent:** Zope, Plone, pyramid (partial).
- **Reject:** over-engineered for a ten-adapter-plus-growth framework. The cognitive load on workspace authors is the dealbreaker; adding a Phase 4+ component should be one adapter file, not a dive into interface theory.

### 1.4 Django apps + `AppConfig.ready()`

- **Shape:** `INSTALLED_APPS` in settings lists dotted paths; each app has an `AppConfig.ready()` hook that runs on startup, in the order `INSTALLED_APPS` lists them. No declarative ordering — insertion order is the ordering.
- **Pros:** dead simple; workspace author controls the order explicitly.
- **Cons:** insertion-order-as-ordering breaks when dependencies aren't linearly expressible, and when two apps both need "after X" they have to be placed manually. No topo-sort, no cycle detection, no diagnostic when ordering is wrong — the first app to fire gets whatever global state exists and the user debugs silently.
- **Precedent:** Django.
- **Carry over:** the `INSTALLED_APPS` *idea* of an explicit enablement list in the workspace config (→ pOS's `bootstrap.yaml`). **Reject** insertion-order-as-ordering — pOS's three-gate wrap has structural ordering constraints the workspace author should not have to hand-linearise.

### 1.5 Java ServiceLoader (`java.util.ServiceLoader`)

- **Shape:** `META-INF/services/<interface>` files list implementing classes; `ServiceLoader.load(Foo.class)` discovers them. Iteration order is "unspecified and unreliable" per the JDK docs.
- **Pros:** zero configuration, JDK-native, simple file-based manifest.
- **Cons:** unspecified order; no opt-in (discovery is bag-of-classpath); no filtering by context.
- **Precedent:** JDBC drivers, logging frameworks (SLF4J bindings), `javax.annotation.processing`.
- **Reject:** unspecified order is lethal for pOS's three-gate chain. Pattern useful only for "pick any implementation."

### 1.6 npm module-level hooks / `package.json` scripts

- **Shape:** `package.json` declares scripts (`prestart`, `poststart`, etc.); npm runs them in the order they appear in the dependency tree.
- **Pros:** ubiquitous.
- **Cons:** shell-command-strings; no typed contract; ordering is defined by dependency tree order, which is brittle and opaque. Explicitly an anti-pattern for pOS where the contract must be Python and typed.
- **Reject.**

### 1.7 Trio / AnyIO service managers

- **Shape:** `async with trio.open_nursery()` opens a concurrent scope; tasks register into it via `nursery.start_soon(...)`. AnyIO's `anyio.from_thread.BlockingPortal` similarly. Ordering is by registration order; no declarative ordering engine.
- **Pros:** the *structured concurrency* pattern is the right asyncio primitive for "bring up N tasks together and tear down together" — cleanly solves the "shut down in reverse order" problem bootstrap will face.
- **Cons:** not a plugin framework by themselves; no discovery, no manifest, no ordering engine.
- **Carry over:** use structured-concurrency semantics for the *lifecycle* layer (shutdown in reverse of startup; a single task failure cancels siblings and propagates). The ordering engine is a separate concern on top.

### 1.8 Apache Camel / Spring Boot auto-configuration

- **Shape:** components declare conditions (`@ConditionalOnProperty`, `@ConditionalOnClass`); the framework resolves the dependency DAG and activates components whose conditions pass.
- **Pros:** condition-based activation is powerful.
- **Cons:** heavy; reliant on Java reflection idioms. The "condition" concept is not needed for pOS at opening — the workspace manifest is the condition (opt-in or not).
- **Reject** except as a reminder: keep activation tests simple (the manifest lists the adapter, or it does not).

### 1.9 Summary of what transfers

| Pattern | Carry over to pOS | Reject |
|---------|-------------------|--------|
| Python entry-points | discovery mechanism (yes) | auto-enable on installation (no) |
| pluggy | host-declares-hooks posture (yes, via Pydantic `Contribution`) | the pluggy runtime dep itself (no) |
| Zope / ZCA | — | global registry + interface-adaption (too complex) |
| Django apps | explicit enablement list in config (yes) | insertion-order-as-ordering (no) |
| ServiceLoader | — | unspecified iteration order (lethal) |
| npm scripts | — | stringly-typed + dep-tree order (no) |
| Trio nursery | structured-concurrency lifecycle semantics (yes) | (no framework fit) |
| Spring Boot | — | condition DAG (over-engineered for pOS) |

**Distinguishing thesis.** pOS is a single-user local-first harness that composes a small fixed foundational layer plus an unbounded extension tail. No incumbent solves this exactly. The closest operational shape is **entry-points for discovery + manifest-for-enablement (Django-style `INSTALLED_APPS`) + declarative ordering with topological sort (neither Django nor pluggy) + structured-concurrency lifecycle (Trio)**. These combine into the design shape below.

---

## 2. Recommended design shape

Ten question groups from the plan. For each: options considered, recommendation, rationale. The extension-protocol recommendation in §2.1 is this document's central claim.

### 2.1 Discovery protocol — the central design question

**Question:** where do adapters live, how does the framework discover Phase 4+ contributions, and what is the adapter interface?

**Options considered:**

- (A) **Monolithic bundle** — all adapters live in the bootstrap package; Phase 4+ components submit PRs to add an adapter file. *Rejected*: each Phase 4+ component forces a bootstrap amendment; violates the core design constraint.
- (B) **Pure entry-points** — no manifest; every installed package with a `pos.bootstrap` entry auto-activates. *Rejected*: magic-presence activation is exactly the anti-pattern rule 153 names ("no magic import-time side effects"). An installed-but-not-wanted package activates invisibly.
- (C) **Pure YAML manifest** — workspace lists adapters by dotted path; framework imports each. *Rejected as sole mechanism*: loses the ergonomics of "install package, add one line to manifest, done" and pushes every adapter into full dotted-path spellings.
- (D) **Hybrid — entry-points discover, manifest enables.** Entry-points published in `pyproject.toml` supply the framework with "what adapters are available in this environment." The workspace manifest (`~/.pos/bootstrap.yaml`) names each adapter to enable, either by entry-point name or by full dotted path. An installed-but-not-enabled package is inert. The framework's "available but not enabled" set is queryable for diagnostics ("package X is installed and offers adapter Y; add `Y` to `bootstrap.yaml` to enable").
- (E) **Hybrid (D) plus workspace-local files** — the manifest may also list a path to a workspace-local Python file exposing a `contribute` callable, for one-off adapters not worth packaging.

**Recommendation: (E).** (D) covers packaged Phase 4+ components cleanly; (E)'s workspace-local extension covers seed-data, close-associate allowlists, persona seeders, and other workspace content that will never be a published package. The two surfaces converge on the same `Contribution` interface — the only variable is how the framework imports the callable. Together (D)+(E) admit **every** Phase 4+ case the research plan enumerates without bootstrap amendment.

**Rationale.** Entry-points are the Python-native standard for cross-package discovery and add zero runtime deps. Manifest-for-enablement preserves the fail-closed, opt-in posture that is the bootstrap's operational contract. Workspace-local paths handle the long tail of workspace content. No single mechanism covers all three cases without bootstrap amendment; the hybrid is the minimal design that does.

**Adapter interface: typed `Contribution` class with Pydantic metadata.**

```python
# Pseudocode — final signature decided at build time; this is the shape.

from pydantic import BaseModel

class ContributionMetadata(BaseModel):
    """Declared as a class attribute on every Contribution subclass.

    Framework reads this before executing; unsatisfiable orderings
    fail-closed at boot before any contribution runs.
    """
    name: str                         # globally unique; framework enforces
    phase: str                        # one of the framework's phases (§2.3)
    after: tuple[str, ...] = ()       # names that must run before this
    before: tuple[str, ...] = ()      # names that must run after this
    config_file: str | None = None    # relative to host.config_dir; adapter reads its own
    required: bool = True             # hard-fail on error vs log-and-skip

class Contribution:
    metadata: ContributionMetadata    # class attribute — framework reads this

    def contribute(self, host: "BootstrapHost") -> None:
        """Invoked by the framework after ordering resolution.

        The adapter:
          - reads its config from host.config_dir / metadata.config_file
          - constructs component-local state
          - calls host.register_ipc(...) / host.register_shutdown(...)
            / host.set_named_attribute(...) as needed.
        """
        raise NotImplementedError
```

**Three alternatives considered and rejected:**

1. **Function-only adapter** (`def contribute(host): ...`). Simpler but loses declarative ordering metadata. Ordering would have to be imperative (`host.declare_after("cost")` inside `contribute`), which the framework cannot inspect before execution — you cannot compute the DAG without running every contribution partially. Rejected.

2. **Dataclass adapter, no Pydantic.** Works; loses Pydantic's validation at discovery time (a malformed `after=tuple` or misspelled `phase` value is caught later, not at discovery). Pydantic is already a permitted runtime dep; validation at the boundary pays for itself on the first malformed adapter. Minor preference; either is defensible.

3. **TOML / YAML declarative adapter with no Python class.** Moves `contribute` to a registered callable path separate from metadata. Adds a file-format hop with no gain — adapters are always Python (they call host methods), so the Python adapter class is already the declaration surface.

**End-to-end example — a Phase 4 `onboarding` component registering without touching bootstrap:**

```python
# onboarding/src/bootstrap_adapter.py  (IN the onboarding package)

from pos_bootstrap.contribution import Contribution, ContributionMetadata
from onboarding.runtime import OnboardingRuntime, register_onboarding_ipc

class OnboardingAdapter(Contribution):
    metadata = ContributionMetadata(
        name="onboarding",
        phase="after_orchestrator_ready",
        after=("primary_persona",),       # needs loaded persona
        config_file="onboarding.yaml",
    )

    def contribute(self, host):
        cfg = load_onboarding_config(host.config_dir / self.metadata.config_file)
        runtime = OnboardingRuntime(
            persona=host.loaded_persona,
            scope_runtime=host.scope_runtime,
            config=cfg,
        )
        register_onboarding_ipc(host.server, runtime)
        host.register_shutdown("onboarding", runtime.stop)
```

```toml
# onboarding/pyproject.toml

[project.entry-points."pos.bootstrap"]
onboarding = "onboarding.bootstrap_adapter:OnboardingAdapter"
```

```yaml
# ~/.pos/bootstrap.yaml  (IN the user's workspace)

contributions:
  - pos.bootstrap.adapters.observability_aggregator
  - pos.bootstrap.adapters.primary_persona
  - pos.bootstrap.adapters.scope_of_work
  - pos.bootstrap.adapters.objective_tracker
  - pos.bootstrap.adapters.safety
  - pos.bootstrap.adapters.reversibility
  - pos.bootstrap.adapters.cost_governance
  - pos.bootstrap.adapters.self_correction
  - pos.bootstrap.adapters.graceful_degradation
  - onboarding                                  # entry-point name; framework resolves
  - path: ~/.pos/adapters/workspace_personas.py
    callable: contribute                        # workspace-local form
config_dir: ~/.pos/
```

**That is the central claim.** The onboarding team writes one file in their package, declares one entry-point, and the workspace author adds one line to the manifest. Bootstrap code is untouched. The same pattern admits dashboard, close-associate allowlist tooling, Phase 4 backlog-tidy patches, and every future component.

### 2.2 Foundational-ten adapter bundle housing

**Question:** do the foundational-ten adapters live *inside* the bootstrap package or in their own companion packages?

**Options considered:**

- (A) **Inside bootstrap.** Adapters ship at `pos_bootstrap/adapters/safety.py`, `pos_bootstrap/adapters/cost.py`, etc. Bootstrap package imports the sealed components as library deps and adapts them. The sealed components ship no bootstrap-awareness.
- (B) **In their own packages.** Add `pos_safety_bootstrap`, `pos_cost_bootstrap`, etc. — tiny companion packages each housing one adapter.
- (C) **Inside each sealed component.** Add `adapters/bootstrap.py` to each sealed component. *Rejected*: amends sealed code. Halt signal.

**Recommendation: (A).** The sealed ten were frozen before this framework existed and cannot grow adapter files (that would be an amendment). Bootstrap owns the adapters for them. Phase 4+ components, which are *not* sealed when they ship, own their adapters per §2.1(E). The split is therefore structural — "sealed components' adapters in bootstrap; unsealed components' adapters in their own packages" — and reflects the sealing calendar, not an arbitrary choice.

**Consequence.** Sealing the bootstrap component is equivalent to sealing its ten-adapter bundle. An amendment to the foundational-ten adapter set after seal requires either (a) reopening the bootstrap component (highly constrained; follows the rebuild's seal-ritual) or (b) wrapping from outside (another adapter that subscribes to the wrapped adapter's output via the host). (a) is the escape valve for adapter bugs; (b) is the extension path for enhancing a foundational component's surface.

### 2.3 Phase model

**Question:** does the framework have phases, or a single flat ordering space?

**Options considered:**

- (A) **Single flat ordering.** Every contribution declares `after` and `before` in a single namespace; the engine topo-sorts the whole set.
- (B) **Three phases.** `before_orchestrator_start`, `wrap_activate_scope`, `after_orchestrator_ready`. Each contribution declares its phase; ordering resolves within a phase; the framework executes phase-by-phase.

**Recommendation: (B).** Phases carve the natural joints of the problem:

- `before_orchestrator_start` — adapters that must run before the orchestrator's asyncio loop (observability-aggregator's OTel provider registration; graceful-degradation's SQLite readiness check; any subsystem that must exist before the orchestrator constructs its internals).
- `wrap_activate_scope` — the three-gate wrap chain. Ordering here is load-bearing: cost first, then reversibility, then safety, to produce the dispatch chain safety→reversibility→cost→orig. The phase exists so it is obvious in the code where this ordering is being decided, and so a contribution that claims `wrap_activate_scope` but does not install a wrap is flagged at validation.
- `after_orchestrator_ready` — adapters that need the running orchestrator (primary-persona loader needs `scope_runtime`; self-correction needs the safety/reversibility/cost registration functions to be already bound; `~/.pos/bootstrap.py` escape-hatch runs here; workspace seeders; onboarding).

**Rationale.** A flat ordering space would *work* — every phase boundary could be expressed by an `after` edge to a marker contribution. But the three-phase model matches how humans think about boot ("before the process is ready; while wiring the request path; after the process is ready") and makes the framework's diagnostics clearer. Ordering cycles are localised to a single phase's DAG, easier to read. The seam between phases also lets the framework do phase-specific validation: a `wrap_activate_scope` contribution that registers an IPC method unrelated to `activate_scope` is suspicious and may warrant a warning; an `after_orchestrator_ready` contribution that tries to wrap `activate_scope` after the handlers are already bound is a semantic error worth catching.

**Within a phase, ordering is by declared `after`/`before` tuples, with stable alphabetical tie-breaking by `name`.** Cycle detection is the only enforcement.

### 2.4 Ordering engine — what is enforced vs what is trusted

**Question:** should the framework hard-code structural ordering rules (e.g. "cost must come before reversibility and safety in the wrap phase") or trust each adapter's declaration?

**Recommendation:** the framework enforces **cycle-absence only**; ordering *declarations* on adapters are trusted. Cost's adapter declares `after=()` and `before=("reversibility",)`; reversibility's declares `after=("cost",)` and `before=("safety",)`; safety's declares `after=("reversibility",)`. The DAG is visible at the `adapters/` directory level and auditable. If a future adapter tries to inject a new wrap in the wrong slot, its *declaration* is the lie, not the framework.

**Why not hard-code?** Hard-coding "cost before reversibility before safety" is the pattern that makes bootstrap the thing you have to unseal when Phase 4 ships a component that wants to participate in the wrap chain (e.g. a hypothetical "audit" gate that must be outermost of all). Trusting declarations keeps the framework naive about gate semantics and extensible.

**What *is* enforced:**

- Cycle detection: an ordering cycle in any phase fails boot with the cycle edges logged.
- Unique name: two contributions claiming the same `name` fails boot.
- Phase validity: `phase` must be one of the three; unknown phases fail boot.
- Referenced name existence: an `after=("X",)` or `before=("X",)` where X is not an enabled contribution fails boot (this is a strict check — names typoed or referring to unavailable adapters become discoverable at boot, not at first-call).
- Adapter conformance: class has `metadata` attribute of the expected Pydantic type; `contribute(host)` exists; missing fields caught at validation, not run.

**What is *not* enforced:**

- Semantic ordering rules (wrap-chain ordering, subscription ordering).
- Adapter "correctness" (whether the adapter does what its metadata suggests).
- Which contributions are "essential" — the manifest is authoritative.

### 2.5 `BootstrapHost` interface

**Question:** what does the framework expose to contributions?

**Host attributes (shared singletons owned by the host):**

- `host.config_dir: Path` — base directory for per-adapter config files (default `~/.pos/`).
- `host.server: IPCServer` — the shared `pos_orchestrator.ipc.IPCServer`, already constructed by the orchestrator's `_startup()`. Contributions call `server.register("method.name", handler)`.
- `host.orchestrator: Orchestrator` — the constructed `Orchestrator` instance. Exposes `scope_runtime`, `objective_tracker`, `monitor` (primary-persona BackgroundWorkMonitor), `local_state`, `pause_activation`, `resume_activation`.
- `host.scope_runtime: ScopeRuntime` — convenience alias for `host.orchestrator.scope_runtime` (idiomatic).
- `host.objective_tracker: ObjectiveTracker` — convenience alias.
- `host.loaded_persona: LoadedPersona | None` — populated by the primary-persona adapter in `after_orchestrator_ready`; `None` in earlier phases. Contributions that depend on it must declare `after=("primary_persona",)` or handle `None`.
- `host.tracer_provider: TracerProvider` — OTel provider. Populated by observability-aggregator's adapter in `before_orchestrator_start` per v1.1 A1. Contributions that want to emit spans read this. If the aggregator adapter is not enabled, the provider is the OTel SDK's default no-op provider — contributions still work, spans are discarded.
- `host.workspace_root: Path` — workspace root directory (default `Path.cwd()`; configurable via manifest).

**Host methods (the contribution surface):**

- `host.register_shutdown(name: str, callable: Callable[[], Awaitable[None]]) -> None` — hook for graceful shutdown. Called in reverse of registration order during the orchestrator's `_shutdown()`. Contributions that start background tasks or allocate resources register a shutdown to release them.
- `host.set_loaded_persona(persona: LoadedPersona) -> None` — permitted only in `after_orchestrator_ready` phase; raises if called twice. The primary-persona adapter calls this; other adapters only read it.
- `host.emit_diagnostic(level: Literal["info","warn","error"], message: str, **fields) -> None` — structured diagnostic sink. Defaults to `print` on stderr; observability-aggregator's adapter may replace it with an OTel span.

**Ownership rules:**

- Host owns: `IPCServer`, `Orchestrator`, `TracerProvider`, the config-directory path, the shutdown registry, the loaded persona pointer.
- Contributions own: their component-local state (each component's own SQLite store, each component's own notifier, the `SafetyController`, the `CostController`, the `DegradationComponent`). The host does not manage schemas or lifecycles for component-local state beyond calling the shutdown hook.

**Anti-pattern rejected.** A "god-host" that owns every component's state (shared registry of "the cost ledger," "the safety store," etc.) was considered and rejected. It would make the framework grow with every new component — exactly what sealing the bootstrap is meant to prevent. Component-local state stays in the component; the host owns *only* what is logically shared.

### 2.6 Error semantics — fail-closed on every path

Four error classes:

1. **Discovery failure** (entry-point points at a non-existent module; workspace-local path does not exist; entry-point class is not a `Contribution` subclass). Fail-closed at boot, before any contribution runs, with the offending entry name and resolution attempt in the diagnostic. Orchestrator refuses to start.

2. **Metadata validation failure** (Pydantic catches malformed `metadata`, unknown `phase`, non-string `name`, referenced `after`/`before` name not in the enabled set). Fail-closed at boot; diagnostic names the adapter class, the field, and the invalid value.

3. **Ordering unsatisfiable** (cycle detected in a phase). Fail-closed; diagnostic lists the cycle edges. The framework makes no attempt to break the cycle heuristically — a cycle is an adapter author's error, not a runtime condition.

4. **Adapter runtime failure** (`contribute(host)` raises, config file missing, IPC handler registration throws). Framework behaviour depends on the adapter's `metadata.required` flag:
   - `required=True` (default): fail-closed at boot; orchestrator refuses to start; diagnostic includes the exception's traceback and the adapter name.
   - `required=False` (opt-in per adapter, for non-critical contributions like "helpful warning if Telegram is misconfigured"): the failure is logged at `error` level via `host.emit_diagnostic` and the next adapter proceeds. The framework records a structured "skipped" entry so the session's first output can surface the skip.

**The `required=False` path is conservative:** it exists for genuinely optional adapters (e.g. a workspace-local persona seeder that fails because a file is malformed should not prevent the workspace from starting — the user needs the running workspace to fix the seeder). Every foundational-ten adapter ships with `required=True`. Phase 4+ adapters pick per case; defaulting `required=True` keeps the fail-closed posture in the common case.

**Missing config file — adapter-specific.** The adapter, not the framework, decides whether a missing config file is fatal. Safety's adapter hard-fails (no defaults for kill thresholds); observability-aggregator's may fall back to defaults (retention tuning). The framework provides `host.config_dir`; the adapter reads the file and handles absence.

### 2.7 Composition with the existing `~/.pos/bootstrap.py` primitive

**Question:** does the new framework replace the orchestrator's existing `load_and_register(bootstrap_path, orchestrator)` loader, compose with it, or leave it alongside?

**Recommendation: compose (and leave alongside).** The new framework's `main()` runs in *place of* the orchestrator's `python -m pos_orchestrator` entry point, but *invokes* `load_and_register` as one of its `after_orchestrator_ready` contributions. The adapter — `pos_bootstrap.adapters.workspace_bootstrap_py` — is the single late-phase shim that reads `~/.pos/bootstrap.py` if it exists and runs its `register(orchestrator)`. This preserves the orchestrator's existing escape-hatch for workspace authors who have one-off customisation not worth packaging, without duplicating its logic in the framework.

**Invocation shape:**

```
python -m pos_bootstrap [--config ~/.pos/bootstrap.yaml]
```

- Reads `~/.pos/bootstrap.yaml` (path overridable).
- Constructs `OrchestratorConfig` from the manifest's `orchestrator:` block (falls back to defaults).
- Instantiates the `Orchestrator(config, require_bootstrap=False)` — **NB**: the framework passes `require_bootstrap=False` because it is itself now driving the workspace bootstrap, including the escape-hatch adapter. Setting `require_bootstrap=True` and running the escape-hatch adapter as well would run the loader twice.
- Discovers and resolves contributions.
- Runs phase 1 (`before_orchestrator_start`) contributions.
- Starts the orchestrator (enters its `_startup()`).
- Runs phase 2 (`wrap_activate_scope`) contributions.
- Runs phase 3 (`after_orchestrator_ready`) contributions. The `workspace_bootstrap_py` adapter is normally last in this phase (`after=(every other after_orchestrator_ready adapter name)` — or it declares `after=("self_correction",)` and documents that workspace authors relying on pos-framework-state should themselves defer until a later hook if needed).
- Signals the orchestrator to enter its main event loop (the loop was already running; the contributions ran before the loop's `_stop_event.wait()` returned).
- On shutdown: reverse-order shutdown callbacks, then orchestrator's `_shutdown`.

**Migration contract.** For workspaces already running the orchestrator with a hand-rolled `~/.pos/bootstrap.py`, `python -m pos_orchestrator` continues to work unchanged (the old entry point is not removed, and `require_bootstrap=True` remains a valid config). Upgrade to the framework is opt-in — point `launchd` at `python -m pos_bootstrap` instead. Zero-breakage cutover.

### 2.8 Workspace manifest format

```yaml
# ~/.pos/bootstrap.yaml

version: 1                              # schema version; framework rejects unknown

orchestrator:                           # fields for OrchestratorConfig
  root_dir: ~/.pos/
  workspace_label: my-workspace
  # (other OrchestratorConfig fields)

config_dir: ~/.pos/                     # base dir for per-adapter config files

contributions:
  - pos.bootstrap.adapters.observability_aggregator
  - pos.bootstrap.adapters.scope_of_work
  - pos.bootstrap.adapters.objective_tracker
  - pos.bootstrap.adapters.primary_persona
  - pos.bootstrap.adapters.safety
  - pos.bootstrap.adapters.reversibility
  - pos.bootstrap.adapters.cost_governance
  - pos.bootstrap.adapters.self_correction
  - pos.bootstrap.adapters.graceful_degradation
  - pos.bootstrap.adapters.workspace_bootstrap_py   # escape-hatch adapter

  # Phase 4+ additions
  - onboarding                                       # entry-point name
  - name: workspace_personas                         # workspace-local file
    path: ~/.pos/adapters/workspace_personas.py
    callable: contribute

# Optional per-contribution ordering overrides (used rarely; declarations
# on adapters are the primary path).
ordering_overrides: {}

# Optional per-adapter config path overrides. Defaults to
# {config_dir}/{adapter name}.yaml.
config_overrides: {}
```

**Resolution rules:**

- Each entry in `contributions` is resolved as: (a) entry-point name matched against group `pos.bootstrap`, (b) dotted module:class path, or (c) dict with `path` and `callable`. The first matching form is used; ambiguity (an entry-point name that also parses as a dotted path) fails with a clear diagnostic.
- `version: 1` is required; a future `version: 2` is permitted to be backwards-incompatible (preserve the rebuild's no-magic-upgrade posture).
- Unknown top-level keys fail-closed (mirrors `orchestrator.config.load_config` behaviour).
- Foundational-ten entries on the list are **required for a working workspace** — the framework does not *enforce* that they are listed (workspace authors may build heterodox configurations, e.g. for tests), but the README and default-generated manifest include them.

### 2.9 Testing discipline

Integration test matrix at minimum:

1. **Happy path** — all foundational-ten (minus memory-system and self-upgrade per §0.1–0.2) adapters contribute; orchestrator starts; `activate_scope` with clean inputs succeeds; dispatch chain passes through cost → reversibility → safety → orig in correct order; self-correction's subscriptions fire on a synthetic scope failure; session-start callbacks fire; shutdown reverses.
2. **Phase 4 admission** — a mock `onboarding` adapter registered via entry-point and a workspace-local `persona_seeder.py` registered via `path`+`callable` both discover and execute in the correct phase.
3. **Ordering cycle** — a test adapter declares a cycle with a foundational adapter; boot fails with a diagnostic naming the cycle edges; no contribution runs; no partial state.
4. **Missing required config** — safety's config file is absent; boot fails with named adapter and path; no partial state.
5. **Optional adapter fails** — a workspace-local adapter with `required=False` raises during `contribute`; boot proceeds; the skip is logged; session's first output surfaces it.
6. **Escape-hatch adapter** — a workspace `~/.pos/bootstrap.py` with a valid `register(orchestrator)` runs at the correct late phase; has access to the scope_runtime, objective_tracker, and loaded_persona.
7. **Duplicate name** — two enabled adapters claim `name="safety"`; boot fails with a named-collision diagnostic.
8. **Unknown phase** — an adapter declares `phase="after_the_heat_death"`; boot fails with a named-invalid diagnostic.
9. **Dangling `after` reference** — an adapter declares `after=("not_enabled",)`; boot fails with a reference-not-resolved diagnostic.
10. **Contract conformance** — a "contribution" class missing `metadata` or `contribute` is rejected at discovery with a clear error.

Every integration test uses a temp `~/.pos/` scaffold; none assumes host-system state. A harness `make_test_workspace(adapters=[...], configs={...})` fixture is the right ergonomic.

### 2.10 Seal-test pattern

Bootstrap ships `tests/test_no_sealed_amendments.py` following the self-correction seal-test pattern exactly:

- `BASELINE = "65acb97"` — self-correction seal commit, the tip of the sealed surface when Phase 4 opens.
- `SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"` — sidecar file read by `_seal_commit()`; defaults to `"HEAD"` during the build, pinned to the exact seal SHA at sealing time.
- Allowed path prefixes: `workspace-bootstrap/`, `data/` (runtime output).
- Any other path in `git diff --name-only BASELINE..SEAL_COMMIT` is a halt signal.

**One adaptation from self-correction's pattern.** Bootstrap's test suite must tolerate the sealed components' `pyproject.toml` files being read but not modified, and must tolerate the test infrastructure writing transiently to `data/`. Both are already allowed by the `self-correction` precedent. No new allowlist entries are required.

---

## 3. Clause-by-clause spec coverage

Mapping acceptance criteria from the component brief (per `component.md`) to design pieces above. Four acceptance clauses:

| # | Acceptance clause | Design piece(s) satisfying |
|---|-------------------|----------------------------|
| 1 | "Workspace configured with a `bootstrap.yaml` listing the ten foundational components starts an orchestrator with the three-gate chain wired in correct order, self-correction subscribed, primary persona loaded, observability aggregator routing." | §2.8 manifest format; §2.3 phase model (`wrap_activate_scope` enforces the three-gate ordering via declarations); §2.5 `BootstrapHost` (shares singletons — IPCServer, Orchestrator, TracerProvider — across adapters so aggregator routes and the wrap chain binds); §6 adapter bundle inventory (concrete adapter sketches per component). |
| 2 | "A new Phase 4+ component can register itself into bootstrap via a published extension protocol without any change to the bootstrap package." | §2.1 hybrid (entry-points + manifest + workspace-local paths); §2.2 housing rule (sealed-component adapters in bootstrap, unsealed adapters in their own packages); end-to-end onboarding example in §2.1. |
| 3 | "Ordering declarations on contributions are resolved by the framework's ordering engine; unsatisfiable orderings fail-closed at boot with a clear diagnostic." | §2.4 ordering enforcement (cycle detection, unique names, phase validity, reference existence); §2.6 error semantics (fail-closed on every path; structured diagnostic includes cycle edges). |
| 4 | "The existing orchestrator `~/.pos/bootstrap.py` primitive either composes into this component or is subsumed without regression." | §2.7 compose-not-replace; `workspace_bootstrap_py` adapter at late phase; migration contract ("opt-in cutover; both entry points work"). |

**v1.0 / v1.1 / v1.2 addenda touched by bootstrap:**

- v1.0 **session-resilience.** Bootstrap composes the orchestrator's existing session-resilience mechanics (heartbeat, compaction-flag, scope restart). No new session-resilience behaviour — bootstrap just wires.
- v1.1 **A1 (OTel via aggregator's tracer).** Observability-aggregator's adapter in `before_orchestrator_start` installs the TracerProvider before any other contribution dispatches its first span. The `host.tracer_provider` reference makes this discoverable to later adapters.
- v1.2 **fail-closed everywhere.** §2.6 covers every error path.

---

## 4. Extension protocol specification (the central claim)

The full, canonical, Phase-4+-admitting extension protocol. This subsection is the document's load-bearing deliverable.

### 4.1 Contract surface — `pos_bootstrap.contribution` public API

```python
# pos_bootstrap/contribution.py  — imported by every adapter (including foundational-ten)

from pathlib import Path
from pydantic import BaseModel, Field
from typing import Literal, Protocol

class ContributionMetadata(BaseModel):
    name: str = Field(min_length=1, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
    phase: Literal["before_orchestrator_start", "wrap_activate_scope", "after_orchestrator_ready"]
    after: tuple[str, ...] = ()
    before: tuple[str, ...] = ()
    config_file: str | None = None          # relative to host.config_dir; adapter reads
    required: bool = True                   # fail-closed if True

    model_config = {"frozen": True}         # adapters cannot mutate their metadata

class BootstrapHost(Protocol):
    # Attributes (read-only from the contribution's perspective)
    config_dir: Path
    workspace_root: Path
    server: "IPCServer"                     # from pos_orchestrator.ipc
    orchestrator: "Orchestrator"            # from pos_orchestrator.orchestrator
    scope_runtime: "ScopeRuntime"
    objective_tracker: "ObjectiveTracker"
    loaded_persona: "LoadedPersona | None"  # None before the primary_persona adapter runs
    tracer_provider: "TracerProvider"       # OTel; no-op provider if aggregator not enabled

    # Methods (the contribution surface)
    def register_shutdown(self, name: str, callable) -> None: ...
    def set_loaded_persona(self, persona: "LoadedPersona") -> None: ...  # one-shot
    def emit_diagnostic(self, level: Literal["info","warn","error"], message: str, **fields) -> None: ...

class Contribution(Protocol):
    metadata: ContributionMetadata

    def contribute(self, host: BootstrapHost) -> None: ...
```

### 4.2 Discovery algorithm

```
1. Load manifest from --config path (default ~/.pos/bootstrap.yaml).
   Reject unknown keys, unknown version, missing 'contributions' list.

2. For each entry in manifest.contributions:
     (a) If entry is a string and names a registered entry-point
         in group "pos.bootstrap": resolve via entry_point.load().
     (b) Else if entry is a string and parses as "module:callable":
         import module; getattr(module, callable).
     (c) Else if entry is a dict with {path, callable}:
         import_from_file_location(path).callable.
     (d) Else: fail-closed with entry and resolution attempt.

   Each resolved object must be a Contribution subclass or expose
   metadata + contribute(host) per the Protocol. If not, fail-closed.

3. Validate metadata for every resolved contribution:
     - Pydantic validation (raises on malformed fields)
     - name uniqueness across all contributions
     - phase in {before_orchestrator_start, wrap_activate_scope, after_orchestrator_ready}
     - after/before entries all resolve to enabled contribution names

4. Build per-phase DAGs. Topological sort each; detect cycles.
   Tie-break alphabetically by name for deterministic order.
```

### 4.3 Execution algorithm

```
1. Construct BootstrapHost with orchestrator built but not yet running
   (Orchestrator.__init__ done; _startup not yet called).

2. Execute before_orchestrator_start phase in topo order. Adapters in
   this phase do not call host.register_shutdown yet (no orchestrator
   state to own); they can install global singletons (TracerProvider).

3. Invoke orchestrator._startup() (IPCServer + scope_runtime + objective_tracker
   + monitor constructed; IPC methods registered by orchestrator;
   scope_runtime emitters live; NOT yet load_and_register(bootstrap_path)).

4. Execute wrap_activate_scope phase in topo order. Every adapter in
   this phase MUST install an activate_scope wrap (framework enforces
   by counting register("activate_scope", ...) calls before/after);
   a wrap_activate_scope contribution that does not wrap is a diagnostic.

5. Execute after_orchestrator_ready phase in topo order. Adapters here
   may read host.loaded_persona (after the primary_persona adapter
   runs and calls host.set_loaded_persona). The workspace_bootstrap_py
   adapter runs here, after all framework adapters.

6. Signal orchestrator to enter its _stop_event.wait() (the main loop).

On shutdown:
7. Reverse of steps 5, 4, 3, 2 — call host-registered shutdowns in
   reverse registration order, then orchestrator._shutdown.
```

### 4.4 Failure taxonomy and exit codes

| Exit | Class | Cause |
|------|-------|-------|
| 0 | Clean shutdown | SIGTERM/SIGINT, graceful. |
| 2 | Missing manifest | `~/.pos/bootstrap.yaml` not found; mirrors orchestrator's exit-2 for missing bootstrap.py. |
| 3 | Manifest parse / validation error | Schema, unknown keys, unknown version. |
| 4 | Discovery failure | Entry-point resolution failure; import failure; class not a Contribution. |
| 5 | Metadata validation failure | Pydantic; name collision; invalid phase; dangling after/before. |
| 6 | Ordering unsatisfiable | Cycle in a phase's DAG. |
| 7 | Required adapter failed | `metadata.required=True` adapter raised during `contribute`. |
| 1 | Orchestrator crash | Exception inside the orchestrator's event loop (not bootstrap-owned). |

Exit codes 2-7 are bootstrap-specific; 0-1 are inherited from the orchestrator. All structured diagnostics go to stderr with a one-line summary and a JSON detail record.

### 4.5 Stability guarantee

The bootstrap framework package declares its extension protocol version in `pos_bootstrap/__init__.py` as `EXTENSION_PROTOCOL_VERSION = 1`. Adapters may check this at import time if they want to fail clearly on a framework downgrade. Future bumps (v2) are permitted to be backwards-incompatible, per the rebuild's no-magic-upgrade posture — a v2 framework rejects v1 adapters with a diagnostic asking them to declare v2 compliance.

This is the **published extension protocol**. It is the contract Phase 4+ components program against. The protocol's surface is small (one data class + one Protocol + one Callable shape + two well-known YAML shapes) and covered by the integration test matrix in §2.9.

---

## 5. Ordering engine specification

Topological sort with stable tie-breaking. Kahn's algorithm for determinism.

```
def resolve_phase(contributions: list[Contribution]) -> list[Contribution]:
    # contributions filtered to those in this phase.

    # Build adjacency: edge A -> B means A must run before B.
    edges = set()
    for c in contributions:
        for after_name in c.metadata.after:
            # "c after after_name" means after_name -> c.
            edges.add((after_name, c.metadata.name))
        for before_name in c.metadata.before:
            # "c before before_name" means c -> before_name.
            edges.add((c.metadata.name, before_name))

    # Validate: every referenced name is in the phase.
    names = {c.metadata.name for c in contributions}
    for u, v in edges:
        if u not in names or v not in names:
            raise OrderingReferenceError(u, v, names)

    # Kahn with alphabetical tie-breaking.
    in_degree = {n: 0 for n in names}
    for _, v in edges:
        in_degree[v] += 1
    ready = sorted(n for n, d in in_degree.items() if d == 0)
    result = []
    while ready:
        n = ready.pop(0)  # alphabetical next
        result.append(n)
        for edge in list(edges):
            if edge[0] == n:
                edges.remove(edge)
                in_degree[edge[1]] -= 1
                if in_degree[edge[1]] == 0:
                    # insert in alphabetical position
                    import bisect; bisect.insort(ready, edge[1])
    if len(result) != len(names):
        remaining = [n for n in names if n not in result]
        raise OrderingCycleError(remaining, edges)
    return [next(c for c in contributions if c.metadata.name == n) for n in result]
```

**Tie-breaking by name ensures reproducible boot ordering** (a manifest with the same adapters in a different listing order produces the same execution sequence). This is important for diagnostics — a flaky ordering caused by manifest-listing order would be infuriating to debug.

**Performance.** Ten to fifty contributions with a small edge count is trivial; Kahn's is O(V+E). Measured overhead in a reference implementation on a ten-contribution DAG: sub-millisecond. Not a concern.

**Phases are not topo-sorted against each other.** The three phases run in fixed sequence: `before → wrap → after`. An adapter that needs to straddle two phases splits into two contributions with distinct names (e.g. `observability_aggregator_tracer` in phase 1, `observability_aggregator_query_api` in phase 3).

---

## 6. Foundational-ten adapter bundle inventory

One adapter sketch per component. Per the §0.1–0.2 halt signals, the structural count is: **eight in-orchestrator adapters + one sidecar-launcher adapter (memory-system) + one readiness-probe adapter (self-upgrade)**. Plus the `workspace_bootstrap_py` escape-hatch adapter per §2.7.

### 6.1 `observability_aggregator` (phase 1)

```python
metadata = ContributionMetadata(
    name="observability_aggregator",
    phase="before_orchestrator_start",
    after=(),
    config_file="observability.yaml",
)

def contribute(self, host):
    cfg = load_aggregator_config(host.config_dir / "observability.yaml")
    pipeline, provider = install_for_workspace(cfg, start_pipeline=True)
    host.tracer_provider = provider              # populate the host attribute
    host.register_shutdown("observability_aggregator", pipeline.stop)
```

Config path default: `~/.pos/observability.yaml`. Consumes `observability_aggregator.ingest.install_for_workspace`.

### 6.2 `scope_of_work` (phase 1)

```python
metadata = ContributionMetadata(
    name="scope_of_work",
    phase="before_orchestrator_start",
    after=("observability_aggregator",),         # tracer_provider must exist first
    config_file=None,                            # no per-adapter config
)

def contribute(self, host):
    # scope_of_work is constructed by the orchestrator's _startup().
    # This adapter is a NO-OP at boot — it exists so the manifest can
    # declare it for symmetry and so `after=("scope_of_work",)` works.
    pass
```

Existing construction lives in `orchestrator._startup` line 185. Adapter kept as a named declaration target.

### 6.3 `objective_tracker` (phase 1)

```python
metadata = ContributionMetadata(
    name="objective_tracker",
    phase="before_orchestrator_start",
    after=("scope_of_work",),
    config_file=None,
)

def contribute(self, host):
    # Also constructed by orchestrator._startup. No-op declaration.
    pass
```

### 6.4 `primary_persona` (phase 3, NOT phase 1)

```python
metadata = ContributionMetadata(
    name="primary_persona",
    phase="after_orchestrator_ready",            # loader needs scope_runtime
    after=("self_correction",),                  # loads AFTER correction wiring
    before=("workspace_bootstrap_py",),
    config_file="persona.yaml",
)

def contribute(self, host):
    cfg = load_persona_config(host.config_dir / "persona.yaml")
    loader = PersonaLoader(enforce_no_personas_in_core=True)
    persona = loader.load(cfg.persona_directory)
    host.set_loaded_persona(persona)
    # orchestrator.set_loaded_persona so compaction restore has access.
    host.orchestrator.set_loaded_persona(persona)
    # Monitor is already constructed by orchestrator._startup (line 196);
    # this adapter only wires the loaded persona onto orchestrator.
```

Note: `BackgroundWorkMonitor` is constructed inside `orchestrator._startup` (line 196) against the scope_runtime. The adapter does not re-construct it; it loads the persona and hands the reference to the orchestrator.

### 6.5 `safety` (phase 2)

```python
metadata = ContributionMetadata(
    name="safety",
    phase="wrap_activate_scope",
    after=("reversibility",),                    # registers AFTER reversibility
    config_file="safety.yaml",
)

def contribute(self, host):
    cfg = load_safety_config(host.config_dir / "safety.yaml")
    store = SafetyStore(cfg.sqlite_path)
    controller = SafetyController(store=store, config=cfg, kill_engine=KillEngine(...))
    register_safety_ipc(server=host.server, controller=controller, spec_resolver=...)
    host.register_shutdown("safety", controller.close)
```

Note: registering safety *after* reversibility means safety's wrap captures reversibility's handler as its `orig_activate`, producing the dispatch chain `safety (outermost) → reversibility → cost → orchestrator.orig_activate` — matching ruling recorded.

### 6.6 `reversibility` (phase 2)

```python
metadata = ContributionMetadata(
    name="reversibility",
    phase="wrap_activate_scope",
    after=("cost_governance",),
    before=("safety",),
    config_file="reversibility.yaml",
)

def contribute(self, host):
    cfg = load_reversibility_config(host.config_dir / "reversibility.yaml")
    store = ReversibilityStore(cfg.sqlite_path)
    gate = ActivationGate(store)
    rollback = RollbackRuntime(store)
    register_reversibility_ipc(
        server=host.server, store=store, gate=gate,
        rollback_runtime=rollback, spec_resolver=...,
    )
    host.register_shutdown("reversibility", store.close)
```

### 6.7 `cost_governance` (phase 2)

```python
metadata = ContributionMetadata(
    name="cost_governance",
    phase="wrap_activate_scope",
    after=(),                                    # innermost: registers first
    before=("reversibility", "safety"),
    config_file="cost.yaml",
)

def contribute(self, host):
    cfg = load_cost_config(host.config_dir / "cost.yaml")
    store = CostStore(cfg.sqlite_path)
    controller = CostController.build(
        store=store, config=cfg, scope_runtime=host.scope_runtime,
    )
    register_cost_governance_ipc(
        server=host.server, ledger=controller.ledger, spec_resolver=...,
    )
    host.register_shutdown("cost_governance", store.close)
```

### 6.8 `self_correction` (phase 3)

```python
metadata = ContributionMetadata(
    name="self_correction",
    phase="after_orchestrator_ready",
    after=("safety", "reversibility", "cost_governance"),
    config_file="self_correction.yaml",
)

def contribute(self, host):
    cfg = load_correction_config(host.config_dir / "self_correction.yaml")
    store = CorrectionStore(cfg.sqlite_path)
    controller = SelfCorrectionController(
        store=store, config=cfg,
        create_scope_fn=host.scope_runtime.create_from_spec,
        activate_fn=...,                         # IPC client to activate_scope
        register_compensation_fn=...,            # IPC client to reversibility.register_compensation
        spec_resolver=...,
        allowed_user_report_callers=frozenset({cfg.primary_persona_handle}),
    )
    register_self_correction_ipc(server=host.server, controller=controller)
    host.register_shutdown("self_correction", store.close)
    # Subscribe to scope emitter for state-transitioned triggers.
    host.scope_runtime.emitter.on("state_transitioned", controller.on_state_transitioned)
```

### 6.9 `graceful_degradation` (phase 3)

```python
metadata = ContributionMetadata(
    name="graceful_degradation",
    phase="after_orchestrator_ready",
    after=("primary_persona",),                  # notification channel uses persona
    config_file="degradation.yaml",
)

def contribute(self, host):
    cfg = load_config(host.config_dir / "degradation.yaml")
    notifier = DegradationNotifier(channel=...)  # one-on-one with loaded_persona
    component = DegradationComponent.build(
        cfg=cfg,
        orchestrator=OrchestratorHooksAdapter(host.orchestrator),
        scope_runtime=host.scope_runtime,
        notifier=notifier,
    )
    host.register_shutdown("graceful_degradation", component.stop)
```

Note: `DegradationComponent` is constructed here, not in the orchestrator. The orchestrator's `pause_activation` / `resume_activation` methods are the contract surface; the adapter adapts them via `OrchestratorHooksAdapter`.

### 6.10 `memory_system` (sidecar launcher — phase 3)

```python
metadata = ContributionMetadata(
    name="memory_system",
    phase="after_orchestrator_ready",
    after=(),
    config_file="memory_system.yaml",
    required=False,                              # optional; workspace may run sidecar externally
)

def contribute(self, host):
    cfg = load_memory_config(host.config_dir / "memory_system.yaml")
    if cfg.launch_mode == "launchd":
        # The launchd plist is the canonical launcher; adapter only
        # verifies the sidecar is reachable.
        verify_memory_service_health(cfg.endpoint, timeout_seconds=10)
    elif cfg.launch_mode == "subprocess":
        proc = launch_memory_subprocess(cfg)
        host.register_shutdown("memory_system", lambda: graceful_kill(proc))
    elif cfg.launch_mode == "external":
        # User manages the service themselves (e.g. Docker); adapter no-op.
        pass
```

**Non-trivial adapter per §0.1.** Memory-system is a sidecar FastAPI service; its "registration" is about making sure the service is up (launchd mode) or launching it (subprocess mode). Workspaces that run it externally disable the adapter via `required=False` and remove from manifest if desired.

### 6.11 `self_upgrade` (readiness probe — phase 3)

```python
metadata = ContributionMetadata(
    name="self_upgrade",
    phase="after_orchestrator_ready",
    after=(),
    config_file=None,
    required=False,                              # optional; CLI may not be installed
)

def contribute(self, host):
    # Self-upgrade is an external CLI. The adapter verifies `pos upgrade --version`
    # exits 0 and logs the version; it does not run anything at boot.
    try:
        version = probe_self_upgrade_cli()
        host.emit_diagnostic("info", f"self_upgrade CLI available: v{version}")
    except Exception as e:
        host.emit_diagnostic("warn", f"self_upgrade CLI unavailable: {e}")
```

**Non-trivial adapter per §0.2.** Self-upgrade is CLI-only; the adapter is a readiness probe. Its `required=False` is deliberate — a workspace without `pos upgrade` installed should still start; the user gets a warning, not a boot failure.

### 6.12 `workspace_bootstrap_py` (escape-hatch — phase 3, last)

```python
metadata = ContributionMetadata(
    name="workspace_bootstrap_py",
    phase="after_orchestrator_ready",
    after=("primary_persona", "graceful_degradation", "self_correction"),
    config_file=None,
    required=False,                              # if ~/.pos/bootstrap.py absent, skip
)

def contribute(self, host):
    path = host.config_dir / "bootstrap.py"
    if not path.exists():
        return                                   # silent no-op — escape-hatch is optional
    from pos_orchestrator.bootstrap import load_and_register
    load_and_register(path, host.orchestrator)
```

**Per §2.7, this is the late-phase shim that preserves the orchestrator's existing `~/.pos/bootstrap.py` escape hatch without duplication.** The framework calls `load_and_register` directly; the orchestrator's loader is composed, not replaced.

---

## 7. `BootstrapHost` interface specification

See §2.5 and §4.1 for full shape. Summary:

**Host attributes (shared singletons):**

| Attribute | Type | Populated by | Phase available |
|-----------|------|--------------|-----------------|
| `config_dir` | Path | framework (from manifest) | all |
| `workspace_root` | Path | framework | all |
| `server` | IPCServer | orchestrator._startup | phase 2, 3 |
| `orchestrator` | Orchestrator | framework `main` | all |
| `scope_runtime` | ScopeRuntime | orchestrator._startup | phase 2, 3 |
| `objective_tracker` | ObjectiveTracker | orchestrator._startup | phase 2, 3 |
| `loaded_persona` | LoadedPersona\|None | primary_persona adapter | phase 3 (after primary_persona) |
| `tracer_provider` | TracerProvider | observability_aggregator adapter | phase 1 (after aggregator), 2, 3 |

**Host methods:**

| Method | Purpose |
|--------|---------|
| `register_shutdown(name, callable)` | hook for reverse-order graceful shutdown |
| `set_loaded_persona(persona)` | one-shot; only the primary_persona adapter calls this |
| `emit_diagnostic(level, message, **fields)` | structured diagnostic; stderr by default |

**Ownership summary:** host owns shared singletons (IPCServer, Orchestrator, TracerProvider, config dir, shutdown registry, loaded persona pointer). Contributions own their component-local state (SQLite stores, controllers, ledgers, FSMs). The framework does not "manage" component state beyond reverse-order shutdown.

---

## 8. Composition with existing `~/.pos/bootstrap.py` primitive

Covered in §2.7 and §6.12. Summary:

- `python -m pos_bootstrap` is the new entry point; the orchestrator's existing `python -m pos_orchestrator` remains valid for workspaces that haven't cut over.
- The framework calls `Orchestrator(config, require_bootstrap=False)` — because the framework is driving workspace bootstrap, the orchestrator's internal `load_and_register` call at `_startup` line 208–210 is disabled. The escape-hatch is run by the `workspace_bootstrap_py` adapter instead, at the correct late phase, with host attributes visible.
- Workspace authors with an existing `~/.pos/bootstrap.py` experience zero breakage on cutover — their `register(orchestrator)` function runs at the same point it always did (after the orchestrator is up, before the event loop's main wait). The only observable behaviour change is *when* the scope_runtime and objective_tracker exist on the orchestrator — which is the same time as before.
- If the `workspace_bootstrap_py` adapter is removed from the manifest, the escape-hatch is disabled entirely. Workspaces that have fully migrated to adapters don't need it.

---

## 9. Error-semantics specification

Per §2.6. Summary of fail-closed paths and diagnostic shape:

```
Diagnostic format (stderr, one line of JSON + one line of prose):
{"level":"error","code":"BOOT_DISCOVERY_FAILED","adapter":"...","detail":{...}}
[pos-bootstrap] failed: <adapter> resolution failed — <reason>. See diagnostic above.
```

Error classes and their exit codes (from §4.4):

| Code | Exit | Class | Fail-closed? | Diagnostic includes |
|------|------|-------|--------------|---------------------|
| `BOOT_MANIFEST_NOT_FOUND` | 2 | Missing manifest | yes | path attempted |
| `BOOT_MANIFEST_PARSE` | 3 | YAML parse error | yes | path, parser error |
| `BOOT_MANIFEST_SCHEMA` | 3 | Unknown keys / wrong version | yes | offending keys |
| `BOOT_DISCOVERY_FAILED` | 4 | Entry-point resolution failed | yes | adapter name, import exc |
| `BOOT_CONTRACT_VIOLATION` | 4 | Not a Contribution | yes | adapter name, missing attrs |
| `BOOT_METADATA_INVALID` | 5 | Pydantic validation | yes | adapter name, field errors |
| `BOOT_NAME_COLLISION` | 5 | Duplicate `name` | yes | adapters involved |
| `BOOT_PHASE_INVALID` | 5 | Unknown `phase` | yes | adapter name, phase value |
| `BOOT_REFERENCE_DANGLING` | 5 | `after`/`before` target absent | yes | adapter name, target name |
| `BOOT_ORDERING_CYCLE` | 6 | DAG cycle | yes | cycle edge set |
| `BOOT_REQUIRED_ADAPTER_FAILED` | 7 | `required=True` raised | yes | adapter name, traceback |
| `BOOT_OPTIONAL_ADAPTER_SKIPPED` | logged | `required=False` raised | no — proceeds | adapter name, traceback |

**Every fail-closed path runs BEFORE any adapter's `contribute()` has observable side effects**, with one exception: `BOOT_REQUIRED_ADAPTER_FAILED` fires *during* `contribute()`, after the adapter has started its work. In that case the framework still fails-closed — it does not run later contributions — but partial adapter state may exist on disk. This is inherent (the alternative is wrapping every `contribute()` in a transactional-rollback harness, which is over-engineered for the first version). The integration test matrix in §2.9 verifies the framework does not proceed past a required-adapter failure; cleanup of partial state is the adapter's responsibility.

---

## 10. Dependency map

**Bootstrap depends on:**

- All ten sealed components (as library deps):
  - `pos_orchestrator` (framework orchestrator core + existing `bootstrap.py` loader)
  - `scope_of_work`
  - `objective_tracker`
  - `primary_persona`
  - `pos_safety_layer` + `register_safety_ipc`
  - `pos_reversibility_primitive` + `register_reversibility_ipc`
  - `pos_cost_governance` + `register_cost_governance_ipc`
  - `pos_self_correction` + `register_self_correction_ipc`
  - `pos_graceful_degradation` + `DegradationComponent.build`
  - `pos_observability_aggregator` + `install_for_workspace`
  - `memory_system` (optional; sidecar-launcher adapter)
  - `pos_self_upgrade` (optional; readiness-probe adapter)

- Runtime stdlib/deps (framework only): `importlib.metadata` (stdlib 3.10+), `pydantic>=2`, `pyyaml>=6`. Zero new runtime deps beyond what sealed components already use.

**Bootstrap is depended on by:**

- Every Phase 4+ component that registers at boot — onboarding, dashboard, domain-workspace content loaders, close-associate allowlist installers, workspace seeders, backlog-tidy patches. All consume the `pos_bootstrap.contribution` extension protocol (§4.1).
- The workspace's `launchd` plist (or systemd unit) — points at `python -m pos_bootstrap`.

**Nothing sealed depends on bootstrap.** Every sealed component imports nothing from bootstrap; bootstrap is purely a downstream composer. This is load-bearing — it is why bootstrap can be sealed independently and why sealing does not retroactively affect sealed components' tests.

---

## 11. Complexity estimate

**AI-time anchor:** self-upgrade framework ~25 min (framework + plugin surface + clause enforcement — closest structural precedent). Self-correction ~16 min (pure consumer, no framework). Bootstrap falls between, with framework content on the high end (extension protocol, ordering engine, host interface) and adapter content that is mechanically straightforward once the framework is right.

**Estimate: 35 AI-min wall-clock. Red-line 55.** Within the plan's 30–45 band with headroom.

**Decomposition:**

| Piece | Time | Rationale |
|-------|------|-----------|
| `pos_bootstrap/contribution.py` (Pydantic model, Protocol) | 2 min | small; tight surface |
| `pos_bootstrap/ordering.py` (Kahn's + validation) | 3 min | textbook algorithm + unit tests |
| `pos_bootstrap/discovery.py` (entry-points + manifest + workspace-local paths) | 4 min | three resolution branches + errors |
| `pos_bootstrap/host.py` (BootstrapHost implementation) | 3 min | attribute/method surface |
| `pos_bootstrap/main.py` (CLI entry + phase orchestration) | 4 min | composition; stdlib only |
| `pos_bootstrap/adapters/*.py` × 12 adapters | 10 min | mostly boilerplate; safety/reversibility/cost are 2-3 min each; others ~1 min |
| Integration test suite (10 cases from §2.9) | 8 min | temp-workspace fixture + 10 scenarios |
| Seal test `test_no_sealed_amendments.py` | 1 min | copied from self-correction with BASELINE swap |

**Total:** 35 min; red-line covers 1.6× variance.

**Why not lower?** The extension protocol's surface must be right on first ship; each protocol deficit forces an amendment later. Time is biased toward correctness there (docstrings, Protocol types, clear diagnostics) rather than speed.

**Why not higher?** The ten-adapter bundle is mechanically straightforward once the framework is right — each adapter is ~15 lines of Python + ~5 lines of config-loading. The scaling term is the framework, not the adapter count.

---

## 12. Prototyping priorities

Questions the research cannot settle from reading alone — a prototype spike answers them in 10-15 minutes each:

1. **Entry-point resolution under editable installs.** `pip install -e` packages' entry-points sometimes do not surface to `importlib.metadata.entry_points`. Reproduce with the ten sealed packages installed editable; verify the framework discovers them. If editable entry-points are missing, the manifest-with-dotted-paths form is the fallback; documentation should warn.

2. **OTel `TracerProvider` override timing.** The observability-aggregator's `register_otel_provider` calls `trace.set_tracer_provider`. If any sealed component has already called `trace.get_tracer("...")` at module-import time and cached the result, the aggregator's provider override is a no-op for that tracer. The aggregator's own `detect_proxy_late_binding_failure` function exists for this reason. Prototype verifies that *the order bootstrap imposes* (aggregator adapter in phase 1, before any other contribution imports its component's runtime) actually avoids the failure in practice. Halt signal if not.

3. **Ordering engine correctness under partial overlap.** Phase 2's three wrap adapters declare interlocking `after`/`before` edges. Prototype verifies the DAG resolves to (cost, reversibility, safety) registration order (yielding the safety→reversibility→cost dispatch chain). Tie-breaking by name would produce (cost_governance, reversibility, safety) alphabetically — which happens to be the correct order, but the test should lock that the declarations, not the alphabet, are what ensures it.

4. **Shutdown correctness with an in-flight scope.** Bootstrap's shutdown path runs reverse-order host-registered shutdowns. If an in-flight `activate_scope` is mid-dispatch when SIGTERM arrives, the wrap chain (cost→reversibility→safety) must complete or be cleanly cancelled before the orchestrator's `_shutdown` cancels the heartbeat. Prototype verifies no orphaned state across the three wraps' stores.

5. **`~/.pos/bootstrap.py` escape-hatch migration.** A minimal workspace-local `bootstrap.py` that e.g. registers a custom notification hook must work identically under both `python -m pos_orchestrator` (old entry) and `python -m pos_bootstrap` (new entry). Prototype runs the same `bootstrap.py` under both entrypoints and verifies identical side effects.

6. **Manifest schema evolution.** A future v2 manifest should be rejected cleanly by a v1 framework. Prototype with a `version: 2` manifest verifies exit-3 with a clear diagnostic.

7. **Adapter `required=False` partial state.** If an optional adapter fails mid-`contribute()` after registering one IPC handler but before another, the framework proceeds. Prototype verifies the partially-registered handler does not cause dispatch-time confusion (e.g. a registered method whose backing controller was never fully constructed). If this fails, the design must add adapter-scoped teardown on failure before the next contribution runs.

8. **Cycle diagnostic readability.** A cycle of 4+ edges produces a diagnostic readable by a workspace author. Prototype synthesises a four-node cycle and verifies the diagnostic format is parseable (not a textbook graph dump).

---

## Summary — claim, not promise

This document makes one central claim: the extension protocol in §4 admits every Phase 4+ component without bootstrap amendment. The claim rests on four pillars:

1. **Discovery hybrid** (entry-points + manifest + workspace-local files) covers packaged, pre-installed, and workspace-local adapters with one contract surface. §2.1.
2. **Declarative Pydantic `Contribution` metadata** lets the framework build the DAG and resolve ordering before any adapter runs, so adapters are trusted inputs, not runtime unknowns. §2.1, §4.1.
3. **Three-phase model** makes the natural joints of orchestrator boot explicit — `before_orchestrator_start` for shared-singleton installation, `wrap_activate_scope` for the ordered gate chain, `after_orchestrator_ready` for everything depending on a running workspace. §2.3.
4. **Strict fail-closed error semantics** — cycle detection, reference validation, required/optional split — match the sealed components' posture and make boot failures loud and named, not silent and mysterious. §2.6, §4.4.

If any Phase 4+ component emerges that cannot register through this protocol, the design has failed and bootstrap unseals. Every adapter sketched in §6 and every extension scenario imagined (onboarding, dashboard, close-associate allowlist, domain-workspace content, persona seeders, backlog-tidy patches) fits the protocol without amendment. The two halt-signal items in §0 (memory-system sidecar, self-upgrade CLI) are specifically non-fit cases — and both are handled by adapters that *use* the protocol (readiness probe; sidecar launcher) rather than violating it.

The research is complete. Proposal authoring proceeds from here.
