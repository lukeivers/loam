# Claude-leverage program — prefer-the-primitive doctrine + living capability knowledge, pushed to users (master plan)

> **Status:** PROGRAM-level master plan-doc (ODD-shaped). Splits into four
> slices, each dispatched off its own sub-plan-doc + manifest. PLAN ONLY — no
> build dispatched off this doc; no manifest authored at program level (see
> §0 note below).
> **WD:** `/Users/lukeivers/loam` (canonical loam).
> **Owner directive (source of truth for intent):** Discord
> 1514741531687256226, 2026-06-11, captured as
> `docs/FUTURE_IDEAS_DRAFT.md` § F-CLAUDE-LEVERAGE-PROGRAM. Owner framing:
> *"the literal core of all of loam is helping users do better at leveraging
> AI without having to learn about how to do it themselves."*
> **Parent objective:** AC.PO.1 + AC.PO.2 (prime objective — per-user-tuned
> translation + the protection floor — `docs/VALUE_PROPOSITION.md`). §4 below
> ladders each leg explicitly.
> **Predecessors (load-bearing):**
> - Research artefact (Tier-0, fetched 2026-06-11):
>   `/Users/lukeivers/pos3/workspace/.scratch/claude-output/claude-primitives-gap-analysis-2026-06-11.md`
>   — the gap table, top-5 shortlist, and 3 discrepancies. Re-verified at
>   plan-author time (2026-06-11): subagent-recursion-to-5-levels confirmed in
>   the Claude Code changelog at v2.1.172; `/goal` native at v2.1.139;
>   `extraKnownMarketplaces` auto-update policy at v2.1.142; latest CC version
>   2.1.173.
> - LOCKED design (Luke 2026-04-26):
>   `docs/plans/research/persona-capability-knowledge-grounding-research.md`
>   — two-class corpus partition (§2.6), currency mechanism (§7bis), sequenced
>   amendments α/β/δ/γ (§7). **α shipped**
>   (`docs/plans/claude-code-corpus-prompt-spine-and-seed-docs.md` — the
>   corpus + AUTHORING.md + persona spine exist). **β (MCP knowledge-server),
>   δ (currency refresh), γ (dynamic contributor) never shipped** — verified
>   2026-06-11: no `knowledge-server/` directory; corpus has 4 Class-A
>   claude-code entries; `CLAUDE_CAPABILITIES.md` is the 2026-04-23 snapshot.
> - Existing surfaces this program graduates or composes with:
>   `plugins/loam-skills/skills/{goal-command,loop-command,schedule-wakeup,handsoff-loop,cron-create,launchd-plist}`,
>   pos3 workspace-local skills `claude-feature-awareness`,
>   `tool-selection-rubric`, `primitive-rationale-check` (hand-rolled
>   prototypes of leg 1), the loam microkernel's "IF about to build a loop…
>   check for a native Claude primitive first" trigger, and
>   `framework/egress-consent/` (binds leg 4's public actions).
> **BASELINE candidate:** `dceb2009` (HEAD of main at plan-authoring; each
> slice's manifest walks its own baseline at apply time).
> **Status-file target:** `docs/STATE.md` change-log + `docs/release-roadmap.md`
> §8 register + FIDRAFT graduation note on F-CLAUDE-LEVERAGE-PROGRAM.
> **Quality bar:** every AC outcome-shaped; ≥1 outcome-altitude AC (★) per
> slice; method stays the builder's call per ODD §1.1; versions derive at
> release time (`feedback_version_numbers_at_release_time`) — no version
> numbers pre-assigned anywhere in this doc.

**§0 note — why no manifest at program level.** Manifests pair with build
cycles, not programs (precedent:
`docs/plans/context-management-see-budget-eviction-master.md` carries no
manifest; its per-cycle sub-plans do). Slice 1's placement decision
(D-CLP.5 + §2) is itself sub-plan work; authoring a manifest now would
pre-bake placement at the wrong altitude. First manifest lands with the
Slice 1 sub-plan-doc.

---

## §1 Summary / TL;DR

**The program (owner's four legs → four slices, dependency-ordered):**

1. **Slice 1 — CURRENCY (`AC.CLP-CUR.*`).** The root-cause fix, first. A
   recurring, unattended refresh keeps the Class A capability corpus current
   against Anthropic's canonical sources, and the stale parallel snapshot
   (`CLAUDE_CAPABILITIES.md`) stops being a second source of truth. Revives
   the locked-2026-04-26 δ design **scoped down** (deterministic projection
   refresh only; no MCP knowledge-server — see D-CLP.3). Includes the
   immediate correction of the proven-wrong subagent-recursion claim.
   **HIGH confidence; independently shippable; everything else leans on it.**

2. **Slice 2 — DOCTRINE (`AC.CLP-DOC.*`).** Prefer-the-primitive made
   operational and checkable: when loam (the persona or a dispatched agent)
   is about to do work directly or build a bespoke equivalent of a catalogued
   Claude primitive, an observable check fires on the production path.
   Doctrine text alone has already failed in this workspace
   (`feedback_structural_enforcement_on_recurrence`); the fix is structural +
   advisory layered (D-CLP.1). Graduates the pos3 hand-rolled prototypes
   (`tool-selection-rubric`, `primitive-rationale-check`,
   `claude-feature-awareness`) into loam proper. **HIGH-MEDIUM confidence.**

3. **Slice 3 — NAMED ADOPTIONS (`AC.CLP-ADOPT.*`).** `/goal` and `/loop` in
   consistent, effective, observable use — the owner-named instance of the
   doctrine. Carries the native-`/goal`-vs-bespoke-`autonomy_continuation.py`
   evaluation (D-CLP.2). **MEDIUM confidence (interacts with live pos3
   machinery). Parallelizable with Slice 2.**

4. **Slice 4 — KNOWLEDGE CORPUS, PUSHED (`AC.CLP-PUSH.*`).** A continuously
   curated body of best-current LLM/Claude/Claude-Code leverage knowledge,
   delivered TO loam users ~weekly with no per-user pull ritual. Distribution
   mechanism is the program's biggest named decision (D-CLP.4 — recommend
   **plugin-marketplace auto-update**). Every step that publishes off-machine
   is **owner-gated** (marked ⛔OWNER in §6). **MEDIUM confidence on
   mechanism; the leg itself is the closest to loam's prime objective.**

**Recommended slice order:** 1 → 2 → (3 ∥ 2) → 4. Rationale: a doctrine that
"always knows about" primitives is only as good as its catalogue — and the
catalogue is the component with a proven live failure (7-weeks-stale,
factually wrong on a load-bearing claim, found 2026-06-11). Slice 4 is last
because it is the largest, owner-gated at multiple steps, and consumes
Slice 1's currency machinery as its content pipeline.

**Named decisions (full register §10; recommendation-is-the-decision unless
the dispatcher overrides):** D-CLP.1 enforcement shape → **layered
(plan-time section + dispatch-time structural check)**; D-CLP.2 → **native
`/goal` first, bespoke retained only where native can't reach**; D-CLP.3 →
**revive locked-δ scoped down, defer β**; D-CLP.4 ★OWNER-facing → **plugin
marketplace auto-update**, per-publish owner gate initially — **RATIFIED by
owner 2026-06-11 ("I'm good with the plugin marketplace auto update thing",
Discord 1514753768175042771)**; D-CLP.5 →
**demote `CLAUDE_CAPABILITIES.md` to an index over the corpus**.

**F2 on scope realism:** Slices 1–3 are honest single-cycle-to-double-cycle
builds. Slice 4 is genuinely larger (new public surface + curation pipeline +
bootstrap wiring) and may itself decompose at sub-plan time; this master plan
licenses that decomposition. The hardest honesty: "pushed, no pull" on a
local-first CLI is asymptotically approximated, not literally achieved — every
mechanism is some form of automated fetch; the test that matters is *zero
user action after one-time setup* (§10 F2.1).

**AI-time bands (estimate-grade, per duration rubric):** Slice 1: 60–180 min;
Slice 2: 45–120 min; Slice 3: 30–90 min; Slice 4: 120–300 min build +
owner-gate latency as separate line items.

---

## §2 Placement decisions (extend-vs-new; final placement at sub-plan time)

| Surface | Placement (recommended) | Rationale |
|---|---|---|
| Class A projection-refresh automation (Slice 1) | **NEW small framework surface or `framework/tools/`-adjacent script set**; binding to a scheduler is workspace-authored. **FINALISED at Slice 1 (D-CUR.1, sealed `c41f9473`): tools-adjacent NEW component `framework/tools/capability-refresh/` (first-seal).** | Per locked δ design, loam ships the contract (source manifest schema + projection transform + diff flow); the schedule binding is workspace content. No existing component owns "keep reference docs current." Final new-component-vs-tools call is the Slice 1 sub-plan's first decision. |
| `CLAUDE_CAPABILITIES.md` (Slice 1) | **DEMOTE in place** to an index/redirect over `docs/capability-corpus/` (D-CLP.5) | Two parallel snapshots is how the 7-week-stale failure happened; one refreshable source of truth. |
| Doctrine catalogue + selection rubric (Slice 2) | **EXTEND `plugins/loam-skills/`** — graduate pos3's `claude-feature-awareness` / `tool-selection-rubric` / `primitive-rationale-check` into shipped skills (merged/renamed as the builder sees fit) | The prototypes are proven in pos3 daily use; loam users don't have them. Skills are the auto-discoverable primitive (Lens 1). |
| Doctrine structural check (Slice 2) | **Hook surface** — dev-mode dispatch path first (`plugins/dev-sdlc`), persona/runtime path second | Structural-enforcement-on-recurrence pattern; exact hook event + scope is builder's call. |
| `/goal`+`/loop` adoption (Slice 3) | **EXTEND existing skills** `goal-command` / `loop-command` / `handsoff-loop` + corpus Class B entries | The skills exist; the gap is consistent *use* + the bespoke-overlap ruling. |
| Weekly knowledge pack (Slice 4 content) | **`docs/capability-corpus/` stays the canonical store**; a distribution projection is built FROM it | Single source of truth; the pack is a rendering, never a fork. |
| Distribution channel (Slice 4) | **NEW public marketplace repo (⛔OWNER to create) carrying a knowledge plugin**; `framework/workspace-bootstrap/` extends to wire it for users | Per D-CLP.4. Outside any sealed fence until created; bootstrap extension is inside the existing `workspace-bootstrap` fence. |

---

## §3 Halt-and-surface AT plan-authoring (recorded surfaces)

1. **No FIDRAFT-vs-gap-analysis contradiction found** (dispatch halt trigger
   checked): the F-CLAUDE-LEVERAGE-PROGRAM capture and the 2026-06-11 gap
   analysis agree on all four legs and the evidence. One sub-claim refined:
   gap-analysis §3.3 said `meta-decision-haiku` has "no SKILL.md on disk" —
   verified at plan-author time: the directory exists but contains only
   `__pycache__`, consistent with the discrepancy as written. Not blocking.
2. **All four legs passed the method-in-AC test** (dispatch halt trigger
   checked): each is expressed outcome-shaped in §5; for leg 2, naming
   `/goal`/`/loop` is the *objective* (owner-named adoption targets), not
   method-in-AC.
3. **Locked-design staleness, named (Lens 6 conflict #1).** The 2026-04-26
   locked design predates the loam rename, the memory-system overhaul
   (graphiti → keep-pace/FBM, with the 2026-06-07 eval rulings), and the
   persona restructure. Conflict: *locked-design-not-license* vs
   *don't-relitigate-locked-decisions*. Signals: scope-confidence (the
   *intent* — two-class partition, deterministic Class A refresh, owner-gated
   Class B curation — remains high-confidence; the *substrate references* —
   graphiti episodes, Stop-hook mirror, "Eve", `personas/<handle>/` — are
   demonstrably stale), reversibility (high; doc-level), blast radius (low).
   Call: **reuse the locked design's intent and cadence table; treat its
   substrate bindings as stale and re-derive at sub-plan time.** Non-obvious
   enough to record, not enough to block: surfaced here for dispatcher
   visibility, proceeding on the recommendation.
4. **Weekly push vs ASK-FIRST-on-public (Lens 6 conflict #2 — the program's
   load-bearing conflict).** Named per the four-step process:
   (1) *Conflict:* leg 4 wants recurring outbound publication with no
   per-event friction; the egress-consent floor + ASK-FIRST-on-public wants
   owner consent before anything leaves the machine. (2) *Signals:* audience
   (public — weighs heavily toward gating), reversibility (published content
   is cached/mirrored — low reversibility), blast radius (all loam users
   receive it), time pressure (weekly cadence — low urgency per event),
   information asymmetry (owner can't pre-read unwritten future content).
   (3) *Call:* gate the **channel** once (creation of the public distribution
   surface = ⛔OWNER), gate **each publish** initially (⛔OWNER per weekly
   pack), and surface a **standing-approval option** (owner may later ratify
   "auto-publish packs that pass the curation gate") as an explicit owner
   decision — never assumed. (4) *Surfaced:* this resolution is in the
   owner-facing summary; the standing-approval question is the owner's to
   answer when Slice 4 dispatches.
5. **`fallbackModel` tension** (gap-analysis §2) conflicts with the standing
   2026-06-09 "never swap models mid-amendment" ruling — **excluded from this
   program** (§7); re-surfaced here only so it isn't lost.

---

## §4 Spec-objective placement — how the program ladders to the prime objective

- **This program is a direct instance of Lens 0 + Lens 1** (the FIDRAFT
  derivation line says so; this plan binds it). Concretely:
  - **Leg 4 ≈ AC.PO.1 (per-user-tuned translation).** The owner's framing —
    users "do better at leveraging AI without having to learn about how to do
    it themselves" — is the VALUE_PROPOSITION prime objective restated. The
    knowledge pack is translation-at-scale: loam learns the *how* (best
    current leverage) so no user has to; the persona translates pack content
    into each user's vocabulary per the Lens 0 substance/vocabulary rule.
  - **Legs 1–3 ≈ AC.PO.2 (the protection floor) + Lens 1 hardened.**
    Re-implementing a worse bespoke equivalent of a maintained Anthropic
    primitive is a default AI betrayal (wasted tokens, unmaintained code,
    silent capability gaps). The doctrine + currency machinery is the guard;
    the gap analysis is the evidence the guard is currently advisory-only and
    stale-informed.
- **Lens 2 (both tests):** primary-persona test — every slice reduces
  translation burden (the persona reaches for the right primitive without the
  user knowing primitives exist). Harness test — each slice adds toolkit
  (refresh machinery, doctrine skills + hook, adopted primitives, the pack
  channel). No slice fails either test.

---

## §5 Acceptance criteria

Program-level family `AC.CLP.*`; per-slice families strictly tighter
(Lens 5). ★ = outcome-altitude (production entry-point, no pre-arranged
state). Every AC below passes the method-in-AC test: a method other than the
recommended one can satisfy it.

### Program level

| AC | Outcome | Verification |
|---|---|---|
| AC.CLP.1 ★ | A capability fact that is wrong or missing in loam's reference surface gets corrected/added by loam's own recurring machinery — not by a human noticing — within one refresh cadence of the upstream truth changing. | Inject/observe an upstream change; observe the corpus correction with no manual trigger. |
| AC.CLP.2 | For each of the four legs, the slice that delivers it is sealed, and its AC family is green. | Per-slice seal records. |

### Slice 1 — CURRENCY (`AC.CLP-CUR.*`)

| AC | Outcome | Verification |
|---|---|---|
| AC.CLP-CUR.1 | The corpus's claim about subagent recursion is factually correct per the live Claude Code changelog at build time (known-wrong §7.7 claim corrected), and no in-repo reference doc contradicts it. | Read corpus entry; grep for the stale claim repo-wide. |
| AC.CLP-CUR.2 | Exactly one canonical capability-reference surface exists: `CLAUDE_CAPABILITIES.md` no longer carries independently-maintained capability claims (index/redirect only). | Read the file; no four-section capability entries remain in it. |
| AC.CLP-CUR.3 | A recurring refresh exists that, unattended, projects Class A entries from their canonical upstream sources on the locked cadence classes (high-velocity ≈ daily, long-form ≈ weekly; workspace-overridable) and emits a structured delta. | Inspect the scheduled binding + run one cycle against live sources. |
| AC.CLP-CUR.4 ★ | After the refresh machinery is live, a Claude Code capability change published upstream AFTER the seal appears in the corpus (or in a surfaced pending-delta) within one cadence cycle, with no manual trigger. | Wait one real cadence cycle post-seal against the live changelog; observe the delta. |
| AC.CLP-CUR.5 | Each Class A entry carries a fresh `source_fetch_ts`, and an entry whose source fetch fails is marked stale rather than silently retained as current. | Inspect entries post-refresh; simulate a fetch failure. |

### Slice 2 — DOCTRINE (`AC.CLP-DOC.*`)

| AC | Outcome | Verification |
|---|---|---|
| AC.CLP-DOC.1 | A loam-shipped, auto-discoverable surface exists that maps work-shapes to native Claude primitives (the catalogue/rubric the pos3 prototypes prove out), kept current by Slice 1's machinery or sourced from the corpus. | Skill(s) present in a shipped plugin; content traces to corpus entries. |
| AC.CLP-DOC.2 ★ | On the production dispatch/plan path, work that builds a bespoke equivalent of a catalogued primitive without a recorded primitive-consideration produces an observable check event (warn, block, or required-rationale — builder's call), with no pre-arranged state. | Author a deliberately-bespoke test dispatch; observe the check fire. |
| AC.CLP-DOC.3 | Plan-docs authored after the seal carry a named primitive-check section (the plan-time leg of the layered enforcement), and the convention doc says so. | Inspect convention doc + the next sealed plan-doc. |
| AC.CLP-DOC.4 | The check has an explicit escape hatch for the cases where bespoke IS correct, and using it leaves an audit-visible record. | Exercise the hatch; find the record. |

### Slice 3 — NAMED ADOPTIONS (`AC.CLP-ADOPT.*`)

| AC | Outcome | Verification |
|---|---|---|
| AC.CLP-ADOPT.1 | A recorded ruling exists for native-`/goal`-vs-`autonomy_continuation.py` (and any other bespoke keep-going overlap found), with the losing mechanism retired or its retention reason recorded. | Read the decision record; check the retired path. |
| AC.CLP-ADOPT.2 ★ | A keep-going work item started through loam's normal flow (e.g. the `handsoff-loop` methodology) drives via `/goal` on a real task with no pre-arranged state, halting when the goal condition is met. | Run a fixture build through the production flow; observe `/goal` artifacts. |
| AC.CLP-ADOPT.3 | A cadence-shaped in-session request ("check X every N minutes") routes to `/loop` per the catalogue, observable in the session record. | Issue the request shape; observe `/loop` invocation. |
| AC.CLP-ADOPT.4 | Class B corpus entries exist for both primitives capturing when-to-use vs siblings (`/goal` vs `/loop` vs `/schedule` vs background agents). | Read corpus entries. |

### Slice 4 — KNOWLEDGE CORPUS, PUSHED (`AC.CLP-PUSH.*`)

| AC | Outcome | Verification |
|---|---|---|
| AC.CLP-PUSH.1 | A curation pipeline produces a candidate weekly pack from the corpus (Class A currency + Class B synthesis), with every externally-sourced claim carrying a real citation and a curation gate before anything leaves the machine. | Run the pipeline; inspect a candidate pack + its gate record. |
| AC.CLP-PUSH.2 ⛔OWNER | The distribution channel exists publicly (per D-CLP.4) — created only on recorded owner approval. | Channel exists + the approval record predates it. |
| AC.CLP-PUSH.3 ★ | A loam workspace on another machine/user that performed no action beyond one-time setup has the updated knowledge available to its persona within one distribution cycle of an owner-approved publish. | Publish once (⛔OWNER); observe arrival on a second workspace with zero user action. |
| AC.CLP-PUSH.4 | The persona surfaces newly-arrived leverage knowledge per the Lens 0 vocabulary rule (substance exposed, wording tuned to the user), not as a raw changelog dump. | Observe the persona's surfacing on a fixture user profile. |
| AC.CLP-PUSH.5 | Nothing publishes off-machine without a recorded owner approval (per-publish initially; standing approval only if the owner explicitly ratifies it). | Audit the publish path for the gate; attempt an ungated publish in a test rig and observe refusal. |

---

## §6 Build steps (method-level guidance only; builder's call per ODD §1.1)

Each slice: sub-plan-doc + manifest authored first (plan-before-code), then
`loam amend apply` → build → seal per the amendment-cycle convention.

1. **Slice 1 — CURRENCY.** Sub-plan settles placement (new surface vs
   tools-adjacent). First commit can be the AC.CLP-CUR.1 fact-fix +
   CLAUDE_CAPABILITIES demotion (doc-only, immediately valuable). Scheduler
   binding: evaluate `/schedule` cloud routines first (Lens 1; gap-analysis
   flags `/web-setup` GitHub connection as the precondition — **verify live
   availability before committing to it**); fall back to the shipped
   `cron-create`/`launchd-plist` skills if cloud routines aren't viable on
   the subscription path. Locked-δ cadence table (§7bis.1) is the cadence
   spec; its graphiti/Stop-hook bindings are stale — do not carry them.
2. **Slice 2 — DOCTRINE.** Graduate the pos3 prototypes into
   `plugins/loam-skills` (merge/rename as fits); wire the structural check on
   the dispatch path; add the plan-doc primitive-check section to the
   conventions doc. The check must read the *current* corpus (Slice 1
   output), not a frozen list.
3. **Slice 3 — ADOPTIONS** (parallelizable with Slice 2). Run the
   `/goal`-vs-bespoke evaluation on a real fixture; record the ruling; update
   `handsoff-loop` + corpus accordingly.
4. **Slice 4 — PUSH.** Sub-plan likely decomposes further (curation pipeline
   / channel creation ⛔OWNER / bootstrap wiring / first publish ⛔OWNER).
   Verify marketplace auto-update semantics live (the v2.1.142 changelog line
   is admin-policy-flavored; the load-bearing question is whether a
   user-level added marketplace refreshes plugin content ~weekly with zero
   user action — if NO, D-CLP.4 falls to its fallback, see §10).

---

## §7 Out of scope

1. **β — the MCP knowledge-server** (locked design §7.2). Deferred, not
   dead: files-on-disk + skills serve the corpus today; β re-enters if/when
   corpus scale or cross-workspace retrieval demands it.
2. **γ — dynamic session-start capability contributor.** Post-corpus-
   stabilisation option per the locked design.
3. **`fallbackModel` adoption** — conflicts with the standing 2026-06-09
   model ruling; needs its own owner ruling, separate from this program.
4. **The wider gap-table adoptions** (`/btw`, `/fork`, Notification hook,
   `/batch`, `PostToolUseFailure`, etc.) — each is independently plannable
   per gap-analysis §6 Lens 3; the doctrine (Slice 2) is what will surface
   them organically. Folding them in would balloon the program (F4).
5. **Class B community-survey channel at full locked-δ scope** — Slice 4
   includes curation of best-current knowledge, but the weekly
   community-survey background-agent machinery ships only to the extent the
   Slice 4 sub-plan finds it affordable; otherwise it's the named follow-on.
6. **pos3 workspace cleanup** (retiring local prototypes after graduation) —
   workspace-side chore, tracked separately from canonical loam cycles.

---

## §8 Halt triggers (in-flight, per slice)

1. Any capability claim carried into a build fails live re-verification at
   build time (information-trust: the corpus is proven stale; every
   load-bearing claim re-fetches before code leans on it).
2. `/schedule` cloud routines turn out unavailable/unfit on the subscription
   path AND no shipped fallback scheduler fits → halt Slice 1, surface.
3. Marketplace auto-update cannot deliver ~weekly content updates with zero
   user action after setup → D-CLP.4's recommendation is void; halt Slice 4
   channel work, surface the fallback decision to the owner.
4. Any step about to perform a public action (repo creation, publish, feed
   exposure) without a recorded owner approval → hard stop (egress-consent
   floor; `AC.CLP-PUSH.5` is the test of this trigger).
5. A sub-plan discovers a genuine contradiction with the 2026-04-26 locked
   design that is NOT substrate-staleness (i.e., an intent-level conflict) →
   halt, owner rules (locked-design-not-license cuts both ways).
6. The doctrine check (Slice 2) blocks legitimate work twice in real use
   without the escape hatch resolving it → halt and redesign the check
   (over-tight enforcement is its own failure mode, F4).

---

## §9 Bookkeeping

- `docs/STATE.md` change-log entry per sealed slice.
- `docs/release-roadmap.md` §8 register: program entry + per-slice rows.
- `docs/FUTURE_IDEAS_DRAFT.md`: graduate F-CLAUDE-LEVERAGE-PROGRAM with a
  pointer to this plan (dispatcher-owned surface — flagged for the
  dispatcher, NOT edited by this plan's authoring per dispatch constraint).
- Locked-design doc gets a forward-pointer note (sub-plan time): "δ's intent
  realised by claude-leverage-program Slice 1; substrate re-derived."
- Each slice's manifest + §14 register per the plan-docs convention.

---

## §10 Named-decision register + F2 Ruthless Feedback

### Named decisions (recommendation IS the decision unless dispatcher/owner overrides)

**D-CLP.1 — Doctrine enforcement shape (leg 1).**
Alternatives: (a) advisory only — plan-doc section + skill content; (b)
structural only — dispatch-time hook; (c) layered: plan-time named section +
dispatch-time structural check + corpus-fed catalogue.
**Recommendation: (c) layered.** Evidence: doctrine-as-text already failed
repeatedly in this workspace (`feedback_structural_enforcement_on_recurrence`
is the named parent pattern; the microkernel already carries the check-first
trigger and the gap table still shows unused primitives). Advisory-only
repeats the failure; structural-only without the plan-time leg catches
violations too late (after the bespoke thing is designed). F4 confidence:
HIGH on the layering, MEDIUM on which hook event — builder's call.

**D-CLP.2 — Native `/goal` vs bespoke `autonomy_continuation.py` (leg 2).**
Alternatives: (a) keep bespoke, ignore native; (b) replace outright; (c)
native-first — `/goal` becomes the default keep-going mechanism, bespoke
retained only for shapes native can't express, with the overlap ruling
recorded.
**Recommendation: (c) native-first.** Evidence: `/goal` is shipped + supported
(changelog v2.1.139, verified 2026-06-11); the prefer-the-primitive doctrine
this very program installs would flag (a) as its first violation — the program
must not fail its own check. (b) is premature: the bespoke hook may cover
Stop-event shapes `/goal` doesn't. F4: MEDIUM (live-machinery interaction);
the Slice 3 evaluation is the confidence-raiser.

**D-CLP.3 — Currency mechanism: revive locked-δ scoped down vs redesign (leg 3).**
Alternatives: (a) redesign from scratch; (b) revive δ at full scope (incl. MCP
server + graphiti mirror); (c) revive δ's deterministic-projection core +
cadence table, defer β, re-derive substrate bindings.
**Recommendation: (c).** Evidence: the design intent was owner-locked
2026-04-26 and remains sound (the corpus structure it specified is the one on
disk and working); its substrate references are stale (graphiti retired per
the 2026-06-07 FBM rulings; persona paths renamed). Full-β revival (b) adds a
1–2-week server build the currency outcome doesn't need; redesign (a)
relitigates a locked decision without a bad-outcome reason. F4: HIGH.
**DELIVERED by Slice 1** (`docs/plans/claude-leverage-program-s1-currency.md`;
seal `c41f9473`, 2026-06-11): deterministic-projection core + cadence binding
shipped at `framework/tools/capability-refresh/`; substrate re-derived (cloud
routine primary — activation owner-gated pending — with launchd fallback).

**D-CLP.4 ★ — Distribution mechanism (leg 4; owner explicitly open to
alternatives; every public step ⛔OWNER).**
Alternatives evaluated:
- (a) **Version updates** (knowledge ships inside `loam-harness` releases) —
  REJECT as primary: couples knowledge cadence to code-release cadence;
  forcing weekly releases for doc content abuses the release gate chain and
  delays knowledge behind code QA.
- (b) **Plugin marketplace auto-update** — a loam-published knowledge plugin
  (skills-pack form: corpus-derived skills + docs) in a public marketplace
  repo; Claude Code refreshes marketplace content (auto-update policy surface
  exists per changelog v2.1.142; user-level semantics to verify live, §8.3).
- (c) **Skills-pack releases** standalone — same content as (b) but
  distributed as versioned artifacts; without a marketplace it inherits (a)'s
  pull problem.
- (d) **Published feed + scheduled per-workspace fetch routine** — full
  control, composes with Slice 1 machinery; but it is a bespoke pull loop
  wearing a push costume, exactly the shape the doctrine leg exists to
  prevent when a native channel exists.
**Recommendation: (b) marketplace auto-update**, with (d) as the named
fallback if §8.3's verification fails. Evidence: it is the only alternative
that is simultaneously Claude-native (Lens 1), decoupled from loam's release
cadence, and zero-user-action after one-time setup; and the program's own
distribution choosing the native primitive is the doctrine eating its own
cooking. Owner gates: channel creation (once), each publish (initially),
standing-approval (owner's explicit future option — never assumed). F4:
MEDIUM — hinges on the §8.3 live verification; the fallback is named so a NO
doesn't strand the slice.

**D-CLP.5 — `CLAUDE_CAPABILITIES.md` fate.**
Alternatives: (a) keep + refresh both surfaces; (b) delete; (c) demote to
index/redirect over the corpus.
**Recommendation: (c).** Evidence: the dual-surface arrangement is the
mechanism of the live failure (corpus seeded 2026-05; the 1038-line snapshot
kept being cited as the Lens-1 reference and went 7 weeks stale + wrong).
Deleting (b) breaks inbound references; refreshing both (a) doubles the
projection surface for zero reader value. F4: HIGH.
**DELIVERED by Slice 1** (seal `c41f9473`, 2026-06-11): demoted in place to a
65-line index/redirect; exactly one canonical reference surface remains.

### F2 — honest doubts, named

1. **"Pushed without pulling" is an approximation.** On a local-first CLI,
   every mechanism — marketplace refresh included — is an automated fetch
   under the hood. The defensible claim is *zero user action after one-time
   setup*, and AC.CLP-PUSH.3 tests exactly that, no more. If the owner's
   intent is stronger (true server-push), no current Claude-native channel
   provides it; that gap is named rather than papered over.
2. **A disposition can't be fully enforced.** "Always knows about and
   prefers" is a behavioral disposition; Slice 2's checks sample the
   observable surfaces (plan-time, dispatch-time). A bespoke-equivalent built
   *inside* a single uninstrumented turn can evade both. Coverage-widening
   (e.g., LLM-judge probes per the EVAL_DIMENSIONS pattern) is possible
   follow-on work, not promised here.
3. **Weekly curation has a recurring cost + an owner-attention cost.** The
   per-publish owner gate is the right floor for a public action, but it puts
   the owner on a weekly cadence. If that becomes friction, the
   standing-approval option exists — the plan deliberately does not
   pre-decide it.
4. **`/schedule` cloud-routine availability is HYPOTHESISED, not verified**
   (gap-analysis §5 says the same). Slice 1's scheduler choice carries a
   named fallback so this doubt can't block the slice.
5. **Slice 4 may be under-sliced.** It bundles curation + channel + wiring +
   first publish. The master plan licenses its sub-plan to decompose further
   (Lens 5); treating it as one cycle would be the scope-realism miss.
6. **Self-application gap risk.** loam (the product) shipping doctrine skills
   that pos3 (the dev workspace) already had hand-rolled means two divergent
   copies during the transition. The graduation step must end with one
   canonical copy or the program recreates the dual-surface failure it fixes
   (D-CLP.5's lesson, applied to skills).

---

## §11 Provenance trail

- Owner directive: Discord 1514741531687256226 (2026-06-11), captured at
  `docs/FUTURE_IDEAS_DRAFT.md` § F-CLAUDE-LEVERAGE-PROGRAM (read 2026-06-11;
  dispatcher-owned, unmodified).
- Gap analysis (Tier-0, same-day):
  `/Users/lukeivers/pos3/workspace/.scratch/claude-output/claude-primitives-gap-analysis-2026-06-11.md`.
- Plan-author live re-verification (2026-06-11, WebFetch):
  `https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md`
  — sub-agent recursion to 5 levels @ v2.1.172; `/goal` @ v2.1.139; `/loop`
  fix @ v2.1.163; `extraKnownMarketplaces` auto-update policy @ v2.1.142;
  latest listed 2.1.173.
- Locked design:
  `docs/plans/research/persona-capability-knowledge-grounding-research.md`
  (§2.6, §7, §7bis — locked by Luke 2026-04-26); shipped-α evidence at
  `docs/plans/claude-code-corpus-prompt-spine-and-seed-docs.md` +
  `docs/capability-corpus/` (read 2026-06-11).
- Stale snapshot: `docs/CLAUDE_CAPABILITIES.md` (header: snapshot 2026-04-23;
  1038 lines; §7.7 recursion claim contradicted by changelog).
- Conventions + shape exemplars:
  `plugins/dev-sdlc/docs/conventions/plan-docs.md`;
  `docs/plans/context-management-see-budget-eviction-master.md` (master-plan
  shape, no-manifest precedent);
  `docs/plans/conventional-install-pypi-publish.md` (distribution-model
  context: PyPI `loam-harness`).
- Prime objective: `docs/VALUE_PROPOSITION.md` (AC.PO.1/AC.PO.2 framing).
- Memory corpus patterns cited: `feedback_structural_enforcement_on_recurrence`,
  `feedback_workaround_masks_rootcause_urgency`,
  `feedback_locked_design_not_license_for_bad_outcomes`,
  `feedback_version_numbers_at_release_time`,
  `feedback_scope_descriptive_ac_ids`, `feedback_test_outcome_altitude_required`.
