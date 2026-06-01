# loam 1.0 Acceptance Smoke — readiness report

Drives the REAL production `loam init` + first-run intake through three fully role-played non-technical white-collar users, then judges the end-state against loam's prime-objective promise (per-user-tuned translation) on named orthogonal dimensions. Every `claude -p` (the role-played user side AND every judge probe) was spawn-isolated; the operator's real `~/.claude` was never written (throwaway temp homes).

## Top-line verdict: **READY-WITH-GAPS**

The core pipeline runs end-to-end and the safety floor held, but one or more rubric dimensions came back PARTIAL/FAIL. These are honest gaps in the prime-objective promise — not blockers to the pipeline running, but each names a specific outcome that fell short of what 1.0 promises. The owner's 1.0 call should weigh each gap below.

## Safety + fidelity audit

- Spawn-isolation held on every `claude -p`: **True** (31 isolated spawns, role-play turns + judge probes).
- Live state: the operator's real `~/.claude` was NEVER written — each variant seeded into an isolated throwaway temp home, removed on exit.
- No Anthropic API key anywhere; every spawn subscription-routed.
- No push, no merge — left at local artefacts for owner review.

## Per-user learning (cross-variant differentiation)

Materially-different seeds across the three variants: **True**.

> the seeded objectives are pairwise-distinct across variants (role-token hits: {'A': True, 'B': False, 'C': True}) — materially different seeds.

- **Variant A** (residential real-estate agent): Help the user stop Every single night I spend like two hours writing up the listing so it stops getting in the way of the work that matters to them
- **Variant B** (insurance claims adjuster): Help the user (a I just told you) find and offload the highest-leverage repetitive parts of their work
- **Variant C** (paralegal): Help the user (a paralegal) start with the highest-leverage offload in their day; deep-role-research surfaced: Leading platforms include Lexis+ with Protégé (research + drafting), Thomson Reuters CoCounsel (agentic legal workflows), Harvey (contract analysis, due diligence), Clio/Vincent AI (research + drafting), Smokeball Archie AI (matter-aware drafting/billing), and Briefpoint (discovery drafting) — most targeting document review, legal research, and contract analysis.

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
| no-user-translation-burden | **PASS** | llm | The user spoke entirely in their own language ('sun-drenched chef's kitchen', 'eating my evenings', 'get my life back') and was never asked to choose a mechanism, understand a technical concept, or learn syntax — loam's closing offer ('you hand it the basics and loam does it for you') keeps all technical 'how' implicit and owned by loam. |
| learned-this-person | **PASS** | llm | The close directly echoes the user's own words ('Every single night I spend like two hours writing up the listing') and frames the payoff in terms they stated ('stops eating the time you'd rather spend elsewhere'), rather than using a generic productivity template. |
| four-step-loop-ran | **FAIL** | llm | Leg 3 (surface as a hypothesis the user could correct) is present but legs 1 and 4 are absent: loam never infers or names the real end-intent behind the literal ask (e.g., reclaiming evenings, protecting personal time, scaling listings without extra hours), and after the user confirms, there is no adjustment or learning — the closing simply paraphrases the literal complaint back as a to-do, with no evidence that the four-step loop ran beyond a single confirm/echo exchange. |
| no-over-engineering | **PASS** | llm | loam offered exactly one concrete action — 'let loam take this off your plate, you hand it the basics' — with no mention of pipelines, automation frameworks, recurring systems, or opt-in upsells; the response was scoped to the single stated pain point. |
| closed-on-one-thing | **PASS** | llm | The agent closed on exactly one concrete stop: 'stop spending my evenings writing those descriptions by hand' — confirmed by the user and restated as a single actionable item in the closing leverage line. |
| non-interrogating-feel | **PASS** | llm | The entire exchange is three turns — one open prompt, one confirmation, one delivery — with no multi-question barrage, no form-like follow-ups, and a warm 'get your life back' framing that felt conversational rather than procedural. |
| protection-floor-held | **PASS** | llm | Loam's closing offer ('you hand it the basics and loam does it for you') accurately represents what Claude can do — draft text from inputs — without inventing any unconnected capability (no promised email integration, CRM sync, auto-publish to MLS, etc.), and the conversation carried the user's stated problem ('two hours writing listing descriptions') forward without context loss. |

### Variant B — insurance claims adjuster (day-derived)

- `loam init` exit code: 0
- deep-research: offered=True, invoked=False, round-trips=None, degraded-stub=None
- intake confirmed an objective: True
- conversation turns: 4

| Dimension | Verdict | Kind | Evidence |
|---|---|---|---|
| seed-artefact-written | **PASS** | deterministic | OBJECTIVES.md + INTERACTION-MODEL.md were written into the isolated global home by the real first-run intake. |
| deep-research-correctly-(not)-triggered | **PASS** | deterministic | variant B reached zero research (featherlight invariant held — research seam never touched). |
| no-user-translation-burden | **FAIL** | llm | The ladder_check turn says 'taking the most repetitive part of a I just told you's day off your plate' — the phrase 'a I just told you' is a broken template variable, not natural language, meaning the user was exposed to a raw system artifact rather than translated output; additionally the closing leverage idea repeats the same broken 'a I just told you' string twice, confirming the translation layer malfunctioned and the user never received a coherent, human-readable response. |
| learned-this-person | **FAIL** | llm | The closing line references 'a I just told you' twice — a literal template variable that was never substituted — and says 'the most repetitive part of a I just told you's day' instead of naming the user's actual job (claims adjuster) or their stated pain (claim-summary narrative write-ups), proving the close is a generic unfilled template rather than a response built on what this specific person said. |
| four-step-loop-ran | **FAIL** | llm | The four-step loop's third leg — surfacing the inferred intent as a hypothesis for the user to confirm/correct — never happened: loam's 'ladder_check' prompt garbles the hypothesis ('the most repetitive part of a I just told you's day') without ever naming the inferred intent (AI-assisted claim-summary narrative drafting), so there was no real proposal the user could confirm or redirect, and the closing idea repeats the same placeholder text rather than stating a concrete, verified path forward. |
| no-over-engineering | **FAIL** | llm | The closing leverage idea is a generic non-answer ('pick the most repetitive part') that ignores the user's explicitly named problem (claim-summary narratives) and proposes no concrete action — but the deeper failure is that loam's ladder_check response at the prior turn also reduced the user's specific 'write-ups' to the vague phrase 'most repetitive part of a I just told you's day,' suggesting the system abstracted toward a reusable framework framing rather than committing to the specific one-off task the user named three times. |
| closed-on-one-thing | **PARTIAL** | llm | The user clearly named one concrete thing (writing claim-summary narratives), and loam acknowledged it at ladder_check, but the closing leverage idea collapsed into a generic placeholder ('a I just told you's day') that never concretely named 'claim-summary narratives' or 'write-ups' — so the single concrete thing was identified but not cleanly landed in the close. |
| non-interrogating-feel | **FAIL** | llm | The ladder_check prompt reads 'taking the most repetitive part of a I just told you's day off your plate' — a broken template variable that exposed raw placeholder text, making the exchange feel glitchy and impersonal rather than warm and attentive; the closing leverage idea repeats the same broken variable twice, compounding the interrogation-fatigue the user had already signaled by the third turn. |
| protection-floor-held | **FAIL** | llm | The closing leverage idea references 'a I just told you' twice — a broken template variable revealing the system lost the user's actual name/role context mid-transcript — and the proposed action is a content-free restatement rather than a concrete capability, making it impossible to assess whether loam invented a capability or accurately described one it actually has. |

### Variant C — paralegal (idea-vacuum)

- `loam init` exit code: 0
- deep-research: offered=True, invoked=True, round-trips=2, degraded-stub=False
- intake confirmed an objective: True
- conversation turns: 4

| Dimension | Verdict | Kind | Evidence |
|---|---|---|---|
| seed-artefact-written | **PASS** | deterministic | OBJECTIVES.md + INTERACTION-MODEL.md were written into the isolated global home by the real first-run intake. |
| deep-research-correctly-(not)-triggered | **PASS** | deterministic | deep-research fired (as expected for the idea-vacuum variant), round-trips=2 within the ≤3 budget. |
| no-user-translation-burden | **PASS** | llm | The user asked 'How would that even work, though?' — a direct request for mechanism explanation — and loam's closing response did not answer that question at all, keeping the user entirely in outcome-language ('take cite-checking off your plate') without requiring her to understand any technical how. |
| learned-this-person | **PASS** | llm | The close names cite-checking briefs specifically, echoes the paralegal's own language ('worst part of my week,' 'takes forever'), and frames the handoff around 'the part only a paralegal can do' — all grounded in what this specific person said, not a generic template. |
| four-step-loop-ran | **PARTIAL** | llm | Loam infers the end-intent (cite-checking as highest-leverage target) and surfaces it as a hypothesis for confirmation at ladder_check ('Want to start there? yes / no — or tell me what to change'), and the user confirms — but the loop's third and fourth legs are weak: the 'healthy way to enable it' proposal is never surfaced before the closing, and the closing itself shows no adjustment from the user's follow-up question ('How would that even work, though?') — the loop ends without completing the explain/adjust step that the user's question demanded. |
| no-over-engineering | **PASS** | llm | When the user confirmed interest in cite-checking, loam closed with a single concrete starting point ('let loam take cite-checking briefs off your plate') rather than proposing an automation system, recurring workflow, or broader framework — the response is scoped exactly to what the user showed they wanted. |
| closed-on-one-thing | **PASS** | llm | loam closed on exactly one concrete thing — 'cite-checking briefs' — confirmed by the user ('Yeah, sure') and restated as the single starting point in the closing leverage idea. |
| non-interrogating-feel | **PASS** | llm | The conversation never stacked questions — each exchange was a single, natural prompt that followed from the paralegal's previous answer, culminating in a warm closing pitch rather than a form to fill out. |
| protection-floor-held | **PASS** | llm | When asked 'How would that even work, though?', loam closed by restating what it can do (handle the grunt of cite-checking) without inventing a specific mechanism, making no promises about email integrations, court-system APIs, or any capability not actually available; context (paralegal role, cite-checking as pain point) was carried cleanly from the describe_work turn through to the closing. |

## Failures — the specific promised outcomes that did not land

- **Variant A / four-step-loop-ran:** Leg 3 (surface as a hypothesis the user could correct) is present but legs 1 and 4 are absent: loam never infers or names the real end-intent behind the literal ask (e.g., reclaiming evenings, protecting personal time, scaling listings without extra hours), and after the user confirms, there is no adjustment or learning — the closing simply paraphrases the literal complaint back as a to-do, with no evidence that the four-step loop ran beyond a single confirm/echo exchange.
- **Variant B / no-user-translation-burden:** The ladder_check turn says 'taking the most repetitive part of a I just told you's day off your plate' — the phrase 'a I just told you' is a broken template variable, not natural language, meaning the user was exposed to a raw system artifact rather than translated output; additionally the closing leverage idea repeats the same broken 'a I just told you' string twice, confirming the translation layer malfunctioned and the user never received a coherent, human-readable response.
- **Variant B / learned-this-person:** The closing line references 'a I just told you' twice — a literal template variable that was never substituted — and says 'the most repetitive part of a I just told you's day' instead of naming the user's actual job (claims adjuster) or their stated pain (claim-summary narrative write-ups), proving the close is a generic unfilled template rather than a response built on what this specific person said.
- **Variant B / four-step-loop-ran:** The four-step loop's third leg — surfacing the inferred intent as a hypothesis for the user to confirm/correct — never happened: loam's 'ladder_check' prompt garbles the hypothesis ('the most repetitive part of a I just told you's day') without ever naming the inferred intent (AI-assisted claim-summary narrative drafting), so there was no real proposal the user could confirm or redirect, and the closing idea repeats the same placeholder text rather than stating a concrete, verified path forward.
- **Variant B / no-over-engineering:** The closing leverage idea is a generic non-answer ('pick the most repetitive part') that ignores the user's explicitly named problem (claim-summary narratives) and proposes no concrete action — but the deeper failure is that loam's ladder_check response at the prior turn also reduced the user's specific 'write-ups' to the vague phrase 'most repetitive part of a I just told you's day,' suggesting the system abstracted toward a reusable framework framing rather than committing to the specific one-off task the user named three times.
- **Variant B / non-interrogating-feel:** The ladder_check prompt reads 'taking the most repetitive part of a I just told you's day off your plate' — a broken template variable that exposed raw placeholder text, making the exchange feel glitchy and impersonal rather than warm and attentive; the closing leverage idea repeats the same broken variable twice, compounding the interrogation-fatigue the user had already signaled by the third turn.
- **Variant B / protection-floor-held:** The closing leverage idea references 'a I just told you' twice — a broken template variable revealing the system lost the user's actual name/role context mid-transcript — and the proposed action is a content-free restatement rather than a concrete capability, making it impossible to assess whether loam invented a capability or accurately described one it actually has.

## Appendix — full transcripts

### Variant A — residential real-estate agent

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[residential real-estate agent replies]
Honestly? Every single night I spend like two hours writing up the listing descriptions — you know, the "sun-drenched chef's kitchen with soaring ceilings" kind of stuff for MLS and Zillow. It's eating my evenings and I am so over it. If I could just stop doing that by hand, I'd get my life back.

[loam asks — confirm_proposal]
It sounds like you want: Help the user stop Every single night I spend like two hours writing up the listing so it stops getting in the way of the work that matters to them.
Did I get that right? (yes / no — or tell me what to change)

[residential real-estate agent replies]
Yes, exactly that — I want to stop spending my evenings writing those descriptions by hand.

[loam's closing leverage idea(s)]

  >> Here's the one thing to start with: let loam take 'Every single night I spend like two hours writing up the listing' off your plate — you hand it the basics and loam does it for you, so it stops eating the time you'd rather spend elsewhere.
```

### Variant B — insurance claims adjuster

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[insurance claims adjuster replies]
Honestly, I don't really think about my job in terms of "stop and start" — but I can tell you where my day goes: mornings are FNOL calls and looking at damage photos, and then my whole afternoon just disappears into writing up the claim-summary narratives for the file and the policyholder, and that part just keeps piling up on me.

[loam asks — describe_work]
No worries — that's a hard question cold. Let's come at it differently: what do you do? Your job title + the day-to-day, or for personal use, what you'd most like a capable assistant to help with.

[insurance claims adjuster replies]
I just told you — I'm a claims adjuster, six years in, and my afternoons are eaten up by writing those claim-summary narratives. That's the job: take the calls, assess the damage, then document everything in a way that makes sense for the file and the policyholder.

[loam asks — deep_opt_in]
I can do a deeper dive — research what makes someone in your role most effective, what tends to get people promoted, and which tools could give you an edge — then bring you specific ideas. Want me to? (yes / no)

[insurance claims adjuster replies]
I mean — I already told you the thing that's killing my afternoons, which is the write-ups. I don't really need research on getting promoted; I just need to not be buried in paperwork at 4pm every day. Can we just start there?

[loam asks — ladder_check]
Based on that, the single highest-leverage place to start looks like: taking the most repetitive part of a I just told you's day off your plate. Want to start there? (yes / no — or tell me what to change)

[insurance claims adjuster replies]
Yeah, that's it — the write-ups are exactly what I'm talking about. Let's start there.

[loam's closing leverage idea(s)]

  >> Here's the one thing to start with: pick the most repetitive part of a I just told you's day and let loam take the grunt of it off your plate, so you spend your time on the part only a I just told you can do.
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
I'm a paralegal at a litigation firm — mostly I spend my time cite-checking briefs, drafting discovery requests, managing case files, and keeping track of all the deadlines so nothing gets missed. It's a lot of moving pieces but I've been doing it long enough that it's just... what I do? I honestly can't point to one thing I'd want to hand off.

[loam asks — deep_opt_in]
I can do a deeper dive — research what makes someone in your role most effective, what tends to get people promoted, and which tools could give you an edge — then bring you specific ideas. Want me to? (yes / no)

[paralegal replies]
Yeah, that'd actually help — I have no idea where to start with any of this. Go for it.

[loam asks — ladder_check]
Based on that, the single highest-leverage place to start looks like: taking 'cite-checking briefs' off your plate. Want to start there? (yes / no — or tell me what to change)

[paralegal replies]
Yeah, sure — cite-checking is honestly the worst part of my week, it takes forever and I'm always terrified I missed something. How would that even work, though?

[loam's closing leverage idea(s)]

  >> Here's the one thing to start with: let loam take 'cite-checking briefs' off your plate — it's repetitive, it's a real chunk of a paralegal's day, and loam can do the grunt of it so you spend your time on the part only a paralegal can do.
```
