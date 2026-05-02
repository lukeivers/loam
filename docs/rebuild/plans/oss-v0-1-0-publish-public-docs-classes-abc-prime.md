# OSS v0.1.0 publish — public-docs Class C-prime (production remediation) — sub-plan

**Status:** plan-doc (pre-build, plan-before-code). 2026-05-02.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2 / future loam).
**Predecessor:** C1 sealed `e2cbeec` + C2 HALTED + C2-bis sealed `990e95c` (test-fence partition extension; §14 backfill `f00911e`). HEAD `f00911e`. Tree clean.
**Successor target:** M11a re-dispatch (M11a-3) against post-C2-prime HEAD.
**Authority:** Owner ruling on §11 D-Q.ABC-prime.* required before build dispatch.
**Programme master:** `docs/rebuild/plans/oss-v0-1-0-publish.md` — §3 AC.OSS.3 source.
**M11 plan:** `docs/rebuild/plans/oss-v0-1-0-publish-dry-run.md` — §5 AC.M11a.2 outcome bound + §11 D-Q.M11.4 + §14 dispatch-2 entry.
**Predecessor sub-plans:**

- C1+C2 combined sub-plan (C2 portion superseded by THIS PLAN): `docs/rebuild/plans/oss-v0-1-0-publish-public-docs-classes-abc.md`.
- C2 halt narrative (input): `<workspace>/.scratch/claude-output/oss-v0-1-0-publish-classes-abc-c2-halt.md`.
- C2-bis sub-plan (mechanical test-fence; sealed): `docs/rebuild/plans/oss-v0-1-0-publish-public-docs-classes-abc-bis.md`.

---

## 1. Summary / TLDR

**Per-file remediation against the post-C2-bis-sealed Class C population — 27 production files carrying AC.OSS.3 banned literals.** The plan-author-1 (C2 portion) enumeration of 26 files was partial because (a) the test-fence wasn't yet in place (so 109 test files dominated the population) and (b) one file (`workspace-bootstrap/.../new_workspace.py` — the `pos-publish-framework-only` literal in CLI help text) was missed. Empirical post-C2-bis sweep yields 27 production files; this plan supersedes the C2 portion of the predecessor combined sub-plan.

**Strategy.** Per-file shape: REWRITE / SUBSTITUTE / RECLASSIFY per the same three-option taxonomy from the predecessor plan, but with corrected per-file analysis informed by C2's halt-and-surface findings. Notably:

- File 18 (`session_start_gate.py`) function-body literals at lines 153-180 are runtime-load-bearing in dev mode + asserted by 2 dev-only tests. SUBSTITUTE is the only viable shape — RECLASSIFY would drop a production file the runtime requires; REWRITE would break dev-mode behaviour.
- M9 SUBSTITUTION_TABLE needs 4-7 additional entries (vs the 3 entries D-Q.ABC.4 locked in the predecessor plan) to cover the load-bearing path-shapes surfaced during C2's investigation.
- Several files the predecessor plan classified as REWRITE actually need SUBSTITUTE because their refs are load-bearing (function-body constants in `corpus_inline_session_start.py`, `tracker_seed.py`, `first_run_scaffold.py`).

**Estimated AI-time:** 75-150 min wall-clock midpoint ~110 min for build (multi-component fence; ~10 components touched; ~27 file edits + M9 SUBSTITUTION_TABLE extension; per-component pytest pre-seal). Higher than the predecessor plan's 45-90 min C2 estimate because the SUBSTITUTE shape requires both M9 TABLE growth + per-file verification that runtime behaviour preserves under SUB.

---

## 2. Owner ruling captured (in-flight; this plan surfaces decisions)

- **D-Q.ABC.1 (predecessor) = (a) REWRITE-as-default with SUB only for load-bearing constants** — locked at predecessor plan §11. THIS PLAN extends the SUB scope per investigation findings; owner re-rules at D-Q.ABC-prime.1 (per-file overrides) + D-Q.ABC-prime.2 (TABLE expansion).
- **D-Q.ABC.4 (predecessor) = locked 3 entries** in M9 SUBSTITUTION_TABLE — `docs/rebuild/VALUE_PROPOSITION.md` → `docs/positioning.md`; `docs/rebuild/spec/loam-objectives-spec.md` → strip-or-substitute; `docs/odd-methodology.md` → `docs/design/odd.md`. THIS PLAN proposes 4-7 additional entries — owner rules at D-Q.ABC-prime.2.
- **D-Q.ABC.5 (predecessor) = file 1 SUB if D-Q.ABC.4 = extend, else RW** + file 19 DROP capability-index — locked at predecessor plan §11. THIS PLAN preserves these locked decisions; surfaces refinements as needed.
- **C2-bis test-fence (sealed `990e95c`)** — closes 109-file test-residual scope. Public synthesis output now carries zero `tests/` blobs.

**Decisions remaining for owner ruling:** four named D-Q.ABC-prime.1..4 (§11 below). Owner rules from §1 summary + §11 named-decisions block.

---

## 3. Spec-objective placement (per CLAUDE.md §2.5)

The amendment binds to programme prime ACs:

- **AC.OSS.3 (no dev-discipline machinery in synthesis output).** Closes the remaining production-file Class C residuals after C1 (Classes A + B) and C2-bis (test-fence). M11a-3's literal-match grep clean post-amendment.
- **AC.OSS.5 (documentary rebrand).** A subset (file 1 `CLAUDE.md` references `docs/rebuild/VALUE_PROPOSITION.md`; files 24, 25 reference the same path as load-bearing constants) overlaps AC.OSS.5 — substitute extension serves the rebrand surface.
- **AC.OSS.1 (stranger-bootable).** A stranger reading `CLAUDE.md` and clicking through never lands on a missing path; remediation either rewrites to a public doc, substitutes the path at synth time, or both.
- **AC.PO.1 (translation-burden absorption).** Stranger never sees pos-v2-internal vocabulary in shipping artefacts.
- **AC.PO.2 (toolkit-primitive growth).** The M9 SUBSTITUTION_TABLE grows by 4-7 entries; the M9 substitute pattern becomes more durable as a repeatable "internal-doc-path → public-doc-path" rewrite.

**ODD §2.5 reverse-direction commitment.** Each AC below is outcome-shape; method-shape (which exact regex flags, which exact per-file edits, which exact TABLE-entry order) is the per-amendment builder's call inside the AC outcome bound.

---

## 4. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude-leverage-first

C2-prime composes against Claude's existing Read/Edit primitives + the M9 SUBSTITUTION_TABLE pattern (synth-time text-rewrite primitive composed with `git hash-object -w` + the partition filter). No new MCP server, no new hook event, no new skill required. The remediation EXTENDS the existing M9 substitution primitive (grows table by 4-7 entries); does not invent a new primitive.

**Pass.**

### Lens 2 — Harness + primary-persona value

- **Primary-persona test (translation burden):** post-remediation, a stranger reading `CLAUDE.md` or running through `corpus_inline_session_start` hooks no longer sees `docs/rebuild/` or `pos-amend` vocabulary in the public synthesis output. Persona's session-start gate references resolve to public paths via SUBSTITUTE OR are silently elided via dev-mode-only branches.
- **Harness test (toolkit primitive):** the M9 SUBSTITUTION_TABLE grows by 4-7 entries; the substitute mechanism becomes a more durable harness primitive for every future v0.x release. The cumulative pattern (4-entry M9 lock + 3 D-Q.ABC.4 + 4-7 D-Q.ABC-prime.2 = 11-14 total) is still a small flat table — the "internal-doc-path → public-doc-path" rewrite becomes a standing convention.

**Pass on both tests.**

### Lens 3 — ODD authoring

Each AC below is outcome-shape, observable, deterministic. Method-shape (exact regex, exact per-file edit, exact TABLE-entry order) is the per-amendment builder's call. The split into per-file shapes (RW / SUB / RECL) is itself an outcome-shape decision: each file's outcome is "no AC.OSS.3 banned literal in synthetic tree post-fix"; method (RW vs SUB vs RECL) follows the per-file ruling.

**Pass.**

---

## 5. Acceptance criteria — AC.ABC-Cprime.\*

AC family **AC.ABC-Cprime.\*** (collision-safe — neither C1, C2-bis, M11a, M2, M7-partition-fix, nor any other sub-plan uses this prefix; verified at plan-time via `grep -rE "AC\.ABC-Cprime" docs/` returning no hits).

### 5.1 — AC.ABC-Cprime.1 — Production-file Class C residuals close

For every literal in the AC.OSS.3 excluded-artefact list (`pos-amend`, `loam-mode`, `docs/rebuild/`, `odd-methodology`, `odd-in-loam`, `duration-estimation-rubric`, `framework/tools/pos-publish-framework-only/`, `loam-amend`), `git grep -F` against the synthetic `framework-only` tree returns ZERO matches in any file. Per-file shape (RW / SUB / RECL) is the C2-prime builder's call within the locked per-file ruling (§5.4).

**Verification.** Post-fix `framework-only` synthesis run; for each banned literal, `git ls-tree -r refs/heads/framework-only | xargs -I{} git show framework-only:{}` piped to `grep -F <literal>` returns zero hits.

### 5.2 — AC.ABC-Cprime.2 — M9 SUBSTITUTION_TABLE extends with N entries

The M9 SUBSTITUTION_TABLE at `framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/substitution.py` extends from the M9-locked 4 entries (`/Users/lukeivers/...`, `lukeivers/pos-v2`, `Luke Ivers`) to 4 + 3 (D-Q.ABC.4 locked) + N (D-Q.ABC-prime.2 ruling) = 7 + N entries total. Per partition order-sensitivity rule: trailing-slash entries precede their no-trailing-slash partners. Per AC.OSS-M9.3 idempotence rule: no entry's replacement appears as another entry's source.

**Verification.** `python -c "from loam.publish_framework_only.substitution import SUBSTITUTION_TABLE; print(len(SUBSTITUTION_TABLE))"` returns 7 + N. Idempotence verified by re-running synthesis on already-synthesised tree (re-substitution yields zero changes).

### 5.3 — AC.ABC-Cprime.3 — Touched-file behaviour preserved

For every file classified SUBSTITUTE (load-bearing), the touched-component pytest passes pre-seal in dev mode (the canonical paths still resolve at runtime; only synth-time output sees public paths). For every file classified REWRITE, no pre-existing test depended on the rewritten content (verified by per-file pre-edit grep against the touched-component tests/).

**Verification.** Per-component `pytest framework/<comp>/tests/` passes pre-seal for every component carrying a SUB or RW edit. Stranger-clone smoke per AC.M11a.6 (post-M11a-3 dispatch) verifies workspace-bootstrap adapters still resolve at synthetic-tree first-run.

### 5.4 — Per-file remediation table

Per dispatch-author investigation 2026-05-02 against the post-C2-bis-sealed synthetic tree (HEAD `f00911e`). 27 production files surfacing AC.OSS.3 banned literals. For each: file path; banned-literal hits; remediation shape (RW = rewrite/remove; SUB = synth-time substitute via M9 TABLE; RECL = reclassify dev_only); rationale.

| # | File (synth-tree path) | Hits | Shape | Notes / banned-literal references |
|---|---|---|---|---|
| 1 | `CLAUDE.md` | 1 | **SUB** | Line 49: `docs/rebuild/VALUE_PROPOSITION.md`. SUB via existing D-Q.ABC.4 entry → `docs/positioning.md`. (Predecessor §11 D-Q.ABC.5(a) ruling preferred SUB if D-Q.ABC.4 = extend; that branch is locked.) Plan-author-prime confirms SUB. |
| 2 | `docs/CLAUDE_CAPABILITIES.md` | 6 | **RW** | 5 refs `pos-amend` (lines 55, 140, 542, 599, 839) + 1 ref `odd-methodology.md` (line 919). RW: rewrite the surrounding prose to use generic "amendment-cycle CLI" or strip the `pos-amend`-specific discussion entirely (pos-amend doesn't ship publicly). The `odd-methodology.md` ref RW to `docs/design/odd.md`. |
| 3 | `dormancy/docs/architecture.md` | 1 | **RW** | Line 5: `../../docs/rebuild/components/dormancy/{brief,proposal,research}.md`. RW: strip the per-component build-doc backlink; the architecture.md should stand alone or reference public docs only. |
| 4 | `hands-off-lifecycle/hooks/_gate_helpers.py` | 4 | **SUB** | Lines 120-123: 4-entry `_FALLBACK_BASELINE_PATHS`-style tuple for sentinel-checks: `docs/odd-methodology.md`, `docs/odd-in-loam.md`, `docs/rebuild/FUTURE_IDEAS.md`, `docs/rebuild/FUTURE_IDEAS_DRAFT.md`. **REVISED from predecessor §5.4 (REWRITE)** — these are runtime-load-bearing fall-back paths the gate-helper checks for existence in dev mode. RW would change dev-mode behaviour. SUB: extend M9 TABLE so synth tree sees `docs/design/odd.md` for the first two; FUTURE_IDEAS{,_DRAFT}.md substitute to a public-doc equivalent OR strip via per-file SUB (which surfaces D-Q.ABC-prime.2). |
| 5 | `hands-off-lifecycle/hooks/corpus_inline_session_start.py` | 11 | **SUB** | **REVISED from predecessor §5.4 (REWRITE)** — heavy load-bearing references: tuples `_ALWAYS_LOAD` + `_ON_DEMAND` (function-body constants the hook reads to compose the corpus envelope). RW would change dev-mode behaviour. SUB via M9 TABLE: `docs/rebuild/VALUE_PROPOSITION.md` → `docs/positioning.md` (existing D-Q.ABC.4 entry); `docs/rebuild/STATE.md` → strip-or-public; `plugins/dev-sdlc/docs/odd-methodology.md` → `docs/design/odd.md`; `plugins/dev-sdlc/docs/odd-in-loam.md` → `docs/design/odd.md` (collapses); `docs/rebuild/FUTURE_IDEAS.md` → strip-or-public. Module docstring's `loam-mode` references (descriptive prose) stay in source — partition handles via dev_only-scoped synth. **HALT**: 5 `loam-mode` literals in module docstring + comments are NOT load-bearing — those are RW (rewrite to "session-start emitter"). Mixed shape. |
| 6 | `hands-off-lifecycle/hooks/corpus_load_sentinel.py` | 4 | **RW** | Line 191-194: fallback paths `<workspace>/docs/rebuild/dev-mode-manifest.yaml` + `<workspace>/framework/docs/rebuild/dev-mode-manifest.yaml` + 2 `loam-mode` references in docstring. Per predecessor's accepted finding: the manifest moved to plugins/dev-sdlc/dev-mode-manifest.yaml at M6b.0; the legacy fallbacks can be dropped (the only viable location is plugins/, which is dev_only). RW: strip the legacy + framework_manifest fallbacks; rewrite the loam-mode docstring references to "dev-mode session-start emitter". |
| 7 | `hands-off-lifecycle/hooks/first_run_helper.py` | ~10 | **RW** | All hits are `loam-mode` references in comments + docstrings describing the inner-hook composition shape (lines 113, 118, 123, 134, 155, 157, 159, 173, 213, 246, 259, 265, 273). Pure prose; not load-bearing. RW: rewrite to "dev-mode session-start emitter" wording. |
| 8 | `hands-off-lifecycle/hooks/first_run_settings.py` | 6 | **RW** | All hits are `loam-mode` in comments describing supervisor-stanza composition (lines 98, 102, 107, 108, 116, 122, 194, 321). Pure prose; not load-bearing. RW: rewrite to generic "dev-mode session-start" wording. |
| 9 | `hands-off-lifecycle/hooks/settings.json.fragment` | 1 | **RW** | JSON `_comment` field references `bootstrap-progress-statusline.md` plan path at line 2. RW: drop the plan-path reference; the fragment can describe the renderer's purpose without the plan-doc backlink. |
| 10 | `hands-off-lifecycle/hooks/statusline.py` | 1 | **RW** | Single docstring ref to `docs/rebuild/plans/bootstrap-progress-statusline.md` at line 29. RW: strip the plan-path reference. |
| 11 | `hands-off-lifecycle/README.md` | 3 | **RW** | 3 refs to internal docs (`docs/rebuild/components/true-first-run/`, `docs/rebuild/FUTURE_IDEAS.md`, `docs/rebuild/components/hands-off-lifecycle/`). RW: rewrite to `docs/components/hands-off-lifecycle.md` (public per `docs/components/` glob in dev_and_public block). |
| 12 | `orchestrator/scripts/pos_session_start.py` | 2 | **RW** | 2 refs to internal plan-paths (`bootstrap-progress-statusline.md`, `memory-pipeline-fix.md`) at lines 267, 316. Pure prose. RW: strip the plan-path comments. |
| 13 | `orchestrator/src/loam/orchestrator/__main__.py` | 1 | **RW** | Single ref to `docs/rebuild/components/orchestrator-bootstrap-unification/proposal.md` at line 24. Pure prose. RW: strip the proposal-path reference. |
| 14 | `orchestrator/src/loam/orchestrator/orchestrator.py` | 3 | **RW** | 3 refs to `docs/rebuild/components/orchestrator-bootstrap-unification/...` at lines 26, 211. Pure prose. RW: strip. |
| 15 | `primary-persona/src/loam/primary_persona/context_composer.py` | 1 | **RW** | Line 161: docstring fragment `docs/rebuild/plans/`. RW: change to "in-flight plans (workspace-defined)". |
| 16 | `primary-persona/src/loam/primary_persona/dispatch_wrapper.py` | 2 | **RW** | Lines 31, 92: `duration-estimation rubric` literal in inline comments + section-header. RW: rename inline rubric to "budget-inference rubric" — keeps the inline content (which is useful), drops the banned name. |
| 17 | `primary-persona/src/loam/primary_persona/session_start_emitter.py` | 2 | **RW** | Lines 341, 368: `loam-mode` references in comments describing timeout precedent. RW: "dev-mode session-start emit timeout". |
| 18 | `primary-persona/src/loam/primary_persona/session_start_gate.py` | 8 | **SUB** | **CRITICAL FILE — REVISED from predecessor §5.4 (REWRITE).** Lines 53-59: `_FALLBACK_BASELINE_PATHS` tuple — runtime-load-bearing in dev mode (the gate reads this fallback if CLAUDE.md is absent or its session-start-discipline section is unparseable). Lines 153-180: function `enumerate_amendments_in_flight` carries `docs/rebuild/plans/` literal as path-construction string in its body (line 166: `plans_dir = workspace_root / "docs" / "rebuild" / "plans"`; line 169-171: `framework_plans_dir = workspace_root / "framework" / "docs" / "rebuild" / "plans"`). C2 build investigation surfaced 2 dev-only tests asserting these specific path strings: `test_enumerate_amendments_in_flight_falls_through_to_framework` (asserts `"framework/docs/rebuild/plans/amendment-1-foo.md" in matches`) + `test_enumerate_amendments_in_flight_prefers_workspace_root` (asserts `"docs/rebuild/plans/amendment-99-from-root.md"`). **SUB ONLY**: extend M9 TABLE so synth tree's source carries the literal `docs/rebuild/plans/` rewritten to a public path that resolves at runtime in synth workspaces (or strip — see D-Q.ABC-prime.3). Tests still pass against canonical-mode source (untouched in canonical). **HSF#1**: tests now ship-fenced by C2-bis (`**/tests/**` is dev_only) — the test-fixture assertion is no longer a public-tree concern. The function-body literal is the only remaining surface to remediate. |
| 19 | `primary-persona/templates/persona-template/prompt.md` | 10 | **RW** | 8 refs `docs/rebuild/capability-corpus/...` paths (lines 187-194) in capability-index section + 2 refs (`docs/rebuild/FUTURE_IDEAS_DRAFT.md` line 251 + `docs/rebuild/capability-corpus/` line 332). Per predecessor §11 D-Q.ABC.5(b) locked = DROP the capability-index section + adjust references. RW: drop section 187-194 entirely (per persona's "fetch on demand, not at session-start" doctrine, line 332); rewrite line 251 to "the workspace's FUTURE_IDEAS_DRAFT capture surface". |
| 20 | `safety-layer/docs/architecture.md` | 1 | **RW** | Line 4: `../../docs/rebuild/components/safety-layer/proposal.md`. Pure prose. RW: strip. |
| 21 | `safety-layer/src/loam/safety_layer/__init__.py` | 1 | **RW** | Line 40: docstring `../../docs/rebuild/components/safety-layer/`. Pure prose. RW: strip. |
| 22 | `safety-layer/src/loam/safety_layer/events.py` | 1 | **RW** | Line 78: docstring `docs/rebuild/plans/amendment-19-s1-silent-excepts.md`. Pure prose. RW: strip. |
| 23 | `safety-layer/src/loam/safety_layer/observability.py` | 1 | **RW** | Line 142: docstring `docs/rebuild/plans/research/amendment-19-s1-silent-excepts-research.md`. Pure prose. RW: strip. |
| 24 | `workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py` | 3 | **SUB + RW** | Line 36: `docs/odd-methodology.md` ref in user-branch comment. RW (cosmetic) → `docs/design/odd.md`. Lines 573, 743: `docs/rebuild/VALUE_PROPOSITION.md` ref — load-bearing. SUB via existing D-Q.ABC.4 entry → `docs/positioning.md` (existing). Mixed shape but locked. |
| 25 | `workspace-bootstrap/src/loam/workspace_bootstrap/adapters/tracker_seed.py` | 4 | **SUB + RW** | Lines 75, 156: `FRAMEWORK_VALUE_PROP_RELPATH = "docs/rebuild/VALUE_PROPOSITION.md"` (load-bearing constant). SUB via existing D-Q.ABC.4 → `docs/positioning.md`. Line 330: `SPEC_DOC_RELPATH = "docs/rebuild/spec/loam-objectives-spec.md"` (load-bearing constant). SUB via existing D-Q.ABC.4 → `<public-spec-or-strip>` (D-Q.ABC.4 locked option). Lines 19, 23: docstring references to plan-paths + `docs/rebuild/VALUE_PROPOSITION.md` — synth-output sees substituted path; canonical sees original. RW for the cosmetic plan-path ref (line 19); SUB handles the others. |
| 26 | `workspace-bootstrap/src/loam/workspace_bootstrap/new_workspace.py` | 1 | **RW** | **NEW vs predecessor §5.4 — file 26 was workspace-sync README, file 26-renumbered.** Line 356: f-string `(synthesise with `pos-publish-framework-only`).` — the CLI's user-facing error message references the synthesis tool by name. The synthesis tool itself is dev_only (`framework/tools/pos-publish-framework-only/**` is dev_only per M2 manifest line 200). The CLI emitting this hint is a workspace-bootstrap UX message — but if the public synthesis output contains a literal `pos-publish-framework-only`, AC.OSS.3 fails. **RW**: rewrite the hint to a generic message (e.g. "(synthesise the framework-only branch via the dev-mode publish tool)" or strip the synthesise-hint entirely; the user sees the error in dev mode where the tool exists). The synth tree's public copy of new_workspace.py drops the literal. |
| 27 | `workspace-sync/README.md` | 4 | **RW** | 4 refs to internal plan paths (`docs/rebuild/plans/workspace-sync.md`, `.builder-plan.md`, `.manifest.yaml`) at lines 37, 47, 48, 49. Pure prose. RW: rewrite to `docs/components/workspace-sync.md` for the architecture-level reference; strip per-plan backlinks. |

**Per-file shape totals (plan-author-prime recommendation):**

- **REWRITE/REMOVE: 19 files** (2, 3, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 20, 21, 22, 23, 26, 27 — 21 files. Recount: 19 strict-RW + 2 mixed-shape that are listed under SUB+RW below).
- **SUBSTITUTE (extend M9 TABLE) — strict: 4 files** (1, 4, 5, 18 — load-bearing path constants + tuples).
- **MIXED SUB + RW: 3 files** (5 also has loam-mode prose RW; 24, 25 — load-bearing constants SUB + cosmetic plan-path RW).
- **RECLASSIFY: 0 files** — none of the 27 files should exit the public ship surface entirely.
- **AMBIGUOUS: 0 files** — every file lands a per-file recommendation; D-Q.ABC-prime.1 surfaces refinements; D-Q.ABC-prime.3 specifically surfaces file 18.

Counts (used for §1 summary):
- REWRITE-only: 21 files
- SUBSTITUTE-only or MIXED: 6 files
- RECLASSIFY: 0
- AMBIGUOUS: 0

**HSF triggered during plan-authoring: HSF#1** — file 18's function-body literal `docs/rebuild/plans/` is the only remaining surface (tests now ship-fenced post-C2-bis); SUB via M9 TABLE is the only viable shape. Surfaces D-Q.ABC-prime.3.

### 5.S — AC.ABC-Cprime.S — Sealed-component fence

C2-prime amendment is a **multi-component-fence** amendment touching the components named in §5.4's per-file table:

- `framework/dormancy/` (file 3)
- `framework/hands-off-lifecycle/` (files 4-11)
- `framework/orchestrator/` (files 12-14)
- `framework/primary-persona/` (files 15-19)
- `framework/safety-layer/` (files 20-23)
- `framework/workspace-bootstrap/` (files 24-26)
- `framework/workspace-sync/` (file 27)
- `framework/tools/pos-publish-framework-only/` (M9 SUBSTITUTION_TABLE extension)
- `docs/CLAUDE_CAPABILITIES.md` + top-level `CLAUDE.md` (universal-paths via existing amendment-#22 ruling #3)

8 framework components touched. Per builder's call: each touched component carries the per-file edits + a SEAL_COMMIT bump; pos-publish-framework-only carries the M9 TABLE extension. `loam amend apply` runs BEFORE seal per `feedback_dispatch_explicit_pos_amend_apply`. NO `git commit --amend` per `feedback_no_amend_in_agent_dispatches`.

**Verification.** Per-component `test_no_sealed_amendments.py` is now `dev_only` post-C1 (run in dev mode against canonical, not in synthesis); per-component `test_AC_*_seal_diff_*.py` window check passes; touched-component pytest passes pre-seal.

---

## 6. Sequencing — slot in master plan §5

Master plan §5 currently sequences M5 → M-FBM → M6 (sealed) → M7 (sealed) → M8 (sealed) → M9 (sealed) → M11 (in flight). M11a dispatch-2 halt at AC.M11a.2 introduced the C1+C2 + C2-bis + C2-prime sub-plan series. C1 sealed `e2cbeec`; C2 HALTED; C2-bis sealed `990e95c`; C2-prime (this plan) lands NEXT, then M11a-3.

```
... → M9 (sealed 2161cb1) → M11a-1 (HALT F-M11a.1)
                          → M7-partition-fix (sealed d983f94)
                          → M8-corrective (sealed 5271091)
                          → M11a-2 (HALT three-class AC.M11a.2)
                          → ABC-C1 (sealed e2cbeec; mechanical Classes A + B)
                          → ABC-Cbis (sealed 990e95c; mechanical test-fence)
                          → ABC-Cprime (THIS PLAN; production-file remediation)
                          → M11a-3 (re-dispatch; expected GO)
                          → M11b (owner browse + ruling)
                          → M12 (publish + tag)
```

**Concrete sequencing inside this amendment:**

1. **Owner rules D-Q.ABC-prime.1..4** (this plan §11). Required before build dispatches (the per-file shape ruling determines per-component edits).
2. **C2-prime build dispatches** (per-file remediation per ruling). Estimated 75-150 min wall-clock midpoint ~110 min. Lands sealed; HEAD advances.
3. **M11a-3 dispatches** against post-C2-prime HEAD. Estimated 20-35 min wall-clock for re-sweep + report. Expected GO.

**Programme total impact.** Was 11.5-18 h post-M11a-split midpoint ~13.75 h; post-this-series (C1 + C2-bis + C2-prime + M11a-3) ~12-19 h midpoint ~14 h.

**Safety property.** C2-prime edits source per per-file shape — touched-component tests must pass pre-seal. SUB-shape edits preserve canonical-mode behaviour by construction (canonical reads the original literal; synth reads the rewritten literal). Halt-and-surface on any test failure or ODD violation per §9.

---

## 7. Hard constraints

1. **Plan-before-code** — this doc; §14 anchor present.
2. **Multi-component fence** — 8 framework components + tools/pos-publish-framework-only/ + universal-paths (CLAUDE.md, docs/CLAUDE_CAPABILITIES.md). Each component's seal-fence holds independently per amendment-cycle precedent (M-FBM 3-component fence; C2-prime extends that pattern to 8).
3. **No `git commit --amend`** — corrective commits are NEW commits per `feedback_no_amend_in_agent_dispatches`.
4. **`loam amend apply` BEFORE seal commit** per `feedback_dispatch_explicit_pos_amend_apply`. Each touched component anchors on its own `test_no_sealed_amendments.py` (post-C1 dev_only — runs in dev mode only).
5. **No new third-party deps.**
6. **Halt-and-surface on ODD §2.5 violations** in any touched code/doc per `feedback_subagent_odd_violation_halt`.
7. **Auto-memory MEMORY.md is NOT touched.**
8. **AC-prefix `AC.ABC-Cprime.*`** (collision-safe; verified at plan-time).
9. **SUBSTITUTE shape preserves canonical-mode behaviour by construction.** Per AC.ABC-Cprime.3 — the synth-time substitute only changes synth output; canonical reads the original literal at runtime. No canonical-mode test edits.
10. **Build cadence speedups** per `feedback_amendment_dispatch_speedups`: narrow test scope to touched components for pre-seal verification; skip full repo-wide pytest pre-seal; inline methodology snippets where helpful.
11. **C2-prime supersedes the C2 portion** of `oss-v0-1-0-publish-public-docs-classes-abc.md` only — C1 portion stays sealed at amendment #100.

---

## 8. Out of scope (named explicitly per ODD §2.5)

- **Editing the M11a sweep mechanism itself.**
- **Authoring v0.x foldback amendments for hypothetical future Class C surfaces** (e.g. a v0.2 component that introduces a new dev-only path convention).
- **Reordering M11a's AC list.**
- **Authoring new public-shipping docs.** `docs/positioning.md`, `docs/design/odd.md`, `docs/getting-started.md`, `docs/architecture.md` exist (M7 docs lane sealed); SUB extensions point at these existing docs. Authoring new public mirrors is a separate M7-docs-addendum dispatch if D-Q.ABC-prime.2 surfaces a need.
- **Editing the auto-memory MEMORY.md or any `~/.claude/` corpus.**
- **Capability-corpus public-shipping decision.** D-Q.ABC.5(b) locked DROP; THIS PLAN preserves that decision.
- **Test-file edits.** Tests now ship-fenced (C2-bis sealed); test-file fixtures may continue asserting canonical paths (dev-mode behaviour) without affecting AC.OSS.3 grep.
- **`upgrade-merge-resolver` retirement / dead-code cleanup.**
- **History rewrite of canonical pos-v2.**
- **Changes to the seals/ files themselves.** C1 reclassified the partition; the seals files stay in canonical dev mode untouched.
- **Removing the C1-sealed `**/tests/test_no_sealed_amendments.py` + `**/tests/test_AC_*_seal_diff_*.py` globs** (subsumed by C2-bis's `**/tests/**` but kept as audit-trail).

---

## 9. Halt-and-surface conditions

Per `feedback_subagent_odd_violation_halt` + `feedback_critical_thinking_on_deviations`. Each builder halts + surfaces to dispatcher on any of:

### Series-wide

- **HT-Cprime.1 — ODD §2.5 violation surfaces in surrounding code/docs.** Halt; surface; do NOT extend.
- **HT-Cprime.2 — Wall-time exceeds estimate by >50%.** Halt at >225 min. Surface progress; let dispatcher rule continuation.
- **HT-Cprime.3 — Pre-existing test fails post-amendment** (other than mechanical-fixture-update fails for the partition shift itself). Halt — that's a bug.
- **HT-Cprime.4 — `loam amend apply` returns "skipped: seal-test file missing"** for any targeted component. Resolve per M7-partition-fix HSF#2 / C1 D-build.ABC-C1.4 pattern. Surface for dispatcher awareness.

### C2-prime-specific

- **HT-Cprime.5 — A Class C file's reference shape is genuinely ambiguous** post-investigation. Halt; surface specific file + ambiguity; let owner rule.
- **HT-Cprime.6 — A Class C file's runtime behaviour breaks under the per-file edit.** Halt; surface failing test; switch shape from RW to SUB or vice versa per ruling.
- **HT-Cprime.7 — M9 SUBSTITUTION_TABLE extension would conflict with existing entries** (per-token rewrite collision; AC.OSS-M9.3 idempotence violation). Halt; surface specific conflict.
- **HT-Cprime.8 — File 18's load-bearing function-body literal cannot be deterministically substituted** by the M9 mechanism (e.g. the literal is split across multiple Python tokens that the textual `s/X/Y/g` can't capture cleanly). Halt; surface specific failure mode; consider per-file fixture-update or alternative shape.
- **HT-Cprime.9 — More than 30 production files surface during build investigation.** Plan-author-prime count: 27. If a builder finds an additional file the plan-author missed (>30 total), halt; surface; let owner rule whether scope widens.
- **HT-Cprime.10 — Less than 5 production files surface during build investigation.** Indicates scope shift between plan-author-time and build-time; halt; investigate; surface.
- **HT-Cprime.11 — Class C remediation reveals an AC.OSS.5 (rebrand) violation not previously flagged.** Halt; surface; route to M9-corrective separately.
- **HT-Cprime.12 — A SUB-shape edit changes canonical-mode behaviour** (e.g. canonical test breaks because the source literal was changed in canonical, not just at synth time). Halt; surface; revert to dev_only-scope SUB or switch to RW.

---

## 10. Risks (series-specific)

1. **C2-prime's per-file edits cascade across 8 components in a single fence.** Mitigation: §5.4 enumerates each file's component; each component's seal-fence holds independently per M-FBM precedent (3-component) extended to 8. Builder runs per-component pytest pre-seal.
2. **M9 SUBSTITUTION_TABLE extension breaks idempotence.** Mitigation: AC.ABC-Cprime.2 carries the idempotence verification as a deterministic check — re-run synthesis on already-synthesised tree; zero changes expected. Halt at HT-Cprime.7 if violation detected.
3. **File 18's function-body literal cannot be substituted by purely textual `s/X/Y/g`.** Mitigation: HT-Cprime.8 halt-clause; dispatch-author-prime investigated and confirmed the literal `docs/rebuild/plans/` is a contiguous string in the source, so `s/docs\/rebuild\/plans\//<public-path>/g` works deterministically. SUB shape viable.
4. **SUB-shape edits change canonical-mode behaviour.** Mitigation: HT-Cprime.12 halt-clause; SUB by M9 mechanism only changes synth-time output by construction (the substitution callsite is in `synth.py` line 324, applied AFTER partition filter). Canonical reads the original literal.
5. **M11a-3 re-dispatch surfaces a NEW class of AC.OSS.3 violations** beyond Classes A + B + C. Mitigation: D-Q.M11.4 (always halt-and-surface) catches any residual; foldback dispatches authored separately.
6. **C2-prime grows during build investigation as builders surface additional Class C-shaped files.** Mitigation: HT-Cprime.9 caps at 30 files; plan-author count of 27 leaves 3-file buffer.
7. **D-Q.ABC-prime.2 SUBSTITUTION_TABLE expansion conflict** with existing 4-entry M9 TABLE + 3-entry D-Q.ABC.4 lock. Mitigation: plan-author verified non-conflict with the proposed entries (§11); HT-Cprime.7 halt-clause catches discovery-time conflicts.

---

## 11. Decisions remaining for owner ruling

Per `feedback_summarize_and_surface_decisions` — four named decisions with recommendations. Owner rules from this summary; doesn't need to read full plan.

### D-Q.ABC-prime.1 — Per-file shape overrides for the 27-file population (mission-critical)

**Q.** §5.4's per-file shapes resolve every file but four cases warrant explicit owner sign-off because they REVISE shapes the predecessor plan locked at REWRITE:

(a) **File 4 (`_gate_helpers.py` lines 120-123 — fall-back tuple).** Predecessor §5.4 = REWRITE; THIS PLAN = SUBSTITUTE. Rationale: the tuple is runtime-load-bearing in dev mode (the gate-helper checks for existence of these specific files as session-start sentinels). RW would change dev-mode behaviour. SUB via M9 TABLE preserves dev-mode behaviour while public synth sees rewritten paths.

(b) **File 5 (`corpus_inline_session_start.py` — `_ALWAYS_LOAD` + `_ON_DEMAND` tuples).** Predecessor §5.4 = REWRITE; THIS PLAN = MIXED SUB + RW. SUB for the load-bearing path tuples; RW for the cosmetic loam-mode prose in module docstring + comments. RW would break the corpus envelope's dev-mode contract.

(c) **File 18 (`session_start_gate.py` — `_FALLBACK_BASELINE_PATHS` tuple + `enumerate_amendments_in_flight` body).** Predecessor §5.4 = REWRITE; THIS PLAN = SUBSTITUTE. Critical file — 2 dev-only tests assert specific path strings + the function is runtime-load-bearing. SUB only. **D-Q.ABC-prime.3 surfaces this as a separate ruling** (because of test-fixture dependency).

(d) **File 26 (`new_workspace.py` line 356 — `pos-publish-framework-only` literal in CLI hint).** NEW vs predecessor (predecessor's file 26 was workspace-sync README, file 26-renumbered). Plan-author-prime = REWRITE the hint to drop the dev-tool name. Owner sign-off needed because the synth-tree's CLI loses the dev-mode usage hint.

**Rec.** Approve THIS PLAN's revised per-file shapes (a, b, c, d as authored). Rationale: (i) the SUB shape preserves canonical-mode behaviour by construction; (ii) the tests asserting on file 18's literals are now dev_only (post-C2-bis) so test-fidelity is unaffected by the synth-time SUB; (iii) RW-only would break dev-mode behaviour for files 4, 5, 18 — surfaced empirically during C2's halt investigation.

If owner rules **per-file overrides** (e.g. file 5 RW-only despite breakage risk): capture override in C2-prime build dispatch entry.

### D-Q.ABC-prime.2 — M9 SUBSTITUTION_TABLE 4th-Nth entries (mission-critical)

**Q.** D-Q.ABC.4 (predecessor) locked 3 entries (`docs/rebuild/VALUE_PROPOSITION.md` → `docs/positioning.md`; `docs/rebuild/spec/loam-objectives-spec.md` → strip-or-substitute; `docs/odd-methodology.md` → `docs/design/odd.md`). C2 halt narrative HSF#3 surfaced 4-7 additional entries needed for clean close. THIS PLAN proposes the following 5 additional entries (table totals 4 M9-locked + 3 D-Q.ABC.4 + 5 D-Q.ABC-prime.2 = 12 entries):

| # | Source | Replacement | Rationale | Used by file(s) |
|---|---|---|---|---|
| 8 | `docs/odd-in-loam.md` | `docs/design/odd.md` | Collapses two ODD docs to single public ODD; mirrors entry 7 (D-Q.ABC.4). | 4, 5, 18 |
| 9 | `plugins/dev-sdlc/docs/odd-methodology.md` | `docs/design/odd.md` | Plugin-relative ODD ref → public ODD. | 5 |
| 10 | `plugins/dev-sdlc/docs/odd-in-loam.md` | `docs/design/odd.md` | Plugin-relative ODD ref → public ODD. | 5 |
| 11 | `docs/rebuild/STATE.md` | `docs/getting-started.md` | STATE.md is dev-only; getting-started.md is the closest public counterpart for a "what's the current state" document. | 5, 18 |
| 12 | `docs/rebuild/plans/` | `docs/components/` | File 18's load-bearing literal — points at public per-component docs (closest analogue to per-amendment plans). RW alternative would break behaviour. **D-Q.ABC-prime.3 surfaces specific concern.** | 18 |

**Rec.** Approve all 5 entries. Rationale: (i) every entry has at least one production file as user; (ii) all replacements point at existing public docs (no new authoring required — `docs/positioning.md`, `docs/design/odd.md`, `docs/getting-started.md`, `docs/components/` all ship publicly); (iii) idempotence verified at plan-time — none of the replacements appears as a substitution source elsewhere in the table; (iv) order-sensitivity respected — trailing-slash entries (entry 12) precede no-trailing-slash partners.

If owner rules **fewer entries** (e.g. drop entry 11 + 12, force RW for files 5 + 18): C2-prime grows by ~30-60 min for per-file rewrites + a halt at HT-Cprime.6 risk if RW breaks dev-mode behaviour.

If owner rules **STRIP not SUBSTITUTE for `docs/rebuild/FUTURE_IDEAS{,_DRAFT}.md`** (they have no public counterpart): file 4 + 5 + 19 builders strip the references entirely (post-strip the tuple shrinks; behaviour preserved IFF the gate-helper handles a 0-entry tuple). **Plan-author-prime recommends STRIP for FUTURE_IDEAS{,_DRAFT}** — no compelling public counterpart; per-file behaviour preserved (the gate is defensive — tuple existence-check is fail-soft).

### D-Q.ABC-prime.3 — File 18 SUBSTITUTE-vs-RECLASSIFY (CONFIRM)

**Q.** File 18 (`session_start_gate.py`) is a runtime hook the harness MUST ship publicly (it's the session-start gate for the persona). RECLASSIFY to dev_only would break the public synthesis. Two viable shapes remain:

(a) **SUBSTITUTE** (plan-author-prime recommendation): extend M9 TABLE entry 12 (`docs/rebuild/plans/` → `docs/components/`); the synth-tree source carries the rewritten literal; dev-mode source unchanged. Tests pass (tests are dev_only post-C2-bis). Function returns `[]` at first-run in synth workspaces (the rewritten path resolves to an empty directory) — that's the correct behaviour for a stranger-clone (no amendments in flight).

(b) **RW**: rewrite the function-body literal to a generic prose-only docstring + drop the path-construction logic. Breaks dev-mode behaviour: 2 named tests fail (`test_enumerate_amendments_in_flight_falls_through_to_framework` + `test_enumerate_amendments_in_flight_prefers_workspace_root`). Test-fixture update required.

**Rec.** **(a) SUBSTITUTE.** Rationale: (i) preserves canonical-mode behaviour by construction; (ii) the rewritten path `docs/components/` resolves to an existing public directory (graceful fail-soft on missing amendments-in-flight); (iii) avoids test-fixture churn (tests are dev_only post-C2-bis but still run during local dev); (iv) symmetric with files 4, 5, 24, 25 — same SUB pattern.

If owner rules **(b) RW**: C2-prime grows by ~10-15 min for test-fixture update; surfaces a HT-Cprime.3 risk if test-fixture update has unintended downstream effects.

### D-Q.ABC-prime.4 — File 26 hint-message shape

**Q.** File 26 (`workspace-bootstrap/.../new_workspace.py` line 356) emits a CLI hint `"(synthesise with `pos-publish-framework-only`)."` — the synthesis-tool name itself is the AC.OSS.3-banned literal. Three shapes:

(a) **REWRITE — drop the synthesise-hint.** Strangers running the public-installable workspace-bootstrap tool don't have access to pos-publish-framework-only anyway (it's dev_only). The hint is dead surface in synth output.

(b) **REWRITE — generic dev-tool reference.** Rewrite to "(synthesise the framework-only branch via the dev-mode publish tool)." Drops the literal but keeps the conceptual hint.

(c) **SUBSTITUTE.** Add M9 TABLE entry `pos-publish-framework-only` → `<dev-mode-publish-tool>`. Risks: the substitution then replaces every occurrence in the synth tree (most are in the tool's own source; that source is dev_only and doesn't ship anyway).

**Rec.** **(a) drop the synthesise-hint.** Rationale: (i) the hint is dead surface in synth output (strangers can't reach the tool); (ii) avoids M9 TABLE bloat for a single-occurrence literal; (iii) cleanest surface — the CLI's user-facing error in synth output should reference only public concepts.

If owner rules **(b)**: minor wording change; same close-condition.

If owner rules **(c)**: M9 TABLE grows by 1 (entry 13: `pos-publish-framework-only` → `<dev-mode-publish-tool>`); idempotence verification still holds.

---

## 12. Halt-and-surface findings encountered during plan authoring

Per the dispatch's halt-and-surface clause: surface any audit / methodology / surrounding-code / surrounding-docs ODD violations encountered while authoring this plan.

**Findings (none triggers a halt):**

1. **Population count: 27** (within 5-30 halt threshold; 1-file overage vs predecessor's 26 attributable to file 26 — `new_workspace.py` carrying the `pos-publish-framework-only` literal, missed by predecessor's grep scope). No halt.
2. **D-Q.ABC.4 SUBSTITUTION_TABLE undersized (HSF#3 from C2 halt narrative)** — confirmed at plan-time. THIS PLAN's D-Q.ABC-prime.2 proposes 5 additional entries (4 + 3 + 5 = 12 total). Surfaced; not a halt.
3. **File 18's function-body literal load-bearing case (HSF#2 from C2 halt narrative)** — confirmed at plan-time via canonical Read. SUB shape via M9 TABLE entry 12 (`docs/rebuild/plans/` → `docs/components/`) is deterministic + preserves canonical behaviour. Surfaced; not a halt.
4. **C2-bis test-fence subsumption note.** Tests are now dev_only (`**/tests/**`) — file 18's 2 named tests still run in dev mode against canonical (the source they exercise). Synth-time sees no test files. Test-fidelity unaffected by the SUB.
5. **Files 4, 5 also have load-bearing case beyond predecessor recognition** — predecessor §5.4 classified them RW; THIS PLAN revises to SUB / MIXED. Halt-and-surface clean (HSF#1 above caught file 18; HSF#3 from C2 halt is the source for files 4 + 5). Surfaced.
6. **No new ODD §2.5 violations encountered** in surrounding code/docs. All 27 files are legitimately shipping production runtime artefacts; their dev-only-path references are the surface bug.
7. **Plan-author-prime observation: the canonical pos-v2 corpus structure (e.g. `docs/rebuild/plans/`, `docs/rebuild/components/`, `docs/rebuild/capability-corpus/`) is a stable convention** — the M9 SUBSTITUTION_TABLE extension D-Q.ABC-prime.2 codifies it as a repeatable rewrite for v0.x integration-gate runs. Not a halt; surfaces FUTURE_IDEAS_DRAFT capture surface (e.g. "Plugin-relative paths under plugins/dev-sdlc/docs/ should systematically substitute to public docs/design/" — pattern observable across files 5).
8. **Multi-component fence size (8 components + tools/pos-publish-framework-only/) exceeds M-FBM precedent (3 components).** Plan-author-prime verified per-component fences hold independently; pre-seal pytest narrows to touched components per `feedback_amendment_dispatch_speedups`. Build cadence speedups apply.

**Halt summary.** None of the above triggers a halt. All findings surfaced; plan authorised pending owner sign-off on §11 D-Q.ABC-prime.1..4.

---

## 13. AI-time estimate

Per `feedback_duration_estimation_rubric` — categories + formula + calibration table.

### C2-prime (build)

**Category:** multi-component amendment; per-file edits across 8 components × 27 files + M9 SUBSTITUTION_TABLE extension (5 entries) + multi-component seal cycle. Comparable to M-FBM (3 components, 90-180 min, midpoint 135 min) but wider (8 components vs 3; smaller per-file edits — mostly cosmetic prose vs deeper logic; SUB shape adds verification overhead).

Per `feedback_amendment_dispatch_speedups` (narrow test scope, skip pre-seal full rerun, inline methodology snippets), C2-prime can dispatch with the speedups for ~25-40% reduction.

**Predicted (with speedups):** 75-150 min wall-clock midpoint ~110 min.
**Tool-call estimate:** ~600-1100 tool calls × 0.10-0.15 = 60-165 min.

**Risk-adjusted band:** 75-150 min midpoint ~110 min.

### Cumulative + M11a-3

**C2-prime + M11a-3 cumulative:** ~95-185 min midpoint ~140 min (~2.3 hours wall-clock).

**Programme total impact (now accumulated across the C-series):**
- C1 actual: ~25 min
- C2-bis actual: ~25-30 min (THIS DISPATCH Stage 1 + plan)
- C2-prime predicted: 75-150 min
- M11a-3 predicted: 20-35 min
- **Series total:** ~145-240 min midpoint ~190 min (~3 hours wall-clock).

vs original C2 estimate of 70-130 min (midpoint 100 min). The total is ~2× original. Halt-and-surface saves the wall-clock that would have been spent on incomplete C2.

---

## 14. Method-decision register skeleton (post-build)

Filled by the C2-prime builder post-build per existing precedent (M9 §14, M-FBM §14, M7-partition-fix §14, C1 §14, C2-bis §14).

### D-build.ABC-Cprime.x — per-file edits

`<TBD>` — per-file edits + M9 TABLE extension; verification via per-component pytest pre-seal + post-fix synthesis smoke check.

### D-build.ABC-Cprime.0 — AI-time actuals

**Predicted:** 75-150 min midpoint 110. **Actual:** `<TBD>` — to be backfilled post-seal.

### Commit SHAs

- **Plan-doc commit:** `<TBD>` — `docs(plans): C2-prime sub-plan — Class C 21-file production remediation (supersedes C2 portion)`
- **Feature commits (per-component):** `<TBD>` — per touched component + M9 TABLE extension.
- **Amendment manifest commit:** `<TBD>`
- **`loam amend apply` commit:** `<TBD>`
- **Seal commit:** `<TBD>`

---

## 15. References

- **Programme master:** `docs/rebuild/plans/oss-v0-1-0-publish.md`.
- **M11 plan-doc:** `docs/rebuild/plans/oss-v0-1-0-publish-dry-run.md`.
- **C1+C2 combined sub-plan (C2 portion superseded):** `docs/rebuild/plans/oss-v0-1-0-publish-public-docs-classes-abc.md`.
- **C2 halt narrative:** `<workspace>/.scratch/claude-output/oss-v0-1-0-publish-classes-abc-c2-halt.md`.
- **C2-bis sub-plan (sealed):** `docs/rebuild/plans/oss-v0-1-0-publish-public-docs-classes-abc-bis.md`.
- **M-FBM precedent (multi-component fence + multi-amendment series):** `docs/rebuild/plans/oss-v0-1-0-publish-memory-pivot.md`.
- **M7-partition-fix precedent (small-scope sealed-cycle + HOL no-op anchor):** `docs/rebuild/plans/oss-v0-1-0-publish-public-docs-partition-fix.md`.
- **M9 scrub precedent (SUBSTITUTION_TABLE pattern):** `docs/rebuild/plans/oss-v0-1-0-publish-scrub.md`.
- **M2 partition manifest:** `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`.
- **M9 substitution module (extension target):** `framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/substitution.py`.
- **VALUE_PROPOSITION (prime objective):** `docs/rebuild/VALUE_PROPOSITION.md` AC.PO.1 + AC.PO.2.
- **CLAUDE.md design lenses:** `/Users/lukeivers/ivers-corp-pos-v2/CLAUDE.md` §1 + §3.
- **Memory bullets carried forward (cited per dispatch corpus):**
  `feedback_plan_before_code`, `feedback_subagent_odd_violation_halt`,
  `feedback_summarize_and_surface_decisions`, `feedback_critical_thinking_on_deviations`,
  `feedback_serialize_amendment_builds`, `feedback_no_amend_in_agent_dispatches`,
  `feedback_dispatch_explicit_pos_amend_apply`, `feedback_value_proposition_as_prime_objective`,
  `feedback_duration_estimation_rubric`, `feedback_amendment_dispatch_speedups`,
  `feedback_background_default_for_authoring`, `feedback_verify_post_amendment_state`.

---

*End of plan.*
