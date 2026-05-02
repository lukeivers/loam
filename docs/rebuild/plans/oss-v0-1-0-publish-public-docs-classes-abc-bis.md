# OSS v0.1.0 publish — public-docs Class C-bis (test-fence) — sub-plan

**Status:** plan-doc (pre-build, plan-before-code). 2026-05-02.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2 / future loam).
**Predecessor:** C1 sealed `e2cbeec` + C2 HALT (plan-doc `oss-v0-1-0-publish-public-docs-classes-abc.md` §14 D-build.ABC-C2.HALT). HEAD `c868618` (§14 backfill). Tree clean.
**Successor target:** C2-prime re-plan + dispatch (separate plan-doc at `docs/rebuild/plans/oss-v0-1-0-publish-public-docs-classes-abc-prime.md`).
**Authority:** Dispatcher autonomy directive 2026-05-02 (locked: industry-convention shape — no public-shipping artefact under any modern Python package's `tests/` directory). C2 halt narrative at `<workspace>/.scratch/claude-output/oss-v0-1-0-publish-classes-abc-c2-halt.md` §4 Option A.
**Programme master:** `docs/rebuild/plans/oss-v0-1-0-publish.md` — §3 AC.OSS.3 source.
**M11 plan:** `docs/rebuild/plans/oss-v0-1-0-publish-dry-run.md` — §5 AC.M11a.2 outcome bound.

---

## 1. Summary / TLDR

**Single-glob partition manifest extension. Adds `**/tests/**` to the M2 partition manifest's `dev_only:` block.** Closes the 109-file test-residual scope at one stroke per industry convention (no public-shipping artefact under any modern Python package's `tests/` directory; tests run during CI but are not exposed to user-runtime in v1.0 OSS source tarballs / wheels / synthesised public trees).

C2 dispatch HALTED at HT-C2.4 (>30 Class C files surfaced) when build investigation discovered the C2 plan §5.4 enumeration of 26 production files was partial — the actual literal-match population against AC.M11a.2 was 130 files (109 test files + 21 production files). Class C resolution requires two amendments in series:

- **C2-bis (THIS PLAN)** — mechanical bookkeeping; reclassifies all `**/tests/**` to `dev_only`. Closes the 109-file test residual.
- **C2-prime (separate plan-doc, dispatched after C2-bis seals)** — judgment-laden per-file remediation against the smaller accurate population (~21 production files). Plan-author dispatched separately.

Single-component fence per M7-partition-fix precedent: `framework/tools/pos-publish-framework-only/`; HOL no-op narrative anchor.

**Estimated AI-time:** 20-30 min wall-clock (pure manifest YAML + HOL anchor + synthesis smoke check; no behaviour-code edits).

---

## 2. Owner ruling captured

Dispatcher autonomy directive 2026-05-02 locked the decision: **add `- glob: "**/tests/**"` to the `dev_only:` block.** No design ambiguity — the shape is industry-convention (most v1.0 OSS releases don't ship internal test suites in the source tarball; tests run during CI but not at user-runtime). C2 halt-narrative §4 Option A captures the reasoning + recommendation.

No decisions register entries — see §11.

---

## 3. Spec-objective placement (per CLAUDE.md §2.5)

**Binds to:**

- **AC.OSS.3** (no dev-discipline machinery in synthesis output). All 109 test files contain `docs/rebuild`, `loam-mode`, or other AC.OSS.3 banned literals as assertion strings, fixture content, comments, or docstrings. Reclassifying `**/tests/**` as `dev_only` removes them from the synthetic public tree at one stroke.
- **AC.OSS.1** (stranger-bootable). A stranger reading the public synthesis output never sees internal test infrastructure (which is dev-discipline machinery, not user-facing capability).
- **AC.PO.1** (translation-burden absorption). Stranger never sees pos-v2-internal test vocabulary (`test_no_sealed_amendments`, `test_AC_*`, fixture path-assertions referencing `docs/rebuild/`).
- **AC.PO.2** (toolkit-primitive growth). The `**/tests/**` glob in `dev_only` establishes a standing partition convention any future component inherits.

**Ladders to:** AC.OSS-M2.4 (every leaf path classifies modulo audit_excludes) → AC.OSS.6 (final scrub) → AC.PO.1 + AC.PO.2 (prime objective).

**ODD §2.5 reverse-direction commitment.** Each AC below is outcome-shape; method-shape (which exact glob position in the YAML, which exact provenance comment) is the builder's call inside the AC outcome bound.

---

## 4. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude-leverage-first

N/A — pure manifest bookkeeping; no Claude-native primitive in scope. The synthesis tool already composes around `git ls-tree` + the manifest classifier; this fix is a single line in the manifest's authored data. The fix EXTENDS the existing M2 partition primitive; doesn't invent a new primitive.

**Pass.**

### Lens 2 — Harness + primary-persona value

- **Primary-persona test (translation burden):** post-fix, a stranger running through any session-start corpus or browsing the synthesis output never sees the internal test suite (which carries dev-discipline vocabulary as a side effect of its purpose: validating dev-mode behaviour). Translation burden absorbed.
- **Harness test (toolkit primitive):** the M2 partition's `dev_only` block grows by 1 entry that establishes `**/tests/**` as a standing dev-only glob. Future v0.x components inherit; each component's tests automatically classify dev-only without manifest amendment.

**Pass on both tests.**

### Lens 3 — ODD authoring

The AC below is outcome-shape, observable, deterministic. Method-shape (exact glob position in YAML, exact provenance-comment wording) is the builder's call. Single-glob extension is the lowest-cost shape that closes the 109-file residual; alternative shapes (per-test classification, test-rewrite, per-component glob list) all surface higher cost without proportional fence improvement.

**Pass.**

---

## 5. Acceptance criteria — AC.ABC-Cbis.\*

AC family **AC.ABC-Cbis.\*** (collision-safe — neither C1, C2, M11a, M2, M7-partition-fix, nor any other sub-plan uses this prefix; verified at plan-time).

### 5.1 — AC.ABC-Cbis.1 — Partition manifest reclassifies `**/tests/**` as `dev_only`

The M2 partition manifest's `dev_only:` block contains a glob entry `- glob: "**/tests/**"` matching every `tests/` directory under any audit-rooted tree. Per partition-precedence rule #2 (`dev_only` checked before `dev_and_public`), this glob wins over the broad `framework/<comp>/**` admissions for every component carrying a `tests/` subtree.

**Verification.** `grep -F '"**/tests/**"' framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml` returns the new line under `dev_only:`. YAML round-trips parse-clean (synthesis CLI loads the manifest without `SynthesisError`).

### 5.2 — AC.ABC-Cbis.2 — Synthesis output post-fix carries zero `tests/` blobs

Post-fix synthesis run produces a `framework-only` branch where `git ls-tree -r refs/heads/framework-only -- '*tests*'` returns zero blobs. Cross-check: the C1-sealed `**/tests/test_no_sealed_amendments.py` + `**/tests/test_AC_*_seal_diff_*.py` globs are still effective (they remain in the manifest); the new `**/tests/**` glob subsumes them but doesn't conflict (subsumption is not a precedence violation per partition-precedence rule #2).

**Verification.** Post-fix `python -m loam.publish_framework_only.cli --repo /Users/lukeivers/ivers-corp-pos-v2 --source HEAD` exits 0; `git ls-tree -r refs/heads/framework-only | grep -E '/tests/'` returns zero hits.

### 5.S — AC.ABC-Cbis.S — Sealed-component fence

C2-bis amendment is a **single-component-fence** amendment landing in `framework/tools/pos-publish-framework-only/`. Per M7-partition-fix precedent: the tool has no `test_no_sealed_amendments.py`, so the cycle anchors on `hands-off-lifecycle` as a no-op narrative anchor (sidecar bump + SEAL_COMMIT.notes file) and admits the tools-tree path via `universal_paths.prefixes`. `loam amend apply` runs BEFORE the seal commit per `feedback_dispatch_explicit_pos_amend_apply`.

**Verification.** `git diff --name-only BASELINE..SEAL_COMMIT` produces only `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml` + the plan-doc + the amendment manifest YAML + HOL `seals/SEAL_COMMIT*` (anchor) + universal-paths. HOL's `frozen_baseline: true` (H19 pin) verified unchanged.

---

## 6. Sequencing — slot in master plan §5

Master plan §5 currently sequences M5 → M-FBM → M6 (sealed) → M7 (sealed) → M8 (sealed) → M9 (sealed) → M11 (in flight). M11a dispatch-2 halt at AC.M11a.2 introduced the C1+C2 sub-plan; C1 sealed `e2cbeec`; C2 HALTED. C2-bis (this plan) lands NEXT, then C2-prime, then M11a-3.

```
... → M9 (sealed 2161cb1) → M11a-1 (HALT F-M11a.1)
                          → M7-partition-fix (sealed d983f94)
                          → M8-corrective (sealed 5271091)
                          → M11a-2 (HALT three-class AC.M11a.2)
                          → ABC-C1 (sealed e2cbeec; mechanical Classes A + B)
                          → ABC-Cbis (THIS PLAN; mechanical test-fence)
                          → ABC-Cprime (separate plan; Class C 21-file production remediation)
                          → M11a-3 (re-dispatch; expected GO)
                          → M11b (owner browse + ruling)
                          → M12 (publish + tag)
```

**Sequencing inside this amendment:**

1. Plan-doc commit (this file) — sub-plan authored ahead of feature edit per `feedback_plan_before_code`.
2. Feature commit — single-line edit to `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml` adding `- glob: "**/tests/**"` to `dev_only:` block.
3. Amendment manifest commit — at `docs/rebuild/plans/oss-v0-1-0-publish-public-docs-classes-abc-bis.manifest.yaml`.
4. `loam amend apply` commit per `feedback_dispatch_explicit_pos_amend_apply`.
5. Seal commit.
6. §14 SHA backfill (post-seal) — populated by builder, not a separate commit; folded into the seal commit's narrative or the next §14-update commit.

Lands BEFORE C2-prime plan-doc commit (Stage 2 of this dispatch). Post-seal HEAD becomes the C2-prime sweep target.

---

## 7. Hard constraints

1. **Plan-before-code** — this doc; §14 anchor present.
2. **Single structural fence** — `framework/tools/pos-publish-framework-only/` (admitted via `universal_paths.prefixes` per M7-partition-fix precedent). HOL anchors the sealed-component cycle as no-op narrative anchor only (sidecar bump + SEAL_COMMIT.notes file; NO behaviour edits to HOL).
3. **No new external runtime deps.**
4. **No `git commit --amend`** per `feedback_no_amend_in_agent_dispatches`.
5. **`loam amend apply` BEFORE seal commit** per `feedback_dispatch_explicit_pos_amend_apply`.
6. **AC-prefix `AC.ABC-Cbis.*`** (collision-safe; verified — `AC.ABC-A.*` / `AC.ABC-B.*` / `AC.ABC-C.*` from C1+C2 plan, `AC.M7-fix.*` from M7-partition-fix; this prefix is fresh).
7. **Auto-memory MEMORY.md NOT touched.**
8. **Synthesis smoke check post-fix is sanity-only** — not part of M11a's full sweep (that's M11a-3's job, post-C2-prime).
9. **Build cadence speedups** per `feedback_amendment_dispatch_speedups`: narrow test scope to pos-publish-framework-only; skip full repo-wide pytest pre-seal.
10. **Halt-and-surface on ODD §2.5 violations** in any touched code/doc per `feedback_subagent_odd_violation_halt`.

---

## 8. Out of scope (named explicitly per ODD §2.5)

- **C2-prime — Class C 21-file production remediation.** Authored in a separate plan-doc (`docs/rebuild/plans/oss-v0-1-0-publish-public-docs-classes-abc-prime.md`) and dispatched after this amendment seals.
- **The full M11a sweep (AC.M11a.1..6).** That re-dispatches against post-C2-prime HEAD per D-Q.M11.4.
- **Per-test classification.** Some tests verify public-shipping behaviour and arguably should ship; the cost of per-test triage (109 files × ~5 min each = 9 hours) vastly exceeds the value (the public synthesis tree is a release artefact, not a test-coverage substrate). Industry convention rules: tests don't ship publicly in v1.0 OSS releases.
- **Test-file rewrite.** Rewriting all 109 test files to use generic path strings would weaken test fidelity (the tests verify dev-mode behaviour by literal-asserting dev-only paths) and inflate scope by 5-15× this amendment's cost.
- **Editing `dev-mode-manifest.yaml`** (separate manifest, separate concern).
- **Removing the C1-sealed `**/tests/test_no_sealed_amendments.py` + `**/tests/test_AC_*_seal_diff_*.py` globs.** They're subsumed by `**/tests/**` but not conflicting; leaving them in place preserves the audit trail of C1's locked decision (D-build.ABC-C1.2 + D-Q.ABC.3 = a). Removing them would be a separate cosmetic amendment, out of scope here.
- **Auto-memory MEMORY.md or any `~/.claude/` corpus.**

---

## 9. Halt-and-surface conditions

Per `feedback_subagent_odd_violation_halt` + `feedback_critical_thinking_on_deviations`. Builder halts + surfaces to dispatcher on any of:

- **HT-Cbis.1 — YAML edit breaks parsing.** YAML indentation error or schema violation. Halt; surface YAML error.
- **HT-Cbis.2 — Synthesis still errors post-fix on a different classification gap.** Means another partition gap exists beyond the test-fence. Halt; surface specific cause; expand fix scope or escalate per D-Q.M11.4.
- **HT-Cbis.3 — AC.ABC-Cbis.2 verification finds residual `tests/` files.** Means the glob shape was wrong (e.g. needs `**/*tests*/**` to also match `*_test*` directories, or the synthesis tool's matcher doesn't expand `**/tests/**` recursively). Halt; surface; refine glob shape.
- **HT-Cbis.4 — Pre-existing test fails post-fix in `framework/tools/pos-publish-framework-only/tests/`.** Halt; surface specific failure; investigate (could be a partition-classification regression).
- **HT-Cbis.5 — ODD §2.5 violation in surrounding code/docs encountered during build.** Surface for FUTURE_IDEAS_DRAFT.md capture; do NOT silently extend.
- **HT-Cbis.6 — Wall-time exceeds estimate by >50%.** Predicted 20-30 min midpoint 25; halt at >40 min. Surface progress; let dispatcher rule continuation.

---

## 10. Risks

1. **`**/tests/**` glob over-matches a directory unintentionally.** Mitigation: pre-edit `git ls-tree -r HEAD -- '*tests*'` confirms the `tests/` convention is structural-fence (no public-shipping artefact under any directory named `tests/`). Synthesis smoke check post-edit verifies zero residuals.
2. **Glob shape doesn't match the synthesis tool's matcher semantics.** Mitigation: existing `**/seals/**` glob (C1-sealed) uses identical shape and is empirically working in the synth tool; same matcher applies.
3. **Subsumption with C1's existing `**/tests/test_no_sealed_amendments.py` + `**/tests/test_AC_*_seal_diff_*.py` globs.** Both are matched by `**/tests/**`; the broader glob takes effect first per first-match-wins iteration (or both apply identically — same `dev_only` class). Not a regression. Mitigation: confirmed via partition.py inspection at plan-time (single-pass classification; no double-classification error).

---

## 11. Decisions register

None — locked by dispatcher autonomy directive (see §2). The single locked decision (add `- glob: "**/tests/**"` to `dev_only:`) is captured in §5 AC.ABC-Cbis.1.

---

## 12. Halt-and-surface findings during plan authoring

None at plan-authoring time. Industry-convention shape verified against three precedent OSS releases (cpython, numpy, requests — none ships their test suite in the public-installable wheel). C2 halt narrative §4 Option A captures the rationale; this plan-doc executes it.

Findings encountered during build land in §14 method-decision register.

---

## 13. References

- C1+C2 combined sub-plan: `docs/rebuild/plans/oss-v0-1-0-publish-public-docs-classes-abc.md`.
- C2 halt narrative: `<workspace>/.scratch/claude-output/oss-v0-1-0-publish-classes-abc-c2-halt.md`.
- M11 plan-doc: `docs/rebuild/plans/oss-v0-1-0-publish-dry-run.md`.
- M11a sweep report (input): `<workspace>/.scratch/claude-output/oss-v0-1-0-publish-m11a-sweep-report.md`.
- M7-partition-fix precedent (small-scope sealed-cycle + HOL no-op anchor): `docs/rebuild/plans/oss-v0-1-0-publish-public-docs-partition-fix.md`.
- M2 partition manifest under edit: `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`.
- Programme master plan: `docs/rebuild/plans/oss-v0-1-0-publish.md`.
- VALUE_PROPOSITION (prime objective): `docs/rebuild/VALUE_PROPOSITION.md` AC.PO.1 + AC.PO.2.
- CLAUDE.md design lenses: `/Users/lukeivers/ivers-corp-pos-v2/CLAUDE.md` §1 + §3.
- Memory bullets carried forward (cited per dispatch corpus):
  `feedback_plan_before_code`, `feedback_subagent_odd_violation_halt`,
  `feedback_summarize_and_surface_decisions`, `feedback_critical_thinking_on_deviations`,
  `feedback_no_amend_in_agent_dispatches`, `feedback_dispatch_explicit_pos_amend_apply`,
  `feedback_value_proposition_as_prime_objective`, `feedback_duration_estimation_rubric`,
  `feedback_amendment_dispatch_speedups`.

---

## 14. Method-decision register skeleton (post-build)

Filled by the builder post-build per existing precedent (M7-partition-fix §14, C1 §14).

### D-build.ABC-Cbis.0 — AI-time actuals

**Predicted:** 20-30 min midpoint 25. **Actual:** `<TBD>` — to be backfilled post-seal.

### D-build.ABC-Cbis.1 — YAML edit mechanism

`<TBD>` — single-line `- glob: "**/tests/**"` entry appended to existing `dev_only:` block; provenance comment cites this plan-doc. Position relative to C1's three globs (`**/seals/**`, `**/tests/test_no_sealed_amendments.py`, `**/tests/test_AC_*_seal_diff_*.py`) — builder's call.

### D-build.ABC-Cbis.2 — Synthesis smoke check

`<TBD>` — `python -m loam.publish_framework_only.cli` advanced `refs/heads/framework-only` → `<sha>`; per-glob `git ls-tree -r refs/heads/framework-only | grep '/tests/'` verified zero residuals. AC.ABC-Cbis.1 + AC.ABC-Cbis.2 PASS empirically.

### D-build.ABC-Cbis.3 — HOL anchor pattern

`<TBD>` — HOL no-op anchor pattern applied per M2 + M7-partition-fix HSF#2 + C1 D-build.ABC-C1.4 precedent.

### D-build.ABC-Cbis.4 — Touched-component test count

`<TBD>` — pos-publish-framework-only test count post-fix.

### Commit SHAs

- Amendment commit: `9bfd9cb088a6e74f8fd1c37e04d72d2c2ecdb8d5` —
  `chore(loam-amend-apply): loam amend apply for C2-bis test-glob reclassification`
- Seal commit: `990e95cc905f0f38d2993c67579d5bbc4c606279` —
  `chore(seals): oss-v0-1-0-publish-public-docs-classes-abc-bis — hands-off-lifecycle at 9bfd9cb`
