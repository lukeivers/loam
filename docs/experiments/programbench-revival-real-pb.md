# ProgramBench-revival (REAL public ProgramBench) — does the real sealed loop materially beat a bare LLM on the REAL benchmark, judged independently?

*Report authored 2026-05-16. The deliverable a
non-technical reader rules from (AC.RPB.7). "loam does not materially
beat the baseline on the real benchmark" and "indeterminate" are
FIRST-CLASS plan-success outcomes — reported straight, never retried
to green, the FROZEN margin never weakened.*

## Plain-language answer

**Does loam materially beat a bare LLM at hands-off task execution
for a non-technical user ON THE REAL PUBLIC PROGRAMBENCH, by how much,
judged by something other than loam's own judge?**

> INDETERMINATE — the REAL public ProgramBench subset could not produce a determinate material-win/loss picture; the report names exactly why (a definite finding, not a non-answer — including the k_min small-k floor correctly forcing indeterminate on a degenerate baseline-miss denominator, the named v2 task-#44 fix).

INDETERMINATE: baseline-miss-denominator < k_min (baseline independently-judged non-passes = 0; frozen k_min = 2). The 'clear majority of the baseline's non-passes' computation is UNDEFINED / degenerate on a sub-k_min denominator, so the verdict is FORCED to (c) indeterminate with this machine-stated reason — a degenerate or near-degenerate denominator can NEVER read as a determinate loss or win. This is the named v2 task-#44 / PB3 defect being CORRECTLY handled (v2 forced indeterminate only at exactly 0 baseline misses; this real-PB rule forces it at < k_min). A definite, reportable finding naming exactly why — NOT a loam failure, NOT a reason to re-pick easier tasks or shrink to a substitute.

## This is the REAL public ProgramBench (read this first) — NOT the v2 substitute

This is the REAL public ProgramBench measurement. It is a DIFFERENT, HARDER artefact than the v2 6-task substitute (slug programbench-revival-v2, task_set_id programbench-revival-v2-honest-scope-6task). The v2 substitute result MUST NOT be cited as a real-PB result; it remains a valid honest-scope record FOR ITS TIME, preserved un-extended. This cycle supersedes ONLY v2 task-source decision (the host-block premise is Tier-0-refuted by the builder own live 2026-05-16 recheck), NOT v2 invariant spine.

This measurement ran against a **digest-pinned subset of the REAL
public ProgramBench task images** (5
instances), scored by the **REAL upstream `programbench eval`**
(`4e8456b`) consuming the **REAL
HuggingFace `programbench/ProgramBench-Tests` blobs** (snapshot
`de0ddfb637590c7ecb54fa0b5301f6dc7dfbcee5`) under `linux/amd64` Docker
emulation. The §9 correction of the v2 false host-block premise is
recorded in `docs/STATE.md` and `docs/release-roadmap.md`: the v2
"public ProgramBench host-block recurs" claim was an inherited
8-day-old precedent treated as current reality and is **Tier-0-refuted
by the builder's own live 2026-05-16 recheck** (Docker up, the real
`:task` images present + amd64-emulation-runnable, the upstream clone
fully populated, the HF dataset cached). The v2 substitute number is
**not** a real-PB result and is **not** cited as one here.

## The scoring authority (AC.RPB.3)

INDEPENDENT held-out adversarial tool-grounded judge (programbench_revival.scorer.independent_judge, composing the proven _independent_judge shape via spawn_isolated_claude), GROUNDED in the REAL upstream programbench eval *.eval.json graded score + the frozen per-task floor theta — PROVABLY NOT the loop own handsoff_loop.intake._judge_faithful AC.B.4b judge (never imported / never called by this harness).

The independent judge is grounded in the **REAL upstream
`*.eval.json` graded test-suite result** (`score = n_resolved /
len(test_results)`; `compile_failed` ⇒ 0.0) **plus the frozen
per-task positive-real-outcome floor threshold θ** — never the arm's
friendly summary.

## The frozen margin (AC.RPB.5 — FROZEN-RATIFIED D-PBR-1 + the k_min small-k floor / D-RPB-1)

> loam MATERIALLY BEATS baseline IFF BOTH: (i) among the tasks the BASELINE arm is independently judged a NON-PASS on, the LOAM arm is independently judged a PASS on a CLEAR MAJORITY (strictly >50%) of them; AND (ii) loam's TOTAL independently-judged pass count does NOT regress below baseline's total. Otherwise loam does NOT materially beat baseline (a first-class plan-success outcome). The 'clear majority of the baseline's non-passes' computation is GATED by a FROZEN small-k floor k_min >= 2 on the baseline-miss denominator: if the count of tasks the baseline arm is independently judged a NON-PASS on is < k_min, the verdict is FORCED to INDETERMINATE with the machine-stated reason 'baseline-miss-denominator < k_min' (the named v2 task-#44 degenerate-denominator defect fix) — a degenerate or near-degenerate denominator can NEVER read as a determinate loss or win. 'Every task a pass' is a DOCUMENTED ASPIRATIONAL / SECONDARY metric, EXPLICITLY NOT the gate.

The builder froze EXACTLY this before any run and did NOT move it
after runs began. The **`k_min = 2` small-k floor** is the
named v2 task-#44 / PB3 degenerate-denominator defect fix: v2's rule
forced indeterminate only at *exactly* 0 baseline misses; this
real-PB rule forces verdict (c) indeterminate at `< k_min` baseline
misses — a degenerate OR near-degenerate denominator can never read
as a determinate loss/win.

## Computed three-valued verdict (AC.RPB.5 — computed, not asserted)

- **Verdict:** `indeterminate`
- Baseline independently-judged pass count:
  **0** / 5
- Loam independently-judged pass count:
  **0** / 5
- Baseline non-pass tasks: (none)
- Baseline-miss denominator: **0**
  (frozen `k_min` = 2; below k_min:
  **True**)
- Of the baseline's misses, recovered by loam:
  (none)
- Clear-majority-of-baseline-misses cleared (>50%):
  **False**
- No total-pass regression: **True**

### All-tasks-pass aspirational metric (AC.RPB.7 — NOT the gate)

DOCUMENTED ASPIRATIONAL / SECONDARY metric — explicitly NOT the real-PB pass/fail gate (the gate is the frozen (a)/(b)/(c) margin with the k_min small-k floor).

- baseline all-tasks-pass:
  `False`
- loam all-tasks-pass:
  `False`

## Per-arm failure-signature map (AC.RPB.6 — the false-success class explicit)

Every non-pass carries exactly one class from the frozen four-class
taxonomy. The **produced-but-no-real-effect** column is the
false-success class the positive-real-outcome floor (the real
upstream graded eval at θ) is built to catch: a `compile_failed` /
empty / hollow submission that nominally reports done but passes ~0
real upstream tests.

| Arm | did-not-produce-output | produced-but-no-real-effect | produced-but-wrong | honest-negative-refusal |
|---|---|---|---|---|
| baseline | 0 | 0 | 0 | 0 |
| loam | 0 | 0 | 0 | 0 |

## Baseline arm — definite per-task dispositions (REAL public ProgramBench)

| Task | Instance ID | Passed | Judge tag (independent) | Upstream graded score | n_resolved/n_tests | error_code | Floor θ | Failure class | Cost USD | Agent wall s | Eval-emul wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|

## Loam arm — definite per-task dispositions (REAL public ProgramBench)

| Task | Instance ID | Passed | Judge tag (independent) | Upstream graded score | n_resolved/n_tests | error_code | Floor θ | Failure class | Cost USD | Agent wall s | Eval-emul wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|

## Measured cost + the agent-vs-eval-emulation wall-clock split (AC.RPB.6 / D-RPB-4 — measured, never estimated)

- Baseline arm measured cost (sum of per-task `total_cost_usd`):
  **$0.0000**
- Loam arm measured cost: **$0.0000**
- Cost ceiling (D-RPB-4): $20.00;
  measured spent: $0.0000
- Wall-clock ceiling (D-RPB-4): 21600s;
  measured total wall-clock:
  0.0s
- **Agent wall-clock** (baseline 0s + loam
  0s) vs **real upstream eval-emulation wall-clock**
  (0s) — recorded DISTINCTLY (F2 §10.3: the real-eval
  amd64-emulation leg is the wall-clock-heavy leg, not the agent).
- Halted on ceiling: **False**
  (full subset completed within the measured ceiling)
- Tasks completed: 0
  / 5

## Reproducibility (AC.RPB.6)

The headline is reproducible from the preserved per-(arm,task)
evidence under
`framework/tools/programbench-revival/realpb/.run_evidence/` — raw
transcripts + the **REAL upstream `*.eval.json` artefacts** (the
`test_results` + graded score + `error_code`) + independent-judge
verdicts + measured cost + the agent/eval wall-clock split.
Re-running the frozen scorer over the preserved `*.eval.json` +
transcripts yields the same verdict. Frozen task-set content-hash:
`35aa17a063ae7b76269f257a27a78ea21676970c5c11e47a848bcc83911317fe` (pinned before any run).

## Limitation named in plain language (F2 §10.6)

This is **n=1 per task** — a deliberate architectural-verdict choice
(the question is "does the harness beat the floor *at all* on the
real benchmark?", not "by exactly how many percent with a confidence
interval"), NOT under-powering. On the REAL public ProgramBench the
stochastic compile-failure rate is high (frontier models score 0–3%
on the full public set), so a reader must **especially not** over-read
a single-run delta as a stable population estimate. The cost +
wall-clock discipline forbids burning the ceiling on statistical
replication; a bounded small-k re-run is defined only at the decision
margin (D-RPB-3), never to flip a fail to a pass.

## Zero-interaction parity (AC.RPB.1 / D-RPB-6)

Both arms received the IDENTICAL single task prompt under a CLOSED
(no-answer) user channel — zero interactive back-and-forth, no
simulated/scripted/stand-in user for either arm. The loam arm was
driven with `handsoff-loop run --frozen` so no live question was ever
posed; the loop's interactive intake/approval machinery degraded to
internal best-effort. The only difference under measurement is the
loop's INTERNAL machinery (decompose → dispatch → independent-verify
→ refine-internally → persist) operating on the SAME single prompt. A
task genuinely unresolvable without an answer is an honest-negative
the independent judge scored as a non-pass — the correct in-intent
disposition for a one-shot benchmark, not a confound engineered away.
Neither arm ever saw the real upstream test suite or the scoring
command (ground-truth isolation, AC.RPB.1).
