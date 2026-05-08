# v0.2.5.1 corrective — F-LEAK + F-TIMEOUT + F-VERIFY-ORPHAN — plan

Dev-discipline patch release; touches one sealed component (`dev-sdlc` /
odd-extractor). Single `loam amend` cycle.

**Status:** plan + manifest ready for apply + seal. 2026-05-08.
**Working directory:** /Users/lukeivers/ivers-corp-pos-v2/
**Ancestor record:** v0.2.5 SHIPPED at HEAD `7f41ed0`; tag `v0.2.5` pushed
to `lukeivers/loam`. Last seal `5138dd7` (v0.2.5 corrective C6).
**Research:** captured artefact `/Users/lukeivers/pos3/workspace/.scratch/claude-output/eric-run-issues-friday-processing.md`
(F-LEAK + F-TIMEOUT + F-VERIFY-ORPHAN diagnosis from Eric's actual
install of v0.2.5 against rd-automation; Eric-session three-options
framing).

---

## 1. Summary / TLDR

Three production-path defects surfaced by Eric's actual install of
v0.2.5 against rd-automation. v0.2.5 is live in the public repo at
`lukeivers/loam`; anyone running `loam odd-extract` against a
non-trivial real-world repo with off-limits artefact directories or a
big code surface hits these bugs.

- **F-LEAK** — Filenames from off-limits directories
  (`html-captures/`, `screenshots/`, `public/uploads/`, etc.) leaked
  into the synthesis prompt. Filenames only, not contents — but the
  filenames themselves are scope-violation.
- **F-TIMEOUT** — synthesis subprocess hard-coded 180s timeout exceeded
  on large prompts; CLI exposed no override flag.
- **F-VERIFY-ORPHAN** — verify stage failed when the synthesis LLM
  emitted capabilities pointing to objectives the demotion-guard had
  dropped. Real-world finding: `C.state-diff.1 → dropped O.verification.1`,
  `C.dry-run.1 → dropped O.simulation.1`.

This corrective lands FIVE ACs that fix all three findings + add an
outcome-altitude integration test against rd-automation:

- AC.V025-1.1 — analyze step honors contract off-limits zones (read
  from the survey markdown; default skip-list extends with
  `html-captures` / `screenshots` / `html-output` / common artefact dir
  names as belt-and-suspenders). Filenames from off-limits directories
  do not appear in evidence rows or the synthesis prompt.
- AC.V025-1.2 — `--synthesis-timeout <seconds>` CLI flag threads
  through to the synthesis client; default raised from 180s to 600s.
- AC.V025-1.3 — demotion-guard cascade: when a guard demotes-or-drops
  an objective, capabilities referencing the dropped objective are
  also dropped (cascade-drop). If a capability has multiple `serves`
  references and at least one survives, the capability is retained
  with the surviving references. Validator stays strict; parsing layer
  becomes more disciplined.
- AC.V025-1.4 — outcome-altitude integration test against
  rd-automation real-world. Full pipeline GREEN: zero stages exit
  non-zero; objectives.yaml non-empty; backing-map.yaml exists;
  gap-inventory.yaml ≥1 entry; build-next.yaml ranks ≥1 candidate;
  no `html-captures/` filenames in synthesis prompt log; no verify-
  stage orphan-capability halt.
- AC.V025-1.5 — full odd-extractor + dev-sdlc + framework test suite
  green; no regressions.

Ratifying decisions (closed in §1; no owner ruling required):
- **D-1 (F-LEAK off-limits source):** the survey markdown's `## 10.
  Off-limits zones` section is the canonical source. The survey
  parser at `framework/workspace-bootstrap/src/loam/workspace_bootstrap/survey_parser.py`
  currently parses 6 install-time questions; the off-limits section
  is OUT of that scope. The corrective extracts off-limits dir names
  from the survey raw text via a tiny dedicated parser and injects
  them into `_SKIP_DIR_NAMES` at analyze-walk time — best-effort,
  never blocks on parse failure (mirrors AC.ONBOARD.15 precedent).
  Plus extends the default skip-list to include common artefact dirs
  for the no-survey case.
- **D-2 (F-VERIFY-ORPHAN cascade-drop vs remap):** cascade-drop is
  the simplest correct shape. Multi-objective `serves` capabilities
  with one surviving reference retain the surviving reference.
  Capabilities with all references dropped are dropped entirely.
  Logged at WARN level naming the dropped capability + dropped
  objective. Method-decision recorded in §14 D-1 post-build with
  the band-rule guards' observed rate of objective drop on
  rd-automation as the calibrating signal.
- **D-3 (F-TIMEOUT default value):** 600s. Eric's failed run was at
  the 180s ceiling; observed prompt size after the F-LEAK fix should
  drop substantially (no html-captures filenames burning prompt
  budget), but a 3.3x bump gives generous headroom for legitimately
  large repos. Operator can override with `--synthesis-timeout`.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5 framing)

Per CLAUDE.md §2.5 (every line of code/branch/test maps to a named
AC), this corrective lands FIVE ACs that together fence: F-LEAK
closure (AC.V025-1.1), F-TIMEOUT closure (AC.V025-1.2), F-VERIFY-
ORPHAN closure (AC.V025-1.3), outcome-altitude verification against
the failure surface (AC.V025-1.4), and no-regression guarantee on
the full suite (AC.V025-1.5).

This corrective claims its own V025-1.* prefix scoped to the v0.2.5.1
patch release itself, mirroring the corrective precedents.

---

## 3. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude leverage

The off-limits parser composes on top of the existing
`survey_parser.py` AC.ONBOARD.15 substrate (best-effort, never-block-
on-parse-failure pattern). The synthesis-timeout flag composes on top
of argparse + the existing `ClaudePrintAnthropicShimClient` ctor
parameter. The cascade-drop guard composes on top of the existing
`_apply_band_demotion_guard` + `_apply_plausible_demotion_or_drop_guard`
infrastructure. No new Claude-specific primitive applies; all three
fixes leverage existing scaffolding.

### Lens 2 — Harness + primary-persona value

Primary-persona test: F-LEAK directly hurts every user with a
non-trivial repo (off-limits directories are common: `html-captures`
in Playwright apps, `screenshots` in test apps, `public/uploads`
+ `data/` in many web apps). F-TIMEOUT is a hard wall on big repos.
F-VERIFY-ORPHAN is a hard wall when the LLM is even mildly creative
in its capability-objective mapping. All three fixes reduce the
"did this just blow up on my real repo" friction.

Harness test: the rd-automation outcome-altitude test becomes a
durable real-world probe — the canonical fixture (jsts-playwright-app)
is synthetic; rd-automation is the real-world failure surface. Future
correctives can reuse the pattern.

### Lens 3 — ODD authoring

Five outcome-shaped ACs. None state HOW (no "use frozenset.union /
add try-except / use new variable name" in AC bodies); each pins
WHAT the observable surface is. Method (where the off-limits parser
lives; cascade-drop algorithm details) lives in §14 + implementation.

Per the methodology paper §2.5 positive-framing principle — ACs are
authored as "the system does X" not "the system does not do Y":
- AC.V025-1.1: "analyze step honors contract off-limits zones" (not
  "analyze step does not walk off-limits zones")
- AC.V025-1.2: "configurable synthesis subprocess timeout" (not "no
  hardcoded 180s timeout")
- AC.V025-1.3: "demotion-guard cascades to dependent capabilities"
  (not "verify stage does not halt on orphans")

### Lens 4 — Prompt scope ↔ confidence

High confidence: the three findings are crisply diagnosed in the
captured artefact; fix shapes are obvious (dir-name skip + dict
parser; argparse flag + ctor kwarg threading; existing-pattern
cascade-drop in synthesis layer). Tight scope appropriate.

### Lens 5 — Swarming

Single corrective with three cross-cutting concerns
(analyze.py + synthesis.py + cli.py + claude_print_synthesis_client.py).
Decomposing further (one agent per AC) adds coordination overhead
with no tighter AC. Single agent.

---

## 4. Acceptance criteria (V025-1 — patch release)

### AC.V025-1.1 — Analyze step honors off-limits zones from contract

`plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/analyze.py`'s
`_walk_repo` reads off-limits directory names from the user-survey
markdown's `## 10. Off-limits zones` section (canonical source) and
skips those paths during repo walk. The survey is resolved via the
existing read-order at `multi_source._read_user_survey` (`<repo>/.loam/
onboarding-survey.md` → `~/loam-onboarding-survey.md` → env-var). Best-
effort — never blocks on parse failure (mirrors AC.ONBOARD.15
contract). Plus the static `_SKIP_DIR_NAMES` is extended with
`html-captures`, `screenshots`, `html-output`, `test-results`,
`coverage`, `playwright-report` as belt-and-suspenders defaults for
repos invoked without an off-limits config.

**Verification:** unit test (a) feeds analyze a repo containing
`html-captures/foo.html` + a survey with `html-captures/` in §10 +
verifies the file does NOT appear in the resulting AnalysisPlan;
unit test (b) feeds analyze a repo with `screenshots/foo.png` and
NO survey + verifies the file does NOT appear in the resulting
AnalysisPlan (default skip-list); unit test (c) feeds analyze a
repo with a malformed survey + verifies analyze does NOT raise +
falls back to the default skip-list. Plus the AC.V025-1.4 outcome-
altitude integration test verifies on rd-automation that no
`html-captures/`-prefixed filenames appear in the post-run
synthesis prompt log (read from the per-extraction
`audit-log/synthesis_request_*.txt` if persisted, or by inspection
of the evidence-rows.yaml + plan.yaml — whichever production
artefact reflects the analyze output).

### AC.V025-1.2 — Configurable synthesis subprocess timeout

`ClaudePrintAnthropicShimClient.__init__` default `timeout_seconds`
raised from 180.0 to 600.0. CLI flag `--synthesis-timeout SECONDS`
threads through `_cmd_extract` → `build_default_synthesis_client(
timeout_seconds=...)` → ctor. The flag accepts a positive float;
help text describes the default and the override mechanism.

**Verification:** unit test (a) constructs the shim with `timeout_seconds=30`
and verifies the value is stored on `self._timeout_seconds`;
unit test (b) verifies `build_default_synthesis_client(timeout_seconds=
30.0)` propagates the value to the constructed client;
unit test (c) verifies the CLI parses `--synthesis-timeout 30` and
produces a Namespace with `synthesis_timeout=30.0`; unit test (d)
verifies `loam odd-extract --help` stdout contains the new flag's
help text. Plus integration:
`loam odd-extract <repo> --synthesis-timeout 30` would abort after
30s on a slow synthesis call — exercised in the AC.V025-1.4
integration test by passing a generous `--synthesis-timeout 1200`
that does not abort.

### AC.V025-1.3 — Demotion-guard cascades to dependent capabilities

When `_apply_band_demotion_guard` or
`_apply_plausible_demotion_or_drop_guard` drops an objective from
`objectives_raw` (i.e., the row is removed from the list, not just
demoted), the synthesis layer ALSO filters `capabilities_raw` such
that:

1. Capabilities whose ENTIRE `serves` list resolves to dropped
   objective IDs are dropped (cascade-drop).
2. Capabilities whose `serves` list has ≥1 surviving objective
   ID retain the capability with the dropped IDs filtered out.
3. Each cascade action is logged at WARN level naming the dropped
   capability + the dropped objective(s) referenced.

The validator at `verify._check_capability_references` stays strict
(unchanged surface). Cascade happens parsing-side in
`_validate_rows` before per-row Pydantic validation.

**Verification:** unit test (a) feeds `_validate_rows` a payload
where the band-rule guards drop `O.verification.1` and a capability
references it via `serves: ["O.verification.1"]` — verifies the
capability is dropped from the result + a WARN log line names the
cascade. Unit test (b) feeds a multi-`serves` capability (e.g.,
`serves: ["O.dropped.1", "O.kept.1"]`) — verifies the capability
is retained with `serves` filtered to `["O.kept.1"]`. Unit test (c)
verifies that the AC.OBJX.10 verify-stage check still raises on a
truly dangling reference (cascade only fires when the synthesis
layer itself dropped the objective). Plus the AC.V025-1.4 outcome-
altitude test verifies no verify-stage halt on rd-automation.

### AC.V025-1.4 — Outcome-altitude full pipeline GREEN against rd-automation

A NEW outcome-altitude test in
`plugins/dev-sdlc/odd-extractor/tests/test_AC_V025_1_4_full_pipeline_rd_automation.py`
exercises the full `loam odd-extract` 4-stage pipeline (stages
1-4) end-to-end via subprocess against
`/Users/lukeivers/pos3/workspace/rd-automation` (the local stale
copy is the canonical real-world fixture for this corrective; the
production rd-automation lives on Eric's workstation). The test:

1. Authors a stub PM at
   `<workspace>/workspace/.loam/pms/smoke-pm/contract.yaml`
   (mirrors AC.V025-C6.1 pattern).
2. Verifies rd-automation path exists; skips cleanly if not.
3. Skips cleanly if `claude` or `loam` binary not in PATH.
4. Runs Stage 1 — `loam odd-extract <rd-automation> --live
   --workspace-root <ws> --synthesis-timeout 1200
   --budget-cents 500 --budget-override`.
5. Runs Stage 2 (`--interview`), Stage 3 (`--gaps`), Stage 4
   (`--build-next`).
6. Asserts: zero stages exit non-zero. Asserts the four stage
   artefacts exist + are non-empty: `objectives.yaml`,
   `augmented-objectives.yaml`, `gap-inventory.yaml`,
   `build-next.yaml`. Plus `gap-inventory.yaml` parses to ≥1
   gap entry; `build-next.yaml` parses to ≥1 ranked candidate.
7. F-LEAK regression assertion: walks the post-run plan.yaml +
   evidence-rows.yaml and asserts NO file path beginning with
   `html-captures/` or `screenshots/` appears.
8. F-VERIFY-ORPHAN regression assertion: stage 1 (which runs
   verify internally) exited 0 — no orphan-capability halt
   occurred.

**Verification:** the test is named
`test_AC_V025_1_4_full_pipeline_rd_automation`; the test
PASSES on the build workstation (claude available + rd-automation
present); the test SKIP-passes if rd-automation is absent; the
test SKIP-passes if `claude` is absent.

### AC.V025-1.5 — All existing tests still pass; no regressions

Pre-corrective baseline (post-v0.2.5 SHIPPED at HEAD `7f41ed0`):
sealed AC tests at `plugins/dev-sdlc/odd-extractor/tests/`,
`plugins/dev-sdlc/tests/`, `framework/workspace-bootstrap/tests/`
remain fully green (modulo the documented pre-existing
stochastic-LLM tests + SKILLS-DSDLC yaml-frontmatter parse failures
called out in STATE.md). Any net-new test added by this corrective
passes; no sealed-AC test fails.

**Verification:** `pytest plugins/dev-sdlc/odd-extractor/tests/
plugins/dev-sdlc/tests/` pass-count meets or exceeds the post-v0.2.5
baseline + new V025-1 tests; no sealed-AC test fails. The
pre-existing stochastic live-LLM failures (C3.3 / C4.3) are
verified non-regressions against pre-corrective HEAD.

---

## 5. Behaviour-count check (ODD §3.3 forward; applied as dev-discipline check)

| # | Declared behaviour | AC |
|---|--------------------|-----|
| 1 | Analyze step honors off-limits zones from survey + extended default skip-list; off-limits filenames absent from evidence rows + synthesis prompt | AC.V025-1.1 |
| 2 | `--synthesis-timeout` CLI flag threads through to subprocess timeout; default 600s | AC.V025-1.2 |
| 3 | Demotion-guard cascade drops/filters capabilities referencing dropped objectives; multi-`serves` retains surviving references | AC.V025-1.3 |
| 4 | Outcome-altitude full pipeline GREEN against rd-automation; F-LEAK + F-VERIFY-ORPHAN regression assertions | AC.V025-1.4 |
| 5 | Full sealed test suite green; no regressions | AC.V025-1.5 |

---

## 6. Hard constraints

1. **No `--amend`.** Corrective new commits only. The C4-pivot agent's
   `--amend` deviation is exactly the failure mode to avoid.
2. **Scope fence.** Edits limited to:
   - `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/analyze.py`
     (off-limits parser + skip-list extension)
   - `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/synthesis.py`
     (cascade-drop in `_validate_rows`)
   - `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/claude_print_synthesis_client.py`
     (default timeout bump + ctor kwarg)
   - `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/cli.py`
     (`--synthesis-timeout` flag + plumbing)
   - new test files under `plugins/dev-sdlc/odd-extractor/tests/`
   - `docs/plans/v0-2-5-1-corrective-leak-timeout-verify-orphan.{md,manifest.yaml}`
   - `docs/STATE.md` (post-seal entry)
3. **No edit to `spec.py` validator.** Reference-integrity is
   parsing-layer concern; validator stays strict per design.
4. **No new third-party dependency.** Stdlib only.
5. **No push to `lukeivers/loam:main`.** Hold for dispatcher review.
6. **No `v0.2.5.1` tag.** Hold for dispatcher review.
7. **No extension to negative-alignment detection.** Deferred per
   master plan v0.2.6+.
8. **Backward-compat preserved.** All sealed AC tests green; no API
   surface change beyond the two new optional fields (the
   `--synthesis-timeout` flag + the `timeout_seconds` kwarg on
   `build_default_synthesis_client`).

---

## 7. Out of scope (explicit)

- Push to `lukeivers/loam:main`.
- `v0.2.5.1` tag creation.
- `spec.py` validator changes.
- Negative-alignment detection (deferred per master plan).
- v0.2.5 paper / programbench artefact changes.
- Eric outreach (paused per owner directive).
- Extending the survey parser at `framework/workspace-bootstrap/`
  beyond best-effort off-limits read (the §10 parsing happens at
  the analyze-time boundary, not at the survey-parser boundary,
  to keep the workspace-bootstrap component sealed-fence intact).

---

## 8. Implementation order (suggested — builder's call to refine)

1. Verify pwd is `/Users/lukeivers/ivers-corp-pos-v2`.
2. Author source edits in order:
   a. `analyze.py` — extend `_SKIP_DIR_NAMES` constants; add
      `_extract_off_limits_dirs(survey_text)` parser function;
      `_walk_repo` accepts an extra skip-set argument; `analyze_repo`
      reads survey at the top via the existing
      `multi_source._read_user_survey` and unions the parsed
      off-limits dirs with `_SKIP_DIR_NAMES` before passing to
      `_walk_repo`.
   b. `synthesis.py` — `_validate_rows` extracts the surviving
      objective-id set from `objectives_raw` AFTER both demotion
      guards run; iterates `capabilities_raw` and drops/filters
      capabilities per AC.V025-1.3 algorithm; logs each cascade.
   c. `claude_print_synthesis_client.py` — bump default
      `timeout_seconds` to 600.0; `build_default_synthesis_client`
      accepts `timeout_seconds` kwarg + threads through to ctor.
   d. `cli.py` — add `--synthesis-timeout` argument
      (type=float, default=None); thread through to
      `build_default_synthesis_client` call.
3. Author NEW tests:
   - `test_AC_V025_1_1_off_limits_skip.py` — three unit tests for
     skip-list extension, survey-parsed dirs, malformed-survey
     fallback.
   - `test_AC_V025_1_2_synthesis_timeout_flag.py` — four unit tests
     for ctor kwarg + builder propagation + CLI flag parse + help-
     text.
   - `test_AC_V025_1_3_cascade_drop.py` — three unit tests for
     single-`serves` cascade + multi-`serves` filter + verify
     still-strict on dangling refs.
   - `test_AC_V025_1_4_full_pipeline_rd_automation.py` — outcome-
     altitude integration test (skip-clean if rd-automation or
     claude absent).
4. Run narrow tests: new V025-1 tests pass.
5. Run full odd-extractor + dev-sdlc test suites.
6. Author manifest at
   `docs/plans/v0-2-5-1-corrective-leak-timeout-verify-orphan.manifest.yaml`.
7. `git add` files; conventional commit ladder:
   - feat: source + tests (BASELINE)
   - docs: plan-doc + manifest
   - chore(amend): manifest + apply
   - chore(seals): seal commit (via `loam amend seal`)
   - docs(plans): §14 SHA backfill (auto-emitted by `--plan-doc`)
   - docs(state): STATE.md entry (post-seal)
8. Run `loam amend apply <manifest>` then
   `loam amend seal --plan-doc <plan-doc> <manifest>`.
9. Write build report to
   `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-2-5-1-corrective-report.md`.

---

## 9. Bookkeeping surface

Sealed-component touched: `dev-sdlc` (odd-extractor + plugin). One
sidecar bump via `loam amend apply`. Single combined seal "v0.2.5.1
corrective — F-LEAK + F-TIMEOUT + F-VERIFY-ORPHAN".

```yaml
schema_version: 3
amendment:
  slug: v0-2-5-1-corrective-leak-timeout-verify-orphan
  title: <rendered at manifest authoring time>
baseline: <pinned to source-edit feat commit SHA at manifest commit time>
plan: docs/plans/v0-2-5-1-corrective-leak-timeout-verify-orphan.md
plan_doc_ref: docs/plans/v0-2-5-1-corrective-leak-timeout-verify-orphan.md
ac_count: 5
smoke_outcome: "V025-1.1 off-limits honored; V025-1.2 timeout configurable; V025-1.3 cascade-drop guards capabilities; V025-1.4 rd-automation pipeline GREEN; V025-1.5 no regressions"
components:
  - name: dev-sdlc
    seal_test: plugins/dev-sdlc/tests/test_no_sealed_amendments.py
    sidecar: plugins/dev-sdlc/tests/SEAL_COMMIT
    frozen_baseline: false
    extra_allowed_prefixes: []
universal_paths:
  prefixes:
    - docs/plans/
  files:
    - CLAUDE.md
    - docs/odd-in-loam.md
    - docs/odd-methodology.md
    - docs/STATE.md
    - docs/FUTURE_IDEAS_DRAFT.md
    - .gitignore
narrative:
  target: plugins/dev-sdlc/seals/SEAL_COMMIT.v0-2-5-1-corrective-leak-timeout-verify-orphan
```

STATE.md entry mirrors the v0.2.5 SHIPPED inline format.

---

## 10. Halt triggers (builder halts + signals owner)

1. WD mismatch (pwd ≠ `/Users/lukeivers/ivers-corp-pos-v2`). Halt.
2. rd-automation path absent or empty. Halt.
3. Concurrent agent activity detected (`pos-amend` lock or
   simultaneous build). Halt.
4. `loam amend apply` or `loam amend seal` errors. Halt.
5. Push or tag attempt — held for dispatcher.
6. Cross-component scope expansion beyond the named scope fence.
   Halt.
7. New BLOCKER beyond F-LEAK / F-TIMEOUT / F-VERIFY-ORPHAN. Halt.
8. The cascade-drop choice on F-VERIFY-ORPHAN turns out to lose
   information catastrophically (e.g., dropping ≥50% of capabilities
   on rd-automation). Halt; surface for design ruling.

---

## 11. Decisions remaining for the owner to rule on

(none — D-1 + D-2 + D-3 closed in §1.)

---

## 12. Summary of named decisions (owner-readable)

| Decision | Recommendation | Why it matters |
|---|---|---|
| D-1 — F-LEAK off-limits source | Survey markdown §10 + extended default skip-list | Survey is canonical; default extension covers no-survey case; best-effort parser never blocks |
| D-2 — F-VERIFY-ORPHAN cascade-drop vs remap | Cascade-drop with multi-`serves` retention | Simplest correct shape; multi-`serves` partial retention preserves information when one obj survives; halt-and-surface if observed drop rate ≥50% |
| D-3 — F-TIMEOUT default | Raise default 180s → 600s; `--synthesis-timeout` override | 3.3x headroom on F-LEAK-fixed prompts; operator can tune |

---

## 13. Halt-and-surface findings encountered during plan authoring

Per `feedback_subagent_odd_violation_halt`: halt and surface any
ODD violation observed in surrounding code/docs.

**(none observed during plan authoring.)** The `analyze.py`
`_walk_repo`, `synthesis.py` `_validate_rows`,
`claude_print_synthesis_client.py` ctor, and `cli.py` argparse
surface are all clean, outcome-scoped surfaces. The fix is local
to those four.

---

## 14. Method-decision record (builder, post-build)

The plan §11 left D-build.x method choices to the builder within the
ACs' outcome bounds. This section is populated post-build.

### D-build.1 — F-VERIFY-ORPHAN cascade-drop algorithm

Cascade-drop chosen over remap. Algorithm:

1. After both `_apply_band_demotion_guard` and
   `_apply_plausible_demotion_or_drop_guard` have run, compute
   `surviving_obj_ids = {row["objective_id"] for row in objectives_raw}`.
2. For each capability row in `capabilities_raw`:
   - Filter `serves` to `[ref for ref in serves if ref in
     surviving_obj_ids]`.
   - If filtered list is empty: drop the capability + WARN log.
   - Else: retain capability with filtered `serves`.

Rationale: simplest correct shape; multi-`serves` partial retention
preserves the capability when at least one objective survives;
single-`serves` no-survivor capabilities are precisely what the
verify stage was halting on. Cascade-drop happens parsing-side in
`_validate_rows` BEFORE per-row Pydantic validation; this preserves
the existing AC.OBJX.10 verify-stage strictness for genuinely
dangling references in static contract files (a verify run against
a manually-edited contract.yaml still raises StageError).

Alternative considered: remap dropped objective references to a
surviving sibling (same band / same evidence kind). Rejected
because (a) the LLM's intent in `serves` is opaque post-drop —
fabricating a remap is worse than dropping; (b) verify-stage
strictness is the design contract; cascade is the parsing-layer
concession, not a verify-layer relaxation.

### D-build.2 — survey-resolver lazy-import in analyze.py

`analyze_repo` lazy-imports `multi_source._read_user_survey` rather
than top-level importing. Rationale: `multi_source.py` already
imports the user-survey resolver via the same lazy-import pattern
(survey-parser is in `framework/workspace-bootstrap/` which is a
separate component); maintaining the lazy-import discipline avoids
a hard dependency in the analyze stage. Best-effort never-block-on-
parse-failure mirrors AC.ONBOARD.15 contract.

### D-build.3 — `_walk_repo` signature additive change

`_walk_repo(repo_path)` → `_walk_repo(repo_path, *, extra_skip_dir_names)`
with default empty frozenset. Keyword-only argument with default
preserves the AC.OREK.3 backward-compat surface. All existing
callers (analyze_repo, fixture-loader callers) continue to work
unchanged; the new caller in `analyze_repo` opts in.

### Test breakdown

- AC.V025-1.1 (off-limits skip): 8 tests — 4 parser unit + 1 static-
  list-extension + 1 const-presence + 2 integration (survey extra-
  skip + malformed-survey fallback).
- AC.V025-1.2 (synthesis-timeout): 5 tests — 2 ctor + 1 builder + 1
  CLI parse + 1 help-text.
- AC.V025-1.3 (cascade-drop): 4 tests — 1 cascade-drop + 1 multi-
  serves-filter + 1 helper-non-dict-passthrough + 1 verify-strictness.
- AC.V025-1.4 (rd-automation pipeline): 1 outcome-altitude integration
  test — 4-stage pipeline + F-LEAK regression assertion + F-VERIFY-
  ORPHAN regression assertion (skip-clean on missing claude / loam /
  rd-automation).

Net new tests: 18.

### Backwards-compat verification

- All sealed-AC tests pass post-corrective. Pre-existing OSS_M6
  collection errors + stochastic live-LLM failures verified non-
  regressions against pre-corrective HEAD f480edc (fail with same
  signature on the prior commit; not introduced by this corrective).
- `_walk_repo` signature shift is backward-compatible (new kwarg has
  default empty frozenset).
- `build_default_synthesis_client(timeout_seconds=None)` matches
  prior shape (None passes through to ctor default).
- `--synthesis-timeout` flag is additive on the CLI surface.

### Live verification — F-LEAK fix on rd-automation synthesis prompt

Mid-build process inspection of the live `claude -p` argv for the
rd-automation synthesis call confirmed ZERO occurrences of
html-capture filenames (`01-login-page-*.html`), ZERO `public/uploads/`
paths, ZERO `/logs/` paths, ZERO `test-results/` paths in the
synthesis prompt. The single occurrence of "screenshots" in the
prompt was narrative prose from the rd-automation README ("screenshots
and logs"), not a filename leak. F-LEAK fix verified live.

### Commit SHAs

- Amendment commit: `8130058b320ef592b8b4b4f0ec84bb43ae1f5833` —
  `docs(plans): v0.2.5.1 §14 D-build.{2,3} method-decisions + test breakdown`
- Seal commit: `b1d5f1e2a2966f03b07a076b89bd14fa670d4284` —
  `chore(seals): v0-2-5-1-corrective-leak-timeout-verify-orphan — dev-sdlc at 8130058`
## 15. References

- Eric run issues capture: `/Users/lukeivers/pos3/workspace/.scratch/claude-output/eric-run-issues-friday-processing.md`
- v0.2.5 corrective C6 plan-doc: `docs/plans/v0-2-5-corrective-c6-fixture-pm-and-extraction-resolution.md`
- AC.V025-C6.1 outcome-altitude precedent: `plugins/dev-sdlc/odd-extractor/tests/test_AC_V025_C6_1_full_pipeline_with_authored_pm.py`
- AC.ONBOARD.15 best-effort parser precedent: `framework/workspace-bootstrap/src/loam/workspace_bootstrap/survey_parser.py`
- `odd-test-altitude-discipline` SKILL: `plugins/dev-sdlc/skills/odd-test-altitude-discipline/SKILL.md`
- ODD lean grounding: `docs/odd-llm-grounding.lean.md`
