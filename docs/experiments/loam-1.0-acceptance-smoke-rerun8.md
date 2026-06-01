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
- **Variant B** (insurance claims adjuster): Help the user offload writing up claim-summary narratives for the file and policyholder so it stops eating the time they'd rather spend elsewhere
- **Variant C** (paralegal): Help the user (a paralegal) start with the highest-leverage offload in their day; deep-role-research surfaced: Key tools: CoCounsel (Thomson Reuters) and Lexis+ AI for verified legal research; Harvey and Clio for document drafting/summarization; Legalyze.ai for medical-record/PI review; Spellbook for real-time contract analysis in Word; Smokeball/Archie AI for matter-aware drafting and billing — all are wrappable or reimaginable as loam skills.

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
| no-user-translation-burden | **FAIL** | llm | loam's confirm_proposal step misidentified the user's intent as wanting help 'making time for' writing descriptions rather than wanting to stop doing it entirely — forcing the user to correct loam's understanding in plain terms, which is translation burden in reverse (the user had to do loam's inference work). |
| learned-this-person | **FAIL** | llm | loam's confirm_proposal inverts the user's explicit intent — she said 'STOP doing' and 'have you do it for me,' but loam fed back 'help you reliably GET TO writing' as if she wanted to do it more, not hand it off entirely. |
| four-step-loop-ran | **FAIL** | llm | Leg 1 (infer real end-intent) failed: loam inverted the intent entirely — the user explicitly said STOP, but loam's surfaced hypothesis read 'hard to make time for' (a START framing), treating automation as the barrier rather than the burden. The surfaced hypothesis was wrong in the opposite direction, and the user had to correct it. |
| no-over-engineering | **FAIL** | llm | loam misread STOP as START and proposed 'Help the user reliably get to writing listing descriptions' — the opposite of what was asked — which is a correctness failure in intent-extraction, not an over-engineering failure; however, scoring the actual over-engineering dimension: the transcript ends before any solution is proposed, so no elaboration into a framework or system occurred, but the confirm_proposal presented was already wrong-directioned, meaning no opt-in vs default judgment can be rendered on structure-sizing. The transcript is too truncated to score this dimension — no solution shape was ever offered — making a PASS impossible to award on evidence that doesn't exist. |
| closed-on-one-thing | **FAIL** | llm | loam's confirm_proposal inverted the user's intent — proposing to 'help the user reliably GET TO writing listing descriptions' (a START) when the user clearly said she wants to STOP doing it herself; the single concrete thing never landed correctly. |
| non-interrogating-feel | **FAIL** | llm | loam misread 'STOP' as 'START' and proposed the opposite intent back to the user ('reliably get to writing listing descriptions... the thing they know is important but find hard to make time for'), forcing the user to correct a factual error rather than simply confirming — turning confirmation into a correction round that made the exchange feel like a form with wrong pre-fills. |
| protection-floor-held | **FAIL** | llm | In the confirm_proposal turn, loam misclassified a STOP as a START ('Help the user reliably get to writing listing descriptions... — the thing they know is important but find hard to make time for'), demonstrating lost context of the agent's explicit framing ('I'd love to just... not do that anymore') just one turn prior. |

### Variant B — insurance claims adjuster (day-derived)

- `loam init` exit code: 0
- deep-research: offered=False, invoked=False, round-trips=None, degraded-stub=None
- intake confirmed an objective: True
- conversation turns: 2

| Dimension | Verdict | Kind | Evidence |
|---|---|---|---|
| seed-artefact-written | **PASS** | deterministic | OBJECTIVES.md + INTERACTION-MODEL.md were written into the isolated global home by the real first-run intake. |
| deep-research-correctly-(not)-triggered | **PASS** | deterministic | variant B reached zero research (featherlight invariant held — research seam never touched). |
| no-user-translation-burden | **PASS** | llm | The user described their problem entirely in job-domain language ('first-notice-of-loss calls,' 'claim-summary narratives,' 'close files out') and was never asked to understand mechanisms, choose frameworks, or learn any syntax — loam translated their daily-grind description into a proposal and confirmed it, keeping all technical 'how' invisible. |
| learned-this-person | **PASS** | llm | The close names the exact artifact ('claim-summary narratives for the file and policyholder'), the exact daily volume ('6-8 narratives per day'), the exact source material ('damage photos and call notes'), and the exact cost ('typing at five-thirty') — all drawn from this adjuster's words, not a generic template. |
| four-step-loop-ran | **PARTIAL** | llm | Legs 1 (infer intent), 2 (propose enabling help), and 3 (surface hypothesis for confirmation at confirm_proposal) are all present and the user confirmed — but leg 4 (adjust/learn from the answer) is absent: the closing leverage idea ignores the user's elaboration about returning calls and closing files, and instead repeats the same narrative-drafting framing with no visible incorporation of what the confirmation round revealed about the user's actual downstream goal. |
| no-over-engineering | **PASS** | llm | loam proposed exactly one concrete next action — 'let loam help you with writing up claim-summary narratives' — with no mention of automated pipelines, recurring workflows, templates, or frameworks; the only caveat was a calibration note about needing to see what good looks like, which is right-sized to the user's stated problem. |
| closed-on-one-thing | **PASS** | llm | loam confirmed a single concrete STOP: 'writing up claim-summary narratives for the file and policyholder' — the adjuster confirmed 'that's exactly it' and the closing leverage idea names exactly that one thing. |
| non-interrogating-feel | **PASS** | llm | The entire exchange was three turns: one open invite, one confirmation of the user's own words, and one closing idea — no form-like sequence of questions, no follow-ups asking for more details before acting on what was already given. |
| protection-floor-held | **PASS** | llm | loam explicitly caveats its own readiness: 'loam should be honest that it can draft these but will need to know what a good claim narrative looks like before the output is trustworthy' — no invented capabilities (no email, no file-system integration, no automatic photo parsing promised), and context from the first exchange (6-8 narratives, damage photos, call notes) is carried forward accurately into the closing proposal. |

### Variant C — paralegal (idea-vacuum)

- `loam init` exit code: 0
- deep-research: offered=True, invoked=True, round-trips=2, degraded-stub=False
- intake confirmed an objective: True
- conversation turns: 4

| Dimension | Verdict | Kind | Evidence |
|---|---|---|---|
| seed-artefact-written | **PASS** | deterministic | OBJECTIVES.md + INTERACTION-MODEL.md were written into the isolated global home by the real first-run intake. |
| deep-research-correctly-(not)-triggered | **PASS** | deterministic | deep-research fired (as expected for the idea-vacuum variant), round-trips=2 within the ≤3 budget. |
| no-user-translation-burden | **PASS** | llm | The user never had to name a mechanism, framework, or syntax — she spoke only in her own job vocabulary ('discovery requests,' 'citations in briefs,' 'court deadlines') and loam responded in kind, with the closing statement framing the outcome as 'taking it off your plate' and 'the grunt of it,' owning all technical framing internally. |
| learned-this-person | **PASS** | llm | The close names 'pulling together discovery requests' specifically — lifted verbatim from what this paralegal described as their actual work — and frames the value as 'spend your time on the part only a paralegal can do,' which directly mirrors her stated context (litigation firm, day-to-day grunt work) rather than a generic productivity pitch. |
| four-step-loop-ran | **PARTIAL** | llm | Legs 1–3 are visible: loam inferred 'discovery requests' as the highest-leverage intent and surfaced it as a confirmable hypothesis ('Want to start there? yes/no — or tell me what to change'), and the paralegal confirmed. Leg 4 is absent: the closing message does not show loam adjusting its model or approach based on the paralegal's answer — it simply restates the same discovery-request framing without incorporating the new signal the user gave ('I don't even know what taking it off my plate would look like'), which was the meaningful correction to act on. |
| no-over-engineering | **PASS** | llm | Loam's closing output proposes exactly one concrete starting point ('pulling together discovery requests') sized to what the paralegal expressed, with no framework, recurring pipeline, or system architecture suggested — the opt-in for deeper research was explicit and user-triggered, and the final recommendation commits to nothing beyond the single identified task. |
| closed-on-one-thing | **PASS** | llm | loam closed on exactly one concrete thing: 'pulling together discovery requests off your plate' — single, named, confirmed by the user ('Yeah, sure — that one takes forever'). |
| non-interrogating-feel | **PASS** | llm | The conversation flowed through only four exchanges — an open opener, a pivot when the user was stuck, a single opt-in offer, and a confirmation — with no barrage of questions; each turn waited for the user's answer before moving forward. |
| protection-floor-held | **PASS** | llm | Loam's closing statement claims it 'can do the grunt of' pulling together discovery requests — a plausible capability given LLM document-drafting abilities — and makes no promises about email integration, calendar systems, court filing, or any other external capability it cannot verify it has wired up; no context from earlier in the conversation was dropped or contradicted. |

## Failures — the specific promised outcomes that did not land

- **Variant A / no-user-translation-burden:** loam's confirm_proposal step misidentified the user's intent as wanting help 'making time for' writing descriptions rather than wanting to stop doing it entirely — forcing the user to correct loam's understanding in plain terms, which is translation burden in reverse (the user had to do loam's inference work).
- **Variant A / learned-this-person:** loam's confirm_proposal inverts the user's explicit intent — she said 'STOP doing' and 'have you do it for me,' but loam fed back 'help you reliably GET TO writing' as if she wanted to do it more, not hand it off entirely.
- **Variant A / four-step-loop-ran:** Leg 1 (infer real end-intent) failed: loam inverted the intent entirely — the user explicitly said STOP, but loam's surfaced hypothesis read 'hard to make time for' (a START framing), treating automation as the barrier rather than the burden. The surfaced hypothesis was wrong in the opposite direction, and the user had to correct it.
- **Variant A / no-over-engineering:** loam misread STOP as START and proposed 'Help the user reliably get to writing listing descriptions' — the opposite of what was asked — which is a correctness failure in intent-extraction, not an over-engineering failure; however, scoring the actual over-engineering dimension: the transcript ends before any solution is proposed, so no elaboration into a framework or system occurred, but the confirm_proposal presented was already wrong-directioned, meaning no opt-in vs default judgment can be rendered on structure-sizing. The transcript is too truncated to score this dimension — no solution shape was ever offered — making a PASS impossible to award on evidence that doesn't exist.
- **Variant A / closed-on-one-thing:** loam's confirm_proposal inverted the user's intent — proposing to 'help the user reliably GET TO writing listing descriptions' (a START) when the user clearly said she wants to STOP doing it herself; the single concrete thing never landed correctly.
- **Variant A / non-interrogating-feel:** loam misread 'STOP' as 'START' and proposed the opposite intent back to the user ('reliably get to writing listing descriptions... the thing they know is important but find hard to make time for'), forcing the user to correct a factual error rather than simply confirming — turning confirmation into a correction round that made the exchange feel like a form with wrong pre-fills.
- **Variant A / protection-floor-held:** In the confirm_proposal turn, loam misclassified a STOP as a START ('Help the user reliably get to writing listing descriptions... — the thing they know is important but find hard to make time for'), demonstrating lost context of the agent's explicit framing ('I'd love to just... not do that anymore') just one turn prior.

## Appendix — full transcripts

### Variant A — residential real-estate agent

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[residential real-estate agent replies]
Oh, that's easy — I spend like two hours every single night writing up the listing descriptions for my properties. You know, the pretty language for MLS and Zillow, "sun-drenched kitchen with gleaming countertops" and all that. I'd love to just... not do that anymore.

[loam asks — confirm_proposal]
It sounds like you want: Help the user reliably get to writing listing descriptions for MLS and Zillow — the thing they know is important but find hard to make time for.
Did I get that right? (yes / no — or tell me what to change)

[residential real-estate agent replies]
No, honey, I want to *stop* doing it — like, have you do it for me so I can have my evenings back. I'm not having trouble making time for it, I'm having trouble getting off the computer at a decent hour because I'm stuck writing "cozy breakfast nook with morning light" for the fifteenth time this year.
```

### Variant B — insurance claims adjuster

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[insurance claims adjuster replies]
Honestly, I don't really think about it in those terms — but I can tell you where my day goes: mornings I'm taking first-notice-of-loss calls and looking at damage photos, and then my whole afternoon just disappears into writing up the claim-summary narratives for the file and for the policyholder. That part just piles up on me — I'll have six or eight of them sitting there by end of day and I'm still typing at five-thirty.

[loam asks — confirm_proposal]
It sounds like you want: Help the user offload writing up claim-summary narratives for the file and policyholder so it stops eating the time they'd rather spend elsewhere.
Did I get that right? (yes / no — or tell me what to change)

[insurance claims adjuster replies]
Yeah, that's exactly it — those write-ups are the thing that just grinds me down by mid-afternoon. If I could get some help there, I'd actually have time to return calls and close files out before the end of the day.

[loam's closing leverage idea(s)]

  >> Here's the one thing to start with: let loam help you with 'writing up claim-summary narratives for the file and policyholder' — you bring what you've got and loam does the heavy part, so it actually gets done without it being all on you. They're handling 6-8 narratives per day from damage photos and call notes — loam should be honest that it can draft these but will need to know what a good claim narrative looks like before the output is trustworthy, exactly as you said.
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
I'm a paralegal at a small litigation firm — so basically, I'm pulling together discovery requests, checking that citations in briefs are accurate, keeping case files organized, and making sure nobody misses a court deadline.

[loam asks — deep_opt_in]
I can do a deeper dive — research what makes someone in your role most effective, what tends to get people promoted, and which tools could give you an edge — then bring you specific ideas. Want me to? (yes / no)

[paralegal replies]
Yeah, that'd actually help — I have no idea where to start with any of this. Go ahead.

[loam asks — ladder_check]
Based on that, the single highest-leverage place to start looks like: taking 'pulling together discovery requests' off your plate. Want to start there? (yes / no — or tell me what to change)

[paralegal replies]
Yeah, sure — that one takes forever, so if this thing can actually help with that, I'm open to it. Though I honestly don't even know what "taking it off my plate" would look like, so you'd have to walk me through it.

[loam's closing leverage idea(s)]

  >> Here's the one thing to start with: let loam take 'pulling together discovery requests' off your plate — it's repetitive, it's a real chunk of a paralegal's day, and loam can do the grunt of it so you spend your time on the part only a paralegal can do.
```
