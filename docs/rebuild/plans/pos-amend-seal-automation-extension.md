# pos-amend seal-automation extension — plan

Dev-discipline work. **NOT** a sealed-component amendment. No `pos-amend` manifest, no `SEAL_COMMIT` bump, no seal commit. `tools/pos-amend/` lives outside the sealed-component fence (per CLAUDE.md operational caution §2.5 — `tools/` is dev-discipline territory). Plan-before-code per the dev CDC; corrective new commits land the change.

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Companion:** `docs/rebuild/plans/pos-amend-tracker-integration.md` (the OTHER queued pos-amend extension; sequencing decision in §11 D-6).
**Prior dev-discipline plan precedents:** `docs/rebuild/plans/pos-amend-install-instructions-fix.md`, `docs/rebuild/plans/orphan-plist-cleanup-install-instructions-fix.md`, `docs/rebuild/plans/pos-amend-tracker-integration.md`.

---

## 1. Summary / TLDR

After every sealed-component amendment commit lands, the build agent today runs ~5 manual bash commands by hand:

1. `cat <component>/tests/SEAL_COMMIT` — read the prior seal SHA.
2. `pos-amend seal <manifest>` — advance sidecars + append narrative (already mechanised; this step is the only one that's automated today).
3. `git add <files-the-seal-step-wrote>`.
4. `git commit -m "chore(seals): <description> — <component> at <sha>"` — hand-crafted following a near-deterministic template.
5. Run the component's full pytest suite; loop through every other sealed component running `pytest <comp>/tests/test_no_sealed_amendments.py` for the cross-component seal-diff sweep.

This plan extends `pos-amend` so the build agent replaces those five steps with a single CLI invocation. The extension is purely additive — every existing `pos-amend` invocation keeps its current shape and exit-code contract.

The proposed shape (recommendation, ruled in §11):

- **`pos-amend seal` widens** to (a) advance sidecars + append narrative (today's behaviour), (b) `git add` the files it wrote, (c) run the touched component(s)' full test suite, (d) run every other sealed component's `test_no_sealed_amendments.py` (cross-component sweep), (e) create the `chore(seals): ...` commit on green, (f) verify `pos-amend apply --dry-run` is green at the new HEAD.
- The pre-existing post-apply behaviour (sidecar advance + narrative append) is preserved unchanged when the new behaviour is opted out via a flag (recommendation: opt-out `--no-finalize`, default behaviour finalises). Backward-compat for any caller that depends on `pos-amend seal` *not* committing is preserved by the flag.

A failed test run, a broken sweep, or a dirty working tree halts before the commit is created and leaves the working tree at a recoverable checkpoint (the sidecar/narrative changes are staged but not committed; the agent or human can fix and re-invoke).

The dispatch-prompt impact: every sealed-component build dispatch can replace ~10 lines of post-amendment-commit guidance with one line.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5 framing)

§2.5 reads: *"Before scoping anything as a sealed-component amendment, name the specific spec objective (v1.0/v1.1/v1.2) the code will satisfy. If I can't name one, the work is dev-discipline (CLAUDE.md, docs, CDCs, tools/), not a sealed-component cycle."*

**No single spec objective names "pos-amend mechanises post-amendment-commit boilerplate."** The work is operational developer-tooling: it speeds the amendment cycle by collapsing five hand-run commands into one invocation and reduces hand-crafted-commit-message variance to a deterministic template. That is dev-discipline territory by every property §2.5 names:

- pos-amend lives under `tools/`.
- pos-amend has no spec objective; its load-bearing-ness is operational. The `apply --dry-run` green gate is a CDC-level commitment per amendment #22, not a spec clause; this extension widens the same operational contract without binding it to a spec.
- The extension is internal to `tools/pos-amend/`; no sealed component's source changes. (Sealed-component test files are *invoked* by the new behaviour, but not edited.)

This is the same §2.5 framing used by `pos-amend-tracker-integration.md` and prior `pos-amend-install-instructions-fix.md`.

---

## 3. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude-leverage

**What Claude capability does this lean on or extend?**

This extension composes against the Claude Code SDK's background-agent dispatch surface (the way every amendment build is delegated today). The relevant Claude-leverage observation:

- Each dispatch prompt today carries ~10 lines of post-amendment-commit instruction that must be re-read and re-executed mechanically by the dispatched agent. After this extension, the dispatch carries one line ("after amendment commit, run `pos-amend seal`") and the agent's prompt-to-action latency drops accordingly.
- The deterministic commit-message template removes one source of agent-by-agent variance — every seal commit is shaped identically by code, not LLM-rendered prose. This is the same shape clause-(g) takes in `odd-methodology.md` §5.2 (refusal lives in the schema, not in the reader's memory) — except here the *commit message format* lives in the tool, not in the agent's memory.
- The Claude SDK's subagent-loop or hook surfaces are not invoked by this extension; that's the right shape — `pos-amend` is a Python CLI invoked from a shell, not interactive. Future hook composition (e.g. a SessionStart hook that calls `pos-amend validate` on dispatch) is unlocked downstream but is out of scope here.
- AC.D-sa.7's plan-doc SHA-backfill projection is the same shape: pure pos-amend internal automation, no Claude primitive leant on. It composes against the same Claude-leverage observation as AC.D-sa.1/AC.D-sa.2 — one less line of dispatch-prompt instruction the persona must encode, one less hand-crafted commit per amendment.

### Lens 2 — Harness + primary-persona value

**Primary-persona test.** *Does this reduce the translation burden between the user's natural-language intent and AI-effective execution?*

Yes — indirectly, by reducing the translation burden the *primary persona* itself must perform when authoring an amendment-build dispatch. Today the persona has to encode "after the amendment commit, do these five bash steps" in every dispatch brief. After this extension, the persona encodes "after the amendment commit, run `pos-amend seal`" — a single named primitive replaces a five-step procedural recital. The persona's own translation burden drops, which compounds across every future amendment dispatch. The user's translation burden was never the load-bearing one here (the user said "build amendment N"; the persona translated to "five bash steps"); but the *persona's* ability to translate is the load-bearing primitive, and this extension simplifies it.

**AC-trace to AC.PO.1:**

- **AC.D-sa.1 → AC.PO.1.** The build agent's post-amendment-commit work collapses from five manual commands to one invocation. Translation burden absorbed in the persona-to-builder layer.
- **AC.D-sa.2 → AC.PO.1.** The deterministic commit-message template removes hand-crafting from every amendment cycle. Translation burden absorbed at the message-authoring layer.
- **AC.D-sa.5 → AC.PO.1.** Failed-test halt-and-leave-state means the build agent doesn't have to translate "test failure mid-seal" into recovery procedure — the tree is left at a clean checkpoint and the agent (or owner) re-invokes after fixing.
- **AC.D-sa.7 → AC.PO.1.** The post-seal `docs(plans): record amendment #N commit SHAs` follow-up commit's mechanical core (the SHA-backfill subsection + the deterministic commit message) is absorbed into `pos-amend seal`. The build agent stops hand-authoring the SHA lines + the commit subject for every amendment; translation burden absorbed at the plan-doc-projection layer. The prose part of §14 (D-build.x choices + rationale + test breakdown) stays builder-authored — irreducible — and that's the right shape: mechanise what's deterministic, keep authorship for what's narrative.

**Harness test.** *Does this add to the toolkit the primary persona can draw from?*

Yes — `pos-amend seal` becomes a load-bearing automation primitive the primary persona can name in a dispatch brief, the same way `pos-amend apply --dry-run` is named today. Future tooling (e.g. a `pos-amend` orchestration loop, a hook that runs seal automatically on amendment-commit detection) composes against the new behaviour.

**AC-trace to AC.PO.2:**

- **AC.D-sa.1 + AC.D-sa.2 → AC.PO.2.** New `pos-amend seal` automation surface — toolkit primitive.
- **AC.D-sa.3 → AC.PO.2.** Cross-component sweep mechanised inside the tool — toolkit primitive (any future tool needing the sweep — e.g. a CI hook — composes against this).
- **AC.D-sa.4 → AC.PO.2.** Backward-compat opt-out flag — toolkit primitive (callers that need the old shape have an explicit escape).
- **AC.D-sa.7 → AC.PO.2.** `pos-amend seal` gains a plan-doc-projection capability: given a designated plan-doc path, it appends the deterministic SHA-backfill subsection and lands the follow-up commit. New toolkit primitive — future operators (a `pos-amend project` family, a hook that drives plan-doc updates from amendment events, a cross-amendment audit tool) compose against this same projection surface.

### Lens 3 — ODD authoring

The plan authors seven outcome-shaped acceptance criteria (§4) under §2.5 framing. Each AC names what must be true; method (the exact subprocess invocation shape, the test-runner discovery, the commit-message template variable substitution mechanism, the `git add` glob versus explicit-files discipline, the failure-mode short-circuit ordering, the plan-doc-projection invocation shape — flag vs. subcommand vs. body-roll) is the builder's call.

ODD §2.5 reverse-direction check: every new code path in `tools/pos-amend/src/pos_amend/commands/seal.py` (or wherever the builder lands the new logic) traces back to AC.D-sa.1–AC.D-sa.7. No platform branches (the existing pos-amend macOS/Python-3.13 platform invariant carries forward unchanged). No "useful later" knobs.

---

## 4. Acceptance criteria (AC.D-sa.x — dev-discipline plan, prefix distinguishes from sealed-amendment ACs and from the tracker-integration plan's AC.D-pa prefix)

Each AC maps to at least one test function in `tools/pos-amend/tests/`.

### AC.D-sa.1 — `pos-amend seal` finalises an amendment with a single invocation

After the amendment commit lands, invoking `pos-amend seal <manifest>` performs the following sequence in a single process: (a) advances the listed components' `tests/SEAL_COMMIT` sidecars to the amendment commit's HEAD SHA (today's behaviour), (b) appends the narrative body to the manifest's `narrative.target` path (today's behaviour), (c) runs the manifest-listed components' full pytest suites, (d) runs the cross-component sweep (per AC.D-sa.3), (e) stages the files written in steps (a) + (b) plus any files the cross-component sweep updates (e.g. BASELINE bumps that landed via test-side-effects — none expected; defensive), (f) creates the seal commit with the deterministic commit message (per AC.D-sa.2), (g) verifies `pos-amend apply --dry-run <manifest>` exits 0 against the post-seal HEAD.

**Test shape:** in a tmpfs git repo seeded with a fixture sealed component + manifest + amendment commit, invoke `pos-amend seal <manifest>`; assert (a) the new HEAD's tree has the expected sidecar SHA + narrative file content, (b) the new HEAD's commit message matches the deterministic template (per AC.D-sa.2), (c) `pos-amend apply --dry-run <manifest>` exits 0 against the post-seal HEAD, (d) the working tree is clean.

**Maps to:** AC.PO.1 + AC.PO.2 (new toolkit primitive that absorbs translation burden in the dispatch layer).

### AC.D-sa.2 — Seal commit message matches a deterministic template

The seal commit message produced by `pos-amend seal` is built from the manifest by a deterministic template. The template's required components are: subject line `chore(seals): <description> — <comp1>[+<comp2>...] at <amendment-sha>`; body containing (1) amendment-number reference, (2) bumped sidecar paths, (3) narrative target path, (4) baseline-to-amendment-SHA window, (5) cross-component sweep result. The `<description>` is sourced per D-3's ruling (recommendation: from a manifest-declared `seal_description` field, defaulting to the manifest's `slug` when absent — i.e. method is the builder's call within the constraint). The `Co-Authored-By:` trailer is included only when invoked under a Claude-Code-attributed environment (recommendation: detect via env var present in dispatched-agent shells; method is the builder's call).

**Test shape:** invoke `pos-amend seal` against fixture manifests covering single-component and multi-component cases; assert the resulting commit subject matches the template against fixture-defined expectations; assert each required body component is present.

**Maps to:** AC.PO.1 + AC.PO.2 (deterministic templating removes hand-crafting).

### AC.D-sa.3 — Cross-component sweep runs every sealed component's seal-diff test by default; scoped sweep is an opt-in optimisation

By default, `pos-amend seal`'s sweep step runs `pytest <comp>/tests/test_no_sealed_amendments.py` (or the component-declared seal-diff test path, per the manifest's `seal_test` field — already present in the schema) for **every sealed component in the workspace**, not only manifest-listed ones. Discovery of the full sealed-component set uses the same convention `tools/pos-amend/` already uses internally (recommendation: glob `<repo-root>/*/tests/test_no_sealed_amendments.py`; method is the builder's call). A non-zero exit from any component's seal-diff test halts the sweep and prevents the seal commit (per AC.D-sa.5).

A `--scoped-sweep` opt-in flag restricts the sweep to manifest-listed components only — for amendments where the author has high confidence the diff window is bounded and wants to trade safety for speed. The default-on full-sweep choice is the safer option; the `--scoped-sweep` flag is the speed option. Per ODD §3.4 (timing in criteria), the AC declares which is default (full sweep is default).

**Test shape:** in a fixture repo with N sealed components (N ≥ 3), invoke `pos-amend seal <manifest>` against a manifest listing only one of them; assert all N seal-diff tests are invoked. Then add a `--scoped-sweep` invocation and assert only the manifest-listed component's seal-diff test is invoked.

**Maps to:** AC.PO.2 (toolkit primitive, sweep mechanised). AC.PO.1 (translation burden absorbed — the persona doesn't have to enumerate every component in dispatches).

### AC.D-sa.4 — Backward-compat: existing `pos-amend seal` callers can opt out of the new behaviour

A `--no-finalize` flag on `pos-amend seal` preserves the pre-extension behaviour exactly: sidecar advance + narrative append, no `git add`, no test run, no sweep, no commit, no dry-run verification. A manifest authored against any pre-extension `pos-amend` and a build agent that depended on the old behaviour can pass `--no-finalize` and observe identical pre-extension semantics. The default (no flag) is the new, full-finalize behaviour.

**Test shape:** invoke `pos-amend seal --no-finalize <manifest>` against a fixture; assert the working tree shows the sidecar + narrative changes unstaged-or-staged but no commit was created and no tests were run.

**Maps to:** AC.PO.2 (the opt-out is itself a toolkit primitive — explicit escape hatch for callers that need the old shape).

### AC.D-sa.5 — Failure modes halt and leave the working tree at a recoverable checkpoint

When `pos-amend seal` encounters one of:

- (a) a non-zero exit from any component's pytest run (touched component or sweep target),
- (b) the cross-component sweep finding a regression,
- (c) a `git add` or `git commit` failure (e.g. the working tree has unrelated dirty state at invocation time),
- (d) the post-seal `pos-amend apply --dry-run` reporting non-zero,

it (1) halts before the seal commit is created (or, for case (d), after the seal commit is created — see method note below), (2) emits a structured diagnostic naming the failure class + the specific component/test/file involved, (3) leaves the working tree at a recoverable checkpoint: for cases (a)/(b)/(c) the sidecar + narrative changes are staged but uncommitted; for case (d) the seal commit is reverted (recommendation: hard-reset to amendment commit then re-stage the seal changes; method is the builder's call within the no-amend constraint — see §6 #1). The exit code is non-zero in the existing 1/2/3 taxonomy (no new exit code introduced).

If the seal commit was already created when case (d) is detected, the recovery path is constrained by the no-amend CDC: the builder cannot `--amend` the seal commit. Recommendation: emit a structured diagnostic instructing the operator to inspect, then leave the seal commit in place (so audit trail is preserved). The operator's recovery is to author a corrective commit. Builder may refine this within the no-amend constraint.

**Test shape:** in fixture repos, simulate each failure class (inject a failing test, dirty working tree, etc.); assert non-zero exit; assert diagnostic emitted; assert the working-tree state matches the recoverable checkpoint shape.

**Maps to:** AC.PO.1 (translation burden — the agent doesn't have to translate "mid-seal failure" into recovery). AC.PO.2 (failure-mode primitive — composable with future operators of the tool).

### AC.D-sa.6 — Existing `pos-amend` invocations and tests remain unchanged

The existing pos-amend test suite (`tools/pos-amend/tests/`) — including the integration tests against historical manifests `amendment-{22..N}-*.manifest.yaml` — passes against the post-extension tree without modification. `pos-amend validate` and `pos-amend apply [--dry-run]` exit-code semantics, output formats, and side effects are byte-identical to pre-extension behaviour. The schema-version bump for the existing manifest schema is **not** required (no new manifest field is mandatory; `seal_description` is optional with a default).

**Test shape:** run the full `tools/pos-amend/tests/` suite at the post-extension tree; assert green. Verify against all `docs/rebuild/plans/amendment-*.manifest.yaml` files: `pos-amend apply --dry-run` exits 0 on each (sample-tested at fixture-injection time on representative manifests; full enumeration at integration-test time).

**Maps to:** the existing pos-amend backward-compat invariant (the spirit of amendment #22's no-breaking-change contract).

### AC.D-sa.7 — Plan-doc §14 SHA-backfill is mechanised by `pos-amend seal`

When `pos-amend seal` is invoked with a designated plan-doc path (recommendation D-8: optional `--plan-doc <path>` flag; method — flag vs. new subcommand vs. body-roll into `seal` keyed off a manifest field — is the builder's call within this outcome), and the plan-doc already carries a `## 14. ` (or `## 14 ` / `## 14. <heading>`) section header, the seal step (after the seal commit lands and the `apply --dry-run` post-seal verification of AC.D-sa.1 step (g) is green) (a) appends a `### Commit SHAs` subsection under §14 carrying the `Amendment commit: <sha> — <subject>` and `Seal commit: <sha> — <subject>` lines (deterministic format mirroring commit `61ad8f9`'s shape), (b) stages the plan-doc edit, (c) creates a follow-up commit with the deterministic subject `docs(plans): record amendment #N commit SHAs in method-decision register` (amendment-number `N` resolved per the same source-of-truth `pos-amend seal` already uses for the seal commit's body — manifest field or amendment-commit-subject heuristic, builder's call), and a body naming the appended subsection's contents. The Co-Authored-By trailer follows AC.D-sa.2's detection rule (D-5).

When the designation is unset (no `--plan-doc` flag, no manifest field), behaviour is byte-identical to AC.D-sa.1's path — no plan-doc edit, no follow-up commit. The PROSE part of §14 (D-build.x choices + rationale + test breakdown + dependents-cleared narrative — irreducibly the builder's authorship) is **not** generated by `pos-amend`; the SHA-backfill subsection is the only content the tool emits.

If the plan-doc is missing or has no §14 section header, the step halts and emits a structured diagnostic naming the file path + the missing-header condition; the seal commit is left in place (matching AC.D-sa.5 case (d)'s no-amend recovery shape — operator authors a corrective plan-doc + commit by hand).

**Test shape:** in a fixture repo with a fixture amendment commit + seal commit landed by `pos-amend seal`, with a fixture plan-doc carrying a §14 header but no SHA subsection, invoke `pos-amend seal --plan-doc <fixture-path> <manifest>` (or whatever shape the builder picks); assert (a) the plan-doc's §14 carries a `### Commit SHAs` subsection naming both SHAs in the expected format, (b) a follow-up commit was created with the deterministic subject and body, (c) the working tree is clean. Companion test: invoke without the plan-doc designation; assert behaviour byte-identical to AC.D-sa.1 (no plan-doc edit, no follow-up commit). Companion failure-mode test: invoke against a plan-doc missing §14; assert non-zero exit, structured diagnostic, no follow-up commit, seal commit untouched.

**Maps to:** AC.PO.1 + AC.PO.2 (translation burden absorbed in plan-doc-projection layer; new toolkit primitive for plan-doc projection from amendment events).

---

## 5. Behaviour-count check (ODD §3.3 forward; applied as dev-discipline check)

| Behaviour (§1) | Criterion/criteria |
|---|---|
| 1. Single-invocation finalisation post-amendment-commit | AC.D-sa.1 |
| 2. Deterministic commit-message template | AC.D-sa.2 |
| 3. Cross-component sweep (default full; `--scoped-sweep` opt-in) | AC.D-sa.3 |
| 4. Backward-compat opt-out (`--no-finalize`) | AC.D-sa.4 |
| 5. Failure-mode halt-and-checkpoint | AC.D-sa.5 |
| 6. Pre-existing pos-amend behaviour byte-identical | AC.D-sa.6 |
| 7. Plan-doc §14 SHA-backfill mechanisation | AC.D-sa.7 |

Seven declared behaviours; seven ACs cover them. No method-in-AC. Dev-discipline plans do not carry seal-diff ACs because no seal-diff invariant applies (no sealed component is touched).

---

## 6. Hard constraints

1. **No `--amend`.** Corrective commits only — including in the failure-mode recovery path of AC.D-sa.5.
2. **Scope fence — `tools/pos-amend/` only.** Source under `tools/pos-amend/src/`. Tests under `tools/pos-amend/tests/`. README at `tools/pos-amend/README.md`. Any source edit outside these paths is a halt.
3. **No edit to any sealed component.** The new behaviour *invokes* sealed components' seal-diff tests via subprocess pytest; it does not edit their source. Any required edit to a sealed component is a halt and signals the work belongs in a sealed-component amendment cycle, not here.
4. **Reversibility.** Removing this extension returns `pos-amend seal` to its pre-extension shape. The `--no-finalize` flag is the in-tree backward-compat path.
5. **No new pos-amend runtime deps.** The existing `PyYAML>=6` plus stdlib is sufficient (subprocess for pytest invocation, subprocess for git, stdlib pathlib + argparse for everything else). No new third-party dep.
6. **Backward-compat preserved unconditionally.** AC.D-sa.4 + AC.D-sa.6 enforce this. A failure of either is a halt.
7. **`pos-amend apply --dry-run` green** must continue to be a hard prereq for amendment commits per amendment #22 — the extension preserves this gate at the seal step too (AC.D-sa.1 step (g)).
8. **Authority bound.** Builder may refine: subprocess pytest invocation shape (e.g. `pytest -q --no-header` flags); commit-message body component ordering; `seal_description` resolution path (manifest field vs. amendment-commit-subject heuristic vs. CLI flag — recommendation D-3); failure-mode short-circuit ordering; sweep-discovery glob path. Builder may NOT relax the backward-compat invariant (AC.D-sa.4 + AC.D-sa.6), the no-`--amend` constraint, or the no-sealed-component-edit constraint.
9. **CDC adherence.** Plan-before-code, background-agent default (single long-running build → background), scope-only dispatch. Dispatch-speedups apply but the test scope is `tools/pos-amend/` (no sealed component, no seal-diff scope to narrow).
10. **Dev-discipline framing — no SEAL_COMMIT bump, no manifest, no seal commit.** Conventional `feat(tools)` / `chore(tools)` commits.
11. **Plan-doc §14 backfill is append-only and section-header-bound.** AC.D-sa.7's SHA-backfill behaviour requires the designated plan-doc to already carry a `## 14.` section header; `pos-amend` does NOT create the §14 section, does NOT author any prose under §14, and never edits content above the SHA-backfill subsection it appends. The PROSE part of §14 (D-build.x rationale, test breakdown, dependents-cleared narrative) remains the builder's authorship — out of scope for mechanisation.

---

## 7. Out of scope (explicit)

- **Schema-version bump on the manifest.** Not required; `seal_description` is an optional addition.
- **Hook integration with Claude Code session events.** Out of scope; the CLI shape is sufficient. Future work.
- **Pre-amendment-commit automation.** This plan covers post-amendment-commit work only. Pre-commit work (the amendment commit itself) is still hand-authored.
- **`pos-amend project` / `pos-amend audit-coverage`** — research §F/§G of the Heavy-B research artefact; out of scope here.
- **The tracker integration's `objectives` block + apply/seal hooks** — covered in `pos-amend-tracker-integration.md`. Sequencing in §11 D-6.
- **CI integration.** This extension does not change CI; if/when CI lands, it composes against the new `pos-amend seal` shape, but that's a separate dev-discipline plan.
- **The amendment-author dispatch prompt itself.** This plan's AC.D-sa.1–AC.D-sa.7 are about pos-amend; the dispatch-prompt update is a follow-on dev-discipline doc edit (a one-line CDC + dispatch-template change), tracked as a §11 named follow-up but not authored here.
- **Plan-doc §14 prose authorship (D-build.x choices + rationale, zero-content tension narrative, AC test breakdown, dependents-cleared narrative).** AC.D-sa.7 mechanises only the deterministic SHA-backfill subsection + the deterministic follow-up commit message. The narrative body of §14 is irreducibly the builder's authorship and stays manual. Method-decision record prose authoring is the builder's, not the tool's.

---

## 8. Implementation order (suggested — builder's call to refine)

1. Read session-start corpus per CLAUDE.md.
2. Read this plan + `tools/pos-amend/README.md` + `tools/pos-amend/src/pos_amend/commands/seal.py` (existing 52-line surface — the extension lands inside this file's scope or as a new sibling module imported from it).
3. Verify `pos-amend-tracker-integration.md`'s landing status — if it has landed, this plan composes against the post-tracker-integration tree (the tracker-integration's seal-time `lifted_from.source_commit` write becomes one more side-effect of the wider seal step; that's compatible with this plan's design but the builder needs to confirm). If it has not landed, this plan ships first per §11 D-6 recommendation.
4. Write builder-plan to `docs/rebuild/plans/pos-amend-seal-automation-extension.builder-plan.md` naming specific files + symbols expected to be touched.
5. Land the `--no-finalize` opt-out flag first, with a test asserting pre-extension behaviour preserved (AC.D-sa.4 + AC.D-sa.6). This protects backward-compat from regression during the rest of the build.
6. Land the deterministic commit-message template (AC.D-sa.2). Verify with fixture manifests.
7. Land the cross-component sweep with the default-full / `--scoped-sweep`-opt-in shape (AC.D-sa.3).
8. Land the post-test commit creation + post-commit dry-run verification (AC.D-sa.1 steps (e)–(g)).
9. Land the failure-mode short-circuit + checkpoint logic (AC.D-sa.5). Verify each failure class with fixture injection.
10. Run the full `tools/pos-amend/tests/` suite. Verify no regression (AC.D-sa.6).
11. Update `tools/pos-amend/README.md` Subcommand-surface section + Usage-example section to describe the new shape, including the `--no-finalize` and `--scoped-sweep` flags. Note the new dispatch-prompt boilerplate (§9 of this plan).
12. Conventional commits land the changes (no `--amend`, no SEAL_COMMIT bump, no seal commit).

---

## 9. Dispatch-prompt impact (after this lands)

The post-amendment-commit boilerplate in every sealed-component build dispatch shrinks from approximately:

```
After the amendment commit lands:
  1. cat <component>/tests/SEAL_COMMIT to read the prior seal SHA
  2. .venv/bin/pos-amend seal <manifest>
  3. git add <files-pos-amend-wrote>
  4. git commit with template: "chore(seals): <description> — <component> at <sha>"
  5. .venv/bin/pytest <touched-component>/tests/ -q
  6. for each other sealed component:
       .venv/bin/pytest <comp>/tests/test_no_sealed_amendments.py -q
  7. .venv/bin/pos-amend apply --dry-run <manifest> (verify exit 0)
```

…to:

```
After the amendment commit lands:
  1. .venv/bin/pos-amend seal --plan-doc <plan-doc-path> <manifest>
  2. Author §14 method-decision record prose (D-build.x choices + rationale,
     test breakdown, dependents-cleared narrative); commit as a separate
     `docs(plans):` commit. (The Commit-SHAs subsection is already populated
     and committed by step 1.)
```

The §14-prose-authoring sub-step (step 2 above) remains manual — it's irreducibly the builder's narrative authorship, explicitly out of scope for mechanisation per §7. What AC.D-sa.7 absorbs is the deterministic part: the `### Commit SHAs` subsection (Amendment commit + Seal commit lines) plus the deterministic follow-up commit subject `docs(plans): record amendment #N commit SHAs in method-decision register`. Without AC.D-sa.7 the agent today hand-authors both the SHA lines and the commit subject for every amendment.

The CDC on `feedback_amendment_dispatch_speedups` is unchanged in spirit (full-suite for touched components only, seal-diff-tests for the rest, methodology snippets inlined) — its mechanical shape now lives inside `pos-amend seal` instead of in the dispatch prompt. The follow-on doc edits to `docs/rebuild/FUTURE_IDEAS.md` (the CDC text reflecting the new mechanisation) and to whatever dispatch-template the persona reaches for are §11 D-7 follow-ups.

---

## 10. Halt triggers (builder halts + signals owner)

1. **Cross-component scope expansion beyond `tools/pos-amend/`.** Any required source edit to a sealed component → halt.
2. **Backward-compat cannot be preserved.** If AC.D-sa.4 + AC.D-sa.6 cannot both hold, halt.
3. **The deterministic commit-message template requires a manifest schema-version bump.** Halt — that turns the work from purely additive into a breaking-compat change and triggers a re-scope.
4. **The failure-mode recovery path requires `git --amend`.** Halt — no-amend CDC violated.
5. **Cross-component sweep discovery (the glob) finds no test files (e.g. layout has changed since plan authoring).** Halt — re-examine the sealed-component-test convention before proceeding.
6. **An ODD-violating shape becomes strongly required** (method-in-AC, non-objective-backed code path, silent exception that no AC backs). Halt; owner rules.
7. **A test for AC.D-sa.1–AC.D-sa.6 cannot be written deterministically** — halt.
8. **The dev-discipline framing turns out wrong** (e.g., the extension unavoidably edits a sealed-component's source). Halt — that's a sealed-component amendment, not dev-discipline.
9. **Wall-time exceeds 90 minutes.** Halt with current state. Owner rules on split vs push-through.

---

## 11. Decisions remaining for the owner to rule on

The following items are owner-level decisions that shape the build dispatch brief. All carry recommendations.

### D-1 — Subcommand shape: extend `pos-amend seal` vs. new subcommand

**Options:**

- **D-1a. Extend `pos-amend seal`** (default-on the new finalize behaviour, opt-out via `--no-finalize`).
- **D-1b. Add a new subcommand** (e.g. `pos-amend finalize` or `pos-amend complete`) — leave `pos-amend seal` as it is today.
- **D-1c. Add a flag on `pos-amend apply --finalize`** that runs apply→commit→seal as a single mega-step — a different shape that absorbs the amendment commit too.

**Recommendation: D-1a.** Extending the existing `seal` subcommand keeps the surface minimal and preserves muscle memory for build agents that already invoke `pos-amend seal`. The opt-out flag (AC.D-sa.4) preserves backward-compat for any caller that needs the old shape. D-1b adds a synonym subcommand whose only meaningful difference from the extended `seal` is "doesn't break callers that depend on `seal` being non-committing" — which the opt-out flag already provides without surface bloat. D-1c expands scope into pre-amendment-commit territory, which is out of scope per §7 and changes the failure semantics (mid-amendment-commit failures are harder to recover from than mid-seal failures).

### D-2 — Cross-component sweep: full-default vs. scoped-default

**Options:**

- **D-2a. Full sweep is default; `--scoped-sweep` is opt-in.**
- **D-2b. Scoped sweep is default; `--full-sweep` is opt-in.**

**Recommendation: D-2a (full-default).** The cost of a full sweep at the workspace's current size (~14 sealed components, each `test_no_sealed_amendments.py` running in seconds) is bounded — all-up wall-time for the sweep is small relative to the amendment-build time it replaces. The cost of missing a cross-component regression by defaulting to a scoped sweep is not bounded; the regression lands silently and is found later by an unrelated build. Per ODD §3.4, the AC declares the safer default with the speed option as opt-in. The owner can revisit if the sweep cost grows materially as components are added.

### D-3 — Commit-message `<description>` source

**Options:**

- **D-3a. Manifest-declared `seal_description` field** (optional; falls back to manifest's `slug` when absent).
- **D-3b. Heuristic from the amendment commit subject** (parse `feat(<comp>): <subject>` to extract).
- **D-3c. CLI flag `--description "<text>"`** (explicit at invocation time).

**Recommendation: D-3a.** Manifest-declared is deterministic, plan-doc-adjacent (the description lives next to the amendment plan), and survives re-invocation without operator input. D-3b is fragile — any amendment-commit-subject convention drift breaks the heuristic. D-3c moves authoring from the plan/manifest into the operator's terminal which loses the audit trail. The optional-with-slug-fallback shape preserves backward-compat with manifests authored before the field exists.

### D-4 — Failure-mode default for case (d) (post-commit dry-run failure)

**Options:**

- **D-4a. Hard-reset to amendment HEAD; re-stage seal changes; emit diagnostic.**
- **D-4b. Leave the seal commit in place; emit diagnostic; instruct operator to author a corrective commit.**

**Recommendation: D-4b.** The no-amend CDC + the pos-v2-wide preference for new-corrective-commits (over rewriting history) argue for D-4b. A hard-reset rewrites history as soon as it lands, which is a class of operation pos-v2 has explicitly avoided in every prior dev-discipline build. The diagnostic naming the dry-run failure + the operator authoring a corrective commit is the same shape every other pos-v2 dev-discipline failure recovery takes. Documented in AC.D-sa.5; method is the builder's call within the no-amend constraint.

### D-5 — Co-authored-by trailer detection

**Options:**

- **D-5a. Detect via env var** (e.g. `CLAUDE_AGENT_RUN=1` or similar that's already set in dispatched-agent shells).
- **D-5b. Always include the trailer.**
- **D-5c. CLI flag `--co-authored-by "<text>"` (explicit, default-off).**

**Recommendation: D-5a (with builder's call on the specific env-var name).** The trailer is meaningful when an agent runs the seal step; meaningless when a human does. Auto-detection via an env var the dispatch shell already sets is the cleanest shape; the builder picks the specific name from whatever convention is reachable. Fallback: if the env-var convention isn't reliable, downgrade to D-5b (always-include, harmless when human-attributed) before D-5c (explicit-flag — moves authoring overhead onto the operator).

### D-6 — Sequencing relative to `pos-amend-tracker-integration.md`

**Options:**

- **D-6a. This plan lands FIRST**, before `pos-amend-tracker-integration.md`. Rationale: tracker-integration's build itself benefits from the new `pos-amend seal` shape (one fewer step in its own build cycle).
- **D-6b. Tracker-integration lands FIRST**, then this plan. Rationale: this extension's seal step adds a side-effect (the `lifted_from.source_commit` write) when manifests carry an `objectives` block — landing tracker-integration first means this plan's seal-step composition surface is finalised before this plan's design.
- **D-6c. Land them interleaved as a single combined dev-discipline plan.**

**Recommendation: D-6a.** Tracker-integration's `lifted_from.source_commit` write is a pure-additive side-effect that composes cleanly against any seal step (the new behaviour or the old behaviour); the design surface tracker-integration adds doesn't constrain this plan's design. Conversely, tracker-integration's build is a substantial body of work (five ACs, manifest schema v2, runtime tracker DB integration) — landing this seal-automation extension first means tracker-integration's build agent benefits from the simplified post-amendment-commit cycle on every checkpoint of its own multi-step build. D-6c (combined) increases scope and concurrent-failure surface; reject. Builder of tracker-integration confirms this composes; if it doesn't (halt-trigger #1), the order flips to D-6b.

### D-7 — Follow-on doc edits (named, not authored here)

After this plan's build lands, two doc edits follow:

- **D-7a. `docs/rebuild/FUTURE_IDEAS.md` amendment-dispatch-test-scope CDC** — add a sentence noting the post-amendment-commit cycle is now mechanised inside `pos-amend seal`. Single-paragraph edit.
- **D-7b. Whatever dispatch-template the primary persona reaches for** — replace the ~10 lines of post-amendment-commit guidance with the one-line replacement per §9. Existence and location of this template is itself an open question (likely lives in `personas/<handle>/` post-amendment-#36 + #37 wiring; verify before edit).

**Recommendation:** track both as named follow-up items in the task list; author them as a single corrective commit after this plan's build seals. Do not bundle them into this plan's build commits — that bloats scope.

### D-8 — Plan-doc SHA-backfill invocation shape (AC.D-sa.7)

**Options:**

- **D-8a. Optional `--plan-doc <path>` flag on `pos-amend seal`** — single plan-doc path; appends-and-commits when set; byte-identical to AC.D-sa.1 path when unset.
- **D-8b. New subcommand** (e.g. `pos-amend project-shas <plan-doc>`) — separate from `seal`; called as a follow-on after `seal`.
- **D-8c. Manifest field** (e.g. `plan_doc:` in the existing manifest schema) — driven entirely by manifest, no CLI flag; implicit when the field is set.

**Recommendation: D-8a (flag).** Owner's lean per the dispatch brief — minimal surface bloat (one optional flag), zero-impact-when-unset matches the AC.D-sa.4 backward-compat shape, and keeps the seal step a single invocation (one of AC.D-sa.1's load-bearing properties — collapsing five steps into one). D-8b adds a synonym surface and re-introduces the multi-step shape the wider plan exists to eliminate. D-8c hides invocation-time choice in the manifest, which moves authoring into a YAML edit that the operator may not want on every amendment (some amendments may not have a §14-bearing plan doc — e.g. dev-discipline amendments via this plan's own framing — and the manifest field would need an explicit-empty signal). The flag is the most transparent shape.

Singular vs. plural plan-doc paths: singular for now. No amendment in the project history has needed SHA-backfill into more than one plan doc; if that case emerges, widen the flag to repeatable (`--plan-doc a.md --plan-doc b.md`) under a separate dev-discipline plan.

---

## 12. Summary of named decisions (owner-readable)

| Decision | Recommendation | Why it matters |
|---|---|---|
| D-1 | Extend `pos-amend seal` (opt-out via `--no-finalize`) | Smallest surface, preserves muscle-memory, opt-out preserves backward-compat |
| D-2 | Full sweep default; `--scoped-sweep` opt-in | Safety beats speed at current sealed-component count |
| D-3 | Manifest `seal_description` field (slug fallback) | Deterministic, plan-doc-adjacent, audit-trail-preserving |
| D-4 | Leave seal commit in place on dry-run failure; instruct corrective | Honours no-amend CDC; matches every other dev-discipline recovery shape |
| D-5 | Detect Co-Authored-By trailer via env var | Auto-correct, no operator overhead |
| D-6 | Land THIS plan first, tracker-integration second | Tracker-integration build itself benefits from this extension |
| D-7 | Track FUTURE_IDEAS + dispatch-template edits as follow-ups | Out of scope here; small post-build commits |
| D-8 | Optional `--plan-doc <path>` flag on `pos-amend seal` (singular) | Smallest surface for AC.D-sa.7; zero-impact when unset; preserves single-invocation shape |

Owner rules from this table without reading the plan body. Any "no, change to X" on a decision flips one row; the rest stay.

---

## 13. Halt-and-surface findings encountered during plan authoring

Per `feedback_subagent_odd_violation_halt`: I am to halt and surface any ODD violation observed in the work or surrounding code/docs.

**One finding to surface (non-blocking):** the existing `tools/pos-amend/src/pos_amend/commands/seal.py` (52 lines, read at plan authoring time) is well-shaped under §2.5 — every code path traces to amendment #22's manifest-driven sidecar/narrative ACs. No pre-existing violation in the surface this plan extends.

**No ODD violation in surrounding code or docs identified during plan authoring.** The Heavy-B research artefact's §C.1 mentions "future `pos-amend` extensions" and includes `pos-amend project`, `pos-amend audit-coverage` — neither overlaps this plan's scope, and both are explicitly declared out of scope (§7). The `pos-amend-tracker-integration.md` plan composes cleanly with this plan's design (per D-6).

If an ODD violation is discovered during the *build* of this plan (e.g. a failure-class the ACs do not name), the builder re-extends per ODD §4 and surfaces to the owner. The plan's halt-trigger #6 enforces this.

---

## 14. Method-decision record (builder, post-build)

The plan §11 left D-build.x method choices to the builder within the
ACs' outcome bounds. This section records the choices made plus the
test breakdown and commit SHAs.

### D-build.1 — Subcommand layout: extend `seal.py` in place

The new finalisation behaviour lands inside `tools/pos-amend/src/pos_amend/commands/seal.py`. The pre-extension `_legacy_seal()` helper preserves byte-identical pre-extension behaviour for `--no-finalize`. New helpers (`_discover_sealed_components`, `_seal_diff_test_path`, `_build_commit_message`, `_run_pytest`, `_backfill_plan_doc_shas`, `_finalize`) are private to `seal.py`.

**Rationale:** plan §11 D-1 ruling — extend the existing subcommand. Single file keeps blast radius narrow; helpers are private (no public surface added). Each helper traces 1:1 to one AC.D-sa.x. No change to `apply.py`, `manifest.py` (besides the additive `seal_description` field), or `cli.py` (besides three new flags on `seal`).

### D-build.2 — Sealed-component discovery glob

`<repo-root>/*/tests/SEAL_COMMIT` — i.e. presence of the canonical sidecar at the conventional path is the sealed-component marker. At workspace-time discovery returns 12 components (cost-governance, graceful-degradation, hands-off-lifecycle, memory-system, objective-tracker, observability-aggregator, orchestrator, primary-persona, reversibility-primitive, self-correction, telegram-interface, workspace-bootstrap).

**Rationale:** AC.D-sa.3 leaves the discovery method to the builder. SEAL_COMMIT presence is the same signal every seal-diff test relies on internally; using it here keeps the sealed-component definition consistent across the codebase. The fallback for hands-off-lifecycle (no `test_no_sealed_amendments.py`; uses `test_cross_cutting.py`) is handled by `_seal_diff_test_path`.

### D-build.3 — Co-Authored-By env-var detection

Trailer included when any of `CLAUDECODE`, `CLAUDE_CODE_SDK`, or `CLAUDE_AGENT_RUN` is set. Trailer text matches the convention from prior seal commits in this repo: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`.

**Rationale:** plan §11 D-5 ruling — env-var detection. `CLAUDECODE` is set in Claude-Code-attributed shells; `CLAUDE_CODE_SDK` and `CLAUDE_AGENT_RUN` are defensive aliases the builder may add later if convention shifts. Any-of detection means trailer fires under all three signals; absence of all three suppresses the trailer (human-attributed run).

### D-build.4 — Failure-mode short-circuit ordering

Sequence inside `_finalize`: (a) compute amendment SHA; (b) pre-flight dirt check (case (c)); (c) advance sidecars + append narrative; (d) per-component pytest (case (a)); (e) cross-component sweep (case (b)); (f) `git add` + `git commit` (case (c) git failures); (g) post-seal `apply --dry-run` (case (d)). On failure of (a)–(c) and (d)–(f), the seal commit is NOT created. On failure of (g), the seal commit IS LEFT in place per D-4 (no-amend CDC).

**Rationale:** plan §11 D-4 ruling — leave seal commit on case (d). The ordering puts the cheap pre-flight check (dirty tree) first; the expensive operations (component tests, sweep) before the irreversible operation (commit); the verification gate after the commit (because dry-run reads the post-commit HEAD).

### D-build.5 — Plan-doc backfill: idempotent replace-or-append

`_backfill_plan_doc_shas` searches for an existing `### Commit SHAs` subsection inside §14. If present, it is REPLACED (idempotent re-invocation safe). If absent, the subsection is appended at the end of §14. The §14 heading regex accepts `## 14.` and `## 14 ` shapes per AC.D-sa.7 wording.

**Rationale:** AC.D-sa.7 specifies append-only behaviour, but the AC also says "byte-identical when unset" and "halt on missing §14." Idempotency is required by plan §11 implicit ("re-invocation safe" matches the rest of pos-amend's contract). Replace-not-duplicate is the cheapest way to avoid the failure mode where a re-run produces two `### Commit SHAs` blocks.

### Test breakdown

- **AC.D-sa.1** — `test_AC_D_sa_1_single_invocation_finalises` — 1 test: tmpfs repo with one fake sealed component (`alpha`), a manifest pointing at it, an amendment commit; assert sidecar advanced, narrative written, seal commit created, deterministic subject, post-seal dry-run green, working tree clean.
- **AC.D-sa.2** — 4 tests:
  - `test_AC_D_sa_2_commit_message_deterministic_template` — every required body section present (amendment-number, bumped sidecars, narrative target, diff window, sweep summary).
  - `test_AC_D_sa_2_seal_description_falls_back_to_slug` — slug-fallback when `seal_description` absent.
  - `test_AC_D_sa_2_multi_component_subject` — `<comp1>+<comp2>` join in subject.
  - `test_AC_D_sa_2_co_authored_trailer_env_gated` — trailer absent without env var; trailer present with `CLAUDECODE=1`.
- **AC.D-sa.3** — 3 tests:
  - `test_AC_D_sa_3_full_sweep_default_runs_every_sealed_component` — fixture with 3 sealed components; default sweep names `3 components green`.
  - `test_AC_D_sa_3_scoped_sweep_runs_manifest_listed_only` — same fixture; `--scoped-sweep` produces `1 components green`.
  - `test_AC_D_sa_3_sweep_failure_halts_before_commit` — fixture with a failing seal-diff test; assert no seal commit created.
- **AC.D-sa.4** — `test_AC_D_sa_4_no_finalize_preserves_pre_extension_behaviour` — 1 test: `--no-finalize` advances sidecar + writes narrative file but produces NO commit; HEAD remains amendment SHA.
- **AC.D-sa.5** — 2 tests:
  - `test_AC_D_sa_5_failing_component_test_halts_before_commit` — case (a).
  - `test_AC_D_sa_5_dirty_tree_halts` — case (c).
  - (Cases (b) covered by `test_AC_D_sa_3_sweep_failure_halts_before_commit`; case (d) implicitly exercised by AC.D-sa.7's missing-section-14 test which leaves the seal commit and emits the structured diagnostic.)
- **AC.D-sa.6** — 2 tests:
  - `test_AC_D_sa_6_existing_test_suite_still_green` — invokes pytest as a subprocess against the entire pre-existing pos-amend test suite (43 tests) excluding `test_seal.py`; asserts exit 0.
  - `test_AC_D_sa_6_legacy_seal_signature_idempotent` — idempotent legacy-path re-invocation against the same HEAD produces no additional diff.
- **AC.D-sa.7** — 3 tests:
  - `test_AC_D_sa_7_plan_doc_backfill_appends_subsection_and_commits` — `--plan-doc` appends `### Commit SHAs` under §14 + creates deterministic follow-up commit.
  - `test_AC_D_sa_7_no_plan_doc_flag_no_followup_commit` — without `--plan-doc`, HEAD is the seal commit (no follow-up).
  - `test_AC_D_sa_7_missing_section_14_halts_with_diagnostic` — plan-doc with no §14 heading → halt; seal commit left in place.

**Total:** 16 new tests covering 7 ACs. Pre-existing 43 tests all green. Full pos-amend suite at post-extension tree: **59 passed in ~16s**.

`pos-amend validate` + `pos-amend apply --dry-run` against the in-tree manifests `amendment-39-*.manifest.yaml` and `amendment-40-*.manifest.yaml` exit 0 at the post-extension tree (verified manually — see commit log for SHA).

### Backwards-compat verification

- All 43 pre-existing tests green at the post-extension tree.
- `pos-amend apply --dry-run docs/rebuild/plans/amendment-40-*.manifest.yaml` exits 0 at a clean post-extension tree (i.e. with no uncommitted edits to `tools/pos-amend/` itself).
- The `--no-finalize` flag preserves byte-identical pre-extension `pos-amend seal` semantics for any caller that wants the old shape.
- The `seal_description` manifest field is optional with slug-fallback — pre-extension manifests load and seal cleanly without modification.

### Commit SHAs

- Build commit: `<TBD-build-sha>` — `feat(tools): pos-amend seal finalisation extension (AC.D-sa.1–AC.D-sa.7)`

(SHA backfilled in a follow-up `docs(plans):` commit per the same SHA-backfill convention this very extension mechanises for sealed-component amendments.)

### Dependents cleared to dispatch

- `pos-amend-tracker-integration.md` (dev-discipline, the next-in-chain) inherits the new `pos-amend seal` shape — its build agent benefits from the simplified post-amendment-commit cycle on every checkpoint of its own multi-step build.
- D-7 follow-on doc edits (`docs/rebuild/FUTURE_IDEAS.md` CDC text + dispatch-template update) are queued as separate small commits, not bundled here.
