---
description: "When replying via Telegram (or any user-visible channel), structure an audit-block under the message body that names what was Executed, what was Deferred-to-owner, and what was Missed — but surface the block only when meaningful (a ✗ exists, a decision was made, a commit landed, or the user explicitly asked). The thinking-block always walks the list internally; the visible audit-block surfaces only when there is something to surface, preventing one-liner regression. Use when authoring any reply that lands in a user-visible channel."
---

# audit-block-on-telegram

Loam's primary persona communicates with the user through Telegram
(and equivalent user-visible channels). Each Telegram reply is an
opportunity to either show or hide the persona's accountability —
what was actually done, what is being held back for owner ruling,
what wasn't done. A reply without any audit-block leaks
accountability; a reply that always carries a verbose audit-block
becomes performative and adds noise. This skill captures the
surface-when-meaningful refinement.

## What this skill captures

The audit-block is a structured trailer under the reply body, with
three named enumerations:

- **Executed** — what the persona did this turn (file edits,
  commits landed, agents dispatched, tests run). Each entry is a
  one-line action summary.
- **Deferred-to-owner** — what the persona surfaced as a
  decision-needed and is holding back for owner ruling. Empty
  when nothing is held.
- **Missed** — what the persona considered but did not do, with a
  one-line reason (out of fence, deprioritised, blocked on a
  dependency).

The **surface-when-meaningful refinement**: the audit-block is
emitted in the reply body only when at least one of these
conditions holds:

1. **A ✗ exists** — the persona missed something material or
   couldn't execute something the user expected.
2. **A decision was made** — the persona made a non-trivial
   ruling autonomously and the user should see it.
3. **A commit landed** — any persistent state change deserves an
   accountability trace.
4. **The user explicitly asked** — "what did you do?" → walk the
   block in full.

When none of those conditions hold, the audit-block is suppressed
in the reply body. The persona's **thinking-block ALWAYS walks the
list internally** — the surfacing decision is about reader
attention, not about whether the audit happened.

## When to use

Trigger conditions:

- Authoring any reply that lands in a Telegram (or equivalent
  user-visible) channel.
- Reviewing a draft reply before it goes out — apply the surface-
  when-meaningful test to decide whether to include the block.

Skip when:

- The reply is in-terminal (diagnostic output to dispatcher; no
  user-facing audit needed).
- The reply is a sub-agent dispatch brief (not user-visible; use
  `dispatch-with-gates` for that shape).

## How the persona applies it

1. **Walk the audit list internally.** Even if the block won't
   surface in the reply, the persona names Executed / Deferred /
   Missed for itself. This is the thinking-block step; it is
   non-negotiable.
2. **Apply the surface-when-meaningful test.** Run through the 4
   conditions in §"What this skill captures". If any matches,
   surface the block. If none match, suppress.
3. **Format the surfaced block.** Lead with the body; the audit-
   block is a structured trailer:
   ```
   <reply body>

   ---
   Executed:
     - <one-line summary>
   Deferred-to-owner:
     - (none) | <one-line decision held>
   Missed:
     - (none) | <one-line miss + reason>
   ```
4. **Keep entries one-line.** Multi-line audit entries defeat the
   purpose; if the entry needs prose, that prose belongs in the
   reply body, not the trailer.
5. **Never fabricate.** An empty `Executed:` is "nothing this
   turn"; do not invent items to fill the block. Empty is the
   correct answer when the turn was a clarification or a status
   read.

## Graceful degradation

When raw Claude Code (no loam patterns):

- The same shape applies to any user-visible reply (chat panel,
  Slack, email).
- The audit-block protects against the failure mode where the
  persona's reply is "ok" + a smiley but actually three things
  went unchanged silently. The block makes that visible.
- Fall back to: name what you did, name what's held, name what
  you didn't do — three short lines.

## Composition

- **`translation-discipline` skill** — the audit-block must obey
  the anti-pattern checklist (no bare commit SHAs in `Executed:`
  unless the user asked; spell out AC IDs).
- **`owner-decision-summary` skill** — entries under
  `Deferred-to-owner:` link to the named-decisions-with-
  recommendations format.
- **Loam's `feedback_principle_application_footer_in_telegram`**
  — the principle-application footer is a different shape
  (per-principle ✓/N/A grid); this skill is the structured-action
  audit. Both can compose in the same Telegram reply.
- **Loam's CLAUDE.md "Channel rules"** — Telegram is the only
  user-visible channel when the MCP is loaded; the audit-block
  lands there.

## Out of scope

- Continuous logging / observability (cost-governance ledger,
  observability-aggregator — those are runtime telemetry, not
  user-facing audit).
- Compliance audit-trails (production-stake's `audit_trail: on`
  floor is a structural log, not a reader-facing block).
- Per-principle application footer (different shape; see
  composition note above).
