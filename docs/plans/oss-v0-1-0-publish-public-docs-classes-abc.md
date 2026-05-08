# OSS v0.1.0 publish — public-docs Classes-A/B/C remediation — sub-plan

**Status:** plan-doc (pre-build, plan-before-code). 2026-05-02.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2 / future loam).
**Predecessor:** M11a dispatch-2 HALT at AC.M11a.2 (canonical HEAD `4d75385`). Tree clean.
**Successor target:** M11a re-dispatch (M11a-3) against post-fix HEAD.
**Authority:** Owner ruling 2026-05-02 (M11 plan-doc D-Q.M11.4 — always halt-and-surface; foldback amendments authored sealed before re-dispatch).
**Programme master:** `docs/plans/oss-v0-1-0-publish.md` — §3 AC.OSS.3 source.
**M11 plan:** `docs/plans/oss-v0-1-0-publish-dry-run.md` — §5 AC.M11a.2 outcome bound + §11 D-Q.M11.4 + §14 dispatch-2 entry.
**Sweep report (input):** `<workspace>/.scratch/claude-output/oss-v0-1-0-publish-m11a-sweep-report.md` — three-class root-cause analysis at §3.2.

**Authority documents:**

- M11a dispatch-2 sweep report (three named classes; per-file detail).
- M2 partition manifest at `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml` — current state; reclassification target for Classes A + B.
- M9 SUBSTITUTION_TABLE at `framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/substitution.py` — extension target for Class C systematic substitutes.
- M-FBM precedent (multi-amendment series format reference): `docs/plans/oss-v0-1-0-publish-memory-pivot.md`.
- M7-partition-fix precedent (small-scope sealed-cycle): `docs/plans/oss-v0-1-0-publish-public-docs-partition-fix.md`.
- VALUE_PROPOSITION (prime objective): `docs/VALUE_PROPOSITION.md` AC.PO.1 + AC.PO.2.
- CLAUDE.md design lenses: `/Users/lukeivers/ivers-corp-pos-v2/CLAUDE.md` §1 + §3.

---

## 1. Summary / TL;DR

**Two-amendment series to remediate the three named classes of AC.OSS.3 violations surfaced by M11a dispatch-2 sweep.** Owner D-Q.M11.4 ruled "always halt-and-surface; no auto-foldback at M11a"; this plan-doc is the foldback authoring artefact. Once both amendments seal, M11a re-dispatches against the post-fix HEAD and is expected to close GO.

- **C1 — M2 partition manifest corrective (Classes A + B; mechanical bookkeeping).** Adds three globs to the `dev_only:` block: `**/seals/**` (Class A — per-component SEAL_COMMIT narratives carrying dev-historical references); `**/tests/test_no_sealed_amendments.py` (Class B — dev-discipline meta-test that verifies amendment-cycle invariants); `**/tests/test_AC_*_seal_diff_*.py` (Class B — seal-fence diff-window meta-tests). Single-component fence: `framework/tools/pos-publish-framework-only/` (anchored on HOL per M7-partition-fix precedent — pos-publish-framework-only has no `test_no_sealed_amendments.py`). Estimated **20-35 min AI-time wall-clock**.
- **C2 — Class C remediation (production source/doc references to dev-only paths).** 26 production files reference `docs/rebuild/`, `odd-methodology`, `odd-in-loam`, `loam-mode`, `pos-amend`, or `duration-estimation-rubric` literals. Per-file investigation (this plan §5.3) classified each file into one of three remediation shapes: REWRITE (inherently dev-only reference), SUBSTITUTE (useful public cross-reference; extend M9 SUBSTITUTION_TABLE), or RECLASSIFY (file shouldn't ship publicly at all; add to M2 dev_only). Strategy is a mix; D-Q.ABC.1 surfaces the dominant strategy + per-file overrides. Estimated **45-90 min AI-time wall-clock** depending on strategy ruling.

**Hard cutover:** C1 lands first (cheapest mechanical bookkeeping; closes Classes A + B and shrinks the C2 fence by removing seals/tests as needed verification surfaces); C2 lands second; M11a-3 re-dispatches third. Each amendment seals as its own dispatch-cycle per `feedback_dispatch_explicit_pos_amend_apply`.

**Cumulative AI-time band:** **65-125 min midpoint ~95 min** for both amendments. M11a-3 re-dispatch adds another ~20-35 min wall-clock (mechanical sweep + report).

---

## 2. Owner ruling captured (in-flight; this plan surfaces decisions)

- **M11a D-Q.M11.4 (locked 2026-05-02):** always halt-and-surface; no auto-foldback at M11a. M11a dispatch-2 halted at AC.M11a.2 per this rule.
- **Foldback shape (this dispatch):** plan-author authored coherent multi-class remediation (this plan-doc) covering all three classes; build dispatches execute per ruling.
- **Decisions remaining for owner ruling:** five named D-Q.ABC.1..5 (§11 below). Owner rules from §1 summary + §11 named-decisions block; doesn't need to read the full plan.

---

## 3. Spec-objective placement (per CLAUDE.md §2.5)

The series binds to programme prime ACs:

- **AC.OSS.3 (no dev-discipline machinery in synthesis).** All three classes are AC.OSS.3 violations under the dispatch's literal-match definition. Remediation closes the literal-match grep at M11a-3.
- **AC.OSS.5 (documentary rebrand).** A subset of Class C (e.g. `docs/VALUE_PROPOSITION.md` referenced from `CLAUDE.md`) overlaps AC.OSS.5 — substitute extension would also serve the rebrand surface.
- **AC.OSS.1 (stranger-bootable).** A stranger reading `CLAUDE.md` and clicking through to `docs/VALUE_PROPOSITION.md` hits a missing path; remediation either rewrites to a public doc, substitutes the path at synth time, or removes the reference.
- **AC.PO.1 (translation-burden absorption).** Stranger never sees pos-v2-internal vocabulary (`docs/rebuild/`, `loam-mode`, `pos-amend`, `odd-methodology`) in shipping artefacts.
- **AC.PO.2 (toolkit-primitive growth).** The remediation sharpens the M9 SUBSTITUTION_TABLE pattern + the M2 dev_only partition pattern as repeatable primitives for future v0.x integration-gate runs.

**ODD §2.5 reverse-direction commitment.** Every AC below is outcome-shape; method-shape (which exact regex flags, which exact per-file edits, which exact glob) is the per-amendment builder's call inside the AC outcome bound.

---

## 4. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude leverage

C1 is pure manifest bookkeeping; no Claude-native primitive in scope. C2 composes against Claude's existing Read/Edit primitives + the M9 SUBSTITUTION_TABLE pattern (which itself is a synth-time text-rewrite primitive — composes with `git hash-object -w` + the partition filter). No new MCP server, no new hook event, no new skill required. The remediation EXTENDS two existing harness primitives (M2 partition + M9 substitution); does not invent a third primitive.

**Pass.**

### Lens 2 — Harness + primary-persona value

- **Primary-persona test (translation burden):** post-remediation, a stranger reading `CLAUDE.md` or running through `corpus_inline_session_start` hooks no longer sees `docs/rebuild/` or `pos-amend` vocabulary. Persona's session-start gate references resolve to public paths or are silently elided per partition. Translation burden absorbed.
- **Harness test (toolkit primitive):** the M9 SUBSTITUTION_TABLE grows by 1-3 entries (per Class C strategy), gaining a repeatable "internal-doc-path → public-doc-path" rewrite the harness composes for every future v0.x release. The M2 partition's `dev_only` block grows by 3 entries (Classes A + B), establishing `**/seals/**` + `**/tests/test_no_sealed_amendments.py` + `**/tests/test_AC_*_seal_diff_*.py` as standing dev-only globs that any future component inherits.

**Pass on both tests.**

### Lens 3 — ODD authoring

Each AC below is outcome-shape, observable, deterministic. Method-shape (exact regex, exact glob shape, exact per-file edit) is the per-amendment builder's call. The split into C1 (mechanical Classes A + B) + C2 (Class C remediation) is itself an outcome-shape decision: C1's outcome is "manifest reclassifies the three class A/B globs"; C2's outcome is "all 26 Class C files no longer carry AC.OSS.3 banned literals in synthesis output". Method (does C2 author one big edit-set, or fan out per-component, or use a synth-time substitute, or split into C2a + C2b) is the builder's / owner's call.

**Pass.**

---

## 5. Acceptance criteria — AC.ABC.\*

Outcome-shape only. Method-shape decisions are the per-amendment builder's call. Each AC carries a deterministic verification.

### 5.1 — Class A (seals ship publicly under dev-historical narrative)

#### AC.ABC-A.1 — Partition manifest reclassifies `<comp>/seals/**` as `dev_only`.

The M2 partition manifest's `dev_only:` block contains a glob entry that matches every per-component `seals/` directory in the synthetic tree. Per partition-precedence rule #2 (`dev_only` checked before `dev_and_public`), this glob wins over the broad `framework/<comp>/**` admissions. The seven currently-present `seals/` directories (per dispatch-2 enumeration: `hands-off-lifecycle/seals/`, `objective-tracker/seals/`, `primary-persona/seals/`, `self-upgrade/seals/`, `telegram-interface/seals/`, `workspace-bootstrap/seals/`, `workspace-sync/seals/`) are all matched; future per-component `seals/` directories inherit the same classification.

**Verification.** Post-fix synthesis run produces a `framework-only` branch where `git ls-tree -r refs/heads/framework-only -- '*/seals/*'` returns zero blobs. Per builder's call on glob shape (D-Q.ABC.2 below): preferred `**/seals/**` (catches any future component); acceptable alternative is an explicit per-component list.

### 5.2 — Class B (dev-only meta-tests ship publicly)

#### AC.ABC-B.1 — Partition manifest reclassifies `**/tests/test_no_sealed_amendments.py` as `dev_only`.

M2 partition manifest's `dev_only:` block contains a glob entry matching every `test_no_sealed_amendments.py` test fixture. The 13 currently-present files (per dispatch-2 + recount: `cost-governance`, `dormancy`, `objective-tracker`, `observability-aggregator`, `orchestrator`, `primary-persona`, `reversibility-primitive`, `safety-layer`, `self-correction`, `self-upgrade`, `telegram-interface`, `workspace-bootstrap`, `workspace-sync`) all classify dev_only post-fix; future component tests inherit.

**Verification.** Post-fix synthesis produces a `framework-only` branch where `git ls-tree -r refs/heads/framework-only -- '**/test_no_sealed_amendments.py'` returns zero blobs.

#### AC.ABC-B.2 — Partition manifest reclassifies `**/tests/test_AC_*_seal_diff_*.py` as `dev_only`.

M2 partition manifest's `dev_only:` block contains a glob entry matching every seal-diff-window meta-test. The 10 currently-present files (per dispatch-2 + recount: 5 in `hands-off-lifecycle/tests/test_AC_{A4,CI,OBG,SE,TDG}_S_seal_diff_window.py`, 1 in `objective-tracker/tests/test_AC_SE_S_seal_diff_window.py`, 3 in `primary-persona/tests/test_AC_{A,DSA,M}_S_seal_diff_*.py`, 1 in `workspace-bootstrap/tests/test_AC_E_S_seal_diff_single_component_scope.py`) all classify dev_only post-fix.

**Verification.** Post-fix synthesis produces a `framework-only` branch where `git ls-tree -r refs/heads/framework-only -- '**/tests/test_AC_*_seal_diff_*.py'` returns zero blobs.

### 5.3 — Class C (production source/docs reference dev-only paths)

#### AC.ABC-C.1 — All 26 Class C files contain zero AC.OSS.3 banned literals in synthetic tree post-fix.

For every literal in the AC.OSS.3 excluded-artefact list (`pos-amend`, `loam-mode`, `docs/rebuild/`, `odd-methodology`, `odd-in-loam`, `duration-estimation-rubric`, `framework/tools/pos-publish-framework-only/`), `git grep -F` against the synthetic `framework-only` tree returns ZERO matches in the 26 named Class C files. Remediation per-file shape (REWRITE / SUBSTITUTE / RECLASSIFY) is the C2 builder's call inside the dominant-strategy ruling (D-Q.ABC.1 below).

**Verification.** Post-fix `framework-only` synthesis run; for each banned literal, `git grep -F -l <literal> framework-only` returns zero hits. Cross-check the 26-file enumeration in §5.4 below explicitly.

### 5.4 — Class C per-file remediation table

Per dispatch-author investigation 2026-05-02. For each of the 26 production source/doc files surfacing AC.OSS.3 banned literals: file path; banned-literal hits; remediation shape (RW = rewrite/remove; SUB = synth-time substitute; RECL = reclassify dev_only); and rationale. Plan-author recommends per-file shape; D-Q.ABC.1 captures the dominant strategy + any per-file owner overrides.

| # | File (synthetic tree path) | Hits | Shape | Notes / banned-literal references |
|---|---|---|---|---|
| 1 | `CLAUDE.md` | 1 | **SUB** | Single ref `docs/VALUE_PROPOSITION.md`. Substitute → `docs/VALUE_PROPOSITION.md` in dev mode but → public path in synth. **D-Q.ABC.4 surfaces:** is `VALUE_PROPOSITION.md` a public doc? If yes, substitute path → `docs/VALUE_PROPOSITION.md` and mirror via M7 docs-lane addendum. If no, rewrite line to point at `docs/positioning.md` (which IS public). Plan-author recommends **rewrite to `docs/positioning.md`** — translation-burden test (lens 2) prefers landing strangers on the public positioning doc, not a doc the partition silently maps. |
| 2 | `docs/CLAUDE_CAPABILITIES.md` | 6 | **RW** | 5+ refs to `pos-amend` (lines 55, 140, 542, 599, 839) + 1 to `odd-methodology.md` (line 919). The doc's discussion of `pos-amend` is dev-mode-internal vocabulary; rewrite the surrounding prose to use generic "amendment-cycle CLI" or strip the `pos-amend`-specific discussion entirely (it's about a tool that doesn't ship publicly). The `odd-methodology.md` ref rewrites to `docs/design/odd.md` (public condensed ODD). |
| 3 | `dormancy/docs/architecture.md` | 1 | **RW** | Single ref `../../docs/archive/component-research/dormancy/{brief,proposal,research}.md`. Strip — these are internal build docs; the architecture.md should stand alone or reference public docs only. |
| 4 | `hands-off-lifecycle/hooks/_gate_helpers.py` | 4 | **RW + SUB** | Lines 120-123: 4-entry path tuple for sentinel-checks. Rewrite tuple to drop `docs/FUTURE_IDEAS.md` + `docs/FUTURE_IDEAS_DRAFT.md` (dev-only artefacts). Keep `docs/odd-methodology.md` + `docs/odd-in-loam.md` IFF SUB to `docs/design/odd.md` (collapse to single entry — short form ships). Plan-author recommends: rewrite to single-entry tuple `("docs/design/odd.md",)`. |
| 5 | `hands-off-lifecycle/hooks/corpus_inline_session_start.py` | 11 | **RW** | Heavy dev-only references: `docs/VALUE_PROPOSITION.md`, `docs/STATE.md`, `docs/FUTURE_IDEAS.md`, `plugins/dev-sdlc/docs/odd-methodology.md`, `plugins/dev-sdlc/docs/odd-in-loam.md`. The hook composes a session-start corpus-load envelope referencing dev-only artefacts. **Rewrite path tuple** to public-doc shape: `docs/positioning.md`, `docs/design/odd.md`, `docs/getting-started.md`. The hook itself ships (it's part of the harness's session-start contract); only its referenced corpus changes shape. Multiple `loam-mode` references are dev-tool descriptive (in module docstring); rewrite to generic "session-start emitter" wording. |
| 6 | `hands-off-lifecycle/hooks/corpus_load_sentinel.py` | 4 | **RW** | 1 ref `<workspace>/docs/rebuild/dev-mode-manifest.yaml` + 1 fallback `<workspace>/framework/docs/rebuild/dev-mode-manifest.yaml` + 2 `loam-mode` (descriptive). Rewrite to drop the `docs/rebuild/dev-mode-manifest.yaml` paths (the file MOVED to `plugins/dev-sdlc/dev-mode-manifest.yaml` per M6b.0 — and that plugin is dev_only so the manifest never ships publicly anyway). The hook should fail gracefully when the manifest is absent (it's a dev-mode-only artefact). |
| 7 | `hands-off-lifecycle/hooks/first_run_helper.py` | ~10 | **RW** | All hits are `loam-mode` references in comments + docstrings describing the inner-hook composition shape. Rewrite to "dev-mode session-start emitter" or generic "session-start emit hook" wording. The hook itself ships; only the comment shapes change. |
| 8 | `hands-off-lifecycle/hooks/first_run_settings.py` | 6 | **RW** | All hits are `loam-mode` in comments describing supervisor-stanza composition. Rewrite to generic "dev-mode session-start" wording. |
| 9 | `hands-off-lifecycle/hooks/settings.json.fragment` | 1 | **RW** | Embedded JSON `_comment` field references `bootstrap-progress-statusline.md` plan path (`docs/plans/...`). Rewrite to drop the plan-path reference; the fragment can describe the renderer's purpose without the plan-doc backlink. |
| 10 | `hands-off-lifecycle/hooks/statusline.py` | 1 | **RW** | Single docstring ref to `docs/plans/bootstrap-progress-statusline.md`. Strip the plan-path reference. |
| 11 | `hands-off-lifecycle/README.md` | 3 | **RW** | 3 refs to internal docs (`docs/archive/component-research/true-first-run/`, `docs/FUTURE_IDEAS.md`, `docs/archive/component-research/hands-off-lifecycle/`). Rewrite to point at `docs/components/hands-off-lifecycle.md` (which IS public per `docs/components/` glob in dev_and_public block). |
| 12 | `orchestrator/scripts/pos_session_start.py` | 2 | **RW** | 2 refs to internal plan-paths (`bootstrap-progress-statusline.md`, `memory-pipeline-fix.md`). Strip the plan-path comments; the implementation note can stand alone. |
| 13 | `orchestrator/src/loam/orchestrator/__main__.py` | 1 | **RW** | Single ref to `docs/archive/component-research/orchestrator-bootstrap-unification/proposal.md`. Strip the proposal-path reference (the implementation is the contract). |
| 14 | `orchestrator/src/loam/orchestrator/orchestrator.py` | 3 | **RW** | 3 refs to `docs/archive/component-research/orchestrator-bootstrap-unification/`. Strip. |
| 15 | `primary-persona/src/loam/primary_persona/context_composer.py` | 1 | **RW** | Single docstring fragment `docs/plans/`. Strip — the docstring describes "in-flight plans"; change to "in-flight plans (workspace-defined)". |
| 16 | `primary-persona/src/loam/primary_persona/dispatch_wrapper.py` | 2 | **RW** | 2 refs to `duration-estimation rubric` (lines 31 + 92). The dispatch_wrapper inlines a budget-inference rubric; the rubric itself ships, but the **name** "duration-estimation-rubric" is in the AC.OSS.3 banned literal list. Plan-author recommends: rename inline rubric to "budget-inference rubric" (the function it serves) — keeps the inline content (which is useful), drops the banned name. |
| 17 | `primary-persona/src/loam/primary_persona/session_start_emitter.py` | 2 | **RW** | 2 `loam-mode` references in comments describing timeout precedent. Rewrite to "dev-mode session-start emit timeout". |
| 18 | `primary-persona/src/loam/primary_persona/session_start_gate.py` | 8 | **RW** | 5-entry tuple (lines 54-58): `docs/odd-methodology.md`, `docs/odd-in-loam.md`, `docs/VALUE_PROPOSITION.md`, `docs/STATE.md`, `docs/FUTURE_IDEAS.md`. Rewrite to single public path: `docs/design/odd.md`. The gate's purpose is "verify session-start-relevant docs load"; the single condensed ODD doc serves the test. Lines 155-160: docstring describing `docs/plans/` fallback — strip both fallback paths (the synthesis tree has no `framework/docs/...` prefix anyway). |
| 19 | `primary-persona/templates/persona-template/prompt.md` | 10 | **RW** | 8 refs to `docs/capability-corpus/...` paths in a "Capability index" section (lines 187-194) + 2 refs (`docs/FUTURE_IDEAS_DRAFT.md`, `docs/capability-corpus/`). The capability-corpus is dev-only (ships in `docs/rebuild/`). The template needs significant rewrite: either (a) drop the capability-index section entirely (the persona figures it out without a hardcoded index), or (b) substitute paths to public-doc equivalents IFF the harness ships a public capability-corpus. Plan-author recommends: **drop the capability-index section** (option a); the persona's prompt template already carries a "fetch on demand, not at session-start" doctrine — the index conflicts with that doctrine when the corpus isn't shipping publicly. |
| 20 | `safety-layer/docs/architecture.md` | 1 | **RW** | Single ref `../../docs/archive/component-research/safety-layer/proposal.md`. Strip. |
| 21 | `safety-layer/src/loam/safety_layer/__init__.py` | 1 | **RW** | Single docstring ref `../../docs/archive/component-research/safety-layer/`. Strip. |
| 22 | `safety-layer/src/loam/safety_layer/events.py` | 1 | **RW** | Single docstring ref to `docs/plans/amendment-19-s1-silent-excepts.md`. Strip. |
| 23 | `safety-layer/src/loam/safety_layer/observability.py` | 1 | **RW** | Single docstring ref `docs/plans/research/amendment-19-s1-silent-excepts-research.md`. Strip. |
| 24 | `workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py` | 3 | **SUB or RW** | Line 36: `docs/odd-methodology.md` ref in user-branch comment (rewrite to `docs/design/odd.md`). Lines 573 + 743: `docs/VALUE_PROPOSITION.md` ref in adapter logic — the adapter LOOKS FOR this file at first-run as a sentinel for "this is a pos-v2/loam-canonical workspace". **Plan-author recommends SUB**: extend M9 SUBSTITUTION_TABLE with `docs/VALUE_PROPOSITION.md` → `docs/positioning.md` (or the canonical-public sentinel; D-Q.ABC.4) so the adapter still functions in synthesised v0.1.0 workspaces. Line 36 odd-methodology ref still RW (it's a comment, not load-bearing). |
| 25 | `workspace-bootstrap/src/loam/workspace_bootstrap/adapters/tracker_seed.py` | 4 | **SUB** | 3 refs to `docs/VALUE_PROPOSITION.md` + 1 to `docs/spec/loam-objectives-spec.md` + 1 to `docs/plans/amendment-39-...`. The first two are LOAD-BEARING constants (`FRAMEWORK_VALUE_PROP_RELPATH`, `SPEC_DOC_RELPATH`) used by the tracker_seed adapter to find the canonical objective at first-run. Plan-author recommends **SUB** — extend M9 SUBSTITUTION_TABLE so synthesised v0.1.0 trees see public-doc equivalents (`docs/positioning.md` + `docs/design/objectives.md` if that ships, else strip seed-from-spec functionality at synth time). The plan-doc reference is RW (cosmetic comment). |
| 26 | `workspace-sync/README.md` | 4 | **RW** | 4 refs to internal plan paths (`docs/plans/workspace-sync.md`, `.builder-plan.md`, `.manifest.yaml`). Rewrite to point at `docs/components/workspace-sync.md` (public) for the architecture-level reference; strip per-plan backlinks. |

**Per-file shape totals (plan-author recommendation):**

- **REWRITE/REMOVE: 22 files** (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 26 — most numerous; the surrounding code is dev-mode-internal vocabulary that has no user-facing meaning).
- **SUBSTITUTE (extend M9 TABLE): 2 files** (24, 25 — load-bearing constants where the runtime needs the path to resolve at synthetic-tree first-run; also a partial-substitute for file 1 if owner rules to keep CLAUDE.md's link-out shape).
- **RECLASSIFY (move file to dev_only): 0 files** — none of the 26 Class C files should exit the public ship surface entirely; they are all production runtime hooks, persona templates, or component READMEs that legitimately ship.
- **AMBIGUOUS: 0 files** — every file lands a per-file recommendation; D-Q.ABC.5 carries the dispatch-author's surfaced uncertainty (none in this plan; if owner overrides any per-file shape, the override lands in the build dispatch).

**Halt-and-surface clauses** trigger if more than 30 Class C files surface (this enumeration: 26 — under threshold; not a halt) or if the M9 SUBSTITUTION_TABLE extension would conflict with existing entries (verified: `docs/rebuild/` and `docs/positioning.md` + `docs/design/odd.md` are non-overlapping with the existing 4-entry table; not a halt).

### 5.5 — Sealed-component fences

#### AC.ABC-C1.S — C1 sealed-component fence

C1 amendment is a **single-component-fence** amendment landing in `framework/tools/pos-publish-framework-only/`. Per M7-partition-fix precedent: the tool has no `test_no_sealed_amendments.py`, so the cycle anchors on `hands-off-lifecycle` as a no-op narrative anchor (sidecar bump + SEAL_COMMIT.notes file) and admits the tools-tree path via `universal_paths.prefixes`. `loam amend apply` runs BEFORE the seal commit per `feedback_dispatch_explicit_pos_amend_apply`.

**Verification.** `git diff --name-only BASELINE..SEAL_COMMIT` produces only `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml` + the plan-doc + universal-paths artefacts + HOL `seals/SEAL_COMMIT*`. HOL's `frozen_baseline: true` (H19 pin) verified unchanged.

#### AC.ABC-C2.S — C2 sealed-component fence (multi-component)

C2 amendment is a **multi-component-fence** amendment touching the components named in §5.4's per-file table. Per builder's call inside the locked dominant-strategy ruling: each touched component carries the per-file edits + a SEAL_COMMIT bump. If C2 includes M9 SUBSTITUTION_TABLE extension (per D-Q.ABC.4), the `framework/tools/pos-publish-framework-only/` is also in the fence. `loam amend apply` runs BEFORE seal per `feedback_dispatch_explicit_pos_amend_apply`. NO `git commit --amend` per `feedback_no_amend_in_agent_dispatches`.

**Verification.** Per-component `test_no_sealed_amendments.py` passes on each touched component's seal-fence (these tests are now `dev_only` post-C1, so they run in dev mode against canonical, not in synthesis); per-component `test_AC_*_seal_diff_*.py` window check passes; touched-component pytest passes pre-seal.

---

## 6. Sequencing — slot in master plan §5

Master plan §5 currently sequences M5 → M-FBM → M6 (sealed) → M7 (sealed) → M8 (sealed) → M9 (sealed) → M11 (in flight). M11a dispatch-2 halt at AC.M11a.2 introduces this two-amendment series before M11a-3 re-runs.

```
... → M9 (sealed 2161cb1) → M11a-1 (HALT F-M11a.1)
                          → M7-partition-fix (sealed d983f94)
                          → M8-corrective (sealed 5271091)
                          → M11a-2 (HALT three-class AC.M11a.2)
                          → ABC-C1 (THIS PLAN; mechanical Classes A + B)
                          → ABC-C2 (THIS PLAN; Class C remediation)
                          → M11a-3 (re-dispatch; expected GO)
                          → M11b (owner browse + ruling)
                          → M12 (publish + tag)
```

**Concrete sequencing inside this series:**

1. **Owner rules D-Q.ABC.1..5** (this plan §11). Required before C2 dispatches; C1 is mechanical bookkeeping per M7-partition-fix precedent and could dispatch in parallel with the ruling, but plan-author recommends serialise to avoid redundant builder confusion.
2. **C1 dispatches** (M2 partition manifest corrective; mechanical bookkeeping). Estimated 20-35 min wall-clock. Lands sealed; HEAD advances.
3. **C2 dispatches** (Class C remediation per ruling). Estimated 45-90 min wall-clock per dominant-strategy decision. Lands sealed; HEAD advances.
4. **M11a-3 dispatches** against post-C2 HEAD. Estimated 20-35 min wall-clock for re-sweep + report. Expected GO; if any residual surfaces, foldback dispatches authored separately.

**Post-series HEAD advance sequence (predicted SHA register):**

- C1 plan-doc + manifest commit: `<TBD>`
- C1 `loam amend apply` commit: `<TBD>`
- C1 seal commit: `<TBD>`
- C2 plan-doc commit (if needed): `<TBD>` (or absorbed into this plan-doc's §14 register)
- C2 feature commit(s) (per-component): `<TBD>`
- C2 `loam amend apply` commit: `<TBD>`
- C2 seal commit: `<TBD>`
- M11a-3 sweep run: `<TBD>` (no canonical commit beyond §14 register update)

**Programme total impact.** AI-time band 65-125 min midpoint ~95 min for C1 + C2; M11a-3 adds ~20-35 min. Was 11.5-18 h post-M11a-split midpoint ~13.75 h; post-this-series ~12-19 h midpoint ~14 h.

**Safety property.** C1 is read-only against everything except the manifest YAML; C2 edits source per per-file shape — touched-component tests must pass pre-seal. Halt-and-surface on any test failure or ODD violation per §9 below.

---

## 7. Hard constraints (series-wide)

1. **Plan-before-code** — this doc; §14 anchor present.
2. **Two-amendment series** — C1 and C2 land as separate sealed amendments; do not collapse into one. Rationale: C1 closes Classes A + B with a deterministic glob fix; C2 carries judgment-laden per-file edits — separate fences keep the audit trail clean and let owner rule on each.
3. **No `git commit --amend`** — corrective commits are NEW commits per `feedback_no_amend_in_agent_dispatches`.
4. **`loam amend apply` BEFORE every seal commit** per `feedback_dispatch_explicit_pos_amend_apply`. C1 anchors on HOL no-op narrative (per M7-partition-fix precedent); C2 anchors on each touched component's `test_no_sealed_amendments.py` (which is post-C1 dev_only — runs in dev mode only).
5. **No new third-party deps** — same constraint as M-FBM HC#3 binding analogue.
6. **Halt-and-surface on ODD §2.5 violations** in any touched code/doc per `feedback_subagent_odd_violation_halt`. Builders surface separately; do not silently extend.
7. **Auto-memory MEMORY.md is NOT touched.** Same series-wide constraint as M-FBM.
8. **AC-prefix `AC.ABC-A.*` / `AC.ABC-B.*` / `AC.ABC-C.*`** (collision-safe; verified — neither M11a, M2, M7-partition-fix, nor any other sub-plan uses this prefix).
9. **C2's per-file edits preserve runtime behaviour** — for files 24-25 (load-bearing constants), the SUB shape via M9 SUBSTITUTION_TABLE preserves runtime semantics in canonical dev mode AND synthesised v0.1.0; rewrite shape would break canonical dev mode if the constants are referenced elsewhere. C2 builder verifies via touched-component pytest pre-seal.
10. **C1's glob shape is deterministic.** `**/seals/**` is owner-recommended in §11 D-Q.ABC.2; explicit-list alternative is a per-component fallback. Builder picks once at locked-decision time and the choice is captured in §14.

---

## 8. Out of scope (named explicitly per ODD §2.5)

- **Editing the M11a sweep mechanism itself.** M11a-3 re-dispatches against the existing M11a invocation; this plan doesn't touch the sweep tool.
- **Authoring v0.x foldback amendments for hypothetical future Class A/B/C surfaces** (e.g. a v0.2 component that introduces a new SEAL pattern). Out of v0.1.0 scope; FUTURE_IDEAS_DRAFT capture if a pattern emerges.
- **Reordering M11a's AC list.** M11a's ACs stay as authored; this plan resolves the residual Class A/B/C violations only.
- **Authoring the public-shipping `docs/positioning.md` / `docs/design/odd.md`** — those exist (M7 docs lane sealed). This plan only RW or SUB-extends to those existing public paths.
- **Authoring a new public-shipping `docs/VALUE_PROPOSITION.md`** if D-Q.ABC.4 rules to substitute. If owner picks the substitute path, M7 docs-lane addendum (separate dispatch) authors the public mirror; this plan assumes RW where reasonable.
- **Editing the auto-memory MEMORY.md or any ~/.claude/ corpus.** Out of scope.
- **Capability-corpus public-shipping decision.** File 19 (persona-template/prompt.md) currently references `docs/capability-corpus/...`; this plan recommends drop the capability-index section. If owner rules to ship the capability-corpus publicly (separate v0.x decision), C2's per-file shape for file 19 changes to SUB. D-Q.ABC.5 surfaces this.
- **`upgrade-merge-resolver` retirement / dead-code cleanup.** Same as master plan §9 — out of v0.1.0 scope.
- **History rewrite of canonical pos-v2.** Per master plan §1.1 audit: no history rewrite. M12 squash-at-publish-time only.
- **Any change to the seals/ files themselves.** C1 reclassifies the partition; the seals files stay in canonical dev mode untouched.

---

## 9. Halt-and-surface conditions

Per `feedback_subagent_odd_violation_halt` + `feedback_critical_thinking_on_deviations`. Each builder halts + surfaces to dispatcher on any of:

### Series-wide

- **HT-1 — ODD §2.5 violation surfaces in surrounding code/docs.** Halt; surface; do NOT extend.
- **HT-2 — Wall-time exceeds estimate by >50%.** C1: halt at >55 min. C2: halt at >135 min. Surface progress; let dispatcher rule continuation.
- **HT-3 — Pre-existing test fails post-amendment** (other than mechanical-fixture-update fails for the partition shift itself). Halt — that's a bug.
- **HT-4 — `loam amend apply` returns "skipped: seal-test file missing"** for the targeted component. Resolve per M7-partition-fix HSF#2 pattern: anchor on HOL no-op narrative, admit tool tree via `universal_paths.prefixes`. Surface for dispatcher awareness.

### C1-specific

- **HT-C1.1 — YAML indentation error in manifest edit.** Halt; surface YAML error.
- **HT-C1.2 — Glob over-matching breaks `dev_and_public` admissions.** If `**/seals/**` accidentally matches a `seals/` directory inside `docs/components/<x>/seals/<file>` or similar surface that the partition needs to ship, halt; surface; refine glob shape.
- **HT-C1.3 — Synthesis tool errors post-fix on a different classification gap.** Means another partition gap exists beyond Classes A + B; halt; surface specific cause; expand fix scope or escalate per D-Q.M11.4.

### C2-specific

- **HT-C2.1 — A Class C file's reference shape is genuinely ambiguous and the dispatch-author's recommendation is wrong post-investigation.** Halt; surface specific file + ambiguity; let owner rule.
- **HT-C2.2 — A Class C file's runtime behaviour breaks under the per-file edit** (e.g. a load-bearing constant rewrite leaves the adapter unable to find the canonical sentinel at first-run). Halt; surface failing test; switch shape from RW to SUB or vice versa per ruling.
- **HT-C2.3 — M9 SUBSTITUTION_TABLE extension would conflict with existing 4-entry table.** Plan-author verified non-conflict at plan-time (§5.4); if builder discovers a conflict during edit (e.g. order-sensitivity surfaces), halt; surface; refine table shape.
- **HT-C2.4 — More than 30 Class C files surface during build investigation.** Plan-author count: 26. If a builder finds an additional file the plan-author missed (>30 total), halt; surface; let owner rule whether scope widens.
- **HT-C2.5 — A Class C file remediation requires an unrelated component's source edit** (e.g. file 24's SUB requires a public-shipping `docs/positioning.md` mirror that doesn't exist). Halt; surface; either author the mirror as separate dispatch (M7-docs-addendum) or switch the file's shape to RW.
- **HT-C2.6 — Class C remediation reveals an AC.OSS.5 (rebrand) violation not previously flagged.** Halt; surface; route to M9-corrective separately (do not silently extend C2's fence).

---

## 10. Risks (series-specific)

1. **C1's `**/seals/**` glob over-matches.** Mitigation: pre-edit `git ls-tree -r refs/heads/framework-only -- '*seals*'` confirms zero false-positive matches outside the seven per-component `seals/` dirs. Synthesis smoke check post-edit verifies.
2. **C2 grows during build investigation as builders surface additional Class C-shaped files.** Mitigation: HT-C2.4 halt-clause caps at 30 files; plan-author count of 26 leaves 4-file buffer for surface drift. If exceeded, surface to owner.
3. **C2's RW shape strips load-bearing references.** Mitigation: per-file plan-author analysis at §5.4 already flags files 24-25 as SUB-required (load-bearing constants); HT-C2.2 halt-clause catches any additional load-bearing references the plan-author missed.
4. **C2's per-file edits cascade across components in a single fence.** Mitigation: §5.4 enumerates ~10 components touched (`primary-persona`, `safety-layer`, `orchestrator`, `workspace-bootstrap`, `dormancy`, `hands-off-lifecycle`, `workspace-sync`, plus `framework/tools/pos-publish-framework-only/` for SUB extension if D-Q.ABC.4 rules SUB). Each component's seal-fence holds independently; the multi-component fence is similar in shape to M-FBM (3 components) — precedent exists.
5. **M9 SUBSTITUTION_TABLE order-sensitivity.** Existing table relies on trailing-slash precedence; if D-Q.ABC.4 rules SUB, new entries (e.g. `docs/VALUE_PROPOSITION.md` → `docs/positioning.md`) must order before any prefix-overlapping existing entry. Plan-author verified the existing 4-entry table has no overlap with the proposed Class C substitutes; not a regression risk.
6. **M11a-3 re-dispatch surfaces a NEW class of AC.OSS.3 violations.** Mitigation: D-Q.M11.4 (always halt-and-surface) catches any residual; foldback dispatches authored separately. Cost of additional cycle: 30-90 min per finding.
7. **C2's prompt-template file (file 19) edit changes persona behaviour.** Mitigation: builder runs primary-persona test suite post-edit; HT-C2.2 catches any test failure. The capability-index section drop is a content reduction, not a contract change — primary-persona's prompt template currently carries 8 capability paths; post-edit it carries zero (the persona figures it out by Read-on-demand per the template's own doctrine).

---

## 11. Decisions remaining for owner ruling

Per `feedback_summarize_and_surface_decisions` — five named decisions with recommendations. Owner rules from this summary; doesn't need to read full plan.

### D-Q.ABC.1 — Class C dominant strategy: rewrite-vs-substitute-vs-reclassify-per-file (mission-critical)

**Q.** §5.4 enumerates 26 Class C files with per-file shapes (22 REWRITE, 2 SUBSTITUTE, 0 RECLASSIFY, 0 AMBIGUOUS). The dominant strategy ruling carries:

(a) **REWRITE-as-default with SUB only for load-bearing constants (plan-author recommendation).** 22 files rewrite (drop dev-only path refs, use generic prose); 2 files (24, 25) extend M9 SUBSTITUTION_TABLE because their refs are load-bearing constants. Maximises translation-burden absorption (lens 2 primary-persona test); minimises M9 TABLE growth (table stays small, mechanism stays simple).

(b) **SUBSTITUTE-as-default with RW only for cosmetic refs.** 8-12 files extend M9 SUBSTITUTION_TABLE (every `docs/rebuild/X` → public mirror); ~14 files rewrite (cosmetic prose). Maximises preservation of internal cross-reference structure; grows M9 TABLE significantly (10-15 entries vs 4-7); requires authoring public mirror docs for any path the SUB targets.

(c) **RECLASSIFY-as-default for every file with banned literals.** Move all 26 files to dev_only. Breaks v0.1.0 — most of these files are runtime hooks that MUST ship. Not viable; surfaced for completeness.

**Rec.** **(a) REWRITE-as-default with SUB only for load-bearing constants.** Rationale: (i) lens 2 primary-persona test favours strangers landing on public docs, not silently-mapped paths; (ii) M9 SUBSTITUTION_TABLE stays small + simple (≤7 entries); (iii) RW is mechanical text edits the builder can execute without authoring new public mirrors; (iv) the 2 SUB files (24, 25) are unavoidable because their refs are load-bearing — RW would break the workspace-bootstrap adapter contract; (v) stranger-clone smoke at AC.M11a.6 already exercises the workspace-bootstrap path — SUB ensures it continues passing post-fix.

If owner rules **(b)**: C2 dispatch grows by ~15-30 min (M7-docs-addendum to author public mirrors); M9 TABLE grows; per-file shapes shift toward SUB. Owner-friendlier IFF the cross-reference structure is high-value to public users.

If owner rules per-file overrides: capture per-file owner ruling in §14 dispatch entry.

### D-Q.ABC.2 — Class A glob shape

**Q.** AC.ABC-A.1's glob options: framework-wide `**/seals/**` (catches any future component) vs per-component explicit `framework/<comp>/seals/**` (×7 currently) vs `framework/*/seals/**` (one-level glob).

**Rec.** **`**/seals/**`** (framework-wide). Rationale: (i) catches any future v0.x component that introduces a `seals/` directory without manifest amendment; (ii) consistent with existing `**/__pycache__/**` precedent in `audit_excludes:`; (iii) zero risk of over-matching — `seals/` is a structural-fence convention; no public-shipping artefact under any directory named `seals/` is intended; (iv) verified at plan-time: `git ls-tree -r refs/heads/framework-only -- '*seals*'` returns only the seven per-component `seals/` directories (no false positives).

If owner rules **per-component explicit list**: build-time burden grows for every future component (manifest extension required); but eliminates over-match risk.

### D-Q.ABC.3 — Class B glob shape

**Q.** AC.ABC-B.1 + AC.ABC-B.2 globs: targeted `**/tests/test_no_sealed_amendments.py` + `**/tests/test_AC_*_seal_diff_*.py` vs broader pattern (e.g. `**/tests/test_AC_*_S_*.py` matching the seal-fence test convention).

**Rec.** **Targeted globs** (the two named exact patterns). Rationale: (i) precision avoids accidentally excluding legitimate public tests that happen to match a broader pattern (e.g. a future test named `test_AC_X_S_smoke.py` that exercises a public surface); (ii) the seal-fence test convention currently in use is exhaustive (13 + 10 = 23 files match the targeted globs; no other files match the broader pattern); (iii) future components inherit the same targeted naming convention.

If owner rules **broader `**/tests/test_AC_*_S_*.py`** pattern: simpler glob; risks accidentally excluding future legitimate tests; recommended IFF M3-M5 wire-CLI tests adopt a different naming convention to avoid the `_S_` suffix.

### D-Q.ABC.4 — M9 SUBSTITUTION_TABLE extension scope

**Q.** Extend M9 SUBSTITUTION_TABLE with new entries for Class C SUB files (per §5.4 files 24, 25), or one-off rewrite for unique cases?

**Rec.** **Extend SUBSTITUTION_TABLE for systematic substitutes.** Specifically: add 1-3 entries:

- `docs/VALUE_PROPOSITION.md` → `docs/positioning.md` (used by files 1, 24, 25)
- `docs/spec/loam-objectives-spec.md` → strip-or-substitute (file 25 only; D-Q.ABC.5 sub-decision below)
- `docs/odd-methodology.md` (root-level, NOT under `docs/rebuild/`) → `docs/design/odd.md` (used by files 4, 18)

Rationale: (i) mirrors M9's existing 4-entry pattern (systematic substitutes for cross-cutting tokens); (ii) load-bearing constants in files 24, 25 require runtime resolution at synthesis time — only SUB satisfies the contract; (iii) future components inheriting the same path conventions get free remediation; (iv) plan-author verified non-conflict with existing 4-entry table at plan-time.

If owner rules **one-off rewrite + small TABLE**: 2 files (24, 25) RW their constants directly; M9 TABLE stays at 4 entries; risk: the SUB path no longer applies cleanly to future components that adopt the same convention.

### D-Q.ABC.5 — Per-file decisions surfaced from plan-author investigation

**Q.** Per-file shape decisions the plan-author can't lock without owner ruling. Two surfaced:

(a) **File 1 (`CLAUDE.md` line 49 — `docs/VALUE_PROPOSITION.md` reference).** Plan-author recommended REWRITE to `docs/positioning.md`. Alternative: SUBSTITUTE via M9 TABLE (per D-Q.ABC.4) so the canonical CLAUDE.md keeps the `docs/rebuild/...` reference (useful in dev mode) and synth rewrites to public path. **Owner ruling needed** on whether `CLAUDE.md`'s authority-doc backlink should be RW (loses the dev-mode authority pointer) or SUB (canonical readers see the dev path; public readers see the public path). Plan-author recommends **SUB** if owner picks D-Q.ABC.4 = (extend), else **RW**.

(b) **File 19 (`primary-persona/templates/persona-template/prompt.md` lines 187-194 — capability-index section).** Plan-author recommended DROP the section. Alternative: SUB to a public capability-corpus IFF v0.x ships one. Plan-author recommends **DROP** because the persona's own template doctrine ("fetch on demand, not at session-start") supports it; if owner wants the index preserved, the v0.x decision to ship a public capability-corpus is a separate scope-of-work that gates this sub-decision.

If owner rules differently on (a) or (b): capture override in C2 dispatch entry; per-file shape adjusts; AC.ABC-C.1 verification still holds.

---

## 12. Halt-and-surface findings encountered during plan authoring

Per the dispatch's halt-and-surface clause: surface any audit / methodology / surrounding-code / surrounding-docs ODD violations encountered while authoring this plan.

**Findings (none triggers a halt):**

1. **Class C file count: 26** (within sweep-report's "21+" estimate; under 30-file halt threshold). Verified via `git grep -F -l -E 'docs/rebuild/|odd-methodology|odd-in-loam|loam-mode|pos-amend|duration-estimation' framework-only -- ':!*/seals/*' ':!*/tests/*'`. No halt.
2. **Two new Class C files surfaced beyond dispatch's 21-file enumeration:** `primary-persona/src/loam/primary_persona/dispatch_wrapper.py` (lines 31, 92 — `duration-estimation rubric` literal in inline comments — file 16 in §5.4 table) and `hands-off-lifecycle/hooks/settings.json.fragment` (line 2 — `docs/plans/bootstrap-progress-statusline.md` in JSON `_comment` field — file 9 in §5.4). The full 26-file enumeration in §5.4 supersedes the dispatch-2 sweep report's "21+ files" partial list. **Surfaced; not a halt** — well under 30 threshold.
3. **`docs/odd-methodology.md` root-level path referenced** by files 4 + 18 (`_gate_helpers.py` line 120, `session_start_gate.py` line 54). This is NOT under `docs/rebuild/` — it's a root-level path that doesn't exist in either the canonical tree OR the synthetic tree (only `docs/design/odd.md` exists publicly; `plugins/dev-sdlc/docs/odd-methodology.md` exists in dev-only). The literal still trips the AC.OSS.3 grep on `odd-methodology`. RW to `docs/design/odd.md` resolves both AC + the orphan-path issue. **Not a halt** — surfaced as a clarifying observation.
4. **`docs/odd-in-loam.md` root-level path** similarly orphan (referenced by files 4 + 18). Same RW resolution. **Not a halt.**
5. **No new ODD §2.5 violations encountered in surrounding code/docs.** All Class C files are legitimately shipping production runtime artefacts; their dev-only-path references are the surface bug, not deeper structural violations.
6. **Plan-author observation: capability-corpus public-shipping is a strategic v0.x decision.** File 19's capability-index section is the surface symptom; the deeper question ("does loam ship its capability corpus publicly?") is owner-strategic. Plan-author surfaces as D-Q.ABC.5 (b) for ruling; recommends DROP for v0.1.0; v0.2 lane could revisit. **Not a halt** — surfaces D-Q.ABC.5 (b) for owner ruling.
7. **`primary-persona/templates/persona-template/prompt.md` ALSO references `docs/FUTURE_IDEAS_DRAFT.md`** at line 251 (described as "the no-overhead capture surface"). This adds an 11th hit on file 19. RW: change to "the workspace's FUTURE_IDEAS_DRAFT capture surface" (generic; resolves at runtime from the workspace's own conventions). **Not a halt** — fold into file 19's RW shape.
8. **C1's HOL anchor pattern (per M7-partition-fix HSF#2)** — pos-publish-framework-only has no `test_no_sealed_amendments.py`, so the cycle anchors on HOL as no-op narrative anchor and admits via `universal_paths.prefixes`. C1 dispatch must explicitly name this pattern; otherwise builder will hit the same HSF#2 surface as M7-partition-fix. **Surfaced for dispatcher** (not for owner); not a halt.

**Halt summary.** None of the above triggers a halt. All findings surfaced; plan authorised pending owner sign-off on §11 D-Q.ABC.1..5.

---

## 13. AI-time estimate

Per `feedback_duration_estimation_rubric` — categories + formula + calibration table.

### C1 (mechanical Classes A + B)

**Category:** single-component amendment; manifest YAML edit + glob authoring + synthesis smoke check + seal cycle. Comparable to M7-partition-fix (~30-32 min actual wall-clock per its §14 D-build.M7-fix.0).

**Predicted:** 20-35 min wall-clock midpoint ~28 min.
**Tool-call estimate:** ~150-250 tool calls × 0.10-0.15 = 15-37 min.

**Risk-adjusted band:** 20-35 min.

### C2 (Class C remediation)

**Category:** multi-component amendment; per-file edits across 10 components × ~26 files + optional M9 SUBSTITUTION_TABLE extension + multi-component seal cycle. Comparable to M-FBM (3 components, 90-180 min, midpoint 135 min) but wider (10 components vs 3; smaller per-file edits — mostly cosmetic prose vs deeper logic). Per `feedback_amendment_dispatch_speedups` (narrow test scope, skip pre-seal full rerun, inline methodology snippets), C2 can dispatch with the speedups for ~25-40% reduction.

**Predicted (with speedups):** 45-90 min wall-clock midpoint ~67 min.
**Tool-call estimate:** ~400-700 tool calls × 0.10-0.15 = 40-105 min.

**Risk-adjusted band:** 45-90 min.

**If owner picks D-Q.ABC.1 = (b) SUBSTITUTE-as-default:** add 15-30 min for M7-docs-addendum (public mirrors); C2 grows to 60-120 min midpoint ~90 min.

### Cumulative + M11a-3

**C1 + C2 cumulative:** 65-125 min midpoint ~95 min (per recommended D-Q.ABC.1 = (a)).

**M11a-3 re-dispatch:** 20-35 min midpoint ~28 min (per M11a dispatch-2 actual 25 min).

**Series total (C1 + C2 + M11a-3):** **85-160 min midpoint ~123 min (~2 hours wall-clock)**.

**Programme total impact.** v0.1.0 critical path was 11.5-18 h post-M11a-split midpoint ~13.75 h; post-this-series ~12-19 h midpoint ~14 h.

---

## 14. Method-decision register skeleton (post-build per amendment)

Filled by each phase's builder post-build per existing precedent (M9 §14, M-FBM §14, M7-partition-fix §14).

### C1 — OSS-build.ABC-C1.x — sealed 2026-05-02

- **D-build.ABC-C1.0** AI-time actuals: predicted 20-35 min midpoint 28; actual ~25 min wall-clock — within band, tracks M7-partition-fix precedent (~32 min).
- **D-build.ABC-C1.1** Glob shape locked per D-Q.ABC.2 = (a): framework-wide `**/seals/**` (catches future v0.x components without manifest amendment).
- **D-build.ABC-C1.2** YAML edit mechanism: 3 single-line `- glob:` entries appended to existing `dev_only:` block under the `test_AC_AG_*` / `test_AC_BAG_*` HOL gate-test admissions, with provenance comments citing this plan-doc + locked decisions. Targeted exact patterns for Class B (D-Q.ABC.3 = a) over broader patterns to avoid false-positive exclusion of legitimate public tests.
- **D-build.ABC-C1.3** Synthesis smoke check: `python -m loam.publish_framework_only.cli` advanced `refs/heads/framework-only` → `cbebfd3` (source `cb029a0`); per-glob `git ls-tree -r refs/heads/framework-only | grep <glob>` verified zero residuals across all three globs. AC.ABC-A.1 + AC.ABC-B.1 + AC.ABC-B.2 PASS empirically.
- **D-build.ABC-C1.4** HOL anchor pattern applied per M2 + M7-partition-fix HSF#2 precedent (`pos-publish-framework-only` has no `test_no_sealed_amendments.py`; HOL anchors via `universal_paths.prefixes`). Initial manifest-validate + apply --dry-run pattern verified clean before commit.
- **D-build.ABC-C1.5** Touched-component test count: zero pytest required for C1 (pure manifest YAML + HOL no-op anchor; no behaviour code edits). `loam amend seal --scoped-sweep` ran the standard cross-component sweep clean.

### C2 — OSS-build.ABC-C2.x — HALTED at HT-C2.4 + HT-C2.2 — 2026-05-02

C2 dispatch HALTED during build investigation. Halt-and-surface report at `<workspace>/.scratch/claude-output/oss-v0-1-0-publish-classes-abc-c2-halt.md`.

- **D-build.ABC-C2.HALT** Root cause: plan §5.4's Class C enumeration of 26 files is partial — restricted to "production source/doc files only" — but AC.M11a.2's verification is a literal-match grep across the full synthetic tree, including 109 test files containing dev-only literals as assertion strings, fixture content, comments, and docstrings. Closing the 26 named files would still leave M11a-3 in halt-fail.
- **D-build.ABC-C2.HSF#1** HT-C2.4 fired (>30 Class C files). Empirical post-C1 sweep: `docs/rebuild` literal in 130 files (109 tests + 21 production); `loam-mode` in 20; `odd-methodology` in 26; etc.
- **D-build.ABC-C2.HSF#2** HT-C2.2 fired on file 18 (`session_start_gate.py` lines 153-180). Function-body literal `docs/plans/` is runtime-load-bearing in dev mode + asserted by 2 tests. Plan §5.4's per-file shape (RW) cannot apply without breaking behaviour. Resolution requires SUBSTITUTION_TABLE 4th entry or per-test fixture-update.
- **D-build.ABC-C2.HSF#3** D-Q.ABC.4's 3-entry SUBSTITUTION_TABLE undersized — does not cover the `docs/rebuild/*` paths surfaced as load-bearing constants (STATE.md, FUTURE_IDEAS.md, FUTURE_IDEAS_DRAFT.md, plans/, components/, plugins/dev-sdlc/docs/odd-{methodology,in-loam}.md). ~5-7 additional entries likely needed for a clean C2 close.
- **D-build.ABC-C2.HSF#4** Plan §10 risk #2 mitigation review: the "+4 file buffer" was inadequate for the actual scope-shape mismatch (109-file overage). Future plans should distinguish "surface drift" (extra files of same shape) from "scope-shape mismatch" (different classification axis).
- **D-build.ABC-C2.NEXT** Recommended forward path (for owner ruling): **Option A then B in series.**
  - **Option A — C2-bis** (mechanical): single-line manifest edit adding `**/tests/**` to `dev_only:`. ~20-30 min wall-clock per M7-partition-fix precedent. Closes the 109 test-file residuals at one stroke. (Industry-convention shape — most v1.0 OSS releases don't ship internal test suites in source tarballs.)
  - **Option B — C2-prime** (re-shaped Class C remediation): re-plan against the smaller accurate population (21 production files); owner rules on (i) per-file overrides (file 1, 5, 6 may need SUB; file 18 needs SUB for load-bearing function-body), (ii) SUBSTITUTION_TABLE scope expansion (~5-7 additional entries), (iii) re-dispatch.
  - **Cumulative cost:** ~140-260 min midpoint ~200 min for C2-bis + C2-prime + M11a-3 vs the original 70-130 min C2 estimate. Original estimate didn't account for test-file scope.

### Commit SHAs

- **C1 plan-doc commit:** `21bf1c0` — `docs(plans): C1+C2 combined-remediation sub-plan`
- **C1 feature commit (manifest YAML):** `cb029a0` — `feat(public): C1 partition manifest — Classes A+B reclassified dev_only`
- **C1 amendment manifest commit:** `b260c9f` — `docs(plans): C1 amendment manifest — Classes A+B partition reclassification`
- **C1 `loam amend apply` commit:** `bb00f29` — `chore(loam-amend-apply): loam amend apply for C1 Class A+B partition reclassification`
- **C1 seal commit:** `e2cbeec` — `chore(seals): oss-v0-1-0-publish-public-docs-classes-abc-c1 — hands-off-lifecycle at bb00f29`
- **C2 plan-doc update commit (this §14 backfill):** `<TBD>` — to be assigned at commit-time.
- **C2 feature commits:** **DEFERRED — HALT** (see D-build.ABC-C2.HALT above).
- **C2 `loam amend apply` commit:** **DEFERRED — HALT.**
- **C2 seal commit:** **DEFERRED — HALT.**
- **M11a-3 re-dispatch:** **DEFERRED — pending C2-bis + C2-prime resolution per HSF#1.**

---

## 15. References

- **Programme master:** `docs/plans/oss-v0-1-0-publish.md` — §3 AC.OSS.3 source.
- **M11 plan-doc:** `docs/plans/oss-v0-1-0-publish-dry-run.md` — §5 AC.M11a.2 outcome bound + §11 D-Q.M11.4 + §14 dispatch-2 entry.
- **M11a sweep report (input):** `<workspace>/.scratch/claude-output/oss-v0-1-0-publish-m11a-sweep-report.md` — three-class root-cause analysis at §3.2.
- **M-FBM precedent (multi-amendment series + multi-component fence):** `docs/plans/oss-v0-1-0-publish-memory-pivot.md`.
- **M7-partition-fix precedent (small-scope sealed-cycle + HOL no-op anchor):** `docs/plans/oss-v0-1-0-publish-public-docs-partition-fix.md`.
- **M9 scrub precedent (SUBSTITUTION_TABLE pattern):** `docs/plans/oss-v0-1-0-publish-scrub.md`.
- **M2 partition manifest under edit (Classes A + B target):** `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`.
- **M9 substitution module (Class C SUB extension target):** `framework/tools/pos-publish-framework-only/src/loam/publish_framework_only/substitution.py`.
- **VALUE_PROPOSITION (prime objective):** `docs/VALUE_PROPOSITION.md` AC.PO.1 + AC.PO.2.
- **CLAUDE.md design lenses:** `/Users/lukeivers/ivers-corp-pos-v2/CLAUDE.md` §1 + §3.
- **Memory bullets carried forward (cited per dispatch corpus):**
  `feedback_plan_before_code`, `feedback_subagent_odd_violation_halt`,
  `feedback_summarize_and_surface_decisions`, `feedback_critical_thinking_on_deviations`,
  `feedback_serialize_amendment_builds`, `feedback_no_amend_in_agent_dispatches`,
  `feedback_dispatch_explicit_pos_amend_apply`, `feedback_value_proposition_as_prime_objective`,
  `feedback_duration_estimation_rubric`, `feedback_amendment_dispatch_speedups`,
  `feedback_background_default_for_authoring`.

---

*End of plan.*
