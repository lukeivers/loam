# loam ↔ Claude-primitives integration review

**Date:** 2026-05-31 · **Scope:** READ-ONLY review (nothing changed) ·
**Author:** dispatched research agent (Opus)

This review answers five questions about how loam interacts with Claude
Code / Claude primitives: (1) the refreshed primitive surface, (2) what
loam actually uses, (3) empirical skill-usage telemetry, (4) underused
high-leverage primitives, (5) prioritized recommendations. Every
primitive-semantics claim is doc-cited (Tier-0); every usage claim cites
a file path; every telemetry count is a real grep over transcripts.

---

## TL;DR (the three load-bearing findings)

1. **The skills are not just under-invoked — in pos3 they are
   structurally invisible.** Across **28 pos3 transcripts (613 MB)** and
   **158 loam-repo transcripts (5.7 MB)**, loam-authored skills have been
   invoked via the Skill tool **exactly 0 times**. Across **every project
   on the machine**, the Skill tool has fired **3 times total**, all
   built-in commands (`usage`, `update-config`, `schedule`). The ~40
   loam skills under `plugins/loam-skills` + `plugins/dev-sdlc` are **not
   installed as a plugin and not in any marketplace** — only the
   `telegram` plugin is installed (`~/.claude/plugins/installed_plugins.json`).
   So in a **pos3 session** they never even appear in the skill
   availability list (verified: the `skill_listing` names array in pos3
   transcripts contains only the 5 pos3-local skills + built-ins). In a
   **loam-repo session** they ARE surfaced (symlinked into
   `loam/.claude/skills/`) — and *still* were invoked 0 times. Luke's
   intuition (a) is correct and then some.

2. **Luke's "dozens or hundreds of primitives" framing is wrong on
   count but right on instinct.** The real Claude Code primitive surface
   is a **bounded, catalogued set**: **30 hook events** (not hundreds),
   **5 hook handler types**, **~6 scheduling/iteration primitives**, the
   skill/subagent/MCP/plugin systems, and a handful of session tools.
   The whole catalogue fits on two screens (Section 1). The right frame
   is not "we're using 5 of hundreds" — it's "the catalogue is ~40 named
   things; loam uses the structural-enforcement half heavily and the
   skill/scheduling half barely."

3. **loam's hook usage is genuinely strong — better than the framing
   implies.** pos3 wires **5 of the 30 hook events** with **~24 distinct
   hook handlers** (Section 2), including `PreCompact` (added tonight).
   The Agent tool fired **781 times** in pos3 — background-agents-by-default
   is real and heavily exercised. The gap is not "loam ignores primitives";
   it's specifically **skills + the scheduling/iteration family
   (`/goal`, `/loop`, Routines, Monitor)** that are authored-but-unused.

---

## 1. Refreshed primitive surface (Tier-0, doc-cited)

Source: `https://code.claude.com/docs/en/hooks`, `/en/skills`, `/en/goal`,
`/en/scheduled-tasks` — fetched 2026-05-31.

### 1a. Hook events — now 30 (was 29 in our mid-May catalogue)

Full catalogue per the live hooks doc:

```
SessionStart, Setup, UserPromptSubmit, UserPromptExpansion, PreToolUse,
PermissionRequest, PermissionDenied, PostToolUse, PostToolUseFailure,
PostToolBatch, Notification, MessageDisplay, SubagentStart, SubagentStop,
TaskCreated, TaskCompleted, Stop, StopFailure, TeammateIdle,
InstructionsLoaded, ConfigChange, CwdChanged, FileChanged, WorktreeCreate,
WorktreeRemove, PreCompact, PostCompact, Elicitation, ElicitationResult,
SessionEnd
```

**NEW since our mid-May catalogue:** `MessageDisplay` (fires while
assistant message text is displayed). Our internal
`claude-feature-awareness` SKILL lists 29 and omits `MessageDisplay` —
that's the one delta. Everything else our catalogue had is still present
and correctly named.

### 1b. Hook handler types — 5 (unchanged)

`command`, `http`, `mcp_tool`, `prompt`, `agent` (agent = experimental).
Async flags: `async`, `asyncRewake` (implies async, wakes Claude on
exit-code 2). Our catalogue is accurate here.

### 1c. "Goal" and "Loop" — what Luke named (pinned down)

Both are **session-keep-running iteration primitives**, NOT schedulers.

| | `/goal` | `/loop` |
|---|---|---|
| Introduced | **v2.1.139** (2026-05-12) — genuinely new since mid-May | pre-existing |
| Next turn starts when | previous turn finishes | a time interval elapses |
| Stops when | a **fresh Haiku evaluator** confirms the condition is met | you stop it, or Claude decides it's done |
| Mechanism | **a wrapper around a session-scoped prompt-based Stop hook** | interval re-run |
| Scope | one goal per session; restored on `--resume` (timer/turns reset) | session |
| Runs in | interactive, `-p`, desktop, Remote Control | interactive, `-p` |

**The sharp finding here (F2 below):** the docs state plainly that
`/goal` "is a wrapper around a session-scoped prompt-based Stop hook" —
Haiku evaluator after each turn, yes/no + reason, "no" feeds the reason
back as guidance. **loam already hand-rolls exactly this** in
`/Users/lukeivers/pos3/.claude/hooks/autonomy_continuation.py` (a Stop
hook). `/goal` is the platform-native, Haiku-evaluated, condition-driven
version of loam's autonomy-continuation machinery.
Sources: [/en/goal](https://code.claude.com/docs/en/goal),
[explainx.ai on v2.1.139](https://explainx.ai/blog/claude-code-goal-command-long-running-agents-2026).

### 1d. Scheduling family (Tier-0)

Four ways to run work, two axes (in-session vs independent):

- **In-session keep-running:** `/goal` (condition), `/loop` (interval),
  Stop hook (custom), Monitor tool (watch a command for completion).
- **Independent of any session:** **Routines** (Anthropic-cloud, research
  preview since 2026-04-14, min interval **1h**, created at
  `claude.ai/code/routines` or `/schedule` CLI, also API/GitHub-event
  triggerable — every routine gets its own endpoint + auth token);
  desktop scheduled tasks (local, min 1m); `CronCreate` (session-scoped
  despite `durable:true` — loam's empirical finding, task #77); `launchd`
  (durable cross-session, the loam reference path).
Sources: [/en/scheduled-tasks](https://code.claude.com/docs/en/scheduled-tasks),
[claude.com/blog/introducing-routines-in-claude-code](https://claude.com/blog/introducing-routines-in-claude-code).

### 1e. SKILL frontmatter levers (Tier-0 — full field list)

Per `/en/skills`, the available frontmatter fields are:
`description`, `disable-model-invocation`, `user-invocable`,
`allowed-tools`, `disallowed-tools`, `model`, `effort`, `context`
(set to `fork`), `agent` (subagent type when forked), `hooks`, `paths`
(glob-gated auto-load), `shell`.

**Auto-load mechanism (load-bearing):** a skill's *description* is what's
in context; Claude auto-loads the *body* "when relevant" by matching the
conversation against the description — OR `paths:` gates auto-load to
matching files — OR the user types `/skill-name`. There is **no other
trigger**. A skill with only a `description` and no `paths` relies 100%
on Claude judging the conversation relevant to the description.

---

## 2. What loam actually uses (per-category, file-cited)

| Primitive | Status | Evidence |
|---|---|---|
| **SessionStart hook** | **USED** | `pos3/.claude/settings.json`: 3 handlers (pos_session_start.py, primary_persona session-start, compaction_discipline_reinject) |
| **UserPromptSubmit hook** | **USED (heavy)** | 6 handlers: inject_local_time, primary_persona, principle_reminder, autonomy_baseline_reset, queue_status_inject, intent_classifier_inbound |
| **Stop hook** | **USED (heavy)** | 5 handlers: primary_persona stop, channel_rule_check, agent_outcome_capture, trait-reflection-stop, **autonomy_continuation** (the hand-rolled /goal) |
| **PreToolUse hook** | **USED (heavy)** | matchers for `mcp__...telegram__reply` (5 handlers), `Edit`, `Write`; global `~/.claude` adds Bash matcher (claude_spawn_isolation_guard) + keep_pace |
| **PreCompact hook** | **USED (new, tonight)** | `pos3/.claude/settings.json` PreCompact → compaction_discipline_reinject.py. Confirms brief note. |
| **Hook handler types** | **PARTIAL** | Only `command` type used. `prompt`/`agent`/`http`/`mcp_tool` handlers: 0 used (all are `"type":"command"`). |
| **Agent / Task (background)** | **USED (very heavy)** | **781** `"name":"Agent"` calls in pos3 transcripts. Background-agents-by-default is real. |
| **Monitor tool** | **USED (light)** | 9 invocations in pos3 transcripts |
| **CronCreate** | **USED (light)** | 2 invocations; loam knows it's session-only (task #77) |
| **launchd** | **USED** | `pos3/Library/LaunchAgents/com.loam.pos3.places-audit.plist` (referenced in awareness SKILL) |
| **MCP** | **USED** | telegram plugin MCP (only installed plugin); Gmail/Calendar/Drive/computer-use MCPs available |
| **Skills (auto-load)** | **AUTHORED, NOT INVOKED** | ~40 skills on disk; **0** Skill-tool invocations ever (Section 3) |
| **`/goal`** | **NOT USED** | 0 real command invocations (all "/goal" string hits in transcripts are skill-description prose or goals.md paths). loam reimplements it as a Stop hook instead. |
| **`/loop`** | **NOT USED** | 0 real invocations (all hits are doc/skill-description prose) |
| **Routines (cloud)** | **NOT USED** | No routine config; no `/schedule` use; only launchd for durable scheduling |
| **`prompt`/`agent` hook handlers** | **NOT USED** | inline-LLM-as-judge + subagent-as-hook unused |
| **SubagentStart/Stop, PostToolUseFailure, Notification, TaskCreated/Completed, InstructionsLoaded hooks** | **NOT USED** | settings.json wires none of these events |
| **Skill frontmatter levers** | **NOT USED (1 exception)** | Of ~40 skills, only `start-project` has any field beyond `description` (it sets `name`). **Zero use** of `paths:`, `model:`, `context:fork`, `effort:`, `allowed-tools:`, `disable-model-invocation:`. |
| **Plugin install/marketplace** | **PARTIAL** | loam skills/agents packaged as plugin *directories* but no `.claude-plugin/marketplace.json` exists; not installed as plugins; only `telegram` installed. |

---

## 3. SKILL telemetry — the load-bearing finding (real greps)

**Method:** `grep '"name":"Skill","input":{...}'` over every `.jsonl`
transcript, extracting the `skill` arg. Skill auto-loads and explicit
`/skill` invocations both surface as Skill tool_use entries. Counts are
real, not estimates.

**Grand total, every project on the machine:** 3 Skill-tool invocations,
all built-in: `usage` ×1, `update-config` ×1, `schedule` ×1.
**loam-authored skills: 0 invocations, anywhere, ever.**

| Skill | Location | Auto-load condition | Surfaced in session list? | Invoked (real count) | Why unused |
|---|---|---|---|---|---|
| claude-feature-awareness | pos3/.claude/skills | description-match only (no `paths:`) | pos3: **yes** | **0** | Description-match never fired; persona consults the file directly instead of via Skill tool |
| tool-selection-rubric | pos3/.claude/skills | description-match only | pos3: **yes** | **0** | Same — dispatch decisions made inline, rubric never auto-loaded |
| primitive-rationale-check | pos3/.claude/skills | description-match only | pos3: **yes** | **0** | Same |
| handsoff-loop (pos3) | pos3/.claude/skills | description-match only | pos3: **yes** | **0** | "build me X and verify" intent never triggered an auto-load; build work routed through Agent dispatches directly |
| log-visit | pos3/.claude/skills | description-match (visit-log shapes) | pos3: **yes** | **0** | Trigger shape may not have occurred in these sessions, OR persona handled inline |
| **~38 loam-skills + dev-sdlc skills** | loam/plugins/... (symlinked into loam/.claude/skills) | description-match only | **pos3: NO** (not installed); loam-repo: **yes** | **0** | In pos3: structurally invisible (not installed as plugin). In loam-repo: surfaced but description-match never fired once across 158 transcripts. |

**Two distinct failure modes, not one:**

- **Mode A — structural invisibility (pos3):** the 38 framework/plugin
  skills aren't installed, so a pos3 session literally cannot load or
  `/`-invoke them. Authoring effort with zero possible payoff in the
  primary workspace.
- **Mode B — description-match never fires (everywhere):** even the 5
  pos3-local skills, and all 38 when surfaced in loam-repo sessions,
  show 0 invocations. The persona does the work inline (consulting the
  CLAUDE.md corpus + memory files it already has in context) and never
  reaches for the Skill tool. The skills' descriptions are competing
  against an already-loaded principle corpus that covers the same ground.

---

## 4. Underused / high-leverage primitives (what's on the table)

Ranked by leverage-per-effort. Effort in AI-time (background-agent).

1. **`/goal` to replace/augment `autonomy_continuation.py`** —
   *Leverage: high. Effort: low (~20-40 min to evaluate, more to migrate).*
   The docs confirm `/goal` IS a session-scoped prompt-based Stop hook
   with a Haiku evaluator. loam hand-rolls this. Adopting `/goal` for the
   keep-going leg gets a platform-maintained evaluator, condition-status
   UI (`◎ /goal active`, turns/tokens), `--resume` restoration, and
   `-p` support for free. Worth a head-to-head: does the native
   evaluator's "judge only what's in the transcript" constraint cover
   loam's autonomy semantics, or does the hand-rolled hook do something
   `/goal` can't?

2. **Install the loam skills as a plugin (fix Mode A) — OR retire them.**
   *Leverage: decision-unblocking. Effort: low.* Right now 38 skills are
   invisible in pos3. Either (a) add a `.claude-plugin/marketplace.json`
   + install so pos3 sessions can see them, or (b) accept they're
   loam-repo-only and retire the ones that duplicate the loaded corpus.
   Doing neither is the current waste.

3. **`paths:` frontmatter on the skills that are path-scoped.**
   *Leverage: medium-high. Effort: low (per-skill 1-line edit).*
   `log-visit`, prose skills, dev-sdlc build skills all have natural file
   globs. `paths:`-gating turns "hope description-match fires" into
   "deterministically auto-load when working in the right files." This is
   the single highest-leverage fix to Mode B for the skills that survive
   the retire/keep cut.

4. **`prompt`-type hook handlers (inline Haiku-as-judge).**
   *Leverage: medium. Effort: low.* loam uses only `command` hooks. Several
   command hooks do regex-classification that a cheap `prompt` hook would
   do more robustly (e.g., intent_classifier_inbound, the
   methodology-vocabulary check). Not urgent, but a real lever.

5. **`SubagentStart`/`SubagentStop` hooks.** *Leverage: medium. Effort:
   medium.* loam dispatches 781 agents but brackets them with no hooks.
   These could enforce dispatch-brief shape (the WD-literal-first-action
   rule, model-rationale line, primitive-rationale line) structurally
   instead of via memory rules — exactly the "recurrence → hook" pattern
   loam already believes in.

6. **`PostToolUseFailure` / `Notification` hooks → Telegram bridge.**
   *Leverage: medium. Effort: low-medium.* A failed tool call or a
   Claude notification could surface to Telegram out-of-band — directly
   relevant to the Telegram-outage self-heal rules already in the corpus.

7. **Routines (cloud) for the durable weekly audits.** *Leverage:
   medium. Effort: medium.* The places/restaurant audits run via launchd
   (needs the machine on). Routines run on Anthropic cloud, survive the
   machine being off, and are `/schedule`-managed. Min interval 1h is
   fine for weekly work. Trade-off: cloud routines get a fresh clone (no
   local file access) — only worth it for audits that don't need the
   local tree.

8. **`MessageDisplay` hook (newest event).** *Leverage: low. Effort:
   low.* Net-new; niche (live-display-time side effects). Flag for the
   awareness-SKILL refresh, not for adoption yet.

---

## 5. Prioritized recommendations (ranked, each tied to a leverage gain)

**P0 — decide the skills' fate (resolves the biggest waste).**
The data is unambiguous: 0 invocations ever. Two sub-decisions for Luke:
  - **(a) pos3 visibility:** install the loam skills as a plugin (add
    `.claude-plugin/marketplace.json` + install) so they're *reachable*
    in the primary workspace — or explicitly accept loam-repo-only scope.
  - **(b) Mode-B fix vs retire:** for each skill, either give it a real
    auto-load trigger (`paths:` glob, or `disable-model-invocation:true`
    + treat it as a `/command` the persona/user invokes by name) or
    retire it as corpus-duplication. A skill the persona never reaches
    for because the same content is already in CLAUDE.md is dead weight.
  *Leverage: stops ongoing authoring of never-invoked skills; recovers
  the ones with genuine path-scoped value.*

**P1 — `/goal` head-to-head against `autonomy_continuation.py`.**
Evaluate adopting the native primitive for the keep-going leg. Tie:
platform-maintained Haiku evaluator + status UI + resume + `-p`, minus
hand-rolled-hook maintenance. *Leverage: removes a maintained
reimplementation of a now-native primitive.*

**P2 — refresh `claude-feature-awareness` SKILL.** It self-describes as
"going stale fast" and is now ~17 days old. Concrete deltas to fold in:
30 hook events (add `MessageDisplay`); `/goal` = wrapper-around-Stop-hook
(v2.1.139); the full 13-field skill frontmatter list (it lists ~7);
Routines now in research preview with API/GitHub triggers. *Leverage:
the catalogue the persona consults is the input to every primitive
decision; stale catalogue = wrong decisions.*

**P3 — adopt `paths:` on the surviving path-scoped skills.** Cheapest
Mode-B fix; deterministic auto-load. *Leverage: converts hope-based
description-match into file-triggered load.*

**P4 — `SubagentStart/Stop` hooks to structurally enforce dispatch-brief
shape.** loam's own "recurrence → hook" doctrine applied to the 781-agent
dispatch surface. *Leverage: moves brief-shape rules from memory (soft)
to hook (hard).*

**P5 — `PostToolUseFailure`/`Notification` → Telegram bridge.** Composes
with the existing Telegram-outage self-heal corpus. *Leverage:
out-of-band failure surfacing without polling.*

---

## 6. F2 — Ruthless Feedback on the owner's framing

**On "we're underusing the primitives — there are dozens or hundreds":**
*Disagreement:* the count is wrong; the instinct is right. *Evidence:*
the live hooks doc lists **30 hook events**, **5 handler types**, ~6
scheduling primitives — a bounded catalogue of ~40 named things, not
hundreds (`https://code.claude.com/docs/en/hooks`). *Alternative frame:*
"the catalogue is small and knowable; loam uses the
structural-enforcement half (hooks + background agents) heavily and well,
and the skill + scheduling-iteration half barely." Re-anchoring to the
real count makes the gap actionable instead of vague.

**On "the skills may not be getting invoked much":**
*Disagreement:* it's stronger than "not much" — it's **zero, ever, in
two distinct ways**. *Evidence:* 0 Skill-tool invocations of any
loam-authored skill across 28 pos3 + 158 loam transcripts; in pos3 they
aren't even installed (`installed_plugins.json` shows only `telegram`).
*Alternative:* don't tune trigger conditions on skills that are
invisible — first decide install-vs-retire (P0), THEN fix triggers
(P3) only on survivors.

**Where loam is BETTER than the framing implies (don't validate a false
premise):** the hook layer is genuinely strong — 5 events, ~24 handlers,
`PreCompact` already adopted, and **781 background-agent dispatches**
showing background-agents-by-default is real, not aspirational. The
problem is narrow and specific (skills + scheduling-iteration family),
not a broad "loam ignores the platform." Saying "we underuse primitives"
flat would understate the hook/agent strength and overstate the breadth
of the gap.

**One thing I could NOT verify (stated as a gap, not a guess):** whether
any loam skill auto-LOADED its body without producing a Skill tool_use
entry (i.e., whether description-match injected a skill body via a
different transcript marker). The 3-invocation total and the
`skill_listing`-only name mentions strongly indicate no — but if Claude
Code can inject a skill body without a Skill tool_use record, the "0
invocations" figure would undercount silent auto-loads. The grep
evidence points hard at 0; I flag the one mechanism I couldn't fully
rule out.

---

## Appendix — evidence index

- Hook catalogue: `https://code.claude.com/docs/en/hooks` (30 events, 5 handlers)
- `/goal` semantics: `https://code.claude.com/docs/en/goal` (wrapper around prompt-based Stop hook, v2.1.139)
- Scheduling: `https://code.claude.com/docs/en/scheduled-tasks`; Routines: `https://claude.com/blog/introducing-routines-in-claude-code`
- Skill frontmatter: `https://code.claude.com/docs/en/skills` (13 fields incl `paths`, `context:fork`, `model`, `disable-model-invocation`)
- pos3 hooks: `/Users/lukeivers/pos3/.claude/settings.json`
- global hooks: `/Users/lukeivers/.claude/settings.json`
- skills on disk: `/Users/lukeivers/loam/plugins/{loam-skills,dev-sdlc}/skills/*/SKILL.md`, `/Users/lukeivers/pos3/.claude/skills/*/SKILL.md`
- plugin install state: `/Users/lukeivers/.claude/plugins/installed_plugins.json` (telegram only)
- telemetry: greps over `/Users/lukeivers/.claude/projects/*/*.jsonl` (Skill tool_use, Agent count, skill_listing names) — counts in Sections 2-3
- internal catalogue refreshed against: `/Users/lukeivers/pos3/.claude/skills/claude-feature-awareness/SKILL.md`
