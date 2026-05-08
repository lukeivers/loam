# v0.4.0 Cycle 4 — ProgramBench v0 docs-only baseline (Variant A) (STUB)

**Status:** stub sub-plan-doc; finalizes at cycle-dispatch time per `plan-docs-author` SKILL master-vs-sub-plan trim discipline.
**Slug:** `v0-4-0-cycle-4-programbench-v0-docs-only-baseline`
**Date authored:** 2026-05-08.
**Parent master plan:** `docs/plans/v0-4-0-master-plan.md` §3 Cycle 4.
**Predecessor cycles:** C1 + C2 + C3 sealed.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.

---

## §1 — Outcome shape (the "why")

ProgramBench is a 200-task / 248k-behavioral-test public benchmark; current best is Claude Opus 4.7 at 3% "almost resolved" / 0% fully resolved. Variant A (docs-only feeder → reverse-ODD → ODD-grounded code-gen) is loam's claim that ODD-grounding the code-gen meaningfully improves outcome quality vs blind code-gen. C4 ships the v0 baseline + Variant A run on 3-5 small tasks (jq, ripgrep candidates per `programbench-loam-benchmark-v0.md`).

Either result is ship-worthy data per the source artefact: a substantial Variant A improvement is a real differentiation story for loam; a flat result is signal that the planning layer doesn't help on this class of task and points at where loam IS load-bearing (planning-time decisions in larger codebases).

## §2 — Prime objective ladder

VALUE_PROPOSITION.md prime objective → v0.4.0 §3 outcome → AC.V040.4 (ProgramBench docs-only baseline v0) → C4 ACs below.

## §3 — Component fence

PRIMARY: `docs/experiments/programbench-v0-docs-only.md` (NEW; `docs/experiments/` is a NEW directory at v0.4.0 — first usage).

Secondary:
- ProgramBench task definitions (read-only; via the public site / mini-SWE-agent harness equivalent).
- Per-task small fixture stubs under `plugins/dev-sdlc/odd-extractor/tests/fixtures/programbench/` if needed for the v0 run (decision finalizes at C4 plan-doc dispatch — depending on whether ProgramBench tasks ship runnable fixtures or need local stubbing).

Read-only: C1+C2 code-gen surface (consume; don't widen); C3 substrate composition (consume Routines for background runs if applicable).

Universal admissions: per-task per-variant raw outputs preserved under `docs/experiments/programbench-v0-docs-only/raw/` for audit (or named subdirectory).

## §4 — AC family seed `AC.PBN.*`

- `AC.PBN.1` — Task selection rationale documented in the report. 3-5 small tasks selected (jq, ripgrep, OR alternative small terminal-utility tasks). Selection rationale names why each task was chosen + why excluded tasks (PHP, FFmpeg, SQLite, large) were excluded. `outcome-altitude: false`.
- `AC.PBN.2` — Baseline run executes (plain code-gen via mini-SWE-agent equivalent OR loam-baseline-without-ODD). Per-task pass rate captured + raw outputs preserved. `outcome-altitude: true`.
- `AC.PBN.3` — Variant A run executes (docs-only feeder → reverse-ODD via v0.2.3 multi-source synthesis pipeline → ODD-grounded code-gen via C1+C2 surface). Per-task pass rate captured + raw outputs preserved. `outcome-altitude: true`.
- `AC.PBN.4` — Behavioral test pass rate computed per task per variant. Comparison table in report doc names baseline-vs-Variant-A delta per task. `outcome-altitude: false`.
- `AC.PBN.5` — Report doc renders cleanly; cross-references resolve; named pass-rate numbers reproducible by re-running with stated inputs. `outcome-altitude: true`.
- `AC.PBN.6` — Outcome interpretation paragraph: substantial Variant A improvement → "ODD-grounded code-gen meaningfully outperforms blind code-gen on ProgramBench"; flat result → "planning layer doesn't help on this class of task; points at where loam IS load-bearing." Either interpretation is ship-worthy. `outcome-altitude: false`.

## §5 — Build dispatch brief

Build dispatch brief authored inline by dispatcher at dispatch time per `dispatch-brief-authoring` SKILL.

## §7 — Out of scope

- Variant B docs+binary feeder (v0.5.0; binary-usage observation harness is v0.5.0 AC.V050.1).
- ProgramBench leaderboard submission (v0.5.0 AC.V050.4; the act of submitting is what makes v0.5.0's outcome public).
- SWE-bench Pro submission (harness-landscape RR.3; surfaced for owner ruling, separate gate).
- >5 task scope (parent AC.V040.4 names "3-5 small tasks").
- mini-SWE-agent harness compatibility surface (v0.5.0 AC.V050.3).
- Methodology paper / arXiv preprint (harness-landscape EV.2; surfaced for owner ruling).

## §10 — F2 RF gaps to surface at dispatch

- Final task list — jq + ripgrep are candidates per source artefact; verify against current ProgramBench leaderboard at C4 dispatch (small task availability may have changed).
- Baseline shape — "plain code-gen via mini-SWE-agent equivalent" needs concrete operationalization; loam-baseline-without-ODD (e.g., bypassing reverse-ODD; passing bare task description to `claude -p`) may be the easier-to-control comparison than mini-SWE-agent direct invocation.
- ProgramBench task fixture access — public site vs locally-stubbed fixtures; verify at C4 dispatch.
- Halt trigger §8.5 (zero signal across all tasks all variants) — if all baseline + Variant A runs produce zero behavioral test passes, the experiment shape failed before the planning layer's contribution can be measured. C4 plan-doc names what "ship the negative result" looks like vs scope-expansion.

## §11 — Provenance trail

Master plan §3 Cycle 4; release-roadmap §3 v0.4.0 AC.V040.4; `<workspace>/.scratch/claude-output/programbench-loam-benchmark-v0.md` (canonical experiment shape); v0.2.3 multi-source synthesis pipeline (sealed; consumed read-only); C1+C2 code-gen surface (consumed read-only).

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

Method-decision record finalized at C4 plan-doc dispatch time.

### Post-seal SHA register

| Commit | SHA |
|---|---|
| Plan-doc commit | (pending) |
| Source-edit commit | (pending) |
| Apply commit | (pending) |
| Seal commit | (pending) |
| §14 backfill commit | (pending) |
