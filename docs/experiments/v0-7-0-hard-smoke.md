# v0.7.0 — HARD smoke + outcome-altitude probe verdict

**Date:** 2026-05-09.
**Verdict:** GREEN. AC.NTU.{1-7} all GREEN per the per-AC test families; outcome-altitude AC.NTU.6 probe surfaced + scrubbed an in-scope vocabulary leak inside the cycle (Q4 onboarding text), passed post-fix.

---

## Test coverage summary

62 new NTU.* tests across four components:

| Component | Test file | Tests | Verdict |
|---|---|---|---|
| `plugins/dev-sdlc/tools/loam-amend/` | `tests/test_AC_NTU_4_new_memory.py` | 9 | GREEN |
| `framework/workspace-bootstrap/` | `tests/test_AC_NTU_2_primary_channel_slot.py` | 11 | GREEN |
| `framework/workspace-bootstrap/` | `tests/test_AC_NTU_2_onboarding_extension.py` | 5 | GREEN |
| `framework/workspace-bootstrap/` | `tests/test_AC_NTU_6_outcome_altitude_stranger_clone.py` | 8 | GREEN |
| `framework/primary-persona/` | `tests/test_AC_NTU_1_light_touch_narration.py` | 7 | GREEN |
| `framework/primary-persona/` | `tests/test_AC_NTU_2_channel_routing_decision.py` | 8 | GREEN |
| `framework/primary-persona/` | `tests/test_AC_NTU_7_implementation_tier_picker.py` | 9 | GREEN |
| `framework/hands-off-lifecycle/` | `tests/test_AC_NTU_3_corpus_override_reference_example.py` | 5 | GREEN |
| **Total** | | **62** | **GREEN** |

Run command: `/tmp/loam-build-venv/bin/python -m pytest <test-file>` per component (cross-component runs hit conftest.py path-mismatch errors due to different rootdirs; per-file invocation is the canonical run).

---

## No-regression check

Pre-existing test surface (workspace-bootstrap):

- **Pre-changes (HEAD = `6c4bf55`):** 365 passed, 29 failed, 11 skipped, 17 collection errors.
- **Post-changes (HEAD = `eb0a4d3`):** 389 passed, 29 failed, 11 skipped, 17 collection errors.

Delta: +24 new passing tests (the workspace-bootstrap-component subset of NTU.*); zero new failures; zero regressions on the 29 pre-existing failures + 17 collection errors. Pre-existing failures verified by `git stash --include-untracked && pytest && git stash pop`.

The 29 pre-existing failures are predominantly integration tests requiring component packages not installed in the build venv (workspace-sync / observability-aggregator / orchestrator / safety-layer editable installs absent). The 17 collection errors are MCP-substrate test-file collection failures from `test_AC_OSS_M5_*.py`. Neither category is touched by v0.7.0 work.

---

## AC.NTU.6 outcome-altitude probe — detailed verdict

The probe runs the production-entry-point onboarding ritual against scripted answers + verifies the user-visible surface:

```
$ /tmp/loam-build-venv/bin/python -m pytest \
    framework/workspace-bootstrap/tests/test_AC_NTU_6_outcome_altitude_stranger_clone.py -v

collected 8 items

test_AC_NTU_6_readme_quickstart_section_clean_of_odd_vocab PASSED
test_AC_NTU_6_readme_introduces_quickstart_via_concrete_steps PASSED
test_AC_NTU_6_onboarding_question_text_clean_of_odd_vocab PASSED
test_AC_NTU_6_onboarding_completes_end_to_end_against_scripted_answers PASSED
test_AC_NTU_6_light_touch_narration_skill_at_canonical_path PASSED
test_AC_NTU_6_implementation_tier_picker_skill_at_canonical_path PASSED
test_AC_NTU_6_onboarding_completion_summary_clean_of_odd_vocab PASSED
test_AC_NTU_6_reference_transcript_published_at_canonical_path PASSED

8 passed in 0.11s
```

### First-run RED → in-cycle scrub → GREEN

The first run of the AC.NTU.6 probe surfaced an ODD-vocabulary leak in onboarding Q4:

```
Q4: Run the ODD extractor against this codebase now?
    (1) Yes — fire now (2) Defer — I'll run `loam odd-extract` later
    (3) Never — disable extractor for this workspace
```

`ODD` (uppercase acronym) appears in the user-visible question text. Per AC.NTU.6: forbidden vocabulary in user-visible surface = probe RED.

**In-scope fix applied inside cycle:** Q4 text replaced with —

```
Q4: Scan this codebase for design patterns now?
    (the scanner reads your source files + drafts a design summary;
    useful for software-development workspaces)
    (1) Yes — scan now (2) Defer — I'll run the scan later
    (3) Never — disable the scanner for this workspace
```

Substrate command name `loam odd-extract` preserved for the dev-mode CLI (operators know what it does); user-facing question avoids the substrate term. Existing `framework/workspace-bootstrap/tests/test_AC_ONBOARD_6_extractor_opt_in.py` (4 tests) regression-checked: still GREEN.

### Deeper F-DESIGN finding (deferred)

The vocabulary scrub closes the AC.NTU.6 ship gate, but a deeper design question surfaced: **Q4 + Q5 are dev-mode-only concepts** (extractor scans source code; continuous-watch hooks into git commits). Non-tech-user workspaces (household-finance, journalism, music-production) have no source code to scan; surfacing these questions is noise.

Captured as F-DESIGN candidate for a follow-on amendment: **make Q4 + Q5 conditional on dev-intent detection** (compose with the existing `dev_intent: yes` field on `<workspace>/personas/primary/contract.yaml`; if dev_intent is absent or `no`, skip Q4 + Q5 and default to "skip" for both fields). Estimated 60-120 min AI-time. Logged in plan-doc §status "Halt-and-surface findings" + this writeup.

---

## Per-AC verdict summary (collected for the seal commit narrative)

- **AC.NTU.1** — GREEN. light-touch-narration SKILL ships; 7/7 tests PASS.
- **AC.NTU.2** — GREEN. primary_channel manifest field + onboarding extension + channel_routing policy function; 24/24 tests across 3 files PASS. D-NTU.2.c documented (Stop-hook integration deferred).
- **AC.NTU.3** — GREEN. workspace-corpus-overrides doc + household-finance reference; 5/5 tests PASS.
- **AC.NTU.4** — GREEN. memory-doc template + `loam amend new-memory` orchestration; 9/9 tests PASS. D-NTU.4 switched (parallelism load-bearing).
- **AC.NTU.5** — GREEN. session-transcript artefact published at canonical path.
- **AC.NTU.6** — GREEN. outcome-altitude probe; 8/8 tests PASS post-vocabulary-scrub. F-DESIGN finding deferred per "Halt-and-surface findings" section.
- **AC.NTU.7** — GREEN (Q3 = FOLD IN). implementation-tier-picker SKILL + tier-ladder doc; 9/9 tests PASS.
- **AC.NTU.S** — TBD-AT-SEAL. Verified post-seal via `git diff --name-only BASELINE..SEAL_COMMIT` against the §4 fence.

---

## Authority

- Plan-doc: `docs/plans/v0-7-0-non-tech-user-surface.md`.
- Verdict matrix: §status of plan-doc.
- Source-edit commit: `eb0a4d3`.
