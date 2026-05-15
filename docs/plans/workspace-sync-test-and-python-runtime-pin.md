# Workspace-sync test stale-path fix + Python runtime pin honesty PATCH

**Status:** plan-only at authoring time. Plan-before-code per `feedback_plan_before_code`. Owner ratification: dispatcher brief 2026-05-14 explicitly authorises closure of FIDRAFT F-TF-1 + F-PYTHON-3.9-TEST-FAILURES-PYPROJECT-PIN + amendment of F-RETIRE-MIGRATE-TOOLS framing per the prior-dispatch halt-and-surface evidence at `workspace/.scratch/claude-output/retire-one-time-migration-tools-halt-and-surface.md`. This PATCH executes that closure (Path A scope; Path B/C deferred for owner safety-horizon ratification).
**Slug:** `workspace-sync-test-and-python-runtime-pin` (scope-descriptive; no version pre-baked per `feedback_version_numbers_at_release_time`).
**Date authored:** 2026-05-14.
**Class:** **PATCH** per `docs/release-versioning-policy.md`. Test-fixture stale-path fix (single test-file edit) + FIDRAFT-status updates (3 entries: F-TF-1 RESOLVED + F-PYTHON-3.9-TEST-FAILURES-PYPROJECT-PIN RESOLVED-BY-INSPECTION + F-RETIRE-MIGRATE-TOOLS framing AMENDED). No production code change; no public API change; no new outcome capability.
**Predecessor:** v0.10.6 PATCH SHIPPED PUBLIC (sealed `276e0d5`; published `42c0ee6`). Build-forward per `feedback_build_forward_on_publish_pending`.
**Working directory:** `/Users/lukeivers/loam/`.
**Version derivation:** at release-time per `feedback_version_numbers_at_release_time`: `next_PATCH(v0.10.6) = v0.10.7`. Plan-doc slug scope-descriptive; AC family scope-descriptive (`AC.WSP.*` for `workspace-sync-test-and-python-runtime-pin`).

---

## §1 — Outcome shape (the "why")

The prior dispatch (`retire-one-time-migration-tools`) halt-and-surfaced after empirical investigation found three issues with the F-RETIRE-MIGRATE-TOOLS FIDRAFT framing:

1. `framework/tools/heavy-b-migrate/` is NOT a one-time migration script — it's a load-bearing continuous trigger wired into `plugins/dev-sdlc/tools/loam-mode/src/loam_mode/session_start.py:283-299` via `_invoke_lazy_projection()`. Idempotent re-runner. Retiring it would silently break the dev-discipline contract for new dev-intent workspaces.
2. `framework/tools/orphan-plist-cleanup/` is operator-facing for new operators; its retirement is a 4-file edit (manifest + partition test + workspace-sync test + sibling tool cross-references), not a 1-file deletion.
3. The 3 `loam-migrate-*` per-host helpers have no central "has been run" registry — retirement is a safety-horizon judgment call, not a mechanical cleanup.

The full halt-and-surface evidence (with file:line citations + 4-step empirical-recheck per F-AGENT-EMPIRICAL-RECHECK-BEFORE-HALT) is at `workspace/.scratch/claude-output/retire-one-time-migration-tools-halt-and-surface.md`. The recommended Path A (the cleanly-actionable subset) is what this PATCH ships:

- **Sub-scope 1 (F-TF-1):** `framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py:121-130` `expected` tuple includes `framework_tools / "pos-publish-framework-only" / "pyproject.toml"`. The tool was retired previously (the directory does not exist). The test fails on every pytest run. Fix: drop the stale path from `expected` + drop the corresponding comment line at line 119-120.
- **Sub-scope 2 (F-PYTHON-3.9):** the FIDRAFT entry's "Proposed shape" claims `pyproject.toml should declare python_requires>=3.11`. Empirical recheck (F-AGENT-EMPIRICAL-RECHECK-BEFORE-HALT) on every `find framework plugins -name pyproject.toml -exec grep -l "requires-python" {} \;` invocation shows ALL 30 pyproject.toml files already declare `requires-python = ">=3.11"` (16 files) or `requires-python = ">=3.13"` (6 files). The pin has been in place since 2026-04-27 (per `git blame framework/tools/loam/pyproject.toml`); the FIDRAFT was captured 2026-05-14 without the empirical recheck. Verification via `pip install --dry-run framework/tools/loam/` on Python 3.9 returns `ERROR: Package 'loam-cli' requires a different Python: 3.9.17 not in '>=3.11'` — pip refuses install at install-time, exactly as F-PYTHON-3.9 prescribes. The FIDRAFT entry is auto-RESOLVED-BY-INSPECTION at empirical recheck.
- **Sub-scope 3 (F-RETIRE-MIGRATE-TOOLS framing amendment):** the FIDRAFT entry at `docs/FUTURE_IDEAS_DRAFT.md:244` describes 6 retirement candidates (4 `loam-migrate-*` + `heavy-b-migrate` + `orphan-plist-cleanup` + `pos-publish-framework-only`) as "one-time migration scripts that have run." The prior halt-and-surface evidence shows this framing does not survive empirical contact. Doc-only correction: remove `heavy-b-migrate` from the candidate list, clarify that `orphan-plist-cleanup` retirement is a 4-file edit, clarify the per-host helper safety-horizon framing. Status remains `capture-only` (the doc-only correction does NOT flip the entry; the operator-class call is whether to retire Path B/C and is owner's).

After this PATCH:

1. `pytest framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py` GREEN (4/4 instead of 3/4 + 1 failure).
2. F-TF-1 entry status flipped to RESOLVED with the cycle's slug + commit pointer.
3. F-PYTHON-3.9 entry status flipped to RESOLVED-BY-INSPECTION with the empirical-recheck evidence + chain pointer to the 2026-04-27 commit that established the pin.
4. F-RETIRE-MIGRATE-TOOLS entry's "Proposed shape" rewritten to reflect empirical reality (status unchanged — still `capture-only` pending owner Path B/C ratification).

Composes with: `feedback_agent_empirical_recheck_before_halt` (the F-PYTHON-3.9 finding IS an instance — the prior FIDRAFT capture skipped the recheck; this cycle does it), `feedback_loose_AC_text_fix_AC_not_implementation` (the FIDRAFT framing was loose; tighten doc-only without manufacturing implementation work), `feedback_locked_design_not_license_for_bad_outcomes` (F-RETIRE-MIGRATE-TOOLS framing was locked at capture-time; empirical evidence supersedes), `F-PLAN-DOC-TEMPLATE-AUTO-BUMP-FENCE` (this plan-doc pre-includes `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` in AC.WSP.S allow-list per the convention the FIDRAFT captured).

---

## §2 — Prime objective ladder

```
VALUE_PROPOSITION.md prime objective
   └─ "primary persona is a translation layer between the user's
       natural-language intent and AI-effective execution"
        └─ documented features work as advertised + documented-state
           matches actual-state (v1.0 quality-bar criterion #1)
             └─ test fixtures match actual-state (workspace-sync test
                doesn't assert against retired surfaces); FIDRAFT
                entries match empirical-state (no false-deferral
                items lingering as capture-only when already-resolved
                or when their framing is empirically wrong)
                  └─ AC.WSP.1 (workspace-sync test stale-path
                                  expectation removed; pytest GREEN;
                                  F-TF-1 RESOLVED)
                  └─ AC.WSP.2 (F-PYTHON-3.9-TEST-FAILURES-PYPROJECT-PIN
                                  empirically RESOLVED-BY-INSPECTION;
                                  pin already exists pre-capture; entry
                                  status updated with empirical-recheck
                                  evidence)
                  └─ AC.WSP.3 (F-RETIRE-MIGRATE-TOOLS entry "Proposed
                                  shape" rewritten to reflect prior-halt
                                  empirical evidence; heavy-b-migrate
                                  removed from candidate list; per-host
                                  safety-horizon framing clarified)
                  └─ AC.WSP.4 (outcome-altitude dogfood probe — smoke
                                  writeup confirms test pass + pip-install
                                  refusal on 3.9 + FIDRAFT framing
                                  corrected)
                  └─ AC.WSP.S (seal-diff: only the test fix +
                                  FUTURE_IDEAS_DRAFT.md edits +
                                  STATE/roadmap admin + smoke writeup +
                                  plan-doc + manifest + dev-sdlc seal
                                  anchor artefacts touched)
```

The two VALUE_PROPOSITION tests:

- **Primary-persona test** — clean test suites + accurate FIDRAFT capture-state both reduce the translation burden the persona pays at every cycle dispatch. A failing test the persona must repeatedly re-disambiguate ("is this my edit or pre-existing?") IS translation friction; this PATCH eliminates one such instance and corrects three FIDRAFT entries that would mislead future cycle dispatchers.
- **Harness test** — no harness extension; closes a defect within the existing test surface + FIDRAFT capture surface.

Composes with: prior-dispatch halt-and-surface (the empirical-investigation legwork this PATCH builds on), `feedback_agent_empirical_recheck_before_halt` (the F-PYTHON-3.9 finding is the rule applied to a stale FIDRAFT entry), `feedback_loose_AC_text_fix_AC_not_implementation` (the F-PYTHON-3.9 capture's "Proposed shape" was loose; the AC tightens to the empirical reality without manufacturing implementation work).

---

## §3 — Component fence

**PATCH spans one test-file edit + one FIDRAFT-doc edit (3 entries) + STATE/roadmap admin + 1 slug-named smoke writeup.** Seal anchor: dev-sdlc (matches v0.10.6 / v0.10.5 / v0.10.4 / v0.10.3 / v0.10.2 PATCH precedent for single-cycle docs/test-only PATCHes; `framework/tools/loam/` NOT touched).

**PRIMARY (test fix):**

- `framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py` — drop the `framework_tools / "pos-publish-framework-only" / "pyproject.toml"` line from the `expected` tuple at lines 127-129; drop the corresponding comment line at lines 119-120 (`framework/tools/pos-publish-framework-only/`). Single test-file edit (~5 lines removed).

**PRIMARY (FIDRAFT amendments):**

- `docs/FUTURE_IDEAS_DRAFT.md` — three entries edited:
  - F-TF-1 (line 252): status flipped from `capture-only` to RESOLVED with cycle slug + commit pointer.
  - F-PYTHON-3.9-TEST-FAILURES-PYPROJECT-PIN (line 296): status flipped from `capture-only` to RESOLVED-BY-INSPECTION with empirical-recheck evidence + chain pointer.
  - F-RETIRE-MIGRATE-TOOLS (line 244): "Proposed shape" rewritten to reflect prior-halt empirical evidence (heavy-b-migrate removed from candidate list; orphan-plist-cleanup 4-file-edit clarification; per-host helper safety-horizon framing). Status unchanged (still `capture-only`).

**PRIMARY (smoke writeup):**

- `docs/experiments/workspace-sync-test-and-python-runtime-pin-hard-smoke.md` — slug-named per F-CYCLE-ARTEFACT-SLUG-NAMING. Documents:
  - §1 outcome shape verified (4/4 tests pass)
  - §2 static verification (pytest output before vs after)
  - §3 F-PYTHON-3.9 empirical-recheck (pip --dry-run output on 3.9 confirming the pin works; grep across all pyproject.toml files for requires-python; git blame for original pin commit)
  - §4 F-RETIRE-MIGRATE-TOOLS framing-correction diff summary
  - §5 outcome-altitude dogfood probe (release-CLI 6-gate dry-run all GREEN against this plan-doc)

**ADMIN (universal-admission docs):**

- `docs/STATE.md` — v0.10.7 row added at the SHIPPED-LOCAL position.
- `docs/release-roadmap.md` — §3 v0.10.7 PATCH SHIPPED LOCAL entry; §2 active-version-row updated.
- `docs/plans/workspace-sync-test-and-python-runtime-pin.md` — this plan-doc.
- `docs/plans/workspace-sync-test-and-python-runtime-pin.manifest.yaml` — manifest.

**dev-sdlc seal anchor artefacts:**

- `plugins/dev-sdlc/seals/SEAL_COMMIT.workspace-sync-test-and-python-runtime-pin` — narrative.
- `plugins/dev-sdlc/tests/SEAL_COMMIT` — sidecar (auto-bumped by `loam amend seal`).
- `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` — BASELINE pointer (auto-bumped by `loam amend seal`; pre-included in AC.WSP.S allow-list per F-PLAN-DOC-TEMPLATE-AUTO-BUMP-FENCE).

**OUT OF SCOPE (HARD HALT class — would extend the PATCH unilaterally):**

- Retiring ANY of the migration tools (Path B/C are owner-class — defer per prior-dispatch halt evidence).
- Editing heavy-b-migrate or orphan-plist-cleanup or any production code path.
- Adding new tests beyond what's needed for the AC.WSP.S scope-fence verification.
- `git commit --amend` (NEW commits only per `feedback_no_amend_in_agent_dispatches`).
- Bumping per-component pyproject.toml versions (PATCHes ride predecessor MINOR per AC.HONEST.1 / D-NFCLEAN.4 / D-SDPD / v0.8.3 / v0.10.1-v0.10.6 precedent).

---

## §4 — Acceptance Criteria

### AC.WSP.1 — workspace-sync test stale-path expectation removed; F-TF-1 RESOLVED

**Outcome:** `framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py` no longer asserts that `framework/tools/pos-publish-framework-only/pyproject.toml` exists. Pytest invocation `python3.13 -m pytest framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py` returns 4 passed (was: 3 passed + 1 failed at `test_AC_D_5_5_1_framework_tools_present`). FIDRAFT entry F-TF-1 (`docs/FUTURE_IDEAS_DRAFT.md:252`) status flipped to RESOLVED with slug + commit pointer.

**Verification:** `python3.13 -m pytest framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py -v` → 4/4 PASSED. Captured in smoke writeup §2.

### AC.WSP.2 — F-PYTHON-3.9-TEST-FAILURES-PYPROJECT-PIN RESOLVED-BY-INSPECTION

**Outcome:** FIDRAFT entry F-PYTHON-3.9-TEST-FAILURES-PYPROJECT-PIN (`docs/FUTURE_IDEAS_DRAFT.md:296`) status flipped from `capture-only` to RESOLVED-BY-INSPECTION with empirical-recheck evidence: (a) all 30 `pyproject.toml` files across `framework/` + `plugins/` already declare `requires-python = ">=3.11"` (16 files) or `requires-python = ">=3.13"` (6 files); (b) the pin has been in place since 2026-04-27 (`git blame` on `framework/tools/loam/pyproject.toml` for the `requires-python` line returns commit `0d599bb` from 2026-04-27); (c) `pip install --dry-run framework/tools/loam/` on Python 3.9 returns `ERROR: Package 'loam-cli' requires a different Python: 3.9.17 not in '>=3.11'` — pip refuses install at install-time, exactly as F-PYTHON-3.9 prescribes. The FIDRAFT entry was captured 2026-05-14 without the empirical recheck per `feedback_agent_empirical_recheck_before_halt` discipline.

**Verification:** smoke writeup §3 captures the three pieces of empirical evidence verbatim.

### AC.WSP.3 — F-RETIRE-MIGRATE-TOOLS "Proposed shape" rewritten to reflect prior-halt empirical evidence

**Outcome:** FIDRAFT entry F-RETIRE-MIGRATE-TOOLS (`docs/FUTURE_IDEAS_DRAFT.md:244`) "Proposed shape" line is rewritten to reflect the prior-dispatch halt-and-surface evidence. Specifically: (a) `heavy-b-migrate` removed from the candidate list (it's a load-bearing continuous trigger per `plugins/dev-sdlc/tools/loam-mode/src/loam_mode/session_start.py:283-299`, NOT a one-time script); (b) `orphan-plist-cleanup` retirement clarified as a 4-file edit (delete + dev-mode-manifest update + partition-test allow-list update + workspace-sync test counterpart-list update + sibling-tool cross-reference cleanup) NOT a 1-file deletion; (c) the 3 `loam-migrate-*` per-host helpers' retirement clarified as a safety-horizon judgment call (no central "has been run" registry; per-host / per-operator helpers; owner-class call); (d) `pos-publish-framework-only` confirmed already-retired (the F-TF-1 fix in this PATCH closes the residual stale assertion). Entry STATUS unchanged (still `capture-only`) — the operator-class call (whether to retire Path B / Path C of the prior halt-and-surface) stays owner-gated. Entry text adds a chain pointer to `workspace/.scratch/claude-output/retire-one-time-migration-tools-halt-and-surface.md`.

**Verification:** smoke writeup §4 captures the diff summary (which lines added / removed / changed) + grep verification that `heavy-b-migrate` no longer appears in the F-RETIRE-MIGRATE-TOOLS entry's candidate list.

### AC.WSP.4 — outcome-altitude dogfood probe

**Outcome:** slug-named smoke writeup at `docs/experiments/workspace-sync-test-and-python-runtime-pin-hard-smoke.md` documents the cycle's outcome end-to-end: (a) the workspace-sync test suite passes 4/4 post-fix; (b) the empirical-recheck for F-PYTHON-3.9 captures the pip-refuse-on-3.9 verbatim; (c) the F-RETIRE-MIGRATE-TOOLS framing-correction diff is summarized; (d) the release-CLI 6-gate dry-run for v0.10.7 returns ALL 6 GATES GREEN against the live plan-doc + manifest + STATE/roadmap admin.

**Verification:** smoke writeup exists at the slug-named path; release-CLI dry-run output captured in §5.

### AC.WSP.S — seal-diff scope-fence

**Outcome:** the source-edit commit's diff touches only the files in the allow-list below. Verified via `git diff --name-only` against the source-edit commit.

**Allow-list:**

- `framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py` — the test fix.
- `docs/FUTURE_IDEAS_DRAFT.md` — F-TF-1 + F-PYTHON-3.9 + F-RETIRE-MIGRATE-TOOLS edits.
- `docs/STATE.md` — v0.10.7 row.
- `docs/release-roadmap.md` — v0.10.7 §3 entry + §2 active-version row.
- `docs/experiments/workspace-sync-test-and-python-runtime-pin-hard-smoke.md` — smoke writeup.
- `docs/plans/workspace-sync-test-and-python-runtime-pin.md` — this plan-doc.
- `docs/plans/workspace-sync-test-and-python-runtime-pin.manifest.yaml` — manifest.
- `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` — BASELINE pointer auto-bumped at seal-time per F-PLAN-DOC-TEMPLATE-AUTO-BUMP-FENCE pre-inclusion.
- `plugins/dev-sdlc/tests/SEAL_COMMIT` — sidecar auto-bumped at seal-time.
- `plugins/dev-sdlc/seals/SEAL_COMMIT.workspace-sync-test-and-python-runtime-pin` — narrative.

NO entries in any framework/* component source code; NO `__version__` updates; NO pyproject.toml version bumps; NO test additions or removals beyond the in-scope F-TF-1 stale-path drop.

**Verification:** smoke writeup §5 captures `git diff --name-only` against the source-edit commit.

---

## §5 — Method-decision register

### D-WSP.1 — Path A scope only (Path B/C deferred for owner safety-horizon ratification)

**Decision:** Ship F-TF-1 + F-PYTHON-3.9 RESOLVED-BY-INSPECTION + F-RETIRE-MIGRATE-TOOLS doc-only framing correction. Do NOT retire any of the 5 migration tools (Path B = retire 3 `loam-migrate-*` per-host helpers; Path C = additionally retire `orphan-plist-cleanup`).

**Rationale:** the prior-dispatch halt-and-surface artefact ruled the per-host helper retirement (Path B) is "have we passed the safety horizon for the M1b/M1c/M1f per-host upgrade helpers?" — that's an owner call. Path C (orphan-plist-cleanup retirement) is "is the pre-#6 archaeological-orphan remediation surface no longer needed for new operators?" — same shape, different historical horizon. Both are M5-class principle-conflict resolutions (owner-vs-cleanup tension, signal weights: blast radius MEDIUM-to-HIGH, reversibility LOW-to-MEDIUM, audience operator-facing) → halt-and-surface for owner ruling per `feedback_principle_conflict_resolution_multi_signal`. Dispatcher chose Path A scope explicitly.

### D-WSP.2 — F-PYTHON-3.9 RESOLVED-BY-INSPECTION (NOT a deletion + capture cycle)

**Decision:** F-PYTHON-3.9-TEST-FAILURES-PYPROJECT-PIN's status flips to RESOLVED-BY-INSPECTION (the F-RESOLVED-BY-COMPOSITION-VOCABULARY pattern, applied to "the proposed work was already done before the entry was captured" rather than "multiple cycles composed to close it"). Entry stays in the FIDRAFT file with the empirical-recheck evidence + chain pointer; not deleted.

**Rationale:** alternative shapes considered: (a) delete the entry entirely — rejected, loses the empirical-recheck audit trail + the lesson for future capture discipline; (b) flip to plain RESOLVED — rejected, "RESOLVED" implies this PATCH did the resolving work; the work was already done by the 2026-04-27 commit `0d599bb`. RESOLVED-BY-INSPECTION names the actual shape: empirical recheck found the proposed work already in place. Composes with `feedback_agent_empirical_recheck_before_halt` (this entry IS an instance of "F-AGENT-EMPIRICAL-RECHECK-BEFORE-HALT applied retroactively to a stale FIDRAFT capture") — capturing the pattern in the entry text itself extends the discipline.

### D-WSP.3 — F-RETIRE-MIGRATE-TOOLS framing correction is doc-only; status unchanged

**Decision:** rewrite the "Proposed shape" line of F-RETIRE-MIGRATE-TOOLS to reflect prior-halt empirical evidence (3 framing corrections + chain pointer). Do NOT flip the entry's status (`capture-only` stays).

**Rationale:** the operator-class call (whether to ship Path B / Path C) is owner-gated; the FIDRAFT entry is the decision-context the owner reads when ratifying. Correcting the framing improves the decision-context without making the decision. Composes with `feedback_locked_design_not_license_for_bad_outcomes` (the FIDRAFT framing was wrong; correcting it doesn't close the entry, it improves what's there).

### D-WSP.4 — pyproject.toml versions stay at 0.10.0

**Decision:** no per-component pyproject.toml version bumps in this PATCH.

**Rationale:** per AC.HONEST.1 / D-NFCLEAN.4 / D-SDPD / v0.8.3 / v0.10.1-v0.10.6 precedent — PATCHes ride the predecessor MINOR's per-component version. v0.10.7 stays at 0.10.0 across all 30 pyproject.toml files. No drift from the established convention.

### D-WSP.5 — dev-sdlc seal anchor; pre-include `test_no_sealed_amendments.py` in allow-list per F-PLAN-DOC-TEMPLATE-AUTO-BUMP-FENCE

**Decision:** seal anchor is dev-sdlc (matches v0.10.6 / v0.10.5 / v0.10.4 / v0.10.3 / v0.10.2 PATCH precedent). The AC.WSP.S allow-list pre-includes `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` because the dev-sdlc seal workflow auto-bumps the file's BASELINE pointer at seal-time.

**Rationale:** F-PLAN-DOC-TEMPLATE-AUTO-BUMP-FENCE captured the convention 2026-05-14 specifically to prevent the v0.10.3 fix-up rework where this file was omitted. This plan-doc honors the convention.

### D-WSP.6 — extra_allowed_prefixes admits `framework/workspace-sync/tests/`

**Decision:** the manifest's `extra_allowed_prefixes` for the dev-sdlc seal anchor includes `framework/workspace-sync/tests/` to admit the F-TF-1 test fix.

**Rationale:** the test fix is the only file in `framework/` touched by this PATCH; the dev-sdlc seal anchor's universal-admission list does not include `framework/`. Extending via `extra_allowed_prefixes` per the same pattern v0.10.6 used to admit `docs/papers/`. Single targeted prefix; not whole `framework/`.

---

## §6 — F-FIDRAFT-FLIP-ON-UNBLOCK-PATCH discipline check

Per F-FIDRAFT-FLIP-ON-UNBLOCK-PATCH: when a PATCH closes a FIDRAFT item AND that item's RESOLVED entry text mentions another FIDRAFT entry as "blocked-by-this-helper" / "depends-on-this-helper", the source-edit MUST flip every dependent entry's status in the same commit.

**Empirical recheck:**

- F-TF-1 entry text: "composes with F-RETIRE-MIGRATE-TOOLS." — F-RETIRE-MIGRATE-TOOLS stays `capture-only` (its operator-class call is unchanged); F-TF-1 RESOLUTION does not unblock F-RETIRE-MIGRATE-TOOLS by itself. F-RETIRE-MIGRATE-TOOLS receives a doc-only framing correction in this same source-edit (AC.WSP.3); both are co-edited in the same commit. Discipline satisfied.
- F-PYTHON-3.9-TEST-FAILURES-PYPROJECT-PIN entry text: "Composes with F-TF-* class (test-environment-fragility); v1.0 readiness (architecture-clarity surface)." — no F-TF-* entry mentions F-PYTHON-3.9 as a blocker / dep / unblocker. F-PYTHON-3.9 RESOLUTION does not unblock any other entry by structural composition; the empirical pin already exists.
- F-RETIRE-MIGRATE-TOOLS entry text post-amendment: "Composes with reviewer's Axis-2 verdict; AC.HONEST.6 F-TF-1 (the workspace-sync test-fixture stale-path fix); v1.0 ship gate." — F-TF-1 is co-edited in this same source-edit (RESOLVED); v1.0 ship gate is a downstream surface, not an entry. No discipline action needed.

Discipline GREEN on all three FIDRAFT edits.

---

## §7 — References

- Prior-dispatch halt-and-surface: `workspace/.scratch/claude-output/retire-one-time-migration-tools-halt-and-surface.md`.
- Predecessor cycle: v0.10.6 PATCH `paper-html-regeneration` (sealed `276e0d5`; published `42c0ee6`).
- FIDRAFT file: `docs/FUTURE_IDEAS_DRAFT.md` — F-TF-1 (line 252) + F-PYTHON-3.9 (line 296) + F-RETIRE-MIGRATE-TOOLS (line 244).
- Test under fix: `framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py` (lines 117-130 area).
- Original pin commit: `0d599bb` (2026-04-27, Luke Ivers — `framework/tools/pos-amend/pyproject.toml` with `requires-python = ">=3.11"`).
- Composes-with feedback memories: `feedback_agent_empirical_recheck_before_halt`, `feedback_loose_AC_text_fix_AC_not_implementation`, `feedback_locked_design_not_license_for_bad_outcomes`, `feedback_principle_conflict_resolution_multi_signal`, `feedback_no_amend_in_agent_dispatches`, `feedback_version_numbers_at_release_time`.
- Convention compliance: F-CYCLE-ARTEFACT-SLUG-NAMING (smoke writeup slug-named); F-PLAN-DOC-TEMPLATE-AUTO-BUMP-FENCE (allow-list pre-includes `test_no_sealed_amendments.py`); F-FIDRAFT-FLIP-ON-UNBLOCK-PATCH (§6 above).
