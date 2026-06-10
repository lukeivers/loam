# Context-Management Cycle 2 — context budget

> **Status:** sub-plan-doc (ODD-shaped). PLAN ONLY.
> **Master plan:** `docs/plans/context-management-see-budget-eviction-master.md`.
> **WD:** `/Users/lukeivers/loam`.
> **Parent objective:** AC.PO.1 + AC.PO.2 (via master §4).
> **Confidence (Lens 4):** HIGH-MEDIUM. The math is deterministic (HIGH); the
> SKILL-edit that feeds the measured number into the rubric is a prose edit with a
> behavioural payoff (MEDIUM on adoption, but the AC tests the consumption seam,
> not adoption).
> **Depends on:** Cycle 1's `read()` sensor.

---

## §1 Objective

Turn the Cycle-1 occupancy reading into a context budget: occupancy-vs-ceiling
math with reserves (`remaining = window − reserve_out − reserve_work −
occupied`), a threshold classifier (<60% / 60–85% / >85% / >92%), and the wiring
that feeds the MEASURED number into the existing `strategic-compact` decision
rubric — retiring its "utilization isn't directly exposed as a number → heuristic
only" honest-limit.

## §2 Predecessors / context

- **Cycle 1** (`framework/context-management/`) — the `read()` sensor this budget
  consumes.
- `framework/usage-window-guard/` — the twin's window-model + threshold shape.
- `plugins/loam-skills/skills/strategic-compact/SKILL.md` — the rubric; the
  honest-limit seam at lines 143–144 / 171 / 254; the 60/85 split already in the
  decision rule (lines 80–84), so the measured number drops in without
  re-deriving thresholds.
- Research §5.2 — the occupancy-vs-ceiling math + the explicit "do NOT copy the
  token-budget `/n` even-pacing formula."

## §3 Scope

**In scope:**
- Budget function in `framework/context-management/`: `remaining` computation +
  occupancy-percentage, over named `reserve_out` / `reserve_work` constants.
- Threshold classifier mapping a reading to exactly one band.
- Edit `strategic-compact` SKILL branch-1 (the §"How the persona applies it" step
  1): replace "infer heuristically / name as a guess" with "read the measured
  occupancy from the context budget; fall back to the heuristic ONLY when the
  sensor reports unavailable." Keep the heuristic fallback text for the
  unavailable case (backwards-compat: AC.COMPACT.* must not regress).
- Tests including outcome-altitude `AC.CTXBUD.S`.

**Out of scope:**
- Auto-firing `/compact` — owner-class stays (D-COMPACT.TRIGGER lock); the budget
  supplies the number, the rubric supplies the recommendation, the OWNER fires.
- The dispatch-time worker-budget gate (that's lean-mode §7 of the master — plan
  only).
- Microcompact wiring (always-on floor is a CC built-in; nothing to build).
- PreCompact summary-steering — API-only, not buildable (research §2.3).

## §4 Acceptance criteria

| AC ID | Outcome | Verification |
|---|---|---|
| `AC.CTXBUD.1` | `remaining = window − reserve_out − reserve_work − occupied`; given a known reading the computed remaining + occupancy-% match the arithmetic. | Fixture readings → assert remaining + % equal the independently-computed values (arithmetic verified per `feedback_arithmetic_verification`). |
| `AC.CTXBUD.2` | The classifier maps a reading to exactly ONE band: <60% continue / 60–85% externalize-early / >85% recommend-compact / >92% hard-surface. Boundary readings (exactly 60, 85, 92) resolve deterministically. | Readings across + on each boundary → assert single band; boundaries deterministic. |
| `AC.CTXBUD.3` | The `strategic-compact` SKILL's decision step consumes the measured occupancy when the sensor is available, and falls back to the heuristic only when the sensor reports unavailable. The honest-limit text no longer claims utilization is unexposed when the sensor is present. | SKILL body assertion: branch-1 names the measured-number read + the unavailable-fallback; the unconditional "not directly exposed" claim is gone / conditioned. |
| `AC.CTXBUD.S` **(OUTCOME-ALTITUDE)** | A cold session reading crossing 85% occupancy, fed through the production budget path with NO pre-arranged state, yields the recommend-compact band off the MEASURED number — not a guess. | Real budget entry-point + a realistic >85% reading (no staged classifier state); assert band == recommend-compact AND the band's provenance is the measured reading. RED-on-mutation: revert the measured-read wiring → band derives from nothing / wrong. |

**Method-in-AC test:** the data structures, the constant values, the SKILL prose
wording are the builder's call. Outcome-shape confirmed.

**Ladder-up:** AC.CTXBUD.* → master AC family → AC.PO.1 (the guess becomes a
measured number in the persona's translation) + AC.PO.2 (the >85%/>92% bands are
the protection trigger against silent state-loss to compaction).

## §5 Sealed-component fence

- **`framework/context-management/`** (the budget function + classifier + tests).
- **`plugins/loam-skills/`** (the `strategic-compact` SKILL edit + a regression
  assertion). Seal test `plugins/loam-skills/tests/test_no_sealed_amendments.py`.
- Universal admissions: `docs/plans/`.
- **No other component touched.**

## §6 Halt triggers

1. WD not `cd /Users/lukeivers/loam` before source edits → halt.
2. Cycle 1 not sealed (no `read()` sensor to consume) → halt; Cycle 2 depends on it.
3. The `strategic-compact` SKILL edit would regress an existing AC.COMPACT.* test
   (the heuristic-fallback path must survive) → halt + re-scope the edit to
   additive-only.
4. The 60/85 thresholds in the SKILL's existing decision rule conflict with the
   classifier's bands → halt + reconcile (they should align per research §5.2;
   verify Tier-0).
5. An AC reframes to method-in-AC → halt.

## §7 Ship shape

Single cycle, single seal. Manifest:
`docs/plans/context-management-see-budget-eviction-c2-budget.manifest.yaml`.
Two-component fence (`context-management` + `loam-skills`). Apply → seal.

## §8 Risk / open questions

- **Q1 — reserve constants.** `reserve_out` ≈ 15% (research §5.2); `reserve_work`
  for in-flight growth. Builder tunes; AC.CTXBUD.1 tests the arithmetic, not the
  constant. Expose as named constants so the band is tunable without a rewrite.
- **Q2 — SKILL-edit blast radius.** The honest-limit phrase appears at lines
  143–144, 171, 254 of `strategic-compact/SKILL.md`. The edit must condition (not
  blanket-delete) so the unavailable-sensor fallback stays honest. Verify each
  occurrence's context at build time.

## §14 Method-decision register (populated at build time)

- D-build.1 — reserve constant values + named-constant exposure. *(builder)*
- D-build.2 — classifier band-boundary resolution (inclusive/exclusive). *(builder)*
- D-build.3 — exact SKILL branch-1 rewording (condition vs replace). *(builder)*

## §15 Backwards-compat verification

- `strategic-compact` AC.COMPACT.* tests must all pass (heuristic-fallback path
  retained).
- `loam-skills` `test_no_sealed_amendments.py` must pass.
- Cycle 1's `framework/context-management/` tests unchanged.

## §16 Halt-and-surface findings (plan-authoring)

- Surfaced (non-blocking): Q2 SKILL-edit must condition the honest-limit text per
  occurrence, not blanket-delete. No owner gate blocks this cycle.
