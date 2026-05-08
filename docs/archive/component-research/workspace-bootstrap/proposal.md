# Proposal — Workspace Bootstrap

**Component:** Workspace Bootstrap — the framework that composes the ten sealed foundational components into a running orchestrator + gate chain, plus the foundational-adapter bundle, plus the published extension protocol through which Phase 4+ components register themselves without amending bootstrap.
**Status:** DRAFT — awaiting owner's approval before brief authoring.

**Branch:** `pos-v2`. **Language:** Python 3.13.
**Baseline:** `ac48a7b` (reversibility docstring fix, landed this session).
**Phase 4 opens on this component.**

---

## 1. Objective

Deliver workspace bootstrap such that:

- A workspace configured with a `bootstrap.yaml` listing the foundational-layer contributions starts a running orchestrator with the three-gate chain wired in the correct order (safety outermost, reversibility middle, cost innermost, orchestrator `orig_activate` at core), self-correction subscribed, primary-persona monitor ticking, observability aggregator routing, memory-sidecar launched and health-verified, self-upgrade CLI availability probed.
- A Phase 4+ component registers itself via a published extension protocol — one `bootstrap_adapter.py` contribution file in its own package, one `pyproject.toml` entry-point declaring availability, one line added to the workspace's `bootstrap.yaml` to enable it. **Bootstrap's own code never changes.**
- Ordering declarations on contributions (`name`, `phase`, `after`, `before`) are resolved by a topological sort with alphabetical tie-breaking; unsatisfiable orderings fail-closed at boot with a named cycle diagnostic; name-uniqueness enforced.
- The orchestrator's existing `~/.pos/bootstrap.py` escape hatch composes as a late-phase contribution — no regression.
- All boot errors (missing contribution, malformed config, unsatisfiable ordering, erroring adapter) fail-closed with named diagnostics. No silent substitution.

---

## 2. the owner's rulings (locked inputs)

| # | Question | Ruling |
|---|----------|--------|
| 1 | Reversibility stale docstring | **Amended as a discrete commit** before bootstrap build. Commit `ac48a7b` corrected the stale wrap-ordering docstring; 43/43 reversibility tests still pass. Bootstrap can baseline against `ac48a7b`. |
| 2 | Memory-system sidecar — in-process or separate process? | **Leave as sidecar.** The memory-system adapter is a sidecar launcher/health-probe; bootstrap accepts the structural asymmetry. No unseal. |
| 3 | Self-upgrade CLI — in-process IPC surface? | **Leave as CLI.** The self-upgrade adapter is a readiness probe (`pos upgrade --version`). Non-standard adapter shape accepted. |
| 4 | Orchestrator-constructed-four — extract into adapters? | **Leave as-is.** Graceful-degradation, primary-persona monitor, objective-tracker, and scope-of-work remain constructed inside `orchestrator._startup()`. Their adapters reference the constructed instances off `BootstrapHost` attributes rather than re-construct. |
| 5 | No-op declaration adapters for scope_of_work + objective_tracker | **Ship them.** Zero-side-effect adapters that register names in the ordering DAG so Phase 4+ contributions can declare `after=("scope_of_work",)` etc. |

---

## 3. Design shape (summary — detail in `research.md`)

### 3.1 Two-layer architecture

A new package `workspace-bootstrap/` (Python, on `pos-v2`) containing:

**Layer 1 — the framework.** Stable surface, sealed once, extended by future components *to* bootstrap rather than *within* bootstrap. Its objectives:

- A contribution type — a Pydantic-validated metadata record (name, phase, ordering declarations, optional config-file reference, required/optional flag) plus a `contribute(host)` callable. Metadata `extra="forbid"`, frozen.
- A discovery surface — hybrid: Python packaging entry-points supply *availability*; the workspace's `bootstrap.yaml` supplies *enablement*. Installed-but-not-listed is inert.
- A workspace-local escape — the manifest also accepts path-plus-callable entries for workspace-authored contributions that don't ship in a package.
- An ordering engine — per-phase DAG with deterministic tie-breaking, cycle detection, unknown-reference detection. `before` declarations resolve to reverse edges. The algorithm choice is the builder's call; the guarantee is a stable reproducible order given the same inputs.
- A `BootstrapHost` — constructed by the framework at boot. Owns shared singletons (IPC server, orchestrator, tracer provider, channel registry, config directory) and exposes named access to components the orchestrator constructs in its own `_startup()`. Access before the relevant phase is an error.
- A `main()` entry point — reads the manifest, discovers and validates contributions, topo-sorts per phase, constructs the host, runs contributions in order, starts the orchestrator's event loop, and provides structured-concurrency lifecycle so partial startup failures cancel siblings and shutdown reverses startup.

**Layer 2 — the foundational-adapter bundle.** One adapter per foundational component. Sealed alongside the framework. Twelve adapters total (inventory below).

### 3.2 Adapter inventory

| # | Adapter | Phase | Role | Ordering |
|---|---------|-------|------|----------|
| 1 | `observability_aggregator` | before | Registers the shared tracer provider every later span emitter depends on. | First in phase. |
| 2 | `scope_of_work` | before | Declaration-only. Orchestrator constructs the runtime in `_startup()`; this adapter registers the name for Phase 4+ `after=` declarations. | — |
| 3 | `objective_tracker` | before | Declaration-only; same rationale as #2. | — |
| 4 | `primary_persona` | before | Orchestrator constructs the monitor; adapter loads persona config and registers channels. | — |
| 5 | `graceful_degradation` | before | Declaration-only; orchestrator constructs. | — |
| 6 | `memory_system` | before | Sidecar launcher and health-probe per ruling #2. Fails-closed if the sidecar is unreachable within the configured deadline. | — |
| 7 | `reversibility_primitive` | wrap | Invokes the sealed registration entry point. Registers second among the wraps; becomes middle wrap at dispatch. | `after=cost_governance` |
| 8 | `safety_layer` | wrap | Invokes the sealed registration entry point. Registers last among the wraps; becomes outermost wrap at dispatch. | `after=reversibility_primitive` |
| 9 | `cost_governance` | wrap | Invokes the sealed registration entry point. Registers first among the wraps; becomes innermost wrap at dispatch against `orig_activate`. | `after=observability_aggregator` |
| 10 | `self_correction` | after | Constructs the controller and registers its subscriptions on the now-ready orchestrator. | — |
| 11 | `self_upgrade` | after | CLI availability probe per ruling #3. No in-process registration. | — |
| 12 | `workspace_bootstrap_py` | after | Invokes the orchestrator's existing `~/.pos/bootstrap.py` loader as a named late-phase contribution. Preserves the escape hatch the orchestrator already ships. | — |

The asymmetry (declaration-only adapters, sidecar launcher, CLI probe, escape-hatch loader) is accepted architecture — the extension protocol absorbs it precisely because `contribute(host)` means "do whatever this component needs at boot," not a narrow "register IPC method" shape.

### 3.3 Workspace manifest

A workspace `bootstrap.yaml` lists enabled contributions — dotted paths to `Contribution` subclasses for packaged contributions, and path-plus-callable dict entries for workspace-local files. The file version is pinned (`version: 1`) and the config-directory location is declared. The framework imports, validates metadata, inserts into the phase DAG, and runs each contribution.

Phase 4+ contributions and workspace-local adapters are appended to the same `contributions:` list; bootstrap's code never changes to admit them.

### 3.4 Error codes

Reserve `-32080..-32089` to bootstrap. Ship:

- `-32080 BOOTSTRAP_MISSING_CONFIG` — `bootstrap.yaml` not found or unparseable.
- `-32081 BOOTSTRAP_CONTRIBUTION_NOT_FOUND` — a listed contribution cannot be imported.
- `-32082 BOOTSTRAP_METADATA_INVALID` — a contribution's `ContributionMetadata` fails Pydantic validation.
- `-32083 BOOTSTRAP_NAME_COLLISION` — two contributions declare the same `name`.
- `-32084 BOOTSTRAP_ORDERING_CYCLE` — topological sort detects a cycle; edge set named in the diagnostic.
- `-32085 BOOTSTRAP_UNKNOWN_REFERENCE` — a contribution declares `after` or `before` against a name that is not listed.
- `-32086 BOOTSTRAP_ADAPTER_RAISED` — a `contribute(host)` invocation raised; contribution name + exception type + message in the diagnostic.

`-32087..-32089` reserved.

### 3.5 Seal-test pattern

`tests/test_no_sealed_amendments.py` uses the `SEAL_COMMIT` sidecar-file pattern from self-correction. Baseline `ac48a7b`. The sidecar file is populated at seal time; the test reads it and diffs `BASELINE..SEAL_COMMIT`. HEAD-based variant is the defect fixed on `f94d602` and must not be reintroduced.

---

## 4. Acceptance criteria (ODD — 25 objectives)

### 4.1 Framework — discovery & validation

- **B1.** A missing or malformed manifest raises `-32080` with a diagnostic that names the file and the parse error.
- **B2.** A contribution listed in the manifest but not available via the configured discovery mechanism raises `-32081` naming the missing identifier.
- **B3.** A contribution whose metadata fails schema validation raises `-32082` with the contribution identifier and the validation error.
- **B4.** Two contributions declaring the same `name` raise `-32083` naming both.
- **B5.** Workspace-local path-plus-callable entries that cannot be resolved (file missing, callable missing) raise `-32081` with the offending reference.

### 4.2 Framework — ordering engine

- **B6.** Topological sort resolves a well-formed DAG with `after`/`before` declarations; alphabetical `name` tie-breaking makes the order stable and reproducible.
- **B7.** A cycle is detected and raises `-32084` with the edge set listed.
- **B8.** An `after` or `before` reference to an unknown name raises `-32085`.
- **B9.** Phase ordering is respected — `before_orchestrator_start` contributions complete before any `wrap_activate_scope` contribution runs; `wrap_activate_scope` completes before any `after_orchestrator_ready`.

### 4.3 Framework — host + lifecycle

- **B10.** The host exposes the shared singletons (IPC server, orchestrator, tracer provider, channel registry, config directory) and named access to the orchestrator-constructed components (scope runtime, objective tracker, primary-persona monitor, graceful-degradation). Access before the phase that produces a given attribute raises a clear error.
- **B11.** Shutdown reverses startup order. A single adapter raising during startup triggers graceful teardown of already-started adapters; no adapter is left orphaned.

### 4.4 Foundational-adapter bundle

- **B12.** End-to-end integration test: all twelve foundational adapters listed in `bootstrap.yaml`; `main()` runs; orchestrator starts; `activate_scope` with no gate-fire conditions succeeds and flows through the three-wrap chain in dispatch order (safety → reversibility → cost → orig_activate).
- **B13.** Self-correction subscriptions fire on a synthetic failed scope (verified by asserting correction-episode row).
- **B14.** Memory-sidecar adapter launches the configured sidecar command, polls `/health`, proceeds on 200 response; times out to `-32086` after configurable deadline if `/health` never returns success.
- **B15.** Self-upgrade adapter runs `pos upgrade --version`; proceeds on exit 0; `-32086` on any other exit code.
- **B16.** Orchestrator-constructed-four (scope_of_work, objective_tracker, primary_persona monitor, graceful_degradation) are exposed on `host` as named attributes after `_startup()`; the no-op declaration adapters register their names in the ordering DAG without side effects.
- **B17.** `workspace_bootstrap_py` adapter invokes `orchestrator/src/bootstrap.py::load_and_register` with `host.orchestrator`; a missing `~/.pos/bootstrap.py` fails-closed with the orchestrator's existing `BootstrapMissing` error; a workspace-authored file executes its `register(orchestrator)` hook.

### 4.5 Phase 4+ extensibility (the protocol's actual test)

- **B18.** Synthetic Phase 4 contribution: a mock `onboarding_adapter` module defines a `Contribution` subclass with metadata `{name: "onboarding", phase: "after_orchestrator_ready", after: ("self_correction",)}`. Adding one line to the test workspace's `bootstrap.yaml` enables it; the framework discovers, validates, orders, and invokes `contribute(host)`. **Zero change to bootstrap's code.**
- **B19.** The same synthetic contribution with a cycle (`after: ("self_correction",), before: ("observability_aggregator",)`) trips `-32084`.

See also **B25** (§4.8) for the complementary framework-internal phase-set criterion — B18 scopes "zero change to bootstrap's code" to external-contribution registration; B25 names the framework-internal phase surface that bootstrap amendments (e.g. Amendment #4's `first_run_scaffold`) may extend.

### 4.6 Cross-cutting integration

- **B20.** `git diff --stat ac48a7b..<bootstrap-seal>` shows only `workspace-bootstrap/` changes (plus `data/` if runtime test output lands there). Zero deltas to any sealed component.
- **B21.** OTel spans flow through the observability aggregator's registered tracer provider; bootstrap emits its own `loam.bootstrap.*` spans (`contribution_started`, `contribution_completed`, `contribution_failed`, `ordering_resolved`, `phase_complete`).
- **B22.** Zero imports from current-gen Ruby pOS rules-file machinery.

### 4.7 Seal-test pattern + structural defences

- **B23.** `tests/test_no_sealed_amendments.py` uses `SEAL_COMMIT` sidecar-file pattern with baseline `ac48a7b`. HEAD-based variant refused in test-code review.
- **B24.** `ContributionMetadata` refuses empty `name`, phase values outside the three-enum set, or non-tuple `after`/`before`. SQL-equivalent structural defences: `name` uniqueness enforced by a dict lookup at framework load, not by SQL (no store needed for the framework itself — contributions are in-memory).

### 4.8 Framework-internal phase set (added amendment #17)

- **B25 — framework-internal phase set.** The `Phase` enum values in
  `workspace_bootstrap.spec` are the phases registered by contributions
  that live in `workspace-bootstrap/src/workspace_bootstrap/adapters/`
  (the framework-internal adapter bundle). Every enum value has at
  least one framework-internal adapter declaring
  `phase=Phase.<value>` in its `ContributionMetadata`. An external
  (Phase 4+) contribution declares its phase by referencing one of
  these existing values; adding an external contribution does not
  require extending the enum. If the framework-internal phase set
  grows (e.g. Amendment #4 added `first_run_scaffold`), the addition
  is a bootstrap amendment — not an external contribution — and the
  B18 "zero change to bootstrap's code" clause scopes to
  external-contribution registration, not to bootstrap-amendment
  commits. B25 names the framework-internal phase surface so future
  phase-enum additions have explicit audit-trail affordance rather
  than landing as silent widenings of B18's letter.

  Rationale. B18 asserts the external-extension contract — a Phase 4+
  contribution registers without touching `workspace-bootstrap/src/`.
  B25 asserts the complementary invariant — the phase-enum values ARE
  the framework-internal phase set, and external contributions
  consume them rather than extend them. Together B18 and B25 partition
  the space: B18 governs the external-extension protocol, B25 names
  the internal phase surface. When a future amendment widens the enum
  (as #4 did with `first_run_scaffold`), the amendment lands as a
  bootstrap amendment with its own ACs (H1–H5 for #4) and B25
  continues to hold; the grown enum set stays "the phases the
  bootstrap source itself registers."

---

## 5. Constraints

- **Branch:** `pos-v2`. **Language:** Python 3.13.
- **Permitted runtime deps:** stdlib (especially `importlib.metadata`, `asyncio.TaskGroup`), pydantic, pyee, opentelemetry, PyYAML, duckdb. **Test-only:** pytest, pytest-asyncio.
- **No amendments to sealed components.** The docstring fix on reversibility already landed as a discrete commit (`ac48a7b`) before this build starts; it is part of baseline.
- **Extension protocol is the central contract.** A protocol that doesn't admit Phase 4+ without bootstrap amendment is a rejectable outcome. Halt and surface.
- **No monkeypatching.** Framework composes via explicit entry-points / manifest.
- **Fail-closed everywhere.** Missing config, malformed metadata, unsatisfiable ordering, erroring adapter — all fail-closed with named `-32080..-32086` diagnostics.
- **Compose with existing `~/.pos/bootstrap.py`** — adapter #12 (`workspace_bootstrap_py`) preserves the orchestrator's existing loader.
- **Seal-test pattern mandatory** — `SEAL_COMMIT` sidecar-file.
- **Max-first.** No LLM inference inside the framework.
- **A1 correction held.** `trace.get_tracer("loam.bootstrap")`; no TracerProvider construction.
- **Zero carryover from current pOS.**
- **Halt on deviation.**

---

## 6. File layout

Builder's call. The component should follow the one-package pattern established in the prior ten sealed components — `src/` for implementation, `tests/` for tests, `pyproject.toml` declaring the `loam.bootstrap` entry-point group. File partition inside `src/` is a cohesion judgement the builder makes; the acceptance criteria in §4 define what must be true, not how the code is split.

One output artefact that is a contract rather than an implementation detail: a short `docs/` or top-level document describing how a Phase 4+ component adds itself (one adapter file in their package, one entry-point line in their `pyproject.toml`, one line in the workspace's `bootstrap.yaml`). This is the public face of the extension protocol; it ships with the component.

---

## 7. Build phases and estimate

**Calibrated AI-time estimate: 30–45 minutes wall-clock. Red line at 55.**

Anchors: self-upgrade ~25 min (closest framework precedent — framework + clause enforcement + plugin surface), cost-governance ~16.5 min (pure adapter), self-correction ~16 min (pure consumer). Bootstrap is the most framework-content-heavy Phase 4 component: twelve adapters + topo-sort engine + host + lifecycle + entry-point discovery + manifest loader.

**Halt at 55 minutes.** The two named failure classes to investigate on overrun: ordering-engine edge cases (structured-concurrency shutdown under partial failure, or Kahn's-sort with complex `before`-declaration reverse-edges), or adapter bundle complexity (the sidecar launcher and CLI probe are the two with real I/O — flakiness there could eat budget).

Phase shape and commit granularity are the builder's call. Atomic commits per phase acceptable; single cohesive commit acceptable. The only hard requirement is that the final state satisfies every B-criterion in §4.

---

## 8. inferences recorded — flagged for the builder to challenge

1. **Three phase names** (`before_orchestrator_start`, `wrap_activate_scope`, `after_orchestrator_ready`). Research proposed these three as the minimal partition. If a different partition serves the ordering needs better, halt and propose.
2. **Error-code range `-32080..-32089`.** Parallel to prior frameworks' assignments; no overlap with safety (`-32040s`), reversibility (`-32050s`), cost (`-32060s`), or self-correction (`-32070s`).
3. **Memory-sidecar health-probe timeout.** the primary persona has not specified a value. The adapter needs a sensible default with per-workspace override; the specific number is the builder's call, informed by the sidecar's actual startup profile.
4. **Self-upgrade CLI probe invocation.** The adapter verifies the CLI is installed and responsive. The exact invocation the builder uses (`--version` vs a dedicated health subcommand vs exit-code-only) is the builder's call after inspecting the sealed CLI's actual entry points.
5. **Declaration-only adapters' structural check.** The no-op adapters for `scope_of_work` / `objective_tracker` need some test proving they're named participants rather than typos. The test shape is the builder's call; the objective is "the ordering engine resolves a DAG referencing these names."
6. **`workspace_bootstrap_py` adapter's phase.** Default lean is late-phase so the escape-hatch hook sees a fully-wired orchestrator. If a legitimate use case wants an earlier phase, the adapter may declare differently — challenge if so.
7. **Config-file-per-adapter vs unified bootstrap config.** recommendation is per-adapter (each reads its own config file from the configured directory; no unified bootstrap-level schema). Challenge if unifying proves cleaner.
8. **Structured-concurrency primitive choice.** Python 3.13 target has stdlib options; the builder picks. Objective is "partial startup failure cancels siblings; shutdown reverses startup cleanly."

---

## 9. Approval ask

sign-off on this proposal moves the component to `proposal_approved` and opens handoff-brief drafting. On brief review, the background agent is dispatched.

Specifically requesting approval of:

- The locked rulings in §2 as faithful to the conversation.
- The 24 ODD acceptance criteria in §4 (B1–B24) as the complete objective set.
- The constraints in §5 (two-layer architecture, fail-closed everywhere, no amendments, `-32080..-32089` error-code range, seal-test pattern).
- The 30–45 min estimate with 55-min red line.
- the primary persona's flagged inferences in §8 (approve as written, or adjust and re-land).

Approve as-is, approve with changes, or reject.
