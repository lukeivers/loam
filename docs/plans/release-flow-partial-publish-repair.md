# release-flow-partial-publish-repair — sub-plan-doc

Status: sub-plan-doc — BUILD-READY pending dispatcher ratification.
WD: /Users/lukeivers/loam (canonical loam; LOCAL only, NO push).
Class: PATCH (DEV). **Scheduling constraint (carried from roadmap §4
  Candidate 7): this PATCH lands BEFORE the next publish of any class —
  it is a publish-gate dependency, not a competing feature build.**
Parent context: docs/release-roadmap.md §4 Candidate 7
  (`release-flow-partial-publish-repair`, inserted at `0b978198`).
Predecessors (load-bearing, Tier-0 verified this authoring pass):
  - `0b978198` (2026-06-11) — roadmap Candidate 7 insertion (objective,
    constraints, AC.RFPR.* draft).
  - FIDRAFT `F-RELEASE-FLOW-PARTIAL-PUBLISH-NOT-REPAIRABLE`
    (docs/FUTURE_IDEAS_DRAFT.md:311) — the v1.5.0 live-incident empirical
    record; all three claims re-verified in code this pass (§1).
  - `fc4210dd` — v1.5.0 tag SHA on origin (the incident's tag-only state).
  - loam-cli SEAL_COMMIT at plan-authoring: `7e6621f9`.
  - Amendment #143 Scope B — `_find_plan_doc` implicit path delegated to
    `loam_amend.plan_locator.find_plan_doc_by_slug_glob` (gates.py:203-212);
    the locator-fix placement decision (D-RFPR.1) is shaped by this.
BASELINE candidate: `f76164a4` (main tip at plan-authoring; builder
  re-walks if HEAD has moved — do not treat as the apply-time pin).
Quality bar: release-flow correctness fix; existing gate semantics
  untouched; idempotency on fully-published versions is an AC, not a hope.

## §1 Objective / TL;DR

Outcome: **`loam release` re-run completes a partial publish instead of
declaring "nothing to do."** When the tag exists on origin but the GitHub
Release is missing, the flow (with `--release`) detects and creates the
missing Release with generated notes; release-notes generation finds
plan-docs under the `release-integration-v<X-Y-Z>.md` naming; the flow's
success/backfill reporting asserts both halves (tag AND Release) before
declaring the publish complete.

Tier-0 re-verified state at `f76164a4` (re-run this authoring pass, not
taken from the FIDRAFT entry):

1. **Already-on-origin short-circuit — CONFIRMED.** `runner.run()` step 2
   (runner.py:266-322): when `_tag_exists_on_remote` is true, the branch
   runs backfill + post-ship proposal and returns
   `gh_release_created=False`, `idempotent_noop=True`. No `gh release
   view` check anywhere under `src/` (grep: zero hits); a missing Release
   is never detected or created, even with `--release`.
2. **Locator glob misses release-integration naming — CONFIRMED.**
   `gates._find_plan_doc` implicit path (gates.py:202-212) delegates to
   `find_plan_doc_by_slug_glob(repo_root, slug)` (plan_locator.py:96-119),
   which globs `<slug>-*.md` + `<slug>.md` over `docs/plans/sealed/` then
   `docs/plans/`. `release-integration-v1-5-0.md` does not start with the
   `v1-5-0` slug prefix → no match. Nine `release-integration-*.md` docs
   exist under docs/plans/ today (v0-13-0 through v1-5-0).
3. **Notes "(unavailable)" degradation — CONFIRMED, plus a sibling
   fact.** `notes.generate_notes(repo_root, version)` (notes.py:124-151)
   calls `_find_plan_doc(repo_root, version)` with NO explicit path and
   emits "(unavailable: no plan-doc found...)" on miss. Sibling (F2,
   named): `generate_notes` has no `plan_doc` parameter at all — even
   when the operator passes `--plan-doc` (as the v1.5.0 incident recovery
   did), the explicit path never reaches notes generation
   (runner.py:428 calls `generate_notes(repo_root, version)` bare).
   The release-integration docs DO carry extractable `## §1` and `## §13`
   sections (verified against release-integration-v1-5-0.md), so the
   naming fix yields real content, not a different placeholder.
4. **Latent adjacent bug discovered during re-verification (F2,
   named):** the already-on-origin branch ignores `dry_run` entirely —
   runner.py:286 calls `apply_backfill(..., dry_run=False)` and then
   `_commit_and_push_backfill` even when the operator passed `--dry-run`.
   A dry-run against an already-published version can commit AND push
   backfill edits. The repair work rewrites exactly this branch, so the
   guard is folded in (D-RFPR.4, AC.RFPR.4) rather than left as a
   separate cycle touching the same lines twice.

AC family: AC.RFPR.* (4 ACs; AC.RFPR.3 outcome-altitude). Fence: loam-cli
component only (`framework/tools/loam/`), bookkeeping via docs/plans/.

## §2 Placement

All source edits land under `framework/tools/loam/src/loam_cli/release/`
(runner.py; gates.py `_find_plan_doc`; notes.py `generate_notes`
signature) + tests under `framework/tools/loam/tests/` — the loam-cli
component, matching the roadmap Dependencies note ("touches
`framework/tools/loam/src/loam_cli/release/` only"). The shared
`loam_amend.plan_locator` is deliberately NOT touched (D-RFPR.1). Plan
pair + sealed narrative ride the `docs/plans/` universal admission.

## §3 Scope

In scope:
- The already-on-origin branch of `runner.run()` (Release-existence
  detection + repair + dry-run honoring).
- `gates._find_plan_doc` implicit-path resolution of the
  `release-integration-v<X-Y-Z>.md` naming (release-side; D-RFPR.1).
- `notes.generate_notes` accepting the explicit/resolved plan-doc
  (D-RFPR.2).
- The both-halves publish assertion on `--release` runs (success AND
  repair paths).
- Tests for the four ACs; this plan pair; standard `loam amend
  apply`/`seal` bookkeeping.

Out of scope (deferred):
- **Manifest sweep before release-prep stub commits** (the
  manifest-data-conformance plan's §10 F2.2 carry-forward) — named
  decision D-RFPR.3: EXCLUDED from this fence. See §10.
- Any other gate-semantics change (roadmap constraint: only the
  already-on-origin branch gains the Release-existence check). The new
  both-halves assertion is publish-reporting, not a pre-publish gate.
- `loam_amend.plan_locator` (shared helper stays byte-unchanged;
  D-RFPR.1).
- Forcing `--release` on by default (Release creation stays opt-in;
  public action, owner-gated at publish time — the BUILD itself is
  local-only and never invokes the real `gh`).
- Version assignment (derives at release time) and publishing (LOCAL
  only — this plan pair is committed, not pushed).

## §4 Acceptance criteria

| ID | Outcome | Verification |
|---|---|---|
| AC.RFPR.1 | **Partial-publish repair.** With the tag on origin and no GitHub Release, a re-run with `--release` ends with the Release created carrying generated notes, instead of short-circuiting at "already on origin; nothing to do". A `--dry-run` against the same state reports the would-create-Release without creating it. | Test drives the production runner against a faked remote/gh surface (tag present, Release absent); asserts the Release-create invocation occurs with a notes body, and that the dry-run variant performs no create. |
| AC.RFPR.2 | **Release-integration plan-doc naming.** Release-notes generation for a version whose plan-doc is named `release-integration-v<X-Y-Z>.md` produces real §1 + §status/§13 content — no "(unavailable)" placeholders — via both the implicit lookup and an explicit `--plan-doc` path. | Test fixture with a `release-integration-v<X-Y-Z>.md` plan-doc; assert generated notes contain the fixture's §1/§13 text and no "(unavailable" substring; explicit-path variant included. |
| AC.RFPR.3 (outcome-altitude: true) | **Both-halves publish assertion.** A deliberately tag-only state run through the production release entry-point (with `--release`, no pre-arranged repair-specific state) ends with the Release existing, and the flow reports the publish complete only when tag AND Release both exist; a Release-half failure is reported as incomplete, never as success. | Outcome-altitude test: production entry-point (CLI dispatch / `runner.run`) on a fixture repo with faked tag-on-origin + missing Release; assert end-state has the Release and the outcome/report reflects both halves; failure-injection variant asserts non-success reporting. |
| AC.RFPR.4 | **Idempotency + dry-run safety preserved.** A re-run against a fully published version (tag AND Release both present) remains a no-op — no duplicate Release attempt, no spurious mutation. A `--dry-run` invocation that reaches the already-on-origin branch performs no repository mutation (no Release create, no backfill commit, no push) while still reporting state. | Test: fully-published fixture → no `gh release create` invocation, outcome still idempotent-noop; dry-run fixture → zero mutating subprocess invocations from that branch. |

Method-in-AC check passed per AC: each pins WHAT (Release ends up
existing; notes carry real content; both halves asserted; no-op/no-mutate
preserved) and is satisfiable by any mechanism — e.g. the
Release-existence check could be `gh release view`, `gh api`, or a
release-list parse; the naming fix could live in a fallback glob or a
widened resolution chain; all satisfy the ACs. AC.RFPR.1/.2/.3 are the
roadmap-drafted family (AC.RFPR.2 restated outcome-shape — the roadmap
draft named `_find_plan_doc`, a method pointer; the outcome is the
notes-content behavior). AC.RFPR.4 is derived from roadmap constraint 1
(idempotency) + the Tier-0 dry-run finding (§1.4, D-RFPR.4).

Ladder-up: AC.RFPR.* → roadmap §4 Candidate 7 objective (re-run completes
a partial publish) → the publish flow's standing promise that "SHIPPED
PUBLIC" means user-visibly shipped → AC.PO.2 (protection: the harness
must not silently betray the user's published-state belief — this is the
`feedback_published_state_only_from_git_refs` failure surface: the tag
ref was green while the user-visible Releases page was stale for a day).

## §5 Sealed-component fence

- Component: `loam-cli` (seal_test
  `framework/tools/loam/tests/test_no_sealed_amendments.py`, sidecar
  `framework/tools/loam/tests/SEAL_COMMIT`, currently `7e6621f9`).
  Source edits confined to `framework/tools/loam/` (release subpackage +
  tests).
- Universal admissions: `docs/plans/` prefix (this plan pair + sealed
  narrative).
- NOT in fence: `plugins/dev-sdlc/` (the shared plan locator and
  everything else under loam-amend stays byte-unchanged — touching it is
  a fence breach → halt).

## §6 Halt triggers (build-time)

1. Tier-0 re-check at the build's HEAD diverges from the §1 diagnosis
   (short-circuit branch moved/changed, locator already release-aware, or
   notes already plan_doc-parameterized).
2. The Release-existence check or repair cannot be implemented without
   changing pre-publish gate semantics (roadmap constraint) — halt;
   the constraint is owner-ratified roadmap text.
3. Satisfying any AC.RFPR.* turns out to require the shared
   `loam_amend.plan_locator` to change (D-RFPR.1 wrong) — halt and
   surface; widening the fence into dev-sdlc is owner-gated.
4. Any test would need to invoke the real `gh` or push to a real remote —
   halt; the BUILD is local-only (existing convention: tests monkeypatch
   `subprocess.run`; `--release` against real GitHub is a publish-time,
   owner-gated public action).
5. An existing AC.V060.* / AC.BACKFL.* test goes red and the fix would
   require loosening that test — halt; existing guarantees are not
   negotiable inside a PATCH.
6. `loam amend seal` halts on the dispatcher's intentionally-dirty
   `docs/FUTURE_IDEAS_DRAFT.md` → stash → seal → stash-pop with sha256
   verification, per the manifest-data-conformance §14 precedent
   (autonomous; record in §14). Any OTHER dirty state at seal → halt.

## §7 Build steps (method-level guidance; mechanics are the builder's call)

1. `cd /Users/lukeivers/loam && pwd && git log -1 --oneline` — verify WD;
   re-walk BASELINE if HEAD moved past `f76164a4`.
2. Tier-0 RED first: author the AC.RFPR.* tests against the current code
   (existing test conventions: `test_AC_V060_*` fixtures monkeypatch
   `subprocess.run`; follow `test_AC_V060_3_tag_and_push.py` /
   `test_AC_V060_4_release_notes.py` shapes) — expect the four to fail
   for the §1 reasons.
3. Implement per D-RFPR.1/.2/.4: rework the already-on-origin branch
   (Release detection + repair + dry-run honoring + both-halves
   reporting), add the release-side naming resolution, thread the
   resolved plan-doc into notes generation.
4. Full loam-cli test suite green (new ACs + all existing V060/BACKFL/
   SDPD siblings byte-meaning-unchanged per §15).
5. `loam amend apply` + `loam amend seal` against this plan's manifest;
   §14 register backfill. LOCAL only — no push.

## §10 Named decisions (recommendations are the decision; dispatcher rules only if overriding)

- **D-RFPR.1 — Where the naming fix lives: release-side, not the shared
  locator.** RECOMMENDED: `gates._find_plan_doc`'s implicit path gains a
  release-integration-aware fallback (e.g. try the shared slug glob, then
  the `release-integration-v<X-Y-Z>.md` naming); the shared
  `loam_amend.plan_locator.find_plan_doc_by_slug_glob` stays
  byte-unchanged. Grounds (Tier-0): the only non-test caller of the
  shared helper outside loam-amend itself is gates.py:210 — but the
  helper also serves amendment-cycle resolution inside loam-amend, where
  release-integration docs are NOT amendment plan-docs; teaching the
  shared helper a release-only naming is semantic pollution AND drags
  `plugins/dev-sdlc/` into the fence (roadmap Dependencies note pins the
  fence to the release subpackage). Alternative (widen the shared glob)
  rejected on both grounds.
- **D-RFPR.2 — Explicit `--plan-doc` reaches notes generation.**
  RECOMMENDED: `generate_notes` accepts the resolved plan-doc (optional
  parameter; bare call stays valid) and the runner threads its
  `plan_doc` argument through. Grounds (Tier-0, §1.3): the v1.5.0
  incident ran WITH `--plan-doc` and notes still degraded, because
  runner.py:428 calls `generate_notes(repo_root, version)` bare and the
  function has no such parameter. This is in-scope of AC.RFPR.2's
  outcome (the explicit-path variant), not an extra feature.
- **D-RFPR.3 — Adjacent item: manifest sweep before release-prep stubs
  (manifest-data-conformance plan §10 F2.2 carry-forward) — EXCLUDED
  from this fence.** Grounds: (a) roadmap Candidate 7 constraint freezes
  gate semantics — a new pre-publish manifest-sweep gate IS a
  gate-semantics change; (b) Tier-0: no release-prep tooling exists
  under `loam_cli` (grep `release.prep|release-prep` over src: zero
  hits) — the stubs were authored by the release-prep AGENT process, so
  the structural fix is a new gate or a release-prep flow change, not a
  patch to this branch; (c) this PATCH is a publish-gate dependency and
  stays smallest-possible. DISPOSITION: belongs as its own roadmap
  candidate / FIDRAFT graduation ("pre-publish gate: manifest sweep over
  `docs/plans/*.manifest.yaml`" — cheap, the sweep test already exists).
  Surfaced to the dispatcher for FIDRAFT capture (this plan does not
  edit docs/FUTURE_IDEAS_DRAFT.md — dispatcher's capture surface).
- **D-RFPR.4 — Dry-run honoring folded into the reworked branch.**
  RECOMMENDED: IN. The already-on-origin branch ignores `dry_run` today
  (§1.4 — real backfill commit+push during `--dry-run` is possible), and
  the new Release-repair MUST be dry-run-aware regardless (a dry-run
  creating a public GitHub Release would be an ASK-FIRST violation by
  construction). Since the repair rewrites exactly this branch, the
  backfill leg gains the same `dry_run` pass-through in the same edit.
  Maps to AC.RFPR.4 (no mutation from that branch under dry-run).
  Alternative (separate cycle for the dry-run bug) rejected: two cycles
  editing the same lines, and the bug is publish-flow safety — the same
  class this PATCH exists to fix.
- **D-RFPR.5 — Both-halves assertion scope: `--release` runs only.**
  RECOMMENDED: the tag-AND-Release completeness assertion applies when
  the flow is asked for a Release (`--release`); a deliberate
  no-`--release` publish remains legitimately tag-only and is NOT
  reported as incomplete. Grounds: Release creation is opt-in by
  owner-ratified design (roadmap constraint 2); asserting a Release the
  operator never requested would invert that. Residual risk named in F2
  item 2 below.

### F2 Ruthless Feedback / honest doubts

1. **The dry-run mutation bug (§1.4) predates this candidate and was not
   in the FIDRAFT.** Evidence: runner.py:286 (`dry_run=False` literal)
   + `_commit_and_push_backfill` on the same path. Folding it in
   (D-RFPR.4) widens the roadmap's literal "only the already-on-origin
   branch gains the Release-existence check" by one guard in the same
   branch — named here rather than silently absorbed; dispatcher can
   strike AC.RFPR.4's dry-run clause if they rule the widening out.
2. **A no-`--release` publish can still produce a lasting tag-only
   state** (D-RFPR.5). The v1.5.0 incident itself was a `--release`-path
   failure, so this PATCH covers the observed failure; but an operator
   habitually omitting `--release` recreates the user-visible staleness
   with no flow-level signal. Alternative if this recurs: a post-publish
   advisory (not a gate) when the latest Release lags the latest tag —
   future candidate, not this fence.
3. **Repair-path notes inherit notes-quality limits.** The repair creates
   the Release with `generate_notes` output; the sanctioned "manual
   edit-pass post-create" (notes.py docstring) still applies. The awful
   part of the v1.5.0 recovery was the cross-package hand-import +
   splice, which this PATCH eliminates; notes polish remains best-effort.
4. **FIDRAFT's "all 9 gates GREEN" count not re-verified** — gate count
   may have moved (the state-of-loam slice added a substrate-audit gate).
   Not load-bearing for any AC; noted for honesty.

## §14 Method-decision register (populated at build + seal time)

(empty at plan-authoring)

## §15 Backwards-compat verification

- Full loam-cli test suite green; in particular `test_AC_V060_3_tag_and_push.py`
  (tag idempotency), `test_AC_BACKFL.py` (backfill idempotency),
  `test_AC_SDPD_plan_doc_flag.py` (explicit `--plan-doc` gate path), and
  `test_AC_V060_4_release_notes.py` (notes shape) must stay green — the
  short-circuit branch and notes signature both change under them.
- `plugins/dev-sdlc/` diff over the cycle: empty (fence guard).

## §16 Halt-and-surface findings at plan-authoring

1. All three FIDRAFT empirical claims re-verified GREEN against
   `f76164a4` (§1.1-1.3) — no contradiction; no halt.
2. AC.RFPR.2's roadmap draft named `_find_plan_doc` (method pointer);
   restated outcome-shape in §4 with the roadmap intent preserved — the
   drafted family IS satisfiable without method-in-AC; no halt.
3. Two F2-named widenings beyond the roadmap's literal text, both
   surfaced as named decisions with recommendations rather than silently
   applied: D-RFPR.2 (explicit plan-doc threading — in-outcome of
   AC.RFPR.2) and D-RFPR.4 (dry-run guard — same branch, safety-class).
4. Adjacent item ruled OUT with recorded disposition (D-RFPR.3);
   operational-objective test run on all five named decisions — none is
   critical-call / financial; the only public-action surface (`gh
   release create`) stays behind `--release` at publish time and is
   never exercised by the build (halt trigger 4).

## §17 Provenance trail

- Roadmap: docs/release-roadmap.md §4 Candidate 7 (inserted `0b978198`).
- FIDRAFT: docs/FUTURE_IDEAS_DRAFT.md:311
  (`F-RELEASE-FLOW-PARTIAL-PUBLISH-NOT-REPAIRABLE`).
- Short-circuit branch: framework/tools/loam/src/loam_cli/release/runner.py
  :266-322 (idempotency check + early return), :286 (backfill
  `dry_run=False`), :428 (bare `generate_notes` call), :185-213
  (`_gh_release_create`).
- Locator: framework/tools/loam/src/loam_cli/release/gates.py:166-212
  (`_find_plan_doc`; Amendment #143 delegation comment at :203-209);
  plugins/dev-sdlc/tools/loam-amend/src/loam_amend/plan_locator.py:96-119
  (`find_plan_doc_by_slug_glob` — read-only reference, NOT in fence).
- Notes: framework/tools/loam/src/loam_cli/release/notes.py:124-181
  (`generate_notes`, `_extract_section`, "(unavailable" emissions).
- Naming corpus: nine `release-integration-*.md` under docs/plans/
  (ls verified); §1/§13 sections verified in release-integration-v1-5-0.md.
- Adjacent item source: docs/plans/manifest-data-conformance-backfill.md
  §10 F2.2 (sealed 2026-06-11, seal `40fba3ef`).
- Conventions: plugins/dev-sdlc/docs/conventions/plan-docs.md.
