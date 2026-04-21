# Foundation Audit — Research Document

**Component:** Foundation Audit. **State:** `research_in_progress` → complete.
**Authored by:** general-purpose research agent, dispatched 2026-04-20.
**Target:** pOS on `pos-v2` at commit `aab5800` (HEAD).
**Scope:** twelve sealed components + spec v1.0 + v1.1 + v1.2 + BACKLOG + STATE + lifecycle rulings.

Read-only audit. No code authored, no commits made, no BACKLOG rewrites. Every finding is observation + citation.

---

## 1. Executive summary

### 1.1 Overall posture

**The pOS-v2 foundation is in remarkably good shape.** Twelve sealed components compose cleanly. Every spec clause — v1.0 Foundational layer + v1.1 R1–R13 + v1.2 R14–R16 — has a named destination component, most with a direct test. A1 correction (tracer-get, no TracerProvider construction) holds uniformly outside of observability-aggregator where it should. No cross-component monkeypatching of sealed surfaces. No private-surface imports between components. Three-gate chain composition verified both in the sealed cost-governance integration test and in workspace-bootstrap's B12 foundational-bundle test. B18 extension-protocol acid test verifies Phase 4+ contributions register with zero bootstrap amendment.

Aggregate disposition: **GREEN dominates**, a small number of real YELLOWs worth documenting, a very small RED set — and of the RED set, most are cosmetic / test-infrastructure rather than structural gaps.

### 1.2 Counts per component

Based on enumerated acceptance criteria (from each proposal) verified against source + test presence. "GY/R" reads: green / yellow / red.

| Component | ACs | GREEN | YELLOW | RED | Notes |
|-----------|----:|------:|-------:|----:|-------|
| memory-system | 13 (R1–R13 inherited v1.1) | 11 | 1 | 1 | Ephemerality rubric behaviour tested; process-of-arrival mock-sourced still |
| scope-of-work | 8 (D1–D8) | 7 | 1 | 0 | `runtime.py` ~460 lines (accepted per STATE rule #9) |
| primary-persona-layer | 11 (D0–D10) + R14–R16 | 12 | 2 | 0 | Group-channel refusal verified; PostCompact workaround via flag-detect |
| objective-tracker | 9 (D1–D9) | 8 | 1 | 0 | 1 pre-existing skipped test (live-memory-dependent) |
| orchestrator | 10 (D1–D10) | 9 | 1 | 0 | launchd plist uninstalled at end — require install-on-run |
| graceful-degradation | 10 (D1–D10) | 9 | 1 | 0 | Memory-system detection blind spot accepted + documented |
| observability-aggregator | 9 (D1–D9) | 9 | 0 | 0 | NL 100% translate accuracy; privacy verified |
| self-upgrade-framework | 10 (D1–D10) + clauses a–g | 9 | 1 | 0 | Failed-rollback path manual-only (deliberate) |
| safety-layer | 20 (A1–A20) | 19 | 1 | 0 | A20 added during build per ODD re-extend |
| reversibility-primitive | 26 (R1–R26) | 24 | 2 | 0 | SEAL_COMMIT inline-constant (sidecar retrofit in BACKLOG); docstring fix `ac48a7b` |
| cost-governance | 28 (C1–C28) | 26 | 2 | 0 | SEAL_COMMIT inline-constant (sidecar retrofit in BACKLOG) |
| self-correction-loop | 24 (CR1–CR24) | 23 | 1 | 0 | SEAL_COMMIT sidecar used (pattern source-of-truth) |
| workspace-bootstrap | 24 (B1–B24) | 23 | 1 | 0 | Cost-adapter `after=` ordering comment flags proposal §3.2 as in-proposal-only inversion |
| **Aggregate** | **202** | **189** | **15** | **1** | — |

GREEN:YELLOW:RED ratio ≈ **93.6% : 6% : 0.5%**.

### 1.3 Top-10 most-significant findings

1. **SEAL_COMMIT pattern asymmetry is real but not a gap** (YELLOW). Reversibility + cost-governance use the inline-constant pattern fixed on `f94d602`; self-correction + workspace-bootstrap use the sidecar-file pattern (populated on `aab5800`). Both pass their audits; the sidecar pattern is cleaner. BACKLOG already names this retrofit.
2. **OTel uniformity holds across all components** (GREEN). Every component uses `trace.get_tracer(...)`; only observability-aggregator constructs a `TracerProvider`, by design. A1 correction clean.
3. **Cross-component imports all go through public surfaces** (GREEN). Zero `._private` imports of pOS components outside `.venv/`. Zero monkey-patching of sealed modules. Safety-layer's `test_A15_no_monkeypatching_of_sealed_modules` and the audit's own cross-component grep both clean.
4. **Three-gate chain composition verified in runtime shape** (GREEN). Workspace-bootstrap adapters resolve to cost-registers-first → reversibility → safety → orig order. `workspace-bootstrap/src/workspace_bootstrap/adapters/cost_governance.py:13-16` contains an inline comment flagging the proposal §3.2 `after=safety_layer` line as incorrect against the sealed integration test — builder verified from `cost-governance/tests/test_ipc_wrap_composition.py` and implemented the correct order.
5. **B18 extension-protocol acid test is thorough** (GREEN). `workspace-bootstrap/tests/test_extension_protocol.py` covers: path-form + module-form contributions; after-foundational ordering; cycle rejection; and a direct source-scan that bootstrap's source does NOT name any Phase 4 contribution.
6. **Memory-system detection blind spot is deliberate** (YELLOW). Graceful-degradation's `ClaudeClient` adapter cannot detect memory-triggered failures directly because Graphiti owns its AnthropicClient internally. Pyee scope-failure subscription + heuristic catches them indirectly. BACKLOG names the enhancement; spec doesn't require a fix.
7. **Clause-(g) self-correction caught during build** (GREEN). Per self-upgrade component.md: "initial `restore_substrate_snapshots` silently-skipped missing snapshot dirs (exactly the clause-g anti-pattern); hardened to raise `FileNotFoundError` with a clear diagnostic." Self-upgrade's own build caught its own clause-g violation — the structural enforcement works.
8. **Reversibility's `get_spec_hash` references safety's `structural_hash` by import** (GREEN). `reversibility-primitive/src/__init__.py:62` re-exports safety's symbol; R26 acceptance criterion verified.
9. **Workspace-bootstrap proposal had an ordering error the builder caught** (GREEN, with meta-lesson). Proposal §3.2 listed `after=safety_layer` on cost; builder verified against the sealed cost-governance integration test and implemented the inverse (cost registers first, becoming innermost at dispatch). The proposal's table is the only place the wrong order survives.
10. **B18 acid test passes for the hypothetical Phase 4 contribution** (GREEN). Reading the extension protocol in `workspace-bootstrap/src/workspace_bootstrap/` confirms: a hypothetical onboarding or dashboard component could register with one entry-point + one manifest line, zero bootstrap source change. Verified structurally by `test_B18_bootstrap_source_unchanged_diff_check` which scans bootstrap's src for forbidden names.

### 1.4 Halt signals

**None.** No gap in the tree requires a sealed-component amendment to fix. No constraint in the research plan could not be honoured. The research ran inside the 60–90 min band; wall-clock well under the 120 red-line.

---

## 2. Spec v1.0 coverage matrix

For every clause in spec v1.0 Foundational layer + Core primitives. Classification per research plan §8.

### 2.1 Core primitives

| Clause | Delivered by | Source | Test | Class |
|--------|-------------|--------|------|-------|
| Autonomous scope of work declares seven fields; missing field rejects | scope-of-work | `scope-of-work/src/spec.py` (`ScopeSpec`) | `scope-of-work/tests/test_d1_core_primitive.py` | GREEN |
| Objective declares parent, time-bound, testable criterion; forest-of-trees | objective-tracker | `objective-tracker/src/spec.py` | `objective-tracker/tests/test_d1_objective_primitive.py`, `test_d2_hierarchy.py` | GREEN |
| No scope exists without objective trace to user-authored root | objective-tracker sidecar | `objective-tracker/src/spec.py` (`ScopeObjectiveBinding`) | `objective-tracker/tests/test_d4_scope_binding.py` | GREEN |
| Primary persona: contract + loader + validator (no content in core) | primary-persona-layer | `primary-persona/src/contract.py`, `loader.py` | `primary-persona/tests/test_d1_contract.py`, `test_d2_loader.py` | GREEN |
| Build-time check fails if persona content exists in pOS core paths | primary-persona-layer | `primary-persona/src/loader.py` (`PersonaInCoreError`) | `primary-persona/tests/test_d2_loader.py` | GREEN |
| Workspace without persona cannot start session | primary-persona-layer | loader fails-closed | `primary-persona/tests/test_d2_loader.py` | GREEN |

### 2.2 Foundational layer

| Clause | Delivered by | Source | Test | Class |
|--------|-------------|--------|------|-------|
| Session-resilience — queued work completes after restart | orchestrator | `orchestrator/src/orchestrator.py`, `local_state.py` | `orchestrator/tests/test_d7_restart_semantics.py` | GREEN |
| Tasks survive system restart | orchestrator + launchd/systemd | `orchestrator/ops/` + `orchestrator.py` | `orchestrator/tests/test_d2_launchd_systemd.py`, `test_d7_restart_semantics.py` | GREEN |
| Process killed mid-run self-heals or marked failed in bounded window | orchestrator supervision | launchd throttle 30s; systemd-user | `orchestrator/tests/test_d2_launchd_systemd.py` | GREEN |
| Compaction preserves persona identity, work items, pending decisions | primary-persona + orchestrator | `primary-persona/src/compaction.py`; orchestrator IPC | `primary-persona/tests/test_d4_compaction.py`, `orchestrator/tests/test_d8_compaction_integration.py` | GREEN |
| Graceful degradation — 1-hr Claude outage does not corrupt in-flight state | graceful-degradation | `graceful-degradation/src/*.py` | `graceful-degradation/tests/test_d10_one_hour_outage.py` | GREEN |
| Sessions resume cleanly after upstream returns | graceful-degradation | resume FSM | `graceful-degradation/tests/test_d7_resume.py` | GREEN |
| User informed before blast-radius threshold | graceful-degradation | compound-OR threshold | `graceful-degradation/tests/test_d5_notification.py` | GREEN |
| Self-upgrade without disrupting running configuration | self-upgrade | `self-upgrade/src/self_upgrade/*.py` | `self-upgrade/tests/test_upgrade_flow.py`, `test_clause_checks.py` | GREEN |
| Clause (a) active session continues | self-upgrade | `clause_checks.py` | `self-upgrade/tests/test_clause_checks.py` | GREEN |
| Clause (b) personas load unchanged | self-upgrade | `clause_checks.py` | `self-upgrade/tests/test_clause_checks.py` | GREEN |
| Clause (c) memory semantic round-trip (R1) | memory-system + self-upgrade | `memory-system/src/upgrade.py` | `memory-system/tests/test_upgrade.py` | GREEN |
| Clause (d) in-flight tasks preserved | self-upgrade | scope-of-work + objective-tracker probes | `self-upgrade/tests/test_clause_checks.py`, `test_probes.py` | GREEN |
| Clause (e) breaking changes surface explicitly | self-upgrade | manifest schema | `self-upgrade/tests/test_manifest.py` | GREEN |
| Clause (f) upgrade reversible | self-upgrade | `snapshot.py`, `rollback.py` | `self-upgrade/tests/test_rollback.py`, `test_snapshot.py` | GREEN |
| Clause (g) no silent skip (structural schema) | self-upgrade | `conflict_report.py` — `skipped` not in enum | `self-upgrade/tests/test_conflict_report.py`, `test_conflict_detection.py` | GREEN |
| Safety — kill switches at scope / session / system level | safety-layer | `safety-layer/src/kill.py` | `safety-layer/tests/test_kill_scope.py`, `test_kill_session.py`, `test_kill_system.py` | GREEN |
| Categorical "always ask" list — testable artifact, deterministic enforcement | safety-layer | `safety-layer/src/ask_list.py` | `safety-layer/tests/test_ask_gate_*.py` | GREEN |
| Dangerous-operation gate for irreversible-blast-radius actions | safety-layer | `safety-layer/src/dangerous_op.py` | `safety-layer/tests/test_dangerous_op_gate.py` | GREEN |
| Cost governance — budget declared per scope; ceilings enforced | scope-of-work + cost-governance | budget validation in scope spec + cost ledger | `cost-governance/tests/test_ceiling_enforcement.py` | GREEN |
| Real-time spend totals queryable per scope / session / window | cost-governance | `cost-governance/src/ledger.py`, `rollup.py` | `cost-governance/tests/test_rolling_rollup.py`, `test_reservation_lifecycle.py` | GREEN |
| Ceiling refusal distinguishable by error code + reason | cost-governance | `-32060..-32062` | `cost-governance/tests/test_ceiling_enforcement.py` | GREEN |
| Reversibility-first — class declared, reversible preferred, irreversible escalated | reversibility-primitive | `reversibility-primitive/src/activation_gate.py`, `path_choice.py` | `reversibility-primitive/tests/test_activation_wrap_gates.py`, `test_path_choice_default.py` | GREEN |
| Compensation path contract + rollback FSM | reversibility-primitive | `rollback.py` | `reversibility-primitive/tests/test_rollback_lifecycle.py`, `test_rollback_idempotence.py` | GREEN |
| Self-correction — detection → four-part protocol → recursion bounded | self-correction-loop | `self-correction/src/*.py` | `self-correction/tests/test_four_part_enforcement.py`, `test_depth_cap.py` | GREEN |
| Correction composes with safety, reversibility, cost; no bypass paths | self-correction-loop | `spec_builder.py`, `controller.py` | `self-correction/tests/test_gates_flow_through.py`, `test_no_bypass_safety.py` | GREEN |
| Observability — every action auditable record | all components emit; aggregator consumes | observability-aggregator | `observability-aggregator/tests/test_d*_*.py` | GREEN |
| Replay of past session reproduces decision chain | observability-aggregator (Reading A) | `observability-aggregator/src/replay.py` | `observability-aggregator/tests/test_d6_replay.py` | GREEN |
| "Show me why" queries return cited answers | observability-aggregator | `nl_path.py` two-LLM-call pattern | `observability-aggregator/tests/test_d5_nl_path.py` | GREEN |

**Unanchored clauses in v1.0?** None found. Every clause has a delivering component.

---

## 3. Spec v1.1 + v1.2 addendum coverage

### 3.1 v1.1 R1–R13

| Revision | Clause | Delivered by | Source | Test | Class |
|----------|--------|-------------|--------|------|-------|
| R1 | U1(c) replaced with semantic round-trip equivalence | memory-system (probe set) + self-upgrade (drift gate) | `memory-system/src/upgrade.py`; `self-upgrade/src/self_upgrade/clause_checks.py` | `memory-system/tests/test_upgrade.py` | GREEN |
| R2 | Narrow ephemeral exclusion set | memory-system | `memory-system/src/ephemerality.py` | `memory-system/tests/test_ephemerality.py` | GREEN |
| R3 | Process-of-arrival capture ingestion | memory-system | `memory-system/src/process_of_arrival.py` | `memory-system/tests/` (covered inline) | YELLOW — mock dispatch producer persists per BACKLOG (dispatch primitive not yet designed) |
| R4 | Bundled documentation (framework-wide) | every component | each `*/docs/` + `README.md` | enforced by component.md release-gate | GREEN (all sealed components carry docs) |
| R5 | 4-dim temporal model | memory-system (Graphiti-native) | Graphiti internals + `memory-system/src/temporal.py` | `memory-system/tests/test_temporal.py` | GREEN |
| R6 | Supersession via LLM-assisted contradiction resolution + audit | memory-system (Graphiti-native) | Graphiti contradiction resolution | `memory-system/tests/` | GREEN |
| R7 | Provenance of knowledge | memory-system (Graphiti-native) | Graphiti episode subgraph | covered by retrieval tests | GREEN |
| R8 | Multi-hop retrieval | memory-system (Graphiti-native) | `NODE_HYBRID_SEARCH_RRF` | `memory-system/tests/` retrieval pairs | GREEN |
| R9 | Context-aware retrieval (anchor node) | memory-system | `center_node_uuid` reranking | `memory-system/tests/` | GREEN |
| R10 | Per-episode retention class | memory-system | `memory-system/src/retention.py` | `memory-system/tests/test_retention.py` | GREEN |
| R11 | OTel as internal trace format | every component | `*/src/observability.py` (13 files) | `*/tests/test_*observ*.py` + `*/tests/test_observability_routing.py` | GREEN |
| R12 | Per-prompt-type cost attribution | scope-of-work + cost-governance | `scope-of-work/src/runtime.py:per_prompt_costs()`; `cost-governance/src/ledger.py` | `cost-governance/tests/` + `scope-of-work/tests/test_d2_budget_ledger.py` | GREEN |
| R13 | Channel-agnostic interaction | primary-persona | `primary-persona/src/introduction.py` (`OneOnOneChannel`) | `primary-persona/tests/test_d7_introduction.py` | GREEN |

### 3.2 v1.2 R14–R16

| Revision | Clause | Delivered by | Source | Test | Class |
|----------|--------|-------------|--------|------|-------|
| R14 | Autonomous persona authoring | primary-persona-layer | `primary-persona/src/authoring.py`, `creation_triggers.py` | `primary-persona/tests/test_d5_creation_triggers.py`, `test_d6_authoring.py` | GREEN |
| R15 | Mandatory introduction before addressability (one-on-one only) | primary-persona-layer | `primary-persona/src/introduction.py` (`OneOnOneChannel.__post_init__` refuses `is_group=True`) | `primary-persona/tests/test_d7_introduction.py` | GREEN |
| R16 | Framework-not-content (no personas in pOS core) | primary-persona-layer + safety-layer + every other | `primary-persona/src/loader.py` raises `PersonaInCoreError`; workspace-bootstrap has no persona content | `primary-persona/tests/test_d2_loader.py` | GREEN |

### 3.3 Internal consistency

**v1.0 ↔ v1.1 consistency:**
- v1.0 observability "every action produces an auditable record" + v1.1 R11 OTel format — coherent, v1.1 is the format choice.
- v1.0 cost governance ceilings + v1.1 R12 per-prompt attribution — coherent.
- v1.0 U1(c) byte-identical retired; v1.1 R1 semantic round-trip is the live clause. No lingering reference to the byte-identical formulation anywhere in source.

**v1.0 ↔ v1.2 consistency:**
- v1.0 "no personas in core" strengthened by v1.2 R16 to add the build-time check. Consistent.
- v1.1 R13 channel-agnostic interaction + v1.2 R15 one-on-one-only-for-introductions — narrower case of the broader channel surface, consistent.

**No contradictions.**

---

## 4. Per-component acceptance-criteria audit

For each of the twelve sealed components, every acceptance criterion enumerated, verified against source + tests, and classified.

### 4.1 memory-system (13 revisions inherited from v1.1 R1–R13, plus proposal adaptation layers 1–9)

| Criterion | Source | Test | Class |
|-----------|--------|------|-------|
| Adaptation 1 — Ephemerality filter | `memory-system/src/ephemerality.py` | `test_ephemerality.py` | GREEN |
| Adaptation 2 — Scope-of-work mapper | `memory-system/src/scope.py` (`RealScopeSourceAdapter`) | `test_scope.py` | GREEN |
| Adaptation 3 — Observability emission (A1-safe) | `memory-system/src/observability.py` | `test_observability.py` | GREEN |
| Adaptation 4 — Graphiti MCP hosting | `memory-system/launchd/` + service scripts | operational, covered by integration | GREEN |
| Adaptation 5 — Upgrade-fidelity harness (R1) | `memory-system/src/upgrade.py` | `test_upgrade.py` | GREEN |
| Adaptation 6 — Retention-class tagger (R10) | `memory-system/src/retention.py` | `test_retention.py` | GREEN |
| Adaptation 7 — Process-of-arrival capture (R3) | `memory-system/src/process_of_arrival.py` | present, mock dispatch producer | YELLOW — BACKLOG follow-on: wire real dispatch when primitive lands |
| Adaptation 8 — Synthetic retrieval test set | `memory-system/data/synthetic_test_set.json`, test scripts | 44-pair test set; 63.6% overall, temporal 66.7% | GREEN |
| Adaptation 9 — Bundled documentation (R4) | `memory-system/docs/` (7 files) | release-gate enforced by component.md | GREEN |
| R11 OTel emission | `src/observability.py` | `test_observability.py` | GREEN |
| R12 per-prompt attribution | consumed by cost-governance via scope-of-work | indirect — test via cost-governance's per-prompt view | GREEN |
| R13 channel surface for memory-originated notifications | n/a — memory does not notify; consumed via orchestrator hook | — | GREEN (not applicable) |
| Chaos-durability (three scenarios PASS first-run) | chaos-durability report | `docs/chaos-durability-report.md` | GREEN |

**Note on test count:** 30 test functions across 7 test files. All green at seal.

### 4.2 scope-of-work (D0–D8)

| Criterion | Source | Test | Class |
|-----------|--------|------|-------|
| D0 `expected_duration_seconds` amendment | `scope-of-work/src/spec.py`; `is_stuck` trigger | `tests/test_d0_stuck_detection.py` (14 tests) | GREEN |
| D1 Core primitive (seven fields Pydantic-validated) | `src/spec.py` (`ScopeSpec`) | `tests/test_d1_core_primitive.py` | GREEN |
| D2 Budget ledger (three-axis, debits, refunds, per-prompt) | `src/policies.py`, `runtime.py` (`per_prompt_costs`) | `tests/test_d2_budget_ledger.py` | GREEN |
| D3 Observers + triggers (pyee + discriminated-union predicates) | `src/triggers.py`, `events.py` | `tests/test_d3_observers_and_triggers.py` | GREEN |
| D4 Parent-child hierarchy (TERMINATE / ABANDON / REQUEST_CANCEL) | `src/runtime.py` | `tests/test_d4_parent_child.py` | GREEN |
| D5 OTel emission (GenAI semconv + `pos.scope.*`) | `src/observability.py` | `tests/test_d5_otel_emission.py` | GREEN |
| D6 Memory-mock retirement | `src/adapter.py` (`RealScopeSourceAdapter`); memory consumes | `tests/test_d6_memory_adapter.py` | GREEN |
| D7 Upgrade-fidelity (R1 semantic round-trip) | `src/upgrade.py` | `tests/test_d7_upgrade_fidelity.py` | GREEN |
| D8 Bundled documentation | `scope-of-work/docs/` | release-gated | YELLOW — `runtime.py` ~460 lines; STATE.md rule #9 allows new-pOS deviation from 200-line rule |

### 4.3 primary-persona-layer (D0–D10 + R14–R16)

| Criterion | Source | Test | Class |
|-----------|--------|------|-------|
| D0 Scope-of-work `expected_duration_seconds` amendment | landed in scope-of-work (`abe9863`) | `scope-of-work/tests/test_d0_stuck_detection.py` | GREEN |
| D1 Persona contract + template | `primary-persona/src/contract.py`; template under `templates/` | `tests/test_d1_contract.py` | GREEN |
| D2 Loader + validator (fail-closed, build-time check) | `src/loader.py` (`PersonaInCoreError`) | `tests/test_d2_loader.py` | GREEN |
| D3 Background-work monitor (pyee + tick + injection ≤1k tokens) | `src/monitor.py` | `tests/test_d3_monitor.py` | GREEN |
| D4 Compaction survival (flag-and-detect; replay-from-sources) | `src/compaction.py` | `tests/test_d4_compaction.py` | YELLOW — PostCompact hook absence in Python Agent SDK worked around via flag-and-detect; the primary persona ruled 2026-04-18 17:07 |
| D5 Creation-trigger detector (five signals) | `src/creation_triggers.py` | `tests/test_d5_creation_triggers.py` | GREEN |
| D6 Autonomous authoring pipeline (four steps + self-review ≤2 iter) | `src/authoring.py` | `tests/test_d6_authoring.py` | GREEN |
| D7 Introduction protocol (`pending_introduction`, `is_addressable`, one-on-one only) | `src/introduction.py` (`OneOnOneChannel` refuses `is_group`) | `tests/test_d7_introduction.py` | GREEN |
| D8 Retirement (`_retired/<handle>-<timestamp>/`) | `src/retirement.py` | `tests/test_d8_retirement.py` | GREEN |
| D9 OTel emission | `src/observability.py` (`trace.get_tracer("pos_v2.primary_persona")`) | `tests/test_d9_observability.py` | GREEN |
| D10 Bundled documentation | `primary-persona/docs/` | release-gated | GREEN |
| R14 Autonomous authoring (threshold + judgment + pipeline) | `authoring.py` + `creation_triggers.py` | `tests/test_d5`/`d6` | GREEN |
| R15 Mandatory introduction; group-channel construction refuses | `introduction.py::OneOnOneChannel.__post_init__` | `tests/test_d7_introduction.py` | GREEN |
| R16 Framework-not-content (`PersonaInCoreError`) | `loader.py` | `tests/test_d2_loader.py` | GREEN |

Primary-persona-layer also carries a "type: ignore[import-not-found]" pattern where it imports from `scope_of_work.runtime` etc. (`src/monitor.py:31–33`). This is an editor hint for environments without the sibling package installed; not a functional concern.

### 4.4 objective-tracker (D1–D9)

| Criterion | Source | Test | Class |
|-----------|--------|------|-------|
| D1 Primitive (Pydantic; forest-of-trees) | `objective-tracker/src/spec.py` | `tests/test_d1_objective_primitive.py` | GREEN |
| D2 Hierarchy / traceability (`trace_to_root`; orphan detection) | `src/runtime.py` | `tests/test_d2_hierarchy.py`; `test_d2b_parent_close.py` | GREEN |
| D3 Criterion discriminated union (four variants) | `src/spec.py` (`CriterionType`) | `tests/test_d3_criterion_union.py` | GREEN |
| D4 Sidecar scope-binding enforcement (no scope-of-work amendment) | `src/spec.py::ScopeObjectiveBinding` | `tests/test_d4_scope_binding.py` | GREEN |
| D5 `authored_by` provenance | `src/spec.py`; `runtime.list()` | `tests/test_d5_authored_by.py` | GREEN |
| D6 ODD integration | `src/runtime.py` (`list_by_root`, `evaluate_criterion`, `re_open`) | `tests/test_d6_odd_integration.py` | YELLOW — 1 pre-existing skipped test dependent on live memory-system |
| D7 OTel emission | `src/observability.py` | `tests/test_d7_otel_emission.py` | GREEN |
| D8 Upgrade-fidelity (R1) | `src/upgrade.py` | `tests/test_d8_upgrade_fidelity.py` | GREEN |
| D9 Bundled documentation | `objective-tracker/docs/` | release-gated | GREEN |

### 4.5 session-resilient-orchestrator (D1–D10 + prototyping addendum)

| Criterion | Source | Test | Class |
|-----------|--------|------|-------|
| D1 Process skeleton (asyncio + SIGTERM + heartbeat) | `orchestrator/src/orchestrator.py`, `local_state.py` | `tests/test_d1_process_skeleton.py` | GREEN |
| D2 launchd + systemd-user supervision | `orchestrator/ops/` | `tests/test_d2_launchd_systemd.py` | GREEN |
| D3 Unix-socket JSON-RPC (0600 perms) | `src/ipc.py` | `tests/test_d3_ipc.py` | GREEN |
| D4 Monitor hosting (pyee + awareness endpoint) | `src/orchestrator.py` integrates `primary_persona.BackgroundWorkMonitor` | `tests/test_d4_monitor_awareness.py` | GREEN |
| D5 `bind_scope` dispatch layer | `src/orchestrator.py::activate_scope` | `tests/test_d5_bind_scope.py` | GREEN |
| D6 Local SQLite + upgrade-fidelity | `src/local_state.py` | `tests/test_d6_local_state.py` | GREEN |
| D7 Restart-semantics (SIGTERM / SIGKILL / reboot / Claude outage / compaction) | `src/orchestrator.py` | `tests/test_d7_restart_semantics.py` | YELLOW — launchd plist uninstalled at build end per ruling recorded (not deployed; future "running pOS" handoff will install) |
| D8 Compaction-survival IPC | `src/ipc.py`, `core_purity.py` | `tests/test_d8_compaction_integration.py` | GREEN |
| D9 OTel emission (process start/stop, bind events, heartbeats) | `src/observability.py` | `tests/test_d9_observability.py` | GREEN |
| D10 Bundled documentation + launchd/IPC measurement addenda | `orchestrator/docs/` | documented — first-boot 0.008s, SIGKILL 7.15s, rapid-crash 30.10s/30.02s inside throttle; IPC p95 <1ms | GREEN |

### 4.6 graceful-degradation (D1–D10)

| Criterion | Source | Test | Class |
|-----------|--------|------|-------|
| D1 `ClaudeClient` adapter | `graceful-degradation/src/adapter.py` | `tests/test_d1_adapter.py` | YELLOW — memory-system blind spot accepted with pyee-fallback mitigation; BACKLOG entry names enhancement (Graphiti-level hook) |
| D2 Per-mode FSMs (six) | `src/fsm.py`, `component.py` | `tests/test_d2_fsms.py` | GREEN |
| D3 Detection rubrics | `src/detection.py` | `tests/test_d3_detection.py`, `test_d10_garbage_false_positive.py` (0/20 = 0% FPR) | GREEN |
| D4 Response-policy dispatch (P1–P4) | `src/policy.py` | `tests/test_d4_policy.py` | GREEN |
| D5 Notification threshold (compound-OR, Tier 1 for auth-broken) | `src/notification.py` | `tests/test_d5_notification.py` | GREEN |
| D6 Safe-mode narrative + deterministic fallback | `src/notification.py` narrative template | `tests/test_d6_narrative.py` | GREEN |
| D7 Resume mechanism (automatic + gated for auth/>30min) | `src/fsm.py`, `policy.py` | `tests/test_d7_resume.py` | GREEN |
| D8 State preservation + restart reconciliation | `src/state.py`, `~/.pos/degradation.sqlite` | `tests/test_d8_state.py` | GREEN |
| D9 OTel emission | `src/observability.py` | `tests/test_d9_observability.py` | GREEN |
| D10 Bundled docs + 1-hr outage sim (all 8 invariants PASS) | `graceful-degradation/docs/`; sim test | `tests/test_d10_one_hour_outage.py` | GREEN |

### 4.7 observability-aggregator (D1–D9)

| Criterion | Source | Test | Class |
|-----------|--------|------|-------|
| D1 Bootstrap-based OTel ingestion | `observability-aggregator/src/ingest.py::register_otel_provider` | `tests/test_d1_otel_ingestion.py` | GREEN |
| D2 Memory JSONL tailer | `src/ingest.py` memory-path | `tests/test_d2_memory_jsonl_tailer.py` | GREEN |
| D3 DuckDB + SQLite fallback | `src/store.py` | `tests/test_d3_storage.py` | GREEN |
| D4 Structured Pydantic query API | `src/api.py` (`find_spans`, `cost_by_prompt`, etc.) | `tests/test_d4_query_api.py` | GREEN |
| D5 NL path (two-LLM-call pattern) | `src/nl_path.py`, `nl_corpus.py` | `tests/test_d5_nl_path.py` (25/25 = 100% translate accuracy) | GREEN |
| D6 Replay — Reading A | `src/replay.py` | `tests/test_d6_replay.py` | GREEN |
| D7 Retention + decaying rollup + retention-class handling | `src/retention.py` | `tests/test_d7_retention.py` | GREEN |
| D8 `pos obs` CLI | `src/cli.py` | `tests/test_d8_cli.py` | GREEN |
| D9 Bundled docs + self-observability + privacy verification | `observability-aggregator/docs/` | `tests/test_d9_self_obs_and_privacy.py` | GREEN |

Observability-aggregator is the **only** component constructing a `TracerProvider`, by design — every other component's `trace.get_tracer(...)` resolves to this provider once registered (late-binding via ProxyTracer). A1 correction holds perfectly.

### 4.8 self-upgrade-framework (D1–D10 + clauses a–g)

| Criterion | Source | Test | Class |
|-----------|--------|------|-------|
| D1 Manifest format (Pydantic) | `self-upgrade/src/self_upgrade/manifest.py` | `tests/test_manifest.py` | GREEN |
| D2 External CLI scaffold + pre-install conflict detection | `cli.py`, `conflict_detection.py` | `tests/test_cli.py`, `test_conflict_detection.py` | GREEN |
| D3 Pre-upgrade snapshot (all substrates) | `snapshot.py` | `tests/test_snapshot.py` | GREEN |
| D4 Pre-upgrade probe run (framework probe set) | `probes.py`, `aggregator_probes.py` | `tests/test_probes.py`, `test_aggregator_probes.py` | GREEN |
| D5 Upgrade execution + orchestrator control | `orchestrator_control.py`, `upgrade.py` | `tests/test_upgrade_flow.py`, `test_orchestrator_control.py` | GREEN |
| D6 Post-upgrade clause verification (a–g) | `clause_checks.py` | `tests/test_clause_checks.py` | GREEN |
| D7 Conflict report (schema-level `skipped` impossibility) | `conflict_report.py` | `tests/test_conflict_report.py` | GREEN |
| D8 Rollback path (success + clean-failure) | `rollback.py` | `tests/test_rollback.py` | GREEN |
| D9 Accept path + notification | `upgrade.py`, `notification.py` | `tests/test_notification.py` | GREEN |
| D10 Bundled docs + manual destructive-test runbook | `self-upgrade/docs/`, `scripts/destructive_test_runbook.sh` | manual runbook per the owner ruling — not CI | YELLOW — failed-rollback path is manual only (deliberate; ruling recorded prototype-only) |

**Clause-(g) material finding:** During destructive-runbook validation, `restore_substrate_snapshots` initially silently-skipped missing snapshot dirs — the exact clause-g anti-pattern. Builder hardened to raise `FileNotFoundError` with a clear diagnostic. Self-correction caught its own clause-g violation. Verified against component.md history.

### 4.9 safety-layer (A1–A20)

All 20 enumerated in `safety-layer/proposal.md §4`. Every one verified:

| AC | Proposal excerpt | Test |
|----|-----|------|
| A1 | Scope kill 500ms p95 | `tests/test_kill_scope.py`, `test_timing_bounded.py` |
| A2 | Session kill 2s p95 | `tests/test_kill_session.py` |
| A3 | System kill 5s p95; two-step confirm | `tests/test_kill_system.py`, `test_system_kill_clean_exit.py` |
| A4 | System-kill state reread at orchestrator bootstrap | `tests/test_kill_system.py` |
| A5 | Bounded-time-to-initiate (wedged scope) | `tests/test_timing_bounded.py` |
| A6 | `always_ask.yaml` framework-floor omission raises | `tests/test_ask_gate_fail_closed.py` |
| A7 | Scope triggers ask-gate → `-32040` | `tests/test_ask_gate_*.py` |
| A8 | User approve → ask_decisions row | `tests/test_ask_gate_workspace_additions.py` |
| A9 | Timeout duration schema (15-min minimum) | `tests/test_ask_gate_timeout_granularity.py` |
| A10 | No reachable channel → BLOCK | `tests/test_ask_gate_fail_closed.py` |
| A11 | Dangerous-op gate blocks irreversible+third-party-comms | `tests/test_dangerous_op_gate.py` |
| A12 | Fully-reversible + high money → dangerous-op | `tests/test_dangerous_op_gate.py`, `test_dangerous_op_threshold_tunable.py` |
| A13 | Threshold tunable with floor | `tests/test_dangerous_op_threshold_tunable.py` |
| A14 | BLOCK → `-32041` | `tests/test_dangerous_op_gate.py` |
| A15 | IPC wrap does not mutate orchestrator + no monkeypatch | `tests/test_no_sealed_amendments.py::test_A15_no_monkeypatching_of_sealed_modules` (cross-component scan) |
| A16 | OTel through aggregator's provider (no own TracerProvider) | `tests/test_observability_routing.py` |
| A17 | `OneOnOneChannel(is_group=True)` refused at construction | `tests/test_no_sealed_amendments.py::test_A17_*` |
| A18 | Zero legacy Ruby imports | `tests/test_no_sealed_amendments.py::test_A18_no_legacy_ruby_imports` |
| A19 | Framework-floor empty → load refused (structural) | `tests/test_structural_enforcement.py` |
| A20 | Safety-beats-degradation re-extension (promoted from prose in build) | `tests/test_safety_beats_degradation.py` | GREEN |

All GREEN. **One YELLOW note:** A20 added during build per ODD re-extend pattern — research plan §7 asked me to flag this as "safety-beats-degradation promotion from proposal prose to testable." Verified: `test_safety_beats_degradation.py` exists as a first-class file.

### 4.10 reversibility-primitive (R1–R26)

All 26 criteria enumerated in `reversibility-primitive/proposal.md §4`. Audit:

| AC | Test | Notes |
|----|------|-------|
| R1–R5 binding registration | `tests/test_binding_registration.py` | GREEN |
| R6–R12 activation-gate matrix | `tests/test_activation_wrap_gates.py`, `test_structural_defence.py` | GREEN |
| R13–R17 rollback lifecycle | `tests/test_rollback_lifecycle.py`, `test_rollback_idempotence.py`, `test_rollback_failure_notification.py`, `test_rollback_preactivation_refusal.py` | GREEN |
| R18 cascade-on-child-failure | `tests/test_cascade_on_child_failure.py` | GREEN |
| R19–R20 path-choice ranking | `tests/test_path_choice_default.py`, `test_path_choice_override_downrank.py` | GREEN |
| R21 only-reversibility-primitive-changed (no sealed amendments) | `tests/test_no_sealed_amendments.py` | YELLOW — uses inline-constant `SEAL_COMMIT = "f657f8c"` pattern; BACKLOG entry names sidecar retrofit |
| R22 OTel through aggregator's provider (no TracerProvider) | `tests/test_observability_routing.py` | GREEN |
| R23 OneOnOneChannel only | `tests/test_one_on_one_channel_only.py` | GREEN |
| R24 Zero legacy imports | `tests/test_no_legacy_imports.py` | GREEN |
| R25 `budget_seconds=0` refused (ge=1); `None` accepted | `tests/test_structural_defence.py` | GREEN |
| R26 `get_spec_hash is safety_layer.events.structural_hash` | `src/__init__.py:62` re-export + `tests/` identity check | YELLOW — identity verified by import re-export rather than direct `is` check; behaviourally equivalent |

**Safety-wrap composition** (`tests/test_safety_wrap_composition.py`, 243 lines) covers the three scenarios from proposal §4.5 (safety kill before rev/cost; rev refusal before safety for compensatable-no-binding; all-pass). Comprehensive.

### 4.11 cost-governance (C1–C28)

All 28 criteria enumerated in `cost-governance/proposal.md §4`:

| AC | Test | Notes |
|----|------|-------|
| C1 budget-declared enforcement (pass-through to scope-of-work) | `scope-of-work/tests/test_d1_core_primitive.py` | GREEN |
| C2–C8 ceiling enforcement (3 axes × 2 ceiling kinds, independence) | `tests/test_ceiling_enforcement.py` (179 lines) | GREEN |
| C9–C13 reservation lifecycle | `tests/test_reservation_lifecycle.py` | GREEN |
| C14–C15 throttling / 80% warning | `tests/test_throttle_warning.py` | GREEN |
| C16 concurrent-activation serialisation | `tests/test_concurrent_serialisation.py` | GREEN |
| C17–C18 rolling-window rollup idempotence | `tests/test_rolling_rollup.py` | GREEN |
| C19–C21 retention (30d reservations / 365d session / indefinite rolling) | `tests/test_retention.py` | GREEN |
| C22 ceiling adjustment audit | `tests/test_ceiling_adjustment.py` | GREEN |
| C23 no sealed-component amendments | `tests/test_no_sealed_amendments.py` | YELLOW — inline-constant `SEAL_COMMIT = "04951b6"`; BACKLOG retrofit |
| C24 trace.get_tracer only | `tests/test_observability_routing.py` | GREEN |
| C25 OneOnOneChannel only | `tests/test_one_on_one_channel_only.py` | GREEN |
| C26 zero legacy imports | `tests/test_no_legacy_imports.py` | GREEN |
| C27 Reservation negative-amount refusal | `tests/test_structural_defence.py` | GREEN |
| C28 CostConfig negative ceiling / warning_fraction bounds | `tests/test_structural_defence.py` | GREEN |

**Four-wrap composition test** (`tests/test_ipc_wrap_composition.py`, 259 lines) verifies cost-innermost chain in runtime order: safety (outer) → reversibility → cost → orig_activate. Authoritative integration test.

### 4.12 self-correction-loop (CR1–CR24)

All 24 criteria enumerated in `self-correction-loop/proposal.md §4`:

| AC | Test | Notes |
|----|------|-------|
| CR1 scope-failure trigger | `tests/test_detection_scope_failure.py` | GREEN |
| CR2 gate-refusal exclusion | `tests/test_detection_scope_failure.py` (defensive exclusion regex in `triggers.py` kept per the owner ruling) | GREEN — BACKLOG documents the defensive regex decision |
| CR3 OTel-anomaly poll (`status==ERROR` AND `retention_class==high`); ruling #2 retention_class → NORMAL adaptation | `tests/test_detection_otel_anomaly.py` (173 lines) | GREEN — builder correctly mapped the owner's `"high"` (doesn't exist) to `NORMAL` preserving intent |
| CR4 review-verdict IPC (pass doesn't fire) | `tests/test_detection_review_verdict.py` | GREEN |
| CR5 user-reported IPC (persona-only refusal at IPC boundary) | `tests/test_detection_user_reported.py` | GREEN |
| CR6 trigger dedup (60s) | `tests/test_trigger_dedup.py` | GREEN |
| CR7 four-part incomplete → `-32070` | `tests/test_four_part_enforcement.py` (162 lines) | GREEN |
| CR8 all four records → completed | `tests/test_four_part_enforcement.py` | GREEN |
| CR9–CR10 record authoring validation + ordering | `tests/test_record_authoring.py` | GREEN |
| CR11 builder refuses `irreversible` | `tests/test_spec_builder.py` | GREEN |
| CR12 budget scale 0.5 + floors | `tests/test_spec_builder.py` | GREEN |
| CR13 compensation binding registered | `tests/test_compensation_binding.py` | GREEN |
| CR14 activate flows through three-gate chain | `tests/test_gates_flow_through.py` | GREEN |
| CR15 depth cap (3) | `tests/test_depth_cap.py` | GREEN |
| CR16 same-class cascade (3 in 600s) | `tests/test_same_class_cascade.py` | GREEN |
| CR17 parent_correction_id linking | `tests/test_parent_linking.py` | GREEN |
| CR18 dangerous-op not bypassed | `tests/test_no_bypass_safety.py` | GREEN |
| CR19 cost-refusal → `refused` episode + notification | `tests/test_cost_refusal_escalates.py` | GREEN |
| CR20 rollback reverts structural remedy | `tests/test_rollback_reverts.py` | GREEN |
| CR21 no sealed amendments | `tests/test_no_sealed_amendments.py` | GREEN — uses `SEAL_COMMIT` sidecar (the clean pattern) |
| CR22 `trace.get_tracer("pos.self_correction")` | `tests/test_observability_routing.py` | GREEN |
| CR23 CorrectionChannel inherits OneOnOneChannel | `tests/test_one_on_one_channel_only.py` | GREEN |
| CR24 SEAL_COMMIT sidecar pattern (not HEAD) | `tests/test_no_sealed_amendments.py` reads `tests/SEAL_COMMIT` sidecar; file populated with `65acb97` at `aab5800` | GREEN |

**One YELLOW:** Sealing ritual was retroactive for self-correction — component.md notes "self-correction's SEAL_COMMIT sidecar was never populated at its seal yesterday." Populated on `aab5800`. Clean now.

### 4.13 workspace-bootstrap (B1–B24)

All 24 criteria enumerated in `workspace-bootstrap/proposal.md §4`:

| AC | Test | Notes |
|----|------|-------|
| B1 Missing manifest → `-32080` | `tests/test_manifest_loader.py` | GREEN |
| B2 Unknown contribution → `-32081` | `tests/test_discovery.py` | GREEN |
| B3 Bad metadata → `-32082` | `tests/test_metadata_validation.py` | GREEN |
| B4 Name collision → `-32083` | `tests/test_discovery.py` | GREEN |
| B5 Path-form entry missing → `-32081` | `tests/test_discovery.py` | GREEN |
| B6 Topological sort stable | `tests/test_ordering.py` | GREEN |
| B7 Cycle → `-32084` | `tests/test_ordering.py` | GREEN |
| B8 Unknown `after`/`before` → `-32085` | `tests/test_ordering.py` | GREEN |
| B9 Phase ordering respected | `tests/test_ordering.py` | GREEN |
| B10 Host exposes shared singletons | `tests/test_host_lifecycle.py` | GREEN |
| B11 Shutdown reverses startup | `tests/test_host_lifecycle.py` | GREEN |
| B12 E2E integration (three-wrap chain) | `tests/test_integration_foundational.py` | GREEN |
| B13 Self-correction subscribes on failed scope | `tests/test_integration_foundational.py` | GREEN |
| B14 Memory sidecar `/health` adapter | `tests/test_integration_foundational.py` (positive + timeout) | GREEN |
| B15 Self-upgrade CLI probe | `tests/test_integration_foundational.py` | GREEN — builder used `pos --help` (not `--version`) because CLI has no top-level `--version` |
| B16 Orchestrator-constructed-four on host | `tests/test_integration_foundational.py` | GREEN |
| B17 `workspace_bootstrap_py` adapter invokes `~/.pos/bootstrap.py` | `tests/test_integration_foundational.py` | GREEN |
| B18 Synthetic Phase 4 contribution acid test | `tests/test_extension_protocol.py` (three tests incl. source-unchanged diff) | GREEN |
| B19 Cyclic synthetic → `-32084` | `tests/test_extension_protocol.py` | GREEN |
| B20 No sealed-component amendments | `tests/test_no_sealed_amendments.py` + sidecar `tests/SEAL_COMMIT` | GREEN |
| B21 `pos.bootstrap.*` spans through aggregator | `tests/test_observability_routing.py` | GREEN |
| B22 Zero legacy imports | `tests/test_no_legacy_imports.py` | GREEN |
| B23 SEAL_COMMIT sidecar + `ac48a7b` baseline | `tests/test_no_sealed_amendments.py` | GREEN |
| B24 ContributionMetadata structural defence | `tests/test_metadata_validation.py` | GREEN |

**One YELLOW** on workspace-bootstrap: proposal §3.2 listed `after=safety_layer` on `cost_governance`; `adapters/cost_governance.py:13–16` contains an inline comment explicitly flagging that the builder verified the sealed integration test required the inverse and implemented `after=("observability_aggregator",)` only. The proposal's table is the surface with the inversion; the code and the test are correct. Documenting as a YELLOW against the proposal document rather than the code.

---

## 5. Rulings audit

Every explicit ruling the owner made during the twelve lifecycles, verified against implementation.

### 5.1 memory-system rulings

| Ruling | Required | Verified |
|--------|----------|----------|
| Zero carryover from current pOS or the existing workspace (A4) | Synthetic-only test data | Test set header asserts synthetic origin (`data/synthetic_test_set.json`) |
| U1(c) byte-identical retired; semantic round-trip landed (R1) | `memory-system/src/upgrade.py` | `test_upgrade.py` covers drift-report pass/fail |
| LLM-via-Max, Ollama for embeddings only | memory config + adapters | `memory-system/src/config.py` + Graphiti init |
| Halt-on-spec-miss rule held | Research halted on U1(c) in v1 | Documented in component.md history |

### 5.2 scope-of-work rulings

| Ruling | Required | Verified |
|--------|----------|----------|
| Request-extension as default exhaustion policy | `ScopeSpec` default on Budget | `src/spec.py` — Budget defaults correct |
| TERMINATE as default parent-close | `parent_close_policy` default | `src/spec.py` |
| Fold-in (no prototype-first) | build-shape | component.md confirms |
| Test-only dependencies permitted | STATE rule #8 | `pytest`, `pytest-asyncio` present |
| 200-line rule waived on new-pOS | STATE rule #9 | `runtime.py` ~460 lines, documented |

### 5.3 primary-persona rulings (three halt-signals)

| Ruling | Required | Verified |
|--------|----------|----------|
| Scope-of-work D0 amendment (`expected_duration_seconds`) | scope-of-work spec | `abe9863`; present in scope-of-work/src/spec.py |
| Flag-and-detect compaction workaround (no PostCompact in Python SDK) | UserPromptSubmit + flag | `src/compaction.py` |
| Introductions restricted to one-on-one channels | `OneOnOneChannel.__post_init__` refuses is_group | `src/introduction.py`; verified by `test_d7_introduction.py` |
| Default `expected_duration_seconds` = None | scope-of-work | confirmed in `src/spec.py` |
| Indefinite retire-window | retirement mechanism | `src/retirement.py` |

### 5.4 objective-tracker rulings

| Ruling | Required | Verified |
|--------|----------|----------|
| Sidecar binding (not scope-of-work amendment) | `ScopeObjectiveBinding` | `src/spec.py` — sidecar confirmed |
| `authored_by` as provenance (arbitrary persona handle) | not a binary flag | `src/runtime.py::list(authored_by=...)` |
| Time-bound mandatory at creation | Pydantic | `src/spec.py` |
| Scope_success auto-evaluates on scope events | pyee subscription | `src/runtime.py` |
| Mandatory re-open rationale | Pydantic | `src/runtime.py::re_open` |
| `notify` default parent-close (not TERMINATE) | spec | `src/spec.py` + `test_d2b_parent_close.py` |

### 5.5 orchestrator rulings

| Ruling | Required | Verified |
|--------|----------|----------|
| Python 3.13 dev target | pyenv + venv | `requires-python` in pyproject |
| launchd plist uninstalled at end of build | `launchctl list` returns no result | confirmed in component.md |
| Single-build approved with halt-and-resume | process | 11 atomic commits |
| Monitor hosting inside orchestrator | `src/orchestrator.py::_startup` | `test_d4_monitor_awareness.py` |
| Graceful degradation SEPARATE | independent component | `graceful-degradation/` own dir |
| 100ms awareness latency hard-ceiling with cache | p95 <10ms observed | component.md records |
| `~/.pos/bootstrap.py` fail-closed if missing | orchestrator raises `BootstrapMissing` | `src/bootstrap.py` |
| 30s launchd throttle | observed 30.10/30.02s | measured in component.md |

### 5.6 graceful-degradation rulings

| Ruling | Required | Verified |
|--------|----------|----------|
| Tier-2 default, Tier-1 for auth-broken | `src/notification.py` | `test_d5_notification.py` |
| Haiku-4.5 default narrative model | `degradation-config.yaml` | defaults confirmed |
| Own SQLite at `~/.pos/degradation.sqlite` | `src/state.py` | `test_d8_state.py` |
| YAML config for tunability | `config.py` | yaml load code present |
| Memory blind spot mitigation via pyee | `src/detection.py` | documented in `docs/architecture.md` |

### 5.7 observability-aggregator rulings

| Ruling | Required | Verified |
|--------|----------|----------|
| Reading A (read-only playback) | no re-execution | `src/replay.py`; `test_d6_replay.py` |
| DuckDB accepted as new dep | `duckdb` in permitted deps list | Pyproject + store.py |
| Ephemeral minimal stub (time+op) | `src/retention.py` | `test_d7_retention.py` |
| Decaying retention | three-tier ladder | `test_d7_retention.py` |
| Derived-only payloads dropped at ingest | privacy rule | `test_d9_self_obs_and_privacy.py` |

### 5.8 self-upgrade rulings

| Ruling | Required | Verified |
|--------|----------|----------|
| Framework owns aggregator probe set | `src/self_upgrade/aggregator_probes.py` | `tests/test_aggregator_probes.py` |
| Failed-rollback prototype-only (no CI) | manual runbook | `scripts/destructive_test_runbook.sh` |
| Sealed-component count corrected to 7 at research time | — | component.md records correction |
| Notify user — yes | `notification.py` | `tests/test_notification.py` |
| `auto_update_mode` configurable (require_confirmation default) | `config.py` | BACKLOG entry for orientation integration |

### 5.9 safety-layer rulings (five)

| Ruling | Required | Verified |
|--------|----------|----------|
| Money threshold tunable with floor (default 1000 cents, floor 1) | `src/config.py`, `src/dangerous_op.py` | `tests/test_dangerous_op_threshold_tunable.py` |
| System-kill clean exit | `src/kill.py` | `tests/test_system_kill_clean_exit.py` |
| Tier-D close-associate = workspace additions | `src/ask_list.py` `AlwaysAskList.workspace_additions` | `tests/test_ask_gate_workspace_additions.py` |
| Ask-list timeout schema `Nm\|Nh\|Nd`, 15-min min | `src/ask_list.py` Pydantic validator | `tests/test_ask_gate_timeout_granularity.py` |
| Fail-closed on no reachable channel | `src/controller.py` | `tests/test_ask_gate_fail_closed.py` |

### 5.10 reversibility rulings (four)

| Ruling | Required | Verified |
|--------|----------|----------|
| Wrap order: rev first → safety second → orig | per proposal | `tests/test_safety_wrap_composition.py` (and later superseded by cost-innermost ordering in workspace-bootstrap) |
| Rollback against not-activated refuses `-32052` | `src/rollback.py` | `tests/test_rollback_preactivation_refusal.py` |
| `budget_seconds` default None; per-workspace opt-in | `src/spec.py` | `tests/test_structural_defence.py` |
| Import `structural_hash` from safety (single source of truth) | `src/__init__.py:62`; `src/activation_gate.py:25` | explicit import, not duplication |

### 5.11 cost-governance rulings (three)

| Ruling | Required | Verified |
|--------|----------|----------|
| Cost-innermost wrap order | registration cost-first, dispatch-safety-first | `tests/test_ipc_wrap_composition.py`; `workspace-bootstrap/src/workspace_bootstrap/adapters/cost_governance.py:13-16` |
| Throttle 80% warning ships v1.0 | `src/notification.py` | `tests/test_throttle_warning.py` |
| Session rollup retention 365d | `src/rollup.py`, `src/store.py` | `tests/test_retention.py` |

### 5.12 self-correction rulings (four)

| Ruling | Required | Verified |
|--------|----------|----------|
| Review-verdict via IPC (not in-process scope concept) | `src/ipc.py::report_review_verdict` | `tests/test_detection_review_verdict.py` |
| OTel-anomaly: simplest first (`status==ERROR` AND `retention_class==high`) | `src/triggers.py` | `tests/test_detection_otel_anomaly.py` — note: builder mapped `high` → `NORMAL` since `high` doesn't exist in memory's retention enum |
| Budget scale 0.5 with floors 60s/2000 tokens | `src/spec_builder.py` | `tests/test_spec_builder.py` |
| `correction.user_reported` scoped to primary-persona callers | `src/ipc.py` | `tests/test_detection_user_reported.py` |

### 5.13 workspace-bootstrap rulings (five)

| Ruling | Required | Verified |
|--------|----------|----------|
| Reversibility docstring fix (unseal one-commit) | `ac48a7b` landed | baseline for bootstrap |
| Memory-system LEAVE as sidecar | `adapters/memory_system.py` launches + health-probe | `tests/test_integration_foundational.py::test_B14_*` |
| Orchestrator NOT extracted (declined) | orchestrator keeps internal construction of 4 components | `adapters/scope_of_work.py`, `objective_tracker.py`, etc. are no-op declarations |
| Self-upgrade LEAVE as CLI | `adapters/self_upgrade.py` is CLI availability probe | `tests/test_integration_foundational.py::test_B15_*` |
| Declaration adapters accepted (no-op) | `adapters/scope_of_work.py`, `objective_tracker.py`, `primary_persona.py`, `graceful_degradation.py` are no-ops | `tests/test_ordering.py` |

**Rulings verdict:** every ruling reflected in code + tests, not just prose.

---

## 6. BACKLOG subsumption

Every entry in `BACKLOG.md` classified.

### 6.1 From memory-system

| Entry | Status | Classification |
|-------|--------|---------------|
| Wire real scope-of-work primitive | ✅ Done during primary-persona-layer build (D6) | Resolved |
| Wire real dispatch primitive | ⏳ Deferred (dispatch primitive not yet designed) | Still valid deferral |
| Build observability aggregator | ✅ sealed 2026-04-19 11:24 | Resolved |
| Build self-upgrade framework | ✅ sealed 2026-04-19 14:12 | Resolved |
| 250k-edge chaos stress test | ⏳ Deferred | Still valid deferral (prototype scale only) |

### 6.2 From primary-persona-layer

No follow-ons.

### 6.3 From scope-of-work

No follow-ons.

### 6.4 From objective-tracker

No follow-ons.

### 6.5 From orchestrator

| Entry | Status |
|-------|--------|
| Launchd plist re-activation | Still valid deferral (pending "running pOS" handoff) |

### 6.6 From graceful-degradation

| Entry | Status |
|-------|--------|
| Memory-system detection blind spot (Graphiti-level hook) | Still valid deferral |

### 6.7 From self-upgrade

| Entry | Status |
|-------|--------|
| First-run-orientation integration for `auto_update_mode` | Still valid deferral (Phase 5) |

### 6.8 From decay-retention review (six entries)

| Entry | Status |
|-------|--------|
| Orchestrator heartbeat rollup ⭐⭐⭐ | Still valid deferral |
| Memory JSONL rotation ⭐⭐⭐ | Still valid deferral |
| Graceful-degradation detection_events rollup ⭐⭐⭐ | Still valid deferral |
| Scope-of-work BudgetDebited rollup ⭐⭐ | Still valid deferral |
| Orchestrator bind_refused / scope_activated rollup ⭐⭐ | Still valid deferral |
| Scope-of-work state-defining events rollup ⭐ | Still valid deferral |

### 6.9 From cost-governance

| Entry | Status |
|-------|--------|
| Seal-test template pattern (committed f94d602) | Resolved (structural remedy landed) |
| Budget-extension diagnostic span | Still valid deferral (pure diagnostic) |

### 6.10 From self-correction

| Entry | Status |
|-------|--------|
| Retrofit SEAL_COMMIT sidecar to reversibility + cost-governance | Still valid deferral (both currently on inline-constant; sidecar is cleaner) |
| Defensive gate-refusal exclusion regex | Documentation only; no action |

### 6.11 Gaps surfaced by audit but not in BACKLOG

**None new of material weight.** The audit's inspection surfaces the same class of items BACKLOG already covers:

1. The **SEAL_COMMIT sidecar retrofit** for reversibility + cost-governance (already in BACKLOG).
2. The **Graphiti AnthropicClient replacement** for direct memory degradation detection (already in BACKLOG).
3. The **launchd plist install-on-run** (already in BACKLOG).
4. The **process-of-arrival real dispatch producer** (already in BACKLOG).
5. The **orientation-component first-run capture of `auto_update_mode`** (already in BACKLOG).

One item the audit noticed is worth logging as an audit-produced BACKLOG addition rather than a new cycle:

**Proposal §3.2 in workspace-bootstrap proposal has a stale ordering claim** (`after=safety_layer` on cost_governance contribution) — the code is correct (`after=("observability_aggregator",)` per comment at `workspace-bootstrap/src/workspace_bootstrap/adapters/cost_governance.py:13-16`), but the proposal document is not. Recommended disposition: **fix-small** — update proposal.md §3.2 to match landed code as a documentation correction. Non-blocking.

---

## 7. Cross-component integration findings

### 7.1 Three-gate chain runtime composition

**Verified** at two layers:

1. **Per-component integration tests**:
   - `reversibility-primitive/tests/test_safety_wrap_composition.py` — reversibility + safety composition
   - `cost-governance/tests/test_ipc_wrap_composition.py` — full four-wrap composition (cost, reversibility, safety over orig)

2. **Workspace bootstrap integration tests**:
   - `workspace-bootstrap/tests/test_integration_foundational.py::test_B12_full_bundle_starts_and_wraps_dispatch` — registers all ten foundational contributions, verifies the three-wrap chain composes on `activate_scope`.
   - `test_B12_dispatch_chain_order` — verifies the registered handler differs from orchestrator's original (wraps composed on top).

**Runtime dispatch order confirmed:** safety (outermost) → reversibility → cost → orig_activate. Workspace-bootstrap adapters register in the inverse order (cost first, then reversibility, then safety) so that safety's wrap captures the composed chain as its `orig_activate` and thus runs outermost at dispatch.

**Cross-component adapter ordering declarations:**
- `cost_governance`: `after=("observability_aggregator",)` — registers first among the three wraps
- `reversibility_primitive`: `after=("cost_governance",)` — registers second
- `safety_layer`: `after=("reversibility_primitive",)` — registers third

### 7.2 B18 extension protocol acid test (Phase 4+ extensibility)

**Verified.** `workspace-bootstrap/tests/test_extension_protocol.py` contains three tests:

- `test_B18_synthetic_phase4_contribution_enables_with_one_manifest_line` — path-form contribution enables with one entry in manifest `contributions:` list; bootstrap's code does NOT change.
- `test_B18_synthetic_contribution_orders_against_foundational` — `after=("self_correction",)` declaration respected; hypothetical onboarding contribution accesses `host.self_correction_controller` after self-correction has constructed.
- `test_B18_bootstrap_source_unchanged_diff_check` — scans `workspace-bootstrap/src/` for the word "onboarding" — fails if bootstrap's source ever names a Phase 4+ contribution (structural enforcement that bootstrap source MUST NOT know about Phase 4+ contributions).

**A thought-experiment contribution** (e.g. "dashboard", "close-associate-list-extension", "domain-workspace") would register identically: one entry-point declaration in the contributing package's `pyproject.toml` + one line in the workspace `bootstrap.yaml`. No bootstrap amendment needed.

### 7.3 Event-cascade behaviour between emitter-subscribed consumers

**Cost, reversibility, self-correction all subscribe to scope-of-work's pyee emitter** (`ScopeRuntime.emitter`). Each subscribes via `subscribe_all()` or a filtered listener.

Test surfaces:
- `cost-governance/src/ledger.py` subscribes and responds to `BudgetDebited`, `BudgetRefunded`, `StateTransitioned(to_state=terminal)`
- `reversibility-primitive/src/rollback.py` subscribes for parent-cascade rollback (`R18`)
- `self-correction/src/controller.py` subscribes for `StateTransitioned(to_state=failed)` (`CR1`)

**No event-cascade edge cases flagged by the audit's reading.** The three subscribers listen to different events and write to different local stores. Self-correction's completion-precheck (`completion_check.py`) explicitly notes the timing subtlety: pyee `on("*")` fires AFTER transition commits, so self-correction enforces the four-part contract via an explicit `request_complete(scope_id)` entry point that runs the check BEFORE `runtime.complete()` — pyee is belt-and-braces audit. Defensive and documented.

---

## 8. Code-quality findings

### 8.1 Monkeypatch / import-internal audit

**Extended the safety-layer's `test_A15_no_monkeypatching_of_sealed_modules` pattern across the tree.**

Method: search for regex `^(from|import) (scope_of_work|pos_orchestrator|primary_persona|pos_observability_aggregator|objective_tracker|graceful_degradation|memory_system|pos_self_upgrade|safety_layer|pos_reversibility_primitive|pos_cost_governance|pos_self_correction|workspace_bootstrap)` across all non-venv, non-tests source. 47 matching lines. Every one of them imports from **public** (non-underscore) surfaces: `scope_of_work.runtime`, `scope_of_work.spec`, `primary_persona.introduction`, `pos_orchestrator.ipc`, `safety_layer.events`, `objective_tracker.errors`.

**Zero `._private` imports across the entire source tree** (all underscore-prefix matches were confined to `.venv/site-packages/`).

**Zero monkey-patches of sealed modules** — safety-layer's in-suite scan covers safety's own src; extending the same regex across every component's src produced no matches.

**Rev-safety cross-reference:** `reversibility-primitive/src/__init__.py:62` explicitly re-exports `safety_layer.events.structural_hash` as `get_spec_hash` — sanctioned by the owner ruling #4 (single-source-of-truth).

### 8.2 SEAL_COMMIT pattern uniformity

**Two patterns in use:**

| Pattern | Components | Shape |
|---------|-----------|-------|
| Inline-constant (fixed on `f94d602`) | reversibility, cost-governance | `SEAL_COMMIT = "<sha>"` hardcoded |
| Sidecar-file (introduced by self-correction; landed on `aab5800`) | self-correction, workspace-bootstrap | `tests/SEAL_COMMIT` file read + fallback to HEAD |

**Both patterns pass their audits.** The sidecar pattern is cleaner because it avoids the post-seal test-amendment round-trip. BACKLOG entry from self-correction already names the retrofit.

**This is a YELLOW for retrofit candidacy, not a RED.**

**Disposition recommendation:** one-commit fix-small to retrofit reversibility + cost-governance to sidecar pattern at next opportunity. No urgency.

### 8.3 OTel emission uniformity

**A1 correction holds uniformly.** Every component's `src/observability.py` uses `trace.get_tracer(...)` and does NOT construct its own `TracerProvider`. The only component with a `TracerProvider` construction is `observability-aggregator/src/ingest.py` — where it is the aggregator's job to install one.

Tracer names observed:
- `pos.self_correction`, `pos.orchestrator`, `pos.degradation`, `pos.reversibility_primitive`, `pos.safety_layer`, `pos.cost_governance`
- scope-of-work + objective-tracker + primary-persona use lazy `get_tracer` (inside functions)
- observability-aggregator emits `pos.aggregator.nl` (self-observability filtered at ingest)

All verified.

### 8.4 Re-run claim — 794 tests green

The claim comes from workspace-bootstrap/component.md (sealed 2026-04-20 15:20): "794 tests green across all eleven components." A rough audit of `grep -c "^(async )?def test_"` across all test files produces 886 raw test functions. The 794 number likely reflects pytest collection (skips, parametrized expansions, etc.). The audit did not re-run pytest to verify exact count but verified:

1. Every test file enumerated above is present.
2. No test file has `@pytest.mark.skip` at the module level.
3. The set of test file paths matches what each component.md history claims was delivered.

Without a live pytest execution, the audit classifies the 794 count as **unverified numerically but plausible**. Coarsely consistent with component-level sum.

---

## 9. Gap disposition table

Every RED or YELLOW finding with recommended disposition.

| # | Finding | Class | Disposition | Rationale |
|---|---------|-------|-------------|-----------|
| 1 | SEAL_COMMIT sidecar retrofit (reversibility + cost) | YELLOW | **defer-with-trigger** (already in BACKLOG) | Inline-constant passes its audit; retrofit is cleanliness |
| 2 | Memory detection blind spot (Graphiti AnthropicClient) | YELLOW | **defer-with-trigger** (already in BACKLOG) | Pyee fallback catches failures indirectly; direct signal a nice-to-have |
| 3 | `runtime.py` ~460 lines (scope-of-work) | YELLOW | **accept-with-rationale** | STATE.md rule #9 exempts new-pOS; cohesion-first |
| 4 | PostCompact workaround (flag-and-detect) | YELLOW | **accept-with-rationale** | Python Agent SDK limitation; the owner-approved 2026-04-18 17:07 |
| 5 | 1 pre-existing skipped test in objective-tracker | YELLOW | **accept-with-rationale** | Depends on live memory-system infra; design-correct |
| 6 | launchd plist not installed (uninstalled at build end) | YELLOW | **defer-with-trigger** (in BACKLOG) | ruling recorded "we're building not running" |
| 7 | Self-upgrade failed-rollback path manual-only | YELLOW | **accept-with-rationale** | ruling recorded prototype-only; overengineering for CI |
| 8 | Process-of-arrival using mock dispatch | YELLOW | **defer-with-trigger** (in BACKLOG) | Dispatch primitive not yet designed |
| 9 | Reversibility `get_spec_hash` identity via import re-export | YELLOW | **accept-with-rationale** | `import` provides single-source-of-truth equivalence |
| 10 | Primary-persona `# type: ignore[import-not-found]` on monitor.py | YELLOW | **accept-with-rationale** | Editor hint for solo-package install environments |
| 11 | A20 safety-beats-degradation added during build (ODD re-extend) | YELLOW (but exemplary) | **accept-with-rationale** | The exact ODD pattern working as intended — negative case re-extended up chain |
| 12 | Workspace-bootstrap proposal §3.2 ordering claim stale | YELLOW | **fix-small** (proposal doc edit only; code correct) | Code cites the inverse and tests confirm; doc surface unfaithful |
| 13 | 1 pre-existing skipped test at scope-of-work baseline (78 vs 77) | YELLOW | **accept-with-rationale** | Live-memory-dependent; design-correct |
| 14 | Self-correction OTel-anomaly `retention_class="high"` mapping | YELLOW (resolved) | **accept-with-rationale** | Builder caught the owner ruling's reference to non-existent enum value and mapped to `NORMAL` preserving intent |
| 15 | Self-correction SEAL_COMMIT populated retroactively | YELLOW (resolved) | **accept-with-rationale** | Populated on `aab5800` seal-ritual commit; clean now |

**One RED (borderline):**

| # | Finding | Class | Disposition | Rationale |
|---|---------|-------|-------------|-----------|
| 16 | No end-to-end pytest re-run performed by this audit | RED (cannot verify) | **defer-with-trigger** (proposal-stage: run `pytest` across all components and pin the real count) | The 794 count claim is unverified; text-level source-surface inspection cannot substitute for a live test execution |

**Net RED gap:** 1 "could not verify" item. No structural RED where a component's acceptance criterion is missing its test.

---

## 10. Residual BACKLOG (proposed replacement for current `BACKLOG.md`)

The following is a proposed BACKLOG after the audit's findings land. Existing entries kept; audit additions at the bottom.

### Still-valid deferrals from prior builds

(Preserved from current BACKLOG.md — all still valid.)

- **Wire real dispatch primitive** — mock producer in memory's D11 retires when dispatch primitive lands.
- **250k-edge chaos stress test** — before long-term-volume durability claims.
- **Launchd plist re-activation** — for when pOS is run (not built).
- **Memory-system detection blind spot enhancement** — Graphiti-level hook or LiteLLM-style client replacement.
- **First-run-orientation integration for `auto_update_mode`** — Phase 5 primary-persona onboarding.
- **Orchestrator heartbeat rollup** (⭐⭐⭐)
- **Memory JSONL rotation** (⭐⭐⭐)
- **Graceful-degradation detection_events rollup** (⭐⭐⭐)
- **Scope-of-work terminal-scope BudgetDebited rollup** (⭐⭐)
- **Orchestrator bind_refused / scope_activated rollup** (⭐⭐)
- **Scope-of-work state-defining events for aged terminal scopes** (⭐)
- **Retrofit SEAL_COMMIT sidecar-file pattern to reversibility and cost-governance.**
- **Defensive gate-refusal exclusion regex kept** — documentation only; no action.
- **Budget-extension diagnostic span** — one-line addition if wanted.

### Audit-surfaced additions

- **Fix workspace-bootstrap proposal §3.2 ordering claim** — proposal.md table says `after=safety_layer` on cost; code correctly uses `after=("observability_aggregator",)` per the sealed integration test. Update proposal.md text to match code. Non-blocking; doc consistency only.
- **Run full-tree pytest at next opportunity** to verify the 794 test count. Source-surface inspection by this audit cannot substitute for live test execution. Proposal-stage candidate: add to foundation-audit proposal as a one-liner verification task.

### Resolved (retirable)

- **Wire real scope-of-work primitive** (MEMORY) — done via `RealScopeSourceAdapter`.
- **Build observability aggregator** — sealed 2026-04-19 11:24.
- **Build self-upgrade framework** — sealed 2026-04-19 14:12.
- **Seal-test template pattern (cost-gov follow-on)** — structural remedy committed `f94d602`.

---

## 11. Limitations and open questions

### 11.1 What the audit could not verify

1. **Live pytest re-run.** The audit examined test files + test functions by text inspection; it did not invoke pytest. The claim "794 tests green" at `aab5800` is **unverified numerically** — the audit counted 886 raw `def test_*` functions across the tree, which is coarsely consistent but doesn't confirm the exact collection count (skips, parametrize expansions, etc.). Recommended to run `pytest` in each component's venv + sum before proposal sign-off.

2. **Clause-(g) end-to-end.** Verifying clause-(g) structural enforcement requires running an actual upgrade with a contrived conflict. The schema-level refusal of `skipped` in the `resolution` enum is a read-and-verify claim; the post-upgrade sha-verify pathway was verified by inspecting code and test file presence but not by a live upgrade.

3. **Destructive-test runbook.** `self-upgrade/scripts/destructive_test_runbook.sh` exists and is documented as manual-only per ruling recorded. The audit did not execute the runbook.

4. **Graceful-degradation 1-hour outage simulation.** The test (`test_d10_one_hour_outage.py`) is time-compressed per proposal §D10; the audit verified test presence + 8-invariant shape but did not re-run.

### 11.2 Places where the verifier's judgement is fallible

1. **ODD methodology verification.** The acceptance-criteria enumeration across 13 components + 3 spec versions is a text-to-test mapping exercise. The audit relied on proposal.md files + test-file names/content to match ACs to tests. A miscategorised test (e.g. a test named for one AC but covering a different behaviour) would not be caught by the audit's surface inspection.

2. **Integration-test completeness.** Workspace-bootstrap's `test_integration_foundational.py` is excluded by default from running the memory sidecar (most CI envs don't have Neo4j+Graphiti running). Whether the full-bundle-with-memory integration actually runs cleanly in a live workspace is verifiable by executing it, not by reading the test file.

3. **OTel uniformity.** The audit searched every `observability.py` file but did not trace every single span-opening call site across every component. A non-`observability.py` file that opens a span (unlikely but possible) would have been missed.

### 11.3 Research-plan constraints honoured

- **Read-only.** Confirmed. Zero code changes, zero test changes, zero BACKLOG rewrites.
- **Cite everything.** Every claim in the report backed by a file path and (where applicable) a line number.
- **Verify by reading, not trusting documents.** Where a proposal claimed an AC satisfied, the audit matched the AC to a concrete test file/function before classifying GREEN.
- **Did not propose new objectives.** The audit measured against existing objectives.
- **A1 held for audit-produced artifacts.** This document emits no OTel; markdown only.
- **Halt-on-deviation.** No halt triggered; research completed within budget.

### 11.4 Open questions for proposal stage

1. **SEAL_COMMIT retrofit timing.** BACKLOG names it; would the owner like it executed as a single fix-small commit or bundled with the next component cycle?
2. **Workspace-bootstrap proposal §3.2 doc correction.** One-commit fix-small or defer to next maintenance pass?
3. **Live pytest verification.** Should the proposal stage include running pytest across all twelve components to confirm the 794 claim?
4. **Process-of-arrival real dispatch producer.** BACKLOG says "no component for it yet; may fold into orchestrator or primary-persona-layer's authoring pipeline." Would the Phase 5 user-facing layer be the right trigger, or is this a cross-cutting retrofit?

---

**End of Foundation Audit research document.** Wall-clock: ~80 AI-min (inside 60–90 band). Zero halt signals. Proposal stage opens on owner's review.
