# Plan — Amendment #39: workspace-bootstrap tracker-seed (first-run seeds value-prop-rooted tracker tree)

**Status:** authored 2026-04-25, awaiting brief-dispatch.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Pre-amendment tip:** captured at brief-dispatch time (post-#38-seal).
**Amendment number:** `#39` placeholder; renumbered at dispatch per the convention amendments #29–#37 followed.
**Filename:** family-named (`workspace-bootstrap-tracker-seed`) so the path survives renumbering.
**Companion research:** `docs/plans/research/value-prop-as-root-heavy-b-migration-research.md` — the Heavy-B master research artefact; this sub-plan is amendment 2 of the four-amendment Heavy-B sealed-component programme.

**Sibling work in this programme.** This is **amendment 2 of 4** in the Heavy-B programme.

- **#38:** `objective-tracker` — `lifted_from` schema widening + `query_projection_view(filter)` API. **Hard prerequisite for this amendment.**
- **#39 (this plan):** `workspace-bootstrap` — first-run scaffold seeds the tracker DB with the value-prop root + spec-derived descendants. Depends on #38.
- **#40:** `primary-persona` — tracker-context contributor on SessionStart / UserPromptSubmit. Depends on #39.
- **`pos-amend-tracker-integration.md`** — dev-discipline; pos-amend registers ObjectiveSpec records on `apply` + writes `lifted_from.source_commit` on `seal`. Depends on #38.
- **`heavy-b-phase-alpha-beta-gamma-migration.md`** — dev-discipline; the α/β/γ data migration. Depends on the above.

**Prerequisite verification (builder's hard halt before code).** Before any source edit, the builder confirms via `git log` that amendment #38 has sealed (i.e., the `objective-tracker` `SEAL_COMMIT` sidecar advances to #38's seal SHA, the `lifted_from` field is present on `ObjectiveSpec`, and `ObjectiveTracker.query_projection_view(filter)` is importable and callable). If #38 has not yet sealed, halt — the dependency contract this plan rests on is not yet on disk.

---

## 1. Summary / TLDR

The `workspace-bootstrap` first-run scaffold gains one additive responsibility: on a workspace whose tracker DB does not yet contain the workspace's value-prop root, seed the DB with that root + spec-tier descendants, all `authored_by="user"`. The root's content is whatever the workspace user authors (per owner ruling D-4 — Reading (b) of locked ruling #5: the workspace-user authors their own value prop; pos-v2 dev workspaces template Luke's text from `docs/VALUE_PROPOSITION.md`).

The seed is governed by two policy layers that resolve the F.4 "zero content" tension head-on:

1. **pOS-core ships zero objective content.** The framework template (the source string the scaffold uses on a pos-v2 dev workspace) lives in `docs/VALUE_PROPOSITION.md` — that file is core docs, not bootstrap-seed payload, and its content is read at first-run time, not bundled into `workspace-bootstrap/` source. Any tracker payload-shipping-in-source is forbidden by AC39.6 (the framework-not-content invariant on tracker seeding, mirroring R16's persona invariant).
2. **The workspace user owns the root.** On a workspace classified as pos-v2 dev (the bootstrap layer detects this — exact mechanism is method), the seed reads `docs/VALUE_PROPOSITION.md` and projects it onto an `ObjectiveSpec` with `authored_by="user"`, `parent_id=None`, two `prose` criteria (AC.PO.1 + AC.PO.2 transcribed verbatim from VALUE_PROPOSITION.md), `time_bound = TimeBound(evergreen=True, review_cadence="amendment-driven")`, and `lifted_from` populated with the source-doc pointer. On a workspace not classified as pos-v2 dev, the seed prompts (or templates from a known location) the user's value prop and seeds against that. Both paths produce a tree where the user authored the root; pOS core supplies the framework, not the content.

The seed is idempotent: re-running first-run on a workspace whose tracker already carries a root with `authored_by="user"` is a no-op. The scaffold's existing `partial_recovery` machinery is extended to recognise the tracker-seeded state as a tracked artefact.

Nothing in this amendment touches `objective-tracker/`, `primary-persona/`, or `hands-off-lifecycle/` source. The tracker is consumed via its public runtime API (`tracker.create()`); the value-prop file is read from the framework's docs path; the pos-v2-dev classification is read-only of workspace metadata (existing surface).

---

## 2. Spec-objective placement (per CLAUDE.md §2.5 operational caution)

**Named spec objectives this amendment satisfies:**

- **v1.0 Architectural — "no workflow / task / scope without objective trace"** (`docs/spec/pos-v2-objectives-spec.md` §161 + audit-addendum acceptance backfill at line 162): *"alignment is re-checked at every scope boundary and the check is logged; missing check is a process failure flagged by the self-correction loop."* A workspace with no objective tree cannot satisfy "objective-trace at every scope boundary" because there is no tree to trace against. This amendment is the structural mechanism that makes the tree exist on a fresh-clone first-run, satisfying the precondition for the v1.0 architectural-layer "Objective-based" objective at workspace-level.
- **v1.0 line 152 — Non-tech users — low-friction onboarding** (§152): the user does not author tracker records by hand to reach a working objective-trace state; the scaffold seeds the tree at first-run.
- **v1.2 R16 — Framework-not-content** (`docs/spec/pos-v2-objectives-spec.md` §348–356, by extension): *"pOS core ships … the framework for handling personas. pOS core ships no persona content."* The exact same rule extends to tracker seeding — pOS core ships the seed-mechanism (the framework), not the seed-payload (the user's value prop content). AC39.6 enforces this at build-time via a no-payload-in-source check.
- **workspace-bootstrap proposal B16 / B25** (`docs/archive/component-research/workspace-bootstrap/proposal.md`): the framework-internal phase surface (the `first_run_scaffold` adapter introduced by amendment #4 + extended by amendment #36's persona scaffold) is the correct layer for new bootstrap-time contributions; this amendment extends that adapter without altering the phase model itself.
- **objective-tracker proposal D2 + D4** (`docs/archive/component-research/objective-tracker/proposal.md`): D2 (user-authored-root invariant) + D4 (`bind_scope` enforcement reads `authored_by == "user"` on the terminal ancestor) — both consumed unchanged here. The seed's root has `authored_by="user"`; every subsequent descendant chains up to it cleanly.

**Sealed-component amendment classification.** Single sealed component (`workspace-bootstrap`). The framework value-prop document is read-only consumed; the tracker public runtime API is consumed via import; no source change to other sealed components.

---

## 3. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude-leverage

**What Claude capability does this lean on or extend?**

The seed itself does not invoke a Claude primitive; it is plain file I/O + tracker-API calls inside the existing `first_run_scaffold` adapter. The Claude-leverage observation is that the **seed enables** the downstream Claude-leverage lands at amendment #40 — the primary-persona tracker-context contributor reads tracker state on `SessionStart` / `UserPromptSubmit` (Claude hook events) and surfaces in-flight objectives in `additionalContext`. Without this amendment's seed, that contributor has nothing to surface on a fresh-clone first-session.

The pos-v2-dev classification mechanism (which decides whether to template Luke's value prop or prompt the user) may compose with Claude Code's session-context surface in a future iteration — e.g., the first-run hook could ask the user a short prompt via the standard interactive surface. **Method is the builder's call**; the AC bounds the outcome (root exists, `authored_by="user"`, valid criteria).

### Lens 2 — Harness + primary-persona value

**Primary-persona test.** *Does this reduce the translation burden between the user's natural-language intent and AI-effective execution?*

Yes — substantially, as a prerequisite for the Heavy-B programme's user-visible value. Today the tracker DB exists at `<workspace>/.pos/tracker.db` (or wherever workspace-bootstrap places it) but is empty on a fresh clone. The user reaches "objective-traced work" only by hand-authoring tracker records via the public API, which is exactly the translation burden the primary persona (post-amendment-#40) is supposed to absorb but cannot, because there is no tree to query.

**AC-trace to AC.PO.1:**

- **AC39.1 → workspace-bootstrap proposal B16 (first-run scaffold extension surface) → v1.0 Architectural "Objective-based" → AC.PO.1.** Scaffold seeds value-prop root + spec descendants on first-run → tracker tree exists → primary-persona's tracker-context contributor (amendment #40) has content to surface → user does not have to translate "what is in flight under this workspace" into a memory of which plan doc to read → translation burden absorbed (downstream).
- **AC39.2 → objective-tracker D2 (user-authored-root invariant) + v1.2 R16 (framework-not-content) → AC.PO.1.** Root is `authored_by="user"` → `bind_scope` invariant enforces user-authorship on every chain-up → user's authority over the tree is structurally enforced → user does not have to litigate "is this the right root" because the framework refuses to bind anything to a non-user root → translation burden absorbed.
- **AC39.3 → objective-tracker D8 (semantic round-trip) → v1.1 R1 → AC.PO.1.** Re-running first-run is a no-op when the root already exists → user-edited descendants are durable across re-runs → user does not see surprise re-seed → translation burden absorbed.
- **AC39.4 → workspace-bootstrap proposal partial_recovery → v1.0 line 152 (low-friction onboarding) → AC.PO.1.** Mid-seed interruption recovers cleanly → user does not see a half-seeded tree that breaks the next session's context-load → translation burden absorbed at the failure boundary.
- **AC39.5 → v1.2 R16 (framework-not-content extended to tracker seeding) → AC.PO.1.** Workspace user authors the root → on a non-pos-v2-dev workspace the user supplies their own value prop → user's natural-language statement of their goals becomes the tree's root → translation burden absorbed at workspace-genesis time.

**Harness test.** *Does this add to the toolkit the primary persona can draw from?*

Yes — three new toolkit primitives:

1. **The seeded tracker DB** is the toolkit substrate every Heavy-B downstream consumer operates on (amendment #40's contributor, dev-discipline pos-amend's `project` subcommand, the α/β/γ migration's continuous-registration path). Without it, the toolkit has no input.
2. **The seed mechanism** itself — a callable from `first_run_scaffold` that knows how to read the workspace's value-prop content (templated or user-prompted) + project it onto `ObjectiveSpec` with `lifted_from` provenance — is reusable by future first-run extensions that seed additional tracker subtrees (e.g., the dev CDCs as harness-toolkit objectives per Heavy-B research §E.2).
3. **The framework-not-content invariant on tracker seeding** establishes the precedent for "pOS core ships zero tracker content; workspaces supply." Mirrors R16's persona invariant; enables the same multi-workspace composability.

**AC-trace to AC.PO.2:**

- **AC39.1 → AC.PO.2.** Seeded root + spec descendants are the toolkit substrate the persona-layer's tracker-context contributor and the pos-amend `project` tooling operate on.
- **AC39.4 → AC.PO.2.** Partial-recovery extension reuses an existing scaffold-level mechanism — the bootstrap layer's substrate-management primitive composes with the new tracker-seeded artefact.
- **AC39.6 → AC.PO.2.** Framework-not-content invariant preserved → toolkit purity preserved (the harness extends what the persona can do without injecting workspace-shaped content into the framework tree).

### Lens 3 — ODD authoring

The plan authors seven outcome-shaped acceptance criteria (§4) under §2.5 reverse-direction discipline. Each AC names what must be true; method (the pos-v2-dev classifier mechanism, the value-prop projection shape, the seed transaction boundary, the partial_recovery integration shape, the user-prompt UX on non-dev workspaces) is the builder's call.

ODD §2.5 reverse-direction check: every new code path traces back. The seed mechanism maps to AC39.1 + AC39.2. The idempotency check maps to AC39.3. The partial_recovery extension maps to AC39.4. The pos-v2-dev-vs-other-workspace fork maps to AC39.5. The framework-not-content boundary maps to AC39.6. No platform branches, no defensive `if`s without an AC backing them, no "might be useful later" surface.

---

## 4. Acceptance criteria (AC39.x)

Each AC maps to at least one test function named `test_AC39_<n>_<slug>` in `workspace-bootstrap/tests/`.

### AC39.1 — Fresh-clone first-run on a pos-v2 dev workspace seeds value-prop root + spec descendants

After `first_run_scaffold` completes on a pos-v2 dev workspace (the framework-tree itself or any workspace whose dev-classification matches) where the tracker DB is empty:

- The tracker contains exactly one objective whose `parent_id is None`, with `goal` derived from `docs/VALUE_PROPOSITION.md`'s prime statement, two `prose` criteria (AC.PO.1 transcribed from VALUE_PROPOSITION.md's "Primary-persona test" section + AC.PO.2 transcribed from "Harness test" section), `authored_by == "user"`, `time_bound.evergreen is True`, and `lifted_from.source_doc == "docs/VALUE_PROPOSITION.md"`.
- The tracker contains spec-tier child objectives chaining to the root: at minimum one objective per spec phase (v1.0, v1.1, v1.2), each `authored_by == "user"`, each with `lifted_from.source_doc == "docs/spec/pos-v2-objectives-spec.md"` and `lifted_from.source_ac` naming the spec section it lifts from. **Exact spec-tier shape is method** within the constraint that every record traces to root via `trace_to_root()` returning a chain ending at the value-prop root.
- `tracker.bind_scope` against any descendant of the seeded tree succeeds (the `authored_by == "user"` invariant on the terminal ancestor is satisfied).

**Test shape:** scaffold a fresh tmpfs workspace through the existing first-run-test harness with pos-v2-dev classification asserted; instantiate `ObjectiveTracker` against the workspace's tracker DB; assert root exists with the named properties; assert spec-tier descendants exist with `lifted_from` populated; call `bind_scope` against a descendant + assert success.

**Maps to:** v1.0 Architectural "Objective-based" + objective-tracker D2 → AC.PO.1.

### AC39.2 — Seeded root has `authored_by="user"` invariant preserved across all descendants

Every record produced by the seed has `authored_by == "user"`. `trace_to_root(<any seeded descendant>)` returns a chain whose terminal ancestor is the value-prop root and whose every link's `authored_by == "user"`. No record produced by the seed has `authored_by` set to any other value (no `"primary-persona"`, no `"workspace-bootstrap"`).

**Test shape:** scaffold + first-run; enumerate every seeded record via `tracker.list()`; assert `authored_by == "user"` on every record. Pick one descendant; call `trace_to_root`; assert the chain terminates at the value-prop root; assert every link in the chain has `authored_by == "user"`.

**Maps to:** objective-tracker D2 (user-authored-root invariant) + D4 (`bind_scope` enforcement) → AC.PO.1.

### AC39.3 — Re-running first-run on a workspace with an existing seeded tracker is a no-op

`first_run_scaffold` on a workspace whose tracker already carries the value-prop root with `authored_by == "user"`:

- does NOT create a duplicate root,
- does NOT modify any existing seeded record (`get(<seed-id>)` returns identical fields pre/post),
- does NOT emit additional `objective_created` events for already-seeded IDs,
- does NOT raise — first-run completes successfully.

The behaviour holds whether descendants have been added, modified, or marked achieved/abandoned by user activity since the original seed.

**Test shape:** scaffold once; capture every seeded record's projection; scaffold again; assert projections unchanged; count `objective_created` events for the value-prop root's ID; assert exactly one event exists.

**Maps to:** objective-tracker D8 (semantic round-trip — re-runs preserve state) → AC.PO.1.

### AC39.4 — `partial_recovery` recognises a half-seeded tracker as a recoverable state

If `first_run_scaffold` is interrupted mid-seed (simulated via a fault injection that aborts after the root is created but before all spec-tier descendants are landed), a subsequent `first_run_scaffold` invocation completes the seed by querying for missing records (using `query_projection_view` with `lifted_from.source_doc` filter, per amendment #38's API) and creating only the missing ones. No record is duplicated; no record is left in a half-state.

**Test shape:** abort first-run after seeding the root + N children; assert tracker has root + N children; invoke first-run again; assert tracker has root + full descendant set; verify no duplicate records exist via deterministic ID enumeration.

**Maps to:** workspace-bootstrap proposal partial_recovery surface → AC.PO.1.

### AC39.5 — Non-pos-v2-dev workspace seed reads the workspace user's value-prop content

On a workspace that is NOT classified as pos-v2 dev (the classification mechanism's exact shape is method), `first_run_scaffold` either (a) prompts the user for a value-prop statement (interactive path — exact UX is method) and seeds a root with `goal` = the user's input + prose criteria from a templated AC.PO.1 / AC.PO.2 framework shape, or (b) reads a templated path the workspace user has pre-populated (e.g., `<workspace>/value-prop.md`) — and seeds the root with `lifted_from.source_doc` pointing at that templated path. The root's `authored_by == "user"` regardless of which path was taken. **No pOS-core value-prop content is shipped into a non-pos-v2-dev workspace's tree.**

**Test shape:** scaffold a tmpfs workspace classified as non-dev; provide a fixture user-prompt response or templated value-prop file (whichever path the builder chooses); first-run; assert root has the workspace-user-supplied content + `authored_by == "user"` + `lifted_from.source_doc` pointing at the workspace-supplied source (NOT at `docs/VALUE_PROPOSITION.md`).

**Maps to:** v1.2 R16 framework-not-content extended to tracker seeding (workspaces supply, framework provides) + owner ruling D-4 (Reading (b) of locked ruling #5) → AC.PO.1 + AC.PO.2.

### AC39.6 — No tracker payload content shipped from `workspace-bootstrap/`

Source under `workspace-bootstrap/src/` does not contain literal value-prop prose or spec-clause prose hard-coded as constants. The seed reads the value-prop from a framework docs path at first-run-time (on pos-v2 dev workspaces) or from a workspace-supplied path (on non-dev workspaces). A test-fixture scan asserts the source files contain none of the unique prose markers from `docs/VALUE_PROPOSITION.md`'s primary statement.

**Test shape:** grep `workspace-bootstrap/src/` for the unique opening clause of VALUE_PROPOSITION.md's prime statement; assert zero matches. Repeat for the unique acceptance phrasing of AC.PO.1 and AC.PO.2.

**Maps to:** v1.2 R16 framework-not-content (tracker-seeding extension) → AC.PO.2 (toolkit purity).

### AC39.S — Seal-diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` shows changes only under:

- `workspace-bootstrap/` (source + tests),
- `docs/plans/amendment-39-workspace-bootstrap-tracker-seed*` (this plan + manifest),
- universal-paths admissions per §10.

Anything outside that set is a halt condition. Specifically: no edits to `objective-tracker/`, `primary-persona/`, `hands-off-lifecycle/`, or any other sealed component.

---

## 5. Behaviour-count check (ODD §3.3 forward)

| Behaviour (§1) | Criterion/criteria |
|---|---|
| 1. First-run seeds value-prop root + spec descendants on pos-v2 dev workspace | AC39.1 |
| 2. Seeded tree honours user-authored-root invariant | AC39.2 |
| 3. Re-run is a no-op | AC39.3 |
| 4. Partial-recovery recovers from interrupted seed | AC39.4 |
| 5. Non-dev workspace reads user-supplied value prop | AC39.5 |
| cross-cutting | AC39.6 (framework-not-content), AC39.S (seal-diff) |

Five declared behaviours; seven ACs cover them plus the cross-cutting framework-not-content and seal-diff invariants. No method-in-AC.

---

## 6. Hard constraints

1. **No `--amend`.** Corrective commits only.
2. **Scope fence — `workspace-bootstrap/` only.** Source under `workspace-bootstrap/src/`. Tests under `workspace-bootstrap/tests/`. Read-only consumption of `docs/VALUE_PROPOSITION.md` (file content) + import of `objective-tracker`'s public runtime API permitted. Any source edit outside `workspace-bootstrap/` is a halt (§9).
3. **No edit to amendment #38's tracker schema or query API.** They are consumed; if they need a change, halt and signal — the change belongs in #38's territory.
4. **Reversibility.** Removing this amendment's seed-extension returns the layer to its pre-amendment state. Already-seeded tracker DBs on existing workspaces are durable artefacts — removing the amendment does not require deleting them, just stops re-seeding new workspaces.
5. **No new runtime deps.** Permitted runtime deps per workspace-bootstrap proposal apply unchanged.
6. **No tracker payload content in `workspace-bootstrap/`.** Value-prop prose comes from `docs/VALUE_PROPOSITION.md` (read at first-run time) on dev workspaces; from a workspace-supplied path on non-dev workspaces. AC39.6 enforces this build-time.
7. **User-authored-root invariant honoured.** Every seeded record has `authored_by == "user"` per owner ruling #2 (locked) + objective-tracker D2 invariant. Hard halt on any seeded record with a different `authored_by`.
8. **Idempotency by query, not by clobber.** Re-runs query the tracker for already-seeded records (via #38's `query_projection_view` filter on `lifted_from.source_doc` + `lifted_from.source_ac`) and skip; they do NOT clobber existing records nor recreate the tree.
9. **No persona surface change.** This amendment's scope is workspace-bootstrap; the primary-persona tracker-context contributor is amendment #40's territory.
10. **Authority bound.** Builder may refine the pos-v2-dev classifier mechanism, the spec-tier descendant shape (within the constraint that each chains to the value-prop root + every link has `authored_by="user"`), the seed transaction boundary, the partial_recovery integration shape, the user-prompt UX on non-dev workspaces, the templated-value-prop-file location convention. Builder may NOT relax the framework-not-content invariant (AC39.6), the user-authored-root invariant (AC39.2), or the idempotency contract (AC39.3).
11. **CDC adherence.** Plan-before-code, background-agent default, scope-only dispatch, the three amendment-dispatch speedups.
12. **`pos-amend apply --dry-run` green** is a hard prereq per amendment #22.
13. **Amendment #38 must be sealed before this amendment begins** — verified at builder's pre-edit gate.

---

## 7. Out of scope (explicit)

- **Schema widening or query API on `ObjectiveTracker`** — amendment #38.
- **Primary-persona tracker-context contributor** — amendment #40.
- **pos-amend `objectives` manifest block / `project` / `audit-coverage` subcommands** — `pos-amend-tracker-integration.md` (dev-discipline).
- **α/β/γ data migration of legacy plan docs into tracker records** — `heavy-b-phase-alpha-beta-gamma-migration.md` (dev-discipline). This amendment lands **only** the value-prop root + spec descendants — not the 13 sealed components, not the 26 amendment plans, not the test functions.
- **Plan-doc rendering** — dev-discipline (pos-amend integration plan).
- **Drift detection between projected plan docs and tracker state** — dev-discipline.
- **CDC-as-objective seeding** under the harness-toolkit branch — explicitly deferred to a later amendment or to the α/β/γ migration's manual-seeding phase. This amendment's scope is the value-prop root + spec descendants; the dev CDCs (research §E.2) are a separate seeding operation under their own §2.5 framing.
- **Dev-vs-non-dev workspace classification mechanism** — exact mechanism is method. The classifier's outcome bounds AC39.1 vs AC39.5; the mechanism itself is the builder's call.
- **A new tracker DB persistence path** — uses whatever path workspace-bootstrap currently uses for objective-tracker (read existing scaffold layout; do not relocate).

---

## 8. Implementation order (suggested — builder's call to refine)

1. Read session-start corpus per CLAUDE.md.
2. Read Heavy-B research artefact + amendment #38 plan + this plan + workspace-bootstrap proposal + objective-tracker public API surface (`runtime.py:117` `create()`, `runtime.py:599` `trace_to_root`, the new `query_projection_view` from #38).
3. Verify amendment #38 has sealed (per §6 constraint 13).
4. Write builder-plan to `docs/plans/amendment-39-workspace-bootstrap-tracker-seed.builder-plan.md` naming specific files + symbols expected to be touched.
5. Land the pos-v2-dev classifier mechanism. Verify it cleanly distinguishes the framework workspace from a non-dev workspace.
6. Land the seed mechanism on the pos-v2 dev path (read VALUE_PROPOSITION.md → project to ObjectiveSpec → call `tracker.create()` with `lifted_from`). Verify AC39.1 + AC39.2.
7. Land the user-supplied path on the non-dev workspace path. Verify AC39.5.
8. Land the idempotency check using `query_projection_view`. Verify AC39.3.
9. Land the partial_recovery extension. Verify AC39.4.
10. Land the framework-not-content build-time check. Verify AC39.6.
11. Run AC39.1–AC39.6 + the existing `workspace-bootstrap/tests/` suite + the existing first-run integration test.
12. `pos-amend apply --dry-run` green gate.
13. Amendment commit.
14. Seal commit via `pos-amend seal`; sidecar bump + narrative append.
15. Post-seal: seal-diff-only across all sealed components.

---

## 9. Halt triggers (builder halts + signals owner)

1. **Cross-component scope expansion beyond `workspace-bootstrap/`.** Any required source edit to `objective-tracker/`, `primary-persona/`, `hands-off-lifecycle/`, or any other sealed component → halt.
2. **Amendment #38 has not sealed before this build begins.** Halt.
3. **`tracker.query_projection_view`'s actual signature differs from the AC39.4 + AC39.3 expectations** in a way that prevents idempotency-by-query. Halt — coordinate with #38's territory or surface for owner.
4. **The pos-v2-dev classifier cannot be authored without a structural workspace-metadata change** (e.g., a new field in workspace-identity per amendments #6/#28). Halt — that's multi-component scope expansion.
5. **The user-authored-root invariant cannot be honoured** because some path in the seed structurally requires `authored_by` set to something other than `"user"`. Halt — that contradicts owner ruling #2 + D2.
6. **Framework-not-content invariant cannot be enforced** without shipping value-prop prose into source. Halt — AC39.6 is non-negotiable per CLAUDE.md design discipline.
7. **An ODD-violating shape becomes strongly required** (method-in-AC, non-objective code path, silent exception that no AC backs). Halt; owner rules.
8. **A test for AC39.1–AC39.6 cannot be written deterministically** — halt.
9. **`pos-amend apply --dry-run` red** — halt.
10. **The non-dev workspace path's UX (user prompt vs templated file) requires a Claude primitive that workspace-bootstrap currently has no surface to invoke** — halt; coordinate with master plan author on whether this is amendment-#40 scope or splits to a follow-on.
11. **Amendment-dispatch wall-time exceeds 60 minutes** — halt with current state. Owner rules on split vs push-through.

---

## 10. Bookkeeping (`pos-amend` manifest stub)

```yaml
schema_version: 1
amendment:
  number: 39
  slug: workspace-bootstrap-tracker-seed
  title: "workspace-bootstrap tracker-seed (first-run seeds value-prop-rooted tree)"

# BASELINE: <pre-amendment tip captured at brief-dispatch — should
# be the seal commit of #38, mirroring the BASELINE-as-HEAD~1
# pattern when no other commits intervene; otherwise HEAD~1 of the
# amendment commit.>
baseline: <captured-at-dispatch-post-#38-seal>
plan: docs/plans/amendment-39-workspace-bootstrap-tracker-seed.md

# Single-component amendment. workspace-bootstrap only.
components:
  - name: workspace-bootstrap
    seal_test: workspace-bootstrap/tests/test_no_sealed_amendments.py
    sidecar: workspace-bootstrap/tests/SEAL_COMMIT
    frozen_baseline: false
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
  target: workspace-bootstrap/seals/SEAL_COMMIT.tracker-seed
  body: |
    # Amendment #39 — workspace-bootstrap tracker-seed
    #                  (first-run seeds value-prop-rooted tracker tree)
    ...
    # Body authored at seal time; describes:
    #  - First-run scaffold seeds the workspace's tracker DB with a
    #    value-prop root + spec-tier descendants on a pos-v2 dev
    #    workspace (templated from docs/VALUE_PROPOSITION.md
    #    read at first-run time).
    #  - On non-dev workspaces, seed reads workspace-user-supplied
    #    value prop content (interactive prompt or templated file).
    #  - Every seeded record has authored_by="user"; root has
    #    parent_id=None; criteria are AC.PO.1 + AC.PO.2 transcribed
    #    verbatim from VALUE_PROPOSITION.md.
    #  - lifted_from populated on every seeded record (consumes
    #    amendment #38's schema widening).
    #  - Idempotent by query (uses #38's query_projection_view to
    #    detect already-seeded records).
    #  - partial_recovery extended to recognise the seeded state.
    #  - Framework-not-content invariant enforced at build-time:
    #    no value-prop prose hard-coded in workspace-bootstrap/src/.
    #  - Resolves the F.4 zero-content tension via Reading (b) of
    #    locked ruling #5: the workspace user authors the root;
    #    pos-v2 dev workspaces template Luke's text.
    #  - No edits to objective-tracker, primary-persona, or
    #    hands-off-lifecycle source.
```

---

## 11. Decisions remaining for the build agent

The following items remain method-level builder choices within this scope. Master-research recommendations are cited but not pinned.

- **D-build.1 — pos-v2-dev classifier mechanism.** Three reasonable shapes: (a) detect by presence of `docs/VALUE_PROPOSITION.md` at workspace root; (b) detect by repo metadata (e.g., remote URL matching `ivers-corp` or workspace-identity slug matching a known set); (c) explicit configuration flag in workspace-bootstrap's existing config. **Master-research recommendation:** (a) — minimal blast radius, no new metadata surface, existing artefact is sufficient. **Builder's call within scope.** AC39.1 + AC39.5 measure outcomes (which path runs given which classification).
- **D-build.2 — Spec-tier descendant shape.** Two reasonable shapes: (a) one objective per spec phase (v1.0, v1.1, v1.2) with `prose` criteria summarising the phase; (b) one objective per `R*` clause in v1.1 + v1.2 plus one per architectural-layer / foundational-layer / user-facing-layer of v1.0. **Master-research recommendation:** (a) — keeps the seeded tree compact (~10 records) and matches the research's Phase α scope (~30 records seeded in α; this amendment ships a subset, the rest land in the dev-discipline migration). **Builder's call within scope.** AC39.1 measures outcome (root + spec descendants chain correctly).
- **D-build.3 — Non-dev workspace UX.** Three reasonable shapes: (a) interactive prompt at first-run via the existing first-run hook stdin; (b) templated path the workspace user pre-creates (e.g., `<workspace>/value-prop.md`) with a guidance note in the bootstrap log if missing; (c) defer the seed on non-dev workspaces and emit a structured diagnostic prompting the user to run a follow-up command. **Master-research recommendation:** (b) — non-interactive, durable, matches how amendment #36's persona scaffold treats workspace-supplied content. **Builder's call within scope.** AC39.5 measures outcome (workspace-user content reaches root).
- **D-build.4 — Seed transaction boundary.** Two reasonable shapes: (a) wrap the entire seed (root + descendants) in a single tracker transaction; (b) seed root first, commit, then seed descendants individually. **Master-research recommendation:** (b) — matches the partial_recovery contract (mid-seed interruption is recoverable per AC39.4). **Builder's call within scope.** AC39.4 measures outcome (interrupted seed completes on re-run).

These four are surfaced to make the dispatch brief tighter; they are not blockers for plan approval.

---

## 12. Source plan (historical context)

This sub-plan derives from the Heavy-B master research artefact:

- **Master research:** `docs/plans/research/value-prop-as-root-heavy-b-migration-research.md` — covers the full investigation, decisions D-1 through D-6, the executive recommendation, and the lens trace at §H.

The owner ruled (post-master-research) that Heavy-B ships as **four coordinated sealed-component amendments + two dev-discipline plans**. This file is **amendment 2 of 4**. Amendment #38 is a hard prerequisite. Amendment #40 + the two dev-discipline plans depend on this amendment landing.

Master-research decision ↔ this-plan AC mapping (for traceability):

| Master decision | This-plan AC | Note |
|---|---|---|
| D-4 (workspace-bootstrap seed: who owns the value-prop root in derived workspaces?) | AC39.5 + AC39.6 | Owner ruled Reading (b) — workspace user authors; dev workspaces template Luke's. |
| Research §F.4 (zero-content tension resolution) | AC39.5 + AC39.6 | Reading (b) preserves rule #4 + ruling #5. |
| Research §F.5 (chicken-and-egg: amendment ACs in tracker before tracker is seeded) | AC39.1 (the seed runs as part of this amendment's first-run flow; the amendment's ACs verify post-seed state) | Resolution per research §F.5. |
| Research §B.2 phasing (Phase α: root + spec + components) | AC39.1's spec-tier descendants are a subset of Phase α | Components themselves seed in the dev-discipline migration. |

---

## 13. Dispatch-time additions (brief-phase material)

When the brief is drafted, it carries these CDC + ODD enforcement requirements verbatim:

- Working directory: `/Users/lukeivers/ivers-corp-pos-v2/`. No cd-out.
- Session-start corpus read mandatory before any code edit.
- **Pre-edit gate:** verify amendment #38 has sealed (`objective-tracker/tests/SEAL_COMMIT` advanced past #38's seal SHA + `lifted_from` field on `ObjectiveSpec` + `query_projection_view` callable). Halt if unmet.
- Plan-before-code: builder writes its own builder-plan to disk before touching source.
- ODD §2.4 + §2.5: no method-in-acceptance, no non-objective-backed code.
- Strong-ODD-adherence: halt if the builder believes an ODD break is strongly required.
- Scope-only downstream dispatches.
- No `git commit --amend`.
- Amendment-dispatch speedups: narrow test scope to `workspace-bootstrap/` + seal-diff on others; skip pre-seal full rerun; methodology snippets inlined.
- workspace-bootstrap is not a frozen-baseline component — manifest sets `frozen_baseline: false`.

---

## 14. Method-decision record (builder, post-build)

The plan §11 left D-build.1 through D-build.4 to the builder. This
section records the choices made and the rationale, plus the test
breakdown and commit SHAs.

### D-build.1 — pos-v2-dev classifier: presence of canonical VALUE_PROPOSITION.md

`tracker_seed.classify_workspace(workspace_root)` returns
`"pos-v2-dev"` iff `<workspace>/docs/VALUE_PROPOSITION.md`
exists, else `"user"`. Pure function; no metadata surface added;
the existing artefact is sufficient as a discriminator.

**Rationale:** plan §11 D-build.1 candidate (a) — master-research
recommendation. Minimal blast radius. The classifier checks for the
same file the seed reads as source on the dev path, so the
"classifier matched but loader can't find the file" branch is
structurally impossible (and surfaces loudly via `FileNotFoundError`
if it ever did happen). Candidates (b) (repo metadata) and (c)
(explicit config flag) would have widened the workspace-identity
surface or added a YAML knob without lift.

### D-build.2 — Spec-tier descendant shape: one objective per spec phase

Three descendants — one each for v1.0, v1.1, v1.2. Each has
`authored_by="user"`, `parent_id=ROOT_OBJECTIVE_ID`, a single prose
criterion (`"spec-{phase}-met"`), evergreen time-bound, and
`lifted_from=LiftedFrom(source_doc=
"docs/spec/pos-v2-objectives-spec.md", source_ac=phase)`.
Stable IDs `spec-v1.0` / `spec-v1.1` / `spec-v1.2` keep the
re-run query-then-skip check deterministic.

**Rationale:** plan §11 D-build.2 candidate (a) — master-research
recommendation. Compact tree (4 records total: root + 3
descendants); matches research §B.2 Phase α subset. Candidate (b)
(one objective per `R*` clause) would have ballooned to ~25 records
and violated the explicit out-of-scope "this amendment's scope is
the value-prop root + spec descendants; the dev CDCs are a separate
seeding operation."

### D-build.3 — Non-dev workspace UX: templated path with skip-on-absent

On a workspace classified as `"user"`, the seed reads
`<workspace>/value-prop.md` if present and seeds against that;
if absent, it returns `TrackerSeedResult(seeded=False,
reason="skipped_no_value_prop", ...)` and the scaffold completes
without raising. The user can supply the file later and re-invoke
`seed_tracker` to complete the seed (covered by AC39.5's "re-run
after value prop supplied" test).

**Rationale:** plan §11 D-build.3 candidate (b) — master-research
recommendation. Non-interactive, durable, parallels amendment
#36's persona template-from-disk shape. Candidate (a) (interactive
prompt) would have required new I/O surface in the scaffold —
plan §9 #10 names that as a halt condition. Candidate (c) (defer +
emit diagnostic) is structurally what shipped, since the skip
result IS a structured diagnostic the caller can route on.

### D-build.4 — Seed transaction boundary: root first, descendants individually

`seed_tracker` creates the root via `tracker.create(root_spec,
objective_id=ROOT_OBJECTIVE_ID)`, then iterates the spec phases
creating each descendant individually, querying via
`query_projection_view(ObjectiveFilter(lifted_from_source_doc=...))`
to detect already-seeded records and skip. The root + each
descendant land in their own create() call, so an interrupted seed
that wrote the root + one descendant resumes by creating only the
remaining descendants on the next invocation.

**Rationale:** plan §11 D-build.4 candidate (b) — master-research
recommendation. Matches the partial-recovery contract — AC39.4
test fixtures simulate root-only and root+one-descendant interrupted
states; both resume cleanly with `reason="completed_partial"`.
Candidate (a) (single transaction) would have blocked partial-
recovery resumption: an aborted transaction leaves zero records,
and a successful one leaves the full tree, but the actual fault
shape (process crash mid-seed) does not map to either.

### Zero-content tension resolution (research §F.4 / sub-plan §1)

The chosen method satisfies STATE.md rule #4 ("pOS core ships zero
personas/content") AND the single-tree ruling AND owner D-4
ruling (b) simultaneously:

- pos-v2 source code (`workspace-bootstrap/src/`) embeds **zero**
  literal value-prop prose. AC39.6's sentinel-scan test verifies
  that the canonical VALUE_PROPOSITION.md sentences ("AI has a
  usability problem", "primary persona is a translation layer",
  "do this thing every 12 hours", etc.) do not appear hard-coded
  in any `.py` file under `workspace-bootstrap/src/`.
- The "template source" for pos-v2 dev workspaces is the
  canonical doc `docs/VALUE_PROPOSITION.md` itself —
  framework documentation that lives in `docs/`, not bootstrap-
  seed payload bundled in source. The seed `read_text()`s the doc
  at first-run-time. Reading from disk at runtime is structurally
  identical in shape to amendment #36's persona-template-from-
  disk pattern.
- Single tree: there is exactly ONE `docs/VALUE_PROPOSITION.md`
  in the framework. Forks of pos-v2 that classify as pos-v2 dev
  (because the classifier looks for that file) inherit the same
  content — which is the explicit template-from-Luke shape D-4
  ruling (b) sanctions. A workspace user who forks pos-v2 to
  build their own thing replaces `docs/VALUE_PROPOSITION.md`
  with their own content; the classifier still routes to the dev
  path; the seed reads the user's now-replaced file. Authority
  remains with the workspace.
- Non-dev workspaces never inherit Luke's content: the seed
  reads `<workspace>/value-prop.md` (workspace-user authored),
  or skips entirely. AC39.5 cross-checks framework sentinels do
  not leak into a user workspace's tracker tree.

### Test breakdown

- **AC39.1** — 5 tests (`test_AC39_1_fresh_clone_seeds_root_and_
  descendants.py`): root carries goal + AC.PO.1 + AC.PO.2 +
  evergreen + `lifted_from`; descendants chain via `trace_to_root`;
  `bind_scope` succeeds; `query_projection_view` returns seeded
  subset; `ScaffoldResult` reports outcome.
- **AC39.2** — 3 tests (`test_AC39_2_authored_by_user_invariant.py`):
  every record `authored_by="user"`; chain is user-authored end-to-
  end; no record carries persona/bootstrap `authored_by`.
- **AC39.3** — 4 tests (`test_AC39_3_re_run_is_noop.py`): direct
  `seed_tracker` re-call → `already_seeded`; `run_first_run_scaffold`
  re-call → `already_scaffolded` + tracker untouched; user transitions
  survive re-seeds; one ObjectiveCreated event per ID.
- **AC39.4** — 3 tests (`test_AC39_4_partial_recovery_resumes.py`):
  root-only state resumes (`completed_partial`); root+one-descendant
  resumes only missing; no duplicate records.
- **AC39.5** — 5 tests (`test_AC39_5_non_dev_workspace_user_supplied.py`):
  classifier returns `"user"`; user file with `value-prop.md`
  seeds from local file; absent file skips cleanly; framework
  sentinels do not leak; re-invoke after supply completes.
- **AC39.6** — 4 tests (`test_AC39_6_no_tracker_payload_in_source.py`):
  no VP sentinels in src; no spec-doc sentinels in src;
  `tracker_seed.py` reads at runtime; consumes #38's API.
- **AC39.S** — covered by `test_no_sealed_amendments.py`;
  BASELINE advanced via `pos-amend apply` to
  `fa15127134ad5dfa68166b9641cfa6cc174e66df`; SEAL_COMMIT
  advanced via `pos-amend seal` to the amendment commit
  `3f0cd8d3e352481e5cc3b191113630e87038c969`. test_B23 +
  test_B20 green post-seal.
- Existing baseline suite: no regressions. **Full workspace-
  bootstrap suite: 157 passed (133 baseline + 24 new AC39
  tests).**
- **Cross-component seal-diff sweep** (per amendment-dispatch-
  speedups): every other sealed component's
  `test_no_sealed_amendments.py` (or `test_cross_cutting.py` for
  hands-off-lifecycle) green at its pinned SEAL_COMMIT —
  cost-governance, graceful-degradation, memory-system,
  observability-aggregator, orchestrator, primary-persona,
  reversibility-primitive, safety-layer, self-correction,
  telegram-interface, objective-tracker, hands-off-lifecycle.
- `pos-amend apply --dry-run`: green pre-amendment-commit and
  post-seal-commit (workspace-bootstrap is not a frozen-baseline
  component; the BASELINE literal advance completed cleanly).

### Commit SHAs

- Amendment commit: `3f0cd8d3e352481e5cc3b191113630e87038c969` —
  `feat(workspace-bootstrap): tracker-seed — first-run seeds
  value-prop-rooted tree (amendment #39)`
- Seal commit: `13770df7410d0dd4489594e4a15aaaccc3413769` —
  `chore(seals): tracker-seed seal — workspace-bootstrap at
  3f0cd8d`

### Dependents cleared to dispatch

The Heavy-B chain advances. Sibling sub-plan #40 (primary-persona
tracker-context contributor) and the two dev-discipline plans
(`pos-amend-tracker-integration.md`, `heavy-b-phase-alpha-beta-
gamma-migration.md`) inherit a satisfied workspace-bootstrap-
seeded-tracker precondition:

- **#40** (primary-persona tracker-context contributor) — depends
  on #38 + #39; tracker DB carries the value-prop root + spec
  descendants on a fresh-clone first-run; cleared to dispatch.
- **`pos-amend-tracker-integration.md`** (dev-discipline) —
  depends on #38; `LiftedFrom.source_commit` write surface +
  query API available; cleared to dispatch.
- **`heavy-b-phase-alpha-beta-gamma-migration.md`** (dev-
  discipline) — depends on #38 + #39 + #40 + pos-amend
  integration; ready for dispatch after #40 + integration land.

No remaining workspace-bootstrap dependency lurks on the Heavy-B
chain.
