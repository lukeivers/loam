# v0.4.0 Cycle 2 — Code-gen outcome-altitude verification on `jsts-playwright-app`

**Status:** finalized at dispatch time per `plan-docs-author` SKILL trim discipline.
**Slug:** `v0-4-0-cycle-2-code-gen-outcome-altitude-verification`
**Date authored:** 2026-05-08 (stub); finalized 2026-05-08 at dispatch.
**Parent master plan:** `docs/plans/v0-4-0-master-plan.md` §3 Cycle 2.
**Predecessor cycle:** Cycle 1 sealed at `cc2efbba` (LOCAL; predecessor source-edit `b59a228d`, apply `a7d1182b`).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.

---

## §1 — Outcome shape (the "why")

C1 ships SOFT-altitude code-gen against synthetic fixtures: `--code-gen`
flag, `_cmd_code_gen` handler, `generate_code()` + `persist_diff()`,
per-commit `objectives:` block per amendment #38 LiftedFrom schema.
That's necessary but insufficient for the END-USER class quality gate.
Per `feedback_test_outcome_altitude_required.md` + master plan §3
AC.V040.6: the outcome AC must invoke the production CLI against a
real fixture with the real `claude -p` subprocess, no monkeypatch.

C2 closes that requirement against `jsts-playwright-app` — the same
canonical fixture v0.1.8 → v0.2.5 used to verify the JS/TS adapter +
multi-source synthesis pipeline. Cycle ACs go green at outcome
altitude (not just synthetic-altitude) so the v0.4.0 release gate
doesn't surface defects the cycle ACs missed.

C2 also folds in the C1 build report's five F2 RF findings: F1
(multi-commit shape), F2 (redundant local seal-diff test), F3
(`_resolve_source_doc` fallback), F4 (live-LLM tests in full suite),
F5 (stub-vs-live divergence).

## §2 — Prime objective ladder

`docs/VALUE_PROPOSITION.md` prime objective → v0.4.0 §3 outcome →
AC.V040.1 (close fully) + AC.V040.6 (outcome-altitude requirement
against real fixture) → C2 ACs below.

## §3 — Component fence

PRIMARY: outcome-altitude test at
`plugins/dev-sdlc/odd-extractor/tests/test_AC_V040C2_1_outcome_altitude.py`.

Secondary:
- `jsts-playwright-app` fixture (read-only). Verified at dispatch
  pre-time; shape unchanged since v0.1.8 sealing per
  `tests/fixtures/jsts-playwright-app/README.md`.
- C1 code-gen surface (`code_gen.py`, `cli.py`) — UNIVERSAL ADMISSION
  for prompt-shape adjustments needed to make outcome-altitude pass;
  NEW commits only (no `--amend`).
- F2 cleanup: delete `tests/test_AC_V040C1_S_seal_diff.py` (redundant
  per C1 build report F2; dev-sdlc parent owns the seal-diff
  invariant via `plugins/dev-sdlc/tests/test_no_sealed_amendments.py`).

Read-only: `framework/`, sealed `objective-tracker`, sealed v0.1.8 /
v0.2.3 / v0.2.5 surface.

## §4 — AC family `AC.V040C2.*`

- **AC.V040C2.1** — Outcome-altitude probe: a test invokes the full
  production chain (`loam odd-extract <repo> --live` → `--interview`
  → `--gaps` → `--build-next` → `--code-gen`) against a clone of
  `jsts-playwright-app`, with the real `claude -p` subprocess in
  every LLM-routed stage. NO monkeypatch of `messages.create()`,
  `subprocess.run`, the binary, or any client constructor. Skips
  cleanly when `claude` or `loam` is not on PATH. **`outcome-altitude:
  true`**.
- **AC.V040C2.2** — Subscription-only invariant preserved: AST-walk
  of `code_gen.py` (and any C1 corrective code added in this cycle)
  shows zero `import anthropic` / `from anthropic import …`; zero
  references to `ANTHROPIC_API_KEY` outside docstrings. The C1
  AC.V040C1.3 AST-walk test (already green) is the binding probe;
  C2 verifies no C2 corrective regresses it. The production wiring
  uses `ClaudePrintAnthropicShimClient` from
  `claude_print_synthesis_client` — `--strict-mcp-config` + empty
  MCP-config tempfile invariant per the v0.2.5 C5 propagation.
- **AC.V040C2.3** — Multi-commit `lifted_from` shape verification:
  if real `claude -p` against jsts-playwright-app produces a
  multi-commit response, the test asserts each commit's
  `lifted_from` populates correctly. If real output produces
  single-commit (the common case for one build-next candidate
  closing one gap), the test asserts single-commit shape and the
  multi-commit verification **defers to C3-or-later** with a
  documented rationale: the schema (`CodeGenDiff.commits` is
  `tuple[CodeGenCommit, ...]` of length ≥1) supports multi-commit;
  whether the prompt should produce multi-commit is a separate
  methodology question (one build-next candidate → one commit is
  the v0.4.0 baseline). Closes C1 build-report F1.
- **AC.V040C2.4** — `_resolve_source_doc` fallback verified against
  real fixture: the test asserts `commit.lifted_from.source_doc`
  contains the resolved objective_id (`O.<...>` pattern) AND the
  `source` field (e.g., `extracted`). If real ODD-extracted
  objectives carry richer source pointers in future, schema
  widening is a separate amendment (out of C2 scope per master
  plan §6 stance: "consume objective-tracker schema; don't
  widen"). Closes C1 build-report F3.
- **AC.V040C2.5** — Sub-component-local seal-diff test removed:
  `tests/test_AC_V040C1_S_seal_diff.py` deleted (redundant per
  C1 build report F2; dev-sdlc parent owns the sidecar +
  seal-diff invariant via `test_no_sealed_amendments.py`).
- **AC.V040C2.6** — No regression: pre-existing C1 + earlier-cycle
  tests still pass on the C2-built tree. Subset rerun across the
  C1 AC test set + the new C2 outcome-altitude test must be all
  green; full odd-extractor suite skipped per
  `feedback_amendment_dispatch_speedups` (full pre-seal rerun
  not required).

### Note on C1 build report F4 (live-LLM tests in full suite)

F4 surfaces an operational risk for future CI integration: existing
odd-extractor tests that invoke real `claude -p` hang the full suite.
**C2 disposition:** out of C2 scope (no test-runner discipline
amendment in this cycle). The C2 outcome-altitude test follows the
same skip-by-default-locally pattern (`pytest.skip` when `claude` /
`loam` absent on PATH) that the v0.2.5 outcome-altitude tests
established. Surfaced for owner ruling on whether the full-suite
hang itself warrants a v0.4.1 patch or stays a v0.5.0+ test-runner
amendment surface.

### Note on C1 build report F5 (stub-vs-live divergence risk)

F5's whole point: C2 IS the closing of the gap. If real `claude -p`
output differs from the stub's controlled-diff shape (e.g., the LLM
wraps the diff in markdown fences, omits the `subject:` prefix,
returns content in `content[N>0]` blocks), the test will fail.
Disposition: in-cycle correctives (NEW commits, no `--amend`) to
`code_gen.py`'s `_parse_llm_response` or `_build_prompt` — whichever
is cheaper and less invasive. If divergence is structural (real
output simply cannot be coerced into the contract C1 fixed), surface
as F-DESIGN-1 and recommend C1 redesign vs C2-redesign vs C3-reframe.

## §5 — Constraints

1. Subscription-only via `claude -p` — NO `ANTHROPIC_API_KEY`, NO
   `import anthropic`. AC.V040C2.2.
2. No monkeypatch of LLM dispatch path in the outcome-altitude test
   (it's the whole AC). Stub-injected unit tests stay; outcome
   probe MUST exercise the real subprocess.
3. C1 surface is universal admission for in-cycle correctives.
   Other components stay read-only.
4. NEW commits only — no `git commit --amend`,
   `git rebase --interactive`, force-push.
5. NO `git push`, NO `git tag`, NO `gh release`. v0.4.0 ships at C5.
6. Method follows ODD §2.5 — every line of test code maps to a named
   AC; no off-AC code.

## §6 — Smoke

D2 steady-state: outcome-altitude test passes when `claude` + `loam`
are both on PATH. D1 cold-state: fresh clone of fixture per test
invocation. D5 / D6 not applicable (single-run code-gen verification).

## §7 — Out of scope

- Multi-fixture verification (rd-automation-class targets stay
  v0.5.0+).
- ProgramBench v0 run (C4).
- Behavioral test pass-rate scoring across many tasks (C4 territory).
- Fixture's `npm test` execution (the fixture's README states
  `npm install && npm test` will not work — it's a shape-only
  fixture, no real implementation behind the surface). The
  AC.CGV.4 behavioral pass-rate assertion proposed in the C2 stub
  was infeasible against this fixture — re-shaped at AC.V040C2.1
  to assert structural shape (unified-diff markers + git-apply
  parseability) instead. ProgramBench Variant A (C4) is where
  behavioral pass-rate scoring actually lives.
- Multi-commit prompt redesign (deferred per AC.V040C2.3).
- Test-runner discipline amendment for full-suite hang (C1 F4
  defers).
- Schema widening for richer `source_doc` provenance (C1 F3 defers
  to v0.4.1 or later).

## §8 — Halt triggers

1. Real `claude -p` invocation fails for unrelated reason (auth,
   MCP config, network) — surface root cause; don't continue
   building until reachable.
2. WD mismatch — `pwd` ≠ `/Users/lukeivers/ivers-corp-pos-v2`.
3. Real-output shape so divergent from C1's `_parse_llm_response`
   contract that no minimal corrective recovers — surface as
   F-DESIGN-1 with C1-corrective vs C1-redesign options.
4. Subscription-only invariant violation in any test or C1
   corrective — immediate halt.
5. Reach for `git commit --amend`, `git push`, or `git tag` —
   immediate halt; corrective NEW commit + RF surface.

## §9 — F2 RF gaps surfaced at dispatch

1. **`jsts-playwright-app` is shape-only — `npm test` will not
   work.** The C2 stub's AC.CGV.4 ("diff compiles + lints + passes
   existing fixture's test surface") was infeasible against this
   fixture; the stub conflated outcome-altitude (the diff comes
   from real `claude -p`) with behavioral-pass-rate scoring (the
   diff actually closes the gap). Re-shaped: AC.V040C2.1 verifies
   structural-altitude (real `claude -p` + parseable unified diff
   + populated `objectives:` block); behavioral pass-rate scoring
   moves to C4 ProgramBench (where the fixtures are real runnable
   tasks).
2. **Pre-arrangement rubric for the chain test.** The test runs
   `--live → --interview → --gaps → --build-next → --code-gen`
   in-test. Per pre-arrangement detection rubric: state IS produced
   by the production code under test (not pre-arranged); each chain
   stage IS a production stage. Verdict: outcome-altitude probe is
   correctly shaped per `odd-test-altitude-discipline` SKILL.
3. **Cost ceiling for live `claude -p` chain.** A single chain run
   on jsts-playwright-app spans 2-4 LLM calls (analyze → generate
   synthesis pass; `--build-next` may invoke an LLM judge depending
   on candidate-count; `--code-gen` is one call). Existing v0.2.5
   pipeline tests use `--budget-cents 500` ($5 ceiling per stage).
   C2 reuses that ceiling. Real cost at Max-subscription is $0
   (envelope reports `total_cost_usd=0` per
   `claude_print_synthesis_client` design).
4. **Stochasticity:** `claude -p` is stochastic. The test asserts
   on structural shape (parseable unified diff, populated
   `objectives:` block, valid `lifted_from`) — properties stable
   across stochastic variation. The test does NOT assert on
   commit subject text or specific diff hunks (those vary).

## §11 — Provenance trail

Master plan §3 Cycle 2; release-roadmap §3 v0.4.0 AC.V040.1 +
AC.V040.6; `docs/odd-llm-grounding.lean.md` §"Outcome-altitude AC
requirement"; `plugins/dev-sdlc/skills/odd-test-altitude-discipline/SKILL.md`
(pre-arrangement rubric); `feedback_test_outcome_altitude_required.md`;
v0.1.8 / v0.2.3 / v0.2.5 jsts-playwright-app fixture sealing history;
v0.2.5 corrective C4-pivot (`claude_print_synthesis_client`); v0.4.0
Cycle 1 build report (5 halt-and-surface findings folded in here).

## §13 — Builder method-decisions

| Decision | Choice | Rationale |
|---|---|---|
| D-V040C2.1 — AC.CGV.4 behavioral assertion | Replaced with structural-shape assertion (parseable unified diff + populated objectives: block) | jsts-playwright-app is shape-only; `npm test` will not work. Behavioral pass-rate scoring is C4 ProgramBench territory. |
| D-V040C2.2 — Test invocation shape | Subprocess via `loam` binary (mirrors `test_AC_V025_C6_1_*`) | Production CLI invocation matches outcome-altitude rubric; in-process `cli.main()` would still be production-altitude but subprocess matches the user's actual invocation shape. |
| D-V040C2.3 — Multi-commit verification | Defer to C3-or-later if real output is single-commit | One build-next candidate → one commit is the v0.4.0 baseline; multi-commit prompt is a separate methodology question. Closes C1 F1. |
| D-V040C2.4 — F4 disposition (live-LLM tests hang full suite) | Out of C2 scope; surface for v0.4.1 or v0.5.0+ test-runner amendment | C2's job is closing AC.V040.6, not test-runner discipline. The new C2 test follows skip-by-default-locally; doesn't widen the existing surface. |
| D-V040C2.5 — Schema-widening for richer `source_doc` | Out of C2 scope | C1 F3 defers; widening sealed objective-tracker spec breaks read-only invariant. AC.V040C2.4 verifies the current fallback is meaningful on real fixture. |
| D-V040C2.6 — Stochasticity tolerance | Test asserts on structural shape only (parseable diff, valid LiftedFrom); not subject text or specific hunks | `claude -p` is stochastic; structural properties are stable. |
| D-V040C2.7 — F2 cleanup | Delete `test_AC_V040C1_S_seal_diff.py` | Per C1 F2; dev-sdlc parent owns sidecar; local test was always-skip-by-design. |

### Post-seal SHA register

| Commit | SHA |
|---|---|
| Source-edit commit | (pending) |
| Apply commit | (pending) |
| Seal commit | (pending) |
| §14 backfill commit | (deferred to v0.4.0 ship) |
