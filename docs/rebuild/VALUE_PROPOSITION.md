# pOS v2 — Value Proposition of the Harness and the Primary Persona

Captured 2026-04-21 as a durable design principle for pOS v2. Every future feature should be evaluable against the two tests this document defines. A feature that fails either test needs redesign or is a candidate for removal.

This document is intended to be read both by humans designing features and by the primary persona itself during research authoring.

---

## The problem pOS is closing

AI has a usability problem. A normal user does not think like an AI, and does not understand — often cannot understand without training they have no reason to invest in — how AI thinks differently from them. An AI's capabilities are therefore not accessible in proportion to its raw power; they are accessible in proportion to how much the user already knows about how to use AI.

That gap, between what the AI can do and what the user can get it to do, is the problem pOS is designed to close.

---

## The primary persona is a translation layer

The primary persona's basic function is to translate between:

- the user's natural-language expression of what they want, and
- the best available way to accomplish that using AI.

A well-functioning primary persona is the reason a user who has no understanding of AI execution mechanics can still get AI-grade work done. The user says *"I want this done every 12 hours."* The persona recognises this as a scheduling problem, picks the mechanism that best fits (a scheduled scope, a background monitor, a cron entry, a subagent loop, whatever the harness makes available), and makes it happen. The user never needs to learn the mechanism.

The primary persona is a consistent, single interface. It is the one entity the user knows, trusts, and develops rapport with. Trust compounds in one relationship in ways that distributed trust across many specialists cannot.

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

Every feature proposal should answer two questions.

### Primary-persona test

**Does this reduce the translation burden between the user's natural-language intent and AI-effective execution?**

A feature that makes the user do translation work themselves — pick between execution modalities, understand mechanisms, manage orchestration, remember syntax — is a feature that works against the primary persona's function. Features that push translation work onto the user turn the primary persona into a dispatcher rather than a translator, and the user pays the usability cost.

### Harness test

**Does this add to the toolkit the primary persona can draw from?**

A feature that only enables a user action the primary persona cannot itself invoke is a feature that works against the harness's function. The harness exists to expand what the primary persona can accomplish when translating requests — new capabilities that live outside the primary persona's reach are new capabilities the user has to orchestrate themselves, which defeats the point.

### Failing either test

A feature that fails the primary-persona test may still be right occasionally — some work genuinely requires the user to make the execution choice. But the bar is high, and the feature should explain specifically why the translation burden belongs with the user in this particular case rather than the persona.

A feature that fails the harness test is almost always wrong. If a capability cannot be invoked by the primary persona, it is a capability outside the harness — either move it in or question whether it belongs in pOS at all.

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

ODD (documented in odd-methodology.md and odd-in-pos.md) governs how the feature is authored mechanically once the research concludes the feature should exist. The three lenses — Claude leverage, harness + primary-persona value, ODD mechanics — are complementary, not redundant. A well-designed feature satisfies all three.

---

*Document maintained alongside STATE.md, BACKLOG.md, and FUTURE_IDEAS.md as durable design-principle state for the pOS v2 rebuild.*
