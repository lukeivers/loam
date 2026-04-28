# Structural enforcement — A2: objective-binding gate (PreToolUse Edit/Write refusal-on-binding-miss)

**Status:** authored 2026-04-28 (plan-doc only; no code, no commits, no manifest yet).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Programme:** A2 of the four-amendment structural-enforcement programme (A1 substrate sealed at amendment #51; A2 first gate-that-refuses; A3 TDD-guard; A4 Bash/Agent-context guards). Programme research artefact: `docs/rebuild/plans/research/structural-enforcement-of-critical-requirements-research.md` (LOCKED 2026-04-26). A2 research: `docs/rebuild/plans/research/structural-enforcement-a2-objective-binding-gate-research.md` (this dispatch).
**Programme-level locks (per A1 plan header; carried forward, not re-litigated):** D1 dev-discipline carve-outs for `docs/`, `tools/`, `.scratch/`, `CLAUDE*.md`, `personas/`; D2 TDD-guard scoped to re-extension-with-new-AC (A3); D3 manifest extends `objective-tracker`; D4 secret/blast-radius gates universal, ODD-discipline gates DEV-MODE-only; D5 KEEP-ADVISORY list of 10.
**Pre-flight verification (mandatory; per `feedback_verify_dispatch_before_sending`):** pre-A2-build dispatch verifies `git log --grep="A2\|objective-binding"` returns no A2 amendment commit AND `ls docs/rebuild/plans/ | grep -i a2` returns nothing matching `structural-enforcement-a2-*`. Halt-and-surface if either does.

---

## 1. Summary / TLDR

A2 is the FIRST gate-that-refuses in the structural-enforcement programme. After A1's substrate (active-scope sentinel, objective-manifest table, workspace-mode bit) lands, A2 turns the substrate into a `PreToolUse` Edit/Write refusal: an attempted edit on a sealed-component source path that does not trace to a manifest-registered `(component, ac_id, source_path_glob)` row that the active-scope sentinel binds against is **denied** by Claude Code via `permissionDecision: "deny"`.

A2 ships:

1. **Single PreToolUse hook script.** `framework/hands-off-lifecycle/hooks/objective_binding_gate.py` — fires on `Edit|Write|MultiEdit` matchers. Stdlib + A1-substrate readers only; no third-party deps.
2. **Settings.json merge mechanism for PreToolUse.** Extension to `first_run_settings.py` mirroring the existing `merge_user_prompt_submit` pattern (amendment #46): `merge_pre_tool_use(settings, new_entry) -> ...` with the `_USER_AUTHORED` back-up convention so a workspace's prior PreToolUse hook is preserved.
3. **Hook composition wiring.** `first_run_helper.py` registers the gate at first-run-scaffold time, same way amendment #46's persona session-start emitter is registered.
4. **Audit log.** Every fire (allow + deny) appends one NDJSON line to `<workspace>/workspace/.pos/objective-binding-gate.log`. Append-only in A2; rotation deferred.

A2's behaviour:

- **DEV MODE workspaces, sealed-component source path edits.** Sentinel + manifest must trace; otherwise deny.
- **DEV MODE workspaces, dev-discipline carve-out paths.** Allow regardless (D1).
- **NORMAL USE workspaces.** Allow regardless (D4).

After A2 lands, every Edit/Write/MultiEdit issued in a DEV MODE pos-v2 workspace is structurally bound to a named AC OR explicitly carved-out as dev-discipline. The "every line of code traces to an AC" rule (ODD §2.5) becomes mechanically enforced at edit time — the failure class moves from "review catches it after the fact" to "the edit cannot fire without the binding."

A2 sets the precedent for A3 (TDD-guard, same hook event class) and A4 (Bash/Agent-context, different matchers).

Per CLAUDE.md output convention, owner reads from §9 (decisions for owner) — every other section supports it.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5)

**Named spec objective this plan satisfies:**

- **`docs/rebuild/spec/pos-v2-objectives-spec.md` line 134–135 — Deterministic (tiered).** Same binding A1 satisfied. A2's gate decisions are the audit log line 135-(b) names ("any arbitrary decision (no rubric cited) surfaces as a lint failure pending rubric definition") — every Edit that fails to bind to an AC IS the surfaced lint output (the deny + reason text).
- **VALUE_PROPOSITION's two tests (the prime objective ACs).**
  - *Primary-persona test (AC.PO.1):* the persona's translation toolkit no longer has to remember "every edit must trace to an AC." The substrate refuses unbound edits; the persona doesn't carry the rule. Reduces translation burden directly.
  - *Harness test (AC.PO.2):* the gate is a reusable harness primitive every future structural-enforcement amendment composes against (the audit log is consumed by dispatch-staleness; the carve-out helper is shared with framework-write-prevention; the decision pattern templates A3 and A4).

**Sealed-component fence (D3 governs):**

- `hands-off-lifecycle` — single sealed component. New PreToolUse hook script + settings-merge surface + first-run-helper wiring + tests.
- `objective-tracker` — consumer-only. A2 calls A1's public read API (`manifest_rows_for_ac`, `manifest_rows_matching_source_path`); no schema or runtime change.
- `loam-mode` — consumer-only via the workspace-mode bit (already a `corpus_load_sentinel.workspace_mode()` thin wrapper from A1).

**Single sealed component touched: `hands-off-lifecycle`.** Symmetric with amendment #46's UserPromptSubmit hook addition shape.

**ODD §2.5 reverse direction.** Every code path, branch, dependency, and test in A2's diff traces back to a named AC under §4. No silent branches; no defensive `if`s without backing AC.

---

## 3. Three-lens analysis

### Lens 1 — Claude leverage

*Required research question: what Claude capability does this lean on or extend?*

A2 leans on three Claude Code primitives end-to-end:

- **`PreToolUse` hook event.** Claude-native; documented; subagent-inheriting. The gate is one entry in the project's settings.json merged via the same machinery `SessionStart` and `UserPromptSubmit` already use. No reimplementation of dispatch-or-edit semantics.
- **`Edit`, `Write`, `MultiEdit` tool matchers.** Native primitives; A2 fires before any of the three. No bypass surface — every textual modification in a Claude Code session goes through one of these tools.
- **`hookSpecificOutput.permissionDecision: "deny"` + `permissionDecisionReason`.** Native deny mechanism; the reason text appears to the model as `additionalContext` so the model sees the diagnostic and adjusts. No prose-warning shape.

The substrate (manifest table, sentinel files) extends Claude-adjacent infrastructure that A1 shipped. Claude doesn't ship an objective registry; A1 added one against `objective-tracker`'s schema-evolution surface. A2 is a pure consumer of that substrate at the Claude hook layer. The asymmetric finding from the locked research §7.1 — *"Claude Code's hook surface IS the structural-enforcement surface"* — applies recursively: A2 is the first concrete gate; the same hook surface carries A3 and A4 next.

### Lens 2 — Harness + primary-persona value

*Primary-persona test: does this reduce the translation burden between the user's natural-language intent and AI-effective execution?*

**Yes — direct, load-bearing reduction.** The persona's translation toolkit currently includes "every Edit/Write must trace to a named AC, and you must remember to author the manifest row + sentinel before dispatching the build." A2 makes the binding structural — the persona dispatches a build; the build's first move is registering manifest rows; the gate enforces the binding from there. The persona's mental model collapses from "remember to enforce ODD §2.5" to "ODD §2.5 enforces itself at the edit boundary." The persona keeps the methodology in mind for AUTHORING (writing ACs, choosing globs); enforcement is no longer the persona's concern.

*Harness test: does this add to the toolkit the primary persona can draw from?*

**Yes — five new toolkit primitives.**

1. **The PreToolUse-gate-script pattern.** A2's `objective_binding_gate.py` is the first script of its shape; A3 and A4 follow the same pattern.
2. **The carve-out detection helper.** A2 ships a small `_is_dev_discipline_path(path)` helper (location method-shaped — could be in a shared `_gate_helpers.py` library). Reusable by every future PreToolUse gate.
3. **The audit-log shape.** NDJSON gate-decision log at `<workspace>/workspace/.pos/objective-binding-gate.log`. Consumed by FIDRAFT-143 dispatch-staleness check + future audit / observability surfaces.
4. **The settings-merge surface for PreToolUse.** `merge_pre_tool_use` mirrors `merge_user_prompt_submit`. Future amendments (and end users authoring their own hooks) compose against it.
5. **The "register-rows-at-build-start" discipline.** A2's halt-trigger names this: every future amendment build registers its (component, ac_id, source_path_glob) rows BEFORE the first source edit. The discipline becomes the canonical pos-v2 build flow.

Both Lens 2 tests pass. **→ AC.PO.1 + AC.PO.2.**

### Lens 3 — ODD authoring

A2 is structurally shaped, not advisory. The gate is deterministic — same path + same sentinel + same manifest = same decision, every fire. The refusal is structured (`permissionDecision: "deny"`), the diagnostic is named (the `permissionDecisionReason`), the audit is captured (the NDJSON log). Every AC below is outcome-shaped (no "the implementation will use X" language). Method (decision-tree shape, exact JSON keys for the deny reason, helper-module placement, exact carve-out path-list ordering) is the builder's call and lives in the builder plan.

ODD §5.1.1 (relocate-vs-eliminate test): A2 ELIMINATES the "edit without AC binding" failure class. A future code change cannot re-introduce the failure without active discipline (i.e. without amending or removing A2 itself); the gate's refusal shape is structural, not an `if/else` a maintainer can forget to update.

---

## 4. Acceptance criteria

A2's outcome is the gate's observable behaviour at every PreToolUse Edit/Write/MultiEdit fire. Eight ACs cover the seven behaviours plus the seal-diff invariant.

- **AC.OBG.1 — Refuse Edit on sealed-component source with no active-scope sentinel (DEV MODE).** Given workspace-mode = `dev-mode`, given `tool_input.file_path` is under a sealed-component source path (i.e. matches at least one of the per-component prefixes that the dev-mode-manifest's `always_loaded` set declares — `framework/<component>/**`), given `read_active_scope_sentinel(workspace_root)` returns `None`, given the path is not in the dev-discipline carve-out list (AC.OBG.5): the hook returns `hookSpecificOutput.permissionDecision: "deny"` with a `permissionDecisionReason` that names (a) the path, (b) the missing sentinel, (c) at least one repair direction (author a sentinel, retry on a carve-out path, halt-and-surface).

- **AC.OBG.2 — Refuse Edit when sentinel binds an AC with no manifest row.** Given the sentinel is present, given `manifest_rows_for_ac(component, ac_id)` returns `[]` for at least one binding in the sentinel AND no other binding has rows that match (i.e. the sentinel's bindings collectively have zero applicable rows): hook returns `permissionDecision: "deny"` with a reason that names the unregistered binding and at least one repair direction (register the row via `tracker.register_source_binding(...)`, or correct the sentinel to a registered binding).

- **AC.OBG.3 — Refuse Edit when no manifest-row glob matches the path.** Given the sentinel is present, given the sentinel's bindings have at least one manifest row each, given no row's `source_path_glob` `fnmatch.fnmatchcase`-matches `tool_input.file_path`: hook returns `permissionDecision: "deny"` with a reason that names the path, the bound `(component, ac_id)` pairs, and the globs each binds to.

- **AC.OBG.4 — Allow Edit when path matches at least one bound manifest-row glob.** Given the sentinel is present, given at least one manifest row whose `(component, ac_id)` matches a sentinel binding has a `source_path_glob` that `fnmatch.fnmatchcase`-matches `tool_input.file_path`: hook returns no `permissionDecision` (default-allow) OR explicit `permissionDecision: "allow"`. The model proceeds with the edit.

- **AC.OBG.5 — Allow Edit on dev-discipline carve-out paths regardless of sentinel state.** Given `tool_input.file_path` is under any of: `docs/`, `tools/`, `.scratch/`, `personas/`, OR matches `CLAUDE*.md` at workspace root, OR matches `.gitignore` at workspace root, OR matches `framework/docs/`, `framework/tools/` (post-D-migration framework-rooted analogues), OR is one of the universal-paths admissions used in pos-amend manifests (`docs/odd-methodology.md`, `docs/odd-in-pos.md`, `docs/rebuild/FUTURE_IDEAS.md`, `docs/rebuild/FUTURE_IDEAS_DRAFT.md`): hook allows regardless of sentinel/manifest state and regardless of mode. (The exact path-list and matching shape — substring vs glob vs prefix-tree — is method per ODD §7.4.)

- **AC.OBG.6 — Gate is a no-op when workspace-mode is `normal-use`.** Given `workspace_mode(workspace_root) == "normal-use"`: hook returns no `permissionDecision` and does not consult the active-scope sentinel or the manifest table. The hook's wall-clock cost in this branch is bounded by the mode-bit read alone (sub-10ms, matches A1's mode-bit p95 envelope).

- **AC.OBG.7 — Every gate fire is observable through a deterministic audit surface.** Each PreToolUse fire (allow + deny + no-op) is recorded in a workspace-local audit surface that a downstream consumer can read deterministically without re-running the gate. The recorded data is sufficient to reconstruct: when the fire happened, which tool/path/mode it observed, the sentinel state, the bound `(component, ac_id)` pairs (when present), the gate's decision, and (on deny) the same reason text the model received. The surface is append-only in A2 (rotation deferred); concurrent fires across processes do not corrupt each other (atomicity guarantee). Path, format, and exact field names are method per ODD §7.4 — the builder confirms the shape composes with the FIDRAFT-143 dispatch-staleness consumer (research §6.3) and any sibling-amendment audit-log shape that may emerge.

- **AC.OBG.S — Seal-diff confined to fence.** A2's seal-diff window contains only edits under `framework/hands-off-lifecycle/{hooks,tests,seals}/` and the universal-paths admissions (`docs/rebuild/plans/`, `CLAUDE.md`, `docs/odd-methodology.md`, `docs/odd-in-pos.md`, `docs/rebuild/FUTURE_IDEAS.md`). Per-invariant frozen-both-endpoints BASELINE pattern (per `docs/odd-in-pos.md` §10.3) for the A2 invariant test.

### Behaviour-count check (forward)

| # | Declared behaviour in §1 / §4 | AC |
|---|---|---|
| 1 | Refuse Edit on sealed-component source with no sentinel (DEV MODE) | AC.OBG.1 |
| 2 | Refuse Edit when sentinel binds AC with no manifest row | AC.OBG.2 |
| 3 | Refuse Edit when no manifest-row glob matches path | AC.OBG.3 |
| 4 | Allow Edit when path matches a bound glob | AC.OBG.4 |
| 5 | Allow Edit on dev-discipline carve-out paths regardless | AC.OBG.5 |
| 6 | No-op in NORMAL USE | AC.OBG.6 |
| 7 | Audit log writes deterministic NDJSON per fire | AC.OBG.7 |
| 8 | Seal-diff confinement | AC.OBG.S |

**Behaviours = 8, ACs = 8.** Match.

### Behaviour-count check (reverse)

The reverse direction (every code path / branch / dep / test in the diff traces back to AC.OBG.x) is exercised in the builder plan's §2.5 reverse-direction audit at build time. This plan asserts the audit will run; the builder records its outcome.

---

## 5. Hard constraints

1. **Dependency fence.** Source-edit scope: `framework/hands-off-lifecycle/{hooks,tests,seals}/`. Any edit to other sealed components is a halt trigger. Non-fence consumer reads (`objective-tracker.runtime.ObjectiveTracker.manifest_rows_*`, `loam-mode` via `corpus_load_sentinel.workspace_mode()`) are READ-ONLY; if a write or schema extension surfaces necessary, that's an A2.1 corrective on A1's substrate.
2. **Reversibility.** Fully reversible. The gate is additive: a new hook script, a new settings.json entry, a new audit log file. Removing the entry restores prior behaviour; the audit log is append-only and operator-deletable.
3. **Budget.** PreToolUse hook < 100ms p95 (target < 50ms — the hook fires per-edit, latency compounds across a build's edit-burst). NORMAL USE branch < 10ms (mode-bit-read only). Audit-log append microseconds-scale. Manifest query < 5ms (single SQLite read against the WAL).
4. **Fail-closed direction (DEV MODE).** Sentinel-absent / row-absent / glob-mismatch → DENY. Every refusal carries a structured `permissionDecisionReason` naming the failure + at least one repair path. Refusal is observable to the model and to the operator (audit log).
5. **Fail-open direction (NORMAL USE).** Mode = `normal-use` → ALLOW unconditionally. The gate must not silently fire in derived workspaces.
6. **No `--amend`.** Corrective commits only (per `feedback_no_amend_in_agent_dispatches`).
7. **ODD §2.5.** Every code path, branch, dependency, and test in A2's diff traces back to AC.OBG.1–AC.OBG.S. The builder runs the §2.5 reverse-direction audit before seal.
8. **No new top-level objective.** A1's audit substrate satisfies spec line 134–135-(a); A2's audit log satisfies the implicit lint surface for line 135-(b). No spec amendment.
9. **No method prescription.** This plan-doc names outcomes; the builder plan picks: hook script structure, decision-tree shape, exact carve-out path-list and ordering, helper-module placement (`_gate_helpers.py` shared library vs inline), JSON keys for the deny reason and audit log, how MultiEdit's `edits` array is iterated, settings-merge function name and signature.
10. **A1 substrate is sealed.** A2 may not propose edits to A1's manifest schema, sentinel JSON shape, mode-bit interface, or A1's reader/writer contracts. If during A2 build a substrate change becomes necessary, halt — it's an A1.1 corrective amendment, not folded into A2 (per A1's constraint 9).
11. **Backwards-compat.** Existing PreToolUse hooks authored by users (or by future amendments) must be preserved. The merge surface mirrors `merge_user_prompt_submit`'s `_USER_AUTHORED` back-up convention.
12. **No agent-side discipline-as-code.** A2 must not require build agents or the persona to "remember to call the gate" — the gate IS the discipline. Failure-mode 4.1 (missing sentinel) is denied at edit time; the dispatcher / build-agent learns from the deny diagnostic.
13. **Sealed-component dispatch must explicitly name `pos-amend apply`** as the bookkeeping mechanism for the seal-diff window per `feedback_dispatch_explicit_pos_amend_apply`.
14. **Build-time AC-row registration is a hard prereq.** The build agent's first action (before the first source edit) is registering the manifest rows for AC.OBG.1–AC.OBG.S via `tracker.register_source_binding(component="hands-off-lifecycle", ac_id="AC.OBG.x", source_path_glob="framework/hands-off-lifecycle/...")`. Without this step, the build agent's own first edit fails the gate (chicken-and-egg).
15. **Audit-log path follows D-migration D.2 convention.** `<workspace>/workspace/.pos/objective-binding-gate.log` (NOT `<workspace>/.pos/`). Builder confirms by inspecting `framework/workspace-bootstrap/src/workspace_bootstrap/workspace_paths.py` at build time — the canonical `WORKSPACE_STATE_SUBDIR` = `"workspace"`.

---

## 6. D-decisions for this plan (record + rationale)

The five programme-level D-decisions are LOCKED 2026-04-26 (see header). This section records the A2-level design choices that follow from the research artefact + the programme locks. **Owner is asked to rule on D1, D2, D3, D4, D6, D7 below; D5 is locked by programme D4; D8 is method per ODD §7.4.** Decisions for owner are summarised in §9 (read this first).

### D-A2.1 — Firing layer

**Recommendation: Candidate A — `PreToolUse` matcher `Edit|Write|MultiEdit`** (per research §2.6).

The PreToolUse hook event is the canonical Claude-native primitive for refusing tool calls; matchers cover every tool call that authors text. Subagent-inheritance covers every dispatched build agent automatically. Symmetric with future A3 (TDD-guard, same event class) and A4 (Bash/Agent-context, different matcher). Method-level: the hook is one Python script invoked per matcher match.

Alternatives rejected in research §2:
- B (UserPromptSubmit + persona discipline) — advisory clothing; ODD §5.1 + §5.1.1 violation.
- C (pos-amend pre-commit) — too late.
- D (Agent-tool-dispatch wrapper) — composes WITH A2 not instead-of (deferred to a separate amendment).
- E (SessionStart-only validation) — too coarse.

### D-A2.2 — Refusal mechanism

**Recommendation: Candidate α — `permissionDecision: "deny"` + structured `permissionDecisionReason`** (per research §3.1).

Native Claude Code surface. Reason text is structured-natural-language: opens with the failure class, names the path, names what would have admitted it, names the repair. Visible to model + operator.

Alternative rejected: γ (allow-with-warning via `additionalContext`) is advisory in structural clothing.

### D-A2.3 — Default on missing active-scope sentinel (DEV MODE)

**Recommendation: deny-with-diagnostic-naming-carve-out-alternative** (per research §4.1, §7.1).

A2 must not auto-create sentinels. The right repair direction depends on the dispatch's intent — the diagnostic surfaces both options ("if this is a docs/plans edit, retry on a carve-out path; if this is a source edit, the dispatch wrapper should have authored a sentinel").

Migration shape (see D-A2.6) handles the cutover.

### D-A2.4 — Default on missing manifest row

**Recommendation: deny-with-diagnostic-naming-registration-command** (per research §4.2).

A2 must not auto-register rows. The build agent is the AC-author; row registration is part of the build's authoring discipline (see hard constraint 14).

### D-A2.5 — DEV-MODE / UNIVERSAL split

**LOCKED by programme D4 — A2 is entirely DEV-MODE-only.** Three sub-cases evaluated and rejected as universal candidates (research §5.2). No A2 sub-cases warrant universal application. Secret-file blocking is A4 territory (different gate shape); main-session-write-prevention is A2.adjacent (different decision data); plan-cross-contamination is a future linter (different surface).

### D-A2.6 — Carve-out path list (D1 dev-discipline)

**Recommendation:** the carve-out list = the union of:

- `docs/` (all)
- `framework/docs/` (post-D-migration analogue)
- `tools/` (all)
- `framework/tools/` (post-D-migration analogue)
- `.scratch/` (all)
- `personas/` (all — historically untracked dev-discipline)
- `CLAUDE.md`, `CLAUDE.dev.md` at workspace root
- `framework/CLAUDE.md` (post-D-migration analogue)
- `.gitignore` at workspace root and per-component
- `docs/odd-methodology.md`, `docs/odd-in-pos.md` — universal-paths admissions
- `docs/rebuild/FUTURE_IDEAS.md`, `docs/rebuild/FUTURE_IDEAS_DRAFT.md`

Per the programme D1 lock + the D-migration D.1+ post-restructure layout, the list contains both pre-D-migration and post-D-migration shapes. The exact match algorithm (substring vs glob vs prefix-tree) and ordering is method per ODD §7.4 and lives in the builder plan.

The set is **expansive by design**: the carve-out is the cheap-and-correct shape; missed source edits are caught by the manifest-glob rules; missed dev-discipline edits would falsely deny operator work and erode trust in the gate.

### D-A2.7 — Migration shape

**Recommendation: Shape α — Hard cutover with diagnostic-named-repair** (per research §7.1).

A2 lands; existing in-flight DEV MODE sessions face deny on the first sealed-component source edit until they author a sentinel. Operator pain ~1 session-restart per workspace; the deny diagnostic names the exact repair command. Soft cutover (Shape β — grace period downgrades deny → log) is rule-shaped (relocate-not-eliminate); first-session-fail-safe-to-allow (Shape γ) needs its own substrate.

The research notes (§7.2) that the carve-out (D-A2.6) covers 95%+ of main-session edits anyway — most actual disruption is for build-agent dispatches that haven't yet adopted the dispatcher-side sentinel-author wrapper. That wrapper is A2.adjacent (out of scope per §7).

### D-A2.8 — Audit log shape (method per ODD §7.4)

**Default: NDJSON at `<workspace>/workspace/.pos/objective-binding-gate.log`** mirroring amendment #48's `dispatch-wrapper.log` pattern. One JSON object per line. Atomic-append via POSIX `O_APPEND`. Append-only in A2; rotation deferred to a future amendment.

The builder may refine the log path / format if a sibling amendment standardises a different shape, OR if a shared `_gate_helpers.py` audit-log module emerges that A3/A4 also consume (per research §9.3 architecture-creep watch).

---

## 7. Out of scope (explicit per ODD §2.5)

The four-amendment programme decomposition (research §6) names A3/A4 explicitly; A2 declares each as a future amendment. Items below are explicitly NOT in A2's surface.

- **A3 — `tdd-guard-test-pinned-to-objective`.** The PreToolUse Edit/Write hook that requires a matching `test_<AC>_*.py` to exist. Depends on A2's manifest-binding mechanism (A3 reads the same `manifest_rows_*` API). A2 ships zero test-existence logic.
- **A4 — `bash-and-agent-context-guards`.** The Bash-tool guards (`git commit --amend` blocker, secret-file commit blocker, `pos-amend apply --dry-run` exit-0 commit gate) and Agent-tool guards (WD-verification, dispatch-staleness check). A2 does not gate Bash; A2 does not gate Agent dispatches.
- **A2.adjacent — Active-scope sentinel auto-author at dispatch time.** The wrapper that writes the sentinel as part of `Agent` tool dispatch invocation. Composes with amendment #52's existing `dispatch_with_scope` (small extension; out of A2's fence). A2 refuses edits without a sentinel; this future amendment removes the dispatcher-side "author the sentinel manually" overhead.
- **A2.adjacent — Audit-log rotation.** A2 ships append-only NDJSON. Rotation is a future amendment (or a generic JSONL rotation primitive).
- **Cross-amendment manifest queries** — "show me every Edit allowed in the last 30 days" historical surface. A2 ships the per-fire log; reporting is downstream.
- **Automatic manifest-row backfill from existing seal commits.** Today the manifest table is empty (A1 ships the table; no rows are seeded). A future amendment could walk the SHA history and backfill rows from existing seal narratives. A2 does not do this; build agents register their own rows at build time (hard constraint 14).
- **Persona-side surfacing of A2 deny diagnostics.** The model receives `permissionDecisionReason` natively; the persona may want to surface the deny in user-readable narration. A2 does not include persona-prompt edits.
- **Composition with FIDRAFT-130 corpus-inlining.** A2's diagnostic mentions corpus state when missing (research §6.1) but does not refuse for missing corpus. A separate amendment (or a refinement of A2 once corpus-inlining ships) may extend the deny rule to corpus-state.
- **Composition with FIDRAFT-136 main-session-write-prevention.** Distinct decision logic; separate amendment. May share helper library with A2 if both ship; A2 must not preempt.
- **Audit-log consumers** (FIDRAFT-143 dispatch-staleness, observability dashboards). A2 ships the log; consumers are downstream amendments.
- **Settings.json migration on existing workspaces.** A2's first-run-helper wires the new PreToolUse hook into freshly-bootstrapped workspaces. Existing workspaces' settings.json files may need a re-merge pass; the existing `merge_user_prompt_submit` / `merge_session_start` precedent handles this for re-bootstrap (the amendment #45 + #46 pattern). The builder confirms the re-merge is idempotent.

---

## 8. Halt triggers

Halt and surface (do not silently extend) when any of the following fires:

1. **A1 substrate gap.** If A2's design surfaces a missing column / table field / sentinel field that A1 doesn't provide → halt; A1 needs an A1.1 corrective. Specifically: if `manifest_rows_for_ac` doesn't return the rows in a shape A2 needs; if `read_active_scope_sentinel` doesn't expose the bindings tuple A2 needs; if `workspace_mode` doesn't expose the two-string contract A2 expects. Verification at build start.
2. **PreToolUse merge mechanism missing.** The existing `first_run_settings.py` covers SessionStart + UserPromptSubmit. PreToolUse may need a parallel `merge_pre_tool_use` function. If the file's merge architecture cannot accept the new entry-type without contract change → halt. The signal back: hands-off-lifecycle's merge surface needs an A2.1 corrective OR substrate amendment.
3. **MultiEdit semantics ambiguity.** If Claude Code's `MultiEdit` tool input shape (the `edits` array) cannot be denied per-entry — i.e. partial-deny is impossible from a single PreToolUse fire — the gate's behaviour is "deny the whole MultiEdit if any edit fails the gate." If verification at build time reveals a different surface, halt and signal — Luke rules on whether whole-batch-deny is correct, OR whether A2 needs a separate per-edit hook (e.g. fire on `Edit` and `Write` only and let MultiEdit through).
4. **Existing PreToolUse hook collision.** If a workspace already has a user-authored PreToolUse hook (the merge_user_prompt_submit precedent is to back the prior hook into `_USER_AUTHORED` state), A2's hook must not silently displace it. If the merge would lose user state, halt and signal.
5. **An ODD §2.5 violation surfaces in surrounding code during A2 build.** The hook script's adjacent modules (`first_run_settings.py`, `first_run_helper.py`) may contain pre-existing §2.5 violations the build's verification pass uncovers. Halt-and-surface per the dispatch's explicit ODD-violation clause; do not silently extend.
6. **An AC the builder cannot author outcome-shaped surfaces.** If during the builder plan's authoring some A2 behaviour resists outcome-shaping (a method prescription is the only natural form), halt and signal back — the AC's wording may need owner ruling before build proceeds.
7. **Architecture creep — multi-tenant gate framework.** If during build the builder concludes a single multi-tenant gate framework (rather than per-amendment hooks) is the right shape, halt — that contradicts the recommendation in research §9.3 and is an architecture-level decision the owner must rule on. The default in this plan is per-amendment hooks; if the builder strongly disagrees, halt-and-signal rather than silently consolidating.
8. **The carve-out path list is incomplete.** If during build the builder discovers a path that is genuinely dev-discipline but NOT in D-A2.6's list, halt and signal — the list needs an explicit owner-approved addition (and the addition is captured as a §14 method-decision register entry).
9. **Substrate-fence breach.** Per constraint 1: any source-edit need outside `framework/hands-off-lifecycle/{hooks,tests,seals}/` halts. Specifically: any edit to `framework/objective-tracker/`, `framework/loam-mode/` (note: loam-mode is dev-discipline tools/, but read-only-by-A2-contract per constraint 1), or any other sealed component → halt. Universal-paths admissions are the only exception.
10. **Self-bootstrap fails.** Per hard constraint 14: the build agent's first move must be registering manifest rows for AC.OBG.x. If the agent's environment cannot reach `objective-tracker.runtime.ObjectiveTracker.register_source_binding` (e.g. the tracker isn't bootstrapped for the workspace, or the API has changed since A1 sealed), halt — the agent's own first source edit will fail the gate, which means A2's own build is structurally blocked.

---

## 9. Decisions for owner (only genuinely uncertain)

The five programme-level D-decisions are LOCKED 2026-04-26 (see header) and not surfaced here. **Six decisions are surfaced for owner ruling**, with recommendation per `feedback_summarize_and_surface_decisions`:

### D-A2.1 — Firing layer

- **Question:** PreToolUse Edit|Write|MultiEdit hook (Candidate A) vs alternatives B/C/D/E.
- **Recommendation:** **Candidate A**. Native Claude primitive; per-edit granularity; subagent-inheriting; symmetric with A3/A4. (Research §2.6.)
- **Alternatives:** B (UserPromptSubmit) advisory clothing; C (pos-amend pre-commit) too late; D (Agent-wrapper) composes WITH not INSTEAD; E (SessionStart only) too coarse.
- **Caveat:** if owner picks anything other than A, every AC below changes shape.

### D-A2.2 — Refusal mechanism

- **Question:** `permissionDecision: deny` + structured reason (Candidate α) vs warning-only (γ).
- **Recommendation:** **Candidate α**. Hard refusal; structured reason; native surface. Warning-only fails ODD §5.1.1.
- **Alternatives:** β (exit 2 + stderr) less structured; γ (warning) advisory.

### D-A2.3 — Default on missing active-scope sentinel (DEV MODE)

- **Question:** missing sentinel → deny vs auto-create vs warn.
- **Recommendation:** **deny with diagnostic naming carve-out alternative + sentinel-author repair direction** (research §4.1).
- **Why:** A2 must not auto-create sentinels — that hides the dispatcher-side failure. Auto-creation is rule-shaped (relocate-not-eliminate per ODD §5.1.1).

### D-A2.4 — Default on missing manifest row

- **Question:** missing manifest row → deny vs auto-register vs warn.
- **Recommendation:** **deny with diagnostic naming the registration command** (research §4.2).
- **Why:** A2 must not auto-register rows — the build agent is the AC-author; row registration is part of the build's authoring discipline.

### D-A2.6 — Carve-out path list

- **Question:** which paths are dev-discipline carve-outs?
- **Recommendation:** the union of `docs/`, `framework/docs/`, `tools/`, `framework/tools/`, `.scratch/`, `personas/`, `CLAUDE*.md` at root, `framework/CLAUDE.md`, `.gitignore`, plus the universal-paths admissions (`docs/odd-methodology.md`, `docs/odd-in-pos.md`, `docs/rebuild/FUTURE_IDEAS.md`, `docs/rebuild/FUTURE_IDEAS_DRAFT.md`).
- **Why:** matches programme D1 lock + post-D-migration layout. Expansive by design — missed dev-discipline edits would falsely deny operator work.
- **Alternatives:** a tighter list catches more (false-deny rate goes up); a looser list misses real bindings (false-allow rate goes up). Current list errs on operator-trust.

### D-A2.7 — Migration shape

- **Question:** hard cutover (α) vs grace-period soft cutover (β) vs first-time fail-safe-to-allow (γ).
- **Recommendation:** **α — hard cutover** with diagnostic-named repair (research §7.1).
- **Why:** soft cutover is rule-shaped (relocate-not-eliminate); first-time fail-safe needs its own substrate. Operator pain is one diagnostic-read per existing session; the carve-out covers 95%+ of main-session edits.
- **Caveat:** if owner picks β or γ, AC.OBG.1 changes shape (allow-with-log instead of deny).

### Surfaced for owner ruling: 6 (D-A2.1, D-A2.2, D-A2.3, D-A2.4, D-A2.6, D-A2.7).

(D-A2.5 locked by programme D4. D-A2.8 is method per ODD §7.4 — builder default is NDJSON at `<workspace>/workspace/.pos/objective-binding-gate.log`; a sibling amendment may relocate.)

---

## 10. Risks

- **R1 — Carve-out list drift.** The carve-out path list (D-A2.6) hard-codes the dev-discipline boundary. A future amendment that introduces a new dev-discipline top-level path (e.g. a new `framework/whatever-tools/` tree) needs to amend A2's list. This is the relocate-not-eliminate trap A2 itself is supposed to avoid (per ODD §5.1.1). Mitigation: the carve-out helper SHOULD compose with the dev-mode-manifest's audit_excludes / always_loaded sets where possible. Builder confirms the cheapest correct shape; if the dev-mode-manifest already encodes the needed information, A2's helper consumes it directly.
- **R2 — MultiEdit whole-batch-deny ergonomics.** If MultiEdit cannot be partially-denied, an operator who batches 5 edits and 1 of them fails the gate gets the WHOLE batch denied. The natural recovery is to retry without the bad edit, but the operator has to manually parse which edit failed. Mitigation: the deny diagnostic names the failing edit's `file_path` precisely; operator can split the batch.
- **R3 — Hook latency on edit-bursts.** A build that makes 100 edits in a short span pays the hook cost 100×. Target < 50ms means total burst overhead < 5s — acceptable. But if the manifest table grows large (1000+ rows) and the matching-rows query becomes expensive, the hook latency could creep. Mitigation: AC.OBG.4's match check is bounded by the SENTINEL's bound rows (typically 1–10), not the manifest table size. Cost stays bounded.
- **R4 — Stale audit log not rotated.** Append-only NDJSON grows unboundedly. Out-of-scope-for-A2 (§7) but tracked: a future maintenance amendment.
- **R5 — Sentinel auto-create temptation.** Operators frustrated by AC.OBG.1's "deny-on-missing-sentinel" may push for an auto-create flag. Resisting that pressure is part of A2's discipline (D-A2.3 lock); if it surfaces, the right fix is the dispatcher-wrapper amendment (A2.adjacent) — auto-author at dispatch time, not auto-create on first edit.
- **R6 — Settings.json merge regression.** If `merge_pre_tool_use` is mis-implemented, a workspace's user-authored PreToolUse hook could be silently dropped. Mitigation: the existing `merge_user_prompt_submit` test pattern (`framework/hands-off-lifecycle/tests/test_AC37_1_settings_agent_merge.py` + amendment #46 tests) is the precedent; A2's merge mirrors it byte-for-byte.
- **R7 — Workspace-mode resolution failure → wrong default.** If `workspace_mode()` raises (it shouldn't — A1 contract is fail-closed-to-permissive), the gate would default to NORMAL USE behaviour and silently allow. Mitigation: AC.OBG.6's "no-op when mode = normal-use" is correct; the failure is actually OPEN (allow), which is acceptable for a workspace whose mode can't be resolved (per A1's fail-closed-to-permissive direction).
- **R8 — Path-canonicalisation bugs.** `tool_input.file_path` may be absolute, relative, or symlinked. The match against `source_path_glob` must canonicalise. Mitigation: use `Path(file_path).resolve().relative_to(workspace_root)` BEFORE `fnmatch.fnmatchcase`. Builder records the canonicalisation contract in §14.
- **R9 — Carve-out vs binding-glob overlap.** A path that matches BOTH a carve-out AND a binding glob (e.g. a manifest row with `**/CLAUDE.md` would overlap with the CLAUDE.md carve-out). The carve-out check fires FIRST in the decision tree (per AC.OBG.5's "regardless of sentinel state"); the binding check fires only if carve-out doesn't match. Mitigation: builder confirms carve-out-first ordering in §14; tests cover the overlap case.

---

## 11. Bookkeeping

- **Plan-doc:** this file at `docs/rebuild/plans/structural-enforcement-a2-objective-binding-gate.md`.
- **Research artefact:** `docs/rebuild/plans/research/structural-enforcement-a2-objective-binding-gate-research.md` (this dispatch).
- **Programme research:** `docs/rebuild/plans/research/structural-enforcement-of-critical-requirements-research.md` (locked 2026-04-26; governs).
- **A1 plan (sibling, sealed):** `docs/rebuild/plans/structural-enforcement-a1-substrate.md`.
- **Builder plan:** to be authored by the build agent post-owner-approval at `docs/rebuild/plans/structural-enforcement-a2-objective-binding-gate.builder-plan.md`. Contains files-touched, symbol-level details, AC-to-test mapping, D-build choices (decision-tree shape, helper-module placement, exact carve-out path-list ordering, hook script structure), §2.5 reverse-direction audit, halt-trigger checks, pos-amend bookkeeping flow.
- **Manifest:** authored alongside the builder plan at `docs/rebuild/plans/structural-enforcement-a2-objective-binding-gate.manifest.yaml`. Single-component manifest (`hands-off-lifecycle`); `frozen_baseline: true` (H19 is frozen since project-start). Universal-paths block as standard.
- **Pos-amend bookkeeping flow** (per `feedback_dispatch_explicit_pos_amend_apply`):
  1. Author manifest at `docs/rebuild/plans/structural-enforcement-a2-objective-binding-gate.manifest.yaml` with the correct BASELINE (HEAD~1 of the upcoming amendment commit per the established #29/#34/.../#52 pattern).
  2. **Build-time manifest-row registration** (hard constraint 14): build agent's first action is `tracker.register_source_binding(component="hands-off-lifecycle", ac_id="AC.OBG.x", source_path_glob="...")` for each AC.OBG.1 through AC.OBG.S. Without this, the agent's own first edit fails the gate (chicken-and-egg).
  3. Author all source edits + tests; commit as the amendment commit on branch `pos-v2`.
  4. `pos-amend apply --dry-run <manifest>` — must exit 0.
  5. `pos-amend apply <manifest>` — advances BASELINE literals + widens seal-diff bindings + writes SEAL_COMMIT sidecars.
  6. `pos-amend seal --plan-doc /Users/lukeivers/ivers-corp-pos-v2/docs/rebuild/plans/structural-enforcement-a2-objective-binding-gate.builder-plan.md <manifest>` — runs the scoped test sweep, creates the seal commit, advances SEAL_COMMIT to the seal commit, appends builder-plan §SHA backfill follow-up commit.
  7. Verify: `pos-amend apply --dry-run <manifest>` exits 0 against post-seal HEAD.
- **Seal-diff window:** BASELINE = HEAD~1 of amendment commit (set in builder plan after dispatch). Allowed paths under the window: `framework/hands-off-lifecycle/{hooks,tests,seals}/`, plus universal admissions.
- **Programme tracking:** A2 unblocks A3 (TDD-guard, depends on A2's manifest-binding mechanism). A4 depends on A1's workspace-mode bit, not A2. The four amendments serialise per `feedback_serialize_amendment_builds` (no parallel builds in canonical tree until pos-amend worktree-isolation is verified).
- **Test scope per amendment-dispatch CDC speedups:** narrow pre-amendment test scope to `framework/hands-off-lifecycle/tests/` + `framework/objective-tracker/tests/` (consumer-only; sanity check that A1's substrate API still works). Skip pre-seal full-suite rerun (sidecar-only edits between amendment and seal). Inline odd-methodology snippets into the dispatch brief.

---

## 12. References

- Locked programme research: `docs/rebuild/plans/research/structural-enforcement-of-critical-requirements-research.md`
- A2 research (this dispatch): `docs/rebuild/plans/research/structural-enforcement-a2-objective-binding-gate-research.md`
- A1 plan (sealed; substrate this builds on): `docs/rebuild/plans/structural-enforcement-a1-substrate.md`
- A1 builder plan (records D-build choices): `docs/rebuild/plans/structural-enforcement-a1-substrate.builder-plan.md`
- A1 substrate code (read-only inputs):
  - `framework/objective-tracker/src/store.py` (manifest-table CRUD; `objective_manifest` schema)
  - `framework/objective-tracker/src/runtime.py` (public API: `register_source_binding`, `manifest_rows_for_*`, `manifest_rows_matching_source_path`)
  - `framework/hands-off-lifecycle/hooks/active_scope_sentinel.py` (reader contract `read_active_scope_sentinel` returning `ActiveScopeSentinel | None`)
  - `framework/hands-off-lifecycle/hooks/corpus_load_sentinel.py` (workspace-mode bit `workspace_mode(workspace_root) -> "dev-mode" | "normal-use"`)
- Hook merge precedent (sibling pattern):
  - `framework/hands-off-lifecycle/hooks/first_run_settings.py` `merge_user_prompt_submit` (amendment #46 — A2's `merge_pre_tool_use` mirrors this shape)
  - `framework/hands-off-lifecycle/hooks/first_run_helper.py` (composition wiring; A2 extends the same pattern)
- Sibling plan-doc shape: `docs/rebuild/plans/structural-enforcement-a1-substrate.md` (the immediate precedent)
- ODD methodology: `docs/odd-methodology.md` (§2.5 reverse direction; §5.1 structural-over-advisory; §5.1.1 relocate-vs-eliminate test; §8.1 authoring-time violations)
- ODD-in-pos: `docs/odd-in-pos.md` (§10.3 per-invariant frozen-both-endpoints baseline pattern — for AC.OBG.S seal-diff invariant)
- VALUE_PROPOSITION: `docs/rebuild/VALUE_PROPOSITION.md` (AC.PO.1 + AC.PO.2 — A2's Lens 2 anchor)
- FUTURE_IDEAS: `docs/rebuild/FUTURE_IDEAS.md` Idea 1 (programme), Idea 8 (structural context-load gate — A2.adjacent)
- FIDRAFT items A2 composes with: `docs/rebuild/FUTURE_IDEAS_DRAFT.md` lines 130 (corpus-inlining), 136 (main-session-write-prevention), 143 (dispatch-staleness)
- Claude Code hooks docs: https://code.claude.com/docs/en/hooks (PreToolUse decision-control surface; matchers; permissionDecision; permissionDecisionReason)
- Memory-bullet feedback rules carried forward:
  - `feedback_no_amend_in_agent_dispatches` — corrective commits only.
  - `feedback_dispatch_explicit_pos_amend_apply` — pos-amend named in dispatch.
  - `feedback_subagent_odd_violation_halt` — halt-and-surface explicit clause.
  - `feedback_amendment_dispatch_speedups` — narrow test scope, inline methodology.
  - `feedback_serialize_amendment_builds` — no parallel builds in canonical tree.
  - `feedback_summarize_and_surface_decisions` — §9 surface with recommendations.
  - `feedback_always_specify_wd_in_dispatches` — WD `/Users/lukeivers/ivers-corp-pos-v2/`.

---

## 14. Method-decision register (post-build, builder-backfilled)

Method-level decisions made during the build land here at seal time per `pos-amend seal --plan-doc` convention. Empty at plan-author time.

### Commit SHAs

(populated by `pos-amend seal --plan-doc <ABSOLUTE PATH>` per the seal-automation extension. Pass an ABSOLUTE path to avoid the `Path.relative_to` crash documented at commit `75c4d73`. The amendment commit + seal commit + plan-SHA backfill commit each appear here on completion.)

---

*End of plan-doc. Builder plan + manifest authored after owner approval.*
