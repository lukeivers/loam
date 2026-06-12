# Claude-leverage program Slice 1 — CURRENCY — apply ladder

First of four slices under the master plan
`docs/plans/claude-leverage-program.md` (program ratified 2026-06-11;
D-CLP.4 owner-RATIFIED Discord 1514753768175042771; D-CLP.3 + D-CLP.5
delivered by this slice). Root cause fixed first: the Lens-1 reference
surface went 7 weeks stale and factually wrong on a load-bearing claim
(gap analysis 2026-06-11 §3.1 — "subagents cannot spawn other
subagents" vs Claude Code 2.1.172's 5-level recursion), because the
locked-2026-04-26 δ refresh automation never shipped and two parallel
reference surfaces drifted apart.

This amendment:
  1. Corrects the recursion claim in the Class A corpus
     (docs/capability-corpus/claude-code/background-agents.md,
     re-verified live at build) and sweeps the repo for contradicting
     reference text (AC.CLP-CUR.1).
  2. Demotes docs/CLAUDE_CAPABILITIES.md in place to an index/redirect
     over docs/capability-corpus/ — exactly one canonical
     capability-reference surface remains (AC.CLP-CUR.2, D-CLP.5).
  3. Lands framework/tools/capability-refresh/ (NEW component,
     first-seal): deterministic Class A projection from a data-declared
     source manifest; structured delta; auto-land vs review-flag
     partition per D-CUR.4 (new claims / removals / overlay touches /
     contradictions NEVER auto-land — the protection-floor guard);
     source_fetch_ts stamping + stale-marking on fetch failure
     (AC.CLP-CUR.3/5/6); no-cross-class-write — Class B is structurally
     untouched (AC.CLP-CUR.7, locked §7bis.3 invariant).
  4. Binds the unattended cadence for the canonical repo: cloud routine
     primary (live-verified at build; no machine awake; no API key),
     shipped launchd-plist fallback recorded in plan §14 if the
     verification says no (D-CUR.2).
  5. ★ AC.CLP-CUR.4 (outcome-altitude): observed over the first real
     post-seal cadence cycle — an upstream change lands in the corpus
     or a surfaced pending-delta with no manual trigger; the roadmap
     row carries a pending-observation marker until green.

Deferred with named handoffs (plan §7): gap-analysis §3.2
(claude-feature-awareness skill — pos3 surface, fixed by Slice 2
graduation) and §3.3 (loam-skills README count — Slice 2 owns that
fence and rewrites the README). β MCP knowledge-server and Class B
accrual stay out per master §7.

NO public-action steps; NO Anthropic API key anywhere (any LLM-routed
step uses claude -p via the house client with spawn isolation).
BASELINE 266aa93c — HEAD at sub-plan authoring; counter 184 next free;
builder confirms both at apply time.
