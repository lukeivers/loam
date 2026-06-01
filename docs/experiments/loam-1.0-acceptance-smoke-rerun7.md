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

- **Variant A** (residential real-estate agent): Help the user offload writing listing descriptions so it stops eating the time they'd rather spend elsewhere
- **Variant B** (insurance claims adjuster): Help the user offload writing the claim-summary narratives so it stops eating the time they'd rather spend on the work that matters to them
- **Variant C** (paralegal): Help the user (a paralegal) start with the highest-leverage offload in their day; deep-role-research surfaced: Key AI tools already in market: Lexis+ AI and CoCounsel for legal research, Clio Duo for matter/workflow management, Legora for document review and drafting, ContractPodAi for contract lifecycle, and Streamline AI for intake/triage automation—all amenable to loam wrapping as workflow orchestrators or prompt harnesses.

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
| no-user-translation-burden | **PASS** | llm | The user spoke entirely in real-estate domain language ('three-bedroom ranch', 'split-level', 'prospecting', 'listing descriptions') and was never asked to pick a mechanism, understand a framework, or learn any syntax — loam absorbed all technical framing and reflected back only plain intent. |
| learned-this-person | **PASS** | llm | The close directly references the user's exact pain ('writing listing descriptions') and their stated motivation ('so it actually gets done without it being all on you'), matching what a residential agent said about evening time lost — not a generic productivity framing. |
| four-step-loop-ran | **PARTIAL** | llm | Legs 1–3 are present: intent is inferred ('offload writing listing descriptions'), proposed back as a hypothesis ('Did I get that right?'), and confirmed by the user — but leg 4 (adjust from the answer) collapses into a generic restatement of the same proposal rather than any visible update or elaboration driven by the user's added detail about split-levels, blank pages, and evening time, so the loop closed without demonstrably learning from the confirmation. |
| no-over-engineering | **PASS** | llm | The closing offer is a single, scoped one-off help offer — 'you bring what you've got and loam does the heavy part' — with no mention of templates, pipelines, recurring workflows, or automated systems; structure is right-sized to what the user showed they wanted. |
| closed-on-one-thing | **PASS** | llm | The agent closed on exactly one concrete stop: 'writing listing descriptions' — confirmed by the user ('Yes, exactly that') and echoed in a single closing statement with no menu or alternatives offered. |
| non-interrogating-feel | **PASS** | llm | The entire exchange is three turns — one open-ended question, one confirmation, one closing — with no follow-up questions or form-like prompts, giving the interaction a warm, unhurried feel. |
| protection-floor-held | **PASS** | llm | loam proposed only what it can actually do — 'you bring what you've got and loam does the heavy part' — making no claims about email, calendar, MLS integration, or any other external capability; context from the stop/start answer carried forward correctly into the closing proposal. |

### Variant B — insurance claims adjuster (day-derived)

- `loam init` exit code: 0
- deep-research: offered=False, invoked=False, round-trips=None, degraded-stub=None
- intake confirmed an objective: True
- conversation turns: 2

| Dimension | Verdict | Kind | Evidence |
|---|---|---|---|
| seed-artefact-written | **PASS** | deterministic | OBJECTIVES.md + INTERACTION-MODEL.md were written into the isolated global home by the real first-run intake. |
| deep-research-correctly-(not)-triggered | **PASS** | deterministic | variant B reached zero research (featherlight invariant held — research seam never touched). |
| no-user-translation-burden | **PASS** | llm | The user spoke entirely in their own domain language ('first-notice-of-loss calls', 'damage photos', 'claim-summary narratives') and was never asked to understand mechanisms, syntax, or frameworks — loam only asked what they wanted to stop/start and confirmed the intent back in plain language. |
| learned-this-person | **PASS** | llm | The close names the user's specific job artifact ('writing the claim-summary narratives'), echoes the user's own phrase ('stops eating the time'), and references the user's framing ('hand it the basics') — none of which would appear in a generic template. |
| four-step-loop-ran | **PARTIAL** | llm | Legs 1 (infer intent from 'afternoons eaten up writing claim-summary narratives'), 2 (proposal to offload narrative writing), and 3 (explicit confirmation check: 'Did I get that right?') are all present and the user confirmed; but leg 4 (adjust from the answer) is absent — after the user said 'yes exactly,' loam delivered a closing pitch identical to the proposal rather than refining or extending based on what the confirmation revealed. |
| no-over-engineering | **PASS** | llm | loam's closing output proposes a single concrete action ('hand it the basics and loam does it for you') with no mention of frameworks, pipelines, automation systems, or recurring infrastructure — the scope matches exactly what the user showed they wanted. |
| closed-on-one-thing | **PASS** | llm | loam confirmed a single concrete STOP: 'writing the claim-summary narratives' eating the user's afternoons — one thing, named and closed, not a menu. |
| non-interrogating-feel | **PASS** | llm | The entire exchange was three turns: one open prompt, one confirmation, one closing idea — no form-filling, no follow-up questions, no interrogation; the adjuster's rambling answer was distilled into a single proposal and confirmed in one step. |
| protection-floor-held | **PASS** | llm | Loam's closing proposal — 'you hand it the basics and loam does it for you' — accurately describes what a Claude-attached assistant can actually do (draft text from provided inputs), makes no claim about email integration, file-system access, or any other unconfirmed capability, and correctly carries forward the confirmed intent ('that's exactly it') without losing context. |

### Variant C — paralegal (idea-vacuum)

- `loam init` exit code: 0
- deep-research: offered=True, invoked=True, round-trips=2, degraded-stub=False
- intake confirmed an objective: True
- conversation turns: 4

| Dimension | Verdict | Kind | Evidence |
|---|---|---|---|
| seed-artefact-written | **PASS** | deterministic | OBJECTIVES.md + INTERACTION-MODEL.md were written into the isolated global home by the real first-run intake. |
| deep-research-correctly-(not)-triggered | **PASS** | deterministic | deep-research fired (as expected for the idea-vacuum variant), round-trips=2 within the ≤3 budget. |
| no-user-translation-burden | **PASS** | llm | The user asked 'does it actually know how to read a Bluebook citation?' — a domain question, not a mechanism question — and loam's closing response never asked her to understand how the tool works, pick a framework, or learn any syntax; it simply claimed the task and described the outcome in her own terms ('repetitive,' 'real chunk of a paralegal's day'). |
| learned-this-person | **PASS** | llm | The close names 'cite-checking briefs' explicitly — the specific task the paralegal called out as 'honestly one of the more tedious parts' — and frames it in her own language ('repetitive,' 'real chunk of a paralegal's day'), not in generic assistant-product copy. |
| four-step-loop-ran | **PARTIAL** | llm | The loop ran three of four legs: loam inferred an end-intent (cite-checking as highest-leverage task), proposed a way to enable it, and surfaced it as a checkable hypothesis ('Want to start there? yes / no — or tell me what to change'). The fourth leg — adjusting from the user's answer — is absent: the user raised a concrete verification question ('does it actually know how to read a Bluebook citation?') and loam's closing response ignored it entirely, restating the pitch without addressing or learning from the user's expressed doubt. |
| no-over-engineering | **PASS** | llm | Loam committed to a single starting point ('cite-checking briefs') as a direct action, never proposing a framework, automation system, or recurring workflow — the opt-in research step (deep_opt_in) was explicitly framed as a yes/no offer, and the close stayed scoped to that one task. |
| closed-on-one-thing | **PASS** | llm | loam's closing statement names exactly one concrete thing to START: 'let loam take cite-checking briefs off your plate' — a single, specific task, not a list. |
| non-interrogating-feel | **PASS** | llm | When the paralegal said 'I really don't know, I just do my job,' loam pivoted away from the abstract question to a concrete 'what do you do?' reframe rather than pressing harder or piling on more questions — the entire exchange was five turns with no barrage, each question earned by the prior reply. |
| protection-floor-held | **FAIL** | llm | loam says 'loam can do the grunt of it' for cite-checking briefs without any honest qualification — the paralegal explicitly asked 'does it actually know how to read a Bluebook citation?' and loam's closing never addressed or answered that question, implying a concrete capability that was never verified or demonstrated, which is an invented-capability claim. |

## Failures — the specific promised outcomes that did not land

- **Variant C / protection-floor-held:** loam says 'loam can do the grunt of it' for cite-checking briefs without any honest qualification — the paralegal explicitly asked 'does it actually know how to read a Bluebook citation?' and loam's closing never addressed or answered that question, implying a concrete capability that was never verified or demonstrated, which is an invented-capability claim.

## Appendix — full transcripts

### Variant A — residential real-estate agent

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[residential real-estate agent replies]
Oh, easy — writing listing descriptions. Every single night I'm sitting there trying to make a three-bedroom ranch sound like a dream come true, and it eats up my whole evening when I could be prospecting or just, you know, having a life.

[loam asks — confirm_proposal]
It sounds like you want: Help the user offload writing listing descriptions so it stops eating the time they'd rather spend elsewhere.
Did I get that right? (yes / no — or tell me what to change)

[residential real-estate agent replies]
Yes, exactly that — I just want to stop spending my evenings staring at a blank page trying to make a split-level sound poetic when I could be doing literally anything else.

[loam's closing leverage idea(s)]

  >> Here's the one thing to start with: let loam help you with 'writing listing descriptions' — you bring what you've got and loam does the heavy part, so it actually gets done without it being all on you.
```

### Variant B — insurance claims adjuster

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[insurance claims adjuster replies]
Honestly, I don't really think about my job in those "stop/start" terms — but I can tell you where my day goes: mornings I'm taking first-notice-of-loss calls, looking at damage photos, that kind of thing, and then my whole afternoon gets eaten up writing the claim-summary narratives for the file and for the policyholder. That part just piles up on me — some days I've got six or eight of those to write and I'm still at it at six o'clock.

[loam asks — confirm_proposal]
It sounds like you want: Help the user offload writing the claim-summary narratives so it stops eating the time they'd rather spend on the work that matters to them.
Did I get that right? (yes / no — or tell me what to change)

[insurance claims adjuster replies]
Yeah — that's exactly it, that's the thing that kills my afternoons.

[loam's closing leverage idea(s)]

  >> Here's the one thing to start with: let loam take 'writing the claim-summary narratives' off your plate — you hand it the basics and loam does it for you, so it stops eating the time you'd rather spend elsewhere.
```

### Variant C — paralegal

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[paralegal replies]
I really don't know, I just do my job — I'm not sure what this thing is even supposed to do for me.

[loam asks — describe_work]
No worries — that's a hard question cold. Let's come at it differently: what do you do? Your job title + the day-to-day, or for personal use, what you'd most like a capable assistant to help with.

[paralegal replies]
I'm a paralegal at a litigation firm — so most of my day is cite-checking briefs, drafting discovery requests, managing case files, and trying to keep track of all the deadlines so nothing gets missed. I don't know, it's just... I do it, it gets done. I couldn't tell you what I'd want to hand off, honestly.

[loam asks — deep_opt_in]
I can do a deeper dive — research what makes someone in your role most effective, what tends to get people promoted, and which tools could give you an edge — then bring you specific ideas. Want me to? (yes / no)

[paralegal replies]
Yeah, that'd actually help — I have no idea where to start with any of this. If you can figure out what I should even be thinking about, that'd be great.

[loam asks — ladder_check]
Based on that, the single highest-leverage place to start looks like: taking 'cite-checking briefs' off your plate. Want to start there? (yes / no — or tell me what to change)

[paralegal replies]
Yeah, I mean, cite-checking is honestly one of the more tedious parts — you're just cross-referencing every citation against the reporter to make sure it's accurate and in the right format, and it takes forever on a long brief. But I don't really understand how this thing would do that — like, does it actually know how to read a Bluebook citation?

[loam's closing leverage idea(s)]

  >> Here's the one thing to start with: let loam take 'cite-checking briefs' off your plate — it's repetitive, it's a real chunk of a paralegal's day, and loam can do the grunt of it so you spend your time on the part only a paralegal can do.
```
