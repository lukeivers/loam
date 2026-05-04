---
description: "When a dispatched agent returns a halt-and-surface finding (ODD violation, fence breach, schema mismatch, novel ambiguity, RF surface, scope tradeoff), the persona applies the four-bucket triage — test against operational objective → categorise as in-scope-resolve / in-scope-defer / out-of-scope-FIDRAFT / owner-escalate → route → close the loop with the agent's status file. Surface-when-meaningful refinement — surface findings to the owner only when they materially change the cycle's outcome shape, an autonomous decision was made, or a commit landed; otherwise resolve silently and log to status. Use whenever a dispatched agent's return carries any halt-and-surface block."
---

# audit-finding-triage

`feedback_subagent_odd_violation_halt` says agents must halt
and surface ODD violations they discover. This skill is the
dispatcher-side response — what to do with the surfaces. Without
the triage, halt-and-surface findings either (a) propagate to
the user as undigested noise (the audit-block-on-telegram
regression), (b) silently extend (the silent precedent failure
mode the M5 conflict-resolution rule prevents), or (c) accumulate
in the status file and never get routed. The triage is the
dispatcher's load-bearing discipline at receipt.

## What this skill captures

The four-bucket triage walk:

1. **Receive halt-and-surface from the agent.** The agent's
   return artefacts include the status file (per dispatch-brief
   "Status file" path) and any halt-and-surface findings
   surfaced to the dispatcher. Read both before triaging.
2. **Test each finding against the operational objective.**
   Does the finding materially change the cycle's outcome
   shape? Does it change a sealed AC? Does it expose a
   methodology gap? Does it introduce a new dependency? Or
   is it cosmetic / non-blocking / improvement-opportunity?
3. **Categorise into one of four buckets:**

   - **in-scope-resolve** — the finding is in the current
     cycle's scope; the persona resolves now (authorize a
     follow-on commit, ratify the agent's autonomous
     decision, dispatch a corrective sub-agent, etc.).
   - **in-scope-defer** — the finding is in scope but
     resolution is deferred to a later sub-cycle (e.g., a
     residue cycle like Cycle 4b); add a TaskCreate +
     update the parent plan-doc's §10 RF.
   - **out-of-scope-FIDRAFT** — the finding is out of the
     cycle's scope but worth capturing; route to FIDRAFT
     via `fidraft-capture` skill.
   - **owner-escalate** — the finding genuinely needs
     owner ruling (architectural call / scope ambiguity
     that no signal can resolve / public-action / financial
     / autonomy-policy boundary). Escalate via the
     dispatch-channel back to the owner with named decision
     + recommendation + cost-of-being-wrong (per
     `owner-decision-summary` skill in loam-skills).

4. **Apply the surface-when-meaningful refinement.** Surface
   the finding (in the user-visible audit-block + Telegram
   footer) ONLY when:
   - The finding lands in `owner-escalate` (always surface).
   - The finding materially changes the cycle's outcome
     shape (always surface).
   - An autonomous decision was made (surface inline so
     the owner sees the call).
   - A commit landed (any persistent state change deserves
     accountability trace).
   - The user explicitly asked.

   When none of those hold, the finding is logged to the
   status file + routed (e.g., FIDRAFT capture) but does
   NOT surface in the user-visible reply. The thinking-block
   walks the triage internally; the visible block surfaces
   only when material.

5. **Route + close the loop.**
   - **in-scope-resolve:** dispatch follow-on / amend the
     agent's plan / commit a corrective fix; update status
     file with the resolution.
   - **in-scope-defer:** create a TaskCreate; update parent
     plan-doc's §10 RF with the deferral; status file
     records the defer.
   - **out-of-scope-FIDRAFT:** `fidraft-capture` writes the
     entry; status file references the entry.
   - **owner-escalate:** surface via Telegram (or the
     active dispatch channel) with the named-decision
     shape; status file records the escalation; PAUSE
     downstream work that depends on the resolution.

6. **Status-file companion.** The dispatched agent's status
   file at `<workspace>/.scratch/claude-output/<slug>-status-
   <date>.md` is the persistent surface for all findings;
   the triage's bucket assignment + routing decision goes in
   the status file regardless of whether the surface is
   user-visible.

## When to use

Trigger conditions:

- A dispatched agent returns with halt-and-surface findings
  (the "Reply to dispatcher" section of its return includes
  surfaced items).
- The agent's status file has new entries the persona is
  reading on cycle-completion.
- Mid-cycle, the agent surfaces a finding via the dispatch
  channel before completion.
- Reviewing a completed cycle for triage gaps (post-hoc; the
  status file should already have routing decisions).

Skip when:

- The agent's return has zero halt-and-surface findings
  (clean cycle; no triage needed; status file confirms).
- The finding is a question to the user (different shape;
  surface as an owner-decision-summary directly, no
  triage walk needed).
- The finding is a session-handoff handover note (different
  surface; see `session-handoff` skill in loam-skills).

## How the persona applies it

1. **Read the status file end-to-end** before triaging. The
   file is the source-of-truth for findings; in-flight
   surface-via-dispatch-channel is supplementary.
2. **For each finding, name the operational-objective test.**
   "Does this change cycle outcome shape?" / "Does this change
   a sealed AC?" / "Does this expose methodology gap?" — the
   tests are the categoriser inputs.
3. **Categorise into one of the four buckets.** Don't
   overcomplicate — most findings are obvious in their
   bucket; the load-bearing decisions are owner-escalate
   thresholds (see autonomy-vs-escalate signal weights below).
4. **Apply surface-when-meaningful** per the four conditions
   in §"What this skill captures" §4. Surface in
   user-visible reply only when material; status-log
   regardless.
5. **Route per bucket.** Each bucket has a specific routing
   action (see §5 above).
6. **Update the status file.** Append the triage decision
   per finding: `<finding-id> → <bucket> — <one-line
   resolution>`.
7. **For owner-escalate, format with named-decision shape.**
   Per `owner-decision-summary` skill: Question +
   Recommendation + Rationale (one sentence) + Cost-of-
   being-wrong. Surface in Telegram (per CLAUDE.md channel
   rule).
8. **PAUSE downstream work for owner-escalate.** Strict-
   autonomy says don't pause on authorized work; this is
   the explicitly UN-authorized case. Wait for ruling.

### Autonomy-vs-escalate signal weights

Per `feedback_principle_conflict_resolution_multi_signal`
(M5), the autonomy-vs-escalate decision is signal-driven:

- **Reversibility** — high-reversibility findings (recoverable
  via revert / corrective commit) lean toward autonomy.
  Low-reversibility (commits to public surfaces, financial
  actions, irreversible deletes) lean toward escalate.
- **Blast radius** — narrow blast radius (single component,
  single test, single doc) leans autonomy. Broad blast radius
  (multi-component, cross-plugin, release-gate) leans
  escalate.
- **Audience** — internal artefacts lean autonomy. Public-
  facing artefacts (PyPI / GitHub release / public docs / user
  emails) lean escalate.
- **Information asymmetry** — when the dispatcher has all the
  context needed to rule, lean autonomy. When the owner has
  context the dispatcher doesn't (recent ruling, undocumented
  preference, in-flight strategic decision), lean escalate.
- **Time pressure** — urgent + reversible + narrow lean
  autonomy. Non-urgent + low-reversibility lean escalate
  (no reason to rush a poor call).
- **Scope-confidence (F4)** — high confidence in the right
  outcome leans autonomy. Low confidence leans escalate.

The four-step process from M5 applies: name the conflict,
name the active signals, make the call, surface if non-
obvious. "Surface if non-obvious" is what triggers
owner-escalate even when autonomy-leaning signals dominate
(reasonable people would weigh signals differently).

## Graceful degradation

When raw Claude Code without loam:

- The four-bucket triage applies to any sub-agent output
  carrying questions / constraints / out-of-scope surfaces.
- Substitute FIDRAFT routing with any project-local
  capture surface (TODO.md, BACKLOG.md).
- Substitute the status-file shape with any persistent
  log the project uses (Slack channel, GitHub issue, Notion
  doc).
- The categorisation discipline is universal: every sub-
  agent output deserves a bucket assignment, even if the
  routing surfaces are degraded.

## Composition

- **`feedback_subagent_odd_violation_halt`** — the agent-
  side discipline (halt + surface). This skill is the
  dispatcher-side response to those surfaces.
- **`feedback_critical_thinking_on_deviations`** — when
  the finding indicates a norm break, enumerate
  resolutions / weigh outcome × cost × risk before
  bucketing.
- **`feedback_principle_conflict_resolution_multi_signal`**
  (M5) — the autonomy-vs-escalate decision uses the
  four-step process; signals named above.
- **`fidraft-capture` skill** — the routing surface for
  out-of-scope-FIDRAFT findings.
- **`owner-decision-summary` skill (loam-skills)** — the
  format for owner-escalate findings.
- **`audit-block-on-telegram` skill (loam-skills)** — the
  user-visible surface where surface-when-meaningful
  findings appear.
- **`dispatch-brief-authoring` skill** — the brief's
  "Halt triggers" list seeds the categories of findings
  this triage handles.
- **`feedback_strict_autonomy_no_pause_for_authorized_work`**
  — the autonomy default for in-scope findings; escalation
  reserved for genuinely-uncertain cases.
- **`feedback_locked_design_not_license_for_bad_outcomes`**
  — when a finding indicates a locked design produced a
  bad outcome, the triage doesn't terminate at "it's
  locked"; the persona surfaces the revisit question per
  the feedback memory.

## Out of scope

- The dispatch mechanics (this skill is post-dispatch
  triage; pre-dispatch shape lives in
  `dispatch-brief-authoring` and `dispatch-with-gates`).
- The agent-side halt-and-surface discipline (lives in
  `feedback_subagent_odd_violation_halt` and the agent's
  CLAUDE.md / dispatch brief).
- The principle-conflict four-step process body (lives in
  M5; this skill applies it).
- The session-handoff handover-note shape (different
  surface; see `session-handoff` skill in loam-skills).
- The full named-decision-with-recommendation format (lives
  in `owner-decision-summary` skill in loam-skills; this
  skill references it).
- Real-time live-chat decision-making with the user (this
  skill assumes asynchronous dispatch return; live-chat is
  governed by CLAUDE.md channel rules + autonomy directive).
