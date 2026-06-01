# failure-mode-guard matrix — loam's protection pillar made a living, machine-checkable catalogue — plan

**Status:** sub-plan-doc (PLAN-ONLY; no code authored by this drive).
**Working directory:** `/Users/lukeivers/loam` (canonical loam tree). This plan
was authored in the isolated worktree `/Users/lukeivers/loam-wt-fmm` on branch
`plan/failure-mode-guard-matrix` to avoid racing a concurrent build in the main
tree; the build agent that picks this up works the canonical tree per the
manifest fence.
**Parent doctrine:** `docs/design/loam-doctrine.md` — *§"The two sides of leg 2 —
translation in, protection around"* (the protection pillar this plan operationalises).
**Predecessors (load-bearing, Tier-0 read at plan-time):**
- `docs/design/loam-doctrine.md` @ `f1f6116` (the doctrine; the floor; the known-AI-failures list).
- `docs/VALUE_PROPOSITION.md` @ `f1f6116` (prime-objective + protection-floor + proportionality §).
- `CLAUDE.md` Lens 0 @ `f1f6116` (the prime lens naming protection as one side of translation).
- `framework/tools/loam/src/loam_cli/release/gates.py` @ `f1f6116` (the nine pre-publish gates — the existing guard substrate).
- `framework/tools/loam/src/loam_cli/audit/cli.py` + `reconcile.py` @ `f1f6116` (the `loam audit` verb — the machine-checkable entry-point PATTERN this plan mirrors).
- The hook ecosystem under `framework/safety-layer/hooks/`, `plugins/dev-sdlc/hooks/`, `framework/hands-off-lifecycle/hooks/` @ `f1f6116`.
- The failure-mode feedback-memory captures under `~/.claude/projects/-Users-lukeivers-pos3/memory/` (enumerated in §11 provenance — these ARE the catalogue's rows).
**BASELINE candidate:** current `main` @ `f1f6116` (`chore(seals): N3 translate-in onboarding intake`).
**Status-file target:** `docs/STATE.md` rollup + `docs/release-roadmap.md` §2 (backfilled at seal; see §9).
**Quality bar:** dev-mode ODD/CDC; every AC outcome-shape; ≥1 outcome-altitude AC verified at a real entry-point.

---

## §1 — Summary / TL;DR

**What ships:** loam's *protection pillar* — today an implicit set of guards
scattered across nine release gates, a dozen hooks, ODD, file-based memory, and
the audit comparator — becomes an **explicit, single-source, living, machine-
checkable catalogue**: each known way an AI betrays a user by default × loam's
actual guard against it × whether that guard is **default-on** × whether it is
**floor-class (non-negotiable) or proportional** × how we **verify the guard
fires**.

**AC families:**
- **AC.FMG-CAT** — the catalogue artefact exists, has the named schema, and every
  row binds a real failure mode to a real, citable guard (no invented guards).
- **AC.FMG-CHECK** — a real coverage-check entry-point (`loam guards`) that
  derives the guard set from ground truth and asserts the floor invariant.
- **AC.FMG-LIVE** — the catalogue is refreshed on the doctrine's existing recurring
  cadence (composes on the pruning flow; not a net-new scheduler).
- **AC.FMG-GAP** — the coverage check NAMES the failure modes with no default-on
  guard yet (the actionable output — the gaps are the point, not a defect to hide).
- **AC.FMG-S** ★ — outcome-altitude: a real `loam guards` run against the *actual*
  guard set, at the production entry-point, with no pre-arranged state, asserting
  every floor-class failure mode has a default-on guard (and listing those that don't).

**Key decisions baked (recommendations in §12; forks for the dispatcher in §13):**
1. The catalogue lives as a **machine-readable manifest (`failure-mode-guard-matrix.yaml`)
   + a generated human-readable companion** — the manifest is the source of truth the
   check reads; the prose is rendered, never hand-maintained in parallel (avoids the
   doc↔code drift the substrate-audit gate exists to catch).
2. The coverage check is a **new `loam guards` verb** registered through the existing
   `loam.cli.subcommands` entry-point group — the SAME composition the `loam audit`
   verb uses (Lens 1; no new CLI plumbing).
3. The check **derives the live guard set from ground truth** (settings.json hook
   registrations + the `ALL_GATES` tuple + the manifest), then reconciles the manifest's
   claimed guards against what is actually wired — a guard the manifest claims but that
   is not registered is itself a divergence (mirrors the substrate-audit comparator).

**F2 scope-realism (Lens 7):** the load-bearing finding of this whole exercise is
the GAP SET (§13 fork F-3 + the AC.FMG-GAP family). At least three named failure
modes from the doctrine + memories currently have **no default-on programmatic
guard** — they are guarded only by persona discipline (a prose rule), which is
exactly the kind of guard that "decays first under pressure" (doctrine §"Follow the
defined workflow"). Cataloguing them honestly, and marking them `guard: persona-
discipline / default-on: NO-PROGRAMMATIC`, is more valuable than papering over them.
This plan's fence is the catalogue + the check; **building new guards for the gaps
is explicitly downstream** (§7) — but the gaps must be VISIBLE, not silently omitted.

---

## §2 — Placement decisions (per partition rule)

| Item | Placement | Rationale |
|---|---|---|
| The matrix manifest (source of truth) | **new component** `framework/protection-matrix/` (data + the `loam guards` verb package) | It is a cross-cutting catalogue ABOUT every other component; it does not belong inside any one of them. New component = clean layer boundary (doctrine §"How loam is built — in layers"). |
| The `loam guards` verb | inside the new `framework/protection-matrix/` package, registered via `loam.cli.subcommands` entry-point | Mirrors how `loam audit` ships from its own package and registers through the entry-point group (`cli.py` discovery loop). No edit to the canonical dispatcher. |
| The recurring refresh | composes on the **doctrine's existing recurring pruning/refresh cadence** (doctrine §3 + §"Follow the defined workflow") — a flow entry, NOT a net-new launchd/cron | Lens 1: the doctrine already commits loam to recurring self-maintenance "on its own, on a recurring schedule." The matrix-refresh is one item in that flow, not a parallel scheduler. |
| The human-readable companion | generated artefact at `docs/design/protection-matrix.md` (rendered from the manifest) | Rendered, never hand-maintained — keeps the substance exposed (doctrine §"Always expose the substance") without a second drift surface. |
| Optional release-gate arm | a tenth gate `check_floor_guards_present` in `release/gates.py` (FORK F-4, §13) | Whether the floor invariant becomes a HARD publish-block is a proportionality call the dispatcher should rule; the verb ships either way. |

---

## §3 — Halt-and-surface recorded DURING plan authoring

These are decisions I made autonomously at plan-time (recorded, not gates the
builder must re-ask) plus the genuine forks the builder/dispatcher must respect.

**Recorded autonomous (no re-ask needed):**
- **R-1.** No existing guard-matrix/registry exists (grep across `framework/` +
  `docs/` @ `f1f6116` found only incidental phrase matches, no registry). This is
  net-new; no duplication risk. Decided: author fresh.
- **R-2.** The catalogue is data-first (a manifest), not code-first. A guard row is
  *declarative*; the check is the only code. This keeps the floor list reviewable by
  a human and diffable, and lets the coverage check be a pure reconcile (Tier-0
  ground truth vs declared), exactly like the substrate-audit comparator.
- **R-3.** Catalogue rows are sourced ONLY from Tier-0-real guards I read this drive
  (the nine gates, the named hooks, ODD, FBM/memory, the audit/reconcile comparator).
  No guard is invented to make a row look covered (doctrine §"a confident
  hallucination with a delete key" — the protection pillar must not itself hallucinate
  coverage).

**Gates the builder must respect (genuine forks → §13):**
- **F-1** — does the manifest schema field set match §5 exactly, or does the builder
  refine it? (Recommendation: ship §5 as-is; it is outcome-complete.)
- **F-2** — `loam guards` exit-code semantics on a gap (0-with-report vs non-zero).
- **F-3** — which gaps are in the v1 manifest as `NO-PROGRAMMATIC` rows.
- **F-4** — does the floor invariant also become a release-gate HARD-block now.

---

## §4 — Spec-objective placement (ladder-up)

- **Binds to:** the **protection side of leg 2** of the doctrine (doctrine
  §"The two sides of leg 2"), and through it to `VALUE_PROPOSITION.md` §"The prime
  objective — per-user-tuned translation," whose closing line is the acceptance
  condition: *"When the user … is being betrayed by a known AI failure mode loam
  should have guarded, the prime objective has failed."*
- **Ladders up to** the prime objective (Lens 0 / VALUE_PROPOSITION prime objective):
  the matrix is the instrument that makes the protection-failure condition
  *observable* — it turns "loam should have guarded" from a prose aspiration into a
  checkable invariant (every floor-class failure mode has a default-on guard).
- **AC.PO binding:** this work is verified against the VALUE_PROPOSITION harness test
  (does it add to the persona's toolkit? — yes: `loam guards` is persona-invokable)
  and primary-persona test (does it reduce user translation burden? — yes: the user
  never has to know the failure taxonomy; loam guards it invisibly, the floor's whole
  point per doctrine §"non-negotiable floor … invisibly, especially for a non-
  technical user who cannot even name them").

---

## §5 — The matrix SCHEMA (the load-bearing artefact)

The catalogue is a manifest of rows, one per known failure mode. Each row:

| Field | Type | Meaning | Verification source |
|---|---|---|---|
| `id` | scope-descriptive string (e.g. `FM.HALLUCINATION`, `FM.NARRATION-NOT-ACTION`) | the failure mode, scope-named not version-packed (`feedback_scope_descriptive_ac_ids`) | — |
| `name` | string | plain-language name (doctrine vocabulary, user-facing) | — |
| `description` | string | one sentence: how this betrays a user by default | the doctrine / the source memory |
| `source` | citation | the doctrine § or the `feedback_*.md` file that names this mode | Tier-0 file path |
| `guard` | string | the actual loam guard (a named hook / a named gate / ODD / FBM / the reconcile discipline / `persona-discipline`) | Tier-0 code path |
| `guard_kind` | enum `hook \| release-gate \| odd \| memory \| comparator \| persona-discipline \| none` | the mechanism class | — |
| `guard_ref` | path/symbol | the file + symbol that IS the guard (e.g. `framework/.../release/gates.py:check_substrate_audit`) | Tier-0 — the check verifies this exists/is-wired |
| `default_on` | enum `YES \| NO-PROGRAMMATIC \| NONE` | is the guard on by default for every user, no opt-in? | derived from ground truth (settings registration / `ALL_GATES` membership) |
| `class` | enum `floor \| proportional` | floor = non-negotiable, always-on for everyone; proportional = scales with stakes (doctrine §"Two standing constraints") | declared, reviewed |
| `proportionality_note` | string (proportional rows only) | what stakes dial this guard's weight | — |
| `verification` | string | HOW we know the guard fires — a test ref, a probe, or the registration check | Tier-0 test/probe path |
| `gap` | bool (derived) | TRUE iff `class: floor` AND `default_on != YES` — the actionable signal | computed by the check |

**Where it lives + machine-checkable vs prose split:**
- **Source of truth (machine-checkable):** `framework/protection-matrix/data/failure-mode-guard-matrix.yaml`.
- **Generated prose companion (human-readable, never hand-edited):** `docs/design/protection-matrix.md`, rendered from the YAML so the substance is always exposed in plain language (doctrine §"Always expose the substance; adapt only the vocabulary").
- **The check (`loam guards`)** reads the YAML, derives the live guard set from ground truth (hook registrations + `ALL_GATES` + ODD presence), reconciles the two, and reports.

**The candidate row set (Tier-0 sourced — this is the v1 catalogue the builder
authors; method to refine wording is the builder's, the row SET is the contract):**

| `id` | failure mode | guard (Tier-0 real) | `guard_kind` | `class` | `default_on` |
|---|---|---|---|---|---|
| `FM.HALLUCINATION` | invents facts that don't exist | information-trust-ordering + claim-or-cite + the audit comparator (`loam audit`) catching stale status claims | comparator + persona-discipline | floor | partial: comparator YES on shipping docs, broader recall NO-PROGRAMMATIC |
| `FM.MISSING-CONTEXT` | works from missing/degraded context | SessionStart corpus-load gate + compaction re-inject + keep-pace retrieval | hook | floor | YES |
| `FM.SILENT-BREAKAGE` | one change breaks the surrounding work | ODD objective-binding gate + TDD-guard + the release-gate chain | hook + release-gate + odd | floor | YES (dev-mode); proportional in derived workspaces |
| `FM.GOAL-DRIFT` | loses the original goal | ODD authoring (every line maps to a named AC) + active-scope sentinel | odd + hook | floor | YES (dev-mode) |
| `FM.NO-MEMORY` | has no real memory | file-based memory (FBM) + the memory-system component | memory | floor | YES |
| `FM.NARRATION-NOT-ACTION` | narrates intent without the tool call | **persona-discipline only** (`feedback_narration_is_not_action`) — channel auto-route fixed one hole; no general guard | persona-discipline | floor | **NO-PROGRAMMATIC → GAP** |
| `FM.INFERRED-RHYTHM` | infers the user's session/time/rhythm | **persona-discipline only** (`feedback_session_is_a_surface…`) | persona-discipline | proportional | **NO-PROGRAMMATIC → GAP** |
| `FM.ENV-PERCEPTION-MVC` | confuses its internal env-model with the user's view | **persona-discipline only** (`feedback_environment_perception_model_dont_assume`) | persona-discipline | floor | **NO-PROGRAMMATIC → GAP** |
| `FM.PROCESS-DRIFT-UNDER-PRESSURE` | abandons the defined flow under pressure | flow-position discipline + (partial) keep-pace; mostly **persona-discipline** | persona-discipline | floor | **NO-PROGRAMMATIC → GAP** |
| `FM.BUILT-NE-LIVE` | claims built/published from prose, not git refs | **`feedback_published_state_only_from_git_refs`** + substrate-audit gate (partial — shipping docs only) | release-gate + persona-discipline | floor | partial → GAP for non-doc claims |
| `FM.STALE-MEMORY-VS-TRUTH` | trusts a stored claim over live ground truth | the FBM reconcile entry-point (`audit/reconcile.py`) — comparator catches checkable stored claims | comparator | floor | YES for checkable claims; NO for non-checkable (surfaced, owner rules) |
| `FM.SECRET-LEAK` | commits secrets / .env | secret-pattern guard + dangerous-flag guard | hook | floor | YES (UNIVERSAL) |
| `FM.DESTRUCTIVE-PRUNE` | deletes load-bearing thing while pruning | reversibility (version control) + "does anything still depend on it?" check + surface-before-destructive (doctrine §3) | persona-discipline + odd | floor | partial → candidate GAP |
| `FM.BOUNDARY-VIOLATION` | framework writes user-state outside declared homes | `check_boundary_respected` gate (ADR-0001) | release-gate | floor | YES |
| `FM.MIGRATION-GAP` | ships state change with no migration | `check_migration_declared` gate | release-gate | floor | YES |
| `FM.FALSE-FAULT` | manufactures fault that isn't real | four-test discipline (`feedback_no_false_fault_admission`) | persona-discipline | proportional | NO-PROGRAMMATIC |

The builder may refine wording and add proportional rows; the **floor rows and
their gap-status are the contract** (changing a floor row's class or removing a gap
row requires a halt-and-surface per §8).

---

## §6 — Acceptance criteria (outcome-shape; method-in-AC test passed on each)

### AC.FMG-CAT.1 — the catalogue exists and is schema-conformant
The manifest at `framework/protection-matrix/data/failure-mode-guard-matrix.yaml`
parses, and every row carries every required §5 field with a value in its declared
enum. *Outcome-shape: pins the artefact + shape, not the parser.*

### AC.FMG-CAT.2 — every row binds to a REAL, citable guard or an explicit gap
For every row whose `guard_kind` is not `none`/`persona-discipline`, the
`guard_ref` resolves to a path+symbol that exists in the tree at check-time; a row
whose guard does not resolve is reported (no row may claim a guard that isn't
there). *Outcome-shape: pins the no-invented-guards invariant; the resolution method
is the builder's.*

### AC.FMG-CHECK.1 — a real coverage-check entry-point exists and is persona-invokable
`loam guards` is registered through `loam.cli.subcommands`, runs against the live
tree, and emits a report of every floor-class failure mode + its guard + default-on
status. *Outcome-shape: pins the verb + behaviour, not argparse wiring.*

### AC.FMG-CHECK.2 — the check derives the guard set from ground truth, not the manifest's own claim
For a guard the manifest claims is `default_on: YES` via a hook, the check confirms
that hook is actually registered (settings/registration ground truth); a manifest
claim that contradicts ground truth is reported as a divergence. *Outcome-shape:
pins the reconcile invariant (manifest-claim vs wired-reality), mirroring the
substrate-audit comparator; the derivation method is the builder's.*

### AC.FMG-LIVE.1 — the catalogue refresh is wired to the existing recurring cadence
The matrix-refresh is registered as an item in loam's existing recurring
maintenance/pruning flow (NOT a net-new scheduler), such that the catalogue is
re-derived and gap-status re-computed on that cadence. *Outcome-shape: pins
"composes on existing cadence," not which flow-file line; the wiring is the builder's.*

### AC.FMG-GAP.1 — the coverage check NAMES the gaps
A run against the actual guard set emits, as a distinct section of its output, the
list of floor-class failure modes whose `default_on != YES` (the gaps). The list is
non-empty iff such modes exist in the manifest. *Outcome-shape: pins the
actionable-output invariant; the report format is the builder's.*

### ★ AC.FMG-S.1 — outcome-altitude coverage-check at the production entry-point
**`outcome-altitude: true`.** Invoking the production `loam guards` entry-point with
NO pre-arranged state, against the real installed guard set, (a) succeeds, (b) asserts
the floor invariant — *every `class: floor` row is checked for a default-on guard* —
and (c) for every floor row lacking a default-on guard, emits that row in the gap
section. The test inspects the real output of the real verb; it does not stub the
guard set or pre-seed the manifest. *Outcome-shape: pins a real end-to-end coverage
run + the floor invariant + the gap surface; satisfiable by any verb implementation.*
*(Per `feedback_test_outcome_altitude_required`: a STUB-class test that pre-arranges
the manifest does NOT satisfy this AC — the entry-point must walk the real tree.)*

---

## §7 — Out of scope (deferred + when)

1. **Building new guards to CLOSE the gaps.** This plan catalogues + checks; it does
   not author the missing programmatic guards (e.g. a narration-not-action hook, an
   env-perception assertion gate). Each gap is a downstream cycle, prioritised by the
   proportionality of the failure it leaves open. *Deferred to: per-gap follow-up
   cycles, dispatcher-prioritised off the gap report.*
2. **Making the floor invariant a HARD publish-block.** Adding a tenth release gate
   (`check_floor_guards_present`) is a proportionality call (F-4); the verb ships
   independently. *Deferred until: dispatcher rules F-4.*
3. **Auto-remediation.** The check reports; it does not auto-wire a missing guard.
4. **Proportional-tier tuning per user.** The per-user dial above the floor
   (doctrine §"above the floor, rigor flexes") is the adaptive-interaction-model's
   surface, not this catalogue's. *Deferred to: that component.*

---

## §8 — Halt triggers (in-flight; abort the build + surface)

- A floor-class row's guard, on inspection, turns out NOT to exist as claimed → the
  builder must NOT silently downgrade the row to `persona-discipline`; halt and
  surface (it may be a real, undiscovered coverage hole or a manifest error).
- Authoring the catalogue would require EDITING a sealed component's source to make a
  guard "real" → out of fence; halt (this plan adds a catalogue + a verb, it does not
  modify existing guards).
- The `loam guards` entry-point cannot derive the live guard set without an Anthropic
  API key or a network call → halt (`feedback_no_anthropic_api_key`: the check must be
  deterministic, no LLM call; if it can't be, the design is wrong, surface it).
- The gap set comes out EMPTY → halt and surface: given §5's Tier-0 row set, an empty
  gap report means the derivation is wrong (false-negative), not that loam is perfect.

---

## §9 — Bookkeeping (backfill at seal)

- `docs/STATE.md` — append the rollup: objective sentence + seal SHA + the gap-count
  headline (the actionable output is a first-class state fact).
- `docs/release-roadmap.md` §2 — new row for this work with the seal anchor.
- `docs/design/protection-matrix.md` — the generated companion (committed; regenerable).
- A `*.migration.yaml` declaring `operation: no-op` (this adds a verb + data, no
  user-state migration) so `check_migration_declared` passes at publish.
- Parent-doctrine backfill: a pointer from `docs/design/loam-doctrine.md`
  §"protection around" to the matrix as its operational instrument (doc-only,
  exempt surface).

---

## §10 — F2 Ruthless Feedback (honest doubts + named risks)

1. **The gaps are the deliverable, and they are uncomfortable.** Four-to-five floor-
   class failure modes (`FM.NARRATION-NOT-ACTION`, `FM.ENV-PERCEPTION-MVC`,
   `FM.PROCESS-DRIFT-UNDER-PRESSURE`, partially `FM.BUILT-NE-LIVE`,
   `FM.DESTRUCTIVE-PRUNE`) are today guarded **only by persona discipline** — a prose
   rule that the doctrine itself says "decays first under pressure." *Evidence:* each
   has a `feedback_*.md` born from a REAL failure that recurred despite the rule being
   in the corpus (`feedback_narration_is_not_action` fired four times in one night;
   `feedback_environment_perception_model` is explicitly "THIRD instance in one
   session"). *Alternative:* name them as gaps loudly (this plan does), and let the
   gap report drive structural-enforcement cycles (`feedback_structural_enforcement_
   on_recurrence`: a rule violated >once → the fix is a hook, not another memory). The
   matrix is the instrument that makes this trigger systematic instead of incidental.
2. **Risk: the catalogue itself becomes a drift surface.** A hand-maintained matrix
   that lies about coverage is worse than none (it gives false confidence — the exact
   `FM.HALLUCINATION` failure, recursively). *Mitigation baked into §5/AC.FMG-CHECK.2:*
   the check derives the live set from ground truth and reconciles; a manifest that
   over-claims is itself flagged. The prose companion is generated, never hand-edited.
3. **Risk: floor-vs-proportional is a judgment call that could be gamed.** Marking a
   gap row `proportional` quietly removes it from the floor invariant. *Mitigation:* a
   floor→proportional reclassification is a halt-and-surface (§8) — you cannot demote a
   floor failure mode to dodge the gap report without owner sight
   (`feedback_locked_design_not_license_for_bad_outcomes`).
4. **Honest doubt on the `loam guards` ground-truth derivation.** Deriving "is this
   hook default-on?" from settings.json is straightforward; deriving it for ODD/persona-
   discipline rows is NOT programmatically decidable — those rows are inherently
   `NO-PROGRAMMATIC`. That is not a bug to engineer around; it is the finding. The
   check must be honest that a persona-discipline guard is *unverifiable by the check*,
   which is itself the argument for promoting it to a structural guard.

---

## §11 — Provenance trail (every load-bearing source)

**Doctrine + objective:**
- `docs/design/loam-doctrine.md` — §"two sides of leg 2" (protection pillar); §"non-negotiable floor / proportionality"; §3 pruning + recurring-schedule; §"Follow the defined workflow" (prose decays under pressure).
- `docs/VALUE_PROPOSITION.md` — prime-objective § (protection-failure condition); harness/primary-persona tests.
- `CLAUDE.md` Lens 0 + Lens 1 (Claude-leverage) + Lens 3 (ODD) + Lens 7 (RF).

**Guard substrate (Tier-0 read this drive):**
- `framework/tools/loam/src/loam_cli/release/gates.py` — the nine gates (`ALL_GATES`); specifically `check_substrate_audit`, `check_boundary_respected`, `check_migration_declared`.
- `framework/tools/loam/src/loam_cli/audit/cli.py` + `reconcile.py` + `comparator.py` — the `loam audit` verb + FBM reconcile (the entry-point + reconcile PATTERN this plan mirrors).
- `framework/tools/loam/src/loam_cli/cli.py` — the `loam.cli.subcommands` entry-point discovery loop (how `loam guards` registers).
- Hooks: `framework/safety-layer/hooks/{secret_pattern_guard,dangerous_flag_guard,config_write_guard}.py`; `plugins/dev-sdlc/hooks/{objective_binding_gate,tdd_guard,agent_guard,bash_guard}.py`; `framework/hands-off-lifecycle/hooks/{active_scope_sentinel,corpus_load_session_start,keep_pace/*}.py`.

**Failure-mode rows (the catalogue's sources — `~/.claude/projects/-Users-lukeivers-pos3/memory/`):**
- `feedback_narration_is_not_action.md` → `FM.NARRATION-NOT-ACTION`
- `feedback_environment_perception_model_dont_assume.md` → `FM.ENV-PERCEPTION-MVC`
- `feedback_session_is_a_surface_never_infer_user_rhythm.md` → `FM.INFERRED-RHYTHM`
- `feedback_published_state_only_from_git_refs.md` → `FM.BUILT-NE-LIVE`
- `feedback_notes_and_users_are_pointers_evidence_resolves.md` + `feedback_reconcile_checks_against_memory.md` → `FM.STALE-MEMORY-VS-TRUTH`
- `feedback_no_false_fault_admission.md` → `FM.FALSE-FAULT`
- `feedback_structural_enforcement_on_recurrence.md` → the meta-rule that turns gaps into structural-guard cycles.
- `feedback_information_trust_ordering.md` + `feedback_claim_or_cite_no_fake_sources.md` → `FM.HALLUCINATION`.

---

## §12 — Summary of named decisions (owner-readable recommendations)

1. **Catalogue = manifest (source) + generated prose (companion).** *Recommendation:
   adopt.* Single source of truth, no parallel drift surface, substance stays exposed.
2. **Coverage check = a new `loam guards` verb via the existing entry-point group.**
   *Recommendation: adopt.* Lens 1 — zero new CLI plumbing; mirrors `loam audit`.
3. **Check derives the guard set from ground truth + reconciles against the manifest.**
   *Recommendation: adopt.* Makes the matrix self-honest (a manifest that over-claims is
   flagged), defeating the recursive-hallucination risk.
4. **Refresh composes on the doctrine's existing recurring pruning flow.**
   *Recommendation: adopt.* Lens 1 — no net-new scheduler.
5. **Floor-class gaps ship as visible `NO-PROGRAMMATIC` rows, not omissions.**
   *Recommendation: adopt — this IS the deliverable.* The gap report is the actionable
   output that drives downstream structural-enforcement cycles.

---

## §13 — Forks for the dispatcher to rule (with recommendations)

- **F-1 — Manifest schema field set.** Ship §5 verbatim, or let the builder refine?
  *Recommendation: ship §5 as-is; it is outcome-complete.* Low confidence that
  refinement adds value at plan-time; tight scope.
- **F-2 — `loam guards` exit code on a gap.** (a) exit 0 with a gap report (gaps are
  expected, not errors), or (b) exit non-zero (treat any floor gap as a failing check,
  CI-style). *Recommendation: (a) for the standalone verb (gaps are the normal
  reporting state); reserve non-zero for F-4's release-gate arm if adopted.* Signals:
  the verb is a *reporter* first; a non-zero default would make every run "fail" until
  every gap is closed, which punishes honesty.
- **F-3 — v1 gap rows.** Include all five candidate gaps (§5: NARRATION-NOT-ACTION,
  ENV-PERCEPTION-MVC, INFERRED-RHYTHM, PROCESS-DRIFT-UNDER-PRESSURE, plus partial
  BUILT-NE-LIVE / DESTRUCTIVE-PRUNE), or a narrower set? *Recommendation: include all
  five — under-reporting gaps defeats the purpose.* F2: omitting a known gap to make the
  report look better is the `FM.HALLUCINATION` failure applied to loam's own coverage.
- **F-4 — Floor invariant as a release-gate HARD-block now?** Add `check_floor_guards_
  present` as gate #10, OR ship the verb standalone first and gate later.
  *Recommendation: ship the verb standalone in this cycle; defer the gate.* Signals:
  proportionality (a HARD-block on day one would block every publish while the five
  known gaps are open — too heavy before the gaps are even triaged); reversibility (the
  gate is cheap to add once the verb + manifest are proven). This is the multi-signal
  M5 call; reasonable people could weigh "fail loud now" the other way, so it is a fork,
  not an autonomous ruling.

---

## §14 — Method-decision record (builder, post-build)

Builder method choices (ODD §1.1: builder owns method, this plan owns scope).
Build BASELINE: `d9ece972` (main tip + merge-base of `plan/failure-mode-guard-matrix`).

- **D-build.1 — package layout = `loam.protection_matrix` namespace under
  `src/loam/`** mirroring `loam.state_migration_engine` (the template component).
  Modules: `catalogue.py` (loader+schema), `derive.py` (ground-truth resolution),
  `check.py` (reconcile+gap+renderers), `cli.py` (the verb). One module per
  concern keeps the reconcile (`derive`) separable from the report (`check`).
- **D-build.2 — guard_ref resolution = static path + symbol inspection, no
  import/exec.** `derive.resolve_guard_ref` splits `path:symbol`, confirms the
  file exists, and regex-matches a `def`/`class`/module-assignment of the symbol
  in the file text. Deterministic, no LLM, no import side-effects, no network
  (`feedback_no_anthropic_api_key`; plan §8 halt-trigger #3 avoided by design).
  This is the AC.FMG-CHECK.2 ground-truth derivation — it never trusts the
  manifest's own claim.
- **D-build.3 — divergence vs gap are orthogonal axes.** `gap` = floor AND
  default_on≠YES (the coverage signal). `divergence` = a guard-ref-required row
  whose ref does NOT resolve (the over-claim signal — the recursive-hallucination
  guard, plan §10 item 2). A persona-discipline/none row never diverges (empty
  ref is legitimate); only hook/release-gate/comparator/memory rows must resolve.
- **D-build.4 — `default_on` YAML-boolean coercion.** YAML 1.1 reads a bare
  `YES` as boolean `True`. The shipped catalogue quotes the tokens; the loader
  ALSO coerces a parsed `True`→`"YES"` so a maintainer who writes the natural
  unquoted `default_on: YES` is not tripped (defensive — the same trap the
  build hit once).
- **D-build.5 — AC.FMG-LIVE.1 wiring = `loam guards --refresh` as the
  recurring-maintenance ITEM + the doctrine §"protection around" backfill pointer
  naming it.** No standalone canonical "pruning-flow" file artifact exists to slot
  a line into (the cadence is doctrine prose + the self-correction/dormancy
  engines). The honest, proportionate wiring: the refresh is an idempotent,
  generated-not-hand-maintained re-derivation (the property the cadence relies on),
  pointed-to from the doctrine. Building a net-new scheduler is explicitly NOT done
  (Lens 1). The AC test verifies the refresh item exists + is idempotent + the
  companion carries the do-not-hand-edit banner.
- **D-build.6 — the gap report surfaces 6 rows, not 5.** FORK F-3 named five
  floor gaps; the real run ALSO surfaces `FM.HALLUCINATION` as a (partial) floor
  gap (the comparator covers shipping-doc status claims only, not broad
  fact-recall). Surfacing it is the honest derivation (F2 / plan §8 halt-trigger
  #4: an under-count would be the false-negative the plan forbids); the five F-3
  gaps are asserted present by an explicit test, the sixth is a correct addition.
- **D-build.7 — seal-fence BASELINE = `d9ece972`**, allowed prefixes
  `framework/protection-matrix/` + `docs/plans/`, allowed files the manifest
  `universal_paths` set (CLAUDE.md, the odd docs, STATE.md, release-roadmap.md,
  loam-doctrine.md, protection-matrix.md) + `docs/state-migrations/` for the
  no-op migration. Sidecar `SEAL_COMMIT` reads HEAD pre-seal, the seal SHA
  post-seal (the established pattern).

### Commit SHAs

- Amendment commit: `68fb6f892becbc7a010db09f048c07c1e8c7fc6f` —
  `chore(amend): failure-mode-guard-matrix manifest+apply — protection-matrix BASELINE+sidecar bump to d9ece97`
- Seal commit: `729ce44d414b46fe2b7cfbd924714aec02dcfa5c` —
  `chore(seals): failure-mode-guard-matrix — protection-matrix at 68fb6f8`
