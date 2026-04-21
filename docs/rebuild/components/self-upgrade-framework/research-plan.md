# Research Plan — Self-Upgrade Framework

**Component:** Self-Upgrade Framework — the coordinator that takes every sealed component's per-component R1 round-trip harness, wraps them in a system-wide upgrade operation, and enforces the seven-clause acceptance (the owner's, from memory-system's proposal addendum).
**Status:** DRAFT — awaiting owner's approval before research begins.

---

## Objective this research must serve

Identify the design shape for the self-upgrade framework such that:

- Every one of the seven clauses (a–g) from the owner's v1.1 R1 refinement can be verified atomically on a single upgrade operation.
- The framework composes the existing per-component R1 harnesses (memory's upgrade probe, scope-of-work's `capture_pre_upgrade` / `replay_post_upgrade`, objective-tracker's semantic round-trip, orchestrator's local-SQLite snapshot, graceful-degradation's snapshot_probe, observability-aggregator's DuckDB round-trip) without requiring amendment to any of them.
- The no-silent-skip rule (clause g — the owner's insertion) is enforced structurally: every change in the upgrade is accounted for (installed, skipped-with-surfaced-conflict, or rolled-back); there is no silent path.
- Rollback is deterministic: a failed upgrade restores the system to the pre-upgrade state byte-for-byte where possible, semantically where not.
- The orchestrator itself can be upgraded (self-referential case worth calling out — you can't upgrade the running process from inside it without care).

## Starting position

- **Eight sealed components on `pos-v2`** — memory, scope-of-work, primary-persona layer, objective tracker, orchestrator, graceful-degradation, observability-aggregator, plus the four Phase 1 primitives. Each has its own R1 harness:
    - Memory: `upgrade.py` with fidelity probe
    - Scope-of-work: `upgrade.py` with `capture_pre_upgrade` / `replay_post_upgrade` / `assert_no_drift`
    - Primary-persona layer: compaction-survival pattern doubles as upgrade-fidelity for persona identity
    - Objective tracker: mirrors scope-of-work's `upgrade.py` pattern
    - Orchestrator: `local_state.py` has `snapshot_probe()`; its launchd plist install + uninstall pattern lives in `operations.md`
    - Graceful-degradation: `state.py` has `snapshot_probe()`
    - Observability aggregator: DuckDB schema with v1.1 R1 semantic round-trip harness
- **pOS framework upgrade convention already has a precedent** in current pOS (`bin/upgrade-pos`) — the owner explicitly flagged silent-skip as the anti-pattern that inspired clause g. The current pOS's mechanism is the counter-example, not the reference.
- **Python 3.13 dev target, `pos-v2` branch**, permitted deps stdlib + pydantic + pyee + opentelemetry + PyYAML + DuckDB.
- **No assumed downstream consumer (A1 correction)** applies: framework emits OTel; consumers already include observability aggregator.

## Questions the research must answer

### 1. What counts as a "framework upgrade"

1. What is the upgrade unit — a git commit on `pos-v2`? A release tag? A set of files that have changed? The research should clarify what the framework considers an atomic upgrade so both the user and the rollback mechanism have the same semantic.
2. What's in scope of "framework" vs "workspace"? Clause (b) says personas survive — personas are workspace content. Clause (c) says memory entries survive — memory's durable state is workspace content. Clause (d) says in-flight tasks survive — scope-of-work's event log is workspace content. The framework upgrade must distinguish its own code changes from workspace-state preservation.
3. How does version numbering work — a single framework semver across all components, per-component semver with a framework manifest, hybrid? The spec implies single-framework-versioned; the research confirms.

### 2. Pre-upgrade readiness

4. What's the pre-upgrade check sequence? Candidates: each component's `snapshot_probe()` returns current state; durability snapshots are taken (DuckDB file copies, SQLite file copies, memory's Kuzu DB snapshot); the orchestrator pauses activation via the graceful-degradation hooks; in-flight scopes are given a graceful-stop window; observability aggregator flushes spool.
5. What's the "declared probe set" that each component replays? Each component has its own; the framework's job is to collect them all into a single pre-upgrade probe execution.

### 3. Upgrade execution

6. How does the upgrade execute? Options: (a) shell out to `git checkout` at a named commit + rerun any migration scripts; (b) explicit migration-file-based system with forward/backward migrations like Django or Alembic; (c) a declarative manifest of files-to-update + migrations-to-run. What fits pOS's single-user, Python-native, "framework is code + schema" shape?
7. How are schema migrations handled? Every component with a SQLite store has a `_SCHEMA_VERSION`; the framework orchestrates migrations where schemas change.
8. How is the orchestrator itself upgraded — stop the running process, replace files, restart? Or can we do in-place code reload? The orchestrator has its own launchd supervision; the research needs to sequence "stop → replace → start" correctly.

### 4. Post-upgrade verification — the seven-clause enforcement

9. How does the framework verify clause (a) — "active session continues without restart"? A session health check that runs post-upgrade while the session is still attached via the Unix socket.
10. Clause (b) — "personas load unchanged and pass compaction-survival": load each configured persona, run its compaction-survival self-test; assert all pass.
11. Clause (c) — "memory semantic round-trip equivalence": run memory's upgrade probe; compare; drift below threshold.
12. Clause (d) — "in-flight tasks preserved": diff pre-upgrade scope projections against post-upgrade scope projections; state-defining events must be intact.
13. Clause (e) — "breaking contract changes surface explicitly": the upgrade manifest declares breaking changes; the framework blocks upgrades with unsurfaced breaking changes.
14. Clause (f) — "upgrade is reversible": the pre-upgrade snapshot exists; the framework can restore it. Verify by doing a test rollback in CI.
15. Clause (g) — "every change actually installs, no silent skip": for each file-change in the manifest, post-upgrade diff verifies the change is applied OR the conflict is explicitly recorded in the upgrade report. Silent skip is a bug, not a feature.

### 5. Rollback

16. On any post-upgrade check failing, what's the rollback sequence? Restore pre-upgrade snapshots to all component stores; revert framework files; restart affected processes.
17. What's the atomicity boundary? If clause (c) passes and clause (d) fails, does the whole upgrade roll back, or do we retain (c)'s successful outcome? Research's call — likely atomic whole-upgrade rollback.

### 6. Conflict handling (clause g)

18. What's a "conflict with user customisation"? Examples: the user has edited a framework file locally and the upgrade wants to change the same lines; the user has added a workspace-local persona that would be shadowed by a new framework template; the user's workspace config has a key whose semantic has changed in the upgrade.
19. What does "surfaced with explicit resolution options" look like? A structured report listing each conflict with three-way-diff-style context; user picks resolution per conflict; upgrade resumes.
20. Is there a "bail" option — user can abort without applying any changes — preserving the pre-upgrade state entirely?

### 7. User-facing experience

21. What does the user see during an upgrade? Primary persona notifies via the one-on-one channel (inherits v1.1 R13 + v1.2 R15 restriction)? A CLI progress output? Both?
22. How long does a typical upgrade take? Research should estimate based on the current sealed-component snapshot sizes + probe set runtimes.
23. What's the failure-mode experience — if rollback succeeds, user sees "upgrade rejected, previous version restored"; if rollback fails, what? (This is the worst case and needs a story.)

### 8. Integration with adjacent components

24. **Orchestrator:** pauses activation during upgrade via `pause_activation("upgrade")`; resumes post-verification. The self-referential case — upgrading the orchestrator itself — needs a careful sequence.
25. **Graceful-degradation:** upgrade events are observable; the component should not treat an upgrade-induced pause as a Claude degradation event (otherwise false positive).
26. **Observability aggregator:** upgrade events are first-class spans. The aggregator's own DuckDB is part of what the upgrade checks. Bootstrap-based ingestion means the aggregator survives the orchestrator restart that an orchestrator upgrade may require.
27. **Primary-persona layer:** personas are loaded; upgrade doesn't replace them but does check they still pass compaction-survival.

## Constraints the research must respect

- **Python-native.** stdlib + pydantic + pyee + opentelemetry + PyYAML + DuckDB. Anything else requires halt-and-signal.
- **No amendments to any of the seven sealed components.** The framework consumes their existing `snapshot_probe()` / `upgrade.py` surfaces; if the research concludes a sealed component needs a new method to support a clause, halt and surface for owner's call.
- **Zero carryover from current pOS.** `bin/upgrade-pos` is the example of silent-skip to AVOID, not a reference implementation.
- **Max-first.** LLM inference inside the framework is unexpected. If needed for conflict-resolution wording, uses Claude via Max.
- **A1 correction held.** Framework emits OTel; observability aggregator subscribes automatically.
- **No personas in pOS core.**
- **Halt-on-deviation.** Surface rather than invent.
- **ODD-compatible.** Every recommendation traces to a clause (a)–(g); untestable options noted.

## Deliverable — what the research document must contain

A markdown document at `components/self-upgrade-framework/research.md` with:

1. **Survey of existing patterns** — Django migrations, Alembic, Flyway, Cargo's version management, git-based deployment rollback patterns, single-user local-first upgrade patterns (Homebrew's self-upgrade, Ollama's upgrade story).
2. **Recommended design shape** — for each of the eight question groups, options considered, recommended option, rationale.
3. **Clause-by-clause enforcement map** — for each of the seven clauses (a)–(g), the concrete mechanism that verifies it.
4. **Atomicity + rollback specification** — the atomicity boundary, the rollback sequence, the failure-mode for a failed rollback.
5. **Self-referential orchestrator upgrade** — the concrete sequence for upgrading the running process safely.
6. **Conflict report format** — what "silent-skip forbidden" looks like operationally.
7. **User-experience specification** — what the user sees, through which channel, at what cadence during an upgrade.
8. **Dependency map** — consumed by: nothing yet (self-upgrade is a root operation). Depends on: all eight sealed components.
9. **Complexity estimate** — AI-time with calibration note. Expected comparable to orchestrator (this is also an integration component with cross-cutting concerns); ballpark 400–600 AI-min.
10. **Prototyping priorities** — questions only a prototype can answer (e.g. the self-referential orchestrator-upgrade sequence timing; Kuzu snapshot size at realistic data volumes).

## Execution note

On owner's approval, the plan is passed to a general-purpose Agent. Halt-on-deviation applies throughout.

---

## Awaiting owner's approval

- Approve as written → the primary persona dispatches the research agent.
- Approve with changes → the primary persona incorporates and resubmits.
- Reject → the primary persona reworks.
