# Adversarial Critique — `keep-pace-with-user.md`

**Date:** 2026-05-28
**Reviewer role:** skeptic / red-team
**Verdict (headline):** Fundamentally sound *direction*, but the doc overstates loam's
existing infrastructure (the "rides hooks loam already runs" claim is largely false on the
verified machine state), under-specifies the one mechanism that actually fixes tonight's
failure, and is roughly 2× larger than the minimal version that delivers the outcome.
Needs **sound-with-fixes**, not rework — the spine survives, four load-bearing claims need
correction, and the build should ship a much smaller MVP first.

The critique is organized by the five prompts I was asked to test against.

---

## 0. The thing the doc gets RIGHT (so the fixes aren't misread as rejection)

- The "one loop, four views" synthesis is the correct framing. Surfacing / cross-session /
  objectives / voice genuinely do share the per-prompt hook + the bounded hot index. That
  is a real insight, not packaging.
- BM25/FTS5-over-embeddings is the right substrate call for this corpus + the no-API-key
  constraint. The research backs it (`keep-pace-research-surfacing.md` §8, claude-mem
  existence proof at $0). I tried to break this and couldn't.
- The append-only partition-per-writer journal is the right concurrency model and is
  correctly identified as the part no off-the-shelf product solves.
- "Self-correction fails for register → the voice check must be independent of the
  generating context" is the correct, non-obvious conclusion and it kills the lazy
  "have it check itself" design. Good.
- Surfacing technical pointers into the persona's context, then forcing translation on
  the way out, is the right inbound/outbound split.

None of that is in dispute. Everything below is where the doc is wrong, soft, or too big.

---

## 1. Would it ACTUALLY have prevented tonight's failure? (PARTIAL — the weakest real gap)

**Tonight's failure (verbatim intent):** the assistant forgot / failed-to-surface relevant
on-file things *while actively working on a related topic.*

**Walk the concrete scenario the design implies it fixes.** Say the persona is editing
Chapter 2 of the litrpg pipeline (Task #7, in-flight tonight), and there's an on-file canon
rule — e.g. the message-delivery "semantic vs identical-text" ruling (Task #2, sealed
earlier). The persona writes a line that violates it and never surfaces the rule.

KP1 fires on `UserPromptSubmit`. It BM25-scores **the user's prompt** against the corpus.
Here is the break: **the violation does not happen in the user's prompt — it happens in the
persona's own generated draft, mid-turn, many tokens after the hook already ran.** The
prompt might be "keep going on the batch" or "do chapter 2's close-read." Those terms do not
lexically hit "message-delivery semantic ruling." So:

1. **KP1's trigger is the wrong event for the named failure.** `UserPromptSubmit` fires
   once, before generation, keyed to what the *user* typed. Tonight's failure is the model
   drifting from on-file context *during its own multi-step work*, where the user's prompt is
   a vague "continue." BM25 on a vague continuation prompt surfaces nothing — and KP2's
   miss-gate would *also* stay silent, because a vague prompt isn't a low-score anomaly, it's
   just low-information. The gate detects "this request misses the loaded set," not "the
   model is about to contradict a memory it isn't thinking about."

2. **The doc asserts the fix in §2.1 ("when the prompt mentions topic X, the hook matches
   the on-file memory about X") but the failure mode is precisely the case where the prompt
   does NOT mention X — the model is deep in X's territory by inference, not by lexical
   mention.** That is the gap between "retrieval keyed to the prompt" and "retrieval keyed
   to what the work is actually about." The doc never names this gap; it is the single most
   important hole, because it is the literal reported failure.

**Fix (name the alternative):**
- **(a) Add a topic/work-anchor to the retrieval key, not just the raw prompt.** The hook
  should score against `prompt + active-objective text + active-subgoal + the last
  turn's topic` — so "continue the batch" inherits "litrpg Ch2 canon" as retrieval terms
  and the canon rule surfaces. This is cheap (concatenate before BM25) and it is the actual
  fix. The doc's own §3.3 hotness score has `active_objective_match`; that same signal
  belongs in the *retrieval key*, not only the rotation score. The doc separates them; they
  should be unified on the read path.
- **(b) Accept that no `UserPromptSubmit` hook can catch a mid-draft contradiction, and put
  the canon-class catch where it belongs — the draft-to-send / PreToolUse gate (Layer 1/2),
  which the doc already builds for *voice*.** Extend that gate to also check the draft
  against active high-salience constraint-memories (canon rules, sealed rulings). The
  infrastructure is identical; the doc just doesn't connect the voice gate to the
  recall failure. This is the only place in the loop that sees the generated text.
- **(c) Be honest in the doc that KP1+KP2 raise the *probability* the right memory is in
  context; they do not *guarantee* the model attends to it.** Injecting a pointer ≠ the
  model using it (lost-in-the-middle applies to the injected pointer too). The doc claims
  KP1+KP2 "fixes the named failure directly" (§7.1). That is over-claimed. It improves it
  substantially; it does not close it. F2: name the residual.

**Severity: HIGH.** This is the flagship requirement and the doc's central claim about it
is over-stated. The fix is small (retrieval-key change + extend the draft gate) but it must
be made or the build will ship something that demonstrably still drifts mid-batch.

---

## 2. Is every piece buildable on loam's REAL setup? (NO — four false-infrastructure claims)

The doc repeatedly says the design "rides loam's existing hook chain" and names specific
live hooks. I verified against the machine. **Several of these claims are false as written**,
which inflates the confidence ratings and shrinks the apparent effort.

**Verified facts (Tier-0, this machine, 2026-05-28):**

1. **`/Users/lukeivers/.claude/settings.json` has `"hooks": {}` — EMPTY.** There is no
   wired `UserPromptSubmit`, `Stop`, `PreToolUse`, or `SessionStart` hook in the active
   global settings. The doc's §6 header claim — *"verified: loam already runs ≥5
   `UserPromptSubmit` hooks incl. `queue_status_inject.py`"* — does not match the active
   config. **`queue_status_inject.py` does not exist anywhere in the tree** (searched whole
   repo + `~/.claude`; zero hits outside the doc itself). The "proven `queue_status_inject.py`
   re-reads `workstream-queue.yaml` every turn — same channel" claim (§3.1, repeated §4.5) is
   citing a file that isn't there. Either it was renamed/removed, or it never landed. **The
   "same proven channel" existence-proof for cross-session re-read is unsubstantiated.**

2. **`translation_jargon_check.py` exists only as a `.pyc` + a module under
   `principle-foundation/.../hooks/` and a test — it is NOT wired into `settings.json` as a
   live `PreToolUse` hook.** KP9 says "extend the existing `translation_jargon_check.py`
   PreToolUse hook" and KP9's confidence is HIGH "(extends a working hook)." It is a built
   component, not a *running* hook on this machine. Extending it is fine; calling it a
   "working hook" the design merely augments is misleading about the wiring work required.

3. **`claude_print_client.py` at `framework/memory-system/src/...` does NOT exist.** The
   MEMORY.md rule (`feedback_no_anthropic_api_key`) cites that exact path, and the doc leans
   on it (§5.2 KP10: "`claude -p` via `claude_print_client.py`"). What exists is
   `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/claude_print_synthesis_client.py`
   — a different module in a different component. `framework/memory-system/` is not a source
   tree; the only `memory-system` dir is `docs/archive/component-research/memory-system`.
   **KP10's named primitive points at a path that isn't there.** The capability (claude -p
   subprocess) is real; the cited wrapper is not where the doc says.

4. **`pos_session_start.py` IS real and IS a genuine `SessionStart` hook** (verified —
   header confirms "Invoked by the Claude Code `SessionStart` hook"). So KP7's substrate is
   the one infrastructure claim that holds up. Credit where due. But note its current job is
   service-health probing (launchctl reseat), not context surfacing — KP7 is a real *new*
   feature on it, not an extension of existing surfacing behavior.

**Why this matters (not pedantry):** the doc's confidence column and effort estimates assume
a live hook chain to plug into. The real state is "one SessionStart hook wired; everything
else is unwired modules or non-existent files." That means:
- KP1/KP2/KP3/KP9/KP11 all require **wiring new hook entries into `settings.json`** (or a
  plugin `hooks.json`), which the doc treats as already-done plumbing. That's real work and
  a real risk surface (hook ordering, the #15174 SessionStart-compact bug the doc itself
  flags, FD-inheritance — see `pos_session_start.py`'s own warnings about the v2.1.87
  FD bug).
- The "$0 / 45ms / proven" framing is borrowed from claude-mem's *deployed* system, not from
  loam's. loam has not run a per-prompt retrieval hook in production; the perf/cost numbers
  are claude-mem's, correctly cited but **not yet loam's measured reality.**

**Fix:**
- Correct §6's "verified: loam already runs ≥5 UserPromptSubmit hooks" to the true state:
  "loam runs one wired SessionStart hook (`pos_session_start.py`); the per-prompt
  retrieval/voice/journal hooks are NEW wiring." Re-grade KP1/KP3/KP9/KP11 confidence
  accordingly (they're still buildable — just not "extend a running hook").
- Fix the `claude_print_client.py` path (or build the wrapper) before KP10.
- Add an explicit **KP0: wire the hook chain into settings.json + a hook-ordering/timeout
  smoke** as the first build item. Right now it's invisible, which is exactly how the
  FD-inheritance and SessionStart-compact bugs bite.

**Severity: HIGH** on accuracy (the doc claims verified infra that isn't there);
**MEDIUM** on buildability (it's all still buildable — the primitives exist — but the work
is larger and riskier than the doc's confidence column implies).

---

## 3. Does it default to ABSTRACTION, or leak mechanism? (MOSTLY YES, one self-undercut)

The design's *user-facing* output discipline is good: §5.4's inbound/outbound split is
correct, and "the gate's own feedback is model-facing only, never user-facing — a 'your reply
was blocked by the register judge' message would itself be a mechanism-leak" is exactly
right and shows the author internalized Luke's #8.

**But two leaks survive:**

1. **The drift-audit surface (§4.4 / KP8) leaks objective-mechanism to the user.** The
   sample surface — *"Your week is all fiction-pipeline; the revenue objective hasn't moved
   in 8 days — mark it dormant?"* — is actually well-abstracted prose. Good. BUT the doc
   elsewhere frames objectives with `status: active/dormant/retired`, `cadence`, `subgoal
   state`, `detail-path` — and there is a real risk the *implementation* surfaces those raw
   field names ("marking objective `revenue-push` dormant; cadence exceeded"). The doc should
   state explicitly that **objective surfaces obey the same abstraction gate as every other
   reply** — right now KP8's surface is not routed through the Layer-1/2 voice gate in the
   loop diagram (the gate is drawn only on the Telegram-reply path). A drift proposal sent to
   Luke is *also* a Telegram reply and must pass the same gate. The doc doesn't close that
   loop. Fix: route ALL user-facing surfaces (SessionStart summary, drift proposals,
   miss-recovery if ever surfaced) through the same gate, not just persona free-text replies.

2. **Self-undercut: the design's own internal vocabulary is the densest jargon in the
   building.** "ARC hotness rotation," "GD-commission/omission proxies," "w_s term,"
   "EVAL_DIMENSIONS named-axis." That's fine for a design doc. The risk is that this
   vocabulary leaks into *Luke-facing* status when the system reports on itself ("rotated 3
   memories out of the hot index per the ARC score"). The doc never says the system must
   describe its own behavior to Luke in plain language. Given Luke's #8 is load-bearing for
   the whole pitch, **the system explaining itself is the highest-risk leak surface** and
   it's unaddressed. Fix: one explicit line — "when the system reports on its own memory
   behavior to the user, it uses plain language ('I've been keeping your fiction work close
   at hand') never internal terms ('ARC-promoted')."

**Severity: MEDIUM.** The defaults are right; the gap is that the gate is drawn around only
one of the several user-facing surfaces, and self-reporting is unaddressed.

---

## 4. Does it handle ALL of Luke's scenarios? (YES on coverage, with soft spots)

Mapping each scenario to its mechanism, with the skeptic's note:

| Luke # | Scenario | Mechanism | Skeptic verdict |
|---|---|---|---|
| #1 | recall while working | KP1+KP2 | **Soft — see §1.** Keyed to prompt, not to work-in-progress. Fix = work-anchor retrieval key + extend draft gate. |
| #2 | session-start surface | KP7 | OK. Real hook exists. |
| #3 | multi-session cross-load | KP3 journal | OK *but* turn-granular, not instant (doc admits this). Honest. The unverified part: the "same proven re-read channel" cites a file that doesn't exist (§2 above). The n=1 two-session verify is correctly required. |
| #4 | learn frequent asks, preload | KP4 ARC | OK in theory; **all weights uncalibrated** (doc admits). Real risk: frequency-learning needs *weeks* of real traffic before it does anything useful — this is the longest-horizon payoff and the doc's effort estimate (40–70 min) is the *build* cost, not the *time-to-value*. Name that. |
| #5 | context-miss recovery | KP2 gate | **Soft — the vague-prompt blind spot.** A miss-gate keyed to BM25 low-score catches "off-topic request," not "vague continuation of on-topic work." Same root as §1. |
| #6 | objective drift, refine-not-erase | KP5/KP6/KP8 | OK. Append-not-overwrite + retire-keeps-entry is correct. KP8 proxies uncalibrated (admitted). |
| #7 | rotate under cap, don't lose old | KP4 + cold demotion | OK. The "file stays, index line goes" demotion is the right refine-without-erase mechanism. |
| #8 | abstraction by default | KP9/10/11 | OK with the §3 gaps (gate not drawn around all surfaces; self-reporting unaddressed). |

**Coverage is complete** — every scenario has a named mechanism. The soft spots are #1/#5
(the shared work-anchor gap) and the time-to-value reality on #4. No scenario is *missing*.

**One cross-scenario risk the doc under-weights:** the entire keep-pace half depends on
KP5's `OBJECTIVES.md` being *accurate and current*. If the objective register is stale or
wrong, the `w_s` rotation key is wrong, so the hot index rotates to the *wrong* scope, so
retrieval is mis-targeted — the doc's own §4.1 point #1 ("if the objective model is stale,
every retrieval is mis-targeted") **applies to its own architecture.** The drift audit (KP8)
is supposed to keep objectives current, but KP8 is the *last, loosest, least-calibrated*
item. So the architecture's correctness pivot (objectives → rotation) depends on its weakest
component (drift detection). That's a structural fragility the doc doesn't flag. Fix: until
KP8 is calibrated and trusted, keep objective status changes *fully owner-gated and
frequent-touch*, and don't let an un-calibrated `w_s` dominate the hotness score (cap its
weight low initially; let frequency+recency carry rotation until objectives are proven
current). The doc's §3.3 says "weights need tuning" but doesn't say "start `w_s` low because
its input is the least reliable."

**Severity: MEDIUM.**

---

## 5. Cost / complexity — is it over-engineered? (YES — ~2× the minimal version)

Eleven build items, five open forks, four uncalibrated tuning surfaces, a journal+fold+ARC
compaction subsystem, a 4-axis LLM judge, a behavioural depth-preference learner. For a
problem whose **named, concrete, tonight failure** is "surface the right memory while working
on a related topic."

**The minimal version that delivers the core outcome:**

1. **MVP = KP1 (work-anchored retrieval) + KP2 (miss-gate) + KP5 (`OBJECTIVES.md`, seeded) +
   KP9 (jargon lint).** Four items. This directly attacks tonight's failure (with the §1
   fix), closes the zero-objectives gap, and protects the user-facing promise on day one.
   Everything else is optimization of a loop that doesn't exist yet.

2. **Defer KP3/KP4/KP8/KP10/KP11 until the MVP loop is observed in real use.** Specifically:
   - **KP3 (cross-session journal):** real need, but Luke runs simultaneous sessions
     *sometimes*, and turn-granular cross-load is a refinement on top of "retrieval works at
     all." Ship after MVP. (And it can't cite the `queue_status_inject.py` precedent that
     doesn't exist — it needs its own n=1 proof first anyway.)
   - **KP4 (ARC rotation):** gated on `memory-architecture.md` M1/M2 *and* needs weeks of
     traffic to matter. It's a v2 concern. A bounded hot index with simple recency+manual
     pinning is enough until frequency data accrues.
   - **KP8 (drift audit):** the loosest, most-likely-to-annoy item (false "your revenue
     objective is dormant" proposals erode trust fast). Ship last, behind heavy owner-gating,
     after objectives are manually curated for a while.
   - **KP10 (register judge):** adds a `claude -p` round-trip of latency to *every flagged
     Telegram reply* — on the most latency-sensitive surface Luke has. The deterministic
     Layer-1 lint (KP9) catches the regular-form leaks (paths, filenames, IDs) that are 80%
     of the actual problem. The semantic judge is the expensive 20%. Defer it; let KP9 +
     per-turn re-injection (cheap) carry voice until there's evidence the semantic leak is
     frequent enough to justify the latency.
   - **KP11 (depth-learning):** longest-horizon, most speculative. A static per-topic depth
     map (hand-set: "fiction = abstraction; loam-dev = technical") delivers most of the value
     with none of the learning machinery. Learn later if the static map proves wrong.

3. **The journal+fold+ARC+atomic-rename subsystem (KP3+KP4) is the single biggest
   complexity sink** and it serves the two *lowest-urgency* scenarios (#3 cross-load, #4
   frequency). The doc correctly notes no product solves cross-session concurrency — but
   that's an argument it's *hard*, not that it's *urgent*. Tonight's failure was single-
   session. Build the single-session loop first.

**Counter-argument the doc could make (and my response):** "the items are independently
shippable, so listing 11 isn't over-engineering — it's a backlog." Fair, and the §6.1
sequencing does front-load KP1/KP2/KP5/KP9. **But** the doc frames all 11 as "the design,"
names KP1+KP2 as "the single highest-leverage piece" while *also* building 9 other things,
and the forks (§8) are mostly about items 4 items deep in the backlog (compactor cadence,
drift autonomy, judge gating) that don't need deciding to ship the MVP. **The over-
engineering is in presenting v2/v3 decisions as v1 forks** — it asks Luke to rule on judge-
gating policy before the retrieval hook he actually needs tonight exists. That violates
one-question-at-a-time and front-loads premature decisions.

**Fix:** Re-cut the doc into **MVP (4 items, ship now) + Backlog (7 items, ship on observed
need)**. Move forks §8.2/§8.3/§8.4 (compactor cadence, drift autonomy, judge gating) out of
"open forks Luke must rule on" and into "decisions deferred to their build item." Keep only
§8.1 (BM25-vs-dense, recommendation sparse — but this is barely a fork, the doc already
makes the call) and §8.5 (objectives user-scope-vs-workspace, genuinely needs deciding for
KP5) as live owner-asks. That's **one real fork** (KP5 scope), not five.

**Severity: MEDIUM-HIGH on scope discipline.** Nothing here is *wrong* to eventually build;
the failure is presenting the full system as the design and front-loading premature forks.

---

## 6. Smaller specific weaknesses (lower severity, worth a line each)

- **"45ms / $0" is claude-mem's number, stated as if it's loam's** (§0, §2.1, §7.3). Cited
  honestly in the research doc, but the design doc drops the attribution and reads as a loam
  guarantee. Mark it as "claude-mem's measured figure; loam's TBD on first build."
- **The miss-gate threshold is the one un-buildable-blind piece** (doc admits, §6.1 step 1:
  "log scores for a week, then calibrate"). Good that it's flagged — but it means KP2 cannot
  actually *function* for a week after KP1 ships. The doc should state the MVP is KP1-only
  for the first week, with KP2 dark-launched (logging, not steering) until calibrated.
- **No failure-mode story for the hook itself.** Every `UserPromptSubmit` turn now runs a
  BM25 query + journal read + objective match + voice re-inject. If that hook errors or
  hangs, every turn degrades. The doc says "hard-timeout, fail-open" for individual pieces
  but never specifies the aggregate per-turn latency budget or what the user experiences if
  the whole hook chain times out. `pos_session_start.py`'s own header shows loam has been
  burned by hook-process bugs (FD-inheritance, v2.1.87). Add an explicit total-turn-latency
  budget + fail-open-whole-chain behavior.
- **`InstructionsLoaded` and `SessionStart`-compact (#15174)** are flagged as verify-first
  risks (§8.6) — good — but #15174 (SessionStart additionalContext lost on compaction) is a
  *direct threat to KP7*, the session-start surface. The doc routes "re-injection around it
  via UserPromptSubmit" but doesn't say what happens to the *SessionStart* surface itself
  post-compact. If KP7's objective-surface vanishes on the first compaction, the session-
  start value evaporates mid-session. Name the mitigation for KP7 specifically.
- **Effort estimates look like build-time only, not wire+test+calibrate.** KP1 "30–60 min"
  is plausible for the script; it omits settings.json wiring, the smoke, and the week of
  score-logging before KP2 works. Per the duration rubric, surface AI-build-time and
  time-to-value as distinct line items (as the rubric itself requires).

---

## 7. Bottom line

**Fundamentally sound — needs targeted fixes, not rework.** The spine (one loop, four
views, BM25 substrate, append-only journal, independent voice gate) is correct and the
research under it is strong. The doc fails as a *build-ready* artefact on four points:

1. **(HIGH) It over-claims the tonight-failure fix.** KP1+KP2 keyed to the user's prompt
   miss the actual failure mode (mid-work drift on a vague continuation). Fix: work-anchored
   retrieval key (prompt + active objective + last topic) + extend the draft-to-send gate to
   check the *generated draft* against active constraint-memories. That draft gate is the
   only place in the loop that sees the text where the failure actually happens.

2. **(HIGH accuracy / MEDIUM buildability) It claims verified infrastructure that isn't
   there.** `settings.json` hooks are empty; `queue_status_inject.py` doesn't exist;
   `translation_jargon_check.py` is an unwired module not a running hook;
   `claude_print_client.py` is at a path that doesn't exist. Only `pos_session_start.py` is a
   real wired hook. Fix: correct the infra claims, add an explicit hook-wiring KP0, re-grade
   confidence.

3. **(MEDIUM) Abstraction gate is drawn around only one user-facing surface.** Drift
   proposals + session-start summaries + system self-reporting must pass the same gate. Add
   "the system describes its own memory behavior in plain language" explicitly.

4. **(MEDIUM-HIGH scope) It's ~2× the minimal version and front-loads premature forks.**
   MVP = KP1(work-anchored) + KP2(dark-launched) + KP5(seeded) + KP9(lint). Defer KP3/4/8/10/
   11 to observed need. Collapse five forks to one real one (KP5 scope).

The architecture's own stated principle — "if the objective model is stale, every retrieval
is mis-targeted" — applies recursively to itself: the correctness pivot (objectives→rotation)
rests on the weakest, last-built, uncalibrated component (drift detection). Cap `w_s` low
until KP8 is trusted.
