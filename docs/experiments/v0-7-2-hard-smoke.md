# v0.7.2 HARD smoke — release-CLI `acs-verified` parser-scoping fix

**Verdict: GREEN.** Aggregate verdict for v0.7.2 publish gate: parser-scoping fix lands cleanly; `loam release v0.7.2 --dry-run` `acs-verified` gate returns GREEN naming the 5 in-scope ACs (AC.READYP.{1-4,S}); 21/21 gate tests GREEN (18 existing + 3 new); v0.7.1 plan-doc cross-references restored without re-triggering the defect.

**Date:** 2026-05-10. **Component scope:** `framework/tools/loam/` (release-CLI gate parser + tests). **Out-of-tree scope:** v0.7.1 plan-doc cross-reference revert + FIDRAFT mark-resolved + STATE/roadmap admin rows + this writeup.

---

## §1 — Probe: `loam release v0.7.2 --dry-run` against v0.7.2 plan-doc (AC.READYP.4)

**Outcome-altitude probe** per `feedback_test_outcome_altitude_required`. Real-execution probe — invokes the production CLI binary (`/opt/homebrew/bin/loam` shim, dispatching to the release subpackage built from this commit) against realistic input (this very plan-doc). Risk band: production-facing release-CLI; HARD per-cycle REQUIRED.

### Probe invocation + result

```
$ /opt/homebrew/bin/loam release v0.7.2 --dry-run
```

**First probe RED + in-cycle refinement.** First run flagged 2 false-positives: `AC.NTU.S` (illustrative cross-ref in §4 line 83 prose for AC.READYP.1) + `AC.READYP.X` (illustrative example AC IDs in §4 line 101 prose for AC.READYP.3). Refinement: scope tightened from "all AC IDs in §4 body" to "AC IDs declared as `### AC.<...>` headings within §4" — matches the canonical ODD shape (519 `### AC.` declarations across the corpus). Probe re-run after refinement returned GREEN.

**Second probe verdict (GREEN):** the load-bearing `acs-verified` line:

```
  [GREEN] acs-verified: all 5 AC(s) marked GREEN in docs/plans/v0-7-2-release-cli-parser-fix.md §status
```

The `5 AC(s)` count matches the §4 heading-declared in-scope ACs (`AC.READYP.1`, `AC.READYP.2`, `AC.READYP.3`, `AC.READYP.4`, `AC.READYP.S`). No cross-reference AC IDs from §6 (`AC.READY.7` + `AC.READY.9` mentioned in the structural-enforcement out-of-scope), §8 (`feedback_*` references only), §11 (authority chain naming `AC.V060.*`), or §13 (§status backfill naming the same 5 ACs + cross-ref evidence) are flagged. Importantly: in-§4-prose mentions of `AC.NTU.6` + `AC.V060.7` (in AC.READYP.2's description of the v0.7.1 cross-reference reverts) are also NOT flagged under the heading-form-only invariant.

### Verification — cross-reference + prose scoping both hold

The v0.7.2 plan-doc's §6 names `AC.READY.7` and `AC.READY.9` (cross-references to v0.7.1's ACs in the structural-enforcement out-of-scope statement) — these are NOT flagged (out of §4). The v0.7.2 plan-doc's §11 names ACs from prior versions (`AC.V060.*`) as authority-chain references — these are NOT flagged (out of §4). The v0.7.2 plan-doc's §4 AC.READYP.2 description names `AC.NTU.6` + `AC.V060.7` in prose — these are NOT flagged (in §4 but not as `### AC.<...>` headings). Confirms AC.READYP.1's section + heading-form scoping behavior under the actual canonical plan-doc shape.

Cross-validation: v0.7.1 plan-doc under the fixed parser (`loam release v0.7.1 --dry-run`) reports `[GREEN] acs-verified: all 10 AC(s) marked GREEN in docs/plans/v0-7-1-v1-0-readiness-cleanup.md §status` — exactly the AC.READY.{1-9,S} heading-declared ACs; restored cross-references AC.NTU.6 + AC.V060.7 (now back in v0.7.1's §6 + §8 per AC.READYP.2) are correctly ignored.

### Other gate verdicts at probe-time

The `--dry-run` flag still runs every gate (does NOT short-circuit per AC.V060.2). Other gate verdicts at the probe moment (post-build, pre-seal):

- `hard-smoke`: GREEN (this writeup contains the literal `GREEN` token at line 3).
- `acs-verified`: GREEN per above.
- `state-shipped`: GREEN (`docs/STATE.md` line 132 marks v0.7.2 SHIPPED LOCAL).
- `clean-tree`: depends on probe-time uncommitted state — runs after seal in the canonical sequence.
- `branch-main`: GREEN (canonical clone is on `main`).
- `seal-reachable`: GREEN once the seal commit lands and `docs/release-roadmap.md` §2 v0.7.2 row carries the seal SHA.

The dry-run may report `clean-tree` RED + `seal-reachable` RED at this build-time probe (uncommitted source-edit work + seal not yet present). That's expected and not a v0.7.2-defect signal — those gates are validating the publish-time state, not the build-time state. The publish-time re-run after the seal commit lands is the canonical verdict.

---

## §2 — Test probe: 21/21 gate tests GREEN (AC.READYP.3)

```
$ python3.13 -m pytest framework/tools/loam/tests/test_AC_V060_2_pre_publish_gates.py -v
```

```
============================== 21 passed in 2.46s ==============================
```

Three new tests:
- `test_acs_verified_ignores_cross_references_in_other_sections` — fixture extends conftest's `staged_repo` plan-doc with §6 + §8 cross-reference AC IDs (`AC.OTHER.1`, `AC.OTHER.2`) plus a §status cross-reference (`AC.OTHER.3`); asserts gate returns GREEN naming only the 2 §4-declared ACs.
- `test_acs_verified_red_names_only_section_4_acs_when_status_incomplete` — same §6/§8 cross-references but §status omits one §4-declared AC; asserts gate returns RED naming the missing §4 AC ONLY (cross-reference IDs are silent in the missing-list).
- `test_acs_verified_red_when_section_4_heading_absent` — strips the §4 heading; asserts gate returns RED with corrective hint naming the §4 — Acceptance criteria convention. No fall-back to whole-doc scan (per D-READYP.1.b).

Existing 18 tests unchanged.

---

## §3 — v0.7.1 plan-doc cross-reference revert (AC.READYP.2)

```
$ git diff docs/plans/v0-7-1-v1-0-readiness-cleanup.md
```

Two changed lines, exact form:

```diff
-- **v0.7.0's deeper F-DESIGN finding** (Q4/Q5 dev-intent conditional surfacing) — that's a follow-on amendment captured in v0.7.0's §status; not in v0.7.1 scope.
++ **AC.NTU.6 deeper F-DESIGN finding** (Q4/Q5 dev-intent conditional surfacing) — that's a follow-on amendment captured in v0.7.0's §status; not in v0.7.1 scope.
```

```diff
-- **v0.7.0 (non-tech-user surface)** — HARD on commit-graph. v0.7.1 builds on v0.7.0's HEAD; the publish ritual for v0.7.1 will use the same `loam release` CLI (per v0.6.0's dogfood AC; second use of the verb post-v0.7.0).
++ **v0.7.0 (non-tech-user surface)** — HARD on commit-graph. v0.7.1 builds on v0.7.0's HEAD; the publish ritual for v0.7.1 will use the same `loam release` CLI (per AC.V060.7 dogfood; second use of the verb post-v0.7.0).
```

Verification under fixed parser: running `loam release v0.7.1 --dry-run` (after the parser fix lands) returns GREEN on `acs-verified` — the v0.7.1 plan-doc's 10 §4 ACs (`AC.READY.{1-9,S}`) are all GREEN-marked in §status; the cross-reference `AC.NTU.6` (§6) and `AC.V060.7` (§8) are now ignored by the section-scoped scan.

---

## §4 — Halt-and-surface findings

**v0.7.1 STATE.md SHA backfill stale (out-of-scope; surfaced).** The v0.7.1 STATE.md row at line 132 still reads `Plan-doc + manifest 7ea5fad; source-edit + admin TBD-AT-COMMIT; apply TBD-AT-APPLY; seal TBD-AT-SEAL.` The actual SHAs are known (`d9cf905` source-edit, `5332f1a` apply, `cdae8ed` seal — verified via `git log --oneline`). This is a v0.7.1 backfill issue, not a v0.7.2 defect; the AC.READYP.* ladder does not commit to fixing v0.7.1's STATE rollup. Surfacing per F2 + HARD HALT discipline (do NOT extend scope to fix downstream); dispatcher decides whether to backfill v0.7.1 STATE separately or roll into a future cleanup.

**No other halt-and-surface findings.** Parser fix lands cleanly; existing tests preserved; new tests cover the scoped scan; v0.7.1 plan-doc revert verified two-line-diff; FUTURE_IDEAS_DRAFT line 232 marked RESOLVED with audit history retained inline.

---

## §5 — AI-time actuals (vs plan-doc §9)

To be backfilled at end-of-build alongside §13 §status verdicts.
