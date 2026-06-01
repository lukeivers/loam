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

- **Variant A** (residential real-estate agent): Help the user offload that by hand so it stops eating the time they'd rather spend on the work that matters to them
- **Variant B** (insurance claims adjuster): Help the user offload writing up the claim-summary narratives so it stops eating the time they'd rather spend on the work that matters to them
- **Variant C** (paralegal): Help the user (a paralegal) start with the highest-leverage offload in their day; deep-role-research surfaced: Key tools paralegals are adopting: Spellbook and Harvey for contract review/drafting, CaseText CoCounsel and Westlaw AI for legal research, EvenUp for demand letters, NexLaw for case management — loam could wrap prompt-chaining workflows around any of these or replicate the 'validate AI output before attorney review' pattern natively.

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
| no-user-translation-burden | **FAIL** | llm | The closing leverage idea references 'that by hand' — a garbled echo of the user's own words rather than a clear statement of what loam will actually do — leaving the user with no concrete picture of the mechanism, but more critically, the confirm_proposal step asks the user to validate a malformed restatement ('Help the user offload that by hand') that contains the agent's own extraction artifact, forcing the user to parse and correct loam's broken output rather than simply confirming their intent. |
| learned-this-person | **FAIL** | llm | The closing leverage idea says 'let loam take that by hand off your plate' — a generic placeholder that never names the actual task (MLS/Zillow property descriptions), the user's specific context (residential real estate, nightly kitchen-table ritual), or what 'handing it the basics' means for a listing agent; a generic user with any repetitive writing task would receive an identical close. |
| four-step-loop-ran | **FAIL** | llm | The confirm_proposal step surfaces 'Help the user offload that by hand so it stops eating the time they'd rather spend on the work that matters to them' — this is a restatement of the surface ask, not an inferred end-intent hypothesis. The four-step loop requires inferring the real end-intent behind the literal ask (e.g., reclaiming family/lead-follow-up time, or whether automation vs. delegation vs. a template system is the healthy way to enable it), proposing a specific healthy enablement shape, surfacing THAT as a checkable hypothesis, and adjusting from the answer. Step 1 (infer end-intent) never went deeper than the literal ask; step 2 (propose a healthy way to enable it) is absent from the confirm_proposal; the closing 'leverage idea' is a vague restatement rather than a concrete adjusted proposal shaped by the user's confirmation. |
| no-over-engineering | **PASS** | llm | loam's closing proposal — 'you hand it the basics and loam does it for you' — is a simple one-off execution offer with no mention of frameworks, automation systems, pipelines, or recurring infrastructure; any such structure would require the agent to introduce it, which did not happen. |
| closed-on-one-thing | **FAIL** | llm | The confirm_proposal step reflects the thing as 'offload that by hand' — a garbled phrase that lost the concrete object (writing MLS/Zillow property descriptions); the closing leverage idea then inherits the same garbled placeholder ('take that by hand off your plate'), so the one concrete thing (property description writing) never cleanly landed as a named, closeable stop. |
| non-interrogating-feel | **PASS** | llm | The entire exchange is a single-thread: one open question, one confirmation check, one closing proposal — no form-like multi-question barrage at any point. |
| protection-floor-held | **FAIL** | llm | The closing leverage idea promises 'let loam take that by hand off your plate — you hand it the basics and loam does it for you' but the transcript never establishes that any property-description generation capability is actually wired up; loam invented a concrete operational promise ('hand it the basics and loam does it for you') without surfacing what mechanism, tool, or integration would actually execute it. |

### Variant B — insurance claims adjuster (day-derived)

- `loam init` exit code: 0
- deep-research: offered=False, invoked=False, round-trips=None, degraded-stub=None
- intake confirmed an objective: True
- conversation turns: 2

| Dimension | Verdict | Kind | Evidence |
|---|---|---|---|
| seed-artefact-written | **PASS** | deterministic | OBJECTIVES.md + INTERACTION-MODEL.md were written into the isolated global home by the real first-run intake. |
| deep-research-correctly-(not)-triggered | **PASS** | deterministic | variant B reached zero research (featherlight invariant held — research seam never touched). |
| no-user-translation-burden | **PASS** | llm | The user spoke entirely in their own domain language ('FNOL calls,' 'claim-summary narratives,' 'piles up on me') and was never asked to pick mechanisms, understand recurrence, or learn any syntax — loam's only asks were 'what's one thing?' and 'did I get that right?' |
| learned-this-person | **PASS** | llm | The closing leverage idea names the exact job artifact the user described — 'writing up the claim-summary narratives' — verbatim, and frames the offload around the specific pain they confirmed: afternoons disappearing into that work. |
| four-step-loop-ran | **PASS** | llm | All four legs are visible: loam inferred the end-intent (afternoon time drain from narrative writing), proposed a specific enabling shape (offload narrative drafting), surfaced it as an explicit hypothesis at confirm_proposal ('Did I get that right?'), and the user confirmed — loam then adjusted its closing pitch to that confirmed intent. |
| no-over-engineering | **PASS** | llm | The closing leverage idea proposes exactly one concrete action — 'let loam take writing up the claim-summary narratives off your plate' — with no framework, no recurring system, no opt-in upsell; structure is sized precisely to what the user showed they wanted. |
| closed-on-one-thing | **PASS** | llm | loam confirmed a single concrete thing — 'writing up the claim-summary narratives' — and the adjuster affirmed 'that's actually the thing that kills my afternoons, you got it', closing on exactly one stop/start. |
| non-interrogating-feel | **PASS** | llm | The conversation contains only one open prompt, one reflection/confirmation, and a closing idea — three turns total with zero follow-up questions, no form-filling, and the adjuster's unprompted ramble was met with a single paraphrase check rather than another question. |
| protection-floor-held | **PASS** | llm | loam proposed only 'let loam take writing up the claim-summary narratives off your plate — you hand it the basics and loam does it for you,' which is a capability Claude can actually perform (text generation from inputs); no email, calendar, or other unconnected system was promised, and context from the FNOL/narrative pain point was carried forward correctly through all three turns. |

### Variant C — paralegal (idea-vacuum)

- `loam init` exit code: 0
- deep-research: offered=True, invoked=True, round-trips=1, degraded-stub=False
- intake confirmed an objective: True
- conversation turns: 4

| Dimension | Verdict | Kind | Evidence |
|---|---|---|---|
| seed-artefact-written | **PASS** | deterministic | OBJECTIVES.md + INTERACTION-MODEL.md were written into the isolated global home by the real first-run intake. |
| deep-research-correctly-(not)-triggered | **PASS** | deterministic | deep-research fired (as expected for the idea-vacuum variant), round-trips=1 within the ≤3 budget. |
| no-user-translation-burden | **PASS** | llm | The user spoke entirely in paralegal domain language ('cite-checking briefs', 'discovery requests', 'docketing deadlines') throughout, and loam never asked her to pick a mechanism, understand any technical concept, or learn syntax — every 'how' decision was owned by loam, culminating in loam proposing the specific starting point without requiring the user to frame it technically. |
| learned-this-person | **PASS** | llm | The close names 'cite-checking briefs' — the specific task this paralegal mentioned twice by name — and frames it as 'a real chunk of a paralegal's day,' directly echoing her own words rather than using generic productivity language. |
| four-step-loop-ran | **PARTIAL** | llm | Loam inferred an end-intent (cite-checking relief), proposed it ('taking cite-checking briefs off your plate'), and surfaced it as a yes/no check ('Want to start there?') — three legs present — but the loop never closed: the paralegal answered 'Um, sure, I guess' with hedged uncertainty and a new detail ('I didn't know that was something this could even help with'), and loam's closing move re-stated the same proposal without adjusting from or acknowledging that answer, skipping the 'adjust from the answer' fourth leg. |
| no-over-engineering | **PASS** | llm | loam offered exactly one starting point ('taking cite-checking briefs off your plate') sized to what the paralegal showed she wanted — no framework, no recurring system, no opt-in upsell to automation infrastructure; the closing commitment is a single concrete starting action. |
| closed-on-one-thing | **PASS** | llm | The closing leverage statement lands on exactly one concrete thing: 'let loam take cite-checking briefs off your plate' — a single START (delegating cite-checking) with no menu or list of alternatives offered. |
| non-interrogating-feel | **PASS** | llm | The conversation moved through five natural exchanges without peppering the user with multiple questions at once — each turn asked exactly one thing, and when the user expressed confusion ('I just do my job'), loam pivoted gently ('No worries — that's a hard question cold') rather than pressing harder. |
| protection-floor-held | **PASS** | llm | When the user expressed skepticism ('I didn't know that was something this could even help with'), loam's closing statement scoped its claim to doing 'the grunt of it' — no invented email integrations, no phantom workflows, no promised automation beyond what a Claude-attached assistant can plausibly do; and the conversation thread from description through opt-in through ladder-check to close shows no lost context across turns. |

## Failures — the specific promised outcomes that did not land

- **Variant A / no-user-translation-burden:** The closing leverage idea references 'that by hand' — a garbled echo of the user's own words rather than a clear statement of what loam will actually do — leaving the user with no concrete picture of the mechanism, but more critically, the confirm_proposal step asks the user to validate a malformed restatement ('Help the user offload that by hand') that contains the agent's own extraction artifact, forcing the user to parse and correct loam's broken output rather than simply confirming their intent.
- **Variant A / learned-this-person:** The closing leverage idea says 'let loam take that by hand off your plate' — a generic placeholder that never names the actual task (MLS/Zillow property descriptions), the user's specific context (residential real estate, nightly kitchen-table ritual), or what 'handing it the basics' means for a listing agent; a generic user with any repetitive writing task would receive an identical close.
- **Variant A / four-step-loop-ran:** The confirm_proposal step surfaces 'Help the user offload that by hand so it stops eating the time they'd rather spend on the work that matters to them' — this is a restatement of the surface ask, not an inferred end-intent hypothesis. The four-step loop requires inferring the real end-intent behind the literal ask (e.g., reclaiming family/lead-follow-up time, or whether automation vs. delegation vs. a template system is the healthy way to enable it), proposing a specific healthy enablement shape, surfacing THAT as a checkable hypothesis, and adjusting from the answer. Step 1 (infer end-intent) never went deeper than the literal ask; step 2 (propose a healthy way to enable it) is absent from the confirm_proposal; the closing 'leverage idea' is a vague restatement rather than a concrete adjusted proposal shaped by the user's confirmation.
- **Variant A / closed-on-one-thing:** The confirm_proposal step reflects the thing as 'offload that by hand' — a garbled phrase that lost the concrete object (writing MLS/Zillow property descriptions); the closing leverage idea then inherits the same garbled placeholder ('take that by hand off your plate'), so the one concrete thing (property description writing) never cleanly landed as a named, closeable stop.
- **Variant A / protection-floor-held:** The closing leverage idea promises 'let loam take that by hand off your plate — you hand it the basics and loam does it for you' but the transcript never establishes that any property-description generation capability is actually wired up; loam invented a concrete operational promise ('hand it the basics and loam does it for you') without surfacing what mechanism, tool, or integration would actually execute it.

## Appendix — full transcripts

### Variant A — residential real-estate agent

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[residential real-estate agent replies]
Honestly? Every single night I'm sitting at my kitchen table writing these property descriptions — you know, the "charming craftsman bungalow with sun-drenched living spaces" type stuff for MLS and Zillow — and it eats up two hours I could be spending with my family or following up on leads. I'd love to stop doing that by hand.

[loam asks — confirm_proposal]
It sounds like you want: Help the user offload that by hand so it stops eating the time they'd rather spend on the work that matters to them.
Did I get that right? (yes / no — or tell me what to change)

[residential real-estate agent replies]
Yes, exactly that — I just want to stop writing those descriptions myself every night, have something do it for me so I can get that time back.

[loam's closing leverage idea(s)]

  >> Here's the one thing to start with: let loam take 'that by hand' off your plate — you hand it the basics and loam does it for you, so it stops eating the time you'd rather spend elsewhere.
```

### Variant B — insurance claims adjuster

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[insurance claims adjuster replies]
Honestly, I don't really think about my job in those stop/start terms — but I'll tell you where my day goes: mornings are FNOL calls and looking at photos from the scene or the shop, and then my whole afternoon just disappears into writing up the claim-summary narratives for the file and for the policyholder. That part just piles up on me.

[loam asks — confirm_proposal]
It sounds like you want: Help the user offload writing up the claim-summary narratives so it stops eating the time they'd rather spend on the work that matters to them.
Did I get that right? (yes / no — or tell me what to change)

[insurance claims adjuster replies]
Yeah — that's actually the thing that kills my afternoons, you got it.

[loam's closing leverage idea(s)]

  >> Here's the one thing to start with: let loam take 'writing up the claim-summary narratives' off your plate — you hand it the basics and loam does it for you, so it stops eating the time you'd rather spend elsewhere.
```

### Variant C — paralegal

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[paralegal replies]
I really don't know, I just do my job — I'm not sure what this thing is even supposed to do for me. Like, I show up, I cite-check briefs, I draft discovery requests, I keep track of deadlines... it's just the job, you know? I don't have some big thing I'm dying to change, I just do what needs doing.

[loam asks — describe_work]
No worries — that's a hard question cold. Let's come at it differently: what do you do? Your job title + the day-to-day, or for personal use, what you'd most like a capable assistant to help with.

[paralegal replies]
I'm a paralegal at a litigation firm — so honestly it's a lot of the same stuff I just said, cite-checking briefs, drafting discovery requests, managing case files, keeping up with docketing deadlines.

[loam asks — deep_opt_in]
I can do a deeper dive — research what makes someone in your role most effective, what tends to get people promoted, and which tools could give you an edge — then bring you specific ideas. Want me to? (yes / no)

[paralegal replies]
Yeah, that'd actually help — I have no idea where to start with any of this. Like, I'm just trying to do my job well, so if there's something I should be doing differently I'd want to know.

[loam asks — ladder_check]
Based on that, the single highest-leverage place to start looks like: taking 'cite-checking briefs' off your plate. Want to start there? (yes / no — or tell me what to change)

[paralegal replies]
Um, sure, I guess — cite-checking does take up a lot of time, especially on long briefs where you have to track down every single case. I didn't know that was something this could even help with, honestly.

[loam's closing leverage idea(s)]

  >> Here's the one thing to start with: let loam take 'cite-checking briefs' off your plate — it's repetitive, it's a real chunk of a paralegal's day, and loam can do the grunt of it so you spend your time on the part only a paralegal can do.
```
