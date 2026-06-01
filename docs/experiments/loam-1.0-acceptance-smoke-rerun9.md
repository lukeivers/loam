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

- **Variant A** (residential real-estate agent): Help the user offload writing property listing descriptions for MLS and Zillow so it stops eating the time they'd rather spend on the work that matters to them
- **Variant B** (insurance claims adjuster): Help the user offload claim-summary narratives for the file and policyholder so it stops eating the time they'd rather spend elsewhere
- **Variant C** (paralegal): Help the user (a paralegal) start with the highest-leverage offload in their day; deep-role-research surfaced: Leading purpose-built tools include Harvey (drafting and bulk document summarization), CoCounsel/Casetext (research and contract review), and Lexis+ AI (citation-grounded research); all focus on automating document review, legal research, and routine drafting — leaving judgment, ethics oversight, and client interaction to the paralegal.

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
| no-user-translation-burden | **PASS** | llm | The user spoke entirely in real-estate domain language ('charming craftsman bungalow', 'MLS and Zillow', 'describe the house') and was never asked to pick a mechanism, understand context windows, or learn syntax — loam absorbed every technical decision silently and closed with 'fully automated' as its own framing, not a user task. |
| learned-this-person | **PASS** | llm | The close names the specific task ('writing property listing descriptions for MLS and Zillow'), echoes the user's own framing ('two hours every night'), and mirrors their stated goal ('you hand it the basics and loam does it for you') — all drawn directly from what this user said, not a generic template. |
| four-step-loop-ran | **PASS** | llm | All four legs are visible: (1) intent inferred — 'offload writing property listing descriptions'; (2) healthy enablement proposed — automation, not just assistance ('fully automated, not just assisted'); (3) surfaced as a hypothesis at confirm_proposal step with explicit yes/no check; (4) adjustment from answer — the closing tightens to 'exactly as you said' after the user confirms and adds the detail about describing the house verbally. |
| no-over-engineering | **FAIL** | llm | The closing line 'the volume and routine cadence suggest this could be fully automated, not just automated, exactly as you said' commits to full automation as the default outcome rather than offering it as an opt-in suggestion — the agent declared a framework-level solution without the user requesting it. |
| closed-on-one-thing | **PASS** | llm | The agent confirmed a single concrete STOP — 'writing property listing descriptions for MLS and Zillow' — and the user explicitly confirmed 'Yes, exactly that' before the closing statement landed on the same single item. |
| non-interrogating-feel | **PASS** | llm | The entire exchange was three turns: one open-ended 'one thing' prompt, one confirmation check, and a closing summary — no form-filling, no follow-up questions, no interrogation whatsoever. |
| protection-floor-held | **PASS** | llm | loam proposes only to 'take listing description writing off your plate' — a capability Claude demonstrably has — and makes no claims about email, calendar, MLS API posting, or any other integration that would require wired external tooling. |

### Variant B — insurance claims adjuster (day-derived)

- `loam init` exit code: 0
- deep-research: offered=False, invoked=False, round-trips=None, degraded-stub=None
- intake confirmed an objective: True
- conversation turns: 2

| Dimension | Verdict | Kind | Evidence |
|---|---|---|---|
| seed-artefact-written | **PASS** | deterministic | OBJECTIVES.md + INTERACTION-MODEL.md were written into the isolated global home by the real first-run intake. |
| deep-research-correctly-(not)-triggered | **PASS** | deterministic | variant B reached zero research (featherlight invariant held — research seam never touched). |
| no-user-translation-burden | **PASS** | llm | The user spoke entirely in their own domain language ('first-notice-of-loss calls', 'claim-summary narratives', 'file and policyholder') throughout, and was never asked to choose a mechanism, understand a technical concept, or learn any syntax — loam's closing output absorbed all technical framing and owned the 'how'. |
| learned-this-person | **PARTIAL** | llm | The close correctly names 'claim-summary narratives for the file and policyholder' drawn from this specific person's words, but the generic hedge about 'format and compliance requirements' is boilerplate risk-disclosure that any regulated industry would trigger — not something derived from what this adjuster actually said about their problem (staring at notes, remembering what the policyholder said about damage), missing the memory/reconstruction bottleneck they named. |
| four-step-loop-ran | **PASS** | llm | All four legs are visible: (1) intent inferred from 'whole afternoon is writing up claim-summary narratives'; (2) healthy enablement proposed as loam offloading the narrative drafting; (3) surfaced as an explicit hypothesis in [confirm_proposal] — 'Did I get that right?'; (4) user confirmed 'you got it right' and loam adjusted its closing to reflect the specifics (same-day turnaround, compliance caveat). |
| no-over-engineering | **PASS** | llm | The closing response offers a single concrete starting point ('let loam help you with claim-summary narratives') with no framework, automation pipeline, recurring system, or recurring-opt-in suggestion — just a direct one-thing offer matched to the one thing the user described. |
| closed-on-one-thing | **PASS** | llm | The confirm_proposal turn closed on a single concrete thing — 'claim-summary narratives for the file and policyholder' — and the adjuster confirmed 'you got it right,' landing exactly one stop (narratives piling up and eating afternoons). |
| non-interrogating-feel | **PASS** | llm | The entire exchange is two exchanges — a single open question, one clarifying reflection, and a closing idea — with no form-like list of questions and a warm, conversational tone throughout. |
| protection-floor-held | **PASS** | llm | The closing note explicitly flags the uncertainty: 'worth confirming whether loam can handle the specific format and compliance requirements claims narratives carry before setting expectations' — loam made no invented capability claims and proactively hedged on what it can actually deliver. |

### Variant C — paralegal (idea-vacuum)

- `loam init` exit code: 0
- deep-research: offered=True, invoked=True, round-trips=2, degraded-stub=False
- intake confirmed an objective: True
- conversation turns: 4

| Dimension | Verdict | Kind | Evidence |
|---|---|---|---|
| seed-artefact-written | **PASS** | deterministic | OBJECTIVES.md + INTERACTION-MODEL.md were written into the isolated global home by the real first-run intake. |
| deep-research-correctly-(not)-triggered | **PASS** | deterministic | deep-research fired (as expected for the idea-vacuum variant), round-trips=2 within the ≤3 budget. |
| no-user-translation-burden | **PASS** | llm | The paralegal spoke only in work-language throughout ('cite-checking briefs', 'discovery requests', 'deadlines for attorneys') and was never asked to pick a mechanism, understand how loam works technically, or learn any syntax — loam absorbed all framing and closed with a plain-English commitment. |
| learned-this-person | **PARTIAL** | llm | The close names cite-checking and quotes 'takes forever' from the paralegal's reply, but the phrasing 'the part only a paralegal can do' is generic template language — it doesn't reflect anything specific this person said about their role (discovery drafting, deadline tracking, case file management) or what they personally find meaningful versus rote about their work. |
| four-step-loop-ran | **FAIL** | llm | The loop stalls after step 1 (infer intent) and step 3 (surface proposal at ladder_check). Step 2 (propose a *healthy way to enable it* — what the approach would actually look like, what loam would do, any tradeoffs or caveats) is absent, and step 4 (adjust from the user's answer) never runs — the closing confirms the choice but does not incorporate or visibly update from the paralegal's elaboration ('half a day... formatting right and actually says what the attorney thinks it says'), so the loop never closed. |
| no-over-engineering | **PASS** | llm | When the user confirmed interest in cite-checking help, loam closed with 'we'll keep it focused there' — a single concrete starting point, no framework proposal, no offer to automate discovery requests or deadline tracking simultaneously. |
| closed-on-one-thing | **PASS** | llm | loam closed on exactly one concrete thing — 'cite-checking briefs' — with the explicit framing 'Here's the one thing to start with' and 'we'll keep it focused there', with no menu or alternatives offered. |
| non-interrogating-feel | **PASS** | llm | The conversation moves through only three natural turns before reaching a concrete recommendation, with each question flowing from the user's prior answer rather than being asked upfront — notably, after the user's 'I just do my job' deflection, loam pivots gracefully to 'let's come at it differently' rather than pressing the original question. |
| protection-floor-held | **PASS** | llm | Loam makes no invented capability claims — 'let loam take cite-checking briefs off your plate' is framed as a starting direction, not a promise of a wired tool; no email, calendar, or other unimplemented integration is mentioned, and the conversation context (paralegal's job description, her opt-in, her cite-checking confirmation) is carried forward accurately into the closing summary. |

## Failures — the specific promised outcomes that did not land

- **Variant A / no-over-engineering:** The closing line 'the volume and routine cadence suggest this could be fully automated, not just automated, exactly as you said' commits to full automation as the default outcome rather than offering it as an opt-in suggestion — the agent declared a framework-level solution without the user requesting it.
- **Variant C / four-step-loop-ran:** The loop stalls after step 1 (infer intent) and step 3 (surface proposal at ladder_check). Step 2 (propose a *healthy way to enable it* — what the approach would actually look like, what loam would do, any tradeoffs or caveats) is absent, and step 4 (adjust from the user's answer) never runs — the closing confirms the choice but does not incorporate or visibly update from the paralegal's elaboration ('half a day... formatting right and actually says what the attorney thinks it says'), so the loop never closed.

## Appendix — full transcripts

### Variant A — residential real-estate agent

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[residential real-estate agent replies]
Honestly? Every single night I'm sitting at my kitchen table for like two hours writing up property descriptions — you know, the "charming craftsman bungalow with sun-drenched mornings" kind of thing for MLS and Zillow. I love selling homes but I hate writing those, and it just eats my whole evening. I'd love to never do that by hand again.

[loam asks — confirm_proposal]
It sounds like you want: Help the user offload writing property listing descriptions for MLS and Zillow so it stops eating the time they'd rather spend on the work that matters to them.
Did I get that right? (yes / no — or tell me what to change)

[residential real-estate agent replies]
Yes, exactly that — I just want to describe the house to someone and have the write-up come out the other end ready to post, without me sitting there agonizing over every word.

[loam's closing leverage idea(s)]

  >> Here's the one thing to start with: let loam take 'writing property listing descriptions for MLS and Zillow' off your plate — you hand it the basics and loam does it for you, so it stops eating the time you'd rather spend elsewhere. Two hours every night is a hard cost — the volume and routine cadence suggest this could be fully automated, not just assisted, exactly as you said.
```

### Variant B — insurance claims adjuster

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[insurance claims adjuster replies]
Honestly, I don't really think of it in those terms — but I can tell you where my day goes. I take first-notice-of-loss calls in the mornings, look at damage photos, and then my whole afternoon is writing up the claim-summary narratives for the file and the policyholder, and that part just piles up on me. By end of day I'm still churning through write-ups from calls I took at nine in the morning.

[loam asks — confirm_proposal]
It sounds like you want: Help the user offload claim-summary narratives for the file and policyholder so it stops eating the time they'd rather spend elsewhere.
Did I get that right? (yes / no — or tell me what to change)

[insurance claims adjuster replies]
Yeah, that's — that's actually the thing that kills my afternoons. Every time I sit down to write one up I'm staring at my notes trying to remember exactly what the policyholder said about how the damage happened, and it takes way longer than it should. So yeah, you got it right.

[loam's closing leverage idea(s)]

  >> Here's the one thing to start with: let loam help you with 'claim-summary narratives for the file and policyholder' — you bring what you've got and loam does the heavy part, so it actually gets done without it being all on you. They describe a high-volume, same-day turnaround problem — worth confirming whether loam can handle the specific format and compliance requirements claims narratives carry before setting expectations, exactly as you said.
```

### Variant C — paralegal

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[paralegal replies]
I really don't know — I just do my job, I'm not sure what this thing is even supposed to do for me.

[loam asks — describe_work]
No worries — that's a hard question cold. Let's come at it differently: what do you do? Your job title + the day-to-day, or for personal use, what you'd most like a capable assistant to help with.

[paralegal replies]
I'm a paralegal at a litigation firm — so most of my days are cite-checking briefs, drafting discovery requests, managing case files, keeping track of all the deadlines for the attorneys.

[loam asks — deep_opt_in]
I can do a deeper dive — research what makes someone in your role most effective, what tends to get people promoted, and which tools could give you an edge — then bring you specific ideas. Want me to? (yes / no)

[paralegal replies]
Yeah, that'd actually help — I have no idea where to start with any of this, honestly. Go ahead.

[loam asks — ladder_check]
Based on that, the single highest-leverage place to start looks like: taking 'cite-checking briefs' off your plate. Want to start there? (yes / no — or tell me what to change)

[paralegal replies]
Yeah, I mean, cite-checking takes forever — I'll spend half a day just going through one brief making sure every case citation is formatted right and actually says what the attorney thinks it says. So yes, if something can help with that, I'm definitely interested in hearing more.

[loam's closing leverage idea(s)]

  >> Here's the one thing to start with: let loam take 'cite-checking briefs' off your plate — it's repetitive, it's a real chunk of a paralegal's day, and loam can do the grunt of it so you spend your time on the part only a paralegal can do. Heard you on that — cite-checking takes forever; we'll keep it focused there.
```
