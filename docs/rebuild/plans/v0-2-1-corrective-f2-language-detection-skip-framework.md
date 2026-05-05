# v0.2.1 Corrective F2 — language detection skips `framework/` subdirectory

**Status:** plan-doc; pre-code per `feedback_plan_before_code`. Authored 2026-05-04 (Sonnet, single-agent plan-author + builder).

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.

**Predecessor:** v0.2.1 corrective F1 SEALED — apply `0904064`, seal `ad42314`, §14 backfill `5fea94c`. F2 is the second of three independently HARD-BLOCKING findings from v0.2.1 Cycle 3 HARD smoke (RED). F1 + F2 + F5 land via separate dispatches.

**Authority:** v0.2.1 master plan §3 Cycle 3 + Decision R explicitly authorize "halt + corrective amendment" on RED smoke. Smoke evidence at `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-2-1-live-oss-smoke-2026-05-04.md` §6 (search "F2").

**BASELINE (pre-build tip):** to be set to the source-edit feat commit when the build commit lands.

---

## §1 — Outcome shape (the "why")

The smoke evidence proved that `loam onboard` running from inside a loam-bootstrapped workspace mis-detects the project language. The documented happy path — `loam init <workspace>` then `cd <workspace> && loam onboard` — leaves a cloned canonical at `<workspace>/framework/`, which contains canonical pos-v2's archived Ruby Gemfile fixtures. The detection walker (`framework/workspace-bootstrap/src/loam/workspace_bootstrap/language_detection.py`) walks `workspace_root` depth-bounded without skipping `framework/`, finds those Ruby signals, and reports polyglot — even when the user's app code is JS/TS-only.

**Eric's first-run experience (the smoke probe):** Q1 = "I detected **both Ruby and JS/TS**. Which is primary?" — wrong; his app is JS/TS-only. The Ruby came from `framework/`. This is the **first question** in the install ritual, the highest-leverage moment for "feels intentional," and it's wrong on the documented happy path.

The fix is detection-side, single-source-of-truth: the walker treats `framework/` (and a small set of similar harness-internal directories) as opaque to detection. Add `framework` to the existing skip-set the walker already maintains for `node_modules/`, `vendor/`, `.git/`, etc. **Tight scope: skip framework/ at the depth-bound walk boundary; nothing else changes.**

**Why detection-side:** `framework/` is loam's own scaffolding inside a bootstrapped workspace, not the user's app. Language detection's purpose (per AC.ONBOARD.2) is to identify the **user's** primary language — not loam's framework internals. The skip is consistent with the existing skip-list intent (skip noise dirs that don't represent user code).

**Why this passed v0.2.1 Cycle 1 release-level tests:** the Cycle 1 fixtures (`synthetic-rails`, `synthetic-jsts`, `synthetic-mixed`, `synthetic-unknown`) don't contain a `framework/` subdir. Cycle 3 HARD smoke was the first end-to-end exercise of the documented `loam init` → `cd workspace && loam onboard` happy path, which is exactly what surfaced the gap.

**Cycle 3 smoke promise on this fix:** rerunning Probe 1 (onboarding on a fresh-init'd workspace, app code JS/TS-only at root) post-fix produces Q1 = "I detected this is **ts**" (or `js` if no tsconfig), NOT "Ruby and JS/TS — which is primary?".

---

## §2 — ACs — `AC.LD.SKIP-FRAMEWORK.*` (locked, 4 ACs)

ODD §2.5: every line of code, every branch, every test maps to a named AC.

- **AC.LD.SKIP-FRAMEWORK.1 — Walker skips `framework/` subdirectory at depth-1.**
  - Surface: `framework/workspace-bootstrap/src/loam/workspace_bootstrap/language_detection.py` `_walk()` extends the existing skip-set (which already contains `.git`, `node_modules`, `vendor`, `.venv`, `venv`, `__pycache__`, `dist`, `build`, `.next`, `.turbo`) to include `framework`. The skip applies at every depth-bound where the walker descends; `framework/` at any nested level is treated as opaque.
  - Test: `test_AC_LD_SKIP_FRAMEWORK_1_framework_dir_skipped.py` — construct tmp workspace with `framework/Gemfile`; assert `detect_language(tmp)` returns `primary == "unknown"` (no signals leak from framework/).

- **AC.LD.SKIP-FRAMEWORK.2 — Bootstrapped JS/TS workspace detects as `ts` (NOT `mixed`).**
  - Surface: same; happy-path scenario validated end-to-end against a fixture mirroring post-`loam init` shape.
  - Test: `test_AC_LD_SKIP_FRAMEWORK_2_bootstrapped_jsts_primary_ts.py` — uses synthetic fixture `synthetic-bootstrapped-jsts/` (root-level `package.json` + `tsconfig.json` + `framework/Gemfile` + `framework/Gemfile.lock` mimicking what `loam init` clones). Assert `primary == "ts"`. Assert `signals` includes `package.json` + `tsconfig.json` AND does NOT include `Gemfile` (framework/ skipped).

- **AC.LD.SKIP-FRAMEWORK.3 — Bootstrapped Rails workspace detects as `rails` (NOT polyglot).**
  - Surface: inverse case; root-level Gemfile + `framework/` containing JS signals. Root-level signals win; framework/ skipped.
  - Test: `test_AC_LD_SKIP_FRAMEWORK_3_bootstrapped_rails_primary_rails.py` — uses synthetic fixture `synthetic-bootstrapped-rails/` (root-level `Gemfile` + `config/application.rb` + `framework/package.json` + `framework/tsconfig.json`). Assert `primary == "rails"`. Assert `signals` does NOT include `package.json` or `tsconfig.json`.

- **AC.LD.SKIP-FRAMEWORK.4 — Pre-existing AC.ONBOARD.2 tests remain green post-fix.**
  - Surface: structural — the fix is purely additive to the skip-set; existing fixtures (`synthetic-rails`, `synthetic-jsts`, `synthetic-mixed`, `synthetic-unknown`) do not contain `framework/`, so behavior is unchanged.
  - Test: meta-AC honored by running full `framework/workspace-bootstrap/tests/` suite at seal-time and verifying zero regressions.

---

## §3 — Build dispatch brief (folded into this run)

This corrective amendment is single-agent: plan-author + builder are the same Sonnet run per dispatch. Build sequence:

1. **Source-edit feat commit (BASELINE).** Edit `language_detection.py` `_walk()` to add `framework` to the skip-set. Add 2 new test fixtures (`synthetic-bootstrapped-jsts/`, `synthetic-bootstrapped-rails/`) under `framework/workspace-bootstrap/tests/fixtures/fresh-user-onboarding/`. Add 3 named-AC test files under `framework/workspace-bootstrap/tests/`. Run touched-component tests. Single commit subject: `fix(workspace-bootstrap): language detection skips framework/ subdir (v0.2.1 corrective F2)`.
2. **Manifest baseline-pin commit.** Update manifest's `baseline:` to the source-edit feat SHA; commit-only docs change.
3. **Manifest+apply commit.** `loam amend apply <this manifest>` produces a single merged commit per AC.DPS1.6 schema-v3.
4. **Seal commit.** `loam amend seal --plan-doc <abs path> <this manifest>` produces a deterministic short-form seal commit per AC.DPS2 schema-v3 + a §14 backfill follow-up commit per AC.D-sa.7.

**No `git --amend`. No push. Single semantic commit per stage.**

---

## §4 — Halt triggers + bookkeeping

**Halt-and-surface triggers:**
- WD drifts from `/Users/lukeivers/ivers-corp-pos-v2/`.
- Producer fix exceeds single-file source edit (`language_detection.py`) by more than 2 source files. Signal: blast radius bigger than estimated.
- Existing AC.ONBOARD.2 tests fail post-fix → halt + investigate; the skip should be additive.
- Synthetic fixture's framework/ contents don't materially exercise the detection path (e.g., no Ruby Gemfile in framework/) → halt + surface; fix the fixture.
- Cycle wall-clock > 75 min with no progress → halt.
- ODD §2.5 violations in surrounding code → halt + surface.
- Config-layer scope creep (`skip_dirs` parameter argued for) — defer per dispatch's explicit "default to the simpler shape (no config; hard-coded skip set)." Surface only if the AC family fundamentally requires it.
- > 3 escalations needed → halt.

**Bookkeeping:**
- `loam amend apply` (= `pos-amend apply`). NOT `git --amend`. NOT manual `git commit`.
- Manifest schema v3.
- Single semantic commit on apply. Subject: `fix(workspace-bootstrap): language detection skips framework/ subdir (v0.2.1 corrective F2)`.
- Short-form seal commit per AC.DPS2 schema-v3.
- §14 backfill via `loam amend seal --plan-doc` flag (separate post-seal commit per AC.D-sa.7).
- NO push.

---

## §5 — Method-decision register stub (filled at §14 backfill)

Locked decisions:
- **D-F2.1 (config layer):** Hard-coded skip set. The dispatch named the simpler shape as default; no AC requires runtime config; YAGNI. If a future user needs to detect language inside `framework/` (e.g., contributor working on the harness itself), they can pass the framework-internal path directly to `detect_language()` and the function will descend into it (it's only the depth-1 skip that's blocked when walking from a parent).
  - Wait — re-reading the existing `_walk()`: the skip-set is checked at every directory descent, not depth-1 only. So `detect_language(framework/workspace-bootstrap/)` would still skip nested `framework/` (none expected at that path). Acceptable; no AC requires the inverse capability.
- **D-F2.2 (skip-set membership):** `framework` is the only addition. Don't pre-emptively add hypothetical names (`canonical/`, `bootstrap/`); YAGNI per F4. If a future bootstrapper introduces a different harness directory, that's a separate corrective.
- **D-F2.3 (fixture content):** `framework/Gemfile` + `framework/Gemfile.lock` (for the JS/TS bootstrapped case) is sufficient — minimal Ruby-signal mass to verify the skip works. Real `loam init` clones much more, but the test only needs to prove the skip behavior; it doesn't need to mirror full canonical content.

---

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

Corrective amendment scope is tight (single-line edit to `_walk()` skip-set). Method decisions at §1 (detection-side single-source-of-truth fix) + §2 (4 ACs locked under `AC.LD.SKIP-FRAMEWORK.*`) + §4 (halt triggers + bookkeeping) + §5 (D-F2.{1,2,3}). Predecessor master plan: `docs/rebuild/plans/v0-2-1-master-plan.md` §3 Cycle 3 + Decision R. Sibling corrective: `docs/rebuild/plans/v0-2-1-corrective-f1-odd-extractor-contract-draft-fields.md` (sealed at `ad42314`).

### Commit SHAs

- Plan-doc commit: `92b970c` — `docs(plans): v0-2-1-corrective-f2-language-detection-skip-framework plan-doc + manifest`
- Source-edit feat commit (BASELINE): `0efd160` — `fix(workspace-bootstrap): language detection skips framework/ subdir (v0.2.1 corrective F2)`
- Manifest baseline-pin commit: `5954870` — `docs(plans): pin v0-2-1-corrective-f2 manifest baseline to 0efd160`
- Amendment apply commit: `70987e5` — `chore(amend): v0-2-1-corrective-f2-language-detection-skip-framework manifest+apply — workspace-bootstrap BASELINE+sidecar bump to 0efd160`
- Seal commit: `d82a43b` — `chore(seals): v0-2-1-corrective-f2-language-detection-skip-framework — workspace-bootstrap at 70987e5`
- Auto-backfill commit (loam amend seal --plan-doc): `2520adc` — `docs(plans): record v0-2-1-corrective-f2-language-detection-skip-framework commit SHAs in method-decision register`
- Manual §14 full-ladder backfill commit: this commit (post-seal follow-up matching F1 corrective's pattern per dispatch direction)
