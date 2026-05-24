---
description: "Use when the user signals cost-awareness ('loam is expensive', 'tokens are burning', 'cut my costs', 'what should my settings be', 'how do I save money on this', 'my Claude bill is too high') or explicitly invokes `/skill cost-optimised-defaults`. Present the four recommended token-optimization settings (model: sonnet default, env.MAX_THINKING_TOKENS=10000, env.CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50, MCP/tool discipline of <10 MCPs + <80 active tools per project) with one-line cost-rationale per setting (savings percentages attributed to ECC source — loam has not independently measured), surface the exact diff that would land in ~/.claude/settings.json including any pre-existing user-key collisions shown side-by-side (existing value vs recommended value), AWAIT EXPLICIT USER APPROVAL ('yes', 'proceed', 'apply', 'go ahead' or equivalent affirmative), and on approval merge the keys non-destructively via the colocated merge.py helper (existing user keys preserved by default; collision-keys accept the user's per-key choice; atomic write-temp-then-rename so partial writes can't corrupt the file). On rejection, emit 'no changes' diagnostic and exit without write. This SKILL is the ONLY mutation surface for these defaults per D-TOKEN.ENFORCE (maintainer ruling TG 12301) — install-time scripts MUST NOT touch ~/.claude/settings.json; auto-mutation is REJECTED. The persona makes the invocation call on detected cost-signal; the SKILL itself never auto-fires; user-config sovereignty is the load-bearing constraint."
---

# cost-optimised-defaults

Loam's recommended token-optimization defaults (Sonnet default,
MAX_THINKING_TOKENS cap, earlier auto-compact, MCP/tool discipline)
absorbed from ECC's settings recommendations, with explicit
user-approval before any write to `~/.claude/settings.json`.

## What this skill captures

A four-setting recommendation set with one-line cost-rationale per
setting, a non-destructive merge mechanism that preserves pre-existing
user keys, an explicit user-approval flow before any write, and a
toggle-back-off instruction set so the user can revert by manually
removing the keys.

The discipline is **opt-in only**. Loam's install-time scripts do not
touch `~/.claude/settings.json`. This SKILL is the only mutation
surface, and it writes only on explicit user approval after surfacing
the exact proposed diff.

### The four recommended settings + their cost-rationale

ECC source: `https://github.com/affaan-m/everything-claude-code`
README → "Token Optimization & Cost Management" section (verified
2026-05-24). Cost-savings percentages below are ECC's claims; loam has
not independently measured.

#### 1. `model: "sonnet"`

- **Setting shape:** top-level `model` field in `~/.claude/settings.json`.
- **Cost rationale (per ECC):** ~60% cost reduction vs Opus; handles
  80%+ of coding tasks. Opus is the heavy tier for complex
  architectural decisions; Sonnet covers routine work.
- **Loam composition:** matches the global Token-efficiency discipline
  in `~/.claude/CLAUDE.md` ("Sonnet for routine tasks; Opus only for
  complex architectural decisions") — this SKILL generalizes the
  maintainer-only discipline to a user-facing surface.

#### 2. `env.MAX_THINKING_TOKENS: "10000"`

- **Setting shape:** nested under `env` (object of string key-value
  pairs); applies to every session and to subprocesses Claude Code
  spawns.
- **Cost rationale (per ECC):** ~70% reduction in hidden thinking cost
  per request. Default thinking budget is unbounded; the 10k cap is a
  high-leverage cost lever with low quality impact on routine work.
- **Loam composition:** composes with the `strategic-compact` SKILL —
  thinking-cost discipline at request level; compact-vs-continue
  discipline at session level.

#### 3. `env.CLAUDE_AUTOCOMPACT_PCT_OVERRIDE: "50"`

- **Setting shape:** nested under `env`.
- **Cost rationale (per ECC):** compacts earlier (50% context
  utilization instead of the default later threshold), preserving
  quality in long sessions. The earlier compaction trades one
  compaction round for better per-turn quality across the session
  tail.
- **Loam composition:** composes with the `strategic-compact` SKILL
  (which informs WHEN to manually `/compact` vs `/clear` vs continue)
  and `precompact-hook` (which preserves state at compaction time).

#### 4. MCP / tool discipline — `<10` MCPs per project, `<80` active tools

- **Setting shape:** discipline, not settings.json keys. Surfaced in
  the docs section + this SKILL body as guidance.
- **Cost rationale (per ECC):** each MCP server + each registered tool
  adds context overhead at session start; staying under the named caps
  keeps the per-turn baseline cost manageable.
- **Loam composition:** composes with the per-workspace `.mcp.json`
  + `.claude/settings.json` workspace-local override pattern; user
  trims MCPs/tools at the workspace level, not via this SKILL.

### The merge mechanism

The colocated helper `merge.py` (see `plugins/loam-skills/skills/
cost-optimised-defaults/merge.py`) implements:

- **Read:** loads existing `~/.claude/settings.json` (preserving
  content if file absent → starts from empty object).
- **Plan:** computes the exact diff: which recommended keys would be
  newly added, which would collide with existing user values, what
  the existing values are.
- **Surface:** returns the planned-diff structure for the SKILL's
  approval flow to display side-by-side.
- **Apply:** on user approval, merges the approved keys into the
  existing settings object, writes atomically (write-temp-then-rename
  so a partial write can't corrupt the file), and returns a structured
  diagnostic listing keys written + keys preserved-due-to-conflict +
  the path written to.
- **Reject:** on user rejection, returns a "no changes" diagnostic
  without writing.

### The user-approval flow

When the persona invokes this SKILL:

1. **Read + plan.** Invoke `merge.py plan` to compute the diff
   against the user's current `~/.claude/settings.json`.
2. **Display the diff side-by-side.** For each recommended key:
   - If absent in user's settings → "NEW: `<key>` → `<recommended-value>`".
   - If present with same value → "ALREADY SET: `<key>` = `<value>` (no change)".
   - If present with different value → "COLLISION: `<key>` — existing
     `<user-value>` vs recommended `<recommended-value>`. Keep
     existing OR overwrite?".
3. **Ask explicit approval.** "Apply these changes to your
   `~/.claude/settings.json`? Reply yes/proceed/go OR no/skip/cancel."
   For collision-keys, ask per-key: "Overwrite `<key>` or keep
   existing?".
4. **Apply or reject.** On affirmative → `merge.py apply` writes the
   approved keys atomically. On rejection → emit "no changes" diag
   + exit.
5. **Confirm.** On apply, surface the structured diagnostic: keys
   written, keys preserved-due-to-conflict, path written.

### Toggle back off

To revert the SKILL's writes:

1. Open `~/.claude/settings.json` in a text editor.
2. Remove the keys you want to revert: `model`, or the relevant entries
   under `env` (`MAX_THINKING_TOKENS`, `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`).
3. Save the file. Next Claude Code session reads the new settings.

The SKILL never auto-reverts. A future `cost-optimised-defaults-undo`
SKILL is a candidate if user demand surfaces (currently captured as
FIDRAFT F-COST-OPTIMISED-DEFAULTS-UNDO in the plan-doc).

## When to use

The SKILL fires when EITHER of these holds:

1. **User cost-signal.** The user expresses cost-awareness in chat:
   "loam is expensive", "tokens are burning", "what should my
   settings be", "how do I save money on this", "my Claude bill is
   too high", or any close paraphrase. The persona makes the
   invocation call.

2. **Explicit invocation.** The user types `/skill
   cost-optimised-defaults` or the equivalent natural-language
   "apply the cost-optimised defaults".

Skip when:

- The user has already applied the defaults (re-running the SKILL is
  idempotent — same diff display + same approval flow + no-op if
  user declines — but surfaces noise unnecessarily).
- The user has explicitly opted out for the session ("don't surface
  settings recommendations").

## How the persona applies it

Before invoking:

1. **Detect the cost-signal.** Listen for the patterns named in the
   frontmatter `description`. The persona's judgment on signal
   detection; false-positive cost is low (user can decline), false-
   negative cost is higher (user hits cost pain unnecessarily).

2. **Invoke this SKILL.** The SKILL handles the technical detail; the
   persona's job is the dispatch + interpretation of the user's
   approval response.

3. **Run `merge.py plan`** to compute the diff against the user's
   current `~/.claude/settings.json`.

4. **Surface the diff side-by-side with rationale.** For each
   recommended key, show what would change + the one-line cost
   rationale + the ECC-attribution for the savings claim.

5. **Await explicit approval.** The user MUST reply with an
   affirmative ("yes", "proceed", "apply", "go ahead" or equivalent).
   For collision-keys, ask per-key. Default-to-skip on ambiguity.

6. **Apply on approval; emit no-changes diag on rejection.**

7. **Confirm.** Surface the structured diagnostic showing keys
   written, keys preserved-due-to-conflict, and the settings path.

## Honest limits

- **Cost-savings percentages are ECC's claims, not loam-measured.**
  The 60% / 70% numbers come from ECC's documented settings table;
  loam has not benchmarked Sonnet-vs-Opus or thinking-token-cap cost
  on loam-typical workloads. Real-world savings will vary by usage
  pattern.
- **Collision-handling depends on user attention.** The SKILL surfaces
  collisions side-by-side and asks per-key — but a user rubber-
  stamping "approve all" without reading carefully could silently
  lose preferred values. The per-key prompt mitigates; the user's
  attention is load-bearing.
- **MCP/tool discipline is guidance, not enforcement.** The `<10 MCPs
  + <80 tools` caps are surfaced in this SKILL body + the docs
  section, but loam does not enforce them at install time. The user
  manages their workspace `.mcp.json` directly.
- **`ECC_CONTEXT_MONITOR_COST_WARNINGS=off` is NOT included.** That
  ECC-specific env var is for ECC's own context monitor; loam has no
  equivalent monitor; absorbing it as-is would set a no-op env var.

## Graceful degradation

Without loam — running raw Claude Code without this SKILL — the same
four settings can be applied manually:

1. Open `~/.claude/settings.json` in an editor.
2. Set `"model": "sonnet"`.
3. Under `"env"` (create the object if absent), set
   `"MAX_THINKING_TOKENS": "10000"` and
   `"CLAUDE_AUTOCOMPACT_PCT_OVERRIDE": "50"`.
4. Save. Restart Claude Code (settings.json is read once at session
   start).
5. For MCP/tool discipline: trim your workspace `.mcp.json` to keep
   active MCP servers under 10 per project, and trim registered
   tools to under 80 active per project.

The SKILL automates the read-plan-surface-approve-write loop with
collision handling; without loam, the user does the diff in their
head and writes manually.

## Composition

This SKILL composes with:

- **`strategic-compact` (sibling SKILL)** — session-management
  discipline. This SKILL installs the SETTINGS that make compaction
  effective (earlier autocompact at 50% utilization); strategic-
  compact informs WHEN to manually `/compact` vs `/clear` vs continue.

- **`precompact-hook` (sibling SKILL)** — structural enforcement of
  state preservation at compaction time. Composes downstream of this
  SKILL: this SKILL sets the autocompact threshold; precompact-hook
  preserves state when compaction (auto or manual) fires.

- **`feedback_compact_clear_decision_heuristic.md`** (memory, now
  graduated to the `strategic-compact` SKILL) — the rubric for
  session-management decisions composes with the SETTINGS this SKILL
  installs.

- **`~/.claude/CLAUDE.md` Token efficiency section** — the global
  discipline ("Sonnet for routine tasks; Opus only for complex
  architectural decisions") that this SKILL generalizes to a
  user-facing surface.

- **`docs/getting-started.md` Token-optimization section** —
  documentation surface that surfaces the same four settings for
  docs-first user discovery. This SKILL is the action surface; the
  docs section is the visibility surface.

- **`feedback_test_outcome_altitude_required.md`** (memory) —
  AC.TOKEN.S is the outcome-altitude AC: a synthetic end-to-end
  session invokes the production discovery path with no pre-arranged
  state.

## Out of scope

- **Auto-mutation of `~/.claude/settings.json` on install** —
  D-TOKEN.ENFORCE rules out. The SKILL is the ONLY mutation surface.

- **Auto-firing of this SKILL on cost-signal detection without
  user approval** — the persona's invocation call is judgment-bound;
  this SKILL itself never auto-fires; the approval flow is always
  load-bearing.

- **Modifying workspace-local `.claude/settings.json`** — only
  `~/.claude/settings.json` (user-global) is in scope. Workspace-
  local overrides are user's call.

- **Cost-measurement / telemetry of post-write savings** — the SKILL
  surfaces ECC's claimed-savings percentages; it does not measure
  loam-specific savings. Cost-measurement is a separate work-item
  (FIDRAFT F-LOAM-COST-MEASUREMENT).

- **Undo / revert command** — out of scope for this work-item;
  manual revert via text editor is documented in "Toggle back off"
  above. FIDRAFT F-COST-OPTIMISED-DEFAULTS-UNDO captures the
  follow-up.

- **Auto-detection hooks (SessionStart / UserPromptSubmit) that
  trigger this SKILL** — out of scope; FIDRAFT F-COST-SIGNAL-
  AUTOFIRE-HOOK captures the follow-up.

- **Mutating shell profiles (`.zshrc`, `.bashrc`) to set env vars
  outside settings.json** — Claude Code's `env` field in
  `settings.json` accepts both env vars (verified 2026-05-24
  against `https://code.claude.com/docs/en/settings`); merging
  there is single-surface and lower-blast-radius than touching
  shell profiles.
