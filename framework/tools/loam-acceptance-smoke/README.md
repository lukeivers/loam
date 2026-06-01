# loam-acceptance-smoke — the loam 1.0 acceptance gate

The non-tech-user end-to-end smoke. It drives the **real** production
`loam init` + first-run intake through three fully role-played non-technical
white-collar users, then judges the resulting end-state against loam's
prime-objective promise — per-user-tuned translation — on named orthogonal
dimensions.

Design: `docs/plans/loam-1.0-acceptance-smoke.md`.

## What it does

1. **Three role-play variants** (the three onboarding paths the pipeline was
   built to handle):
   - **A — real-estate agent** (idea-rich → zero research)
   - **B — claims adjuster** (day-derived → zero research)
   - **C — paralegal** (idea-vacuum → opt-in deep role-research, ≤3 round-trips)

   The user side of each conversation is an **isolated `claude -p`** that
   role-plays the persona and answers whatever the production intake actually
   asks, turn by turn (the prose briefs live in `scripts/variant_*.md`).

2. **The runner** instantiates a **throwaway** fresh loam workspace via the
   real `loam init`, runs the real `run_first_run_intake` orchestrator against
   an **isolated global home** (never the operator's `~/.claude`), and for the
   idea-vacuum variant wires the real `RoleResearchProvider` so the bounded
   deep-research subagent actually fires.

3. **The judge** scores each transcript on named dimensions
   (`no-user-translation-burden`, `learned-this-person`, `four-step-loop-ran`,
   `no-over-engineering`, `closed-on-one-thing`, `non-interrogating-feel`,
   `protection-floor-held`, plus the variant-specific deep-research dimension):
   deterministic assertions for the checkable ones, one isolated `claude -p`
   LLM-as-judge probe per soft dimension.

4. **The report** — per variant × dimension PASS/PARTIAL/FAIL with transcript
   evidence + the top-line 1.0 recommendation (READY / READY-WITH-GAPS /
   NOT-READY).

## Safety floor (non-negotiable)

Every `claude -p` — role-play AND judge — spawns ONLY through
`loam_spawn_isolation.spawn_isolated_claude` (`--strict-mcp-config` + empty MCP
config + `TELEGRAM_BOT_TOKEN`/`ANTHROPIC_API_KEY`-scrubbed env). This protects
the operator's single Telegram bot slot from being SIGTERM-stolen by an
un-isolated spawn loading the telegram plugin. No Anthropic API key —
subscription-only.

## Run it

```
loam-acceptance-smoke \
    --canonical /path/to/loam-tree \
    --out docs/experiments/loam-1.0-acceptance-smoke-run.md
```

Re-runnable + self-cleaning: each variant runs in a throwaway temp workspace +
isolated global home removed on exit; the only residue is the report.

## AC ladder (design §5)

- **AC.SMOKE.1** outcome-altitude — real `loam init` + real intake, zero
  pre-arranged state.
- **AC.SMOKE.2** the three variants produce materially-different seeds.
- **AC.SMOKE.3** deep-research only in variant C, within the ≤3 budget; A+B
  zero research.
- **AC.SMOKE.4** every rubric dimension scored per variant with cited evidence.
- **AC.SMOKE.5** re-runnable + self-cleaning throwaway workspace.

The hermetic ODD test suite (`tests/`) proves the harness logic offline; the
live LLM walk is the run-report (the priority deliverable).
