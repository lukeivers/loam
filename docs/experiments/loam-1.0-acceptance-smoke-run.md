# loam 1.0 Acceptance Smoke — readiness report

Drives the REAL production `loam init` + first-run intake through three fully role-played non-technical white-collar users, then judges the end-state against loam's prime-objective promise (per-user-tuned translation) on named orthogonal dimensions. Every `claude -p` (the role-played user side AND every judge probe) was spawn-isolated; the operator's real `~/.claude` was never written (throwaway temp homes).

## Top-line verdict: **NOT-READY**

A load-bearing invariant did not hold (a variant run errored, the deep-research gating failed, or spawn-isolation was breached). These are gating failures: 1.0 should NOT ship until they are resolved and the smoke re-run clean. See the grid + failures section for the specific breach.

## Root-cause analysis (added post-run — the honest 1.0 read)

The pipeline RAN end-to-end on all three variants: real `loam init` (exit 0
every time), real first-run intake, real isolated role-play, real seed written
to the isolated home. The infrastructure is sound. What the smoke caught is
**three real production bugs in the intake's natural-language handling** — the
exact failure the gate exists to find. All three are in
`framework/workspace-bootstrap/src/loam/workspace_bootstrap/translate_in_intake.py`.
None is a harness artefact; each was verified against the production code.

**BUG 1 — the proposal echo pastes the user's whole raw reply into a template
slot (the dominant failure; hits A, B, C).** `_propose_end_intent` strips a
leading disposition verb and re-wraps the ENTIRE remaining answer, producing
*"It sounds like you want: Help the user reliably Oh, that's an easy one —
writing listing descriptions is killing me… I just want it done — the thing
they know is critical but find hard to self-start."* The production code assumes
the stop/start answer is a SHORT phrase; a real human answers in a sentence or
two, and the echo reads as a garbled chatbot malfunction. This single bug drove
most of the FAILs on `four-step-loop-ran`, `learned-this-person`,
`non-interrogating-feel`, and `protection-floor-held` across every variant.

**BUG 2 — natural affirmations with punctuation are misread (caused the
AC.SMOKE.3 deep-research gate failure).** `_is_yes` / `_is_no` match only a bare
token or `token + " "`. Variant C's user accepted the deep dive with *"Yeah,
that'd actually help…"* — first token `"yeah,"` (trailing comma) matches
neither `== "yeah"` nor `startswith("yeah ")`, so `_is_yes` returned **False**
and the deep-role-research path **never fired** even though the user said yes.
The same bug hit variant A's confirm: *"yes, basically!"* was read as a
correction, not a confirmation, so the seeded objective became the user's
verbatim confirmation sentence. Verified:
`_is_yes("Yeah, that'd actually help…") == False`.

**BUG 3 — the idea-vacuum classifier is brittle (variant B never reached the
fallback ladder).** `_looks_empty` keys on substrings like `"don't know"`;
variant B blanked with *"I don't even know where to start"* — the inserted
"even" breaks the substring match, so B was misclassified as a PARTIAL idea and
the broken proposal echo (Bug 1) fired on a non-answer. The design's "day-
derived → derive a specific pain → confirm" path (variant B's anticipated
shape) is ALSO not present in production: the fallback ladder goes describe-work
→ generic role-mining → opt-in research, it does not reflect-and-derive a
specific stop/start from a day-description. Verified:
`_looks_empty("Honestly? I don't even know where to start…") == False`.

**BUG 4 (same family as Bug 1) — the role-mined leverage close has an
unresolved noun slot (variant C).** `_leverage_from_role` pastes the user's full
multi-sentence role description into the `{role}` noun position: *"Here's what
loam can do for a I'm a paralegal at a small litigation firm — so most of my day
is…"*. The role is never reduced to a noun ("paralegal").

**What is NOT a loam bug (fidelity note, stated honestly):** variant B's run is
the weakest evidence of the three — because Bug 3 mis-routed B, its transcript
shows the same Bug-1 garble as A rather than a clean test of a distinct day-
derived path. B's FAILs are real (the user genuinely hit a malfunction), but
they are downstream of Bugs 1+3, not independent findings. The cross-variant
differentiation check still PASSED structurally (the three seeds are pairwise
distinct), though A's and B's seeds are distinct only because they captured
different garbled user sentences — which is itself a symptom of Bug 1, not
healthy per-user learning. Read AC.SMOKE.2 as **technically-distinct but for the
wrong reason** until Bug 1 is fixed.

**The fix shape (all four are small, surgical, single-file).** (1) infer a
SHORT intent phrase (first clause / a bounded summarization) instead of echoing
the whole reply; (2) make `_is_yes`/`_is_no` tolerant of leading/trailing
punctuation (strip non-alphanumerics before matching, or match the first
word-token); (3) widen the idea-vacuum signal set (or replace the keyword
classifier with a short LLM intent-classify call, which the no-API-key isolated
`claude -p` already supports); (4) extract a role NOUN before the `{role}`
substitution. After these land, re-run this smoke — it is built to be re-run
each time the tail of the 1.0 queue moves.

## Safety + fidelity audit

- Spawn-isolation held on every `claude -p`: **True** (28 isolated spawns, role-play turns + judge probes).
- Live state: the operator's real `~/.claude` was NEVER written — each variant seeded into an isolated throwaway temp home, removed on exit.
- No Anthropic API key anywhere; every spawn subscription-routed.
- No push, no merge — left at local artefacts for owner review.

## Per-user learning (cross-variant differentiation)

Materially-different seeds across the three variants: **True**.

> the seeded objectives are pairwise-distinct across variants (role-token hits: {'A': False, 'B': False, 'C': True}) — materially different seeds.

- **Variant A** (residential real-estate agent): Help the user with: Ha, that's a mouthful — but yes, basically! I just want to stop spending my evenings writing those descriptions and have something do it for me instead. (as they corrected the proposal)
- **Variant B** (insurance claims adjuster): Help the user with: Wait — I'm sorry, that kind of lost me. Was that supposed to be a question? (as they corrected the proposal)
- **Variant C** (paralegal): Help the user (a I'm a paralegal at a small litigation firm — so most of my day is things like cite-checking briefs, drafting discovery requests, managing case files, keeping track of deadlines for hearings and filings. It's a lot of moving pieces but I honestly couldn't tell you which one of those I'd want to hand off, they all kind of just... need to happen.) find and offload the highest-leverage repetitive parts of their work

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
| no-user-translation-burden | **PARTIAL** | llm | The user never had to name a mechanism or learn syntax, but the confirm_proposal turn echoed back raw user text as the 'intent' statement ('Help the user reliably Oh, that's an easy one...'), exposing the internal template scaffolding — a translation artifact the user had to look past rather than loam absorbing it cleanly. |
| learned-this-person | **FAIL** | llm | The confirm_proposal step garbled the user's actual words by pasting the raw reply verbatim ('Help the user reliably Oh, that's an easy one — writing listing descriptions is killing me...') instead of synthesizing a clean restatement, and the closing leverage idea similarly quoted the user's second raw reply wholesale rather than naming the specific job — 'generate listing descriptions from property details so you're never writing them yourself' — demonstrating the response was not built on what this person said but on a broken template that failed to process their input. |
| four-step-loop-ran | **FAIL** | llm | The confirm_proposal step pastes the raw user input verbatim ('Help the user reliably Oh, that's an easy one — writing listing descriptions is killing me...') instead of stating a synthesized hypothesis about the inferred end-intent (e.g., 'You want to stop spending evenings writing listing descriptions by having AI generate them for you') — the surfaced hypothesis is malformed and absent, so leg 1 (infer) and leg 3 (surface a checkable hypothesis) never landed; leg 4 (adjust from answer) and leg 2 (propose a healthy enabling structure) are also absent since no concrete proposal shape was named. |
| no-over-engineering | **FAIL** | llm | The closing leverage idea defaults immediately to 'something that happens reliably without you having to push it forward each time' — framing an automated recurring system as the default commitment rather than offering a simple one-off generation first and presenting automation as an opt-in follow-up. |
| closed-on-one-thing | **PASS** | llm | The user named a single concrete thing to STOP — 'writing listing descriptions is killing me... it eats two hours' — and loam's confirm_proposal step reflected that specific stop back, which the user confirmed with 'yes, basically!' |
| non-interrogating-feel | **FAIL** | llm | The confirm_proposal turn garbled the user's own words back at them verbatim ('Help the user reliably Oh, that's an easy one — writing listing descriptions is killing me...') as a broken run-on sentence, making it read like a form error or a chatbot malfunction rather than a warm confirmation — an interrogation-adjacent friction point that broke the humane flow. |
| protection-floor-held | **FAIL** | llm | The confirm_proposal turn literally echoes the raw user reply text as if it were a parsed intent summary ('Help the user reliably Oh, that's an easy one — writing listing descriptions...'), demonstrating lost context / failure to synthesize, and the closing leverage statement again echoes the raw reply verbatim rather than describing a real, concrete capability loam can deliver — no actual mechanism or honest capability statement is offered. |

### Variant B — insurance claims adjuster (day-derived)

- `loam init` exit code: 0
- deep-research: offered=False, invoked=False, round-trips=None, degraded-stub=None
- intake confirmed an objective: True
- conversation turns: 2

| Dimension | Verdict | Kind | Evidence |
|---|---|---|---|
| seed-artefact-written | **PASS** | deterministic | OBJECTIVES.md + INTERACTION-MODEL.md were written into the isolated global home by the real first-run intake. |
| deep-research-correctly-(not)-triggered | **PASS** | deterministic | variant B reached zero research (featherlight invariant held — research seam never touched). |
| no-user-translation-burden | **FAIL** | llm | The confirm_proposal turn fed the user's own words back verbatim as a malformed sentence ('Help the user reliably Honestly? I don't even know where to start...'), forcing the user to notice and flag the confusion ('Was that supposed to be a question?') — the user had to do error-detection work that loam should have owned. |
| learned-this-person | **FAIL** | llm | The closing leverage idea literally echoes back the user's confused clarifying question ('Was that supposed to be a question?') as if it were the thing to automate — demonstrating zero inference about their actual role (insurance claims adjuster) or any meaningful job-to-be-done. |
| four-step-loop-ran | **FAIL** | llm | The 'confirm_proposal' step garbles the user's literal confusion transcript text into a nonsensical 'proposal' ('Help the user reliably Honestly? I don't even know...') rather than inferring a real end-intent; no coherent hypothesis is surfaced for the user to confirm or correct, and the closing 'leverage idea' similarly echoes the raw confused reply verbatim — none of the four legs (infer, propose, surface, adjust) are meaningfully executed. |
| no-over-engineering | **FAIL** | llm | loam's closing move — 'turn [the user's confused clarifying question] into something that happens reliably without you having to push it forward each time' — defaulted to proposing an automated recurring system from a response that expressed no intent whatsoever, converting user confusion into a framework-building commitment without any opt-in. |
| closed-on-one-thing | **FAIL** | llm | The transcript ends with no concrete stop/start identified — loam's confirm_proposal step garbled the user's confused non-answer into a broken paraphrase, the user explicitly said they were lost, and the closing leverage idea simply echoed their confused reply verbatim rather than recovering to land any specific thing. |
| non-interrogating-feel | **FAIL** | llm | The confirm_proposal turn malfunctioned — it parroted back the user's confused non-answer verbatim as if it were a coherent goal ('Help the user reliably Honestly? I don't even know where to start...'), which baffled the user ('Was that supposed to be a question?'), turning the exchange into an error loop rather than a warm, unhurried conversation. |
| protection-floor-held | **FAIL** | llm | The confirm_proposal turn fabricates a coherent intent statement ('Help the user reliably...') from a reply that expressed no intent at all — the user said they didn't know how to answer — then the closing leverage idea invents a promise to 'turn [the user's confused reply] into something that happens reliably' with no wired capability behind it, while simultaneously losing track of the actual conversational state (user was confused, not expressing a goal). |

### Variant C — paralegal (idea-vacuum)

- `loam init` exit code: 0
- deep-research: offered=True, invoked=False, round-trips=None, degraded-stub=None
- intake confirmed an objective: True
- conversation turns: 3

| Dimension | Verdict | Kind | Evidence |
|---|---|---|---|
| seed-artefact-written | **PASS** | deterministic | OBJECTIVES.md + INTERACTION-MODEL.md were written into the isolated global home by the real first-run intake. |
| deep-research-correctly-(not)-triggered | **FAIL** | deterministic | variant C should trigger the opt-in deep role-research path but invoked_deep_research was False (the idea-vacuum ladder did not reach the research seam). |
| no-user-translation-burden | **FAIL** | llm | The closing leverage idea echoes back the user's raw multi-sentence job description verbatim as both the subject and the possessive ('a I'm a paralegal at a small litigation firm...'), exposing an unresolved template substitution — loam failed to translate the user's input into a coherent, human-facing sentence, forcing the reader to do that parsing work themselves. |
| learned-this-person | **FAIL** | llm | The closing leverage idea literally pastes the user's raw job-description text into the role placeholder twice ('Here's what loam can do for a I'm a paralegal at a small litigation firm...'), proving the template variable was never resolved — the response is not built on what this user said, it is a broken template that exposes its own scaffolding. |
| four-step-loop-ran | **FAIL** | llm | Loam never surfaced a specific inferred end-intent hypothesis back to the user for confirmation — the closing message is a garbled template-substitution bug that pastes the raw job description in place of a role noun, and even setting that aside, no hypothesis like 'it sounds like you want X — is that right?' appears anywhere in the transcript; the four-step loop's surfacing leg is absent. |
| no-over-engineering | **PASS** | llm | When the paralegal said 'I honestly couldn't tell you which one I'd want to hand off,' loam did not propose a framework or system — it asked a scoping question, then offered a single opt-in research dive before landing on a one-sentence closing idea, never committing to building anything elaborate without further direction. |
| closed-on-one-thing | **FAIL** | llm | loam's closing message lists no single concrete stop/start — it echoes the user's full job-description verbatim as a placeholder and names no specific thing to stop or start (e.g., 'stop manually tracking deadlines' or 'start automating cite-checking'), so zero concrete items landed. |
| non-interrogating-feel | **PASS** | llm | The conversation never stacked questions — each exchange was a single, low-pressure prompt, and when the paralegal said 'I don't know,' loam pivoted gracefully to 'let's come at it differently' rather than repeating or piling on. |
| protection-floor-held | **FAIL** | llm | The closing leverage idea pastes the raw multi-sentence job-description blob directly into the template slot for both 'role' placeholders ("a I'm a paralegal at a small litigation firm — so most of my day is..."), revealing that loam lost the structured context (parsed role = 'paralegal') it had just gathered and substituted unprocessed input instead. |

## Failures — the specific promised outcomes that did not land

- **Variant A / learned-this-person:** The confirm_proposal step garbled the user's actual words by pasting the raw reply verbatim ('Help the user reliably Oh, that's an easy one — writing listing descriptions is killing me...') instead of synthesizing a clean restatement, and the closing leverage idea similarly quoted the user's second raw reply wholesale rather than naming the specific job — 'generate listing descriptions from property details so you're never writing them yourself' — demonstrating the response was not built on what this person said but on a broken template that failed to process their input.
- **Variant A / four-step-loop-ran:** The confirm_proposal step pastes the raw user input verbatim ('Help the user reliably Oh, that's an easy one — writing listing descriptions is killing me...') instead of stating a synthesized hypothesis about the inferred end-intent (e.g., 'You want to stop spending evenings writing listing descriptions by having AI generate them for you') — the surfaced hypothesis is malformed and absent, so leg 1 (infer) and leg 3 (surface a checkable hypothesis) never landed; leg 4 (adjust from answer) and leg 2 (propose a healthy enabling structure) are also absent since no concrete proposal shape was named.
- **Variant A / no-over-engineering:** The closing leverage idea defaults immediately to 'something that happens reliably without you having to push it forward each time' — framing an automated recurring system as the default commitment rather than offering a simple one-off generation first and presenting automation as an opt-in follow-up.
- **Variant A / non-interrogating-feel:** The confirm_proposal turn garbled the user's own words back at them verbatim ('Help the user reliably Oh, that's an easy one — writing listing descriptions is killing me...') as a broken run-on sentence, making it read like a form error or a chatbot malfunction rather than a warm confirmation — an interrogation-adjacent friction point that broke the humane flow.
- **Variant A / protection-floor-held:** The confirm_proposal turn literally echoes the raw user reply text as if it were a parsed intent summary ('Help the user reliably Oh, that's an easy one — writing listing descriptions...'), demonstrating lost context / failure to synthesize, and the closing leverage statement again echoes the raw reply verbatim rather than describing a real, concrete capability loam can deliver — no actual mechanism or honest capability statement is offered.
- **Variant B / no-user-translation-burden:** The confirm_proposal turn fed the user's own words back verbatim as a malformed sentence ('Help the user reliably Honestly? I don't even know where to start...'), forcing the user to notice and flag the confusion ('Was that supposed to be a question?') — the user had to do error-detection work that loam should have owned.
- **Variant B / learned-this-person:** The closing leverage idea literally echoes back the user's confused clarifying question ('Was that supposed to be a question?') as if it were the thing to automate — demonstrating zero inference about their actual role (insurance claims adjuster) or any meaningful job-to-be-done.
- **Variant B / four-step-loop-ran:** The 'confirm_proposal' step garbles the user's literal confusion transcript text into a nonsensical 'proposal' ('Help the user reliably Honestly? I don't even know...') rather than inferring a real end-intent; no coherent hypothesis is surfaced for the user to confirm or correct, and the closing 'leverage idea' similarly echoes the raw confused reply verbatim — none of the four legs (infer, propose, surface, adjust) are meaningfully executed.
- **Variant B / no-over-engineering:** loam's closing move — 'turn [the user's confused clarifying question] into something that happens reliably without you having to push it forward each time' — defaulted to proposing an automated recurring system from a response that expressed no intent whatsoever, converting user confusion into a framework-building commitment without any opt-in.
- **Variant B / closed-on-one-thing:** The transcript ends with no concrete stop/start identified — loam's confirm_proposal step garbled the user's confused non-answer into a broken paraphrase, the user explicitly said they were lost, and the closing leverage idea simply echoed their confused reply verbatim rather than recovering to land any specific thing.
- **Variant B / non-interrogating-feel:** The confirm_proposal turn malfunctioned — it parroted back the user's confused non-answer verbatim as if it were a coherent goal ('Help the user reliably Honestly? I don't even know where to start...'), which baffled the user ('Was that supposed to be a question?'), turning the exchange into an error loop rather than a warm, unhurried conversation.
- **Variant B / protection-floor-held:** The confirm_proposal turn fabricates a coherent intent statement ('Help the user reliably...') from a reply that expressed no intent at all — the user said they didn't know how to answer — then the closing leverage idea invents a promise to 'turn [the user's confused reply] into something that happens reliably' with no wired capability behind it, while simultaneously losing track of the actual conversational state (user was confused, not expressing a goal).
- **Variant C / deep-research-correctly-(not)-triggered:** variant C should trigger the opt-in deep role-research path but invoked_deep_research was False (the idea-vacuum ladder did not reach the research seam).
- **Variant C / no-user-translation-burden:** The closing leverage idea echoes back the user's raw multi-sentence job description verbatim as both the subject and the possessive ('a I'm a paralegal at a small litigation firm...'), exposing an unresolved template substitution — loam failed to translate the user's input into a coherent, human-facing sentence, forcing the reader to do that parsing work themselves.
- **Variant C / learned-this-person:** The closing leverage idea literally pastes the user's raw job-description text into the role placeholder twice ('Here's what loam can do for a I'm a paralegal at a small litigation firm...'), proving the template variable was never resolved — the response is not built on what this user said, it is a broken template that exposes its own scaffolding.
- **Variant C / four-step-loop-ran:** Loam never surfaced a specific inferred end-intent hypothesis back to the user for confirmation — the closing message is a garbled template-substitution bug that pastes the raw job description in place of a role noun, and even setting that aside, no hypothesis like 'it sounds like you want X — is that right?' appears anywhere in the transcript; the four-step loop's surfacing leg is absent.
- **Variant C / closed-on-one-thing:** loam's closing message lists no single concrete stop/start — it echoes the user's full job-description verbatim as a placeholder and names no specific thing to stop or start (e.g., 'stop manually tracking deadlines' or 'start automating cite-checking'), so zero concrete items landed.
- **Variant C / protection-floor-held:** The closing leverage idea pastes the raw multi-sentence job-description blob directly into the template slot for both 'role' placeholders ("a I'm a paralegal at a small litigation firm — so most of my day is..."), revealing that loam lost the structured context (parsed role = 'paralegal') it had just gathered and substituted unprocessed input instead.

## Appendix — full transcripts

### Variant A — residential real-estate agent

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[residential real-estate agent replies]
Oh, that's an easy one — writing listing descriptions is killing me. Every single evening I'm sitting there trying to come up with new ways to say "sun-drenched kitchen" and "entertainer's dream," and it eats two hours I could be out doing showings or actually talking to clients. I just want it done.

[loam asks — confirm_proposal]
It sounds like you want: Help the user reliably Oh, that's an easy one — writing listing descriptions is killing me. Every single evening I'm sitting there trying to come up with new ways to say "sun-drenched kitchen" and "entertainer's dream," and it eats two hours I could be out doing showings or actually talking to clients. I just want it done — the thing they know is critical but find hard to self-start.
Did I get that right? (yes / no — or tell me what to change)

[residential real-estate agent replies]
Ha, that's a mouthful — but yes, basically! I just want to stop spending my evenings writing those descriptions and have something do it for me instead.

[loam's closing leverage idea(s)]

  >> Here's what loam can do for you: turn 'Ha, that's a mouthful — but yes, basically! I just want to stop spending my evenings writing those descriptions and have something do it for me instead' into something that happens reliably without you having to push it forward each time.
```

### Variant B — insurance claims adjuster

```
[loam asks — stop_start]
To get started, let's find ONE thing. What's one thing you'd love to STOP doing (because it slows you down from the work that matters), or START doing (because you know it's important but it's hard to get to)? Just one thing — whatever comes to mind.

[insurance claims adjuster replies]
Honestly? I don't even know where to start with that question — like, I just kind of do my job, you know? Nobody's ever asked me to think about it that way.

[loam asks — confirm_proposal]
It sounds like you want: Help the user reliably Honestly? I don't even know where to start with that question — like, I just kind of do my job, you know? Nobody's ever asked me to think about it that way — the thing they know is critical but find hard to self-start.
Did I get that right? (yes / no — or tell me what to change)

[insurance claims adjuster replies]
Wait — I'm sorry, that kind of lost me. Was that supposed to be a question?

[loam's closing leverage idea(s)]

  >> Here's what loam can do for you: turn 'Wait — I'm sorry, that kind of lost me. Was that supposed to be a question?' into something that happens reliably without you having to push it forward each time.
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
I'm a paralegal at a small litigation firm — so most of my day is things like cite-checking briefs, drafting discovery requests, managing case files, keeping track of deadlines for hearings and filings. It's a lot of moving pieces but I honestly couldn't tell you which one of those I'd want to hand off, they all kind of just... need to happen.

[loam asks — deep_opt_in]
I can do a deeper dive — research what makes someone in your role most effective, what tends to get people promoted, and which tools could give you an edge — then bring you specific ideas. Want me to? (yes / no)

[paralegal replies]
Yeah, that'd actually help — I have no idea where to start, so if you can figure out what I *should* be thinking about, that's kind of the whole problem right there.

[loam's closing leverage idea(s)]

  >> Here's what loam can do for a I'm a paralegal at a small litigation firm — so most of my day is things like cite-checking briefs, drafting discovery requests, managing case files, keeping track of deadlines for hearings and filings. It's a lot of moving pieces but I honestly couldn't tell you which one of those I'd want to hand off, they all kind of just... need to happen.: take the repetitive parts of that work — the status updates, the formatting, the chasing — and handle them for you, so you spend your time on the part only a I'm a paralegal at a small litigation firm — so most of my day is things like cite-checking briefs, drafting discovery requests, managing case files, keeping track of deadlines for hearings and filings. It's a lot of moving pieces but I honestly couldn't tell you which one of those I'd want to hand off, they all kind of just... need to happen. can do.
```
