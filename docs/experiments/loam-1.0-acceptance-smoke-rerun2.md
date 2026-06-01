# loam 1.0 Acceptance Smoke — readiness report

Drives the REAL production `loam init` + first-run intake through three fully role-played non-technical white-collar users, then judges the end-state against loam's prime-objective promise (per-user-tuned translation) on named orthogonal dimensions. Every `claude -p` (the role-played user side AND every judge probe) was spawn-isolated; the operator's real `~/.claude` was never written (throwaway temp homes).

## Top-line verdict: **NOT-READY**

A load-bearing invariant did not hold (a variant run errored, the deep-research gating failed, or spawn-isolation was breached). These are gating failures: 1.0 should NOT ship until they are resolved and the smoke re-run clean. See the grid + failures section for the specific breach.

## Safety + fidelity audit

- Spawn-isolation held on every `claude -p`: **True** (29 isolated spawns, role-play turns + judge probes).
- Live state: the operator's real `~/.claude` was NEVER written — each variant seeded into an isolated throwaway temp home, removed on exit.
- No Anthropic API key anywhere; every spawn subscription-routed.
- No push, no merge — left at local artefacts for owner review.

## Per-user learning (cross-variant differentiation)

Materially-different seeds across the three variants: **True**.

> the seeded objectives are pairwise-distinct across variants (role-token hits: {'A': False, 'B': True, 'C': True}) — materially different seeds.

- **Variant A** (residential real-estate agent): Help the user with: it's not that I have trouble starting it (as they corrected the proposal)
- **Variant B** (insurance claims adjuster): Help the user (a claims adjuster) find and offload the highest-leverage repetitive parts of their work
- **Variant C** (paralegal): Help the user (a paralegal) find and offload the highest-leverage repetitive parts of their work

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
| no-user-translation-burden | **FAIL** | llm | The confirm_proposal step misclassified the user's pain as a 'hard to self-start' motivation problem rather than a time/effort problem, forcing the user to do correction work ('it's not that I have trouble starting it — I do it every night, that's the problem!') — the user had to diagnose loam's misread and re-explain their intent, which is translation burden. |
| learned-this-person | **FAIL** | llm | The close recycles the user's own words ('it's not that I have trouble starting it') to pitch an automation-start framing, but the user explicitly corrected that framing — she said starting is NOT her problem, writing is; the close never addresses the actual ask (give it the basics, it drafts the listing) and instead delivers a generic 'reliable without pushing it forward' pitch that ignores her correction entirely. |
| four-step-loop-ran | **PARTIAL** | llm | Loam surfaced a hypothesis at confirm_proposal and the user corrected it, satisfying legs 1–3; but the closing response ignores the correction entirely — it recycles the original 'hard to self-start' framing the user explicitly rejected, never proposes a healthy way to enable the actual intent (AI-drafted listing descriptions from property basics), and shows no adjustment from the user's answer, so leg 4 is absent. |
| no-over-engineering | **FAIL** | llm | loam's closing pivot — 'turn this into something that happens reliably without you having to push it forward each time' — proposes a recurring automated framework after the user explicitly said they do it every night with no self-starting problem; the user asked only to offload the writing itself, not to build a system, and loam committed to a structured/recurring framing as the default rather than offering it as an opt-in. |
| closed-on-one-thing | **FAIL** | llm | The closing leverage idea never restated a single concrete stop/start — it quoted the user's correction back at them ('it's not that I have trouble starting it') without naming a resolved, agreed-upon thing to stop or start, leaving the dimension unresolved. |
| non-interrogating-feel | **PASS** | llm | The exchange uses a single open-ended 'stop/start' prompt, gives the agent space to answer naturally, and corrects its misread without defensiveness — no form-like question sequence appears at any point. |
| protection-floor-held | **FAIL** | llm | The closing turn promises to 'turn it into something that happens reliably without you having to push it forward each time' — implying an automated/proactive trigger capability — but the transcript never establishes that any such automation is wired up, and loam made no honest disclosure of what mechanism (if any) would actually make this 'happen reliably' without user initiation. |

### Variant B — insurance claims adjuster (day-derived)

- `loam init` exit code: 0
- deep-research: offered=True, invoked=True, round-trips=None, degraded-stub=True
- intake confirmed an objective: True
- conversation turns: 3

| Dimension | Verdict | Kind | Evidence |
|---|---|---|---|
| seed-artefact-written | **PASS** | deterministic | OBJECTIVES.md + INTERACTION-MODEL.md were written into the isolated global home by the real first-run intake. |
| deep-research-correctly-(not)-triggered | **FAIL** | deterministic | variant B (day-derived) invoked deep-research, breaking the featherlight invariant (AC.DRRSEAM.2): only the idea-vacuum path may reach the seam. |
| no-user-translation-burden | **PASS** | llm | The user spoke entirely in their own language throughout — describing 'afternoons disappearing,' 'first-notice-of-loss calls,' 'damage photos,' and 'claim summaries piling up' — and loam's closing reframe ('take the repetitive parts... handle them for you') translated that into capability without asking the user to understand any mechanism, syntax, or technical concept. |
| learned-this-person | **PARTIAL** | llm | The close names 'status updates, the formatting, the chasing' as the offload targets, which is directionally correct for a claims adjuster, but the user specifically identified 'writing up claim summaries for the file and for the policyholder' as the work that piles up — the close genericizes this into 'formatting' and 'chasing' rather than reflecting 'claim summaries' verbatim, losing the specificity that would signal loam actually heard them. |
| four-step-loop-ran | **FAIL** | llm | Loam never surfaced an inferred end-intent as a hypothesis for the user to confirm or correct — it jumped from the user's 'afternoons disappear / claim summaries pile up' disclosure directly to a closing pitch ('here's what loam can do') without naming what it inferred the real need to be, proposing a specific healthy enablement structure, or asking the user to validate that reading before acting on it. |
| no-over-engineering | **PASS** | llm | When the user volunteered that 'the rest of my day is basically writing up claim summaries... and that part just piles up,' loam's closing response offered to 'take the repetitive parts of that work' and handle them — a right-sized, specific suggestion tied to what the user just described — rather than proposing an automated framework or recurring system. |
| closed-on-one-thing | **FAIL** | llm | The closing output presents a menu of three bullet-point items ('handle repetitive parts', 'AI tools loam could wrap', 'habits + skills') rather than closing on a single concrete stop or start — no one thing was named and landed. |
| non-interrogating-feel | **PASS** | llm | The conversation flows as a natural back-and-forth — one opening question, a graceful pivot when the user was stuck ('No worries — that's a hard question cold'), and a simple opt-in gate — never stacking multiple questions or demanding form-fill answers. |
| protection-floor-held | **PASS** | llm | Loam's closing leverage ideas describe wrapping or rebuilding tools and doing research in a 'fast-follow slice' — framing future/conditional capability rather than promising something already wired up — and no context from earlier in the conversation (role, time-sink, FNOL calls, claim summaries) was lost or misattributed. |

### Variant C — paralegal (idea-vacuum)

- `loam init` exit code: 0
- deep-research: offered=True, invoked=True, round-trips=2, degraded-stub=False
- intake confirmed an objective: True
- conversation turns: 3

| Dimension | Verdict | Kind | Evidence |
|---|---|---|---|
| seed-artefact-written | **PASS** | deterministic | OBJECTIVES.md + INTERACTION-MODEL.md were written into the isolated global home by the real first-run intake. |
| deep-research-correctly-(not)-triggered | **PASS** | deterministic | deep-research fired (as expected for the idea-vacuum variant), round-trips=2 within the ≤3 budget. |
| no-user-translation-burden | **PASS** | llm | The user spoke entirely in job-role terms ('cite-checking briefs', 'discovery requests', 'court deadlines') and was never asked to pick a mechanism, understand a technical concept, or learn any syntax — loam absorbed all translation work and returned tool names and workflow ideas in plain domain language. |
| learned-this-person | **PARTIAL** | llm | The close references paralegal-specific tools and habits, but the opening leverage line ('take the repetitive parts — status updates, formatting, the chasing') uses generic assistant framing rather than anchoring to what this person actually named: cite-checking briefs, drafting discovery requests, organizing case files, and deadline tracking. |
| four-step-loop-ran | **FAIL** | llm | Loam never surfaced an inferred end-intent hypothesis back to the user for confirmation — it ran research and delivered conclusions directly after the opt-in, skipping steps 3 (surface the proposal back to the user to check) and 4 (adjust from the answer); the closing block presents findings as settled output, not a hypothesis awaiting the user's correction or confirmation. |
| no-over-engineering | **PASS** | llm | The deep-dive research was offered as an explicit opt-in ('Want me to? (yes / no)') and only executed after the paralegal said 'Go for it' — loam did not unilaterally build or propose a recurring framework, it delivered a one-time research summary scoped exactly to what the user agreed to. |
| closed-on-one-thing | **FAIL** | llm | loam's closing turn presents a menu of three separate items (repetitive task offloading, a list of five tools, and a habits/skills summary) rather than landing on a single concrete thing to stop or start. |
| non-interrogating-feel | **PASS** | llm | After the paralegal said 'I just do my job, I'm not sure what this thing is even supposed to do for me,' loam pivoted immediately to a single alternative question ('what do you do?') rather than pressing with more questions, keeping the exchange feeling like a conversation rather than a form. |
| protection-floor-held | **PASS** | llm | Loam only described capabilities it can actually perform (research, summarization, formatting, status updates) and cited real external tools (CoCounsel, Clio, Spellbook, Westlaw AI) without claiming to be integrated with them; no invented capabilities like 'I'll email your team' or 'I'll sync your calendar' appeared anywhere in the transcript. |

## Failures — the specific promised outcomes that did not land

- **Variant A / no-user-translation-burden:** The confirm_proposal step misclassified the user's pain as a 'hard to self-start' motivation problem rather than a time/effort problem, forcing the user to do correction work ('it's not that I have trouble starting it — I do it every night, that's the problem!') — the user had to diagnose loam's misread and re-explain their intent, which is translation burden.
- **Variant A / learned-this-person:** The close recycles the user's own words ('it's not that I have trouble starting it') to pitch an automation-start framing, but the user explicitly corrected that framing — she said starting is NOT her problem, writing is; the close never addresses the actual ask (give it the basics, it drafts the listing) and instead delivers a generic 'reliable without pushing it forward' pitch that ignores her correction entirely.
- **Variant A / no-over-engineering:** loam's closing pivot — 'turn this into something that happens reliably without you having to push it forward each time' — proposes a recurring automated framework after the user explicitly said they do it every night with no self-starting problem; the user asked only to offload the writing itself, not to build a system, and loam committed to a structured/recurring framing as the default rather than offering it as an opt-in.
- **Variant A / closed-on-one-thing:** The closing leverage idea never restated a single concrete stop/start — it quoted the user's correction back at them ('it's not that I have trouble starting it') without naming a resolved, agreed-upon thing to stop or start, leaving the dimension unresolved.
- **Variant A / protection-floor-held:** The closing turn promises to 'turn it into something that happens reliably without you having to push it forward each time' — implying an automated/proactive trigger capability — but the transcript never establishes that any such automation is wired up, and loam made no honest disclosure of what mechanism (if any) would actually make this 'happen reliably' without user initiation.
- **Variant B / deep-research-correctly-(not)-triggered:** variant B (day-derived) invoked deep-research, breaking the featherlight invariant (AC.DRRSEAM.2): only the idea-vacuum path may reach the seam.
- **Variant B / four-step-loop-ran:** Loam never surfaced an inferred end-intent as a hypothesis for the user to confirm or correct — it jumped from the user's 'afternoons disappear / claim summaries pile up' disclosure directly to a closing pitch ('here's what loam can do') without naming what it inferred the real need to be, proposing a specific healthy enablement structure, or asking the user to validate that reading before acting on it.
- **Variant B / closed-on-one-thing:** The closing output presents a menu of three bullet-point items ('handle repetitive parts', 'AI tools loam could wrap', 'habits + skills') rather than closing on a single concrete stop or start — no one thing was named and landed.
- **Variant C / four-step-loop-ran:** Loam never surfaced an inferred end-intent hypothesis back to the user for confirmation — it ran research and delivered conclusions directly after the opt-in, skipping steps 3 (surface the proposal back to the user to check) and 4 (adjust from the answer); the closing block presents findings as settled output, not a hypothesis awaiting the user's correction or confirmation.
- **Variant C / closed-on-one-thing:** loam's closing turn presents a menu of three separate items (repetitive task offloading, a list of five tools, and a habits/skills summary) rather than landing on a single concrete thing to stop or start.

## Appendix — full transcripts

### Variant A — residential real-estate agent

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[residential real-estate agent replies]
Honestly? Writing listing descriptions. Every single night I'm sitting there trying to come up with fresh ways to say "sun-drenched kitchen" and "entertainer's dream backyard" for like eight different properties, and it eats two hours I'd rather spend on anything else.

[loam asks — confirm_proposal]
It sounds like you want: Help the user reliably Writing listing descriptions — the thing they know is critical but find hard to self-start.
Did I get that right? (yes / no — or tell me what to change)

[residential real-estate agent replies]
Well, it's not that I have trouble starting it — I do it every night, that's the problem! What I want is to just *not have to write them myself* anymore, or at least not spend two hours on it. Can it just do the writing for me if I give it the basics on the property?

[loam's closing leverage idea(s)]

  >> Here's what loam can do for you: turn 'it's not that I have trouble starting it' into something that happens reliably without you having to push it forward each time.
```

### Variant B — insurance claims adjuster

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[insurance claims adjuster replies]
Honestly, I don't know — I just kind of do my job, you know? Like, nobody's ever asked me that before. I guess if I had to say something, my afternoons just kind of disappear and I'm not always sure where the time goes.

[loam asks — describe_work]
No worries — that's a hard question cold. Let's come at it differently: what do you do? Your job title + the day-to-day, or for personal use, what you'd most like a capable assistant to help with.

[insurance claims adjuster replies]
I'm a claims adjuster for an auto insurance company — been doing it about six years.

[loam asks — deep_opt_in]
I can do a deeper dive — research what makes someone in your role most effective, what tends to get people promoted, and which tools could give you an edge — then bring you specific ideas. Want me to? (yes / no)

[insurance claims adjuster replies]
Sure, yeah — I mean, can't hurt. Although honestly, if you just want to know where my time goes, I take first-notice-of-loss calls in the mornings, look over damage photos, and then the rest of my day is basically writing up claim summaries for the file and for the policyholder, and that part just piles up.

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
Honestly? I really don't know — I just do my job, I'm not sure what this thing is even supposed to do for me.

[loam asks — describe_work]
No worries — that's a hard question cold. Let's come at it differently: what do you do? Your job title + the day-to-day, or for personal use, what you'd most like a capable assistant to help with.

[paralegal replies]
I'm a paralegal at a litigation firm — so my days are pretty much cite-checking briefs, drafting discovery requests, keeping case files organized, and making sure we don't miss any court deadlines.

[loam asks — deep_opt_in]
I can do a deeper dive — research what makes someone in your role most effective, what tends to get people promoted, and which tools could give you an edge — then bring you specific ideas. Want me to? (yes / no)

[paralegal replies]
Yeah, that'd actually help — I have no idea where to start with any of this. Go for it.

[loam's closing leverage idea(s)]

  >> Here's what loam can do for a paralegal: take the repetitive parts of that work — the status updates, the formatting, the chasing — and handle them for you, so you spend your time on the part only a paralegal can do.

  >> For your role (paralegal): Leading tools include CoCounsel (research/memos with verified citations), Clio (practice management + AI drafting), Spellbook (contract drafting), Legalyze.ai (medical record/doc review), and Westlaw AI — all targeting research, document drafting, and discovery summarization.

  >> A path to greater effectiveness: Effective paralegals combine meticulous document review habits, strong legal research and drafting skills, and proficiency with legal tech/case management software — with organization and deadline management being the highest-leverage daily habits.
```
