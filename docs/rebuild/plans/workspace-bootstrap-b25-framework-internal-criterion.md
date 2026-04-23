# Amendment #17 — workspace-bootstrap B25 framework-internal-phase criterion plan

**Status:** plan (written before any code edit, per plan-before-code CDC).
**Branch:** `pos-v2` at HEAD `c94e146` (d12-chaos-durability-split-pytest seal — amendment #16's seal commit).
**Amends:** `workspace-bootstrap/docs/rebuild/components/workspace-bootstrap/proposal.md` (new B25 criterion), `workspace-bootstrap/tests/test_extension_protocol.py` (new B25 test), `docs/odd-in-pos.md` (§6 cross-reference). Docs + test-only. Zero `workspace-bootstrap/src/` edits.
**Motivation:** Amendment #4 added `Phase.first_run_scaffold` to `workspace_bootstrap.spec.Phase`. B18's worked example in `docs/odd-in-pos.md` §6 relies on the "Zero change to bootstrap's code" diff assertion and B20 reinforces it at the seal level. The audit surfaced that the new enum value contradicts the *letter* of B18, which reads (in the proposal §4.5) "Zero change to bootstrap's code." B18's *intent* is that a Phase 4+ contribution registers via the public extension protocol without amending bootstrap. The enum addition, however, was a framework-internal amendment (it shipped a new bootstrap-internal adapter — `FirstRunScaffoldContribution`), not an external contribution. The criterion set had no named surface for "framework-internal phase values" vs "phases available to external contributions" — B25 closes that gap.

Owner ruling landed: **path a — add B25** naming `first_run_scaffold` as an intentional framework-internal phase, with rationale and deterministic bounds. B18 continues to govern the external-extension protocol; B25 carves out the framework-internal phase set so the audit has a named surface for each side of the boundary.

---

## 1. Objective

Restore coherence between code reality (four `Phase` enum values shipped: `first_run_scaffold`, `before_orchestrator_start`, `wrap_activate_scope`, `after_orchestrator_ready`) and the B-series criterion set, by adding a new criterion B25 that names the framework-internal phase set and distinguishes it structurally from the external-extension protocol B18 governs.

## 2. Scope

**Primary surfaces:**

- `docs/rebuild/components/workspace-bootstrap/proposal.md` — add §4.8 (new group "Framework-internal phase set") with a single criterion **B25**. Update §4's count header (24 → 25 objectives). Leave B18 text unchanged at the criterion level; it continues to govern the external-extension protocol.
- `workspace-bootstrap/tests/test_extension_protocol.py` — add one new test `test_B25_framework_internal_phases_match_bootstrap_source_adapters`. Co-locates with B18 and B19 since all three cover "what's framework-internal vs external" on the extension-protocol surface.
- `docs/odd-in-pos.md` §6 — append a one-sentence cross-reference to B25 at the end of §6.1 (the "pattern B18 teaches" subsection), noting that B25 is the framework-internal carve-out. Do not rewrite §6's narrative; the B18 worked example stays intact.

**Secondary surfaces (bookkeeping):**
- `workspace-bootstrap/tests/test_no_sealed_amendments.py` — advance `BASELINE` from `b9e1f96` to `c94e146`; extend the BASELINE-history comment block with this amendment's narrative. Extend `allowed_prefixes` to admit `docs/rebuild/components/workspace-bootstrap/` (not previously admitted — the proposal hasn't been modified since the initial port at `a11f081`). Also admit `docs/odd-in-pos.md` via a precise `allowed_files` entry.
- `workspace-bootstrap/tests/SEAL_COMMIT` — sidecar bump to the amendment commit SHA (seal-commit step).
- `hands-off-lifecycle/tests/test_cross_cutting.py` — `BASELINE` advance from `1b144f6` to `c94e146`; extend the BASELINE-history comment block. The existing allowed-top-level set already admits `docs`, `workspace-bootstrap`, and `hands-off-lifecycle` — no tuple change.
- `hands-off-lifecycle/tests/SEAL_COMMIT` — sidecar bump mirroring workspace-bootstrap.
- `hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run` — append an amendment-cycle narrative note.
- `docs/rebuild/plans/workspace-bootstrap-b25-framework-internal-criterion.md` — this plan.

**Not touched:**
- `workspace-bootstrap/src/*` — zero implementation edits. The `Phase` enum stays as-is at four values; B25 names the reality, doesn't change it.
- `workspace-bootstrap/tests/test_first_run_scaffold.py` — no edits. The H-criteria it covers are out of scope for B25.
- B18's test text (`test_B18_*` in `test_extension_protocol.py`) — no edits. B18 continues to govern external extensibility unchanged.
- Any other sealed component's src or tests.

**Boundary with amendment #17's chosen scope:** B25 is a criterion-level carve-out, not an implementation. There is no new code path, no new guard. The test is observational (asserts an invariant over `Phase` + the adapters directory). If the invariant requires a code structural refusal (e.g. "external contributions cannot register under `Phase.first_run_scaffold`"), that would be a separate amendment — halt and flag. B25's test as planned asserts the *current* framework-internal set matches the set the bootstrap source registers; no new refusal code.

## 3. Proposed B25 criterion text

Drafted here as a builder proposal for the proposal doc. Final wording is the builder's call to refine in the commit; the shape below is what §4.8 in the proposal will land.

> **B25 — framework-internal phase set.** The `Phase` enum values in
> `workspace_bootstrap.spec` are the phases registered by contributions
> that live in `workspace-bootstrap/src/workspace_bootstrap/adapters/`
> (the framework-internal adapter bundle). Each enum value has at least
> one bootstrap-internal adapter declaring `phase=Phase.<value>` in its
> `ContributionMetadata`. An external (Phase 4+) contribution declares
> its phase by referencing one of these existing values; adding an
> external contribution does not require extending the enum. If the
> framework-internal phase set grows (e.g. Amendment #4 added
> `first_run_scaffold`), the addition is a bootstrap amendment — not an
> external contribution — and the B18 "zero change to bootstrap's code"
> clause scopes to external-contribution registration, not to
> bootstrap-amendment commits. This criterion provides a named surface
> for the framework-internal phase set so future phase-enum additions
> have explicit audit-trail affordance rather than being silent widenings
> of B18's letter.

Rationale (narrative accompaniment in the proposal): B18 asserts the external-extension contract — a Phase 4+ contribution registers without touching `workspace-bootstrap/src/`. B25 asserts the complementary invariant — the phase-enum values ARE the framework-internal phase set, and external contributions consume them rather than extend them. The two criteria together partition the space: B18 governs the external-extension protocol, B25 names the internal phase surface. When a future amendment widens the enum (as #4 did), the amendment lands as a bootstrap amendment with its own ACs (H1–H5 for #4) and B25 continues to hold; the grown enum set stays "the phases the bootstrap source itself registers."

## 4. Test name + assertion shape

### 4.1 New test: `test_B25_framework_internal_phases_match_bootstrap_source_adapters`

Location: `workspace-bootstrap/tests/test_extension_protocol.py` (same file as B18/B19 — keeps the "what's framework-internal vs external" cohort together).

**Assertion shape** (outcome-shaped; no source-grep):

1. Import `workspace_bootstrap.spec.Phase` and iterate its members.
2. Import each adapter module in `workspace_bootstrap.adapters.*` via `importlib` + `pkgutil.iter_modules` on the adapters package (dynamic discovery; not a hard-coded adapter list).
3. For every adapter module, collect the `ContributionMetadata` off the class(es) that subclass `BaseContribution` or satisfy the `Contribution` protocol. Record each adapter's `phase` attribute.
4. Assert: the set of phases used by framework-internal adapters equals `set(Phase)` — i.e. every `Phase` member has at least one framework-internal adapter using it, and no framework-internal adapter uses a phase outside the enum (tautological but explicit).
5. Assert: `Phase.first_run_scaffold` specifically is used by exactly one framework-internal adapter (the `FirstRunScaffoldContribution` in `workspace_bootstrap.adapters.first_run_scaffold`). This anchors the Amendment-#4 phase's single-purpose status in the criterion.

This shape is observational, not structural-refusal. It asserts an invariant about the code's current shape via dynamic discovery — no grep, no file-path pattern matching, no source-text regex. If a future bootstrap amendment adds a new phase-enum value, this test WILL fail (correctly) until a framework-internal adapter lands using it; the failure message identifies which phase is orphaned. If a future amendment removes an adapter without removing its phase-enum value, same result. The test encodes B25's invariant deterministically.

**Why B18's "zero source change" assertion still holds unchanged:** B18's existing tests (`test_B18_synthetic_phase4_contribution_enables_with_one_manifest_line`, `test_B18_synthetic_contribution_orders_against_foundational`, `test_B18_bootstrap_source_unchanged_diff_check`) assert that a Phase 4+ contribution (the synthetic `onboarding` adapter) registers via the public protocol using an EXISTING phase (`Phase.after_orchestrator_ready`). They do not assert anything about the enum set being closed. B25's invariant is additive — it names the phase-set structure without contradicting the B18 contract. No B18 text change needed.

### 4.2 B18 phrasing adjustment — **not needed**

Per review of `docs/rebuild/components/workspace-bootstrap/proposal.md` §4.5 and `test_extension_protocol.py`: B18's text reads "Zero change to bootstrap's code" *in the context of* admitting a Phase 4+ contribution. The proposal's own framing ("A Phase 4+ component registers itself via a published extension protocol…one line added to the workspace's `bootstrap.yaml` to enable it. **Bootstrap's own code never changes.**" — §1 Objective) already scopes "bootstrap's own code never changes" to the registration act. The B18 test (`test_B18_bootstrap_source_unchanged_diff_check`) is specifically a scan for the string `onboarding` in `src/` — i.e. the test asserts bootstrap's source does not name the synthetic contribution, which is an invariant on the external-extension protocol, not on bootstrap amendments in general.

No phrasing change to B18's criterion text needed. The proposal's §4.5 gets an optional one-sentence cross-reference to B25 after B19 ("See also B25 (§4.8) for the complementary framework-internal phase-set criterion") — builder's call whether to add or omit. Recommend **add** for navigation ergonomics; the criterion set stays coherent either way.

## 5. Plan for §6 cross-reference in `docs/odd-in-pos.md`

At the end of §6.1 ("The pattern B18 teaches"), append one to two sentences as a cross-reference block, before §7 begins. Proposed text:

> B25 (added in amendment #17) is the framework-internal complement to B18:
> it names the `Phase` enum values as the framework-internal phase set that
> bootstrap's own adapters register under, distinguishing a bootstrap
> amendment (which may add a phase-enum value, as Amendment #4's
> `first_run_scaffold` did) from a Phase 4+ contribution (which registers
> against the existing enum values via the external-extension protocol).
> B18's "zero change to bootstrap's code" scopes to external-contribution
> registration; B25 covers the framework-internal phase surface.

No other §6 edits. The B18 worked-example narrative (§6, §6.1 before the appended paragraph) stays intact.

## 6. Test-count delta

- `workspace-bootstrap/` full run: 86 → 87 passing (+1 new B25 test).
- `hands-off-lifecycle/` full run: 66 → 66 (unchanged — BASELINE + narrative edits only).
- All other sealed components' `test_no_sealed_amendments.py`: unchanged (their SEAL_COMMIT sidecars don't move).

## 7. BASELINE advances

- `workspace-bootstrap/tests/test_no_sealed_amendments.py`: `b9e1f96` → `c94e146` (the pre-amendment tip — amendment #16's seal commit immediately before this amendment's code commit).
- `hands-off-lifecycle/tests/test_cross_cutting.py`: `1b144f6` → `c94e146` (same pre-amendment tip).

## 8. `allowed_prefixes` / `allowed_files` changes in workspace-bootstrap seal test

- Add to `allowed_prefixes` tuple: `"docs/rebuild/components/workspace-bootstrap/"` (this amendment is the first workspace-bootstrap proposal-doc edit since the initial port at `a11f081`; the prefix must be admitted so the B20 diff-scope check tolerates the proposal edit).
- Add to `allowed_files` set: `"docs/odd-in-pos.md"` (the methodology doc gets a one-paragraph cross-reference; admitting the exact file keeps the diff-scope check tight — no `docs/` blanket widening).

Both changes are narrow — they admit the exact documentation surfaces this amendment needs, not a broad new top-level bucket.

## 9. `hands-off-lifecycle/tests/test_cross_cutting.py` `allowed` set

No change. The existing set already admits `workspace-bootstrap`, `hands-off-lifecycle`, and `docs` (top-level). `docs/odd-in-pos.md` is reachable via the `docs` top-level admission.

## 10. Halt triggers

- [ ] `first_run_scaffold` actually DOES violate B18 structurally (beyond the criterion-gap resolved by B25) — halt and flag. **Status: CHECKED. Not a structural defect.** B18's assertion is scoped to external-contribution registration (the `onboarding` synthetic is the test fixture); Amendment #4 was a bootstrap amendment with its own H1–H5 criteria, not an external contribution. The B18 test's source-scan (`"onboarding" not in py_file.read_text()`) is agnostic to the phase-enum value count. B25 names the carve-out explicitly; no structural change needed.
- [ ] B25's assertion cannot be written outcome-shaped without source-grep — halt. **Status: CHECKED. Outcome-shaped via `importlib` + `pkgutil.iter_modules`, reading runtime metadata off adapter classes.** No string search over source files.
- [ ] Scope cascades beyond workspace-bootstrap + hands-off-lifecycle + `docs/odd-in-pos.md` + plan doc. **Status: CHECKED. Scope as listed in §2.**
- [ ] B18's existing test breaks and cannot be minimally adjusted — halt. **Status: CHECKED. B25's test does not touch B18's fixtures, data, or assertions; B18's three existing tests keep passing unchanged.**

Halt-check status recorded at plan-writing time:
- Pre-amendment test suites: workspace-bootstrap 86/86 passing; hands-off-lifecycle 66/66 passing (after restoring `hands-off-lifecycle/hooks/first-run.sh` which was missing from the working tree — a pre-existing environmental condition, restored via `git checkout`, unrelated to this amendment's scope).
- All nine other sealed components' `test_no_sealed_amendments.py`: green pre-amendment.
- `allowed_prefixes` tuple in workspace-bootstrap seal test: verified missing `docs/rebuild/components/workspace-bootstrap/` and `docs/odd-in-pos.md` — both get added, both scoped precisely.

## 11. Commit structure

Two commits (no amends, per sealed-component amendment cycle):

1. **Amendment commit** — `fix(workspace-bootstrap, hands-off-lifecycle): workspace-bootstrap B25 framework-internal-phase criterion (amendment #17)` — includes:
   - New B25 text in `docs/rebuild/components/workspace-bootstrap/proposal.md` §4.8; §4 count header 24 → 25; optional one-sentence cross-reference in §4.5 after B19.
   - New `test_B25_framework_internal_phases_match_bootstrap_source_adapters` in `workspace-bootstrap/tests/test_extension_protocol.py`.
   - One-paragraph cross-reference appended to `docs/odd-in-pos.md` §6.1.
   - BASELINE bumps + BASELINE-history comment blocks in `workspace-bootstrap/tests/test_no_sealed_amendments.py` and `hands-off-lifecycle/tests/test_cross_cutting.py`.
   - `allowed_prefixes` + `allowed_files` extensions in workspace-bootstrap seal test.
   - This plan doc.
   - SEAL_COMMIT sidecars: set to the amendment commit's own SHA at the amendment commit itself (matching BASELINE during that commit's window — the cost-governance-C14 pattern; the seal commit below moves them forward to close the window).

   Test suites green before commit:
   - `workspace-bootstrap/`: 87 passing (86 + new B25).
   - `hands-off-lifecycle/`: 66 passing.
   - All other sealed components' `test_no_sealed_amendments.py`: green (their sidecars unchanged).

2. **Seal commit** — `chore(seals): workspace-bootstrap-b25-framework-internal-criterion seal — workspace-bootstrap + hands-off-lifecycle at <amendment-sha>` — bumps `workspace-bootstrap/tests/SEAL_COMMIT` and `hands-off-lifecycle/tests/SEAL_COMMIT` to the amendment commit SHA; appends the amendment-cycle narrative note to `hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run`. Tests green again against the bumped sidecars; diff window B20..c94e146..<amendment-sha> now captures only this amendment's surface.
