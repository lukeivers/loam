# Foundation revision — rebuild (Path B per OD-1) — plan-doc

**Status:** plan-doc, plan-before-code. Authored 2026-05-03 by foundation-revision plan-author dispatch.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2).
**Authority:** owner ruled Path B (re-do from strategic-decision inputs) over Path A (recover-as-authored) per OD-1 in `<pos3>/workspace/.scratch/claude-output/session-recapture-audit-2026-05-03.md` §"OD-1".
**Predecessor (killed-session work, treated as research input only):**
- `<pos3>/framework/docs/principles/principles.md` (1297 lines, 2026-05-02 13:48 PT) — F1a draft
- `<pos3>/framework/plugins/dev-sdlc/docs/odd-methodology.md` (1027 lines, 2026-05-02 13:35 PT) — F1b draft (extends existing 794-line canonical version)
- `<pos3>/framework/plugins/dev-sdlc/docs/odd-in-loam.md` (731 lines, 2026-05-02 13:49 PT) — F1c draft (replaces 1058-line canonical version)
- `<pos3>/docs/plans/foundation-revision-dependency-map-2026-05-02.md` (474 lines) — sequencing plan
- `<pos3>/docs/plans/foundation-revision-classification-pass-2026-05-02.md` (197 lines) — classification table

These are the **strategic-decision sources** — not the source-of-truth for the rebuild. The rebuild authors fresh against the recovered decisions.

---

## 1. Top-line summary

The foundation revision splits the existing monolithic ODD documentation into three tiers (principles / methodology / project-bridge) and codifies four cross-cutting principles (F4 prompt-scope-confidence; F3 swarming; F2 ruthless-feedback; M5 conflict-resolution discipline) in the canonical session-start corpus. Most of the F4/F3/F2/M5 codification has already landed in the global `~/.claude/CLAUDE.md` (verified per system-reminder); the foundation-revision rebuild closes the remaining canonical pos-v2 gaps and creates the principles-tier document that does not yet exist anywhere in canonical.

| Item | Value |
|---|---|
| Total AI-time band | **3.5–6.0 hr wall-clock** (midpoint ~4.5 hr); critical path Stage 2 → 3b → 4 |
| Owner gate-review time | ~50 min total across 5 gates (separate from AI-time) |
| Sequencing | **Three-amendment ladder** (Stage A: F4-derivation-map + classification-pass; Stage B: F1a + F1b parallel; Stage C: F1c bridge + canonical CLAUDE.md consolidation) |
| Sealed-component fences touched | **One** — `plugins/dev-sdlc/` (sealed at `0c4d9a0`); F1b re-authors `plugins/dev-sdlc/docs/odd-methodology.md` |
| Other in-flight work to coordinate with | FBE.4–7 v0.1.0 foldback ladder (orthogonal: foldback touches `framework/workspace-bootstrap/`, `framework/loam-init/`, `plugins/dev-sdlc/` source — not its `docs/` subtree, so collisions are diff-only, not lock-shaped). **Serialize:** the F1b dispatch must wait for FBE.4 seal to finish to avoid two builds racing on `plugins/dev-sdlc/`'s `index.lock` per `feedback_serialize_amendment_builds.md`. |
| Owner decisions to clear before build dispatch | **5 items** (G2 classification-pass, G3 soft-objective proxy, G4 model-selection mechanism, F1c-or-not for bridge re-author, dev-sdlc-amendment-vs-universal-admission for F1b path) |

**One-paragraph recommendation:** ship as a three-amendment ladder (FR.1, FR.2, FR.3) sequenced after FBE.4–7 seals. Use the killed-session F1a/F1b/F1c drafts as research inputs and the classification-pass table as the input partition. F1b touches a sealed component — fence on `plugins/dev-sdlc/` and amend via `pos-amend`. F1a + F1c create new files at admitted universal paths and don't touch sealed components. Owner clears the 5 decisions in §7 before FR.1 dispatches.

---

## 2. Recovered strategic decisions (from killed session, audit-cited)

The killed session reached the following decisions during a 5-hour Telegram discussion 2026-05-02 (audit Findings #3, #7, #12, with primary citation to `<pos3>/docs/plans/foundation-revision-dependency-map-2026-05-02.md` which is the killed-session's own consolidation of those decisions). Each decision below carries a citation to its source line; per `feedback_specific_claims_verified_or_marked_guess.md` every claim is sourced or explicitly marked.

### D1 — Three-tier ODD documentation split

ODD documentation serves three distinct audiences and lives at three distinct abstraction levels. Collapsing into one document creates maintenance debt and scope confusion. Split:

- **F1a — Principles tier (universal, exportable):** what ODD is, why it exists, the named failure modes. Anthropic-publish-quality bar. Lives at `framework/docs/principles/odd-principles.md` (NEW path; directory does not exist in canonical).
- **F1b — Methodology tier (loam-specific, proscriptive):** "how to do ODD in practice" with mechanical rules + descriptive practice + rationale. Re-authors existing `plugins/dev-sdlc/docs/odd-methodology.md`.
- **F1c — Project-bridge tier (mapping layer):** maps ODD's abstract concepts onto loam's concrete structures (VALUE_PROPOSITION as prime objective, ACs in amendment plans, A/B-eval runtime probes). Re-authors existing `plugins/dev-sdlc/docs/odd-in-loam.md`.

**Source:** `<pos3>/docs/plans/foundation-revision-dependency-map-2026-05-02.md` lines 30–119 (F1 split definition); audit Finding #12 names this as "Killed-session 'principles vs methodology layered relationship' — Luke's view that principles are higher tier than ODD-as-methodology" with cited Telegram messages 9680/9683/9687/9691 from 2026-05-02 17:07–17:31 UTC.

### D2 — F4 (prompt-scope-confidence) is most-broadly-applicable, NOT first-axiom

Owner ruled during the 5-hour discussion: F4 is the most-broadly-applicable principle and feeds a derivation map labelling each existing principle compose-with-F4 / independent / partial — but is NOT the strict first axiom from which all others derive. Some principles (Ruthless Feedback F2, plan-before-code, ODD itself) plausibly stand independent of F4.

**Source:** `<pos3>/docs/plans/foundation-revision-dependency-map-2026-05-02.md` lines 176–206 ("Framing correction from the original plan").

**Verification this decision has propagated:** the global `~/.claude/CLAUDE.md` (per system-reminder) carries the "most-broadly-applicable, NOT first-axiom" framing in its Universal Principles. Canonical pos-v2's `CLAUDE.md` does NOT yet carry Lens 4 (verified 2026-05-03 via Read). Canonical also has NO `framework/CLAUDE.md` file (verified via filesystem check). The killed-session pos3-local `framework/CLAUDE.md` carries Lens 4 + Lens 5 — those are pos3-only and need to land in canonical via this rebuild.

### D3 — M5 (principle-conflict resolution) is multi-signal, NOT priority-list

When two principles conflict, the resolution is NOT "F4 always beats X." It is a four-step process: (1) name the conflict; (2) name the active signals from an open list (scope-confidence, reversibility, blast radius, audience, time pressure, information asymmetry); (3) make the call given signal weights; (4) surface to user if non-obvious. **No principle always beats another.** Procedural rule: every new feedback memory carries a derivation/relationship line.

**Source:** `<pos3>/docs/plans/foundation-revision-dependency-map-2026-05-02.md` lines 209–232.

**Verification:** global `~/.claude/CLAUDE.md` (per system-reminder) carries M5 in Universal Principles. Canonical pos-v2 has no project-side mirror.

### D4 — F1a Anthropic-publish quality bar (50–100% time buffer)

F1a (principles spec) is targeted at Anthropic-publish quality — readable as a standalone document outside loam, citable by other LLM-using-systems projects. This costs 50–100% time premium over generic principle codification.

**Source:** `<pos3>/docs/plans/foundation-revision-dependency-map-2026-05-02.md` line 40 ("Premium bar means 50-100% time buffer over generic principle-codification. Estimate band for F1a: 60-120 min midpoint 90 min").

### D5 — Classification-pass partition (input to F1a + F1b authoring)

Every rule currently in ODD documentation gets classified as **principle** (universal, exportable, project-agnostic) or **methodology** (proscriptive, process-dependent, loam-specific). The killed session executed this classification: 77 rules classified across 4 sections, 41 principle / 24 methodology / 8 split / 4 ambiguous.

The 4 ambiguous items (Section E of the classification table) need owner ruling before F1b void-fill authoring proceeds. They are:
- E.1 — `feedback_background_agents.md` (background-agents-by-default): is the principle kernel "don't block the interactive channel on long work" load-bearing enough to surface in F1a?
- E.2 — Frozen-vs-floating BASELINE convention: principle kernel is "name the BASELINE before measuring", but the methodology-tier wrapping is so loam-specific that promoting only the kernel feels like cherry-picking.
- E.3 — clause-(g) pattern: is "verify the verification" load-bearing enough for its own F1a entry, or adequately covered by §5.1 "structural over advisory"?
- E.4 — Symlink-resolution finding (operational, not a classification ambiguity): pos3 had `docs/odd-methodology.md` and `docs/odd-in-loam.md` as broken symlinks; canonical has `plugins/dev-sdlc/docs/odd-{methodology,in-loam}.md` as the actual files. F1b/F1c authoring should re-author the existing rich content under the new split, NOT author from scratch.

**Source:** `<pos3>/docs/plans/foundation-revision-classification-pass-2026-05-02.md` lines 38–197 (full table) and lines 145–172 (Section E ambiguities).

### D6 — Void-fill discipline (F1b)

For every rule that moves from methodology-tier to principle-tier, F1b must NOT silently drop it — it gets void-filled with mechanical rule + descriptive practice + rationale. Void-fills are NOT checklists. Methodology is described practice including spirit and rationale. Acknowledge cases where no clean substitute exists rather than papering over.

**Source:** `<pos3>/docs/plans/foundation-revision-dependency-map-2026-05-02.md` lines 67–73; audit Finding #7 names this as "Void fills can be descriptive prose, not just checklists" with cited Telegram message 9691 (2026-05-02 17:31 UTC).

### D7 — A/B-vs-naked-Claude pattern as soft-objective probe

F1b text must include the A/B-vs-naked-Claude pattern as the operative probe for soft-objective ACs (e.g., "reduces translation burden"). Five operationalization concerns: cost discipline (representative probe set), confounders (held-constant variables), probe authoring (real transcripts not synthetic scenarios), judge bias (randomized ordering + 10% spot-check), repeatability (`claude -p` as deterministic primitive).

**Source:** `<pos3>/docs/plans/foundation-revision-dependency-map-2026-05-02.md` lines 74–84.

### D8 — Three explicit mappings in F1c

F1c (project bridge) must map exactly three things: (a) prime objective = VALUE_PROPOSITION (with the two harness-test and primary-persona-test ACs named); (b) ACs live in amendment plans (with the path convention named); (c) runtime probes are executed via the A/B eval pattern (reference F1b for the full spec).

**Source:** `<pos3>/docs/plans/foundation-revision-dependency-map-2026-05-02.md` lines 105–119.

### D9 — Principles-distribution shape (informational; F1a-installer adjacent)

Killed session reached a separate decision (audit Finding #3, captured to canonical FIDRAFT) on shipping F1a's principles in two forms: (a) ship-in-loam at the canonical path; (b) install at user's `~/.claude/` via an onboarding prompt that asks universal-vs-local install (default local). This is NOT in scope for the foundation-revision-rebuild plan-doc itself — the FIDRAFT entry covers it as a future feature. Mentioned here for completeness because the killed-session F1a draft contained installer-resolver text that this rebuild does NOT carry forward.

**Source:** audit Finding #3 (Telegram message 9683, 2026-05-02 17:15 UTC); FIDRAFT pending entry at `<pos3>/workspace/.scratch/claude-output/fidraft-captures-pending-2026-05-03-recapture.md`.

---

## 3. Four deliverables

### 3.1 — F1a — Principles spec (NEW)

| Field | Value |
|---|---|
| Target path | `framework/docs/principles/odd-principles.md` |
| Replaces | nothing (does not exist in canonical) |
| Intended shape | Anthropic-publish-quality standalone document. Two sections per principle (Definition + loam-integration). Contains the 41 principle-tier rules from the classification pass. Four foundational principles get extended treatment: F4 (prompt-scope-confidence), M5 (conflict-resolution), F2 (ruthless-feedback), F3 (swarming). Lifts text verbatim where source corpus reads cleanly; tightens otherwise. |
| Composes with | Cross-referenced by F1b (methodology cross-refs principles) and F1c (bridge links to both). |
| Sealed-component fence | NONE — `framework/docs/principles/` is a NEW directory at canonical's framework root; not under any sealed component. Universal-paths admission for the new path. |

### 3.2 — F1b — Methodology re-author (REPLACES)

| Field | Value |
|---|---|
| Target path | `plugins/dev-sdlc/docs/odd-methodology.md` |
| Replaces | existing 794-line file (sealed at `0c4d9a0`); re-author per the principle/methodology classification — moves principle-tier content to F1a (cross-ref) and void-fills with mechanical rule + descriptive practice + rationale per D6. |
| Intended shape | Loam-specific proscriptive document. Cross-references F1a for principle-tier content (no duplication). New §11 "Measurable outcomes per objective" + §12 "Demonstrated-runtime delivery" per killed-session draft. A/B-eval pattern with five operationalization concerns per D7. Updated §9 quick-reference card. |
| Composes with | Cross-referenced by F1c bridge. |
| Sealed-component fence | **`plugins/dev-sdlc/`** (sealed at `0c4d9a0`). Re-author requires sealed-component amendment via `pos-amend apply` + `pos-amend seal`. **This is the one fence the foundation-revision touches.** |

### 3.3 — F1c — Project-bridge re-author (REPLACES)

| Field | Value |
|---|---|
| Target path | `plugins/dev-sdlc/docs/odd-in-loam.md` |
| Replaces | existing 1058-line file (sealed at `0c4d9a0`); re-author per D8 — three explicit mappings (prime objective = VALUE_PROPOSITION; ACs in amendment plans; A/B-eval for runtime probes). |
| Intended shape | The mapping layer between F1a (principles) and F1b (methodology) for this specific project. Links to both; does not duplicate content from either. |
| Composes with | Read by primary persona at session-start (per existing canonical CLAUDE.md cross-references); links F1a + F1b. |
| Sealed-component fence | **`plugins/dev-sdlc/`** (same fence as F1b). Can land in the same sealed-component amendment as F1b (single seal point) or a separate one. Recommendation: same amendment to minimize seal-overhead. |

### 3.4 — Foundation-revision dependency map (OPTIONAL)

| Field | Value |
|---|---|
| Target path | `docs/plans/foundation-revision-rebuild-dependency-map.md` (proposed name; differs from killed-session's path to avoid collision) |
| Replaces | nothing in canonical; killed-session draft at `<pos3>/docs/plans/foundation-revision-dependency-map-2026-05-02.md` is preserved as research-input artefact (move to `<pos3>/workspace/.scratch/claude-output/foundation-revision-plan-killed-session-2026-05-02.md` per OD-4 recommendation). |
| Intended shape | Internal-only dependency map showing which existing principles compose-with-F4, are independent, or partial. **Same content as `framework/docs/design/principle-derivation-map.md`** (the location named in canonical CLAUDE.md Lens 4 footer, per the system-reminder of pos3's framework/CLAUDE.md). |
| Composes with | Referenced by F1a foundational-principles section. |
| Sealed-component fence | NONE — `framework/docs/design/` is at framework root; not under any sealed component. Universal-paths admission for the new file. |
| **Recommendation** | **Combine with F1a's authoring as a single deliverable** — the derivation-map is a small artefact (≤300 lines per killed-session pattern); spinning it out as a separate plan-deliverable adds coordination overhead without tightening scope. Land at `framework/docs/design/principle-derivation-map.md` per the existing canonical CLAUDE.md cross-reference (when Lens 4 lands). |

### 3.5 — Sub-deliverable: canonical CLAUDE.md update (REQUIRED)

Not a standalone deliverable, but a required sub-task that lands in FR.3 consolidation amendment. Canonical pos-v2's `CLAUDE.md` carries Lens 1, 2, 3 only (verified 2026-05-03 via Read). The killed-session pos3-local `framework/CLAUDE.md` carries Lens 4 + Lens 5 (per system-reminder). The foundation-revision rebuild MUST land Lens 4 + Lens 5 in canonical pos-v2's CLAUDE.md so the always-on lens corpus matches what the global `~/.claude/CLAUDE.md` already references. This is a small edit (~80 lines added to `CLAUDE.md`).

| Field | Value |
|---|---|
| Target path | `CLAUDE.md` (canonical pos-v2 root) |
| Replaces | nothing; appends Lens 4 + Lens 5 sections |
| Intended shape | Mirror the existing pos3-local `framework/CLAUDE.md` Lens 4 + Lens 5 text; verify text matches global `~/.claude/CLAUDE.md` framing (most-broadly-applicable, NOT first-axiom). |
| Composes with | F1a (links to it for derivation map); F1b (cross-references for methodology); F1c (cross-references for project bridge). |
| Sealed-component fence | NONE — root `CLAUDE.md` is universal-admissions per existing convention. |

---

## 4. Amendment shape

**Recommendation: three-amendment ladder** rather than single mega-amendment. Rationale: each amendment has a measurably tighter acceptance criterion than the parent (per Lens 5 swarming stopping rule); each lands a complete unit owner can gate-review independently; F1b + F1c share a sealed-component fence so they live in one amendment, but F1a + derivation-map are file-disjoint and can land separately.

### FR.1 — F1a + derivation map (no sealed-component touch)

**Scope:** create `framework/docs/principles/odd-principles.md` + `framework/docs/design/principle-derivation-map.md`. Authored against the classification-pass table (D5). Anthropic-publish quality per D4.

**Sealed-component fence:** NONE. Universal-paths admission for the two new files.
**Model:** Opus (per D4 quality bar; Anthropic-publish-shape synthesis is high-uncertainty).
**`model-rationale` line:** `model-rationale: Opus — Anthropic-publish quality bar per D4; principle-tier synthesis across 41 classified rules is high-uncertainty enough that Sonnet's plausible-but-shallow output costs more in re-author time than Opus's first-shot quality saves.`
**Scope-tightness:** mixed. Tight on file paths + classification-pass partition + cross-reference targets. Loose on internal section ordering + worked-example selection + tone calibration (Anthropic-publish bar requires editorial judgment; over-tight scope blocks the actually-correct prose shape).
**Wall-clock estimate:** 90–180 min (midpoint 135 min) per the duration rubric × premium for D4. Tool-call estimate: ~80–120 calls × 0.10–0.15 = 8–18 min IF token-shape were the only signal; the 50–100% premium for Anthropic-publish quality (synthesis + re-tightening passes) puts wall-clock at 90–180 min.

### FR.2 — F1b + F1c sealed-component amendment (single seal point)

**Scope:** re-author `plugins/dev-sdlc/docs/odd-methodology.md` + `plugins/dev-sdlc/docs/odd-in-loam.md` per D5/D6/D7/D8. Both files in the same sealed-component fence (`plugins/dev-sdlc/`); land together to minimize seal overhead.

**Sealed-component fence:** `plugins/dev-sdlc/` (sealed at `0c4d9a0`). Apply via `pos-amend apply` + `pos-amend seal` per the dev-sdlc amendment convention (mirror M6c, FBE.4 patterns).
**Model:** Sonnet (per killed-session plan §3 Stage 4 — F1b inputs are classification-pass + existing rich text; void-fill authoring is medium-confidence once classification settles. F1c is mapping-layer with three explicit decisions; clear inputs).
**`model-rationale` line:** none required (Sonnet is default).
**Scope-tightness:** tight. Classification-pass table is the input partition; void-fills follow a known three-part shape (mechanical rule + descriptive practice + rationale). F1c has three explicit mappings (D8). High confidence in outcome shape → tight scope; method (which void-fill prose, which sectioning) stays builder's call.
**Wall-clock estimate:** 60–120 min (midpoint 90 min) per duration rubric for two-file sealed-component amendment with clear classification input. Tool calls ~60–100 × 0.10–0.15 = ~6–15 min on tool calls; full wall-clock includes pos-amend apply/seal cycle, sidecar bumps, sealed-component commit ladder (~20 min overhead per the FBE.4 pattern).

### FR.3 — Canonical CLAUDE.md consolidation + tracking (no sealed-component touch)

**Scope:** add Lens 4 + Lens 5 to canonical `CLAUDE.md`; mirror text from global `~/.claude/CLAUDE.md`. Verify F1a + F1b + F1c are referenced from the consolidated CLAUDE.md (cross-references match the actual landed paths). Update STATE.md to record foundation-revision-complete row.

**Sealed-component fence:** NONE. Universal-paths admission for `CLAUDE.md` + `docs/STATE.md`.
**Model:** Sonnet (consolidation is low-uncertainty; text already exists in pos3-local form per system-reminder).
**`model-rationale` line:** none required.
**Scope-tightness:** tight. Source text exists; target text is mirror; cross-references are mechanical.
**Wall-clock estimate:** 30–60 min (midpoint 45 min). Tool calls ~30–50.

### Ladder summary

| Amendment | Scope | Sealed-component fence | Model | Wall-clock midpoint |
|---|---|---|---|---|
| FR.1 | F1a + derivation map | NONE | Opus | 135 min (range 90–180) |
| FR.2 | F1b + F1c re-author | `plugins/dev-sdlc/` | Sonnet | 90 min (range 60–120) |
| FR.3 | CLAUDE.md consolidation + STATE | NONE | Sonnet | 45 min (range 30–60) |
| **Critical-path total (sequential)** | | | | **~270 min ≈ 4.5 hr** (range 180–360 min ≈ 3.0–6.0 hr) |
| Owner gate-review (5 gates × ~10 min) | | | | 50 min (separate from AI-time) |

**Why three amendments not one:**
1. **Sealed-component fence is binary.** F1b touches `plugins/dev-sdlc/` (sealed); F1a + F1c-as-bridge + CLAUDE.md updates touch unsealed paths. Combining unsealed + sealed work in one amendment widens the fence unnecessarily and complicates `pos-amend` apply.
2. **Owner gate-review cadence.** Three landing points = three independent gate moments where owner can ship-or-halt without re-bundling.
3. **Per-amendment scope-tightening (Lens 5 stopping rule).** FR.1's AC ladder is "principles spec exists at quality"; FR.2's is "methodology + bridge re-authored under split"; FR.3's is "session-start corpus references the new layout". Each is strictly tighter than the parent foundation-revision objective; further decomposition (e.g., F1b alone vs F1c alone) would split shared fence overhead without tightening scope.

**Why FR.1 + FR.2 are NOT parallel-safe:**
- FR.2's F1b void-fills cross-reference F1a's principles by anchor. F1a anchors are determined at FR.1 authoring time. Running FR.2 before FR.1 lands forces FR.2 to author against guessed F1a anchors.
- Ordering: FR.1 → owner gate G1 (F1a quality) → FR.2 → owner gate G2 (sealed-component verification) → FR.3 → owner gate G5 (final CLAUDE.md sign-off).

**Why FBE.4–7 must seal before FR.2:**
- FR.2 touches `plugins/dev-sdlc/` (sealed component). FBE.4 currently in flight also touches `plugins/dev-sdlc/` (sidecar bump per FBE.4 plan §1). Two builds in one tree race on `index.lock` per `feedback_serialize_amendment_builds.md`. Serialize: FBE.4 → FBE.7 → FR.2.

---

## 5. Acceptance criteria

ODD-shaped (objective + acceptance, no method-in-acceptance) per Lens 3.

### AC.FR.1.* — F1a + derivation map (FR.1)

| AC | Outcome | Verification |
|---|---|---|
| **AC.FR.1.1** | `framework/docs/principles/odd-principles.md` exists at canonical pos-v2. | `test -f framework/docs/principles/odd-principles.md` exits 0. |
| **AC.FR.1.2** | The principles spec contains the 41 principle-tier rules from D5's classification pass, each with the two-section shape (Definition + loam-integration). | Section count matches; spot-check 5 randomly-sampled principles against the classification table. |
| **AC.FR.1.3** | The four foundational principles (F4 / M5 / F2 / F3) get extended treatment with the framing decisions from D2 / D3 / OD-1 audit baked in (F4 = "most-broadly-applicable, NOT first-axiom"; M5 = multi-signal four-step process). | Grep for "most-broadly-applicable" near F4 section; grep for "four-step" near M5 section. |
| **AC.FR.1.4** | `framework/docs/design/principle-derivation-map.md` exists with each principle in the corpus labeled compose-with-F4 / independent / partial. | File exists; labels grep-verifiable. |
| **AC.FR.1.5** | F1a "would read well outside loam context" — applied by Opus authoring agent's own halt-and-surface; documented in dispatch report. | Authoring agent self-asserts in dispatch report; owner confirms at G1. |
| **AC.FR.1.6** | Negative AC: zero edits to any sealed component. | `git diff <BASELINE>..<seal> --name-only` produces only paths under `framework/docs/principles/`, `framework/docs/design/`, `docs/plans/` (this plan + its manifest), and any universal-admission targets. |

### AC.FR.2.* — F1b + F1c re-author (FR.2)

| AC | Outcome | Verification |
|---|---|---|
| **AC.FR.2.1** | `plugins/dev-sdlc/docs/odd-methodology.md` re-authored: principle-tier rules from D5 classification moved out (cross-reference F1a anchors), void-fills authored per D6 for every Y in classification's "Void-fill needed?" column. | File diff shows expected restructure; grep for cross-reference anchors to F1a; void-fill sections present per classification table's Y-rows. |
| **AC.FR.2.2** | `plugins/dev-sdlc/docs/odd-methodology.md` carries the A/B-vs-naked-Claude pattern with the five operationalization concerns per D7. | Grep for "A/B" + "naked-Claude" + each of the five concerns by name (cost discipline, confounders, probe authoring, judge bias, repeatability). |
| **AC.FR.2.3** | `plugins/dev-sdlc/docs/odd-in-loam.md` re-authored to map exactly the three things in D8: (a) prime objective = VALUE_PROPOSITION with two ACs named; (b) ACs live in amendment plans with path convention; (c) runtime probes via A/B-eval (link to F1b). | Grep for "VALUE_PROPOSITION" with the two AC names; grep for "amendment plans" with path; grep for "A/B-eval". |
| **AC.FR.2.4** | Both files cross-reference F1a's `framework/docs/principles/odd-principles.md` for principle-tier content; no duplication. | Grep for the F1a path appears N times; spot-check 3 principle-tier rules absent from F1b body (only cross-referenced). |
| **AC.FR.2.5** | Sealed-component fence: `plugins/dev-sdlc/` SEAL_COMMIT advances exactly once per `pos-amend seal`; sidecar amendment-trail records the foundation-revision FR.2 landing. | `cat plugins/dev-sdlc/tests/SEAL_COMMIT` shows new SHA; sidecar file diff records FR.2 entry. |
| **AC.FR.2.6** | Negative AC: zero edits outside `plugins/dev-sdlc/` (the named fence) and admitted universal paths (`docs/plans/` for the manifest). | `git diff <BASELINE>..<seal> --name-only` produces only paths under those two trees. |

### AC.FR.3.* — Canonical CLAUDE.md consolidation (FR.3)

| AC | Outcome | Verification |
|---|---|---|
| **AC.FR.3.1** | Canonical pos-v2 `CLAUDE.md` adds Lens 4 (prompt-scope-confidence, with "most-broadly-applicable, NOT first-axiom" framing per D2). | Grep for "Lens 4" + "most-broadly-applicable" in `CLAUDE.md`. |
| **AC.FR.3.2** | Canonical pos-v2 `CLAUDE.md` adds Lens 5 (swarming, with the three reference patterns named: PlannerWorkerSwarm cycle, ModelOutput.rationale, EVAL_DIMENSIONS). | Grep for "Lens 5" + each of the three pattern names. |
| **AC.FR.3.3** | Lens 4 + Lens 5 text matches the global `~/.claude/CLAUDE.md` framing (cross-coherence). | Spot-check by reading both; flag any divergence at G5. |
| **AC.FR.3.4** | `docs/STATE.md` records foundation-revision-rebuild-complete row with FR.1+FR.2+FR.3 commit SHAs. | Grep STATE.md for "foundation-revision-rebuild" or "FR.1". |
| **AC.FR.3.5** | Negative AC: zero edits to source code or sealed components. | `git diff <BASELINE>..<seal> --name-only` produces only `CLAUDE.md` + `docs/STATE.md` + plan/manifest paths. |

### AC.FR.* — Programme-level (verified after all three amendments seal)

| AC | Outcome | Verification |
|---|---|---|
| **AC.FR.PROG.1** | Three-tier ODD documentation split is in place at canonical pos-v2: principles at `framework/docs/principles/odd-principles.md`; methodology at `plugins/dev-sdlc/docs/odd-methodology.md`; bridge at `plugins/dev-sdlc/docs/odd-in-loam.md`. All three files exist; cross-references resolve. | `test -f` each path; grep cross-references resolve. |
| **AC.FR.PROG.2** | The four foundational principles (F4 / M5 / F2 / F3) are codified in canonical's session-start corpus AND in the principles spec — both surfaces carry the same framing decisions. | Cross-grep CLAUDE.md + odd-principles.md; framing matches. |
| **AC.FR.PROG.3** | Adoption signal (3-shot per killed-session plan §6 AC.FND.11): the next 3 dispatches authored after FR.3 lands carry decomposition reasoning (Lens 5) + scope-tightness annotation (Lens 4) + demonstrated-runtime line (F1b). Soft AC; deferred to future post-foundation observation; not gating. | Observable against post-FR.3 dispatch transcripts; tracked separately. |

---

## 6. AI-time estimate

Per `feedback_duration_estimation_rubric.md` (categories + `wall_clock_min ≈ tool_calls × 0.10–0.15` formula + parallelism critical-path rule).

| Phase | Category | Tool-call band | Wall-clock midpoint | Range | Rationale |
|---|---|---|---|---|---|
| FR.1 — F1a + derivation map | full new-component cycle + Anthropic-publish premium | 80–120 calls | 135 min | 90–180 min | D4 50–100% premium; multi-section synthesis across 41 classified rules + 4 foundational principles + cross-corpus citations |
| FR.2 — F1b + F1c re-author | sealed-component amendment + void-fill authoring | 60–100 calls | 90 min | 60–120 min | Classification table is input partition (high-confidence); pos-amend apply/seal cycle adds ~20 min overhead |
| FR.3 — CLAUDE.md consolidation | medium docs edit | 30–50 calls | 45 min | 30–60 min | Mirror text exists in pos3-local; cross-reference verification |
| **Critical-path total (sequential)** | | 170–270 calls | **~270 min ≈ 4.5 hr** | **180–360 min ≈ 3.0–6.0 hr** | FR.1 → FR.2 → FR.3 with owner gates between |
| **Owner gate-review (separate)** | | — | 50 min | 30–80 min | 5 gates × ~10 min each |

**Calibration notes:**
- Killed-session plan §3 Stage 3b estimated F1a + F1b authoring at 80–140 min wall-clock midpoint 110 min in 2-agent parallel (or 110 min serial). This rebuild splits F1a (FR.1) from F1b (FR.2) for fence reasons — wall-clock is therefore higher than killed-session's parallel estimate but the comparison validates the band.
- Killed-session plan total to "foundation laid" was 2.7–4.5 hr critical-path (range matches).
- This plan adds FR.3 (CLAUDE.md consolidation) which the killed session folded into Stage 4 — same wall-clock budget, different decomposition.
- Specific-claims discipline: every duration band above is a calibrated estimate per the rubric, not a measured actual; tool-call counts are guesses based on the killed-session draft sizes (1297 + 1027 + 731 lines) and the rubric's per-line authoring rate. Actuals to be logged after each FR.* completes per `feedback_duration_estimation_rubric.md`.

---

## 7. Owner-decisions queue (BEFORE build dispatch)

Five decisions need owner ruling before the FR.1 build dispatches. Each has a recommendation; if the owner rules per recommendation, dispatch can proceed without re-planning.

### G2 — Classification-pass Section E ambiguities (gate to FR.2; recommend ruling NOW for FR.1 cross-ref planning)

The killed-session classification table has 4 ambiguous items in Section E (D5 above). Each needs a principle-vs-methodology ruling before F1a + F1b authoring proceeds.

- **E.1 — `feedback_background_agents.md`:** classify as `principle + methodology` (promote the kernel "don't block the interactive channel on long work" to F1a) OR `methodology` only (kernel too thin to surface)?
  - **Recommendation: methodology** (per killed-session's own low-confidence recommendation). Kernel is real but thin; padding it to F1a-section length adds prose without sharpening practice.
- **E.2 — Frozen-vs-floating BASELINE convention:** classify as `principle + methodology` (promote "name the BASELINE before measuring" kernel) OR `methodology` only?
  - **Recommendation: methodology** (per killed-session's own low-confidence recommendation). The convention is so loam-amendment-cycle-shaped that promoting only the kernel feels cherry-picked.
- **E.3 — clause-(g) pattern:** classify as `principle + methodology` (promote "verify the verification" to F1a) OR `methodology` only?
  - **Recommendation: methodology** (per killed-session's own low-confidence recommendation). §5.1 "structural over advisory" already covers the underlying principle; clause-(g) is the loam worked example.
- **E.4 — Symlink-resolution finding:** F1b/F1c re-author against the existing rich content under the new split, NOT from-scratch authoring?
  - **Recommendation: re-author existing content under split.** Killed-session's own recommendation; the existing 794+1058 lines of methodology + bridge content is rich and load-bearing; throwing it away forfeits captured judgment.

### G3 — Soft-objective measurability proxy class (gate to FR.2; F1b authoring needs this)

F1b's measurability discipline (per D7) requires choosing which proxy class best fits "translation burden" (AC.PO.1) and "toolkit additions" (AC.PO.2) — VALUE_PROPOSITION's two ACs. Three candidates:

- **Behavioural proxy:** dispatch-count using primitive X / month.
- **Friction indicator:** count of "I had to do step Y manually" turns in transcripts.
- **Structural proxy:** primitive exists + integration test proves primary persona can invoke it.

**Recommendation: delegate to FR.2 dispatch with autonomy-to-rule**, with the constraint that the rule choice is documented in F1b's §11 (Measurable outcomes per objective). Pre-ruling adds owner overhead for a choice the FR.2 builder can make against the actual void-fill content; delegating-with-autonomy preserves builder judgment while keeping the choice auditable.

### G4 — F3 model-selection mechanism (informational; already-resolved per system-reminder)

Killed-session plan named three strawmen (checklist agents apply; stop-hook scanning; separate review agent). The global `~/.claude/CLAUDE.md` (per system-reminder) names the resolution as a required `model-rationale: <model> — <reason>` line in every dispatch brief that selects a non-default model — closer to "checklist agents apply" than the other two.

**Recommendation: NO ruling needed.** Already resolved in global memory; FR.1's F1a authoring carries the same mechanism into the principles spec. Surfaced for owner confirmation that the global resolution is the intended one.

### G5 — F1c-or-not for `plugins/dev-sdlc/docs/odd-in-loam.md` re-author (gate to FR.2)

Canonical's existing `plugins/dev-sdlc/docs/odd-in-loam.md` (1058 lines) is currently the bridge document. The killed session proposed a F1c bridge at `docs/odd-in-loam.md` (different path; doesn't exist in canonical). Two options:

- **A — Re-author in place at existing path** (`plugins/dev-sdlc/docs/odd-in-loam.md`). Preserves the existing session-start cross-reference (canonical CLAUDE.md doesn't directly reference this file but the dev-sdlc plugin loader does). Sealed-component fence applies (same as F1b). This plan's recommendation per §3.3.
- **B — Create new bridge at `docs/odd-in-loam.md`** (canonical root) per killed-session plan path. Leaves existing `plugins/dev-sdlc/docs/odd-in-loam.md` in place (or redirects). Avoids sealed-component fence. Forces a session-start cross-reference update (not just substitution).

**Recommendation: A (re-author in place).** Cleaner audit trail; one fence amendment for F1b + F1c; preserves the existing session-start corpus shape. The killed-session's proposed `docs/odd-in-loam.md` path was authored against pos3's broken-symlink layout (per D5 E.4 finding); canonical's file IS the source of truth and lives at `plugins/dev-sdlc/docs/`.

### G6 — Sealed-component amendment shape for FR.2 (gate to FR.2 dispatch design)

FR.2 amends a sealed component (`plugins/dev-sdlc/`). Two amendment shapes:

- **A — Standard pos-amend cycle** (apply + seal): mirrors M6c, FBE.4. Sidecar bumps record the amendment-trail entry. ~20 min overhead.
- **B — Universal-paths admission** (admit `plugins/dev-sdlc/docs/odd-{methodology,in-loam}.md` as universal paths and edit without sealed-component cycle): cleaner for docs-only edits but bypasses the seal-trail audit.

**Recommendation: A (standard pos-amend cycle).** Documentation IS load-bearing for the dev-sdlc plugin's contract (the plugin's own users read these files); changing them deserves the same audit-trail discipline as code changes. Mirror FBE.4 fence pattern. Surface to owner for confirmation since universal-paths admission has been used for some doc edits in FBE.7 (CLAUDE.md, docs/odd-in-loam.md per FBE.7 manifest) — the precedent exists.

---

## 8. Risk register

Risks that could force re-planning during execution.

| # | Risk | Likelihood | Mitigation |
|---|---|---|---|
| R.1 | F1a Anthropic-publish quality bar takes 2× the upper estimate (e.g., 4+ hr instead of 1.5–3 hr). | Medium. Killed-session draft is 1297 lines — substantial; re-doing at quality from classification-pass partition is non-trivial. | If Opus dispatch reports >180 min wall-clock or >150 tool calls, halt + surface; owner reviews progress + decides continue-vs-checkpoint. |
| R.2 | Section E ambiguities (G2) ruling diverges from the killed-session recommendations and forces classification-pass re-work. | Low. Three of four E-items have already been recommended-as-methodology by the killed session itself. | If owner rules differently from recommendations, FR.1 dispatch absorbs the re-classification (owner-decision documented in dispatch brief). |
| R.3 | FBE.4–7 ladder slips and serializes against FR.2 longer than expected. | Medium. FBE.4 is currently in flight; FBE.5/6/7 are downstream. | Monitor FBE seal commits; FR.1 can launch independently of FBE state (no fence overlap). FR.2 dispatch waits for FBE.4 + any other dev-sdlc-touching FBE seal. |
| R.4 | F1b void-fill authoring under-delivers (skipping void-fills, summarizing into checklists) and violates D6. | Low–medium. D6 is explicit about discipline; FR.2 dispatch carries D6 in scope. | Halt-trigger in FR.2 dispatch: any void-fill that's a checklist instead of mechanical-rule + descriptive-practice + rationale = halt and surface. |
| R.5 | F1a + F1b cross-reference anchors drift between FR.1 landing and FR.2 dispatch (FR.2 cross-refs to F1a anchors that don't exist). | Low. FR.1 → owner gate G1 → FR.2 sequencing means FR.2 reads the actual landed F1a before authoring cross-refs. | Per `feedback_verify_post_amendment_state.md`: FR.2 dispatch READS the actual landed F1a (not a prior agent's report) before authoring cross-references. |
| R.6 | Canonical CLAUDE.md Lens 4 + Lens 5 text drifts from global `~/.claude/CLAUDE.md` text. | Low. Source-of-truth is the global file (per system-reminder). | FR.3 dispatch reads the global file at authoring time and mirrors verbatim where prose; tightens or rewrites only with explicit dispatch-report rationale. |
| R.7 | Killed-session F1a/F1b/F1c drafts re-surface as Path-A-style pressure ("just recover what was already authored"). | Low. OD-1 ruled Path B explicitly. | Plan-doc itself is the authority; treat killed-session drafts as research input only, never as source-of-truth (per OD-1 reasoning: mid-discussion shape bakes in pre-conclusion bias). |

---

## 9. Cross-references

**Spec-objective placement.** The foundation revision binds to:
- **AC.PO.1 + AC.PO.2** (prime objective per `docs/VALUE_PROPOSITION.md`) — the principles spec + methodology + bridge are the authoring discipline that delivers the harness-test and primary-persona-test scope of the prime objective.
- **`feedback_value_proposition_as_prime_objective.md`** — every component/feature/amendment ladders up to VALUE_PROPOSITION; the foundation revision codifies the discipline that operationalizes this.
- **AC.FND.* family** in killed-session plan §6 — the rebuild's AC.FR.PROG.* family is a partition of those (FR.1 covers AC.FND.1-3+7+10; FR.2 covers AC.FND.6+8+9; FR.3 covers AC.FND.4-5; AC.FND.11 carries forward as AC.FR.PROG.3 soft AC).

**Predecessor artefacts (research-input only):**
- `<pos3>/framework/docs/principles/principles.md` — F1a draft.
- `<pos3>/framework/plugins/dev-sdlc/docs/odd-methodology.md` — F1b draft.
- `<pos3>/framework/plugins/dev-sdlc/docs/odd-in-loam.md` — F1c draft.
- `<pos3>/docs/plans/foundation-revision-dependency-map-2026-05-02.md` — sequencing source.
- `<pos3>/docs/plans/foundation-revision-classification-pass-2026-05-02.md` — classification table source (D5).
- `<pos3>/workspace/.scratch/claude-output/session-recapture-audit-2026-05-03.md` — audit + OD-1 ruling.

**Sibling plans (format reference):**
- `docs/plans/oss-v0-1-0-publish.md` — master-plan format.
- `docs/plans/v0-1-0-foldback-scope-expansion-fbe4.md` — sealed-component sub-plan format with sidecar fence.

**Composes with in-flight work:**
- FBE.4–7 v0.1.0 foldback ladder — orthogonal; FR.2 serializes after FBE.4 + any dev-sdlc-touching FBE seal per `feedback_serialize_amendment_builds.md`.

---

## 10. Summary for owner gate-review

| Decision point | What owner rules on | When |
|---|---|---|
| **G2 — Classification ambiguities** | Confirm or override 4 Section E recommendations (E.1/E.2/E.3 → methodology; E.4 → re-author existing) | BEFORE FR.1 dispatch |
| **G3 — Soft-objective proxy class** | Pre-rule OR delegate-with-autonomy for AC.PO.1/AC.PO.2 measurement shape | BEFORE FR.2 dispatch |
| **G4 — Model-selection mechanism** | Confirm `model-rationale` line is the resolved mechanism (already in global CLAUDE.md) | Informational; no blocking ruling |
| **G5 — F1c path (in-place vs new)** | Confirm A (re-author in place at `plugins/dev-sdlc/docs/odd-in-loam.md`) | BEFORE FR.2 dispatch |
| **G6 — FR.2 amendment shape** | Confirm A (standard pos-amend cycle) vs B (universal-paths admission) | BEFORE FR.2 dispatch |
| **G1 — F1a Anthropic-publish quality** | Spot-read F1a after FR.1 lands; confirm quality before FR.2 cross-refs to it | AFTER FR.1 lands |

---

*Plan-doc authored 2026-05-03 by foundation-revision plan-author dispatch. No source code changed. No commits made by this dispatch (this plan-doc itself is the only canonical-tree write). Three-amendment build ladder (FR.1 → FR.2 → FR.3) proceeds after owner clears decisions G2/G3/G5/G6 and FBE.4 seals. Status surfaced to dispatcher at `<pos3>/workspace/.scratch/claude-output/foundation-revision-plan-status-2026-05-03.md`.*
