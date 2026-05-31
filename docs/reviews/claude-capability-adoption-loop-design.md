# The loam capability-adoption loop — standing-process design (Pass-2B)

**Date:** 2026-05-31 · **Scope:** READ-ONLY *design* (nothing built — every
job/setting/skill change below is an owner-gated follow-on build) ·
**Author:** dispatched research agent (Opus) · **Companion:**
`claude-primitives-adoption-matrix.md` (Pass-2A, **[2A]**) ·
**Foundation:** `claude-primitives-integration-review.md` (Pass-1, **[P1]**).

**The problem this solves:** Anthropic ships Claude Code features on a
**weekly cadence** [P1 §12]; loam's `claude-feature-awareness` SKILL is
~17 days old and self-describes as "going stale fast" [P1 P2]. A one-time
review (Pass-1/Pass-2) is a snapshot that decays. loam needs a **standing
process** that (a) keeps the catalogue current as the platform ships, and
(b) keeps loam's *usage* current as work-patterns drift — so the harness
keeps matching how work actually happens, not how it happened in May.

**Design discipline:** this is a Lens-1 (Claude-leverage-first) design —
every part of the loop **names the Claude-native primitive it USES** rather
than re-implementing. The loop dogfoods the adoption thesis. It is ALSO an
ODD design: objective + the three sub-passes (acceptance) + surfacing-gate;
method (the agent's analysis) stays the builder's call.

---

## 0. Objective (the loop's prime directive)

> Keep the loam ↔ Claude-primitives fit current. Each cycle: refresh the
> feature surface from Anthropic's official changelog, re-pull usage
> telemetry, reassess usage-drift, and surface new-feature + adoption
> recommendations to Luke — auto-applying ONLY safe/reversible changes,
> surfacing everything else for his okay. The adoption matrix [2A] and
> `claude-feature-awareness` SKILL are the LIVING artifacts the loop
> maintains; they are never allowed to go stale.

Acceptance = the three sub-passes (§2) run and produce a dated delta report
+ updated living artifacts each cycle, surfaced via the existing Telegram
path (§3).

---

## 1. Cadence + triggers

Two trigger classes, both **durable across session boundaries** — modeled
on loam's existing launchd jobs (`com.loam.pos3.{places-audit,
usage-monitor,...}.plist`, verified on disk), because P1/[2A] establish
launchd is the durable cross-session scheduler and CronCreate/`/loop` are
session-bound [P1 §1d, 2A #76/#80/#81].

### 1a. Time-based (the floor — guarantees freshness even if nothing pings)

- **Recommended cadence: weekly.** Rationale: Anthropic's release cadence is
  weekly [P1 §12]; a monthly cadence (the SKILL's current self-prescription)
  lets up to ~4 releases pile up before review — the SKILL was 17 days stale
  and *already* missing `MessageDisplay` + the full frontmatter list [P1 P2].
  Weekly keeps the lag ≤1 release. Cost is low: the cycle is a single
  background research+diff dispatch (~tool-call count ≈ 30–60 → ~5–9 min
  AI-time per the duration rubric), not a build.
- **Mechanism (USES):** a **launchd job** (`com.loam.pos3.capability-adoption-loop.plist`,
  weekly) — OR a **cloud Routine** (`/schedule`, min-interval 1h is fine for
  weekly) [2A #77]. **Recommendation: Routine**, because the feature-surface
  sub-pass (§2a) needs only web access (no local tree), and a Routine
  survives the machine being off — strictly better than launchd for this
  specific workload [2A #77]. The usage sub-passes (§2b/§2c) need local
  transcript/settings access, so they run as the launchd-or-local leg. This
  is a **split**: cloud Routine for surface-refresh, local launchd for
  telemetry — each on the primitive that fits its data-access need.

### 1b. Event-based (the responsiveness — fires when the platform actually moves)

- **Claude Code version bump.** On a detected `claude --version` change vs
  the last-seen version, trigger an out-of-cycle surface-refresh.
  **Mechanism (USES):** a **`shell:`/`!`cmd`` dynamic injection** [2A #73]
  in the awareness SKILL renders `claude --version` at load; a lightweight
  SessionStart hook (or the existing keep-pace PreToolUse hook) compares it
  to a stored last-seen value and, on mismatch, enqueues a loop cycle.
- **Changelog change.** On a content-hash change of the official changelog /
  release-notes feed. **Mechanism (USES):** the loop's own surface-refresh
  step hashes the fetched changelog; a changed hash since last cycle is the
  signal that there's something new to fold in. `/release-notes` [2A #11] is
  the native viewer; the changelog URL is the fetched source.
- **Usage-anomaly (optional, lower priority).** A sharp change in the
  `/usage` per-skill/subagent breakdown [2A F9] (e.g. a skill that was firing
  drops to zero, or a new inline pattern spikes) can trigger an out-of-cycle
  drift-reassessment. Mark as v2 — the weekly floor covers it.

**Net cadence recommendation:** **weekly time-based floor + version-bump and
changelog-hash event triggers.** Time-based guarantees the artifacts never
rot; event-based makes the loop responsive to the actual release stream
instead of a calendar.

---

## 2. The three sub-passes (run every cycle)

Each cycle is a **decompose-and-judge** unit (Lens 5 swarming): three
sub-passes with tighter-than-parent acceptance, plus a judge step. Each
sub-pass names the primitive it USES.

### 2a. Feature-surface refresh — "what did Anthropic ship?"

- **Input:** the official changelog + docs (`code.claude.com/docs/en/*`,
  `/release-notes`).
- **Method (builder's call):** fetch the changelog + the hook/skills/
  sub-agents/commands/scheduling doc pages; diff against the last-cycle
  snapshot; enumerate net-new primitives + changed semantics.
- **USES:** the **`/deep-research` bundled workflow** [2A #74] (or a plain
  WebFetch research dispatch) over the doc URLs — this is the SAME changelog-
  research pattern that produced the awareness SKILL originally
  (`workspace/.scratch/claude-output/claude-code-changelog-research-2026-05-14.md`,
  verified on disk). **Compose, don't reinvent:** the loop re-runs the
  existing PLAN-BC research pattern [P1 §12], it doesn't author a new one.
- **Output:** a dated `claude-code-changelog-research-<date>.md` delta +
  a list of net-new rows to add to the adoption matrix [2A].
- **Acceptance:** every doc page in the evidence index [2A appendix] re-
  fetched; every net-new primitive enumerated with a doc citation (Tier-0
  claim-or-cite discipline carries into the loop).

### 2b. Usage-telemetry re-pull — "what is loam actually invoking?"

- **Input:** recent transcripts + the native `/usage` breakdown.
- **Method:** re-run P1's telemetry greps (Skill-tool invocations, Agent
  count, skill_listing names) over the *new* transcripts since last cycle;
  pull the `/usage` per-skill/subagent/MCP/plugin breakdown.
- **USES:** **`/usage`** [2A F9] as the PRIMARY native telemetry feed (its
  per-skill/subagent/MCP breakdown is exactly the invocation-count data P1
  hand-grepped) — cheaper and more authoritative than re-grepping. Transcript
  greps remain the fallback / cross-check (Tier-0: verify the native number
  against the raw transcript when they're cheap to reconcile).
- **Output:** updated invocation counts per skill/primitive; flags for
  anything that *was* firing and stopped (regression) or *should* be firing
  and never does (the standing 0-invocation finding [P1 §3]).
- **Acceptance:** a count per loam-authored skill + per primitive category,
  dated, diffed against last cycle.

### 2c. Usage-drift reassessment — "what is the persona doing inline that a primitive now does better?"

- **Input:** §2a's net-new primitives + §2b's invocation counts + the
  native friction report.
- **Method (the high-judgment leg):** for each inline pattern the persona
  repeats, ask "does a primitive (new this cycle, or existing-but-unadopted)
  now do this better?" This is the `autonomy_continuation.py`→`/goal`
  realization [P1 P1] generalized into a *standing question*. Cross-reference
  every [2A] SKIP/⚠ row: did a constraint that justified the skip change this
  cycle? (e.g. a previously-experimental primitive going GA flips a SKIP to ADOPT.)
- **USES:** **`/insights`** [2A F10] (native session-pattern + friction-point
  report) as the drift signal feed — it surfaces "what the persona does
  repeatedly / where friction is," which is precisely the inline-pattern
  inventory this sub-pass needs.
- **Output:** a ranked list of drift-driven adoption recommendations (inline
  pattern → primitive that now covers it), each with the [2A]-style
  leverage/effort/⚠ annotation.
- **Acceptance:** ≥1 explicit "inline pattern X is now better served by
  primitive Y" judgment OR an explicit "no drift this cycle" finding — never
  silent.

### Judge step (closes the cycle — Lens 5 CycleVerdict)

A **fresh evaluator** (not the agent that ran the sub-passes) produces a
`CycleVerdict`: is the cycle complete, are there gaps, did the agent drift
from "refresh+recommend" into "implement" (a scope violation — the loop is
READ-ONLY by default). **USES:** a **`prompt`-type hook or Haiku judge agent**
[2A #32]. On `needs_fresh_start` (the agent diverged), discard and re-run —
don't ship a drifted delta report.

---

## 3. Surfacing + human-gate

Luke's stated lean: **surface-and-recommend by default; auto-apply only
safe/reversible.** The gate has two lanes.

### 3a. Surfacing (compose with the existing Telegram path)

- Every cycle emits a **delta report** written to disk (output-to-disk
  convention — the report exceeds 40 lines), with a **terse Telegram summary
  + path** sent via `mcp__plugin_telegram_telegram__reply` (the only
  user-visible channel). Summary shape: "N net-new features this cycle; M
  adoption recs (K auto-applied, L awaiting your okay); top rec: …; full
  report: <path>." Prose-first, no AC-IDs/SHAs (translate-outbound discipline).
- **USES:** the existing Telegram MCP reply path + the output-to-disk
  convention — the loop reuses loam's surfacing machinery wholesale, it
  doesn't build a new notification channel.

### 3b. The auto-apply vs owner-gate boundary

**Auto-apply (safe + reversible only — all are doc/catalogue edits, zero
runtime-behavior change):**
- Updating the **adoption matrix [2A]** with net-new rows + refreshed status.
- Refreshing the **`claude-feature-awareness` SKILL** catalogue (new hook
  events, frontmatter fields, scheduling-table changes).
- Appending drift findings to a dated delta report + FUTURE_IDEAS_DRAFT.
- Re-running telemetry counts.
All of these are **pure documentation updates under version control** —
reversible by `git revert`, no behavior change, no settings/hook/job mutation.

**Owner-gated (anything that changes runtime behavior or is hard to reverse):**
- Adding/removing/editing a **hook** (the recent incident was un-verified
  hooks interacting — hooks are NEVER auto-applied [task brief F2 guard]).
- Installing/retiring a **skill or plugin**, or changing skill frontmatter
  that alters auto-load (`paths:`, `disable-model-invocation:`).
- Creating/editing a **scheduled job** (launchd/Routine).
- Any **settings.json** change.
- Adopting a primitive flagged **⚠** in [2A] (conditional-on-not-over-wiring).

**Rule:** the loop's default verb is **recommend**; it only *acts* on the
auto-apply allowlist above, and even then leaves a git trail + Telegram note.
Everything that touches behavior is a surfaced recommendation Luke ratifies —
and per loam's record-ratification-before-dispatch rule, his okay is recorded
into the matrix/plan before any build agent runs.

---

## 4. Living artifacts (how they stay current, not snapshots)

The loop maintains **two living docs** + one rolling log:

1. **`claude-feature-awareness` SKILL** — the persona's catalogue.
   - *Update each cycle:* §2a's net-new primitives + changed semantics are
     folded in (auto-apply lane — pure catalogue edit). The "Status +
     maintenance" footer's date + last-seen-version bump each cycle.
   - *Self-freshening assist (USES):* adopt **`shell:`/`!`cmd`` dynamic
     injection** [2A #73] so the SKILL renders `claude --version` + the
     changelog head at load — a stale catalogue at least *announces* its
     own staleness against the live version. After an update, **`/reload-skills`**
     [2A F12] makes it take effect same-session without restart.
2. **The adoption matrix [2A]** — the decision ledger.
   - *Update each cycle:* net-new primitives become new rows (auto-apply);
     SKIP/⚠ rows whose justifying constraint changed get re-evaluated (§2c)
     and flipped with a dated note; the roll-up counts re-tally. The matrix
     is the durable memory of *why* each skip was a skip — so the loop never
     re-litigates a settled decision, only revisits when a constraint moves.
3. **Rolling delta log** — `docs/reviews/adoption-loop-cycles/<date>.md` (or
   FUTURE_IDEAS_DRAFT append) — the dated per-cycle delta + CycleVerdict +
   what-was-surfaced. This is the audit trail; it's what makes "living" mean
   *traceable*, not *overwritten*.

**Staleness guard:** because the matrix records the last-cycle date and the
SKILL renders the live version, a *missed* cycle is itself observable —
the gap between last-cycle-date and today, surfaced at session-start, is the
backstop if the scheduled job ever silently dies (dead-agent-detection
applied to the loop itself: probe the artifact mtime, don't trust the
scheduler's "it ran" claim).

---

## 5. Compose-don't-reinvent — primitive map for the loop itself

Every part of the loop USES a Claude-native primitive (Lens 1 dogfood):

| Loop part | Claude-native primitive it USES | Why (not reinvent) |
|---|---|---|
| Weekly durable trigger (surface-refresh) | **Cloud Routine** (`/schedule`) [2A #77] | Survives machine-off; surface-refresh needs only web access (no local tree) |
| Weekly durable trigger (telemetry/drift) | **launchd** (the existing pos3 reference shape) [2A #81] | Needs local transcript+settings access; the proven durable local path |
| Version-bump / changelog event trigger | **`shell:` dynamic injection** [2A #73] + a lightweight SessionStart compare | Native render-time injection; no polling daemon |
| Sub-pass 2a (feature-surface) | **`/deep-research` workflow** [2A #74] over the doc URLs | Re-runs the existing PLAN-BC changelog-research pattern |
| Sub-pass 2b (telemetry) | **`/usage`** breakdown [2A F9] | Native per-skill/subagent/MCP invocation counts — replaces hand-greps |
| Sub-pass 2c (drift) | **`/insights`** [2A F10] | Native session-pattern + friction report = the inline-pattern inventory |
| Judge / cycle-verdict | **`prompt`-type hook / Haiku judge agent** [2A #32] | Fresh-evaluator drift-detection (Lens 5 CycleVerdict) |
| Surfacing | **Telegram MCP reply + output-to-disk** | The existing user-visible channel + convention |
| Same-session artifact reload | **`/reload-skills`** [2A F12] | Applies the SKILL update without a restart |
| Feature-surface viewer (human) | **`/release-notes`** [2A F11] | Native changelog viewer for Luke's own read |

**The thesis-test:** if loam can't build its own capability-adoption loop
mostly out of Claude-native primitives, the "adopt the primitives" thesis is
weaker than claimed. This design uses **10 named native primitives** for the
loop's own machinery — the loop is itself the first adopter.

---

## 6. F2 — Ruthless Feedback on the loop design

**Disagreement (with a naive "just schedule a monthly re-review"):** monthly
is too slow against a weekly release cadence and was *already proven*
insufficient — the awareness SKILL went stale + wrong (missing
`MessageDisplay`, partial frontmatter list) at 17 days [P1 P2]. **Evidence:**
P1 §12 (weekly cadence), P1 P2 (concrete staleness deltas). **Alternative:**
weekly floor + event triggers, as designed.

**Disagreement (with "auto-apply adoptions to move fast"):** the recent
incident was un-verified hooks interacting [task brief]. Auto-applying any
behavior-changing adoption would re-create exactly that failure mode at
machine speed. **Evidence:** the F2 guard in the brief + [2A] §G. **Alternative:**
the auto-apply allowlist is strictly *documentation edits* (matrix + SKILL +
logs); every behavior change (hook/skill-install/job/settings/⚠-row) is
owner-gated. The loop moves fast on knowledge, slow on behavior.

**One thing flagged, not assumed:** whether a **cloud Routine** can reach
loam's private doc-research targets and write back the delta report to the
local repo is unverified (Routines run on a fresh clone w/ no local file
access [2A #77]). If a Routine can't commit to the local tree, the surface-
refresh leg must be launchd-local too, and the cloud-Routine advantage
(survives machine-off) is forfeited for the write-back step. **Resolution
path:** prototype the Routine's repo write-back before committing to the
split-scheduler design — owner-gated, flagged here, not silently assumed.

---

## 7. What's owner-gated (explicit — nothing below is built here)

This doc designs; it implements nothing. Each item is a follow-on build:
1. The weekly **scheduled job(s)** — Routine and/or launchd plist.
2. The **event-trigger** wiring (version-bump compare + changelog-hash).
3. The loop's **dispatch brief / subagent definition** (the 3 sub-passes + judge).
4. The **`shell:` dynamic-injection** edit to the awareness SKILL.
5. The **auto-apply allowlist enforcement** (which edits the loop may make unattended).
6. The prerequisite **skills-fate decision [P1 P0 / 2A F2/#62]** — the loop
   maintains the matrix, but the *first* matrix-actioned build (install-vs-
   retire) is its own owner-gated cycle.
