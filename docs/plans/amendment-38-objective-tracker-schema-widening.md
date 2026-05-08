# Plan — Amendment #38: objective-tracker schema widening (`lifted_from` provenance + `query_projection_view` API)

**Status:** authored 2026-04-25, awaiting brief-dispatch.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Pre-amendment tip:** captured at brief-dispatch time.
**Amendment number:** `#38` placeholder; renumbered at dispatch per the convention amendments #29–#37 followed. If a competing amendment lands first, this plan is the next sequential number after the new tip.
**Filename:** family-named (`objective-tracker-schema-widening`) so the path survives renumbering.
**Companion research:** `docs/plans/research/value-prop-as-root-heavy-b-migration-research.md` — the Heavy-B master research artefact; this sub-plan is amendment 1 of the four-amendment Heavy-B sealed-component programme.

**Sibling work in this programme.** This is **amendment 1 of 4** in the Heavy-B programme, plus two dev-discipline plans.

- **#38 (this plan):** `objective-tracker` — `lifted_from` schema widening + `query_projection_view(filter)` API. **No upstream dependency.**
- **#39:** `workspace-bootstrap` — first-run scaffold seeds the value-prop-rooted tracker tree. Depends on #38.
- **#40:** `primary-persona` — tracker-context contributor on SessionStart / UserPromptSubmit. Depends on #39.
- **`pos-amend-tracker-integration.md`** — dev-discipline; pos-amend registers ObjectiveSpec records on `apply` + writes `lifted_from.source_commit` on `seal`. Depends on #38.
- **`heavy-b-phase-alpha-beta-gamma-migration.md`** — dev-discipline; the α/β/γ data migration. Depends on #38, #39, #40, and pos-amend integration all landing.

---

## 1. Summary / TLDR

The sealed `objective-tracker` component gains two additive surfaces inside its existing fence:

1. **`lifted_from` provenance pointer on `ObjectiveSpec`.** A new optional Pydantic-validated structured field carrying `{source_doc, source_ac, source_commit}` so a tracker record can record which document/clause/commit it was extracted from. Defaults to `None` for records authored without provenance (current behaviour). Existing tests pass unchanged because the field is optional.
2. **`query_projection_view(filter)` API.** A new read-side query surface on `ObjectiveTracker` that returns `ObjectiveProjection` records filtered by attributes including `authored_by` and `lifted_from.source_doc`. The surface is latent today — `list_by_root()` walks descendants and `list()` filters by status/authored_by — but no surface exposes "give me every record lifted from this source document." This widening makes plan-doc-as-projection (Heavy-B's downstream consumer) tractable; it is also the surface the migration extractor uses to verify idempotency (re-runs query for existing `lifted_from` records and skip).

The widening is the schema/query foundation the four downstream Heavy-B amendments and dev-discipline plans rest on. **Nothing in this amendment touches any other sealed component.** No migration data is seeded here — that is dev-discipline (Phase α/β/γ migration plan). No projection-rendering tool ships here — that is dev-discipline (pos-amend-tracker-integration).

This shape lets the schema + query API ship + seal independently of the migration data, validating the Pydantic round-trip + the upgrade-fidelity (D8 semantic round-trip) with `lifted_from` populated and unpopulated, before any downstream consumer depends on the new surface.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5 operational caution)

**Named spec objectives this amendment satisfies:**

- **v1.0 Objective primitive** (`docs/spec/pos-v2-objectives-spec.md` §128–129; v1.0 audit-addendum acceptance backfill): *"objective carries parentage, measurability, time-bound."* The `lifted_from` field is additive metadata on the existing primitive; it does NOT change the parentage / measurability / time-bound contract. The widening preserves the v1.0 acceptance because `lifted_from` is `Optional` and defaults to `None` on records that omit it, so all existing v1.0 contract tests pass unchanged.
- **v1.1 R1 — semantic round-trip equivalence** (`docs/spec/pos-v2-objectives-spec.md` §210–214): *"semantic round-trip equivalence — pre-upgrade probe queries produce the same answers when replayed post-upgrade."* Adding an optional field is a schema-extension class the D8 upgrade-fidelity harness must keep green; the amendment ships D8-compliant probes that verify pre-widening records (no `lifted_from` set) replay identically post-widening, and post-widening records with `lifted_from` populated round-trip via store-restart.
- **objective-tracker proposal D1 + D8** (`docs/archive/component-research/objective-tracker/proposal.md`): D1's contract-shape clauses (`ObjectiveSpec` with `extra="forbid"`, frozen) and D8's semantic round-trip harness — both extended additively here.

**Sealed-component amendment classification.** Single sealed component (`objective-tracker`). Owner ruling D-1 (Heavy-B research) confirmed the schema-widening decision; ruling D-3 confirmed pos-amend integration is dev-discipline (lives in `tools/`, no spec objective).

The query API addition is part of the same amendment because it is the natural read-side surface the schema widening enables: a `lifted_from` field with no query surface that filters on it would ship a deadweight column. Bundling them keeps the amendment's behaviour count tight (two declared behaviours, see §5) and avoids a dependent-amendment chain inside the same component.

---

## 3. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude-leverage

**What Claude capability does this lean on or extend?**

This amendment is foundation; the Claude-leverage lands on downstream consumers. The schema widening is internal Pydantic + SQLite; no Claude primitive is invoked at this layer. The query API is plain Python; the consumers (pos-amend integration, primary-persona tracker-context contributor) compose Claude-native surfaces *onto the records this amendment makes queryable*. This amendment's job is to make those compositions possible.

The relevant Claude-leverage observation is **what this amendment unlocks**: amendment #40 (primary-persona contributor) reads tracker state on `SessionStart` / `UserPromptSubmit` (Claude hook events) and surfaces in-flight objectives in `additionalContext`; the dev-discipline pos-amend integration emits `pos-amend project` plan-doc rendering. Both depend on a queryable tracker surface; the surface lands here.

### Lens 2 — Harness + primary-persona value

**Primary-persona test.** *Does this reduce the translation burden between the user's natural-language intent and AI-effective execution?*

Indirectly. This amendment ships no user-visible feature; it is foundation. But every downstream consumer in the Heavy-B programme reduces translation burden, and they all rest on this surface:

- The user no longer translates "what is amendment-29 verifying" into a memory of which plan doc to read; the persona queries the tree directly (amendment #40 + this amendment's query API).
- Plan docs become projections that are always current with tracker state (pos-amend `project` subcommand reads `lifted_from.source_doc` to group records); the user never wonders "is this plan doc stale" (dev-discipline plan + this amendment's `lifted_from` field).

**AC-trace to AC.PO.1:**

- **AC38.1 → objective-tracker D1 (contract-shape primitive) → v1.0 Objective primitive → AC.PO.1.** `lifted_from` is `Optional`, validated, frozen — preserves the v1.0 primitive's invariants. Without provenance the persona cannot answer "which plan doc does this AC come from?" without the user pointing at the file; with provenance the persona resolves the pointer through one query → translation burden absorbed (downstream).
- **AC38.2 → objective-tracker D1 + D8 → v1.0 Objective + v1.1 R1 → AC.PO.1.** Pre-widening records round-trip post-widening with no behavioural change → existing tracker state (any seeded data, the in-flight workspace's state) carries forward unchanged across the widening → user does not see migration discontinuity → translation burden absorbed.
- **AC38.3 → objective-tracker D1 → v1.0 Objective → AC.PO.1.** `query_projection_view(filter)` filters by `lifted_from.source_doc` (and other attributes — exact filter shape is method) → the persona/tooling answers "what records came from amendment-29?" by query, not by reverse-engineering goal-string conventions → translation burden absorbed (downstream).

**Harness test.** *Does this add to the toolkit the primary persona can draw from?*

Yes — three new toolkit primitives:

1. **The `lifted_from` field** is the structural anchor that lets every Heavy-B downstream consumer compose plan-doc / source-commit context onto tracker records. Without it, plan-docs-as-projections is brittle prose-pattern-matching.
2. **`query_projection_view(filter)`** is a primitive any future tracker-consuming tool invokes — pos-amend's `project` subcommand, primary-persona's tracker-context contributor, future audit-coverage tools, future projection-rendering tools.
3. **The schema-widening precedent** demonstrates the additive-field upgrade pattern under D8 semantic round-trip: future `ObjectiveSpec` extensions follow the same shape (Optional, validated, defaults to `None`, D8 harness verifies pre/post round-trip).

**AC-trace to AC.PO.2:**

- **AC38.1 → AC.PO.2.** `lifted_from` field is reusable from any callsite that has source-doc provenance — adds a primitive to the toolkit.
- **AC38.3 → AC.PO.2.** Query API is the surface every Heavy-B downstream consumer composes against — direct toolkit expansion.
- **AC38.4 → AC.PO.2.** D8 semantic round-trip harness extended to cover the new field — toolkit reliability up (the upgrade-fidelity contract continues to hold under widening).

### Lens 3 — ODD authoring

The plan authors five outcome-shaped acceptance criteria (§4) under §2.5 reverse-direction discipline. Each AC names what must be true; method (the field's exact Pydantic shape, the query API's filter signature, internal storage representation) is the builder's call.

ODD §2.5 reverse-direction check: every new code path traces back. The new `lifted_from` field maps to AC38.1 (validation) + AC38.2 (round-trip preservation). The query API maps to AC38.3. The D8 harness extension maps to AC38.4. The seal-diff invariant maps to AC38.S. No platform branches, no defensive `if`s without an AC backing them, no "might be useful later" surface.

---

## 4. Acceptance criteria (AC38.x)

Each AC maps to at least one test function named `test_AC38_<n>_<slug>` in `objective-tracker/tests/`.

### AC38.1 — `lifted_from` field exists on `ObjectiveSpec` and validates

`ObjectiveSpec` exposes an optional structured field `lifted_from` (default `None`). When set, the field validates as a structured value carrying `source_doc` (non-empty string), `source_ac` (non-empty string), and `source_commit` (optional non-empty string — defaults `None`). A YAML/JSON containing `lifted_from: null` round-trips through `model_validate` → serialisation → `model_validate` and produces an equivalent record. A YAML omitting the field validates with `lifted_from is None`. A YAML containing a malformed `lifted_from` (missing required keys, wrong types, extra keys per existing `extra="forbid"` policy) rejects with a clear validation error.

**Test shape:** parametric round-trip across {`lifted_from` populated with all three keys, populated without `source_commit`, omitted entirely, set to `null`, set to a malformed-extra-key dict, set to a missing-key dict, set to a non-dict scalar (rejection)}. Asserts the existing D1 contract tests (the spec.py-level Pydantic surface) still pass unchanged.

**Maps to:** v1.0 Objective primitive (parentage / measurability / time-bound preserved, additive metadata) → AC.PO.1.

### AC38.2 — Pre-widening records round-trip post-widening with no behavioural change

A tracker DB seeded against the pre-widening schema (records with no `lifted_from` field present in their persisted form) loads post-widening with `lifted_from is None` on every record, and every existing read-side query (`get`, `list`, `list_by_root`, `trace_to_root`, `child_closure_status`) returns identical results compared to pre-widening on the same input set.

**Test shape:** seed an in-memory tracker with N records under the pre-widening shape (no `lifted_from`); upgrade the schema in-place (no migration script needed because the field is Optional with a `None` default); assert every existing read-side query produces output equivalent to a control run on the pre-widening tracker. The D8 semantic-round-trip harness already provides the pre/post probe set; this AC re-uses it with `lifted_from` as a probe-extension axis.

**Maps to:** v1.1 R1 semantic round-trip equivalence + objective-tracker D8 → AC.PO.1.

### AC38.3 — `query_projection_view(filter)` returns records matching the filter

`ObjectiveTracker.query_projection_view(filter)` (signature is method — the AC bounds the outcome) accepts a filter that includes at minimum `authored_by` (existing semantics) and `lifted_from.source_doc` (the new attribute), and returns a tuple of `ObjectiveProjection` records matching the filter. Records lacking `lifted_from` (i.e. `lifted_from is None`) are excluded from any filter that names a `lifted_from.source_doc` value. Empty filter returns the full record set (or the full set under a deterministic ordering — exact ordering is method, but the AC requires deterministic ordering across calls on a stable DB).

**Test shape:** seed a tracker with mixed records (some with `lifted_from`, some without); call `query_projection_view` with `{"lifted_from.source_doc": "VALUE_PROPOSITION.md"}`; assert returned set equals the lifted-from-VALUE_PROPOSITION subset. Repeat for `{"authored_by": "user"}` (existing semantics preserved). Empty filter returns full set, deterministic ordering verified across two calls.

**Maps to:** objective-tracker D1 read-side query surface (parentage-traceable) → AC.PO.1 + AC.PO.2.

### AC38.4 — D8 semantic round-trip harness covers `lifted_from` populated and unpopulated

The existing D8 upgrade-fidelity harness (`objective-tracker/src/upgrade.py` + tests) is extended with probe records that exercise `lifted_from` populated and `lifted_from is None`; pre-upgrade probes replay identically post-upgrade for both shapes. Drift report against the D8 declared threshold is zero (or below the existing threshold — the AC defers to the harness's existing pass/fail rule).

**Test shape:** add probe fixtures to the D8 harness covering the four shapes (populated with all keys, populated without `source_commit`, `lifted_from is None`, lifted_from omitted at write time → loaded as `None`); run the D8 harness; assert pass under existing threshold rule.

**Maps to:** v1.1 R1 semantic round-trip equivalence + objective-tracker D8 (substrate-level snapshot preserves physical reversibility) → AC.PO.2 (toolkit reliability — the upgrade contract holds).

### AC38.5 — Existing tracker test suite passes unchanged

The full pre-existing `objective-tracker/tests/` suite (D1–D9 + cross-cutting) passes after the widening lands without any test modification. New tests under `test_AC38_*.py` are additive.

**Test shape:** `pytest objective-tracker/tests/` returns 0 with the pre-existing test count + AC38.* count green. No pre-existing test edited.

**Maps to:** the no-regression guarantee implicit in any sealed-component amendment + objective-tracker D1–D9 contract preservation.

### AC38.S — Seal-diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` shows changes only under:

- `objective-tracker/` (source + tests),
- `docs/plans/amendment-38-objective-tracker-schema-widening*` (this plan + manifest),
- universal-paths admissions per §10.

Anything outside that set is a halt condition.

---

## 5. Behaviour-count check (ODD §3.3 forward)

| Behaviour (§1) | Criterion/criteria |
|---|---|
| 1. `lifted_from` field exists, validates, defaults to `None` | AC38.1 |
| 2. Pre-widening records round-trip post-widening | AC38.2 |
| 3. `query_projection_view(filter)` returns filter-matching records | AC38.3 |
| 4. D8 harness covers `lifted_from` populated and unpopulated | AC38.4 |
| cross-cutting | AC38.5 (no-regression), AC38.S (seal-diff) |

Four declared behaviours; six ACs cover them plus the cross-cutting no-regression and seal-diff invariants. No method-in-AC.

---

## 6. Hard constraints

1. **No `--amend`.** Corrective commits only.
2. **Scope fence — `objective-tracker/` only.** Source under `objective-tracker/src/`. Tests under `objective-tracker/tests/`. Any source edit outside `objective-tracker/` is a halt (§9).
3. **Schema widening is additive only.** The amendment may NOT rename, remove, or change the type of any existing `ObjectiveSpec` field. The `extra="forbid"` policy on `ObjectiveSpec` is preserved on the parent model; the new `lifted_from` field, if it is itself a Pydantic model, applies its own `extra="forbid"` to its own keys.
4. **Reversibility.** Removing this amendment's surface returns the layer to its pre-amendment state. Records persisted with `lifted_from` populated under this amendment lose the field's runtime visibility post-removal but the underlying event log preserves it; the semantic round-trip contract holds in the forward direction (this amendment's responsibility) and a future un-widening would be its own amendment.
5. **No new runtime deps.** Pydantic + SQLite + pyee already pinned per the component's `pyproject.toml`; no new dependency lands here.
6. **No migration data seeded here.** The α/β/γ migration is dev-discipline (separate plan); this amendment ships the schema + query API only.
7. **No external consumer wiring.** This amendment lands the surface; no edit to pos-amend, no edit to primary-persona, no edit to workspace-bootstrap. Their integrations land in their own amendments / dev-discipline plans.
8. **`extra="forbid"`/`frozen=True` invariant on `ObjectiveSpec` preserved.** The new field is a Pydantic-shaped value (model or TypedDict — builder's call), not a free-form dict, so the spec's existing strict-shape contract carries through to provenance.
9. **Authority bound.** Builder may refine the exact Pydantic shape of `lifted_from` (nested `BaseModel` vs `TypedDict` vs `dict` with validator), the query API's signature (one method with a kwargs filter vs typed-filter object, the storage layer's column representation, the D8 probe-fixture shape. Builder may NOT relax the `lifted_from is None` default-behaviour preservation (AC38.2) or the validation tightness on the field's keys (AC38.1).
10. **CDC adherence.** Plan-before-code, background-agent default, scope-only dispatch, the three amendment-dispatch speedups.
11. **`pos-amend apply --dry-run` green** is a hard prereq per amendment #22.

---

## 7. Out of scope (explicit)

- **Migration data seeding** — the α/β/γ data work lives in `heavy-b-phase-alpha-beta-gamma-migration.md`.
- **pos-amend `objectives` manifest block + `project` / `audit-coverage` subcommands** — `pos-amend-tracker-integration.md`.
- **Primary-persona tracker-context contributor** — amendment #40.
- **Workspace-bootstrap first-run tracker seed** — amendment #39.
- **Drift detection between projected plan docs and tracker state** — dev-discipline (consumer-side, not this amendment).
- **A `query_projection_view` filter language richer than the named keys (`authored_by`, `lifted_from.source_doc`)** — explicitly out of scope; the AC names exactly the keys downstream Heavy-B consumers need. Future filters land as their own amendments under §4 re-extension.
- **Removing the existing `list()` / `list_by_root()` surfaces** — not removed; `query_projection_view` is additive.
- **Adding a new criterion variant to `Criterion`** — explicitly out of scope per Heavy-B research §A.2 (prose variant suffices for AC.PO.1 + AC.PO.2).
- **Cycle detection / DAG enforcement changes** — research §A.3 confirms the current cycle policy is correct under Heavy-B.

---

## 8. Implementation order (suggested — builder's call to refine)

1. Read session-start corpus per CLAUDE.md.
2. Read Heavy-B research artefact + this plan + objective-tracker proposal §D1 + §D8 + the existing `spec.py` + `runtime.py` + `upgrade.py`.
3. Write builder-plan to `docs/plans/amendment-38-objective-tracker-schema-widening.builder-plan.md` naming specific files + symbols expected to be touched.
4. Land `lifted_from` field on `ObjectiveSpec` with Pydantic validation + AC38.1 tests. Verify AC38.1.
5. Land `query_projection_view(filter)` on `ObjectiveTracker` runtime + storage-side query support if needed. Verify AC38.3.
6. Extend D8 harness with `lifted_from` probes. Verify AC38.4.
7. Run pre-widening round-trip test (AC38.2). Verify.
8. Run full `objective-tracker/tests/` suite. Verify AC38.5.
9. Run seal-diff invariant test. Verify AC38.S.
10. Skip pre-seal full repo rerun per the dispatch-speedups CDC.
11. Amendment commit (descriptive, not prescribed here).
12. `pos-amend apply --dry-run` green gate.
13. Seal commit via `pos-amend seal`; sidecar bump + narrative append.
14. Post-seal: seal-diff-only across all sealed components.

---

## 9. Halt triggers (builder halts + signals owner)

1. **Cross-component scope expansion beyond `objective-tracker/`.** Any required source edit elsewhere → halt.
2. **D8 harness cannot be extended without breaking the pre-existing semantic round-trip threshold.** Halt; the widening shape is wrong.
3. **`lifted_from` cannot be additive without modifying an existing `ObjectiveSpec` field.** Halt; the schema widening is structurally wrong.
4. **`query_projection_view` cannot be authored without altering the public signature of `list` or `list_by_root`.** Halt; coordinate scope with owner — additive surface only.
5. **An ODD-violating shape becomes strongly required** (method-in-AC, non-objective code path, silent exception that no AC backs). Halt; owner rules.
6. **A test for AC38.1–AC38.5 cannot be written deterministically** — halt.
7. **`pos-amend apply --dry-run` red** — halt.
8. **The latent surface in `list_by_root()` referenced in research §C.1 turns out non-latent and a wholly new query API is required to land** — halt; surface for owner's reading on whether the wider surface is in scope or splits to a follow-on.
9. **Amendment-dispatch wall-time exceeds 60 minutes** — halt with current state. Owner rules on split vs push-through.

---

## 10. Bookkeeping (`pos-amend` manifest stub)

```yaml
schema_version: 1
amendment:
  number: 38
  slug: objective-tracker-schema-widening
  title: "objective-tracker schema widening (lifted_from + query_projection_view)"

# BASELINE: <pre-amendment tip captured at brief-dispatch — should
# be the immediate-prior commit, mirroring amendments #29 and #34's
# "BASELINE = HEAD~1" pattern. Avoids spurious cross-component
# missing-admission reports for unrelated commits intervening
# between objective-tracker's prior seal and this amendment.>
baseline: <captured-at-dispatch>
plan: docs/plans/amendment-38-objective-tracker-schema-widening.md

# Single-component amendment. objective-tracker only.
components:
  - name: objective-tracker
    seal_test: objective-tracker/tests/test_no_sealed_amendments.py
    sidecar: objective-tracker/tests/SEAL_COMMIT
    frozen_baseline: false   # tracker is not a frozen-baseline component
    extra_allowed_prefixes: []

# Universal admissions per amendment #22 ruling #3.
universal_paths:
  prefixes:
    - docs/plans/
  files:
    - CLAUDE.md
    - docs/odd-in-pos.md
    - docs/odd-methodology.md
    - docs/FUTURE_IDEAS.md

narrative:
  target: objective-tracker/seals/SEAL_COMMIT.schema-widening
  body: |
    # Amendment #38 — objective-tracker schema widening
    #                  (`lifted_from` provenance pointer +
    #                  `query_projection_view(filter)` API)
    ...
    # Body authored at seal time; describes:
    #  - `lifted_from` Optional structured field on ObjectiveSpec
    #    (source_doc, source_ac, source_commit). Additive; defaults
    #    to None; existing tests pass unchanged.
    #  - `query_projection_view(filter)` runtime API filtering by
    #    authored_by + lifted_from.source_doc. Latent surface in
    #    list_by_root() lifted to a named API.
    #  - D8 semantic round-trip harness extended with lifted_from
    #    probes; pre/post upgrade preserves semantic equivalence.
    #  - Foundation for the four-amendment Heavy-B programme:
    #    workspace-bootstrap seeds tracker (#39), primary-persona
    #    contributes tracker context (#40), pos-amend registers
    #    ObjectiveSpec records (dev-discipline), Phase α/β/γ data
    #    migration (dev-discipline).
    #  - No migration data, no external consumers, no plan-doc
    #    rendering — those land in their own amendments / plans.
```

---

## 11. Decisions remaining for the build agent

The following items remain method-level builder choices within this scope. Master-research recommendations are cited but not pinned.

- **D-build.1 — `lifted_from` Pydantic shape.** Three reasonable shapes: (a) nested `BaseModel` with its own `extra="forbid"` and `frozen=True`; (b) `TypedDict` validated by a field-validator; (c) `dict[str, str]` with a custom validator. **Master-research recommendation:** (a) — preserves the `ObjectiveSpec` strict-shape pattern recursively. **Builder's call within scope.** AC38.1 measures the outcome (validation tightness, key constraints).
- **D-build.2 — `query_projection_view` filter signature.** Two reasonable shapes: (a) `query_projection_view(**filter_kwargs)` with named-key conventions; (b) `query_projection_view(filter: ObjectiveFilter)` where `ObjectiveFilter` is a Pydantic model. **Master-research recommendation:** (b) — Pydantic-shaped filters land cleanly in the existing Pydantic-first codebase and self-document. **Builder's call within scope.** AC38.3 measures the outcome (named keys return correct subsets).
- **D-build.3 — Storage-layer representation of `lifted_from`.** Two reasonable shapes: (a) JSON-serialised text in a single column; (b) three discrete columns. **Master-research recommendation:** (a) — matches how `acceptance_criteria` is currently stored (text-encoded JSON in `objective_state` per `store.py`); avoids a schema migration on the SQLite side. **Builder's call within scope.** AC38.2 measures the outcome (round-trip preservation).
- **D-build.4 — D8 probe-fixture extension shape.** Two reasonable shapes: (a) extend the existing probe set with new `lifted_from`-shaped probes; (b) author a separate D8 sub-suite for provenance probes. **Master-research recommendation:** (a) — single probe set, single drift threshold, easier to read. **Builder's call within scope.** AC38.4 measures the outcome (D8 harness green under widening).

These four are surfaced to make the dispatch brief tighter; they are not blockers for plan approval.

---

## 12. Source plan (historical context)

This sub-plan derives from the Heavy-B master research artefact:

- **Master research:** `docs/plans/research/value-prop-as-root-heavy-b-migration-research.md` — covers the full investigation, all six master-research decisions (D-1 through D-6), the executive recommendation that decomposed Heavy-B into four sealed amendments + dev-discipline plans, and the lens trace at §H.

The owner ruled (post-master-research) that Heavy-B ships as **four coordinated sealed-component amendments + two dev-discipline plans**. This file is **amendment 1 of 4**. Amendments #39, #40, and the two dev-discipline plans depend on this amendment landing first.

Master-research decision ↔ this-plan AC mapping (for traceability):

| Master decision | This-plan AC | Note |
|---|---|---|
| D-1 (schema widening: add `lifted_from`?) | AC38.1 + AC38.2 + AC38.4 | Owner ruled YES per dispatch context. |
| Research §C.1 (`query_projection_view` API; latent in `list_by_root()`) | AC38.3 | The query surface that makes plan-doc-as-projection tractable. |
| Research §A.2 (prose variant suffices; no new criterion variant) | n/a (negative — confirmed scope-fenced out) | Out-of-scope §7. |

Master-research decisions D-2 through D-6 land in subsequent plans (D-2 → amendment #40; D-3 → pos-amend integration plan; D-4 → amendment #39; D-5 + D-6 → Phase α/β/γ migration plan).

---

## 13. Dispatch-time additions (brief-phase material)

When the brief is drafted, it carries these CDC + ODD enforcement requirements verbatim:

- Working directory: `/Users/lukeivers/ivers-corp-pos-v2/`. No cd-out.
- Session-start corpus read mandatory before any code edit.
- Plan-before-code: builder writes its own builder-plan to disk before touching source.
- ODD §2.4 + §2.5: no method-in-acceptance, no non-objective-backed code.
- Strong-ODD-adherence: halt if the builder believes an ODD break is strongly required.
- Scope-only downstream dispatches.
- No `git commit --amend`.
- Amendment-dispatch speedups: narrow test scope to `objective-tracker/` + seal-diff on others; skip pre-seal full rerun; methodology snippets inlined.
- objective-tracker is not a frozen-baseline component — manifest sets `frozen_baseline: false`.

---

## 14. Method-decision record (builder, post-build)

The plan §11 left D-build.1 through D-build.4 to the builder. This
section records the choices made and the rationale, plus the test
breakdown and commit SHAs.

### D-build.1 — `LiftedFrom` Pydantic shape: nested `BaseModel`

`LiftedFrom` is a Pydantic `BaseModel` with `model_config = ConfigDict(
extra="forbid", frozen=True)`. Three fields: `source_doc: str
(min_length=1)`, `source_ac: str (min_length=1)`, `source_commit: str
| None = None` (with a `field_validator` rejecting empty / whitespace-
only strings when set). `ObjectiveSpec.lifted_from: LiftedFrom | None
= None` is added at the bottom of the field list.

**Rationale:** plan §11 D-build.1 candidate (a) — preserves the
`ObjectiveSpec` strict-shape pattern recursively. `TimeBound` is the
existing precedent (same `extra="forbid" / frozen=True` config); the
new model mirrors it. Candidate (b) (`TypedDict`) would have lost the
recursive frozen contract and split validation across two layers
(field-validator + TypedDict). AC38.1 measures the validation tightness
without method-in-acceptance.

### D-build.2 — `query_projection_view` filter signature: Pydantic `ObjectiveFilter`

`ObjectiveTracker.query_projection_view(filter: ObjectiveFilter |
None = None) -> tuple[ObjectiveProjection, ...]`. `ObjectiveFilter`
lives in `objective-tracker/src/filter.py`, is `extra="forbid"` +
`frozen=True`, and declares two optional fields: `authored_by: str |
None = None` and `lifted_from_source_doc: str | None = None`. An
empty / `None` filter returns the full record set; set fields AND
together. An `is_empty()` helper on the filter exposes the
"no-constraint" semantic.

**Rationale:** plan §11 D-build.2 candidate (b) — Pydantic-shaped
filters self-document and reject unknown keys at construction.
Candidate (a) (`**filter_kwargs`) would have allowed silent typo
acceptance, which §2.5 forbids. Future filter expressiveness lands as
new optional fields on `ObjectiveFilter` (additive widening); the
filter-language extension is its own future amendment per plan §7.

### D-build.3 — Storage representation: `lifted_from_json` text column

The `objective_state` schema gains `lifted_from_json TEXT NOT NULL
DEFAULT 'null'`. `projection_to_state_row` writes either
`proj.lifted_from.model_dump_json()` (when populated) or the literal
string `"null"` (when `lifted_from is None`). An in-place ALTER TABLE
guard in `EventStore.__init__` adds the column to legacy DBs that
already have the table without it (PRAGMA table_info → check column
set → ADD COLUMN if missing).

**Rationale:** plan §11 D-build.3 candidate (a) — matches the
existing convention (`time_bound_json`, `criteria_json`,
`criteria_latest_json` are all JSON-serialised text columns).
Candidate (b) (three discrete columns) would have required three new
indexes for the same query selectivity and complicated the in-place
ALTER. The `'null'` sentinel is parseable by `json.loads` and round-
trips through the public projection as `lifted_from is None`.

### D-build.4 — D8 probe-fixture extension: extend the existing probe set

A new test file `test_AC38_4_d8_lifted_from_probes.py` seeds four
records covering the named provenance shapes (full / partial /
explicit-None / omitted), captures the pre-upgrade probe set via the
existing `capture_pre_upgrade` helper, replays via
`replay_post_upgrade`, and asserts `total_drift == 0` against
`assert_no_drift(threshold=0)`. The `lifted_from_json` column flows
through `projection_to_state_row` → `state_row` → drift comparison
without harness modification.

**Rationale:** plan §11 D-build.4 candidate (a) — single probe set,
single drift threshold, no harness fork. Candidate (b) (separate D8
sub-suite) would have doubled the threshold-management surface for
zero coverage gain.

### Test breakdown

- **Objective-tracker:** **132 passed** (86 baseline + 46 new AC38.x
  tests). Test files added:
  `tests/test_AC38_1_lifted_from_field.py` (17 tests),
  `tests/test_AC38_2_round_trip_preservation.py` (8),
  `tests/test_AC38_3_query_projection_view.py` (12),
  `tests/test_AC38_4_d8_lifted_from_probes.py` (4),
  `tests/test_AC38_5_existing_suite_unchanged.py` (3),
  `tests/test_no_sealed_amendments.py` (2 — AC38.S + the B23
  pinning-pattern meta-test).
- Existing D1–D8 baseline suites: no regressions; AC38.5
  structurally asserts the file-list discipline.
- **Cross-component seal-diff** (per amendment-dispatch-speedups):
  every other sealed component's `test_no_sealed_amendments.py`
  (or `test_cross_cutting.py` for hands-off-lifecycle) green at its
  pinned SEAL_COMMIT — cost-governance, graceful-degradation,
  memory-system, observability-aggregator, orchestrator,
  primary-persona, reversibility-primitive, safety-layer (sealed
  via import-shape probes, not git-diff), self-correction,
  telegram-interface, workspace-bootstrap, hands-off-lifecycle.
- `pos-amend apply --dry-run`: green pre-amendment-commit and
  post-seal-commit (objective-tracker is not a frozen-baseline
  component; the BASELINE literal bump completed cleanly to
  `5ad573d226b14571ebdeac357cfdb56097be90ab`).

### Sealed-component sidecar surface introduction

Objective-tracker historically shipped without a `tests/SEAL_COMMIT`
sidecar or a seal-diff test (per amendment #18 seal narrative
`f1ff28b`). Amendment #38 lands the surface inside the same fence as
the first behaviour change, mirroring the precedent set in amendment
#32 for primary-persona. Two new files:

- `objective-tracker/tests/test_no_sealed_amendments.py` — diff
  `BASELINE..SEAL_COMMIT` admits only `objective-tracker/` +
  `docs/plans/` + universal files.
- `objective-tracker/tests/SEAL_COMMIT` — sidecar carrying the
  BASELINE post-`pos-amend apply` (empty-diff window), advanced to
  the seal commit SHA via `pos-amend seal`.

The amendment also creates `objective-tracker/seals/` as the
narrative-target directory, with `SEAL_COMMIT.schema-widening` as the
amendment-cycle narrative file (per the manifest's `narrative.target`
spec).

### Commit SHAs

- Amendment commit: `be7737bbadc03586c94a06f5c70619a75d593ef1` —
  `feat(objective-tracker): schema widening — lifted_from + query_projection_view (amendment #38)`
- Seal commit: `92bead1719d26d32957a2a19f4ed4921dba6d69f` —
  `chore(seals): schema-widening seal — objective-tracker at be7737b`

### Dependents cleared to dispatch

The Heavy-B foundation is in place. The four downstream Heavy-B
amendments / dev-discipline plans inherit a satisfied schema-widening
precondition:

- **#39** (workspace-bootstrap tracker seed) — depends on #38;
  `LiftedFrom` + `query_projection_view` available; cleared to
  dispatch.
- **#40** (primary-persona tracker-context contributor) — depends on
  #38 + #39; tracker-context query surface available; cleared to
  dispatch (post-#39).
- **`pos-amend-tracker-integration.md`** (dev-discipline) — depends
  on #38; `LiftedFrom.source_commit` write surface available; cleared
  to dispatch.
- **`heavy-b-phase-alpha-beta-gamma-migration.md`** (dev-discipline)
  — depends on #38, #39, #40, and pos-amend integration; cleared to
  dispatch (post-#39 + #40 + integration).

No remaining objective-tracker dependency lurks on the Heavy-B chain.
