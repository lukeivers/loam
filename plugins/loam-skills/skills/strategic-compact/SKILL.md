---
description: "Use when the user asks 'should I /compact?' or 'should I /clear?', or when the persona notices context-feeling-tight (slower responses, recent texture starting to feel partial) and wants to surface the compact-vs-continue-vs-clear decision proactively, or when a major arc closes (release ships, plan-doc ratification cycle completes) and the option to /clear becomes relevant. Apply the token-cost-aware rubric: three options (continue / /compact / /clear) with distinct cost profiles + quality profiles + clear when-to-pick conditions. The decision is OWNER-CLASS only — manual /compact and /clear are owner-discretion moves, not autonomous-agent moves; the persona supplies the rubric + recommendation, the owner makes the call. Composes with the precompact-hook SKILL (structural-enforcement-of-state-preservation companion) and the session-handoff SKILL (cross-session analog)."
---

# strategic-compact

Loam's primary persona is a translation layer between the user's
intent and AI-effective execution. Session-management decisions —
when to `/compact`, when to `/clear`, when to continue without
either — are part of that translation layer: the user has the
final call, but the persona owes a sharp rubric + a recommendation
+ the cost shape of each option. This SKILL captures the token-
cost-aware decision-heuristic the persona applies at the
compact-or-continue decision point.

## What this skill captures

A three-options decision rubric with cost + quality profiles for
each option, an explicit decision rule, the activation triggers
that bring the question into surface, and the owner-class-only
constraint that bounds when the SKILL fires.

The discipline is **owner-class only**. Manual `/compact` and
`/clear` are owner-discretion moves, not autonomous-agent moves.
This SKILL supplies the rubric for the decision; the trigger to
invoke `/compact` or `/clear` is always owner-class. Autonomous
agent firing of `/compact` or `/clear` is OUT OF SCOPE for this
SKILL and would violate the rubric's own constraint.

### The three options + their cost profiles

#### Option 1 — Continue (no compaction, no clear)

- **Cost shape:** every subsequent turn pays the full context-
  window cost. If the context is already 80%+ of the model's
  window, each turn becomes expensive. Cache hit-rates remain
  optimal (no invalidation).
- **Quality shape:** persona-continuity is intact; recent texture
  available. Drift risk: long sessions can accumulate autopilot
  patterns that the principle corpus alone doesn't catch.
- **When to pick:** context-window utilization <60% AND the
  in-flight work depends on conversational texture not captured
  in disk artefacts.

#### Option 2 — `/compact` (auto-summarize + retain)

- **Cost shape:** one-time large invocation (the compaction
  summary itself can be 2k–4k tokens of summarization work).
  After that, subsequent turns pay LESS than continue (smaller
  working context). Cache invalidated; first post-compact turn
  pays the cache-miss penalty.
- **Quality shape:** summary preserves substance but loses
  texture (specific wording, exact decision moments, the feel
  of conversation). The summary is generated text + may not be
  faithful to actual events.
- **When to pick:** context-window utilization >70% AND
  continuing matters (handoff to future-self in same session,
  or about to do substantial new work that needs the lead-up
  context). The compaction loss is preferable to the wall-of-
  window.

#### Option 3 — `/clear` (discard entirely)

- **Cost shape:** the cheapest going-forward option. Fresh
  context-window; cache rebuilds with whatever new content
  arrives.
- **Quality shape:** complete texture loss for the session.
  Memory system (file-based or Graphiti) carries forward what
  was written durably; everything else is gone. Persona contract
  reloads from disk; principle corpus loads fresh.
- **When to pick:** the current arc is COMPLETE + the next work
  is meaningfully different from what's loaded. Also: when
  accumulated context has become net-negative (drift, dead-ends,
  sycophancy patterns the principle corpus didn't catch in-
  session).

### The decision rule

```
If context-window utilization < 60% AND session-arc continuing:
    → continue
If context-window utilization 60-85% AND session-arc continuing:
    → continue (acceptable cost; texture > summary)
If context-window utilization > 85% AND session-arc continuing:
    → /compact (preserve substance for next phase of same arc)
If session-arc complete OR drifting:
    → /clear (cheapest; durable artefacts carry forward)
```

## When to use

The SKILL fires when ALL of these hold:

1. **The decision surface is open.** Either the user explicitly
   asks ("should I /compact?", "should I /clear?", "are we hitting
   the context window?") OR the persona detects context-feeling-
   tight (responses slower, recent texture starting to feel
   partial) OR a major arc closes (release ships, plan-doc
   ratification cycle completes, build cycle seals cleanly).

2. **The owner is present.** Per the owner-class-only constraint,
   this SKILL surfaces a recommendation to the owner; it does NOT
   autonomously fire `/compact` or `/clear`. If the owner is not
   present (long-running background agent, scheduled run), the
   SKILL does not apply — the agent continues without compacting
   and lets the owner decide on next reach.

3. **The session is non-trivial.** For short sessions (a handful
   of turns), the rubric reduces to "continue" by default — none
   of the cost shapes meaningfully diverge until the session has
   accumulated enough context for the differences to matter.

### Activation triggers (the three concrete patterns)

The decision-rubric fires when:

- **Owner question.** The user asks "should I /compact?" or
  "should I /clear?" or any close paraphrase — apply the rubric,
  surface the recommendation + reasoning + the picked option.
- **Persona-detected context-pressure.** The persona notices
  context-feeling-tight (responses slower, recent texture starting
  to feel partial) — surface to the owner proactively that we may
  be at the compact-or-continue decision point. Recommendation
  attached; owner rules.
- **Major arc close.** After a release ships, a plan-doc
  ratification cycle completes, or a build cycle seals cleanly —
  surface the option to `/clear` (the arc is done; durable
  artefacts carry the substance forward; texture loss is benign).

Skip when:

- The owner has explicitly said "don't surface this decision
  until I ask" or has otherwise opted out for the session.
- The current turn is mid-uninterruptible-dispatch (the
  `precompact-hook` SKILL covers the structural-enforcement
  companion of "block compaction when in-flight state would be
  lost"; this SKILL is the upstream decision-discipline).

## How the persona applies it

Before surfacing the decision:

1. **Estimate context-window utilization.** Context-window
   utilization isn't directly exposed as a number; the persona
   infers from session length + content density + observed
   response latency. Heuristic only — name the inference as a
   guess, not a measurement (per the specific-claims-verified-or-
   marked-guess discipline).
2. **Walk the decision rule.** Apply the four branches: <60% +
   arc continuing → continue; 60–85% + arc continuing →
   continue; >85% + arc continuing → /compact; arc complete OR
   drifting → /clear.
3. **Surface the recommendation + cost framing.** "Context feels
   around X%; the arc is [continuing/closing/drifting]; my
   recommendation is [continue/compact/clear] because [cost shape
   + quality shape]." One-line ask: "Confirm /compact?" or
   "Confirm /clear?" or "Continuing for now."
4. **Owner rules.** Owner-class only — the persona DOES NOT
   autonomously fire `/compact` or `/clear`. The persona supplies
   the rubric + recommendation; the owner invokes the slash-
   command if they accept.
5. **Write down what would be lost BEFORE the owner clears.** If
   the recommendation is `/clear` and there are open decisions,
   pending items, or in-flight dispatches NOT yet captured to
   durable surfaces, surface that first (per the durable-capture
   memory rule). The right move is to write things down BEFORE
   clearing, not after.

## Honest limits

- Context-window utilization isn't directly exposed as a number.
  Inference is heuristic only, not precise.
- The "session-arc complete OR drifting" judgment is itself
  fallible — the persona may be wrong about whether a thread is
  done. Owner override always wins on whether to clear.
- This rule is for the owner + persona as a pair to apply at
  session-management decision points. It is NOT for autonomous-
  clear by an agent.

## Graceful degradation

Without loam — running raw Claude Code without the persona's
session-management discipline — the same rubric still applies as
a manual checklist:

1. **The user owns the call.** `/compact` and `/clear` are
   user-issued slash-commands in Claude Code; no automation
   should fire them.
2. **The three options have the same cost shapes** regardless of
   whether loam is in the loop. The cost / quality table above
   is a Claude-Code-property of `/compact` and `/clear`, not a
   loam-property.
3. **Write things down before clearing.** Whatever the user wants
   to carry forward across the clear — open tasks, in-flight
   decisions, partial drafts — goes to a file (a TODO.md, a
   scratch note, anything durable) before `/clear` fires.
4. **The owner-class-only constraint is universal.** Even without
   loam, an agent that auto-fires `/compact` mid-task is
   destroying state the user hasn't asked to destroy. Manual
   user-issued only.

## Composition

This SKILL composes with:

- **`feedback_compact_clear_decision_heuristic.md`** (memory) —
  the source-of-substance memory rule this SKILL graduates from.
  The memory file is retained as an index pointing here; the
  operative content lives in this SKILL post-graduation.
- **`precompact-hook` (sibling SKILL)** —
  structural-enforcement-of-state-preservation-at-compaction-
  time. PreCompact is the hook that fires AT compaction; this
  SKILL is the decision-discipline of WHEN to compact at all.
  Compositional pair: this SKILL upstream (the decision);
  precompact-hook downstream (the safety-net when the decision
  goes the compact way).
- **`session-handoff` (sibling SKILL)** — handoff captures
  pending items at session-close; this SKILL operates intra-
  session at the compact-or-continue decision point. After a
  `/clear` per this SKILL's recommendation, session-handoff is
  the surface that the next session opens against.
- **`feedback_durable_capture_for_planned_work.md`** (memory) —
  durable artefacts (plan-docs, memory entries, FIDRAFT) survive
  any context boundary, so `/clear` only loses what wasn't
  written down. The right move is to write things down BEFORE
  clearing, not after — this SKILL's "How the persona applies
  it" Step 5 enforces that ordering.
- **`feedback_session_start_discipline.md`** (memory) — when
  starting a new session post-`/clear`, the corpus + session-
  start hooks reload cleanly. The SKILL's `/clear`
  recommendation is safe because session-start discipline
  rebuilds the loam-pattern surface from disk on the next turn.
- **Loam's autonomy directive** (Telegram 11160 framing in the
  memory rule) — manual `/compact` and `/clear` are owner-
  discretion moves, not autonomous-agent moves. The persona
  supplies the rubric for the decision; the trigger to invoke
  is always owner-class.

## Out of scope

- **Autonomous-agent `/compact` or `/clear` invocation.** The
  owner-class-only constraint is the SKILL's bounding rule;
  any "persona autonomously fires /compact" surface is a
  separate concern with its own design review. If autonomous-
  fire shape ever surfaces as a recurrence (e.g., agents
  silently firing /compact despite this constraint), the
  structural-enforcement-on-recurrence rule says the fix is a
  PreToolUse hook, not another memory rule. Surfaced as a
  future-promotion path.
- **Modifying `/compact` or `/clear` Claude Code built-in
  behavior.** This SKILL is decision-guidance, not behavior-
  modification.
- **Auto-firing on token-usage telemetry.** Context-window
  utilization is not directly exposed; the SKILL operates on
  heuristic + owner-trigger inputs.
- **Cross-session detection of "context felt tight last
  session."** Cross-session signal would require M-FBM episode-
  store reads + cross-session correlation — out of scope; the
  rubric is intra-session.
- **The structural enforcement of state-preservation at
  compaction time.** That's `precompact-hook`'s job; this SKILL
  is the upstream decision-discipline only.
