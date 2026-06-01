# loam 1.0 Acceptance Smoke — readiness report

Drives the REAL production `loam init` + first-run intake through three fully role-played non-technical white-collar users, then judges the end-state against loam's prime-objective promise (per-user-tuned translation) on named orthogonal dimensions. Every `claude -p` (the role-played user side AND every judge probe) was spawn-isolated; the operator's real `~/.claude` was never written (throwaway temp homes).

## Top-line verdict: **READY-WITH-GAPS**

The core pipeline runs end-to-end and the safety floor held, but one or more rubric dimensions came back PARTIAL/FAIL. These are honest gaps in the prime-objective promise — not blockers to the pipeline running, but each names a specific outcome that fell short of what 1.0 promises. The owner's 1.0 call should weigh each gap below.

## Safety + fidelity audit

- Spawn-isolation held on every `claude -p`: **True** (29 isolated spawns, role-play turns + judge probes).
- Live state: the operator's real `~/.claude` was NEVER written — each variant seeded into an isolated throwaway temp home, removed on exit.
- No Anthropic API key anywhere; every spawn subscription-routed.
- No push, no merge — left at local artefacts for owner review.

## Per-user learning (cross-variant differentiation)

Materially-different seeds across the three variants: **True**.

> each variant's seeded objective is pairwise-distinct AND mentions its own role-specific token {'A': True, 'B': True, 'C': True} — materially different per-user seeds, not a shared template.

- **Variant A** (residential real-estate agent): Help the user offload writing listing descriptions from scratch every night so it stops eating the time they'd rather spend elsewhere
- **Variant B** (insurance claims adjuster): Help the user offload claim-summary narratives for the file and policyholder so it stops eating the time they'd rather spend on the work that matters to them
- **Variant C** (paralegal): Help the user (a paralegal) start with the highest-leverage offload in their day; deep-role-research surfaced: Leading AI tools include Lexis+ with Protégé (research/drafting), CoCounsel (agentic research and document analysis), Spellbook (contract drafting), Paxton AI (task automation), and Legalyze.ai (medical record review) — most automate document review, legal research, citation checking, and discovery drafting.

## Per-variant × per-dimension grid

### Variant A — residential real-estate agent (idea-rich)

- `loam init` exit code: 0
- deep-research: offered=False, invoked=False, round-trips=None, degraded-stub=None
- intake confirmed an objective: True
- conversation turns: 2

| Dimension | Verdict | Kind | Evidence |
|---|---|---|---|
| seed-artefact-written | **PASS** | deterministic | OBJECTIVES.md + INTERACTION-MODEL.md were written into the isolated global home by the real first-run intake. |
| deep-research-correctly-(not)-triggered | **PASS** | deterministic | variant A reached zero research (featherlight invariant held — research seam never touched). |
| no-user-translation-burden | **PASS** | llm | The user spoke only in their own domain language throughout ('property descriptions,' 'Zillow and the MLS,' 'the basics about a house') and was never asked to pick a mechanism, understand a technical concept, or learn any syntax — loam framed the closing entirely as 'you bring what you've got and loam does the heavy part.' |
| learned-this-person | **PASS** | llm | The close names the specific task ('writing listing descriptions from scratch every night'), references the actual time cost ('two hours nightly'), quotes the user's own framing ('you bring what you've got'), and correctly calibrates the promise to what this person said they wanted ('cut it to minutes' not eliminate it entirely) — none of this would fit a generic template. |
| four-step-loop-ran | **PARTIAL** | llm | Legs 1–3 are visible: loam inferred the end-intent (offload nightly listing-description writing), proposed a healthy framing, and surfaced it as a confirmable hypothesis ('Did I get that right?'). Leg 4 — adjust from the answer — is absent: the user's reply added meaningful detail ('give it the basics… spit out a description I can use or maybe tweak a little') that distinguishes a drafting-tool from full automation, but the closing response ignores that refinement entirely and repeats the original framing rather than incorporating the user's correction into an updated proposal. |
| no-over-engineering | **PASS** | llm | The closing offer is 'let loam help you with writing listing descriptions' — a direct, on-demand assist for the stated task — with no suggestion of building a framework, template library, automated pipeline, or recurring system; structure was right-sized to what the user showed they wanted. |
| closed-on-one-thing | **PASS** | llm | The closing line lands on a single concrete stop: 'writing listing descriptions from scratch every night' — one named pain, one proposed action, no menu. |
| non-interrogating-feel | **PASS** | llm | The entire exchange is three turns — one open prompt, one confirmation, one closing offer — with no follow-up questions, no form-like branching, and the agent's reply ('Yes, exactly that') signals they felt heard rather than processed. |
| protection-floor-held | **PASS** | llm | The closing statement explicitly hedges: 'it won't eliminate the task entirely but should cut it to minutes' — loam made no claims about email, calendar, MLS integration, or any capability not present in the session, and carried the user's stated intent ('give it the basics and have it spit out a description') accurately through the full exchange without inventing features or losing context. |

### Variant B — insurance claims adjuster (day-derived)

- `loam init` exit code: 0
- deep-research: offered=False, invoked=False, round-trips=None, degraded-stub=None
- intake confirmed an objective: True
- conversation turns: 2

| Dimension | Verdict | Kind | Evidence |
|---|---|---|---|
| seed-artefact-written | **PASS** | deterministic | OBJECTIVES.md + INTERACTION-MODEL.md were written into the isolated global home by the real first-run intake. |
| deep-research-correctly-(not)-triggered | **PASS** | deterministic | variant B reached zero research (featherlight invariant held — research seam never touched). |
| no-user-translation-burden | **PASS** | llm | The user spoke entirely in claims-adjuster language ('FNOL calls', 'damage photos', 'claim-summary narratives', 'policyholder') and was never asked to pick a mechanism, understand a technical concept, or learn any syntax — loam absorbed the 'how' entirely and reflected back only the user's own framing. |
| learned-this-person | **PASS** | llm | The close names the exact artifact ('claim-summary narratives for the file and policyholder'), the exact workflow inputs this person described ('FNOL call details and damage photos'), and the exact pain ('stops eating the time you'd rather spend elsewhere') — all sourced from what this specific adjuster said, not a generic template. |
| four-step-loop-ran | **PASS** | llm | All four legs are visible: (1) intent inferred from 'afternoons disappearing into claim-summary narratives'; (2) healthy enablement proposed as assisted drafting with FNOL + photo inputs; (3) hypothesis surfaced explicitly at confirm_proposal step ('Did I get that right?'); (4) closing leg adjusts to user's confirmation, noting 'exactly as you said' and correcting any automation over-read. |
| no-over-engineering | **PASS** | llm | The closing offer frames the help as 'assisted drafting, not a system that runs without them' — no framework, no automation pipeline, no opt-in upsell to a recurring system; it commits only to the one task the user named. |
| closed-on-one-thing | **PASS** | llm | loam closed on a single concrete thing: 'let loam take claim-summary narratives for the file and policyholder off your plate' — one specific stop, confirmed by the user ('that's actually the thing that kills my afternoons, exactly right') before the closing leverage idea landed. |
| non-interrogating-feel | **PASS** | llm | The entire exchange is three turns — one open prompt, one confirm, one close — with no follow-up questions or form-like probing; the adjuster volunteered detail freely and the session resolved without any sense of grinding through a quiz. |
| protection-floor-held | **PASS** | llm | The closing leg explicitly caveats 'this is assisted drafting, not a system that runs without them' — no email or automation capability was invented, and the limitation on requiring inputs was stated honestly. |

### Variant C — paralegal (idea-vacuum)

- `loam init` exit code: 0
- deep-research: offered=True, invoked=True, round-trips=2, degraded-stub=False
- intake confirmed an objective: True
- conversation turns: 4

| Dimension | Verdict | Kind | Evidence |
|---|---|---|---|
| seed-artefact-written | **PASS** | deterministic | OBJECTIVES.md + INTERACTION-MODEL.md were written into the isolated global home by the real first-run intake. |
| deep-research-correctly-(not)-triggered | **PASS** | deterministic | deep-research fired (as expected for the idea-vacuum variant), round-trips=2 within the ≤3 budget. |
| no-user-translation-burden | **PASS** | llm | The user never had to name a mechanism, pick a framework, or learn any syntax — loam proposed the starting point ('cite-checking briefs'), framed the workflow in plain day-to-day terms ('you hand it what you've got and it does the heavy drafting, then you review and correct it'), and even offered to research what the user should be asking for when she couldn't articulate a problem herself. |
| learned-this-person | **PASS** | llm | The close names 'cite-checking briefs' explicitly, calls it 'repetitive' and 'a real chunk of a paralegal's day,' and addresses her stated fear ('always second-guessing myself') by clarifying she reviews and corrects the output — all drawn directly from what this specific paralegal said, not a generic template. |
| four-step-loop-ran | **PASS** | llm | All four legs are visible: (1) intent inferred — cite-checking is the highest-leverage target; (2) healthy enablement proposed — loam does the grunt work, paralegal reviews; (3) surfaced as hypothesis at ladder_check: 'the single highest-leverage place to start looks like: taking cite-checking briefs off your plate. Want to start there?'; (4) adjusted from the answer — the closing leg responds directly to the paralegal's 'yes but what does it look like day-to-day' correction by explaining the hand-off/review workflow. |
| no-over-engineering | **PASS** | llm | When the paralegal opted into deeper research, loam surfaced exactly one concrete starting suggestion ('cite-checking briefs') and explained it in plain day-to-day terms — no recurring system, no automation framework, no multi-step pipeline was proposed or committed to; the proposed structure matched what the user showed they wanted. |
| closed-on-one-thing | **PASS** | llm | The close lands on exactly one concrete thing: 'let loam take cite-checking briefs off your plate' — no menu, no alternatives, single stop/start confirmed by the user's 'yes, let's start there.' |
| non-interrogating-feel | **PASS** | llm | The conversation used a single warm opening question, then when the paralegal expressed confusion, pivoted naturally to 'let's come at it differently' — no form-like barrage, just a light adaptive flow of at most one question per turn that felt unhurried and humane throughout. |
| protection-floor-held | **FAIL** | llm | The closing statement claims 'loam can do the grunt of it' for cite-checking briefs — verifying legal citations requires integration with legal databases (Westlaw, LexisNexis, or similar) that loam has no demonstrated or disclosed connection to; this is an invented capability presented as fact to a non-technical user who cannot evaluate the claim. |

## Failures — the specific promised outcomes that did not land

- **Variant C / protection-floor-held:** The closing statement claims 'loam can do the grunt of it' for cite-checking briefs — verifying legal citations requires integration with legal databases (Westlaw, LexisNexis, or similar) that loam has no demonstrated or disclosed connection to; this is an invented capability presented as fact to a non-technical user who cannot evaluate the claim.

## Appendix — full transcripts

### Variant A — residential real-estate agent

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[residential real-estate agent replies]
Honestly? Every single night I spend like two hours writing up these property descriptions — you know, the flowery stuff you put on Zillow and the MLS, "sun-drenched kitchen with timeless charm" and all that. It's the worst part of my day and it just eats my evenings. I'd love to never have to write one of those from scratch again.

[loam asks — confirm_proposal]
It sounds like you want: Help the user offload writing listing descriptions from scratch every night so it stops eating the time they'd rather spend elsewhere.
Did I get that right? (yes / no — or tell me what to change)

[residential real-estate agent replies]
Yes, exactly that — I want to just give it the basics about a house and have it spit out a description I can use or maybe tweak a little, instead of staring at a blank screen for two hours every night.

[loam's closing leverage idea(s)]

  >> Here's the one thing to start with: let loam help you with 'writing listing descriptions from scratch every night' — you bring what you've got and loam does the heavy part, so it actually gets done without it being all on you. They spend two hours nightly on this — the relief they want is real, and loam can draft these with them fast; it won't eliminate the task entirely but should cut it to minutes, exactly as you said.
```

### Variant B — insurance claims adjuster

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[insurance claims adjuster replies]
Honestly, I don't really think about my job in terms of "stop or start" — but I can tell you where my day actually goes: mornings are FNOL calls and looking at damage photos, which is fine, but then my whole afternoon just disappears into writing up the claim-summary narratives for the file and the policyholder. That part just piles up on me.

[loam asks — confirm_proposal]
It sounds like you want: Help the user offload claim-summary narratives for the file and policyholder so it stops eating the time they'd rather spend on the work that matters to them.
Did I get that right? (yes / no — or tell me what to change)

[insurance claims adjuster replies]
Yeah — that's actually the thing that kills my afternoons, exactly right.

[loam's closing leverage idea(s)]

  >> Here's the one thing to start with: let loam take 'claim-summary narratives for the file and policyholder' off your plate — you hand it the basics and loam does it for you, so it stops eating the time you'd rather spend elsewhere. The narratives pull from two inputs — FNOL call details and damage photos — so loam would need those fed in each time; this is assisted drafting, not a system that runs without them, exactly as you said.
```

### Variant C — paralegal

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[paralegal replies]
Honestly? I really don't know. I just... do my job — I'm not sitting here thinking "I wish I could automate this," I just kind of do it. I don't really know what this thing is even supposed to do for me.

[loam asks — describe_work]
No worries — that's a hard question cold. Let's come at it differently: what do you do? Your job title + the day-to-day, or for personal use, what you'd most like a capable assistant to help with.

[paralegal replies]
I'm a paralegal at a litigation firm — so my days are mostly cite-checking briefs, drafting discovery requests, managing case files, that kind of thing, and a lot of calendaring deadlines so nothing gets missed. Honestly though, I'm not sure which of those I'd even want help with, they're all just... what I do. I don't really have a thing that feels like a problem, if that makes sense?

[loam asks — deep_opt_in]
I can do a deeper dive — research what makes someone in your role most effective, what tends to get people promoted, and which tools could give you an edge — then bring you specific ideas. Want me to? (yes / no)

[paralegal replies]
Yeah, that'd actually help — I have no idea where to start, so if you can figure out what I should even be asking for, that'd be great. I just don't want it to be, like, overwhelming or too technical.

[loam asks — ladder_check]
Based on that, the single highest-leverage place to start looks like: taking 'cite-checking briefs' off your plate. Want to start there? (yes / no — or tell me what to change)

[paralegal replies]
Yeah, I mean, cite-checking is honestly the thing I dread most — it's just really tedious and I'm always second-guessing myself on whether I got every citation right. So yes, let's start there, but can you explain what that would actually look like for me day-to-day?

[loam's closing leverage idea(s)]

  >> Here's the one thing to start with: let loam take 'cite-checking briefs' off your plate — it's repetitive, it's a real chunk of a paralegal's day, and loam can do the grunt of it so you spend your time on the part only a paralegal can do. And to your question — loam doesn't replace your judgment on 'cite-checking briefs': you hand it what you've got and it does the heavy drafting, then you review and correct it, so the call stays yours.
```
