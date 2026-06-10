# Context-Management Cycle 3 — eviction discipline

> **Status:** sub-plan-doc (ODD-shaped). PLAN ONLY.
> **Master plan:** `docs/plans/context-management-see-budget-eviction-master.md`.
> **WD:** `/Users/lukeivers/loam`.
> **Parent objective:** AC.PO.1 + AC.PO.2 (via master §4).
> **Confidence (Lens 4):** MEDIUM. A discipline SKILL's payoff is a behavioural
> disposition (unmeasurable in a seal test); its highest-leverage lever
> (fork-isolation) rests on a research claim the research itself marks UNVERIFIED.
> The outcome-altitude AC is the verifier for that claim — gated.
> **Depends on:** Cycle 1's sensor + Cycle 2's >60% externalize-early threshold.

---

## §1 Objective

Ship the achievable substitute for the runtime-forbidden "strike out specific
content": a discoverable `context-hygiene` discipline SKILL encoding the three
runtime-legal doors — input-discipline (cap tool-return size, keep MCP deferred),
fork-by-default for noisy read work, externalize-early — which together produce
the *effect* of evicting content that was never resident. Gate the fork lever on
an empirical probe that the research's UNVERIFIED token-attribution claim holds.

## §2 Predecessors / context

- **Cycles 1+2** — the sensor + the >60% externalize-early budget trigger this
  discipline fires on.
- `loam-spawn-isolation` (research §1 / contingency-plan §3.2) — the fork muscle
  the fork-by-default door points at.
- `plugins/loam-skills/skills/precompact-hook/SKILL.md` — composes (block + log
  at PreCompact; CANNOT steer the summary on the subscription path — research
  §2.3 F2 correction).
- `plugins/loam-skills/skills/strategic-compact/SKILL.md` — the sibling
  compact-decision SKILL; `context-hygiene` is the keep-OUT mirror to its
  shrink-IT lever.
- Research §3 (the 3-lever model), §5.3 (deliberate eviction), §2.5
  (subagent/fork isolation + the skill-truncation footgun), §7 (the UNVERIFIED
  fork token-attribution doubt).

## §3 Scope

**In scope:**
- New `context-hygiene` SKILL at `plugins/loam-skills/skills/context-hygiene/SKILL.md`
  (subdirectory shape — the discoverable contract per the v0.1.7 AC.LAYERED.2
  pattern).
- Body: the three doors + the F2 note that delete-message is NOT a runtime
  primitive on the subscription path + the composition surfaces.
- The empirical fork token-attribution probe (the `AC.CTXEVICT.S` verifier).

**Out of scope:**
- Any new fork/isolation MECHANISM — `loam-spawn-isolation` already exists; this
  SKILL points the persona at it, does not rebuild it.
- The API context-editing path (skipped — `feedback_no_anthropic_api_key`).
- Auto-firing the discipline (the persona applies it; no autonomous mutation).
- Steering `/compact` summaries (API-only).

## §4 Acceptance criteria

| AC ID | Outcome | Verification |
|---|---|---|
| `AC.CTXEVICT.1` | The `context-hygiene` SKILL is discoverable (valid frontmatter; reachable via the `_symlink_plugin_skills` walk) and its body carries the three doors (input-discipline / fork-by-default / externalize-early) + the F2 note that delete-message is not a subscription-path runtime primitive. | Frontmatter YAML valid + ≤ Anthropic char budget; body assertions for each door + the F2 note. |
| `AC.CTXEVICT.2` | The SKILL names its composition surfaces: `loam-spawn-isolation` (fork), `precompact-hook` (block+log, cannot steer summary), the context budget's >60% externalize-early trigger. | Body assertions naming each surface. |
| `AC.CTXEVICT.S` **(OUTCOME-ALTITUDE)** | An empirical probe shows work run in an isolated fork does NOT add its tool-call tokens to the caller's `context_window` occupancy reading — the fork lever actually keeps content out. | Real fork dispatch of a token-spending task; compare the caller's occupancy reading before/after (via Cycle 1's sensor) against the fork's own token spend; assert the parent reading does NOT absorb the fork's spend. **RED if fork tokens leak into the parent reading** → halt (master §9 trigger 3). |

**Method-in-AC test:** the SKILL prose, the probe harness construction, the
token-spend task are the builder's call. `AC.CTXEVICT.S` states the OUTCOME (fork
tokens stay out of the parent reading), not the probe's method. Outcome-shape
confirmed.

**Ladder-up:** AC.CTXEVICT.* → master AC family → AC.PO.2 (the protection floor:
keeping load-bearing state from being silently compacted away is the intra-session
mirror of the memory-system's cross-session protection) + AC.PO.1 (the persona
translates "this is getting noisy" into a fork/externalize action rather than
letting the window fill).

## §5 Sealed-component fence

- **`plugins/loam-skills/`** (the new SKILL + the probe test). Seal test
  `plugins/loam-skills/tests/test_no_sealed_amendments.py`.
- Universal admissions: `docs/plans/`.
- **No other component touched.** If the fork probe needs a harness outside
  `loam-skills`, HALT + surface placement (do not silently widen).

## §6 Halt triggers

1. WD not `cd /Users/lukeivers/loam` before source edits → halt.
2. **`AC.CTXEVICT.S` probe shows fork tokens LEAK into the parent
   `context_window` reading** → halt + surface; the fork-by-default lever's
   premise (research §7 UNVERIFIED) is false. Re-scope Cycle 3 to externalize-early
   + input-discipline only and surface to owner. **Do NOT ship Cycle 3 with the
   probe red.**
3. Cycles 1–2 not sealed (no sensor / no >60% trigger to reference) → halt.
4. The `context-hygiene` slug collides with an existing SKILL → halt.
5. An AC reframes to method-in-AC → halt.

## §7 Ship shape

Single cycle, single seal. Manifest:
`docs/plans/context-management-see-budget-eviction-c3-eviction.manifest.yaml`.
Single-component fence (`loam-skills`). Apply → seal. This is the minor's last
cycle → HARD-smoke ride-along here per `feedback_hard_smoke_per_minor_before_publish`.

## §8 Risk / open questions

- **Q1 — the fork-attribution probe is the load-bearing risk.** Research §7 marks
  fork token-attribution to the parent's `context_window` field UNVERIFIED.
  `AC.CTXEVICT.S` IS the verification; halt-trigger 2 is its failure path. This is
  the cycle's central uncertainty — flag it at dispatch.
- **Q2 — skill-truncation footgun (research §2.5).** Invoked skill content stays
  resident; auto-compaction reattaches ≤5000 tok/skill, ≤25000 total → heavy
  skill stacks silently truncated post-compact. The `context-hygiene` SKILL body
  itself must stay lean (it's a discipline, not a reference dump) AND its body
  should name this footgun as a reason to keep state in files, not resident skills.
- **Q3 — measuring discipline adoption is out of reach.** A seal test cannot
  verify the persona actually forks noisy work by default. The AC tests the
  lever's MECHANICS (`AC.CTXEVICT.S`) + the SKILL's discoverability + content. Named
  honestly (master §10 F2.1).

## §14 Method-decision register (populated at build time)

- D-build.1 — fork-attribution probe harness construction. *(builder)*
- D-build.2 — SKILL body structure + the footgun-warning placement. *(builder)*
- D-build.3 — token-spend task used to drive the probe. *(builder)*

## §15 Backwards-compat verification

- `loam-skills` `test_no_sealed_amendments.py` must pass.
- `_symlink_plugin_skills` discoverability of existing SKILLs (strategic-compact,
  precompact-hook) unchanged.
- Cycles 1–2 `context-management` tests unchanged.

## §16 Halt-and-surface findings (plan-authoring)

- Surfaced (BLOCKING the cycle's ship, not the plan): `AC.CTXEVICT.S` must go
  green before Cycle 3 ships; if the fork-attribution claim fails, the cycle
  re-scopes and surfaces to owner (halt-trigger 2). No owner gate blocks
  authoring this plan.
