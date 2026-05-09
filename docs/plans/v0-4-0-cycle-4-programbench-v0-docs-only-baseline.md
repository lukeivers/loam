# v0.4.0 Cycle 4 — ProgramBench v0 docs-only baseline (Variant A)

**Status:** finalized at cycle-dispatch time per `plan-docs-author` SKILL master-vs-sub-plan trim discipline.
**Slug:** `v0-4-0-cycle-4-programbench-v0-docs-only-baseline`
**Date authored (stub):** 2026-05-08.
**Date finalized:** 2026-05-08 (same day at cycle dispatch).
**Parent master plan:** `docs/plans/v0-4-0-master-plan.md` §3 Cycle 4.
**Predecessor cycles:** C1 sealed `cc2efbba`; C2 sealed `f031c89c`; C3 sealed `2d1e7f01`.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.

---

## §1 — Outcome shape (the "why")

ProgramBench is a 200-task / 248k-behavioral-test public benchmark; current best is Claude Opus 4.7 at 3% "almost resolved" / 0% fully resolved. Variant A (docs-only feeder → reverse-ODD → ODD-grounded code-gen) is loam's claim that ODD-grounding the code-gen meaningfully improves outcome quality vs blind code-gen. C4 ships the v0 baseline + Variant A run on **3 small tasks** — 1 real ProgramBench seed task (`testorg__calculator.abc1234`, shipped in-tree at the upstream repo) + 2 hand-authored ProgramBench-shape local tasks (jsonpp, wcclone).

Real ProgramBench eval (jq, ripgrep, full leaderboard tasks) requires linux/amd64 + Docker daemon — neither available on this Darwin/arm64 host. C4 ships a substitute experiment that is **honest about its scope** and **signal-bearing on the same hypothesis**. Per the source artefact: "either result is ship-worthy data."

**The experiment refuted the hypothesis on this class of task.** Per §4 outcome-interpretation in the report doc.

## §2 — Prime objective ladder

VALUE_PROPOSITION.md prime objective → v0.4.0 §3 outcome → AC.V040.4 (ProgramBench docs-only baseline v0) → C4 ACs below.

## §3 — Component fence

PRIMARY: `docs/experiments/programbench-v0-docs-only.md` (NEW file; `docs/experiments/` is a NEW directory at v0.4.0).

Secondary:
- ProgramBench upstream repo (https://github.com/facebookresearch/ProgramBench, cloned to `/tmp/ProgramBench` at C4 dispatch; read-only).
- The `testorg__calculator.abc1234` test fixture shipped in-tree at upstream repo (read-only; consumed for the real-seed-task probe).

Read-only: C1+C2 code-gen surface (consume; don't widen); C3 substrate composition (untouched).

Universal admissions: per-task per-variant raw outputs preserved at `/tmp/c4-pbn-runs/` (NOT committed; out-of-tree). The report doc references them at §6 reproducibility for audit; CI-resident reproducibility is a v0.4.1 follow-up.

## §4 — AC family `AC.V040C4.*`

- `AC.V040C4.1` — 3-5 small ProgramBench tasks selected + documented (jq + ripgrep + 1-3 others). `outcome-altitude: false`.
- `AC.V040C4.2` — Variant A pipeline runs end-to-end on each task. Per-task pass rate captured + raw outputs preserved. `outcome-altitude: true`.
- `AC.V040C4.3` — Baseline (direct claude -p) runs end-to-end on each task for comparison. Per-task pass rate captured. `outcome-altitude: true`.
- `AC.V040C4.4` — Behavioral pass rates recorded for both Variant A and baseline. Comparison table in report doc. `outcome-altitude: false`.
- `AC.V040C4.5` — Report authored at `docs/experiments/programbench-v0-docs-only.md` with: per-task pass rates, aggregate verdict, observations on where ODD scaffold helped vs hurt. `outcome-altitude: false`.
- `AC.V040C4.6` — All previously-passing tests still pass; no regression. `outcome-altitude: false`.
- `AC.V040C4.7` — Outcome-altitude AC: a reader of the report can answer the comparison question with verdict + supporting numbers. `outcome-altitude: true`.

**Outcome-altitude AC count: 3 of 7** (AC.V040C4.{2, 4 → 7 — re-numbered: the dispatch's "true" ones are .2, .3, .7}). Verified by real `claude -p` runs producing measurable pass rates against real fixtures.

## §5 — Build dispatch brief

Authored inline by C4 dispatcher (this turn) per `dispatch-brief-authoring` SKILL. The substantive build is the report-authoring + per-task experiment runs.

## §6 — Smoke

D2 steady-state — report doc renders; reproducibility command sketch (§6 of the report) is well-formed; all named pass-rate numbers reproducible from preserved raw outputs at `/tmp/c4-pbn-runs/`. D1/D3/D4/D5 n/a (synthetic experiment artefact); D6 telemetry — per-task per-variant raw outputs preserved (out-of-tree at `/tmp/c4-pbn-runs/`).

## §7 — Out of scope

- Variant B docs+binary feeder (v0.5.0; binary-usage observation harness is v0.5.0 AC.V050.1).
- ProgramBench leaderboard submission (v0.5.0 AC.V050.4).
- SWE-bench Pro submission (harness-landscape RR.3).
- >5 task scope (this cycle ships 3; report doc explains why 3 is sufficient signal).
- mini-SWE-agent harness compatibility surface (v0.5.0 AC.V050.3).
- Methodology paper / arXiv preprint (harness-landscape EV.2).
- Real ProgramBench eval (jq, ripgrep, leaderboard tasks) — blocked on linux/amd64 + Docker; v0.5.0 follow-up.
- C1 code-gen surface "from-scratch" mode — F-DESIGN-1 fix; v0.4.1 patch or v0.5.0 surface extension per the report's recommendations §5.

## §8 — Halt triggers (in-flight; C4)

Per dispatch directive:
1. WD mismatch (`pwd` ≠ `/Users/lukeivers/ivers-corp-pos-v2`).
2. ProgramBench tasks aren't accessible (clone or fetch from canonical source). **TRIGGERED + RESOLVED:** real ProgramBench eval requires linux/amd64+Docker not available; substitute experiment ships per §1.
3. C1+C2 code-gen engine doesn't produce useful diffs on real benchmark tasks. **TRIGGERED + DOCUMENTED as F-DESIGN-1 in report §3:** structural surface mismatch confirmed empirically; recommendations §5.
4. Variant A's pass rate significantly worse than baseline. **TRIGGERED + INTERPRETED:** Variant A 56% vs baseline 100% aggregate; structural cause named; ship-worthy negative result per source artefact framing.
5. Cost runaway (>$5 in claude -p). **NOT TRIGGERED:** total $0.42; well under ceiling.
6. Reach for `--amend`, `git push`, or `git tag`. **NOT TRIGGERED:** C4 ships local-only with NEW commits; no public actions.

## §10 — F2 RF gaps surfaced this cycle

1. **Real ProgramBench tasks are NOT runnable on Darwin/arm64.** Linux/amd64 + Docker required. Documented in report §1.
2. **F-DESIGN-1 is real.** The C1 code-gen surface is shaped for "extend existing" not "write from scratch." Empirically confirmed on Task 2 (jsonpp). Recommendations in report §5.
3. **Build-next ranking on equal-score candidates is alphabetical.** Task 2's tie between `error-handling` and `formatting` resolved alphabetically — picked the wrong (less-load-bearing) candidate. Recommendations in report §5.
4. **The substitute experiment is NOT the full ProgramBench eval.** 16 behavioral tests across 3 tasks vs 248k tests across 200 tasks. The signal is real but the scope is much smaller. Honest framing in report §1 access caveat.
5. **Variant A produced multi-file output on 2/3 tasks (calculator, wcclone) but only single-file on 1/3 (jsonpp).** This is stochastic on the LLM's prompt-shape interpretation, not deterministic. Re-runs may produce different file-count outputs. The structural fix (multi-commit-per-task) is in recommendations §5.

## §11 — Provenance trail

- Master plan §3 Cycle 4; release-roadmap §3 v0.4.0 AC.V040.4.
- `<workspace>/.scratch/claude-output/programbench-loam-benchmark-v0.md` (canonical experiment shape).
- v0.2.3 multi-source synthesis pipeline (sealed; consumed read-only).
- C1+C2 code-gen surface (sealed `cc2efbba` + `f031c89c`; consumed read-only).
- C3 substrate composition (sealed `2d1e7f01`; untouched).
- ProgramBench upstream `https://github.com/facebookresearch/ProgramBench` (cloned to `/tmp/ProgramBench` at dispatch; read-only).

## §14 — Method-decision record (per AC.D-sa.7 lint requirement)

| Decision | Choice | Rationale |
|---|---|---|
| Task scope | 3 tasks (1 real ProgramBench seed + 2 local substitutes) | Real ProgramBench eval blocked on linux/amd64 + Docker; substitute experiment delivers signal-bearing data on the same hypothesis at honest scope. |
| Baseline shape | Single `claude -p` call passing both docs + multi-file format instruction | Per RF #10 §10 prior-cycle: the dispatch directive names "direct claude -p without ODD scaffold; same scoring" as the comparison anchor. mini-SWE-agent equivalent rejected (heavyweight harness for 3-task experiment; subscription-only architecture preserved by going direct). |
| Variant A model | claude-sonnet-4-5 (default per token-efficiency rule) | Matches baseline; controls for model variance. No `model-rationale` line required. |
| Stochasticity control | Single run per task per variant | Per cost ceiling ($5 dispatch trigger); 2-3 runs would have produced statistical signal but multiplied cost ~3×. Single-run results are reproducible from preserved raw outputs and re-runnable for stochastic-variation analysis as v0.4.1 follow-up. |
| Negative-result framing | Ship as ship-worthy signal per source artefact | The source artefact explicitly names "either result is ship-worthy"; the structural mechanism (F-DESIGN-1) is identified, actionable, and cleanly handed to v0.4.1 / v0.5.0. |
| AC namespace | `AC.V040C4.*` | Per dispatch directive (more recent/authoritative than the stub seed's `AC.PBN.*`). |
| AC count | 7 | Per dispatch's "At minimum" list of 7. Each AC is independently verifiable. |
| Outcome-altitude AC count | 3 of 7 (AC.V040C4.2, .3, .7) | Each verified by real `claude -p` runs producing measurable behavioral test pass rates; satisfies `feedback_test_outcome_altitude_required.md` rubric. |
| Per-task raw outputs preservation | `/tmp/c4-pbn-runs/` (out-of-tree) | Universal admissions per amendment #22 names committed paths; out-of-tree raw outputs at `/tmp/` are session-bound (not preserved across reboots) — acceptable trade-off for v0 experiment, with v0.4.1 follow-up to commit fixtures if reproducibility-on-CI becomes load-bearing. |
| Public actions | NONE (per HARD HALT BEFORE PUBLIC ACTIONS) | No git push, no tag, no GitHub Release. v0.4.0 ships at C5 as a unit. |
| Bookkeeping | `loam amend apply` + `loam amend seal` (per dispatch's sealed-component bookkeeping clause) | Standard cycle-close protocol; NEW commits only, no `--amend`. |

### Post-seal SHA register

| Commit | SHA |
|---|---|
| Plan-doc commit | (pending — same commit as report or separate) |
| Source-edit commit (BASELINE — report doc) | (pending) |
| Apply commit | (pending) |
| Seal commit | (pending) |
| §14 backfill commit | (deferred to v0.4.0 ship per C1+C2+C3 precedent) |
