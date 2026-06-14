# Claude-leverage program Slice 3 — NAMED ADOPTIONS: `/goal` + `/loop` in consistent, observable use (sub-plan-doc)

> **Status:** SUB-PLAN-DOC (ODD-shaped). Third of four slices under the
> master plan `docs/plans/claude-leverage-program.md`. PLAN ONLY — no build
> dispatched off this doc; the manifest pairs with this plan and drives the
> build cycle.
> **WD:** `/Users/lukeivers/loam` (canonical loam).
> **Parent plan:** `docs/plans/claude-leverage-program.md` §Slice-3 (AC.CLP-ADOPT.\*),
> §2 placement table row 5, D-CLP.2 register entry (RULED: native-`/goal`
> first, bespoke retained only where native can't reach).
> **Predecessors (load-bearing):**
> - **Slice 2 — DOCTRINE, sealed `f308b398`** (2026-06-12): ships the
>   prefer-the-primitive doctrine made operational — the dispatch-time
>   `primitive_check_guard.py` PreToolUse `Task` hook + its
>   `primitive_check_matchers.py` ROWS table + the graduated skill trio in
>   `plugins/loam-skills/`. **Slice 3 is the worked example of that doctrine:**
>   `/goal`+`/loop` are the owner-named adoption targets, and the guard's
>   matcher table currently has NO row for the bespoke-keep-going work-shape
>   that `/goal` covers (verified: `primitive_check_matchers.py` ROWS cover
>   schedule / loop / background-agents only). Slice 3 closes that coverage gap.
> - **Slice 1 — CURRENCY, sealed `c41f9473`** (2026-06-11): the
>   `docs/capability-corpus/` is the one refresh-kept claims surface. The
>   corpus already carries `claude-code/loop.md`; it carries **no**
>   `claude-code/goal.md` (verified). Slice 3 adds the `/goal` Class B entry
>   and the `/goal`-vs-`/loop` disambiguation, both refresh-kept thereafter.
> - **Existing surfaces graduated/extended:** `plugins/loam-skills/skills/{goal-command,loop-command,handsoff-loop}/SKILL.md`
>   (read 2026-06-14 — `goal-command` already documents `/goal` as the
>   keep-going leg of `handsoff-loop`; the gap is consistent *use* + the
>   recorded bespoke-overlap ruling, not the skill text).
> - **pos3 bespoke machinery under evaluation (read-only reference):**
>   `/Users/lukeivers/pos3/.claude/hooks/autonomy_continuation.py` (read
>   2026-06-14 — analysed in D-ADOPT.1; it is a Stop-hook idle-recovery
>   *queue dispatcher*, NOT a drive-to-goal mechanism — the disposition turns
>   on that distinction).
> **BASELINE candidate:** the Slice-2 seal `f308b398` is the load-bearing
> predecessor; the manifest names HEAD-of-main at apply time and the builder
> CONFIRMS against the live tip + counter (`feedback_version_numbers_at_release_time`).
> **Status-file target:** `docs/STATE.md` change-log + `docs/release-roadmap.md`
> §8 register row.
> **Quality bar:** every AC outcome-shaped; ≥1 outcome-altitude AC (★);
> method stays the builder's call per ODD §1.1; versions derive at release
> time — no version number pre-assigned anywhere in this doc.
> **Live-verification stamp (information-trust, 2026-06-14, WebFetch
> `anthropics/claude-code` CHANGELOG):** `/goal` @ v2.1.139 ("set a completion
> condition and Claude keeps working across turns until it's met; works in
> interactive, `-p`, and Remote Control; shows live elapsed/turns/tokens"),
> hook-interaction fix @ v2.1.141, idle-render + parallel-subagent fix @
> v2.1.152; `/loop` fixes @ v2.1.141 (redundant-wakeup) + v2.1.152 (remote
> de-promotion); latest CC version **2.1.176** (was 2.1.173 at master-plan
> time). No changelog entry contradicts any claim this plan leans on.

---

## §1 Objective

`/goal` and `/loop` are in consistent, observable use as loam's reach for
their respective work-shapes (drive-to-checkable-outcome; in-session
recurring/self-paced), the bespoke-keep-going overlap with pos3's
`autonomy_continuation.py` is RULED and recorded, and the doctrine check
shipped in Slice 2 covers the `/goal` work-shape so a future bespoke
keep-going re-implementation is caught on the production dispatch path —
making this slice the doctrine eating its own cooking.

---

## §2 Predecessors / context

| Predecessor | SHA | What Slice 3 consumes from it |
|---|---|---|
| Slice 2 — DOCTRINE | `f308b398` | The `primitive_check_guard.py` + `primitive_check_matchers.py` ROWS table Slice 3 extends with a `/goal` row; the graduated `goal-command` / `loop-command` skills; the plan-time Primitive-check convention this plan conforms to (§2bis). |
| Slice 1 — CURRENCY | `c41f9473` | `docs/capability-corpus/` as the one refresh-kept claims surface; the existing `claude-code/loop.md`; the entry shape Slice 3's `goal.md` matches. |
| Master plan | `claude-leverage-program.md` | D-CLP.2 RULED (native-first); §2 placement (EXTEND existing skills + corpus Class B); the AC.CLP-ADOPT.\* family. |

**Why this slice exists (Lens 1 made concrete).** Re-implementing a worse
bespoke equivalent of a maintained Anthropic primitive is a default AI
betrayal (master §4). `/goal` is a shipped, supported, maintained keep-going
primitive (changelog-verified). The doctrine the program installs would flag
"ignore native, keep bespoke" as its first violation; this slice ensures the
program does not fail its own check, and demonstrates the check working on a
real adoption.

---

## §2bis Primitive check (REQUIRED — per the Slice-2 convention)

Slice 3 introduces **one** new mechanism: a matcher row added to the
Slice-2 dispatch-time guard, covering the bespoke-keep-going work-shape.

| New mechanism | Native primitive considered | Chosen | Rationale |
|---|---|---|---|
| Catch bespoke "keep-going / drive-to-goal / re-run-until-done" dispatches on the production path | The Slice-2 `primitive_check_guard.py` PreToolUse `Task` hook + its `primitive_check_matchers.py` ROWS table (the native dispatch-time-check primitive already shipped) | **EXTEND the Slice-2 guard** — add a `goal.md`-keyed matcher row; do NOT build a new hook | The guard primitive already exists and is the correct surface; a new hook would be the exact bespoke re-implementation the doctrine forbids. Adding a row is data, not a new mechanism-class. |
| The `/goal` and `/loop` adoption surfaces themselves | `/goal`, `/loop` (the native Claude Code slash commands) | **The native primitives** — this slice's whole objective is their adoption | No bespoke equivalent authored anywhere in this slice. |

No other new mechanism is introduced. The `goal.md` corpus entry, the
`/goal`-vs-`/loop` disambiguation, the recorded D-ADOPT.1 ruling, and the
`handsoff-loop` cross-reference are content/documentation, not mechanisms.

---

## §3 Scope

### In scope

1. **The native-`/goal`-vs-bespoke-`autonomy_continuation.py` ruling**, recorded
   durably, with the losing mechanism retired OR its retention reason recorded
   (D-ADOPT.1). Includes a sweep for any OTHER bespoke keep-going overlap in
   loam-proper (not pos3 — see boundary note below).
2. **The `/goal` Class B corpus entry** (`docs/capability-corpus/claude-code/goal.md`),
   matching the existing entry shape, capturing when-to-use `/goal` vs `/loop`
   vs `/schedule` vs background agents — and the `/loop` entry gains the
   reciprocal `/goal` disambiguation it currently lacks (AC.CLP-ADOPT.4).
3. **The doctrine-check coverage extension:** a `goal.md`-keyed matcher row in
   `primitive_check_matchers.py` so the Slice-2 guard fires on a bespoke
   keep-going dispatch — closing the coverage gap and making the slice the
   doctrine's worked example. The Slice-2 bidirectional coverage guard (corpus
   ↔ matcher) keeps the new `goal.md` from drifting uncovered.
4. **The observable-use surface** for `/goal`: a fixture keep-going work item
   started through loam's normal flow (the `handsoff-loop` methodology) drives
   via `/goal` on a real task with no pre-arranged state, halting when the goal
   condition is met, with the `/goal` artifacts observable in the run record
   (AC.CLP-ADOPT.2 ★).
5. **The observable-use surface** for `/loop`: a cadence-shaped in-session
   request ("check X every N minutes") routes to `/loop` per the catalogue,
   observable in the session/skill record (AC.CLP-ADOPT.3).
6. **`handsoff-loop` SKILL alignment** with the recorded ruling, if the ruling
   changes anything the skill states (it already names `/goal` as its
   keep-going leg — the likely edit is a back-reference to the D-ADOPT.1
   record, not a behavior change).

### Out of scope (deferred, with when)

1. **Retiring or modifying `autonomy_continuation.py` itself.** It lives in the
   **pos3 workspace**, not canonical loam; canonical-loam cycles do not edit
   pos3 (master §7.6 names pos3 cleanup as a workspace-side chore tracked
   separately). The RULING is in scope; the pos3 edit is not — the ruling
   records the disposition, the pos3 chore executes it if the ruling retires it.
   **D-ADOPT.1 rules KEEP-BOTH-SCOPED, so no pos3 retirement is implied** (see
   §10) — this boundary matters only as the halt-trigger guard.
2. **`/goal` / `/loop` matcher rows beyond the one keep-going row.** `/loop`'s
   poll/cadence shape is already covered by the Slice-2 `loop.md` rows; Slice 3
   adds only the missing `/goal` keep-going row.
3. **The runtime/persona-path doctrine check** for NORMAL-USE workspaces
   (master §2 row 4 "second" — its own future cycle).
4. **Wider gap-table primitive adoptions** (`/btw`, `/fork`, etc. — master §7.4).
5. **Any `/goal` / `/loop` core-behavior change.** These are Anthropic-maintained
   primitives; Slice 3 adopts, never forks them.

### Boundary note (the canonical-vs-pos3 line — load-bearing)

The master plan's D-CLP.2 names `autonomy_continuation.py` as the bespoke
overlap to evaluate. That file is pos3-local. The **evaluation + ruling** is
canonical-loam work (it is a recorded design decision about loam's keep-going
posture). The **execution of a retirement**, were one ruled, is a pos3
workspace chore. Because D-ADOPT.1 rules KEEP-BOTH-SCOPED (§10), no pos3 edit
is triggered — but the plan names the line so a builder who reads the ruling
differently halts (§6 trigger 2) rather than reaching into pos3.

---

## §4 Acceptance criteria

Family `AC.CLP-ADOPT.*` (scope-descriptive per `feedback_scope_descriptive_ac_ids`).
★ = outcome-altitude (production entry-point, no pre-arranged state). Every AC
passes the method-in-AC test: a method other than the one the author has in
mind can satisfy it.

| AC | Outcome | Verification |
|---|---|---|
| **AC.CLP-ADOPT.1** | A durable recorded ruling exists for native-`/goal`-vs-`autonomy_continuation.py` (and any other bespoke keep-going overlap found in loam-proper), stating the disposition (replace / complement / keep-both-scoped) and, for any mechanism the ruling retires, the retirement is executed or its non-execution reason recorded; for any mechanism retained, the retention reason is recorded. | Read the decision record; for each named mechanism, confirm its disposition is stated and its retire/retain reason recorded. |
| **AC.CLP-ADOPT.2 ★** | A keep-going work item started through loam's normal production flow (the `handsoff-loop` methodology) drives via `/goal` on a real task with **no pre-arranged state**, and halts when the goal condition is met. | Run a fixture build through the production `handsoff-loop` flow with no seeded `/goal` state; observe `/goal` artifacts in the run record and a clean halt at goal-met. |
| **AC.CLP-ADOPT.3** | A cadence-shaped in-session request ("check X every N minutes" / "poll until Y") routes to `/loop` per the catalogue, observable in the session or skill record. | Issue the request shape against the catalogue/skill surface; observe the `/loop` routing in the record. |
| **AC.CLP-ADOPT.4** | Class B corpus entries exist for both primitives capturing when-to-use vs siblings: a `/goal` entry exists (currently absent) and the `/loop` entry carries the reciprocal `/goal` disambiguation (currently absent); both name the `/goal` ↔ `/loop` ↔ `/schedule` ↔ background-agents decision boundaries. | Read `docs/capability-corpus/claude-code/goal.md` (exists, sibling-disambiguation present) + `loop.md` (now references `/goal`). |
| **AC.CLP-ADOPT.5** | The Slice-2 dispatch-time doctrine guard fires on a bespoke keep-going dispatch: a deliberately-bespoke "build a keep-going / drive-to-done loop" dispatch prompt, with no recorded primitive-rationale, produces the guard's observable check event naming `/goal`, with no pre-arranged state. | Author a deliberately-bespoke keep-going test dispatch; observe the guard's check event (deny/warn) naming `/goal` + its `goal.md` corpus entry; confirm the Slice-2 corpus↔matcher coverage guard stays green. |

**AC ladder-up (per `feedback_value_proposition_as_prime_objective`).**
AC.CLP-ADOPT.\* → master AC.CLP.2 (each leg's slice sealed + family green) →
AC.PO.2 (the protection floor: not re-implementing a worse bespoke equivalent
of a maintained primitive) + Lens 1 hardened. AC.CLP-ADOPT.2 ★ additionally
serves AC.PO.1 (the persona reaches for the right primitive without the user
knowing primitives exist).

**Outcome-altitude declaration (`feedback_test_outcome_altitude_required`).**
AC.CLP-ADOPT.2 is the ★ outcome-altitude AC: it invokes the production
`handsoff-loop` entry-point with no pre-arranged `/goal` state. AC.CLP-ADOPT.5
is a second no-pre-arranged-state AC (production dispatch path). STUB-class
tests do not satisfy either; both require the real production surface.

---

## §5 Sealed-component fence

| Component | Why in fence | Surface touched |
|---|---|---|
| **dev-sdlc** | The doctrine-check coverage extension (§3.3) — one matcher row + its coverage in the Slice-2 guard's test suite. | `plugins/dev-sdlc/hooks/primitive_check_matchers.py` (+ the guard's existing test suite extension for the new row + AC.CLP-ADOPT.5). |
| **loam-skills** | The `goal.md` + `loop.md` corpus-adjacent skill alignment IF the `handsoff-loop` / `goal-command` / `loop-command` SKILLs need a back-reference to the D-ADOPT.1 record; corpus entries live under `docs/` (universal), but any skill-text edit is here. | `plugins/loam-skills/skills/{handsoff-loop,goal-command,loop-command}/SKILL.md` (back-reference edits only, if any). |

**`docs/capability-corpus/` admission — builder's call at manifest time.**
The `goal.md` creation + `loop.md` edit are corpus content. Slice 2's manifest
held the corpus OUT of its fence (a corpus discrepancy there surfaced as a
Slice-1 pending-delta, never a silent edit) because Slice 2 *consumed* the
corpus. Slice 3 *authors* corpus Class B entries as its explicit deliverable
(AC.CLP-ADOPT.4) — so the corpus MUST be admitted to this fence (either as a
component or a universal-prefix admission). **Recommendation: admit
`docs/capability-corpus/` as a universal prefix** in the Slice-3 manifest, since
the entries are authored content this slice owns, not a consumed surface. This
is the one fence decision that differs from Slice 2 and the builder confirms it
at manifest time. **Halt trigger 3 guards the inverse:** if the build finds a
corpus *claim* (not the new entries) that is wrong, that is still a Slice-1
pending-delta, not a silent edit.

The decision-record location (AC.CLP-ADOPT.1) is the builder's call between
the plan-doc §14 register, a `docs/` decision note, or both; whichever it is
must be durable and named in §9.

---

## §6 Halt triggers (in-flight)

1. **`/goal` or `/loop` live re-verification fails at build time.** Any
   capability claim this plan carries (the §0 live-verification stamp) that
   fails re-fetch against the live changelog at build time → halt, surface, do
   not author against the stale claim (master §8.1; information-trust).
2. **A builder reads D-ADOPT.1 as retire-`autonomy_continuation.py`.** The
   ruling is KEEP-BOTH-SCOPED (§10); if a build path concludes the bespoke hook
   should be retired, that crosses into pos3 (out of fence, §3 boundary note)
   AND contradicts the recorded ruling → halt, surface to owner (this is the
   master §8.5 intent-conflict trigger + the brief's explicit halt-and-surface:
   "a disposition that would weaken the proven pos3 autonomy machinery").
3. **A corpus *claim* (not the new entries) is found wrong at build.** Surface
   as a Slice-1 pending-delta question (master §8.1), never a silent corpus
   edit outside the new `goal.md` / `loop.md`-disambiguation deliverables.
4. **The fixture `/goal` run (AC.CLP-ADOPT.2 ★) cannot reach no-pre-arranged-
   state honestly** (e.g. the only way to make it pass is to seed `/goal`
   state) → halt; an outcome-altitude AC satisfied by pre-arranged state is a
   false pass (`feedback_test_outcome_altitude_required`).
5. **The new `goal.md` matcher row makes the Slice-2 guard block legitimate
   work** in the build's own test corpus (a true-keep-going dispatch that
   SHOULD use `/goal` is fine to flag; a non-keep-going dispatch wrongly
   matched is a false positive) → tune the row's precision; if it cannot be
   made precise without either over-matching or missing the real shape → halt
   and surface (master §8.6 over-tight-enforcement trigger).
6. **Any public-action step.** This slice is LOCAL-only; nothing publishes,
   creates a repo, or exposes a feed. A step about to do so → hard stop
   (egress-consent floor).

---

## §7 Ship shape

Single amendment cycle (the slice is honest single-cycle work — master §1.1
estimate 30–90 min AI-time). Commit ladder per the amendment-cycle convention:
plan + manifest committed first (this pair, docs-only), then `loam amend apply`
→ source edits → tests → seal. First substantive commit can be the
`goal.md` corpus entry + `loop.md` disambiguation (doc-only, immediately
valuable, AC.CLP-ADOPT.4). The D-ADOPT.1 ruling record lands early too (it
gates nothing downstream and is the slice's design spine).

---

## §8 Risks / test scope

- **AC.CLP-ADOPT.2 ★ is the real-build risk.** It runs a fixture through the
  production `handsoff-loop`, which dispatches a real `claude -p` sub-agent with
  `/goal` driving the keep-going leg. The fixture must be small enough to run in
  the build window but real enough that `/goal` actually iterates (a checkable
  success predicate that takes ≥2 iterations). The builder picks the fixture;
  the constraint is no-pre-arranged-`/goal`-state + observable artifacts.
  NO Anthropic API key (`feedback_no_anthropic_api_key`); the `/goal` leg runs
  through the real `claude` binary, default Sonnet.
- **The matcher-row precision risk** (halt trigger 5). The Slice-2 ROWS use
  build-verb + primitive-shape proximity regexes; the `/goal` row follows the
  same shape (build-verb like "build/write/implement" + keep-going-shape like
  "keep going until / drive to / re-run until done / continuation loop / Stop
  hook that re-fires"). The `warn`-tier (shape alone) vs `deny`-tier (build-verb
  + shape) two-tier posture from Slice 2 applies unchanged.
- **Backwards-compat (§15):** the Slice-2 guard suite, the corpus↔matcher
  coverage guard, and the loam-skills derived-from-disk suites must stay green.

---

## §14 Method-decision register (populated at build/seal time)

This register is the **durable recorded ruling** AC.CLP-ADOPT.1 contracts
for (the Slice-2 precedent: the §14 register is the durable record, not a
separate `docs/` note). Each row states the disposition + the retain/retire
reason for every named mechanism; SHAs backfilled at seal.

| ID | Decision | Builder narrative (at build) | SHA (at seal) |
|---|---|---|---|
| **D-ADOPT.1** | native-`/goal` vs bespoke `autonomy_continuation.py` disposition → **KEEP-BOTH-SCOPED** (RULED). | **Disposition: keep-both-scoped.** **`/goal` (native) — RETAINED as the default keep-going leg** for single-task drive-to-checkable-outcome; reason: it is a shipped, maintained Anthropic primitive (changelog v2.1.139, local binary 2.1.174 carries it — Tier-0 verified) and is ALREADY the keep-going leg of `handsoff-loop` (`goal_drive.build_goal_drive_argv`). **`autonomy_continuation.py` (pos3 bespoke) — RETAINED, NOT retired**; reason: read off the actual hook 2026-06-14 it is a Stop-event idle-recovery *queue dispatcher* over a durable cross-turn `workstream-queue.yaml` (token-delta + task-count safety caps, owner-class exclusion) — a distinct work-shape `/goal` does not express ("pick the next item off a durable cross-turn queue" ≠ "drive THIS task to THIS predicate"). The two do not overlap on the load-bearing axis, so neither is retired; the boundary is stated and recorded. **NO pos3 edit triggered** (keep = no retirement; the pos3 file is out of the canonical fence — §3 boundary note). **Sweep:** no other bespoke keep-going re-implementation found in loam-proper (the only overlap is the dispositioned pos3 hook). Full rationale + F2 flip-condition in §17 D-ADOPT.1. | `59c85aa8` |
| **D-ADOPT.2** | `goal.md` matcher-row precision tier (deny/warn boundary). | Two rows added to `primitive_check_matchers.ROWS`: `bespoke-keep-going-loop` (**deny** — `_BUILD_VERB` + a NARROW keep-going lexicon: `keep going until` / `drives? … to done\|goal\|completion` / `re-run until done\|pass\|green` / `iterate\|loop … until … test\|check\|build\|goal\|predicate` / `continuation loop\|driver` / `Stop hook … re-fires` / `drive-to-goal\|done\|outcome loop`) and `keep-going-shape` (**warn** — the keep-going phrase alone). Deliberately NARROW per F2.4 / halt-trigger-5: requires an explicit drive-to-done/keep-going-until phrase, NOT a bare "loop" — so cadence/poll "loop" stays loop.md's jurisdiction and prose "for loop" does not match. Precision verified against a deny-corpus + a should-not-match corpus (poll-loop / scheduler / orchestrator / "drive the motor to position" / plain prose all correctly NOT attributed to `/goal`). Coverage guard (AC.CLP-DOC.8) green: `goal.md` covered by the row, row pointer resolves. | `59c85aa8` |
| **D-ADOPT.3** | corpus fence admission (universal-prefix vs component). | **Universal-prefix admission** confirmed at apply: `docs/capability-corpus/` added to the manifest `universal_paths.prefixes` (alongside `docs/plans/`). Reason: Slice 3 AUTHORS Class B corpus entries as its explicit AC.CLP-ADOPT.4 deliverable (`goal.md` creation + `loop.md` `/goal` disambiguation) — author-vs-consume, the one fence call differing from Slice 2 (which held the corpus OUT because it consumed it). Halt-trigger-3 guard intact: a wrong corpus *claim* outside the new entries would still surface as a Slice-1 pending-delta, never a silent edit. | `59c85aa8` |
| **D-ADOPT.4** | graduate nothing from pos3 to loam-proper in Slice 3. | Confirmed: nothing graduated. The keep-going leg loam-proper needs is `/goal` (native) + the existing `handsoff-loop` orchestration, both already in loam-proper; the pos3 queue-dispatcher is workspace-autonomy machinery, not a product capability, and graduating it would be scope-creep beyond the owner-named `/goal`+`/loop` targets. | `59c85aa8` |

**Seal:** apply `4d896f19`; seal `59c85aa8` (dev-sdlc + loam-skills).
All 5 AC.CLP-ADOPT.* GREEN at seal.

---

## §15 Backwards-compat verification

- Slice-2 `primitive_check_guard.py` suite + `primitive_check_matchers.py`
  bidirectional corpus↔matcher coverage guard: green after the new `/goal` row.
- `plugins/loam-skills/` derived-from-disk suites (LSK/SKTRI): green after any
  SKILL back-reference edits.
- The existing `claude-code/loop.md` corpus entry's refresh-binding (Slice-1
  machinery) still resolves after the disambiguation edit (the edit is body
  content; the `Source` block + `source_fetch_ts` stay intact).

---

## §16 Halt-and-surface findings (recorded at plan-authoring)

1. **`autonomy_continuation.py` is NOT a `/goal` analog — it is a queue
   dispatcher** (the finding that decides D-ADOPT.1). Read 2026-06-14: it is a
   Stop-hook that fires on idle turn-ends, reads a durable cross-turn
   `workstream-queue.yaml`, picks the next eligible (non-owner-class,
   unblocked) item, and injects a continuation directive — with token-delta
   and task-count safety caps. `/goal` is single-task drive-to-checkable-
   predicate with autonomous halt. These are **different work-shapes**: `/goal`
   = "drive THIS task to THIS success state"; autonomy_continuation = "when
   idle with queued work, pick up the next workstream." `/goal` does not
   express durable cross-turn queue dispatch. This is why D-ADOPT.1 rules
   KEEP-BOTH-SCOPED, not replace. Surfaced because the master plan's D-CLP.2
   phrasing ("`/goal` becomes the default keep-going mechanism, bespoke
   retained only for shapes native can't express") could be misread as
   "replace"; the evidence says native-first for the *single-task* keep-going
   leg, bespoke retained for the *queue-dispatch* shape it uniquely covers.

2. **Method-in-AC test passed for all five ACs.** Naming `/goal`/`/loop` is the
   *objective* (owner-named adoption targets — master §3.2), not method-in-AC.
   Each AC is satisfiable by a method other than the recommended one (e.g.
   AC.CLP-ADOPT.1's record could be plan §14 OR a docs note; AC.CLP-ADOPT.5's
   check could deny OR warn — builder's call).

3. **Fence differs from Slice 2 on the corpus** (recorded in §5). Slice 2 held
   the corpus out (it consumed it); Slice 3 authors corpus entries as a
   deliverable, so the corpus is admitted. Surfaced because silently
   re-admitting a surface a sibling slice deliberately excluded would be a
   fence-drift if unexplained; the reason (author-vs-consume) is the
   justification.

4. **No FIDRAFT-vs-master contradiction** found; the master's §5 AC.CLP-ADOPT.\*
   family is carried forward verbatim in shape, tightened per-AC for the build.

---

## §17 Named-decision register + F2 Ruthless Feedback

### Named decisions (recommendation IS the decision unless dispatcher/owner overrides)

**D-ADOPT.1 — native-`/goal` vs bespoke `autonomy_continuation.py` disposition
(the master's D-CLP.2 made precise; the slice's load-bearing call).**
Alternatives: (a) **replace** — retire `autonomy_continuation.py`, route all
keep-going through `/goal`; (b) **complement** — `/goal` for single-task
keep-going, bespoke for everything else, both fully live; (c) **keep-both-
scoped** — `/goal` is the default keep-going leg for single-task
drive-to-checkable-outcome (it already is, inside `handsoff-loop`);
`autonomy_continuation.py` is retained ONLY for its distinct shape (durable
cross-turn workstream-queue dispatch on idle), with that retention reason
recorded and the boundary between the two stated.
**Recommendation: (c) keep-both-scoped.**
*Evidence (Tier-0, read the actual hook 2026-06-14,
`/Users/lukeivers/pos3/.claude/hooks/autonomy_continuation.py`):* the hook is a
Stop-event idle-recovery dispatcher over `workstream-queue.yaml` — it does not
drive a single task to a checkable predicate; it picks the next queued
workstream when the persona goes idle with work remaining, gated by
token-delta + task-count safety caps and owner-class scope exclusion. `/goal`
(changelog v2.1.139, live-verified 2026-06-14) is the inverse shape:
single-task, checkable completion condition, autonomous halt-on-met. They
**do not overlap on the load-bearing axis** — `/goal` cannot express "pick the
next item off a durable cross-turn queue." (a) replace would **weaken proven
machinery** (the brief's explicit halt-and-surface tradeoff — the queue
dispatcher has token-cap safety the persona relies on) AND delete a capability
`/goal` does not provide. (b) complement is nearly right but leaves the
boundary unstated, which invites the next agent to silently re-derive it. (c)
states the boundary, adopts the native primitive for the leg it fits, and
keeps the bespoke hook for the leg it uniquely covers — which is exactly the
prefer-the-primitive doctrine applied honestly (prefer the primitive *where it
reaches*; the doctrine never said "delete every bespoke thing"). **F4: HIGH**
(the shape distinction is empirical, read off the code, not inferred). **No
pos3 edit is triggered by this ruling** (keep = no retirement); the boundary
note in §3 guards a misread.
*Sweep result:* in loam-proper, `/goal` is already the keep-going leg of
`handsoff-loop` (verified in `goal-command`/`handsoff-loop` SKILLs) — no other
bespoke keep-going re-implementation found in canonical loam. The only bespoke
overlap is the pos3 hook, dispositioned above.

**D-ADOPT.2 — what "observable use" means as a checkable AC.**
Alternatives: (a) a usage *signal* (telemetry that `/goal` was invoked); (b) a
*skill/catalogue routing* that maps keep-going requests to `/goal`; (c) a
*doctrine doc + worked example*; (d) the *production-flow artifact* — a real
`handsoff-loop` run whose record shows `/goal` drove the keep-going leg and
halted at goal-met.
**Recommendation: (d) production-flow artifact, as the ★ outcome-altitude AC
(AC.CLP-ADOPT.2)** — backed by (b) the catalogue routing (the `goal.md` corpus
entry + the matcher row that catches the bespoke alternative).
*Evidence:* "observable use" is strongest when it is the production entry-point
producing an artifact with no pre-arranged state (`feedback_test_outcome_
altitude_required`); `handsoff-loop` already uses `/goal` internally as its
keep-going leg (verified in the SKILL), so the production path exists — the AC
just exercises it and observes the artifact. A usage *signal* (a) is weaker (it
proves invocation, not that the production flow reaches for it); a doc (c) alone
repeats the doctrine-as-text failure the program exists to fix. F4: HIGH.

**D-ADOPT.3 — `/loop`'s adoption surface (the routing point).**
Alternatives: (a) a new hook that intercepts cadence-shaped requests; (b) the
existing `loop-command` SKILL + the `loop.md` corpus entry as the catalogue the
persona consults; (c) the Slice-2 matcher guard (already covers the bespoke
poll-loop shape).
**Recommendation: (b) the existing skill + corpus catalogue is the routing
point; (c) the Slice-2 guard already covers the bespoke alternative — no new
mechanism for `/loop`.**
*Evidence:* `/loop`'s skill exists and its corpus entry exists (verified); the
Slice-2 matcher already DENY/warns a bespoke poll-loop and names `/loop`. So
`/loop`'s adoption is already structurally enforced on the bespoke side and
catalogued on the reach-for side — AC.CLP-ADOPT.3 verifies the catalogue
routing works, not that a new mechanism is built. Building a new `/loop`
interceptor (a) would itself be a bespoke re-implementation the doctrine
forbids. F4: HIGH. This is why `/loop`'s slice work is lighter than `/goal`'s:
`/goal` had a coverage GAP in the matcher (no row) + no corpus entry; `/loop`
had both already.

**D-ADOPT.4 — does anything graduate from pos3 to loam-proper in this slice?**
Alternatives: (a) graduate `autonomy_continuation.py` into loam-proper; (b)
graduate nothing.
**Recommendation: (b) graduate nothing in Slice 3.**
*Evidence:* the keep-going leg loam-proper needs is `/goal` (native) + the
existing `handsoff-loop` orchestration — both already in loam-proper. The pos3
queue-dispatcher is a *workspace-autonomy* mechanism (it dispatches the next
queued workstream on idle), not a *product* capability loam ships to users;
graduating it would be scope-creep beyond the owner-named adoption targets
(`/goal`+`/loop`). If a future cycle wants a shipped workspace-autonomy
primitive, that is its own plannable feature (and would itself face the
prefer-the-primitive check against `/goal` + `/schedule` + `/loop`). F4: HIGH.

### F2 — honest doubts, named

1. **D-ADOPT.1's keep-both-scoped could read as not-fully-committing to the
   doctrine.** The honest tension: a maximalist reading of prefer-the-primitive
   says "retire the bespoke thing." The evidence-based reading says "the bespoke
   thing covers a shape the primitive doesn't." I am choosing the
   evidence-based reading and naming it so the owner can overrule toward
   maximalism if the queue-dispatch shape is judged not-worth-keeping. The flip
   condition: if the owner decides the cross-turn queue-dispatch behavior should
   itself be expressed via `/goal` + a native queue primitive (none currently
   exists — verified), D-ADOPT.1 flips to (a) replace and the pos3 retirement
   becomes a tracked chore. Absent that, keep-both-scoped stands.

2. **AC.CLP-ADOPT.2 ★ depends on `handsoff-loop` running a real `claude -p` leg
   in the build window.** If the build environment can't run a real sub-agent
   leg (rate-limit, isolation), the ★ AC can't be honestly verified and the
   slice must halt (trigger 4) rather than stub-pass. This is the slice's
   single hardest dependency; it is named, not papered over. Mitigation: the
   fixture is the builder's call and can be sized to the smallest real
   `/goal`-iterating task.

3. **"Consistent use" is a disposition, not a fully-enforceable state** (master
   §10 F2.2, applied here). Slice 3 makes `/goal`/`/loop` the *catalogued,
   structurally-guarded, production-demonstrated* reach — but a persona could
   still hand-roll a keep-going loop inside one uninstrumented turn. The
   matcher row catches the *dispatch* surface; the in-turn surface is the same
   coverage limit the whole doctrine program acknowledges. Not closed here;
   named.

4. **The `goal.md` matcher row's regex precision is a build-time judgment.** I
   recommend the build-verb + keep-going-shape proximity pattern (mirroring the
   Slice-2 ROWS), but the exact keep-going lexicon ("drive to / keep going
   until / re-run until done / continuation / Stop hook that re-fires") is the
   builder's tuning, guarded by halt trigger 5. A too-broad row that flags every
   "loop" is the failure mode; the two-tier deny/warn posture is the mitigation.

---

## §18 Provenance trail

- Master plan: `docs/plans/claude-leverage-program.md` (§Slice-3, §2 row 5,
  §5 AC.CLP-ADOPT.\*, D-CLP.2 — read 2026-06-14).
- Slice 2 sealed: `f308b398` — `docs/plans/claude-leverage-program-s2-doctrine.md`
  + `plugins/dev-sdlc/hooks/primitive_check_guard.py` +
  `plugins/dev-sdlc/hooks/primitive_check_matchers.py` (ROWS coverage
  verified: schedule/loop/background-agents, NO goal row — read 2026-06-14).
- Slice 1 sealed: `c41f9473` — `docs/capability-corpus/` (entries verified:
  `claude-code/loop.md` exists, NO `goal.md` — read 2026-06-14).
- Skills: `plugins/loam-skills/skills/{goal-command,loop-command,handsoff-loop}/SKILL.md`
  (read 2026-06-14).
- pos3 bespoke machinery (read-only ref):
  `/Users/lukeivers/pos3/.claude/hooks/autonomy_continuation.py` (read
  2026-06-14 — the queue-dispatcher finding driving D-ADOPT.1).
- Live capability re-verification (2026-06-14, WebFetch
  `https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md`):
  `/goal` @ v2.1.139, fixes @ v2.1.141 / v2.1.152; `/loop` fixes @ v2.1.141 /
  v2.1.152; latest CC 2.1.176.
- Convention: `plugins/dev-sdlc/docs/conventions/plan-docs.md` (Primitive-check
  REQUIRED section — read 2026-06-14).
- Corpus entry shape exemplars: `docs/capability-corpus/claude-code/loop.md` +
  `schedule.md` (read 2026-06-14).
- Memory corpus patterns: `feedback_structural_enforcement_on_recurrence`,
  `feedback_scope_descriptive_ac_ids`, `feedback_test_outcome_altitude_required`,
  `feedback_version_numbers_at_release_time`, `feedback_no_anthropic_api_key`,
  `feedback_value_proposition_as_prime_objective`,
  `feedback_locked_design_not_license_for_bad_outcomes`.
