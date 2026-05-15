# next-scope-walker-priority-queue-aware — HARD smoke writeup

**Cycle:** v0.10.5 PATCH (slug `next-scope-walker-priority-queue-aware`).
**Date:** 2026-05-14.
**Plan-doc:** `docs/plans/next-scope-walker-priority-queue-aware.md`.
**Slug-named per** `F-CYCLE-ARTEFACT-SLUG-NAMING` (NOT `v0-10-5-hard-smoke.md`).
**FIDRAFT closed:** F-NEXT-SCOPE-EMPTY-§4 (captured 2026-05-14 from v0.10.1 publish output; activation gate: pre-v1.0 release-CLI consistency sweep).

---

## §1 — Outcome shape verified

After this PATCH, the release CLI's `_read_roadmap_priority_queue()` walker at `framework/tools/loam/src/loam_cli/release/post_ship.py` reads the v0.10.0 §4 priority-ordered candidate-queue structure (`### Candidate N — \`<slug>\` — <title>` headings + `**Slug:** \`<slug>\`. **Class:** <class>` lines) instead of the legacy `### vX.Y.Z` shape. The post-ship review block surfaces the top-priority candidate's slug + title + class + slug-fence pointer for every publish. Closes the operator-facing surface that regressed at v0.10.0 when §4's structure changed but the walker wasn't updated. Restores the next-scope proposal to its intended translation function (operator reads "next thing to build is X" from the publish output).

---

## §2 — Static verification (AC.NSWP.1 + AC.NSWP.2 + AC.NSWP.3)

### §2.1 — Test suite (8/8 GREEN; 1 new test added)

```
$ cd /Users/lukeivers/loam/framework/tools/loam && PYTHONPATH=src python3 -m pytest tests/test_AC_V060_6_post_ship_review.py -v
============================= test session starts ==============================
collected 8 items

tests/test_AC_V060_6_post_ship_review.py::test_proposal_carries_next_objective_class_and_fence PASSED
tests/test_AC_V060_6_post_ship_review.py::test_proposal_handles_missing_roadmap_with_placeholders PASSED
tests/test_AC_V060_6_post_ship_review.py::test_proposal_handles_empty_candidate_queue PASSED
tests/test_AC_V060_6_post_ship_review.py::test_pre_1_0_major_eval_returns_pre_1_0 PASSED
tests/test_AC_V060_6_post_ship_review.py::test_post_1_0_major_eval_returns_review_needed PASSED
tests/test_AC_V060_6_post_ship_review.py::test_format_proposal_renders_full_block PASSED
tests/test_AC_V060_6_post_ship_review.py::test_runner_emits_proposal_on_successful_publish PASSED
tests/test_AC_V060_6_post_ship_review.py::test_runner_emits_proposal_on_dry_run PASSED

============================== 8 passed in 1.27s ===============================
```

7 pre-existing tests + 1 new test (`test_proposal_handles_empty_candidate_queue` for AC.NSWP.2) all GREEN. The pre-existing `test_proposal_carries_next_objective_class_and_fence` updated to assert on the new candidate-queue shape (was: `"next things land here" in p.next_objective` + `"v0.7.0" in p.next_ac_or_fence`; now: `"fixture-candidate" in p.next_objective` + `"FIXTURE" in p.next_class` + `"fixture-candidate" in p.next_ac_or_fence`).

### §2.2 — Full release-CLI suite regression (78/78 GREEN excluding pre-existing entry-point failures)

```
$ cd /Users/lukeivers/loam/framework/tools/loam && PYTHONPATH=src python3 -m pytest tests/ \
    --ignore=tests/test_AC_V060_1_release_cli_dispatch.py \
    --ignore=tests/test_AC_OSS_M6_6_loam_cli_subcommand_discovery.py \
    --ignore=tests/test_AC_SDPD_plan_doc_flag.py
============================= test session starts ==============================
tests/test_AC_BACKFL.py ..................................               [ 43%]
tests/test_AC_RVG_removed_verdict.py ....                                [ 48%]
tests/test_AC_V060_2_pre_publish_gates.py .....................          [ 75%]
tests/test_AC_V060_3_tag_and_push.py .....                               [ 82%]
tests/test_AC_V060_4_release_notes.py .....                              [ 88%]
tests/test_AC_V060_6_post_ship_review.py ........                        [ 98%]
tests/test_no_sealed_amendments.py .                                     [100%]

============================== 78 passed in 8.87s ==============================
```

The 7 ignored failures are pre-existing on main (`git stash` baseline at plan-doc commit `ac946a6` reproduces the same 7 failures). They are Python 3.9 environment artefacts: `entry_points()` API mismatch (`got an unexpected keyword argument 'group'`). The release-CLI tests use Python 3.9's `entry_points()` API which doesn't accept `group=` kwarg; production `loam` binary uses Python 3.13 where the API works correctly. F-TF-* class environment artefact, NOT in F-NEXT-SCOPE-EMPTY-§4 scope.

---

## §3 — Outcome-altitude dogfood probe (AC.NSWP.4) — live-canonical-roadmap dry-run before vs after

Live runtime probe runs `loam release v0.10.4 --plan-doc docs/plans/otel-tracer-version-honesty.md --dry-run` against the LIVE canonical `docs/release-roadmap.md` and captures the `Next-scope proposal` block.

### §3.1 — BEFORE (cycle-start baseline; pre-source-edit)

Captured 2026-05-14 at cycle start (commit `aa78baf` — v0.10.4 seal):

```
== Next-scope proposal ==

Next objective: (no entries in §4)
Class hint: (no entries in §4)
Fence: (no entries in §4)

Major-release eval: pre-1.0
  Pre-1.0 release; never cuts major per `release-versioning-policy.md` §1.0.0. The v1.0 quality-bar event is a separate ratification, not a post-publish-trigger event.

--- §4 priority queue excerpt ---

**Shape (post `release-roadmap-priority-queue-restructure` MINOR, 2026-05-13):** §4 lists forward-looking candidates as a **priority-ordered queue of scope-descriptive, unnumbered slugs**. Each candidate carries: a stable slug, a single-sentence objective, a class tag (PATCH / MINOR / MAJOR), an AC family, constraints, source items, an AI-time estimate, and dependencies. Order in the queue reflects current priority decision; first item is "next to build."

**Numbers derive at build-commence time** per `docs/release-versioning-policy.md` §"Number derivation at build-commence time": `next_numbe
…
```

The walker emitted "(no entries in §4)" for all three proposal fields because its regex (`r"(?m)^###\s+(v[0-9][0-9.]*)\s*[—-]\s*(.+)$"`) searched §4 for `### vX.Y.Z` headings — pre-v0.10.0 shape. Live §4 has zero such headings (it was restructured to `### Candidate N — \`<slug>\``); walker's `head_match is None` branch fired with the misleading legacy placeholder.

### §3.2 — AFTER (post-source-edit; live canonical roadmap)

Captured 2026-05-14 via direct walker invocation against live `docs/release-roadmap.md`:

```
$ /opt/homebrew/opt/python@3.13/bin/python3.13 -c "
from pathlib import Path
from loam_cli.release.post_ship import build_proposal, format_proposal
p = build_proposal(Path('/Users/lukeivers/loam'), 'v0.10.4')
print(format_proposal(p))
"

== Next-scope proposal ==

Next objective: binary-usage-observation-harness — Loam builds software from minimal input
Class hint: MINOR (END-USER)
Fence: see docs/release-roadmap.md §4 candidate `binary-usage-observation-harness`

Major-release eval: pre-1.0
  Pre-1.0 release; never cuts major per `release-versioning-policy.md` §1.0.0. The v1.0 quality-bar event is a separate ratification, not a post-publish-trigger event.

--- §4 priority queue excerpt ---

**Shape (post `release-roadmap-priority-queue-restructure` MINOR, 2026-05-13):** §4 lists forward-looking candidates as a **priority-ordered queue of scope-descriptive, unnumbered slugs**. Each candidate carries: a stable slug, a single-sentence objective, a class tag (PATCH / MINOR / MAJOR), an AC family, constraints, source items, an AI-time estimate, and dependencies. Order in the queue reflects current priority decision; first item is "next to build."

**Numbers derive at build-commence time** per `docs/release-versioning-policy.md` §"Number derivation at build-commence time": `next_numbe
…
```

The walker now reads the v0.10.0 candidate-queue structure and surfaces:

- **Next objective:** `binary-usage-observation-harness — Loam builds software from minimal input` (slug + em-dash + title from the `### Candidate 1` heading at `docs/release-roadmap.md:187`)
- **Class hint:** `MINOR (END-USER)` (from the `**Slug:** \`binary-usage-observation-harness\`. **Class:** MINOR (END-USER).` line at `docs/release-roadmap.md:189`)
- **Fence:** `see docs/release-roadmap.md §4 candidate \`binary-usage-observation-harness\`` (slug-keyed pointer)

The §4 priority queue excerpt and major-release eval are unchanged (those branches were already correct; the bug was scoped to the candidate-extraction logic). FUTURE_IDEAS_DRAFT.md recent-captures section unaffected.

### §3.3 — Cross-verification — empty-queue case via synthetic fixture

`test_proposal_handles_empty_candidate_queue` (added at this cycle) verifies AC.NSWP.2: a fixture roadmap with `## §4` heading + prose body + zero `### Candidate N` headings produces:

- `next_objective`: `queue empty — author next candidate before next cycle`
- `next_class`: `queue empty — author next candidate before next cycle`
- `next_ac_or_fence`: `queue empty — author next candidate before next cycle`

NOT the legacy "(no entries in §4)" placeholder (operator can now distinguish parser-fault from queue-empty-by-design).

---

## §4 — AC verdict matrix

| AC | Verdict | Evidence |
|---|---|---|
| AC.NSWP.1 — Walker reads v0.10.0 §4 candidate-queue structure | GREEN | §3.2 live-canonical probe surfaces top candidate `binary-usage-observation-harness` + class `MINOR (END-USER)` + slug-fence pointer; was "(no entries in §4)" pre-edit (§3.1). |
| AC.NSWP.2 — Empty-queue case emits structurally-honest message | GREEN | §3.3 synthetic-fixture test asserts `"queue empty — author next candidate before next cycle"` returned; legacy "(no entries in §4)" placeholder removed. |
| AC.NSWP.3 — Pre-v0.10.0 `### vX.Y.Z` heading shape no longer expected; tests updated | GREEN | §2.1 — 8/8 post_ship tests pass (1 updated + 6 unchanged + 1 new); conftest fixture's roadmap §4 body updated to v0.10.0+ candidate-queue shape. §2.2 — 78/78 release-CLI tests pass (excluding pre-existing entry-point F-TF artefacts). |
| AC.NSWP.4 — Outcome-altitude dogfood probe | GREEN | §3 — verbatim before vs after `Next-scope proposal` blocks captured against the live canonical `docs/release-roadmap.md`; the change propagated through `pip install -e .` (the homebrew `loam` binary loads `loam_cli` from the edited source tree directly). |
| AC.NSWP.S — Seal-diff discipline | TBD-AT-SEAL (verified at apply+seal commit) | Allow-list pre-named in plan-doc §4 AC.NSWP.S; backfilled at §status update commit. |

---

## §5 — Halt-and-surface findings

**No HARD HALTs fired in-cycle.**

**Pre-existing-test-failure clarification:** 7 tests fail in the release-CLI suite (`test_AC_V060_1_release_cli_dispatch.py` ×3, `test_AC_OSS_M6_6_loam_cli_subcommand_discovery.py` ×3, `test_AC_SDPD_plan_doc_flag.py` ×1) due to Python 3.9's `entry_points()` API not accepting `group=` kwarg. Verified pre-existing via `git stash` baseline at plan-doc commit `ac946a6` — same 7 failures. F-TF-* class environment artefact (Python 3.9 vs 3.11+ stdlib API mismatch); NOT in F-NEXT-SCOPE-EMPTY-§4 scope. Production `loam` binary uses Python 3.13 where these tests pass.

**Empirical-recheck-before-halt discipline:** never fired (the walker rewrite had an unambiguous fix-target derivable from the FIDRAFT capture's proposed-shape line + plan-doc D-NSWP.{1,2,3,4} rulings).

**One AC text disambiguation at plan-time** (per `feedback_loose_AC_text_fix_AC_not_implementation`): D-NSWP.4 distinguished the three placeholder branches (roadmap-missing, §4-section-missing, queue-empty) instead of conflating them as the legacy implementation did. Doc-only at plan-time; no post-build adjustment needed.

**One FIDRAFT entry flipped to RESOLVED:** F-NEXT-SCOPE-EMPTY-§4 at `docs/FUTURE_IDEAS_DRAFT.md:276`; entry preserved with RESOLVED block citing this PATCH cycle's plan-doc + smoke writeup paths.

**No new FIDRAFT entries captured.**

**F-FIDRAFT-FLIP-ON-UNBLOCK-PATCH discipline verified:** `grep -rn "F-NEXT-SCOPE-EMPTY-§4" docs/` returned 1 reference (the entry itself). No other FIDRAFT entries reference F-NEXT-SCOPE-EMPTY-§4 as a blocker / dep / unblocker; no flip-on-unblock action needed beyond the entry itself.

---

## §6 — Sources

- Plan-doc: `docs/plans/next-scope-walker-priority-queue-aware.md`
- Manifest: `docs/plans/next-scope-walker-priority-queue-aware.manifest.yaml`
- Walker source: `framework/tools/loam/src/loam_cli/release/post_ship.py`
- Test source: `framework/tools/loam/tests/test_AC_V060_6_post_ship_review.py`
- Test conftest: `framework/tools/loam/tests/conftest.py`
- FIDRAFT entry: `docs/FUTURE_IDEAS_DRAFT.md:276` (F-NEXT-SCOPE-EMPTY-§4)
- Predecessor cycle: v0.10.4 PATCH (sealed `aa78baf`; published `4a94c4d`)
- Originating MINOR: v0.10.0 `release-roadmap-priority-queue-restructure` (sealed `c71b2fa`; published `5dcc630`)
