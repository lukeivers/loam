# principle-foundation-structural-enforcement — Slice B — GATES — apply ladder

Second of four ordered slices under the candidate plan
`docs/plans/principle-foundation-structural-enforcement.md`. Baselines on
Slice A's seal (1b1d5d33). Delivers two structural gates that make
principle-discipline mechanical.

This amendment:
  1. AC.PFSE.3 — the four-research-question gate. Extends
     stages.check_gate's research stage with a deterministic
     section-presence check: a loam feature-research plan cannot advance
     until all four lens-research questions (Claude-leverage /
     Primary-persona / Harness / ODD) carry a non-empty section. NO LLM —
     the check is a parse. The gate is OPT-IN via a `lens_research: true`
     frontmatter flag so generic ODD research is NOT gated by the four
     loam-internal lens questions (feedback_odd_cdc_scope — the M5
     conflict with AC.OSS-M6.4's generic-ODD contract resolved by scope).
     The odd-research template gains the four sections + the flag.
  2. AC.PFSE.5 — the context-load gate. A new dev-sdlc PreToolUse sibling
     blocks dispatch (Task) + non-carve-out author (Edit/Write/MultiEdit)
     until the session's required design corpus is loaded. A DETERMINISTIC
     loaded-set predicate over the existing corpus-load sentinel's state
     {loaded,partial,missing} — NOT an LLM relevance judgment (plan
     halt-trigger 2, the §3.1 latency ruling). Dev-mode only; carve-out
     author edits (docs/scratch — how context loads) never gated;
     fail-open on a missing sentinel/session-id. Same two-tier
     _gate_helpers NDJSON-audit + dev-mode short-circuit + fail-open
     envelope (D-PFSE.4).
  3. Wires the context-load gate into bootstrapped workspaces via the A4
     precedent: first_run_helper._context_load_gate_stanzas (two matcher
     entries) + the first_run_settings marker. This is the ONE
     hands-off-lifecycle edit (wiring only). test_first_run's PreToolUse
     count assertion rebaselined 6->8 (ODD §4 in-band — Slice B extends
     the stanza list by two).

Out with named handoffs: the Stop-hook contributor framework + the
permission-ask/terminology-drift contributors + the AC.PFSE.2★
outcome-altitude fire (Slice C); slug-collision + the meta-decision-haiku
arbiter SKILL (Slice D).

NO public-action steps; NO Anthropic API key anywhere (every check is
deterministic parse/predicate). BASELINE = Slice A seal (confirmed at
apply); counter 189 next free; builder confirms both at apply time.
LOCAL only.
