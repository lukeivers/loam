# v0.2.1 Corrective F1 — odd-extractor `contract-draft.yaml` carries `acs:` + `unhandled_paths:`

**Status:** plan-doc; pre-code per `feedback_plan_before_code`. Authored 2026-05-04 (Sonnet, single-agent plan-author + builder).

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.

**Predecessor:** v0.2.1 Cycle 2 SEALED — apply `c48aa68`, seal `298172e`, §14 backfill `29b26ed`, master plan §9 backfill `5b9b3fd`. v0.2.1 Cycle 3 HARD smoke completed RED (smoke evidence at `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-2-1-live-oss-smoke-2026-05-04.md`).

**Authority:** v0.2.1 master plan §3 Cycle 3 + Decision R explicitly authorize "halt + corrective amendment" on RED smoke. F1 is one of three independently HARD-BLOCKING findings; F2 + F5 land via separate dispatches.

**BASELINE (pre-build tip):** to be set to the source-edit feat commit when the build commit lands.

---

## §1 — Outcome shape (the "why")

The smoke evidence proved the v0.1.9 PR-safety gate is structurally non-functional on real-fixture extractions: extractor writes `contract-draft.yaml` with summary metadata only; pr-safety's `contract.read_contract()` reads `acs:` + `unhandled_paths:` lists from that exact file and finds none, so every diff line classifies as novel and VERIFIED-AC-touching diffs slip past as SURFACE_DECISION instead of HARD_BLOCK.

The fix is producer-side, single-source-of-truth: `verify_contract()` (the Stage 4 writer at `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/verify.py`) writes the full `acs:` list (the same dict shape `raw-acs.yaml` carries) plus the `unhandled_paths:` list into `contract-draft.yaml`. The pr-safety reader contract at `plugins/dev-sdlc/pr-safety/src/loam_pr_safety/contract.py:144-187` is correct as-shipped — producer was wrong. No gate-side change.

**Why producer-side:** synthetic test fixtures (e.g. `plugins/dev-sdlc/odd-extractor/tests/fixtures/synthetic-banded-contract.yaml` and pr-safety's `synthetic_contract_dict` in `tests/conftest.py`) **already carry the `acs:` + `unhandled_paths:` shape** the gate expects. The shape is established; only the production-pipeline writer was lagging.

**Why this passed v0.1.9 / v0.2.0 release-level smoke:** synthetic-fixture tests construct `BandedContract` via the pr-safety fixtures path (which writes the correct shape directly), bypassing the YAML round-trip. Cycle 3 HARD smoke was the first end-to-end production-pipeline exercise, which is exactly what surfaced the gap.

**Cycle 3 smoke promise on this fix:** rerunning the synthetic VERIFIED-AC-deletion probe against rd-automation post-fix produces `action: HARD_BLOCK` (not SURFACE_DECISION). The headline v0.1.9 PR-safety enforcement becomes structurally functional on real fixtures.

---

## §2 — ACs — `AC.OE.CONTRACT-FULL.*` (locked, 5 ACs)

ODD §2.5: every line of code, every branch, every test maps to a named AC.

- **AC.OE.CONTRACT-FULL.1 — `verify_contract()` writes `acs:` field into `contract-draft.yaml`.**
  - Surface: `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/verify.py` extends the `sidecar_payload` dict with `acs: <raw.acs>` (the same `list[dict]` `raw-acs.yaml` carries via `RawACs.model_dump(mode="json")`).
  - Pre-existing summary fields (`schema_version`, `extraction_id`, `repo_path`, `ac_count`, `unhandled_count`, `dry_run`, `created_at`) preserved unchanged; field order updated so `acs:` + `unhandled_paths:` come after `created_at`.
  - Test: `test_AC_OE_CONTRACT_FULL_1_acs_field_written.py` — call `verify_contract()` against a banded `RawACs` (3+ ACs); assert `contract-draft.yaml` parses to a dict whose `acs` key is a list of length-equal-to input; each entry round-trips through `BandedAC.model_validate()`.

- **AC.OE.CONTRACT-FULL.2 — `verify_contract()` writes `unhandled_paths:` field into `contract-draft.yaml`.**
  - Surface: same writer; `sidecar_payload["unhandled_paths"] = [str(p) for p in raw.unhandled_paths]` (string-coerced; `Path` objects don't YAML-dump cleanly via `safe_dump`).
  - Test: `test_AC_OE_CONTRACT_FULL_2_unhandled_paths_field_written.py` — call `verify_contract()` against a `RawACs` with 5+ unhandled paths; assert `contract-draft.yaml`'s `unhandled_paths` is a list of strings; length equals input.

- **AC.OE.CONTRACT-FULL.3 — Round-trip: pr-safety `read_contract()` parses extractor-written `contract-draft.yaml` and produces a populated `BandedContract`.**
  - Surface: integration test at the boundary; no code change to pr-safety. Producer-side fix MUST round-trip cleanly through the consumer's loader.
  - Test: `test_AC_OE_CONTRACT_FULL_3_round_trip.py` — write a banded `RawACs` via `verify_contract()` to a tmp workspace; call `loam_pr_safety.contract.read_contract(repo_id, workspace_root)`; assert `BandedContract.acs` length matches; assert at least one AC.confidence equals VERIFIED.

- **AC.OE.CONTRACT-FULL.4 — Real-fixture regression: production pipeline against `jsts-playwright-app` produces a contract whose pr-safety gate classifies a VERIFIED-AC-touching synthetic diff as HARD_BLOCK.**
  - Surface: end-to-end test exercising the production write path (NOT the test-side `BandedContract` short-circuit). Uses the existing `plugins/dev-sdlc/odd-extractor/tests/fixtures/jsts-playwright-app/` fixture (already in the tree — verified during context-gather).
  - Test: `test_AC_OE_CONTRACT_FULL_4_jsts_fixture_e2e.py` — run `init_extraction → analyze_repo → generate_raw_acs → verify_contract` end-to-end against `jsts-playwright-app`; load contract via `read_contract`; pick one VERIFIED AC (or skip-with-message if fixture has none); construct a synthetic diff that touches that AC's first backing-file; pass through pr-safety's classifier; assert `action == HARD_BLOCK`.
  - Halt-and-surface trigger: if `jsts-playwright-app` produces zero VERIFIED ACs, fall back to pre-constructing one VERIFIED AC into the `RawACs` before `verify_contract()` (the test's purpose is to verify contract round-trip + gate classification on the production write path, not to verify the JS/TS adapter itself).

- **AC.OE.CONTRACT-FULL.5 — Pre-existing extractor + pr-safety test suites remain green post-fix.**
  - Surface: structural — fix MUST NOT regress any sealed AC.
  - Test: meta-AC honored by running full `plugins/dev-sdlc/odd-extractor/tests/` + `plugins/dev-sdlc/pr-safety/tests/` suites at seal-time and verifying zero regressions.

---

## §3 — Build dispatch brief (folded into this run)

This corrective amendment is single-agent: plan-author + builder are the same Sonnet run per dispatch. Build sequence:

1. **Source-edit feat commit (BASELINE).** Edit `verify.py` to add `acs` + `unhandled_paths` to `sidecar_payload`. Add the 4 named-AC test files under `plugins/dev-sdlc/odd-extractor/tests/`. Run touched-component tests + `pr-safety` tests. Single commit subject: `fix(odd-extractor): write acs + unhandled_paths into contract-draft.yaml (v0.2.1 corrective F1)`.
2. **Manifest+apply commit.** `loam amend apply <this manifest>` produces a single merged commit per AC.DPS1.6 schema-v3.
3. **Seal commit.** `loam amend seal --plan-doc <abs path> <this manifest>` produces deterministic short-form seal commit per AC.DPS2 schema-v3 + a §14 backfill follow-up commit per AC.D-sa.7.

**No `git --amend`. No push. Single semantic commit per stage.**

---

## §4 — Halt triggers + bookkeeping

**Halt-and-surface triggers:**
- Producer fix exceeds single-file edit (`verify.py`) by more than 3 files. Signal: blast radius bigger than estimated.
- Real-fixture regression test (AC.OE.CONTRACT-FULL.4) requires extending odd-extractor's test infrastructure non-trivially (e.g., writing a brand-new fixture). The plan commits to using the existing `jsts-playwright-app` fixture; if that fixture's adapter run produces zero VERIFIED ACs, fall back to pre-constructing the `RawACs` directly with one VERIFIED AC (still exercises the production write path).
- Gate-side change emerges as necessary (i.e., extractor-side fix alone doesn't unblock pr-safety). Surface — the smoke evidence pinned producer-side as preferred; deviating requires owner decision.
- Field schema drift between `raw-acs.yaml`'s AC dict shape and what `BandedAC.model_validate()` accepts. The shape is verified-aligned (raw-acs uses `RawACs.model_dump(mode="json")`; pr-safety uses `BandedAC.model_validate(ac_dict)`), but if a real-fixture round-trip surfaces a validation error, surface.
- Cycle wall-clock > 90 min with no progress.
- ODD §2.5 violations in surrounding code → halt + surface.
- Pre-existing tests (any AC.* in odd-extractor or pr-safety) regress → halt + surface; do NOT silently update sealed-AC tests.

**Bookkeeping:**
- `loam amend apply` (= `pos-amend apply`). NOT `git --amend`. NOT manual `git commit`.
- Manifest schema v3.
- Single semantic commit on apply. Subject: `fix(odd-extractor): write acs + unhandled_paths into contract-draft.yaml (v0.2.1 corrective F1)`.
- Short-form seal commit per AC.DPS2 schema-v3.
- §14 backfill via `loam amend seal --plan-doc` flag (separate post-seal commit per AC.D-sa.7).
- NO push.

---

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

Corrective amendment scope is tight (single producer-side YAML field write). Method decisions at §1 (producer-side single-source-of-truth fix; gate-side reader unchanged) + §2 (5 ACs locked under `AC.OE.CONTRACT-FULL.*`) + §4 (halt triggers + bookkeeping). Predecessor master plan: `docs/plans/v0-2-1-master-plan.md` §3 Cycle 3 + Decision R.

### Commit SHAs

- Plan-doc commit: `eda155c` — `docs(plans): v0-2-1-corrective-f1-odd-extractor-contract-draft-fields plan-doc + manifest`
- Source-edit feat commit (BASELINE): `330e66e` — `fix(odd-extractor): write acs + unhandled_paths into contract-draft.yaml (v0.2.1 corrective F1)`
- Manifest baseline-pin commit: `2e74bbd` — `docs(plans): pin v0-2-1-corrective-f1 manifest baseline to 330e66e`
- Amendment apply commit: `0904064` — `chore(amend): v0-2-1-corrective-f1-odd-extractor-contract-draft-fields manifest+apply`
- Seal commit: `ad42314` — `chore(seals): v0-2-1-corrective-f1-odd-extractor-contract-draft-fields — dev-sdlc at 0904064`
- §14 backfill commit: this commit (post-seal follow-up per AC.D-sa.7)
