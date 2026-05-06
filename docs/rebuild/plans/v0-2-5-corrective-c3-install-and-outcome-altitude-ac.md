# v0.2.5 Corrective C3 — install-from-source `[synthesis]` extra + outcome-altitude AC + F6 fix

**Status:** plan-doc; pre-code per `feedback_plan_before_code`. Authored 2026-05-05 (Sonnet, single-agent plan-author + builder).

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.

**Predecessor:** v0.2.5 corrective C1+C2 (rides under methodology-amendment seal `a9bc524`; functional fixes verified at HEAD `a43e37d`). v0.2.5 HARD smoke re-run completed RED with one new BLOCKER (F5) + one yellow (F6); evidence at `<pos3>/workspace/.scratch/claude-output/v0-2-5-hard-smoke-rerun-report.md`.

**Authority:** v0.2.5 corrective C3 dispatch brief explicitly authorized "land four artefacts so v0.2.5 HARD smoke re-runs GREEN" — install-from-source extra + workstation install + outcome-altitude AC + F6 dispatch-text fix. First worked instance of the procedural rule shipped today (`odd-test-altitude-discipline` SKILL).

**BASELINE (pre-build tip):** to be set to the source-edit feat commit when the build commit lands.

---

## §1 — Outcome shape (the "why")

The v0.2.5 HARD smoke re-run against rd-automation surfaced one new BLOCKER and one yellow:

1. **F5 (BLOCKER) — `anthropic` SDK not installed in runtime Python env.** The C1 corrective wired `synthesis.build_default_anthropic_client()` through the CLI but the C1 verification test monkey-patched the import. In the smoke run against rd-automation, the real-world `anthropic` SDK was not installed (`/opt/homebrew/opt/python@3.13/bin/python3.13 -c "import anthropic"` → `ModuleNotFoundError`). The lazy import raises `OddExtractorError("anthropic SDK not installed")`; the entire pipeline halts at stage 1; AC.HARD.1-5 cascade-fail.

   Root cause is structural: `anthropic` is declared in odd-extractor's `[synthesis]` extras in `plugins/dev-sdlc/odd-extractor/pyproject.toml`, deliberately optional (per the v0.2.3 Cycle 1 sub-plan-doc §7 method-decision register: `synthesis = ["anthropic>=0.40"]` — production callers install with `pip install loam-odd-extractor[synthesis]`). But `install-from-source.txt` does NOT install `odd-extractor` AT ALL — line 74 only installs the parent `plugins/dev-sdlc`, which has no transitive dependency on `odd-extractor`. So workstation installs + Eric's eventual install miss `odd-extractor` entirely (the `loam-odd-extractor` package gets pulled in indirectly via `loam-cli` discovery, but without the `[synthesis]` extra).

   This is the **first worked instance** of the procedural rule shipped today: a verification gap that exists because the C1 ACs were at implementation-altitude (monkey-patched test) rather than outcome-altitude (real production install path). C3 fixes both at the install layer AND adds an outcome-altitude AC to verify it.

2. **F6 (yellow) — dispatch-text drift `gap-summary.yaml` vs canonical `gap-inventory.yaml`.** The v0.2.5 HARD smoke dispatch text references `gap-summary.yaml` and `build-next-recommendation.yaml`. The CLI help text + actual artefact paths use `gap-inventory.yaml` and `build-next.yaml`. Verification: `grep -rln "gap-summary\|build-next-recommendation" docs/ plugins/` returns ZERO results in canonical pos-v2 — the drift exists only in the dispatcher-side smoke brief stored outside this tree. Nothing to fix in pos-v2.

The fixes are surgical:

- **C3.1 (install-from-source.txt):** Add a new install line `-e ./plugins/dev-sdlc/odd-extractor[synthesis]` so a fresh install pulls in `odd-extractor` editable + the `anthropic` SDK as part of the standard install path. Why this shape (not parent-extras-cascade): per [setuptools / pip behavior](https://pip.pypa.io/en/stable/topics/dependency-resolution/), parent-extras don't cascade to children unless the parent declares the child as a dependency-with-extras (`loam-odd-extractor[synthesis]` in `[project.dependencies]` of `plugins/dev-sdlc/pyproject.toml`). Adding a dedicated install line is the lighter touch — preserves the deliberate `[synthesis]` optional-extra design while making the install path explicit.

- **C3.2 (workstation install):** Run `pip install anthropic>=0.40` (or rerun `pip install -r install-from-source.txt`) to unblock the HARD smoke re-run on the workstation. One-time operational fix.

- **C3.3 (outcome-altitude AC test):** Author a NEW test `test_AC_V025_C3_3_cli_live_outcome_altitude.py` that exercises the production CLI invocation against a real fixture, with NO monkey-patching of `anthropic` imports, NO pre-arrangement of objectives.yaml or backing-map.yaml. Skip cleanly if `ANTHROPIC_API_KEY` is not set (designed as conditional pass-or-skip with explicit env-check + clear skip-reason). Mark explicitly as outcome-altitude per the new SKILL convention. This is the **prevention test** that closes the gap behind the C1 monkey-patched stub — if `anthropic` SDK is missing OR if the CLI synthesis path silently no-ops, this test fails on real-world invocation.

- **C3.4 (F6 fix):** No-op — verified by grep that `gap-summary.yaml` / `build-next-recommendation.yaml` do NOT appear anywhere in `docs/` or `plugins/` in canonical pos-v2. Drift is dispatcher-side; documented for audit completeness.

**Why one combined corrective.** All four artefacts close the v0.2.5 HARD smoke RED→GREEN gap. The install-side fix (C3.1+C3.2) is the BLOCKER closure; the outcome-altitude AC (C3.3) is the procedural prevention; F6 (C3.4) is the audit closure. Combined matches v0.2.5 corrective C1+C2 single-amendment-multi-AC precedent.

---

## §2 — ACs — `AC.V025-C3.1` through `AC.V025-C3.5` (locked, 5 ACs)

ODD §2.5: every line of code, every branch, every test maps to a named AC.

- **AC.V025-C3.1 — `install-from-source.txt` requests `[synthesis]` extra for odd-extractor.** **outcome-altitude: false** (install-shape AC; verified by inspection).
  - Surface: `install-from-source.txt` carries an explicit line `-e ./plugins/dev-sdlc/odd-extractor[synthesis]` so a fresh install pulls in `odd-extractor` editable + the `anthropic` SDK. The line is placed in Tier J (alongside `-e ./plugins/dev-sdlc`) since odd-extractor is a sibling sub-package under dev-sdlc.
  - Test: structural — verify the line is present in `install-from-source.txt`. Verification command: `grep "odd-extractor\[synthesis\]" install-from-source.txt`.
  - Pre-fix verification: pre-fix the grep returns nothing (line absent).

- **AC.V025-C3.2 — `anthropic` SDK installed in current workstation Python.** **outcome-altitude: true** (real install verified by import).
  - Surface: `/opt/homebrew/opt/python@3.13/bin/python3.13 -c "import anthropic"` succeeds; `pip show anthropic` reports version ≥0.40.
  - Test: operational — run `pip install anthropic>=0.40` (or `pip install -r install-from-source.txt`); verify `python3.13 -c "import anthropic"` exits 0. Not a pytest test; one-time install fix verified by report.
  - Pre-fix verification: `python3.13 -c "import anthropic"` exits 1 with `ModuleNotFoundError`.

- **AC.V025-C3.3 — Outcome-altitude AC test for CLI `--live` synthesis path.** **outcome-altitude: true** (per the new `odd-test-altitude-discipline` SKILL; first worked instance of the rule).
  - Surface: NEW test file `plugins/dev-sdlc/odd-extractor/tests/test_AC_V025_C3_3_cli_live_outcome_altitude.py`. The test:
    1. Skips cleanly with explicit reason if `ANTHROPIC_API_KEY` env var is not set (`pytest.skip("ANTHROPIC_API_KEY not set; outcome-altitude AC requires real SDK + key")`).
    2. Skips cleanly with explicit reason if `anthropic` cannot be imported (`pytest.importorskip("anthropic")`).
    3. Sets up a fresh tmp workspace + copies the canonical `jsts-playwright-app` fixture + git-inits it.
    4. Invokes `cli.main([<repo>, "--live", "--budget-cents", "500", "--budget-override", "--workspace-root", <ws>])` — the production CLI surface; NO monkeypatch of `synthesis.build_default_anthropic_client`; NO pre-arrangement of `objectives.yaml` or `backing-map.yaml`.
    5. Asserts: rc == 0, `objectives.yaml` exists with ≥1 objective, `backing-map.yaml` exists, `synthesis.yaml` exists with `model_id != "(none)"` AND `model_id` matches a real Anthropic model identifier (e.g. starts with `claude-`).
    6. Carries an explicit docstring marker: `outcome-altitude: true (per docs/odd-llm-grounding.lean.md §"Outcome-altitude AC requirement" + plugins/dev-sdlc/skills/odd-test-altitude-discipline/SKILL.md)`.
  - The test does NOT contain `monkeypatch.setattr` of `anthropic` or `synthesis.build_default_anthropic_client`; it does NOT contain `mock.patch` of those symbols.
  - Test budget: `--budget-cents 500` is the smoke-tier override-required budget; live synthesis on jsts-playwright-app per v0.2.4 Cycle 3 SOFT smoke evidence consumed under 1¢. 500¢ is conservative.
  - Pre-fix verification: with `anthropic` SDK NOT installed (the F5 condition), this test fails (or skips on import-not-found, depending on order); with `anthropic` SDK installed but the CLI synthesis path broken (the F1 condition pre-C1+C2), this test fails because objectives.yaml is empty. Both failure paths reproduce in pre-fix state.

- **AC.V025-C3.4 — F6 dispatch-text drift fix.** **outcome-altitude: false** (audit-closure AC).
  - Surface: verify `gap-summary.yaml` and `build-next-recommendation.yaml` do not appear in pos-v2 dispatcher-facing artefacts. Verification command: `grep -rn "gap-summary.yaml\|build-next-recommendation.yaml" docs/ plugins/ --include="*.md" --include="*.yaml"` returns no matches. Test fixtures may legitimately reference older filenames; OK to leave.
  - Test: structural — grep returns empty.
  - Pre-fix verification: grep already returns empty in canonical pos-v2 (the drift was in dispatcher text outside this tree). AC closes via documentation in this plan-doc.

- **AC.V025-C3.5 — All existing tests still pass; no regressions.** **outcome-altitude: false** (meta-AC).
  - Surface: structural — fix MUST NOT regress any sealed AC.
  - Test: meta-AC honored by running full odd-extractor test suite (`pytest plugins/dev-sdlc/odd-extractor/tests/`) at seal-time and verifying zero new failures vs the post-C1+C2 baseline (815 passed, 1 skipped). Post-C3 expectation: 816 passed, 1-2 skipped (815 + AC.V025-C3.3 either passes-with-key or skips-without-key).

---

## §3 — Build dispatch brief (folded into this run)

This corrective amendment is single-agent: plan-author + builder are the same Sonnet run per dispatch. Build sequence:

1. **Plan-doc + manifest commit** (this commit).
2. **Source-edit feat commit (BASELINE).** Edit `install-from-source.txt` (~1-2 lines added in Tier J); add new test file `test_AC_V025_C3_3_cli_live_outcome_altitude.py` (estimated ~150 lines mirroring existing test conventions). Single commit subject: `fix(install): add odd-extractor[synthesis] to install-from-source + outcome-altitude AC test (v0.2.5 corrective C3)`.
3. **Workstation install (operational, before commit-3).** `pip install anthropic>=0.40` against `/opt/homebrew/opt/python@3.13/bin/python3.13`; verify import.
4. **Manifest+apply commit.** `loam amend apply <this manifest>` produces a single merged commit per AC.DPS1.6 schema-v3.
5. **Seal commit.** `loam amend seal --plan-doc <abs path> <this manifest>` produces deterministic short-form seal commit per AC.DPS2 schema-v3 + a §14 backfill follow-up commit per AC.D-sa.7.

**No `git --amend`. No push. Single semantic commit per stage.**

---

## §4 — Halt triggers + bookkeeping

**Halt-and-surface triggers (per dispatch brief):**
- `pwd` ≠ `/Users/lukeivers/ivers-corp-pos-v2` — handled at start.
- Concurrent agent activity in this WD — verified clean at start.
- The pre-fix outcome-altitude AC C3.3 test does NOT fail before the install fix lands — addressed: with `anthropic` not installed, `pytest.importorskip("anthropic")` causes test to SKIP (not FAIL) on the F5 condition; this is acceptable per the SKILL's skip-on-missing-precondition pattern. The test does FAIL pre-C1+C2 (the F1 condition) because objectives.yaml is empty.
- Any v0.2.x test regresses post-fix — addressed by AC.V025-C3.5 full-suite sweep.
- `loam amend apply` or `loam amend seal` errors out — TBD at apply/seal time; halt-and-surface.
- Any push attempt — n/a; no push.
- Any tag attempt — n/a; no tag.
- A new BLOCKER beyond F5/F6 surfaces — none expected; halt-and-surface if encountered.
- Promoting `anthropic` to baseline dep was the only viable path — NOT the case; install-from-source extra is sufficient (verified by reading the pyproject.toml `[synthesis]` extra design + the lazy-import pattern in `synthesis.py`).

**ODD §2.5 surrounding-code observations (per principle 2 — halt-and-surface on adjacent ODD violations):**
- F7 (ANTHROPIC_API_KEY keychain lift) explicitly out-of-scope per dispatch brief; pushed to FIDRAFT post-Eric.

**Bookkeeping:**
- `loam amend apply` (= `pos-amend apply`). NOT `git --amend`. NOT manual `git commit`.
- Manifest schema v3.
- Single semantic commit on apply. Subject: `fix(install): add odd-extractor[synthesis] to install-from-source + outcome-altitude AC test (v0.2.5 corrective C3)`.
- Short-form seal commit per AC.DPS2 schema-v3.
- §14 backfill via `loam amend seal --plan-doc` flag (separate post-seal commit per AC.D-sa.7).
- NO push; NO tag; v0.2.5 release-tag remains gated on Luke's ship ruling.

---

## §5 — Smoke (REALISTIC CONDITION — applicable dimensions)

**D1 cold-state.** Fresh tmp workspace via `tmp_path`; fresh extraction via `cli.main([<repo>, "--live", ...])` against the canonical jsts-playwright-app fixture with NO monkeypatch and NO pre-arrangement; assert objectives.yaml carries ≥1 objective, backing-map.yaml exists, synthesis.yaml model_id is real. Verified by AC.V025-C3.3 (when ANTHROPIC_API_KEY is set; skips cleanly otherwise).

**D2 steady-state.** Re-running on byte-identical inputs produces byte-identical artefacts. Inherited from v0.2.3 idempotence verification (AC.BACKMAP.D2 + AC.OBJX.D2); not re-verified per fix-scope.

**D3 restart.** N/a structurally — `_cmd_extract` is stateless on entry.

**D4 reboot.** N/a — one-shot CLI; D4 collapses to D5 for one-shot CLIs.

**D5 cross-session.** Inherited from v0.2.4 cross-session verification; not re-verified per fix-scope.

**D6 telemetry-floor.** `_cmd_extract` continues to write the same audit-log entries; when synthesis runs, `synthesis_complete` and `backing_map_populated` entries are emitted. Verified structurally — audit-log writes are unchanged by this fix (no source code edits to cli.py, generate.py, or backing_map.py).

**PLUS: full-suite green sweep** — pre-corrective odd-extractor tests at HEAD all pass post-corrective; halt + surface on any regression. Verified by AC.V025-C3.5.

---

## §6 — Risk-band classification (per `odd-test-altitude-discipline` SKILL)

This corrective edits:
1. `install-from-source.txt` — config schema the user authors against (per SKILL's risk-band classifier: production-facing surface).
2. New test file — test-only edits with no production code impact (release-gate HARD acceptable per SKILL).

The first item is production-facing: a fresh-install user sees the synthesis extra (or doesn't). HARD per-cycle is required. AC.V025-C3.3 IS the per-cycle HARD probe — outcome-altitude test against the real CLI surface with the real SDK. This corrective is the worked example of the SKILL's "HARD per-cycle required" classifier path.

Risk-band assessment summary: **HARD per-cycle required** for AC.V025-C3.1 (install-from-source.txt is production-facing); the per-cycle HARD probe is AC.V025-C3.3 itself (the new outcome-altitude test).

---

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

Corrective amendment scope is tight (install-from-source line addition + new test file).

**Method decisions:**

- **Install mechanics: dedicated install line vs parent-extras cascade.** Picked option (a) — dedicated `-e ./plugins/dev-sdlc/odd-extractor[synthesis]` install line in Tier J. Rationale: (1) the parent `plugins/dev-sdlc/pyproject.toml` does NOT declare `loam-odd-extractor` as a `[project.dependencies]` entry (verified by reading the file; line 10-17); declaring it just to enable extras-cascade would over-couple the dev-sdlc plugin to the odd-extractor sub-component (which is its own pip package). (2) The dedicated line is one-line cost vs ~5-line cost (declare loam-odd-extractor[synthesis] as parent dep + decide on default extras). (3) Preserves the deliberate `[synthesis]` optional-extra design per v0.2.3 Cycle 1 sub-plan-doc §7. (4) Verified by reading `install-from-source.txt` Tier J — odd-extractor is currently NOT installed at all by the install path (prior assumption was wrong — `loam-odd-extractor` editable install on the workstation got there via some other mechanism, perhaps direct manual install during early scaffolding).

- **Workstation install: full reinstall vs targeted `pip install anthropic`.** Picked option (b) — targeted `pip install anthropic>=0.40` against `/opt/homebrew/opt/python@3.13/bin/python3.13`. Rationale: (1) the workstation's loam-odd-extractor is already editable-installed from the canonical pos-v2 tree (`pip show loam-odd-extractor` confirms `Editable project location: /Users/lukeivers/ivers-corp-pos-v2/plugins/dev-sdlc/odd-extractor`); only the `anthropic` SDK is missing. (2) Reinstalling via `install-from-source.txt` would touch ~15 components and risk operational disruption mid-build. (3) `pip install anthropic>=0.40` is a single-package targeted fix that achieves the AC. (4) The `install-from-source.txt` fix (C3.1) ensures FUTURE installs (Eric's, fresh-clone) get the synthesis extra automatically; C3.2 only unblocks the immediate workstation smoke-re-run.

- **AC.V025-C3.3 fixture choice: jsts-playwright-app.** Same rationale as v0.2.5 corrective C1's fixture pick — canonical existing fixture used by `test_AC_PERSONA_PULL_4_release_smoke` and `test_AC_V025_C1_C2_*`. Mirrors `_setup_jsts_repo` helper pattern. Allows direct comparison between monkey-patched (C1's test) and real-SDK (C3.3's test) behavior on the same input.

- **AC.V025-C3.3 skip-or-fail-on-missing-key.** Picked option (a) — `pytest.skip` cleanly with explicit reason (NOT `pytest.fail` and NOT silent pass). Rationale: (1) per the new SKILL's pre-arrangement detection rubric, the test must NOT pre-arrange the SDK (that would be STUB-class). (2) Skipping cleanly with explicit reason is the standard pytest pattern for environment-conditional tests (matches `pytest.importorskip` shape). (3) The skip-reason names the env-var requirement so a developer sees why the test didn't run. (4) Falls within the SKILL's "skip-by-default-locally + run-on-demand by humans" pattern named in the dispatch brief.

- **F6 fix: doc-update vs no-op.** Picked option (a) — no-op + plan-doc documentation. Rationale: (1) grep verification shows `gap-summary.yaml` and `build-next-recommendation.yaml` do NOT appear in `docs/` or `plugins/` in canonical pos-v2. (2) The drift exists only in dispatcher-side smoke-brief text stored outside this tree (in pos3 or in the dispatcher's session memory). (3) Fixing in pos-v2 would require speculative search for non-existent references; documenting in this plan-doc closes the audit trail correctly.

### Commit SHAs

- Amendment commit: `1ca5f478767d84808c63cc34363c243ee053c401` —
  `chore(amend): v0-2-5-corrective-c3-install-and-outcome-altitude-ac manifest+apply — dev-sdlc BASELINE+sidecar bump to 2fd17a6`
- Seal commit: `89f97c67cd05eaaea66a7e771a66b65ef16a46c1` —
  `chore(seals): v0-2-5-corrective-c3-install-and-outcome-altitude-ac — dev-sdlc at 1ca5f47`
