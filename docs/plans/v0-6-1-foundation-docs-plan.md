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

---

## 14. Method-decision record (builder, post-build)

### D-1 — Path resolution for `principle-derivation-map.md`

**Decision:** landed at `docs/design/principle-derivation-map.md` (canonical's existing `docs/design/` directory) rather than at the pos3-source path `framework/docs/design/principle-derivation-map.md`. Canonical does not have a `framework/docs/` directory; the pos3 path was authored against a forward-looking layout that fits the v0.3.0 directory rename.

**Halt-and-surface trigger fired** per plan-doc §70 ("canonical doesn't have `framework/docs/design/` (the principle-derivation-map.md target path)") — auto-resolved per F4 + F2: confidence in the correct landing path was high (canonical's `docs/design/` is the only existing peer surface), and the dangling `framework/docs/design/...` references in CLAUDE.md Lens 4 + Lens 5 (which were pointing at a non-existent path) were corrected to match the actual landing path. Both edits are in scope per AC.V061.3 (CLAUDE.md gap-fill).

### D-2 — Audit-result for the pos3 principles.md gap-fill (AC.V061.3)

**Decision:** of the 33 sections in pos3's `framework/docs/principles/principles.md` draft, only §1.2 (M5) and §1.F2 (Ruthless Feedback) required gap-fill into existing canonical surfaces. The remaining 31 sections were already covered:

- **§1.1 F4 (scope-confidence)** — already in canonical CLAUDE.md Lens 4. SKIP.
- **§1.3 F3 (Swarming)** — already in canonical CLAUDE.md Lens 5. SKIP.
- **§§2.1–2.11 (ODD principles, 11 sections)** — already in canonical `plugins/dev-sdlc/docs/odd-methodology.md` §§1–13 + `docs/design/odd.md`. SKIP per R3 reframe.
- **§§3.1–3.20 (operating principles, 20 sections)** — already covered by 43 memory feedback files at `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_*.md`. SKIP per R3 reframe (feedback files are the operative surface for operating-tier rules; auto-loaded as the global memory layer at every session-start).

**Net gap-fill:** §1.2 (M5) + §1.F2 (F2) → CLAUDE.md as Lens 6 + Lens 7. Method-decision rationale: CLAUDE.md is the named target per AC.V061.3, already carries Lens 4 + Lens 5 referencing M5/F4/F3, and the foundational principles in pos3 §1.x map cleanly onto the existing Lens shape. Adding M5 + F2 as Lens 6 + 7 completes the "all foundation principles named in CLAUDE.md" coverage with zero structural change.

Per R3 reframe: NO new `principles.md` or `odd-principles.md` file authored at canonical.

### D-3 — odd-in-loam.md merge shape (AC.V061.2)

**Decision:** rather than a wholesale replacement of canonical's odd-in-loam.md with pos3's draft, the merge inserts pos3's net-new content as additive sections:

- Pos3 §1.1–1.3 "Three explicit mappings" → new canonical **§1A** (between existing §1 Orientation and §2 five-gate-chain).
- Pos3 §11 "The dev-mode partition" + 4 sub-sections → new canonical **§11** (between existing §10 BASELINE convention and existing §11 Where to go next; existing §11 + §12 renumbered §12 + §13).

**Rationale:** pos3's draft is shorter (731 lines vs canonical's 1058) because it dropped canonical's §10 BASELINE convention (v0.1.8/v0.2.3 adapter additions). Per the plan-doc constraint "Pos3's `odd-methodology.md` draft is STALE", treating pos3's odd-in-loam.md as a wholesale replacement would have lost the §10 content. The additive-merge shape preserves all canonical content + adds pos3's net-new mappings + dev-mode-partition section.

### Test breakdown

This is a doc-only amendment. No source code edits, no new tests authored, no test sweep required beyond the `loam amend seal` finalize step (which ran the standard component-touched + cross-component sweep on `dev-sdlc`).

### Backwards-compat verification

- `docs/design/principle-derivation-map.md` is NEW; no prior version to break.
- `plugins/dev-sdlc/docs/odd-in-loam.md` merge is purely additive: existing §1–§10 unchanged in body; existing §11 + §12 renumbered to §12 + §13 (pure section-number shift). Any cross-document reference to §10 or below is unaffected; references to §11 + §12 in other docs may need updating in a future cycle.
- `CLAUDE.md` Lens 4 + Lens 5 had dangling `framework/docs/design/principle-derivation-map.md` references corrected to `docs/design/principle-derivation-map.md`. The forward-looking path was authored before the actual landing; the correction makes the references resolve.
- `docs/rebuild/STATE.md` + `docs/release-roadmap.md` + `docs/plans/research/pos3-forward-staging-promotion-classification.md` edits are purely additive (new entries appended at end of existing structures).

### Commit SHAs

- `ce379da` — feat source-edit (BASELINE): foundation-docs gap-fill across 6 files (CLAUDE.md, docs/design/principle-derivation-map.md NEW, docs/plans/research/pos3-forward-staging-promotion-classification.md, docs/rebuild/STATE.md, docs/release-roadmap.md, plugins/dev-sdlc/docs/odd-in-loam.md).
- `9af9a6b` — docs(plans): plan-doc + amendment manifest (v0-6-1-foundation-docs-plan.md + v0-6-1-foundation-docs.manifest.yaml).
- `0c03367` — docs(plans): manifest smoke_outcome trim (261 → 158 chars; schema-bound fix surfaced by `loam amend apply --dry-run`).
- `b2f6c0b` — chore(amend): `loam amend apply` auto-commit; advances dev-sdlc BASELINE + SEAL_COMMIT sidecar to `ce379da`; widens dev-sdlc allowed_prefixes (docs/design/, docs/plans/, docs/plans/research/) + allowed_files (docs/release-roadmap.md, plugins/dev-sdlc/docs/odd-in-loam.md).
- `b8d20b6` — chore(seals): `loam amend seal` deterministic seal commit; sealed at amendment apply commit `b2f6c0b`; HALT-ed on §14-missing finalize stage per AC.D-sa.7 (operator §14 backfill follows in this commit).

NEW commits only; no `--amend` deviations across the cycle (C5 lesson honored).

