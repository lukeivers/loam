# v0.4.0 Cycle 1 — Code-gen-from-objectives core (FINALIZED)

**Status:** finalized at cycle-dispatch time per `plan-docs-author` SKILL master-vs-sub-plan trim discipline. Dispatched to background build agent.
**Slug:** `v0-4-0-cycle-1-code-gen-from-objectives-core`
**Date authored:** 2026-05-08 (stub) → finalized 2026-05-08 at dispatch.
**Parent master plan:** `docs/plans/v0-4-0-master-plan.md` §3 Cycle 1.
**Predecessor cycles:** N/A (first cycle of v0.4.0). Inherits v0.3.0 SHIPPED state at seal `3c6fdd5e` + v0.3.0.1-patch SHIPPED at seal `8569b727` (NOT pushed yet — local-only).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.

---

## §1 — Outcome shape (the "why")

C1 supplies the dispatch surface that consumes objectives.yaml + gap-inventory.yaml + build-next.yaml and emits a unified diff (or branch) where each commit carries an `objectives:` block per amendment #38 `lifted_from = {source_doc, source_ac, source_commit}` schema. This is the "loam stops scaffolding and starts shipping code" inflection — pre-C1 loam ends at planning input; post-C1 loam ends at working code attributable to its motivating objectives.

C1 ships SOFT-altitude only (synthetic-fixture smoke, no real `claude -p` subprocess). C2 closes outcome-altitude against the `jsts-playwright-app` canonical fixture with real `claude -p` invocation. The split keeps each cycle in the 1-3hr range per master plan §3 cycle decomposition rationale.

## §2 — Prime objective ladder

VALUE_PROPOSITION.md prime objective (loam helps people use LLMs to build software) → v0.4.0 release-roadmap §3 outcome (loam ships working code from extracted objectives) → AC.V040.1 (code-gen-from-objectives integration) → C1 ACs `AC.V040C1.*` below (SOFT-altitude core; AC.V040C1.5 outcome-altitude DEFERRED to C2 explicitly).

## §3 — Component fence

**PRIMARY (decided at dispatch):** **EXTEND** `plugins/dev-sdlc/odd-extractor/` rather than ship a NEW `plugins/dev-sdlc/code-gen/` component. Rationale verified at dispatch:

- The `loam odd-extract <repo> --build-next` CLI surface already exists at `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/cli.py` line 431 (`_cmd_build_next` at line 679).
- `BuildNextRecommendation` schema already shipped at `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/spec.py:944`.
- Subscription-routed LLM client (`claude_print_synthesis_client.py`) already exists in the same package — no new wrapper to author.
- The cycle's deliverable is "consume build-next.yaml + emit code-gen diff," which is the natural successor stage after build-next ranking. New `code-gen/` component would duplicate the package boundary.

**Concretely.** New module: `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/code_gen.py`. CLI flag: `loam odd-extract <repo> --code-gen` (mirrors `--build-next` shape; the agent may name a different invocation if a tighter UX is found — AC bounds the outcome). New tests under `plugins/dev-sdlc/odd-extractor/tests/test_AC_V040C1_*.py`.

**Read-only:**
- `framework/objective-tracker/src/loam/objective_tracker/spec.py` — consume `LiftedFrom` schema (line 236) directly via import.
- `framework/memory-system/` — no writes.
- All other framework components — sealed.

**Universal admissions:** `docs/plans/v0-4-0-cycle-1-code-gen-from-objectives-core.md` (this file), pos-amend manifest at `docs/plans/v0-4-0-cycle-1-code-gen-from-objectives-core.vars.yaml` (or equivalent), seal narrative.

## §4 — AC family `AC.V040C1.*` (TIGHTENED at dispatch)

Each AC maps to ≥1 test under `plugins/dev-sdlc/odd-extractor/tests/test_AC_V040C1_*.py`. The agent authors test names within this convention.

### AC.V040C1.1 — Code-gen dispatch surface exists

A loam-CLI invocation (named `--code-gen` flag on `odd-extract` or successor name the agent chooses; see `decisions remaining`) accepts an extraction directory containing `objectives.yaml` (or `augmented-objectives.yaml`) + `gap-inventory.yaml` + `build-next.yaml`. Invocation produces a unified diff or branch as a persisted artefact. The CLI flag is registered in argparse + manifest entries; help-text describes the deliverable shape.

`outcome-altitude: false` (CLI registration; method-altitude).

### AC.V040C1.2 — Per-commit `objectives:` block populated per amendment #38 schema

Each emitted commit in the produced diff (or branch) carries an `objectives:` block in its commit-message footer (or equivalent persisted carrier — git trailer / structured commit body) populated with the amendment #38 `LiftedFrom` schema fields: `source_doc`, `source_ac`, `source_commit` (where `source_commit` may be null at C1 since the source-commit is the not-yet-existent commit being authored — the agent rules on whether `source_commit` is omitted, set to a placeholder like `null`, or populated post-write at C1 plan-doc-author time). The block round-trips through Pydantic `LiftedFrom.model_validate` cleanly.

Single-commit case verified at C1. Multi-commit case attempted; if scope expands, surfaced as F2 RF for C2 or v0.4.1 patch.

`outcome-altitude: false` (schema-population; method-altitude).

### AC.V040C1.3 — SOFT-altitude smoke vs synthetic fixture (no real `claude -p`, no real codebase)

A test file `test_AC_V040C1_3_soft_smoke.py` invokes the code-gen entry-point against a synthetic fixture under `plugins/dev-sdlc/odd-extractor/tests/fixtures/code-gen/synthetic-v0/` (NEW directory the agent creates). Fixture seed: a small objectives.yaml (1-3 objectives) + gap-inventory.yaml (1-2 gaps) + build-next.yaml (1 candidate). LLM dispatch is **stubbed via duck-typed `messages.create()` returning a controlled diff** — same stub-mode contract `claude_print_synthesis_client.py` documents (`Skip semantics: callers that want to test without a live claude binary must inject a stub directly`). Test asserts:
1. Entry-point produces a non-empty diff/branch artefact.
2. Each commit's `objectives:` block validates via `LiftedFrom.model_validate`.
3. `lifted_from.source_doc` matches the source objective's origin doc.
4. `lifted_from.source_ac` matches the source build-next candidate's gap-id-derived AC reference.

`outcome-altitude: true` BUT against synthetic fixture only — C2's AC.V040C2.* closes the real-world outcome-altitude requirement with real `claude -p` + real `jsts-playwright-app` fixture.

### AC.V040C1.4 — No regression in pre-existing odd-extractor / framework test suites

`pytest plugins/dev-sdlc/odd-extractor/tests/` returns 0 with the pre-existing test count (verify via `git diff --stat` pre-vs-post-build that no pre-existing test was edited). Per amendment-dispatch-speedups: skip pre-seal full-repo rerun; cross-component seal-diff is verified by `pos-amend apply --dry-run` green.

`outcome-altitude: false` (no-regression invariant).

### AC.V040C1.S — Seal-diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` shows changes only under:
- `plugins/dev-sdlc/odd-extractor/` (source + tests + fixtures),
- `docs/plans/v0-4-0-cycle-1-*` (this plan + manifest),
- universal-paths admissions (CLAUDE.md, docs/odd-in-pos.md, docs/odd-methodology.md, docs/FUTURE_IDEAS.md if surfaced).

Anything outside that set is a halt condition.

### AC.V040C1.5 (outcome-altitude) — DEFERRED to C2

Per master plan §3 cycle-1 / cycle-2 split rationale: outcome-altitude verification against real `claude -p` subprocess + real-world fixture (`jsts-playwright-app`) is C2's exclusive responsibility. C1 explicitly does NOT close this AC. C1's plan-doc names the deferral; C2's plan-doc names the closure.

`outcome-altitude: true` BUT scope-deferred to C2 (master-plan-altitude split is intentional per Lens 5 stopping criterion + halt-trigger §8.1).

## §5 — Build dispatch brief

Built inline by dispatcher at dispatch time per `dispatch-brief-authoring` SKILL — see Telegram-context-doc / orchestrator dispatch.

## §6 — Hard constraints

1. **No `--amend`.** Corrective commits are NEW commits. Streak intact (C5 had inadvertent --amend; C6/C6.1/v0.3.0/smoke/C7/v0.3.0.1 all stayed clean).
2. **Scope fence — `plugins/dev-sdlc/odd-extractor/` + universal-paths only.** Source edits outside fence = halt.
3. **No Anthropic API key, no `pip install anthropic`.** All LLM calls (where exercised; C1 does NOT exercise live LLM calls per AC.V040C1.3 stub-mode) route through `claude -p` subprocess via the existing `claude_print_synthesis_client.py` wrapper. C1 codepath that *would* invoke the LLM lives behind the same shim — sealed by AC.V040C1.3's stub-injection contract.
4. **`--strict-mcp-config` invariant.** When the code-gen path *does* invoke `claude -p` (which C1's stub-mode does NOT, but the code-path being stubbed must) the invocation passes `--strict-mcp-config` + an empty MCP config tempfile per the v0.2.5 C5 propagation invariant (AC.WSα.8 precedent).
5. **No new runtime deps.** Pydantic + pyyaml + the existing odd-extractor dep set already pinned. No new pyproject.toml dependency lines.
6. **`pos-amend apply --dry-run` green** is a hard prereq + hard post-apply gate.
7. **No public action.** No `git push`, no `git tag`, no GitHub Release. v0.4.0 SHIPS as a unit at C5 with owner ratification.
8. **Reuse amendment #38 `LiftedFrom` schema by import.** Do NOT re-author the schema. Import directly from `framework/objective-tracker/src/loam/objective_tracker/spec.py`.
9. **Plan-before-code.** The build agent writes its own builder-plan to `docs/plans/v0-4-0-cycle-1-code-gen-from-objectives-core.builder-plan.md` (or equivalent) BEFORE touching source.
10. **ODD §2.5 + §2.4.** Every line of code maps to a named AC. No method-in-AC. No "options to rule on" framing for methodology-answered questions.

## §7 — Out of scope (explicit)

- Outcome-altitude verification against real `claude -p` + real `jsts-playwright-app` fixture (C2).
- Routines runtime layer (C3); Code Review composition (C3); Outcomes-pattern ADR (C3).
- ProgramBench v0 run (C4).
- Multi-fixture verification beyond synthetic + (deferred) jsts-playwright-app.
- Schema widening on `objective-tracker` (sealed component; widening is a separate amendment).
- `loam status` background-work-inventory primitive (harness-landscape RR.1).
- Live `claude -p` subprocess invocation (C2; C1 stubs the call site).
- BYOK / multi-provider (subscription-only architectural floor; out of v0.4.0 entirely).

## §8 — Halt triggers

1. Cross-component scope expansion beyond `plugins/dev-sdlc/odd-extractor/`. Halt + surface.
2. AC.V040C1.* count grows beyond 5 (excluding `.S`). ODD §2.5 violation triage; halt.
3. Multi-commit `objectives:` block case is structurally infeasible at C1 (e.g., the per-commit carrier shape conflicts with git's commit-message format). Halt; surface for owner ruling on whether to defer to C2 or v0.4.1 patch.
4. Synthetic fixture's "soft" verdict diverges so far from production that C2's outcome-altitude verification will obviously fail (e.g., the stub returns a hard-coded diff that bears no resemblance to what real `claude -p` would produce). Halt; surface for C1 redesign.
5. Any reach for `--amend`, `git push`, or `git tag`. Immediate halt; corrective NEW commit + RF surface.
6. Subscription-only constraint violated (any new `import anthropic`, any new `ANTHROPIC_API_KEY` env reference). Immediate halt.
7. AI-time exceeds upper band (240 min) by >50% → 360 min wall-clock. Halt with current state; surface for owner ruling on split vs push-through.
8. ODD §2.5 violation discovered in surrounding code (subagent-must-halt-on-ODD-violations). Halt + surface; do NOT silently extend.

## §9 — Dependencies

- Master plan §3 (parent authority).
- Amendment #38 `LiftedFrom` schema (sealed; consumed read-only).
- v0.2.5 C5 `claude -p --strict-mcp-config` invariant (consumed read-only via `claude_print_synthesis_client.py`).
- v0.2.4 C3 build-next ranking surface (consumed; this cycle is the natural successor stage).
- No predecessor cycles within v0.4.0 (first cycle).

## §10 — F2 RF gaps to surface during build

- **Multi-commit `objectives:` block case.** The amendment #38 `LiftedFrom` schema is per-record; whether each commit in a multi-commit diff inherits the same `lifted_from` from the originating build-next candidate, OR each commit names its own `lifted_from` (e.g., "this commit closes AC.X; the parent commit closes AC.Y"), is an open question. C1 plan-doc verifies single-commit; multi-commit may surface a methodology amendment for C2 or v0.4.1 patch.
- **`source_commit` value at code-gen time.** The commit being authored does not yet have a SHA when the `objectives:` block is being drafted. Three reasonable shapes: (a) omit `source_commit` from the block at write time; (b) set it to `null`; (c) populate post-write via a post-commit hook that rewrites the message. Builder's call within scope; surface rationale in §14.
- **Synthetic fixture vs real-`claude -p` divergence.** A controlled stub by definition produces a controlled diff. C2's outcome-altitude verification will discover divergences. The C1 dispatch trusts that the *interface contract* between code-gen and the stubbed LLM is the same one C2 will exercise live; if interface drift is discovered at C2, NEW corrective commits in C2's cycle (NOT C1 retroactive amendment).
- **Code-gen prompt shape.** The prompt the production code path *would* send to `claude -p` (had C1 been live) needs to be representative enough that C2's live invocation isn't a surprise. Builder authors a representative prompt in code (not in the stub); the stub intercepts it.

## §11 — Provenance trail

- `docs/plans/v0-4-0-master-plan.md` §3 Cycle 1 — parent authority.
- `docs/release-roadmap.md` §3 v0.4.0 AC.V040.1 — root authority.
- `docs/plans/amendment-38-objective-tracker-schema-widening.md` §14 — `LiftedFrom` schema specification + commit SHA `be7737bb`.
- `framework/objective-tracker/src/loam/objective_tracker/spec.py:236` — `LiftedFrom` Pydantic class.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/build_next.py` — predecessor stage (build-next ranking).
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/spec.py:944` — `BuildNextRecommendation` schema (consumed input).
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/claude_print_synthesis_client.py` — subscription-routed LLM client wrapper (consumed; not edited at C1).
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/cli.py:431,679` — predecessor CLI surface integration point.
- `plugins/dev-sdlc/odd-extractor/tests/fixtures/build-next/high-priority-match/` — synthetic-fixture shape precedent.
- `feedback_no_anthropic_api_key.md` — subscription-only constraint.
- `feedback_test_outcome_altitude_required.md` — outcome-altitude AC requirement (deferred to C2 per master plan §3 split rationale).
- `plugins/dev-sdlc/skills/dispatch-brief-authoring/SKILL.md` — dispatch-brief shape.
- `plugins/dev-sdlc/skills/plan-docs-author/SKILL.md` — sub-plan-doc trim discipline.

## §12 — Bookkeeping (`pos-amend` manifest stub)

```yaml
schema_version: 1
amendment:
  number: v0-4-0-cycle-1
  slug: v0-4-0-cycle-1-code-gen-from-objectives-core
  title: "v0.4.0 Cycle 1 — code-gen-from-objectives core (SOFT smoke vs synthetic fixture)"

baseline: <captured-at-dispatch>  # immediate-prior commit at apply time
plan: docs/plans/v0-4-0-cycle-1-code-gen-from-objectives-core.md

components:
  - name: dev-sdlc
    seal_test: plugins/dev-sdlc/tests/test_no_sealed_amendments.py  # or component-equivalent
    sidecar: plugins/dev-sdlc/tests/SEAL_COMMIT
    frozen_baseline: false
    extra_allowed_prefixes:
      - plugins/dev-sdlc/odd-extractor/

universal_paths:
  prefixes:
    - docs/plans/
  files:
    - CLAUDE.md
    - docs/odd-in-pos.md
    - docs/odd-methodology.md
    - docs/FUTURE_IDEAS.md

narrative:
  target: plugins/dev-sdlc/odd-extractor/seals/SEAL_COMMIT.v0-4-0-cycle-1-code-gen-from-objectives-core
  body: |
    # v0.4.0 Cycle 1 — Code-gen-from-objectives core
    # Body authored at seal time. Describes:
    #  - new code_gen.py module + CLI integration on odd-extract --code-gen flag;
    #  - per-commit objectives: block populated from amendment #38 LiftedFrom schema;
    #  - SOFT-altitude smoke against synthetic fixture (stub-injected LLM client);
    #  - OUTCOME-ALTITUDE deferred to C2 per master plan §3 split rationale;
    #  - subscription-only LLM path preserved through claude_print_synthesis_client.py.
```

## §13 — Decisions remaining for the build agent

The following items remain method-level builder choices within this scope.

- **D-build.1 — CLI flag name.** Three reasonable shapes: (a) `loam odd-extract <repo> --code-gen` (mirrors --build-next; minimal new surface); (b) `loam odd-extract <repo> --build-next --emit-code` (composed flag onto the predecessor stage); (c) `loam build-next-emit <repo>` (new top-level subcommand). **Dispatcher recommendation:** (a) — the smallest CLI surface that closes AC.V040C1.1. Builder may select (b) or (c) with rationale recorded in §14.
- **D-build.2 — `source_commit` value at code-gen time.** Three reasonable shapes: (a) omit field from the block (LiftedFrom permits `source_commit: None`); (b) set to literal `null`; (c) populate post-write via a follow-up rewrite. **Dispatcher recommendation:** (a) — simplest; LiftedFrom already supports the `None` default. Builder may select (b) or (c) with rationale.
- **D-build.3 — `objectives:` block carrier in commit message.** Two reasonable shapes: (a) git trailer (`Objectives: <yaml-inline>`); (b) structured commit-message body section with a clear delimiter (e.g., `\n---objectives---\n<yaml>\n---`). **Dispatcher recommendation:** (b) — git trailers are line-bounded; YAML is multiline. Builder may select (a) with a workaround or (b).
- **D-build.4 — Synthetic-fixture seed objectives.** Builder selects 1-3 small objectives from existing fixture library (`build-next/high-priority-match/` is the closest precedent at 3 objectives). Builder may copy/adapt or author from scratch. AC.V040C1.3 measures the outcome.

These are surfaced to make the dispatch brief tighter; they are NOT blockers. Builder records choices in §14.

## §14 — Method-decision record (builder, post-build)

To be filled in by build agent post-seal. Section structure mirrors amendment #38 §14: D-build.1 through D-build.4 choices + rationale, test breakdown (file list + counts), commit SHAs (apply, seal, plan-update).

### Post-seal SHA register

| Commit | SHA |
|---|---|
| Plan-doc finalize commit | (pending; lands in apply) |
| Source-edit commit | (pending) |
| Apply commit | (pending) |
| Seal commit | (pending) |
| §14 backfill commit | (pending) |
