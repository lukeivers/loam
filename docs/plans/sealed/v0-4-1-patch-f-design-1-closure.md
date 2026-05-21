# v0.4.1 patch — F-DESIGN-1 closure (multi-commit + from-scratch + tie-breaker)

**Status:** finalized at dispatch time. Plan-before-code per `feedback_plan_before_code` (hard rule).
**Slug:** `v0-4-1-patch-f-design-1-closure`
**Date authored:** 2026-05-09.
**Parent authority:** `docs/release-roadmap.md` §6 owner-action-line entry on F-DESIGN-1; v0.4.0 SHIPPED at seal `7787a226` per §2.
**Predecessor:** v0.4.0 C5 §14 backfill commit `895718d3` (HEAD at dispatch).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Owner authorization:** Telegram 10448 ("Push 0.4.0. Move on to 0.4.1.").

---

## §1 — Outcome shape (the "why")

v0.4.0 C4 ProgramBench v0 baseline empirically confirmed that loam's code-gen surface is shaped for **extending an existing repo** (consume objectives.yaml + emit unified diff against source tree) — NOT for **writing from scratch given only docs**. Variant A scored 56% (9/16) vs direct `claude -p` baseline 100% (16/16) on 3 small tasks. The structural mechanism (per `docs/experiments/programbench-v0-docs-only.md` §3 "F-DESIGN-1 confirmed"):

1. **Single-commit-per-candidate.** C1's `--code-gen` produces ONE commit per invocation. Multi-file submissions need ≥2 files (build script + source); single-commit cannot author both.
2. **Prompt assumes existing source.** "Produce a unified diff" defaults to `--- a/<path>` against (possibly hallucinated) source. Cold-start needs `--- /dev/null` + create-new-files framing.
3. **Build-next ranking ties resolve alphabetically.** Task 2's tie between `error-handling` and `formatting` resolved to `error-handling` (less load-bearing). Wrong objective got selected without operator override.

v0.4.1 is a PATCH-class release per `docs/release-versioning-policy.md` — defect closure within v0.4.0's outcome. **It does not extend v0.4.0's outcome shape**; it makes the v0.4.0 outcome work on the cold-start docs-only multi-file class of task that C4 surfaced as a gap.

## §2 — Prime objective ladder

VALUE_PROPOSITION.md prime objective (loam helps people use LLMs to build software) → v0.4.0 release-roadmap §3 outcome (loam ships working code from extracted objectives) → F-DESIGN-1 closure (cold-start docs-only multi-file code-gen works) → v0.4.1 ACs `AC.V041.*` below (3 sub-fixes + ProgramBench re-run + no-regression + HARD smoke).

## §3 — Component fence

**PRIMARY:** `plugins/dev-sdlc/odd-extractor/` — same component v0.4.0 C1+C2 extended. No new component, no new package. Edits land in:

- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/code_gen.py` — multi-commit emission + from-scratch prompt mode.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/build_next.py` — tie-break extension beyond alphabetical.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/cli.py` — surface flags for from-scratch mode (auto-detect + explicit override) and any new tie-break operator surface.
- `plugins/dev-sdlc/odd-extractor/tests/test_AC_V041_*.py` — new tests covering the 3 sub-fixes + no-regression.

**Read-only:**
- `framework/objective-tracker/src/loam/objective_tracker/spec.py` — `LiftedFrom` schema (consumed; sealed in amendment #38).
- All other framework components — sealed.
- C1+C2 code-gen prior surface — extended via NEW commits; existing tests must continue to pass without edit.

**Universal admissions:** `docs/plans/v0-4-1-patch-f-design-1-closure.md` (this file), `docs/plans/v0-4-1-patch-f-design-1-closure.manifest.yaml`, seal narrative file, `docs/release-roadmap.md` §6 (mark closure of the F-DESIGN-1 owner-action-line on completion), `docs/STATE.md` (v0.4.1 SHIPPED rollup row), and `docs/experiments/programbench-v0-docs-only.md` (append v0.4.1 re-run section per AC.V041.4).

**Out of fence:** `framework/`, `plugins/dev-sdlc/seals/`, any other plugin tree, sealed objective-tracker schema. Edits outside fence = halt.

## §4 — AC family `AC.V041.*` (TIGHT)

Each AC maps to ≥1 test under `plugins/dev-sdlc/odd-extractor/tests/test_AC_V041_*.py` OR an empirical artefact (the ProgramBench re-run report, the HARD smoke writeup). The agent authors test names within the convention.

### AC.V041.1 — Multi-commit-per-task

When the build-next candidate's natural decomposition spans ≥2 files (e.g., a build script + a source file, or schema + handler + test), the code-gen emits **multiple `CodeGenCommit` records** in a single `CodeGenDiff`. Each commit carries its own `objectives:` block (same `lifted_from.source_doc` + `source_ac` from the parent candidate; the per-commit shape preserved from amendment #38 schema).

The schema (`CodeGenDiff.commits: tuple[CodeGenCommit, ...]`) already supports this; only the emit logic needs widening. The widening path:

- The LLM prompt is widened to instruct multi-commit when the candidate naturally decomposes (heuristic: gap rationale references multiple file types, OR an explicit `--multi-commit` flag). Builder rules on the heuristic shape (method).
- The response parser is widened to consume multiple `subject:` + diff-body pairs separated by a delimiter the prompt names. Builder rules on the delimiter shape (method).
- `persist_diff` already handles multi-commit (it iterates `diff.commits`); no change required there.

**Test:** A new `test_AC_V041_1_multi_commit.py` invokes `generate_code` against a fixture whose build-next candidate naturally decomposes (e.g., a "JSON pretty-printer" objective whose gap covers BOTH the source file AND the build script). Test asserts the returned `CodeGenDiff.commits` has length ≥2; each commit has its own `objectives:` block; each commit's `diff_text` contains a `--- /dev/null` line (from-scratch shape).

`outcome-altitude: false` (schema + emit-shape; method-altitude). Verified via stub-injected LLM client returning a controlled multi-commit response.

### AC.V041.2 — From-scratch prompt mode

When the source directory is empty (or near-empty per a heuristic the builder defines, e.g., "no source files matching the build-next gap's domain"), the code-gen path uses a **from-scratch** prompt instead of the existing extend-existing prompt. The from-scratch prompt:

- Instructs "create new files" not "modify existing source."
- Uses `--- /dev/null` as the source-side line in the unified diff.
- Optionally scaffolds initial structure (test file, source file skeleton, package config) before generating implementation.

Mode selection: explicit flag (e.g., `--from-scratch`) on the CLI OR auto-detect when the source directory is empty per the heuristic. Both must work.

**Test:** A new `test_AC_V041_2_from_scratch_mode.py` invokes `generate_code` against a fixture with an empty source dir; asserts the LLM prompt sent (captured via the stub's `last_call_kwargs`) contains the from-scratch framing (named markers like "create new files" or `--- /dev/null` instructions); asserts the returned diff_text contains `--- /dev/null` source-side lines.

`outcome-altitude: false` (prompt-shape branching). Verified via stub-injected LLM client.

### AC.V041.3 — Build-next tie-breaker beyond alphabetical

When multiple build-next candidates have **equal composite_score**, the tie-breaker uses a documented heuristic that is **NOT alphabetical** as the primary signal. The chosen heuristic (builder picks one, documents the choice in §14):

- Higher gap-confidence (STRONG > WEAK) — already in `_tiebreak_key`.
- OR shorter dependency chain (objective with fewer prerequisite objectives ranked higher).
- OR higher orphan-cluster size (more evidence rows = more load-bearing).
- OR explicit user-pin via a `build-next.yaml` user-config carrier (e.g., `pinned_first: <gap_id>`).

Alphabetical only as the **final fallback** when all other signals are equal. Documented in `build_next.py` module docstring + the manifest method-decision register.

**Test:** A new `test_AC_V041_3_tie_breaker.py` constructs a synthetic gap-inventory where two gaps tie on composite_score but differ on the chosen heuristic dimension (e.g., one is STRONG, the other WEAK; or one has cluster_size 5, the other 1). Asserts the higher-heuristic candidate ranks first; alphabetical only fires when all heuristic dimensions tie.

`outcome-altitude: false` (deterministic ranking; method-altitude).

### AC.V041.4 — ProgramBench v0 re-run (Variant A vs baseline)

Re-run the same 3 ProgramBench tasks from v0.4.0 C4 (`testorg__calculator.abc1234`, `jsonpp`, `wcclone`) under the v0.4.1 surface. Same baseline (direct `claude -p`). Goal: meaningfully closer to baseline 100%.

**Procedure:** for each task, run the full 5-stage pipeline (extract → interview → gaps → build-next → code-gen) under v0.4.1 HEAD; record per-task pass rate; compare to v0.4.0 C4 numbers. Append a `## v0.4.1 re-run` section to `docs/experiments/programbench-v0-docs-only.md` with the per-task table and aggregate verdict. Same cost ceiling as C4 ($5 per dispatch directive); subscription-only architecture preserved (real `claude -p --strict-mcp-config`).

**Verdict shape:** GREEN if Variant A aggregate pass-rate is meaningfully closer to 100% than C4's 56% (e.g., ≥75%, with the specific bar set at empirical-time per outcome data). RED if ≤56% (no improvement = the 3 sub-fixes don't move the needle = halt-and-surface as F-DESIGN-2). YELLOW if 57-74% (partial improvement; surface for owner ruling).

`outcome-altitude: true` — real `claude -p` subprocess, real fixture inputs, real behavioral test pass rates. Per `feedback_test_outcome_altitude_required.md`.

### AC.V041.5 — No regression

All previously-passing tests still pass. Specifically:

- `pytest plugins/dev-sdlc/odd-extractor/tests/` returns 0 with the v0.4.0-sealed test count (verify pre-existing tests untouched via `git diff --stat`).
- `loam amend apply --dry-run` GREEN against the v0.4.1 manifest pre-apply AND post-seal.
- C1 outcome-altitude AC (AC.V040C2.1 against `jsts-playwright-app`) is NOT re-run inline (that's a 60-120s real-`claude -p` run; v0.4.0 C5's HARD smoke-clean state is the inherited baseline).

`outcome-altitude: false` (no-regression invariant; covered by the test suite).

### AC.V041.6 (outcome-altitude) — HARD smoke against rd-automation

Per `feedback_hard_smoke_per_minor_before_publish.md`: every minor's release sequence has a HARD smoke gate against rd-automation. Even though v0.4.1 is a patch (not a minor), the same rule applies because public-action gating happens at the v0.4.1 publish line. Cold install of v0.4.1 HEAD into a fresh venv; real `claude -p` subprocess; real rd-automation tree at `/Users/lukeivers/pos3/workspace/rd-automation`; end-to-end extract + verify objectives.yaml + key fields; regression ride-along on F-LEAK / F-TIMEOUT / F-VERIFY-ORPHAN closures from v0.2.5.1.

**Verdict:** GREEN before publish. RED triggers corrective + re-smoke.

**Output:** writeup at `<workspace>/.scratch/claude-output/v0-4-1-hard-smoke.md` per the v0.3.0 / v0.4.0 precedent.

`outcome-altitude: true` per the rubric — cold install + real `claude -p` + real fixture, no monkeypatch.

### AC.V041.S — Seal-diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` shows changes only under:

- `plugins/dev-sdlc/odd-extractor/` (source + tests + fixtures).
- `docs/plans/v0-4-1-patch-*` (this plan + manifest + seal narrative).
- `docs/experiments/programbench-v0-docs-only.md` (re-run append).
- `docs/release-roadmap.md` (§6 owner-action-line entry closed; §2 SHIPPED row appended).
- `docs/STATE.md` (v0.4.1 SHIPPED rollup row).

Anything outside that set is a halt condition.

## §5 — Hard constraints

1. **No `--amend`.** Corrective commits are NEW commits. Streak intact (every cycle since v0.3.0 C5 stayed clean).
2. **Scope fence per §3.** Edits outside fence = halt.
3. **No Anthropic API key, no `pip install anthropic`.** All LLM calls route through `claude -p` subprocess via `claude_print_synthesis_client.py`. Same shim that v0.4.0 used. No new SDK dependency.
4. **`--strict-mcp-config` invariant.** Every production-path `claude -p` invocation passes `--strict-mcp-config` + empty MCP config tempfile per the v0.2.5 C5 propagation invariant.
5. **No new runtime deps.** Pydantic + pyyaml + the existing odd-extractor dep set already pinned.
6. **`loam amend apply --dry-run` green** is a hard prereq + hard post-apply gate.
7. **No public action.** No `git push`, no `git tag`, no GitHub Release. v0.4.1 HALTS at seal; owner gates the publish.
8. **Reuse amendment #38 `LiftedFrom` schema by import.** No re-authoring.
9. **Plan-before-code.** This plan-doc lands BEFORE source edits.
10. **ODD §2.5 + §2.4.** Every line of code maps to a named AC. No method-in-AC. No "options to rule on" framing.
11. **Outcome-altitude AC requirement** per `feedback_test_outcome_altitude_required.md`. AC.V041.4 + AC.V041.6 are the outcome-altitude probes (real `claude -p` runs).

## §6 — Out of scope (explicit)

- Variant B (docs+binary feeder) — v0.5.0 territory.
- ProgramBench leaderboard submission — v0.5.0 AC.V050.4.
- linux/amd64 + Docker testbed for full ProgramBench eval — v0.5.0+.
- Schema widening on `objective-tracker` — sealed in amendment #38.
- New CLI verb (e.g., `loam build-next-and-codegen`) — out; reuse `--code-gen`.
- Multi-fixture HARD smoke beyond rd-automation — v0.5.0+.
- BYOK / multi-provider — subscription-only architectural floor preserved.
- jsts-playwright-app outcome-altitude re-run inline — covered by v0.4.0 C2 sealed state + AC.V041.5 no-regression.

## §7 — Halt triggers

1. Cross-component scope expansion beyond `plugins/dev-sdlc/odd-extractor/`. Halt + surface.
2. AC.V041.* count grows beyond 6 (excluding `.S`). ODD §2.5 violation triage; halt.
3. AC.V041.4 ProgramBench re-run produces aggregate Variant A ≤56% (no improvement). Halt; surface as F-DESIGN-2 with recommendation for v0.4.2 or v0.5.0 reframe.
4. AC.V041.6 HARD smoke RED. Halt; corrective NEW commit + re-smoke.
5. Any reach for `--amend`, `git push`, or `git tag`. Immediate halt.
6. Subscription-only constraint violated (any new `import anthropic`, any new `ANTHROPIC_API_KEY` env reference). Immediate halt.
7. AI-time exceeds upper band (240 min) by >50% → 360 min wall-clock. Halt with current state.
8. ODD §2.5 violation discovered in surrounding code. Halt + surface.
9. Cost runaway >$5 on the ProgramBench re-run. Halt; reduce task count or model.
10. WD mismatch — `pwd` returns anything other than `/Users/lukeivers/ivers-corp-pos-v2`. Immediate halt.

## §8 — Dependencies

- v0.4.0 SHIPPED state (seal `7787a226`) — predecessor; consumed read-only.
- Amendment #38 `LiftedFrom` schema (sealed; consumed read-only).
- v0.2.5 C5 `claude -p --strict-mcp-config` invariant (consumed read-only).
- v0.4.0 C4 ProgramBench experiment infrastructure (3 task fixtures preserved at `/tmp/c4-pbn-runs/` — session-bound; if absent at re-run time, regenerate per the procedure in `docs/experiments/programbench-v0-docs-only.md` §6).

## §9 — F2 RF gaps to surface during build

- **Multi-commit prompt shape vs LLM stochasticity.** A widened prompt instructing multi-commit may produce single-commit responses some fraction of the time (LLM stochasticity). The test injects a stub returning a controlled multi-commit response; the production path's reliability is verified via the ProgramBench re-run AC.V041.4. If re-run shows multi-commit reliably emits in production, GREEN; if intermittent, RF-surface for v0.4.2 follow-on.
- **From-scratch heuristic vs explicit flag.** Auto-detection on "empty source dir" risks false positives when the user has docs-only intent in an existing repo (e.g., adding a new utility script). The fix: explicit `--from-scratch` flag wins; auto-detect only when truly zero source files matching the gap domain. Builder rules on the exact heuristic.
- **Tie-breaker choice.** Multiple candidate heuristics (gap-confidence, cluster-size, dependency-chain depth, user-pin). Picking ONE introduces a method-decision; documented in §14. Surface for owner ruling if the choice has non-obvious second-order effects.
- **Cost band variance on ProgramBench re-run.** v0.4.0 C4 was $0.42 total; v0.4.1 may run higher if multi-commit prompts are longer or if from-scratch mode adds preamble. Halt-trigger 9 is the upper bound.
- **HARD smoke time.** rd-automation Stage 1 is ~230s based on v0.4.0 baseline. v0.4.1 should not regress this; if it does, surface as a perf-regression for v0.4.2.

## §10 — F4 self-check (scope-confidence)

The 3 sub-fixes are NAMED in C4's recommendations §5 + the v0.4.1 dispatch directive — high author confidence in the outcome shape. Scope is TIGHT (objective + constraints + AC.V041.{1,2,3} pin the outcome; method stays builder's call within fence). AC.V041.4 (re-run) and AC.V041.6 (HARD smoke) are confidence-bearing outcome probes — TIGHT scope at AC level (run real `claude -p` against real fixtures and report numbers); LOOSE on what the numbers will show (we don't know empirically until the run).

Per Lens 4 (compose-with-F4): tight scope leaves method *inferable from constraints*. The constraints in §5 + halt-triggers in §7 + AC text in §4 are sufficient for the builder to infer: from-scratch prompt mode is a branching path inside `_build_prompt`; multi-commit is a parser change in `_parse_llm_response` + a prompt change; tie-breaker is a `_tiebreak_key` extension. Method NOT named in AC text.

## §11 — Dispatch shape

This patch is built **inline in this main session** (not background-dispatched) because:

1. The 3 sub-fixes are tightly scoped and serial.
2. The HARD smoke + ProgramBench re-run need to happen on the same HEAD as the source edits (parallel-tree races would invalidate).
3. v0.4.0 C4's ProgramBench experiment was foreground; v0.4.1 mirrors that pattern.

Build order:

1. **Plan-doc lands** (this file) + manifest stub.
2. **Sub-fix 1 (multi-commit)** — code edit + new test + green.
3. **Sub-fix 2 (from-scratch)** — code edit + new test + green.
4. **Sub-fix 3 (tie-breaker)** — code edit + new test + green.
5. **No-regression check** — full pytest run on `plugins/dev-sdlc/odd-extractor/tests/`.
6. **AC.V041.4 ProgramBench re-run** — real `claude -p`; 3 tasks; report append.
7. **AC.V041.6 HARD smoke** — cold install + rd-automation extract + writeup.
8. **`loam amend apply` + `loam amend seal`** — single seal commit covering all sub-fixes.
9. **HARD HALT** — no push, no tag, no Release.

## §12 — Provenance trail

- `docs/release-roadmap.md` §6 owner-action-line on F-DESIGN-1 closure — root authority.
- v0.4.0 C4 ProgramBench v0 baseline at `docs/experiments/programbench-v0-docs-only.md` §3 + §5 — empirical mechanism + recommendations.
- v0.4.0 C4 build report at `<workspace>/.scratch/claude-output/v0-4-0-cycle-4-build-report.md` §5 — three sub-fixes named.
- v0.4.0 SHIPPED at seal `7787a226` per `docs/release-roadmap.md` §2.
- `feedback_hard_smoke_per_minor_before_publish.md` — HARD smoke procedural rule.
- `feedback_test_outcome_altitude_required.md` — outcome-altitude AC requirement (AC.V041.4 + AC.V041.6).
- `feedback_no_anthropic_api_key.md` — subscription-only architectural floor.
- `framework/objective-tracker/src/loam/objective_tracker/spec.py` — `LiftedFrom` schema (consumed).
- v0.4.0 C1 surface at `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/code_gen.py` (extended).
- v0.2.4 C3 surface at `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/build_next.py` (tie-breaker extended).

## §13 — AI-time band

Per duration-estimation rubric (`wall_clock_minutes ≈ tool_calls × 0.1–0.15`):

- Plan-doc + manifest: 5–10 min (~50 tool calls).
- Sub-fix 1 (multi-commit): 25–50 min (~200–400 tool calls).
- Sub-fix 2 (from-scratch): 20–40 min (~150–300 tool calls).
- Sub-fix 3 (tie-breaker): 15–30 min (~100–200 tool calls).
- No-regression check: 5–10 min.
- AC.V041.4 ProgramBench re-run: 30–60 min (3 tasks; mirrors C4 actual ~25 min for the run portion + ~10 min report append).
- AC.V041.6 HARD smoke: 30–45 min (mirrors v0.4.0 hard-smoke ~230s Stage 1 + writeup).
- Apply + seal + report: 10–20 min.

**Aggregate range: 140–265 min ≈ 2.3–4.4 hr AI-time.** Midpoint ~3.4 hr. Within halt-trigger 7 upper bound (240 min × 1.5 = 360 min).

## §14 — Method decisions (filled at build time)

(Filled inline as the build proceeds; entries appended below.)

- D-V041.1 (multi-commit emit shape) — TBD at sub-fix 1 build time.
- D-V041.2 (from-scratch heuristic) — TBD at sub-fix 2 build time.
- D-V041.3 (tie-breaker primary signal) — TBD at sub-fix 3 build time.
- D-V041.4 (ProgramBench re-run task selection) — same 3 tasks as C4 (calculator, jsonpp, wcclone) per the dispatch directive.
- D-V041.5 (HARD smoke fixture) — rd-automation per `feedback_hard_smoke_per_minor_before_publish.md`.
- D-V041.6 (apply + seal bookkeeping) — `loam amend apply` + `loam amend seal --scoped-sweep` per v0.4.0 C2/C3/C4 precedent.

## §15 — SHA register (filled at seal time)

(Filled at seal time; backfill commit is the standard §11-style SHA log.)

| Order | Type | SHA | Description |
|---|---|---|---|
| 1 | plan-doc | TBD | docs(plans): v0.4.1 patch plan-doc + manifest |
| 2 | source-edit (sub-fix 1) | TBD | feat(code-gen): multi-commit-per-task emission |
| 3 | source-edit (sub-fix 2) | TBD | feat(code-gen): from-scratch prompt mode |
| 4 | source-edit (sub-fix 3) | TBD | feat(build-next): tie-breaker beyond alphabetical |
| 5 | docs (re-run + ship rollups) | TBD | docs: v0.4.1 ProgramBench re-run + STATE.md SHIPPED + release-roadmap §6 closure |
| 6 | apply | TBD | chore(amend): v0-4-1-patch-f-design-1-closure manifest+apply |
| 7 | seal | TBD | chore(seals): v0-4-1-patch-f-design-1-closure |
