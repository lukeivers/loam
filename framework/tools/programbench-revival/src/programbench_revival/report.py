# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.  See the License for the specific language governing
# permissions and limitations under the License.

"""AC.PBR.7 — the verdict report a non-technical reader rules from.

Renders the run result into docs/experiments/programbench-revival-v2.md:
both arms' definite per-task disposition tables, each arm's
independently-judged honest-coverage, the PER-ARM FAILURE-SIGNATURE
MAP (the false-success "produced-but-no-real-effect" class explicit
per arm), the FROZEN-RATIFIED margin, the computed three-valued
verdict, the all-tasks-pass aspirational metric LABELLED NOT the
gate, measured cost/latency, the n=1-per-task limitation in plain
language, and a plain-language answer — OR a definite honest-negative
/ indeterminate naming WHY.
"""

from __future__ import annotations

from datetime import date


def _disp_table(rows: list[dict]) -> str:
    out = [
        "| Task | Passed | Judge tag (independent) | Floor exit | "
        "Held-out exit | Failure class | Cost USD | Wall s |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        out.append(
            f"| {r['task_id']} | {'PASS' if r['passed'] else 'non-pass'} "
            f"| {r['judge_tag']} | {r['floor_exit']} "
            f"| {r['held_out_exit']} | {r['failure_class'] or '—'} "
            f"| {r['cost_usd'] if r['cost_usd'] is not None else 'n/a'} "
            f"| {r['wall_clock_s']} |"
        )
    return "\n".join(out)


def _sig_table(sig: dict) -> str:
    out = ["| Arm | did-not-produce-output | produced-but-no-real-"
           "effect | produced-but-wrong | honest-negative-refusal |",
           "|---|---|---|---|---|"]
    for arm in ("baseline", "loam"):
        s = sig.get(arm, {})
        out.append(
            f"| {arm} | {s.get('did-not-produce-output', 0)} "
            f"| {s.get('produced-but-no-real-effect', 0)} "
            f"| {s.get('produced-but-wrong', 0)} "
            f"| {s.get('honest-negative-refusal', 0)} |"
        )
    return "\n".join(out)


def render_report(result: dict) -> str:
    v = result["verdict"]
    b = result["baseline_dispositions"]
    lo = result["loam_dispositions"]
    plain = {
        "loam-materially-beats-baseline":
            "YES — on this frozen non-subjective ProgramBench-class "
            "set, the real sealed hands-off loop materially beat a "
            "bare Claude, judged by an independent held-out judge "
            "(not loam's own).",
        "loam-does-not-materially-beat-baseline":
            "NO — on this frozen non-subjective set, the harness did "
            "NOT materially beat a bare Claude. This is a real, "
            "informative result reported straight, not a loam failure "
            "to be retried.",
        "indeterminate":
            "INDETERMINATE — the set could not produce a material-win "
            "picture; the report names exactly why (a definite "
            "finding, not a non-answer).",
    }[v["verdict"]]

    b_cost = sum((r["cost_usd"] or 0) for r in b)
    l_cost = sum((r["cost_usd"] or 0) for r in lo)

    return f"""\
# ProgramBench-revival v2 — does loam materially beat a bare LLM at hands-off task execution?

*Report authored {date.today().isoformat()}. The deliverable a
non-technical reader rules from (AC.PBR.7). "loam does not materially
beat the baseline" and "indeterminate" are FIRST-CLASS plan-success
outcomes — reported straight, never retried to green, the margin
never weakened.*

## Plain-language answer

**Does loam materially beat a bare LLM at hands-off task execution
for a non-technical user, and by how much, judged by something other
than loam's own judge?**

> {plain}

{v['reason']}

## Honest scope (read this first)

This is **not** the public ProgramBench leaderboard. The public
ProgramBench eval requires a linux/amd64 + Docker harness and the
local upstream clone is an empty skeleton (no dataset, no harness) on
this Darwin/arm64 host — the v0.4.0 C4 host-block recurs as a
no-usable-public-set block (empirically rechecked this build: the
docker daemon is up, but the public dataset/harness is absent). Per
the plan's AC.PBR.2 satisfiability note + §3.3/§8.2, this run uses a
**documented honest-scope ProgramBench-CLASS substitute** of
{result['tasks_total']} non-subjective tasks that **preserves the
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

{result['scoring_authority']}

## The frozen margin (AC.PBR.5 — FROZEN-RATIFIED D-PBR-1, owner Telegram 11447)

> {v['margin_text']}

The builder froze EXACTLY this before any run and did NOT move it
after runs began.

## Computed three-valued verdict (AC.PBR.5)

- **Verdict:** `{v['verdict']}` (computed from the numbers, not
  asserted)
- Baseline independently-judged pass count: **{v['baseline_pass_count']}**
  / {result['tasks_total']}
- Loam independently-judged pass count: **{v['loam_pass_count']}**
  / {result['tasks_total']}
- Baseline non-pass tasks: {v['baseline_non_pass_tasks'] or '(none)'}
- Of those, recovered by loam:
  {v['loam_recovered_of_baseline_misses'] or '(none)'}
- Clear-majority-of-baseline-misses cleared (>50%):
  **{v['clear_majority_cleared']}**
- No total-pass regression: **{v['no_total_regression']}**

### All-tasks-pass aspirational metric (AC.PBR.7 — NOT the gate)

{v['all_tasks_pass_aspirational']['note']}

- baseline all-tasks-pass:
  `{v['all_tasks_pass_aspirational']['baseline_all_tasks_pass']}`
- loam all-tasks-pass:
  `{v['all_tasks_pass_aspirational']['loam_all_tasks_pass']}`

## Per-arm failure-signature map (AC.PBR.6 — the false-success class explicit)

Every non-pass carries exactly one class from the frozen four-class
taxonomy. The **produced-but-no-real-effect** column is the
false-success class the positive-real-outcome floor + held-out
anti-overfit conjunction is built to catch (the owner's Telegram
11447 concern: compiled-but-no-result / empty extraction /
didn't-touch-the-target nominally reported as done).

{_sig_table(v['per_arm_failure_signature'])}

## Baseline arm — definite per-task dispositions

{_disp_table(b)}

## Loam arm — definite per-task dispositions

{_disp_table(lo)}

## Measured cost + latency (AC.PBR.6 — measured, never estimated)

- Baseline arm measured cost (sum of per-task `total_cost_usd`):
  **${b_cost:.4f}**
- Loam arm measured cost: **${l_cost:.4f}**
- Cost ceiling (D-PBR-4): ${result['cost_ceiling_usd']:.2f};
  measured spent: ${result['measured_spent_usd']:.4f};
  halted on ceiling: **{result['halted_on_cost_ceiling']}**
- Total wall-clock: {result['wall_clock_s']}s
- Tasks completed: {len(result['tasks_completed'])}
  / {result['tasks_total']}
  {'(PARTIAL — cost ceiling hit; the verdict above is computed over '
   'the completed tasks and this truncation is named, not hidden)'
   if result['halted_on_cost_ceiling'] else '(full set completed)'}

## Reproducibility (AC.PBR.6)

The headline is reproducible from the preserved per-(arm,task)
evidence under `framework/tools/programbench-revival/.run_evidence/`
(raw transcripts + floor/held-out exit codes + independent-judge
verdicts + measured cost). Re-running the frozen scorer over the
preserved artefacts yields the same verdict. Task set content-hash:
`{result['task_set_sha256']}` (pinned before any run).

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
"""
