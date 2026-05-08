# dev-pattern simplifications 1 — manifest narrative collapse + manifest+apply commit merge + amendment-number deprecation

**Working directory.** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.

**Status.** Plan (pre-build). 2026-05-04.

**Source authority.** `docs/plans/cost-audit-loam-dev-pattern-2026-05-04.md` recommendations A, D, E (§3.2, §3.1-partial, §3.4) + §5 priorities 1, 4, 5.

**Audience.** Build agent (this dispatch). Owner gate-review on completion.

---

## §1 — TLDR

Three simplifications to the loam-amend dev pattern, landed as a single sealed amendment (`dev-pattern-simplifications-1`) on the `dev-sdlc` plugin component:

- **A (manifest narrative collapse).** Replace `narrative.body` (~80% duplicate of plan-doc) with a `plan_doc_ref` pointer. Forward-only schema change at v3; v1 / v2 manifests still parse unchanged.
- **D (manifest+apply commit merge).** `loam amend apply` stages the manifest YAML alongside BASELINE/sidecar bumps and produces ONE commit, not two. Eliminates the human-authored "manifest baseline" precursor commit.
- **E (amendment-number deprecation).** New manifests omit `amendment.number`; identification is by `slug` only. Existing v1 / v2 manifests preserved; v3 makes `number` optional.

Net effect after this lands: every future amendment ships 1 ceremony commit at apply time (not 2), with ~150 fewer LOC of duplicated narrative authoring per amendment, and no ceremonial number to assign.

This amendment ITSELF uses the OLD format end-to-end (schema_version 1, amendment.number assigned, manifest authored as a separate commit then `loam amend apply` runs the legacy two-commit path) because the schema being introduced is the schema this amendment introduces. Once sealed, NEW amendments use the new schema.

---

## §2 — Spec placement (CLAUDE.md §2.5)

Per ODD §2.5 (no non-objective code), every line maps to a named AC under `AC.DPS1.*`. The simplifications are the actual product; the surrounding doc is anchor for the AC family. The `loam-amend` schema + apply path is the fence; tests for each AC live under `plugins/dev-sdlc/tools/loam-amend/tests/`.

---

## §3 — Lens analysis

### Lens 1 — Claude leverage

The simplifications are pure dev-pattern internal — no Claude-API surface to compose on. The simplifications REDUCE per-cycle work the dispatched agent has to do (one less commit, ~150 LOC less narrative, no amendment-number lookup). The Claude leverage is *in* the dispatcher: agents stop authoring duplicated narrative content.

### Lens 2 — Harness + primary-persona value

- **Primary-persona test.** Reduces translation burden: the agent no longer has to translate plan-doc content into a manifest narrative.body shape. Pass.
- **Harness test.** Adds nothing to the harness (in fact, simplifies it). The cost-audit's verdict holds: this is removing redundancy, not adding capability. Acceptable per cost-audit Recommendations A/D/E being SIMPLIFY verdicts, not BUILD verdicts.

### Lens 3 — ODD authoring

Outcome stated; method (which lines change in `manifest.py`, `apply.py`, etc.) left to the builder. AC family `AC.DPS1.*` defines pinned outcomes; component fence is `plugins/dev-sdlc/`.

### Lens 4 — Prompt scope ↔ confidence

**High confidence on outcome shape** (cost-audit was specific; verdicts are SIMPLIFY with clear targets). Tight scope warranted. Method left to builder per Lens 3.

### Lens 5 — Swarming

Three discrete simplifications. Each independent: A is a schema change, D is an apply-path change, E is a schema-field deprecation. Could be three sub-amendments but the combined coordination overhead would dwarf the cost; bundling as one cycle is correct (each sub-task's AC isn't tighter than the parent's individually — they're sibling slices, not nested).

`max_planner_depth: 1` — no sub-planners.

---

## §4 — Acceptance criteria (`AC.DPS1.*`)

### Schema (Recommendation A — manifest narrative collapse)

- **AC.DPS1.1** — `Manifest` dataclass exposes a `plan_doc_ref` field (str, nullable), populated when manifest sets `plan_doc_ref:` at top level.
- **AC.DPS1.2** — Schema version 3 manifests MUST set `plan_doc_ref:` when `narrative:` is omitted; MAY set both `narrative:` and `plan_doc_ref:` for transitional manifests authored mid-flip; MUST set at least one of the two so the seal step has a target. Validator surface enforces this.
- **AC.DPS1.3** — Schema version 1 / 2 manifests keep their existing semantics: `narrative.body` carries the seal-narrative text; `plan_doc_ref` is rejected with `InvalidField` if present (forward-only field).
- **AC.DPS1.4** — When schema 3 manifests carry `plan_doc_ref` only (no `narrative.body`), `loam amend seal` synthesizes a 5-15 line seal-narrative body from `<title> + apply-commit-SHA + plan_doc_ref + smoke-summary` and appends it to the configured `narrative.target`. The full plan-doc content is NOT inlined.
- **AC.DPS1.5** — `narrative.target` remains required at v3 (the seal-narrative file path is load-bearing for component-boundary audit). `narrative.body` is replaced by the synthesized summary when `plan_doc_ref` mode is in use.

### Apply-path (Recommendation D — manifest+apply commit merge)

- **AC.DPS1.6** — `loam amend apply` (non-dry-run, schema 3 manifest) stages the manifest YAML in addition to the per-component seal-test + sidecar paths and produces a SINGLE commit with subject `chore(amend): <description> manifest+apply — <comp1>[+...] BASELINE+sidecar bump to <baseline-short>`.
- **AC.DPS1.7** — Schema 1 / 2 manifests preserve the legacy two-commit shape (manifest commit human-authored, apply commit auto-generated). The schema-version gate is the decision point.
- **AC.DPS1.8** — When the manifest YAML is already committed at apply-time (legacy two-commit path or repeated apply), `git add` of the manifest YAML produces no staged change and the apply commit's content matches today's behavior — backward-compatible.
- **AC.DPS1.9** — Idempotent re-runs (no BASELINE/sidecar deltas, no manifest YAML change) skip the commit per existing AC.LAE.1.

### Schema (Recommendation E — amendment-number deprecation)

- **AC.DPS1.10** — Schema version 3 manifests MAY omit `amendment.number`. When omitted, `Manifest.number` carries `None` (typed `int | None`). Existing v1 / v2 manifests REQUIRE `amendment.number` (backward-compat).
- **AC.DPS1.11** — Apply / seal commit subjects degrade gracefully when `manifest.number is None`: the body line `Apply commit for amendment #<N> (<slug>)` becomes `Apply commit for amendment <slug>` (no `#N` prefix). Subjects use `slug` exclusively for identification.
- **AC.DPS1.12** — `loam amend new-plan` scaffolding does NOT pre-fill an amendment number. The vars-file scaffold drops any number-prefilling lines.

### Backward compatibility (cross-cutting)

- **AC.DPS1.13** — All 106 existing manifest YAMLs (schema 1 + schema 2) under `docs/plans/` continue to validate clean post-amendment (`loam amend validate <path>` returns 0 for all of them). This is the hard backward-compat guarantee.
- **AC.DPS1.14** — All sealed amendments in canonical history (HEAD pre-build) continue to seal-test clean post-amendment (no schema-change-induced fence breakage).

### Tests

- **AC.DPS1.15** — Each AC.DPS1.{1..14} carries at least one explicit pytest under `plugins/dev-sdlc/tools/loam-amend/tests/` named `test_AC_DPS1_<n>_<slug>.py`. The v3 schema has tests for: clean v3 manifest validates, v1 manifest with `plan_doc_ref:` rejects, v3 manifest without `plan_doc_ref:` AND without `narrative:` rejects, v3 manifest without `amendment.number` validates, apply produces 1 commit (not 2) under v3, apply preserves 2-commit shape under v1/v2.

---

## §5 — Behaviour-count table

| # | Declared behaviour | AC |
|---|--------------------|-----|
| 1 | `plan_doc_ref` field on Manifest dataclass | AC.DPS1.1 |
| 2 | v3 schema requires plan_doc_ref or narrative.body | AC.DPS1.2 |
| 3 | v1/v2 reject plan_doc_ref | AC.DPS1.3 |
| 4 | seal synthesizes summary from plan_doc_ref | AC.DPS1.4 |
| 5 | narrative.target still required at v3 | AC.DPS1.5 |
| 6 | apply produces single commit under v3 | AC.DPS1.6 |
| 7 | v1/v2 preserve two-commit shape | AC.DPS1.7 |
| 8 | Already-committed manifest YAML produces no extra staged change | AC.DPS1.8 |
| 9 | Idempotent re-run skips commit | AC.DPS1.9 |
| 10 | amendment.number optional at v3 | AC.DPS1.10 |
| 11 | Commit subjects degrade gracefully without number | AC.DPS1.11 |
| 12 | new-plan does not prefill number | AC.DPS1.12 |
| 13 | Existing manifests validate clean | AC.DPS1.13 |
| 14 | Existing seals stay green | AC.DPS1.14 |
| 15 | Per-AC tests authored | AC.DPS1.15 |

---

## §6 — Hard constraints

1. **No `--amend`.** Corrective NEW commits only.
2. **Scope fence.** All implementation lives under `plugins/dev-sdlc/` (loam-amend tool + dev-mode partition manifest). No edits outside this fence except universal-admitted paths (this plan-doc, manifest YAML, STATE.md if release-row needed).
3. **Plan-before-code.** This plan exists; a builder-plan is OPTIONAL — the spec here is tight enough that the builder may go straight to code.
4. **No new third-party dependency.** Stdlib + existing deps only.
5. **Backward-compat preserved unconditionally.** AC.DPS1.13 + AC.DPS1.14 are gating.
6. **CDC adherence.** Standard sealed-amendment CDC: seal-test stays green; widening only via manifest; manifest validates; apply lands clean.
7. **Forward-only schema.** Schema version 3 is purely additive in capability — v1 + v2 manifests preserved verbatim. No retroactive rewrite of historical manifests.
8. **Single sealed amendment.** Bundle all three simplifications into one cycle — coordination overhead of three cycles dwarfs the per-recommendation isolation benefit.

---

## §7 — Out of scope

- **Seal-narrative compression to summary+link** — that's amendment 2 of this dispatch series (held per dispatch text §"out of scope").
- **Principle-reminder hook compression** — held; lives in pos3, not pos-v2.
- **v0.1.8 work** — held until simplifications complete.
- **Retroactive rewrite of existing manifests** — preserved as-is. Forward-only.
- **Cycle decomposition / multi-cycle release ladder shape** — out of scope per cost-audit §3.3 (KEEP).
- **STATE.md / roadmap / eric-final triple-update** — out of scope (cost-audit §4.3 verdict was low-priority).
- **Plan-doc inflation** — out of scope (cost-audit §4.1 verdict was separate cycle).
- **Per-component .venv** — out of scope (cost-audit §4.2 verdict was KEEP).

---

## §8 — Implementation order

1. Read session-start corpus (CLAUDE.md, cost-audit doc, in-flight plans).
2. Read this plan + the cost-audit at §3.1 / §3.2 / §3.4 / §5.
3. Land schema v3 surface in `loam_amend/manifest.py` (additive `plan_doc_ref` field, `number` typed `int | None`, version gate).
4. Update `Manifest` dataclass + `load_manifest` parser to recognize v3 + add the v3-specific validation rules (AC.DPS1.2 / AC.DPS1.3 / AC.DPS1.5 / AC.DPS1.10).
5. Update `commands/apply.py` to:
   - For v3 manifests: stage `manifest_path` alongside seal-test + sidecar paths.
   - For v3 manifests: emit subject with `manifest+apply` token instead of `apply`.
   - For all schema versions: degrade gracefully when `manifest.number is None`.
6. Update `commands/seal.py` to:
   - For v3 manifests with `plan_doc_ref` only: synthesize the seal-narrative body (5-15 lines) from `<title> + apply-commit-SHA + plan_doc_ref + smoke-summary`.
   - For v1/v2: preserve existing `narrative.body` writing path verbatim.
   - Degrade gracefully when `manifest.number is None`.
7. Update `commands/new_plan.py` vars-file scaffold to drop number-prefilling.
8. Author tests for AC.DPS1.{1..15}.
9. Run `loam amend validate` against ALL existing manifests (`find docs/rebuild/plans -name "*.manifest.yaml"`) to verify backward-compat. Capture results.
10. Run touched-component test suite (`pytest plugins/dev-sdlc/tools/loam-amend/tests/`) — full pass required.
11. Author this amendment's manifest YAML at `docs/plans/dev-pattern-simplifications-1.manifest.yaml` (using OLD shape — schema_version 1 — because this IS the amendment introducing v3; the manifest itself is the LAST one to use the legacy shape).
12. Commit the manifest YAML manually (the legacy two-commit path) → `loam amend apply` → `loam amend seal` per the standard ladder.
13. Land status file at `/Users/lukeivers/pos3/workspace/.scratch/claude-output/dev-pattern-simplifications-1-status-2026-05-04.md`.
14. Reply to dispatcher with: seal SHAs, ACs satisfied, smoke outcome, halt-and-surface findings.

---

## §9 — Bookkeeping surface

This amendment uses the OLD shape end-to-end:

- `schema_version: 1`
- `amendment.number` assigned (next free integer = 133, since 132 was workspace-bootstrap-framework-only-to-main and the dispatcher's audit said 131 was Cycle 4; verify at build time).
- Two-commit ladder: human-authored manifest commit → `loam amend apply` (auto-commit) → `loam amend seal` (deterministic seal-commit).
- Component fence: `dev-sdlc` (the loam-amend tool's parent component).

The NEW shape (v3) becomes available IMMEDIATELY post-seal for the next amendment.

### Manifest stub

```yaml
schema_version: 1
amendment:
  number: <next free integer>
  slug: dev-pattern-simplifications-1
  title: "Dev-pattern simplifications #1 — manifest narrative collapse + manifest+apply commit merge + amendment-number deprecation"
baseline: <pre-apply HEAD>
plan: docs/plans/dev-pattern-simplifications-1.md
components:
  - name: dev-sdlc
    seal_test: plugins/dev-sdlc/tests/test_no_sealed_amendments.py
    sidecar: plugins/dev-sdlc/tests/SEAL_COMMIT
universal_paths:
  prefixes: [docs/plans/]
  files:
    - CLAUDE.md
    - docs/odd-in-loam.md
    - docs/odd-methodology.md
    - docs/STATE.md
narrative:
  target: plugins/dev-sdlc/seals/SEAL_COMMIT.dev-pattern-simplifications-1
  body: |
    (concise narrative referencing this plan-doc + outcome summary;
    intentionally short to model the new pattern)
```

---

## §10 — Halt triggers

1. Cross-component scope expansion beyond `plugins/dev-sdlc/`. Halt.
2. Backward-compat (AC.DPS1.13 / AC.DPS1.14) cannot be preserved. Halt + surface.
3. ODD-violating shape becomes strongly required. Halt; owner rules.
4. A new third-party dependency becomes required. Halt.
5. Wall-time exceeds 5 hours. Halt with current state per dispatch text.
6. ODD violation observed in surrounding code/docs (per `feedback_subagent_odd_violation_halt`). Halt; do NOT extend.
7. Sealed-amendment in canonical history fails to validate post-schema-change. Halt + surface.
8. More than 5 in-build decisions need owner escalation. Halt + describe.

---

## §11 — Decisions

### D-1 — Schema version bump path: v3 (skip 2.5)

**Recommendation.** Bump to schema v3 (already exists v1, v2). The change is non-trivial (multiple field shifts: plan_doc_ref add, number optional, narrative.body optional). Major version step is the right unit.

**Why it matters.** A schema bump is the explicit signal to readers that the YAML shape has shifted. Downstream tooling can branch on `schema_version`.

### D-2 — `narrative` block at v3: keep `target`, drop `body`

**Recommendation.** v3 manifests still set `narrative.target` (the seal-narrative file path). `body` is OPTIONAL at v3; when omitted, the seal step synthesizes a 5-15 line summary from `plan_doc_ref` + apply-commit metadata.

**Why it matters.** The seal-narrative file IS load-bearing — it's the per-component-boundary audit-trail file at `framework/<comp>/seals/SEAL_COMMIT.<slug>`. Removing `target` would lose that. Removing `body` reproduces the cost-audit's win.

### D-3 — Default schema for new manifests: v3

**Recommendation.** `loam amend new-plan` scaffolding (vars-file + plan-doc) generates v3-shaped output going forward. Existing v1/v2 manifests still validate, but new authored manifests default to v3.

**Why it matters.** The win only realizes if new amendments adopt the new shape. Default-v3 is the forcing function.

### D-4 — Single sealed amendment vs three

**Recommendation.** Bundle as ONE sealed amendment (per §6 constraint 8).

**Why it matters.** Three cycles of ceremony to remove ceremony is self-defeating. The three changes share the same component fence (`dev-sdlc`) and the same release-note shape; coordination overhead of three cycles >> isolation benefit per recommendation.

### D-5 — Use the OLD shape for THIS amendment's manifest

**Recommendation.** Use schema_version 1 for `dev-pattern-simplifications-1.manifest.yaml`. This IS the amendment introducing v3; using v3 inside the amendment that introduces v3 creates a chicken-and-egg. The simpler path: this manifest is the LAST one authored in v1 shape; everything after uses v3.

**Why it matters.** Avoids the recursive-bootstrap pattern; reduces build-time risk.

### Decision summary

| Decision | Recommendation | Why it matters |
|---|---|---|
| D-1 — Schema version bump path | v3 (clean major bump) | explicit signal to readers + tooling |
| D-2 — narrative block at v3 | keep target, drop body | preserve audit-trail file; reproduce win |
| D-3 — default for new manifests | v3 | forcing-function so the win realizes |
| D-4 — single vs three amendments | one sealed amendment | three cycles to remove ceremony is self-defeating |
| D-5 — shape of THIS manifest | old (v1) | avoid recursive-bootstrap chicken-and-egg |

---

## §12 — Halt-and-surface findings

Per `feedback_subagent_odd_violation_halt`: halt and surface any ODD violation observed in surrounding code/docs.

**(none observed during plan authoring.)**

---

## §13 — References

- `docs/plans/cost-audit-loam-dev-pattern-2026-05-04.md` — source authority for Recommendations A/D/E.
- `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/manifest.py` — schema definition.
- `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/commands/apply.py` — apply-time logic.
- `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/commands/seal.py` — seal-time logic.
- `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/commands/new_plan.py` — vars-file scaffolder.
- `CLAUDE.md` — design lenses + ODD authoring discipline.

---

## 14. Commit SHAs

(populated by `loam amend seal --plan-doc` post-build)

### Commit SHAs

- Amendment commit: `990e60a56e1cfabe6f0066973e186bb0ba57b688` —
  `docs(plans): tighten §14 heading shape for loam-amend seal regex`
- Seal commit: `019cfca7fd2a117c32b824ee4f09edefcac70da9` —
  `chore(seals): dev-pattern-simplifications-1 — dev-sdlc at 990e60a`
