# v0.4.2 patch — F-DESIGN-2 closure (Test-interface load-bearing + Py 3.9 syntax)

**Status:** finalized at dispatch time. Plan-before-code per `feedback_plan_before_code` (hard rule).
**Slug:** `v0-4-2-patch-f-design-2-closure`
**Date authored:** 2026-05-09.
**Parent authority:** `docs/release-roadmap.md` §6 owner-action-line entry on F-DESIGN-2 closure (NEW row added by v0.4.1 patch); v0.4.1 SHIPPED LOCAL at seal `7b8e22e0` per §2.
**Predecessor:** v0.4.1 seal `7b8e22e0` (HEAD at dispatch).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Owner authorization:** Telegram 10465 ("Continue with 0.4.2 before pushing 0.4.1.").

---

## §1 — Outcome shape (the "why")

v0.4.1 patch closed F-DESIGN-1 (multi-commit + from-scratch + tie-breaker — all working in production). The v0.4.1 ProgramBench re-run confirmed the structural mechanisms work: 3 commits per task, `--- /dev/null` framing across all diffs, tie-breaker correctly picked `formatting` over `error-handling`. BUT the empirical pass-rate gain was bounded by F-DESIGN-2 (per `docs/experiments/programbench-v0-docs-only.md` "v0.4.1 RF surfaces" section):

1. **The from-scratch prompt doesn't pass the SPEC's "Test interface" section as load-bearing context.** The LLM is instructed to "create new files" but doesn't see what shape the test harness expects (subprocess form, output format, named artefacts like `compile.sh`). It makes reasonable but spec-incompatible choices: library shape vs CLI; multi-line vs single-line output; Makefile install vs `compile.sh`.
2. **wcclone regression (6/6 → 0/6) on Py 3.9 type-hint syntax.** v0.4.1's wcclone diff used `str | Path` (PEP-604 union, Py 3.10+); the eval harness ran on Py 3.9. Plus library-shape-vs-CLI mismatch.

v0.4.2 is a PATCH-class release per `docs/release-versioning-policy.md` — defect closure within v0.4.1's outcome shape. **It does not extend v0.4.1's outcome shape**; it makes the v0.4.1 from-scratch surface produce SPEC-compatible output by passing the SPEC content (including Test interface) as load-bearing prompt context AND handling Py-version compatibility.

## §2 — Prime objective ladder

VALUE_PROPOSITION.md prime objective (loam helps people use LLMs to build software) → v0.4.0 release-roadmap §3 outcome (loam ships working code from extracted objectives) → F-DESIGN-2 closure (cold-start docs-only multi-file code-gen produces SPEC-compatible artefacts) → v0.4.2 ACs `AC.V042.*` below (3 sub-fixes + ProgramBench re-run + no-regression + HARD smoke).

## §3 — Component fence

**PRIMARY:** `plugins/dev-sdlc/odd-extractor/` — same component v0.4.0 + v0.4.1 extended. No new component, no new package. Edits land in:

- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/code_gen.py` — Test-interface section as load-bearing context in from-scratch prompt + Py-version compatibility instruction.
- `plugins/dev-sdlc/odd-extractor/tests/test_AC_V042_*.py` — new tests covering the sub-fixes + no-regression.

**Read-only:**
- `framework/objective-tracker/src/loam/objective_tracker/spec.py` — `LiftedFrom` schema (consumed; sealed in amendment #38).
- All other framework components — sealed.
- v0.4.1 surface (multi-commit parser + from-scratch detect helpers + tie-breaker) — extended via NEW commits; existing tests must continue to pass without edit.

**Universal admissions:** `docs/plans/v0-4-2-patch-f-design-2-closure.md` (this file), `docs/plans/v0-4-2-patch-f-design-2-closure.manifest.yaml`, seal narrative file, `docs/release-roadmap.md` §6 (mark closure of F-DESIGN-2 owner-action-line on completion + add v0.4.2 §2 row), `docs/STATE.md` (v0.4.2 SHIPPED rollup row), and `docs/experiments/programbench-v0-docs-only.md` (append v0.4.2 re-run section per AC.V042.{3,4,5}).

**Out of fence:** `framework/`, `plugins/dev-sdlc/seals/`, any other plugin tree, sealed objective-tracker schema. Edits outside fence = halt.

## §4 — AC family `AC.V042.*` (TIGHT)

Each AC maps to ≥1 test under `plugins/dev-sdlc/odd-extractor/tests/test_AC_V042_*.py` OR an empirical artefact (the ProgramBench re-run report, the HARD smoke writeup). The agent authors test names within the convention.

### AC.V042.1 — From-scratch prompt template includes Test-interface section

When a docs-only repo contains a SPEC document with a "Test interface" section (or equivalent named section), the from-scratch prompt MUST include the SPEC content (or specifically the Test interface section + named-artefact references like `compile.sh`) as load-bearing context. The LLM MUST be instructed explicitly to author whatever shim/executable/script the test interface requires (e.g., `compile.sh`, `run.sh`, CLI binary, `executable`) as a first-class commit.

The widening path:

- The from-scratch prompt branch in `_build_prompt` reads the SPEC content from `repo_path` (when supplied) and embeds the relevant section(s) into the user-prompt body under a dedicated header (e.g., `Test interface from SPEC:`). Builder rules on the exact extraction strategy (full SPEC body, or just a "Test interface" section regex, or full docs-tree concat) per §14 D-V042.1.
- The system prompt is widened to instruct: "If the SPEC names a build script (e.g., `compile.sh`) or a named output artefact (e.g., `executable`), you MUST author that artefact as a first-class commit. The test harness invokes the program via the SPEC's Test interface — match it exactly (subprocess form, output format, trailing newlines)."

**Test:** A new `test_AC_V042_1_test_interface_in_prompt.py` invokes `generate_code` with `from_scratch=True` against a fixture whose SPEC.md contains a "Test interface" section (e.g., a `wcclone`-style SPEC). Asserts the captured user-prompt contains the SPEC's Test interface text (literal substring match on a load-bearing snippet like the `subprocess.run([...])` line). Asserts the system prompt instructs `compile.sh` / executable authoring.

`outcome-altitude: false` (prompt-shape verification; method-altitude). Verified via stub-injected LLM client.

### AC.V042.2 — Py-version compatibility handled

The from-scratch prompt MUST handle Py-version compatibility for Python tasks. Builder picks ONE path (documented in §14 D-V042.2):

- (a) **Detect Python from SPEC** — if the SPEC names Python (or no language is specified and Python is plausible via the repo / build constraints), instruct the LLM to author Python-3.9-compatible syntax (no PEP-604 unions like `str | Path`; no `match`/`case` statements; no `:=` walrus in non-3.8+ ways; `from typing import Union, Optional` instead).
- OR (b) **Post-process emitted code** — walk the emitted commits' diff bodies, lower Py-3.10+ constructs to Py-3.9-compatible (regex-based: `X | Y` → `Union[X, Y]`; `match X:` → if/elif chains).

**Test:** A new `test_AC_V042_2_py_version_compat.py` invokes `generate_code` with `from_scratch=True` against a Python-task SPEC fixture. If path (a): asserts the user-prompt contains a Py-3.9-compat instruction (e.g., "Python 3.9-compatible syntax" or "no PEP-604 unions"). If path (b): asserts that a stub LLM response with `str | Path` gets lowered to `Union[str, Path]` (or equivalent) in the persisted diff. Builder rules; the test follows the chosen path.

`outcome-altitude: false` (prompt-shape OR post-processor; method-altitude).

### AC.V042.3 — wcclone regression recovery

Re-run the wcclone ProgramBench task under v0.4.2 HEAD. Pass rate ≥4/6 (recovery from 0/6 in v0.4.1). Goal: restore the structural mechanism that worked in C4 (6/6) by ensuring the LLM authors `compile.sh` + a CLI shape matching the SPEC's Test interface.

**Procedure:** run the full 5-stage pipeline (extract → interview → gaps → build-next → code-gen) on the wcclone fixture under v0.4.2 HEAD; eval via existing `/tmp/v041-pbn-runs/eval-task.sh` infrastructure; record per-task pass rate. Compare to v0.4.1 0/6.

**Verdict shape:** GREEN if ≥5/6; YELLOW if 4/6 (the AC threshold, structurally-acceptable recovery); RED if ≤3/6 (fix didn't move the needle — F-DESIGN-3 surface OR v0.5.0 reframe).

`outcome-altitude: true` — real `claude -p` subprocess, real fixture, real test pass rate. Per `feedback_test_outcome_altitude_required.md`.

### AC.V042.4 — No regression on calculator + jsonpp

Re-run the calculator + jsonpp ProgramBench tasks under v0.4.2 HEAD. Pass rates MUST hold at v0.4.1 levels (calculator 3/3, jsonpp 7/7) — RELAXED counts acceptable per the eval harness.

**Verdict shape:** GREEN if both at v0.4.1 levels (calculator 3/3, jsonpp 7/7). YELLOW if either at -1 (e.g., 2/3 or 6/7 — surface for owner ruling). RED if either drops by ≥2 (regression — halt).

`outcome-altitude: true` — same probe shape as AC.V042.3.

### AC.V042.5 — Aggregate ProgramBench v0 ≥75%

Aggregate pass-rate across all 3 tasks (calculator + jsonpp + wcclone): **≥75%** (≥12/16) — meaningful step-up from v0.4.1's 62.5% (10/16).

**Verdict shape:** GREEN if ≥12/16 (75%); YELLOW if 11/16 (68.75%, partial); RED if <11/16 (no meaningful step-up).

`outcome-altitude: true`.

### AC.V042.6 — No regression on test suite

All previously-passing tests still pass. Specifically:

- `pytest plugins/dev-sdlc/odd-extractor/tests/` returns 0 with the v0.4.1-sealed test count plus the new `AC_V042_*` tests (verify pre-existing tests untouched via `git diff --stat`).
- `loam amend apply --dry-run` GREEN against the v0.4.2 manifest pre-apply AND post-seal.
- v0.4.0 + v0.4.1 outcome-altitude AC outputs (v0.4.0 C2 jsts-playwright-app, v0.4.1 HARD smoke) NOT re-run inline — the inherited sealed state is the baseline.

`outcome-altitude: false` (no-regression invariant; covered by the test suite).

### AC.V042.7 (outcome-altitude) — HARD smoke against rd-automation

Per `feedback_hard_smoke_per_minor_before_publish.md`: every minor's release sequence has a HARD smoke gate against rd-automation. Even though v0.4.2 is a patch, the same rule applies because public-action gating happens at the v0.4.2 publish line. Cold install of v0.4.2 HEAD into a fresh venv; real `claude -p` subprocess; real rd-automation tree at `/Users/lukeivers/pos3/workspace/rd-automation`; end-to-end extract + verify objectives.yaml + key fields; regression ride-along on F-LEAK / F-TIMEOUT / F-VERIFY-ORPHAN closures from v0.2.5.1.

**Verdict:** GREEN before publish. RED triggers corrective + re-smoke.

**Output:** writeup at `<workspace>/.scratch/claude-output/v0-4-2-hard-smoke.md` per the v0.3.0 / v0.4.0 / v0.4.1 precedent.

`outcome-altitude: true` per the rubric — cold install + real `claude -p` + real fixture, no monkeypatch.

### AC.V042.S — Seal-diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` shows changes only under:

- `plugins/dev-sdlc/odd-extractor/` (source + tests + fixtures).
- `docs/plans/v0-4-2-patch-*` (this plan + manifest + seal narrative).
- `docs/experiments/programbench-v0-docs-only.md` (re-run append).
- `docs/release-roadmap.md` (§6 owner-action-line entry closed; §2 SHIPPED row appended).
- `docs/STATE.md` (v0.4.2 SHIPPED rollup row).

Anything outside that set is a halt condition.

## §5 — Hard constraints

1. **No `--amend`.** Corrective commits are NEW commits. Streak intact (every cycle since v0.3.0 C5 stayed clean).
2. **Scope fence per §3.** Edits outside fence = halt.
3. **No Anthropic API key, no `pip install anthropic`.** All LLM calls route through `claude -p` subprocess via `claude_print_synthesis_client.py`. No new SDK dependency.
4. **`--strict-mcp-config` invariant.** Every production-path `claude -p` invocation passes `--strict-mcp-config` + empty MCP config tempfile per the v0.2.5 C5 propagation invariant.
5. **No new runtime deps.** Pydantic + pyyaml + the existing odd-extractor dep set already pinned.
6. **`loam amend apply --dry-run` green** is a hard prereq + hard post-apply gate.
7. **No public action.** No `git push`, no `git tag`, no GitHub Release. v0.4.2 HALTS at seal; owner gates the publish (v0.4.1 + v0.4.2 ship together when owner says go).
8. **Reuse v0.4.1 from-scratch helpers by import.** No re-authoring of `_detect_from_scratch` / multi-commit parser / tie-breaker.
9. **Plan-before-code.** This plan-doc lands BEFORE source edits.
10. **ODD §2.5 + §2.4.** Every line of code maps to a named AC. No method-in-AC. No "options to rule on" framing.
11. **Outcome-altitude AC requirement** per `feedback_test_outcome_altitude_required.md`. AC.V042.{3,4,5,7} are the outcome-altitude probes (real `claude -p` runs).

## §6 — Out of scope (explicit)

- Variant B (docs+binary feeder) — v0.5.0 territory.
- ProgramBench leaderboard submission — v0.5.0 AC.V050.4.
- linux/amd64 + Docker testbed for full ProgramBench eval — v0.5.0+.
- Schema widening on `objective-tracker` — sealed in amendment #38.
- New CLI verb — out; reuse `--code-gen`.
- Multi-fixture HARD smoke beyond rd-automation — v0.5.0+.
- BYOK / multi-provider — subscription-only architectural floor preserved.
- jsts-playwright-app outcome-altitude re-run inline — covered by v0.4.0 C2 sealed state + AC.V042.6 no-regression.
- Move ProgramBench fixtures into the repo — out (still session-bound at `/tmp/v042-pbn-runs/`).

## §7 — Halt triggers

1. Cross-component scope expansion beyond `plugins/dev-sdlc/odd-extractor/`. Halt + surface.
2. AC.V042.* count grows beyond 7 (excluding `.S`). ODD §2.5 violation triage; halt.
3. AC.V042.3 wcclone re-run STILL 0/6 (no recovery). Halt; surface as F-DESIGN-3 candidate for v0.4.3 OR v0.5.0 reframe per the dispatch directive.
4. AC.V042.5 aggregate <60% (regression on calculator or jsonpp). Halt; surface.
5. AC.V042.7 HARD smoke RED. Halt; corrective NEW commit + re-smoke.
6. Any reach for `--amend`, `git push`, or `git tag`. Immediate halt.
7. Subscription-only constraint violated (any new `import anthropic`, any new `ANTHROPIC_API_KEY` env reference). Immediate halt.
8. AI-time exceeds upper band (240 min) by >50% → 360 min wall-clock. Halt with current state.
9. ODD §2.5 violation discovered in surrounding code. Halt + surface.
10. Cost runaway >$5 on the ProgramBench re-run. Halt; reduce task count or model.
11. WD mismatch — `pwd` returns anything other than `/Users/lukeivers/ivers-corp-pos-v2`. Immediate halt.

## §8 — Dependencies

- v0.4.1 SHIPPED LOCAL state (seal `7b8e22e0`) — predecessor; consumed read-only.
- v0.4.0 SHIPPED state (seal `7787a226`) — consumed read-only.
- Amendment #38 `LiftedFrom` schema (sealed; consumed read-only).
- v0.2.5 C5 `claude -p --strict-mcp-config` invariant (consumed read-only).
- v0.4.1 ProgramBench experiment infrastructure (3 task fixtures preserved at `/tmp/v041-pbn-runs/` — session-bound; if absent at re-run time, regenerate per the procedure in `docs/experiments/programbench-v0-docs-only.md` §6).

## §9 — F2 RF gaps to surface during build

- **SPEC content extraction strategy.** A regex match on "## Test interface" header risks false-negatives if the SPEC uses a different heading (e.g., "## Tests" or "## Behavior"). Builder rules on the strategy in §14 D-V042.1; full-SPEC pass-through is the safe default; section-extraction is the optimization. Surface tradeoff if path (a) pins a specific header.
- **Py-version compat: instruction vs post-process.** Path (a) instruction is simpler but LLM-stochastic; path (b) post-process is deterministic but adds a regex dependency that may miss edge cases. Builder rules on the choice; surface for owner ruling if the path has non-obvious second-order effects.
- **wcclone-specific recovery vs general fix.** A fix that only recovers wcclone (e.g., hard-coded `compile.sh` instruction) is a band-aid; a general fix passes the SPEC's Test interface section as context. The AC text mandates the general fix (AC.V042.1); RF if the implementation drifts toward wcclone-specific.
- **Cost band variance on ProgramBench re-run.** v0.4.1 was ~$0.40 total; v0.4.2 prompts will be longer (SPEC content embedded); may run higher. Halt-trigger 10 is the upper bound.
- **HARD smoke time.** rd-automation Stage 1 is ~267s based on v0.4.1 baseline. v0.4.2 should not regress this; if it does, surface as a perf-regression for v0.4.3.

## §10 — F4 self-check (scope-confidence)

The 3 sub-fixes are NAMED in the v0.4.2 dispatch directive + v0.4.1 build report's F-DESIGN-2 surface — high author confidence in the outcome shape. Scope is TIGHT (objective + constraints + AC.V042.{1,2,3,4,5} pin the outcome; method stays builder's call within fence). AC.V042.{3,4,5,7} are confidence-bearing outcome probes — TIGHT scope at AC level (run real `claude -p` against real fixtures and report numbers); LOOSE on what the numbers will show empirically.

Per Lens 4 (compose-with-F4): tight scope leaves method *inferable from constraints*. The constraints in §5 + halt-triggers in §7 + AC text in §4 are sufficient for the builder to infer: the from-scratch prompt change is a `_build_prompt` extension that reads `repo_path` for SPEC content; the Py-version compat fix is either a prompt instruction OR a post-processor (builder choice in §14). Method NOT named in AC text.

## §11 — Dispatch shape

This patch is built **inline in this main session** (not background-dispatched) because:

1. The 2 sub-fixes are tightly scoped and serial.
2. The HARD smoke + ProgramBench re-run need to happen on the same HEAD as the source edits (parallel-tree races would invalidate).
3. v0.4.0 C4 + v0.4.1 ProgramBench experiments were foreground; v0.4.2 mirrors that pattern.

Build order:

1. **Plan-doc lands** (this file) + manifest stub.
2. **Sub-fix 1 (Test-interface in prompt)** — code edit + new test + green.
3. **Sub-fix 2 (Py-version compat)** — code edit + new test + green.
4. **No-regression check** — full pytest run on `plugins/dev-sdlc/odd-extractor/tests/`.
5. **AC.V042.{3,4,5} ProgramBench re-run** — real `claude -p`; 3 tasks; report append.
6. **AC.V042.7 HARD smoke** — cold install + rd-automation extract + writeup.
7. **`loam amend apply` + `loam amend seal`** — single seal commit covering all sub-fixes.
8. **HARD HALT** — no push, no tag, no Release.

## §12 — Provenance trail

- `docs/release-roadmap.md` §6 owner-action-line on F-DESIGN-2 closure — root authority.
- v0.4.1 ProgramBench v0 re-run at `docs/experiments/programbench-v0-docs-only.md` "v0.4.1 re-run" + "v0.4.1 RF surfaces" — empirical mechanism.
- v0.4.1 patch build report at `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-4-1-patch-build-report.md` — three sub-fixes named.
- v0.4.1 SHIPPED LOCAL at seal `7b8e22e0` per `docs/release-roadmap.md` §2.
- `feedback_hard_smoke_per_minor_before_publish.md` — HARD smoke procedural rule.
- `feedback_test_outcome_altitude_required.md` — outcome-altitude AC requirement.
- `feedback_no_anthropic_api_key.md` — subscription-only architectural floor.
- v0.4.1 surface at `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/code_gen.py` (extended).

## §13 — AI-time band

Per duration-estimation rubric (`wall_clock_minutes ≈ tool_calls × 0.1–0.15`):

- Plan-doc + manifest: 5–10 min.
- Sub-fix 1 (Test-interface in prompt): 25–45 min.
- Sub-fix 2 (Py-version compat): 15–30 min.
- No-regression check: 5–10 min.
- AC.V042.{3,4,5} ProgramBench re-run: 30–60 min (3 tasks; mirrors v0.4.1 actual).
- AC.V042.7 HARD smoke: 30–45 min (mirrors v0.4.1 ~267s Stage 1 + writeup).
- Apply + seal + report: 10–20 min.

**Aggregate range: 120–220 min ≈ 2.0–3.7 hr AI-time.** Midpoint ~2.8 hr. Within halt-trigger 8 upper bound (240 min × 1.5 = 360 min).

## §14 — Method decisions (filled at build time)

(Filled inline as the build proceeds; entries appended below.)

- D-V042.1 (Test-interface extraction strategy) — TBD at sub-fix 1 build time.
- D-V042.2 (Py-version compat path: instruction vs post-process) — TBD at sub-fix 2 build time.
- D-V042.3 (ProgramBench re-run task selection) — same 3 tasks as v0.4.1 (calculator, jsonpp, wcclone) per the dispatch directive.
- D-V042.4 (HARD smoke fixture) — rd-automation per `feedback_hard_smoke_per_minor_before_publish.md`.
- D-V042.5 (apply + seal bookkeeping) — `loam amend apply` + `loam amend seal --scoped-sweep` per v0.4.0 / v0.4.1 precedent.

## §15 — SHA register (filled at seal time)

(Filled at seal time; backfill commit is the standard §11-style SHA log.)

| Order | Type | SHA | Description |
|---|---|---|---|
| 1 | plan-doc | TBD | docs(plans): v0.4.2 patch plan-doc + manifest |
| 2 | source-edit (sub-fix 1) | TBD | feat(code-gen): Test-interface section as load-bearing context in from-scratch prompt |
| 3 | source-edit (sub-fix 2) | TBD | feat(code-gen): Py-version compatibility instruction/post-process |
| 4 | docs (re-run + ship rollups) | TBD | docs: v0.4.2 ProgramBench re-run + STATE.md SHIPPED + release-roadmap §6 closure |
| 5 | apply | TBD | chore(amend): v0-4-2-patch-f-design-2-closure manifest+apply |
| 6 | seal | TBD | chore(seals): v0-4-2-patch-f-design-2-closure |
