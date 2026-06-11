> **RETIRED-PROVENANCE BANNER 2026-06-11.** ProgramBench was fully
> retired by owner ruling (Discord 1514747695972094165; plan
> `docs/plans/programbench-full-retirement.md`). The pos3 experiment-scaffold paths
> referenced herein (`…/experiments/programbench-derivative/…`) are
> historical provenance / migration-source addresses for the GENERIC
> binary-extraction capability this plan proposes — no ProgramBench
> benchmark work is current or future work, and no PB fixture is to be
> used in any build off this plan.

# Promote multi-channel extractor + iteration-loop family into canonical loam — plan

**Slug:** `promote-multi-channel-extractor-and-iteration-loop-family`.
**Date authored:** 2026-05-11.
**Status:** PLAN-ONLY. Plan-before-code per `feedback_plan_before_code`. Owner ratification PENDING on §11 open questions. This document scopes a **future** sealed-component amendment build; it is not itself a sealed amendment, and it does not touch canonical loam code. Once §11 is ruled, a follow-on plan-doc with manifest + AC ladder + builder-cycle fence will dispatch the build.
**Class proposal:** MINOR (new outcome shape — loam can extract from binary executables and run iteration-loop verification against compile success). Version number deferred to build-commence-time per §6.0 roadmap convention. Maps onto the §4 v0.7.0-placeholder ("Loam builds software from minimal input") entry's AC.V050.1 + AC.V050.2 + AC.V050.3 surface.
**Predecessor work (canonical):** v0.4.0 code-gen (`plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/code_gen.py`); v0.4.1 + v0.4.2 closures (multi-commit + from-scratch + test-interface load-bearing); v0.2.3 multi-source bundle (`plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/multi_source.py`). The promotion extends this surface with **binary-channel inputs** + **iteration-loop verification**, not a parallel system.
**Predecessor work (experiment scaffold — to be migrated, not edited in place):**
- `~/pos3/workspace/experiments/programbench-derivative/harness/binary_interrogate.py` — 425 lines, three subprocess channels + vacuous-README detector.
- `~/pos3/workspace/experiments/programbench-derivative/harness/continuum_extract.py` — extends the prose extractor with `binary_path` parameter + provenance threading.
- `~/pos3/workspace/experiments/programbench-derivative/harness/compile_loop.py` — 430 lines, iteration-loop substrate (compile + retry + cap + telemetry).
- `~/pos3/workspace/experiments/programbench-derivative/harness/extract_empty_loop.py` — sibling iteration-loop (extraction-empty verifier), under parallel build.
**Working directory for the future build:** `/Users/lukeivers/loam/`.
**Empirical evidence the patterns work:**
- Multi-channel extractor: csview 0% → 27.2% mean; gron variance 23pp → 2.2pp; htmlq saturated at ~75% (4-step synthesis 2026-05-11).
- Compile-loop: yj 0% → 37.3%; csview 27.2% → 37.6%; ~17% token overhead; 0 exhaustions across 5 generations (Step 4 partial benchmark).
- Full evidence: `~/pos3/workspace/.scratch/claude-output/4-step-plan-synthesis-2026-05-11.md`; `~/pos3/workspace/.scratch/claude-output/step-1-extraction-fix-build-2026-05-11.md`; `~/pos3/workspace/.scratch/claude-output/step-3-compile-loop-build-2026-05-11.md`; `~/pos3/workspace/.scratch/claude-output/phase-4-b-deeper-extraction-analysis-2026-05-11.md`.

---

## §1 — Outcome shape (the "why")

Loam today consumes one input channel for ODD extraction (README/docs/source patterns/tests/survey — all prose-or-symbol). When a user hands loam a binary they want reproduced and the README is incomplete or vacuous, loam's extractor has no path to the binary itself — it HALTs (correctly, per persona discipline) on zero objectives. ProgramBench's framing names this directly: *"Given only a compiled binary AND its documentation, AI agents must architect and implement a complete codebase."* — two inputs, not one. The current extractor is single-input on a two-input task.

Separately, loam's code-gen surface (v0.4.x) produces files in one shot. When the model emits code that doesn't compile, loam has no feedback loop — the broken submission is the final submission. This is an iteration-deficit failure mode that's already been observed empirically (yj 0% in baseline because of unused-import errors in Go) and has a cheap recoverable verifier (`compile.sh; echo $?`).

The promotion closes both gaps as a single MINOR:

1. **Binary-channel extractor** — `odd-extract` accepts `--binary <path>`; three subprocess channels (help, version, strings) feed the existing multi-source bundle as labeled design-doc entries with provenance threading. The vacuous-README unblock rule lets the extractor proceed when the README is empty but the binary is interrogable. The output is unchanged in shape — typed objectives with `provenance` field naming the source channel(s) — so downstream `code_gen` / `gap-inventory` / `build-next` see binary-sourced objectives identically to README-sourced ones, with the channel surface available for confidence-weighting (FIDRAFT F-EXTRACT-CONVERGE).

2. **Iteration-loop family substrate** — a generic verifier-loop primitive: given a candidate submission + a verifier function (compile.sh exit code; extraction-non-empty; future verifiers), iterate up to N times, feeding the verifier's failure signal back as retry context, capping spend, telemetering per attempt. Compile-loop is the first verifier in the family; extraction-empty-loop is the second. The substrate is verifier-pluggable, not compile-specific.

After the promotion lands:

- A user with a binary + a stub README can run `loam odd-extract <repo> --binary <path>` and reach a populated objectives.yaml that names the binary's documented flag surface, value enums, defaults, and error templates.
- A code-gen run that emits non-compiling code self-recovers within a bounded retry budget rather than shipping a broken submission.
- The two surfaces compose: binary-extraction populates objectives → code-gen produces a submission → compile-loop verifies → output is a working submission grounded in the binary's actual behavior.

This ladders up to AC.V100.1 (all documented features work as advertised) by making loam's code-gen pipeline empirically converge on the "reproduce this binary" shape that the v0.7.0-placeholder roadmap entry names.

---

## §2 — Prime-objective ladder

```
VALUE_PROPOSITION.md prime objective
  └─ "translation layer between user's natural-language intent
      and AI-effective execution"
      └─ User says "reproduce this binary" → loam produces a working
         submission without the user understanding ODD / extraction
         channels / iteration loops
          ├─ AC.PROMOTE-BIN.1 (binary-channel surface — three subprocess
          │   channels reach extraction)
          ├─ AC.PROMOTE-BIN.2 (vacuous-README unblock — extractor
          │   proceeds when README is empty AND binary is interrogable)
          ├─ AC.PROMOTE-BIN.3 (provenance threading — every emitted
          │   objective carries its source channel(s))
          ├─ AC.PROMOTE-ITER.1 (iteration-loop substrate — verifier-
          │   pluggable, telemetry-emitting, cap-honoring)
          ├─ AC.PROMOTE-ITER.2 (compile verifier — first verifier in
          │   the family)
          ├─ AC.PROMOTE-ITER.3 (extraction-empty verifier — second
          │   verifier; closes figlet-class failure mode)
          └─ AC.PROMOTE-INT.1 (end-to-end outcome-altitude probe —
              binary + stub README → working submission via the
              composed pipeline)
```

**VALUE_PROPOSITION tests:**

- **Primary-persona test (translation burden):** today a user with a binary + stub README hits a HALT.txt; the persona has no path forward without the user adding documentation themselves. After: the persona invokes the binary-channel extractor + iteration-loop substrate transparently; the user surface is unchanged. Translation burden moves from user-supplies-docs to harness-interrogates-binary. **PASSES.**
- **Harness test (toolkit expansion):** the primary persona gains two new tools — a binary-as-input modality for objective extraction, and a verifier-loop primitive composable with arbitrary verifiers. Both are invocable by the persona (CLI flag + library API). **PASSES.**

---

## §3 — Canonical-home recommendation per pattern

### Pattern 1 — Multi-channel binary extractor

**Recommendation:** extend `plugins/dev-sdlc/odd-extractor/` with a new `binary_channels.py` module + a `--binary <path>` CLI flag on `loam odd-extract`. The binary-channel collectors plug into the existing `multi_source.py` bundle as a fourth source kind, named alongside README / design docs / tests / survey / code patterns.

**Composition argument:**

- `multi_source.py` is **already** the multi-source input collector for `odd-extractor`. It exposes a `MultiSourceBundle` shape that carries per-source addressability + per-source byte caps + token estimation. The binary-channel additions are a new source kind on the same shape — not a parallel system.
- The experiment scaffold's `binary_interrogate.py` is shaped almost exactly like what plugs in. Three channel collectors (`collect_subprocess_help`, `collect_subprocess_version`, `collect_subprocess_strings`) return `ChannelOutput` records (channel / text / ok / truncated / error / invocation). Migration is mostly relocation + integration into `MultiSourceBundle`, not redesign.
- The experiment scaffold's `continuum_extract.py` is a parallel extractor that bypasses `multi_source.py` and `analyze.py` — this is a side-effect of the experiment having an isolated harness. **The canonical promotion does NOT migrate `continuum_extract.py`; it migrates the channel collectors (Phase 4-B contribution) into the existing `multi_source.py` bundle + adds the vacuous-README rule + provenance threading to the existing extractor pipeline.** This is the architectural simplification that the experiment-context didn't have to honor.
- The vacuous-README unblock rule (`is_readme_vacuous`) plugs into `multi_source.py`'s README handler. It's a pre-condition check, not a separate code path.
- The provenance field already exists at the objective shape level — `Objective` carries `provenance` per the `loam-rebuild` extractor's typed-stack shape. The promotion adds channel-aware provenance derivation alongside the existing README-excerpt-driven derivation.

**Sub-recommendation:** the `odd-extractor` plugin is the canonical home, NOT a new top-level `framework/` component. Reasoning: extraction-from-foreign-codebases is the plugin's existing concern; binary-extraction is the same concern with an additional input modality. A new `framework/binary-interrogation/` component would split a single concern across two components and require coordination across the seal fence. Composition under the existing plugin is the simpler shape.

### Pattern 2 — Iteration-loop family

**Recommendation:** new shared substrate at `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/iteration_loop.py` exposing a `VerifierLoop` primitive + two concrete verifiers (`CompileVerifier`, `ExtractionEmptyVerifier`). The compile-loop integration plugs into `code_gen.py`'s output-emission path. The extraction-empty-loop integrates at the extraction-output path.

**Composition argument:**

- The iteration-loop is **architecturally above** the binary-channel extractor — it composes with both the extractor output (extraction-empty verifier) and the code-gen output (compile verifier). Either pattern can ship independently of the other.
- A `VerifierLoop` substrate is verifier-pluggable: `Verifier.check(submission) → VerifierResult { ok, signal, error_context }`. The loop itself is generic; verifiers are concrete. Future verifiers in the family (README-self-test, behavioral-equivalence-probe, LLM-judge) plug into the same substrate.
- Co-locating in `loam_odd_extractor` (the same package as code_gen.py) lets the compile-loop integrate without cross-package imports. **Sub-recommendation:** keep verifiers in the same package; consider lifting `VerifierLoop` to `framework/` only if a second non-extraction-non-codegen consumer arrives (Lens 1 — leverage existing harness primitives rather than over-generalize ahead of need).
- The experiment scaffold's `compile_loop.py` is shaped close to what plugs in — it has a clean separation between `run_compile_in_docker` (the verifier), `build_retry_prompt` + `call_claude_retry` (the LLM-call + retry-prompt-construction), and `compile_loop_run` (the loop driver). Migration refactors the loop driver into a generic `VerifierLoop` + recasts `run_compile_in_docker` as a `CompileVerifier` concrete class.
- **Halt-and-surface (F2):** the experiment's `compile_loop.py` uses a hard-coded `TASK_IMAGE` dict mapping short task names to ProgramBench Docker images. This is benchmark-specific and does NOT translate cleanly to canonical loam. The canonical `CompileVerifier` must take a Docker image config from the extraction state (or from the workspace's safety-profile) rather than carry a hard-coded benchmark mapping. **This is a real design delta from the experiment — not a paper-over.** The experiment-scaffold version is a benchmark-specialized variant; the canonical version generalizes the image-resolution path.

### Both patterns — interaction with `loam-builder` persona + `objective-tracker`

- **`loam-builder` persona** (the typed sub-agent at `plugins/dev-sdlc/agents/loam-builder.md`) is the dispatcher for amendment cycles. The promotion build itself uses `loam-builder`. After the promotion lands, `loam-builder` gains no new responsibilities — the binary-channel and compile-loop surfaces are library/CLI primitives the persona invokes via existing extraction + code-gen flows, not new persona-behavior surfaces. **No persona-prompt edits required.**
- **`objective-tracker` component** (event-sourced runtime tracking at `framework/objective-tracker/`) tracks runtime objectives, not extraction-time objectives. The extractor produces the typed objective stack that downstream consumers (including `objective-tracker` if/when wired) consume. Provenance threading adds the source-channel field to the typed objective; if `objective-tracker` later wants to display "this objective came from `subprocess_help`" in a UI, the data is already on the row. **No `objective-tracker` edits required for promotion; the provenance field is forward-compat.**

---

## §4 — Acceptance criteria (the AC ladder)

Seven ACs covering both patterns. AC IDs use scope-descriptive `PROMOTE-BIN.*` (binary extractor) + `PROMOTE-ITER.*` (iteration-loop) + `PROMOTE-INT.*` (integration) families per `feedback_scope_descriptive_ac_ids`.

| AC | Outcome | Verification |
|---|---|---|
| **AC.PROMOTE-BIN.1 — Binary channels surface** | `loam odd-extract <repo> --binary <path>` accepts a path argument; the extractor invokes three subprocess channels (`subprocess_help`, `subprocess_version`, `subprocess_strings`); each non-empty channel becomes a labeled entry in the `MultiSourceBundle` with the channel-label as `path`. | Unit: bundle-shape test on a fixture binary (a small loam-internal stub binary — see §11 D-Q.PROMOTE-BIN.1; the retired benchmark's task binaries are no longer a fixture option). Outcome-altitude: live extraction against one task binary produces ≥1 objective whose provenance names `subprocess_help`. |
| **AC.PROMOTE-BIN.2 — Vacuous-README unblock** | When `is_readme_vacuous(readme_text)` returns True AND `subprocess_help.ok` is True, the extractor proceeds rather than HALTing on zero-objective README. The persona's no-speculative-features constraint becomes provenance-aware: the binary IS the documentation source. | Unit: fixture with a 50-char placeholder README + a help-yielding binary → extraction returns ≥5 objectives whose provenance is `subprocess_help`. Negative: empty README + non-executable binary → still HALTs. |
| **AC.PROMOTE-BIN.3 — Provenance threading** | Every emitted `Objective` carries a `provenance` string of `+`-joined channel labels derived from `evidence.design_doc_refs` + `evidence.readme_excerpts`. Canonical order: `task-readme`, then channel labels in `BINARY_CHANNEL_LABELS` order. | Unit: extraction against a fixture where README mentions flag X and `--help` also lists flag X → resulting Objective for that flag has `provenance="task-readme+subprocess_help"`. |
| **AC.PROMOTE-ITER.1 — Iteration-loop substrate** | `VerifierLoop(verifier, max_attempts, retry_call)` runs verify → if-fail-retry → re-verify → cap-and-record loop. Telemetry fields populated per attempt: `attempt_idx`, `verifier_result`, `verifier_signal_tail`, `retry_cost_usd`, `retry_wall_clock_s`. Exhaustion sets `loop_exhausted=True`. | Unit: substrate test with a duck-typed verifier returning fail then ok → loop converges at attempt 2; telemetry shape matches schema. Substrate-only test with always-fail verifier → exhausts at max_attempts. |
| **AC.PROMOTE-ITER.2 — Compile verifier (first in family)** | `CompileVerifier(image_resolver)` runs `compile.sh` inside a Docker image returned by `image_resolver(task_id)`; returns VerifierResult with `signal=stderr+stdout-tail-4KB` on failure. Integrated into `code_gen.py`'s submission-emission path behind a `--compile-loop on/off` flag (default on; off is byte-identical to pre-promotion behavior). | Outcome-altitude: code-gen against a fixture that produces a known-bad first-pass (yj-class: unused import in Go) → submission converges via retry; final submission compiles exit-0. No-regression: `--compile-loop off` against a known-good fixture → byte-identical pre-promotion shape. |
| **AC.PROMOTE-ITER.3 — Extraction-empty verifier (second in family)** | `ExtractionEmptyVerifier` checks `len(extracted_files) > 0` after the LLM's submission-emission; on empty extraction, builds a retry prompt explicitly instructing fenced-FILE-block format. Plugs into the same substrate as the compile verifier. | Outcome-altitude: a fixture where the first-pass LLM response is prose-only (no FILE blocks) → retry recovers; final extraction has ≥1 file. (Figlet-class failure mode from Step 4 synthesis is the empirical target.) |
| **AC.PROMOTE-INT.1 — End-to-end outcome-altitude probe** | A single integration test runs `loam odd-extract <fixture-repo> --binary <fixture-binary>` against a stub-README fixture, then runs `loam <code-gen-verb>` with `--compile-loop on`, then verifies the final submission compiles exit-0 inside the same Docker image. Captures cost + wall + per-attempt telemetry. Documented in `docs/experiments/<promotion-slug>-hard-smoke.md`. | Smoke: live `claude -p` execution against the fixture; final submission compiles; per-attempt detail recorded in run.json. |

**Seal-discipline AC** (added at build-time per amendment-cycle conventions): `AC.PROMOTE.S — Seal diff is within the named component fence.` Verified by `loam amend seal`.

---

## §5 — Behaviour-count check (ODD §3.3 dev-discipline)

Per ODD §3.3, every new code path maps to a named AC. Enumerated coverage:

- Channel collectors (`collect_subprocess_help`, `collect_subprocess_version`, `collect_subprocess_strings`): AC.PROMOTE-BIN.1.
- `is_readme_vacuous` predicate + extractor's no-HALT path: AC.PROMOTE-BIN.2.
- `_provenance_for_row` + Objective.provenance field plumbing: AC.PROMOTE-BIN.3.
- `VerifierLoop` driver + telemetry container: AC.PROMOTE-ITER.1.
- `CompileVerifier` + `run_compile_in_docker` + `image_resolver` interface: AC.PROMOTE-ITER.2.
- `ExtractionEmptyVerifier` + retry-prompt-for-empty-extract: AC.PROMOTE-ITER.3.
- End-to-end integration test wiring: AC.PROMOTE-INT.1.
- `loam amend apply` + `loam amend seal` admin: AC.PROMOTE.S.

No orphan code paths. Every branch in the migrated code maps to an AC above OR is verbatim-relocated from the experiment scaffold (in which case the experiment's ACs satisfy the path; the verification step re-runs the relocated code against fresh canonical tests).

---

## §6 — Cycle structure + AI-time estimate

**Recommendation: TWO CYCLES, sequential.** Cycle 1 ships the binary-channel extractor (AC.PROMOTE-BIN.{1,2,3}); Cycle 2 ships the iteration-loop substrate (AC.PROMOTE-ITER.{1,2,3} + AC.PROMOTE-INT.1).

**Rationale for split (not single-cycle):**

1. The two patterns compose but are not mutually-dependent. Cycle 1 is shippable + valuable standalone (binary-extraction unblocks csview-class tasks; compile-loop is orthogonal).
2. Each cycle is approximately one full sealed-component amendment. Combining them into one cycle creates a wider fence + a larger seal-diff + more rollback risk on a single seal commit. Two narrower cycles compose cleanly with `feedback_serialize_amendment_builds` (single working tree, sequential builds).
3. The §11 open questions on Cycle 2 (image-resolver shape; persona-prompt integration depth) are higher than on Cycle 1. Cycle 1 is closer to a relocate-and-integrate; Cycle 2 has live design decisions. Splitting lets Cycle 1 land while Cycle 2 ratifies.

**Cycle 1 — Binary-channel extractor.**

- Scope: AC.PROMOTE-BIN.{1,2,3} + AC.PROMOTE.S (cycle-1 seal).
- Source-edits: `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/binary_channels.py` (NEW, ~250 lines — relocated from `binary_interrogate.py` with caps + filter regexes preserved); extend `multi_source.py` to accept binary-channel entries; extend `analyze.py` / `cli.py` for `--binary` flag plumbing; add `_provenance_for_row` to the objective-shape converter; vacuous-README pre-condition check.
- Tests: ~12 unit tests (channel collectors against fixture binaries OR mocked subprocess; bundle integration; vacuous-README threshold; provenance derivation rules) + 1 outcome-altitude probe (live extraction).
- Estimated AI-time: 90–180 min midpoint **~135 min**. Plan-doc + manifest authoring is +30–45 min on top.

**Cycle 2 — Iteration-loop family substrate.**

- Scope: AC.PROMOTE-ITER.{1,2,3} + AC.PROMOTE-INT.1 + AC.PROMOTE.S (cycle-2 seal).
- Source-edits: `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/iteration_loop.py` (NEW, ~400 lines — generalizes `compile_loop.py`'s loop driver into `VerifierLoop`; pulls in `CompileVerifier` + `ExtractionEmptyVerifier`); extend `code_gen.py` to invoke `VerifierLoop[CompileVerifier]` at submission-emission; extend the extractor output to invoke `VerifierLoop[ExtractionEmptyVerifier]` (or compose the verifier into the existing retry path); CLI flag `--compile-loop on/off` on the code-gen verb.
- Tests: ~10 unit tests (substrate driver against duck-typed verifiers; compile + extraction-empty verifier paths; exhaustion; no-regression with loop off) + 1 outcome-altitude probe (end-to-end binary + stub README → working submission).
- Estimated AI-time: 150–240 min midpoint **~195 min**. Plan-doc + manifest authoring is +30–45 min on top.

**Total promotion AI-time:** 240–420 min midpoint **~330 min** (~5.5 hours), spread across two cycles. Plus owner gate-review between cycles (separate from AI-time).

---

## §7 — Composability discussion

### With existing loam architecture

- **`loam-builder` persona** — no edits. The promotion adds library + CLI surface; persona-side dispatch shape is unchanged. (Future plan-docs in v0.7.0+ that dispatch the binary-extractor cycle invoke `loam-builder` with the standard amendment-cycle prompt shape.)
- **`objective-tracker` component** — no edits. The provenance field on Objective is forward-compat additional data; runtime-objective-tracking is orthogonal to extraction-time provenance.
- **`code_gen.py`** — extends. The submission-emission path gains the compile-loop wrapping; this is the canonical integration site for the compile verifier. Existing `--from-scratch` / multi-commit-per-task / tie-breaker surfaces (v0.4.1 / v0.4.2 closures) compose unchanged.
- **`multi_source.py`** — extends. The binary-channel collectors plug in as a fourth source kind alongside README / design docs / tests / survey / code patterns; per-source byte caps + token estimation existing logic applies to the binary channels with channel-specific caps (5 KB / 1 KB / 4 KB for help / version / strings per experiment-validated values).
- **`analyze.py` repo walker** — extends. The `--binary` flag plumbs binary path through the existing extraction-config pipeline; default is None (binary-channels disabled) so no regression on existing extraction shape.
- **Safety profile / cost-governance** — composes. The compile-loop fires `claude -p` retries; existing budget-envelope logic applies. The Docker invocation is sandboxed (per the v0.7.0-placeholder roadmap constraint on sandboxed binary execution). **Halt-and-surface (F2):** the experiment scaffold runs Docker inside the inference container without checking the workspace's safety-profile production-stake floor. The canonical version MUST consult `framework/safety-layer/` for sandbox policy before invoking Docker. This is a real composition step the experiment didn't need.

### Fate of the experiment-scaffold versions

**Recommendation:** keep as reference; do not delete.

- The scaffold lives at `~/pos3/workspace/experiments/programbench-derivative/` (a pos3 workspace, NOT canonical loam). The pos3 workspace is gitignored from canonical loam; the experiment files are not in the canonical tree.
- The experiment scaffold contains benchmark-specific tooling (5 task binaries, the `TASK_IMAGE` hard-coded dict, the per-task Docker images, the eval scripts) that has no canonical home. Deleting the scaffold loses the experimental harness; that harness is the regression substrate for any future benchmark-vs-loam comparison.
- After promotion lands, the scaffold's `binary_interrogate.py` + `compile_loop.py` + `continuum_extract.py` continue to exist in pos3 as benchmark-specialized variants. The canonical versions are the source of truth; the scaffold consumes them (replaces local copies with imports from `loam_odd_extractor`).
- **Halt-and-surface (F2):** if the scaffold consumes the canonical version via `pip install -e plugins/dev-sdlc/odd-extractor/`, the scaffold becomes test infrastructure for the canonical version — useful continuous-validation. If it stays divergent, drift between scaffold + canonical accumulates. **§11 D-Q.PROMOTE.SCAFFOLD-FATE — defer to owner ruling on whether the scaffold imports from canonical or stays divergent.**

### Backward compatibility

- **Default-on vs opt-in:** the binary-channel extractor is **opt-in** (requires `--binary <path>`). Existing `loam odd-extract <repo>` invocations are byte-identical pre/post-promotion; no behavior change without the new flag.
- **Compile-loop:** **default-on** with `--compile-loop off` opt-out. Rationale: the experiment validated ~17% token overhead with conditional firing (only on bad first-pass) AND empirically converged on the iteration-deficit failure class. Default-on lifts the median outcome; opt-out preserves a regression escape. **Halt-and-surface (F2):** this is a behavior-default flip relative to today (today no compile-loop). The deciding criterion is whether the cost-overhead is acceptable to the default user. The experiment data says yes (~17% overhead; 0 exhaustions across 5 generations). If owner wants extra conservatism, default-off is also defensible. **§11 D-Q.PROMOTE-ITER.DEFAULT.**
- **Migration plan for existing loam-builder dispatches:** dispatches that don't name `--binary` or `--compile-loop` get pre-promotion behavior. Dispatches that opt-in to either gain the new surface. No existing dispatch-brief edits required.

---

## §8 — Hard constraints

- **Subscription-only architecture** — every LLM call in the promoted code routes through `claude_print_synthesis_client` (or equivalent `claude -p` subprocess wrapper). NO `import anthropic`; NO `ANTHROPIC_API_KEY`. Per `feedback_no_anthropic_api_key` + roadmap §1 architectural constraints. The experiment's `call_claude_retry` already uses `claude -p` directly; the canonical version replaces this with the canonical client.
- **`--strict-mcp-config` + empty MCP-config tempfile** on every `claude -p` invocation per `AC.WSα.8`. The experiment scaffold honors this; the canonical promotion must continue to.
- **ODD §2.5 — every line of migrated code maps to a named AC.** Per `feedback_odd_no_non_objective_code`. The §5 behaviour-count check enumerates this.
- **Sealed-component fence** — both cycles touch `plugins/dev-sdlc/odd-extractor/`; the seal-test gates the fence per existing component conventions. No cross-component edits without owner ratification.
- **No `git commit --amend`** in any dispatched cycle (per `feedback_no_amend_in_agent_dispatches`).

---

## §9 — Out of scope (explicit)

- **The migration build itself.** This document plans the build; the dispatched cycle plan-doc + manifest is the next artefact.
- **`extract_files` reuse from `run_agent.py`** — the experiment's compile_loop has its own copy. The canonical version uses code-gen's existing extraction primitive; no duplicate.
- **Additional verifiers beyond compile + extraction-empty.** README-self-test, behavioral-equivalence, LLM-judge are named in the 4-step synthesis as future family members. They plug into the same substrate at later versions, not this promotion.
- **F-EXTRACT-CONVERGE confidence-weighting from multi-channel convergence.** Captured at FIDRAFT line 266 (2026-05-11). Activates when the data justifies it; this promotion ships the provenance substrate, NOT the confidence-weighting layer above it.
- **Probe-input library** for binary-channel extraction (CSV / JSON / HTML / TOML probes). Phase 4-B names this as a fourth channel; the experiment didn't build it. Defer to follow-on PATCH/MINOR if probe-runs prove necessary on a target task. (Step 4 evidence: the three implemented channels were sufficient on csview / gron / htmlq / yj / figlet; probe-runs were not required for the empirical wins.)
- **Domain-convention inference** as a fifth source kind (Phase 4-B §"Mechanism 4"). Risk: speculation creep. Defer to follow-on with explicit prompt-engineering scope.
- **Multi-LLM router** for the retry call. Subscription-only architecture (Claude Max via `claude -p`); other providers are backlog.
- **Compile-loop for non-Docker environments** (raw host compile). The experiment uses task-specific Docker images; the canonical version requires sandboxed compile (per the v0.7.0-placeholder roadmap constraint). Raw-host compile is owner-ratifiable later if a use case surfaces.
- **Touching experiment-scaffold code.** This plan-doc explicitly does NOT migrate scaffold code; it scopes how the migration will look + leaves scaffold-fate to §11.

---

## §10 — Halt triggers (for the future build cycles)

The Cycle 1 + Cycle 2 builds halt-and-surface if:

- A migrated function's behaviour deviates from the experiment-scaffold version (relocation should be near-verbatim modulo image-resolver generalization + `claude -p` wrapper swap). Surface the divergence + reason BEFORE merging.
- A test against canonical fixtures (real binaries OR loam-internal stub) fails where the experiment-scaffold equivalent passed. Likely cause: environment delta (Docker config, claude-binary path, MCP-config); surface + diagnose, do not silently work around.
- The `_provenance_for_row` derivation produces a different result on a regression fixture vs the experiment's smoke output. Tag-set drift means the canonical version is silently re-classifying; halt.
- The `VerifierLoop` substrate runs hot (>1 retry call per attempt) — indicates a wrong loop-shape; halt + surface.
- Docker invocation requires `--platform linux/amd64` on a non-Darwin host or fails to bind-mount; surface the host-portability gap.
- Any `claude -p` invocation fails to honor `--strict-mcp-config` — kills the parent Telegram bot; immediate halt per `AC.WSα.8`.

---

## §11 — Decisions remaining for the owner to rule on

Each decision below is **non-obvious** per the F2/M5 four-step process — silent resolution would propagate as implicit precedent.

### D-Q.PROMOTE-BIN.1 — Test-fixture binary source

**The question:** the binary-channel collectors need fixture binaries to test against. Three options:

- **Option A: ship the ProgramBench 5 task binaries as test fixtures inside `plugins/dev-sdlc/odd-extractor/tests/fixtures/binaries/`.** Total disk: ~16 MB (csview 1.0 MB + figlet ~0.5 MB + gron 6.3 MB + htmlq 2.7 MB + yj 4.9 MB). Concrete + behavior-matches-experiment; but bloats the loam tree with multi-MB binary blobs.
- **Option B: build a tiny loam-internal stub binary** (Go or Rust) that exposes `--help` / `--version` / a few flags. Lightweight (~1 MB single binary); generic; doesn't tie tests to a specific benchmark. Cost: ~30 min to author + the build step.
- **Option C: mock the subprocess channel calls** in unit tests; only the outcome-altitude probe runs against a real binary (and that binary lives outside the loam tree, e.g., pulled from a system path or a temp fixture-build).

**My recommendation:** **B + C hybrid.** Author a loam-internal stub binary for the bulk of unit tests; mock subprocess channels for tight pure-Python unit tests; use a system binary (e.g., `git --help`) for the outcome-altitude probe so no fixture-build dependency. Avoids binary-blob bloat while keeping tests behavior-faithful.

### D-Q.PROMOTE-ITER.IMAGE-RESOLVER — How does the canonical `CompileVerifier` resolve Docker images?

**The question:** the experiment uses a hard-coded `TASK_IMAGE` dict; the canonical version needs an `image_resolver(task_id)` interface. Three options:

- **Option A: workspace-config-driven** — `image_resolver` reads from `<workspace>/.loam/compile-images.yaml`; user-configurable. Defers to the workspace owner.
- **Option B: extraction-state-driven** — the extraction artefact (`.loam/extractions/<repo-id>/config.yaml`) carries the Docker image config alongside the binary path; image binding is per-extraction, not per-workspace.
- **Option C: detected-from-language-adapter** — the language adapter (Ruby / JsTs / Python / Go via auto-detect from repo) returns a default Docker image; user-overridable but no required config.

**My recommendation:** **B (extraction-state-driven) with Option C fallback.** Per-extraction binding lets the user reproduce different binaries with different images without workspace-level config. The language-adapter fallback gives the no-config path. Option A is the most flexible but the least defaulted; Option C alone is the most defaulted but the least flexible.

### D-Q.PROMOTE-ITER.DEFAULT — Default-on vs opt-in for compile-loop

**The question:** does `--compile-loop on` ship as default-on (with `--compile-loop off` opt-out) or default-off (with `--compile-loop on` opt-in)?

**Empirical data:** experiment Step 4 — compile-loop fired on 2 of 5 tasks (yj + csview), converged in both cases, ~17% token overhead averaged across all 5. No exhaustions.

**My recommendation:** **default-on.** The empirical overhead is small relative to the recovery benefit. Default-off requires every user to discover the flag; default-on captures the median value with a clean opt-out path. This is a behavior-default flip relative to today; I surface the question for explicit owner ruling because it's a small but observable behavior change.

### D-Q.PROMOTE.SCAFFOLD-FATE — Does the experiment scaffold consume canonical or stay divergent?

**The question:** after promotion, do the pos3 experiment scaffold files (`binary_interrogate.py`, `compile_loop.py`) import from the canonical `loam_odd_extractor` package, or do they stay as standalone divergent copies?

- **Option A: scaffold imports canonical.** `binary_interrogate.py` becomes a thin shim: `from loam_odd_extractor.binary_channels import collect_subprocess_help, ...`. Scaffold becomes test infrastructure for canonical — every benchmark run validates the canonical version.
- **Option B: scaffold stays divergent.** Scaffold files keep local copies as they are today; canonical is independent. Drift accumulates over time.
- **Option C: scaffold deleted.** Aggressive; loses the experimental harness.

**My recommendation:** **A (scaffold imports canonical).** Continuous-validation is high-leverage; the alternative (B) silently lets drift accumulate. C is over-aggressive — the harness is reusable across benchmarks.

### D-Q.PROMOTE.VERSION-NUMBER — What MINOR does this become?

The §4 roadmap entry labeled `v0.7.0 placeholder` (was v0.5.0 — "Loam builds software from minimal input") names this promotion's surface as AC.V050.1 + AC.V050.2. But v0.7.0 has already been used for a different MINOR (non-tech-user surface, shipped 2026-05-09). The roadmap §3 says version-numbering is deferred to build-commence-time per the priority-queue restructure plan-doc (uncommitted).

**My recommendation:** **defer to roadmap-restructure timing.** When this plan-doc dispatches its build cycles, the priority-queue restructure should be in effect; the cycle plan-docs name the version at that time. For now, this plan-doc names the **outcome shape** + the **AC surface**; the version number is derived later.

### D-Q.PROMOTE-INT.FIXTURE — End-to-end probe fixture

**The question:** the AC.PROMOTE-INT.1 outcome-altitude probe runs a binary + stub-README fixture through extraction + code-gen + compile-loop. What's the fixture?

- **Option A: a ProgramBench task binary** (e.g., csview — load-bearing in the empirical evidence). Pros: empirically-grounded. Cons: ties test to a third-party benchmark; multi-MB binary blob in tree.
- **Option B: the loam-internal stub binary from D-Q.PROMOTE-BIN.1.** Pros: lightweight; under loam control. Cons: less empirically meaningful (the stub is whatever shape we author).
- **Option C: a system binary** (e.g., `jq --help` if jq is installed). Pros: zero fixture-build cost. Cons: environment dependency; fails if jq isn't installed.

**My recommendation:** **B (loam-internal stub).** Outcome-altitude probe is about the pipeline shape, not benchmark performance. Stub is sufficient + controllable + under loam discipline.

---

## §12 — Summary of named decisions (owner-readable)

Six decisions, each with a recommendation. Two are method-of-implementation (B + C hybrid for fixture binaries; extraction-state-driven for image resolver); two are policy (compile-loop default-on; scaffold imports canonical); two are sequencing (version number deferred; outcome-altitude probe uses internal stub).

| ID | Decision | My recommendation | Why surface (not silent) |
|---|---|---|---|
| D-Q.PROMOTE-BIN.1 | Fixture binaries source | B+C hybrid (stub + mocks + system binary for probe) | Reasonable people would weigh binary-blob bloat vs empirical-faithfulness differently. |
| D-Q.PROMOTE-ITER.IMAGE-RESOLVER | Docker image resolver shape | B (extraction-state-driven) + C fallback | Three plausible shapes; binding-altitude affects user-facing config surface. |
| D-Q.PROMOTE-ITER.DEFAULT | Compile-loop default | default-on with opt-out | Behavior-default flip; default-on changes the median user experience. |
| D-Q.PROMOTE.SCAFFOLD-FATE | Experiment scaffold after promotion | A (scaffold imports canonical) | Drift-vs-shim tradeoff is a maintenance-discipline call. |
| D-Q.PROMOTE.VERSION-NUMBER | What MINOR number | Defer to roadmap-restructure timing | Numbering policy is upstream of this plan. |
| D-Q.PROMOTE-INT.FIXTURE | Outcome-altitude probe fixture | B (loam-internal stub) | Less empirical, more controlled — defensibility delta. |

---

## §13 — Halt-and-surface findings from plan authoring

Surfaced now per F2 (name the disagreement; name the evidence; name the alternative).

### Finding 1 — `continuum_extract.py` does NOT promote cleanly; it bypasses canonical multi-source bundle

**Evidence:** the experiment's `continuum_extract.py` loads `odd_extract` dynamically via `importlib.util` and bypasses `multi_source.py` + the language-adapter chain entirely. It's a parallel extractor optimised for one-shot prose+binary extraction in an isolated harness. The canonical loam tree's `multi_source.py` + `analyze.py` + `generate.py` is the four-stage pipeline (init → analyze → generate → verify) and is where multi-source extraction lives.

**Alternative:** the canonical promotion migrates the **channel collectors** + the **vacuous-README rule** + the **provenance threading** — three discrete primitives — into the existing pipeline. It does **NOT** migrate `continuum_extract.py` as a parallel system. This is the architectural simplification the experiment-context didn't have to honor and the right call now.

### Finding 2 — Hard-coded `TASK_IMAGE` is benchmark-specialized, NOT canonical

**Evidence:** `compile_loop.py:53-59` has a 5-entry dict mapping short task names to `programbench/...:task` Docker images. There is no general task-to-image resolution mechanism. This is the benchmark's specific deployment shape.

**Alternative:** the canonical `CompileVerifier` requires an `image_resolver(task_id) -> str` interface (per §11 D-Q.PROMOTE-ITER.IMAGE-RESOLVER). The canonical version cannot inherit the benchmark mapping; this is a real design step, not a relocation.

### Finding 3 — `call_claude_retry` re-implements `claude -p` invocation; canonical version must use `claude_print_synthesis_client`

**Evidence:** `compile_loop.py:234-291` re-implements `claude -p` subprocess invocation with its own argv assembly + env scrubbing. The canonical version of this primitive is `framework/primary-persona/src/loam/primary_persona/claude_print_client.py` (referenced in `feedback_no_anthropic_api_key`) and `claude_print_synthesis_client` (the shim consumed by `code_gen.py`).

**Alternative:** the migration replaces `call_claude_retry` with calls into the canonical client. Same `--strict-mcp-config` + empty MCP-tempfile contract; same `--output-format json` envelope parsing; existing wrapper.

### Finding 4 — `--max-compile-attempts` cap discipline differs experiment vs canonical

**Evidence:** experiment caps total attempts at 3 (attempt 1 = initial submission; attempts 2–3 are retries). The substrate's exhaustion record sets `compile_loop_exhausted = True` only when `idx == max_attempts` is reached. The substrate doesn't currently distinguish "retry-call failed" (claude -p errored) from "verifier still failed after retry" — both increment idx.

**Alternative:** the canonical `VerifierLoop` should distinguish two failure modes at telemetry level: `retry_call_returncode != 0` (non-recoverable; loop terminates) vs `verifier still failing` (recoverable; cap-honoring). Clean failure-attribution at the telemetry layer makes downstream cost-attribution analysis tractable.

### Finding 5 — The empirical figlet failure mode demonstrates the verifier-pluggability requirement

**Evidence:** in Step 4 (compile-loop benchmark), figlet's run produced 0 extracted FILE blocks because the LLM emitted prose-not-FILE-format. Compile-loop never fired because there was nothing to compile. The compile-loop alone couldn't recover figlet; an extraction-empty verifier would have.

**Alternative:** AC.PROMOTE-ITER.3 ships the second verifier in the family precisely to address this. The plan ships compile + extraction-empty TOGETHER, not compile alone. Shipping only compile leaves the figlet-class failure mode unaddressed.

### Finding 6 — F-EXTRACT-CONVERGE (FIDRAFT line 266) is NOT in this promotion's scope

**Evidence:** the FIDRAFT entry captures the confidence-weighting layer that would consume provenance data. This promotion ships the provenance substrate; the layer above is owner-flagged as deferred ("not sure if this is worth a significant effort to implement now").

**Alternative:** explicit out-of-scope in §9; ship the provenance + leave confidence-weighting to follow-on. This is the silent-acceptance failure mode prevented by F2 — naming explicitly rather than silently rolling the layer in.

### Finding 7 — `O.persona.no-speculative-features` interaction is provenance-aware, not source-blind

**Evidence:** the experiment's prompt instruction makes the no-speculation rule provenance-aware: when README is vacuous AND binary is interrogable, the binary IS the documentation. The canonical promotion needs to thread this through the persona's prompt surface in `multi_source.py` / wherever the no-speculation contract lives.

**Alternative:** the canonical version explicitly threads the provenance-awareness through the system prompt. This is named as part of AC.PROMOTE-BIN.2's verification but I'm surfacing it as a finding because the persona-contract interaction is non-obvious and could be lost in the relocation.

---

## §14 — Method-decision record (post-build; placeholder)

(Populated at build time per `loam amend seal --plan-doc`.)

### D-build placeholder

### Test breakdown

### Backwards-compat verification

### Commit SHAs

### Dependents cleared to dispatch

---

## §15 — References

- **CLAUDE.md** (project + global): `~/loam/CLAUDE.md` + `~/.claude/CLAUDE.md`.
- **VALUE_PROPOSITION**: `docs/VALUE_PROPOSITION.md`.
- **Plan-doc conventions**: `plugins/dev-sdlc/docs/conventions/plan-docs.md`.
- **ODD methodology**: `plugins/dev-sdlc/docs/odd-methodology.md`, `plugins/dev-sdlc/docs/odd-in-loam.md`.
- **Release roadmap**: `docs/release-roadmap.md` (§3 active version; §4 mapped-versions next entry as `v0.7.0 placeholder` formerly `v0.5.0` — "Loam builds software from minimal input"; AC.V050.1 + AC.V050.2 + AC.V050.3 surface).
- **Architectural constraints**: `docs/release-versioning-policy.md` (subscription-only; no Anthropic API key); `feedback_no_anthropic_api_key`.
- **Existing components composed-with**:
  - `plugins/dev-sdlc/odd-extractor/` (canonical home for both patterns).
  - `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/multi_source.py` (existing multi-source bundle).
  - `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/code_gen.py` (compile-loop integration site).
  - `framework/primary-persona/src/loam/primary_persona/claude_print_client.py` (subscription-only LLM wrapper).
  - `plugins/dev-sdlc/agents/loam-builder.md` (persona-side dispatcher for the future build).
- **Experiment evidence (read-only inputs to this plan)**:
  - `~/pos3/workspace/.scratch/claude-output/4-step-plan-synthesis-2026-05-11.md`
  - `~/pos3/workspace/.scratch/claude-output/step-1-extraction-fix-build-2026-05-11.md`
  - `~/pos3/workspace/.scratch/claude-output/step-3-compile-loop-build-2026-05-11.md`
  - `~/pos3/workspace/.scratch/claude-output/phase-4-b-deeper-extraction-analysis-2026-05-11.md`
- **Experiment scaffold (NOT migrated by this plan; read for shape only)**:
  - `~/pos3/workspace/experiments/programbench-derivative/harness/binary_interrogate.py`
  - `~/pos3/workspace/experiments/programbench-derivative/harness/continuum_extract.py`
  - `~/pos3/workspace/experiments/programbench-derivative/harness/compile_loop.py`
- **FIDRAFT cross-reference**: `docs/FUTURE_IDEAS_DRAFT.md` line 266 (F-EXTRACT-CONVERGE — confidence-weighting layer; out-of-scope here, captured for follow-on).
- **Feedback memories applied**:
  - `feedback_plan_before_code` (this plan-doc precedes the build).
  - `feedback_scope_descriptive_ac_ids` (AC IDs use PROMOTE-BIN / PROMOTE-ITER / PROMOTE-INT scope abbreviations).
  - `feedback_odd_no_non_objective_code` (§5 enumerates AC coverage of every new code path).
  - `feedback_no_anthropic_api_key` (§8 hard constraint).
  - `feedback_serialize_amendment_builds` (§6 two-cycle sequencing).
  - `feedback_no_amend_in_agent_dispatches` (§8 hard constraint).
  - `feedback_ruthless_feedback` (§13 names six surfaceable findings rather than silently absorbing).
  - `feedback_summarize_and_surface_decisions` (§12 owner-readable decision summary).
  - `feedback_locked_design_not_license_for_bad_outcomes` (the experiment's `TASK_IMAGE` dict + `continuum_extract.py` parallel extractor — both "locked design" at experiment-time — are revisited here per the rule).
