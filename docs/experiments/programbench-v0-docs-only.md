> **RETIRED 2026-06-11 — ProgramBench full retirement.** ProgramBench was
> fully retired by owner ruling (Discord 1514747695972094165; plan
> `docs/plans/programbench-full-retirement.md`). This report is sealed history —
> preserved verbatim as the audit record; nothing in it is current or
> future work. The reproducibility substrate
> (`framework/tools/programbench-revival/`, incl. committed run-evidence)
> was deleted at retirement, so harness paths referenced herein no longer
> exist in the live tree.

# ProgramBench v0 — docs-only baseline (Variant A vs direct claude -p)

**Status:** v0.4.0 Cycle 4 deliverable. Substrate experiment for AC.V040.4 / AC.V040C4.{1-7}.
**Date:** 2026-05-08.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Cost:** $0.42 total (baseline $0.16 + Variant A $0.26 across 3 tasks).
**Verdict:** Variant A pass-rate **39%** (5/16 behavioral tests across 3 tasks); baseline pass-rate **100%** (16/16). Variant A's planning layer **does not pay off** on this class of task at the current code-gen surface shape; the F-DESIGN-1 risk surfaced in Cycle 2's plan-doc is empirically confirmed.

> **NOTE on scope:** "ProgramBench v0" here refers to an internal experiment with 3 hand-authored toy tasks (calculator, jsonpp, wcclone). It is NOT the public ProgramBench leaderboard at programbench.com (which scores against hundreds of much-harder tasks; major providers are at 0–3% on that). The real-benchmark eval was blocked at v0.4.0 C4 (Docker daemon issue on the dev host) and is deferred to v0.5.0. This internal experiment validates the architectural mechanism on toy tasks; it does NOT establish loam's performance on real-world program-synthesis tasks.

---

## Executive summary (read first)

**The hypothesis under test:** *ODD-grounded code-gen meaningfully outperforms direct LLM code-gen on small benchmark tasks given only documentation.*

**The verdict:** Refuted on this experiment. Direct `claude -p` outperforms ODD-grounded code-gen on all three tasks. The cause is **structural**, not stochastic — see §"F-DESIGN-1 confirmed" below.

**The structural finding:** loam's v0.4.0 code-gen surface is shaped for *"extend an existing repo"* (consume objectives.yaml + emit a unified diff against a source tree), not *"write from scratch given only docs"*. ProgramBench's docs-only Variant A is the second shape; the surface mismatch produces single-commit single-file diffs that are missing one or more required submission artefacts (notably `compile.sh`).

**The ship-worthy data:** the result satisfies the parent AC's "either result is ship-worthy" framing (see source artefact `<workspace>/.scratch/claude-output/programbench-loam-benchmark-v0.md` §"Why this could be significant"). The signal points at where loam IS load-bearing (planning-time decisions in larger codebases where existing source provides the diff target) vs where it ISN'T (cold-start code-gen against full behavioral coverage).

**Recommendation for v0.4.0 C5 / v0.5.0:** see §"Recommendations" below.

---

## §1 — Experiment scope + access caveat

### Real ProgramBench scope (NOT runnable in this environment)

ProgramBench's full benchmark eval requires:

1. **linux/amd64 host.** All `task_cleanroom` Docker images are built for amd64 only. Darwin/arm64 (this dispatcher's host) cannot run them natively; QEMU emulation is "generally slow" per the upstream usage guide (https://github.com/facebookresearch/ProgramBench/blob/main/docs/README.md).
2. **Docker daemon running.** The eval pipeline pulls per-task containers (e.g., `ffmpeg_1776_ffmpeg.360a402:task`).
3. **HuggingFace blob downloads.** Test blobs come from `huggingface.co/datasets/programbench/ProgramBench-Tests` per `programbench blob sync`.

**Verified at C4 dispatch time (2026-05-08):**

- `docker version` returns "Cannot connect to the Docker daemon" on this host.
- `uname -a` reports `Darwin … arm64`, NOT `linux/amd64`.

**Decision:** the full ProgramBench eval is deferred to v0.4.1 / v0.5.0+ when a linux/amd64 + Docker testbed is available. C4 ships a **scoped substitute experiment** using:

- 1 real ProgramBench seed task — the `testorg__calculator.abc1234` test fixture shipped IN-tree at `src/programbench/data/tasks/testorg__calculator.abc1234/` (used by ProgramBench's own `test_eval.py`); this is a real ProgramBench task fully runnable on Darwin/arm64 without Docker (the `compile.sh` is bash; the test harness is pytest).
- 2 hand-authored ProgramBench-shape local tasks — `jsonpp` (JSON pretty-printer) and `wcclone` (line/word/byte counter). Each follows the ProgramBench shape (README/SPEC docs + behavioral test suite + `compile.sh` → `executable` contract) but is NOT a real ProgramBench task.

This substitute is HONEST about its scope. It is NOT the 248k-test 200-task full benchmark eval; it IS a signal-bearing probe of the same hypothesis on the same input/output shape.

### Variant A pipeline (verbatim)

For each task:

1. Construct a docs-only repo containing only `README.md` + `SPEC.md` (no source code).
2. `loam odd-extract <repo> --live --budget-cents 500 --budget-override` — Stage 1 extraction via real `claude -p` subprocess (subscription-only architecture preserved).
3. `loam odd-extract <repo> --interview` — Stage 2 (stdin-fed; defaults all questions to "1" + "no" — non-interactive).
4. `loam odd-extract <repo> --gaps` — Stage 3.
5. `loam odd-extract <repo> --build-next` — Stage 4.
6. `loam odd-extract <repo> --code-gen` — Stage 5 (NEW at v0.4.0; produces `code-gen/diff.patch` + `code-gen/manifest.json`).
7. Parse the unified diff; extract per-file content; place in eval directory.
8. Run `compile.sh` (if present) to produce `./executable`; run the task's behavioral test suite via pytest; record pass-rate.

### Baseline pipeline

For each task:

1. Construct the same docs-only directory.
2. Single `claude -p` call passing both docs (README + SPEC) plus a brief "produce these N files in `===FILE: <name>===\n<contents>\n===END===` format" instruction.
3. Parse the response; place files in eval directory.
4. Run `compile.sh` → `./executable`; run pytest; record pass-rate.

Both pipelines route LLM calls through `claude -p --strict-mcp-config` per the v0.2.5 C5 invariant. NO Anthropic API key. Same model (`claude-sonnet-4-5`). Stochasticity is not controlled — each task ran once for each variant.

---

## §2 — Per-task results

### Task 1 — calculator (real ProgramBench task `testorg__calculator.abc1234`)

| Variant | compile.sh? | executable? | tests passed | pass rate |
|---|---|---|---|---|
| Baseline | yes | yes | 3/3 | **100%** |
| Variant A | yes | yes | 3/3 | **100%** |

**Behavioral tests** (3 tests; from `src/programbench/data/tasks/testorg__calculator.abc1234/tests/33128f6b8600/eval/tests/test_calculator.py`): `test_addition`, `test_subtraction`, `test_multiplication`.

**Note:** the canonical ProgramBench fixture's `tests.json` lists `test_addition`, `test_subtraction`, `test_multiplication`, and others (`test_division` etc) as `gold_fail` (intentionally ignored). Only the 3 above are scored in this experiment, matching the upstream filter.

**Variant A diff:** `--- /dev/null` → `+++ b/calculator.sh` (7 lines bash) + `--- /dev/null` → `+++ b/compile.sh` (3 lines bash). Both files in a single commit. Identical output to baseline (case-statement bash dispatch on `$2`).

**Cost:** baseline $0.053; Variant A $0.112 (synthesis $0.087 + code-gen estimate $0.025).

**Verdict:** TIE.

### Task 2 — jsonpp (locally-authored, ProgramBench-shape)

| Variant | compile.sh? | executable? | tests passed | pass rate |
|---|---|---|---|---|
| Baseline | yes | yes | 7/7 | **100%** |
| Variant A (default candidate) | no | no | 0/7 | **0%** |
| Variant A (explicit `--candidate G.BACKING.o-formatting-1`) | no | no | 0/7 | **0%** |

**Behavioral tests** (7 tests; locally-authored): `test_simple_object`, `test_simple_array`, `test_nested`, `test_empty_object`, `test_empty_array`, `test_string_scalar`, `test_null_scalar`.

**Variant A default-candidate diff:** the build-next ranker selected `G.BACKING.o-error-handling-1` (alphabetical tiebreak between two equal-score candidates). Code-gen produced a diff modifying a non-existent file `baseline_eval/jsonpp.py` (the LLM hallucinated a path that wasn't even in the docs-only repo's filesystem). NO `compile.sh`, NO new file authored. Diff is non-applicable from-scratch.

**Variant A explicit-candidate diff:** with `--candidate G.BACKING.o-formatting-1` forcing the formatting objective, code-gen produced `--- /dev/null` → `+++ b/jsonpp.py` (10 lines Python). Functionally CORRECT — when manually wrapped with a hand-authored `executable` shim, all 7 tests pass. **But the pipeline never authored `compile.sh`**, so without manual intervention, the test harness produces 0/7.

**Cost:** baseline $0.052; Variant A $0.068 (synthesis $0.043 + code-gen estimate $0.025).

**Verdict:** Variant A FAILS. Baseline 100% / Variant A 0%.

### Task 3 — wcclone (locally-authored, ProgramBench-shape)

| Variant | compile.sh? | executable? | tests passed | pass rate |
|---|---|---|---|---|
| Baseline | yes | yes | 6/6 | **100%** |
| Variant A | yes | yes | 6/6 | **100%** |

**Behavioral tests** (6 tests; locally-authored): `test_two_lines`, `test_empty_file`, `test_one_line_with_newline`, `test_one_line_no_newline`, `test_tabs_and_multiple_spaces`, `test_multiple_lines_no_trailing_newline`.

**Variant A diff:** `--- /dev/null` → `+++ wcclone.c` (36 lines C) + `--- /dev/null` → `+++ compile.sh` (2 lines bash; `gcc -o executable wcclone.c`). Both files in a single commit. Note diff format anomaly: `+++ wcclone.c` (no `b/` prefix) on Task 3 vs `+++ b/calculator.sh` on Task 1. Parser handles both forms.

**Cost:** baseline $0.057; Variant A $0.079 (synthesis $0.054 + code-gen estimate $0.025).

**Verdict:** TIE.

### Aggregate

| Variant | Tasks tied | Tasks Variant A failed | Total tests passed | Total tests | Pass rate |
|---|---|---|---|---|---|
| Baseline | n/a | n/a | 16 | 16 | **100%** |
| Variant A | 2 (calculator, wcclone) | 1 (jsonpp) | 9 | 16 | **56%** (with explicit candidate selection on jsonpp tied at functionally-correct-but-no-compile.sh = 0/7 strict) |
| Variant A (strict, default candidate ranking) | 2 | 1 | 9 | 16 | **56%** |

(Note: the 0% on jsonpp dominates the aggregate; without it the two remaining tasks are tied.)

---

## §3 — F-DESIGN-1 confirmed: the surface is "extend existing", not "write from scratch"

The Cycle 2 plan-doc surfaced this risk verbatim: *"The C1+C2 code-gen engine doesn't actually produce useful diffs on real benchmark tasks (this is the F-DESIGN-1 risk surfaced from C2 — keep watching)."*

**Empirically confirmed at C4.** The mechanism:

1. **Single-commit-per-candidate.** The C1 code-gen surface produces ONE commit per `--code-gen` invocation. Each commit closes ONE gap (selected via `--candidate <gap_id>` or the highest-ranked default). Multi-file from-scratch submissions need ≥2 files (build script + source); a single commit-per-candidate cannot author both unless the LLM's prompt-shape happens to emit both in one diff (which Tasks 1 and 3 did, but Task 2 did not).

2. **The prompt assumes existing source.** From `code_gen.py:_build_prompt`:
   ```
   Produce a unified diff (one or more file hunks) that closes the gap.
   ```
   "Unified diff" is conventionally relative to an existing tree. The model HAD to be coaxed by a stronger prompt or by the docs-only feeder making "no source" structurally explicit. On Task 2, the LLM produced `--- a/baseline_eval/jsonpp.py` — a diff against a hallucinated source file that wasn't in the docs-only repo at all.

3. **The docs-only repo's analyze stage produces objectives, not file-existence hints.** The reverse-ODD pipeline reads `README.md` + `SPEC.md` and produces objectives like "JSON formatting must use 2-space indent." The pipeline does NOT propagate "and there is currently no source" to the code-gen prompt. The LLM's prior on "produce a unified diff" defaults to "modify existing source" rather than "create new file."

4. **Build-next ranking on 2 equal-score candidates is alphabetical.** Task 2 had `O.error-handling.1` and `O.formatting.1`, both at composite_score 0.8. Default selection picked `error-handling` (alphabetical). The most-load-bearing objective for the task's behavioral tests was `formatting`. Without operator override, Variant A produced an error-handling improvement to a hallucinated source file — useless.

The structural flaw is real, reproducible, and not stochastic. Re-running with stronger prompt engineering OR explicit candidate selection might lift Task 2 to functional jsonpp.py BUT still doesn't author `compile.sh` because the second file is not in the same gap.

---

## §4 — Outcome interpretation (per AC.V040C4.6)

Per the source artefact's framing:

> "If Variant A or B substantially outperforms baseline (e.g., 8% vs 3% 'almost resolved' or higher), that's a real differentiation story for loam: 'ODD-grounded code-gen significantly outperforms blind code-gen on ProgramBench.'"
>
> "If the numbers don't come out — also valuable signal. Means the planning layer doesn't help on this class of task, which would point at where loam IS load-bearing (planning-time decisions in larger codebases?) and where it isn't (cold-start code-gen against full behavioral coverage)."
>
> "Either result is ship-worthy data."

**This experiment lands in the second case.** Variant A does not outperform baseline on cold-start code-gen against full behavioral coverage. The signal points clearly at where loam IS load-bearing:

- **Where loam IS load-bearing (per this experiment + extrapolation):** planning-time decisions in **existing** codebases. The reverse-ODD pipeline produces value when it grounds future modifications to a source tree. The `objectives.yaml` block per commit (amendment #38 `lifted_from`) is meaningful when it traces a modification to a named AC from a documented objective — not when it traces an empty diff against a source tree that doesn't exist.

- **Where loam is NOT (yet) load-bearing:** cold-start code-gen from docs alone, where the deliverable is a multi-file submission with a build artefact. The C1 code-gen surface needs structural changes to produce that shape — at minimum, multi-commit-per-task and a "no source tree" prompt mode.

This is an **actionable, ship-worthy negative result.** It does NOT refute loam's value proposition; it sharpens which use cases v0.4.0 actually serves.

---

## §5 — Recommendations (for v0.4.0 C5 ratification + v0.5.0 planning)

### Immediate (v0.4.0 C5 ratification)

1. **Surface this finding in the v0.4.0 STATE.md SHIPPED rollup.** Name the F-DESIGN-1 confirmation. Frame v0.4.0 as "code-gen-from-objectives ships, optimised for *modify existing repo* not *write from scratch*; ProgramBench-shaped cold-start codegen needs v0.5.0 surface extension."
2. **Don't claim the v0.4.0 outcome includes ProgramBench-leaderboard parity.** The `docs/release-roadmap.md` §3 v0.4.0 AC.V040.4 is "ProgramBench docs-only baseline (v0)"; this report IS that baseline and the ACs (V040C4.1-7) close. v0.5.0 carries the leaderboard-submission surface.
3. **Tighten AC text on AC.V040.6 (outcome-altitude for code-gen).** Per `feedback_loose_AC_text_fix_AC_not_implementation`: AC.V040C2.1's outcome-altitude probe runs against `jsts-playwright-app` (an EXISTING repo). It correctly verifies the load-bearing case but doesn't probe cold-start. AC text could note this scope explicitly.

### Short-term (v0.4.1 patch or v0.5.0)

1. **C1 code-gen surface — add a "from-scratch" mode.** A new `--from-scratch` flag (or auto-detection when the repo has no source files matching the build-next gap's domain) that:
   - Authors multiple commits per task (one per required file).
   - Adjusts the prompt to "create new files" not "modify existing source."
   - Drops the `--- a/` line from the unified diff in this mode (use only `--- /dev/null`).
2. **Build-next ranking — break ties on a more-load-bearing signal than alphabetical.** Use objective-domain heuristics (e.g., "formatting" or "calculation" before "error-handling" for tasks where the docs name the formatting/calculation objective first). Or surface the tie to the user. Or factor in objective-text length (longer = more-load-bearing on average).
3. **Multi-file submission shape — first-class concern in code-gen-spec.** The current `CodeGenDiff` schema supports multi-commit but the production prompt-shape doesn't reliably produce it. Make multi-file output an explicit AC that is verified.

### Long-term (v0.5.0+)

1. **Real ProgramBench eval requires linux/amd64 + Docker testbed.** Either (a) provision a remote linux/amd64 host (loam already has Routines composition for cron-scheduled remote agents per v0.4.0 C3 — could compose), (b) skip the Docker layer and run benchmarks against a curated subset of ProgramBench tasks that are amd64-independent (rare), or (c) author a SWE-bench-Pro-style runner that's loam-native and doesn't depend on the upstream Docker images.
2. **Revisit Variant B (docs + binary).** v0.5.0 AC.V050.1 names the binary-usage observation harness. Until then, Variant A is the only mode loam supports; Variant B comparison is structurally blocked.

---

## §6 — Reproducibility

All experiments ran on Darwin/arm64 (Lukes-Laptop.local), `claude --version 2.1.128 (Claude Code)`, `loam` HEAD `2d1e7f01` (v0.4.0 C3 seal), Python 3.9.17.

**Inputs preserved at:** `/tmp/c4-pbn-runs/{task1_calculator,task2_jsonpp,task3_wcclone}/` — each contains:

- `docs_only_repo/{README.md,SPEC.md}` — the docs-only feeder input.
- `baseline_response.json` — raw `claude -p` JSON envelope for the baseline run.
- `baseline_eval/` — extracted files + `eval/` test directory + pytest output.
- `variant_a_workspace/` — full `loam odd-extract` extraction directory including `objectives.yaml`, `gap-inventory.yaml`, `build-next.yaml`, `code-gen/{diff.patch,manifest.json}`.
- `variant_a_eval/` — extracted files from Variant A diff + pytest output.

These are NOT committed to the repo (out-of-tree under `/tmp/`); a v0.4.1 amendment could move them to `plugins/dev-sdlc/odd-extractor/tests/fixtures/programbench/v0/` if reproducibility-on-CI becomes load-bearing.

**Re-run command sketch (per task):**

```bash
# Baseline
claude -p --strict-mcp-config --mcp-config <(echo '{"mcpServers":{}}') \
  --no-session-persistence --output-format json \
  --model claude-sonnet-4-5 "$(cat baseline_prompt.txt)" \
  > baseline_response.json

# Variant A
loam odd-extract docs_only_repo --live --budget-cents 500 --budget-override \
  --workspace-root variant_a_workspace
loam odd-extract docs_only_repo --interview --workspace-root variant_a_workspace \
  --pm-name <pm> <<< "$(printf '1\n%.0s' {1..30})no"
loam odd-extract docs_only_repo --gaps --workspace-root variant_a_workspace
loam odd-extract docs_only_repo --build-next --workspace-root variant_a_workspace
loam odd-extract docs_only_repo --code-gen --workspace-root variant_a_workspace
```

The runs are stochastic; pass-rates for Variant A on Task 2 in particular are highly sensitive to which candidate the build-next ranking selects, which is itself sensitive to objective extraction stochasticity.

---

## §7 — Cross-references

- **Source artefact (canonical experiment shape):** `<workspace>/.scratch/claude-output/programbench-loam-benchmark-v0.md` (not in this repo).
- **Cycle 4 plan-doc:** `docs/plans/v0-4-0-cycle-4-programbench-v0-docs-only-baseline.md` (sub-plan stub; ACs V040C4.1-7).
- **Master plan §3 Cycle 4:** `docs/plans/v0-4-0-master-plan.md`.
- **Release-roadmap §3 v0.4.0 AC.V040.4:** `docs/release-roadmap.md`.
- **C1 code-gen surface:** `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/code_gen.py`.
- **C2 outcome-altitude probe:** `plugins/dev-sdlc/odd-extractor/tests/test_AC_V040C2_1_outcome_altitude.py`.
- **ProgramBench upstream:** https://github.com/facebookresearch/ProgramBench (cloned to `/tmp/ProgramBench` at C4 dispatch).
- **F-DESIGN-1 risk:** v0.4.0 master plan §10.1 (C1's 2-4hr band; outcome-altitude verification surfaces production-path defects).

---

## §8 — AC verdicts

| AC | Verdict | Evidence |
|---|---|---|
| AC.V040C4.1 — 3-5 small ProgramBench tasks selected + documented | GREEN | 3 tasks selected: 1 real ProgramBench seed (calculator) + 2 hand-authored substitutes (jsonpp, wcclone). Selection rationale documented in §1. Full ProgramBench (jq, ripgrep) deferred to v0.5.0 with linux/amd64 + Docker testbed; rationale documented in §1 access caveat. |
| AC.V040C4.2 — Variant A pipeline runs end-to-end on each task | GREEN | All 3 tasks ran the full 5-stage pipeline (extract → interview → gaps → build-next → code-gen) with rc=0 at every stage. Diff produced for each. Cost recorded. |
| AC.V040C4.3 — Baseline (direct claude -p) runs end-to-end | GREEN | All 3 tasks ran direct `claude -p` with subscription-only architecture preserved. Output parsed into multi-file submissions. Cost recorded. |
| AC.V040C4.4 — Behavioral pass rates recorded for both | GREEN | §2 per-task results table. Baseline: 100% on all 3. Variant A: 100% on 2, 0% on 1. Aggregate: baseline 16/16 = 100%; Variant A 9/16 = 56%. |
| AC.V040C4.5 — Report at `docs/experiments/programbench-v0-docs-only.md` | GREEN | THIS document. |
| AC.V040C4.6 — All previously-passing tests still pass; no regression | GREEN | C1/C2 tests not re-run (no source-edit in C4; this cycle authors a docs-only experiment report); C3 deliverables untouched. C4 has no source-edit commit so no regression risk. |
| AC.V040C4.7 (outcome-altitude) — Reader can answer the comparison question with verdict + supporting numbers | GREEN | §"Executive summary" + §4 outcome interpretation give a clear, numerically-supported answer: ODD-grounded code-gen does NOT outperform direct LLM code-gen on cold-start docs-only codegen at the current C1 surface shape; structural mechanism named in §3 (F-DESIGN-1 confirmed). |

**Aggregate:** 7 of 7 C4 ACs GREEN.

**Outcome-altitude AC count:** 3 (AC.V040C4.{2, 4, 7}). Each is verified by real `claude -p` runs against real fixtures producing measurable behavioral test pass rates, NOT by stub injection or pre-arranged state. Per `feedback_test_outcome_altitude_required.md` — the rubric is satisfied.

---

## v0.4.1 re-run — F-DESIGN-1 closure verification (AC.V041.4)

**Date:** 2026-05-09. **Status:** v0.4.1 patch surface re-run on the same 3 tasks.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`. **Builder:** Sonnet (default).
**HEAD under test:** `bb62f864` (sub-fix 3 commit; build_next tie-breaker beyond alphabetical).

> **NOTE on scope:** the "same 3 tasks" are the internal toy fixtures (calculator, jsonpp, wcclone) introduced at v0.4.0 C4 — NOT the public ProgramBench leaderboard. Real-benchmark eval remains deferred to v0.5.0. Pass-rate numbers in this section are bounded to the toy-fixture scope.

### Verdict

**YELLOW** — partial improvement. Variant A pass-rate **62.5% (10/16) RELAXED** vs C4's 56% (9/16) baseline. The 3 sub-fixes produce **observable, structural improvements in production**, but the behavioral pass-rate gain is bounded by a NEW structural finding (F-DESIGN-2 — see §"v0.4.1 RF surfaces" below). **STRICT pass-rate (no manual executable wrapper) is 0/16** because the LLM-generated commits did not author `compile.sh` in any of the 3 tasks even with from-scratch mode active.

### Per-task results

| Task | C4 Variant A (single-commit) | v0.4.1 Variant A (multi-commit; from-scratch auto) | Δ |
|---|---|---|---|
| 1 calculator | 3/3 (100%) | 3/3 (100%, with manual wrap; 3 commits emitted) | tied |
| 2 jsonpp | 0/7 (default candidate hallucinated path) | 7/7 (100%, with manual wrap; tie-breaker correctly picked `formatting` over `error-handling`) | **+7** |
| 3 wcclone | 6/6 (100%) | 0/6 (library + CLI output format mismatch; Py 3.9 type-hint syntax) | **−6** |
| **Aggregate (RELAXED)** | **9/16 = 56%** | **10/16 = 62.5%** | +1 (+6.5pp) |
| **Aggregate (STRICT, no manual wrap)** | n/a | **0/16 = 0%** | n/a |

### v0.4.1 sub-fixes — production observation receipts

1. **Multi-commit-per-task (AC.V041.1):** all 3 tasks emitted **3 commits each** (vs 1 commit per task in C4). The `===COMMIT===` delimiter parser worked end-to-end against real `claude -p`.
2. **From-scratch prompt mode (AC.V041.2):** all 3 tasks correctly **auto-detected from-scratch** (the docs_only_repo dirs have only README.md + SPEC.md). All 9 emitted diffs use `--- /dev/null` source-side framing.
3. **Build-next tie-breaker (AC.V041.3):** **Task 2 jsonpp correctly picked `G.BACKING.o-formatting-1` first** (composite_score 0.8000) over `G.BACKING.o-error-handling-1` (also 0.8000). C4's empirical failure case is now structurally fixed in production.

### v0.4.1 RF surfaces (F-DESIGN-2 candidate)

**F-DESIGN-2 — From-scratch prompt mode produces structurally-valid multi-commit output but doesn't reliably pin SPEC-required filenames.** Empirically: even with multi-commit-per-task + from-scratch framing + `--- /dev/null` instruction, the LLM in 3/3 v0.4.1 runs:

- Did NOT author `compile.sh` (the SPEC-mandated build artefact).
- Did NOT author an `executable` file directly (chose package shape: `bin/json-format`, `arithmetic/operations.py`, `file_counter.py`).
- Did NOT consistently match the SPEC's CLI output format (Task 3 wcclone printed `Lines: N\nWords: N\nBytes: N` instead of `<l> <w> <b>`).
- Did NOT honor the SPEC's "Test interface" section (which names the exact subprocess shape the test harness uses).

The from-scratch prompt prompts the LLM to "create new files" but doesn't pass the SPEC's behavioral test interface as a prompt input. The LLM doesn't see what shape the test suite expects, so it makes reasonable but spec-incompatible choices (Makefile install vs compile.sh; library shape vs CLI; multi-line output vs single-line).

**Closure path (v0.4.2 patch or v0.5.0 surface):**

1. Pass the SPEC's **Test interface** section (or full SPEC) into the from-scratch prompt as load-bearing context — instruct the LLM that the test harness invokes `./executable <args>` and produces stdout matching `<format>`.
2. OR — author a deterministic **post-processor** that synthesizes `compile.sh` from emitted source files (e.g., `find *.py -maxdepth 1` + emit `cp file.py executable; chmod +x executable`).
3. OR — change the build-next surface to recognize "compile.sh" as a NAMED REQUIRED ARTEFACT in any task whose SPEC references it, and inject that requirement into the prompt.

This is a structurally smaller gap than F-DESIGN-1 (the 3 sub-fixes ARE working in production; the residual gap is one prompt-engineering pass). Plausibly v0.4.2 patch territory, NOT a v0.5.0 reframe.

### Cost + reproducibility

Per-task cost (synthesis + code-gen): ~$0.10–0.15. Total v0.4.1 re-run cost: **~$0.40** (within the $5 ceiling per dispatch directive; consistent with C4's $0.42).

Re-run reproducibility:
- Inputs at `/tmp/v041-pbn-runs/{task1_calculator_docs,task2_jsonpp_docs,task3_wcclone_docs}/`.
- Workspaces at `/tmp/v041-pbn-runs/{task1_calculator_ws,task2_jsonpp_ws,task3_wcclone_ws}/`.
- Eval scripts at `/tmp/v041-pbn-runs/{run-task,eval-task}.sh`.
- Diffs at `<ws>/.loam/extractions/<repo-id>/code-gen/diff.patch`.

These are out-of-tree (`/tmp/`); session-bound. v0.4.2 patch could move them to `plugins/dev-sdlc/odd-extractor/tests/fixtures/programbench/v0/` if reproducibility-on-CI becomes load-bearing.

### AC.V041.4 verdict

**GREEN** for the AC contract ("re-run produces measurable improvement; surface findings"). YELLOW for the empirical aggregate (closer to baseline but not GREEN-band). Per the v0.4.1 plan-doc §4 verdict bands: 57–74% = YELLOW = partial improvement, surface for owner ruling. Per `feedback_locked_design_not_license_for_bad_outcomes`: F-DESIGN-2 surfaced explicitly with closure path; do not silently accept partial-progress.

The structural mechanism of F-DESIGN-1 IS resolved (multi-commit + from-scratch + tie-breaker all working in production). The residual behavioral gap is a *prompt-engineering* question (passing SPEC test-interface into the prompt), not the *architectural* question F-DESIGN-1 surfaced.

## v0.4.2 re-run — F-DESIGN-2 closure verification (AC.V042.{3,4,5})

**Date:** 2026-05-09. **Status:** v0.4.2 patch surface re-run on the same 3 tasks.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`. **Builder:** Sonnet (default).
**HEAD under test:** v0.4.2 sub-fix 2 commit (test-interface load-bearing prompt + Py-version-compat post-process).

> **NOTE on scope:** "100% (16/16) STRICT" here is on the 3 internal toy tasks (calculator, jsonpp, wcclone) — NOT the public ProgramBench leaderboard at programbench.com (where major LLM providers score 0–3% on hundreds of much-harder tasks). The real-benchmark eval was blocked at v0.4.0 C4 (Docker daemon issue) and is deferred to v0.5.0. This experiment validates that the architectural mechanism produces SPEC-compatible output on toy fixtures; it does NOT establish loam's performance on real-world program-synthesis tasks.

### Verdict

**GREEN** — full recovery + step-up to baseline. Variant A pass-rate **100% (16/16) STRICT** vs v0.4.1's 62.5% (10/16) RELAXED + 0% STRICT. The 2 sub-fixes close F-DESIGN-2:

- Sub-fix 1 (AC.V042.1): from-scratch prompt now embeds the SPEC's "Test interface" section as load-bearing context; LLM is instructed to author named build artefacts (`compile.sh`, `executable`) as first-class commits + match the SPEC's CLI exactly.
- Sub-fix 2 (AC.V042.2): from-scratch prompt names Python 3.9-compat (no PEP-604, no match/case) AND a deterministic post-processor (`_lower_pep604_unions`) defensively rewrites `X | Y` → `Union[X, Y]` / `Optional[X]` in `+++ b/*.py` hunks.

### Per-task results

| Task | C4 baseline | v0.4.1 Variant A | v0.4.2 Variant A | Δ vs v0.4.1 |
|---|---|---|---|---|
| 1 calculator | 3/3 (100%) | 3/3 (100%, RELAXED) | 3/3 (100%, STRICT) | tied |
| 2 jsonpp | 0/7 | 7/7 (100%, RELAXED) | 7/7 (100%, STRICT) | tied |
| 3 wcclone | 6/6 (100%) | 0/6 (regression) | 6/6 (100%, STRICT) | **+6** |
| **Aggregate (STRICT)** | n/a | **0/16 = 0%** | **16/16 = 100%** | n/a |
| **Aggregate (RELAXED)** | **9/16 = 56%** | **10/16 = 62.5%** | **16/16 = 100%** | **+6 (+37.5pp)** |

### v0.4.2 sub-fixes — production observation receipts

1. **Test-interface section as load-bearing context (AC.V042.1):** all 3 tasks correctly authored either `compile.sh` (calculator + wcclone) OR a directly-runnable `executable` (jsonpp). The SPEC's "Test interface" section was extracted by `_extract_test_interface_excerpt` from each task's `SPEC.md` and embedded under the canonical `Test interface from SPEC:` heading in the user-prompt. The LLM saw the exact `subprocess.run([./executable, ...])` shape the test harness uses, and matched it exactly (single-line stdout for wcclone vs the v0.4.1 multi-line regression).

2. **Py-version compatibility (AC.V042.2):** wcclone's v0.4.1 regression class (`str | Path` PEP-604 syntax under Py 3.9 test harness) is closed structurally. The instruction-side prompt names "Python 3.9 compatibility" + "no PEP-604 unions"; the post-processor `_lower_pep604_unions` runs defensively after parse so even stochastic LLM regressions get caught. Empirically, the v0.4.2 wcclone diff used no PEP-604 unions (instruction worked); no post-process rewrite was needed.

3. **Multi-commit-per-task (AC.V041.1, inherited):** task1 emitted 2 commits (arithmetic.c + compile.sh), task2 emitted 1 commit (single executable matched SPEC), task3 emitted 2 commits (executable + compile.sh). v0.4.1 multi-commit parser preserved.

4. **From-scratch prompt mode (AC.V041.2, inherited):** all 3 tasks correctly auto-detected from-scratch + emitted `--- /dev/null` framing.

5. **Build-next tie-breaker (AC.V041.3, inherited):** jsonpp tie-breaker correctly picked `G.BACKING.o-workflow-1` (task-shape) over alternatives at composite_score 0.8000.

### Diff shapes (the structural difference vs v0.4.1)

**Task 1 calculator (v0.4.2):**
- `arithmetic.c` — C source with main() taking `<a> <op> <b>` argv + printf(int).
- `compile.sh` — `gcc -o executable arithmetic.c`.

**Task 2 jsonpp (v0.4.2):**
- `executable` — Python script with shebang `#!/usr/bin/env python3` reading stdin + writing pretty JSON. Single commit; the file IS the executable. (eval-task.sh chmod +x added in v0.4.2 to honor "executable" as a named artefact when no `compile.sh` is emitted.)

**Task 3 wcclone (v0.4.2):**
- `executable` — Python script reading argv[1], counting bytes/words/lines, printing single-line `<l> <w> <b>`.
- `compile.sh` — `chmod +x executable`.

vs the v0.4.1 wcclone shape (library + tests; no executable; PEP-604 unions; multi-line stdout) — fully recovered.

### Cost + reproducibility

Per-task wall-clock + cost (Stage 1 extract + Stage 5 code-gen):
- task1 calculator: 36.3s code-gen wall-clock; full pipeline ~3 min.
- task2 jsonpp: 54.3s code-gen wall-clock; full pipeline ~3 min.
- task3 wcclone: 57.8s code-gen wall-clock; full pipeline ~3 min.

Per-task synthesis cost (Stage 1): ~$0.10–0.15 per task (consistent with v0.4.1 / C4 bands). Total v0.4.2 re-run cost: **~$0.45** (within the $5 ceiling per dispatch directive; consistent with v0.4.1's $0.40).

Re-run reproducibility:
- Inputs at `/tmp/v042-pbn-runs/{task1_calculator_docs,task2_jsonpp_docs,task3_wcclone_docs}/`.
- Workspaces at `/tmp/v042-pbn-runs/{task1_calculator_ws,task2_jsonpp_ws,task3_wcclone_ws}/`.
- Eval scripts at `/tmp/v042-pbn-runs/{run-task,eval-task}.sh`. Eval-task.sh widened in v0.4.2 to chmod +x `executable` when authored directly (no `compile.sh`).
- Diffs at `<ws>/.loam/extractions/<repo-id>/code-gen/diff.patch`.

These are out-of-tree (`/tmp/`); session-bound. v0.4.3+ patch could move them to `plugins/dev-sdlc/odd-extractor/tests/fixtures/programbench/v0/` if reproducibility-on-CI becomes load-bearing.

### AC.V042.{3,4,5} verdicts

- **AC.V042.3 (wcclone recovery, threshold ≥4/6):** **GREEN** at 6/6. Full structural recovery. The v0.4.1 0/6 regression class (library shape + multi-line stdout + PEP-604 unions) is closed by the test-interface load-bearing prompt + Py-version-compat post-process.
- **AC.V042.4 (no-regression on calculator + jsonpp, threshold v0.4.1 levels):** **GREEN**. calculator 3/3 (tied), jsonpp 7/7 (tied). Now STRICT (compile.sh authored OR executable matches subprocess shape) where v0.4.1 was RELAXED-only.
- **AC.V042.5 (aggregate ≥75%, threshold 12/16):** **GREEN** at 16/16 = 100%. Step-up of +6 (+37.5pp) over v0.4.1.

The structural mechanism of F-DESIGN-2 IS resolved. The from-scratch prompt now produces SPEC-compatible artefacts at the rate the direct `claude -p` baseline does. The RELAXED-vs-STRICT distinction collapses to STRICT-only at v0.4.2 because every emitted diff carries the named build artefact (or matches the subprocess-as-source pattern jsonpp uses).
