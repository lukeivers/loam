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

"""AC.RPB.7 — the REAL public ProgramBench verdict report a
non-technical reader rules from.

Renders the run result into
``docs/experiments/programbench-revival-real-pb.md``: both arms'
definite per-task disposition tables over the REAL public ProgramBench
subset (each task named by its real upstream instance-id + image
digest), each arm's independently-judged honest-coverage, the PER-ARM
FAILURE-SIGNATURE MAP (the false-success "produced-but-no-real-effect"
class explicit per arm), the FROZEN-RATIFIED margin + the k_min
small-k floor, the computed three-valued verdict, the all-tasks-pass
aspirational metric LABELLED NOT the gate, measured cost + the
agent-vs-eval-emulation wall-clock split, an EXPLICIT statement that
this is the REAL public ProgramBench (a different/harder artefact than
the v2 substitute), the n=1-per-task limitation in plain language, and
a plain-language answer — OR a definite honest-negative / indeterminate
naming WHY.
"""

from __future__ import annotations

from datetime import date


def _disp_table(rows: list[dict]) -> str:
    out = [
        "| Task | Instance ID | Passed | Judge tag (independent) | "
        "Upstream graded score | n_resolved/n_tests | error_code | "
        "Floor θ | Failure class | Cost USD | Agent wall s | "
        "Eval-emul wall s |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        out.append(
            f"| {r['task_id']} | `{r['instance_id']}` "
            f"| {'PASS' if r['passed'] else 'non-pass'} "
            f"| {r['judge_tag']} | {r['upstream_score']} "
            f"| {r['upstream_n_resolved']}/{r['upstream_n_tests']} "
            f"| {r['upstream_error_code'] or '—'} "
            f"| {r['floor_theta']} "
            f"| {r['failure_class'] or '—'} "
            f"| {r['cost_usd'] if r['cost_usd'] is not None else 'n/a'} "
            f"| {r['agent_wall_clock_s']} "
            f"| {r['eval_emulation_wall_clock_s']} |"
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
            "YES — on this digest-pinned subset of the REAL public "
            "ProgramBench, the real sealed hands-off loop materially "
            "beat a bare Claude, judged by an independent held-out "
            "judge (not loam's own) grounded in the real upstream "
            "test suite.",
        "loam-does-not-materially-beat-baseline":
            "NO — on this REAL public ProgramBench subset, the "
            "harness did NOT materially beat a bare Claude. This is a "
            "real, informative result on the benchmark that matters, "
            "reported straight, not a loam failure to be retried.",
        "indeterminate":
            "INDETERMINATE — the REAL public ProgramBench subset "
            "could not produce a determinate material-win/loss "
            "picture; the report names exactly why (a definite "
            "finding, not a non-answer — including the k_min small-k "
            "floor correctly forcing indeterminate on a degenerate "
            "baseline-miss denominator, the named v2 task-#44 fix).",
    }[v["verdict"]]

    b_cost = sum((r["cost_usd"] or 0) for r in b)
    l_cost = sum((r["cost_usd"] or 0) for r in lo)
    b_agent_wall = sum(r["agent_wall_clock_s"] for r in b)
    l_agent_wall = sum(r["agent_wall_clock_s"] for r in lo)
    eval_wall = sum(
        r["eval_emulation_wall_clock_s"] for r in (b + lo)
    )

    return f"""\
# ProgramBench-revival (REAL public ProgramBench) — does the real sealed loop materially beat a bare LLM on the REAL benchmark, judged independently?

*Report authored {date.today().isoformat()}. The deliverable a
non-technical reader rules from (AC.RPB.7). "loam does not materially
beat the baseline on the real benchmark" and "indeterminate" are
FIRST-CLASS plan-success outcomes — reported straight, never retried
to green, the FROZEN margin never weakened.*

## Plain-language answer

**Does loam materially beat a bare LLM at hands-off task execution
for a non-technical user ON THE REAL PUBLIC PROGRAMBENCH, by how much,
judged by something other than loam's own judge?**

> {plain}

{v['reason']}

## This is the REAL public ProgramBench (read this first) — NOT the v2 substitute

{result['v2_substitute_relationship']}

This measurement ran against a **digest-pinned subset of the REAL
public ProgramBench task images** ({result['tasks_total']}
instances), scored by the **REAL upstream `programbench eval`**
(`{result['upstream_eval']['clone_head']}`) consuming the **REAL
HuggingFace `{result['hf_dataset']}` blobs** (snapshot
`{result['hf_revision_snapshot']}`) under `linux/amd64` Docker
emulation. The §9 correction of the v2 false host-block premise is
recorded in `docs/STATE.md` and `docs/release-roadmap.md`: the v2
"public ProgramBench host-block recurs" claim was an inherited
8-day-old precedent treated as current reality and is **Tier-0-refuted
by the builder's own live 2026-05-16 recheck** (Docker up, the real
`:task` images present + amd64-emulation-runnable, the upstream clone
fully populated, the HF dataset cached). The v2 substitute number is
**not** a real-PB result and is **not** cited as one here.

## The scoring authority (AC.RPB.3)

{result['scoring_authority']}

The independent judge is grounded in the **REAL upstream
`*.eval.json` graded test-suite result** (`score = n_resolved /
len(test_results)`; `compile_failed` ⇒ 0.0) **plus the frozen
per-task positive-real-outcome floor threshold θ** — never the arm's
friendly summary.

## The frozen margin (AC.RPB.5 — FROZEN-RATIFIED D-PBR-1 + the k_min small-k floor / D-RPB-1)

> {v['margin_text']}

The builder froze EXACTLY this before any run and did NOT move it
after runs began. The **`k_min = {v['k_min']}` small-k floor** is the
named v2 task-#44 / PB3 degenerate-denominator defect fix: v2's rule
forced indeterminate only at *exactly* 0 baseline misses; this
real-PB rule forces verdict (c) indeterminate at `< k_min` baseline
misses — a degenerate OR near-degenerate denominator can never read
as a determinate loss/win.

## Computed three-valued verdict (AC.RPB.5 — computed, not asserted)

- **Verdict:** `{v['verdict']}`
- Baseline independently-judged pass count:
  **{v['baseline_pass_count']}** / {result['tasks_total']}
- Loam independently-judged pass count:
  **{v['loam_pass_count']}** / {result['tasks_total']}
- Baseline non-pass tasks: {v['baseline_non_pass_tasks'] or '(none)'}
- Baseline-miss denominator: **{v['baseline_miss_count']}**
  (frozen `k_min` = {v['k_min']}; below k_min:
  **{v['baseline_miss_below_k_min']}**)
- Of the baseline's misses, recovered by loam:
  {v['loam_recovered_of_baseline_misses'] or '(none)'}
- Clear-majority-of-baseline-misses cleared (>50%):
  **{v['clear_majority_cleared']}**
- No total-pass regression: **{v['no_total_regression']}**

### All-tasks-pass aspirational metric (AC.RPB.7 — NOT the gate)

{v['all_tasks_pass_aspirational']['note']}

- baseline all-tasks-pass:
  `{v['all_tasks_pass_aspirational']['baseline_all_tasks_pass']}`
- loam all-tasks-pass:
  `{v['all_tasks_pass_aspirational']['loam_all_tasks_pass']}`

## Per-arm failure-signature map (AC.RPB.6 — the false-success class explicit)

Every non-pass carries exactly one class from the frozen four-class
taxonomy. The **produced-but-no-real-effect** column is the
false-success class the positive-real-outcome floor (the real
upstream graded eval at θ) is built to catch: a `compile_failed` /
empty / hollow submission that nominally reports done but passes ~0
real upstream tests.

{_sig_table(v['per_arm_failure_signature'])}

## Baseline arm — definite per-task dispositions (REAL public ProgramBench)

{_disp_table(b)}

## Loam arm — definite per-task dispositions (REAL public ProgramBench)

{_disp_table(lo)}

## Measured cost + the agent-vs-eval-emulation wall-clock split (AC.RPB.6 / D-RPB-4 — measured, never estimated)

- Baseline arm measured cost (sum of per-task `total_cost_usd`):
  **${b_cost:.4f}**
- Loam arm measured cost: **${l_cost:.4f}**
- Cost ceiling (D-RPB-4): ${result['cost_ceiling_usd']:.2f};
  measured spent: ${result['measured_spent_usd']:.4f}
- Wall-clock ceiling (D-RPB-4): {result['wall_ceiling_s']:.0f}s;
  measured total wall-clock:
  {result['measured_total_wall_clock_s']}s
- **Agent wall-clock** (baseline {b_agent_wall:.0f}s + loam
  {l_agent_wall:.0f}s) vs **real upstream eval-emulation wall-clock**
  ({eval_wall:.0f}s) — recorded DISTINCTLY (F2 §10.3: the real-eval
  amd64-emulation leg is the wall-clock-heavy leg, not the agent).
- Halted on ceiling: **{result['halted_on_ceiling']}**
  {('— halt reason: ' + result['halt_reason'] +
    ' — the verdict above is computed over the COMPLETED tasks and '
    'this truncation is NAMED, not hidden; the picture is '
    'partial-but-DEFINITE (§8.6, never silently truncated/downscoped)'
    ) if result['halted_on_ceiling'] else
   '(full subset completed within the measured ceiling)'}
- Tasks completed: {len(result['tasks_completed'])}
  / {result['tasks_total']}

## Reproducibility (AC.RPB.6)

The headline is reproducible from the preserved per-(arm,task)
evidence under
`framework/tools/programbench-revival/realpb/.run_evidence/` — raw
transcripts + the **REAL upstream `*.eval.json` artefacts** (the
`test_results` + graded score + `error_code`) + independent-judge
verdicts + measured cost + the agent/eval wall-clock split.
Re-running the frozen scorer over the preserved `*.eval.json` +
transcripts yields the same verdict. Frozen task-set content-hash:
`{result['task_set_sha256']}` (pinned before any run).

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
"""
