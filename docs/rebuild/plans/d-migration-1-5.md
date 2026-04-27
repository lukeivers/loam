# D-migration D.1.5 — pos-amend rename-aware seal — plan

Critical-path interstitial amendment between **D.1** (directory
restructure, sealed at `570092a`) and **D.2** (workspace-state
directory). Adds rename-detection to `pos-amend apply` so a
component whose only diff between BASELINE and the amendment
commit is a directory rename (every file `R100` — byte-identical
modulo path) does **not** get its `BASELINE` literal advanced and
does **not** get its `SEAL_COMMIT` sidecar bumped to the amendment
window. Conditional bump preserves the prior fence's diff window
where the fence didn't conceptually move.

Without D.1.5, the same cross-component test-fence cascade D.1 hit
will fire again on D.2 (and D.3, D.4, D.5 — every D-chain
amendment that touches multiple components carries a rename-only
component in at least the partial sense). The cascade shape: every
prior amendment's `AC.X.S` seal-diff test (e.g.
`test_AC_M_S_seal_diff_window.py`) hardcodes path prefixes for ITS
amendment's fence; when SEAL_COMMITs advance uniformly to the new
amendment window, those tests see paths from the new window inside
their old window's diff and fail. D.1's recovery path
(transitional OLD prefixes for `test_no_sealed_amendments.py`)
patched 13 tests; the inner `AC.X.S` tests across many amendments
(estimated 20–50) need the same treatment unless the root-cause
gap closes.

**Status:** plan (pre-dispatch). 2026-04-27.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`
**Companions:**
- **D-migration parent plan:** `docs/rebuild/plans/d-migration.md`
  (D.1 → D.5 sequence; D.1.5 inserts here as a pre-D.2 unblocker).
- **Surface that triggered D.1.5:**
  `/Users/lukeivers/pos3/.scratch/claude-output/d1-seal-blocker-surface-2026-04-27.md`
  — primary persona's surface; Luke ruled (b)+(c) on 2026-04-27;
  D.1 sealed under (b) (manual narrative + `--no-finalize`-style
  bookkeeping); D.1.5 IS (c).
- **D.1 builder plan §8 (post-build register):**
  `docs/rebuild/plans/d-migration-1.builder-plan.md` §8 — records
  the hand-rolled seal flow + names this gap explicitly.
- **Vars-file:** `docs/rebuild/plans/d-migration-1-5.vars.yaml`.

**Ancestor record:**
- **Owner ruling 2026-04-27 (locked, surface ledger):**
  D.1.5 lands as a pos-amend amendment between D.1 and D.2
  before any further D-chain dispatches (option (c) of the
  surface). No additional new top-level rulings required;
  D.1.5 is *method-shape* realisation of the (c) ruling.
- **Bug pattern recognised:** D.1's seal-cycle on cross-component
  `AC.X.S` test failures named the conceptual gap. The gap is
  inside `pos-amend`'s apply step, not inside the seal-diff tests
  themselves — every prior test correctly enforces ITS
  amendment's fence; the bug is that `pos-amend apply` advances
  the fence *origin* (BASELINE + SEAL_COMMIT) for components
  whose fence did not conceptually move.
- **Precedent:** amendments #22 (introduced `pos-amend`), #23
  (added `frozen_baseline:` to manifest schema for hands-off-
  lifecycle's H19 baseline), #41 (added `--plan-doc` to seal),
  #46 (introduced `seal_description:`). D.1.5 fits the same
  shape: additive flag/field with backwards-compatible default.

**Research:** None required. The conceptual gap, the detection
mechanism, and the conditional-bump path are all named in the
surface artefact. D.1.5 is a tooling-only amendment; its
"research" is the surface document plus the codebase read
performed during plan authoring.

---

## 1. Summary / TLDR

**The gap.** `pos-amend apply` walks the manifest's component
list and unconditionally advances each component's `BASELINE`
literal (in `tests/test_no_sealed_amendments.py`) to the
manifest's `baseline:` SHA, and writes the component's
`SEAL_COMMIT` sidecar to that same SHA. For components whose
diff in the amendment window is rename-only (every file
`R100` per `git diff --find-renames`), this is a conceptual
error: the component's fence didn't move; advancing the fence
origin produces wrong-window assertions in every prior
`AC.X.S` test for that component once the seal step bumps
SEAL_COMMIT to the seal commit.

**The fix.** In `pos-amend apply`, before bumping a component's
BASELINE/SEAL_COMMIT, run a per-component rename-only check
(`git diff --diff-filter=ADMRT --find-renames=<threshold>`
restricted to the component's old-path + new-path; if every
non-rename entry is itself a created/deleted seal-bookkeeping
sidecar AND every renamed entry is `R<threshold-or-better>`,
the component is rename-only). When rename-only:

1. Skip the BASELINE literal bump (preserve the prior pin).
2. Skip the SEAL_COMMIT sidecar bump (preserve the prior
   sidecar value).
3. Still apply `allowed_prefixes` / `allowed_files` widenings
   (the new-path prefix needs admission for D.2+'s seal-diff
   windows; pos-amend's existing widening logic already
   handles this and is orthogonal to BASELINE/SEAL_COMMIT
   advancement).
4. Record in apply's stdout (and the apply-chore commit
   body when invoked under the chore-shape commit shape):
   `<comp>: rename-only — BASELINE preserved at <prior-sha>;
   SEAL_COMMIT preserved at <prior-sha>; allowed_prefixes
   widened.`

When NOT rename-only (the common case): existing behaviour
unchanged. **HC#1 binding.**

**The cleanup.** D.1.5 *also* retroactively reverts D.1's
spurious BASELINE/SEAL_COMMIT bumps on rename-only components.
The 14 sealed components in D.1's manifest divide into two
classes: (a) components whose D.1 diff is rename-only (their
BASELINE + SEAL_COMMIT should not have advanced); (b)
components whose D.1 diff included substantive edits (their
BASELINE + SEAL_COMMIT correctly advanced). D.1.5's apply
chore-shape commit reverts (a)'s BASELINE/SEAL_COMMIT
literals to their pre-D.1 values. The seal-diff windows for
(a)'s prior amendments stop seeing D.1's renames once the
sidecar reverts.

**The shape of the amendment.** Sealed-component amendment
on `framework/tools/pos-amend/`. Single-component fence (per
amendment-#22 / #41 / #46 precedent for pos-amend
amendments). New flag-or-field is the apply-side detection
+ conditional-bump path; tests under
`framework/tools/pos-amend/tests/`.

**Sequencing.** Lands AFTER D.1 (already sealed at `570092a`)
and BEFORE D.2 dispatches. Numbering: amendment **#62**
(next free after D.1's #61). Same-tree-serialize per
`feedback_serialize_amendment_builds`.

**Wall-time estimate (AI-builder):** **2–3h**. Dominated by
the rename-detection logic + tests + the retroactive revert
machinery. Calibration: pos-amend test surface is mature
(amendment-22 onward); the new logic is one method
(`_is_rename_only`), one wiring change in `apply.run`, and
one new revert path. Per Luke's duration-estimation rubric:
"single-component additive logic + tests" with mid-range
multiplier ~1.3× over raw tool-call count.

**Decisions surfaced in §11** for owner ruling. Method-shape
decisions (exact code shape, exact test names) are the
builder's call inside the locked outcome bound.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5)

Binds to **VALUE_PROPOSITION's AC.PO.2 (toolkit-primitive
growth)** as the primary spec hook. Rename-aware bookkeeping
is a new primitive the primary persona / dev-persona can
draw from when authoring future structural-relocation
amendments — not just D.2–D.5, but any future amendment whose
shape is "move components around without changing them."
AC.PO.1 (translation-burden) is a secondary hook: Luke (or
the dev-persona) no longer translates "this is a rename-only
amendment so manually skip the bump" into the apply-chore
patch; pos-amend handles it.

**No new top-level objective.** D.1.5 is method-realisation
of the existing self-upgrade (= pos-amend tooling) objective,
not a new outcome axis. Plan-author considered whether this
belongs as a new objective or as an extension of #22's
pos-amend objective — it's the latter. Halt trigger 1 does
NOT fire.

---

## 3. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude leverage

D.1.5 leverages git's existing rename-detection machinery
(`git diff --find-renames`) rather than re-implementing
content-equivalence detection. Composes on a mature primitive
the operator's tools already understand. No new Claude-SDK
surface; no new MCP server; no new hook event. The leverage
gain is a small but real reduction in pos-amend's bespoke-
ness — every line of new code is a thin wrapper around git
shellout, matching pos-amend's existing pattern (every other
git interaction in pos-amend is also shellout).

### Lens 2 — Harness + primary-persona value

**Primary-persona test.** The persona authors structural-
relocation amendments under the same `pos-amend apply` verb
they use for substantive amendments. Translation burden
drops to "name the components in the manifest"; pos-amend
translates "is this rename-only?" automatically. Without
D.1.5 the persona must hand-engineer the rename-only path
per amendment — which is exactly what happened on D.1, took
hours, and produced the hand-rolled seal in §8 of the D.1
builder plan. **Pass.**

**Harness test.** Adds a primitive (rename-aware apply) the
toolkit can use for any future structural-relocation
amendment — D.2's workspace-state migration is one
immediate consumer; future plugin-relocation, future
component-rename, future tools-reshuffling amendments all
compose on the same primitive. **Pass.**

### Lens 3 — ODD authoring

Each AC in §4 is outcome-shaped. Method-shape (exact code
shape, exact test names, exact diagnostic output strings)
is the builder's call inside the AC outcome bound. The
behaviour-count check is in §5; reverse trace per ODD §2.5
is captured in §13's plan-author check + the builder's
pre-seal §5 check captured in the eventual builder-plan.

---

## 4. Acceptance criteria

Outcome-shape only. Method-shape decisions are the builder's
call inside each AC's locked outcome bound.

### AC.D.1.5.1 — Rename-only detection works against any manifest component

**Outcome.** When `pos-amend apply` is invoked against a
manifest with `baseline: <B>` and the workspace's HEAD at
`<H>`, for each component in `manifest.components`, the
apply step computes a per-component rename-only verdict by
running git's rename-detection over the component's
old-path + new-path file set in the `<B>..<H>` window.
The verdict is True iff:

  (a) Every file under the component's prior top-level
      path (`<comp>/`) at `<B>` has either been renamed
      to a sibling under the component's new top-level
      path (`framework/<comp>/` for D-migration-shaped
      amendments, OR an arbitrary new path when the
      manifest declares an explicit rename-pair —
      builder's call on schema additions), at a
      similarity threshold ≥ 99% (R99 per `git diff
      --find-renames`), AND
  (b) No file inside the component's diff window has a
      non-rename, non-bookkeeping change. Bookkeeping
      = the seal-test sidecar (`tests/SEAL_COMMIT`) and
      the seal-diff test file (`tests/test_no_sealed_
      amendments.py` / `tests/test_cross_cutting.py`),
      because pos-amend's own apply-step is what
      modifies those files.

When the verdict is True, the component is "rename-only"
for the amendment window.

**Verification.** Test in `framework/tools/pos-amend/tests/`
constructs a fixture git repo with two fake components: one
where every file in the diff window is `R100`-renamed, one
where the diff includes `R100`-renames AND a substantive
content edit on a source file. Invokes the
rename-only-detection helper directly; asserts True for the
first component and False for the second.

### AC.D.1.5.2 — Rename-only components skip BASELINE + SEAL_COMMIT advance

**Outcome.** When `pos-amend apply` (non-`--dry-run`)
processes a manifest and the rename-only verdict (per
AC.D.1.5.1) is True for a component, the apply step:

  (a) Does NOT call `set_baseline()` on that component's
      seal-test (the BASELINE literal stays at its prior
      value).
  (b) Does NOT call `write_sidecar()` on that component's
      `tests/SEAL_COMMIT` to the new manifest baseline
      (the sidecar stays at its prior value).
  (c) DOES still call `widen_binding()` on
      `allowed_prefixes` / `allowed_files` (the new path
      prefix admissions are required for downstream
      windows even when this amendment doesn't move the
      fence origin).
  (d) Emits a structured stdout line of the shape:
      `<comp>: rename-only — BASELINE preserved at <prior-
      sha>; SEAL_COMMIT preserved at <prior-sha>;
      allowed_prefixes widened.` (Builder's call on exact
      diagnostic-string formatting, but the structure is
      observable + named.)

When the rename-only verdict is False, the existing apply
behaviour applies unchanged (BASELINE + SEAL_COMMIT advance
plus widening). **HC#1 binding — additive only on the
rename-only path.**

**Verification.** Test in `framework/tools/pos-amend/tests/`
constructs a fixture with one rename-only component and one
substantively-edited component, invokes `pos-amend apply`,
and asserts:

- Rename-only component: `BASELINE` literal in seal-test
  unchanged; `SEAL_COMMIT` sidecar unchanged; allowed_prefixes
  widened with new entries.
- Substantive component: `BASELINE` literal advanced to
  manifest baseline; `SEAL_COMMIT` sidecar written to manifest
  baseline; allowed_prefixes widened.

### AC.D.1.5.3 — `--dry-run` reports rename-only verdicts in the apply preview

**Outcome.** `pos-amend apply --dry-run` against the same
manifest reports per-component rename-only status in its
preview output. Operators reading the preview can see which
components will skip the BASELINE/SEAL_COMMIT advance before
the real apply runs. The non-dry-run admission-counter
(missing_admissions / skipped_reason) semantics are
unchanged.

**Verification.** Test in `framework/tools/pos-amend/tests/`
runs `apply --dry-run` against the AC.D.1.5.2 fixture and
asserts the preview output names rename-only verdict per
component (presence + correctness).

### AC.D.1.5.4 — Backwards-compat with v1 manifests + substantive amendments

**Outcome.** Manifests authored before D.1.5 (and any future
manifest where every component is substantively edited)
process byte-identically to pre-D.1.5 behaviour. The schema
remains v1-compatible; no manifest-author migration is
required.

**Verification.** The existing pos-amend test suite
(`tests/test_apply.py`, `tests/test_seal.py`, etc.) passes
unchanged. A new test exercises a synthetic "all-substantive"
fixture (no `R100` renames in the window) and asserts the
apply behaviour matches the pre-D.1.5 trace exactly:
BASELINE advanced, SEAL_COMMIT advanced, widening applied.
**HC#2 binding.**

### AC.D.1.5.5 — Retroactive cleanup of D.1's spurious bumps

**Outcome.** D.1.5's amendment commit ALSO reverts D.1's
spurious BASELINE/SEAL_COMMIT bumps on rename-only
components. For each of the 14 sealed components in D.1's
manifest, classify (rename-only | substantive) per the
detection logic of AC.D.1.5.1; for the rename-only set,
restore each component's:

  (a) `framework/<comp>/tests/SEAL_COMMIT` content to its
      prior-to-D.1 value (the SEAL_COMMIT value the file
      carried before D.1's apply chore at `97a4459`
      bumped it).
  (b) `BASELINE = "..."` literal in
      `framework/<comp>/tests/test_no_sealed_amendments.py`
      (or `test_cross_cutting.py` for hands-off-lifecycle)
      to its prior-to-D.1 value.

`allowed_prefixes` widening from D.1 stays in place — the
new `framework/<comp>/` admissions are still needed.
Transitional OLD prefixes added in `c7fb441` may stay or be
removed (builder's call; rule of thumb: keep them, since
ODD §10's monotonic-admission convention treats added
admissions as cheap historical tails. If removal is
attractive — they're admittedly dead post-D.2 once
workspaces no longer reference the OLD form — do it as a
separate D.5 cleanup task, not D.1.5's scope).

**Verification.** Per-component assertion in a new test
file under `framework/tools/pos-amend/tests/` (e.g.
`test_AC_D_1_5_5_retroactive_cleanup.py`) reads each
post-D.1.5 SEAL_COMMIT sidecar value + each post-D.1.5
BASELINE literal value; asserts they match the
pre-D.1 values for the rename-only set. (The pre-D.1
values are computable: each component's
prior-amendment seal commit; pulled from `git log -1
<sealing-amendment-commit>`. The test can either
hardcode them as expected literals — D-build builder's
call — or derive them via `git log` lookups in-test.
Hardcoding is simpler.)

The retroactive cleanup must NOT touch substantively-
edited components' BASELINEs or SEAL_COMMITs. Verification
test asserts those stay at the post-D.1 (advanced) values.

### AC.D.1.5.6 — Rename-only manifest schema extension (optional, builder's call)

**Outcome (optional).** If during build the rename-detection
heuristic over `git diff` proves brittle (false positives /
false negatives), the manifest schema gains an *optional*
per-component override key (e.g. `rename_only: true | false |
auto`, default `auto`). When set explicitly, the override
short-circuits the heuristic. Schema bump is to v3 (or
v1.1 — builder's call; ideally no schema bump since the
field is optional with an `auto` default that preserves
v1 semantics).

**Verification.** If the override field is added, a test
asserts: `auto` produces the heuristic verdict;
`rename_only: true` skips bumps unconditionally;
`rename_only: false` advances bumps unconditionally.

**Builder note.** Plan-author's recommendation: build
without the override first; if the heuristic is robust
enough on the D-migration manifests + the test fixtures,
skip AC.D.1.5.6 entirely. The override is insurance, not
a feature. (See §11 D-Q.5 for the surfaced decision.)

### AC.D.1.5.S — Seal-diff invariant (single-component scope)

**Outcome.** Diff between BASELINE and SEAL_COMMIT for
amendment #62 (D.1.5) is confined to:

- `framework/tools/pos-amend/src/pos_amend/` — apply.py
  + any new helper modules.
- `framework/tools/pos-amend/tests/` — new + updated
  tests.
- The 14 sealed-component tree edits required by
  AC.D.1.5.5: each rename-only component's
  `framework/<comp>/tests/SEAL_COMMIT` sidecar + each
  rename-only component's
  `framework/<comp>/tests/test_no_sealed_amendments.py`
  (or `test_cross_cutting.py`)'s BASELINE literal — both
  reverted to pre-D.1 values per the cleanup. **These
  are bookkeeping edits to sealed components, not
  substantive edits.** Plan-author has surfaced this as
  a halt-and-surface candidate (§13 finding 1) because
  it crosses fences; resolution is in D-Q.4.
- Universal admissions (`docs/rebuild/plans/`,
  `CLAUDE.md`, `docs/odd-in-pos.md`,
  `docs/odd-methodology.md`,
  `docs/rebuild/FUTURE_IDEAS.md`).

**Verification.** Standard seal-diff test in
`framework/tools/pos-amend/tests/test_no_sealed_amendments.py`
(if pos-amend gets a sidecar in this amendment) OR
through the manifest's universal admissions for tools/
(per current convention — pos-amend isn't itself
sealed, lives under `framework/tools/`). Builder
chooses based on D-Q.3 ruling.

---

## 5. Behaviour-count check (ODD §3.3 forward)

Forward direction:

| Behaviour | Backing AC |
|-----------|-----------|
| Detect rename-only per component | AC.D.1.5.1 |
| Skip BASELINE+SEAL_COMMIT bump on rename-only | AC.D.1.5.2 |
| Apply still widens allowed_prefixes on rename-only | AC.D.1.5.2 |
| `--dry-run` previews rename-only verdicts | AC.D.1.5.3 |
| Backwards-compat for substantive amendments | AC.D.1.5.4 |
| Retroactively revert D.1's spurious bumps | AC.D.1.5.5 |
| (Optional) schema override for explicit rename-only | AC.D.1.5.6 |
| Seal-diff confined to fence | AC.D.1.5.S |

Forward check passes (7 behaviours / 7 ACs, with .6 optional).

Reverse direction (every code path / branch / dependency / test
in D.1.5's diff → backing AC) is the builder's pre-seal check,
captured in the eventual builder-plan §5 (per amendment-#46/#47
precedent). Plan-author has done a partial reverse trace in
§13 to surface known fence-crossings.

---

## 6. Hard constraints (binding from dispatch)

**HC#1.** No regression of pos-amend's current behaviour for
substantively-changed amendments (the common case). The
rename-aware path is purely additive — wrapped as a guarded
branch around the existing BASELINE+SEAL_COMMIT bump logic.
**Verification:** AC.D.1.5.4.

**HC#2.** Backwards-compat with existing manifests. No
schema changes required for existing manifests (every D.1
through D.5 manifest works without any new fields). If the
optional override (AC.D.1.5.6) is added, default `auto`
preserves v1 behaviour. **Verification:** AC.D.1.5.4 +
AC.D.1.5.6.

**HC#3.** D.1 retroactively benefits — D.1.5's scope
includes a one-shot revert of D.1's spurious BASELINE/
SEAL_COMMIT bumps for rename-only components. Without the
revert, prior amendments' AC.X.S tests continue to fail
post-D.1.5 (D.1.5 only fixes future amendments). With the
revert, the cascade unwinds. **Verification:** AC.D.1.5.5.

**HC#4.** No new third-party deps. Use `subprocess` shellout
to git, the existing `pos_amend` modules, and stdlib. Same
pattern as `pos_amend.commands.seal._discover_sealed_components`
+ `_run_pytest` + the seal-diff test framework's existing
`subprocess.check_output(['git', 'diff', ...])` shape.

**HC#5.** Halt-and-surface contract: plan-author has surfaced
the cross-fence cleanup (D-Q.4) as a halt-trigger. Builder
must acknowledge the resolution (D-Q.4 ruling) before edits
to non-pos-amend trees land.

**HC#6.** No `--amend`. Standard: every corrective commit is
a NEW commit (`feedback_no_amend_in_agent_dispatches`).

**HC#7.** Plan-before-code: this plan-doc + the eventual
builder-plan exist before any source edit
(`feedback_plan_before_code`).

---

## 7. Out of scope (explicit)

Per dispatch + halt-and-surface analysis:

- **Reverting D.1's transitional OLD prefix patches in 13
  test_no_sealed_amendments.py files (commit `c7fb441`).**
  ODD §10's monotonic-admission convention treats added
  admissions as cheap historical tails; removing them is a
  separate cleanup. Surface to D.5 (D-migration cleanup
  amendment) at end of D.3.
- **Touching the inner AC.X.S tests (estimated 20–50 across
  primary-persona, hands-off-lifecycle, etc.) directly.**
  D.1.5's mechanism (revert SEAL_COMMITs to pre-D.1 values
  on rename-only components) means the inner AC.X.S tests
  no longer see D.1's renames in their diff window. They
  pass unchanged. If they don't (e.g. because some
  component's prior amendment used a different sealing
  baseline that itself overlapped with D.1's diff), the
  builder halts and surfaces — but the design's first-
  principles expectation is that the cleanup unwinds the
  cascade structurally without test edits.
- **Adopting `git diff --diff-filter=R` as the *only*
  detection mechanism without considering content-hash
  cross-check.** See D-Q.1 — plan-author recommends git's
  rename-detection as the primary mechanism with sha256-
  of-tree as a research-only fallback if the heuristic
  proves brittle in build.
- **Schema v3 manifest.** No new manifest schema version is
  required. The optional override (AC.D.1.5.6, if built)
  is an additive optional field; no schema bump.
- **Retroactive cleanup of pre-D.1 amendments' bookkeeping.**
  D.1.5's revert is scoped to D.1's window only. Any
  future amendment that itself ships rename-only
  components benefits going forward via the standard
  apply path; no cleanup ladder.
- **D.2's plan-doc edits.** D.2 still needs to be authored
  with the post-D.1.5 understanding; that's the parent-
  plan's concern (D-migration §13 finding gets an
  addendum after D.1.5 lands), not D.1.5's scope.

---

## 8. Implementation order

Suggested order for D.1.5's builder. Sequential per
`feedback_serialize_amendment_builds`.

1. **Read session-start corpus + this plan-doc + D.1's
   builder-plan §8 + the D.1 surface artefact.**
2. **Author builder-plan** at
   `docs/rebuild/plans/d-migration-1-5.builder-plan.md`
   per `feedback_plan_before_code`.
3. **Implement rename-only detection** in `pos_amend.apply`
   (or a new `pos_amend.rename_detection` module — builder's
   call). Helper signature: `is_rename_only(repo_root,
   manifest, component) -> bool` (or a richer return-shape
   carrying the set of renames, builder's call).
4. **Wire the detection into `apply.run`'s component loop.**
   Guard the `set_baseline()` + `write_sidecar()` calls on
   the rename-only verdict; widening calls stay unconditional.
   Diagnostic stdout line per rename-only component.
5. **Implement retroactive cleanup** as a one-shot path in
   `apply.run` keyed on the manifest's slug or amendment-
   number — i.e., when the manifest is D.1.5's own manifest
   AND `--cleanup-d1` (or equivalent) is passed, OR (cleaner)
   the cleanup is invoked manually by a new `pos-amend
   cleanup-d1` subcommand. Builder's call on the
   subcommand-shape question; plan-author's recommendation
   is a flag on `apply` since the cleanup is one-shot. See
   D-Q.2.
6. **Author tests** (every AC in §4 backed by ≥1 test). New
   tests in `framework/tools/pos-amend/tests/`. Fixture
   shape: tmpfs git repos with fake "rename-only" and
   "substantive" components + manifests pointing at them.
   Reuse the existing `_make_fake_component` fixture
   builder from `tests/test_seal.py` if helpful.
7. **Author manifest** at
   `docs/rebuild/plans/d-migration-1-5.manifest.yaml` per
   §9 sketch. Single-component (pos-amend) OR universal-
   admissions-only (per D-Q.3).
8. **Run touched-component tests**
   (`framework/tools/pos-amend/tests/`); iterate.
9. **`pos-amend apply --dry-run --plan d-migration-1-5.
   manifest.yaml`**; iterate until clean.
10. **`pos-amend apply --plan d-migration-1-5.manifest.yaml`**
    — applies (a) D.1.5's apply-chore commit + (b) the
    retroactive cleanup. Stages per the manifest's
    components + the cleanup paths under each rename-only
    `framework/<comp>/tests/`.
11. **Commit** with subject:
    `feat(framework/tools/pos-amend): D-migration D.1.5 —
    rename-aware seal + D.1 cleanup (amendment #62,
    AC.D.1.5.1–AC.D.1.5.S)`.
12. **`pos-amend seal --plan-doc /Users/lukeivers/ivers-corp-pos-v2/docs/rebuild/plans/d-migration-1-5.md
    --plan d-migration-1-5.manifest.yaml`**.
13. **Empirical post-seal verification:** run the AC.X.S
    test sweep across rename-only components. Expectation:
    every prior-amendment AC.X.S test now passes (the
    cascade unwinds). If not, halt + surface for resolution.

**Speedups applied per
`feedback_amendment_dispatch_speedups`:**

- (a) Scoped-sweep seal: `pos-amend seal --scoped-sweep`
  on the pos-amend touched component (single-component).
- (b) Pre-seal smoke: pos-amend's full test suite passes
  before commit; full repo-wide pytest skipped pre-seal.
  Empirical AC.X.S sweep is a *post-seal* verification
  (step 13 above) for HC#3 confidence.
- (c) Inline methodology snippets in commit prose.

---

## 9. Bookkeeping surface (per-AC plan-doc convention)

### D.1.5 manifest sketch (single-component)

```yaml
schema_version: 1
amendment:
  number: 62  # next free after D.1's #61
  slug: d-migration-1-5-rename-aware-seal
  title: "D-migration D.1.5 — pos-amend rename-aware seal + D.1 cleanup"

# BASELINE: the seal commit of D.1, since D.1.5 lands as the
# next amendment after D.1. Plan-doc backfilling commit (cdd6e2a)
# may also satisfy as baseline; builder's call between cdd6e2a /
# 570092a / current HEAD-1 at dispatch.
baseline: <HEAD~1 SHA at D.1.5 dispatch>

plan: docs/rebuild/plans/d-migration-1-5.md

seal_description: "D-migration D.1.5 — pos-amend rename-aware seal + D.1 cleanup"

# D.1.5 is single-component (pos-amend). pos-amend itself is
# unsealed (lives under framework/tools/, no SEAL_COMMIT
# sidecar pre-D.1.5). Per D-Q.3 ruling, the manifest either
# (a) declares no components + admits framework/tools/pos-amend/
# under universal_paths (matches amendment #22's shape), or
# (b) declares a synthetic component "pos-amend" that points
# at a new SEAL_COMMIT sidecar created by D.1.5 itself
# (sealed-pos-amend convention).
# Plan-author recommends (a) — pos-amend has historically been
# admitted via universal/extra prefixes; introducing a sidecar
# in this amendment is an in-scope creep.

components: []  # pending D-Q.3 ruling

universal_paths:
  prefixes:
    - docs/rebuild/plans/
    - framework/tools/pos-amend/
  files:
    - CLAUDE.md
    - docs/odd-in-pos.md
    - docs/odd-methodology.md
    - docs/rebuild/FUTURE_IDEAS.md

# Cleanup target list — the rename-only components from D.1.
# Listed here so the plan-doc's reader can audit which components
# get reverted. Computed at build time by the builder (pulling
# pre-D.1 SEAL_COMMIT values from `git log` of each component's
# prior amendment-seal commit).
# Components whose D.1 diff was rename-only (no substantive edits
# to source/test files, only `git mv` plus apply-step bookkeeping):
#   - cost-governance
#   - graceful-degradation
#   - memory-system
#   - objective-tracker
#   - observability-aggregator
#   - reversibility-primitive
#   - safety-layer (no SEAL_COMMIT pre-D.1; no-op for cleanup)
#   - scope-of-work (no SEAL_COMMIT; no-op)
#   - self-correction
#   - telegram-interface
#   - workspace-sync (TBD — verify; D.1's restructure may have
#     edited workspace-sync's source code paths)
#
# Components with substantive D.1 edits (source/test edits beyond
# rename) — DO NOT revert their SEAL_COMMIT/BASELINE:
#   - hands-off-lifecycle (first_run_helper.py, .claude template)
#   - workspace-bootstrap (first_run_scaffold.py LAUNCHD_TEMPLATES)
#   - primary-persona (TBD — verify; D.1 may or may not have
#     edited primary-persona substantively)
#   - self-upgrade (TBD — verify)
#   - orchestrator (TBD — verify)
#
# Builder finalises this list at build time via per-component
# `git diff --find-renames=99% --name-status 57d735f..0d599bb
# -- <old-path> <new-path>` inspection. (See §10 build-step.)

narrative:
  target: framework/hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run
  body: |
    # Amendment #62 — D-migration D.1.5 — pos-amend rename-aware seal + D.1 cleanup

    2026-04-XX (TBD at dispatch). Interstitial amendment between D.1
    (sealed at 570092a) and D.2 (yet to dispatch). Closes the
    structural gap surfaced during D.1's seal cycle: pos-amend's
    apply step bumped BASELINE + SEAL_COMMIT uniformly across all 14
    sealed components in D.1's manifest, including components whose
    actual diff in D.1's window was rename-only (every file `R100`
    per `git diff --find-renames`). The uniform bump made every
    prior amendment's AC.X.S seal-diff test see paths from D.1's
    rename window inside its own (now-stale) diff window, producing
    a fence-violation cascade across primary-persona,
    hands-off-lifecycle, and other components.

    D.1.5's fix: per-component rename-only detection in `pos-amend
    apply`. When a component's amendment-window diff is entirely
    `R<threshold>`-renames (modulo apply-step bookkeeping sidecars),
    skip the BASELINE + SEAL_COMMIT bump for that component. The
    fence origin stays at the prior seal commit; the prior amendment's
    AC.X.S tests continue to assert against their original (and
    correct) diff window.

    D.1.5 also reverts D.1's spurious BASELINE/SEAL_COMMIT bumps for
    each rename-only component, restoring each to its pre-D.1 value.
    The cascade unwinds structurally — no inner AC.X.S test edits
    required. The D.1 transitional OLD prefix patches in 13
    `test_no_sealed_amendments.py` files (commit `c7fb441`) stay
    in place per ODD §10's monotonic-admission convention; D.5
    (D-migration cleanup) may prune them later.

    Surface edited:

      - framework/tools/pos-amend/src/pos_amend/commands/apply.py
        — rename-only detection helper + conditional-bump path.
      - framework/tools/pos-amend/tests/ — new tests for AC.D.1.5.1
        through AC.D.1.5.S.

    Reverted (cleanup):

      - 8–10 sealed components' SEAL_COMMIT sidecars + BASELINE
        literals — restored to pre-D.1 values. Component list in §9
        of the plan-doc.

    Behaviour:

      - rename-only verdict computed via `git diff --find-renames`
        against the manifest baseline.
      - Apply skips BASELINE + SEAL_COMMIT bump on rename-only;
        widening still applies.
      - --dry-run previews per-component rename-only verdict.
      - Schema unchanged (no new manifest fields required for v1
        semantics).

    Backwards-compat:

      - HC#1: substantive amendments byte-identical to pre-D.1.5
        behaviour. Existing test suite passes unchanged.
      - HC#2: existing manifests parse + apply unchanged. No
        manifest-author migration required.

    BASELINE <SHA> (HEAD at dispatch). pos-amend not sealed; admitted
    via framework/tools/pos-amend/ universal-paths prefix per
    amendment #22's pattern.

    Next: D.2 dispatches against the post-D.1.5 tree. D.2's
    rename-only sub-set (e.g. components that get only a path edit
    inside their tree) flows through the new path automatically.
```

---

## 10. Halt-and-surface triggers (binding for builder)

The builder must halt and surface (do NOT silently extend) on:

1. **Rename-detection heuristic disagrees with reality.** If
   the heuristic returns True for a component the operator
   knows had substantive D.1 edits, OR False for a component
   the operator knows was rename-only, halt + surface (the
   builder may have hit a corner case — e.g. a component
   whose D.1 diff included a content-edit + rename-pair on
   the same file, which `git diff --find-renames` may
   report as `R<low-similarity>` or `M`).
2. **Cleanup target list audit fails.** If `git log -1` of a
   component's prior amendment-seal commit doesn't exist
   (e.g. the component was never sealed before its first
   amendment), halt + surface; cleanup is a no-op for that
   component.
3. **Sealed-component fence violation.** AC.D.1.5.5's
   cleanup edits `framework/<comp>/tests/SEAL_COMMIT` and
   the seal-test BASELINE literal across multiple components.
   pos-amend itself owns the bookkeeping convention, so
   editing those files via the apply step is doctrinally
   permitted (this is what apply DOES for substantive
   amendments). But the multi-component fence shape requires
   D-Q.4 resolution before the cleanup commit lands.
4. **Wall-time exceeds 1.5h plan-authoring or 3h builder.**
5. **Pre-existing pos-amend test fails post-edit.** Halt;
   investigate the regression before continuing.
6. **Cross-component AC.X.S test still fails after the
   retroactive cleanup.** Halt + surface — the cleanup
   should unwind the cascade structurally; if it doesn't,
   the design assumption (cascade is purely SEAL_COMMIT-bump-
   driven) is wrong and we need to investigate further.
7. **Manifest schema needs a v3 bump for the optional
   override.** Halt + surface; either skip the override
   (build only AC.D.1.5.1–.S) or surface the v3 bump for
   owner ruling.
8. **D-Q.4 multi-component edit cross-fence is unresolvable
   under D.1.5's locked single-component shape.** Halt +
   surface; either expand D.1.5's fence or split into
   D.1.5a (pos-amend logic) + D.1.5b (cleanup).

---

## 11. Decisions surfaced for owner ruling

**All 5 D-Q decisions LOCKED 2026-04-27 by primary persona under confidence-delegation** (Luke 2026-04-27 broad-autonomy directive). Detail preserved below for audit trail.

- **D-Q.1 LOCKED:** path (a) — `git diff --find-renames=99%` with apply-step-bookkeeping whitelist for A/D pairs. Standard git tooling; deterministic at the 99% threshold; whitelist handles pos-amend's own bookkeeping deletes/creates per Finding 4.
- **D-Q.2 LOCKED:** path (a) — bundle retroactive cleanup into `pos-amend apply` via manifest cleanup directives. One-shot; reuses existing apply-flow; doesn't add a new subcommand surface.
- **D-Q.3 LOCKED:** path (b) — admit pos-amend via universal-paths prefix per amendment #22 precedent. Don't seal pos-amend in D.1.5. High confidence.
- **D-Q.4 LOCKED (LOAD-BEARING):** path (a) — treat cross-fence cleanup as in-scope by doctrine. pos-amend is THE canonical SEAL_COMMIT/BASELINE writer; its touching of any component's bookkeeping sidecars is structurally legitimate, not a fence violation. Splitting (option c) doubles wall-time without architectural benefit; multi-component fence (option b) over-formalizes what's already pos-amend's role.
- **D-Q.5 LOCKED:** path (b) — skip the optional `rename_only:` manifest override. Heuristic-only; build override only if a fixture surfaces an edge case.

**Decisions detail follow below for audit-trail purposes.**



### D-Q.1 — Detection mechanism

**Question.** Use `git diff --find-renames` (similarity-
threshold heuristic) OR sha256-of-tree (content-equivalence
hash) as the rename-only detection mechanism?

**Recommendation.** **(a) `git diff --diff-filter=ADMRT
--find-renames=99%`**, with the test that "every entry in
the diff is `R<99|100>` plus optionally A/D pairs that are
themselves apply-step bookkeeping sidecars."

**Alternatives:**

- **(b) sha256-of-tree.** Compute the recursive sha256 of
  the component's old-path tree at `<B>` and the
  component's new-path tree at `<H>`; if they match, the
  component is rename-only. Conceptually cleaner — content
  equivalence is what we actually want. But the
  implementation is more code (recursive walk + hash) and
  has subtleties: file-mode changes, executable-bit changes,
  symlink content, and the non-tracked workspace-state
  files inside the component's tree are all edge cases.
- **(c) Hybrid.** Run (a); cross-check with (b) on
  components where (a) returns True. If they disagree,
  halt + surface for owner ruling.

**Rationale for (a).** git's rename-detection is mature,
well-audited, fast, and fits the existing pos-amend
shellout pattern. The 99% similarity threshold catches
rename-with-trivial-content-edit cases (e.g. a header
comment that mentions the new path) the way we want them
caught (treat as rename-only; the content edit is
incidental). The 100% threshold is too strict — D.1's own
data shows hands-off-lifecycle had `R099` entries
(`first_run_settings.py` had a path-string edit during
move).

**Confidence.** **Medium-high.** Plan-author accepts (a)
with a builder-side option to fall back to (c) if any AC's
test fixture surfaces a false-verdict edge case.

### D-Q.2 — Retroactive cleanup invocation shape

**Question.** Does the D.1 cleanup land as part of the
standard `pos-amend apply` against D.1.5's manifest, OR as
a new `pos-amend cleanup-d1` subcommand?

**Recommendation.** **(a) bundled into `apply` via
manifest-driven cleanup directives.** D.1.5's manifest
declares (in a new `cleanup:` block, OR as
`extra_files`-shaped directives per component) the exact
SEAL_COMMIT sidecar and BASELINE literal values to revert
to. `pos-amend apply` reads the directives and writes them
during the same chore-shape commit that lands D.1.5's
sidecar advances.

**Alternatives:**

- **(b) New `pos-amend cleanup-d1` subcommand.** Hardcoded
  one-shot logic. Cleaner separation but more code +
  bigger surface change in pos-amend's CLI. Not generalisable.
- **(c) Manual hand-edit + a separate `chore:` commit
  alongside D.1.5's apply chore.** Builder hand-edits the
  10 sidecar files + 10 BASELINE literals manually; pos-
  amend doesn't carry the cleanup logic at all. Simple but
  loses audit-trail-mechanisation.
- **(d) Generic cleanup directive in apply.** Bigger
  surface — apply gains a generic `cleanup:` shape that
  any future amendment can use (e.g. for "reset SEAL_COMMIT
  to <sha>" directives). Higher leverage if more
  cleanups are anticipated; over-engineering otherwise.

**Rationale for (a).** Mechanises the cleanup in the same
verb as the apply (operator runs one command, gets one
chore commit). Doesn't generalise the cleanup shape into a
re-usable primitive (so we don't spend code on hypothetical
future cleanups). Manifest-driven directives keep the
audit trail in version control.

**Confidence.** **Medium.** (a) and (c) are roughly equally
defensible. Plan-author leans (a) for mechanisation /
audit-trail; (c) is the pragmatic option if the manifest-
driven shape proves complicated.

### D-Q.3 — D.1.5 sealed-component fence shape

**Question.** Does D.1.5's manifest declare pos-amend as a
sealed component (creating `framework/tools/pos-amend/tests/SEAL_COMMIT`
in this amendment), OR admit pos-amend via the universal-
paths prefix `framework/tools/pos-amend/` (per amendment
#22's pattern)?

**Recommendation.** **(b) admit via universal-paths
prefix.** pos-amend has historically been admitted via
`tools/` (pre-D.1) and is now admitted via
`framework/tools/` (post-D.1) in every sealed component's
allowed_prefixes tuple. Introducing a new SEAL_COMMIT
sidecar in this amendment is in-scope creep.

**Alternatives:**

- **(a) Seal pos-amend.** Add `framework/tools/pos-amend/tests/SEAL_COMMIT`
  + `test_no_sealed_amendments.py`; declare in the manifest;
  inherit the standard sealed-component machinery. Cleaner
  long-term (pos-amend gets the same fence discipline as
  every other component). But — bigger amendment surface,
  introduces a dependency on the seal-diff test shape that
  pos-amend doesn't currently have. Defer to a future
  amendment.

**Rationale for (b).** Matches amendment #22's precedent;
keeps D.1.5 minimal; the structural-fence argument for
sealing pos-amend is genuine but orthogonal to D.1.5's
objective.

**Confidence.** **High.**

### D-Q.4 — Multi-component cleanup-edit fence

**Question.** D.1.5's retroactive cleanup edits files in
8–10 sealed components' `tests/` directories (the SEAL_COMMIT
sidecar + the seal-test BASELINE literal). pos-amend's apply
step doctrinally OWNS those files (every sealed-component
amendment edits them; that's what apply DOES). But fence
discipline says D.1.5 (a single-component pos-amend
amendment) shouldn't touch other sealed components'
directories. Resolution?

**Recommendation.** **(a) Treat as in-scope by doctrine —
pos-amend's apply step is the canonical writer of
SEAL_COMMIT + BASELINE across every component's tree, and
D.1.5 is itself a pos-amend amendment.** The seal-diff
window for D.1.5 admits the cleanup edits via the
universal-paths shape (every rename-only component's
`framework/<comp>/tests/SEAL_COMMIT` + seal-test files
are admitted by D.1.5's manifest in addition to the
canonical `framework/tools/pos-amend/` prefix). Builder
authors the universal admissions accordingly.

**Alternatives:**

- **(b) Multi-component sealed amendment.** Declare D.1.5
  as multi-component; list every rename-only component as
  a sealed component in the manifest. Larger fence, more
  apply-step surface, but matches the "any sealed-component
  edit lands in a multi-component amendment" rule. Less
  ergonomic — D.1.5 isn't conceptually about those
  components, just bookkeeping.
- **(c) Split D.1.5 into D.1.5a (pos-amend logic) +
  D.1.5b (cleanup).** D.1.5a is a clean single-component
  pos-amend amendment; D.1.5b is a multi-component cleanup
  amendment. Cleaner fence discipline but two
  amendment-cycles for one logical change.

**Rationale for (a).** pos-amend's apply is THE canonical
mechanism that edits SEAL_COMMITs + BASELINEs; the cleanup
is mechanically the same path with reverted (rather than
advanced) values. The doctrine is: pos-amend's apply has
fence-crossing privilege by design. (Confirm this doctrine
with Luke if uncertain — see plan §13 finding 1.) The
manifest's universal_paths admission for the cleanup
target paths makes the seal-diff invariant clean.

**Confidence.** **Medium.** This is the load-bearing
decision; pulling Luke's read is highest-value at dispatch
time.

### D-Q.5 — Optional manifest override (`rename_only:`)

**Question.** Build the optional `rename_only: true | false
| auto` override (AC.D.1.5.6), or skip?

**Recommendation.** **(b) skip — build heuristic-only.**
Add the override only if a build-time fixture surfaces a
case the heuristic gets wrong. ODD §4: not building
unrequested machinery.

**Alternatives:**

- **(a) build the override.** Insurance against heuristic
  edge cases; a manifest author can force a verdict
  explicitly. Adds ~20 LOC + 1 schema field + 1 test.

**Rationale for (b).** D-migration's known manifests (D.1,
D.2 prospective) don't surface a heuristic edge case in
plan-authoring's read of the codebase. If the build does
surface one, the builder halts (per §10 trigger 1) and
surfaces; we add the override at that point under owner
ruling.

**Confidence.** **High.**

---

## 12. Sequencing context

**Where D.1.5 sits in the D-chain:**

```
D.1   feat (0d599bb) → apply chore (97a4459) → fix (c7fb441) → seal (570092a) → §14 backfill (cdd6e2a)   [LANDED]
D.1.5 feat (#62) → apply chore → seal (#62 chore-seals)                                                  [THIS PLAN]
D.2   feat (#63) → apply chore → seal                                                                    [PENDING; benefits from D.1.5]
D.3   feat (#64) → apply chore → seal                                                                    [PENDING]
D.4   feat (#65) → apply chore → seal                                                                    [PENDING]
D.5   feat (#66) → apply chore → seal                                                                    [PENDING]
```

**Why D.1.5 is critical-path before D.2.** D.2's manifest
will list multiple components (workspace-bootstrap +
hands-off-lifecycle + workspace-sync + possibly self-
upgrade). D.2's diff will substantively edit
workspace-bootstrap (scaffold) + hands-off-lifecycle (hook
paths) + workspace-sync (sync_protected) + self-upgrade
(migration script). For those components, the BASELINE +
SEAL_COMMIT advance is correct. But D.2's manifest also
needs to *not* re-trigger the cascade for components it
admits via universal/cross-component-partner prefixes —
i.e., D.2's apply step touching `framework/observability-
aggregator/tests/SEAL_COMMIT` (already at c7fb441 today;
should it advance to D.2's amendment or stay at the
prior seal?).

After D.1.5 lands and reverts the spurious bumps, the
SEAL_COMMITs of rename-only components return to their
pre-D.1 values. D.2's manifest can then either explicitly
list rename-only components (in which case D.1.5's
detection short-circuits the bump) or omit them entirely
from the components list (in which case D.2 doesn't touch
their SEAL_COMMIT at all — the cleanest shape).

**Effect on D.3, D.4, D.5.** D.3 (workspace-sync only) +
D.4 (workspace-bootstrap only) are single-component; the
rename-only path likely doesn't fire for them (their
diffs are substantive). D.5 (workspace-sync cleanup) is
optional + small. None of D.3-D.5 are critical-path-
gated by D.1.5, but they all benefit from the cleaner
apply semantics.

---

## 13. Halt-and-surface findings during plan authoring

**Finding 1 — pos-amend's apply step is the canonical
SEAL_COMMIT/BASELINE writer; "fence-crossing" doctrine
needs explicit confirmation.** D-Q.4 captures this. Plan-
author leans (a) — apply has fence-crossing privilege by
design, evident from amendment #22's apply behaviour. But
this is the load-bearing decision; surface to Luke.

**Finding 2 — The pre-D.1 SEAL_COMMIT values for
rename-only components are recoverable via `git log`.**
For each rename-only component, the pre-D.1 SEAL_COMMIT
value is the SEAL_COMMIT sidecar value at commit `57d735f^`
(immediately before D.1's apply chore at `97a4459`). The
builder pulls this via `git show 57d735f^:<comp>/tests/SEAL_COMMIT`
at build time. (Pre-D.1 path is bare `<comp>/tests/SEAL_COMMIT`,
not `framework/<comp>/tests/SEAL_COMMIT`.) Mechanical.

**Finding 3 — pos-amend test fixtures use post-D.1 layout.**
`tests/test_seal.py`'s `_make_fake_component` creates fixtures
under `framework/<name>/` — matches post-D.1. New rename-
detection tests can extend the same fixture-builder by adding
a "post-rename state" + "pre-rename state" parameter (i.e.,
a fixture that simulates "this component was renamed during
the amendment" requires staging old-path + new-path commits).
Builder's call on exact fixture shape.

**Finding 4 — `--diff-filter=ADMRT` may need refinement.**
D.1's actual diff for cost-governance includes both `R100`
entries (the renamed source files) AND `D` entries (the
old `cost-governance/tests/SEAL_COMMIT` deleted by the
apply chore at `97a4459`) AND `A` entries (the new
`framework/cost-governance/tests/SEAL_COMMIT` added by
the apply chore). The detection logic must whitelist
A/D pairs that are apply-step bookkeeping (matching the
component's own seal-test/sidecar paths) rather than
treating them as substantive changes. Builder authors the
whitelist.

**Finding 5 — `c7fb441` (D.1's transitional OLD prefix
fix) is a substantive edit by the rename-detection
metric.** It touches 13 `test_no_sealed_amendments.py`
files — content edits, not renames. So if D.1.5's
rename-detection runs against the window `BASELINE..c7fb441`
or `BASELINE..570092a` (the seal commit), it will see
those edits and classify several components as
substantive-rather-than-rename-only. D.1.5's cleanup
machinery must use the window `57d735f..0d599bb`
(D.1's amendment commit, not the seal commit) for the
rename-only verdict — which IS the conceptually correct
window (the amendment-commit fence; the seal commit is
post-fence-advance machinery). Builder must thread this
correctly. Surfaced as a build-time pitfall for builder
awareness.

**Finding 6 — D.2 plan needs an addendum after D.1.5
lands.** The D.2 amendment's plan section in
`d-migration.md` doesn't currently account for the
rename-aware behaviour. After D.1.5 lands, the parent
plan needs a small note that D.2 leverages D.1.5's
detection (or a confirming statement that D.2's
substantive components legitimately advance their bumps).
Captured as a follow-up task; not in D.1.5's scope.

**Finding 7 — `safety-layer` and `scope-of-work` are
unsealed pre-D.1.** These have no SEAL_COMMIT sidecar.
The cleanup is a no-op for them — there's no sidecar to
revert. The detection logic should handle this gracefully:
if a component has no prior SEAL_COMMIT sidecar (i.e., the
file didn't exist at `57d735f^`), the cleanup skips it
entirely. Same for the BASELINE literal — if pre-D.1
BASELINE wasn't set in the seal-test, the revert is a
no-op.

---

## 14. Method-decision register (post-build; backfilled by `pos-amend seal`)

(To be populated by the builder + `pos-amend seal --plan-doc`
mechanism.)

### Commit SHAs

- Amendment commit: `8908b1980dcfb3387a0473fde6fae3cf8d5b034c` —
  `fix(framework/tools/pos-amend): apply skips bump-then-revert noise for cleanup_directive components`
- Seal commit: `21e27f244deb3fe04ff8eac27b0ef8182f49acb7` —
  `chore(seals): D-migration D.1.5 — pos-amend rename-aware seal + D.1 cleanup — cost-governance+graceful-degradation+memory-system+observability-aggregator+reversibility-primitive+self-correction+self-upgrade+telegram-interface at 8908b19`
### Method-shape decisions

(Populated by builder during build. Expected entries:
exact rename-detection helper signature + module placement;
exact wording of stdout diagnostic line; exact manifest
shape for the cleanup directives; exact cleanup invocation
verb; whether AC.D.1.5.6 was built or skipped.)

---

## 15. Plan-author run summary

**Walltime:** ~50 minutes of the 1.5h ceiling (under).

**Halts surfaced:** 0 critical halts. 7 informational
findings in §13 for builder awareness.

**Decisions for owner ruling:** **5** — D-Q.1 (detection
mechanism), D-Q.2 (cleanup invocation shape), D-Q.3
(D.1.5 sealed-component fence), D-Q.4 (multi-component
cleanup-edit fence — load-bearing), D-Q.5 (optional
manifest override).

**Outcome-shape decisions only:** True. Method-shape
decisions deferred to builder.

**Plan-doc + vars-file land alongside this commit.**
Companion vars-file at `docs/rebuild/plans/d-migration-1-5.vars.yaml`.
