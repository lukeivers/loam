# Structural enforcement — A3: TDD-guard test-pinned-to-objective (PreToolUse Edit/Write refusal-on-missing-test-for-new-AC)

**Status:** authored 2026-04-28 (plan-doc only; no code, no commits, no manifest yet).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Programme:** A3 of the four-amendment structural-enforcement programme (A1 substrate sealed at amendment #51; A2 objective-binding gate sealed at amendment #70; A3 TDD-guard; A4 Bash/Agent-context guards). Programme research artefact: `docs/plans/research/structural-enforcement-of-critical-requirements-research.md` (LOCKED 2026-04-26). A3 research: `docs/plans/research/structural-enforcement-a3-tdd-guard-research.md` (this dispatch).
**Programme-level locks (per A1 plan header; carried forward, not re-litigated):** D1 dev-discipline carve-outs for `docs/`, `tools/`, `.scratch/`, `CLAUDE*.md`, `personas/`; **D2 TDD-guard scoped to re-extension-with-new-AC** (governs A3 directly); D3 manifest extends `objective-tracker`; D4 secret/blast-radius gates universal, ODD-discipline gates DEV-MODE-only; D5 KEEP-ADVISORY list of 10.
**Pre-flight verification (mandatory; per `feedback_verify_dispatch_before_sending`):** pre-A3-build dispatch verifies `git log --grep="A3\|tdd-guard\|TDD-guard"` returns no A3 amendment commit AND `ls docs/plans/ | grep -iE "a3|tdd-guard"` returns nothing matching `structural-enforcement-a3-*` other than this plan-doc. Halt-and-surface if either does.

---

## 1. Summary / TLDR

A3 is the SECOND gate-that-refuses in the structural-enforcement programme, after A2 (sealed at amendment #70). A2 refuses Edits whose path doesn't trace to a manifest-registered binding the active-scope sentinel admits. A3 refuses Edits that introduce code satisfying a NEW acceptance criterion without a test pinned to that AC landing in the same diff.

A3 ships:

1. **Single PreToolUse hook script.** `framework/hands-off-lifecycle/hooks/tdd_guard.py` — fires on `Edit|Write|MultiEdit` matchers AFTER A2's gate (A2 admits the path; A3 then verifies the test-existence invariant). Stdlib + A1-substrate readers + A2-shared-helper imports only; no third-party deps.
2. **Shared helper library extraction.** A2's `objective_binding_gate.py` is REFACTORED in-place to consume a new `framework/hands-off-lifecycle/hooks/_gate_helpers.py` module. The library carries: path canonicalisation, mode-bit query, sentinel reader wrapper, tracker-open, carve-out detection, audit-log appender. A2's existing AC.OBG.x tests must remain green byte-for-byte after the refactor (regression-protected by `test_no_sealed_amendments.py` + AC.OBG.S frozen-both-endpoints invariant).
3. **Multi-contributor `merge_pre_tool_use`.** A2's settings-merge function is extended to admit two pos-v2-owned PreToolUse entries (A2's gate + A3's gate) plus optional user-authored entries. The `_USER_AUTHORED` back-up convention is preserved.
4. **Audit log.** Every fire (allow + deny + no-op) appends one NDJSON line to `<workspace>/workspace/.pos/tdd-guard.log`. Append-only in A3; rotation deferred.

A3's behaviour:

- **DEV MODE workspaces, sealed-component non-test source path edits, NEW AC bound by sentinel without matching test:** deny.
- **DEV MODE workspaces, NEW AC has matching test (file + function):** allow.
- **DEV MODE workspaces, EXISTING AC (in-AC modification, not new in this diff):** allow (out of A3 scope per D2).
- **DEV MODE workspaces, test-tree paths (`framework/<comp>/tests/**`):** allow (chicken-and-egg avoidance).
- **DEV MODE workspaces, dev-discipline carve-out paths:** allow (D1, inherited from A2).
- **NORMAL USE workspaces:** allow regardless (D4).

After A3 lands, every Edit/Write/MultiEdit in a DEV MODE pos-v2 workspace that introduces code satisfying a NEW acceptance criterion is structurally bound to the test for that AC existing first. The "test before code for new ACs" rule (ODD §4 re-extension pattern) becomes mechanically enforced at edit time — the failure class moves from "review catches code-without-test after the fact" to "the edit cannot fire without the test."

A3 sets the precedent for A4 (Bash/Agent-context, different matchers), specifically: the shared helper library this amendment extracts is the substrate A4 composes against.

Per CLAUDE.md output convention, owner reads from §9 (decisions for owner) — every other section supports it.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5)

**Named spec objective this plan satisfies:**

- **`docs/spec/pos-v2-objectives-spec.md` line 134–135 — Deterministic (tiered).** Same binding A1 + A2 satisfied. A3's gate decisions add a second class of structural enforcement (test-pinned-to-AC) to the audit-log surface that line 135-(b) names ("any arbitrary decision (no rubric cited) surfaces as a lint failure pending rubric definition"). Every Edit that introduces a new AC without a test IS the surfaced lint output.
- **VALUE_PROPOSITION's two tests (the prime objective ACs).**
  - *Primary-persona test (AC.PO.1):* the persona's translation toolkit no longer has to remember "every new AC needs its test authored first." The substrate refuses test-less new-AC edits; the persona doesn't carry the rule. Reduces translation burden directly.
  - *Harness test (AC.PO.2):* the gate is a reusable harness primitive; its helper-library extraction is the substrate A4 composes against. The new-AC detection pattern (manifest `created_at` vs sentinel `created_at`) is itself a reusable primitive future amendments can compose on.

**Sealed-component fence (D3 governs):**

- `hands-off-lifecycle` — single sealed component. New PreToolUse hook script (`tdd_guard.py`); new helper library (`_gate_helpers.py`); A2's `objective_binding_gate.py` refactored to consume helpers; settings-merge surface extended to multi-contributor; first-run-helper wiring extended; tests for AC.TDG.1..AC.TDG.S + AC.TDG.helper-extraction-equivalence (if D-A3.7 approved).
- `objective-tracker` — consumer-only. A3 calls A1's public read API (`manifest_rows_for_ac` returning rows that include `created_at`); no schema or runtime change.
- `loam-mode` — consumer-only via the workspace-mode bit (already a `corpus_load_sentinel.workspace_mode()` thin wrapper from A1).

**Single sealed component touched: `hands-off-lifecycle`.** Symmetric with A2's shape.

**ODD §2.5 reverse direction.** Every code path, branch, dependency, and test in A3's diff traces back to a named AC under §4. No silent branches; no defensive `if`s without backing AC. The helper-library extraction's regression coverage is the AC.TDG.8 invariant (or the existing AC.OBG.x suite, depending on D-A3.7 ruling).

---

## 3. Three-lens analysis

### Lens 1 — Claude leverage

*Required research question: what Claude capability does this lean on or extend?*

A3 leans on the same three Claude Code primitives A2 leaned on:

- **`PreToolUse` hook event.** Claude-native; documented; subagent-inheriting. A3 is a SECOND entry under the same event in the merged settings.json. Claude Code admits multiple matcher entries for one event; A2 evaluates first, A3 second.
- **`Edit`, `Write`, `MultiEdit` tool matchers.** Native primitives. A3 fires after A2 admits the path.
- **`hookSpecificOutput.permissionDecision: "deny"` + `permissionDecisionReason`.** Native deny mechanism; the reason text appears to the model as `additionalContext`.

The substrate (manifest table with `created_at`, sentinel with `created_at`, helper library) extends Claude-adjacent infrastructure A1 + A2 shipped. A3 is a pure consumer of that substrate at the Claude hook layer.

The asymmetric finding from the locked research §7.1 — *"Claude Code's hook surface IS the structural-enforcement surface"* — applies recursively: A3 is the second concrete gate; the same hook surface carries A4 next. A3's helper-library extraction makes the pattern explicitly composable for future gate amendments.

### Lens 2 — Harness + primary-persona value

*Primary-persona test: does this reduce the translation burden between the user's natural-language intent and AI-effective execution?*

**Yes — direct, load-bearing reduction.** The persona's translation toolkit currently includes "every new AC introduced in an amendment must have its test authored first per ODD §4." A3 makes this binding structural — the persona dispatches a build; the build's first step (per A2's already-established discipline) is registering manifest rows; A3 then refuses source edits for new ACs without backing tests. The persona's mental model collapses from "remember to enforce ODD §4 re-extension" to "ODD §4 enforces itself at the edit boundary." The methodology is preserved for AUTHORING; enforcement is no longer the persona's concern.

*Harness test: does this add to the toolkit the primary persona can draw from?*

**Yes — three new toolkit primitives (plus the helper-library extraction).**

1. **The `tdd_guard.py` PreToolUse-gate-script pattern.** Second of its shape (A2 was the first); the pattern is now established for A4.
2. **The "new AC in this diff" detection primitive.** Consuming `manifest_rows_for_ac` + sentinel `created_at` — a reusable check future gate amendments can adopt.
3. **The shared `_gate_helpers.py` library.** Extracted now for A3's reuse and A4's adoption. Consolidates path canonicalisation, mode-bit query, sentinel reader, tracker-open, carve-out detection, audit-log appender.
4. **The "test-pinned-to-AC" filename-pattern convention promoted to structural.** Pos-v2's existing test-naming convention (`test_AC_<id>_*.py` containing `def test_AC_<id>_*`) becomes mechanically enforced; the convention is no longer reviewer-enforced.

Both Lens 2 tests pass. **→ AC.PO.1 + AC.PO.2.**

### Lens 3 — ODD authoring

A3 is structurally shaped, not advisory. The gate is deterministic — same path + same sentinel + same manifest = same decision, every fire. The refusal is structured (`permissionDecision: "deny"`), the diagnostic is named (the `permissionDecisionReason`), the audit is captured (the NDJSON log). Every AC below is outcome-shaped (no "the implementation will use X" language). Method (decision-tree shape, exact AC normalisation rule, regex-vs-AST for matching-function detection, helper-module symbol layout, hook-chain ordering specifics) is the builder's call and lives in the builder plan.

ODD §5.1.1 (relocate-vs-eliminate test): A3 ELIMINATES the "code-for-new-AC-without-backing-test" failure class. A future code change cannot re-introduce the failure without active discipline (i.e. without amending or removing A3 itself); the gate's refusal shape is structural, not an `if/else` a maintainer can forget to update.

ODD §4 alignment: A3 enforces the re-extension flow's "test first, then source" sequencing structurally. The methodology's recommended discipline becomes the gate's required discipline.

---

## 4. Acceptance criteria

A3's outcome is the gate's observable behaviour at every PreToolUse Edit/Write/MultiEdit fire after A2's gate has admitted the path. Eight ACs cover the seven behaviours plus the seal-diff invariant. An optional ninth AC covers the helper-library extraction equivalence (added if D-A3.7 is approved).

- **AC.TDG.1 — Refuse Edit on sealed-component non-test source for a NEW AC with no matching test file (DEV MODE).** Given workspace-mode = `dev-mode`, given A2's gate admitted the path, given `tool_input.file_path` is under `framework/<X>/` but NOT under `framework/<X>/tests/`, given the active-scope sentinel binds `(X, Y)`, given at least one manifest row for `(X, Y)` has `created_at` strictly after the sentinel's `created_at` (the AC is "new in this diff"), given no file matching `framework/<X>/tests/test_AC_<Y-normalised>_*.py` exists: hook returns `hookSpecificOutput.permissionDecision: "deny"` with a `permissionDecisionReason` that names (a) the source path, (b) the new AC `(X, Y)`, (c) the expected test path glob, (d) at least one repair direction (author the test first, retry the source edit; halt-and-surface if the AC is wrong).

- **AC.TDG.2 — Refuse Edit when test file exists but no matching function inside.** Given a file matching `framework/<X>/tests/test_AC_<Y-normalised>_*.py` exists, given no function whose name starts with `test_AC_<Y-normalised>_` is defined in any such file: hook returns `permissionDecision: "deny"` with a reason that names the file path(s) found, the expected function-name pattern, and at least one repair direction (rename the function, add a function with the matching pattern).

- **AC.TDG.3 — Allow Edit when path is a test path.** Given `tool_input.file_path` matches `framework/<comp>/tests/**`: hook returns no `permissionDecision` (default-allow). Test-tree edits bypass A3 regardless of new-AC state — the test file IS the satisfaction surface, gating its own creation creates a chicken-and-egg.

- **AC.TDG.4 — Allow Edit when AC is NOT new (existing AC, in-AC modification).** Given the sentinel binds `(X, Y)`, given every manifest row for `(X, Y)` has `created_at` strictly BEFORE the sentinel's `created_at` (no row was registered after the sentinel was authored): hook returns no `permissionDecision`. Per D2 lock, A3 does not gate in-AC modifications.

- **AC.TDG.5 — Allow Edit when new AC has matching test (file + function).** Given the sentinel binds `(X, Y)`, given at least one `(X, Y)` manifest row's `created_at` is after the sentinel's, given a file matching `framework/<X>/tests/test_AC_<Y-normalised>_*.py` exists AND contains at least one function whose name starts with `test_AC_<Y-normalised>_`: hook returns no `permissionDecision`.

- **AC.TDG.6 — Gate is a no-op when workspace-mode is `normal-use`.** Given `workspace_mode(workspace_root) == "normal-use"`: hook returns no `permissionDecision` and does not consult the active-scope sentinel, manifest table, or filesystem. The hook's wall-clock cost in this branch is bounded by the mode-bit read alone (sub-10ms, matches A2's AC.OBG.6 envelope).

- **AC.TDG.7 — Every gate fire is observable through a deterministic audit surface.** Each PreToolUse fire (allow + deny + no-op) is recorded in a workspace-local audit surface that a downstream consumer can read deterministically without re-running the gate. The recorded data is sufficient to reconstruct: when the fire happened, the tool/path/mode observed, the sentinel state, the bound `(component, ac_id)` pairs, the new-vs-existing classification per binding, the test-file/test-function presence per new AC, the gate's decision, and (on deny) the same reason text the model received. The surface is append-only in A3; concurrent fires across processes do not corrupt each other (atomicity guarantee). Path, format, and exact field names are method per ODD §7.4 — the builder confirms the shape composes with the FIDRAFT-143 dispatch-staleness consumer.

- **AC.TDG.S — Seal-diff confined to fence.** A3's seal-diff window contains only edits under `framework/hands-off-lifecycle/{hooks,tests,seals}/` and the universal-paths admissions (`docs/plans/`, `CLAUDE.md`, `docs/odd-methodology.md`, `docs/odd-in-pos.md`, `docs/FUTURE_IDEAS.md`, `docs/FUTURE_IDEAS_DRAFT.md`). Per-invariant frozen-both-endpoints BASELINE pattern (per `docs/odd-in-pos.md` §10.3) for the A3 invariant test.

**Optional, contingent on D-A3.7 ruling:**

- **AC.TDG.8 — Helper-library extraction preserves A2's behaviour byte-for-byte.** Given A2's existing AC.OBG.1..AC.OBG.7 test suite + the AC.OBG.S frozen-both-endpoints invariant: post-A3-extraction, all 8+ A2 tests pass with byte-for-byte identical assertions; A2's `objective_binding_gate.py` consumes symbols from `_gate_helpers.py`; behaviour-equivalent at the hook-envelope-in / JSON-out boundary on a parametrised harness covering A2's 8 deny/allow paths. (This AC is the regression coverage for the extraction; equivalent guarantees can be expressed without an additional AC if the existing AC.OBG.x test suite is structurally re-run as part of A3's seal sweep — D-A3.7 names which shape.)

### Behaviour-count check (forward)

| # | Declared behaviour in §1 / §4 | AC |
|---|---|---|
| 1 | Refuse Edit on non-test source for NEW AC with no matching test file | AC.TDG.1 |
| 2 | Refuse Edit when test file exists but no matching function | AC.TDG.2 |
| 3 | Allow Edit when path is a test path (chicken-and-egg avoidance) | AC.TDG.3 |
| 4 | Allow Edit when AC is NOT new (existing-AC modification) | AC.TDG.4 |
| 5 | Allow Edit when new AC has matching test | AC.TDG.5 |
| 6 | No-op in NORMAL USE | AC.TDG.6 |
| 7 | Audit log writes deterministic NDJSON per fire | AC.TDG.7 |
| 8 | Seal-diff confinement | AC.TDG.S |
| (9) | Helper-library extraction preserves A2's behaviour | AC.TDG.8 (contingent on D-A3.7) |

**Behaviours = 8 (or 9 with D-A3.7), ACs = 8 (or 9).** Match.

### Behaviour-count check (reverse)

The reverse direction (every code path / branch / dep / test in the diff traces back to AC.TDG.x) is exercised in the builder plan's §2.5 reverse-direction audit at build time. This plan asserts the audit will run; the builder records its outcome. The helper-library refactor's reverse-direction audit is the most delicate — every line moved into `_gate_helpers.py` must trace to either an AC.TDG.x or an AC.OBG.x.

---

## 5. Hard constraints

1. **Dependency fence.** Source-edit scope: `framework/hands-off-lifecycle/{hooks,tests,seals}/`. Any edit to other sealed components is a halt trigger. Non-fence consumer reads (`objective-tracker.runtime.ObjectiveTracker.manifest_rows_for_ac`, `loam-mode` via `corpus_load_sentinel.workspace_mode()`) are READ-ONLY; if a write or schema extension surfaces necessary, that's an A3.1 corrective on A1's substrate.
2. **A2's seal-diff is honoured.** The helper-library refactor edits A2's `objective_binding_gate.py` in place. A2's AC.OBG.1..AC.OBG.7 tests must remain green byte-for-byte after the refactor; AC.OBG.S frozen-both-endpoints invariant is untouched (its endpoints close before A3 begins). This is the regression contract for the refactor — A3 must not relax A2's behaviour.
3. **Reversibility.** Fully reversible. The new gate is additive (a new hook script, a new settings.json entry, a new audit log file); removing the entry restores prior behaviour. The helper-library extraction is also reversible — A2's gate could be reverted to inlined helpers if needed.
4. **Budget.** PreToolUse hook < 100ms p95 (target < 50ms — fires per-edit in addition to A2). NORMAL USE branch < 10ms (mode-bit-read only). Audit-log append microseconds-scale. Manifest query < 5ms (single SQLite read). Filesystem scan via `os.scandir` on `framework/<comp>/tests/` < 10ms for typical-sized test directories. Cumulative A2 + A3 hook chain budget < 200ms p95 — stays under the per-edit envelope.
5. **Fail-closed direction (DEV MODE).** Missing test for new AC → DENY. Every refusal carries a structured `permissionDecisionReason` naming the failure class + at least one repair path. Refusal is observable to the model and to the operator (audit log).
6. **Fail-open direction (NORMAL USE).** Mode = `normal-use` → ALLOW unconditionally. The gate must not silently fire in derived workspaces.
7. **Fail-closed-to-permissive at substrate-import boundary.** Tracker unreachable / sentinel reader fails → fall through to allow. Mirrors A2's R7 mitigation. The audit log records the failure.
8. **No `--amend`.** Corrective commits only (per `feedback_no_amend_in_agent_dispatches`).
9. **ODD §2.5.** Every code path, branch, dependency, and test in A3's diff traces back to AC.TDG.1–AC.TDG.S (and AC.TDG.8 if D-A3.7 approved). The builder runs the §2.5 reverse-direction audit before seal — including the helper-library refactor's lines.
10. **No new top-level objective.** A1 + A2 already satisfied spec line 134–135; A3's audit log feeds the same lint surface. No spec amendment.
11. **No method prescription.** This plan-doc names outcomes; the builder plan picks: hook script structure, decision-tree shape, exact AC normalisation rule, regex-vs-AST for matching-function detection, helper-module symbol layout, settings-merge multi-contributor extension shape, hook-chain ordering specifics in settings.json, JSON keys for the deny reason and audit log.
12. **A1 + A2 substrate is sealed.** A3 may not propose edits to A1's manifest schema, sentinel JSON shape, mode-bit interface, A1's reader/writer contracts, A2's evaluate function signatures, or A2's audit-log shape. If during A3 build a substrate change becomes necessary, halt — it's an A1.1 / A2.1 corrective amendment, not folded into A3.
13. **Backwards-compat.** Existing PreToolUse hooks authored by users (and A2's pos-v2-owned entry) must be preserved. The multi-contributor merge surface extends `merge_pre_tool_use` without breaking A2's single-contributor invariant — the same function admits two pos-v2 entries OR one + user OR two + user.
14. **No agent-side discipline-as-code.** A3 must not require build agents or the persona to "remember to call the gate" — the gate IS the discipline. Failure-mode (missing test for new AC) is denied at edit time; the dispatcher / build-agent learns from the deny diagnostic.
15. **Sealed-component dispatch must explicitly name `pos-amend apply`** as the bookkeeping mechanism for the seal-diff window per `feedback_dispatch_explicit_pos_amend_apply`.
16. **Build-time AC-row registration is a hard prereq (inherited from A2).** The build agent's first action (before the first source edit) is registering manifest rows for AC.TDG.1–AC.TDG.S via `tracker.register_source_binding(component="hands-off-lifecycle", ac_id="AC.TDG.x", source_path_glob="framework/hands-off-lifecycle/...")`. Without this step, A2's gate denies the first edit (AC.OBG.2). Bootstrap order: (a) register manifest rows; (b) author A3's tests first (test_AC_TDG_1_*.py through test_AC_TDG_S_*.py); (c) THEN author A3's source files. This bootstrap order satisfies BOTH A2 (rows registered → A2 admits) AND A3 (tests authored before source for new ACs → A3 admits).
17. **Audit-log path follows D-migration D.2 convention.** `<workspace>/workspace/.pos/tdd-guard.log` (NOT `<workspace>/.pos/`). Builder confirms by inspecting `framework/workspace-bootstrap/src/workspace_bootstrap/workspace_paths.py` at build time — the canonical `WORKSPACE_STATE_SUBDIR` = `"workspace"`.
18. **Helper-library refactor is in scope for A3, not a future amendment.** The locked research §7.1 + A2's research §9.3 + A3's research §6.1 unanimously recommend extracting helpers when the second gate ships. Deferring the extraction is method creep (each gate re-inlines; cleanup amendment later). A3 is the right window.

---

## 6. D-decisions for this plan (record + rationale)

The five programme-level D-decisions are LOCKED 2026-04-26 (see header). This section records the A3-level design choices that follow from the research artefact + the programme locks. **Owner is asked to rule on D-A3.1, D-A3.2, D-A3.3, D-A3.4, D-A3.7, D-A3.8 below; D-A3.5 + D-A3.6 are locked by programme D2 + D4 respectively; D-A3.9 + D-A3.10 are method per ODD §7.4.** Decisions for owner are summarised in §9 (read this first).

### D-A3.1 — Firing layer

**Recommendation: Candidate A — `PreToolUse` matcher `Edit|Write|MultiEdit`** (per research §3.6).

Mirrors A2 exactly. The `PreToolUse` hook event admits multiple matcher entries; A3 runs after A2 in the hook chain. Subagent-inheritance covers every dispatched build agent.

Alternatives rejected in research §3:
- B (commit-time hook) — too late.
- C (Stop hook) — misses per-edit granularity.
- D (Stop + PreCompact) — same as C plus more complexity.
- E (pos-amend seal invariant) — way too late.

### D-A3.2 — Refusal mechanism

**Recommendation: Candidate α — `permissionDecision: "deny"` + structured `permissionDecisionReason`** (mirrors A2).

Native Claude Code surface. Reason text is structured-natural-language: opens with the failure class, names the path + AC + expected test, names the repair.

### D-A3.3 — Pinning mechanism (test-to-AC binding)

**Recommendation: Candidate α — filename + function-name pinning** (per research §1.1).

`tests/test_AC_<Y-normalised>_*.py` containing `def test_AC_<Y-normalised>_*`. The convention is already universal in pos-v2 (objective-tracker, hands-off-lifecycle, orchestrator, workspace-bootstrap); making it structural is a small step.

Alternatives rejected:
- β (manifest column `test_path_glob`) — would require A1.1 substrate amendment; not necessary when convention is already established.
- γ (plan-doc §4 row count change) — too brittle; plan-doc parsing fails the elimination-over-relocation test.

### D-A3.4 — "New AC in this diff" detection

**Recommendation: Candidate A — manifest-row `created_at` strictly after sentinel `created_at`** (per research §2.5).

A binding `(X, Y)` is "new in this diff" when at least one manifest row for `(X, Y)` has `created_at` strictly after the sentinel's `created_at`. Cheapest correct shape; substrate already in place; handles both canonical cases (fresh AC, re-extension mid-build).

Alternatives rejected:
- B (existence check at sentinel-author time) — substrate creep.
- C (plan-doc parsing) — too brittle.
- D (sentinel-binding diff vs prior-sentinel) — substrate creep.

### D-A3.5 — Direction (impl-without-test only, per D2)

**LOCKED by programme D2 — A3 enforces direction A only (impl-without-test refusal).** Direction B (test-without-impl refusal) is out of A3 scope (research §4.4). Test-without-impl is a separate failure class candidate for a future amendment (FIDRAFT capture).

### D-A3.6 — DEV-MODE / UNIVERSAL split

**LOCKED by programme D4 — A3 is entirely DEV-MODE-only.** Three sub-cases evaluated and rejected as universal candidates (research §5.2). No A3 sub-cases warrant universal application.

### D-A3.7 — Helper-library extraction

**Recommendation: extract `_gate_helpers.py` as part of A3's seal-diff window, with A2's `objective_binding_gate.py` refactored in-place to consume it.**

Rationale (research §6.1):
- A2's builder plan explicitly named "premature extraction" as the rationale for inlining (D-build.2). A3 is the second gate; the rationale flips.
- A4 will be the third gate; extracting NOW saves repeated inlining + cleanup work.
- The refactor is reversible; A2's existing tests are the regression contract (AC.TDG.8 if added; otherwise A2's existing test suite is the de-facto contract).

**Alternative (rejected):** keep A2 inlined; A3 has its own copy of helpers. This duplicates code across two gates and stages the cleanup as a third amendment. Method creep.

### D-A3.8 — Hook-chain ordering + decision-chain duplication

**Recommendation: A3 runs AFTER A2 in settings.json; A3 runs the FULL decision chain (defensive duplication of mode + carve-out + sentinel-presence checks).**

Rationale (research §6.2):
- A2's deny short-circuits A3 (Claude Code stops the chain on the first deny).
- A3 inheriting A2's correctness for free is the optimistic shape, but defensive duplication is cheap (sub-millisecond per check) and:
  - protects against hook-chain ordering changes;
  - protects against A2 being removed in a future amendment;
  - keeps each gate self-contained (architecture-creep-watch recommendation).

**Alternative:** A3 trusts A2 and only runs the test-existence check. Marginally cheaper but couples the two gates.

### D-A3.9 — AC normalisation rule (method per ODD §7.4)

**Default:** dot → underscore + uppercase + drop leading `AC.` if present. So `AC.OBG.1` → `OBG_1`, `AC.SE.S` → `SE_S`, `AC.A8.A` → `A8_A`. The test-file glob becomes `test_AC_<normalised>_*.py`; the function-name prefix becomes `test_AC_<normalised>_`.

The builder confirms by reading existing test names at build start; if conventions diverge across components (e.g. `test_AC36_3_*` without underscore between `AC` and component prefix), the builder records the deterministic rule covering all observed cases in §14.

### D-A3.10 — Audit log shape (method per ODD §7.4)

**Default:** NDJSON at `<workspace>/workspace/.pos/tdd-guard.log` mirroring A2's `objective-binding-gate.log` pattern. One JSON object per line. Atomic-append via POSIX `O_APPEND`. Append-only in A3; rotation deferred to a future amendment.

The builder may refine the log path / format if a sibling amendment standardises a different shape, OR if the shared `_gate_helpers.py` audit-log appender (per D-A3.7) emerges with a different signature.

---

## 7. Out of scope (explicit per ODD §2.5)

The four-amendment programme decomposition (research §6) names A4 explicitly; A3 declares it as a future amendment. Items below are explicitly NOT in A3's surface.

- **A4 — `bash-and-agent-context-guards`.** The Bash-tool guards (`git commit --amend` blocker, secret-file commit blocker, `pos-amend apply --dry-run` exit-0 commit gate) and Agent-tool guards (WD-verification, dispatch-staleness check). A3 does not gate Bash; A3 does not gate Agent dispatches. A4 inherits A3's helper library (`_gate_helpers.py`).
- **Direction B — test-without-implementation refusal.** Out of A3 scope per programme D2 lock (research §4). Surfaced as a future amendment candidate; FIDRAFT capture appropriate.
- **Test quality validation.** A3 verifies test-file existence + matching-function existence. Test body correctness, assertion strength, fixture quality are reviewer-shaped (ODD §8.2.10) — out of A3.
- **Dispatcher-side test-author-on-dispatch wrapper.** Analogous to A2's "active-scope sentinel auto-author at dispatch time" candidate — a future amendment that wraps the Agent dispatch tool to author the test stubs at scope-creation time. Composes with amendment #52's existing `dispatch_with_scope`. A3 ships the gate; auto-stub-authoring is the dispatcher's job.
- **Audit-log rotation.** A3 ships append-only NDJSON. Rotation is a future amendment.
- **Cross-amendment manifest queries** — historical "show me every Edit allowed by A3 in the last 30 days" surface. A3 ships the per-fire log; reporting is downstream.
- **Test-file deletion detection.** If a builder deletes a test for an existing AC, A3 does not catch it (A3 fires on Edit/Write/MultiEdit; deletion goes through different tools). A test-deletion gate is out of A3 scope.
- **Persona-side surfacing of A3 deny diagnostics.** The model receives `permissionDecisionReason` natively; the persona may surface deny in user-readable narration. A3 does not include persona-prompt edits.
- **Composition with FIDRAFT-130 corpus-inlining.** A3's diagnostic mentions corpus state when missing (mirrors A2) but does not refuse for missing corpus.
- **Composition with FIDRAFT-136 main-session-write-prevention.** Distinct decision logic; separate amendment. May share `_gate_helpers.py` with A3 if both ship.
- **Audit-log consumers** (FIDRAFT-143 dispatch-staleness). A3 ships the log; consumers are downstream.
- **Helper-library expansion beyond what A3 needs.** D-A3.7 extracts the helpers A3 + A2 share. Adding helpers A4 might want but A3 doesn't is out of A3 scope (premature).
- **Settings.json migration on existing workspaces.** A3's first-run-helper wires the new PreToolUse hook into freshly-bootstrapped workspaces. Existing workspaces' settings.json files may need a re-merge pass; the existing `merge_user_prompt_submit` / `merge_session_start` precedent handles this for re-bootstrap (the amendment #45 + #46 + A2 pattern). The builder confirms the re-merge is idempotent.

---

## 8. Halt triggers

Halt and surface (do not silently extend) when any of the following fires:

1. **A1 substrate gap.** If A3's design surfaces a missing field A1 doesn't provide → halt; A1.1 corrective. Specifically: if `manifest_rows_for_ac` doesn't return rows with `created_at` directly readable; if the active-scope sentinel reader doesn't expose `created_at`; if `workspace_mode` doesn't expose the two-string contract A3 expects. Verification at build start by reading A1 readers + sample query output.
2. **A2 helper incompatibility.** If A2's `objective_binding_gate.py` cannot be refactored to consume `_gate_helpers.py` without breaking AC.OBG.x tests → halt. Specifically: if A2's helpers depend on module-private state that doesn't survive extraction; if the lazy-import pattern creates circular import risks; if symbol signatures diverge between what A2 needs and what A3 needs. Verification: dry-run-extract before authoring A3's gate.
3. **A2 manifest API insufficient.** If `manifest_rows_for_ac` returns rows in a shape that doesn't include `created_at` directly accessible (e.g. dict missing the field, Row object hides it) → halt. Verification: read `objective-tracker/src/store.py::list_manifest_rows_for_ac` at build start and confirm the dict-shape includes `created_at`.
4. **MultiEdit semantics changed.** A2's empirical answer (Q1 in A2 builder plan §5: MultiEdit is single-path, no batch-of-paths) inherited by A3. If verification reveals the surface has changed since A2 sealed, halt.
5. **Existing PreToolUse hook collision.** Settings.json may now have two pos-v2-owned PreToolUse entries (A2's gate + A3's gate) plus user-authored entries. A2's `merge_pre_tool_use` is single-contributor; if extending it to multi-contributor breaks A2's existing single-contributor tests, halt and signal.
6. **Surrounding-code ODD §2.5 violation.** The hook script's adjacent modules (`first_run_settings.py`, `first_run_helper.py`) may contain pre-existing §2.5 violations the build's verification pass uncovers — particularly during the helper-library extraction's scope-walk. Halt-and-surface per the dispatch's explicit ODD-violation clause.
7. **Outcome-resistant AC.** If during builder plan authoring some A3 behaviour resists outcome-shaping (a method prescription is the only natural form), halt and signal.
8. **Architecture creep — multi-tenant gate framework.** The helper-extraction question may surface a deeper "should the gates share a single entry-point dispatcher" question. The locked programme research + A2 research + A3 research all recommend per-amendment hooks with shared helpers; if the builder strongly disagrees, halt-and-signal rather than silently consolidating.
9. **AC normalisation ambiguity.** If existing pos-v2 test names follow inconsistent conventions (e.g. some `test_AC_OBG_1`, some `test_OBG_1`, some `test_A20_*` without `AC` prefix), the normalisation rule may not have a deterministic canonical form. Verification at build start: scan `framework/*/tests/test_AC*.py` and `framework/*/tests/test_A[0-9]*.py` filenames + sample function names; if conventions diverge in a way that makes a single normalisation rule miss legitimate tests, surface to owner. Most likely outcome: the rule covers `test_AC_*` with the dotted-AC-id convention; pre-`AC` legacy names (e.g. `test_A20_*`) are rare and out of A3's scope (those tests were authored before the convention crystallised).
10. **Substrate-fence breach.** Per constraint 1: any source-edit need outside `framework/hands-off-lifecycle/{hooks,tests,seals}/` halts.
11. **Self-bootstrap fails.** Per hard constraint 16: the build agent's bootstrap order (manifest rows first, A3 tests second, A3 source third) must be followed. If A2 denies the first row registration (chicken-and-egg from a wrong ordering), or A3 denies its own test files (test files for A3's ACs must exist on disk before the test files themselves are edited — meaning the build agent authors them via Write rather than Edit, which is fine because Write of a new file passes A3's chicken-and-egg avoidance via the test-tree carve-out). Verification: trace the bootstrap sequence on paper before the dispatch lands.
12. **AC.OBG.x regression in A3's diff.** The helper-library refactor in `objective_binding_gate.py` could subtly change A2's behaviour. Halt if any AC.OBG.x test fails post-refactor; this is the regression contract for D-A3.7.
13. **Dispatch staleness.** The dispatch-staleness pre-flight (already named at the top of this plan and its dispatch brief) catches A3-already-shipped scenarios. If §14 below contains commit SHAs at dispatch time, halt.

---

## 9. Decisions for owner (only genuinely uncertain)

The five programme-level D-decisions are LOCKED 2026-04-26 (see header) and not surfaced here. **Six decisions are surfaced for owner ruling**, with recommendation per `feedback_summarize_and_surface_decisions`:

### D-A3.1 — Firing layer

- **Question:** PreToolUse Edit|Write|MultiEdit hook (Candidate A) vs alternatives B/C/D/E.
- **Recommendation:** **Candidate A**. Mirrors A2; native Claude primitive; per-edit granularity; subagent-inheriting; symmetric with A4. (Research §3.6.)
- **Alternatives:** B (commit-time) too late; C/D (Stop / Stop+PreCompact) misses per-edit granularity; E (pos-amend seal) way too late.
- **Caveat:** if owner picks anything other than A, every AC below changes shape.

### D-A3.2 — Refusal mechanism

- **Question:** `permissionDecision: deny` + structured reason (Candidate α) vs warning-only.
- **Recommendation:** **Candidate α**. Hard refusal; structured reason; native surface. Mirrors A2's lock.
- **Why:** warning-only is advisory in structural clothing; fails ODD §5.1.1.

### D-A3.3 — Pinning mechanism

- **Question:** filename + function-name pinning (α) vs manifest-column extension (β) vs plan-doc parsing (γ).
- **Recommendation:** **Candidate α** — filename + function-name pinning (`tests/test_AC_<normalised>_*.py` containing `def test_AC_<normalised>_*`).
- **Why:** the convention is already universal in pos-v2; making it structural is a small step. β requires A1.1 substrate change (forbidden by A1's constraint 9 unless explicit corrective). γ is too brittle.

### D-A3.4 — "New AC in this diff" detection

- **Question:** manifest-row `created_at` comparison (A) vs existence check (B) vs plan-doc parsing (C) vs sentinel-binding diff (D).
- **Recommendation:** **Candidate A** — manifest-row `created_at` strictly after sentinel `created_at`.
- **Why:** substrate already in place (A1's manifest table has `created_at`; A1's sentinel has `created_at`). Cheapest correct shape; handles canonical cases.
- **Alternatives:** B requires snapshot-at-sentinel-time substrate (creep); C is brittle; D requires journal of past sentinels (creep).

### D-A3.7 — Helper-library extraction

- **Question:** extract `_gate_helpers.py` as part of A3 (refactor A2 to consume) vs keep A2 inlined and duplicate helpers in A3 vs defer extraction to a third amendment.
- **Recommendation:** **extract NOW** (as part of A3's seal-diff window).
- **Why:** A2's "premature extraction" rationale flips at the second gate. A4 will benefit. Refactor is reversible; A2's AC.OBG.x test suite is the regression contract.
- **Alternatives:** duplicate-then-clean-up (method creep); defer (more method creep). The extraction is in scope for A3 per hard constraint 18.
- **Adds AC.TDG.8** if approved (regression-equivalence guarantee for A2's behaviour). If rejected, A3 ships with duplicated helpers; AC.TDG.8 is dropped; the refactor moves to a future amendment.

### D-A3.8 — Hook-chain ordering + decision-chain duplication

- **Question:** A3 runs the FULL decision chain (defensive duplication of A2's mode + carve-out + sentinel-presence checks) vs A3 trusts A2 and runs only the test-existence check.
- **Recommendation:** **full decision chain** (defensive duplication).
- **Why:** sub-millisecond cost; protects against hook-chain ordering changes, A2 removal, asymmetric carve-out lists. Architecture-creep-watch recommendation.
- **Alternative:** trust-A2 is marginally cheaper but couples the two gates.

### Surfaced for owner ruling: 6 (D-A3.1, D-A3.2, D-A3.3, D-A3.4, D-A3.7, D-A3.8).

(D-A3.5 locked by programme D2. D-A3.6 locked by programme D4. D-A3.9 + D-A3.10 are method per ODD §7.4 — builder defaults are the dot-to-underscore normalisation rule and NDJSON at `<workspace>/workspace/.pos/tdd-guard.log`; a sibling amendment may relocate.)

---

## 10. Risks

- **R1 — Helper-library extraction regression.** Refactoring A2's `objective_binding_gate.py` to consume `_gate_helpers.py` could subtly change A2's behaviour. Mitigation: A2's existing AC.OBG.x test suite (8+ tests) runs as part of A3's pre-seal sweep; AC.TDG.8 (if D-A3.7 approved) is the explicit regression coverage. AC.OBG.S frozen-both-endpoints invariant is untouched (its endpoints close before A3 begins).
- **R2 — Multi-contributor `merge_pre_tool_use` regression.** Extending A2's single-contributor merge to multi-contributor could break A2's existing settings-merge tests. Mitigation: A2's `test_AC_OBG_settings_merge.py` runs as part of A3's pre-seal sweep; the multi-contributor extension preserves single-contributor behaviour as a special case.
- **R3 — `created_at` wall-clock skew.** A3's "new AC in this diff" detection relies on `created_at` comparison. Same-machine skew is sub-second; ISO-8601 second-resolution timestamps from A1's `_now_iso` collapse the difference. Risk is essentially zero; mitigation is documenting the contract in §14.
- **R4 — Bootstrap order chicken-and-egg.** A3's own build must satisfy A3's own gate. The bootstrap order (rows → tests → source) is the canonical resolution; if a build agent reverses it, A2 (rows-missing) or A3 (tests-missing) denies the first source edit. Mitigation: hard constraint 16 names the order explicitly; the dispatch brief reproduces it.
- **R5 — Hook latency on edit-bursts.** A build that makes 100 edits pays the A2 + A3 chain cost 100×. Target cumulative < 200ms means burst overhead < 20s — acceptable. Mitigation: AC.TDG.6's mode-bit short-circuit is the cheap path; non-DEV-MODE workspaces pay only mode-bit-read cost.
- **R6 — AC normalisation rule misfire.** If A3's normalisation rule doesn't match a legitimate AC's test naming, the gate denies a build that should pass. Mitigation: D-A3.9 names the rule; halt-trigger 9 surfaces convention divergence at build start; the diagnostic names the expected glob explicitly so the operator can rename if needed.
- **R7 — Substrate-unreachable false-allow.** A3 falls through to allow when the tracker can't be opened (mirrors A2's R7). Acceptable for a workspace whose substrate is mid-bootstrap or environmentally broken — A2 also falls through, so A3 inherits the same fail-open envelope.
- **R8 — Path-canonicalisation bugs.** Same as A2's R8 — `tool_input.file_path` may be absolute, relative, or symlinked. Mitigation: A3 uses the same `_workspace_relative` helper as A2 (post-extraction, the shared helper from `_gate_helpers.py`).
- **R9 — Test-tree carve-out vs. test-binding-glob overlap.** A path that is BOTH a test-tree path (per AC.TDG.3) AND admitted by a binding-glob is fine — A3 short-circuits on test-tree FIRST, so the gate is silent. The carve-out check fires before the new-AC check; the order is method per ODD §7.4 but the order is documented in §14.
- **R10 — D-A3.7 rejected; helpers duplicated.** If owner rules against the helper extraction, A3 ships with its own private copy of helpers. Future cleanup is a third amendment. Cost: code duplication + cleanup amendment later.

---

## 11. Bookkeeping

- **Plan-doc:** this file at `docs/plans/structural-enforcement-a3-tdd-guard.md`.
- **Research artefact:** `docs/plans/research/structural-enforcement-a3-tdd-guard-research.md` (this dispatch).
- **Programme research:** `docs/plans/research/structural-enforcement-of-critical-requirements-research.md` (locked 2026-04-26; governs).
- **A1 plan (sibling, sealed):** `docs/plans/structural-enforcement-a1-substrate.md`.
- **A2 plan (sibling, sealed):** `docs/plans/structural-enforcement-a2-objective-binding-gate.md`.
- **A2 builder plan (D-build choices A3 inherits + extends):** `docs/plans/structural-enforcement-a2-objective-binding-gate.builder-plan.md`.
- **Builder plan:** to be authored by the build agent post-owner-approval at `docs/plans/structural-enforcement-a3-tdd-guard.builder-plan.md`. Contains files-touched, symbol-level details, AC-to-test mapping, D-build choices (decision-tree shape, AC normalisation rule, helper-library symbol layout, multi-contributor merge shape, hook-chain ordering specifics), §2.5 reverse-direction audit, halt-trigger checks, pos-amend bookkeeping flow, helper-extraction equivalence verification.
- **Manifest:** authored alongside the builder plan at `docs/plans/structural-enforcement-a3-tdd-guard.manifest.yaml`. Single-component manifest (`hands-off-lifecycle`); `frozen_baseline: true` (H19 frozen since project-start). Universal-paths block as standard.
- **Pos-amend bookkeeping flow** (per `feedback_dispatch_explicit_pos_amend_apply`):
  1. Author manifest at `docs/plans/structural-enforcement-a3-tdd-guard.manifest.yaml` with the correct BASELINE (HEAD~1 of the upcoming amendment commit per the established #29/#34/.../#70 pattern).
  2. **Build-time manifest-row registration** (hard constraint 16): build agent's first action is `tracker.register_source_binding(component="hands-off-lifecycle", ac_id="AC.TDG.x", source_path_glob="...")` for each AC.TDG.1 through AC.TDG.S (and AC.TDG.8 if D-A3.7 approved). Without this, the agent's own first edit fails A2 (chicken-and-egg).
  3. **Test files authored before source files.** Per hard constraint 16: A3's tests (test_AC_TDG_1_*.py through test_AC_TDG_S_*.py + test_AC_TDG_8_*.py if applicable) are authored BEFORE the source files (`tdd_guard.py`, `_gate_helpers.py`, `objective_binding_gate.py` refactor edits). This satisfies BOTH A2's gate (rows-registered → admit) AND A3's own gate (tests-exist-before-source for new ACs → admit).
  4. Author all source edits + tests; commit as the amendment commit on branch `pos-v2`.
  5. `pos-amend apply --dry-run <manifest>` — must exit 0.
  6. `pos-amend apply <manifest>` — advances BASELINE literals + widens seal-diff bindings + writes SEAL_COMMIT sidecars.
  7. `pos-amend seal --plan-doc /Users/lukeivers/ivers-corp-pos-v2/docs/plans/structural-enforcement-a3-tdd-guard.builder-plan.md <manifest>` — runs the scoped test sweep, creates the seal commit, advances SEAL_COMMIT to the seal commit, appends builder-plan §SHA backfill follow-up commit.
  8. Verify: `pos-amend apply --dry-run <manifest>` exits 0 against post-seal HEAD.
- **Seal-diff window:** BASELINE = HEAD~1 of amendment commit (set in builder plan after dispatch). Allowed paths under the window: `framework/hands-off-lifecycle/{hooks,tests,seals}/` plus universal admissions.
- **Programme tracking:** A3 unblocks A4 (Bash/Agent-context). A4 inherits A3's `_gate_helpers.py` library + the multi-contributor `merge_pre_tool_use` mechanism. The four amendments serialise per `feedback_serialize_amendment_builds` (no parallel builds in canonical tree until pos-amend worktree-isolation is verified).
- **Test scope per amendment-dispatch CDC speedups:** narrow pre-amendment test scope to `framework/hands-off-lifecycle/tests/` (the only sealed component A3 touches; covers AC.OBG.x regression too) + `framework/objective-tracker/tests/` (consumer-only sanity check that A1 + A2's substrate API still works). Skip pre-seal full-suite rerun (sidecar-only edits between amendment and seal). Inline odd-methodology snippets into the dispatch brief.

---

## 12. References

- Locked programme research: `docs/plans/research/structural-enforcement-of-critical-requirements-research.md`
- A3 research (this dispatch): `docs/plans/research/structural-enforcement-a3-tdd-guard-research.md`
- A1 plan (sealed; substrate this builds on): `docs/plans/structural-enforcement-a1-substrate.md`
- A2 plan (sealed; sibling gate this composes with): `docs/plans/structural-enforcement-a2-objective-binding-gate.md`
- A2 builder plan (D-build choices A3 inherits + the helper-extraction-deferred rationale A3 reverses): `docs/plans/structural-enforcement-a2-objective-binding-gate.builder-plan.md`
- A1 substrate code (read-only inputs):
  - `framework/objective-tracker/src/store.py` (manifest-table CRUD; `objective_manifest` schema with `created_at`)
  - `framework/objective-tracker/src/runtime.py` (public API: `register_source_binding`, `manifest_rows_for_ac`, `manifest_rows_matching_source_path`)
  - `framework/hands-off-lifecycle/hooks/active_scope_sentinel.py` (reader contract; `ActiveScopeSentinel.created_at`)
  - `framework/hands-off-lifecycle/hooks/corpus_load_sentinel.py` (workspace-mode bit `workspace_mode(workspace_root) -> "dev-mode" | "normal-use"`)
- A2 gate code (helper-extraction source + composition surface):
  - `framework/hands-off-lifecycle/hooks/objective_binding_gate.py` (the candidate-extraction body — A3 refactors)
  - `framework/hands-off-lifecycle/hooks/first_run_settings.py` (`merge_pre_tool_use` — A3 extends to multi-contributor)
  - `framework/hands-off-lifecycle/hooks/first_run_helper.py` (composition wiring; A3 extends with second `_maybe_merge_pre_tool_use` call site)
- ODD methodology: `docs/odd-methodology.md` (§3.3 one-criterion-per-behaviour; §4 re-extension pattern + §4.2 canonical safety-layer A20 example; §5.1 structural-over-advisory; §5.1.1 relocate-vs-eliminate test; §7.4 flagged inferences; §8.1 authoring-time violations)
- ODD-in-pos: `docs/odd-in-pos.md` (§10.3 frozen-both-endpoints baseline pattern — for A3's seal-diff invariant)
- VALUE_PROPOSITION: `docs/VALUE_PROPOSITION.md` (AC.PO.1 + AC.PO.2 — A3's Lens 2 anchor)
- FUTURE_IDEAS: `docs/FUTURE_IDEAS.md` Idea 1 (programme), Idea 8 (structural context-load gate)
- FIDRAFT items A3 composes with: `docs/FUTURE_IDEAS_DRAFT.md` lines 130 (corpus-inlining), 136 (main-session-write-prevention), 143 (dispatch-staleness)
- Test-naming convention examples (the structural pinning A3 promotes):
  - `framework/objective-tracker/tests/test_AC_SE_6_objective_manifest_table.py`
  - `framework/hands-off-lifecycle/tests/test_AC_OBG_1_deny_missing_sentinel.py`
  - `framework/orchestrator/tests/test_AC_A8_A_activate_scope_with_spec.py`
  - `framework/workspace-bootstrap/tests/test_AC_E_1_classify_dev_when_dev_intent_yes.py`
- Claude Code hooks docs: https://code.claude.com/docs/en/hooks (PreToolUse decision-control surface; matchers admitting multiple entries; `permissionDecision`; `permissionDecisionReason`)
- Memory-bullet feedback rules carried forward:
  - `feedback_no_amend_in_agent_dispatches` — corrective commits only.
  - `feedback_dispatch_explicit_pos_amend_apply` — pos-amend named in dispatch.
  - `feedback_subagent_odd_violation_halt` — halt-and-surface explicit clause.
  - `feedback_amendment_dispatch_speedups` — narrow test scope, inline methodology.
  - `feedback_serialize_amendment_builds` — no parallel builds in canonical tree.
  - `feedback_summarize_and_surface_decisions` — §9 surface with recommendations.
  - `feedback_always_specify_wd_in_dispatches` — WD `/Users/lukeivers/ivers-corp-pos-v2/`.
  - `feedback_verify_post_amendment_state` — read post-A2 code (gate + helpers shape) before A3 design.

---

## 14. Method-decision register (post-build, builder-backfilled)

Method-level decisions made during the build land here at seal time per `pos-amend seal --plan-doc` convention. Empty at plan-author time.

### Commit SHAs

- Amendment commit: `a52e04a3b123c0849ec8c28f60e65781fd06f4fe` —
  `feat(structural-enforcement-a3): TDD-guard test-pinned-to-objective (PreToolUse Edit/Write/MultiEdit deny on new-AC source edit without backing test)`
- Seal commit: `ad7c50c36bdf6fbfcad9405af39cfebd1dc2ecd2` —
  `chore(seals): structural-enforcement A3 TDD-guard (PreToolUse Edit/Write/MultiEdit deny on new-AC source edit without backing test; helper-library extraction; A2 refactored to consume; multi-contributor PreToolUse merge; NDJSON audit log) — hands-off-lifecycle at a52e04a`
