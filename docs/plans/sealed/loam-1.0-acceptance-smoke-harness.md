# loam 1.0 acceptance smoke — harness build + first run — apply ladder

The 1.0 acceptance gate (design:
`docs/plans/loam-1.0-acceptance-smoke.md`). A NET-NEW reusable
acceptance-test component that answers the owner's question in the
owner's terms: does a freshly-instantiated loam deliver its
prime-objective promise — per-user-tuned translation — to a genuinely
non-technical white-collar user told only "use this to get more
efficient"?

It is an OUTCOME-ALTITUDE test: it drives the REAL production `loam init`
+ the REAL first-run intake (run_first_run_intake) through a full
role-played conversation per variant, with the user side supplied by an
isolated `claude -p`, then judges the END STATE against the
VALUE_PROPOSITION rubric on named orthogonal dimensions — NOT a unit test
of inner modules.

The three variants exercise the three onboarding paths the pipeline was
built to handle: A (idea-rich real-estate agent) and B (day-derived
claims adjuster) reach ZERO research; C (idea-vacuum paralegal) is the
NEED-trigger for the opt-in deep-role-research, bounded to the sealed
≤3 round-trip / ≤3 idea caps. The judge runs deterministic checks where
checkable (seed written? cross-variant seeds differ? budget respected?
deep-research fired only in C?) and one isolated `claude -p` LLM-as-judge
probe per soft dimension (no-user-translation-burden / learned-this-person
/ four-step-loop-ran / no-over-engineering / closed-on-one-thing /
non-interrogating-feel / protection-floor-held).

THE SAFETY FLOOR (non-negotiable, design F-5): every `claude -p` — the
role-played user side AND every judge probe — spawns ONLY through
`loam_spawn_isolation.spawn_isolated_claude` (--strict-mcp-config + empty
MCP config + TELEGRAM_BOT_TOKEN/ANTHROPIC_API_KEY-scrubbed env), so an
un-isolated spawn cannot SIGTERM-steal the operator's single Telegram bot
slot. No Anthropic API key — subscription-only. Throwaway self-cleaning
workspace + isolated global home; the operator's real `~/.claude` is never
written.

FIRST-RUN VERDICT: NOT-READY. The infrastructure is sound (real init exit
0 every variant; 28 spawns all isolated; seeds written; self-clean held),
but the smoke caught four real production bugs in the intake's
natural-language handling, all in
`framework/workspace-bootstrap/.../translate_in_intake.py`: (1) the
proposal echo pastes the user's whole raw reply into a template slot;
(2) the affirmation parser fails on natural replies with trailing
punctuation ("Yeah, ..."), which suppressed variant C's deep-research
opt-in despite the user accepting it; (3) the idea-vacuum classifier is a
brittle keyword match that mis-routed variant B; (4) the role-mined
leverage close leaves the role-noun slot unresolved. Full evidence +
root-cause + fix shape:
`docs/experiments/loam-1.0-acceptance-smoke-run.md`. The harness is
re-runnable; the owner re-runs it as the tail of the 1.0 queue lands the
fixes.
