# Structural enforcement — A2: objective-binding gate — Research

**Author:** research dispatch (Opus, background)
**Date:** 2026-04-28
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`
**Status:** authored, pending owner ruling on D-decisions §6 below.

**Locked governance (do not re-litigate):**

- Programme research: `docs/plans/research/structural-enforcement-of-critical-requirements-research.md` (locked 2026-04-26).
- A1 plan: `docs/plans/structural-enforcement-a1-substrate.md` (sealed; commits in §14).
- A1 substrate code (read-only inputs to A2): `framework/objective-tracker/src/{store.py,runtime.py,errors.py}`, `framework/hands-off-lifecycle/hooks/{active_scope_sentinel.py,corpus_load_sentinel.py,corpus_load_session_start.py}`.

**Programme-level locks (per A1 plan header):** D1 dev-discipline carve-outs; D2 TDD-guard scoped to re-extension-with-new-AC; D3 manifest extends `objective-tracker`; D4 secret/blast-radius universal, ODD-discipline DEV-MODE-only; D5 KEEP-ADVISORY list of 10. None re-opened in this research.

---

## Summary (read this first)

A2 is the FIRST gate-that-refuses in the structural-enforcement programme. It fires at Claude Code's `PreToolUse` hook for `Edit|Write|MultiEdit` tool calls; its fence is "an Edit/Write whose `tool_input.file_path` lies under a sealed-component source tree must trace to a `(component, ac_id, source_path_glob)` row in the objective-manifest table that the active-scope sentinel binds to." Edits without an active-scope sentinel, or whose path falls outside every glob the sentinel's bindings name, are denied with a structured `permissionDecisionReason`. DEV MODE only (D4). NORMAL USE workspaces short-circuit to allow.

Recommendation across the seven design questions:

- **Q1 firing layer:** `PreToolUse` + `Edit|Write|MultiEdit` matcher. Single hook script under `hands-off-lifecycle/hooks/objective_binding_gate.py`. Composes on A1's reader API (`read_active_scope_sentinel`, `manifest_rows_for_component`, `manifest_rows_matching_source_path`).
- **Q2 substrate consumed:** active-scope sentinel + objective-manifest table. Both are A1 deliverables — no A1 substrate gap. Workspace-mode bit (also A1) gates the whole behaviour.
- **Q3 absent-sentinel default:** **fail-closed-with-bypass-for-dev-discipline-paths**. Edit on a sealed-component source path with no sentinel = deny. Edit on `tools/`, `docs/`, `CLAUDE*.md`, `.scratch/`, `personas/` = allow regardless. (D1 carve-outs.)
- **Q4 mode-aware:** the gate ENTIRELY no-ops when mode = `normal-use` (per D4 — A2 is ODD-discipline). The DEV-MODE/UNIVERSAL split lives in A4, not A2.
- **Q5 mid-dispatch transitions:** the sentinel is read fresh on every PreToolUse fire — no caching across tool calls within the same session. Sentinel rewrites between Edit calls take effect on the next Edit.
- **Q6 carve-out shape:** carve-outs (D1) are the IDENTICAL tree the dev-mode-manifest already names as `dev_only` PLUS `tools/` + `personas/` + `.scratch/` + `CLAUDE*.md`. A2's carve-out helper is a separate module (not the dev-mode-manifest selector) because the audit-glob set there is for context-loading, not edit-gating.
- **Q7 missing-manifest-row default:** **deny.** A sentinel binding to `(orchestrator, AC.O.42)` where no `(orchestrator, AC.O.42, *)` row exists in the objective-manifest table is a misconfigured dispatch — not an edit-permission decision. Surface a clear diagnostic; refuse the edit.

The gate composes with three FIDRAFT items captured this session:

- **Corpus-inlining hook (FIDRAFT line 130):** A2 also reads the corpus-load sentinel; sessions with `state = "missing"` get a soft-warning addendum in the deny reason, but A2 does NOT itself refuse for missing corpus (that's a separate amendment — A2.1 candidate). A2 does refuse when the active-scope sentinel is absent in DEV MODE.
- **Main-session-write-prevention (FIDRAFT line 136):** A2's gate is the natural carrier of this check — when the workspace is a derived workspace whose `<workspace>/framework/` contains the sealed code, edits to `<workspace>/framework/**` from a `dev-mode` workspace whose canonical-pos-v2 path is elsewhere are denied (out of scope for A2 in this research; flagged for A2.2 or A4).
- **Dispatch-staleness verification (FIDRAFT line 143):** A2's gate-decision audit log is the substrate the dispatch-staleness check (a future PreToolUse `Agent`-tool gate) consults. A2 ships the log; staleness check is A4 territory.

The plan that follows authors A2 with seven outcome-shaped ACs + a seal-diff invariant. Method (decision-tree shape, exact JSON keys for the deny reason, exact carve-out path list ordering) is the builder's call.

---

## 1. What "objective-binding" means structurally

The locked programme research defines the binding as: every Edit/Write to a sealed-component source path must trace to a named acceptance criterion via three composable substrates A1 ships.

### 1.1 The three substrates the binding traces through

| Substrate | A1 surface | A2's use of it |
|---|---|---|
| Active-scope sentinel | `<workspace>/workspace/.pos/active-scope.json`; reader `read_active_scope_sentinel(workspace_root)` returning `ActiveScopeSentinel \| None` | Source-of-truth for the (component, ac_id) tuple the current dispatch is authoring against |
| Objective-manifest table | `objective_manifest(component, ac_id, source_path_glob, created_at)`; queries `manifest_rows_for_ac`, `manifest_rows_matching_source_path` | Source-of-truth for the source-path-glob set each AC may modify |
| Workspace-mode bit | `corpus_load_sentinel.workspace_mode(workspace_root)` returning `"dev-mode" \| "normal-use"` | Gate-firing predicate (D4 — DEV MODE only) |

A1 ships nothing else; A2 invokes only those three surfaces (read-only against `objective-tracker`'s public API; read-only against `hands-off-lifecycle`'s sentinel readers).

### 1.2 The fence statement

A `tool_input.file_path` is **inside the binding** when:

1. The workspace is `dev-mode` (else the gate does not apply); AND
2. The path is not in the dev-discipline carve-out list (D1: `tools/`, `docs/`, `CLAUDE*.md`, `.scratch/`, `personas/`, plus `.gitignore` and other universal-paths admissions); AND
3. The active-scope sentinel exists; AND
4. At least ONE binding `(component, ac_id)` in the sentinel has at least one manifest row whose `source_path_glob` matches the path (via `fnmatch.fnmatchcase`).

When all four hold, the edit is **allowed**. Any one false → **denied**, with a structured `permissionDecisionReason` that names which check failed and how to repair.

### 1.3 What an edit "outside the glob" looks like in practice

False-negatives the gate must refuse:

- **Drift edit.** Active-scope sentinel binds `(orchestrator, AC.O8.A1)` whose manifest row glob is `framework/orchestrator/src/**`. Builder edits `framework/cost-governance/src/wiring.py` "to be helpful while I'm here." Path doesn't match `framework/orchestrator/src/**`; deny.
- **Wrong-component edit.** Sentinel binds `(primary-persona, AC.A8.1)`. Builder edits `framework/orchestrator/src/orchestrator.py`. Path doesn't match any glob bound to `(primary-persona, AC.A8.1)`; deny.
- **Mid-amendment scope-creep.** Sentinel binds `(memory-system, AC.MS.5)`. Builder discovers what looks like a §2.5 violation in `framework/safety-layer/src/floor.py` and starts to "just fix it." Path doesn't match the binding; deny — the right move is halt-and-surface or extend the sentinel's bindings via a re-extension first.

False-positives the gate must NOT refuse:

- **Test next to source under same AC.** AC.O8.A1's source-path-glob is `framework/orchestrator/src/**`. The same AC also requires a test at `framework/orchestrator/tests/test_AC_O8_A1_*.py`. Either the manifest row admits both globs (`framework/orchestrator/{src,tests}/**`), OR a second manifest row is registered for the test path. Recommended: the latter — one (component, ac_id) tuple may have multiple rows, each a glob. Builders register source + test as two rows.
- **Universal-paths admissions.** `docs/plans/<plan>.md`, `CLAUDE.md`, `docs/odd-methodology.md`, `docs/FUTURE_IDEAS.md`, `.gitignore` — all are dev-discipline edits backing the binding; A2 admits them via the carve-out list (Q6) regardless of the sentinel.
- **Concurrent sub-component edits within scope.** A multi-component amendment (e.g. amendment #52 with `primary-persona` + `orchestrator`) authors a sentinel with TWO bindings: `(primary-persona, AC.A8.1)` AND `(orchestrator, AC.A8.A1)`. Both globs admit edits to their respective trees; A2's "any binding admits" rule (§1.2 step 4) handles multi-component amendments naturally.
- **Test fixtures under `tests/fixtures/`.** Per ODD §3.3 each AC gets a 1:1 test file; fixtures supporting them belong under the same component's tests/fixtures/ tree. The component's manifest rows must admit them (recommend a second glob `framework/<comp>/tests/**` per AC, or one shared `framework/<comp>/tests/fixtures/**` row admitted across all the component's ACs).

### 1.4 Why the gate is "objective-binding" not "scope-binding"

Three terms get conflated in the locked research:

- **Scope** is the dispatch unit (one plan-doc, one builder-agent run). One sentinel per active scope.
- **Objective** (in ODD's terminology, §1) is the named outcome. ACs are the deterministic-check leaves of an objective.
- **Binding** is the link from a file path → a specific AC.

A2 enforces **objective-binding** because it traces edits to ACs (the leaf), not to scopes (the dispatch unit). The active-scope sentinel is the indirection layer (one scope → 1+ bindings → 1+ paths via globs). This matters for the failure-mode taxonomy (§4) — "missing sentinel" is a scope-level failure; "binding doesn't admit path" is an AC-level failure; the gate must distinguish both in its diagnostic.

---

## 2. Firing layer — five candidates evaluated

The locked research §3.1 named `PreToolUse` matcher `Edit|Write` as the gate's surface. This research evaluates the deeper question: AT WHICH LAYER (which Claude Code event, which subagent boundary, which substrate-write moment) does the gate run? Five candidates evaluated.

### 2.1 Candidate A — `PreToolUse` matcher `Edit|Write|MultiEdit` (RECOMMENDED)

Hook fires immediately before each individual Edit / Write / MultiEdit tool call. Hook receives JSON envelope on stdin including `tool_input.file_path`. Hook returns JSON on stdout including `hookSpecificOutput.permissionDecision: "deny"` to refuse.

**Pros:**

- Claude-native primitive; documented and stable surface.
- Fires on every individual edit — even MultiEdit (one batched call may touch multiple files; matcher fires per-call, builder responsible for applying the same gate to each `edits[*].file_path` inside).
- Subagent-inheritance: project-level hooks apply to subagents automatically. Every dispatched build agent inherits A2 without per-agent wiring.
- Symmetric with the future A3 (TDD-guard) and A4 (Bash/Agent-context) — the same hook event class.

**Cons:**

- One-time per-call latency. Hook script must be sub-100ms; Python-stdlib-only is the discipline. (A1's sentinel readers are stdlib-only and fast; the manifest query is one SQLite call which is microseconds-scale; total target <50ms p95 per fire.)
- MultiEdit handling requires the builder to iterate `edits` array and apply the gate to each (the matcher fires once for the whole call; deciding to deny on any one path means denying the whole call).

### 2.2 Candidate B — `UserPromptSubmit` hook + persona-level enforcement

Inject the sentinel-check into the `UserPromptSubmit` flow (already in use by amendment #46's persona session-start emitter). The persona then refuses to dispatch / refuses to author edits when state-of-tree mismatches the sentinel.

**Rejected:**

- Advisory (relies on persona discipline) — exactly the failure mode A2 exists to eliminate. Per ODD §5.1 the gate must be structural, not "the persona will check." Promotes a relocate (rule moved to persona prompt) where elimination (the edit cannot fire without the binding) is available.
- Per-edit granularity is impossible — `UserPromptSubmit` fires once per turn, not per edit.

### 2.3 Candidate C — Per-component pre-commit hook (`pos-amend apply --dry-run` extension)

`pos-amend apply --dry-run`'s seal-diff invariant test catches diffs that escape the seal-diff window after the fact. Extend the dry-run to also verify each diff entry traces to a manifest row that the manifest-window's bindings admit.

**Rejected:**

- Catches violations at commit time, not at edit time. By then the builder has authored 50+ files; the deny is too late and the recovery cost is high. Same anti-pattern as `git commit -e` warnings vs PreToolUse refusals.
- Doesn't compose with the dispatch's run-loop (the pos-amend invocation is the LAST step; the gate should fire on the FIRST edit).
- Doesn't help amendments that haven't yet reached pos-amend (during build, before the first apply).

A2 still informs the pos-amend extension — the gate's audit-log is the data the dry-run could consult — but pos-amend is not the gate.

### 2.4 Candidate D — Subagent dispatch entry (Agent tool wrapper)

Wrap the `Agent` tool dispatch so every subagent dispatch carries an active-scope sentinel write before the subagent starts. The subagent inherits the sentinel; A2's PreToolUse hook applies to the subagent's edits.

**Pros (composes with A2-A, doesn't replace it):**

- Solves the "build agent forgot to author the sentinel" failure class structurally — the dispatch itself authors the sentinel.

**As an ALTERNATIVE to A2-A: rejected.** The wrapper authors the sentinel; the gate still has to refuse edits outside the binding, which is the per-edit decision A2-A owns. Use both — Agent-dispatch sentinel-author is an A2.adjacent amendment (or an A4 sub-feature), and A2-A is the gate that consumes the sentinel.

### 2.5 Candidate E — `SessionStart` validation only

Validate at session-start that a sentinel is present + binds to a real manifest row. Refuse the entire session if not.

**Rejected:**

- Too coarse. Sessions begin BEFORE a builder authors a plan; requiring a sentinel at session-start would deny session-bootstrap turns (the persona reads context, plans, dispatches a build — no sentinel until the builder agent runs).
- Doesn't refuse drift-edits during the session.

### 2.6 Recommendation: A (PreToolUse)

A is the canonical gate; D is its useful sibling for sentinel-authoring on dispatch (deferred to A4 / a separate amendment). A1 substrate is sufficient for A alone; D requires Agent-tool-dispatch wrapping that A8's `dispatch_with_scope` (already shipped in amendment #52) provides 80% of — the missing 20% is "active-scope sentinel write at scope-creation time" which is a small extension of A8 (out of scope for A2; flagged for A2.adjacent in §11).

---

## 3. Refusal mechanism — three candidates evaluated

### 3.1 Candidate α — `permissionDecision: "deny"` (Claude Code native)

Hook returns:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "<structured reason text>"
  }
}
```

The reason text is structured-natural-language: opens with the failure class, names the path, names what would have admitted it, names the repair. Example:

> ODD §2.5 — file `framework/cost-governance/src/wiring.py` has no objective binding. The active-scope sentinel binds (orchestrator, AC.O8.A1) whose globs are [`framework/orchestrator/src/**`, `framework/orchestrator/tests/**`]. To edit cost-governance: extend the active-scope sentinel via the dispatch wrapper, OR add a (cost-governance, AC.O8.A1, framework/cost-governance/src/**) row to the objective-manifest table, OR retry the edit on a path the sentinel binds to. To edit cost-governance INTENTIONALLY across components, halt and surface to the dispatcher.

**Recommended.** Native Claude Code surface; tested across the codebase via existing dev-mode-manifest tooling; structured + natural-language hybrid mirrors the audit-target's style.

### 3.2 Candidate β — `exit 2 + stderr`

Hooks can also signal refusal via exit code 2. Less structured; the reason text appears in stderr. **Rejected** for A2 — the hookSpecificOutput JSON is the documented structured surface.

### 3.3 Candidate γ — Allow-with-warning (`additionalContext` only)

Don't refuse; emit `additionalContext` instead so the model sees the warning but the edit proceeds.

**Rejected.** This is advisory in structural clothing (ODD §5.1 + §5.1.1 — the relocate-vs-eliminate test). The whole point of A2 is to make the edit unrepresentable without the binding. Warning is not refusal.

---

## 4. Failure-mode taxonomy

Five named failure modes the gate must distinguish + handle:

### 4.1 Missing active-scope sentinel (DEV MODE)

- **State:** `read_active_scope_sentinel(workspace_root)` returns `None`. Workspace-mode = `dev-mode`. Path is sealed-component source.
- **Cause:** dispatcher forgot to author the sentinel before dispatching the build agent. Or the builder is mid-bootstrap (planning) and the path is in carve-out (false alarm — reaches step 2 of §1.2 before this check).
- **Decision:** **deny.** Diagnostic names the missing sentinel + the carve-out alternative ("if this is a docs/plans/CLAUDE.md edit, retry on the carve-out path"). 
- **Caveat:** A2 should NOT auto-create the sentinel — that's the dispatch wrapper's job. Auto-creation hides the dispatcher-side failure.

### 4.2 Sentinel present but no manifest row for the bound `(component, ac_id)`

- **State:** `read_active_scope_sentinel` returns a sentinel binding `(X, Y)`; `manifest_rows_for_ac(X, Y)` returns `[]`.
- **Cause:** the dispatcher / builder authored a sentinel that names an AC the manifest doesn't yet know about. Most often happens when an amendment is mid-build and the manifest row for the new AC hasn't been registered yet (the builder is the natural row-registrar at AC-author time).
- **Decision:** **deny** with a clear diagnostic: "sentinel binds (X, Y) but no manifest row exists. Register a row via `tracker.register_source_binding(component=X, ac_id=Y, source_path_glob=...)` before the first edit."
- **Caveat:** A2 should NOT auto-register a row. The builder is the AC-author; the row is part of the build's authoring discipline.

### 4.3 Sentinel binds, manifest row exists, path doesn't match any glob

- **State:** `read_active_scope_sentinel` returns sentinel; sentinel's bindings have manifest rows; no row's `source_path_glob` matches `tool_input.file_path`.
- **Cause:** drift / scope-creep / wrong-component edit (§1.3 false-negatives).
- **Decision:** **deny.** Diagnostic names the path, the bound (component, ac_id) pairs, and the globs each binds to.

### 4.4 Sentinel is malformed / unreadable

- **State:** `read_active_scope_sentinel` returns `None` because of JSON-parse failure or partial-write race (§4.5 below).
- **Cause:** atomic-write race, manual sentinel edit gone wrong, FS corruption.
- **Decision:** **deny.** Diagnostic distinguishes "no sentinel" from "malformed sentinel" — the read API doesn't expose the difference, but A2 can stat the file: file exists + reader returns None ⇒ malformed.
- **Caveat:** an explicit `read_active_scope_sentinel_with_diagnostics` reader could expose a `MalformedSentinel` outcome; A1's reader API doesn't currently offer this, but the read-and-stat pattern is fine.

### 4.5 Race conditions

Three racey shapes considered:

- **Race A — Sentinel write mid-rename.** Atomic write via `.tmp` + `os.rename` (A1 contract; AC.SE.3 names "concurrent read while writer is mid-rename returns either pre-rename content or post-rename content"). A2's reader inherits this property — the gate sees pre or post, never partial.
- **Race B — Manifest write mid-query.** SQLite WAL mode (objective-tracker default); reads are isolated from concurrent writes. A2's queries return a consistent snapshot.
- **Race C — Workspace-mode bit flips mid-dispatch.** The mode bit is read from the persona contract YAML each time `workspace_mode()` is called. If the YAML changes mid-dispatch, the next gate fire sees the new value. Acceptable — mode flips are rare (manual operator action), and the gate is fail-safe in either direction (DEV MODE → enforce; NORMAL USE → allow).

None of the races introduce a soundness hole. The gate is consistent at each fire.

### 4.6 Mode-bit transitions mid-dispatch

Per Race C above. A2 does not need explicit handling; the next fire reads the current value. Documenting the behaviour in the diagnostic is sufficient ("if you just ran `loam-mode set normal-use`, this gate is now off").

---

## 5. Mode-aware refusal — UNIVERSAL vs DEV-MODE-only

D4 lock: ODD-discipline gates are DEV-MODE-only. A2 is ODD-discipline (objective-binding is the methodology's structural enforcement of §2.5). **A2 entirely no-ops in NORMAL USE.**

### 5.1 The reasoning chain

- A2's purpose is to enforce ODD §2.5 (every edit traces to a named AC). 
- ODD applies to pos-v2 dev work. Per `feedback_odd_cdc_scope` it does NOT apply to derived workspaces (pos3, eval clones).
- In a NORMAL USE workspace the user is doing arbitrary work — running scripts, editing docs, building unrelated software. There are no "ACs" to bind to.
- Therefore A2 must not fire there, and short-circuiting on the mode bit is the cheapest correct behaviour.

### 5.2 Are there A2 sub-cases that should be UNIVERSAL?

Considered three candidates; rejected all:

- **Edit/Write of `~/.ssh/`, `.env*`, credentials.** These are blast-radius (D4-universal) but they're A4 territory (Bash secret-file commit blocker). A2 is path-binding-by-AC; secret files are path-blocked-by-content-type. Different gate. **Reject.**
- **Write to a sealed-component source path in NORMAL USE.** Even in a derived workspace, edits to `<workspace>/framework/<sealed>/src/**` could break the workspace-sync invariant (D-migration). This is the FIDRAFT main-session-write-prevention rule (line 136). **Reject for A2.** This is A2.adjacent (a separate amendment); it's path-by-content-policy not path-by-AC-binding; it composes with A2's scaffold but uses different decision data.
- **Write outside the active-scope's plan path during plan-authoring.** Edits to plans/ files outside the active scope's plan (e.g. accidentally editing a sibling plan). **Reject.** Plans/ is a dev-discipline carve-out per D1; A2 doesn't gate it. The right amendment for plan-cross-contamination is a future linter, not A2.

**Conclusion: A2 entirely DEV-MODE-only.** No sub-cases warrant universal application.

---

## 6. Composition with FIDRAFT items

Three FIDRAFT items (newest entries at lines 130, 136, 143) compose with A2.

### 6.1 Corpus-inlining hook (FIDRAFT line 130)

The captured idea: SessionStart contributor reads the corpus files + emits content into `additionalContext`. A1 ships the corpus-load sentinel that records `state ∈ {loaded, partial, missing}`. The corpus-inlining hook would set `state = loaded` (because the content is in context).

**Composition with A2:**

- A2's gate consults the corpus-load sentinel as part of its diagnostic (when state ≠ "loaded", the deny reason names "and the session may not have loaded the required corpus — verify with `cat <workspace>/workspace/.pos/session-state/<session_id>.json`").
- A2 does NOT refuse for missing corpus. That's a separate gate (the locked research's "structural context-load gate" per FUTURE_IDEAS Idea 8) — A2 stays scoped to objective-binding.
- After the corpus-inlining hook lands, A2's diagnostic message stops mentioning corpus state (becomes implicit — the `additionalContext` always carries the corpus). A1's substrate already supports the composition; no A2 design impact.

### 6.2 Main-session-write-prevention (FIDRAFT line 136)

The captured idea: a hook that detects Edit/Write whose path falls under `<workspace>/framework/` and refuses (or redirects to the canonical equivalent). This addresses the wrong-tree-write failure class.

**Composition with A2:**

- The two gates have OVERLAPPING decision data (path + workspace context) but DISTINCT decision logic:
  - A2: "is this path in the binding glob?" — AC-shaped.
  - Main-session-write-prevention: "is this path in the workspace's framework mirror, regardless of binding?" — content-policy-shaped.
- They can share the PreToolUse hook script ENTRY-POINT (one script handles all PreToolUse Edit/Write fires), with branched decision logic. OR they can be separate scripts; Claude Code matchers admit multiple PreToolUse entries.
- **Recommendation:** keep them separate (one amendment each). Share a small library of helpers (carve-out detection, workspace-root resolution) in a non-fence module if both ship.
- A2 design must NOT preempt the main-session-write-prevention check — A2's deny diagnostic must not say "edit allowed" when the framework-write check would say "denied." If both are active, the main-session-write check should fire FIRST (cheaper; doesn't read the manifest); A2 second.
- Order: in the PreToolUse hook chain, framework-write-prevention is registered ahead of A2. If FIDRAFT-136 lands first as a separate amendment, A2 composes naturally. If A2 lands first, the future amendment slots in ahead.

### 6.3 Dispatch-staleness verification (FIDRAFT line 143)

The captured idea: PreToolUse hook on the `Agent` (Task) tool that grep's the dispatch prompt for "amendment <NUM>" or "AC.<X>.<Y>" patterns, diff against canonical's seal commits, flag re-targeting.

**Composition with A2:**

- Dispatch-staleness operates on `Agent` tool calls; A2 operates on `Edit|Write|MultiEdit`. Different matchers, different fire surfaces — they don't conflict.
- A2's audit log (every gate decision: allow / deny + reason + path + bindings) is the data the dispatch-staleness hook consults to detect "this dispatch references an AC that has manifest rows from a sealed amendment." A2 ships the substrate; staleness is downstream consumer.
- **Recommendation:** A2 ships an audit log (NDJSON `<workspace>/workspace/.pos/objective-binding-gate.log` mirroring amendment #48 D8's diagnostic-log pattern). Dispatch-staleness consumes it. No A2 design impact beyond shipping the log.

### 6.4 Composition summary

A2 is the FIRST gate; its substrate (audit log + sentinel-read pattern + carve-out helper) is reusable by every subsequent PreToolUse gate. The plan-shape A2 establishes (single-script-with-helper-library, fail-closed-with-bypass, ndjson-audit-log) is the precedent for A3 and A4.

---

## 7. Migration / coexistence with already-active sessions

When A2 lands, sessions in flight have no active-scope sentinel. The first PreToolUse Edit fire in a DEV MODE session post-A2-deploy faces:

- Active-scope sentinel: absent (`read_active_scope_sentinel` returns `None`).
- Path: presumably under a sealed-component source tree.
- Decision under §1.2 step 3: deny.

This is fail-closed — the right behaviour for an opt-in safety mechanism, but it would refuse every edit in every existing dev session until the session's persona / dispatcher authors a sentinel.

### 7.1 Three migration shapes considered

- **Shape α — Hard cutover.** A2 lands; existing sessions break until they author sentinels. Operator pain ~1 session-restart per workspace.
- **Shape β — Soft cutover.** A2 lands with a "grace period" mode (from settings / env var) that downgrades deny → log-only-allow for the first N days. Easy to forget to flip off; advisory in clothing.
- **Shape γ — Fail-safe-to-allow on missing sentinel for first session post-deploy.** Detect "no sentinel exists in this workspace at all" (vs "sentinel exists but binds wrong AC") and allow with a warning the first time. Requires state tracking ("we already warned this workspace once") which is its own substrate.

**Recommendation: α (hard cutover) with a documented "how to author a sentinel" diagnostic in the deny reason.** The deny diagnostic names the exact `pos-amend` / dispatch wrapper command that authors a sentinel for the current dispatch. Operator pain is one diagnostic-read per existing session. Soft cutover is rule-shaped (relocate-not-eliminate); fail-safe-to-allow needs its own substrate.

### 7.2 First-time bootstrap of the sentinel for the dispatcher persona

When the primary persona session starts in a fresh workspace, there's no sentinel. The persona is in PLANNING mode, not BUILDING mode — its first edits are typically docs/plans/ which are carve-out-bypass. The first SOURCE edit happens after a build dispatch lands; the dispatch wrapper (a future amendment) authors the sentinel as part of dispatch.

**Implication for A2:** the gate's carve-out (D1) covers planning-mode work — `docs/`, `tools/`, `CLAUDE.md`, `personas/`, `.scratch/`. These are 95%+ of main-session edits. The remaining 5% (main-session direct source edits) should be rare and intentional; per `feedback_session_start_discipline` the right shape is "main-session goes to dispatch agents for source work." A2 enforces this structurally — main-session source edits without a sentinel are denied.

This is a feature, not a bug. Per the locked research: A2 makes the rule-in-memory ("dispatch source work to agents") structural.

---

## 8. Design-decision register (for the plan)

The seven design decisions §1–§7 surface, with recommendations:

| ID | Question | Recommendation | Open / Locked |
|---|---|---|---|
| D1 | Firing layer | Candidate A — `PreToolUse` matcher `Edit\|Write\|MultiEdit` (§2.6) | Open for owner ruling |
| D2 | Refusal mechanism | Candidate α — `permissionDecision: deny` + structured `permissionDecisionReason` (§3.1) | Open for owner ruling |
| D3 | Default on missing sentinel (DEV MODE) | Deny with diagnostic naming carve-out alternative (§4.1) | Open for owner ruling |
| D4 | Default on missing manifest row | Deny with diagnostic naming registration command (§4.2) | Open for owner ruling |
| D5 | DEV-MODE / UNIVERSAL split | Entirely DEV-MODE-only (§5.2) — programme-D4 lock subsumes this | Locked by programme D4 |
| D6 | Carve-out path list (D1 dev-discipline) | `docs/`, `tools/`, `CLAUDE*.md`, `.scratch/`, `personas/`, plus `.gitignore` and the universal-paths admissions (`docs/odd-methodology.md`, `docs/odd-in-pos.md`, `docs/FUTURE_IDEAS.md`, etc.) (§1.2 + §6.4) | Open for owner ruling — recommendation matches programme D1 |
| D7 | Migration shape | α — Hard cutover with diagnostic-named-repair (§7.1) | Open for owner ruling |
| D8 | Audit log shape | NDJSON at `<workspace>/workspace/.pos/objective-binding-gate.log` mirroring amendment #48's `dispatch-wrapper.log` pattern (§6.3) | Open for owner ruling — method-shaped; flagged for builder per ODD §7.4 |

Owner is asked to rule on D1, D2, D3, D4, D6, D7. D5 is locked by programme D4. D8 is method per ODD §7.4 (the builder may refine the log path / format if a sibling amendment standardises a different shape).

---

## 9. Sealed-component fence + halt triggers

### 9.1 Fence

A2 is a hands-off-lifecycle amendment. The objective-binding gate is a SessionStart-style hook script under `framework/hands-off-lifecycle/hooks/objective_binding_gate.py` (new file) plus the wiring that registers it as a `PreToolUse` hook in the merged settings.json (extension to `first_run_settings.py` mirroring the existing `merge_user_prompt_submit` pattern at line 405).

**Single sealed component:** `hands-off-lifecycle/`. `objective-tracker/` is consumer-only (A2 only calls A1's public read API; no schema or runtime change). `loam-mode/`, `tools/pos-amend/`, etc. are dev-discipline (untouched).

A2's seal-diff window ⊆ `hands-off-lifecycle/{hooks,tests,seals}/` plus the universal-paths admissions.

### 9.2 Halt triggers

A2 build halts on:

1. **A1 substrate gap.** Any A1-substrate field A2 needs that A1 didn't ship → halt. (Section §1.1's table is the contract.)
2. **PreToolUse merge mechanism missing.** The existing `first_run_settings.py` covers SessionStart + UserPromptSubmit. PreToolUse may need a parallel `merge_pre_tool_use` function. If `first_run_settings.py`'s merge surface cannot accept the new entry without contract change → halt; A2 needs an A1.1 corrective on hands-off-lifecycle's merge surface OR a substrate amendment.
3. **MultiEdit semantics ambiguity.** Claude Code's `MultiEdit` tool batches edits; the matcher fires once but the `tool_input` carries an `edits` array. If the JSON shape forces A2 to make per-edit decisions inside a single hook fire (i.e. there's no way to deny just one of the edits), halt and surface — that's a Claude Code surface-level question and a design decision Luke must rule on.
4. **Existing PreToolUse hook collision.** If a workspace already has a user-authored PreToolUse hook (the `merge_pre_tool_use` precedent: amendment #46's UserPromptSubmit merge backs the prior hook into `_USER_AUTHORED` state), A2's hook must not silently displace it. Halt-and-surface if the merge would lose user state.

### 9.3 Architecture-creep watch

The design space surfaces one deeper question: **should A2's hook be ONE entry point that A3 + A4 extend (multi-tenant gate framework), or N separate hooks (one per amendment)?**

The locked programme research §6.2 implies one-hook-per-amendment. A2's research recommends staying with that — each gate amendment is a separate `PreToolUse` matcher entry. Claude Code admits multiple matchers for the same event; the per-amendment isolation makes seal-diff windows clean.

Counter-argument: a single multi-tenant gate framework could share helper code (carve-out detection, mode-bit query, sentinel reader, audit log), which is a real concern. Resolution: ship the helpers as a small NON-fence library at `framework/hands-off-lifecycle/hooks/_gate_helpers.py` (or similar — method, builder's call) that both A2 and the future A3/A4 import. Each amendment's `objective_binding_gate.py` / `tdd_guard.py` / `bash_context_guard.py` is its own thin script importing the shared helpers. This composes WITHOUT a meta-framework.

**Conclusion: stay with per-amendment hooks; ship a shared helper library on first amendment landing (A2). No architecture creep.**

---

## 10. ODD self-check on the proposed AC set

This section runs the ODD methodology §8.1 checks against the AC set the plan-doc will author. Behaviour-count match, halt trigger, constraints, fail-closed direction, §2.5 reverse-direction.

### 10.1 Acceptance criteria the plan will declare

(Pre-authored here so the §8.1 check is grounded; the plan §4 reproduces them.)

- **AC.OBG.1 — Gate refuses Edit on sealed-component source with no active-scope sentinel (DEV MODE).** Hook fires on `PreToolUse Edit|Write|MultiEdit`; mode = `dev-mode`; path = sealed-component source; sentinel absent → returns `permissionDecision: "deny"` with a structured reason naming the missing sentinel and the carve-out alternatives.
- **AC.OBG.2 — Gate refuses Edit when sentinel binds an AC with no manifest row.** Sentinel present; bound `(component, ac_id)` has zero `manifest_rows_for_ac` → deny with diagnostic naming the missing row and the registration command.
- **AC.OBG.3 — Gate refuses Edit when no manifest-row glob matches the path.** Sentinel present, manifest rows present, no row's glob matches `tool_input.file_path` → deny with diagnostic naming all bound globs and the path.
- **AC.OBG.4 — Gate allows Edit when path matches at least one bound manifest-row glob.** Sentinel present, manifest row exists, at least one glob `fnmatch.fnmatchcase`-matches the path → returns no `hookSpecificOutput` (default-allow) or explicit `permissionDecision: "allow"`.
- **AC.OBG.5 — Gate allows Edit on dev-discipline carve-out paths regardless of sentinel state.** Path under `docs/`, `tools/`, `CLAUDE*.md`, `.scratch/`, `personas/`, `.gitignore`, or other carve-outs → allow regardless of sentinel/manifest state.
- **AC.OBG.6 — Gate is a no-op when workspace-mode is `normal-use`.** Mode = `normal-use` → allow regardless of sentinel/manifest/path. Hook completes without consulting sentinel or manifest (cheap path).
- **AC.OBG.7 — Gate audit log is written deterministically.** Every gate fire (allow + deny) appends one NDJSON line to `<workspace>/workspace/.pos/objective-binding-gate.log` with `{ts, file_path, mode, sentinel_state, bound_acs, decision, reason}`. Append-only; non-rotating in A2 (rotation deferred to a future amendment).
- **AC.OBG.S — Seal-diff confined to fence.** A2's seal-diff window contains only edits under `hands-off-lifecycle/{hooks,tests,seals}/` and the universal-paths admissions.

### 10.2 §8.1 authoring-time violation checks

| Check | Pass / Fail |
|---|---|
| §8.1.1 Method in acceptance | PASS — every AC is outcome-shaped. "Returns `permissionDecision: deny`" is a Claude Code surface contract, not a method choice; the gate's INTERNAL structure (decision tree, validator shape, helper-library use) is unspecified. |
| §8.1.2 Behaviour-count match | 7 AC behaviours + 1 invariant = 8. Behaviours declared in §10.1: 7 (deny-no-sentinel, deny-no-row, deny-no-glob-match, allow-glob-match, allow-carveout, no-op-normal-use, audit-log) + S = 8. **PASS — match.** |
| §8.1.3 Missing acceptance | PASS — every behaviour has an AC. |
| §8.1.4 Acceptance relies on judgment | PASS — every AC is mechanical. "Hook returns deny JSON" is testable; "diagnostic names the missing sentinel" tests via substring in the reason text. |
| §8.1.5 Procedure in objective | PASS — no "first X then Y" in any AC. |
| §8.1.6 Unbounded scope | PASS — §5 hard constraints fence the surface (single sealed component, no method-of-decision-tree, no schema/runtime change to A1). |
| §8.1.7 Missing halt trigger | PASS — §8.2 plan-doc names halt triggers explicitly. |

### 10.3 §2.5 reverse-direction (forward-only at plan-author time; full reverse is the builder's audit)

Plan-author confirms each declared behaviour (§10.1) maps to exactly one AC. The builder's reverse-direction audit (every code path / branch / dependency / test in the diff traces back to an AC) is named in the plan's halt triggers.

### 10.4 Constraint completeness

Per ODD §2.2 the five constraint shapes:

- **Budget:** PreToolUse hook < 100ms p95 (matches A1's SessionStart inner-hook envelope; tighter because PreToolUse fires per-edit). Audit-log append is microseconds. Total target < 50ms.
- **Reversibility:** fully reversible. The hook is additive; an existing settings.json without the entry continues to work; removing the entry restores prior behaviour.
- **Dependency fence:** stdlib-only-plus-loam-mode. Imports from `objective-tracker.runtime` (public read API), `hands-off-lifecycle.hooks.active_scope_sentinel`, `hands-off-lifecycle.hooks.corpus_load_sentinel.workspace_mode`. No new third-party dependency.
- **Authority bound:** A2 may not amend `objective-tracker` schema, may not amend A1's sentinel JSON shape, may not amend `loam-mode`'s mode-bit interface. Read-only against all three. Single sealed component touched: `hands-off-lifecycle/`.
- **Fail-closed direction:** deny on missing sentinel (DEV MODE). The DENY direction is fail-closed; the NORMAL-USE direction is fail-open (mode short-circuit). Matches D4.

All five present.

---

## 11. Open questions (research-time)

Items the plan can defer to the builder OR that surface for separate research.

### Q1 — MultiEdit semantics

Claude Code's `MultiEdit` tool batches edits into one tool call. The matcher fires once; the JSON envelope carries `edits: [{file_path, ...}, ...]`. A2's gate must apply to EVERY entry in `edits`. The Claude Code surface for partial-deny in MultiEdit is unclear from documentation alone.

**Recommendation:** the builder verifies during build by reading current Claude Code hook docs + testing on a real MultiEdit invocation. If MultiEdit cannot be partially-denied, A2's behaviour is "deny the whole MultiEdit if any edit fails the gate." That's the cheapest correct shape; the builder records the verification outcome in §14.

### Q2 — Audit log rotation

A2 ships an append-only NDJSON log. Long-running workspaces will accumulate; one row per Edit fire times session-count is a non-trivial volume.

**Recommendation:** rotation is OUT OF SCOPE for A2. A future maintenance amendment (or a generic JSONL rotation primitive) handles it. Same shape as A1's session-state-sentinels-accumulate finding (R4 on A1 plan).

### Q3 — Sentinel-author dispatcher integration

The amendment that wraps `Agent` tool dispatches to author the sentinel automatically (Candidate D in §2.4) is a separate amendment. **A2 ships the gate; sentinel authoring is the dispatcher's job.** During the migration period (between A2 landing and the dispatcher-wrapper landing), every sealed-component edit needs a manually-authored sentinel.

**Recommendation:** flag for a follow-on (A2.adjacent or A4 sub-feature). Compose with amendment #52's existing dispatch wrapper — extend it to write the sentinel at scope-activation time. Shape: tiny addition to `framework/primary-persona/src/dispatch_wrapper.py` calling `write_active_scope_sentinel(...)` at the same time it calls `activate_scope_with_spec`. Not in A2's fence.

### Q4 — Existing canonical edits in flight when A2 lands

When A2 seals, the seal commit itself is an Edit/Write to `framework/hands-off-lifecycle/`. The sealing process must NOT trigger A2's gate against itself (chicken-and-egg). Two resolutions:

- The seal-commit edits land via `pos-amend seal --plan-doc` which uses git operations, not the Claude Code Edit tool. PreToolUse hooks do not fire on git operations. **Resolution: not actually a problem.** The build-time Edits do fire the gate; the build-agent's active-scope sentinel covers them.
- The build-agent's sentinel binds `(hands-off-lifecycle, AC.OBG.x)`; manifest rows for those ACs admit `framework/hands-off-lifecycle/{hooks,tests,seals}/**`. Self-bootstrap works.

**Recommendation:** the build-agent registers manifest rows AS PART OF the build (at AC-author time) before the first source edit. The build dispatch's first action: `register_source_binding` for each AC in this amendment. A2's hook then admits the build's own edits.

This is the canonical shape for every future gate amendment — the build agent registers its own AC manifest rows at build-start.

---

## 12. Cross-references

- Locked research (governs): `docs/plans/research/structural-enforcement-of-critical-requirements-research.md`
- A1 plan (locked, sealed): `docs/plans/structural-enforcement-a1-substrate.md`
- A1 builder plan (records D-build choices): `docs/plans/structural-enforcement-a1-substrate.builder-plan.md`
- A1 substrate code (read-only inputs):
  - `framework/objective-tracker/src/store.py` (manifest table CRUD)
  - `framework/objective-tracker/src/runtime.py` (public API: `register_source_binding`, `manifest_rows_for_*`)
  - `framework/hands-off-lifecycle/hooks/active_scope_sentinel.py` (reader contract)
  - `framework/hands-off-lifecycle/hooks/corpus_load_sentinel.py` (workspace-mode bit)
- ODD methodology: `docs/odd-methodology.md` (§5.1 structural-over-advisory; §5.1.1 relocate-vs-eliminate test; §8.1 authoring-time violations)
- ODD-in-pos: `docs/odd-in-pos.md` (§10.3 per-invariant-baseline pattern — relevant for A2's seal-diff invariant test)
- VALUE_PROPOSITION: `docs/VALUE_PROPOSITION.md` (AC.PO.1 + AC.PO.2 — A2's Lens 2 anchor)
- FUTURE_IDEAS: `docs/FUTURE_IDEAS.md` Idea 1 (programme), Idea 8 (structural context-load gate — A2.adjacent)
- FIDRAFT items: `docs/FUTURE_IDEAS_DRAFT.md` lines 130 (corpus-inlining), 136 (main-session-write-prevention), 143 (dispatch-staleness)
- Sibling plan-doc shape: `docs/plans/structural-enforcement-a1-substrate.md` (the immediate precedent for A2's plan structure)
- Claude Code hooks docs: https://code.claude.com/docs/en/hooks (PreToolUse decision-control surface; matchers; permissionDecision; permissionDecisionReason)

---

*End of research artefact. Plan-doc at `docs/plans/structural-enforcement-a2-objective-binding-gate.md` consumes these findings.*
