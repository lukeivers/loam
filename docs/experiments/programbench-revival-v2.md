# ProgramBench-revival v2 — does loam materially beat a bare LLM at hands-off task execution?

*Report authored 2026-05-16. The deliverable a
non-technical reader rules from (AC.PBR.7). "loam does not materially
beat the baseline" and "indeterminate" are FIRST-CLASS plan-success
outcomes — reported straight, never retried to green, the margin
never weakened.*

## Plain-language answer

**Does loam materially beat a bare LLM at hands-off task execution
for a non-technical user, and by how much, judged by something other
than loam's own judge?**

> NO — on this frozen non-subjective set, the harness did NOT materially beat a bare Claude. This is a real, informative result reported straight, not a loam failure to be retried.

loam does NOT materially beat the baseline on this set: loam recovered only 0/1 of the baseline's misses (not a >50% clear majority). This is a FIRST-CLASS plan-success outcome, reported straight — NOT retried to green, the margin NOT weakened.

## Honest scope (read this first)

This is **not** the public ProgramBench leaderboard. The public
ProgramBench eval requires a linux/amd64 + Docker harness and the
local upstream clone is an empty skeleton (no dataset, no harness) on
this Darwin/arm64 host — the v0.4.0 C4 host-block recurs as a
no-usable-public-set block (empirically rechecked this build: the
docker daemon is up, but the public dataset/harness is absent). Per
the plan's AC.PBR.2 satisfiability note + §3.3/§8.2, this run uses a
**documented honest-scope ProgramBench-CLASS substitute** of
6 non-subjective tasks that **preserves the
positive-real-outcome-floor property** (each task's deterministic
check exits 0 IFF the real outcome was actually delivered; a
compiled-but-no-effect / empty-extraction / target-untouched result
is a non-pass by construction). It does **not** fake real-leaderboard
numbers and does **not** silently shrink the question. This is also
explicitly **distinct** from the v0.4.x ProgramBench history (3
hand-authored toy tasks against the code-gen surface, never the loop,
never independently judged) — a different, harder, independently-
judged measurement; the toy-task pass-rate framing is NOT inherited.

## The scoring authority (AC.PBR.3)

INDEPENDENT held-out adversarial tool-grounded judge (programbench_revival.scorer.independent_judge, composing the proven _independent_judge shape via spawn_isolated_claude) — PROVABLY NOT the loop's own handsoff_loop.intake._judge_faithful AC.B.4b judge (never imported / never called by this harness).

## The frozen margin (AC.PBR.5 — FROZEN-RATIFIED D-PBR-1, owner Telegram 11447)

> loam MATERIALLY BEATS baseline IFF BOTH: (i) among the tasks the BASELINE arm is independently judged a NON-PASS on, the LOAM arm is independently judged a PASS on a CLEAR MAJORITY (strictly >50%) of them; AND (ii) loam's TOTAL independently-judged pass count does NOT regress below baseline's total. Otherwise loam does NOT materially beat baseline (a first-class plan-success outcome). If there are too few baseline non-passes to define a clear majority (0 baseline misses) OR the set is under-powered, the verdict is INDETERMINATE (a definite reportable finding naming why). 'Every task a pass' is a DOCUMENTED ASPIRATIONAL / SECONDARY metric, EXPLICITLY NOT the gate.

The builder froze EXACTLY this before any run and did NOT move it
after runs began.

## Computed three-valued verdict (AC.PBR.5)

- **Verdict:** `loam-does-not-materially-beat-baseline` (computed from the numbers, not
  asserted)
- Baseline independently-judged pass count: **5**
  / 6
- Loam independently-judged pass count: **5**
  / 6
- Baseline non-pass tasks: ['PB3-dedupe-lines']
- Of those, recovered by loam:
  (none)
- Clear-majority-of-baseline-misses cleared (>50%):
  **False**
- No total-pass regression: **True**

### All-tasks-pass aspirational metric (AC.PBR.7 — NOT the gate)

DOCUMENTED ASPIRATIONAL / SECONDARY metric — explicitly NOT the v2 pass/fail gate (the gate is the frozen (a)/(b)/(c) margin).

- baseline all-tasks-pass:
  `False`
- loam all-tasks-pass:
  `False`

## Per-arm failure-signature map (AC.PBR.6 — the false-success class explicit)

Every non-pass carries exactly one class from the frozen four-class
taxonomy. The **produced-but-no-real-effect** column is the
false-success class the positive-real-outcome floor + held-out
anti-overfit conjunction is built to catch (the owner's Telegram
11447 concern: compiled-but-no-result / empty extraction /
didn't-touch-the-target nominally reported as done).

| Arm | did-not-produce-output | produced-but-no-real-effect | produced-but-wrong | honest-negative-refusal |
|---|---|---|---|---|
| baseline | 0 | 1 | 0 | 0 |
| loam | 0 | 1 | 0 | 0 |

## Baseline arm — definite per-task dispositions

| Task | Passed | Judge tag (independent) | Floor exit | Held-out exit | Failure class | Cost USD | Wall s |
|---|---|---|---|---|---|---|---|
| PB1-csv-sum | PASS | FAITHFUL | 0 | 0 | — | 0.0517447 | 18.7 |
| PB2-json-extract | PASS | FAITHFUL | 0 | 0 | — | 0.0966978 | 15.66 |
| PB3-dedupe-lines | non-pass | CHECKABLE-BUT-WRONG | 0 | 1 | produced-but-no-real-effect | 0.08012845 | 15.69 |
| PB4-rename-key | PASS | FAITHFUL | 0 | 0 | — | 0.0403339 | 16.89 |
| PB5-word-count-cli | PASS | FAITHFUL | 0 | 0 | — | 0.0896053 | 16.59 |
| PB6-fix-off-by-one | PASS | FAITHFUL | 0 | 0 | — | 0.08770965 | 11.84 |

## Loam arm — definite per-task dispositions

| Task | Passed | Judge tag (independent) | Floor exit | Held-out exit | Failure class | Cost USD | Wall s |
|---|---|---|---|---|---|---|---|
| PB1-csv-sum | PASS | FAITHFUL | 0 | 0 | — | n/a | 14.61 |
| PB2-json-extract | PASS | FAITHFUL | 0 | 0 | — | n/a | 14.71 |
| PB3-dedupe-lines | non-pass | CHECKABLE-BUT-WRONG | 0 | 1 | produced-but-no-real-effect | n/a | 16.69 |
| PB4-rename-key | PASS | FAITHFUL | 0 | 0 | — | n/a | 31.29 |
| PB5-word-count-cli | PASS | FAITHFUL | 0 | 0 | — | n/a | 188.3 |
| PB6-fix-off-by-one | PASS | FAITHFUL | 0 | 0 | — | n/a | 14.53 |

## Measured cost + latency (AC.PBR.6 — measured, never estimated)

- Baseline arm measured cost (sum of per-task `total_cost_usd`):
  **$0.4462**
- Loam arm measured cost: **$0.0000**
- Cost ceiling (D-PBR-4): $8.00;
  measured spent: $0.4462;
  halted on ceiling: **False**
- Total wall-clock: 630.4s
- Tasks completed: 6
  / 6
  (full set completed)

## Reproducibility (AC.PBR.6)

The headline is reproducible from the preserved per-(arm,task)
evidence under `framework/tools/programbench-revival/.run_evidence/`
(raw transcripts + floor/held-out exit codes + independent-judge
verdicts + measured cost). Re-running the frozen scorer over the
preserved artefacts yields the same verdict. Task set content-hash:
`8ca7c4de98e33ea5c33a006efff409bb7024015f7ab720c1531ff14fa566921d` (pinned before any run).

## Limitation named in plain language (F2 §10.1)

This is **n=1 per task** — a deliberate architectural-verdict choice
(the question is "does the harness beat the floor *at all*?", not
"by exactly how many percent with a confidence interval"), NOT
under-powering. A reader must **not** over-read a single-run delta as
a stable population estimate. The cost discipline forbids burning the
ceiling on statistical replication; a bounded small-k re-run is
defined only at the decision margin (D-PBR-3), never to flip a fail
to a pass.

## Cost-measurement gap named, not papered (F2 — honest-absent, never estimated)

The baseline arm's per-task cost is **measured** from the
`--output-format json` `total_cost_usd` envelope (D-COST-BAND). The
**loam arm's per-task cost surfaced as `$0.00`** — a real
**measurement gap**, recorded honestly as zero/absent and **never
estimated or fabricated** (the D-COST-BAND discipline: an unmeasured
cost is reported absent, not back-filled with a guess). Root cause
(named, not papered): the real `handsoff-loop` CLI's stdout JSON
result line carries `cost_usd` summed from its sub-agents'
`total_cost_usd`, but in these runs that field resolved to `0`/absent
from the loop's own envelope — the loop's internal sub-agent cost
summation did not surface a non-zero figure through the CLI result
line this harness parses. This is a **reported-metric gap, not a
verdict defect**: the three-valued verdict is computed from the
independent judge tag + the floor + held-out exit codes (AC.PBR.4),
**not** from cost; the loam-arm cost figure is a secondary reported
metric and its absence does not move the verdict. The measured
baseline cost + total measured spend are accurate; the loam-arm
per-task cost line should be read as "not surfaced", not "$0 of real
work" (the loam arm provably did real multi-turn `claude` sub-agent
work — see the preserved `loam_artifacts/sub_0_*.transcript` per task,
`is_error:false`, multi-turn). Closing this is a follow-on
loop-CLI-cost-surfacing item, not in this measurement cycle's fence.

## Zero-interaction parity (AC.PBR.1 / D-PBR-6)

Both arms received the IDENTICAL single task prompt under a CLOSED
(no-answer) user channel — zero interactive back-and-forth, no
simulated/scripted/stand-in user for either arm. The loam arm was
driven with `handsoff-loop run --frozen` so no live question was ever
posed; the loop's interactive intake/approval machinery degraded to
internal best-effort. The only difference under measurement is the
loop's INTERNAL machinery (decompose → dispatch → independent-verify
→ refine-internally → persist) operating on the SAME single prompt.
A task genuinely unresolvable without an answer is an honest-negative
the independent judge scored as a non-pass — the correct in-intent
disposition for a one-shot benchmark, not a confound engineered away.
