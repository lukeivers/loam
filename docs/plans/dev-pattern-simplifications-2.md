# dev-pattern simplifications 2 — seal-narrative compression (recommendation B)

**Working directory.** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.

**Status.** Plan (pre-build). 2026-05-04.

**Source authority.** `docs/plans/cost-audit-loam-dev-pattern-2026-05-04.md` recommendation B (§3.1 verdict-partial, §3.2, §5 priority 2). Predecessor amendment: `dev-pattern-simplifications-1.md`, sealed at `019cfca`.

**Audience.** Build agent (this dispatch). Owner gate-review on completion.

---

## §1 — TLDR

Second of the two dev-pattern simplification amendments. Predecessor (`dev-pattern-simplifications-1`, sealed `019cfca`) introduced **schema v3** of the loam-amend manifest, which made `plan_doc_ref:` a top-level field, made `narrative.body` optional at v3, and added a synthesizer in `commands/seal.py::_resolve_narrative_body` that emits a 12-line summary when a v3 manifest carries `plan_doc_ref` only.

The schema part of recommendation B is therefore already partly landed. What remains for DPS2:

- **Enrich the v3 synthesizer.** Current synthesis emits 12 lines but lacks the dispatch-mandated content: ACs-satisfied count, smoke outcome, what shipped. Tighten the synthesizer so a v3 plan_doc_ref-only manifest produces a **5-15 line summary covering: what shipped, ACs satisfied count, smoke outcome, plan-doc reference**.
- **Add a `plan_doc_ref:` line to the seal commit MESSAGE body.** Today's seal commit message body has subject + amendment-N + bumped-sidecars + narrative-target + diff-window + sweep-summary. v3 should additionally surface `plan-doc:` as a body line so a reader of `git log` sees the pointer to the full reasoning without opening the SEAL_COMMIT.<slug> file.
- **Update `commit-ladder.md`** §3 (which still says "body from `narrative.body`") and §1 (which calls the seal commit narrative "long; copies the manifest's `seal_description`") to describe the v3 collapsed shape alongside the v1/v2 legacy shape. Backward-compat narration: existing long-form seal commits stay readable; new v3 seal commits ship the collapsed shape.
- **Update the dispatch template** (`plugins/dev-sdlc/templates/dispatch/sealed-component-build.md`) and any other prescriptive doc text that names the long-form-narrative expectation — those should describe v3 as the going-forward default.
- **Use schema v3 for THIS amendment's manifest.** DPS2 is the first amendment authored at v3; its manifest exercises the schema end-to-end (omits `amendment.number`, sets `plan_doc_ref:`, omits `narrative.body`, lands a single merged manifest+apply commit). The dispatch text names this as the validation case for the schema landed by DPS1.
- **Backward-compat hard guarantee.** Existing long-form seal commits (in canonical history) and existing v1/v2 manifests stay byte-identical and parse clean. The change is forward-only.

Net effect after this lands: every v3-authored future amendment ships a 5-15 line auto-synthesized seal narrative that names ACs + smoke explicitly, plus a seal commit message that points readers at the plan-doc.

**Estimated saved cost forward (per cost-audit §3.1 + §3.2 verdict):** ~150 LOC of duplicated narrative authoring per amendment; ~13K LOC across the corpus going forward.

---

## §2 — Spec placement (CLAUDE.md §2.5)

Per ODD §2.5 (no non-objective code), every line maps to a named AC under `AC.DPS2.*`. Component fence: `plugins/dev-sdlc/` (the loam-amend tool, dev-mode partition templates + docs). Tests for each AC live under `plugins/dev-sdlc/tools/loam-amend/tests/` named `test_AC_DPS2_*.py`.

Doc updates inside `plugins/dev-sdlc/docs/` are part of the fenced surface — those are conventions docs that prescribe the dev pattern's mechanical shape.

---

## §3 — Lens analysis

### Lens 1 — Claude leverage

Pure dev-pattern internal — no Claude-API surface. The simplifications REDUCE the per-amendment translation burden agents pay (no need to author duplicated narrative content; the synthesizer + plan-doc link carries the audit trail). Same pattern as DPS1.

### Lens 2 — Harness + primary-persona value

- **Primary-persona test.** Reduces translation burden: the agent stops authoring duplicated narrative.body content; the synthesizer + plan-doc link carries the audit trail. Pass.
- **Harness test.** The synthesizer + the doc updates are toolkit additions for the authoring workflow. Pass.

### Lens 3 — ODD authoring

Outcome stated; method (which lines change in `seal.py::_resolve_narrative_body` and `_build_commit_message`, which doc paragraphs update) left to the builder. AC family `AC.DPS2.*` defines pinned outcomes; component fence is `plugins/dev-sdlc/`.

### Lens 4 — Prompt scope ↔ confidence

**High confidence on outcome shape.** Cost-audit recommendation B + DPS1 schema landing leave the target very specific: enrich the v3 synthesizer, add `plan_doc_ref:` line to commit message, update prescriptive docs. Tight scope warranted. Method left to builder.

### Lens 5 — Swarming

Four discrete edits (synthesizer, commit-message body, two doc updates), all sharing the same component fence (`plugins/dev-sdlc/`) and the same release-note shape. Splitting into four cycles of ceremony to remove ceremony is self-defeating (DPS1's same reasoning). Bundle as ONE sealed amendment.

`max_planner_depth: 1` — no sub-planners.

---

## §4 — Acceptance criteria (`AC.DPS2.*`)

### Synthesizer enrichment (recommendation B core)

- **AC.DPS2.1** — `_resolve_narrative_body` (in `commands/seal.py`) emits a body that includes, when a v3 manifest carries `plan_doc_ref` only: (a) "what shipped" — the manifest title + slug + component(s); (b) ACs satisfied count, derived from the manifest (see AC.DPS2.2 for source); (c) smoke outcome line, derived from the manifest (see AC.DPS2.3); (d) plan-doc reference (already present); (e) the amendment-commit SHA + baseline window (already present).
- **AC.DPS2.2** — The synthesizer reads ACs-satisfied count from a new optional manifest field `ac_count: <int>` at the top level. When set on a v3 manifest, the count appears in the synthesized body as `acs-satisfied: <N>`. When absent, the line is omitted (the field is optional). v1/v2 reject `ac_count` (forward-only field; same pattern as DPS1's `plan_doc_ref` rejection).
- **AC.DPS2.3** — The synthesizer reads smoke outcome from a new optional manifest field `smoke_outcome: <str>` at the top level. When set on a v3 manifest, the value appears in the synthesized body as `smoke: <str>`. Free-form short string (e.g. "all 6 dimensions exercised"); validation is non-empty + max 200 chars + single-line. When absent, the line is omitted. v1/v2 reject `smoke_outcome`.
- **AC.DPS2.4** — The full synthesized body, with all optional fields set, fits within 5-15 lines per the dispatch's quality bar. Verified by counting lines on a representative manifest in tests.
- **AC.DPS2.5** — When `narrative.body` is set explicitly on a v3 manifest, the synthesizer returns it verbatim (existing AC.DPS1.4 invariant — preserved).

### Seal commit message body

- **AC.DPS2.6** — `_build_commit_message` (in `commands/seal.py`) appends a `Plan doc: <plan_doc_ref>` line in the seal commit message body when the manifest is schema v3 AND carries `plan_doc_ref`. Position: between "Narrative appended to" and "Diff window". Schema v1/v2 (and v3 manifests without `plan_doc_ref`) keep today's body byte-identical.
- **AC.DPS2.7** — The seal commit message subject line is unchanged across all schema versions (`chore(seals): <description> — <comp1>[+<comp2>...] at <sha-short>`). Backward compatibility for tooling that greps subjects.

### Documentation updates

- **AC.DPS2.8** — `plugins/dev-sdlc/docs/conventions/commit-ladder.md` describes BOTH the v1/v2 legacy long-form-narrative shape AND the v3 collapsed shape. The §3 line "body from `narrative.body`" gains a v3 alternative ("at v3, body synthesized from `plan_doc_ref` + `ac_count` + `smoke_outcome`"). The §1 line characterizing seal commits as "long; copies the manifest's `seal_description`" gains a v3 qualifier.
- **AC.DPS2.9** — `plugins/dev-sdlc/templates/dispatch/sealed-component-build.md` (the sealed-component build dispatch template) is verified against the new shape — if it prescribes any specific narrative-body content, the prescription is updated to name v3 collapsed shape as the going-forward default. (When inspection shows no narrative-body prescription in this template — current state — AC.DPS2.9 is satisfied by a no-op verification trace recorded in §14 of this plan.)

### Backward compatibility (cross-cutting)

- **AC.DPS2.10** — All 110 existing manifest YAMLs (schema 1 + 2 + 3) under `docs/plans/` continue to validate clean post-amendment (`loam amend validate <path>` returns 0 for all of them).
- **AC.DPS2.11** — All sealed amendments in canonical history (HEAD pre-build) continue to seal-test clean post-amendment (no schema-change-induced fence breakage). The dev-sdlc seal-test stays green at the pre-build BASELINE.
- **AC.DPS2.12** — Existing long-form `SEAL_COMMIT.<slug>` files in canonical history are NOT rewritten; the change is forward-only. Tooling that READS those files (any test or script that opens them) keeps working.

### v3-as-first-use validation (the dispatch's halt trigger #3 inverse)

- **AC.DPS2.13** — THIS amendment's manifest (`dev-pattern-simplifications-2.manifest.yaml`) is authored at schema_version 3, omits `amendment.number`, sets `plan_doc_ref:` (no `narrative.body`), sets `ac_count` + `smoke_outcome`, lands as a SINGLE merged `manifest+apply` commit (per AC.DPS1.6), and seals with the synthesized body covering all dispatch-required content. This AC is the schema's first end-to-end validation in canonical history.

### Tests

- **AC.DPS2.14** — Each AC.DPS2.{1..13} carries at least one explicit pytest under `plugins/dev-sdlc/tools/loam-amend/tests/` named `test_AC_DPS2_<n>_<short>.py` or in a single combined file `test_AC_DPS2_seal_narrative_compression.py` (matching DPS1's combined-file convention). Tests for new manifest fields cover: clean v3 manifest with `ac_count` + `smoke_outcome` validates, v1/v2 manifest with either field rejects, synthesized body contains required lines + line count fits 5-15, commit message body has `Plan doc:` line at v3, v1/v2 commit message body unchanged, full sweep over 110 existing manifests stays clean.

---

## §5 — Behaviour-count table

| # | Declared behaviour | AC |
|---|--------------------|-----|
| 1 | Synthesizer body includes what-shipped + ACs + smoke + plan-doc | AC.DPS2.1 |
| 2 | `ac_count` field — additive at v3, rejected at v1/v2 | AC.DPS2.2 |
| 3 | `smoke_outcome` field — additive at v3, rejected at v1/v2 | AC.DPS2.3 |
| 4 | Synthesized body fits 5-15 lines | AC.DPS2.4 |
| 5 | Explicit `narrative.body` still preserved verbatim at v3 | AC.DPS2.5 |
| 6 | Seal commit message body gains `Plan doc:` line at v3 | AC.DPS2.6 |
| 7 | Seal commit message subject unchanged across schemas | AC.DPS2.7 |
| 8 | `commit-ladder.md` describes both shapes | AC.DPS2.8 |
| 9 | Dispatch template verified / updated against new shape | AC.DPS2.9 |
| 10 | All 110 existing manifests still validate clean | AC.DPS2.10 |
| 11 | dev-sdlc seal-test stays green | AC.DPS2.11 |
| 12 | Existing long-form SEAL_COMMIT.<slug> files unchanged | AC.DPS2.12 |
| 13 | THIS amendment's manifest is the v3 first-use validator | AC.DPS2.13 |
| 14 | Per-AC tests authored | AC.DPS2.14 |

---

## §6 — Hard constraints

1. **No `--amend`.** Corrective NEW commits only.
2. **Scope fence.** All implementation lives under `plugins/dev-sdlc/`. No edits outside this fence except universal-admitted paths (this plan-doc, manifest YAML, STATE.md if release-row needed).
3. **Plan-before-code.** This plan exists. Builder may go straight to code.
4. **No new third-party dependency.** Stdlib + existing deps only.
5. **Backward-compat preserved unconditionally.** AC.DPS2.10 + AC.DPS2.11 + AC.DPS2.12 are gating.
6. **CDC adherence.** Standard sealed-amendment CDC: seal-test stays green; widening only via manifest; manifest validates; apply lands clean. New: the apply ladder is single-commit (v3) — no separate manifest-baseline commit.
7. **Forward-only schema additions.** `ac_count` + `smoke_outcome` are purely additive at v3; v1/v2 manifests preserved verbatim. No retroactive rewrite of historical manifests or seal commits.
8. **Single sealed amendment.** Bundle synthesizer + commit-message + doc updates into one cycle.
9. **v3 first-use validation.** This amendment's manifest IS authored at v3, exercising the schema end-to-end. If v3 doesn't actually work for this manifest, halt and surface (would mean DPS1 has a defect — dispatch halt-trigger #3).

---

## §7 — Out of scope

- **Principle-reminder hook compression** — held per dispatcher.
- **Retroactive rewrite of existing seal commits / SEAL_COMMIT.<slug> files** — preserved as-is. Forward-only.
- **v0.1.8 work** — held until this amendment lands.
- **The 2 follow-up findings from amendment 1** (loam-mode allowlist scope-shrink; seal-tool §14 regex loosen) — separate amendments later.
- **Changing the seal commit MESSAGE shape beyond adding `Plan doc:` line.** The body shape (subject + amendment-ref + bumped-sidecars + narrative-target + diff-window + sweep-summary) is preserved otherwise.
- **STATE.md / roadmap / eric-final triple-update collapse** — out of scope per cost-audit §4.3 (low-priority; separate amendment if pursued).

---

## §8 — Implementation order

1. Read session-start corpus (CLAUDE.md, cost-audit doc, DPS1 plan-doc + manifest, in-flight plans).
2. Read this plan + the cost-audit at §3.1 / §3.2 / §5.
3. Update `manifest.py`:
   - Add optional fields `ac_count: int | None = None` and `smoke_outcome: str | None = None` to `Manifest` dataclass.
   - In `load_manifest`, parse top-level `ac_count` + `smoke_outcome`; reject at v1/v2 (InvalidField); validate at v3 (`ac_count` non-negative int when present; `smoke_outcome` non-empty single-line str ≤ 200 chars when present).
4. Update `commands/seal.py::_resolve_narrative_body` to emit the dispatch-required body covering: title + slug + components + baseline + amendment-commit + plan-doc + ac_count (if set) + smoke_outcome (if set) + narrative-collapse note. Verify line count fits 5-15 across reasonable input sets.
5. Update `commands/seal.py::_build_commit_message` to append `Plan doc: <plan_doc_ref>` line (between Narrative-appended-to and Diff-window) when the manifest is schema v3 AND carries `plan_doc_ref`.
6. Update `plugins/dev-sdlc/docs/conventions/commit-ladder.md` per AC.DPS2.8 — add a v3 alternative to §1 + §3.
7. Verify `plugins/dev-sdlc/templates/dispatch/sealed-component-build.md` per AC.DPS2.9; update or record no-op trace.
8. Author tests for AC.DPS2.{1..14} as `test_AC_DPS2_seal_narrative_compression.py` (single combined file matching DPS1's convention).
9. Run `loam amend validate` against ALL existing manifests (`find docs/rebuild/plans -name "*.manifest.yaml"`, expected 110) — backward-compat sweep.
10. Run touched-component test suite (`pytest plugins/dev-sdlc/tools/loam-amend/tests/`) — full pass required.
11. Author this amendment's manifest YAML at `docs/plans/dev-pattern-simplifications-2.manifest.yaml` using **schema_version 3** (NEW shape — see §9).
12. Run the merged ladder: `loam amend apply` (single commit per AC.DPS1.6 — manifest+apply combined) → `loam amend seal --plan-doc <abs path>` (deterministic seal commit + §14 backfill).
13. Land status file at `/Users/lukeivers/pos3/workspace/.scratch/claude-output/dev-pattern-simplifications-2-status-2026-05-04.md`.
14. Reply to dispatcher with: seal SHAs, ACs satisfied, all-6-smoke-dimensions outcome, halt-and-surface findings, v3-schema-defect findings.

---

## §9 — Bookkeeping surface (uses NEW shape per dispatch)

This amendment uses the NEW v3 shape end-to-end:

- `schema_version: 3`
- `amendment.number` **OMITTED** (per AC.DPS1.10 + AC.DPS1.11 — number-deprecation; identification by slug).
- `plan_doc_ref:` set, `narrative.body` OMITTED (per AC.DPS1.2 + AC.DPS1.4 — synthesized summary).
- `ac_count: 14` + `smoke_outcome: "all 6 dimensions exercised"` (the new fields this amendment adds — used immediately).
- **Single merged `manifest+apply` commit ladder** per AC.DPS1.6 — the manifest YAML lands in the same commit as the BASELINE/sidecar bumps. `loam amend seal` runs against the merged commit.
- Component fence: `dev-sdlc` (the loam-amend tool's parent component).

### Manifest stub

```yaml
schema_version: 3
amendment:
  # number omitted — schema v3 deprecates amendment.number per AC.DPS1.10
  slug: dev-pattern-simplifications-2
  title: "Dev-pattern simplifications #2 — seal-narrative compression (recommendation B)"

baseline: <pre-apply HEAD>

plan: docs/plans/dev-pattern-simplifications-2.md
plan_doc_ref: docs/plans/dev-pattern-simplifications-2.md

ac_count: 14
smoke_outcome: "all 6 dimensions exercised"

components:
  - name: dev-sdlc
    seal_test: plugins/dev-sdlc/tests/test_no_sealed_amendments.py
    sidecar: plugins/dev-sdlc/tests/SEAL_COMMIT

universal_paths:
  prefixes:
    - docs/plans/
  files:
    - CLAUDE.md
    - docs/odd-in-loam.md
    - docs/odd-methodology.md
    - docs/STATE.md

narrative:
  target: plugins/dev-sdlc/seals/SEAL_COMMIT.dev-pattern-simplifications-2
  # body omitted — seal step synthesizes 5-15 line summary from
  # plan_doc_ref + ac_count + smoke_outcome + apply-commit metadata.
```

The synthesized body that lands at `plugins/dev-sdlc/seals/SEAL_COMMIT.dev-pattern-simplifications-2` will include the title, slug, components, baseline, amendment-commit, plan_doc_ref, ac_count, smoke_outcome, and the narrative-collapse note — exercising every line of the synthesizer.

---

## §10 — Halt triggers

1. Cross-component scope expansion beyond `plugins/dev-sdlc/`. Halt.
2. Backward-compat (AC.DPS2.10 / AC.DPS2.11 / AC.DPS2.12) cannot be preserved. Halt + surface.
3. v3 schema (just landed by DPS1) doesn't actually work for THIS amendment's manifest. Halt + surface — DPS1 defect signal.
4. ODD-violating shape becomes strongly required. Halt; owner rules.
5. A new third-party dependency becomes required. Halt.
6. Wall-time exceeds 4 hours per dispatch text. Halt with current state.
7. Backward-compat with existing long-form SEAL_COMMIT.<slug> files breaks. Halt + surface.
8. ODD violation observed in surrounding code/docs (per `feedback_subagent_odd_violation_halt`). Halt; do NOT extend.
9. More than 5 in-build decisions need owner escalation. Halt + describe.
10. Any AC ships partial. Halt + reframe per dispatch quality bar.

---

## §11 — Decisions

### D-1 — Carry ACs-satisfied count + smoke outcome in MANIFEST, not just synthesizer hardcode

**Recommendation.** Add `ac_count: <int>` + `smoke_outcome: <str>` as new top-level optional manifest fields at v3. Reject at v1/v2 (forward-only).

**Why it matters.** The dispatch wants the synthesizer to surface "ACs satisfied count" and "smoke outcome". These are per-amendment values — they MUST come from somewhere amendment-author-controlled. Manifest is the right authoring surface (consistent with how `plan_doc_ref` works). Hardcoding values inside `_resolve_narrative_body` would be wrong (each amendment has different counts + smoke outcomes).

**Alternative considered.** Parse the plan-doc's behaviour-count table to extract AC count automatically. Rejected — adds plan-doc-parser surface area for marginal authoring-time savings; manifest authoring already establishes the AC family upstream. Plain manifest field is simpler.

**Tradeoff.** Two additional optional manifest fields. Acceptable: both are forward-only at v3; both are optional; both have validation; both serve the cost-audit recommendation B target directly.

### D-2 — `Plan doc:` line in seal commit message body, not subject

**Recommendation.** Append `Plan doc: <plan_doc_ref>` as a body line, between "Narrative appended to" and "Diff window". Subject unchanged (AC.DPS2.7).

**Why it matters.** The dispatch text mentions both "subject" (no change) and "plan-doc reference" (in body content). Touching the subject would break tooling that greps `chore(seals): ...` headlines (cost-audit §3.1 verdict explicitly preserves subject). Body line is the right placement.

### D-3 — Single combined test file, matching DPS1's convention

**Recommendation.** All AC.DPS2.* tests live in `plugins/dev-sdlc/tools/loam-amend/tests/test_AC_DPS2_seal_narrative_compression.py` with one `test_AC_DPS2_<n>_*` function per AC.

**Why it matters.** DPS1 used `test_AC_DPS1_dev_pattern_simplifications_1.py` as a single combined file. Matching the precedent reduces friction for the next-amendment author who reads tests as a corpus. Per-file-per-AC is the older convention (AC35.x / AC40.x); DPS1 already pivoted away from it.

### D-4 — Use schema v3 for THIS manifest (forcing function)

**Recommendation.** This amendment's manifest is authored at schema_version 3. Numbers + body omitted; `plan_doc_ref` + `ac_count` + `smoke_outcome` set.

**Why it matters.** DPS1 deferred v3-as-first-use to "the next amendment" by design (chicken-and-egg avoidance). DPS2 IS the next amendment. If we author this manifest at v1, we'd lose the schema's first-use validation and forward-only intent gets stale. The dispatch text names this halt-trigger explicitly: "v3 manifest schema (just landed) doesn't actually work for THIS amendment's manifest → halt + surface (would mean amendment 1 has a defect)."

### D-5 — `commit-ladder.md` describes BOTH shapes, not a flip-cut

**Recommendation.** Add v3 alternative paragraphs alongside the existing v1/v2 narration. Don't delete the v1/v2 description — historical seal commits exist at the v1/v2 shape; readers of `git log` need that context.

**Why it matters.** Forward-only change with backward-compat = the doc must describe both shapes truthfully, or future readers misread historical commits. The cost saving is in NEW amendments using the new shape; the doc cost is small (~20 added lines).

### Decision summary

| Decision | Recommendation | Why it matters |
|---|---|---|
| D-1 — ACs + smoke source | new `ac_count` + `smoke_outcome` manifest fields at v3 | per-amendment values need authoring surface; forward-only; consistent with `plan_doc_ref` |
| D-2 — `Plan doc:` placement | body line, not subject | subject change breaks `git log` greps; body is right placement |
| D-3 — Test file shape | single combined `test_AC_DPS2_seal_narrative_compression.py` | matches DPS1 precedent |
| D-4 — THIS manifest's schema | v3 (forcing function + first-use validation) | dispatch halt-trigger names this explicitly |
| D-5 — `commit-ladder.md` shape | both v1/v2 + v3 paragraphs | historical commits need their narration preserved |

---

## §12 — Halt-and-surface findings

Per `feedback_subagent_odd_violation_halt`: halt and surface any ODD violation observed in surrounding code/docs.

**Observation 1 (F2 RUTHLESS FEEDBACK note for the dispatcher).** The dispatch text and the cost-audit recommendation B target slightly different artefacts:

- Cost-audit §3.1 / §3.2 / §2.6 names the **per-component `SEAL_COMMIT.<slug>` narrative file** as the redundancy target (cited 148-line `SEAL_COMMIT.v0-1-7-cycle4-one-question-pm-flow` sample). Cost claim: ~13K LOC of doc redundancy across 95 files.
- The dispatch text §"What this amendment delivers" item 1 names the **auto-generated seal commit message body** ("Subject: `chore(seals): <amendment-slug>` (no change). Body: a SHORT summary (5-15 lines)").

These are different artefacts. The synthesizer in `_resolve_narrative_body` (already landed by DPS1) writes the **`SEAL_COMMIT.<slug>` file**. The seal commit message body is built by `_build_commit_message`, which is already short (~13 lines) and doesn't duplicate the plan-doc.

**This plan covers BOTH** to honor the dispatch + the cost-audit jointly: enrich the synthesizer (cost-audit target) AND add a `Plan doc:` line to the commit message body (dispatch target). Both are appropriate work; combining them in one amendment is correct (same fence, same cycle, same audience).

If the dispatcher considers this F2 finding non-obvious enough that the work scope should be narrowed to just one of the two artefacts, halt-and-surface this plan during review and the build re-aims. As authored, the plan covers both targets without scope inflation (the synthesizer enrichment is the bigger half; commit-message line is one branch).

**Observation 2.** No other ODD violations observed during plan authoring.

---

## §13 — References

- `docs/plans/cost-audit-loam-dev-pattern-2026-05-04.md` — source authority for Recommendation B (§3.1 verdict-partial, §3.2, §5 priority 2).
- `docs/plans/dev-pattern-simplifications-1.md` — predecessor plan; DPS1 §13 explicitly held DPS2 (seal-narrative compression) for "amendment 2 of this dispatch series".
- `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/manifest.py` — schema definition (DPS1 added v3 + `plan_doc_ref`).
- `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/commands/seal.py` — `_resolve_narrative_body` + `_build_commit_message`.
- `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/commands/apply.py` — merged `manifest+apply` commit shape (DPS1 AC.DPS1.6).
- `plugins/dev-sdlc/docs/conventions/commit-ladder.md` — doc target for AC.DPS2.8.
- `plugins/dev-sdlc/templates/dispatch/sealed-component-build.md` — verification target for AC.DPS2.9.
- `CLAUDE.md` — design lenses + ODD authoring discipline.

---

## 14. Commit SHAs

(populated by `loam amend seal --plan-doc` post-build)

### Commit SHAs

- Amendment commit: `282620ec2e73f8d3a7011966103ab930d0f1ad84` —
  `chore(amend): dev-pattern-simplifications-2 manifest+apply — dev-sdlc BASELINE+sidecar bump to ce5d13e`
- Seal commit: `df3f50f69f2f67de0907e1e0506cd6ecc4895653` —
  `chore(seals): dev-pattern-simplifications-2 — dev-sdlc at 282620e`
