# Plan — v0.3.0 master plan authoring

**Authored:** 2026-05-08.
**Status:** plan-for-the-plan; the deliverable is the v0.3.0 master plan + cycle sub-plan-docs.

---

## Objective

Author the **v0.3.0 master plan + cycle ladder** that decomposes the next minor into shippable cycles. v0.3.0's outcome (per `docs/release-roadmap.md`): "Loam's documented features work as advertised AND loam's terminology is consistent across forward-looking surface." This is a META-FRAMEWORK class minor with multiple distinct work-streams that need explicit cycle decomposition.

The master plan + sub-plan-docs let v0.3.0 ship through serially-dispatched cycle builds. Each cycle has its own plan-doc, dispatch, build, seal, §14 backfill — per the canonical sealed-component convention.

## Constraints

- **Sequential builds enforced.** Cycles ship one at a time; no parallel sealed-component-amendment-build agents in the same WD per `feedback_serialize_amendment_builds`.
- **Foundation docs (formerly mis-framed as v0.6.1 / v0.7.0 Cycle 1) fit inside v0.3.0.** Same feature-honesty defect class — principles referenced in canonical docs that don't have canonical text. Per Luke 2026-05-08: docs go where they fit, but builds happen in version order.
- **R3 reframe holds for foundation docs:** no new principles.md or odd-principles.md; gap-fill into existing surfaces.
- **R4 holds:** F1a-installer stays fork-only; out of scope.
- **Class is META-FRAMEWORK.** Foundational-investment rationale: feature-honesty work doesn't deliver new user-visible capability but UNBLOCKS every subsequent minor (v0.4.0+ all depend on canonical docs being trustworthy + terminology being consistent + graphiti residue being out of the way).
- **NO Anthropic API key.** No subscription-only violation in any cycle.
- **No "rebuild" terminology in any new content** AND v0.3.0 includes the cycle that scrubs existing rebuild references.

## Acceptance criteria

1. **AC.V030MP.1 — Master plan exists** at `docs/plans/v0-3-0-master-plan.md`. Contains:
   - Objective sentence (verbatim from release-roadmap)
   - Class tag (META-FRAMEWORK) + foundational-investment rationale
   - Cycle ladder (named cycles in dependency order)
   - Per-cycle: objective + scope items + AC count + AI-time band + dependencies
   - Methodology amendments (if any) noted
   - Smoke gate at end of cycle ladder
2. **AC.V030MP.2 — Cycle ladder is shipped-tractable.** Each cycle has scope tight enough to land in 1-3 hours AI-time per the rubric. No mega-cycles. Likely shape:
   - Cycle 1: directory rename (`docs/rebuild/` → `docs/`) + 744-file reference scrub
   - Cycle 2: graphiti rip-out (component, venv, install-from-source, cross-references)
   - Cycle 3: foundation docs gap-fill (principle-derivation-map port + odd-in-loam F1c bridge merge + pos3 principles.md audit)
   - Cycle 4: lint pass (ruff + mypy + clean) + KNOWN_CROSS_MODE_DEBT shrinkage + F3/F4 closures
   - Cycle 5: terminology-consistency pass (loam-aligned names: substrate / seed / cultivar / amend / seal — single definitions, glossary-published)
   - Cycle 6: feature-honesty audit (memory system verification + claude -p discipline regression scan + ODD-conformance sweep) — last to validate everything else landed correctly
   - Cycle 7: release-level smoke gate (the v0.3.0 SHIPPED sealing event)
3. **AC.V030MP.3 — Dependencies named.** E.g., directory rename precedes reference scrub; graphiti rip-out can run parallel to foundation docs; lint pass runs late; terminology-consistency runs after directory rename; feature-honesty audit runs last.
4. **AC.V030MP.4 — Sub-plan-doc stubs authored** at `docs/plans/v0-3-0-cycle-N-<slug>.md` for each cycle. Stubs name the cycle objective + sketch ACs + reference master plan + tag as "to-be-finalized at dispatch time." Full sub-plan-doc happens at cycle-dispatch time per the master-plan-author + cycle-author pattern.
5. **AC.V030MP.5 — Composes with existing roadmap.** The master plan REFERENCES `docs/release-roadmap.md` v0.3.0 entry as authority; doesn't duplicate. Updates the entry if needed (e.g., add foundation-docs scope explicitly).
6. **AC.V030MP.6 — Word count 2500-4500** for the master plan; sub-plan-doc stubs short (300-500 words each).
7. **AC.V030MP.7 — NEW commit, no --amend, no push.**

## Out of scope

- **Don't execute any cycle.** Master plan + stub sub-plan-docs only.
- **Don't modify release-roadmap.md beyond the foundation-docs scope addition** if needed.
- **Don't push.**
- **Don't create v0.3.0 tag.** Tag waits for end-of-cycle-ladder.

## Authority chain

- `docs/release-roadmap.md` v0.3.0 entry (authority on v0.3.0 outcome + scope items)
- `docs/release-versioning-policy.md` (SemVer + class tags + quality gate)
- `docs/odd-semver-pinning.md` (cycle-vs-minor composition)
- `docs/odd-methodology.md` (ODD §2.5 + altitude self-checks for cycle ACs)
- `docs/leverage-discipline.md` (rubric for cycle prioritization within v0.3.0)
- `plugins/dev-sdlc/skills/plan-docs-author/SKILL.md` (canonical plan-doc shape)
- `plugins/dev-sdlc/skills/dispatch-brief-authoring/SKILL.md` (canonical dispatch-brief shape — feeds the cycle-author dispatches that come later)
- `docs/plans/research/pos3-forward-staging-promotion-classification.md` (what foundation-docs work pos3 has staged)

## Output

Write to `docs/plans/v0-3-0-master-plan.md` + `docs/plans/v0-3-0-cycle-N-<slug>.md` stubs. Commit but do NOT push. NEW commit; no --amend.

Reply ≤200 words inline naming the cycle ladder (one-line each) + AI-time band per cycle + total v0.3.0 AI-time band + any halt-and-surface findings.

## Halt-and-surface

WD mismatch. Authority docs missing. The foundation-docs scope can't fit into v0.3.0's outcome cleanly (means the reframe is wrong; surface for owner ruling). Cycle ladder produces >7 cycles or any cycle >5 hours AI-time (means scope is too big; consider splitting v0.3.0 into v0.3.0 + v0.3.1 minor pair or carving into v0.4.0 — surface for owner ruling). Push or tag attempt.
