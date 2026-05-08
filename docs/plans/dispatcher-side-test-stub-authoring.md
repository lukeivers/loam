# Plan — dispatcher-side test-stub authoring

**Status:** plan-doc only (no code, no commits, no manifest yet). 2026-04-28.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Sibling research artefact (governs):** `docs/plans/research/dispatcher-side-test-stub-authoring-research.md`.
**Programme position:** follow-on amendment after the four-amendment structural-enforcement programme (A1 #51, A2 #70, A3 #71, A4 #72) + amendment #52 (A8 dispatch wrapper) + amendment #73 (corpus inlining). Composes; no programme amendment.
**Pre-flight verification (mandatory; per `feedback_verify_dispatch_before_sending` + brief):** pre-build dispatch verifies `git log --grep="test-stub|test.stub|dispatch.*stub|dispatcher.*stub"` returns only the FIDRAFT-capture commit `9b928c8` (no implementation commit), AND `ls docs/plans/ | grep -iE "test.stub|dispatch.*stub"` returns nothing matching this slug other than this plan-doc + its sibling research. Halt-and-surface if either does.

---

## 1. Summary / TLDR

Extend amendment #52's `dispatch_with_scope` (the persona-side Agent-dispatch wrapper) so that on a BUILD dispatch declaring NEW acceptance criteria, the wrapper authors three artefacts on disk BEFORE invoking the agent:

1. The active-scope sentinel (`<workspace>/workspace/.pos/active-scope.json`) binding the dispatched agent to the (component, ac_id) pairs declared in the dispatch.
2. One manifest row per (component, ac_id, source_path_glob) triple via A1's `tracker.register_source_binding(...)`.
3. One placeholder test file per (component, ac_id) at `framework/<component>/tests/test_AC_<NORM>_placeholder.py` containing `def test_AC_<NORM>_placeholder(): pytest.skip("stub authored by dispatcher; ...")`.

The sentinel write is sequenced FIRST so manifest-row `created_at` lands strictly after sentinel `created_at` (A3's "new AC in this diff" predicate, AC.TDG.4). All three steps are idempotent (sentinel: byte-equal-skip; manifest: idempotent on duplicate; stub: byte-equal-skip + skip-when-already-authored). All three are fail-soft (failure logs to the existing dispatch-wrapper diagnostic NDJSON, dispatch continues; gate refusal at A2/A3 surfaces the substrate failure to the operator). DEV-MODE only (parity with A2/A3 mode partition).

After this lands, a build dispatch carrying `new_acs=(NewACSpec(...), ...)` against a sealed plan-doc has the agent's first turn fully set up: sentinel admits binding (A2 passes), manifest row admits source path (A2 passes), test stub admits AC pinning (A3 passes), corpus inlined (#73). The agent's first edit is a real source edit — not a setup edit. Three classes of round-trip failures (no-scope, no-test, wrong-test-name) move from "agent halts, dispatcher re-fires" to "doesn't happen."

The shape applies cleanly to BUILD dispatches; research+plan dispatches (which AUTHOR ACs as output) pass `new_acs=()` and the dispatcher skips the setup phase entirely. This is structurally correct: research+plan dispatches edit only universally-admitted paths (`docs/plans/`), where A2/A3 carve-outs apply.

**Sealed-component fence:** `primary-persona/` (the dispatch_wrapper module + its public surface) PLUS optional small consumer-only reads on `objective-tracker/` (calling A1's public manifest API) and `hands-off-lifecycle/` (calling A1's public sentinel API). The two consumer dependencies are READ/WRITE on PUBLIC seal-stable APIs, not source edits to those components — the fence is single-component (primary-persona) modulo the universal-paths admissions.

Per CLAUDE.md output convention, owner reads from §6 (decisions for owner) — every other section supports it.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5)

**Named spec objectives this amendment satisfies:**

- **`docs/spec/pos-v2-objectives-spec.md` line 134–135 — Deterministic (tiered).** Same binding A1 + A2 + A3 satisfied. A2/A3's gates surface lint failures; this amendment's setup-at-dispatch step ensures the gates DON'T fire on the happy path because the conditions they check are pre-satisfied. The lint surface stays observable; the lint is only triggered when the dispatcher's setup truly fails or when the agent goes off-pattern.
- **VALUE_PROPOSITION's two tests (the prime objective ACs).**
  - *Primary-persona test (AC.PO.1):* the persona's translation toolkit no longer carries "remember to register manifest rows + write sentinel + author stubs as the first three actions of every build dispatch." The dispatcher does it. Reduces translation burden directly across A1+A2+A3's substrate concerns.
  - *Harness test (AC.PO.2):* the dispatch wrapper gains a setup-phase primitive that every future dispatch contributor (scheduled routines, retry loops, multi-build orchestrators) composes against. The setup phase is reusable.

**Sealed-component fence:**

- `primary-persona` — single sealed component edit. Extension of `dispatch_wrapper.py` to author setup artefacts. New helper(s) for stub-content rendering + idempotent stub writing. Tests added.
- `objective-tracker` — consumer-only. Calls existing `register_source_binding` and `manifest_rows_for_ac` (A1 public APIs). No schema or runtime change.
- `hands-off-lifecycle` — consumer-only. Calls existing `write_active_scope_sentinel` (A1 public API). No source change.

**ODD §2.5 reverse direction.** Every code path, branch, dependency, and test in this amendment's diff traces back to a named AC under §4. No silent branches; no defensive `if`s without backing AC. Idempotency-and-overwrite-skip logic traces to AC.DSA.4; failure-mode logic traces to AC.DSA.5; stub-shape logic traces to AC.DSA.2.

---

## 3. Three-lens analysis

### Lens 1 — Claude leverage

*Required research question: what Claude capability does this lean on or extend?*

This amendment is a CONSUMER of two Claude-adjacent surfaces:

1. **Claude Code's `Agent` tool (Task) dispatch.** This amendment extends the persona-side wrapper around `Agent` calls; the wrapper exists today (amendment #52). No re-implementation of dispatch.
2. **Claude Code's `PreToolUse` hook surface (composed by A2 + A3 + A4).** The dispatcher's setup step makes the gate evaluations a no-op on the happy path. The gates remain Claude-native; the dispatcher precondition them.

The asymmetric finding from the locked structural-enforcement programme research §7.1 — *"Claude Code's hook surface IS the structural-enforcement surface"* — applies here as a corollary: *the dispatch wrapper is the structural-precondition surface.* Setup at dispatch time is the natural composition of the wrapper + the gates: gates enforce, wrapper precondition. This amendment formalises the composition.

### Lens 2 — Harness + primary-persona value

*Primary-persona test: does this reduce the translation burden between the user's natural-language intent and AI-effective execution?*

**Yes — direct, load-bearing reduction.** The persona currently dispatches a build, the build agent halts twice (no scope; no test for new AC), the persona reads the deny diagnostic and re-dispatches with corrected setup. After this amendment, the persona's dispatch shape carries `new_acs=(NewACSpec(...), ...)` once; the wrapper does the setup; the agent's first edit succeeds. The translation burden of "remember the substrate steps" moves from the persona's prompt context into the wrapper's code path.

*Harness test: does this add to the toolkit the primary persona can draw from?*

**Yes — three new toolkit primitives:**

1. The `NewACSpec` dataclass on `DispatchShape`: a reusable shape for declaring new ACs in a dispatch. Future dispatch contributors (scheduled routines, retry loops) compose against this shape.
2. The dispatcher's setup-phase pattern: a precedent for adding more pre-dispatch setup steps as future amendments need them (e.g., a future "register persona-narration template" step).
3. The `_render_stub` + `_write_stub_idempotent` helpers: reusable for any future amendment that needs to author a placeholder test file (e.g., a hypothetical "test-deletion gate" amendment that re-authors a stub when a test is deleted).

Both Lens 2 tests pass. **→ AC.PO.1 + AC.PO.2.**

### Lens 3 — ODD authoring

This amendment is structurally shaped, not advisory. Setup is deterministic — same dispatch shape + same workspace = same artefacts on disk. The gates remain the structural enforcement; the dispatcher's setup is a productivity primitive. Every AC below is outcome-shaped (no "the implementation will use X" language). Method (exact field names on `NewACSpec`, exact stub body byte-for-byte, exact ordering of writes within the setup phase, exact diagnostic NDJSON keys) is the builder's call and lives in the builder plan.

ODD §5.1.1 (relocate-vs-eliminate test): this amendment ELIMINATES the round-trip failure class for the named cases (no-scope, no-test, wrong-test-name). A future change cannot re-introduce the round-trip without active discipline (i.e., without removing this setup phase from the wrapper).

ODD §4 alignment: this amendment composes with the §4 re-extension flow. Mid-build AC re-extension still requires the build agent to register the new manifest row + author the test (per §4 protocol); the dispatcher's role is at dispatch-start only, not mid-build. The boundary is clear.

---

## 4. Acceptance criteria

Each AC is outcome-shaped. Forward behaviour-count check below. ODD §2.5 reverse direction is the builder's pre-seal audit (restated as halt-and-signal trigger in §8).

### AC.DSA.1 — DispatchShape extension carries new_acs

Given the existing `DispatchShape` (amendment #52), the dispatch wrapper accepts an optional `new_acs` field whose value is a tuple of (component, ac_id, source_path_glob) triples. When omitted or empty, the dispatcher does not author setup artefacts. When non-empty, the dispatcher proceeds with setup per AC.DSA.2 / AC.DSA.3 / AC.DSA.4.

### AC.DSA.2 — Stub content shape (skip-with-reason)

For each `(component, ac_id, source_path_glob)` in `new_acs`, the dispatcher writes a file at `<workspace_root>/framework/<component>/tests/test_AC_<NORM>_placeholder.py` whose content (a) defines a function whose name starts with `test_AC_<NORM>_` (matching A3's `_function_prefix(ac_id)`), (b) the function's body invokes `pytest.skip(...)` with a reason naming the dispatcher as author and the AC ID as the replacement target, (c) the file is otherwise minimal (module docstring + import + function definition; no fixtures, no class scaffolding). The stub registers as `skipped` (not `passed`, not `failed`) in pytest output.

### AC.DSA.3 — Setup sequencing for A3 "new AC" predicate

For each dispatch with non-empty `new_acs`, the dispatcher writes the active-scope sentinel STRICTLY BEFORE registering manifest rows. Outcome: every manifest row's `created_at` is strictly after the sentinel's `created_at`, satisfying A3's `manifest_row.created_at > sentinel.created_at` "new AC in this diff" predicate (A3 AC.TDG.4 / D-A3.4).

### AC.DSA.4 — Idempotency

For each artefact (sentinel, manifest row, stub file), repeated dispatcher invocations with the same dispatch shape do not corrupt existing on-disk content. Specifically: a re-dispatch with the same `new_acs` finds existing artefacts and either no-ops on byte-equal content (sentinel, stub) or no-ops on duplicate row (manifest). When a stub file already contains a function whose body is NOT the dispatcher's skip-with-reason (i.e., the build agent already authored the real test), the dispatcher does NOT overwrite — it logs a structured diagnostic and proceeds.

### AC.DSA.5 — Fail-soft on substrate failure

When any setup step fails (sentinel write returns `wrote=False, reason="failed-*"`; `register_source_binding` raises; stub write raises OSError), the dispatcher records a structured NDJSON diagnostic to `<workspace>/workspace/.pos/dispatch-wrapper.log` (the existing diagnostic surface from amendment #52 D8) and PROCEEDS with the dispatch. Setup failure does NOT cause the dispatcher to return early or refuse the dispatch; the gates (A2/A3) provide the structural enforcement and surface the failure to the operator at first-edit time.

### AC.DSA.6 — DEV-MODE-only

The dispatcher's setup phase fires only when the workspace is in DEV MODE (per the workspace mode bit consumed by A1/A2/A3 — same source). In NORMAL USE workspaces, the dispatcher does not write the sentinel, does not register manifest rows, does not author stubs (regardless of `new_acs`). Outcome: the wall-clock cost of the setup phase in NORMAL USE is bounded by the mode-bit read alone (sub-10ms; matches A2 AC.OBG.6 envelope).

### AC.DSA.7 — Setup precedes activate_scope_with_spec

In the wrapper's execution sequence, the setup phase (sentinel + manifest + stubs) runs strictly before the IPC call to `activate_scope_with_spec` (amendment #52 AC.A8.A1). On gate-chain refusal at activate_scope_with_spec, the setup artefacts persist on disk (skipped placeholder tests + manifest rows + sentinel). Subsequent dispatches benefit from idempotency (AC.DSA.4); the operator observes the gate refusal and the audit-trail of attempted-setup via the diagnostic log.

### AC.DSA.8 — Build dispatch with declared new_acs sails through A2 + A3 (composition)

Given a dispatch with `new_acs = ((comp_X, AC.X.1, source_path_glob), ...)` against a workspace where A2 + A3 are installed and DEV MODE is active, after the dispatcher's setup phase completes, evaluating A2's `objective_binding_gate.evaluate(...)` against a hypothetical Edit at any path matching the registered glob returns ALLOW, and evaluating A3's `tdd_guard.evaluate(...)` against the same hypothetical Edit returns ALLOW. (Composition test: the dispatcher's setup is correct WHEN both gates report ALLOW post-setup.)

### AC.DSA.9 — Diagnostic surface for setup-phase observability

Every setup-phase fire (success or failure for sentinel, manifest, each stub) emits a structured NDJSON record to the existing `<workspace>/workspace/.pos/dispatch-wrapper.log` surface. The recorded data is sufficient to reconstruct: when the setup fired, which artefact was authored / failed, the AC IDs in scope, the resolved file paths, and (on failure) the reason class. Format and exact field names are method per ODD §7.4.

### AC.DSA.10 — Backwards-compat with amendment #52 callers

Existing callers of `dispatch_with_scope` that omit `new_acs` (i.e., every caller authored before this amendment) observe identical behaviour to the pre-amendment wrapper. AC.A8.1 – AC.A8.S (amendment #52) all remain green. The `DispatchShape` field is keyword-only with a default of `()` so structural compatibility is preserved.

### AC.DSA.S — Seal-diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` shows only paths under: `framework/primary-persona/src/`, `framework/primary-persona/tests/`, `framework/primary-persona/pyproject.toml` (if dependency add needed; expected: no add — pytest is already a test dep), and the universal-paths admissions (`docs/plans/`, `CLAUDE.md`, `docs/odd-in-pos.md`, `docs/odd-methodology.md`, `docs/FUTURE_IDEAS.md`, `docs/FUTURE_IDEAS_DRAFT.md`). Anything outside this set is a halt condition.

### 4.x — Behaviour-count check (forward)

| #  | Declared behaviour                                             | AC          |
| -- | -------------------------------------------------------------- | ----------- |
| 1  | DispatchShape extension carries `new_acs`                       | AC.DSA.1    |
| 2  | Stub content shape: skip-with-reason                            | AC.DSA.2    |
| 3  | Sentinel before manifest (A3 predicate sequencing)              | AC.DSA.3    |
| 4  | Idempotent setup; respect agent-authored content                | AC.DSA.4    |
| 5  | Fail-soft on substrate failure                                  | AC.DSA.5    |
| 6  | DEV-MODE-only                                                   | AC.DSA.6    |
| 7  | Setup precedes activate_scope_with_spec                         | AC.DSA.7    |
| 8  | Composition: build dispatch with new_acs sails through A2+A3    | AC.DSA.8    |
| 9  | Diagnostic surface for setup-phase observability                | AC.DSA.9    |
| 10 | Backwards-compat with amendment #52 callers                     | AC.DSA.10   |
| cross-cutting | Seal-diff window respected                          | AC.DSA.S    |

10 behaviours, 11 ACs (one cross-cutting). No method-in-AC.

---

## 5. Hard constraints

1. **No `--amend`.** Corrective commits only (per `feedback_no_amend_in_agent_dispatches`).
2. **Scope fence.** Source edits land under `framework/primary-persona/{src,tests}/`. Universal-paths admissions per §10. Any edit elsewhere is a halt trigger (§8).
3. **A1 substrate is sealed.** No edits to `framework/objective-tracker/` (consumer-only of `register_source_binding`, `manifest_rows_for_ac`). No edits to `framework/hands-off-lifecycle/hooks/active_scope_sentinel.py` (consumer-only of `write_active_scope_sentinel`).
4. **A2 + A3 substrate is sealed.** No edits to `objective_binding_gate.py`, `tdd_guard.py`, or `_gate_helpers.py`. The dispatcher's setup uses the public APIs A1 ships; A2/A3 are read by the composition test (AC.DSA.8) but their source is untouched.
5. **Amendment #52 surface preserved.** AC.A8.1 – AC.A8.S remain green (AC.DSA.10). The `dispatch_with_scope` public callable signature accepts the new field as a keyword-only default; no existing caller breaks.
6. **Reversibility.** Fully reversible. The new setup phase is additive (callers that don't supply `new_acs` get unchanged behaviour); removing the field default and the setup phase restores prior behaviour.
7. **Budget.** Setup phase wall-clock target: < 50ms p95 in DEV MODE for typical N=5 ACs (sentinel write microseconds; manifest insert sub-millisecond; stub writes microseconds × N). NORMAL USE branch < 10ms (mode-bit read only). Dispatch wrapper's overall budget (with setup) stays under amendment #52's < 50ms wrapper-overhead target.
8. **Fail-soft direction.** Any setup-phase failure (substrate unreachable, write permission denied, OSError) is logged + dispatch continues. Hard-failing the dispatch on setup failure couples the productivity primitive to the substrate's reliability — mirrors AC.A8.6's fail-soft principle.
9. **No method prescription.** This plan-doc names outcomes; the builder picks: exact field names on `NewACSpec`, exact stub body byte-for-byte, exact ordering of writes within the setup phase (subject to AC.DSA.3 sentinel-first), exact diagnostic NDJSON keys, helper-module symbol layout.
10. **No changes to `personas/`.** Persona-prompt content authoring (telling the persona to use `new_acs`) is a follow-up amendment, not this amendment.
11. **No changes to existing diagnostic log path.** Reuses `<workspace>/workspace/.pos/dispatch-wrapper.log` (amendment #52 D8). Setup events land alongside refusal/fallback events.
12. **DEV MODE detection** uses A1's existing public surface (`framework/hands-off-lifecycle/hooks/corpus_load_sentinel.workspace_mode(workspace_root)` or its equivalent thin reader). No new mode-detection mechanism.
13. **Pos-amend bookkeeping mandatory.** `pos-amend apply --dry-run` must exit 0 before the amendment commit; `pos-amend apply` advances BASELINE; `pos-amend seal --plan-doc <abs-path>` finalises (per `feedback_dispatch_explicit_pos_amend_apply`).
14. **Sealed-component preservation.** AC.DSA.10 + the seal-diff invariants on every prior amendment's components stay green.
15. **Build-time AC-row registration is a hard prereq (inherited from A2).** This amendment's BUILD agent must register manifest rows for AC.DSA.1–AC.DSA.S BEFORE the first source edit. Author A3 stubs (test_AC_DSA_1_placeholder.py through ...) BEFORE the first source edit. Sentinel binding the build agent to (primary-persona, AC.DSA.x) before the first edit. Bootstrap order: (a) sentinel, (b) manifest rows, (c) test stubs / real tests, (d) source. NB: this amendment's own build agent has to do the setup MANUALLY because the very feature this amendment ships isn't available yet — meta-recursion is real here.
16. **No agent-side discipline-as-code.** This amendment is itself a productivity primitive; if the build agent forgets to set up its own scope, A2/A3 deny and surface. Same pattern as A2/A3 themselves used for their own self-bootstrap.

---

## 6. Decisions for owner (read this first)

Per `feedback_summarize_and_surface_decisions`: every decision below carries a recommendation + rationale + alternatives. Owner rules from this section without reading the rest of the plan.

### D-DSA.1 — Apply only to BUILD dispatches with declared new_acs

- **Recommendation:** the dispatcher's setup phase fires ONLY when `DispatchShape.new_acs` is non-empty. Research+plan dispatches and any dispatch authoring only universally-admitted paths pass `new_acs=()` and the setup is skipped.
- **Why:** research+plan dispatches AUTHOR ACs as their output; the dispatcher cannot know the AC list at dispatch time. The shape applies cleanly to BUILD dispatches against an existing plan-doc. Skipping setup for empty `new_acs` is the correct fail-soft default; the substrate's universal-paths admissions cover research+plan dispatches' edit traffic.
- **Alternative:** require every dispatch to declare ACs (refuse empty). Rejected — breaks the research+plan use case and most non-amendment dispatches.

### D-DSA.2 — Stub content: skip-with-reason

- **Recommendation:** stub body is `pytest.skip("stub authored by dispatcher; replace with real test for AC.<id>")` inside `def test_AC_<NORM>_placeholder() -> None:`. Module-level docstring names dispatcher + scope_id + plan_path. No fixtures, no class scaffolding.
- **Why:** satisfies A3's file-exists + function-exists predicates; reports as `skipped` (not `passed`, not `failed`) in pytest output; doesn't pollute green-test count with passes-by-default; doesn't break `pos-amend apply --dry-run` with hard fails. Convention-marker via skip reason.
- **Alternatives:** (α) `def ... pass` — passes by default, pollutes green count; rejected. (γ) `pytest.fail(...)` or (δ) `raise NotImplementedError` — break pre-amendment test sweeps; rejected. (ε) richer stub with fixtures — leaks design from dispatcher into agent's working context; out of scope (future amendment).

### D-DSA.3 — One file per AC (per A3 convention)

- **Recommendation:** one file per AC at `framework/<component>/tests/test_AC_<NORM>_placeholder.py`, matching A3's per-AC `test_AC_<NORM>_*.py` convention.
- **Why:** every existing test in `framework/*/tests/test_AC_*.py` follows the one-file-per-AC pattern. A3's glob is per-AC by design. Consolidating breaks the convention.
- **Alternative:** consolidated `tests/test_AC_<NORM>_stubs.py` with multiple stubs. Rejected — would require different AC normalisation (the file-name carries one normalisation; the function names carry others).

### D-DSA.4 — Sentinel write strictly before manifest registration

- **Recommendation:** in the setup phase, write the sentinel FIRST, then register manifest rows. Manifest rows' `created_at` lands strictly after sentinel's `created_at`.
- **Why:** A3's "new AC in this diff" predicate (AC.TDG.4 / D-A3.4) is `manifest_row.created_at > sentinel.created_at`. Reverse ordering silently breaks A3's enforcement (the gate treats every AC as "existing in-AC modification" and never enforces test-pinning). This is an invisible failure mode without explicit sequencing.
- **Caveat:** ISO-8601 second-resolution timestamps (per A1 `_now_iso`) collapse same-second writes. The builder must verify in tests that registering immediately after sentinel write produces strictly-after timestamps; if same-second collisions are a real risk, add a deterministic delay or a monotonic counter — method-level, surfaced in the builder plan as a halt-trigger if the empirical check fails.

### D-DSA.5 — Stub-deletion / agent-authored-content respect

- **Recommendation:** the dispatcher does NOT delete or auto-clean stubs. Idempotent overwrite is byte-equal-skip; if the stub file exists with content that doesn't match the dispatcher's skip-with-reason body, the dispatcher logs a diagnostic and DOES NOT OVERWRITE (the build agent has authored real content; respect it).
- **Why:** stubs are setup artefacts, not enforcement artefacts. Auto-deletion couples the dispatcher to the seal-diff bookkeeping (a different surface). Build-agent-authored content is the goal state; the dispatcher's stub is the placeholder; replacing the placeholder is the build agent's normal work.
- **Alternative:** (a) auto-delete unmodified stubs at seal time. Rejected — out of scope; future amendment if needed. (b) auto-clean unmodified stubs at next dispatch's setup. Rejected — confuses the operator (stubs disappear without trace).

### D-DSA.6 — Caller-supplied (component, ac_id, source_path_glob) triples

- **Recommendation:** the dispatch shape carries an explicit tuple of (component, ac_id, source_path_glob) triples (`new_acs: tuple[NewACSpec, ...]`). The dispatcher does not parse the plan-doc.
- **Why:** plan-doc parsing is brittle (the same brittleness that disqualified A3 D-A3.3 candidate γ). The persona reading the plan-doc and explicit-passing the triples is the correct shape — the persona is the authoring surface, not the dispatcher.
- **Alternative:** infer triples from a manifest-YAML pointer in the dispatch shape. Rejected — the manifest YAML doesn't contain per-AC source-path-globs; that's a separate authoring step.

### D-DSA.7 — Setup phase placement: before activate_scope_with_spec

- **Recommendation:** in `dispatch_with_scope`'s execution sequence, the setup phase (sentinel + manifest + stubs) runs strictly before the IPC call to `activate_scope_with_spec`. On gate-chain refusal at activate_scope_with_spec, the setup artefacts persist (skipped placeholder tests + manifest rows + sentinel).
- **Why:** simpler control flow; setup is local to the wrapper process, IPC is over a socket — combining them adds a window-of-inconsistency. Persistence of setup on refusal is benign (idempotent on retry; gate refusal observable via diagnostic log).
- **Alternative:** (B) setup AFTER gate approval. Marginal cleanliness gain; adds inconsistency window if setup fails after activate_scope succeeded. Rejected. (C) push setup into the orchestrator-side IPC method. Rejected — massive scope expansion.

### D-DSA.8 — DEV-MODE-only

- **Recommendation:** the setup phase fires only when the workspace is in DEV MODE. NORMAL USE workspaces skip it entirely.
- **Why:** A2 + A3 are DEV-MODE-only (D4 + D-A3.6 locks). Setting up artefacts that the gates don't check is wasted work. Mirrors A4's mode partition (universal classes vs. DEV-MODE classes — this amendment is ODD-discipline → DEV-MODE).
- **Alternative:** universal. Rejected — no value-adds in NORMAL USE.

### Surfaced for owner ruling: 8 (D-DSA.1, D-DSA.2, D-DSA.3, D-DSA.4, D-DSA.5, D-DSA.6, D-DSA.7, D-DSA.8).

(All 8 carry recommendations; defaulting to recommendations leaves the builder a fully-specified scope. Owner may flag any for re-consideration.)

---

## 7. Out of scope (named explicitly per ODD §2.5)

Items below are NOT in this amendment's surface.

- **Persona-prompt content authoring.** Telling the persona to USE `new_acs` (e.g., a §"Setup at dispatch" block in `personas/primary/prompt.md`). Out of scope; future amendment.
- **Auto-deletion of unmodified stubs at seal time.** D-DSA.5 alt(a). Out of scope; future amendment if needed.
- **Auto-cleanup of unmodified stubs at next dispatch.** D-DSA.5 alt(b). Out of scope.
- **Mid-build AC re-extension (ODD §4) auto-handling.** The build agent re-extends mid-build by registering the new manifest row + authoring the test, mirroring §4 protocol. The dispatcher's role is at dispatch-start only. Out of scope.
- **Plan-doc parsing.** D-DSA.6 alt. Out of scope.
- **Richer stub content** (fixtures, partial bodies, AC-text references). D-DSA.2 alt(ε). Out of scope.
- **Test-deletion gate.** FIDRAFT line 149 — separate failure class, A4-adjacent. Out of scope.
- **Dispatcher-side authoring of MANIFEST YAML** at scope-creation time. The manifest is a separate authoring artefact (per pos-amend convention); plan + manifest are authored by the persona. Out of scope.
- **Multi-tenant dispatch** (two dispatchers in one workspace). The sentinel is single-tenant per workspace by A1's design — out of this amendment's scope; A1.1 corrective if needed.
- **Background-task / scheduled-routine dispatcher integration.** Future amendment composes this primitive into a cron-equivalent harness.
- **Money-axis budget inference, awareness-block contributors, self-correction wiring** — orthogonal to this amendment.

If any of these surface as hard prerequisites during the build, halt-and-signal; do not silently expand scope.

---

## 8. Halt triggers

Halt and surface (do not silently extend) when any of the following fires:

1. **Pre-flight surfaces this already shipped** (per §0). Specifically: `git log --grep="test-stub|test.stub|dispatch.*stub|dispatcher.*stub"` returns commits OTHER THAN the FIDRAFT-capture commit `9b928c8`; OR `dispatch_wrapper.py` already contains a `register_source_binding` call or a `write_active_scope_sentinel` call. Halt.
2. **A1 substrate gap.** If A1's `register_source_binding` does not accept the `(component, ac_id, source_path_glob)` shape this amendment needs, OR if `write_active_scope_sentinel` does not return an idempotent result for byte-equal content, OR if `manifest_rows_for_ac` doesn't return rows with `created_at` accessible — halt; A1.1 corrective.
3. **A2/A3 substrate gap.** If A2's `objective_binding_gate.evaluate` or A3's `tdd_guard.evaluate` cannot be called from the composition test (AC.DSA.8) without breaking their public surface — halt.
4. **`pos-amend apply --dry-run` red** at any point — halt.
5. **Outcome-resistant AC.** If during builder plan authoring some behaviour resists outcome-shaping (a method prescription is the only natural form), halt and signal.
6. **Architecture creep.** If the design surfaces a need to (a) push setup into the orchestrator (D-DSA.7 candidate C); (b) consolidate stubs across ACs (D-DSA.3 alt); (c) auto-delete stubs (D-DSA.5 alt); (d) parse plan-docs (D-DSA.6 alt) — halt; surface to owner.
7. **Sequencing race.** If the empirical check reveals same-second `created_at` collisions between sentinel write and immediately-following manifest-row insert (D-DSA.4 caveat), halt; the builder must add a deterministic delay or a monotonic counter, and the design choice surfaces as a §14 method-decision register entry.
8. **Stub-content shape regression.** If `pytest.skip(...)` inside `def test_AC_<NORM>_placeholder() -> None:` fails to satisfy A3's regex predicate (`^def\s+test_AC_<NORM>_\w*\s*\(`) — halt. Verification at build start: write a sample stub, run A3's `_file_contains_matching_function` against it, confirm True.
9. **Idempotency regression.** If repeated dispatcher invocations with the same shape corrupt existing artefacts (sentinel, manifest, or stub) — halt.
10. **Backwards-compat regression.** If amendment #52's existing tests (AC.A8.1 – AC.A8.S) fail post-amendment — halt.
11. **Surrounding-code ODD §2.5 violation.** The wrapper's adjacent modules in `primary-persona/src/` may contain pre-existing §2.5 violations the build's verification pass uncovers. Halt-and-surface per the dispatch's explicit ODD-violation clause; do NOT extend a violating surface.
12. **Substrate-fence breach.** Any source-edit need outside `framework/primary-persona/{src,tests}/` halts.
13. **Self-bootstrap fails.** Per hard constraint 15: the build agent's bootstrap order (sentinel → manifest rows → test stubs → source) must be followed manually because this amendment's own feature isn't available yet. If A2 denies the first row registration (chicken-and-egg from a wrong ordering), or A3 denies its own test files (test files for this amendment's ACs must exist on disk before the test files themselves are edited — meaning the build agent authors them via Write rather than Edit, which is fine because Write of a new file passes A3's chicken-and-egg avoidance via the test-tree carve-out). Verification: trace the bootstrap sequence on paper before the dispatch lands.
14. **Composition test fails.** If after the dispatcher's setup phase, calling A2's `evaluate` returns DENY for a hypothetical Edit at the registered glob, OR A3's `evaluate` returns DENY for the same — halt. AC.DSA.8 is the explicit composition contract; failure means the design assumption is wrong.

---

## 9. Risks

- **R1 — Sub-second `created_at` collisions break A3's "new AC" predicate.** Probability: medium-low. ISO-8601 second-resolution + write-then-write ordering should produce strict-after timestamps in practice, but burst timing on fast disks could collide. Mitigation: D-DSA.4 caveat names the empirical check; halt-trigger 7 surfaces; deterministic delay or monotonic counter is the fix.
- **R2 — Build agent overrides stub before dispatcher's idempotent skip detects.** Probability: very low (build agent runs AFTER dispatcher's setup; race only if user manually edits during dispatch). Mitigation: idempotency check reads existing content, compares to expected stub body, skips overwrite if mismatch.
- **R3 — Setup-phase failure is silent.** Probability: low. Diagnostic NDJSON to `<workspace>/workspace/.pos/dispatch-wrapper.log` is the observability surface; if the diagnostic write itself fails (disk full, permission), the dispatch still proceeds (mirrors AC.A8.6 fail-soft). Operator detection: gate refusal at first-edit time names the missing artefact in the deny diagnostic (A2/A3 already do this).
- **R4 — Dispatcher ↔ orchestrator split (cross-process timing).** The dispatcher writes setup artefacts in the persona process; activate_scope_with_spec runs in the orchestrator process. Setup artefacts (sentinel + manifest + stubs) are workspace-local files; orchestrator IPC is over Unix socket. No cross-process synchronisation needed — A1 sentinel is per-workspace single-tenant; manifest is SQLite (per-workspace). Mitigation: design respects A1's single-tenant model.
- **R5 — Persona forgets to populate `new_acs`.** Probability: high without persona-prompt updates (out of scope). Mitigation: backwards-compat (AC.DSA.10) means dispatches without `new_acs` work as before — the amendment is opt-in. Persona-prompt update is a follow-up amendment.
- **R6 — Test-stub naming collision.** Two different ACs normalise to the same name (e.g. `AC.X.1` and `AC.x.1` both → `X_1`). Probability: vanishingly low (case is consistent in practice). A3's `_normalise_ac_id` already does upper-case so case-collision is by design. Mitigation: rely on A3's existing normalisation; if a collision surfaces, halt-trigger 8.
- **R7 — Wrapper-overhead-latency increase.** Adding setup phase adds wall-clock cost. Target: < 50ms p95 for N=5 ACs. Mitigation: hard constraint 7 names the budget; halt if empirical exceeds.
- **R8 — Stub written to wrong workspace tree.** If the dispatcher resolves `workspace_root` incorrectly (e.g., relative path, symlink mismatch), stubs land in the wrong tree. Mitigation: dispatcher already resolves `workspace_root` to a canonical absolute Path (amendment #52 line 409); reuse the same resolution.
- **R9 — Self-bootstrap (this amendment's own build).** This amendment's BUILD agent has to do the setup MANUALLY (sentinel + manifest + stubs) because the very feature isn't available yet. Mitigation: hard constraint 15 + halt-trigger 13 name the bootstrap order explicitly.
- **R10 — Orchestrator-side rejection of new_acs as part of spec_payload.** This amendment does NOT modify `activate_scope_with_spec`'s payload (`new_acs` is consumed dispatcher-side, not sent over IPC). Risk: nil. Verification: amendment #52's `spec.model_dump()` payload remains the same.

---

## 10. Bookkeeping surface (`pos-amend` manifest sketch)

Per amendment #22's `pos-amend` convention. Manifest YAML at build-dispatch, schema:

```yaml
schema_version: 1
amendment:
  number: <assigned-at-dispatch>
  slug: dispatcher-side-test-stub-authoring
  title: "primary-persona dispatch-wrapper setup phase — sentinel + manifest + test-stub authoring"

baseline: <pre-amendment-tip-sha>   # HEAD~1 of amendment commit per #29/#34/.../#73 pattern

plan: docs/plans/dispatcher-side-test-stub-authoring.md

seal_description: "primary-persona dispatch-wrapper setup phase (DEV-MODE; sentinel-first sequencing; idempotent stub authoring)"

# Single sealed component touched per §2 fence:
#   - primary-persona: dispatch_wrapper.py extension + new helpers + tests.
components:
  - name: primary-persona
    seal_test: framework/primary-persona/tests/test_no_sealed_amendments.py
    sidecar: framework/primary-persona/tests/SEAL_COMMIT
    frozen_baseline: false

universal_paths:
  prefixes:
    - docs/plans/
  files:
    - CLAUDE.md
    - docs/odd-in-pos.md
    - docs/odd-methodology.md
    - docs/FUTURE_IDEAS.md
    - docs/FUTURE_IDEAS_DRAFT.md

narrative:
  target: framework/primary-persona/seals/SEAL_COMMIT.dispatcher-side-test-stub-authoring
  body: |
    # Amendment #<N> — dispatcher-side test-stub authoring
    (body authored by builder at seal time; references AC.DSA.1 –
    AC.DSA.S, the research artefact, and the structural-enforcement
    programme + amendment #52 composition.)
```

**Universal admissions** per amendment #22 ruling #3 cover `docs/plans/`, `CLAUDE.md`, `docs/odd-*.md`, `docs/FUTURE_IDEAS.md`, `docs/FUTURE_IDEAS_DRAFT.md`.

**Test scope per amendment-dispatch CDC speedups + composition tests:** narrow pre-amendment test scope to `framework/primary-persona/tests/` (the amendment's component) + `framework/objective-tracker/tests/` (consumer-only sanity) + `framework/hands-off-lifecycle/tests/` (composition test against A2/A3). Skip pre-seal full-suite rerun (sidecar-only edits between amendment and seal). Inline odd-methodology snippets into the dispatch brief.

**Bookkeeping flow** (per `feedback_dispatch_explicit_pos_amend_apply`):
1. Author manifest at `docs/plans/dispatcher-side-test-stub-authoring.manifest.yaml` with the correct BASELINE.
2. **Build-time manifest-row registration** (hard constraint 15): build agent's first action is `tracker.register_source_binding(component="primary-persona", ac_id="AC.DSA.x", source_path_glob="...")` for each AC.
3. **Test files authored before source files.** Per hard constraint 15: tests for AC.DSA.x land BEFORE source edits to `dispatch_wrapper.py`.
4. **Sentinel binding the build agent** to (primary-persona, AC.DSA.x) before the first source edit.
5. Author all source edits + tests; commit as the amendment commit on branch `pos-v2`.
6. `pos-amend apply --dry-run <manifest>` — must exit 0.
7. `pos-amend apply <manifest>` — advances BASELINE literals + writes SEAL_COMMIT sidecars.
8. `pos-amend seal --plan-doc /Users/lukeivers/ivers-corp-pos-v2/docs/plans/dispatcher-side-test-stub-authoring.builder-plan.md <manifest>` — runs the scoped test sweep, creates the seal commit, advances SEAL_COMMIT, appends builder-plan §SHA backfill follow-up commit.
9. Verify: `pos-amend apply --dry-run <manifest>` exits 0 against post-seal HEAD.

**Commits:**
- Amendment commit: `feat(primary-persona): dispatch-wrapper setup phase — sentinel-first sequencing + manifest registration + idempotent test-stub authoring (amendment #<N>, AC.DSA.1–AC.DSA.S)`.
- Seal commit: `chore(seals): dispatcher-side test-stub authoring — primary-persona at <amendment-sha>`.

No `--amend`. `pos-amend apply --dry-run` green is the prereq to amendment commit.

---

## 11. Risks + mitigations

(Consolidated in §9.)

---

## 12. Three-lens AC trace

| AC          | Lens 1 (Claude)                                              | Lens 2 (Translation / Toolkit)                                           | Lens 3 (ODD)        |
| ----------- | ------------------------------------------------------------ | ------------------------------------------------------------------------ | ------------------- |
| AC.DSA.1    | composes on amendment #52's existing `DispatchShape`          | toolkit primitive — every future dispatcher composes against `new_acs`  | outcome-shaped      |
| AC.DSA.2    | composes on A3's filename + function-name convention          | translation: persona doesn't author stubs by hand                        | outcome-shaped      |
| AC.DSA.3    | composes on A1's `created_at` semantics                       | structural — sequencing the writes correctly                             | outcome-shaped      |
| AC.DSA.4    | composes on A1's idempotent sentinel + manifest APIs          | toolkit: retries safe                                                    | outcome-shaped      |
| AC.DSA.5    | composes on amendment #52's diagnostic log                    | translation: substrate failures absorbed at boundary                     | outcome-shaped      |
| AC.DSA.6    | composes on A1's mode-bit                                     | translation: NORMAL USE cost is sub-10ms                                 | outcome-shaped      |
| AC.DSA.7    | composes on amendment #52's IPC sequence                      | structural — local-first, IPC second                                    | outcome-shaped      |
| AC.DSA.8    | composes on A2 + A3 evaluate functions                        | toolkit: the gates become invisible on the happy path                    | outcome-shaped      |
| AC.DSA.9    | composes on amendment #52's NDJSON diagnostic                 | toolkit: setup observability                                             | outcome-shaped      |
| AC.DSA.10   | preserves amendment #52's surface                             | toolkit backwards-compat                                                 | structural          |
| AC.DSA.S    | n/a                                                          | n/a                                                                      | structural          |

---

## 13. Ladder to AC.PO.1 / AC.PO.2 (VALUE_PROPOSITION as prime objective)

- **AC.DSA.1, AC.DSA.2, AC.DSA.3, AC.DSA.4 → AC.PO.1.** Persona declares ACs once at dispatch shape; dispatcher does the substrate setup; agent's first edit succeeds. Translation burden of "remember the substrate steps" absorbed.
- **AC.DSA.5, AC.DSA.6, AC.DSA.9 → AC.PO.1.** Substrate-failure cases absorbed at the wrapper boundary (fail-soft + diagnostic); user doesn't see failed-write traces.
- **AC.DSA.7, AC.DSA.8 → AC.PO.1.** The composition test makes the gates invisible on the happy path — user's dispatch works; user doesn't see deny diagnostics on properly-set-up dispatches.
- **AC.DSA.1, AC.DSA.10 → AC.PO.2.** New toolkit primitive: a setup-phase pattern in the dispatch wrapper. Future contributors (scheduled routines, retry loops) compose against this pattern.
- **AC.DSA.2, AC.DSA.4 → AC.PO.2.** Stub-rendering + idempotent-write helpers are reusable for any future amendment that needs to author placeholder tests.
- **AC.DSA.10 → AC.PO.2.** Backwards-compat preserves amendment #52's wrapper surface.

After this lands, the four primitives compose end-to-end: corpus inlined (#73) → sentinel + manifest + stubs authored (this amendment) → cost/safety/reversibility gates approve (#52) → agent's first edit succeeds (A2 + A3 admit). The "fully-set-up session-start + dispatch-start" picture is complete.

---

## 14. Method-decision register

Method-level decisions made during the build land here at seal time per `pos-amend seal --plan-doc` convention. Empty at plan-author time.

### Commit SHAs

- Amendment commit: `f23dee82638a4af7e084edd180de8f0ceb20d30d` —
  `chore(seals): primary-persona dispatch-wrapper setup phase — sentinel-first sequencing + manifest registration + idempotent test-stub authoring (DEV-MODE-only) — primary-persona at 3b6aa89`
- Seal commit: `69635b21a4f69ef4d3ba7dca66f584c3f0398058` —
  `chore(seals): primary-persona dispatch-wrapper setup phase — sentinel-first sequencing + manifest registration + idempotent test-stub authoring (DEV-MODE-only) — primary-persona at f23dee8`
## 15. References

- Locked research (governs):
  `docs/plans/research/dispatcher-side-test-stub-authoring-research.md` (this dispatch's sibling artefact).
- FIDRAFT capture: `docs/FUTURE_IDEAS_DRAFT.md` line 151 (captured 2026-04-28 by amendment #71 build agent).
- Amendment #52 plan (extension target):
  `docs/plans/agent-dispatch-as-scope-wrapper.md`.
- Amendment #52 wrapper code (extension surface):
  `framework/primary-persona/src/dispatch_wrapper.py`.
- Amendment #52 manifest:
  `docs/plans/agent-dispatch-as-scope-wrapper.manifest.yaml`.
- A1 substrate plan:
  `docs/plans/structural-enforcement-a1-substrate.md`.
- A1 substrate APIs (consumer-only):
  - `framework/objective-tracker/src/runtime.py:669` — `register_source_binding`.
  - `framework/objective-tracker/src/runtime.py:695` — `manifest_rows_for_ac`.
  - `framework/hands-off-lifecycle/hooks/active_scope_sentinel.py:115` — `write_active_scope_sentinel`.
- A2 plan + gate:
  `docs/plans/structural-enforcement-a2-objective-binding-gate.md`;
  `framework/hands-off-lifecycle/hooks/objective_binding_gate.py`.
- A3 plan + gate:
  `docs/plans/structural-enforcement-a3-tdd-guard.md`;
  `framework/hands-off-lifecycle/hooks/tdd_guard.py` (notably `_normalise_ac_id`, `_expected_test_glob`, `_function_prefix`).
- A3 helpers (potential composition):
  `framework/hands-off-lifecycle/hooks/_gate_helpers.py`.
- ODD methodology + ODD-in-pos:
  `docs/odd-methodology.md` (§3.3, §4, §5.1.1, §7.4, §8); `docs/odd-in-pos.md`.
- VALUE_PROPOSITION:
  `docs/VALUE_PROPOSITION.md` (translation-layer §; AC.PO.1, AC.PO.2).
- Amendment-dispatch bookkeeping:
  `framework/tools/pos-amend/`.
- Memory bullets carried forward:
  `feedback_no_amend_in_agent_dispatches`, `feedback_dispatch_explicit_pos_amend_apply`, `feedback_subagent_odd_violation_halt`, `feedback_amendment_dispatch_speedups`, `feedback_summarize_and_surface_decisions`, `feedback_serialize_amendment_builds`, `feedback_always_specify_wd_in_dispatches`, `feedback_verify_post_amendment_state`.
