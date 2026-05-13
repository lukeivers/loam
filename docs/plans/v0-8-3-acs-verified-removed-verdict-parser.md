# v0.8.3 PATCH — `acs-verified` gate accepts `REMOVED` as a non-failure verdict

**Status:** plan-only at authoring time. Plan-before-code per `feedback_plan_before_code`.
**Slug:** `v0-8-3-acs-verified-removed-verdict-parser`. Version-named slug — same exception as v0.8.2: this PATCH ships against the still-version-named-discipline gate, since the v0.8.2 patch only fixed the plan-doc-path side, not the verdict-marker side. This PATCH's HARD smoke writeup uses the version-named convention too (`v0-8-3-hard-smoke.md`) so a flag-absent invocation works.
**Date authored:** 2026-05-13.
**Class:** **PATCH** per `docs/release-versioning-policy.md` — defect-closure on v0.6.0's release-process outcome shape (gates substrate); same family as v0.7.2's parser-scoping fix + v0.8.2's plan-doc-path fix. Both prior patches closed orthogonal `check_acs_verified` defects; this PATCH closes a third orthogonal defect surfaced by v0.8.2's AC.SDPD.4 dogfood probe (captured at FIDRAFT F-REMOVED-VERDICT-GATE).
**Predecessor:** v0.8.2 SEALED LOCAL 2026-05-13 (seal `a54295f`; HEAD `a53a8ed`). v0.9.0 also SEALED LOCAL pending owner publish per ASK-FIRST. v0.8.3 builds-forward per `feedback_build_forward_on_publish_pending` and lands on top of v0.8.2's HEAD.
**Working directory:** `/Users/lukeivers/loam/`.
**Owner authorization:** dispatcher-issued 2026-05-13 (current dispatch brief). Build authorization covers plan-doc + source-edit + apply + seal + HARD smoke. Publish remains owner-asked per ASK-FIRST.

---

## §1 — Outcome shape (the "why")

The `check_acs_verified` gate at `framework/tools/loam/src/loam_cli/release/gates.py` iterates §4-declared AC IDs and asserts each one appears within 240 chars of a `GREEN` token in the plan-doc's §status section. The proximity regex (`re.escape(ac) + r".{0,240}?GREEN"`) recognises only one pass token. When an AC is legitimately struck at build-time per ODD §4 re-extension (decision to drop a sub-objective mid-build because empirical reality made the work unshippable or unnecessary), the §status verdict matrix records `REMOVED` with a reference to the build-time decision that struck it, e.g.

```
| AC.ODDPAPER.3 | REMOVED | Build-time D-ODDPAPER.5.2 Path C — stale HTML removed in plan-doc commit `1a8da67`; ship markdown-only; HTML regen captured as FIDRAFT F-PAPER-HTML-REGEN. |
```

The current parser doesn't see `GREEN` near `AC.ODDPAPER.3`, so it flags the AC as missing and returns RED. The publish IS structurally complete (the REMOVED AC was struck via a named build-time decision, not skipped); the gate's parser doesn't encode that distinction.

`feedback_locked_design_not_license_for_bad_outcomes` captures the operational principle: locked ACs are revisitable mid-build when empirical reality contradicts them. The gate should encode that the design IS revisitable per ODD §4 re-extension, with the discipline that the revision must be named in the plan-doc (D-`<plan-id>.<n>` reference).

The fix is a minimal extension to `check_acs_verified`: an AC counts as verified when EITHER (a) it appears within 240 chars of `GREEN` in §status (the v0.6.0 default), OR (b) it appears within 240 chars of `REMOVED` in §status. The narrow widening preserves all other guarantees:

- Missing-verdict (no `GREEN` AND no `REMOVED` token near the AC ID) still returns RED. The fix doesn't open the gate to silently-skipped ACs.
- The v0.6.0 default behaviour (`GREEN` recognition) is unchanged.
- Cross-references in §6 / §8 / §11 / §13 already get filtered upstream by the v0.7.2 §4-scope fix; this PATCH composes with that fix without modifying it.
- The v0.8.2 `--plan-doc` flag's path resolution is unchanged; this PATCH operates on the verdict-matrix scan that runs after path resolution.

After this PATCH lands, `loam release v0.9.0 --plan-doc docs/plans/odd-paper-methodology-publish.md --dry-run` returns all 6 gates GREEN against the live paper-publish artefacts — closing the third and final orthogonal `acs-verified` defect surfaced by the paper publish flow.

**Why PATCH (not MINOR).** No new outcome capability: the `loam release` CLI already publishes versions; this PATCH narrows the existing `acs-verified` gate's parser to recognise a legitimate ODD §4 re-extension verdict. Defect-closure within already-shipped outcome = PATCH per `docs/release-versioning-policy.md`. Same family as v0.7.2 (`AC.READYP.1` — §4 scoping) and v0.8.2 (`AC.SDPD.{2,3}` — plan-doc-path flag): all three are gates with v0.6.0-era assumptions that need PATCH-class follow-ons as new conventions land.

**Why now (build-forward sequencing).** v0.9.0 paper publish is SHIPPED LOCAL pending owner publish; v0.8.2 added `--plan-doc` so the gates read the right paths; v0.8.3 closes the last gate-side defect blocking a fully-GREEN dogfood probe against the paper publish artefacts. Build-forward per `feedback_build_forward_on_publish_pending`: don't stall the build queue on owner-gate availability.

---

## §2 — Prime objective ladder

```
VALUE_PROPOSITION.md prime objective
   └─ "primary persona is a translation layer between the user's
       natural-language intent and AI-effective execution"
        └─ harness toolkit ships working primitives — `loam release`
           is one of those primitives; it must encode ODD §4
           re-extension as a legitimate build-time outcome
             └─ AC.RVG.1 (`check_acs_verified` accepts REMOVED as a
                           non-failure verdict for §4-declared ACs)
             └─ AC.RVG.2 (REMOVED-marker recognition is robust to
                           surrounding text — table-row form +
                           prose-em-dash form + colon form)
             └─ AC.RVG.3 (missing-verdict regression — no GREEN AND
                           no REMOVED near AC ID still returns RED)
             └─ AC.RVG.4 (outcome-altitude dogfood — `loam release
                           v0.9.0 --plan-doc docs/plans/odd-paper-
                           methodology-publish.md --dry-run` returns
                           all 6 gates GREEN against live paper
                           publish artefacts)
             └─ AC.RVG.S (seal-diff discipline — changes only under
                           named fence)
```

**Primary-persona test:** the parser extension reduces translation burden by removing a hard step (manually flip the REMOVED AC to GREEN-with-prose-explanation before publish, or fall back to manual publish entirely). Before this PATCH, the persona either had to (a) re-author the §status verdict matrix to use `GREEN` and explain the REMOVED state in prose, fighting the verdict-matrix structure; or (b) document the publish step as "manual fallback only for any plan-doc with REMOVED ACs." The fix lets the persona use the verdict matrix's own REMOVED verdict directly.

**Harness test:** the fix sharpens an existing primitive (`check_acs_verified`) to encode ODD §4 re-extension as a recognised build-time outcome. Backward-compat preserved: every existing all-GREEN plan-doc continues to pass.

## §3 — Component fence

**Single-component PATCH.** Touched component: `framework/tools/loam/` (release CLI gates + tests).

**PRIMARY (source edits):**
- `framework/tools/loam/src/loam_cli/release/gates.py`:
  - `check_acs_verified` verdict-loop: before adding an AC to `missing`, also try the REMOVED proximity-pattern (`re.escape(ac) + r".{0,240}?REMOVED"`). Skip the AC from `missing` if either pattern matches.
  - Update the docstring to name the REMOVED verdict as a recognised non-failure pass alongside GREEN, referencing `feedback_locked_design_not_license_for_bad_outcomes` and ODD §4 re-extension.

**PRIMARY (tests):**
- `framework/tools/loam/tests/test_AC_RVG_removed_verdict.py` — new file. Four tests covering AC.RVG.{1,2,3} (AC.RVG.4 is the outcome-altitude dogfood; verified via real CLI invocation, captured in the HARD smoke writeup):
  - `test_acs_verified_green_when_status_marks_ac_removed_table_form` — plan-doc with one REMOVED AC in a markdown table row + rest GREEN; assert GREEN result.
  - `test_acs_verified_green_when_status_marks_ac_removed_em_dash_form` — plan-doc with `AC.X.1 — REMOVED at build per D-FOO.5.2` prose form + rest GREEN; assert GREEN result.
  - `test_acs_verified_red_when_status_omits_ac_entirely` — plan-doc with one AC missing from §status (no GREEN AND no REMOVED token near it); assert RED + missing-list names that AC (regression test — the fix doesn't open the gate to silently-skipped ACs).
  - `test_acs_verified_green_when_all_acs_green_regression` — plan-doc with all-GREEN §status; assert GREEN result (regression — the fix preserves the v0.6.0 default).

**PRIMARY (admin docs):**
- `docs/experiments/v0-8-3-hard-smoke.md` — HARD smoke writeup including AC.RVG.4 dogfood probe verbatim output (all 6 gates' verdicts post-patch against the paper publish artefacts).
- `docs/STATE.md` — v0.8.3 SHIPPED LOCAL row at end-of-build.
- `docs/release-roadmap.md` — v0.8.3 §2 row.
- `docs/FUTURE_IDEAS_DRAFT.md` — mark F-REMOVED-VERDICT-GATE as RESOLVED at v0.8.3 (entry resolution per `feedback_future_ideas_draft_workflow` graduation).

**Universal-admission docs:**
- `docs/plans/v0-8-3-acs-verified-removed-verdict-parser.md` (this file).
- `docs/plans/v0-8-3-acs-verified-removed-verdict-parser.manifest.yaml`.

**Untouched:**
- `runner.py` + `cli.py` — no signature changes; the v0.8.2 `--plan-doc` flag plumbing stays untouched.
- `_extract_section_4_body` + `_find_plan_doc` — the v0.7.2 + v0.8.2 helpers stay untouched.
- `docs/release-process.md` — the runbook reads correctly with the parser extension; gates-table copy unchanged.
- `docs/release-versioning-policy.md` — policy unchanged.
- All other framework/plugin components.
- pyproject.toml versions stay at 0.9.0 (v0.8.3 is PATCH; PATCHes ride predecessor MINOR per AC.HONEST.1 / D-NFCLEAN.4 precedent; v0.9.0 is the most-recent shipped MINOR seal in HEAD's ancestry though SHIPPED LOCAL only).

## §4 — Acceptance criteria

Four primary ACs plus seal-diff. AC IDs use scope-descriptive `AC.RVG.*` family (Removed-Verdict-Gate) per `feedback_scope_descriptive_ac_ids`.

### AC.RVG.1 — `check_acs_verified` accepts REMOVED as a non-failure verdict

**What:** When `check_acs_verified` walks the §4-declared AC IDs and checks each against the §status / §13 section, an AC marked `REMOVED` (within 240 chars in §status) is treated as verified — NOT added to the missing-from-GREEN list.

**Acceptance:**
- A plan-doc with §4 declaring `AC.X.1` + `AC.X.2`, and §status carrying `| AC.X.1 | GREEN | ... |` + `| AC.X.2 | REMOVED | Build-time D-FOO.5.2 ... |`, returns GREEN from `check_acs_verified`.
- The success message reports the total count of §4-declared ACs (REMOVED + GREEN combined).
- New test `test_acs_verified_green_when_status_marks_ac_removed_table_form` covers the table-row form.

`outcome-altitude: false` — implementation-altitude AC (gate behaviour verified by test).

### AC.RVG.2 — REMOVED-marker recognition is robust to surrounding text

**What:** The REMOVED proximity-pattern matches the canonical form used in the paper plan-doc (`| AC.ODDPAPER.3 | REMOVED | Build-time D-ODDPAPER.5.2 Path C — ...`) and the prose em-dash form (`AC.X.1 — REMOVED at build per D-FOO.5.2`).

**Acceptance:**
- Two new tests cover the two surface forms:
  - `test_acs_verified_green_when_status_marks_ac_removed_table_form` (table-row form — covers the live paper plan-doc shape).
  - `test_acs_verified_green_when_status_marks_ac_removed_em_dash_form` (prose form — covers possible future plan-docs that don't use a table).
- Both return GREEN.

`outcome-altitude: false` — implementation-altitude (regex robustness verified by test).

### AC.RVG.3 — Missing-verdict still returns RED (regression)

**What:** An AC that appears in §4 but has NEITHER `GREEN` NOR `REMOVED` within 240 chars in §status is still flagged as missing-from-§status. The fix narrowly handles REMOVED; doesn't open the gate to other unknown verdicts or silently-skipped ACs.

**Acceptance:**
- New test `test_acs_verified_red_when_status_omits_ac_entirely` covers the regression: §4 declares `AC.X.1`; §status omits any verdict line for `AC.X.1`; gate returns RED with missing-list naming `AC.X.1`.
- Existing `test_acs_verified_red_when_status_omits_an_ac` test continues to pass without modification.

`outcome-altitude: false` — implementation-altitude (regression coverage).

### AC.RVG.4 — Outcome-altitude dogfood: real release CLI against live paper-publish artefacts

**What:** Run `loam release v0.9.0 --plan-doc docs/plans/odd-paper-methodology-publish.md --dry-run` from `/Users/lukeivers/loam/` against the live paper-publish artefacts at sealed state. All 6 gates return GREEN:

- `hard-smoke` GREEN at `docs/experiments/odd-paper-methodology-publish-hard-smoke.md`.
- `acs-verified` GREEN — naming the count of §4-declared ACs (5: AC.ODDPAPER.{1,2,3,4,S}); AC.ODDPAPER.3 recognised as REMOVED via the new parser branch.
- `state-shipped` GREEN — v0.9.0 marked SHIPPED in `docs/STATE.md`.
- `clean-tree` GREEN — working tree clean post-seal.
- `branch-main` GREEN — on branch `main`.
- `seal-reachable` GREEN — seal `4a4535f` reachable from HEAD.

Per `feedback_test_outcome_altitude_required`, at least one AC must verify against the real production surface; AC.RVG.4 is that AC.

**Acceptance:**
- Verbatim CLI output of the dogfood probe captured in `docs/experiments/v0-8-3-hard-smoke.md`.
- All 6 gate verdict lines GREEN.
- The `acs-verified` GREEN line names the paper plan-doc (`docs/plans/odd-paper-methodology-publish.md`) and the count of §4-declared ACs.
- If any gate is RED post-patch on something unrelated to `acs-verified`, surface to dispatcher (per dispatch brief HARD HALT) but do NOT extend scope.

`outcome-altitude: true` — outcome-altitude AC (real production entry-point against real artefacts).

### AC.RVG.S — Seal-diff discipline

**What:** `git diff --name-only BASELINE..SEAL_COMMIT` shows changes only under the AC.RVG.{1,2,3,4}-allowed paths.

**Acceptance:**
- All paths in the diff are members of:
  - `framework/tools/loam/src/loam_cli/release/gates.py` (AC.RVG.{1,2} edit — verdict-loop extension).
  - `framework/tools/loam/tests/test_AC_RVG_removed_verdict.py` (4 new tests).
  - Universal-admission docs (`docs/plans/v0-8-3-*`, `docs/experiments/v0-8-3-*`, `docs/STATE.md`, `docs/release-roadmap.md`, `docs/FUTURE_IDEAS_DRAFT.md`).
- No source code changes outside `gates.py` + the new test file.
- No pyproject.toml version bumps (PATCH stays at 0.9.0).

## §5 — Decisions builder rules at build time

- **D-RVG.1.a (verdict-loop extension shape):** add a single conditional branch inside the existing `for ac in ac_ids` loop in `check_acs_verified`. Before the AC is added to `missing`, also try the REMOVED proximity-pattern (`re.escape(ac) + r".{0,240}?REMOVED"`). If either GREEN or REMOVED matches, the AC counts as verified. Minimal change; preserves the existing 240-char proximity discipline.
- **D-RVG.1.b (regex compilation pattern):** compile the REMOVED proximity-pattern with `re.DOTALL` (same flag the GREEN pattern uses) so multi-line table cells are handled identically. No new regex flags.
- **D-RVG.2.a (no expansion beyond REMOVED for now):** the v0.8.3 PATCH scope adds REMOVED recognition only. DEFERRED + N/A + other-verdict expansions are explicitly out of scope; if those verdicts surface in real plan-docs, capture as new FIDRAFT for the next patch-cycle. Keeps the parser's failure semantics tight: missing-verdict (no recognised pass token near AC ID) still RED, narrowly defined.
- **D-RVG.2.b (REMOVED proximity-pattern shape — pure token-match, no decision-reference enforcement):** the proximity-pattern accepts any 240-char span between AC ID and the literal `REMOVED` token. Per the FIDRAFT note, an earlier-proposed shape required a `D-<plan-id>.<n>` reference within the proximity (encoding "REMOVED must name the build-time decision that struck it"). The narrower implementation is chosen for v0.8.3: the gate's job is verdict recognition, not verdict-justification verification. Plan-doc discipline (REMOVED ACs MUST name the decision per ODD §4) is enforced by the plan-doc author + reviewer, not the parser. Capture the stricter shape as a follow-on FIDRAFT if needed.
- **D-RVG.3 (test fixture pattern):** new tests reuse the existing `staged_repo` + `fixture_version` + `fixture_slug` conftest fixtures. The §status verdict-matrix shape in the fixture's plan-doc is the bullet-list form (`- AC.V060.1: GREEN`); each new test re-authors the plan-doc's §status section with a table-row or em-dash-prose form to exercise the regex against both shapes.
- **D-RVG.4 (smoke writeup convention for v0.8.3's own publish):** version-named convention (`docs/experiments/v0-8-3-hard-smoke.md`) — same exception as v0.8.2. The discipline shift to scope-descriptive smoke writeup paths only applies AFTER this PATCH ships (the gate looks for `<plan-doc-stem>-hard-smoke.md` when `--plan-doc` is passed; this PATCH's own publish invocation passes `--plan-doc docs/plans/v0-8-3-acs-verified-removed-verdict-parser.md`, but the version-named path is also probed for via the smoke writeup's `v0-8-3-hard-smoke.md` filename for a flag-absent fallback). Same rationale as D-SDPD.5.

## §6 — Out of scope (explicit)

- **DEFERRED + N/A + other-verdict recognition.** Out of scope per D-RVG.2.a; capture as new FIDRAFT if surfaced.
- **Decision-reference enforcement in REMOVED proximity-pattern.** Out of scope per D-RVG.2.b; gate verifies verdict, not verdict-justification.
- **`acs-verified` gate help text / runbook copy updates.** The runbook + gate hint copy mention "GREEN marker" — copy update is out of scope for this PATCH; if the operator-facing copy needs to mention REMOVED, capture as FIDRAFT for next docs cycle.
- **Restructuring `check_acs_verified` beyond the conditional branch.** Per HARD HALT #1, any significant refactor (>2x current complexity) halts and surfaces.
- **Touching other gates (`check_hard_smoke`, `check_state_shipped`, etc.)**. Only `check_acs_verified` is in fence.
- **Anthropic API key paths** (per `feedback_no_anthropic_api_key`, never).
- **Renaming the v0.8.3 plan-doc to scope-descriptive form.** Same exception as v0.8.2: version-named slug stays because this PATCH ships AGAINST its own predecessor's convention.

## §7 — HARD HALTs (build-time)

Halt-and-surface to dispatcher — do NOT proceed past — on any of:

1. The REMOVED proximity-pattern needs >2x current parser complexity to handle the canonical table-row form cleanly. Surface to dispatcher; consider alternate approach (e.g., enumerate-allowed-non-failure-verdicts via a helper function).
2. AC.RVG.4 dogfood probe surfaces a gate other than `acs-verified` still RED post-patch. Surface but do NOT extend scope.
3. ODD §2.5 violation in your work OR surrounding code (per `feedback_subagent_odd_violation_halt`).
4. Wrong-tree-write (any edit lands at a path outside `/Users/lukeivers/loam/`).
5. Any reach for ASK-FIRST class actions: `cd` outside `/Users/lukeivers/loam/`, `git push`, `git tag`, `git commit --amend` (per `feedback_no_amend_in_agent_dispatches`). Immediate halt.
6. Wall-clock exceeds upper band (30-40 min midpoint per §9) by >2× → 80 min. Halt with current state.
7. Discovery that the parser extension breaks any existing test in `test_AC_V060_2_pre_publish_gates.py` or `test_AC_SDPD_plan_doc_flag.py` (regression). Halt + surface.
8. Any reach for an Anthropic API key path (per `feedback_no_anthropic_api_key`). Immediate halt.
9. Untracked file at `docs/plans/promote-multi-channel-extractor-and-iteration-loop-family.md` blocks `loam amend seal` dirty-tree check. Stash + re-run seal per dispatch-brief precedent.

## §8 — Dependencies

- **v0.6.0 (release process)** — HARD. v0.8.3 patches the `acs-verified` gate v0.6.0 introduced.
- **v0.7.2 (release CLI parser fix)** — SOFT. v0.7.2's §4-scoping fix is upstream of v0.8.3's verdict-loop extension; the AC-ID iteration still runs over §4-declared ACs only.
- **v0.8.1 (honesty-cleanup follow-on)** — SOFT. v0.8.3 keeps pyproject.toml versions at 0.9.0 per AC.HONEST.1 / D-NFCLEAN.4 precedent (PATCHes ride predecessor MINOR's version).
- **v0.8.2 (release-CLI scope-descriptive plan-doc support)** — HARD. v0.8.3 is the PATCH immediately following v0.8.2 in the patch chain; the `--plan-doc` flag plumbing v0.8.2 added is used unmodified by AC.RVG.4's dogfood probe.
- **v0.9.0 (paper publish, SHIPPED LOCAL)** — SOFT. v0.8.3's AC.RVG.4 dogfood probe runs against v0.9.0's artefacts. v0.9.0's publish is owner-gated and not blocked by v0.8.3.
- **`docs/release-versioning-policy.md`** — SOFT. PATCH-class declaration grounded in the policy.
- **`feedback_version_numbers_at_release_time`** — SOFT. The convention v0.8.2 closes the gap for; v0.8.3 follows the same version-named-slug exception for its own publish.
- **`feedback_scope_descriptive_ac_ids`** — SOFT. Drives the `RVG` AC ID family choice.
- **`feedback_locked_design_not_license_for_bad_outcomes`** — HARD. The operational principle the parser extension encodes (ODD §4 re-extension as a recognised build-time outcome).
- **`feedback_build_forward_on_publish_pending`** — SOFT. v0.9.0 + v0.8.2 publish-pending; v0.8.3 dispatched in flight.
- **`feedback_no_amend_in_agent_dispatches`** — HARD. Post-fix commits are NEW commits, never `--amend`.
- **`feedback_test_outcome_altitude_required`** — HARD. AC.RVG.4 satisfies the requirement.
- **No external service dependencies.**
- **No new Python packages.**

## §9 — Estimated AI-time

Per `feedback_duration_estimation_rubric` — single-component PATCH; very tight per-AC scope; extending one function (`check_acs_verified`) with a single conditional branch + one new test file with 4 tests + universal-admission docs. Defect-closure shape; confidence in outcome shape is high (Lens 4 — tight scope appropriate). v0.7.2 + v0.8.2 release-CLI-parser-fix PATCH actuals calibrate the upper bound (~49 min for v0.8.2's broader scope; v0.8.3 is narrower).

| Stage | Band | Midpoint |
|---|---|---|
| Plan-doc + manifest authoring (this file) | 5-10 min | 7 min |
| AC.RVG.{1,2,3} — `gates.py` verdict-loop edit | 3-5 min | 4 min |
| AC.RVG.{1,2,3} — 4 new tests at `test_AC_RVG_removed_verdict.py` | 5-8 min | 6 min |
| AC.RVG.4 — dogfood probe + HARD smoke writeup | 5-8 min | 6 min |
| FIDRAFT update (F-REMOVED-VERDICT-GATE resolved) | 1-2 min | 1 min |
| Plan-doc §13 backfill + STATE/roadmap admin + manifest apply + seal | 8-12 min | 10 min |
| **Total v0.8.3 build** | **27-45 min (~0.5-0.75 hr)** | **~34 min (~0.6 hr)** |

Dispatch brief estimates 30-40 min midpoint. Plan-time revision: **27-45 min midpoint ~34 min**. Defensible: single-function single-conditional-branch addition + 4 tests is smaller than v0.8.2's 3-file optional-parameter addition. Midpoint sits well below the 80-min HARD HALT threshold.

Owner gate-review separate (publish per ASK-FIRST after seal).

## §11 — Authority chain

- Current dispatch brief (2026-05-13) — scope ratification + AI-time band + AC family declaration + AC IDs + universal-admission docs list. The dispatch authority for v0.8.3.
- `feedback_locked_design_not_license_for_bad_outcomes.md` — the operational principle the parser extension encodes.
- `feedback_version_numbers_at_release_time.md` (captured 2026-05-13) — the convention v0.8.2 unblocked; v0.8.3 inherits its own publish's version-named exception.
- `feedback_scope_descriptive_ac_ids.md` — AC ID family scope-descriptive (`AC.RVG.*` not `AC.V083.*`).
- `feedback_build_forward_on_publish_pending.md` — v0.9.0 + v0.8.2 publish-pending; v0.8.3 build-forward.
- `docs/release-versioning-policy.md` — PATCH-class declaration ground.
- `docs/FUTURE_IDEAS_DRAFT.md` line 274 (F-REMOVED-VERDICT-GATE) — the FIDRAFT capture v0.8.2 produced; v0.8.3 resolves it.
- `framework/tools/loam/src/loam_cli/release/gates.py` (sealed at v0.6.0 + patched at v0.7.2 + v0.8.1 + v0.8.2) — the surface AC.RVG.{1,2} edits.
- `framework/tools/loam/tests/test_AC_V060_2_pre_publish_gates.py` + `test_AC_SDPD_plan_doc_flag.py` — existing test suites preserved as backward-compat anchor.
- `docs/plans/odd-paper-methodology-publish.md` (v0.9.0 SHIPPED LOCAL plan-doc) — the live artefact AC.RVG.4 dogfood probes against.
- `docs/experiments/odd-paper-methodology-publish-hard-smoke.md` — the live HARD smoke writeup AC.RVG.4 dogfood probes against.
- Memory rules: `feedback_plan_before_code.md` (this plan-doc IS the gate), `feedback_no_amend_in_agent_dispatches.md` (HARD HALT #5), `feedback_no_anthropic_api_key.md` (HARD HALT #8), `feedback_subagent_odd_violation_halt.md` (HARD HALT #3), `feedback_duration_estimation_rubric.md` (§9), `feedback_test_outcome_altitude_required.md` (AC.RVG.4 outcome-altitude).

## §13 — §status

**Build cycle:** TBD-AT-BUILD.

### AC verdict matrix

TBD-AT-BUILD.

### AI-time actuals

TBD-AT-BUILD.

### Halt-and-surface findings

TBD-AT-BUILD.

## §14 — Method decisions

The plan-doc's §5 names the build-time decisions (D-RVG.1.a verdict-loop shape, D-RVG.1.b regex flag, D-RVG.2.a scope-narrow-to-REMOVED-only, D-RVG.2.b no-decision-reference-enforcement, D-RVG.3 test fixture pattern, D-RVG.4 smoke writeup convention). Method-decision-register entries land at §status backfill time.
