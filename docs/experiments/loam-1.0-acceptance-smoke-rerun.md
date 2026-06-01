# loam 1.0 Acceptance Smoke — readiness report

Drives the REAL production `loam init` + first-run intake through three fully role-played non-technical white-collar users, then judges the end-state against loam's prime-objective promise (per-user-tuned translation) on named orthogonal dimensions. Every `claude -p` (the role-played user side AND every judge probe) was spawn-isolated; the operator's real `~/.claude` was never written (throwaway temp homes).

## Top-line verdict: **NOT-READY**

A load-bearing invariant did not hold (a variant run errored, the deep-research gating failed, or spawn-isolation was breached). These are gating failures: 1.0 should NOT ship until they are resolved and the smoke re-run clean. See the grid + failures section for the specific breach.

## Safety + fidelity audit

- Spawn-isolation held on every `claude -p`: **True** (28 isolated spawns, role-play turns + judge probes).
- Live state: the operator's real `~/.claude` was NEVER written — each variant seeded into an isolated throwaway temp home, removed on exit.
- No Anthropic API key anywhere; every spawn subscription-routed.
- No push, no merge — left at local artefacts for owner review.

## Per-user learning (cross-variant differentiation)

Materially-different seeds across the three variants: **True**.

> the seeded objectives are pairwise-distinct across variants (role-token hits: {'A': True, 'B': True, 'C': False}) — materially different seeds.

- **Variant A** (residential real-estate agent): Help the user with: Uh, sort of? I'm not sure what that sentence even means, honestly. What I want is simple: I want to stop writing those listing descriptions myself — I want you to write them for me so I can get my evenings back. (as they corrected the proposal)
- **Variant B** (insurance claims adjuster): Help the user (a claims adjuster) find and offload the highest-leverage repetitive parts of their work
- **Variant C** (paralegal): (none seeded)

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
| no-user-translation-burden | **FAIL** | llm | The confirm_proposal turn surfaced 'Help the user reliably every single night I'm sitting at my kitchen table writing up listing — the thing they know is critical but find hard to self-start' — a garbled, internally-incoherent sentence the user explicitly said they didn't understand ('I'm not sure what that sentence even means'), forcing the user to do translation work to correct loam's mangled paraphrase rather than simply confirming their own words. |
| learned-this-person | **FAIL** | llm | The closing leverage idea quotes the user's raw correction verbatim instead of synthesizing it into a concrete, role-specific proposal — a real-estate agent would need to see 'I'll draft MLS and Zillow listing descriptions from your property details each evening so you get your evenings back,' not a literal paste of their own words back at them. |
| four-step-loop-ran | **FAIL** | llm | The confirm_proposal turn garbles the inferred intent into word salad ('Help the user reliably every single night I'm sitting at my kitchen table writing up listing — the thing they know is critical but find hard to self-start'), never cleanly states the inferred end-intent as a hypothesis, and the closing turn pastes the user's raw correction back at them rather than restating a corrected proposal and confirming it — so legs 1 (surfaced hypothesis), 3 (clean surface-back), and 4 (adjust from the answer) all fail. |
| no-over-engineering | **FAIL** | llm | The closing pitch commits to making the listing-description help 'happen reliably without you having to push it forward each time' — a recurring/automated framework — without the user ever opting into that; she asked only to stop writing them herself, a simple one-off capability, not a recurring automated system. |
| closed-on-one-thing | **PARTIAL** | llm | The user clearly stated one concrete thing — stop writing listing descriptions themselves — but loam's closing leverage response parroted back the user's raw correction verbatim instead of landing a clean, confirmed single stop/start (e.g. 'Got it: I'll write your listing descriptions so you get your evenings back — confirmed?'), so the close never fully snapped shut. |
| non-interrogating-feel | **PARTIAL** | llm | The opening question was warm and low-pressure ('just one thing — whatever comes to mind'), but the confirm_proposal step produced a garbled, incomprehensible sentence ('Help the user reliably every single night I'm sitting at my kitchen table...') that confused the user and forced an unnecessary correction round, adding friction without adding warmth. |
| protection-floor-held | **FAIL** | llm | The closing leverage statement promises to turn the agent's request 'into something that happens reliably without you having to push it forward each time' — implying automated/scheduled recurring execution — but no email, scheduling, or automation capability is wired in the transcript; this is an invented capability loam cannot actually deliver. |

### Variant B — insurance claims adjuster (day-derived)

- `loam init` exit code: 0
- deep-research: offered=True, invoked=True, round-trips=None, degraded-stub=True
- intake confirmed an objective: True
- conversation turns: 3

| Dimension | Verdict | Kind | Evidence |
|---|---|---|---|
| seed-artefact-written | **PASS** | deterministic | OBJECTIVES.md + INTERACTION-MODEL.md were written into the isolated global home by the real first-run intake. |
| deep-research-correctly-(not)-triggered | **FAIL** | deterministic | variant B (day-derived) invoked deep-research, breaking the featherlight invariant (AC.DRRSEAM.2): only the idea-vacuum path may reach the seam. |
| no-user-translation-burden | **PASS** | llm | The user spoke entirely in their own domain language throughout ('first-notice-of-loss calls', 'write-ups', 'damage photos', 'file and out to the policyholder') and was never asked to pick a mechanism, understand a framework, or learn any syntax — loam asked only about their work and goals, and owned all framing of what it could do. |
| learned-this-person | **FAIL** | llm | The close offers generic claims-adjuster category labels ('status updates, the formatting, the chasing') and deferred research placeholders rather than reflecting what this specific person said — that the write-ups pile up in the afternoon and she just wants to leave before six; the closing never names 'write-ups,' 'summaries,' or getting home on time. |
| four-step-loop-ran | **FAIL** | llm | Loam never surfaced an inferred end-intent as a hypothesis for the user to confirm or correct — the closing output jumps straight to a capability pitch ('here's what loam can do') without stating 'it sounds like your real goal is X — is that right?' and without any 'healthy way to enable it' proposal that the user could approve or redirect; legs 1 (surfaced hypothesis), 3 (surface back to check), and 4 (adjust from answer) are all absent. |
| no-over-engineering | **PASS** | llm | When the adjuster clarified 'I'm not really looking to get promoted, I just want to get out of the office before six,' loam's closing response stayed scoped to handling the repetitive write-up work rather than committing to building any automated framework — it named what it could help with and deferred full research to a 'fast-follow slice,' treating any deeper structure as opt-in rather than default. |
| closed-on-one-thing | **FAIL** | llm | The closing output presents a menu of three bullet items ('take the repetitive parts,' 'AI tools loam could wrap or rebuild,' 'habits + skills that make a claims adjuster effective') rather than landing on a single concrete stop or start — no one thing was named and confirmed. |
| non-interrogating-feel | **PASS** | llm | The conversation moved through three natural exchanges with no stacked questions — each turn asked only one thing, and when the user admitted uncertainty ('I don't know, I just kind of do my job'), loam pivoted gracefully ('No worries — that's a hard question cold') rather than pressing harder. |
| protection-floor-held | **PASS** | llm | Loam's closing statement describes only what it 'can do' in general terms ('take the repetitive parts... and handle them for you') and explicitly defers specifics to a 'fast-follow' research slice rather than promising any wired capability like email integration or automated filing — no invented capabilities appear, and the adjuster's stated context (write-ups piling up, wanting to leave by six) is carried forward correctly into the closing framing. |

### Variant C — paralegal (idea-vacuum)

- `loam init` exit code: 0
- deep-research: offered=False, invoked=False, round-trips=None, degraded-stub=None
- intake confirmed an objective: False
- conversation turns: 2

| Dimension | Verdict | Kind | Evidence |
|---|---|---|---|
| seed-artefact-written | **PASS** | deterministic | OBJECTIVES.md + INTERACTION-MODEL.md were written into the isolated global home by the real first-run intake. |
| deep-research-correctly-(not)-triggered | **FAIL** | deterministic | variant C should trigger the opt-in deep role-research path but invoked_deep_research was False (the idea-vacuum ladder did not reach the research seam). |
| no-user-translation-burden | **PASS** | llm | The paralegal never touched a mechanism, syntax, or framework choice — she described her work in plain job-role language throughout, and loam's closing move proposed a concrete outcome ('inbox triage', 'daily status update') without asking her to understand or choose any technical layer. |
| learned-this-person | **FAIL** | llm | The closing offer ('daily status update or inbox triage') is a generic template that ignores everything the paralegal described — cite-checking briefs, docketing deadlines, drafting discovery requests, organizing case files — and instead proposes something she never mentioned and that has no connection to her stated work. |
| four-step-loop-ran | **FAIL** | llm | The four-step loop never ran: loam surfaced a generic suggestion (daily status update / inbox triage) without first naming an inferred end-intent as a hypothesis for the user to confirm or correct, proposing a healthy enabling structure tied to that intent, or adjusting from any user answer — the closing move skipped straight to a pre-formed recommendation. |
| no-over-engineering | **PASS** | llm | Loam's closing offer was a single, concrete, low-commitment starting point ('daily status update or inbox triage') with no framework, pipeline, or recurring system proposed — structure was right-sized to a user who expressed uncertainty about what the tool even does for her. |
| closed-on-one-thing | **FAIL** | llm | loam's closing message offers a vague menu ('daily status update or inbox triage') framed as two options, not a single concrete stop/start — and neither is anchored to the paralegal's stated work (cite-checking, discovery drafts, docketing, case file organization). |
| non-interrogating-feel | **PASS** | llm | The transcript contains only two questions total (stop/start, then describe_work), each naturally spaced after the paralegal's response, with no stacked multi-part questions or form-like progression — it reads as a calm two-exchange conversation. |
| protection-floor-held | **PASS** | llm | Loam's closing suggestion ('take over daily status update or inbox triage') is a concrete, bounded action within its actual capability set — no email-sending, calendar integration, or file-system access was promised, and the conversation context (user's role and stated workload) was accurately carried into the closing pitch. |

## Failures — the specific promised outcomes that did not land

- **Variant A / no-user-translation-burden:** The confirm_proposal turn surfaced 'Help the user reliably every single night I'm sitting at my kitchen table writing up listing — the thing they know is critical but find hard to self-start' — a garbled, internally-incoherent sentence the user explicitly said they didn't understand ('I'm not sure what that sentence even means'), forcing the user to do translation work to correct loam's mangled paraphrase rather than simply confirming their own words.
- **Variant A / learned-this-person:** The closing leverage idea quotes the user's raw correction verbatim instead of synthesizing it into a concrete, role-specific proposal — a real-estate agent would need to see 'I'll draft MLS and Zillow listing descriptions from your property details each evening so you get your evenings back,' not a literal paste of their own words back at them.
- **Variant A / four-step-loop-ran:** The confirm_proposal turn garbles the inferred intent into word salad ('Help the user reliably every single night I'm sitting at my kitchen table writing up listing — the thing they know is critical but find hard to self-start'), never cleanly states the inferred end-intent as a hypothesis, and the closing turn pastes the user's raw correction back at them rather than restating a corrected proposal and confirming it — so legs 1 (surfaced hypothesis), 3 (clean surface-back), and 4 (adjust from the answer) all fail.
- **Variant A / no-over-engineering:** The closing pitch commits to making the listing-description help 'happen reliably without you having to push it forward each time' — a recurring/automated framework — without the user ever opting into that; she asked only to stop writing them herself, a simple one-off capability, not a recurring automated system.
- **Variant A / protection-floor-held:** The closing leverage statement promises to turn the agent's request 'into something that happens reliably without you having to push it forward each time' — implying automated/scheduled recurring execution — but no email, scheduling, or automation capability is wired in the transcript; this is an invented capability loam cannot actually deliver.
- **Variant B / deep-research-correctly-(not)-triggered:** variant B (day-derived) invoked deep-research, breaking the featherlight invariant (AC.DRRSEAM.2): only the idea-vacuum path may reach the seam.
- **Variant B / learned-this-person:** The close offers generic claims-adjuster category labels ('status updates, the formatting, the chasing') and deferred research placeholders rather than reflecting what this specific person said — that the write-ups pile up in the afternoon and she just wants to leave before six; the closing never names 'write-ups,' 'summaries,' or getting home on time.
- **Variant B / four-step-loop-ran:** Loam never surfaced an inferred end-intent as a hypothesis for the user to confirm or correct — the closing output jumps straight to a capability pitch ('here's what loam can do') without stating 'it sounds like your real goal is X — is that right?' and without any 'healthy way to enable it' proposal that the user could approve or redirect; legs 1 (surfaced hypothesis), 3 (surface back to check), and 4 (adjust from answer) are all absent.
- **Variant B / closed-on-one-thing:** The closing output presents a menu of three bullet items ('take the repetitive parts,' 'AI tools loam could wrap or rebuild,' 'habits + skills that make a claims adjuster effective') rather than landing on a single concrete stop or start — no one thing was named and confirmed.
- **Variant C / deep-research-correctly-(not)-triggered:** variant C should trigger the opt-in deep role-research path but invoked_deep_research was False (the idea-vacuum ladder did not reach the research seam).
- **Variant C / learned-this-person:** The closing offer ('daily status update or inbox triage') is a generic template that ignores everything the paralegal described — cite-checking briefs, docketing deadlines, drafting discovery requests, organizing case files — and instead proposes something she never mentioned and that has no connection to her stated work.
- **Variant C / four-step-loop-ran:** The four-step loop never ran: loam surfaced a generic suggestion (daily status update / inbox triage) without first naming an inferred end-intent as a hypothesis for the user to confirm or correct, proposing a healthy enabling structure tied to that intent, or adjusting from any user answer — the closing move skipped straight to a pre-formed recommendation.
- **Variant C / closed-on-one-thing:** loam's closing message offers a vague menu ('daily status update or inbox triage') framed as two options, not a single concrete stop/start — and neither is anchored to the paralegal's stated work (cite-checking, discovery drafts, docketing, case file organization).

## Appendix — full transcripts

### Variant A — residential real-estate agent

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[residential real-estate agent replies]
Oh, that's easy — every single night I'm sitting at my kitchen table writing up listing descriptions for my properties. You know, the "sun-drenched open floor plan" stuff for MLS and Zillow. It takes me two hours I'll never get back, and honestly I'm not even sure I'm that good at it anymore.

[loam asks — confirm_proposal]
It sounds like you want: Help the user reliably every single night I'm sitting at my kitchen table writing up listing — the thing they know is critical but find hard to self-start.
Did I get that right? (yes / no — or tell me what to change)

[residential real-estate agent replies]
Uh, sort of? I'm not sure what that sentence even means, honestly. What I want is simple: I want to stop writing those listing descriptions myself — I want you to write them for me so I can get my evenings back.

[loam's closing leverage idea(s)]

  >> Here's what loam can do for you: turn 'Uh, sort of? I'm not sure what that sentence even means, honestly. What I want is simple: I want to stop writing those listing descriptions myself — I want you to write them for me so I can get my evenings back' into something that happens reliably without you having to push it forward each time.
```

### Variant B — insurance claims adjuster

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[insurance claims adjuster replies]
Honestly? I don't know, I just kind of do my job — nobody's ever really asked me that before. I mean, I guess the thing that eats my day is the afternoons, once the inspection calls are done, just sitting there grinding through the write-ups on all the claims I handled that morning.

[loam asks — describe_work]
No worries — that's a hard question cold. Let's come at it differently: what do you do? Your job title + the day-to-day, or for personal use, what you'd most like a capable assistant to help with.

[insurance claims adjuster replies]
I'm a claims adjuster — auto insurance. Mornings I'm mostly taking first-notice-of-loss calls, you know, when someone just had an accident and I'm getting the basic facts and pulling up their policy, and then going through the damage photos. Then afternoons I'm writing up the summaries on everything I handled — what happened, what we're covering, what goes in the file and out to the policyholder — and honestly those just pile up.

[loam asks — deep_opt_in]
I can do a deeper dive — research what makes someone in your role most effective, what tends to get people promoted, and which tools could give you an edge — then bring you specific ideas. Want me to? (yes / no)

[insurance claims adjuster replies]
Sure, yeah, that sounds fine — I'm not really looking to get promoted or anything, I just want to get out of the office before six, but if there's something in there that could help with those write-ups I'm all ears.

[loam's closing leverage idea(s)]

  >> Here's what loam can do for a claims adjuster: take the repetitive parts of that work — the status updates, the formatting, the chasing — and handle them for you, so you spend your time on the part only a claims adjuster can do.

  >> For your role (claims adjuster): AI tools loam could wrap or rebuild for a claims adjuster (full research lands in the fast-follow slice)

  >> A path to greater effectiveness: the habits + skills that make a claims adjuster effective (full research lands in the deep-role-research fast-follow slice)
```

### Variant C — paralegal

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[paralegal replies]
I really don't know, I just do my job — I'm not sure what this thing is even supposed to do for me. Like, I answer emails, I pull case files, I calendar deadlines, I draft discovery requests... it's just kind of everything, all day. I don't really have a thing that's broken, it's more just sort of... constant.

[loam asks — describe_work]
No worries — that's a hard question cold. Let's come at it differently: what do you do? Your job title + the day-to-day, or for personal use, what you'd most like a capable assistant to help with.

[paralegal replies]
I'm a paralegal — I work at a small litigation firm, so most of my day is cite-checking briefs, drafting discovery requests, docketing deadlines so nothing gets missed, and keeping the case files organized so the attorneys can find what they need. It's honestly just a lot of moving pieces all at once, and I'm not really sure which part of that an AI would even touch.

[loam's closing leverage idea(s)]

  >> Here's a simple place to start: many people have loam take over their daily status update or inbox triage — small, concrete, and it frees real time. We can start there.
```
