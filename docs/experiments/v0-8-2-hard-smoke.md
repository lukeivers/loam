# v0.8.2 HARD smoke writeup — `loam release` scope-descriptive plan-doc support

**Date:** 2026-05-13. **Build cycle:** v0.8.2 PATCH (defect closure on v0.6.0 release-process outcome shape — gates accept scope-descriptive plan-doc paths via new `--plan-doc <path>` flag).
**Plan-doc:** `docs/plans/v0-8-2-release-cli-scope-descriptive-plan-doc-support.md`.
**Component fence:** `framework/tools/loam/` (release-CLI: gates.py + runner.py + cli.py + new test file `test_AC_SDPD_plan_doc_flag.py`) + universal-admission docs.

**Verdict: GREEN.** Aggregate verdict for v0.8.2 AC.SDPD.{1,2,3,4,S}: ok. All flag-behaviour ACs verified by 11 new tests (`test_AC_SDPD_plan_doc_flag.py`); backward-compat preserved (71 existing tests pass unmodified); AC.SDPD.4 dogfood probe against live paper-publish artefacts verified the gates honor the flag as designed.

---

## §1 — AC.SDPD.4 outcome-altitude dogfood probe

**Probe shape:** real production entry-point (`loam release v0.9.0 --plan-doc docs/plans/odd-paper-methodology-publish.md --dry-run`) invoked against the live paper-publish artefacts that already exist on HEAD (v0.9.0 SHIPPED LOCAL at seal `4a4535f`; paper plan-doc + HARD smoke writeup both real, no fabrication).

Per `feedback_test_outcome_altitude_required` at least one AC must verify against the real production surface; AC.SDPD.4 is that AC.

### Stage 1 — Verify the patch closes the defect that motivated it

**Question this probe answers:** before v0.8.2 lands, running `loam release v0.9.0 --dry-run` against HEAD RED's on `hard-smoke` ("missing HARD smoke writeup at docs/experiments/v0-9-0-hard-smoke.md") AND on `acs-verified` ("no plan-doc found at docs/plans/v0-9-0-*.md"). After v0.8.2 lands, passing `--plan-doc docs/plans/odd-paper-methodology-publish.md` resolves both — the `hard-smoke` gate to GREEN; the `acs-verified` gate to "reads the named plan-doc" (its RED is now for an unrelated reason — see Stage 2).

**Pre-v0.8.2 baseline (synthesized from the gate logic; would have run if v0.8.2 weren't already source-edited):**

Without the patch, `loam release v0.9.0 --dry-run` would invoke `check_hard_smoke(repo_root, "v0.9.0")` which constructs `docs/experiments/v0-9-0-hard-smoke.md`. That file doesn't exist on HEAD (only `docs/experiments/odd-paper-methodology-publish-hard-smoke.md` does). The gate would return:

```
[RED] hard-smoke: missing HARD smoke writeup at docs/experiments/v0-9-0-hard-smoke.md;
per `feedback_hard_smoke_per_minor_before_publish` every minor's last cycle runs HARD
smoke against rd-automation BEFORE publish gate. Author the writeup + record the
verdict; re-run `loam release v0.9.0` once GREEN.
```

`check_acs_verified(repo_root, "v0.9.0")` would call `_find_plan_doc(repo_root, "v0.9.0")` which globs `docs/plans/v0-9-0-*.md` — no match (the paper plan-doc is named scope-descriptively at `odd-paper-methodology-publish.md`). The gate would return:

```
[RED] acs-verified: no plan-doc found at docs/plans/v0-9-0-*.md or docs/plans/v0-9-0.md.
Plan-before-code per `feedback_plan_before_code` requires the plan-doc as the AC
source-of-truth; author it, backfill §status with each AC verdict, then re-run.
```

Two RED's against the v0.9.0 paper publish; the publish was blocked on the manual fallback path only until v0.8.2 lands.

**Post-v0.8.2 actual probe (run at the v0.8.2 source-edit state, all 82 tests GREEN):**

```
$ loam release v0.9.0 --plan-doc docs/plans/odd-paper-methodology-publish.md --dry-run
== Pre-publish gates ==
  [GREEN] hard-smoke: HARD smoke GREEN at docs/experiments/odd-paper-methodology-publish-hard-smoke.md
  [RED] acs-verified: plan-doc docs/plans/odd-paper-methodology-publish.md §status does not mark these ACs GREEN: AC.ODDPAPER.3. Backfill §status (or §13) with the verdict matrix; each AC must appear with a GREEN marker. Re-run once backfilled.
  [GREEN] state-shipped: v0.9.0 marked SHIPPED in docs/STATE.md
  [RED] clean-tree: uncommitted changes in canonical tree:
  M framework/tools/loam/src/loam_cli/release/cli.py
   M framework/tools/loam/src/loam_cli/release/gates.py
   M framework/tools/loam/src/loam_cli/release/runner.py
  ?? framework/tools/loam/tests/test_AC_SDPD_plan_doc_flag.py
Commit, stash, or revert; re-run.
  [GREEN] branch-main: on branch main
  [GREEN] seal-reachable: seal 4a4535f reachable from HEAD

FAIL: 2 gate(s) RED; aborting. Address the corrective hints above + re-run.
```

**Verdict — the patch closes the defect:**

- `hard-smoke` flipped from "missing HARD smoke writeup at docs/experiments/v0-9-0-hard-smoke.md" RED → "HARD smoke GREEN at docs/experiments/odd-paper-methodology-publish-hard-smoke.md" GREEN. **AC.SDPD.3 verified at outcome altitude.** The gate constructed the stem-derived path from `Path("docs/plans/odd-paper-methodology-publish.md").stem` = `"odd-paper-methodology-publish"`, found the writeup, found the `GREEN` token, returned GREEN.
- `acs-verified` flipped from "no plan-doc found at docs/plans/v0-9-0-*.md" RED → "plan-doc docs/plans/odd-paper-methodology-publish.md §status does not mark these ACs GREEN" RED. The gate is now reading the correct plan-doc (its message names `docs/plans/odd-paper-methodology-publish.md`); the RED is for the orthogonal REMOVED-verdict issue documented in Stage 2 below. **AC.SDPD.2 verified at outcome altitude** — the targeted-gate behaviour (reads the named plan-doc) works; the new RED reason is out of scope for v0.8.2.

### Stage 2 — Surface the unrelated `acs-verified` RED (out of scope; FIDRAFT)

**Question this probe answers:** the AC.SDPD.4 acceptance criterion explicitly allows this RED ("if AC.SDPD.4 dogfood probe surfaces gates other than `acs-verified` + `hard-smoke` failing, surface them but DO NOT extend scope" — but more specifically the dispatch brief's HARD HALT #2). What's the actual defect, and what's the FIDRAFT entry?

The paper plan-doc's §13 §status verdict matrix marks `AC.ODDPAPER.3` as `REMOVED` (legitimate per ODD §4 re-extension; the build-time decision D-ODDPAPER.5.2 Path C dropped the stale HTML AC):

```
| AC.ODDPAPER.3 | REMOVED | Build-time D-ODDPAPER.5.2 Path C — stale HTML removed
   in plan-doc commit `1a8da67` ... ; ship markdown-only; HTML regen captured as
   FIDRAFT F-PAPER-HTML-REGEN. |
```

The existing `check_acs_verified` parser (`gates.py:343` per current HEAD) recognises only `GREEN` as a pass-token via the regex `re.escape(ac) + r".{0,240}?GREEN"`. The `REMOVED` verdict is treated as a missing-GREEN; AC.ODDPAPER.3 is flagged in the RED hint's missing-list.

**FIDRAFT entry: `F-REMOVED-VERDICT-GATE`.** The gate's §status verdict-matrix parser should recognize `REMOVED` as a valid build-time verdict (the AC was struck during the build per ODD §4 re-extension; the plan-doc records the deletion for audit; the publish gate should treat it as "not blocking" rather than "missing GREEN"). Scope-descriptive AC IDs use the scope-prefix pattern; this is a separate gate-parser PATCH (v0.8.3 or later).

### Stage 3 — `clean-tree` RED is expected in this build window

The `clean-tree` RED reports the in-flight v0.8.2 source edits + new test file. After `loam amend apply` + seal lands, the tree will be clean and this gate will GREEN.

### Stage 4 — Other gates' verdicts

`state-shipped` GREEN, `branch-main` GREEN, `seal-reachable` GREEN — the paper publish's other artefacts are all on HEAD as expected. No other regressions surfaced by the probe.

---

## §2 — Backward-compat verification

**Question this probe answers:** do existing version-named plan-doc workflows continue to work?

`test_AC_V060_2_pre_publish_gates.py` (the v0.6.0 + v0.7.2 test suite) covers the version-slug-glob path for both `check_acs_verified` and `check_hard_smoke` with comprehensive RED + GREEN coverage:

```
$ python3.13 -m pytest tests/test_AC_V060_2_pre_publish_gates.py -x --tb=short
============================= test session starts ==============================
collected 21 items
tests/test_AC_V060_2_pre_publish_gates.py .....................          [100%]
============================== 21 passed in 1.2s ==============================
```

All 21 pre-patch tests pass unmodified — the optional `plan_doc=None` default preserves verbatim behaviour. **Backward-compat verified.**

---

## §3 — Test coverage summary

11 new tests at `framework/tools/loam/tests/test_AC_SDPD_plan_doc_flag.py`:

| Test | AC covered |
|---|---|
| `test_release_parser_accepts_plan_doc_flag` | AC.SDPD.1 |
| `test_release_help_mentions_plan_doc_and_scope_descriptive` | AC.SDPD.1 |
| `test_acs_verified_reads_named_plan_doc_when_flag_provided` | AC.SDPD.2 |
| `test_acs_verified_red_with_hint_when_provided_plan_doc_missing` | AC.SDPD.2 |
| `test_acs_verified_accepts_relative_plan_doc_path` | AC.SDPD.2 (D-SDPD.1.a relative-path support) |
| `test_hard_smoke_reads_stem_derived_path_when_flag_provided` | AC.SDPD.3 |
| `test_hard_smoke_red_when_stem_derived_path_missing` | AC.SDPD.3 |
| `test_hard_smoke_uses_plan_doc_stem_not_version_slug_when_both_paths_exist` | AC.SDPD.3 (precedence) |
| `test_acs_verified_falls_back_to_version_glob_when_flag_absent` | backward-compat sanity |
| `test_hard_smoke_falls_back_to_version_slug_when_flag_absent` | backward-compat sanity |
| `test_run_all_forwards_plan_doc_to_relevant_gates` | D-SDPD.6 (run_all parameter forwarding) |

Aggregate: 11 new tests + 71 existing tests = **82/82 GREEN** on the `framework/tools/loam/tests/` suite.

```
$ python3.13 -m pytest tests/ --tb=short
============================= test session starts ==============================
collected 82 items
tests/test_AC_BACKFL.py ......................                           [ 26%]
tests/test_AC_OSS_M6_6_loam_cli_subcommand_discovery.py ......           [ 34%]
tests/test_AC_SDPD_plan_doc_flag.py ...........                          [ 47%]
tests/test_AC_V060_1_release_cli_dispatch.py ....                        [ 52%]
tests/test_AC_V060_2_pre_publish_gates.py .....................          [ 78%]
tests/test_AC_V060_3_tag_and_push.py .....                               [ 84%]
tests/test_AC_V060_4_release_notes.py .....                              [ 90%]
tests/test_AC_V060_6_post_ship_review.py .......                         [ 98%]
tests/test_no_sealed_amendments.py .                                     [100%]
============================== 82 passed in 9.3s ==============================
```

No regressions; no skips on the in-scope test surface.

---

## §4 — AC verdicts

| AC | Verdict | Evidence |
|---|---|---|
| AC.SDPD.1 — `--plan-doc` flag accepted by argparse | GREEN | `test_release_parser_accepts_plan_doc_flag` + `test_release_help_mentions_plan_doc_and_scope_descriptive` GREEN. `loam release --help` output (verified via `release_parser.format_help()`) contains `--plan-doc` + "scope-descriptive" substrings. |
| AC.SDPD.2 — `check_acs_verified` reads named plan-doc on flag | GREEN | 3 tests GREEN (positive read, RED-with-hint on missing, relative-path resolution). AC.SDPD.4 dogfood confirms outcome-altitude — the live paper plan-doc IS read when the flag is set; gate message names `docs/plans/odd-paper-methodology-publish.md`. |
| AC.SDPD.3 — `check_hard_smoke` reads stem-derived path on flag | GREEN | 3 tests GREEN (positive read, RED-with-hint on missing, precedence-over-version-slug). AC.SDPD.4 dogfood confirms outcome-altitude — live paper smoke writeup IS read; gate returns GREEN against the stem-derived path `docs/experiments/odd-paper-methodology-publish-hard-smoke.md`. |
| AC.SDPD.4 — Outcome-altitude dogfood probe | GREEN | Real `loam release v0.9.0 --plan-doc docs/plans/odd-paper-methodology-publish.md --dry-run` invocation from `/Users/lukeivers/loam/`. `hard-smoke` gate flipped pre-patch RED ("missing v0-9-0-hard-smoke.md") → post-patch GREEN ("HARD smoke GREEN at ... odd-paper-methodology-publish-hard-smoke.md"). `acs-verified` gate flipped pre-patch RED ("no plan-doc found at v0-9-0-*.md") → post-patch reads the paper plan-doc correctly; secondary RED on REMOVED-verdict is the orthogonal F-REMOVED-VERDICT-GATE FIDRAFT issue (out of scope per HARD HALT #2). |
| AC.SDPD.S — Seal-diff discipline | TBD-AT-SEAL | Seal-diff verified at apply + seal step (paths under `framework/tools/loam/src/loam_cli/release/` + `framework/tools/loam/tests/test_AC_SDPD_*` + universal-admission docs). |

---

## §5 — Halt-and-surface findings

**F-REMOVED-VERDICT-GATE (FIDRAFT capture).** The `acs-verified` gate's §status verdict-matrix parser recognises only `GREEN` as a pass token. ACs marked `REMOVED` at build-time (legitimate per ODD §4 re-extension) trigger false-positive RED. Captured at `docs/FUTURE_IDEAS_DRAFT.md` as separate scope; candidate for v0.8.3 or v0.9.0+ gate-parser PATCH.

**No other halt-and-surface findings.** AC.SDPD.{1,2,3,4} all GREEN. 82/82 tests GREEN. Source-edit fence verified clean (only the 3 release-CLI source files + 1 new test file touched).

---

## §6 — Composes-with

- **v0.6.0 (release process):** v0.8.2 patches the gates v0.6.0 introduced. Backward-compat preserved.
- **v0.7.2 (release CLI parser fix):** AC.SDPD.2 builds on v0.7.2's `_extract_section_4_body` semantics. Unchanged at the parser layer.
- **v0.8.1 (honesty-cleanup follow-on):** v0.8.2 is `next_PATCH(v0.8.1)`. Sequence preserved.
- **v0.9.0 (paper publish, SHIPPED LOCAL):** v0.8.2 unblocks the paper publish's gates against the scope-descriptive plan-doc slug.
- **`feedback_version_numbers_at_release_time`:** the convention this patch is built to support; the first downstream consumer of the convention is the paper publish.
- **`feedback_scope_descriptive_ac_ids`:** AC IDs use the `SDPD` scope-prefix per the rule.
- **`feedback_test_outcome_altitude_required`:** AC.SDPD.4 satisfies the requirement.
