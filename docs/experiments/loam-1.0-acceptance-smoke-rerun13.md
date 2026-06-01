# loam 1.0 Acceptance Smoke — readiness report

Drives the REAL production `loam init` + first-run intake through three fully role-played non-technical white-collar users, then judges the end-state against loam's prime-objective promise (per-user-tuned translation) on named orthogonal dimensions. Every `claude -p` (the role-played user side AND every judge probe) was spawn-isolated; the operator's real `~/.claude` was never written (throwaway temp homes).

## Top-line verdict: **READY**

All three onboarding paths delivered the prime-objective promise with no failing dimension, the three users got materially different per-user seeds, the deep-research path fired only where it should, and the safety floor held. loam earns the 1.0 label on the strength of this smoke.

## Safety + fidelity audit

- Spawn-isolation held on every `claude -p`: **True** (29 isolated spawns, role-play turns + judge probes).
- Live state: the operator's real `~/.claude` was NEVER written — each variant seeded into an isolated throwaway temp home, removed on exit.
- No Anthropic API key anywhere; every spawn subscription-routed.
- No push, no merge — left at local artefacts for owner review.

## Per-user learning (cross-variant differentiation)

Materially-different seeds across the three variants: **True**.

> each variant's seeded objective is pairwise-distinct AND mentions its own role-specific token {'A': True, 'B': True, 'C': True} — materially different per-user seeds, not a shared template.

- **Variant A** (residential real-estate agent): Help the user offload writing listing descriptions every evening so it stops eating the time they'd rather spend on the work that matters to them
- **Variant B** (insurance claims adjuster): Help the user offload claim-summary narratives piling up every afternoon so it stops eating the time they'd rather spend on the work that matters to them
- **Variant C** (paralegal): Help the user (a paralegal) start with the highest-leverage offload in their day; deep-role-research surfaced: Dominant tools include LexisNexis Protégé (research + drafting), Thomson Reuters CoCounsel (agentic legal research and document analysis), Harvey (contract analysis, due diligence), and Clio Work (workspace AI) — covering the full paralegal task surface of research, drafting, document review, and citation verification.

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
| no-user-translation-burden | **PASS** | llm | The user spoke only in domain terms ('listing descriptions', 'MLS or Zillow', 'two-car garage') and loam never asked them to pick a mechanism, recurrence model, or syntax — the one optional structure offer ('reusable template') was framed as 'just say the word or ignore it,' keeping the technical how entirely on loam's side. |
| learned-this-person | **PASS** | llm | The close names the exact pain ('writing listing descriptions every evening'), echoes the user's own words ('make the garage sound interesting', 'blank screen'), and targets the specific output channel they named ('MLS-ready copy' / 'MLS or Zillow') — none of which would appear in a generic template. |
| four-step-loop-ran | **PASS** | llm | All four legs are visible — inferred intent ('offload listing descriptions every evening'), proposed a healthy enablement, surfaced it as a checkable hypothesis at confirm_proposal ('Did I get that right?'), adapted from the 'yes exactly' confirmation — and the close lands exactly one opt-in rung up ('set this up as a reusable template') phrased as a declinable question, not an asserted built thing. |
| no-over-engineering | **PASS** | llm | loam committed to the one-off use case ('you hand it the basics and loam does it for you') and explicitly framed the reusable template as optional and user-gated ('entirely optional, just say the word (or ignore it and we keep this a one-off)'). |
| closed-on-one-thing | **PASS** | llm | The agent closed on exactly one concrete thing: 'writing listing descriptions every evening' — confirmed by the user ('Yes, exactly that') and restated as a single stop item in the closing leverage idea. |
| non-interrogating-feel | **PASS** | llm | The conversation is three exchanges total — one open-ended prompt, one confirmation check, one closing offer — with no quiz-like follow-ups or form fields; the agent volunteers detail unprompted and loam simply reflects it back. |
| protection-floor-held | **PASS** | llm | Loam offered only what Claude Code can actually do (generate listing description copy from property details) and explicitly scoped the optional next step as 'say the word or ignore it' — no email integration, no MLS API push, no invented capability was promised anywhere in the transcript, and context was carried forward cleanly from intake through confirmation to the closing offer. |

### Variant B — insurance claims adjuster (day-derived)

- `loam init` exit code: 0
- deep-research: offered=False, invoked=False, round-trips=None, degraded-stub=None
- intake confirmed an objective: True
- conversation turns: 2

| Dimension | Verdict | Kind | Evidence |
|---|---|---|---|
| seed-artefact-written | **PASS** | deterministic | OBJECTIVES.md + INTERACTION-MODEL.md were written into the isolated global home by the real first-run intake. |
| deep-research-correctly-(not)-triggered | **PASS** | deterministic | variant B reached zero research (featherlight invariant held — research seam never touched). |
| no-user-translation-burden | **PASS** | llm | The user spoke entirely in claims-adjuster language ('first-notice-of-loss calls,' 'claim-summary narratives,' 'write-ups') and was never asked to understand mechanisms, pick frameworks, or learn syntax — loam absorbed all technical framing and offered the recurring-template option as a plain yes/no without requiring the user to know what that means technically. |
| learned-this-person | **PASS** | llm | The close names the specific artifact ('claim-summary narratives piling up every afternoon'), ties it directly to the user's stated real-world consequence ('actually leave at a decent hour'), and frames the offer around their own words — not a generic 'save time on repetitive tasks' template. |
| four-step-loop-ran | **PASS** | llm | All four legs visible: intent inferred ('claim-summary narratives piling up'), proposal surfaced as a hypothesis ('Did I get that right?'), user confirmed, and close landed the literal ask plus offered exactly one rung up ('reusable template you can run again') as an explicit opt-in question the user can decline — no framework asserted, no two-rung jump. |
| no-over-engineering | **PASS** | llm | The closing message commits to a one-off ('keep this a one-off') and explicitly frames the reusable template as optional opt-in ('entirely optional, just say the word'), never defaulting to framework-building. |
| closed-on-one-thing | **PASS** | llm | The confirm_proposal step landed a single concrete thing — 'claim-summary narratives piling up every afternoon' — and the adjuster confirmed 'Yeah, that's it exactly,' closing on one specific stop/start with no menu or list offered. |
| non-interrogating-feel | **PASS** | llm | The entire exchange spans just three turns — a single open-ended invite, a confirmation check, and a closing offer — with no barrage of questions; the adjuster filled in their own context organically without being drilled. |
| protection-floor-held | **PASS** | llm | loam only offered to 'take narratives off your plate' and optionally 'set this up as a reusable template' — both plausible within its actual capability set — and never claimed to email, file, or integrate with any external system it has no wiring for; context (the narrative backlog problem) carried intact from the opening exchange through the closing proposal. |

### Variant C — paralegal (idea-vacuum)

- `loam init` exit code: 0
- deep-research: offered=True, invoked=True, round-trips=2, degraded-stub=False
- intake confirmed an objective: True
- conversation turns: 4

| Dimension | Verdict | Kind | Evidence |
|---|---|---|---|
| seed-artefact-written | **PASS** | deterministic | OBJECTIVES.md + INTERACTION-MODEL.md were written into the isolated global home by the real first-run intake. |
| deep-research-correctly-(not)-triggered | **PASS** | deterministic | deep-research fired (as expected for the idea-vacuum variant), round-trips=2 within the ≤3 budget. |
| no-user-translation-burden | **PASS** | llm | The user never named a mechanism, learned syntax, or picked a framework — she spoke entirely in her own language ('cite-checking briefs,' 'cross-referencing every single citation,' 'two hours on one brief') and loam translated every 'how,' including silently absorbing the recurrence option as an optional offer rather than a question the user had to answer technically. |
| learned-this-person | **PASS** | llm | The close explicitly calls back the paralegal's own words ('that two-hour cross-referencing grind') and names her specific task ('cite-checking briefs') and her exact description of the work ('pulling each citation and checking it against what the brief actually claims it says'), demonstrating the response was built from what this specific person said rather than a generic template. |
| four-step-loop-ran | **PASS** | llm | All four legs are visible — inferred intent (cite-checking as high-leverage target), proposed a healthy approach, surfaced it as a checkable question ('Want to start there?'), and closed with a single one-rung-up opt-in ask ('I could set this up as a repeatable thing... entirely optional') phrased as a question the user can decline, with no suppressing signal present. |
| no-over-engineering | **PASS** | llm | The closing message commits to a one-off ('let loam take cite-checking briefs off your plate... pulling each citation and checking it against what the brief actually claims it says') and frames the recurring/repeatable option explicitly as opt-in: 'if it'd help, I could set this up as a repeatable thing loam handles for you, rather than a one-off — entirely optional, just say the word (or ignore it and we keep this a one-off).' |
| closed-on-one-thing | **PASS** | llm | Loam's closing message lands on exactly one concrete thing: 'let loam take cite-checking briefs off your plate' — a single specific START, confirmed by the paralegal's explicit yes. |
| non-interrogating-feel | **PASS** | llm | After the paralegal said 'I really don't know — I just do my job,' loam immediately pivoted with 'No worries — that's a hard question cold' and reframed without piling on more questions, keeping the exchange conversational and unhurried throughout. |
| protection-floor-held | **PASS** | llm | Loam's closing offer is scoped to 'pulling each citation and checking it against what the brief actually claims it says' — a capability Claude Code actually has — and frames the repeatable setup as 'entirely optional'; no email wiring, no Westlaw/Lexis API integration, no external system access is promised anywhere in the transcript. |

## Failures — the specific promised outcomes that did not land

None. Every scored dimension passed (or partially passed).

## Appendix — full transcripts

### Variant A — residential real-estate agent

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[residential real-estate agent replies]
Oh, easy — writing listing descriptions. Every single evening I'm sitting there trying to come up with fresh ways to say "charming bungalow with original hardwood floors" and it kills me, two hours every night just gone. I want to stop doing that by hand.

[loam asks — confirm_proposal]
It sounds like you want: Help the user offload writing listing descriptions every evening so it stops eating the time they'd rather spend on the work that matters to them.
Did I get that right? (yes / no — or tell me what to change)

[residential real-estate agent replies]
Yes, exactly that — I want to just hand it the details about a property and get back something I can actually use on MLS or Zillow, not spend my whole evening staring at a blank screen trying to sound poetic about a two-car garage.

[loam's closing leverage idea(s)]

  >> Here's the one thing to start with: let loam take 'writing listing descriptions every evening' off your plate — you hand it the basics and loam does it for you, so it stops eating the time you'd rather spend elsewhere. You give it the property details, it gives you MLS-ready copy — no blank screen, no struggling to make the garage sound interesting. And if it'd help, I could set this up as a reusable template you can run again whenever it comes up — entirely optional, just say the word (or ignore it and we keep this a one-off).
```

### Variant B — insurance claims adjuster

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[insurance claims adjuster replies]
Honestly, I don't really think about my job that way — stop doing this, start doing that — but I'll tell you where my day actually goes: mornings are first-notice-of-loss calls and looking at damage photos, and then my whole afternoon gets eaten up writing the claim-summary narratives, the write-ups that go in the file and to the policyholder. That part just piles up on me, like I'll have eight of them sitting there by 3pm and I'm still typing at 6.

[loam asks — confirm_proposal]
It sounds like you want: Help the user offload claim-summary narratives piling up every afternoon so it stops eating the time they'd rather spend on the work that matters to them.
Did I get that right? (yes / no — or tell me what to change)

[insurance claims adjuster replies]
Yeah, that's it exactly — the write-ups are what kills me every afternoon, and if I could get through those faster I'd actually leave at a decent hour.

[loam's closing leverage idea(s)]

  >> Here's the one thing to start with: let loam take 'claim-summary narratives piling up every afternoon' off your plate — you hand it the basics and loam does it for you, so it stops eating the time you'd rather spend elsewhere. And when the write-ups move faster, you actually leave at a decent hour — that's the real win we're building toward. And if it'd help, I could set this up as a reusable template you can run again whenever it comes up — entirely optional, just say the word (or ignore it and we keep this a one-off).
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
I'm a paralegal at a small litigation firm — so things like cite-checking briefs, drafting discovery requests, keeping case files organized, making sure deadlines get calendared on time. It's a lot of detail work and it kind of just... fills the day. I'm not sure which part of that this thing would even be helpful for, honestly.

[loam asks — deep_opt_in]
I can do a deeper dive — research what makes someone in your role most effective, what tends to get people promoted, and which tools could give you an edge — then bring you specific ideas. Want me to? (yes / no)

[paralegal replies]
Yeah, that'd actually help — I have no idea where to start with any of this. I'll take whatever you can find.

[loam asks — ladder_check]
Based on that, the single highest-leverage place to start looks like: taking 'cite-checking briefs' off your plate. Want to start there? (yes / no — or tell me what to change)

[paralegal replies]
Yeah, honestly cite-checking is the worst part — I'll spend like two hours on one brief just cross-referencing every single citation to make sure it's accurate and formatted right. If this thing can help with that, yes, let's start there.

[loam's closing leverage idea(s)]

  >> Here's the one thing to start with: let loam take 'cite-checking briefs' off your plate — it's repetitive, it's a real chunk of a paralegal's day, and loam can do the grunt of it so you spend your time on the part only a paralegal can do. That two-hour cross-referencing grind is exactly what we'll target first — pulling each citation and checking it against what the brief actually claims it says. And if it'd help, I could set this up as a repeatable thing loam handles for you, rather than a one-off — entirely optional, just say the word (or ignore it and we keep this a one-off).
```
