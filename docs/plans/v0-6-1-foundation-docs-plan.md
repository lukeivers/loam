# Plan — v0.6.1 patch: foundation docs gap-fill

**Authored:** 2026-05-08.
**Status:** plan first per the plan-before-code rule.

---

## Objective

Land the foundation docs (principle-derivation-map.md + ODD-doc gap-fills + odd-in-loam.md F1c bridge re-author) as **v0.6.1 patch**. These were drafted in pos3's forward-staging; per Luke 2026-05-08 ruling R1 they ship as a v0.6.1 patch (META-FRAMEWORK class) rather than waiting for v0.7.0.

**Class:** META-FRAMEWORK. **Foundational-investment rationale (per the quality gate):** v0.7.0's structural-enforcement work assumes these foundation docs already exist. Landing them at v0.6.1 — independently of v0.7.0's enforcement work — separates "what the principles are" (META-FRAMEWORK doc surface) from "structural enforcement of those principles" (META-FRAMEWORK code work) cleanly. Without this separation, v0.7.0 would have to absorb both authoring + enforcement, doubling its scope.

**Quality-gate compliance:** META-FRAMEWORK exempt from user-value-delta gate per `docs/release-versioning-policy.md` quality-gate section. Foundational-investment rationale named (above) + future end-user work this enables (v0.7.0 structural enforcement, which is itself META-FRAMEWORK; the END-USER-felt downstream is v0.8.0 onwards where the principle foundation feeds negative-alignment detection + the persona's structural-enforcement of its own behavior).

## Constraints

- **R3 reframe (Luke 2026-05-08): no new `principles.md` or `odd-principles.md` file.** Pos3's draft is RESEARCH INPUT for gap-filling existing ODD docs (`plugins/dev-sdlc/docs/odd-methodology.md`, `plugins/dev-sdlc/docs/odd-in-loam.md`, `docs/odd-llm-grounding.lean.md`, `docs/odd-llm-grounding-derivation.md`) + `CLAUDE.md` + memory rules. Audit pos3's draft against existing coverage; identify gaps; gap-fill into the appropriate existing surface. Drop content already covered.
- **R4: port docs only, not installer.** Pos3's `first_run_scaffold.py` F1a-installer + test stay fork-only. Out of scope for v0.6.1; revisit later as separate scope question.
- **Pos3's `odd-methodology.md` draft is STALE** (missing canonical's v0.1.8/v0.2.3 adapter additions). Drop it; canonical version is correct as-is.
- **Pos3's `principle-derivation-map.md` ports cleanly** — direct match to existing AC.FR.1.4 plan target.
- **Pos3's `odd-in-loam.md` F1c bridge re-author** — merge into canonical version preserving canonical's existing content; pos3's draft is the research input.
- **NO Anthropic API key** — n/a directly (doc work).
- **NEW commits only.** No --amend.
- **No push.** Held for owner ruling on tag-push.
- **Subscription-only architecture holds.**
- **No "rebuild" terminology** in any new content.

## Acceptance criteria

1. **AC.V061.1 — `principle-derivation-map.md` lands.** Port pos3's `framework/docs/design/principle-derivation-map.md` to canonical at `framework/docs/design/principle-derivation-map.md` (or the equivalent canonical path; verify canonical's existing structure first). Content: which principles compose with F4 (scope ↔ confidence) vs which are independent vs partial. Direct match to existing FR.1.4 expectation per the prior plan.
2. **AC.V061.2 — `odd-in-loam.md` F1c bridge re-author merged.** Read canonical `plugins/dev-sdlc/docs/odd-in-loam.md` + pos3's `plugins/dev-sdlc/docs/odd-in-loam.md` draft. Merge pos3's F1c bridge content (the research-input portion) into canonical, preserving canonical's existing v0.1.8 + v0.2.3 adapter additions. Output: single canonical version with both contents reconciled.
3. **AC.V061.3 — Pos3's `principles.md` audit + gap-fill.** Read pos3's draft (20 operating principles + ODD content). For each principle: identify whether it's already covered in (a) existing ODD docs, (b) `CLAUDE.md`, (c) memory rules under `~/.claude/projects/-Users-lukeivers-pos3/memory/`, (d) personas/primary/. Gap-fill missing content into the most-appropriate existing surface. Drop content already covered. Audit-output documented in plan-doc §14.
4. **AC.V061.4 — STATE.md updated.** Add v0.6.1 SHIPPED entry inline mirroring the v0.2.5.1 entry shape: objective sentence + class tag (META-FRAMEWORK) + seal SHA + foundational-investment rationale + the audit-result summary.
5. **AC.V061.5 — Tag v0.6.1 created locally.** Annotated tag at the v0.6.1 SHIPPED commit. Held for owner ruling on push.
6. **AC.V061.6 — Pos3 promotion classification doc updated.** Add a closure note to `docs/plans/research/pos3-forward-staging-promotion-classification.md` indicating which items shipped as v0.6.1, which stay fork-only (the F1a installer + tests), which were dropped (the stale odd-methodology.md). Composes cleanly with the original classification.
7. **AC.V061.7 — `pos amend apply` + `loam amend seal` cycle.** Use the canonical sealed-component cycle. Plan-doc + manifest + apply + seal + §14 backfill. NEW commits, no --amend.

## Out of scope

- **Don't promote the F1a-installer** (`first_run_scaffold.py` + `test_F1a_principles_install_resolver.py`). Per R4: stay fork-only, revisit later.
- **Don't drop pos3's principles.md draft from pos3.** Read-only on pos3.
- **Don't push the v0.6.1 tag.** Held for owner ruling.
- **Don't apply v0.7.0 work.** Foundation enforcement is its own minor.
- **Don't apply the roadmap re-rank from harness research** (RR.1/RR.2/RR.3) in this dispatch. That's a separate cycle once v0.6.1 lands.
- **Don't touch the v0.3.0 directory rename.** v0.3.0 work is its own cycle.
- **Don't author new methodology docs.** All landed content goes into existing surfaces per R3 reframe.

## Authority chain

- `/Users/lukeivers/pos3/framework/docs/design/principle-derivation-map.md` (source: forward-staging)
- `/Users/lukeivers/pos3/plugins/dev-sdlc/docs/odd-in-loam.md` (source: F1c bridge draft)
- `/Users/lukeivers/pos3/framework/docs/principles/principles.md` (source: 20 operating principles draft)
- `/Users/lukeivers/ivers-corp-pos-v2/plugins/dev-sdlc/docs/odd-methodology.md` (canonical; preserved)
- `/Users/lukeivers/ivers-corp-pos-v2/plugins/dev-sdlc/docs/odd-in-loam.md` (canonical; merge target)
- `/Users/lukeivers/ivers-corp-pos-v2/docs/odd-llm-grounding.lean.md` (canonical; gap-fill target if needed)
- `/Users/lukeivers/ivers-corp-pos-v2/CLAUDE.md` (canonical; gap-fill target if needed; just had Lens 4+5 added at commit 5a0e63a)
- `~/.claude/projects/-Users-lukeivers-pos3/memory/` (gap-fill target if needed)
- `/Users/lukeivers/ivers-corp-pos-v2/docs/release-versioning-policy.md` (quality gate criterion this minor satisfies)
- `/Users/lukeivers/ivers-corp-pos-v2/docs/release-roadmap.md` (insert v0.6.1 entry)
- `/Users/lukeivers/ivers-corp-pos-v2/docs/plans/research/pos3-forward-staging-promotion-classification.md` (closure note target)

## Output

Build report at `<workspace>/.scratch/claude-output/v0-6-1-build-report.md`. Reply ≤200 words inline naming files touched + seal SHA + audit-result summary for the principles.md gap-fill (which content went where) + any halt-and-surface findings.

## Halt-and-surface

WD mismatch. Authority docs missing. The pos3 principles.md content is so substantively different from existing ODD doc framing that gap-filling would distort canonical voice — surface for owner ruling. The principle-derivation-map.md port reveals canonical doesn't have a `framework/docs/design/` directory — surface for path resolution. Push or tag-push attempt. Any modification to canonical files outside the named scope.
