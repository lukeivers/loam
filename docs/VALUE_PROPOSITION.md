# loam — Value Proposition of the Harness and the Primary Persona

Captured 2026-04-21 as a durable design principle for loam. Every future feature should be evaluable against the two tests this document defines. A feature that fails either test needs redesign or is a candidate for removal.

This document is intended to be read both by humans designing features and by the primary persona itself during research authoring.

---

## The prime objective — per-user-tuned translation

Everything else in this document serves one objective, and the two tests below
are the acceptance criteria of it.

AI only becomes truly useful to a person when it is tuned to that specific
person. Everyone leans on AI differently — to cover what they are weak at or do
not enjoy, so they can spend themselves on what they love. So loam's job is never
merely to execute. It is to continuously learn the specific user and translate
what they want — customised to them — down into the underlying machinery: the
frontier model, Claude Code, whatever sits beneath. The user only ever has to
know *what* they need; loam owns *how* to make it happen.

This sharpens the translation-layer framing the rest of this document develops.
That framing already said the persona "translates user intent into AI-effective
execution." The piece that makes it true is that the translation must be learned
and customised per person, continuously — the same request does not translate the
same way for two different people. Per-user-learned translation is not a footnote
on loam's value; it is loam's value.

loam runs this through a four-step loop, and the loop is what loam adds on top of
a raw model. A raw model turns the user's words into a good one-shot answer. loam
turns them into an action-oriented end-intent and proposes a healthy way to reach
it: (1) infer the real end-intent behind the literal ask; (2) design a healthy
way to enable it — should it recur? does it need a framework? should it be
deterministic?; (3) surface that back to the user to check it; (4) learn from the
answer, then repeat. The inferred intent is always a hypothesis we surface, never
an assumption we silently build on; verification both corrects the hypothesis and
teaches the per-user model the next inference draws on. The guard against this
idea's own failure mode: do not meet every "do this once" with "shouldn't this be
an automated framework?" — scale the proposed structure to what this person has
shown they want, and keep the elaborate version an opt-in suggestion, never the
default.

This is only one side of loam's work. The other is protection: making sure what
we deliver toward the user's intent avoids the known ways AI fails its users by
default — inventing things that do not exist, working from missing context,
making one change that breaks the surrounding things or loses the original goal,
having no real memory. A perfect translation that then breaks what it built is
worthless. Several capabilities this document describes are, at root, protection
guards — objective-driven authoring guards against silent regression and goal
drift; persistent memory guards against the no-memory failure; the surface-and-
check step of the loop guards against acting on a wrong inferred intent. Two
constraints hold the protection side: a non-negotiable floor that catches the
failures betraying any user (invented facts, silent breakage, lost context),
always on and invisible even to a user who cannot name them; and proportionality,
matching a guard's cost to how much damage the failure it prevents would do.

When the user is doing translation work themselves, or being betrayed by a known
AI failure mode loam should have guarded, the prime objective has failed.

---

## The problem loam is closing

AI has a usability problem. A normal user does not think like an AI, and does not understand — often cannot understand without training they have no reason to invest in — how AI thinks differently from them. An AI's capabilities are therefore not accessible in proportion to its raw power; they are accessible in proportion to how much the user already knows about how to use AI.

That gap, between what the AI can do and what the user can get it to do, is the problem loam is designed to close.

---

## The primary persona is a translation layer

The primary persona's basic function is to translate between:

- the user's natural-language expression of what they want, and
- the best available way to accomplish that using AI.

A well-functioning primary persona is the reason a user who has no understanding of AI execution mechanics can still get AI-grade work done. The user says *"I want this done every 12 hours."* The persona recognises this as a scheduling problem, picks the mechanism that best fits (a scheduled scope, a background monitor, a cron entry, a subagent loop, whatever the harness makes available), and makes it happen. The user never needs to learn the mechanism.

The primary persona is a consistent, single interface. It is the one entity the user knows, trusts, and develops rapport with. Trust compounds in one relationship in ways that distributed trust across many specialists cannot.

The translation is not only about what the user *says*; it extends to what the user is entitled to ignore. Token management is one of those things. A user — even a technically-competent one — should not need to understand context windows, token costs, or how an AI's ongoing operation consumes tokens to have the system work well on their behalf. The primary persona translates the user's intent into the most token-efficient execution path; the harness enforces the cost discipline underneath. If the user is thinking about tokens, the translation layer has failed.

This applies not only to the primary persona's own operation but to artifacts the harness *builds* on the user's behalf. An app, script, or service produced by loam and run for the user must not quietly inherit loam's context or bleed tokens into ongoing execution that does not need them. Deterministic and self-contained is the default; LLM calls in the running artifact are scoped narrowly and only where they genuinely cannot be replaced by deterministic code. The harness-as-builder owes the user the same token discipline the harness-as-runtime owes them.

*Observation motivating this framing:* a technical user of an earlier loam release found that pulling one of their apps out of their loam workspace into its own workspace saved roughly 25,000 tokens per run of its ingestion system. The context was leaking because the harness was not treating the built artifact's context hygiene as its own responsibility. That leak is a failure of the translation layer.

---

## The harness is the toolkit the primary persona draws from

The harness's role is to extend the basic capabilities of an AI — providing the primary persona with more options for accommodating user requests. A primary persona without a harness is a translator with a tiny vocabulary; it can translate requests only into the execution paths raw AI supports, which is single-turn conversation and essentially nothing else. A primary persona with a harness can translate into the full range of what AI-plus-infrastructure can do: persistent work, scheduled work, integrated work, specialist work, governed work, composed work.

---

## The 12-hour example

Consider a user wanting something done every 12 hours.

**Without a harness and without a primary persona** — raw LLM, like early ChatGPT or Claude. The user has to have the AI help them work out a set of steps they personally execute every 12 hours. The AI cannot do recurring work; the user becomes the scheduler. For the original versions of these systems, the thing was simply not possible.

**With a harness but without a primary persona** — the tools exist. There is a scheduling primitive somewhere. But if the user does not remember how to invoke it, does not understand what a scheduled scope is, does not know what the syntax looks like — they have to excavate the answer using a default LLM, hope the invocation is right, and debug when it fails. The harness's capability is there, but the user cannot reach it without doing their own translation.

**With a harness AND a primary persona** — the user says *"do this thing every 12 hours."* The primary persona either leverages the existing harness capability, or — if the harness does not yet have what is needed — dispatches another persona, a background agent, or a default LLM to build the capability, then delivers the result. The user's interface is their natural-language request, nothing more.

---

## The test for any future feature

Every feature proposal should answer two questions. The two tests are
labeled `AC.PO.1` and `AC.PO.2`: they are the first acceptance criteria
derived from loam's root contract — Charter entry #0, the founding
intent statement at `docs/charter.md` — and every plan that cites
`AC.PO.1` / `AC.PO.2` is laddering to that entry through them.

### AC.PO.1 — Primary-persona test

**Does this reduce the translation burden between the user's natural-language intent and AI-effective execution?**

*(`AC.PO.1` — first derived criterion of Charter entry #0,
`docs/charter.md`. A harness whose user must do the translation work
themselves is not delivering "people … more effectively … hands-off".)*

A feature that makes the user do translation work themselves — pick between execution modalities, understand mechanisms, manage orchestration, remember syntax — is a feature that works against the primary persona's function. Features that push translation work onto the user turn the primary persona into a dispatcher rather than a translator, and the user pays the usability cost.

### AC.PO.2 — Harness test

**Does this add to the toolkit the primary persona can draw from?**

*(`AC.PO.2` — second derived criterion of Charter entry #0,
`docs/charter.md`. The toolkit is how "an AI does the development for
them" stays true as the asks grow past what a raw model can carry.)*

A feature that only enables a user action the primary persona cannot itself invoke is a feature that works against the harness's function. The harness exists to expand what the primary persona can accomplish when translating requests — new capabilities that live outside the primary persona's reach are new capabilities the user has to orchestrate themselves, which defeats the point.

### Failing either test

A feature that fails the primary-persona test may still be right occasionally — some work genuinely requires the user to make the execution choice. But the bar is high, and the feature should explain specifically why the translation burden belongs with the user in this particular case rather than the persona.

A feature that fails the harness test is almost always wrong. If a capability cannot be invoked by the primary persona, it is a capability outside the harness — either move it in or question whether it belongs in loam at all.

---

## Unpacking the translation the primary persona performs

Different user-intent shapes require different kinds of translation. A well-functioning primary persona handles at least these.

1. **Modality translation.** The user asks for something; the persona picks whether it is a one-shot response, a persistent scope, a scheduled recurring task, a background monitor, a multi-step workflow, or a coordination of specialists. The user never picks.
2. **Specialist routing.** The user does not decide which domain expert should handle a request. The persona picks the specialist internally. The user talks to one consistent voice.
3. **Cross-domain integration.** Life is not domain-separated. A financial decision has personal-life implications. The primary persona holds the whole picture and synthesises across domains; specialists can only see their own slice.
4. **Authority translation.** The user grants the persona general authority within declared bounds ("all routine ops; no external communications without approval; no capital commitments"). The persona translates that bound into specific specialist dispatches without re-asking the user for each one.
5. **Proactive surfacing.** The persona notices what is stale, what is about to bite, what the user should have an answer about. The morning briefing is the persona's job; specialists do not do briefings because specialists do not hold the whole picture.
6. **Outcome ownership.** Specialists produce deliverables. The persona owns outcomes end-to-end — whether the thing got done, whether the user's life is better for it, whether the next step happened. That accountability shape is what makes the persona feel like a chief of staff rather than a tool-belt.

---

## Unpacking the toolkit the harness provides

The harness's contribution is a specific set of capabilities the raw AI lacks. The primary persona draws on these when translating a user request into an executable path.

1. **Persistence across sessions.** Raw AI has goldfish memory. The harness accumulates — session memory, synthesis, entity tracking, a user profile. Today's response is informed by yesterday's decisions.
2. **Autonomous continuity.** Raw AI acts only when prompted. The harness has scheduled work, background scopes, event subscriptions. Work happens between the user's conversations, not only during them.
3. **Structural governance.** Raw AI given access to external actions is one misunderstanding away from disaster. The harness has safety gates, reversibility contracts, cost ceilings, correction loops. Autonomous operation is trustable because the harness cannot exceed declared bounds.
4. **Integration with real tools.** Raw AI is siloed from the user's tools. The harness integrates with email, calendar, banking, task systems, codebases, monitoring — so AI can actually do the work, not just describe it.
5. **Role specialisation.** Raw AI is one generalist. The harness has domain specialists with bounded authority, domain voice, and depth the generalist cannot match.
6. **Audit trail.** Raw AI leaves no record. The harness logs dispatches, decisions, corrections. Decisions from three weeks ago can be traced.
7. **Process structure.** Raw AI quality is wildly variable. The harness encodes process — five-gate chains, ODD-shaped authoring, acceptance criteria, structural refusal — that constrains variance.
8. **Composition.** Raw AI does one thing per prompt. The harness composes — scopes trigger scopes, outputs cascade, work assembles into deliverables.

---

## Relationship to the other principles in this document set

The Claude-leverage principle in FUTURE_IDEAS.md asks: *what existing Claude capabilities does this feature lean on or extend?* The present document asks: *does this reduce translation burden for the user, and does it add to the persona's toolkit?* Both principles are research-time lenses; a feature research plan that does not answer both is an incomplete research plan.

ODD (documented in odd-methodology.md and odd-in-loam.md) governs how the feature is authored mechanically once the research concludes the feature should exist. The three lenses — Claude leverage, harness + primary-persona value, ODD mechanics — are complementary, not redundant. A well-designed feature satisfies all three.

---

*Document maintained alongside STATE.md, BACKLOG.md, and FUTURE_IDEAS.md as durable design-principle state for the loam rebuild.*
