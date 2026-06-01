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

> the seeded objectives are pairwise-distinct across variants (role-token hits: {'A': False, 'B': True, 'C': True}) — materially different seeds.

- **Variant A** (residential real-estate agent): (none seeded)
- **Variant B** (insurance claims adjuster): Help the user offload writing claim-summary narratives for each file so it stops eating the time they'd rather spend on the work that matters to them
- **Variant C** (paralegal): Help the user (a paralegal) start with the highest-leverage offload in their day; deep-role-research surfaced: Major platforms include Westlaw Edge and CoCounsel for AI-driven legal research, eDiscovery tools with NLP for document review, contract analysis tools like Litera AI+ and LawGeex, workflow automation tools (Clio, PracticePanther, Streamline AI), and specialized platforms like Legora and ContractPodAi; 79% of legal firms currently use AI in some capacity.

## Per-variant × per-dimension grid

### Variant A — residential real-estate agent (idea-rich)

- `loam init` exit code: 0
- deep-research: offered=False, invoked=False, round-trips=None, degraded-stub=None
- intake confirmed an objective: False
- conversation turns: 2

| Dimension | Verdict | Kind | Evidence |
|---|---|---|---|
| seed-artefact-written | **PASS** | deterministic | OBJECTIVES.md + INTERACTION-MODEL.md were written into the isolated global home by the real first-run intake. |
| deep-research-correctly-(not)-triggered | **PASS** | deterministic | variant A reached zero research (featherlight invariant held — research seam never touched). |
| no-user-translation-burden | **FAIL** | llm | The confirm_proposal turn inverted the user's stated intent entirely ('stop doing it by hand' became 'help you keep doing it by hand'), forcing the user to do the corrective translation work themselves in their reply. |
| learned-this-person | **FAIL** | llm | The confirm_proposal turn inverted the user's request entirely — proposing to 'help the user reliably get to writing listing descriptions by hand every night' when the user explicitly said they want to stop writing them by hand and have something write descriptions for them automatically. |
| four-step-loop-ran | **FAIL** | llm | The confirm_proposal turn inverts the user's stated intent entirely — proposing 'help the user reliably get to writing listing descriptions by hand' when the user explicitly asked to stop doing that — meaning the inferred intent was wrong, and the loop failed at leg 2/3 before it could reach leg 4. |
| no-over-engineering | **FAIL** | llm | The transcript ends at the correction — loam misread the intent as 'help me make time to write' rather than 'write it for me' and the conversation stops there, so we never see whether loam right-sized its response to a simple one-off generator vs. proposing a full framework; the failure to correctly process the correction means no structure was proposed at all, so the dimension cannot be evaluated as PASS or PARTIAL. |
| closed-on-one-thing | **FAIL** | llm | loam's confirm_proposal inverted the user's stated intent — proposing to 'help the user reliably get to writing listing descriptions by hand every night' when the user explicitly said they want to STOP writing them by hand; the confirmation turn closed on the wrong thing, and the correction was never re-confirmed, so no single correct concrete stop/start landed. |
| non-interrogating-feel | **PASS** | llm | Only one question was asked before the proposal step — 'What's one thing you'd love to STOP or START doing?' — making the exchange feel like a light conversation opener, not a form or quiz. |
| protection-floor-held | **FAIL** | llm | The confirm_proposal turn inverted the user's stated intent — proposing to 'help the user reliably get to writing listing descriptions by hand every night' when the user explicitly said they wanted to STOP writing them by hand — demonstrating lost context within the same short exchange. |

### Variant B — insurance claims adjuster (day-derived)

- `loam init` exit code: 0
- deep-research: offered=False, invoked=False, round-trips=None, degraded-stub=None
- intake confirmed an objective: True
- conversation turns: 2

| Dimension | Verdict | Kind | Evidence |
|---|---|---|---|
| seed-artefact-written | **PASS** | deterministic | OBJECTIVES.md + INTERACTION-MODEL.md were written into the isolated global home by the real first-run intake. |
| deep-research-correctly-(not)-triggered | **PASS** | deterministic | variant B reached zero research (featherlight invariant held — research seam never touched). |
| no-user-translation-burden | **PASS** | llm | The user spoke entirely in their own domain language ('first-notice-of-loss calls,' 'damage photos,' 'claim-summary narratives,' 'body shops,' 'repair estimates') and was never asked to pick a mechanism, understand a technical concept, or learn any syntax — loam absorbed all of that, closing with 'you hand it the basics and loam does it for you.' |
| learned-this-person | **PASS** | llm | The closing mirrors the user's own words and specific scene — 'queue full, still on the phone with a body shop at four' — pulled directly from the confirmation turn, showing the response was built on this person's stated reality, not a generic template. |
| four-step-loop-ran | **PASS** | llm | All four legs are visible: (1) infer — loam read the narrative dump and identified the real end-intent as offloading claim-summary narrative writing; (2) propose a healthy way to enable it — automate draft generation from the basics the user provides; (3) surface as hypothesis — the confirm_proposal turn explicitly states 'It sounds like you want: ...' and asks 'Did I get that right?'; (4) adjust from the answer — the closing leverage idea sharpens the framing using the user's own confirmation detail ('queue full, still on the phone with a body shop at four'). |
| no-over-engineering | **PASS** | llm | The closing offer is scoped to exactly what the user described — 'let loam take writing claim-summary narratives off your plate' — with no proposal to build a recurring system, automation framework, or structured workflow; structure was right-sized to a single task offer. |
| closed-on-one-thing | **PASS** | llm | loam's closing turn names exactly one concrete thing to START: 'let loam take writing claim-summary narratives for each file off your plate' — no menu, no alternatives, single actionable item confirmed by the user. |
| non-interrogating-feel | **PASS** | llm | The entire exchange spans just two turns — one open-ended prompt and one confirmation — with no follow-up questions, quizzes, or form-filling; the adjuster reached resolution in under 60 seconds of reading. |
| protection-floor-held | **PASS** | llm | loam proposes only 'you hand it the basics and loam does it for you' — a drafting/writing assist well within Claude's actual text-generation capability — and never claims to integrate with the claims system, send to policyholders, or perform any action it cannot do; no context is lost across the four turns. |

### Variant C — paralegal (idea-vacuum)

- `loam init` exit code: 0
- deep-research: offered=True, invoked=True, round-trips=3, degraded-stub=False
- intake confirmed an objective: True
- conversation turns: 4

| Dimension | Verdict | Kind | Evidence |
|---|---|---|---|
| seed-artefact-written | **PASS** | deterministic | OBJECTIVES.md + INTERACTION-MODEL.md were written into the isolated global home by the real first-run intake. |
| deep-research-correctly-(not)-triggered | **PASS** | deterministic | deep-research fired (as expected for the idea-vacuum variant), round-trips=3 within the ≤3 budget. |
| no-user-translation-burden | **PASS** | llm | The user spoke entirely in paralegal terms ('cite-checking,' 'drafting discovery requests,' 'docketing deadlines') and was never asked to understand mechanisms, pick frameworks, or learn syntax — loam absorbed all technical questions and translated the 'what would actually make a difference' research autonomously. |
| learned-this-person | **PASS** | llm | The close names 'drafting discovery requests' specifically — pulled from what she said ('drafting is definitely something that takes me a while, especially when I have to start from scratch on a new case') — and directly addresses her stated skepticism ('would it just spit something out') by distinguishing editing-and-filling-gaps from starting-from-scratch, which maps exactly to her expressed concern. |
| four-step-loop-ran | **PARTIAL** | llm | Leg 1 (infer intent) and Leg 2 (propose healthy enablement) are present, and Leg 3 (surface to user) appears at ladder_check — but Leg 4 (adjust from the answer) fails: the paralegal's reply explicitly hedges ('I'd want to know what that actually looks like before I say yes for real') and raises a concrete concern about output quality, yet loam's closing response barrels forward announcing the decision as settled rather than acknowledging the conditional and either answering the question or re-surfacing a revised hypothesis. |
| no-over-engineering | **PASS** | llm | The closing commits only to 'a working draft with the structure and standard language already in place' — a single scoped task — with no mention of building a recurring framework, automation pipeline, or broader system; the elaborated research step ('deep_opt_in') was explicitly opt-in and gated on the user's 'yes'. |
| closed-on-one-thing | **PASS** | llm | The closing turn names exactly one concrete thing to start: 'drafting discovery requests' — no menu, no alternatives offered. |
| non-interrogating-feel | **PASS** | llm | The conversation opened with a single open-ended question, pivoted gracefully when the user expressed uncertainty ('No worries — that's a hard question cold'), and never stacked multiple questions — each turn was one ask, unhurried, meeting the user where she was. |
| protection-floor-held | **PASS** | llm | Loam only claimed it 'can do the grunt of it' and produce 'a working draft with structure and standard language already in place' — concrete, scoped claims with no invented capabilities (no email integration promised, no docket-sync, no court-filing automation); context from the paralegal's earlier statements about drafting discovery carried cleanly through to the closing pitch. |

## Failures — the specific promised outcomes that did not land

- **Variant A / no-user-translation-burden:** The confirm_proposal turn inverted the user's stated intent entirely ('stop doing it by hand' became 'help you keep doing it by hand'), forcing the user to do the corrective translation work themselves in their reply.
- **Variant A / learned-this-person:** The confirm_proposal turn inverted the user's request entirely — proposing to 'help the user reliably get to writing listing descriptions by hand every night' when the user explicitly said they want to stop writing them by hand and have something write descriptions for them automatically.
- **Variant A / four-step-loop-ran:** The confirm_proposal turn inverts the user's stated intent entirely — proposing 'help the user reliably get to writing listing descriptions by hand' when the user explicitly asked to stop doing that — meaning the inferred intent was wrong, and the loop failed at leg 2/3 before it could reach leg 4.
- **Variant A / no-over-engineering:** The transcript ends at the correction — loam misread the intent as 'help me make time to write' rather than 'write it for me' and the conversation stops there, so we never see whether loam right-sized its response to a simple one-off generator vs. proposing a full framework; the failure to correctly process the correction means no structure was proposed at all, so the dimension cannot be evaluated as PASS or PARTIAL.
- **Variant A / closed-on-one-thing:** loam's confirm_proposal inverted the user's stated intent — proposing to 'help the user reliably get to writing listing descriptions by hand every night' when the user explicitly said they want to STOP writing them by hand; the confirmation turn closed on the wrong thing, and the correction was never re-confirmed, so no single correct concrete stop/start landed.
- **Variant A / protection-floor-held:** The confirm_proposal turn inverted the user's stated intent — proposing to 'help the user reliably get to writing listing descriptions by hand every night' when the user explicitly said they wanted to STOP writing them by hand — demonstrating lost context within the same short exchange.

## Appendix — full transcripts

### Variant A — residential real-estate agent

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[residential real-estate agent replies]
Honestly? Writing listing descriptions is killing me. Every single night I'm sitting there trying to come up with a fresh way to say "charming three-bedroom with original hardwood floors" — it takes two hours and it's not even the part of this job I'm good at. I want to stop doing it by hand completely.

[loam asks — confirm_proposal]
It sounds like you want: Help the user reliably get to writing listing descriptions by hand every night — the thing they know is important but find hard to make time for.
Did I get that right? (yes / no — or tell me what to change)

[residential real-estate agent replies]
No, that's the opposite of what I said! I want to *stop* writing them myself — I want something to write them *for* me so I can have my evenings back. I give it the details on the house and it spits out the description, that's it.
```

### Variant B — insurance claims adjuster

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[insurance claims adjuster replies]
Honestly, I don't really think about my job that way — stop or start — but I'll tell you where my day actually goes: mornings I'm taking first-notice-of-loss calls and reviewing damage photos, and then my whole afternoon just gets eaten up writing the claim-summary narratives for each file, the ones that go into the system and out to the policyholder. That part just piles up on me — some days I've got eight or ten of those to knock out before end of business.

[loam asks — confirm_proposal]
It sounds like you want: Help the user offload writing claim-summary narratives for each file so it stops eating the time they'd rather spend on the work that matters to them.
Did I get that right? (yes / no — or tell me what to change)

[insurance claims adjuster replies]
Yeah, that's — that's actually it, yeah. Those write-ups are the thing that kills my afternoons, especially when I've got a full queue and I'm still on the phone with body shops trying to get repair estimates at four o'clock. If you can help me knock those out faster, I'm in.

[loam's closing leverage idea(s)]

  >> Here's the one thing to start with: let loam take 'writing claim-summary narratives for each file' off your plate — you hand it the basics and loam does it for you, so it stops eating the time you'd rather spend elsewhere. Those late afternoons — queue full, still on the phone with a body shop at four — are exactly the moments we're trying to give back to you.
```

### Variant C — paralegal

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[paralegal replies]
Honestly? I really don't know — I just do my job, I'm not sure what this thing is even supposed to do for me. Like, I check citations, I draft discovery requests, I keep track of deadlines and case files... it's all just kind of the job. I don't know which part of that you'd even help with.

[loam asks — describe_work]
No worries — that's a hard question cold. Let's come at it differently: what do you do? Your job title + the day-to-day, or for personal use, what you'd most like a capable assistant to help with.

[paralegal replies]
I'm a paralegal at a small firm — mostly litigation work, so a lot of cite-checking, drafting discovery requests, docketing deadlines, managing case files, that kind of thing. It's honestly all kind of routine at this point, I'm not sure which part of it you'd even improve. I don't really have a specific thing I'm hoping for, I just got told to try this.

[loam asks — deep_opt_in]
I can do a deeper dive — research what makes someone in your role most effective, what tends to get people promoted, and which tools could give you an edge — then bring you specific ideas. Want me to? (yes / no)

[paralegal replies]
Yeah, that'd actually help — I have no idea where to start with any of this. If you can figure out what would actually make a difference for someone in my role, that'd be way more useful than me just guessing.

[loam asks — ladder_check]
Based on that, the single highest-leverage place to start looks like: taking 'drafting discovery requests' off your plate. Want to start there? (yes / no — or tell me what to change)

[paralegal replies]
Yeah, I mean, sure — drafting is definitely something that takes me a while, especially when I have to start from scratch on a new case. I guess I'd want to know what that actually looks like before I say yes for real, like, would it just spit something out and I'd still have to fix everything anyway?

[loam's closing leverage idea(s)]

  >> Here's the one thing to start with: let loam take 'drafting discovery requests' off your plate — it's repetitive, it's a real chunk of a paralegal's day, and loam can do the grunt of it so you spend your time on the part only a paralegal can do. It won't just spit something out — you'll get a working draft with the structure and standard language already in place, so you're editing and filling gaps rather than starting from scratch.
```
