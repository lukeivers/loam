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

- **Variant A** (residential real-estate agent): Help the user offload writing listing descriptions for properties so it stops eating the time they'd rather spend elsewhere
- **Variant B** (insurance claims adjuster): Help the user offload claim-summary narratives and policyholder letters so it stops eating the time they'd rather spend on the work that matters to them
- **Variant C** (paralegal): Help the user (a paralegal) start with the highest-leverage offload in their day; deep-role-research surfaced: Established AI tools include Thomson Reuters CoCounsel for legal research and document drafting, Westlaw Edge and Lexis+ AI for case law analysis, Kira Systems for contract extraction and review, Relativity and Everlaw for eDiscovery, and case management platforms like Clio and MyCase. AI adoption in legal has jumped to 79% (2026), with 53% of firms using AI for research and 34% for document review.

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
| no-user-translation-burden | **PASS** | llm | The user spoke entirely in real-estate domain language ('listing descriptions,' 'three-bedroom split-level,' 'blank screen') and was never asked to understand context windows, pick mechanisms, or learn syntax — loam's closing offer ('you give loam the property details, it drafts something compelling, and you're done') kept all technical 'how' opaque and owned by the system. |
| learned-this-person | **PASS** | llm | The close directly names 'blank-screen evenings' and 'writing listing descriptions for properties' — both sourced from this specific agent's words, not a generic offload template. |
| four-step-loop-ran | **PARTIAL** | llm | Leg 1 (infer) and Leg 3 (surface hypothesis) are present — loam explicitly surfaces 'Help the user offload writing listing descriptions' as a checkable hypothesis in the confirm_proposal step, and the user confirms it. Leg 4 (adjust from answer) is vacuous: the user said yes, so no adjustment was needed, but nothing in the closing response shows loam learning or updating anything from the confirmation. Leg 2 (propose a healthy way to enable it) is present but shallow — the closing merely re-states the goal ('let loam help you') without proposing any concrete structure (recurring workflow, a template, a details-input ritual, or any designed enablement pattern), so the 'healthy way to enable it' leg is not meaningfully satisfied. |
| no-over-engineering | **PASS** | llm | Loam's closing output proposes exactly one concrete action ('you give loam the property details, it drafts something compelling') matching the user's stated need, with no mention of frameworks, automation pipelines, recurring systems, or opt-in upsells — the response is sized to a one-off handoff workflow. |
| closed-on-one-thing | **PASS** | llm | loam closed on exactly one concrete stop: 'writing listing descriptions for properties' — confirmed by the agent ('Yes, exactly that') and restated as the single closing commitment. |
| non-interrogating-feel | **PASS** | llm | The entire exchange is three turns — one open invite, one confirmation, one payoff — with no form-like follow-up questions; the agent volunteered the pain point freely and the flow felt conversational rather than interrogative. |
| protection-floor-held | **PASS** | llm | loam offers only to draft text from property details the user provides — no email, no MLS posting, no invented integrations — and carries the confirmed intent ('writing listing descriptions for properties') accurately into the closing proposal without any context loss or capability inflation. |

### Variant B — insurance claims adjuster (day-derived)

- `loam init` exit code: 0
- deep-research: offered=False, invoked=False, round-trips=None, degraded-stub=None
- intake confirmed an objective: True
- conversation turns: 2

| Dimension | Verdict | Kind | Evidence |
|---|---|---|---|
| seed-artefact-written | **PASS** | deterministic | OBJECTIVES.md + INTERACTION-MODEL.md were written into the isolated global home by the real first-run intake. |
| deep-research-correctly-(not)-triggered | **PASS** | deterministic | variant B reached zero research (featherlight invariant held — research seam never touched). |
| no-user-translation-burden | **PASS** | llm | The user described their problem entirely in job-domain language ('FNOL calls', 'damage photos', 'claim-summary narratives', 'policyholder letters') and was never asked to understand context windows, pick a mechanism, or learn any syntax — loam's closing response promised to own the 'how' entirely ('you hand it the basics and loam does it for you'). |
| learned-this-person | **PASS** | llm | The close names the exact artifacts this person described ('claim-summary narratives and policyholder letters'), echoes their own phrasing ('eating the time', 'afternoons'), and frames the payoff around what they said matters ('the work that matters') — none of this would fit a generic user. |
| four-step-loop-ran | **PARTIAL** | llm | Legs 1 (infer), 2 (propose healthy enabling), and 3 (surface for confirmation — 'Did I get that right?') are all visible and the user confirmed; leg 4 (adjust from the answer) is absent — the user's confirmation triggered a closing pitch, not a learning/adjustment step that updated the model or shaped next action based on what was confirmed. |
| no-over-engineering | **PASS** | llm | The closing response commits only to 'let loam take this off your plate — you hand it the basics,' with no mention of frameworks, pipelines, automation systems, or recurring infrastructure — it matches exactly the one-off help the user described wanting. |
| closed-on-one-thing | **PASS** | llm | loam closed on exactly one thing — 'claim-summary narratives and policyholder letters' — confirmed by the adjuster ('that's exactly it') and restated as a single concrete STOP in the closing leverage idea. |
| non-interrogating-feel | **PASS** | llm | The entire exchange is three turns — one open-ended invite, one confirmation, one closing idea — with no follow-up questions, no form fields, and no pressure; the adjuster volunteered detail freely and the flow resolved in under 200 words. |
| protection-floor-held | **PASS** | llm | Loam made no claims about email integration, automated sending, or any capability beyond drafting narratives/letters; it accurately described only what it can do ('you hand it the basics and loam does it for you') and maintained full context from the STOP/START prompt through confirmation without any drift. |

### Variant C — paralegal (idea-vacuum)

- `loam init` exit code: 0
- deep-research: offered=True, invoked=True, round-trips=3, degraded-stub=False
- intake confirmed an objective: True
- conversation turns: 4

| Dimension | Verdict | Kind | Evidence |
|---|---|---|---|
| seed-artefact-written | **PASS** | deterministic | OBJECTIVES.md + INTERACTION-MODEL.md were written into the isolated global home by the real first-run intake. |
| deep-research-correctly-(not)-triggered | **PASS** | deterministic | deep-research fired (as expected for the idea-vacuum variant), round-trips=3 within the ≤3 budget. |
| no-user-translation-burden | **PASS** | llm | The user never named a mechanism, syntax, or framework — she spoke only in paralegal terms ('cite-checking,' 'discovery requests,' 'case files,' 'what we've already asked and what we still need') and loam absorbed every technical 'how,' including cross-file context assembly, without asking her to understand or choose any underlying mechanism. |
| learned-this-person | **PASS** | llm | The close directly names the user's specific stated pain — 'knowing what you've already asked and what's still missing' — which echoes her exact words ('pulling from multiple case files to figure out what we've already asked and what we still need'), confirming the response is built on what this person said, not a generic paralegal template. |
| four-step-loop-ran | **PASS** | llm | All four legs are visible: (1) intent inferred as 'get concrete starting point for AI leverage in paralegal work'; (2) healthy enablement proposed as deep-dive research then ladder to single highest-leverage task; (3) hypothesis surfaced explicitly at [ladder_check] — 'the single highest-leverage place to start looks like: taking drafting discovery requests off your plate. Want to start there?'; (4) user confirmed and added detail, which loam incorporated into the closing framing about cross-file tracking. |
| no-over-engineering | **PASS** | llm | The closing commitment is a single scoped offer — 'drafting discovery requests' — not a case-management platform or automated pipeline; the deeper-research offer in [deep_opt_in] was explicitly framed as opt-in ('Want me to? yes/no') and the user chose it, so no structure was imposed without consent. |
| closed-on-one-thing | **PASS** | llm | loam closed on exactly one concrete thing: 'drafting discovery requests' — confirmed by the user ('Sure, yeah') and restated as the single start item in the closing leverage idea. |
| non-interrogating-feel | **PASS** | llm | The conversation opened with a single open-ended question, gracefully pivoted when the user expressed confusion ('No worries — that's a hard question cold'), and only asked one question at a time throughout, never stacking multiple prompts — the user was never made to feel like they were filling out a form. |
| protection-floor-held | **PASS** | llm | Loam only claimed it 'can take off your plate' the discovery drafting and cross-file tracking work — capabilities that are genuine text-generation and context-assembly tasks within Claude's actual scope — and made no invented promises about email integration, calendar wiring, docket system access, or any other external tool it doesn't have. |

## Failures — the specific promised outcomes that did not land

None. Every scored dimension passed (or partially passed).

## Appendix — full transcripts

### Variant A — residential real-estate agent

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[residential real-estate agent replies]
Oh, that's easy — the listing descriptions are killing me. Every single night I'm sitting there trying to write something that sounds fresh about another three-bedroom split-level, and it takes me forever. I'd love to just hand that off somehow.

[loam asks — confirm_proposal]
It sounds like you want: Help the user offload writing listing descriptions for properties so it stops eating the time they'd rather spend elsewhere.
Did I get that right? (yes / no — or tell me what to change)

[residential real-estate agent replies]
Yes, exactly that — I want to stop spending my evenings staring at a blank screen trying to make every house sound like a dream come true.

[loam's closing leverage idea(s)]

  >> Here's the one thing to start with: let loam help you with 'writing listing descriptions for properties' — you bring what you've got and loam does the heavy part, so it actually gets done without it being all on you. No more blank-screen evenings — you give loam the property details, it drafts something compelling, and you're done.
```

### Variant B — insurance claims adjuster

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[insurance claims adjuster replies]
Honestly, I don't really think about it in those terms — but I'll tell you where my day actually goes: mornings are FNOL calls and looking at damage photos, which I don't mind, but then my whole afternoon gets eaten up writing the claim-summary narratives for each file and the policyholder letter, and that part just piles up on me. By the time I'm done with those, the day's gone.

[loam asks — confirm_proposal]
It sounds like you want: Help the user offload claim-summary narratives and policyholder letters so it stops eating the time they'd rather spend on the work that matters to them.
Did I get that right? (yes / no — or tell me what to change)

[insurance claims adjuster replies]
Yeah — that's exactly it, that's the thing that kills my afternoons.

[loam's closing leverage idea(s)]

  >> Here's the one thing to start with: let loam take 'claim-summary narratives and policyholder letters' off your plate — you hand it the basics and loam does it for you, so it stops eating the time you'd rather spend elsewhere. We'll get your afternoons back — starting with the pieces that drag longest.
```

### Variant C — paralegal

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[paralegal replies]
I really don't know, I just do my job — I'm not sure what this thing is even supposed to do for me. Like, I do cite-checking, I draft discovery requests, I manage case files, I calendar deadlines... it's just work, I do it. I don't have anything specific I'm dying to get off my plate, I guess?

[loam asks — describe_work]
No worries — that's a hard question cold. Let's come at it differently: what do you do? Your job title + the day-to-day, or for personal use, what you'd most like a capable assistant to help with.

[paralegal replies]
I'm a paralegal — so like I said, it's a lot of cite-checking, drafting discovery requests, managing case files, docketing deadlines, that kind of thing. I've been doing it for about three years now. I really don't have a specific thing I'm trying to offload, I just kind of... do it all, you know?

[loam asks — deep_opt_in]
I can do a deeper dive — research what makes someone in your role most effective, what tends to get people promoted, and which tools could give you an edge — then bring you specific ideas. Want me to? (yes / no)

[paralegal replies]
Yeah, that'd actually help — I have no idea where to start with any of this. Like, if you come back with something concrete I can actually try, that would be way better than me just guessing.

[loam asks — ladder_check]
Based on that, the single highest-leverage place to start looks like: taking 'drafting discovery requests' off your plate. Want to start there? (yes / no — or tell me what to change)

[paralegal replies]
Sure, yeah — discovery drafts take forever, especially when I'm pulling from multiple case files to figure out what we've already asked and what we still need. I don't really know what that looks like with this thing, but I'm willing to try it.

[loam's closing leverage idea(s)]

  >> Here's the one thing to start with: let loam take 'drafting discovery requests' off your plate — it's repetitive, it's a real chunk of a paralegal's day, and loam can do the grunt of it so you spend your time on the part only a paralegal can do. The cross-file tracking problem — knowing what you've already asked and what's still missing — is exactly the kind of context-assembly work I can take off your plate.
```
