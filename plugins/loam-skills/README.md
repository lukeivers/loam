# Loam Skills plugin for loam

Twenty-six SKILL.md packages: loam's load-bearing translation
patterns, a cluster of per-primitive auto-loaders for Claude Code's
scheduling / background / hook surface, the three-skill
dispatch-decision discipline (catalogue → decide → record), and the
meta-decision-haiku borderline-rule arbiter. Discoverable by Claude
Code via the standard `<plugin>/skills/<skill-name>/SKILL.md`
filesystem walk. Composes with raw Claude Code — a stranger can
install this plugin and benefit from loam's patterns without
committing to the full harness.

The skill count above is derived from disk: every subdirectory of
`skills/` that contains a `SKILL.md` file.

## What this plugin contains

Twenty-six packaged skills in `skills/<skill-name>/SKILL.md` shape,
in three clusters.

### Translation-pattern skills

These capture loam's load-bearing translation patterns — the persona
applies them alongside conversation.

- **`memory-recall`** — when prior-session context is needed,
  retrieve from loam's file-based memory store (or graceful-degrade
  for raw Claude Code: look in standard memory locations).
- **`scope-decompose`** — when a task can be partitioned into
  subtasks each with a tighter acceptance criterion, decompose.
  Codifies loam's F3 swarming stopping criterion.
- **`dispatch-with-gates`** — when invoking a sub-agent, pass
  objective + scope + constraints + halt triggers + ODD-check ONLY.
  Never enumerate files / symbols / ACs / layouts in dispatch
  prompts.
- **`onboarding-conversation`** — when a user-facing session opens
  fresh, greet with what's in flight + what needs attention + what
  completed. The primary-persona greeting shape, externalized.
- **`session-handoff`** — when a session is about to close (or a
  long task is being deferred), capture pending items to a durable
  surface. Prevents "I'll remember next session" failures.
- **`audit-block-on-telegram`** — closing audit block on every
  Telegram reply per the principle-application discipline.
- **`time-claims-discipline`** — verify every time-related claim
  before stating it; translate human-developer-time to AI-time at
  citation.
- **`translation-discipline`** — outbound communication shape:
  prose first, no SHAs / AC-IDs / agent-IDs / un-introduced
  abbreviations.
- **`owner-decision-summary`** — every plan/research artefact gets
  a summary + named-decisions-with-recommendations.
- **`skill-capture-proposal`** — when a pattern recurs and would
  benefit from being externalized, propose a new SKILL.
- **`cost-optimised-defaults`** — when loam cost is the concern,
  apply the cost-cutting defaults.
- **`strategic-compact`** — the `/compact`-vs-`/clear` decision
  heuristic by context-band and arc state.

### Per-primitive auto-loaders

Each fires on a specific Claude Code (or loam-CLI) primitive's
work-shape so Claude's auto-loader picks the right one when the
matching dispatch shape appears.

- **`monitor-tool`** — watching a long-running local subprocess
  for completion or event streams (event-driven local wait).
- **`run-in-background-bash`** — backgrounding a Bash call with
  fire-on-exit notification (`run_in_background: true`).
- **`schedule-wakeup`** — polling external state I can't event-
  stream OR long idle ticks (clock-based one-shot wake).
- **`cron-create`** — scheduled work at specific times, session-
  scoped (5-field cron expression).
- **`loop-command`** — self-paced iteration with judge (the
  `/loop` slash command).
- **`goal-command`** — goal-directed multi-step with autonomous
  halt (the `/goal` slash command).
- **`launchd-plist`** — durable cross-session scheduling on macOS
  that survives Claude sessions.
- **`claude-agents-view`** — native `claude agents` view of
  background-agent inventory.
- **`precompact-hook`** — PreCompact hook event (fires before
  auto-compaction; can block via exit-code-2).
- **`handsoff-loop`** — loam's packaged build methodology as one
  capability the persona invokes for the user.

### Dispatch-decision discipline (catalogue → decide → record)

The three-skill trio for picking the right primitive at dispatch
time. Graduated from workspace prototypes into canonical loam by the
DOCTRINE slice of the claude-leverage program; each carries no
independently-maintained capability claims — they route to or record
against the refresh-kept capability corpus (`docs/capability-corpus/`).

- **`claude-feature-awareness`** — the catalogue lookup: maps a
  work-shape to the corpus entry that describes the matching
  primitive. Carries no capability claims of its own — pure routing
  into the maintained corpus.
- **`tool-selection-rubric`** — the seven-decision framework that
  picks WHICH primitive. Capability facts stay in the corpus; the
  rubric decides.
- **`primitive-rationale-check`** — records WHY a non-default (or
  bespoke) primitive was chosen, as a `primitive-rationale:` audit
  line. The dispatch-time primitive-check guard (a dev-sdlc
  PreToolUse `Task` hook) structurally enforces this line's presence
  on bespoke-equivalent dispatches.

- **`meta-decision-haiku`** — the impartial borderline-rule arbiter
  (the operational arbiter for loam's M5 principle-conflict
  resolution). When the persona hits a genuinely borderline
  meta-decision on a BOUNDED trigger list (plan-doc needed? real
  principle-conflict? scope-only or method-smuggling? verified or
  guess? in-scope-authorized or owner-gated?), it calls a neutral
  Haiku model via `claude -p` (the subscription path, NO API key) to
  rule from a standpoint with no stake in the next action. Bounded +
  off the per-action hot path by design — a tiebreaker, not a gate.
  Packaged by the principle-foundation-structural-enforcement
  candidate (AC.PFSE.8), filling the slot the sealed loam-skills
  root-cause ruling held open.

## How skills are discovered

Per Anthropic's SKILL.md schema
(https://code.claude.com/docs/en/skills), Claude Code walks
`<plugin>/skills/<skill-name>/SKILL.md` files when the plugin is
enabled in the workspace. No bootstrap-time wiring required from
loam's side — Claude Code's native discovery mechanism handles it.
Each skill is invocable via `/<skill-name>` or auto-loaded by
Claude when the description matches the user's intent.

## Install

From the loam source clone (v0.1.0 source-only release), append to
the install-from-source flow:

```bash
pip install -e ./plugins/loam-skills
```

The plugin is included in the canonical
`pip install -r install-from-source.txt` walk under "Tier K — Loam
Skills plugin" (see top-level `install-from-source.txt`).

## Composes with

- **Loam's primary persona** — the persona uses these skills
  natively when its description matches the turn intent. The
  persona's CLAUDE.md and prompt-template surfaces don't need to
  re-derive the patterns (they live in the SKILL.md files).
- **Raw Claude Code** — strangers running `claude` without loam
  installed can enable this plugin alone and benefit from the
  patterns. Each loam-pattern skill's "Graceful degradation" section
  names the raw-Claude-Code path.
- **The capability corpus** (`docs/capability-corpus/`) — the
  dispatch-decision trio routes to and records against the
  refresh-kept corpus rather than caching capability claims.
- **Loam Dev/SDLC plugin** (`plugins/dev-sdlc/`) — the
  `start-project` skill there is task-shaped (kicks off a project);
  these are reference-content shaped (knowledge applied alongside
  conversation). Different roles, complementary surfaces.

## v0.2 trajectory

These packages will publish to PyPI alongside the loam
component family at v0.2 (per v0.1.x roadmap §3 deferred items).
At that point, install becomes:

```bash
pip install loam-plugin-loam-skills
```

Until then, source-only via `install-from-source.txt`.

## Reference

- Anthropic SKILL.md schema:
  https://code.claude.com/docs/en/skills
- Loam design lenses (Lens 1 — Claude-leverage-first):
  `framework/CLAUDE.md` (canonical pos-v2 only) /
  `CLAUDE.md` (in loam workspaces).
- F3 swarming principle (codified in `scope-decompose`):
  `~/.claude/projects/<project>/memory/feedback_swarming_recursive_decomposition.md`
  (when loam memory is loaded).
