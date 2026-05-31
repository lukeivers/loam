# loam evolution — reasoning-process acceleration (the inverse of dogfooding)

**Date:** 2026-05-31. **Class:** read-only historical analysis (no code/system
touched). **Author:** synthesis over the loam git history (single repo
`/Users/lukeivers/loam`, 1622 commits, ~155 numbered amendments), the
`docs/design/` + `docs/plans/` + `docs/reviews/` corpus, and the
`feedback_*.md` corpus (130 files). **Trust discipline:** every historical claim
cites a commit SHA / doc path / date; inferences are marked **[INFER]**.

**The question this answers:** loam crystallized its own core concept — the
doctrine (per-user-tuned translation; two pillars; three legs; the operating
loop; memory-as-core; layered build) — on **2026-05-31**
(`docs/design/loam-doctrine.md:3`; `feedback_loam_prime_directive_user_tuned_translation.md`,
Telegram 13219). The first build landed **2026-04-18** (`git log --reverse`,
`8bc0512`/`e09f985`). That is a **43-day gap** between building loam and
understanding what loam was. The whole journey was an unintentional dogfood. The
payload below: where understanding stalled, the common shape of *why*, and the
mechanizable reasoning-process additions that would have compressed it — and
would help the next user converge faster.

---

## Part 1 — The inflection-point timeline

Each entry: **what was assumed → what it became → the gap → what the lateness cost.**
SHAs/paths are Tier-0 unless marked [INFER].

### IP-1 — "Build the whole stack first" (2026-04-18 → ongoing)
**Assumed:** the right first move was to build the heavy infrastructure —
memory-system (`8b28f6d` "full build D5–D13"), orchestrator (10 deliverables
`09cb263`→`7233a70`), graceful-degradation, observability-aggregator,
cost-governance — all in the **first three days** (2026-04-18→19).
**Became:** the doctrine's actual spine is a *four-step operating loop on top of
Claude* (`loam-doctrine.md:36-56`), and the v-next plan's **first brick** is one
small slice (FBM-LIVE, `loam-vnext-build-plan.md:180`). The orchestrator took
**55 commits** (20 in Apr + 35 in May, `git log -- framework/orchestrator/`) and
is not named as load-bearing for the user-facing doctrine anywhere in
`loam-doctrine.md`.
**Gap:** ~43 days; arguably the whole journey.
**Cost:** the heaviest components were built before the concept that would have
told you whether they were the right components. **[INFER, strongly evidenced]**
the doctrine's leg-3 ("Prune") explicitly names this as known overgrowth:
*"the objective-driven-authoring process is probably overbuilt — it grew elaborate
while the problem was still being understood"* (`loam-doctrine.md:150`).

### IP-2 — Graphiti memory: built-but-never-live, for ~40 days (2026-04-18 → 2026-05-28)
**Assumed:** the memory substrate was the Graphiti+Kuzu+Ollama graph
(`e09f985` 2026-04-18 "Graphiti+Kuzu+Ollama working"; MCP wired `0f4bf91`
amendment #47; async-write queue + worker `262f50d` amendment J).
**Became:** the graph backend **was never actually live**. The file-based pivot
landed `4a9f135`/`e57770f` (2026-05-01, "memory-substrate pivot series"), graphiti
dropped from first-run `a22272c` (2026-05-03, FBE.7/#105) — but the docs and code
still carried the aspirational graph shape until it was finally reconciled
**2026-05-28** (`memory-architecture.md:150-152`: *"S3 is design-aspirational, not
currently live … no `kuzu_db` exists on disk; `memory_consumer.py` is a Protocol
shim"*).
**Gap:** ~40 days between building the graph and the corpus stating plainly it
was never running.
**Cost:** every memory decision in that window reasoned against a backend that
did not exist; `memory_consumer.py` is a Protocol shim that *"never imports
memory-system source"* (`memory-architecture.md:160`). The keep-pace MVP had to
carry an explicit RF correction that retrieval *"runs over the markdown corpus
(BM25/FTS5), not the graph"* (`memory-architecture.md:152`).

### IP-3 — FBM = episode store, not rules store (named only 2026-05-29)
**Assumed [INFER]:** "FBM" (file-based memory) was loosely conflated with the
rules corpus across the build; the owner had to correct it directly —
*"FBM = File-Based Memory. It's supposed to be a COMPREHENSIVE memory storage
system — not file-based RULES storage"* (`fbm-state-and-memory-roadmap-2026-05-29.md:70`).
**Became:** three physically-distinct stores, finally tabled (S1 CLAUDE.md /
S2 feedback corpus / S3 episodic), with the conflation named as *"the root of the
architecture gap"* (`memory-architecture.md:144`). Even the **name** drifted —
the same substrate is "FBE" in `docs/components/memory.md:11` and "FBM" in the
amendment stream (`fbm-state-and-memory-roadmap-2026-05-29.md:98`).
**Gap:** ~6 weeks; a core capability carried two names and a conflated definition.
**Cost:** the owner caught it, not the persona — and the trigger was a live
failure (a stale note trusted over reality; a "Book 1 done" claim made with
pipeline state un-surfaced, `fbm-state-and-memory-roadmap-2026-05-29.md:70`).

### IP-4 — "We've drifted from translator to orchestrator" (owner-caught, 2026-05-04)
**Assumed:** the build mix (heavy plan-docs, dispatch scaffolds, sealed-component
amendments) was on-mission.
**Became:** the owner had to name the drift — *"I've turned you into more of an
orchestrator"* (`value-prop-vs-actual-shape-audit-2026-05-04.md:4`). The audit
confirmed it empirically: the user-visible surface was *"amendment briefs,
gate-review prompts, SHA notifications … not a chief-of-staff translating intent"*
(`value-prop-vs-actual-shape-audit-2026-05-04.md:56-58`). The locked
VALUE_PROPOSITION had *already named "dispatcher" as the failure mode*
(`...audit...:16-18`) — the drift was visible in the founding doc and still happened.
**Gap:** weeks of orchestration-heavy output before the owner zoomed out.
**Cost:** the persona was applying the harness-leverage *test* correctly
(Pattern F, `...audit...:52`) while the *aggregate output* drifted off the prime
objective — local correctness, global drift. The doctrine's prime directive
(2026-05-31) is the sharpened restatement that closes this: per-user-tuned
**translation**, explicitly *"never merely to execute"* (`loam-doctrine.md:19`).

### IP-5 — The rename programme: 8+ amendments of pure renaming (2026-04-29)
**Assumed [INFER]:** the pos-v2 → loam rebrand was tractable as a docs sweep.
**Became:** a multi-amendment programme — #76 prose, #77 env-vars, #78 launchd
labels, #79 OTel roots, #80 namespace pivot (**522 import-callsite rebrands**,
`c806f57`), #81 dormancy, #82 CLI rename + tools-tree pivot. Across the whole
history, **29 of 241 feat-amendments (~12%)** are rename/restructure/migration/
partition work (`git log | grep feat | grep -iE rename|restructure|...`).
**Gap:** the cost was paid at amendment #76-82, after 75 amendments had baked the
old name into 522 callsites + launchd labels + OTel namespaces.
**Cost:** the deferred-naming tax. **[INFER]** had the name been a settled
decision earlier, the 522-callsite sweep would have been near-zero. This is the
"un-audited assumption baked deep, expensive to change later" pattern in its
purest form.

### IP-6 — The "lapsed re-eval" deferral that silently never fired (2026-05-21 → 2026-05-29)
**Assumed:** FBM Tier 3 orchestration could be deferred with a *"Re-evaluate after
~1 week"* trigger (`fbm-state-and-memory-roadmap-2026-05-29.md:112`, queue
`ws-tier3-orchestration` `deferred_at: 2026-05-21`).
**Became:** the trigger silently lapsed — surfaced 8 days later in the roadmap as
exactly the `feedback_workaround_masks_rootcause_urgency` shape, and the v-next
plan had to invent a **structural release-gate** to prevent the class
(`loam-vnext-build-plan.md:218`, gap #3).
**Gap:** the re-eval never self-fired; it was caught only by a fresh grounding pass.
**Cost:** a deferral with a time-based trigger and no enforcing mechanism is a
silent drop. The fix (a gate that *forces* the decision per release) is the same
shape as the structural-enforcement parent (`feedback_structural_enforcement_on_recurrence.md`).

### IP-7 — The keep-pace "rides existing infra" claim that was false (2026-05-28)
**Assumed:** the keep-pace design "rides loam's existing hook chain (≥5 live
UserPromptSubmit hooks)."
**Became:** *"That was false"* — re-verified: *"Global settings.json hooks = {}.
Zero wired hooks except SessionStart"* (`keep-pace-with-user.md:208-212`). A whole
table of prior-draft claims (`queue_status_inject.py` re-reads every turn,
`translation_jargon_check.py` is a live hook, `OBJECTIVES.md` exists) was found
to be **wrong on verification** (`keep-pace-with-user.md:210-218`).
**Gap:** an entire design draft built on un-verified existence claims about its
own substrate.
**Cost:** the design had to be re-graded against verified machine state before any
build. This is the same class as IP-2 (reasoning against a substrate that isn't
there) — and the corpus has a memory for it
(`feedback_never_assert_claude_surface_from_prior.md`).

### IP-8 — The v0.6.1 framing-miss revert (2026-05-08)
**Assumed:** 6 commits of foundation-docs work (`ce379da`→`6c7ebdb`) were on-frame.
**Became:** *"revert: v0.6.1 framing miss — squashed revert of 6 commits"*
(`037aa58`, 2026-05-08).
**Gap:** 6 commits built before the framing miss was caught.
**Cost:** 6 commits of wasted work. **[INFER]** a frame-check before the build,
not after the 6th commit, would have caught it.

### IP-9 — ODD elaboration grown then flagged as overbuilt (2026-04→2026-05-31)
**Assumed:** objective-driven design needed elaborate machinery (the ODD spec, the
methodology, the no-non-objective-code rule, the master-plan rebuild — **6 ODD
plan/design docs**, `ls docs/{plans,design} | grep -ci odd`).
**Became:** the doctrine names ODD's authoring process as **probably overbuilt** —
*"it grew elaborate while the problem was still being understood; a leaner version
protects the same intent with less ceremony"* (`loam-doctrine.md:150`).
**Gap:** the whole build; flagged only at doctrine time.
**Cost:** ceremony accreted faster than the understanding that would have told you
how much ceremony the intent actually needed. This is leg-3 ("Prune") existing
*because* of this pattern.

---

## Part 2 — The pattern behind them

The nine inflection points are not nine unrelated misses. They share four shapes:

**P-A — Linear-reactive building without scheduled zoom-out.** IP-1, IP-4, IP-9.
Work proceeded amendment-by-amendment; the "are we still building the right
thing?" question fired only when the **owner** raised it (IP-4, IP-3) or at a rare
grounding pass (IP-2, IP-6). There was no *recurring, self-fired* concept-altitude
review. The persona's local moves were correct (harness-leverage test applied,
Pattern F `...audit...:52`) while the aggregate drifted. **Local correctness is not
global alignment, and nothing was watching the global.**

**P-B — Un-audited substrate assumptions, baked deep, expensive to change.**
IP-2 (graphiti assumed live), IP-5 (name assumed settled), IP-7 (hooks assumed
wired). Each is the same failure: a load-bearing fact about loam's *own substrate*
was assumed rather than verified, the assumption propagated into code/docs/callsites,
and the correction cost scaled with how long it baked. The corpus already has the
rule for this class — *"every datum that becomes load-bearing is trust-evaluated …
at the moment it becomes load-bearing"* (`feedback_unified_memory_frame.md`) — but
it was authored 2026-05-16, *after* most of the baking, and it relies on the
persona remembering to apply it.

**P-C — Failure-only learning.** IP-3, IP-6 surfaced via live failures (stale note
trusted; "Book 1 done" mis-claim). IP-4 surfaced via owner discomfort. The
realizations were **reactive to a visible failure**, never produced by a proactive
"what would we discover if we audited this now?" pass. The robust-workaround memory
names exactly this (`feedback_workaround_masks_rootcause_urgency`: *"the smoother
the mitigation, the longer the underlying defect survives"*) — but as a memory rule
it again depends on the persona noticing the recurrence.

**P-D — Intent-evolution untracked; current-state re-litigated.** The doctrine
*"sharpens an older framing"* (`loam-doctrine.md:25`) — the value prop already said
"translate intent" but missed "per-user-learned." The naming drift (FBE vs FBM,
IP-3) and the re-litigated machine state (IP-7) are the same: there was no single
**living "what loam currently is + what it currently runs" record** that every new
piece of reasoning checked against. So each new design re-derived (often wrongly)
the current state instead of reading it.

**The uncomfortable through-line (F2):** every one of these was catchable earlier
*from evidence already on disk*. The locked VALUE_PROPOSITION named "dispatcher"
before the drift (IP-4). The graphiti backend's absence was checkable with one
`import graphiti_core` the whole time (IP-2). The hooks-empty fact was one
`cat settings.json` away (IP-7). **The bottleneck was never information — it was
the absence of a scheduled, structural trigger that forced the check before the
assumption became load-bearing.** That is precisely the lesson the corpus learned
the hard way and promoted to a parent rule: *recurrence-despite-corpus →
structural enforcement, not another memory rule* (`feedback_structural_enforcement_on_recurrence.md`).

---

## Part 3 — Reasoning-process improvements for loam (the payload)

Each is concrete and mechanizable, cites the inflection point it would have
prevented, and names how it composes with the v-next build plan. These go **beyond**
the already-named lessons (MVC fits; memory is core; per-user adaptation).

### R-1 — A living "current reality" record that every design step must read first
**What:** a single, terse, always-loaded **STATE-OF-LOAM** record answering "what
loam *currently is* (concept) + what loam *currently runs* (substrate: which hooks
are wired, which backends are live, which components are dark)." Not the doctrine
(the aspiration) and not STATE.md (the amendment ledger) — the **operative-reality**
record. Every design/plan-author step's first action is to read it; every seal
updates it. Backed by a cheap machine probe (e.g. `import graphiti_core` → live/dark;
`settings.json` hooks → wired/empty) so the record can't drift from reality silently.
**Prevents:** IP-2 (40 days reasoning against a dark graph), IP-7 (designing on
false "hooks already wired" claims), IP-3 (the FBE/FBM name+definition drift), P-D
generally. The keep-pace doc's own "Verified machine state" table
(`keep-pace-with-user.md:206-220`) is this record done *reactively, once*; R-1 makes
it standing and machine-backed.
**Composes with v-next:** rides the same boundary record F0.2 already locks
(`loam-vnext-build-plan.md:108`); the failure-mode-guard matrix (P2.2) and the
capability-adoption matrix are its siblings — R-1 is the *substrate-liveness* matrix.

### R-2 — A scheduled concept-altitude review (the zoom-out, self-fired)
**What:** a recurring pass — on a cadence and on a trigger (every N amendments / a
version bump) — that asks one question: *"does the aggregate of recent work still
ladder up to the prime directive, or have we drifted?"* It diffs the *shape of
recent output* (what the user-visible surface looks like) against the doctrine's
spine, and surfaces drift with evidence. This is the persona doing IP-4's audit
**on itself, on a schedule**, instead of waiting for the owner to feel the drift.
**Prevents:** IP-4 (translator→orchestrator drift, owner-caught), IP-1/IP-9
(overbuild caught only at doctrine time), IP-8 (framing miss caught at the 6th
commit). P-A directly.
**Composes with v-next:** this *is* a recurring loop in the doctrine's living
character (`loam-doctrine.md:147`) — slot it beside the capability-adoption loop
(P2.4) and the user-model re-eval (P2.1/AIM-7). It is the "pruning leg's" upstream
trigger: drift detected → prune/redirect. Use the `claude-capability-adoption-loop`
scheduling shape (Routine + launchd) already designed in
`docs/reviews/claude-capability-adoption-loop-design.md`.

### R-3 — Substrate-assumption audit gate before any design becomes load-bearing
**What:** before a design/plan treats a fact about loam's own substrate as
load-bearing (a backend exists, a hook is wired, a name is settled, a component is
live), it must **verify-or-mark-guess** that fact against R-1 + a live probe — a
structural gate, not a discipline the persona must remember. Mechanizable as a
plan-author checklist hook that scans the draft for "rides existing X / X already
does Y" claims and blocks until each is verified.
**Prevents:** IP-2, IP-7, IP-5 (the name-not-settled assumption), P-B entirely.
**Composes with v-next:** this is the structural promotion of
`feedback_unified_memory_frame.md` + `feedback_never_assert_claude_surface_from_prior.md`
from memory-tier to gate-tier — exactly the move
`feedback_structural_enforcement_on_recurrence.md` prescribes (these rules recurred;
promote them). Lands as a PreToolUse/plan-author gate in the v-next kernel's
authoring path; pairs naturally with the migration release-gate (P1.3) which is the
same "force the check, don't rely on memory" pattern.

### R-4 — Track intent-evolution as a first-class artifact (a "concept changelog")
**What:** a small append-only record of *how the understanding of loam itself
changed* — "we thought X; it became Y; on DATE; because Z." The doctrine
*sharpening* the value prop (`loam-doctrine.md:25`) is one entry; the
translator→orchestrator correction is another; the FBE/FBM unification is another.
When a new design is authored, it reads the concept changelog so it inherits the
*current* understanding rather than re-deriving (often a stale version of) it.
**Prevents:** P-D (re-litigated current-state, IP-3/IP-7), and the slow-sharpening
of the prime directive itself (the per-user piece was "missing" for 43 days,
`loam-doctrine.md:27`).
**Composes with v-next:** this is the *concept-level* analogue of the user-state
migration log (P1.3) — migrations track how user-state evolves; the concept
changelog tracks how loam's self-understanding evolves. Both live on the durable
side of the boundary. For a **new user**, this is the highest-value transfer: the
new user's loam keeps a changelog of how *their* project's concept evolves, so they
converge on "what am I actually making" without re-deriving it each session.

### R-5 — Plan-first-then-probe applied to loam's OWN substrate, not just external research
**What:** `feedback_research_existing_solutions_before_building.md` already mandates
"form your own plan, then web-check." Extend the *probe* half inward: before
building, also probe **loam's own substrate** (does this already exist here? is it
live? is it dark-but-built?). IP-7 (FBM "first brick" framed as build-from-scratch
when it was built-but-dark, `loam-vnext-build-plan.md:214`) is the canonical miss
this fixes — the v-next plan itself had to correct the dispatch's "build FBM"
framing to "wire-it-live."
**Prevents:** IP-1 (rebuilding heavy infra), IP-7 (re-building the dark FBM),
duplicated effort generally.
**Composes with v-next:** strengthens Lens-1 (Claude-leverage-first) with a
"loam-leverage-first" inward step — check what loam *already has built-but-dark*
before building new. Directly supports the v-next first-slice reading (wire-and-unify,
not rebuild).

---

## Part 4 — Top 3 highest-leverage (ranked)

**#1 — R-1: the living "current reality" record, machine-backed.**
*Build into v-next as:* a **STATE-OF-LOAM operative-reality record** on the
user-state side of the boundary, refreshed by a cheap liveness probe and read first
by every design/plan step — the sibling of P2.2's failure-mode matrix.
*Prevents:* the single most expensive class — ~40 days reasoning against a dark
graphiti backend (IP-2), plus IP-7 and IP-3. It is the root fix for pattern P-B and
P-D at once. **Highest leverage because the bottleneck was never missing
information — the absence of a single authoritative current-reality surface forced
every other miss.**

**#2 — R-2: the scheduled concept-altitude review (self-fired zoom-out).**
*Build into v-next as:* a **recurring drift-audit loop** beside the
capability-adoption loop (P2.4), diffing recent output-shape against the doctrine
spine and surfacing drift with evidence on a cadence.
*Prevents:* the translator→orchestrator drift the owner had to catch (IP-4), the
overbuild caught only at doctrine-time (IP-1/IP-9), the framing-miss caught at the
6th commit (IP-8) — all of pattern P-A. **Second because it converts owner-caught
drift into self-caught drift; for a new user this is what makes loam converge their
concept *for them* on a schedule.**

**#3 — R-3: the substrate-assumption audit gate (structural, not memory).**
*Build into v-next as:* a **plan-author verify-or-mark-guess gate** that blocks any
"rides existing X / X already does Y" claim until verified against R-1 — promoting
the unified-memory-frame and never-assert-surface rules from memory-tier to
gate-tier per `feedback_structural_enforcement_on_recurrence.md`.
*Prevents:* the false "rides existing infra" design (IP-7), the dark-backend
assumption (IP-2), the unsettled-name assumption (IP-5) — pattern P-B. **Third
because it is the enforcement that makes R-1 load-bearing: R-1 supplies the truth,
R-3 forces designs to consult it.**

These three compose into one mechanism: **R-1 holds current reality, R-3 forces
every design to check it before assuming, R-2 periodically checks the *aggregate*
against the doctrine.** Truth, enforcement, and zoom-out — the three things whose
absence produced all nine inflection points.

---

## Flags (inference vs citation)

- **Cited (Tier-0):** all dates, SHAs, amendment numbers, doc-line references, and
  the 43-day / 29-of-241 / 55-commit / 6-ODD-doc counts (each from a named
  `git log` or `ls | grep -c` in this analysis).
- **[INFER] marked inline at:** IP-1 (overbuild causation — strongly evidenced by
  `loam-doctrine.md:150` but the doctrine is the *interpretation*, not a
  contemporaneous record); IP-3 (the conflation predating the 2026-05-29 correction
  — the owner's correction is cited; the duration of the prior conflation is
  inferred from the FBE/FBM dual-naming across docs); IP-5 (the counterfactual
  near-zero rename cost had the name settled earlier); IP-8 (the frame-check
  counterfactual). The *reverts/corrections themselves* are all Tier-0; the
  *would-have-prevented* counterfactuals are reasoned, not observed.
- **Scope honesty (F2):** I did not re-open the doctrine (settled per the brief) and
  built nothing. Part 3/4 are reasoning-process additions composed onto the existing
  v-next plan, not a new vision. Cairn untouched (never referenced any Cairn path).
