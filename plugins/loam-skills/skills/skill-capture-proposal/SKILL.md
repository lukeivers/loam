---
description: "Use when the user explicitly asks to capture a pattern as a skill ('remember this', 'make this a skill', 'let's codify this', 'capture this as a skill'), OR when the same multi-step procedure is invoked 3+ times within a session, OR when the same shape of question is asked 3+ times and the answer text stabilizes (ask-and-answer pattern). The persona drafts a workspace-local SKILL.md to a .scratch/ path, surfaces a one-line ratification question through PM (Y/N/R), and on Y writes the SKILL to <workspace>/.claude/skills/<slug>/SKILL.md so Claude Code's native discovery auto-loads it next turn. Universal — any loam user, dev or non-dev. Gated on the workspace-bootstrap manifest's enable_auto_skill_capture flag (default false; user opts in when ready)."
---

# skill-capture-proposal

Loam's primary persona is, fundamentally, a translation layer
between the user's natural-language intent and AI-effective
execution. When the user asks the persona to do the same multi-
step procedure repeatedly, or when the user explicitly says
"remember this for next time," the right response is to capture
the pattern as a workspace-local SKILL the persona auto-loads on
future relevant turns. This skill codifies the discipline for
proposing that capture without silently writing files behind the
user's back.

## What this skill captures

The persona-driven skill-capture workflow — three triggers, a
proposal-draft-ratify gate, and a SKILL.md materialization step
that uses Claude Code's native filesystem-walk discovery
mechanism (no `/load-skill` API exists; registration is the file
write).

The mechanism is **universal across loam workflows**: any user
benefits, dev or non-dev. Auto-creation as a primitive is harness-
general — non-dev users especially benefit because their patterns
(rhetorical structures, methodology checklists, runbooks) rarely
fit existing dev-tooling shapes. Per layered-skill story research
§3.6 + Luke's 2026-05-04 universal-scope clarification.

The mechanism is **gated by a single workspace-config flag**:
`enable_auto_skill_capture` in `bootstrap.yaml` (default `false`).
A fresh workspace doesn't auto-propose; the user opts in by
flipping the flag when they're ready. When the flag is `false`,
the persona MUST NOT propose — graceful degradation back to
pre-capture behavior.

The mechanism is **user-ratified, never silent**. Silent skill
write is a known anti-pattern (per layered-skill research §3.1):
a persona that auto-creates SKILLs every time the user does
something twice will bloat workspace-local skills until discovery
becomes noisy and Claude's auto-load misfires. The user-
ratification gate via the per-project-pm one-question-at-a-time
PM batch API (Decision Q + AC.QSURF.1 from v0.1.7 Cycle 4) is the
structural defence.

Three triggers ship at v0.2.0 MVP per Decision N (3-of-6 lock —
quality bar move; ship 3 complete rather than 6 half-implemented):

1. **Explicit request.** Highest-precision; near-zero false-
   positive. Phrase-list match.
2. **Repeated invocation.** The canonical "auto-creation" use
   case from Luke's framing — same multi-step procedure 3+ times.
3. **Ask-and-answer pattern.** High-precision Q&A; especially
   valuable for non-dev users.

Three triggers deferred to v0.2.x (named in
`docs/design/auto-skill-capture-shape.md` forward-path section):
CLAUDE.md drift, memory-recall hit pattern, hook-trigger pattern.
Each requires either component-side instrumentation (M-FBM API
extension; hook-event subscription) or is dev-mode-only —
incompatible with v0.2.0's MVP scope.

## When to use

The persona applies this skill when **all three** of these
conditions hold:

1. **Workspace flag is on.** `enable_auto_skill_capture: true`
   in `<workspace-root>/bootstrap.yaml` (or the manifest path
   pointed to by `$POS_BOOTSTRAP_MANIFEST`). Default is `false`;
   the persona MUST NOT propose under default. Read the flag via
   `loam.workspace_bootstrap.load_manifest(...).enable_auto_skill_capture`
   or by inspecting the manifest YAML directly.

2. **At least one trigger fires.** The persona detects a trigger
   match per the heuristics below.

3. **No suppression gate is active.** Cool-down for the same
   trigger-pattern is not in the past 14 days (per the
   `cooldowns.yaml` check); per-week budget hasn't fired 3
   proposals in the rolling 7-day window (per the `budget.yaml`
   check); workspace-local skills count is under the 20-skill
   hard-cap (walk `<workspace>/.claude/skills/<*>/SKILL.md`).

When ALL three hold, the persona drafts + surfaces. Skip when
any condition fails. The persona's job is to detect the
heuristic match, NOT to override the user-ratification gate.

### Trigger 1 — Explicit request

The user says one of these phrases (or close paraphrase):

- `"remember this"`
- `"make this a thing"` / `"make this a skill"` / `"make this reusable"`
- `"let's codify this"` / `"let's capture this"`
- `"capture this as a skill"` / `"save this as a skill"`
- `"remember this pattern"` / `"add this to my skills"`

On match → proposal-draft mode immediately. No threshold; no
cool-down check (explicit user intent overrides the cool-down).
Highest-precision trigger.

### Trigger 2 — Repeated invocation

The persona has invoked the same multi-step procedure 3 or more
times within the current session, and the procedure has the same
structural shape across invocations.

**Threshold:** ≥3 invocations within a session window.

**Matching heuristic:** tool-call sequence + structural overlap
≥70% across invocations. The procedure is a sequence of tool
calls (Bash, Read, Write, Edit, etc.); structural overlap is
defined as the longest common subsequence of tool-call types,
weighted by argument-shape similarity. If 3 invocations share
≥70% structural overlap → trigger fires.

**Session-scoped at MVP.** Detection happens within a single
session's conversation memory. Cross-session detection requires
M-FBM episode-store reads and is the v0.2.x deferred path. The
persona reads its own session context, NOT M-FBM, to count
invocations.

**Concrete example:** Luke asks the persona to "run `pos pull`
then `pos publish` then `git tag` then `git push --tags`" four
times in one session — that's a `pos-release-tag` workspace-
local skill candidate.

### Trigger 3 — Ask-and-answer pattern

The user asks the persona how to do X; the persona answers; the
user does X. Same shape of question is asked 3+ times in the
session AND the answer text stabilizes (the persona's response
converges across the 3 exchanges).

**Threshold:** ≥3 question-answer exchanges with the same
question shape and stable answer text.

**Matching heuristic:** question-text similarity (≥70% token
overlap or named-pattern match) AND answer-text similarity (≥80%
token overlap across the 3 stabilized answers).

**Especially valuable for non-dev users.** A writer asking the
persona "how do I structure a 3-act argument?" 3 times across a
session, getting the same scaffold each time — that's a workspace-
local SKILL candidate. Non-dev users' patterns rarely fit dev-
tooling shapes; this trigger captures the rhetorical / methodo-
logical recurrences that are otherwise invisible.

**Session-scoped at MVP.** Same scope as Trigger 2 — within-
session conversation memory; M-FBM cross-session reads deferred
to v0.2.x.

## How the persona applies it

The five-step capture workflow.

### Step 1 — Detect + draft

When a trigger fires, the persona drafts a SKILL.md to:

```
<workspace>/.scratch/claude-output/skill-draft-<slug>.md
```

The draft is in `.scratch/`, NOT yet in `.claude/skills/` — this
prevents accidentally bypassing the ratification gate by writing
to the discovery path before the user approves.

The draft uses the **6-section template** that every existing
loam SKILL follows (verified across 8 sealed SKILLs at
`plugins/loam-skills/skills/`):

```markdown
---
description: <ONE PARAGRAPH; ≤1536 chars; trigger-phrase clause>
---

# <skill-name>

<brief paragraph: what the SKILL captures>

## What this skill captures

<the discipline / pattern / decision-procedure>

## When to use

<trigger conditions; when to skip>

## How the persona applies it

<the workflow; concrete steps>

## Graceful degradation

<what to do without loam — raw Claude Code path>

## Composition

<which loam primitives + Claude capabilities the skill leans on>

## Out of scope

<explicitly named non-deliverables>
```

Draft must include a **draft header** at the top of the body:

```
**Draft origin:** trigger=<trigger-name>; evidence=<3 instances
+ in-session reference points>; date=<ISO timestamp>; persona-
proposed; awaiting user ratification.
```

The header makes the proposal's evidence auditable; the user
sees what the persona detected before approving the write.

### Step 2 — Audit-log the trigger fire

Write one audit-log entry to:

```
<workspace>/.loam/skill-capture/audit-log/<YYYY-MM-DD>-<NNNN>.yaml
```

Where `<NNNN>` is a 4-digit zero-padded monotonic counter scoped
to the date (mirrors `framework/per-project-pm`'s audit-log
filename convention). Entry shape:

```yaml
schema_version: 1
event_kind: skill_capture_trigger_fired
timestamp: <ISO 8601 UTC>
trigger: <explicit_request | repeated_invocation | ask_and_answer>
trigger_pattern_hash: <sha256 of the canonical pattern signature>
proposed_slug: <kebab-case slug for the proposed SKILL>
draft_path: <relative path to the .scratch/ draft>
evidence_summary: <brief; ≤200 chars>
```

This is the SOC-2 audit-trail floor (Decision P) for skill-
capture events.

### Step 3 — Surface ratification question via PM

Use the existing `framework/per-project-pm/` batch API. One-line
decision-question shape (per the v0.1.7 Cycle 4 one-question-at-
a-time discipline + Decision Q + AC.QSURF.1):

```
"I noticed [pattern-summary] N times in this session. Capture as
workspace-local skill '<proposed-slug>'? Draft at <draft-path>.
Y / N / R(evise)."
```

The PM enqueue path:

```python
from loam.per_project_pm import PMRuntime

pm = PMRuntime.from_workspace(workspace_root, pm_handle)
pm.enqueue_decision(
    question_text=question_text,
    provenance=f"skill-capture:{trigger}:{proposed_slug}",
)
# Persona surfaces via:
surfaced = pm.surface_next_questions_batch(n=1)
# (n=1 honors the one-question-at-a-time discipline)
```

Write one `skill_capture_proposal_drafted` audit-log entry at
the same path as Step 2 (with the PM provenance string).

### Step 4 — Ratify (Y / N / R)

When the user responds (relayed back through `record_response`):

**Y → Materialize.** Move the draft to:

```
<workspace>/.claude/skills/<proposed-slug>/SKILL.md
```

Use `Write` tool to create the directory + write the file. After
write, write one `skill_capture_ratified` audit-log entry.
Claude Code's native filesystem-walk discovery picks the new
SKILL up on the next relevant turn (verified at v0.1.7 Cycle 3
`bcf699a`).

**N → Reject + cool-down.** Write one `skill_capture_rejected`
audit-log entry. Append to `<workspace>/.loam/skill-capture/
cooldowns.yaml`:

```yaml
schema_version: 1
cooldowns:
  - trigger_pattern_hash: <hash>
    rejection_iso: <ISO 8601 UTC>
    cooldown_until_iso: <rejection + 14 days>
    rejected_slug: <slug>
```

The persona MUST check this file at Step 1 (Detect + draft); on
hit and `now < cooldown_until_iso`, no-op (write a
`skill_capture_cooldown_active` entry instead of drafting).

**R → Revise.** Iterate: persona reads the user's revision-
intent (next user-message), updates the draft in `.scratch/`,
returns to Step 3 with the revised draft. Write one
`skill_capture_revised` audit-log entry per revision iteration.

### Step 5 — Per-week budget + hard-cap gates

Before drafting at Step 1, the persona reads:

```
<workspace>/.loam/skill-capture/budget.yaml
```

```yaml
schema_version: 1
budget:
  weekly_cap: 3                  # ≤3 proposals per rolling 7-day window
  events:
    - proposed_at_iso: <ISO 8601 UTC>
      slug: <slug>
      outcome: <pending | ratified | rejected | revised | budget_exhausted>
```

The persona counts events with `proposed_at_iso > (now - 7d)`;
if count ≥ `weekly_cap`, no-op until the oldest event ages out
(rolling-window reset).

The persona ALSO walks `<workspace>/.claude/skills/<*>/SKILL.md`
(filesystem discovery, same primitive Anthropic uses). If
count ≥ 20 (hard-cap per layered-skill research §3.5 #1), no-op
+ surface a one-line note: "Workspace-local skill count at hard-
cap (20). Consider reviewing via the v0.2.1
skill-promotion-review surface to retire stale skills before
proposing new ones."

The 20-skill hard-cap defends against bloat that Anthropic's
description-budget cap eventually triggers (per layered-skill
research §3.5 #1).

## Graceful degradation

Without loam — running raw Claude Code without the
`framework/workspace-bootstrap/` config-flag mechanism — the
persona has no `enable_auto_skill_capture` gate. The pattern
still works manually:

1. User says "remember this" or recognizes a recurring pattern.
2. User asks Claude Code (or the persona) to draft a SKILL.md.
3. User reviews the draft.
4. User uses `Write` (or the file-system editor) to create
   `<project>/.claude/skills/<slug>/SKILL.md`.
5. Claude Code's native discovery auto-loads on the next
   relevant turn.

The discipline this SKILL captures (drafting → ratification →
write) is portable to raw Claude Code; what loam adds is the
structural defence (PM ratification gate; audit-log; cool-down +
budget + hard-cap suppression). Without loam, those defences
are at the user's discretion.

## Composition

This SKILL composes with:

- **`enable_auto_skill_capture` workspace-config flag** in
  `framework/workspace-bootstrap/manifest.py`. The boolean
  default-false flag is the single workflow-level gate; when
  off, this SKILL's "When to use" gate prevents the persona
  from proposing.
- **`framework/per-project-pm/` PM batch API** (v0.1.7 Cycle 4
  `122a7c8`). `PMRuntime.enqueue_decision` +
  `surface_next_questions_batch(n=1)` + `record_response` is the
  ratification surface. Decision Q + AC.QSURF.1 enforce one-
  question-at-a-time at the structural layer.
- **Anthropic's SKILL.md schema + native discovery** (verified
  2026-05-04). Discovery locations (precedence: enterprise >
  personal > project; plugin in its own `plugin-name:skill-
  name` namespace). Workspace-local SKILLs land at
  `<workspace>/.claude/skills/<slug>/SKILL.md`; Claude Code's
  filesystem walk at session-start picks them up.
- **`docs/design/auto-skill-capture-shape.md`** — the
  architectural reference; explains the universal-tier framing,
  the user-ratifies-not-persona-decides discipline, the v0.2.x
  trigger-expansion roadmap.
- **CLAUDE.md design lenses** — Lens 1 (Claude-leverage-first;
  this SKILL leans on Anthropic's discovery primitive + Claude's
  Write tool + per-project-pm's primitives), Lens 2 (harness +
  persona value; this SKILL is invokable from any loam-driven
  workflow), Lens 4 (HIGH-confidence shape; mirrors 8 existing
  reference SKILLs).
- **F3 swarming** — when a recurring pattern is detected, the
  capture workflow itself is a small decomposition (detect →
  draft → ratify → write → audit) that satisfies F3's stopping
  criterion: each step has a tighter acceptance than the parent.
- **M5 principle-conflict resolution** — when the explicit-
  request trigger fires inside an active cool-down for the same
  pattern, the conflict (user-intent vs cool-down suppression)
  is resolved with explicit-request winning (user intent
  overrides cool-down). Named in §6 of the plan-doc.
- **SOC-2 audit-trail floor (Decision P)** — every trigger fire
  + draft + ratification/rejection + revision + cool-down hit
  emits an audit-log entry under `<workspace>/.loam/skill-
  capture/audit-log/<YYYY-MM-DD>-<NNNN>.yaml`.

## Out of scope

This SKILL deliberately does NOT cover:

- **Cross-session trigger detection.** Triggers 2 + 3 are
  session-scoped at MVP; cross-session detection requires
  M-FBM episode-store reads (deferred to v0.2.x — see master
  plan §7.3 + design note forward-path).
- **Python runtime detector module.** Triggers ship as
  persona-side discipline embedded in this SKILL body, NOT a
  separate `loam_skill_capture` daemon. v0.2.x may extract a
  helper module if utility emerges.
- **Promotion rubric** for workspace-local → plugin / base. The
  workspace-local skills accumulate; the v0.2.1
  `skill-promotion-review` SKILL handles graduation evaluation.
- **Demotion path** for retired skills. Same — v0.2.1.
- **Three deferred triggers.** CLAUDE.md drift; memory-recall
  hit pattern; hook-trigger pattern. Each named in the design
  note's forward-path section; each requires component-side
  instrumentation (M-FBM, hook-event subscription) or is
  dev-mode-only.
- **Mode 2 structured fill-in-blanks UI.** Per Decision D +
  layered-skill research §3.4; MVP uses Mode 1 (persona drafts
  + user reviews); Mode 2 deferred to v0.2.x.
- **Cross-workspace skill sharing.** Not on roadmap.
- **Auto-applying ratified skills to other workspaces.** SKILLs
  written here are workspace-local by definition.
