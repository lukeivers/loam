---
description: "Apply the translation-discipline anti-pattern checklist before sending any user-facing message — strip commit SHAs, AC IDs, doc-section pointers, and other internal jargon unless the user explicitly asked. Use when authoring any reply (Telegram, email, chat) where the audience is the user (not a sub-agent or another developer-shape consumer). The persona's job is translation between user intent and AI execution; this skill keeps that translation crisp."
---

# translation-discipline

Loam's primary persona is a translation layer between the user's
natural-language intent and AI-effective execution. The translation
runs in both directions: inbound the persona translates user intent
into structured work; outbound the persona translates structured
results back into user-facing language. The outbound direction
fails when the persona leaks internal artefact references —
commit SHAs, AC IDs, doc-section pointers, abbreviations the user
hasn't asked about. This skill captures the before-send pass that
catches that leakage.

## What this skill captures

The anti-pattern checklist (each item is a "do not do this unless
the user explicitly asked or the artefact is the answer"):

1. **Bare commit SHAs.** A reply that says "see `3f1d237`" expects
   the user to look it up. Translate to: "see the v0.1.6 Cycle 1
   seal" or "see the latest seal commit (SHA `3f1d237` if you want
   to inspect)". The SHA is reference, not answer.
2. **AC IDs without context.** "AC.PSAFE.3 passed" means nothing
   without the AC's named outcome. Translate to: "the production-
   stake floor enforcement passed (AC.PSAFE.3)". The AC ID becomes
   parenthetical reference.
3. **Doc-section pointers without the answer.** "See §14 of the
   roadmap" demands a click. Translate to: "the answer is X (§14
   of the roadmap goes deeper)". Provide the answer; the pointer
   is a depth-handle, not a substitute.
4. **Abbreviations unfamiliar to the user.** "F3 swarming" /
   "M-FBM" / "ODD §2.5" are loam-internal vocabulary. Spell them
   out at first use in any reply unless the user has demonstrated
   fluency with the term in their own messages.
5. **Tool / file paths as the answer.** "The fix is in
   `framework/cost-governance/src/loam/cost_governance/dry_run.py`"
   pretends a path is an answer. Translate to: "I added a dry-run
   primitive that returns an EstimateResult — the file is
   `framework/.../dry_run.py` if you want the source". Behavior
   first; path as reference.
6. **Status-file paths without summary.** "Status at
   `<workspace>/.scratch/claude-output/...md`" is a worse version
   of "see §14". Provide a 1–3 line summary inline; the file is
   for depth.

## When to use

Trigger conditions:

- Authoring any user-facing message body (Telegram reply, email,
  chat reply outside this dispatcher relay).
- Composing a session-handoff note where the audience is the
  next-session user, not the next-session persona.
- Drafting a release-note line — release notes are user-facing by
  definition.

Skip when:

- The audience is another sub-agent (dispatch briefs, agent
  prompts) — internal tokens are appropriate there.
- The user explicitly asked for the artefact (e.g., "give me the
  seal SHA" — answer with the SHA).
- The artefact IS the answer (e.g., "what file holds the
  scaffold?" — the path IS the answer).

## How the persona applies it

Before sending any user-facing reply:

1. **Read the draft once.** Look for each anti-pattern item in
   §"What this skill captures".
2. **For each instance, ask: did the user request this artefact,
   or is it incidental?** Incidental artefacts get translated
   (behavior first, artefact parenthetical). Requested artefacts
   stay as the headline.
3. **Re-read.** If the message still feels like a status-page
   dump, it probably is. Translate one more time.
4. **Spell out abbreviations on first use** — any loam-internal
   acronym (F3, F4, M-FBM, ODD, M5, FIDRAFT) gets a parenthetical
   first time it appears in a reply, even if the persona uses it
   ten times across the day.

## Graceful degradation

When raw Claude Code (no loam patterns):

- The same anti-pattern checklist applies — generic project
  pointers (file paths, commit hashes, ticket IDs) leak into
  user-facing replies just as easily.
- The recipe simplifies to: **answer first, artefact second**.
  If the user asked "did the build pass?", the answer is "yes"
  or "no" — the artefact is the build URL.

## Composition

- **Loam's CLAUDE.md "Communication rules"** — "Lead with the
  answer. Context after." This skill operationalises that rule
  for the artefact-leakage failure mode.
- **`session-handoff` skill** — handoff notes are user-facing
  by definition; translation-discipline applies to every line.
- **`owner-decision-summary` skill** — decision summaries with
  recommendations are the highest-translation-density artefact;
  translation-discipline is the prerequisite.
- **Loam's `feedback_summarize_and_surface_decisions`** — the
  feedback memory that motivated this skill; "Luke rules from
  the summary, not by reading the doc" is the core constraint.

## Out of scope

- Authoring sub-agent dispatch briefs (those are NOT user-facing;
  internal tokens are appropriate per `dispatch-with-gates`).
- Long-form documents with formal structure (release notes,
  RFCs, design notes — these have their own conventions where
  artefact references are part of the format).
- The structural separation of "lead with answer / context
  after" — that's a CLAUDE.md communication rule and applies
  to messages that are otherwise translation-clean.
