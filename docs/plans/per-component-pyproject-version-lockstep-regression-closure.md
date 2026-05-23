# Per-component pyproject version lockstep — regression closure

**Slug:** `per-component-pyproject-version-lockstep-regression-closure`.
**Date authored:** 2026-05-23.
**Status:** PLAN-ONLY. Plan-before-code per `feedback_plan_before_code`. Owner ratification PENDING on §16 halt-and-surface findings (the four-pyproject `0.0.0` ruling + the "current shipped MINOR" version-anchor ruling).
**Class proposal:** **PATCH** per `docs/release-versioning-policy.md` — defect closure within the AC.HONEST.1 outcome shape (per-component-version discipline established at v0.8.0). No new outcome capability; closes a regression where the v0.8.0 discipline silently stopped firing at v0.11.0 and v0.12.0 minors. The regression-closing test IS the structural enforcement (test exists → CI fails on drift → discipline can't silently break again); the version bumps are mechanical defect closures bringing 26 in-scope component pyprojects back into lockstep with the current shipped MINOR.
**Predecessor work (canonical):**
- **v0.8.0 (sealed `e44b09d`, published `22f4178`)** — established AC.HONEST.1 per-component-version discipline. The outcome shape this plan defects against.
- **v0.8.1 (sealed `9411061`)** — F-PCV-1 FIDRAFT (per-component pyproject patch-number bumps) + D-NFCLEAN.4 explicit ruling: "per-component-version discipline advances with MINORs; PATCHes ride predecessor MINOR." This plan honors that ruling.
- **v0.8.2 (sealed `a54295f`)** — D-SDPD precedent: "pyproject.toml versions stay at 0.8.0 per D-SDPD precedent (per-component-version discipline advances with MINORs; PATCHes ride predecessor MINOR — matches v0.8.1 D-NFCLEAN.4 ruling)." Reconfirms the rule.
- **v0.9.0 (sealed `4a4535f`, source-edit `c1f7089`)** — first post-v0.8.0 MINOR to honor the discipline: "30 pyproject bumps + 4 `__version__` bumps" from 0.8.0 → 0.9.0.
- **v0.10.0 (commit `3354f73`)** — second post-v0.8.0 MINOR to honor: per-component v0.10.0 bump.
- **v0.11.0 (no commit found that bumps pyprojects)** — discipline silently broke.
- **v0.12.0 (sealed under amendment-N numbering scheme; per `d705094` SHIPPED PUBLIC backfill)** — discipline also did not fire.
- **2026-05-23 consistency review** at `/Users/lukeivers/pos3/workspace/.scratch/claude-output/loam-fresh-install-consistency-review-2026-05-23.md` §7 item 5 — surfaced the regression as MINOR severity; recommended a sweep + regression test.
**Working directory:** `/Users/lukeivers/loam/`.

---

## §1 — Outcome shape (the "why")

The v0.8.0 AC.HONEST.1 promise — "component pyproject.toml versions advance with each shipped minor" — broke silently between v0.10.0 (last honored) and v0.11.0 (first skipped). Two MINORs (v0.11.0 + v0.12.0) shipped without per-component pyproject bumps. As of 2026-05-23, every in-scope component pyproject reads `version = "0.10.0"` while the current shipped MINOR is **v0.12.0** (the v0.12.1-21 patches ride v0.12.0 per D-NFCLEAN.4 + D-SDPD precedents — patches do NOT bump per-component versions).

This is a defect within an established outcome shape, not a new outcome capability — PATCH-class.

The defect has two parts:

1. **Stale version numbers** — 26 in-scope component pyprojects at `0.10.0` should be at `0.12.0`. The visible drift: a fresh-install user inspecting a component's `pyproject.toml` reads a version that contradicts both the repo-tag and the AC.HONEST.1 promise. Honesty axis regression.
2. **Discipline-without-structural-enforcement** — AC.HONEST.1's verification was a `grep` invocation in a sealed plan-doc; there was no recurring CI test asserting that pyproject versions match the current MINOR. The v0.11.0 + v0.12.0 builders had no structural reminder; the discipline relied on builder-memory, which is a known-fragile substrate (this defect proves it). The fix-the-AC-not-the-implementation rule (`feedback_loose_AC_text_fix_AC_not_implementation`) does NOT apply here because the AC text was structurally adequate — the implementation lacked the enforcement surface. The right fix is structural: a test that fails CI when pyproject versions drift from the current shipped MINOR.

The patch closes both parts:

- Sweep the 26 stale component pyprojects to `0.12.0`.
- Author a regression test that reads every in-scope pyproject's `version` field, compares against a canonical "current shipped MINOR" source-of-truth, and fails with a clear corrective message on drift.
- Tier-0 mutation-detection: the test fixture deliberately mutates one pyproject's version and asserts the regression test fires — outcome-altitude proof the test isn't a no-op.

After this patch lands, the AC.HONEST.1 discipline is enforced structurally rather than relying on builder-memory; the next MINOR (v0.13.0) cannot silently skip the pyproject bump without making the test RED.

---

## §2 — Prime-objective ladder

```
VALUE_PROPOSITION.md prime objective
  └─ "primary persona is a translation layer between the user's
      natural-language intent and AI-effective execution"
       └─ documented features work as advertised (v1.0 quality-bar
          criterion #1) → documented-state matches actual-state across
          the user-facing surface (the v0.8.0 AC.HONEST outcome extension)
           └─ per-component-version discipline tracked + structurally enforced
              (no longer relies on builder-memory; defect from v0.11/v0.12
              silent-skip closed structurally)
               ├─ AC.PCVR.1 (sweep — 26 in-scope component pyprojects at
               │   current shipped MINOR `0.12.0`)
               ├─ AC.PCVR.2 (anchor — canonical machine-readable
               │   "current shipped MINOR" source-of-truth exists; named;
               │   readable by the regression test)
               ├─ AC.PCVR.3 (regression test exists — reads every in-scope
               │   pyproject's version, compares to anchor, fails with
               │   clear corrective message on drift)
               ├─ AC.PCVR.4 (outcome-altitude — deliberately-mutated
               │   pyproject version makes the regression test RED; reverting
               │   the mutation makes it GREEN; mutation-detection proven)
               └─ AC.PCVR.S (seal-diff discipline)
```

**VALUE_PROPOSITION tests:**

- **Primary-persona test (translation burden):** today a user inspecting `framework/tools/loam/pyproject.toml` reads `version = "0.10.0"` and must reconcile against the repo-tag at `v0.12.21` + the README + the architecture doc before knowing what version they actually have. After: the pyproject reads `0.12.0` (matching current MINOR per the discipline) and the regression test prevents future drift. Translation burden moves from "user reconciles documented-vs-actual" to "documented IS actual, mechanically enforced." **PASSES.**
- **Harness test (toolkit expansion):** the regression test is a primary-persona-toolkit addition — the persona can now treat "pyproject version lockstep with current MINOR" as a structurally-enforced invariant rather than a builder-memory discipline. **PASSES** (toolkit gain on the meta-axis: discipline enforcement moves from builder-memory to CI).

---

## §3 — Component fence

**Multi-component PATCH.** Fence shape mirrors v0.8.0 precedent (single fence-anchor component + universal-path admissions). The pyproject sweep by definition touches every component; the regression test lives in one component's test tree; the source-of-truth anchor file lives in `docs/`.

**Fence-anchor:** `dev-sdlc` plugin (same fence-anchor as v0.8.0/v0.8.1/v0.8.2/v0.9.0 honesty-cycles — established precedent for multi-component pyproject sweeps).

**PRIMARY (mechanical version bump — AC.PCVR.1):** every in-scope component pyproject's `version` field set to `"0.12.0"`. Enumerated from Tier-0 `find . -name pyproject.toml -not -path '*/.venv/*' -not -path '*/docs/archive/*'` against canonical at 2026-05-23 — **30 files total; 26 in-scope for the sweep; 4 halt-and-surface for explicit owner ruling (see §16 finding #1)**.

26 in-scope files (currently `0.10.0` → bump to `0.12.0`):

- `framework/cost-governance/pyproject.toml`
- `framework/dormancy/pyproject.toml`
- `framework/loam-init/pyproject.toml`
- `framework/objective-tracker/pyproject.toml`
- `framework/observability-aggregator/pyproject.toml`
- `framework/orchestrator/pyproject.toml`
- `framework/per-project-pm/pyproject.toml`
- `framework/primary-persona/pyproject.toml`
- `framework/reversibility-primitive/pyproject.toml`
- `framework/safety-layer/pyproject.toml`
- `framework/scope-of-work/pyproject.toml`
- `framework/self-correction/pyproject.toml`
- `framework/self-upgrade/pyproject.toml`
- `framework/telegram-interface/pyproject.toml`
- `framework/tools/heavy-b-migrate/pyproject.toml`
- `framework/tools/loam-memory-inspect/pyproject.toml`
- `framework/tools/loam/pyproject.toml`
- `framework/tools/subloam-driver/pyproject.toml`
- `framework/tools/upgrade-merge-resolver/pyproject.toml`
- `framework/workspace-bootstrap/pyproject.toml`
- `framework/workspace-sync/pyproject.toml`
- `plugins/dev-sdlc/odd-extractor/pyproject.toml`
- `plugins/dev-sdlc/pr-safety/pyproject.toml`
- `plugins/dev-sdlc/pyproject.toml`
- `plugins/dev-sdlc/tools/loam-amend/pyproject.toml`
- `plugins/dev-sdlc/tools/loam-mode/pyproject.toml`
- `plugins/loam-skills/pyproject.toml`

4 explicit-halt-and-surface files (currently `0.0.0` — see §16 finding #1 for context; ruling required before build):

- `framework/tools/handsoff-loop/pyproject.toml` (description: "the real orchestrated hands-off loop, packaged as a primary-persona-invocable capability ... NO Anthropic API key — real claude binary, default Sonnet. Stdlib-only.")
- `framework/tools/loam-spawn-isolation/pyproject.toml` (description: "The ONE shared, importable, mandated telegram-plugin-isolation surface for EVERY loam-adjacent `claude` spawn ...")
- `framework/tools/programbench-revival/pyproject.toml` (description: "ProgramBench-revival v2 — the measurement harness ...")
- `framework/tools/programbench-revival/realpb/pyproject.toml` (description: "ProgramBench-revival (REAL public ProgramBench) — the real-benchmark measurement harness ...")

**PRIMARY (anchor — AC.PCVR.2):** new file `docs/ACTIVE_MINOR` containing a single line (the current shipped MINOR version string, e.g., `0.12.0`). The file is the machine-readable source-of-truth that the regression test consumes. Format: one line, version string only (no `v` prefix, no whitespace beyond a trailing newline). Lives at canonical `docs/` per the existing canonical-state pattern (alongside `STATE.md`, `release-roadmap.md`, `release-versioning-policy.md`).

**PRIMARY (regression test — AC.PCVR.3 + AC.PCVR.4):** new test at `plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py` (fence-anchor is `dev-sdlc` so the test lives in `dev-sdlc`'s tests-tree). The test:

- Reads `docs/ACTIVE_MINOR` (single-line current MINOR).
- Enumerates every in-scope pyproject (the 26-file set documented at AC.PCVR.1 + an explicit allow-list mechanism that admits the 4 `0.0.0` files OR demands they conform — ruling per §16 finding #1).
- Asserts each in-scope pyproject's `version` field equals the anchor's MINOR.
- On failure: emits a corrective message naming the drifted files + the expected version + the corrective command shape.
- Includes a mutation-detection test that deliberately writes a temporary stale value to a fixture pyproject + asserts the assertion-helper fires RED + reverts + asserts GREEN (the AC.PCVR.4 outcome-altitude proof; the mutation is against a fixture file, NOT a real component pyproject).

**Universal-admission docs:**

- `docs/plans/per-component-pyproject-version-lockstep-regression-closure.md` (this file).
- `docs/plans/per-component-pyproject-version-lockstep-regression-closure.manifest.yaml`.
- `docs/STATE.md` — patch-version row added at end-of-build (PATCH-class entry; pyproject versions stay at MINOR per the discipline this plan reaffirms).
- `docs/release-roadmap.md` §2 — patch-version row added at end-of-build.
- `docs/experiments/per-component-pyproject-version-lockstep-regression-closure-hard-smoke.md` — HARD smoke writeup for the patch publish gate (covers AC.PCVR.4 mutation-detection outcome-altitude probe).
- `docs/FUTURE_IDEAS_DRAFT.md` — capture entries for any out-of-scope follow-ons surfaced during build (e.g., the 4 `0.0.0` files' lifecycle decision if owner rules they stay 0.0.0; the `__version__` string drift survey if any module-top `__version__` strings drift from pyproject; the existing F-PCV-1 entry from v0.8.1 may be retired or repurposed as "closed by this PATCH").

**Untouched:**

- All Python source code outside the new test file. The pyproject sweep is metadata-only; no `__version__` string bumps are in this PATCH (PATCHes ride predecessor MINOR per D-NFCLEAN.4 + D-SDPD; the `__version__` string discipline is itself a MINOR-class advance and a v0.13.0 concern).
- `framework/hands-off-lifecycle/` (no `pyproject.toml` at the component root; covered by other-tree composition — out of fence).
- `docs/archive/synthesis-tool-2026-05-04/pyproject.toml` (archived; out of fence).
- Module-top `__version__` strings (out of scope; see HARD HALT #5 + FIDRAFT carry-forward).

---

## §4 — Acceptance criteria (the AC ladder)

Four ACs plus seal-diff. AC IDs use scope-descriptive `PCVR` family ("Per-Component-Version-Regression") per `feedback_scope_descriptive_ac_ids`.

### AC.PCVR.1 — Sweep: 26 in-scope component pyprojects at current shipped MINOR `0.12.0`

**What:** Every in-scope component pyproject's `version` field carries the current shipped MINOR (`0.12.0` at build-time). The 26-file set is named in §3 PRIMARY. The 4 `0.0.0` files (handsoff-loop, loam-spawn-isolation, programbench-revival, programbench-revival/realpb) are EXCLUDED per §16 finding #1 ruling (in-scope-allowlist OR exclusion-allowlist per ruling).

**Acceptance:**
- `grep -E '^version = "' framework/*/pyproject.toml framework/tools/*/pyproject.toml plugins/**/pyproject.toml | sort -u` shows `version = "0.12.0"` for every in-scope component pyproject (modulo the 4 `0.0.0` files per the §16 ruling).
- No source code changes ride along the version bump (metadata-only).
- The bump is mechanical; the per-file edits are uniform (`version = "0.10.0"` → `version = "0.12.0"`).

`outcome-altitude: false` — implementation-altitude AC (mechanical version-bump verified via grep against the file surface).

### AC.PCVR.2 — Anchor: canonical machine-readable "current shipped MINOR" source-of-truth

**What:** A new file at `docs/ACTIVE_MINOR` contains a single line — the current shipped MINOR version string (`0.12.0` at build-time). The file is the machine-readable source-of-truth the regression test consumes.

**Acceptance:**
- `docs/ACTIVE_MINOR` exists.
- File content is a single line: the current shipped MINOR (no `v` prefix; trailing newline allowed).
- File parses cleanly via `Path("docs/ACTIVE_MINOR").read_text().strip()` returning a SemVer-shaped string matching `^\d+\.\d+\.0$` (MINOR boundary always ends in `.0` per `docs/release-versioning-policy.md`).
- A one-paragraph header comment in `docs/release-versioning-policy.md` (or a similarly-canonical doc — builder's call) explains the anchor's role: "`docs/ACTIVE_MINOR` is the single line containing the current shipped MINOR. Component pyproject versions track this anchor per AC.HONEST.1 + AC.PCVR.{1,3} discipline. The anchor advances at every MINOR's source-edit batch; PATCHes never touch it."

`outcome-altitude: false` — implementation-altitude AC (file-presence + content-shape verified via direct read).

### AC.PCVR.3 — Regression test: pyproject versions match the anchor

**What:** New test at `plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py` reads `docs/ACTIVE_MINOR`, enumerates every in-scope pyproject, asserts each `version` field equals the anchor's MINOR, fails with a clear corrective message on drift.

**Acceptance:**
- Test exists at the named path.
- Test reads `docs/ACTIVE_MINOR` via canonical-path resolution (the test's `Path` resolution walks up from `__file__` to find the repo root, OR consumes a known fixture path — builder's call).
- Test enumerates in-scope pyprojects via the same allowlist mechanism the AC.PCVR.1 sweep used (so the in-scope set is a single source-of-truth shared between AC.PCVR.1's sweep and AC.PCVR.3's assertion — the test does NOT silently allow a new pyproject to slip the discipline).
- Test asserts each in-scope pyproject's `version` field equals the anchor's value.
- Test fails on drift with a corrective message of the shape: `Pyproject version drift: <file> is at <stale-version>; expected <anchor-version> per docs/ACTIVE_MINOR. Run: <corrective-command-or-hint>.`
- Test passes against the post-AC.PCVR.1-sweep canonical state.

`outcome-altitude: false` — function-altitude AC (test exists + asserts the shape; the OUTCOME-altitude proof lives at AC.PCVR.4).

### AC.PCVR.4 — Outcome-altitude: mutation-detection proves the regression test isn't a no-op

**What:** A separate test (in the same test file) deliberately writes a stale value to a FIXTURE pyproject (not a real component pyproject), invokes the assertion helper from AC.PCVR.3, asserts the helper raises with the expected corrective-message shape, reverts the fixture, asserts the helper passes. Proves the regression test detects mutation; without this, AC.PCVR.3 could pass vacuously (assertion-helper structured wrong, in-scope enumeration empty, etc.).

**Acceptance:**
- Test exists at `plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py::test_AC_PCVR_4_mutation_detection`.
- Test creates a temporary directory (per `tmp_path` fixture) with a minimal fixture pyproject carrying `version = "0.10.0"`.
- Test invokes the assertion helper (or a parameterizable version of it that accepts a base path) against the fixture + `docs/ACTIVE_MINOR`-equivalent value `0.12.0`.
- Test asserts the helper raises with the corrective-message shape (`"Pyproject version drift"` in the exception body).
- Test then writes `version = "0.12.0"` to the same fixture pyproject + asserts the helper now passes.
- The mutation is against a fixture file in a tmp dir — never against a real component pyproject (the mutation must not be visible to other tests or commits).
- HARD HALT triggers if the assertion helper isn't factored to accept a fixture base (i.e., AC.PCVR.3's helper is implemented as a closed function bound to real paths) — the helper must be refactor-friendly enough to admit a fixture-base invocation. If the refactor is non-trivial, surface to dispatcher per HARD HALT #3.

`outcome-altitude: true` per `feedback_test_outcome_altitude_required` — invokes the regression-test assertion helper against a deliberately-drifted fixture; the mutation IS the outcome-altitude proof. Risk band: **production-facing CI surface** — the regression test is the structural enforcement that closes the v0.11/v0.12 silent-skip defect; HARD per-cycle REQUIRED.

### AC.PCVR.S — Seal-diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` shows changes only under:

- 26 in-scope component pyproject.toml files (AC.PCVR.1) — 4 `0.0.0` files possibly included or excluded per §16 finding #1 ruling.
- `docs/ACTIVE_MINOR` (AC.PCVR.2 — new file).
- `docs/release-versioning-policy.md` (AC.PCVR.2 — one-paragraph anchor explanation) OR another canonical doc per builder's call.
- `plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py` (AC.PCVR.3 + AC.PCVR.4 — new test file).
- `docs/STATE.md` (PATCH SHIPPED LOCAL row).
- `docs/release-roadmap.md` (PATCH §2 row).
- `docs/experiments/per-component-pyproject-version-lockstep-regression-closure-hard-smoke.md` (AC.PCVR.4 outcome-altitude probe writeup).
- `docs/FUTURE_IDEAS_DRAFT.md` (capture entries; carry-forward of F-PCV-1 closure + any §16 follow-ons).
- `docs/plans/per-component-pyproject-version-lockstep-regression-closure.md` (this file — universal-admission).
- `docs/plans/per-component-pyproject-version-lockstep-regression-closure.manifest.yaml` (universal-admission).
- Component sidecars + narrative file (managed by `loam amend apply` / `loam amend seal`).

Sidecar advances per sealed-component-cycle ritual via `loam amend apply` then `loam amend seal --plan-doc <plan-doc>`.

---

## §5 — Decisions builder rules at build time

- **D-PCVR.1.a (sweep target version):** target is `0.12.0` — current shipped MINOR per D-NFCLEAN.4 + D-SDPD precedents. The v0.12.1-21 PATCHes ride v0.12.0; per-component-version discipline tracks MINOR only. If at build-time the current shipped MINOR has advanced (e.g., to v0.13.0), use the then-current MINOR per the established discipline.
- **D-PCVR.1.b (4 `0.0.0` files ruling):** ruled per §16 finding #1 at plan-time. Default recommendation: EXCLUDE from the discipline (the 4 files are experimental/measurement harnesses with explicit `0.0.0` semantics; their version is deliberately unset rather than stale). If owner rules INCLUDE, bump them to `0.12.0`; if owner rules EXCLUDE, document the exclusion in the regression-test's allowlist with a comment naming the rationale.
- **D-PCVR.2.a (anchor file shape):** `docs/ACTIVE_MINOR` is a single-line plain-text file containing the version string with no `v` prefix and no metadata. Trailing newline is allowed (UNIX-text convention). The file is human-readable + machine-readable; the simplest possible shape.
- **D-PCVR.2.b (anchor explanation placement):** the one-paragraph explanation lives in `docs/release-versioning-policy.md` as a new sub-section. Alternative: `docs/components/index.md` (where the AC.HONEST.1 memo lives). Builder's call; recommend `release-versioning-policy.md` because the discipline IS a versioning policy + the policy doc is where versioning-discipline readers will look first.
- **D-PCVR.3.a (regression test mechanism):** the test reads pyprojects via stdlib `tomllib` (Python 3.11+; loam requires 3.13 per per-component `requires-python`). Enumeration via `pathlib.Path.rglob('pyproject.toml')` with an explicit exclusion-set (the 4 `0.0.0` files per D-PCVR.1.b + `docs/archive/` + `.venv/`). The in-scope-allowlist is encoded as a tuple or set at the top of the test module + cited as the single source-of-truth shared with AC.PCVR.1's sweep.
- **D-PCVR.3.b (corrective-message shape):** the message is structured as `Pyproject version drift: <relative-file-path> is at "<stale>"; expected "<expected>" per docs/ACTIVE_MINOR. Fix: bump the file's `version = "..."` line to "<expected>".` Single line per drifted file; a header line names the count of drifted files; a footer line names the docs/ACTIVE_MINOR anchor path.
- **D-PCVR.3.c (anchor-file repo-root resolution):** the test uses a canonical repo-root resolver — walks up from `__file__` until it finds `docs/ACTIVE_MINOR` OR a `pyproject.toml` carrying the `plugins/dev-sdlc/` shape. If neither found, raises a clear `FileNotFoundError` with the searched paths.
- **D-PCVR.4.a (mutation-detection fixture shape):** the fixture pyproject lives in `tmp_path` (pytest-provided), contains a minimal `[project]` block with `name = "fixture"` and `version = "0.10.0"`. The assertion helper is invoked with an explicit `base_path` parameter (the tmp dir) and `expected_version` parameter (the canonical-anchor value). The helper raises `AssertionError` (or a custom exception) with the corrective-message body; the test asserts the message contains `"Pyproject version drift"`.
- **D-PCVR.4.b (helper signature compatibility):** the assertion helper used by AC.PCVR.3 (real-tree assertion) and AC.PCVR.4 (fixture assertion) is the SAME helper — parameterized on `base_path` + `expected_version` + `in_scope_files`. Default parameters reproduce the real-tree behavior; tests override for fixture invocation. If at build-time the helper cannot be cleanly parameterized (e.g., real-tree assertion is implemented inline), refactor at the source-edit batch — surface to dispatcher per HARD HALT #3.
- **D-PCVR.5 (AC ID family):** AC IDs use the scope-descriptive `PCVR` family ("Per-Component-Version-Regression") per `feedback_scope_descriptive_ac_ids`. NOT version-packed.
- **D-PCVR.6 (test discoverability via loam amend seal):** the new test at `plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py` runs under the dev-sdlc component's `seal_test` because the fence-anchor is `dev-sdlc`. The test must pass under `pytest plugins/dev-sdlc/tests/` invocation (the standard `loam amend seal` per-component test discovery shape).

---

## §6 — Out of scope (explicit)

- **Module-top `__version__` string sweep.** The 4 `__version__` bumps that rode v0.8.0's AC.HONEST.1 + v0.9.0's bump are themselves stale at v0.10.0 (not v0.12.0). Per D-NFCLEAN.4 + D-SDPD: PATCHes ride MINOR for pyprojects; the same precedent applies to `__version__` strings — they advance with MINORs, not PATCHes. The v0.13.0 MINOR closure of the `__version__` discipline is the right surface. FIDRAFT capture in this PATCH names the follow-on.
- **Auto-advance of `docs/ACTIVE_MINOR` at MINOR-ship time.** This PATCH establishes the anchor + the regression test; auto-advance (extending the v0.7.4 `apply_backfill` family with an `ACTIVE_MINOR` writer) is a separate concern. FIDRAFT capture names the follow-on.
- **The 21 v0.12.1-21 PATCHes' STATE.md + roadmap §2 rollup completeness.** Already addressed by amendment #149 ("STATE.md leading-title Active-Version + release-roadmap.md §3 Active version flip + v0.12.1..v0.12.21 series rollup change-log entry" per commit `668c251`). Out of scope here; this PATCH does NOT touch the v0.12.x rollup narrative.
- **Reviving the v0.7.4 `post_publish_backfill` to auto-write `ACTIVE_MINOR`.** Structurally additive to the release-CLI; separate v0.13.x or later concern.
- **Drive-to-zero of all v0.11/v0.12 silent-skip consequences.** This PATCH closes the pyproject sweep + adds the regression test. Other v0.11/v0.12 silent-skips (if any beyond the pyproject discipline) are out of scope.
- **Restructure of STATE.md or release-roadmap.md.** Separate v0.13.0+ candidate per the consistency review §7 item 4.
- **Sweep of every `v0.10.0` mention across docs.** This PATCH bumps `version =` fields in pyprojects only; doc bodies that say "v0.10.0" in narrative context (e.g., the v0.10.0 sealed plan-docs) are historical references and stay as-is.
- **Anthropic API key paths** (per `feedback_no_anthropic_api_key`).
- **Multi-LLM via OpenRouter** (per architectural constraint).

---

## §7 — HARD HALTs (build-time)

Halt-and-surface to dispatcher (return owner-call) — do NOT proceed past — on any of:

1. **The 4 `0.0.0` files' ruling is unclear or missing from §16 finding #1's resolution.** Halt; surface; cannot proceed without an explicit IN-vs-OUT ruling on each of the 4 files.
2. **The current shipped MINOR at build-time is NOT `0.12.0`.** If a v0.13.0 MINOR has shipped between plan-author dispatch and build-dispatch, the target version changes. Verify Tier-0 via `docs/release-roadmap.md` §3 active-version line OR STATE.md leading-title at build-start; if `0.12.0` is no longer current, halt + surface for re-targeting.
3. **AC.PCVR.4's assertion-helper refactor is non-trivial.** If extracting the helper to accept `base_path` + `expected_version` requires touching multiple modules or breaks existing test invocations, halt + surface; the dispatcher rules on whether to accept a more complex refactor OR scope the AC down.
4. **The regression test's enumeration logic produces a different in-scope set than §3 PRIMARY.** If `rglob('pyproject.toml')` minus the exclusion set returns a count other than 26 (or 30 if `0.0.0` ruling is INCLUDE), halt; surface; either the enumeration is off OR the §3 PRIMARY list is stale (e.g., a new pyproject landed between plan-author and build).
5. **A pyproject in the in-scope set CAN'T be bumped to `0.12.0` for a real reason** (e.g., the file is auto-generated, the build script consumes the literal `0.10.0` string elsewhere, etc.). Halt; surface; the per-file exception needs an explicit ruling.
6. **Test invocation discovery fails** — if the new test isn't picked up by `pytest plugins/dev-sdlc/tests/` (the `loam amend seal` per-component test discovery), the test exists but doesn't gate. Halt; surface; fix the discoverability before sealing.
7. **`docs/ACTIVE_MINOR` placement conflicts** with an existing file at that path OR with another in-flight plan's expectation of that path. Halt; surface; rule on alternative placement.
8. **ODD §2.5 violation in your work OR surrounding code** (per `feedback_subagent_odd_violation_halt`). Specifically, the regression test's in-scope-set MUST map to AC.PCVR.1 + AC.PCVR.3; no enumeration that admits a pyproject NOT named in the plan.
9. **Wrong-tree-write** (any edit lands at a path outside `/Users/lukeivers/loam/`).
10. **Any reach for ASK-FIRST class actions:** `cd` outside `/Users/lukeivers/loam/`, `git push`, `git tag`, `git commit --amend` (per `feedback_no_amend_in_agent_dispatches`). Immediate halt.
11. **Any reach for an Anthropic API key path** (per `feedback_no_anthropic_api_key`). Immediate halt.
12. **Wall-clock exceeds upper plan band by >2×** (60 min upper × 2 = 120 min). Halt with current state.

---

## §8 — Dependencies

- **v0.8.0 AC.HONEST.1** (sealed `e44b09d`) — HARD. This PATCH defects against AC.HONEST.1's outcome shape; without the v0.8.0 promise this PATCH has no parent.
- **v0.8.1 D-NFCLEAN.4 + F-PCV-1** (sealed `9411061`) — HARD. The "PATCHes ride MINOR" ruling that defines the target version logic for this PATCH.
- **v0.8.2 D-SDPD** (sealed `a54295f`) — SOFT. Reconfirms D-NFCLEAN.4.
- **v0.9.0 AC.ODDPAPER pyproject bump precedent** (sealed `4a4535f`) — SOFT. First post-v0.8.0 MINOR to honor the discipline; this PATCH closes the regression from the v0.11/v0.12 break.
- **`docs/release-versioning-policy.md`** — HARD. The MINOR-only-bumps rule is grounded in this policy + the per-cycle precedents.
- **`docs/release-roadmap.md` §3 active-version line** — SOFT. Used at build-time to verify current shipped MINOR per HARD HALT #2.
- **`docs/STATE.md` leading-title Active-Version** — SOFT. Same verification.
- **`feedback_scope_descriptive_ac_ids`** — SOFT. Drives the `PCVR` AC ID family.
- **`feedback_test_outcome_altitude_required`** — HARD. AC.PCVR.4 is the outcome-altitude proof.
- **`feedback_loose_AC_text_fix_AC_not_implementation`** — SOFT. Considered + dismissed at plan-time (the AC text was structurally adequate; the failure is missing structural enforcement, not loose AC text).
- **`feedback_no_amend_in_agent_dispatches`** — HARD. Every commit is NEW; never `--amend`.
- **`feedback_no_anthropic_api_key`** — HARD.
- **`feedback_subagent_odd_violation_halt`** — HARD.
- **No new external dependencies.** Uses stdlib `tomllib` (Python 3.11+; loam at 3.13).

---

## §9 — Estimated AI-time

Per `feedback_duration_estimation_rubric`. Multi-component PATCH; mechanical sweep + one new test file + one new doc file + STATE/roadmap admin. Confidence in outcome shape is high (Lens 4 — tight scope appropriate per-AC; the work is mechanical defect closure within an established outcome shape).

| Stage | Band | Midpoint |
|---|---|---|
| Plan-doc + manifest authoring (this file) | 20-30 min | 25 min |
| AC.PCVR.1 — 26 pyproject version bumps | 5-8 min | 6 min |
| AC.PCVR.2 — `docs/ACTIVE_MINOR` + policy-doc paragraph | 3-5 min | 4 min |
| AC.PCVR.3 — regression test (enumeration + assertion + corrective-message) | 10-15 min | 12 min |
| AC.PCVR.4 — mutation-detection fixture test | 5-10 min | 7 min |
| HARD smoke writeup + FIDRAFT entries + STATE/roadmap admin | 10-15 min | 12 min |
| Manifest apply + seal + plan §13 backfill | 8-15 min | 11 min |
| **Total build (excluding plan-authoring)** | **41-68 min** | **52 min** |
| **Total PATCH (including plan-authoring)** | **61-98 min** | **77 min** |

Defensible: this is a mechanical PATCH; the dominant cost is the regression test authoring (12 min midpoint) which is the new-Python-test-writing class. Midpoint well below the v0.8.0 honesty-cleanup MINOR's 184 min midpoint because this PATCH ships ONE AC family vs v0.8.0's 7 AC families. The dispatch brief's 20-30 min for plan authoring is at-band (this plan-doc came in at the midpoint).

Owner gate-review separate (publish per ASK-FIRST after seal).

---

## §10 — Risks + mitigations

- **Risk:** the 4 `0.0.0` files have a real reason to stay at `0.0.0` (deliberate "version-unset" semantics for measurement/experimental harnesses). **Mitigation:** §16 finding #1 surfaces the ruling explicitly; default recommendation EXCLUDE; builder cannot proceed without explicit owner-or-dispatcher ruling per HARD HALT #1.
- **Risk:** the "current shipped MINOR" anchor concept conflicts with an existing in-flight plan or convention. **Mitigation:** Tier-0 verified no existing `docs/ACTIVE_MINOR` file + the new file is a single line + the discipline is named in `release-versioning-policy.md`. If a build-time conflict surfaces, HARD HALT #7 catches it.
- **Risk:** the regression test creates a false-RED on first-run because of enumeration glob over-reach (e.g., catches a `.venv/` pyproject the dev's local install dropped). **Mitigation:** D-PCVR.3.a names the exclusion set explicitly (`.venv/` + `docs/archive/` + the 4 `0.0.0` files); the test fixture mutation-detection (AC.PCVR.4) catches the test-mechanism failure mode.
- **Risk:** v0.13.0 ships between plan-author and build, making `0.12.0` stale at build-time. **Mitigation:** HARD HALT #2 — Tier-0 verify the current shipped MINOR at build-start; re-target if drifted.
- **Risk:** the regression test breaks the existing `pytest plugins/dev-sdlc/tests/` invocation (e.g., import-time error in the new test file). **Mitigation:** the new test follows the standard `test_AC_<FAMILY>_<n>_<descriptor>.py` shape per the existing dev-sdlc test convention; the helper is plain Python with stdlib imports only.

---

## §11 — Authority chain

- **2026-05-23 consistency review** at `/Users/lukeivers/pos3/workspace/.scratch/claude-output/loam-fresh-install-consistency-review-2026-05-23.md` §7 item 5 (review dispatched by primary persona at Luke's request via Telegram 12002) — surfaced the regression + recommended the sweep + regression test.
- **Plan-author dispatch 2026-05-23** (this artefact) — authored from the consistency review per dispatcher's brief (Batch C of the three-batch fix sequence per the review's §7 operational note).
- **v0.8.0 AC.HONEST.1** (sealed `e44b09d` 2026-05-10) — the outcome shape this PATCH defects against.
- **v0.8.1 D-NFCLEAN.4** (sealed `9411061`) — the "PATCHes ride MINOR" ruling.
- **`feedback_scope_descriptive_ac_ids`** — AC ID family choice ground.

---

## §12 — Cross-references

- Plan-doc convention: `plugins/dev-sdlc/docs/conventions/plan-docs.md`.
- v0.8.0 sealed exemplar (multi-component pyproject sweep + AC.HONEST family): `docs/plans/sealed/v0-8-0-honesty-cleanup.md` + `.manifest.yaml`.
- v0.8.1 D-NFCLEAN.4 precedent (PATCH-rides-MINOR ruling): `docs/plans/sealed/v0-8-1-honesty-cleanup-followon.md`.
- v0.8.2 D-SDPD precedent (reconfirms): `docs/plans/sealed/v0-8-2-release-cli-scope-descriptive-plan-doc-support.md`.
- v0.9.0 first-post-v0.8.0 MINOR bump precedent: `docs/plans/sealed/odd-paper-methodology-publish.md` (the actual plan-doc slug for v0.9.0 — scope-descriptive).
- Consistency review trigger: `/Users/lukeivers/pos3/workspace/.scratch/claude-output/loam-fresh-install-consistency-review-2026-05-23.md` §7 item 5.
- Memory rules cited in §8 Dependencies.

---

## §13 — §status

**Build cycle:** PLAN-ONLY 2026-05-23 — awaiting dispatcher ratification of §16 halt-and-surface findings, then build dispatch.

**Plan-doc commits:** TBD-AT-COMMIT (this file + manifest).

### AC verdict matrix (populated at build time)

| AC | Verdict | Evidence |
|---|---|---|
| AC.PCVR.1 — Sweep | TBD | TBD |
| AC.PCVR.2 — Anchor | TBD | TBD |
| AC.PCVR.3 — Regression test | TBD | TBD |
| AC.PCVR.4 — Mutation-detection outcome-altitude | TBD | TBD |
| AC.PCVR.S — Seal-diff discipline | TBD | TBD |

### AI-time actuals (populated at build time)

| Stage | Estimated (plan §9) | Actual |
|---|---|---|
| Plan-doc + manifest authoring | 20-30 min | TBD |
| AC.PCVR.1 — 26 bumps | 5-8 min | TBD |
| AC.PCVR.2 — anchor + policy paragraph | 3-5 min | TBD |
| AC.PCVR.3 — regression test | 10-15 min | TBD |
| AC.PCVR.4 — mutation-detection fixture | 5-10 min | TBD |
| HARD smoke + FIDRAFT + STATE/roadmap | 10-15 min | TBD |
| Apply + seal + §13 backfill | 8-15 min | TBD |
| **Total** | **61-98 min** | **TBD** |

### Halt-and-surface findings (populated at build time)

TBD.

---

## §14 — Method decisions (populated at build time)

The plan-doc's §5 names the build-time decisions (D-PCVR.1.a sweep target, D-PCVR.1.b `0.0.0` ruling honoring §16 finding #1, D-PCVR.2.a anchor shape, D-PCVR.2.b anchor placement, D-PCVR.3.a/b/c regression test mechanism, D-PCVR.4.a/b mutation-detection fixture + helper signature, D-PCVR.5 AC ID family, D-PCVR.6 test discoverability). Build-time deviations recorded inline.

### Commit SHAs (populated at build time)

- Plan-doc + manifest authoring: TBD
- Source-edit batch (26 bumps + ACTIVE_MINOR + policy paragraph + regression test + smoke writeup + FIDRAFT entries + STATE/roadmap admin): TBD
- Manifest baseline bump: TBD (if needed)
- Apply auto-commit: TBD
- Seal commit: TBD
- §status SHA backfill (this update): TBD

### Build-time decision deviations (populated at build time)

TBD.

---

## §15 — Backwards-compat verification

- **All existing tests pass** post-source-edit. Per-component test invocations (`pytest plugins/dev-sdlc/tests/`, `pytest framework/<x>/tests/`) must remain GREEN.
- **No existing pyproject's `requires-python` field changes.** The bump is `version` only; `requires-python = ">=3.13"` (or wherever each pyproject already sits) is untouched.
- **No existing build script consumes the literal `0.10.0` string.** Tier-0 verify pre-source-edit via `grep -rE '"0\.10\.0"' --include='*.py' framework/ plugins/`. If matches found, surface per HARD HALT #5.
- **`install-from-source.txt` is unaffected** (uses `-e ./framework/<x>` form; no version pins).
- **`loam release vX.Y.Z` gates** (per v0.6.0 + v0.7.x + v0.8.x release-CLI surface) are unaffected; the regression test runs under `pytest`, not under `loam release` directly. If `loam release` is later extended to invoke the regression test as a pre-publish gate, that's a separate FIDRAFT capture (composes with the auto-advance follow-on from §6).

---

## §16 — Halt-and-surface findings (plan-authoring stage)

### Finding #1 — 4 pyproject files at `version = "0.0.0"`: in or out of the discipline?

**The fact:** four pyprojects carry `version = "0.0.0"`:

- `framework/tools/handsoff-loop/pyproject.toml`
- `framework/tools/loam-spawn-isolation/pyproject.toml`
- `framework/tools/programbench-revival/pyproject.toml`
- `framework/tools/programbench-revival/realpb/pyproject.toml`

Tier-0 read of each pyproject's `description` field shows they are **measurement / experimental / hands-off-loop harnesses** with descriptions naming them as "the real orchestrated hands-off loop" / "the ONE shared, importable, mandated telegram-plugin-isolation surface" / "ProgramBench-revival v2 — the measurement harness" / "the real-benchmark measurement harness." Their `0.0.0` value reads as deliberate "version-unset" semantics — these are not stale; they were authored at `0.0.0` and have been left there intentionally (they were authored AFTER v0.10.0's bump per their `0.0.0` not `0.10.0`).

**The question:** are they IN the per-component-version discipline (bump to `0.12.0`) or OUT (stay `0.0.0` as deliberate experimental-harness semantics)?

**Two options:**

- **A. INCLUDE** — bump all four to `0.12.0` for consistency with the rest of the component tree. Argument: AC.HONEST.1's promise is "every component pyproject advances with each shipped minor"; the 4 files are component pyprojects; they should advance.
- **B. EXCLUDE** — leave the four at `0.0.0` as deliberate experimental-harness semantics; document the exclusion in the regression-test's allowlist with a comment explaining the rationale. Argument: these are measurement harnesses with explicit "version-unset" semantics that's distinct from "stale"; treating them like runtime components muddles the discipline.

**Recommendation: B (EXCLUDE).** Rationale: the 4 files' descriptions explicitly position them as measurement / experimental / hands-off-loop harnesses (not runtime components shipped to end-users); the `0.0.0` value reads as semantically meaningful ("not a versioned release") rather than stale; bumping them to `0.12.0` would falsely imply they are versioned runtime components on the same release cadence as e.g. `primary-persona` or `workspace-bootstrap`. The regression test's allowlist explicitly excludes them with a comment naming the rationale; the discipline still applies to the 26 in-scope component pyprojects.

**Surface: needs explicit ruling.** Default to recommendation B if no ruling surfaces by build-dispatch.

### Finding #2 — Multi-component fence shape: is the v0.8.0 precedent (single fence-anchor + universal_paths) still the correct shape, or does `loam-amend` now support cross-component fences directly?

**The fact:** v0.8.0/v0.8.1/v0.8.2/v0.9.0 all used the `dev-sdlc` plugin as a single fence-anchor + relied on `universal_paths.prefixes: [framework/, plugins/]` to admit pyproject edits across the tree. This works (5 cycles of empirical evidence) but is conceptually awkward — the "fence" includes 26 files outside the named component.

**The question:** is this still the canonical shape, or has `loam-amend` been extended (e.g., via amendments 136 / 138 / 139 / 140 / 141 / 142 on the loam-amend seal-tool) to support a more explicit cross-component fence?

**Tier-0 verified:** the v0.8.2 sealed manifest (post-amendment-140/141 hygiene) still uses the single-fence-anchor + universal_paths pattern. So at the v0.8.2 epoch the convention is stable. No evidence in the recent amendment-N stream (136-149) that the convention changed.

**Recommendation: USE the v0.8.0 precedent.** Single fence-anchor `dev-sdlc` + `universal_paths.prefixes: [framework/, plugins/]` + universal-admission docs file list. Mirrors 5 prior sealed cycles exactly.

**Surface: low-stakes; build-time can adapt if loam-amend's behavior has drifted.** Not a HARD HALT — the v0.8.0 precedent is a safe default.

### Finding #3 — AC.HONEST.1 text tightening: is it needed?

**The fact:** the dispatch brief asked whether the AC.HONEST.1 text needs tightening per `feedback_loose_AC_text_fix_AC_not_implementation`. Tier-0 read of AC.HONEST.1's sealed body (at `docs/plans/sealed/v0-8-0-honesty-cleanup.md:128-139`):

> AC.HONEST.1 — Component pyproject.toml version bump 18/18 framework + plugin → `0.8.0`
> **What:** Every framework component + plugin component's `pyproject.toml` carries `version = "0.8.0"`. **Establishes per-component-version discipline as a tracked surface — component versions advance with shipped minors going forward.**

**The analysis:** the AC text is structurally adequate. It (a) establishes the discipline as a tracked surface, (b) names the advance-with-shipped-minors invariant, (c) was verified at seal-time via grep. The text did NOT mandate structural enforcement (a regression test); the discipline relied on builder-memory at subsequent MINORs. The failure is missing structural enforcement, NOT loose AC text.

**The fix-the-AC-not-the-implementation rule** applies when "the implementation matches intent and AC text is loose." Here, the implementation at v0.11/v0.12 did NOT match intent (pyprojects silently skipped the bump); the discipline relied on a non-structural enforcement mechanism that quietly failed. The right fix is structural (add a regression test that prevents future silent-skips), NOT to tighten the AC text after the fact.

**Recommendation: NO AC text tightening.** AC.HONEST.1 sealed text stays as-is. The structural enforcement is the new AC.PCVR.3 + AC.PCVR.4 in this PATCH; together they make the AC.HONEST.1 discipline non-silently-skippable going forward.

**Surface: F2 RF on the dispatch brief's framing.** The brief said "Update the v0.8.0 AC.HONEST.1 promise — if the original promise's text was structurally insufficient (allowed silent staling), tighten it." Tier-0 evidence says the AC text was NOT structurally insufficient; the enforcement mechanism was. Plan author's call: NO AC text tightening; build the structural enforcement instead.

### Finding #4 — Target version is `0.12.0`, NOT `0.12.21` — F2 RF on the dispatch brief's framing

**The fact:** the dispatch brief said "Sweep all per-component pyproject.toml version fields to the current shipped minor (v0.12.x)." This framing is ambiguous — `v0.12.x` covers everything from `0.12.0` to `0.12.21`. The locked-in D-NFCLEAN.4 + D-SDPD precedents (v0.8.1 + v0.8.2 sealed) are explicit: **PATCHes ride predecessor MINOR; per-component-version discipline advances with MINORs only**.

**The implication:** the target version is `0.12.0` (current MINOR), NOT `0.12.21` (current PATCH). The 21 PATCHes since v0.12.0 do NOT bump per-component pyprojects per the established discipline.

**Recommendation: bump to `0.12.0`, NOT `0.12.21`.** Honors the v0.8.1 D-NFCLEAN.4 + v0.8.2 D-SDPD precedents that this PATCH itself is grounded in.

**Surface: F2 RF on the dispatch brief.** The brief's "v0.12.x" framing was loose; tightening to `0.12.0` is the correct read per established precedent. If the dispatcher meant `0.12.21` (overriding the D-NFCLEAN.4 precedent), surface the question explicitly. Default: `0.12.0`.

### Finding #5 — In-fence pyproject count is 30, NOT ~25

**The fact:** the dispatch brief and consistency review both estimated "~25" pyproject files in scope. Tier-0 enumeration at 2026-05-23 via `find . -name pyproject.toml -not -path '*/.venv/*' -not -path '*/.git/*' -not -path '*/docs/archive/*'` returns **30 files**. Of those: 26 currently at `0.10.0` (in-scope sweep), 4 currently at `0.0.0` (§16 finding #1 ruling).

**Recommendation: use the verified count of 30 (26 in-scope + 4 ruling-pending), NOT the estimated ~25.** Plan §3 PRIMARY enumerates all 30; the regression test enumerates all 30 with the explicit allowlist mechanism.

**Surface: low-stakes F2 RF on the estimate's specificity.** Not a HARD HALT — the verified count is documented + the enumeration drives both the sweep + the test.

### No other halt-and-surface findings at plan-authoring time.

The remaining ACs / decisions land cleanly per the v0.8.0 precedent. Build-time discoveries surface inline per §13.
