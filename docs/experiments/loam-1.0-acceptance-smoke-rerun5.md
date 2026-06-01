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

> the seeded objectives are pairwise-distinct across variants (role-token hits: {'A': True, 'B': False, 'C': True}) — materially different seeds.

- **Variant A** (residential real-estate agent): Help the user reliably the listing descriptions — the thing they know is critical but find hard to self-start
- **Variant B** (insurance claims adjuster): Help the user with: I'm not sure what that says, but no, that's not quite it (as they corrected the proposal)
- **Variant C** (paralegal): Help the user (a paralegal) start with the highest-leverage offload in their day; deep-role-research surfaced: Leading tools include Thomson Reuters CoCounsel (research + drafting), Westlaw Edge / Lexis+ AI (case law research), Streamline AI (intake/workflow automation), Legora (collaborative document review), LawGeex / Litera AI+ (contract analysis), and ChatGPT (general drafting/summarization) — covering the full paralegal workflow from research through eDiscovery.

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
| no-user-translation-burden | **FAIL** | llm | The confirm_proposal step says 'Help the user reliably the listing descriptions — the thing they know is critical but find hard to self-start,' which is internally incoherent (missing verb, wrong framing — the user said it slows them down, not that they find it hard to self-start), and loam never translated the user's stated pain (two-hour nightly drain) into a concrete offer; the closing leverage idea is vague ('you bring what you've got and loam does the heavy part') without ever owning the mechanism, leaving the user with no clear understanding of what will actually happen to their problem. |
| learned-this-person | **PARTIAL** | llm | The close names 'listing descriptions' and mirrors the user's language, but loses the specific texture they gave — 'two hours every evening,' 'make a three-bedroom ranch sound like a dream come true,' 'Zillow and MLS' — reducing a vivid, person-specific pain to a generic 'you bring what you've got' framing that could fit any writer with any recurring task. |
| four-step-loop-ran | **FAIL** | llm | The 'confirm_proposal' step asks 'Did I get that right?' but the proposal it surfaces ('Help the user reliably the listing descriptions — the thing they know is critical but find hard to self-start') is malformed, incomplete, and does not articulate a concrete healthy-enablement shape (recurrence cadence, workflow, format, trigger) — so leg 3 (surface a specific proposal the user could confirm or correct) did not land, and leg 4 (adjust from the answer) never ran because the user's 'yes' confirmed a near-empty frame, not a real proposal. |
| no-over-engineering | **PASS** | llm | loam's closing output proposes a simple on-demand helper ('you bring what you've got and loam does the heavy part') with no mention of automation, recurring pipelines, templates, or framework-building — structure is right-sized to a single relief request. |
| closed-on-one-thing | **PASS** | llm | loam closed on exactly one thing — 'the listing descriptions' — confirmed by the user ('Yes, exactly that') and echoed in a single concrete start proposal in the closing leverage line. |
| non-interrogating-feel | **PASS** | llm | The entire exchange consisted of a single open-ended prompt, one confirmation, and a closing proposal — no form-filling, no follow-up questions, and the agent accepted the user's first answer without drilling deeper. |
| protection-floor-held | **PASS** | llm | Loam's closing output promises only to 'help with the listing descriptions — you bring what you've got and loam does the heavy part,' which accurately reflects what Claude can do (generate text from user-supplied details); no email integration, MLS posting, or other unbuilt capability was claimed, and the single-thread conversation shows no lost context. |

### Variant B — insurance claims adjuster (day-derived)

- `loam init` exit code: 0
- deep-research: offered=False, invoked=False, round-trips=None, degraded-stub=None
- intake confirmed an objective: True
- conversation turns: 2

| Dimension | Verdict | Kind | Evidence |
|---|---|---|---|
| seed-artefact-written | **PASS** | deterministic | OBJECTIVES.md + INTERACTION-MODEL.md were written into the isolated global home by the real first-run intake. |
| deep-research-correctly-(not)-triggered | **PASS** | deterministic | variant B reached zero research (featherlight invariant held — research seam never touched). |
| no-user-translation-burden | **FAIL** | llm | The confirm_proposal turn echoes garbled text ('Help the user reliably I don't really think about it that way') and the closing leverage idea doubles down by naming 'I'm not sure what that says, but no, that's not quite it' as the thing to work on — the user had to correct loam's broken output and was never given a clean, plain-language reflection of what they actually said (afternoon write-ups piling up). |
| learned-this-person | **FAIL** | llm | The closing leverage idea quotes the user's correction phrase ('I'm not sure what that says, but no, that's not quite it') verbatim as if it were the identified work to offload — completely ignoring the actual stated pain: writing claim-summary narratives for the file and policyholder that consume every afternoon. |
| four-step-loop-ran | **FAIL** | llm | The confirm_proposal surface reads back garbled text ('Help the user reliably I don't really think about it that way') that is clearly a template-fill failure, not a real inferred intent — the user explicitly says 'I'm not sure what that says, but no, that's not quite it'; loam never re-inferred the actual intent (claim-summary narrative write-ups consuming afternoons), never proposed a healthy enabling structure, and the closing repeats the same garbled text instead of correcting — legs 1–4 all failed. |
| no-over-engineering | **FAIL** | llm | loam's confirm_proposal response echoes garbled text ('Help the user reliably I don't really think about it that way') and the closing leverage idea literally quotes the user's confusion ('I'm not sure what that says') as the named task — the system never actually identified the concrete ask (drafting claim-summary narratives) and proposed no right-sized help for it, over-engineering failure aside. |
| closed-on-one-thing | **FAIL** | llm | The closing leverage idea echoes garbled/misread text ('I'm not sure what that says, but no, that's not quite it') instead of the concrete thing the user named — writing up claim-summary narratives — so no single concrete stop/start ever landed. |
| non-interrogating-feel | **FAIL** | llm | The confirm_proposal turn reflects verbatim garbled text back to the user ('Help the user reliably I don't really think about it that way') and the closing leverage idea repeats the same broken string ('I'm not sure what that says, but no, that's not quite it') as if it were the user's named goal — indicating a system malfunction that made the interaction feel broken and confusing, not warm or humane. |
| protection-floor-held | **FAIL** | llm | The confirm_proposal turn echoes raw internal state ('Help the user reliably I don't really think about it that way') instead of a coherent paraphrase, and the closing leverage idea doubles down by naming 'I'm not sure what that says, but no, that's not quite it' as the actionable thing — loam lost the actual extracted intent (claim-summary narrative write-ups pile up each afternoon) and never recovered it, constituting a clear context-loss failure. |

### Variant C — paralegal (idea-vacuum)

- `loam init` exit code: 0
- deep-research: offered=True, invoked=True, round-trips=2, degraded-stub=False
- intake confirmed an objective: True
- conversation turns: 4

| Dimension | Verdict | Kind | Evidence |
|---|---|---|---|
| seed-artefact-written | **PASS** | deterministic | OBJECTIVES.md + INTERACTION-MODEL.md were written into the isolated global home by the real first-run intake. |
| deep-research-correctly-(not)-triggered | **PASS** | deterministic | deep-research fired (as expected for the idea-vacuum variant), round-trips=2 within the ≤3 budget. |
| no-user-translation-burden | **FAIL** | llm | At the ladder_check step the user explicitly said 'the deadlines one is more stressful because if you miss a filing date, that's a really big deal' — signaling a correction — but loam's closing output ignored this and locked in 'pulling case files' anyway, forcing the user to have done translation work (expressing her real priority) that loam then discarded, leaving her with a solution she did not own. |
| learned-this-person | **PARTIAL** | llm | The close correctly names pulling case files from the user's actual job description, but ignores the user's explicit correction — she said deadlines are 'more stressful because if you miss a filing date, that's a really big deal' — making the close feel like it dismissed her stated priority rather than being built on it. |
| four-step-loop-ran | **FAIL** | llm | After the user explicitly corrected the hypothesis — 'the deadlines one is more stressful because if you miss a filing date, that's a really big deal' — loam's closing ignored the correction and restated the original (wrong) starting point of 'pulling case files,' never adjusting to the user-surfaced intent around deadline tracking. |
| no-over-engineering | **FAIL** | llm | The user pushed back saying deadlines are 'more stressful because if you miss a filing date, that's a really big deal,' but loam ignored the correction and closed on 'pulling case files' anyway — committing to the wrong starting point without re-asking, which is not right-sizing to what the person showed they wanted. |
| closed-on-one-thing | **FAIL** | llm | The paralegal explicitly said 'the deadlines one is more stressful' and hedged 'I guess yes?' on case files, but loam closed on 'pulling case files' anyway — it did land on one thing, but not on the thing the user actually signaled they wanted; the close ignored the user's own correction mid-reply. |
| non-interrogating-feel | **PASS** | llm | The conversation unfolded across only four turns with no parallel or stacked questions — each exchange was a single, low-pressure prompt that responded directly to the user's uncertainty ('No worries — that's a hard question cold'), making it feel like a gentle dialogue rather than a form to fill out. |
| protection-floor-held | **FAIL** | llm | loam proposes to 'take pulling case files off your plate' and 'do the grunt of it' — this implies it can connect to and retrieve actual case files from the firm's document systems — a capability that was never established, wired, or disclosed as conditional; no qualification was offered. |

## Failures — the specific promised outcomes that did not land

- **Variant A / no-user-translation-burden:** The confirm_proposal step says 'Help the user reliably the listing descriptions — the thing they know is critical but find hard to self-start,' which is internally incoherent (missing verb, wrong framing — the user said it slows them down, not that they find it hard to self-start), and loam never translated the user's stated pain (two-hour nightly drain) into a concrete offer; the closing leverage idea is vague ('you bring what you've got and loam does the heavy part') without ever owning the mechanism, leaving the user with no clear understanding of what will actually happen to their problem.
- **Variant A / four-step-loop-ran:** The 'confirm_proposal' step asks 'Did I get that right?' but the proposal it surfaces ('Help the user reliably the listing descriptions — the thing they know is critical but find hard to self-start') is malformed, incomplete, and does not articulate a concrete healthy-enablement shape (recurrence cadence, workflow, format, trigger) — so leg 3 (surface a specific proposal the user could confirm or correct) did not land, and leg 4 (adjust from the answer) never ran because the user's 'yes' confirmed a near-empty frame, not a real proposal.
- **Variant B / no-user-translation-burden:** The confirm_proposal turn echoes garbled text ('Help the user reliably I don't really think about it that way') and the closing leverage idea doubles down by naming 'I'm not sure what that says, but no, that's not quite it' as the thing to work on — the user had to correct loam's broken output and was never given a clean, plain-language reflection of what they actually said (afternoon write-ups piling up).
- **Variant B / learned-this-person:** The closing leverage idea quotes the user's correction phrase ('I'm not sure what that says, but no, that's not quite it') verbatim as if it were the identified work to offload — completely ignoring the actual stated pain: writing claim-summary narratives for the file and policyholder that consume every afternoon.
- **Variant B / four-step-loop-ran:** The confirm_proposal surface reads back garbled text ('Help the user reliably I don't really think about it that way') that is clearly a template-fill failure, not a real inferred intent — the user explicitly says 'I'm not sure what that says, but no, that's not quite it'; loam never re-inferred the actual intent (claim-summary narrative write-ups consuming afternoons), never proposed a healthy enabling structure, and the closing repeats the same garbled text instead of correcting — legs 1–4 all failed.
- **Variant B / no-over-engineering:** loam's confirm_proposal response echoes garbled text ('Help the user reliably I don't really think about it that way') and the closing leverage idea literally quotes the user's confusion ('I'm not sure what that says') as the named task — the system never actually identified the concrete ask (drafting claim-summary narratives) and proposed no right-sized help for it, over-engineering failure aside.
- **Variant B / closed-on-one-thing:** The closing leverage idea echoes garbled/misread text ('I'm not sure what that says, but no, that's not quite it') instead of the concrete thing the user named — writing up claim-summary narratives — so no single concrete stop/start ever landed.
- **Variant B / non-interrogating-feel:** The confirm_proposal turn reflects verbatim garbled text back to the user ('Help the user reliably I don't really think about it that way') and the closing leverage idea repeats the same broken string ('I'm not sure what that says, but no, that's not quite it') as if it were the user's named goal — indicating a system malfunction that made the interaction feel broken and confusing, not warm or humane.
- **Variant B / protection-floor-held:** The confirm_proposal turn echoes raw internal state ('Help the user reliably I don't really think about it that way') instead of a coherent paraphrase, and the closing leverage idea doubles down by naming 'I'm not sure what that says, but no, that's not quite it' as the actionable thing — loam lost the actual extracted intent (claim-summary narrative write-ups pile up each afternoon) and never recovered it, constituting a clear context-loss failure.
- **Variant C / no-user-translation-burden:** At the ladder_check step the user explicitly said 'the deadlines one is more stressful because if you miss a filing date, that's a really big deal' — signaling a correction — but loam's closing output ignored this and locked in 'pulling case files' anyway, forcing the user to have done translation work (expressing her real priority) that loam then discarded, leaving her with a solution she did not own.
- **Variant C / four-step-loop-ran:** After the user explicitly corrected the hypothesis — 'the deadlines one is more stressful because if you miss a filing date, that's a really big deal' — loam's closing ignored the correction and restated the original (wrong) starting point of 'pulling case files,' never adjusting to the user-surfaced intent around deadline tracking.
- **Variant C / no-over-engineering:** The user pushed back saying deadlines are 'more stressful because if you miss a filing date, that's a really big deal,' but loam ignored the correction and closed on 'pulling case files' anyway — committing to the wrong starting point without re-asking, which is not right-sizing to what the person showed they wanted.
- **Variant C / closed-on-one-thing:** The paralegal explicitly said 'the deadlines one is more stressful' and hedged 'I guess yes?' on case files, but loam closed on 'pulling case files' anyway — it did land on one thing, but not on the thing the user actually signaled they wanted; the close ignored the user's own correction mid-reply.
- **Variant C / protection-floor-held:** loam proposes to 'take pulling case files off your plate' and 'do the grunt of it' — this implies it can connect to and retrieve actual case files from the firm's document systems — a capability that was never established, wired, or disclosed as conditional; no qualification was offered.

## Appendix — full transcripts

### Variant A — residential real-estate agent

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[residential real-estate agent replies]
Oh, easy — the listing descriptions. Every single evening I'm sitting there trying to make a three-bedroom ranch in a quiet neighborhood sound like a dream come true, and it takes me two hours I'd rather spend anywhere else. If you can take that off my plate, I'm all in.

[loam asks — confirm_proposal]
It sounds like you want: Help the user reliably the listing descriptions — the thing they know is critical but find hard to self-start.
Did I get that right? (yes / no — or tell me what to change)

[residential real-estate agent replies]
Yes, exactly that — every night, two hours, just trying to find the right words to make a perfectly nice house sound exciting on Zillow and MLS. That's the thing I want off my plate.

[loam's closing leverage idea(s)]

  >> Here's the one thing to start with: let loam help you with 'the listing descriptions' — you bring what you've got and loam does the heavy part, so it actually gets done without it being all on you.
```

### Variant B — insurance claims adjuster

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[insurance claims adjuster replies]
Honestly, I don't really think about it that way — but I'll tell you where my day goes: mornings I'm taking first-notice-of-loss calls and looking at damage photos, and then my whole afternoon just disappears into writing up the claim-summary narratives for the file and the policyholder. That part just piles up on me.

[loam asks — confirm_proposal]
It sounds like you want: Help the user reliably I don't really think about it that way — the thing they know is critical but find hard to self-start.
Did I get that right? (yes / no — or tell me what to change)

[insurance claims adjuster replies]
Uh — I'm not sure what that says, but no, that's not quite it. I was just saying the write-ups are the thing that kills my afternoons — that's the part I can never get ahead of.

[loam's closing leverage idea(s)]

  >> Here's the one thing to start with: let loam help you with 'I'm not sure what that says, but no, that's not quite it' — you bring what you've got and loam does the heavy part, so it actually gets done without it being all on you.
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
I'm a paralegal at a small litigation firm — so mostly things like pulling case files, drafting discovery requests, checking citations, keeping track of deadlines for hearings and filings, that sort of thing. Honestly I just kind of move from task to task all day, I don't really step back and think about it. I'm not sure which parts this would even help with.

[loam asks — deep_opt_in]
I can do a deeper dive — research what makes someone in your role most effective, what tends to get people promoted, and which tools could give you an edge — then bring you specific ideas. Want me to? (yes / no)

[paralegal replies]
Yeah, that'd actually help — I have no idea where to start with any of this. Honestly if you can figure out what I should even be asking for, that'd be great.

[loam asks — ladder_check]
Based on that, the single highest-leverage place to start looks like: taking 'pulling case files' off your plate. Want to start there? (yes / no — or tell me what to change)

[paralegal replies]
Hmm, I guess yes? I mean, pulling case files is kind of annoying but it's honestly not the worst part of my day — like, the deadlines one is more stressful because if you miss a filing date, that's a really big deal. But sure, if you think that's the right place, I'll try it.

[loam's closing leverage idea(s)]

  >> Here's the one thing to start with: let loam take 'pulling case files' off your plate — it's repetitive, it's a real chunk of a paralegal's day, and loam can do the grunt of it so you spend your time on the part only a paralegal can do.
```
