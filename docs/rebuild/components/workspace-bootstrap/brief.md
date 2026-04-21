# Handoff Brief — Workspace Bootstrap

**For:** the general-purpose Agent dispatched to build workspace bootstrap.
**From:** the primary persona, 2026-04-20 14:47 CDT.
**Status:** awaiting owner's review of this brief; not yet dispatched.
**Phase 4 opens on this component.**

---

## 1. What you are building

A workspace bootstrap component on the `pos-v2` branch of `the existing workspace root` that composes the ten sealed foundational components into a running orchestrator + three-gate chain, ships a foundational-adapter bundle for the ten (twelve adapters total, asymmetric by intent), and publishes an extension protocol through which Phase 4+ components register themselves without amending bootstrap.

Baseline for the build is commit `ac48a7b` (a reversibility-primitive docstring correction landed before build start).

## 2. Authoritative documents (read in this order)

1. **This brief** — operational objective, constraints, acceptance criteria.
2. **`docs/rebuild/components/workspace-bootstrap/proposal.md`** — the contract approved. Binding. Halt and signal rather than deviate.
3. **`docs/rebuild/components/workspace-bootstrap/research.md`** — design detail, prior-art survey, sequence shapes. Reference only; the proposal is the contract.
4. **`docs/rebuild/spec/pos-v2-objectives-spec.md`** — spec v1.0 + v1.1 + v1.2 addenda.
5. **`docs/rebuild/STATE.md`** — governing rules for the rebuild.

**Precedents to emulate** (all sealed on `pos-v2`):
- `orchestrator/src/bootstrap.py` — the existing `~/.pos/bootstrap.py` loader. **Compose with it** (the `workspace_bootstrap_py` adapter invokes it as a late-phase contribution); do not replace.
- `safety-layer`, `reversibility-primitive`, `cost-governance`, `self-correction` — each exposes a factored registration entry point the adapter bundle consumes.
- `self-correction/tests/test_no_sealed_amendments.py` + `tests/SEAL_COMMIT` sidecar-file — use this pattern for bootstrap's own no-amendments test. Baseline `ac48a7b`.

## 3. The objective (single sentence)

Deliver workspace bootstrap such that a workspace configured with a manifest listing the foundational contributions starts a running orchestrator with the three-gate chain in correct dispatch order (safety → reversibility → cost → orig_activate), all subscriptions wired, memory-sidecar health-verified, self-upgrade CLI availability-probed, the orchestrator's existing `~/.pos/bootstrap.py` escape-hatch preserved as a named late-phase contribution — AND such that a Phase 4+ component adds itself with one adapter file in its own package, one entry-point line in its `pyproject.toml`, and one line in the workspace manifest, with zero bootstrap code change.

## 4. Hard constraints (non-negotiable)

- **Branch:** `pos-v2`. **Language:** Python 3.13.
- **Permitted runtime deps:** stdlib, pydantic, pyee, opentelemetry, PyYAML, duckdb. **Test-only:** pytest, pytest-asyncio.
- **No amendments to sealed components.** The reversibility docstring fix landed as commit `ac48a7b` before this build; it is part of your baseline, not part of your scope. Halt and signal if any further amendment seems required.
- **Two-layer architecture.** Framework (contribution type, discovery, ordering engine, host, main) is one sealed surface; foundational-adapter bundle is sealed alongside. **Phase 4+ components extend *to* bootstrap, not *within* bootstrap.** If you find yourself wanting to amend bootstrap's framework to admit a future component, halt — that's the design failing.
- **Extension-protocol acid test is non-optional.** A synthetic Phase 4 contribution must enable via one manifest line plus one entry-point declaration, with zero change to bootstrap's source. This is B18 in the proposal; it's the contract's load-bearing test.
- **Fail-closed everywhere.** Missing manifest, malformed metadata, unsatisfiable ordering, erroring adapter — all fail-closed with named diagnostics in the `-32080..-32089` range.
- **Compose with the orchestrator's existing `~/.pos/bootstrap.py`** — the adapter-bundle entry for it preserves the primitive the orchestrator already ships.
- **No monkeypatching.** Framework composes via explicit entry-points / manifest; no magic import-time side effects.
- **No LLM inference inside the framework.**
- **A1 correction held.** Emit `pos.bootstrap.*` spans via `trace.get_tracer(...)`; do not construct a TracerProvider.
- **Error-code range `-32080..-32089`** reserved to bootstrap; no overlap with safety (`-32040s`), reversibility (`-32050s`), cost (`-32060s`), or self-correction (`-32070s`).
- **Seal-test pattern mandatory.** `SEAL_COMMIT` sidecar-file convention; baseline `ac48a7b`; never `..HEAD`.
- **Zero carryover from current pOS.**
- **Halt on deviation.**

## 5. Acceptance (ODD — 24 criteria, in proposal §4)

B1–B5: framework discovery & validation — manifest loader, entry-point resolution, metadata validation, name-collision detection, workspace-local path resolution.
B6–B9: ordering engine — topological sort with deterministic tie-breaking, cycle detection, unknown-reference detection, phase isolation.
B10–B11: host & lifecycle — shared singletons exposed at the right phase, structured-concurrency shutdown reversal.
B12–B17: foundational-adapter bundle — end-to-end integration, self-correction subscriptions firing, memory-sidecar health probe, self-upgrade CLI probe, orchestrator-constructed-four exposed on host, `workspace_bootstrap_py` escape-hatch firing.
B18–B19: **Phase 4+ extensibility — the protocol's acid test.** A synthetic contribution enables via one manifest line plus one entry-point declaration with zero bootstrap code change; a cyclic contribution trips the ordering engine.
B20–B23: cross-cutting — no sealed-component mutation, aggregator-routed OTel, no legacy imports, seal-test pinning.
B24: structural defences on the metadata schema.

Each criterion is an objective. Tests target it directly. Negative cases re-extend as positive objectives — if you find one worth naming, add as B25+ with rationale in the commit message.

## 6. Verify-against-code discipline

Before relying on any sealed-component surface, open the file on `pos-v2` and confirm the symbol exists with the shape you expect. Three surfaces most consequential to verify first:

- **The orchestrator's `~/.pos/bootstrap.py` loader** — `orchestrator/src/bootstrap.py` exposes `load_and_register(bootstrap_path, orchestrator)` with fail-closed semantics on missing/erroring files. Your `workspace_bootstrap_py` adapter invokes this verbatim; preserve the fail-closed posture.
- **The three gates' registration entry points** — safety, reversibility, and cost each expose a factored registration function. Confirm the exact names and signatures and pass `host.ipc_server` plus any config the sealed function requires. Registration order is load-bearing: reversibility before safety before cost so dispatch becomes safety → reversibility → cost → orig_activate. The sealed integration test `reversibility-primitive/tests/test_safety_wrap_composition.py` (now updated by self-correction's build to cover the four-wrap chain) documents the mechanic.
- **The orchestrator-constructed-four** (scope_of_work runtime, objective_tracker, primary-persona monitor, graceful-degradation) — confirm which attributes on the orchestrator instance expose them after `_startup()`. Your host surfaces these as named attributes; do not re-construct.

If any proposal-level claim doesn't match the code, halt and signal with the named file and symbol.

## 7. inferences recorded (proposal §8) — challenge any that feel wrong

Eight items are the primary persona's extrapolation rather than the owner's direct words:

1. Three phase names (`before_orchestrator_start`, `wrap_activate_scope`, `after_orchestrator_ready`).
2. Error-code range `-32080..-32089`.
3. Memory-sidecar health-probe timeout default.
4. Self-upgrade CLI probe invocation shape.
5. Declaration-only adapters' structural check.
6. `workspace_bootstrap_py` adapter's phase (late).
7. Per-adapter config vs unified bootstrap config.
8. Structured-concurrency primitive choice.

Challenge any with a halt signal and proposed alternative. Not load-bearing unless the owner confirms.

## 8. Estimate

**30–45 AI-minutes wall-clock. Red line at 55.**

Anchors: self-upgrade ~25 min (closest framework precedent), cost-governance ~16.5 min (pure adapter), self-correction ~16 min (pure consumer). Bootstrap is the most framework-content-heavy Phase 4 opener — framework + twelve adapters + ordering engine + discovery + host + lifecycle + integration tests.

**If the build exceeds 55 minutes, halt and signal.** The two named failure classes to investigate on overrun: ordering-engine edge cases under structured-concurrency shutdown with partial failure, or adapter-bundle I/O flakiness (the sidecar launcher and CLI probe are the two real-I/O adapters).

## 9. What I need back

On completion:

1. **Paths to the commits on `pos-v2`.** Commit granularity is your call.
2. **Test results** — every B-criterion (B1–B24, plus any B25+ you added) mapped to a passing test. If any is unsatisfied, name it and explain.
3. **Sealed-component diff check** — `git diff --stat ac48a7b..<your-head>` should show only workspace-bootstrap changes (plus `data/` if runtime test output lands there). Any other delta is a halt-signal.
4. **Confirmation that the no-amendments test uses `SEAL_COMMIT` sidecar-file pinning**, not HEAD. Baseline `ac48a7b`.
5. **Confirmation of the Phase 4+ extension-protocol acid test** (B18) — a synthetic contribution enabling with zero bootstrap code change.
6. **primary-persona inferences you challenged** and the alternative you chose (or halted on).
7. **Any halt signals** — named component + surface + what you tried first.
8. **Actual wall-clock vs the 30–45 min estimate.**

Return summary: under 500 words. Code and tests carry the detail.

## 10. Failure modes I am watching for

- Monolithic framework that knows about the ten foundational components by name rather than by contribution discovery. **The framework must not import any adapter directly**; adapters are discovered through the published protocol.
- Any Phase 4+ component requiring bootstrap code to change to be registerable. **B18 is the test that catches this** — do not let it be the weakest test in the suite.
- Silent activation of installed-but-not-manifested packages via entry-points alone. **Manifest is authoritative for enablement.**
- Prescribing HOW in the foundational adapters — e.g. reaching inside sealed components' internals rather than consuming their public registration surfaces.
- Reintroducing the HEAD-based `test_no_sealed_amendments.py` pattern. Use `SEAL_COMMIT` sidecar-file pinning, baseline `ac48a7b`.
- Letting the estimate slip past 55 minutes quietly. Halt at 55 and signal scope-creep or subtle I/O failure.
- Amending any sealed component. The docstring fix already landed separately; any further amendment is a halt signal.

---

**End of brief.** the owner reviews; on the owner's green light, dispatch follows.
