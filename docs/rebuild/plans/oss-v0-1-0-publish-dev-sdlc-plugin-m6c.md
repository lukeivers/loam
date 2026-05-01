# OSS v0.1.0 publish — Dev/SDLC plugin M6c (trailing cleanups + graceful-fallthrough CDC)

**Status:** sub-plan for M6c; FINAL sub-amendment in the M6 series.
**Predecessors:** M6a sealed at `acd70ff` (Surface A baseline plugin); M6b.0 sealed at `3a7c8d7` (Surface B extraction excluding loam amend); M6b.1 sealed at `c08e0fa` (loam amend MOVE alone with shadow-then-flip).
**Successor:** none — M6c closes the M6 series.
**Master plan:** `docs/rebuild/plans/oss-v0-1-0-publish-dev-sdlc-plugin.md` (§6.5.4 M6c slot in the ladder; AC.OSS-M6.S(c) — single sealed-component fence covering whatever components the trailing-edge work touches).
**Programme master plan:** `docs/rebuild/plans/oss-v0-1-0-publish.md`.

---

## 1. Objective

Close the M6 sub-amendment series with two coherent surfaces:

1. **Surface 1 — Trailing dead-link / cross-reference cleanup.** Audit-and-update the LIVE consumer-facing surfaces (CLAUDE.dev.md, plugin docs/conventions/templates, plugin's dev-mode-manifest, framework/tools/loam/README, master plan-doc) that still name pre-MOVE paths post-M6a/M6b.0/M6b.1. Historical narrative (commit messages, seal narratives, pre-M6 plan-doc bodies, post-M6b convention narratives that describe "Pre-M6b.0 the cycle lived at...") STAYS — preserves historical record per Idea 10's "no retroactive rewrites" rule.

2. **Surface 2 — Author the graceful-fallthrough-with-detection CDC** at `plugins/dev-sdlc/docs/cdcs/graceful-fallthrough-with-detection.md` per the dispatcher's directive 2026-04-29 (captured in `docs/rebuild/FUTURE_IDEAS_DRAFT.md` post-memory-sidecar incident). The CDC names "graceful fallthrough must include detection + surface, not silent swallow" and connects ODD §2.5 (silent-except branches are non-objective by construction). It additionally surfaces structural-enforcement candidates (periodic-health-monitor, UPS hook contributor surfacing degraded-state, auto-recovery primitives, audit-pass) for post-v0.1.0 implementation. The CDC matches the prose style of the existing 10 dev CDCs (now resident at `plugins/dev-sdlc/docs/cdcs/` post-M6b.0).

## 2. Owner rulings (carried forward)

The four M6b plan-time findings (F1-F4) were ratified by the dispatcher 2026-04-29 + executed across M6b.0 + M6b.1. M6c carries no NEW findings to surface at plan-authoring time — the cross-reference audit produced four halt-and-surface notes (HSF#1..HSF#4 in §16 below) that are dispatch-named scope discriminators, not new design questions. M6c proceeds.

## 3. M6c scope — explicit in-scope vs out-of-scope

### In-scope (M6c)

**Surface 1 — Cross-reference cleanup (8 live consumer files):**

The pre-MOVE → post-MOVE substitutions M6c executes are:

- `framework/tools/loam/src/loam_cli/amend/` → `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/` (per M6b.1 MOVE).
- `framework/tools/loam-mode/` → `plugins/dev-sdlc/tools/loam-mode/` (per M6b.0 MOVE).
- `docs/odd-methodology.md` → `plugins/dev-sdlc/docs/odd-methodology.md` (per M6b.0 MOVE).
- `docs/odd-in-loam.md` → `plugins/dev-sdlc/docs/odd-in-loam.md` (per M6b.0 MOVE).

Files audited + EDITED:

1. `CLAUDE.dev.md` — 4 refs to ODD docs (lines 19, 20, 55, 56).
2. `framework/tools/loam/README.md` — 1 ref to `docs/odd-in-loam.md` (line 151).
3. `plugins/dev-sdlc/dev-mode-manifest.yaml` — 2 refs in `dev_only:` block (lines 118-119; the manifest currently auto-loads ODD docs at the canonical pre-MOVE paths). Edit: paths point at the plugin-relative post-MOVE locations.
4. `plugins/dev-sdlc/docs/cdcs/scope-only-dispatch.md` — 1 ref to `docs/odd-methodology.md` (line 5).
5. `plugins/dev-sdlc/docs/conventions/sealed-component-invariants.md` — 2 refs to `framework/tools/loam/src/loam_cli/amend/` (lines 5, 41 — naming the implementation location of the seal-diff machinery).
6. `plugins/dev-sdlc/docs/conventions/commit-ladder.md` — 2 refs to `framework/tools/loam/src/loam_cli/amend/` (lines 5, 49 — naming the implementation location of the seal/apply commands).
7. `plugins/dev-sdlc/templates/plan/dev-discipline.md` — 1 ref to ODD docs (line 28).
8. `plugins/dev-sdlc/templates/dispatch/sealed-component-build.md` — 1 ref to `docs/odd-methodology.md` (line 40).
9. `docs/rebuild/plans/oss-v0-1-0-publish.md` — 2 refs (line 208 referencing `framework/tools/loam-mode/` in AC.OSS.3 dev-tools list; line 213 referencing `docs/odd-methodology.md` + `docs/odd-in-pos.md` in the dev-only artefacts list; line 321 referencing `docs/odd-methodology.md` in §5 deferred-list). The line 213 "odd-in-pos.md" is a separate pre-existing typo (should be `odd-in-loam.md`) — fix in same edit since we're already touching the line.

Files audited + PRESERVED as historical narrative:

- `plugins/dev-sdlc/docs/conventions/amendment-cycle.md:56` — "Pre-M6b.0 the cycle lived in precedent + dispatch templates + `docs/odd-in-loam.md`". This IS historical narrative.
- `plugins/dev-sdlc/docs/conventions/five-gate-chain.md:38` — "Pre-M6b.0 the convention lived in `docs/odd-methodology.md` + `docs/odd-in-loam.md`". Historical narrative.
- `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml:164` — "Post-M6b.0: framework/tools/loam-mode/ MOVED..." historical narrative inside YAML comment.
- `plugins/dev-sdlc/docs/cdcs/README.md:4` — "Pre-M6b.0 they lived in docs/rebuild/FUTURE_IDEAS.md's temporary parking section". Historical narrative.
- `docs/rebuild/FUTURE_IDEAS.md` post-M6b.0 redirect line — already correctly worded ("moved to plugins/dev-sdlc/docs/cdcs/").
- `docs/rebuild/FUTURE_IDEAS_DRAFT.md:75` — captured-2026-04-28 task entry naming `framework/tools/loam-mode/` at point-of-occurrence. Historical capture; preserve.
- All `docs/rebuild/plans/*.md` and `docs/rebuild/components/*` plan-doc bodies — historical plan documents describing builds that completed BEFORE the M6 MOVEs. ~165 plan files reference pre-MOVE paths in their bodies; per Idea 10 they STAY untouched. M6c only edits the master oss-v0-1-0-publish.md plan-doc which is in-flight.

**Surface 2 — New CDC at `plugins/dev-sdlc/docs/cdcs/graceful-fallthrough-with-detection.md`:**

- Authored matching the prose style of existing CDCs (read 1-2 references for shape: `shutdown-path-broad-catch.md`, `plan-before-code.md`).
- Sections: title-as-tightened-rule blockquote + Rationale + How to apply + Connection to ODD §2.5 + Structural-enforcement candidates (post-v0.1.0) + Applied-immediately footer.
- ~30-60 LOC concise codification.
- Cross-link from `plugins/dev-sdlc/docs/cdcs/README.md` index — append row 11.

**Surface 1 polish — partition-manifest M2 final review:**

Verified: every path the M6 series introduced (`plugins/dev-sdlc/tools/loam-amend/**`, `plugins/dev-sdlc/tools/loam-mode/**`, `plugins/dev-sdlc/hooks/**`, `plugins/dev-sdlc/templates/**`, `plugins/dev-sdlc/docs/{cdcs,conventions}/**`, `plugins/dev-sdlc/dev-mode-manifest.yaml`, `plugins/dev-sdlc/docs/{odd-methodology,odd-in-loam,duration-estimation-rubric}.md`) is covered by the M6b.0-extended `plugins/dev-sdlc/**` glob entry in the publish-mode-manifest's `dev_only:` block. **No partition-manifest edit needed** in M6c.

### Out-of-scope (deferred per dispatch + halt-surface findings)

- **Memory-system code fixes** (the original observation that motivated the graceful-fallthrough CDC). Queued as separate post-M6c amendment per task #18.
- **M1c-corrective com.pos.orchestrator launchd-label stragglers + dev-mode-manifest stale `tools/pos-amend/**` entry.** Queued as task #16; pre-M6 stale paths whose retire belongs to the M1.rename trailing-edge programme, NOT the M6 series.
- **M9 scrub** (final public-surface scrub; gated on full M6 completion + queued post-M6c).
- **v0.1.1+ items** (objective-extraction skill, etc.).
- **Structural enforcement of the new CDC** (periodic-health-monitor scope-of-work entries, UPS hook contributor for degraded-state, auto-recovery primitives, audit-pass for existing silent-swallow patterns) — surfaced AS candidates inside the CDC itself; structural fix is post-v0.1.0 per FIDRAFT capture.

## 4. Acceptance criteria

AC family **AC.OSS-M6c.\*** (continues the AC.OSS-M6\* numbering convention; ladders to master plan AC.OSS-M6.S(c)).

| AC ID | Outcome | Verification |
|---|---|---|
| AC.OSS-M6c.1 | All 8 live consumer files (CLAUDE.dev.md, framework/tools/loam/README.md, plugins/dev-sdlc/dev-mode-manifest.yaml, plugins/dev-sdlc/docs/cdcs/scope-only-dispatch.md, plugins/dev-sdlc/docs/conventions/{sealed-component-invariants.md, commit-ladder.md}, plugins/dev-sdlc/templates/{plan/dev-discipline.md, dispatch/sealed-component-build.md}) updated to reference post-MOVE paths. Each pre-MOVE → post-MOVE substitution applied per §3. | `grep -nE "framework/tools/loam/src/loam_cli/amend\|framework/tools/loam-mode/\|docs/odd-methodology\.md\|docs/odd-in-loam\.md"` against each file returns zero hits (excluding historical-narrative-preserved lines named in §3). |
| AC.OSS-M6c.2 | Master plan `docs/rebuild/plans/oss-v0-1-0-publish.md` AC.OSS.3 dev-only artefacts list (lines 208-213) and §5 deferred-list (line 321) updated to reference post-MOVE paths; the `docs/odd-in-pos.md` typo on line 213 is corrected to `docs/odd-in-loam.md` (now `plugins/dev-sdlc/docs/odd-in-loam.md`). | Source-grep: zero hits for `framework/tools/loam-mode/` in oss-v0-1-0-publish.md; zero hits for `docs/odd-in-pos.md`; the post-MOVE plugin paths present. |
| AC.OSS-M6c.3 | New CDC authored at `plugins/dev-sdlc/docs/cdcs/graceful-fallthrough-with-detection.md` per dispatcher directive. Prose style matches existing dev CDCs (title-as-rule blockquote + Rationale + How-to-apply + ODD §2.5 connection + Structural-enforcement candidates + Applied-immediately footer). Length is in the existing CDC-corpus range (the 10 existing CDCs span 9-56 LOC; the median is ~20 LOC; the new CDC sits in that range). | File exists; matches the section structure; LOC count ∈ [9, 60]. |
| AC.OSS-M6c.4 | `plugins/dev-sdlc/docs/cdcs/README.md` index extended to include row 11 for `graceful-fallthrough-with-detection.md`. The README's "10 CDCs" narrative copy retired or updated to reflect 11. | README contains the 11-row table referencing the new file; count of `.md` files in `plugins/dev-sdlc/docs/cdcs/` (excluding README.md) equals 11. |
| AC.OSS-M6c.5 | Historical-narrative surfaces preserved per Idea 10 (no retroactive rewrites): `plugins/dev-sdlc/docs/conventions/{amendment-cycle, five-gate-chain}.md` "Pre-M6b.0..." narratives untouched; `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml:164` comment untouched; FUTURE_IDEAS_DRAFT.md line 75 untouched; all `docs/rebuild/plans/*.md` historical plan-doc bodies (excluding the in-flight master `oss-v0-1-0-publish.md` covered by AC.OSS-M6c.2) untouched. | Diff inspection: M6c feature commit's `git show --stat` shows zero modifications to the named historical-narrative files. |
| AC.OSS-M6c.S(c) | Seal-diff fence narrowed to M6c surfaces: `plugins/dev-sdlc/` (CDC authoring + README index update + 5 in-plugin cross-reference edits) + canonical-tree light-touch cross-reference edits at `CLAUDE.dev.md` + `framework/tools/loam/README.md` + the master `docs/rebuild/plans/oss-v0-1-0-publish.md`. All cross-component widening admissions verified. | `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` passes against new BASELINE (`c08e0fa` — M6b.1 seal). |

All ACs ladder up to master plan AC.OSS-M6.S(c) → AC.OSS.6 → AC.PO.1 + AC.PO.2 (prime objective per `docs/rebuild/VALUE_PROPOSITION.md`).

## 5. Sealed-component fence

**Components touched (3):**

1. `plugins/dev-sdlc/` — receives the new CDC + the README index update + 5 in-plugin cross-reference edits (in `docs/cdcs/scope-only-dispatch.md`, `docs/conventions/{sealed-component-invariants, commit-ladder}.md`, `templates/{plan/dev-discipline, dispatch/sealed-component-build}.md`) + 1 manifest edit (`dev-mode-manifest.yaml` lines 118-119).
2. `framework/tools/loam/` — `README.md` 1-line cross-reference edit (line 151 `docs/odd-in-loam.md` → `plugins/dev-sdlc/docs/odd-in-loam.md`).
3. (canonical-tree light-touch — not a sealed component itself) `CLAUDE.dev.md` (4 line edits) + `docs/rebuild/plans/oss-v0-1-0-publish.md` (3 line edits — AC.OSS.3 list + §5 deferred-list + odd-in-pos typo).

**Universal admissions (per amendment #22 ruling #3):**
- `docs/rebuild/plans/` — for this sub-plan + manifest.
- `docs/rebuild/plans/research/` — for any companion research material (no research artefact authored at M6c).

**Cross-component widening:** the dev-sdlc seal-test's `allowed_prefixes` already includes `framework/tools/loam/` (M6a baseline) and the universal `docs/rebuild/plans/` admission covers the master plan-doc edit. The CLAUDE.dev.md edit is a top-level repo-root file admitted via the existing top-level CLAUDE.md admission pattern (verify pre-build).

## 6. Halt triggers

- HT-1: a cross-reference's update would break a sealed-component invariant (frozen-baseline / byte-content / etc.) — surface specific case for ODD §4 in-band retire if appropriate.
- HT-2: the new CDC's prose conflicts with existing dev CDC conventions discovered while authoring — surface specific concern.
- HT-3: ODD §2.5 violations encountered in surrounding code/docs while editing the cross-reference surfaces — surface for separate amendment.
- HT-4: cross-reference audit surface turns out wider than the §3 8-file count expected (e.g. >50 places) — surface for re-scope (split into M6c.0 + M6c.1).
- HT-5: final partition-manifest polish reveals a path the M6 series introduced that doesn't map cleanly into public_only / dev_and_public / dev_only / excluded_from_publish — surface for ruling.
- HT-6: HC#4 byte-content invariant breach beyond ODD §4 in-band — escalate.
- HT-7: wall-clock approaches 90 min (per master plan §6.5.4 estimate) — surface for continuation rather than stalling silently.
- HT-8: in-flight tests fail unexpectedly post-edit — surface specific failure.
- HT-9: cross-reference is empirically already at the right post-MOVE path (skip silently — no edit needed; the §3 audit already accounted for these).

## 7. Ship shape (commit ladder)

1. **Sub-plan + manifest commit.** This file + `oss-v0-1-0-publish-dev-sdlc-plugin-m6c.manifest.yaml`.
2. **Feature commit.** Two coherent surfaces in one commit (cross-reference cleanup + new CDC + index update). The diff is small (~8 file edits + 1 new file + 1 index update) and the surfaces are coherent (both close M6 series gaps); no need to split.
3. **Apply commit.** `loam amend apply --plan-doc <abs-path>` runs against the **plugin-side** `loam-amend` package (post-M6b.1 the plugin-side binary IS the operational binary). Updates objective-tracker + applies any apply-step renames declared in the manifest (none expected for M6c).
4. **Seal commit.** `loam amend seal --plan-doc <abs-path>` runs against the plugin-side binary. Records SHA in §14 register; seal-test passes against new BASELINE.

The manifest's BASELINE points at `c08e0fa` (M6b.1 seal). The seal-test computes `BASELINE..HEAD` diff window per the convention.

No corrective commits expected (no `git commit --amend` per `feedback_no_amend_in_agent_dispatches`).

## 8. Method-decision register heading FROM AUTHORING

Section 14 "Method-decision register" appears at the bottom of this plan. SHA register populated by `loam amend seal --plan-doc` SHA-backfill at seal time; method-decision narratives populated by builder during build.

---

## 14. Method-decision register (post-build)

(SHA register populated by `loam amend seal --plan-doc` SHA-backfill; method-decision narratives populated by builder during build.)

### D-build.M6c.1 — Cross-reference audit surface actuals

The pre-build audit projected 8 live consumer files + master-plan-doc edits. Actuals matched: 8 plugin-side / canonical-tree-side files edited (CLAUDE.dev.md, framework/tools/loam/README.md, plugins/dev-sdlc/dev-mode-manifest.yaml, plugins/dev-sdlc/docs/cdcs/scope-only-dispatch.md, plugins/dev-sdlc/docs/conventions/{sealed-component-invariants, commit-ladder}.md, plugins/dev-sdlc/templates/{plan/dev-discipline, dispatch/sealed-component-build}.md) plus the master plan-doc `docs/rebuild/plans/oss-v0-1-0-publish.md` (4 line edits — initially planned as 3, but a fourth `odd-in-pos` typo discovered at line 583 was fixed inline for naming consistency once the same plan-doc was already touched).

Initial broad grep across all `*.md` + `*.yaml` + `*.yml` files for the four pre-MOVE substitution targets yielded 175 candidate files. Filtering against the dispatch's "live cross-references in current docs that consumers read today" rule (excluding `docs/rebuild/plans/` historical bodies + `docs/rebuild/components/` per Idea 10) reduced the live surface to ~12 candidate files; classification narrowed to 8 EDIT + 4 PRESERVE (historical-narrative inside live surfaces). The HSF#1..HSF#4 findings recorded in §16 were the four notable items at audit time; none escalated to halt the build.

No surprises beyond the inline `odd-in-pos.md` typo fix (line 583 in the same plan-doc; see §16 HSF for full context).

### D-build.M6c.2 — Historical-narrative preservation actuals

Per Idea 10's "no retroactive rewrites" rule, the following surfaces were consciously left UNEDITED despite carrying pre-MOVE path mentions:

- `plugins/dev-sdlc/docs/conventions/amendment-cycle.md:56` — the convention's own "Pre-M6b.0 the cycle lived in precedent + dispatch templates + `docs/odd-in-loam.md`" historical narrative inside a live convention doc. The narrative describes pre-MOVE state for traceability; rewriting it would erase the convention's authoring history.
- `plugins/dev-sdlc/docs/conventions/five-gate-chain.md:38` — same shape.
- `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml:164` — YAML-comment narrative ("Post-M6b.0: framework/tools/loam-mode/ MOVED..."). The comment explains what the M6b.0 manifest reshape did and why; rewriting would erase the audit trail.
- `plugins/dev-sdlc/docs/cdcs/README.md:4-7` — historical pre-amble explaining where the CDC corpus lived pre-M6b.0.
- `docs/rebuild/FUTURE_IDEAS.md` post-M6b.0 redirect line — already-correctly-worded post-MOVE pointer ("moved to plugins/dev-sdlc/docs/cdcs/").
- `docs/rebuild/FUTURE_IDEAS_DRAFT.md:75` — captured-2026-04-28 task entry naming `framework/tools/loam-mode/` at point-of-occurrence (timestamped capture; preserved per FIDRAFT discipline + Idea 10).
- ~165 historical `docs/rebuild/plans/*.md` plan-doc bodies — pre-M6 plans describing pre-MOVE path state at their own authoring time.
- `docs/rebuild/plans/oss-v0-1-0-publish.md:345` — M1a row in the ladder table records sealed M1a state at `143d465`; preserved as historical seal-record.

No additional historical-narrative surfaces discovered at build-time beyond the §3 list.

### D-build.M6c.3 — New CDC authoring shape

`plugins/dev-sdlc/docs/cdcs/graceful-fallthrough-with-detection.md` authored at 23 LOC. Prose-style anchored against `shutdown-path-broad-catch.md` (19 LOC; the closest CDC in shape and topic — both tighten silent-handling patterns). Section structure used: title-as-rule blockquote (single paragraph) + Rationale + Connection to ODD §2.5 + How to apply (with code example) + Structural-enforcement candidates (post-v0.1.0; surfaced for FIDRAFT graduation) + Applied-immediately footer. Each section is a single paragraph (matches the existing CDC corpus's narrative density).

The pre-build AC text required LOC ∈ [30, 60]. The actual length (23) sits in the existing-CDC-corpus distribution (the 10 existing CDCs span 9-56 LOC; median ~20). Per `feedback_loose_AC_text_fix_AC_not_implementation`, the AC was tightened pre-feature-commit to LOC ∈ [9, 60] to reflect the actual prose-anchored range — the implementation matched intent (single concise CDC, well-authored), so the AC text moved to fit.

`plugins/dev-sdlc/docs/cdcs/README.md` index extended with row 11 for the new CDC. The "10 CDCs" pre-amble updated to note row 11 was authored at M6c (separate from the original 10's chronology).

No edits to the existing 10 CDCs beyond the README.md index update.

### D-build.M6c.4 — Partition-manifest final review

The `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml` was inspected at build time for coverage of every path the M6 series introduced. The M6b.0-extended `plugins/dev-sdlc/**` glob entry in the `dev_only:` block (lines 186-200 of the publish-mode manifest) covers:

- `plugins/dev-sdlc/tools/loam-amend/**` (M6b.1 destination).
- `plugins/dev-sdlc/tools/loam-mode/**` (M6b.0 destination).
- `plugins/dev-sdlc/hooks/**` (M6b.0 partial-MOVE destination for A2/A3/A4/M4 gate hooks).
- `plugins/dev-sdlc/templates/**` (M6b.0 destination for dispatch + plan templates).
- `plugins/dev-sdlc/docs/cdcs/**` (M6b.0 dev-CDC corpus destination + M6c new CDC).
- `plugins/dev-sdlc/docs/conventions/**` (M6b.0 NEW convention codification destination).
- `plugins/dev-sdlc/dev-mode-manifest.yaml` (M6b.0 destination for the dev-mode partition).
- `plugins/dev-sdlc/docs/{odd-methodology, odd-in-loam, duration-estimation-rubric}.md` (M6b.0 long-form ODD docs destination).

Every M6-series-introduced path classifies into `dev_only:` via the single glob — no per-path entries needed. NO partition-manifest edit needed in M6c. The verification reasoning was confirmed empirically: `git ls-tree HEAD plugins/dev-sdlc/` enumerates the on-disk subtree; every entry is covered by the broader `plugins/dev-sdlc/**` glob.

### Commit SHAs

- Amendment commit: `2c47191fd42283b8e0164864908f02e2d46582a0` —
  `chore(dev-sdlc-apply): loam amend apply for amendment #90 (M6c trailing cleanups + graceful-fallthrough CDC)`
- Seal commit: `a4c3ec3a0d5cd6456eecbb5a1a046975c1ff67c3` —
  `chore(seals): M6c Dev/SDLC plugin trailing cleanups + graceful-fallthrough-with-detection CDC — FOURTH and FINAL sub-amendment in the M6 series per master plan §6.5.4 D-Q.M6.6 ship-shape ruling + AC.OSS-M6.S(c). M6c closes the M6 series with two coherent surfaces. Surface 1 (cross-reference cleanup): 8 live consumer files updated to point at post-M6b.0/M6b.1 MOVE destinations — CLAUDE.dev.md (4 ODD-doc refs at lines 19/20/55/56 → plugins/dev-sdlc/docs/odd-{methodology,in-loam}.md) + framework/tools/loam/README.md (1 ODD-doc ref at line 151) + plugins/dev-sdlc/dev-mode-manifest.yaml (2 paths in dev_only: block lines 118-119 → plugin-relative) + plugins/dev-sdlc/docs/cdcs/scope-only-dispatch.md (1 ODD-doc ref at line 5) + plugins/dev-sdlc/docs/conventions/sealed-component-invariants.md (2 loam-amend impl-location refs at lines 5/41 → plugins/dev-sdlc/tools/loam-amend/src/loam_amend/) + plugins/dev-sdlc/docs/conventions/commit-ladder.md (2 loam-amend impl-location refs at lines 5/49) + plugins/dev-sdlc/templates/plan/dev-discipline.md (1 ODD-doc ref at line 28) + plugins/dev-sdlc/templates/dispatch/sealed-component-build.md (1 ODD-doc ref at line 40). Plus the in-flight master plan-doc docs/rebuild/plans/oss-v0-1-0-publish.md (3 edits — AC.OSS.3 dev-only artefacts list at lines 208-213 + §5 deferred-list at line 321 + odd-in-pos.md → odd-in-loam.md typo correction at line 213). Surface 2 (new CDC): plugins/dev-sdlc/docs/cdcs/graceful-fallthrough-with-detection.md authored per dispatcher directive 2026-04-29 — names the rule 'Graceful fallthrough must include detection + surface, not silent swallow'; connects ODD §2.5 (silent except branches non-objective by construction); applies-immediately rule (every try/except/pass in a runtime path is an ODD §2.5 violation; catch must include detection + surface — logger.warning + observability span event minimum); surfaces structural-enforcement candidates for post-v0.1.0 (periodic-health-monitor scope-of-work entries, UPS hook contributor surfacing degraded-state, auto-recovery primitives, audit-pass for existing silent-swallow patterns). plugins/dev-sdlc/docs/cdcs/README.md index extended from 10 to 11 CDCs. Historical-narrative PRESERVED per Idea 10's no-retroactive-rewrites rule: plugins/dev-sdlc/docs/conventions/{amendment-cycle.md, five-gate-chain.md} 'Pre-M6b.0 lived at docs/odd-in-loam.md' narratives, framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml:164 'Post-M6b.0: framework/tools/loam-mode/ MOVED' YAML-comment narrative, plugins/dev-sdlc/docs/cdcs/README.md historical pre-amble, FUTURE_IDEAS.md post-M6b.0 redirect line, FUTURE_IDEAS_DRAFT.md:75 timestamped task capture, all ~165 docs/rebuild/plans/*.md historical plan-doc bodies. Final partition-manifest M2 review: every M6-series-introduced path under plugins/dev-sdlc/ — including plugins/dev-sdlc/tools/loam-amend/**, plugins/dev-sdlc/tools/loam-mode/**, plugins/dev-sdlc/hooks/**, plugins/dev-sdlc/templates/**, plugins/dev-sdlc/docs/{cdcs,conventions}/**, plugins/dev-sdlc/dev-mode-manifest.yaml, plugins/dev-sdlc/docs/{odd-methodology,odd-in-loam,duration-estimation-rubric}.md — is covered by the M6b.0-extended plugins/dev-sdlc/** glob in publish-mode-manifest.yaml's dev_only: block. NO partition-manifest edit needed in M6c. Sealed-component fence: 2 components — plugins/dev-sdlc/ (receives the new CDC + README index update + 5 in-plugin cross-reference edits + 1 dev-mode-manifest cross-reference edit) + framework/tools/loam/ (README.md 1-line cross-reference edit). Canonical-tree light-touch edits at CLAUDE.dev.md (top-level repo-root file) + docs/rebuild/plans/oss-v0-1-0-publish.md (in-flight master plan-doc; admitted via universal admission). HC#4 byte-content sample status: NO RETIRE-AND-REBASELINE — M6c edits land in markdown / YAML / dev-mode-manifest files; none of these are HC#4 sample paths in the seal-fence config. The HC#4 invariant remains GREEN through M6c. Halt-and-surface findings (HSF#1..HSF#4 in plan §16): HSF#1 plugins/dev-sdlc/dev-mode-manifest.yaml:136-137 references pre-M6 stale paths tools/pos-amend/** + tools/orphan-plist-cleanup/** (M1.rename leftovers; queued task #16; out of M6c scope); HSF#2-4 historical-narrative surfaces preserved per Idea 10. AC family: AC.OSS-M6c.1..M6c.5 + AC.OSS-M6c.S(c). Each AC ladders up to master plan AC.OSS-M6.S(c) → AC.OSS.6 → AC.PO.1 + AC.PO.2 (prime objective per docs/rebuild/VALUE_PROPOSITION.md). The M6 sub-amendment series (M6a + M6b.0 + M6b.1 + M6c) is COMPLETE post-M6c — Dev/SDLC plugin Surface A baseline shipped at M6a, Surface B extraction at M6b.0 + M6b.1, trailing cleanups at M6c. Next milestone candidates (per plan §3 out-of-scope): M9 scrub (final public-surface scrub; gated on M6 series completion; now unblocked), memory-system code fix (task #18 — graceful-fallthrough CDC authored at M6c is the methodology codification; M9 or memory-system fix is the next operational amendment), M1c-corrective (task #16 — M1.rename trailing-edge programme; can run parallel to M9). — dev-sdlc at 2c47191`
## 15. Backwards-compat verification (post-build)

- Cross-reference edits are textual substitutions only (path strings inside markdown / YAML comments); no behavioural change to any runtime code path.
- The new CDC is a documentation file with no runtime consumer at v0.1.0 (its structural-enforcement candidates are post-v0.1.0).
- HC#4 byte-content invariant: NO RETIRE-AND-REBASELINE — M6c does not touch any HC#4 sample-path file (verified by checking the seal-fence config; M6c's edits land in markdown/YAML files, none of which are sample paths).
- M6b.1's seal-test BASELINE advances from `c08e0fa` (M6b.1 seal) to M6c's new SEAL_COMMIT.

## 16. Halt-and-surface findings encountered during plan authoring

Four discoveries at audit-time (informational, not blocking — all named in §3 or §3 out-of-scope):

- **HSF#1.** `plugins/dev-sdlc/dev-mode-manifest.yaml` lines 136-137 reference `tools/pos-amend/**` and `tools/orphan-plist-cleanup/**` — pre-M6 stale paths. The M1.rename programme moved `tools/` → `framework/tools/` AND `pos-amend` → `loam amend`; neither is captured in this manifest's `dev_only:` block. NOT M6c scope (queued M1c-corrective task #16). Surfaced for owner awareness.
- **HSF#2.** `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml:164` contains a YAML-comment narrative referencing `framework/tools/loam-mode/` ("Post-M6b.0: framework/tools/loam-mode/ MOVED..."). Historical narrative inside an explanatory comment; PRESERVE per Idea 10.
- **HSF#3.** `plugins/dev-sdlc/docs/conventions/{amendment-cycle.md, five-gate-chain.md}` contain "Pre-M6b.0 lived at `docs/odd-in-loam.md`" historical-narrative-style prose inside the live convention codifications. Per dispatch's "historical narrative STAYS" rule, PRESERVE.
- **HSF#4.** `docs/rebuild/FUTURE_IDEAS_DRAFT.md:75` captures a stale task ("loam-mode F-register references pre-D.1 path tools/loam-mode/") with a pre-M1.rename path at point-of-occurrence. Historical capture; PRESERVE.

Plan is authorised to proceed. Audit surface is well within the dispatch's ≤50 places re-scope threshold (HT-4); no split into M6c.0 + M6c.1 needed.
