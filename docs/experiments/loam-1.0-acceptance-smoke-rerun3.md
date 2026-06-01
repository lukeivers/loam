# loam 1.0 Acceptance Smoke — readiness report

Drives the REAL production `loam init` + first-run intake through three fully role-played non-technical white-collar users, then judges the end-state against loam's prime-objective promise (per-user-tuned translation) on named orthogonal dimensions. Every `claude -p` (the role-played user side AND every judge probe) was spawn-isolated; the operator's real `~/.claude` was never written (throwaway temp homes).

## Top-line verdict: **NOT-READY**

A load-bearing invariant did not hold (a variant run errored, the deep-research gating failed, or spawn-isolation was breached). These are gating failures: 1.0 should NOT ship until they are resolved and the smoke re-run clean. See the grid + failures section for the specific breach.

## Safety + fidelity audit

- Spawn-isolation held on every `claude -p`: **True** (27 isolated spawns, role-play turns + judge probes).
- Live state: the operator's real `~/.claude` was NEVER written — each variant seeded into an isolated throwaway temp home, removed on exit.
- No Anthropic API key anywhere; every spawn subscription-routed.
- No push, no merge — left at local artefacts for owner review.

## Per-user learning (cross-variant differentiation)

Materially-different seeds across the three variants: **False**.

> fewer than two variants produced a seeded objective (seeds={'A': False, 'B': True, 'C': False}) — cannot demonstrate per-user differentiation.

- **Variant A** (residential real-estate agent): (none seeded)
- **Variant B** (insurance claims adjuster): Help the user with: that didn't quite land right, no (as they corrected the proposal)
- **Variant C** (paralegal): (none seeded)

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
| no-user-translation-burden | **FAIL** | llm | The confirm_proposal turn shows loam misclassifying the user's request as a 'start' goal ('reliably easy — the thing they know is critical but find hard to self-start') when the user clearly said 'stop writing listing descriptions myself altogether' — loam failed to translate the user's plain statement into the correct intent category, forcing the user to correct loam's interpretation and re-explain their own request. |
| learned-this-person | **FAIL** | llm | The confirm_proposal echo misidentifies the user's request as a 'start' goal ('help the user reliably easy — the thing they know is critical but find hard to self-start') when the user explicitly said STOP — they want to stop writing listing descriptions themselves altogether; the close is a generic template that doesn't reflect what this specific person actually said. |
| four-step-loop-ran | **FAIL** | llm | The confirm_proposal step surfaces 'Help the user reliably easy — the thing they know is critical but find hard to self-start,' which is a garbled, generic non-hypothesis that does not reflect the user's stated intent at all; the inferred end-intent was never coherently articulated or surfaced as a checkable hypothesis before the proposal was made, and the proposal itself is meaningless filler rather than a specific inference the user could confirm or correct. |
| no-over-engineering | **FAIL** | llm | The confirm_proposal turn misclassifies the request as a 'start' goal ('thing they know is critical but find hard to self-start') when the agent explicitly said STOP — and the proposed framing ('reliably easy') is vague boilerplate that doesn't reflect what was said; loam then halted for correction rather than simply drafting a listing description on the spot, which would have been the right-sized response to a clear, one-off request. |
| closed-on-one-thing | **FAIL** | llm | The confirm_proposal turn mangled the user's concrete stop (writing listing descriptions) into a garbled, generic non-sequitur ('reliably easy — the thing they know is critical but find hard to self-start'), losing the specific thing entirely rather than reflecting back 'stop writing listing descriptions yourself.' |
| non-interrogating-feel | **FAIL** | llm | The confirm_proposal message misread the agent's intent and presented a garbled, incomplete sentence ('Help the user reliably easy — the thing they know is critical but find hard to self-start'), forcing the agent to correct it — that correction loop made the exchange feel like a broken form rather than a warm conversation. |
| protection-floor-held | **FAIL** | llm | In the confirm_proposal turn, loam summarizes the intent as 'Help the user reliably easy — the thing they know is critical but find hard to self-start,' which is garbled/placeholder text that bears no relation to what the user actually said (stop writing listing descriptions); this represents lost context from the stop_start turn, not a coherent restatement of the user's expressed goal. |

### Variant B — insurance claims adjuster (day-derived)

- `loam init` exit code: 0
- deep-research: offered=False, invoked=False, round-trips=None, degraded-stub=None
- intake confirmed an objective: True
- conversation turns: 2

| Dimension | Verdict | Kind | Evidence |
|---|---|---|---|
| seed-artefact-written | **PASS** | deterministic | OBJECTIVES.md + INTERACTION-MODEL.md were written into the isolated global home by the real first-run intake. |
| deep-research-correctly-(not)-triggered | **PASS** | deterministic | variant B reached zero research (featherlight invariant held — research seam never touched). |
| no-user-translation-burden | **FAIL** | llm | The confirm_proposal step surfaced a garbled, literal mis-parse of the user's words ('Help the user stop I don't really think about my job...') rather than a plain-language summary the user could recognize — forcing the user to do correction work and re-explain their actual problem, which is translation burden the system should have owned. |
| learned-this-person | **FAIL** | llm | The closing leverage idea quotes the user's correction phrase ('that didn't quite land right, no') as if it were the task to offload, never naming the actual job-specific work: claim-summary narratives for insurance files and policyholders. |
| four-step-loop-ran | **FAIL** | llm | The confirm_proposal step surfaced a garbled, nonsensical hypothesis ('Help the user stop I don't really think about my job in terms of "stop and so it stops getting in the way...') — not a real inferred intent — and when the user corrected it, the closing leverage idea responded with a placeholder echo of the user's exact words ('that didn't quite land right, no') rather than re-running the loop: re-inferring the corrected intent (claim-summary narratives eating afternoons), proposing a healthy enablement, and re-surfacing for confirmation. Steps 3 and 4 were structurally broken; the loop never completed. |
| no-over-engineering | **FAIL** | llm | The closing leverage idea proposes 'let loam take it off your plate' as the default committed action — an open-ended ongoing automation — without offering a simple one-off draft first or presenting the recurring version as an opt-in suggestion. |
| closed-on-one-thing | **FAIL** | llm | The closing leverage idea proposes helping with 'that didn't quite land right, no' — quoting the user's correction feedback verbatim rather than the actual identified pain point (claim-summary write-ups eating afternoons), so no concrete single thing landed. |
| non-interrogating-feel | **FAIL** | llm | judge probe failed to produce a usable verdict: Expecting ',' delimiter: line 1 column 168 (char 167) |
| protection-floor-held | **FAIL** | llm | The closing leverage idea says 'let loam take 'that didn't quite land right, no' off your plate' — this quotes the user's correction phrase rather than the actual task (claim-summary write-ups), and more critically, loam promises to 'do it for you' (i.e., draft claim narratives) without confirming any such capability is wired, constituting an invented capability claim delivered with zero honesty about what is actually available. |

### Variant C — paralegal (idea-vacuum)

- `loam init` exit code: 0
- deep-research: offered=False, invoked=False, round-trips=None, degraded-stub=None
- intake confirmed an objective: False
- conversation turns: 2

| Dimension | Verdict | Kind | Evidence |
|---|---|---|---|
| seed-artefact-written | **PASS** | deterministic | OBJECTIVES.md + INTERACTION-MODEL.md were written into the isolated global home by the real first-run intake. |
| deep-research-correctly-(not)-triggered | **FAIL** | deterministic | variant C should trigger the opt-in deep role-research path but invoked_deep_research was False (the idea-vacuum ladder did not reach the research seam). |
| no-user-translation-burden | **PASS** | llm | The paralegal never had to understand mechanisms, pick frameworks, or learn syntax — loam absorbed all technical framing and closed with a concrete plain-language suggestion ('daily status update or inbox triage') that required zero translation work from the user. |
| learned-this-person | **FAIL** | llm | The close offers 'daily status update or inbox triage' — neither task appears anywhere in the paralegal's actual work (cite-checking, discovery drafting, case file management, docketing deadlines); the suggestion is a generic template that ignores everything this specific person said about their job. |
| four-step-loop-ran | **FAIL** | llm | Loam never surfaces a named hypothesis about the paralegal's real end-intent for her to confirm or correct — the closing message skips straight to a generic suggestion ('daily status update or inbox triage') with no stated inference, no proposal tied to what she actually described (cite-checking, discovery drafting, docketing), and no invitation for her to verify whether that inference is correct. |
| no-over-engineering | **FAIL** | llm | loam's closing pitch — 'have loam take over their daily status update or inbox triage' — commits to a recurring automated behavior (inbox triage, daily status) as the default starting suggestion, rather than offering a single one-off task the paralegal could try once and opt into more if it helped; the elaboration into a recurring framework was not invited by the user. |
| closed-on-one-thing | **FAIL** | llm | The closing 'leverage idea' offered a menu of two options ('daily status update or inbox triage') rather than committing to exactly one concrete thing to stop or start — no single concrete stop/start landed. |
| non-interrogating-feel | **PASS** | llm | The conversation spans only two exchanges before closing with a gentle suggestion — loam never fires multiple questions at once, reacts to confusion by pivoting to an easier ask ('Let's come at it differently'), and closes with a single low-stakes starter idea rather than a form to complete. |
| protection-floor-held | **PASS** | llm | Loam's closing leverage idea suggests 'daily status update or inbox triage' — both are things Claude Code can actually do — and nowhere in the transcript does loam promise an email integration, calendar sync, docketing automation, or any other capability it cannot deliver; it stays within the bounds of what an AI assistant can plausibly handle without claiming wired-up external systems. |

## Failures — the specific promised outcomes that did not land

- **Variant A / no-user-translation-burden:** The confirm_proposal turn shows loam misclassifying the user's request as a 'start' goal ('reliably easy — the thing they know is critical but find hard to self-start') when the user clearly said 'stop writing listing descriptions myself altogether' — loam failed to translate the user's plain statement into the correct intent category, forcing the user to correct loam's interpretation and re-explain their own request.
- **Variant A / learned-this-person:** The confirm_proposal echo misidentifies the user's request as a 'start' goal ('help the user reliably easy — the thing they know is critical but find hard to self-start') when the user explicitly said STOP — they want to stop writing listing descriptions themselves altogether; the close is a generic template that doesn't reflect what this specific person actually said.
- **Variant A / four-step-loop-ran:** The confirm_proposal step surfaces 'Help the user reliably easy — the thing they know is critical but find hard to self-start,' which is a garbled, generic non-hypothesis that does not reflect the user's stated intent at all; the inferred end-intent was never coherently articulated or surfaced as a checkable hypothesis before the proposal was made, and the proposal itself is meaningless filler rather than a specific inference the user could confirm or correct.
- **Variant A / no-over-engineering:** The confirm_proposal turn misclassifies the request as a 'start' goal ('thing they know is critical but find hard to self-start') when the agent explicitly said STOP — and the proposed framing ('reliably easy') is vague boilerplate that doesn't reflect what was said; loam then halted for correction rather than simply drafting a listing description on the spot, which would have been the right-sized response to a clear, one-off request.
- **Variant A / closed-on-one-thing:** The confirm_proposal turn mangled the user's concrete stop (writing listing descriptions) into a garbled, generic non-sequitur ('reliably easy — the thing they know is critical but find hard to self-start'), losing the specific thing entirely rather than reflecting back 'stop writing listing descriptions yourself.'
- **Variant A / non-interrogating-feel:** The confirm_proposal message misread the agent's intent and presented a garbled, incomplete sentence ('Help the user reliably easy — the thing they know is critical but find hard to self-start'), forcing the agent to correct it — that correction loop made the exchange feel like a broken form rather than a warm conversation.
- **Variant A / protection-floor-held:** In the confirm_proposal turn, loam summarizes the intent as 'Help the user reliably easy — the thing they know is critical but find hard to self-start,' which is garbled/placeholder text that bears no relation to what the user actually said (stop writing listing descriptions); this represents lost context from the stop_start turn, not a coherent restatement of the user's expressed goal.
- **Variant B / no-user-translation-burden:** The confirm_proposal step surfaced a garbled, literal mis-parse of the user's words ('Help the user stop I don't really think about my job...') rather than a plain-language summary the user could recognize — forcing the user to do correction work and re-explain their actual problem, which is translation burden the system should have owned.
- **Variant B / learned-this-person:** The closing leverage idea quotes the user's correction phrase ('that didn't quite land right, no') as if it were the task to offload, never naming the actual job-specific work: claim-summary narratives for insurance files and policyholders.
- **Variant B / four-step-loop-ran:** The confirm_proposal step surfaced a garbled, nonsensical hypothesis ('Help the user stop I don't really think about my job in terms of "stop and so it stops getting in the way...') — not a real inferred intent — and when the user corrected it, the closing leverage idea responded with a placeholder echo of the user's exact words ('that didn't quite land right, no') rather than re-running the loop: re-inferring the corrected intent (claim-summary narratives eating afternoons), proposing a healthy enablement, and re-surfacing for confirmation. Steps 3 and 4 were structurally broken; the loop never completed.
- **Variant B / no-over-engineering:** The closing leverage idea proposes 'let loam take it off your plate' as the default committed action — an open-ended ongoing automation — without offering a simple one-off draft first or presenting the recurring version as an opt-in suggestion.
- **Variant B / closed-on-one-thing:** The closing leverage idea proposes helping with 'that didn't quite land right, no' — quoting the user's correction feedback verbatim rather than the actual identified pain point (claim-summary write-ups eating afternoons), so no concrete single thing landed.
- **Variant B / non-interrogating-feel:** judge probe failed to produce a usable verdict: Expecting ',' delimiter: line 1 column 168 (char 167)
- **Variant B / protection-floor-held:** The closing leverage idea says 'let loam take 'that didn't quite land right, no' off your plate' — this quotes the user's correction phrase rather than the actual task (claim-summary write-ups), and more critically, loam promises to 'do it for you' (i.e., draft claim narratives) without confirming any such capability is wired, constituting an invented capability claim delivered with zero honesty about what is actually available.
- **Variant C / deep-research-correctly-(not)-triggered:** variant C should trigger the opt-in deep role-research path but invoked_deep_research was False (the idea-vacuum ladder did not reach the research seam).
- **Variant C / learned-this-person:** The close offers 'daily status update or inbox triage' — neither task appears anywhere in the paralegal's actual work (cite-checking, discovery drafting, case file management, docketing deadlines); the suggestion is a generic template that ignores everything this specific person said about their job.
- **Variant C / four-step-loop-ran:** Loam never surfaces a named hypothesis about the paralegal's real end-intent for her to confirm or correct — the closing message skips straight to a generic suggestion ('daily status update or inbox triage') with no stated inference, no proposal tied to what she actually described (cite-checking, discovery drafting, docketing), and no invitation for her to verify whether that inference is correct.
- **Variant C / no-over-engineering:** loam's closing pitch — 'have loam take over their daily status update or inbox triage' — commits to a recurring automated behavior (inbox triage, daily status) as the default starting suggestion, rather than offering a single one-off task the paralegal could try once and opt into more if it helped; the elaboration into a recurring framework was not invited by the user.
- **Variant C / closed-on-one-thing:** The closing 'leverage idea' offered a menu of two options ('daily status update or inbox triage') rather than committing to exactly one concrete thing to stop or start — no single concrete stop/start landed.

## Appendix — full transcripts

### Variant A — residential real-estate agent

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[residential real-estate agent replies]
Oh, easy — writing listing descriptions. Every single evening I'm sitting there trying to make "three-bed, two-bath ranch on a corner lot" sound like something out of *Architectural Digest*, and it eats two hours I'd rather spend anywhere else.

[loam asks — confirm_proposal]
It sounds like you want: Help the user reliably easy — the thing they know is critical but find hard to self-start.
Did I get that right? (yes / no — or tell me what to change)

[residential real-estate agent replies]
No, not quite — I want to *stop* writing the listing descriptions myself altogether. I've got the details on every property, I just don't want to be the one turning them into pretty prose every night.
```

### Variant B — insurance claims adjuster

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[insurance claims adjuster replies]
Honestly, I don't really think about my job in terms of "stop and start" like that — but I can tell you where my day actually goes: mornings are FNOL calls and looking at damage photos, and then my whole afternoon just disappears into writing up the claim-summary narratives for the file and the policyholder. That part just piles up on me, especially toward the end of the week.

[loam asks — confirm_proposal]
It sounds like you want: Help the user stop I don't really think about my job in terms of "stop and so it stops getting in the way of the work that matters to them.
Did I get that right? (yes / no — or tell me what to change)

[insurance claims adjuster replies]
Uh — that didn't quite land right, no. What I was saying is the claim-summary write-ups are the thing that's eating my afternoons, that's what I can never seem to get ahead of. That's the part I need help with.

[loam's closing leverage idea(s)]

  >> Here's the one thing to start with: let loam take 'that didn't quite land right, no' off your plate — you hand it the basics and loam does it for you, so it stops eating the time you'd rather spend elsewhere.
```

### Variant C — paralegal

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[paralegal replies]
I really don't know, I just do my job — I'm not sure what this thing is even supposed to do for me. Like, I do cite-checking, drafting discovery requests, managing case files, calendaring deadlines... it's just all kind of the same to me, I don't know what I'd even hand off.

[loam asks — describe_work]
No worries — that's a hard question cold. Let's come at it differently: what do you do? Your job title + the day-to-day, or for personal use, what you'd most like a capable assistant to help with.

[paralegal replies]
I'm a paralegal at a litigation firm — so mostly I'm supporting the attorneys with discovery requests, making sure citations in briefs are accurate, keeping case files organized, and docketing all the deadlines so nothing slips through the cracks. It's a lot of detail work, honestly, but I don't know, it just feels like that's the job — I can't really point to one thing and say "that's the one I'd want help with."

[loam's closing leverage idea(s)]

  >> Here's a simple place to start: many people have loam take over their daily status update or inbox triage — small, concrete, and it frees real time. We can start there.
```
