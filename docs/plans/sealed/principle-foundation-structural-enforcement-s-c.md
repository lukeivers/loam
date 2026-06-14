# principle-foundation-structural-enforcement — Slice C — STOP CONTRIBUTOR FRAMEWORK — apply ladder

Third of four ordered slices under the candidate plan
`docs/plans/principle-foundation-structural-enforcement.md`. Baselines on
Slice B's seal (0aaf7763). Builds the Stop-hook contributor framework
fresh and lands the two own-behaviour contributors.

This amendment:
  1. Builds the Stop-hook contributor FRAMEWORK fresh (D-PFSE.3 / RF-2 —
     no contributor registry existed; the prior cli_stop is
     single-purpose memory-write). stop_contributor.py carries the
     StopContributor Protocol + StopAdvisory + an ordered registry
     (register/compose, duplicate-name reject, fail-soft per
     contributor) + build_stop_output (systemMessage ONLY, never
     decision:block) + run_stop_contributors (fail-soft production
     entry). The Stop-output contract was confirmed against the Claude
     Code Stop-hook docs.
  2. Ships the two contributors (stop_contributors_builtin.py):
     permission_ask (AC.PFSE.4 — a closing-line permission-ask on
     authorized work, closing-region-scoped so a mid-reply clarifying
     question is not flagged) + terminology_drift (AC.PFSE.7 — a
     built/sealed/merged claim whose named SHA the git ref graph does
     not contain; PARTIAL, fail-open when git unavailable). Both
     deterministic; NO LLM on the Stop hot path.
  3. Wires the framework into cli_stop AFTER the memory-write pipeline,
     fail-soft — preserving the exit-0-always + fast-return contract
     (AC.M.4, stop_emitter:478, plan halt-trigger 1). Any error returns
     None / is swallowed.
  4. ★ AC.PFSE.2★ (outcome-altitude): a real persona-CLI `stop`
     subprocess fire of a permission-ask reply through the production
     Stop envelope path, NO pre-arranged state, yields the systemMessage
     advisory + rc 0; a clean reply emits empty stdout.

Out with named handoff: slug-collision detection + the
meta-decision-haiku arbiter SKILL (Slice D).

NO public-action steps; NO Anthropic API key anywhere. BASELINE = Slice B
seal (confirmed at apply); counter 190 next free; builder confirms both
at apply time. LOCAL only.
