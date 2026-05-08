# v0.4.0 Cycle 1 — Builder-plan (PLAN-BEFORE-CODE)

**Status:** authored 2026-05-08 by C1 build agent BEFORE any source touch.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Pre-amendment baseline:** `c0e82d43a8e83c16597c18ffba6861b782028f4a` (HEAD at dispatch).
**Parent plan:** `docs/plans/v0-4-0-cycle-1-code-gen-from-objectives-core.md` (finalized at dispatch).

## Files I expect to touch (PRIMARY)

1. **NEW** `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/code_gen.py` — code-gen module: ingestion + LLM dispatch (stubbed via injectable client) + diff emission + per-commit `objectives:` block population.
2. **NEW** `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/code_gen_spec.py` — Pydantic spec for `CodeGenRequest` / `CodeGenCommit` / `CodeGenDiff` payloads.
3. **EDIT** `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/cli.py` — register `--code-gen` flag on `loam odd-extract <repo>`; dispatch to `_cmd_code_gen` handler.
4. **NEW** `plugins/dev-sdlc/odd-extractor/tests/fixtures/code-gen/synthetic-v0/` — small fixture (objectives.yaml + gap-inventory.yaml + build-next.yaml).
5. **NEW** `plugins/dev-sdlc/odd-extractor/tests/test_AC_V040C1_1_dispatch_surface.py` — CLI flag registration + manifest entry.
6. **NEW** `plugins/dev-sdlc/odd-extractor/tests/test_AC_V040C1_2_objectives_block_schema.py` — per-commit `objectives:` block populates per LiftedFrom.
7. **NEW** `plugins/dev-sdlc/odd-extractor/tests/test_AC_V040C1_3_soft_smoke_synthetic.py` — SOFT-altitude smoke vs synthetic fixture with stub-injected LLM client.
8. **NEW** `plugins/dev-sdlc/odd-extractor/tests/test_AC_V040C1_4_no_regression.py` — sanity: pre-existing test count check (or simple no-modified-test assertion).
9. **NEW** `plugins/dev-sdlc/odd-extractor/tests/test_AC_V040C1_S_seal_diff.py` — seal-diff invariant against BASELINE..SEAL_COMMIT.

## Plan-doc + manifest

10. **EDIT** `docs/plans/v0-4-0-cycle-1-code-gen-from-objectives-core.md` — already finalized at dispatch; will receive §14 backfill post-seal.
11. **NEW** `docs/plans/v0-4-0-cycle-1-code-gen-from-objectives-core.vars.yaml` — pos-amend manifest. Generated via `loam amend new-plan` if available, else hand-authored.

## Method-decision pre-commits (D-build.1 through D-build.4)

- **D-build.1 (CLI flag name):** Selected `--code-gen` per dispatcher recommendation. Mirrors `--build-next` shape; minimal new surface.
- **D-build.2 (`source_commit` value at code-gen time):** Selected (a) — omit field. `LiftedFrom.source_commit` defaults to `None`. Cleanest; defers post-write rewrite as a future enhancement.
- **D-build.3 (`objectives:` block carrier in commit message):** Selected (b) — structured commit-message body section with delimiters. Format: commit message body contains `\n---objectives---\n<yaml>\n---objectives-end---\n`. Multiline YAML preserves the LiftedFrom shape cleanly. Extraction by regex on the delimited block. (b) chosen over (a) because git trailers are line-bounded (`Key: value` on a single line), and LiftedFrom is multi-key.
- **D-build.4 (synthetic fixture):** Hand-author 2 objectives + 1 gap + 1 build-next candidate. Smaller than `high-priority-match/` (which has 3+ objectives). Single candidate validates single-commit case for AC.V040C1.2 + AC.V040C1.3. Multi-commit case attempted via 2-objective fixture if scope permits; else surfaced for C2/v0.4.1.

## Implementation order

1. Read this builder-plan. Confirm scope alignment with parent §3 fence.
2. Author `code_gen_spec.py` (`CodeGenRequest`, `CodeGenCommit`, `CodeGenDiff` Pydantic shapes).
3. Author `code_gen.py` (entry-point: `generate_code(extraction_dir, *, llm_client=None) → CodeGenDiff`; default `llm_client` is None, requiring caller to inject; ALL LLM invocation routed through injected client matching `claude_print_synthesis_client.py` shape).
4. Author synthetic fixture under `tests/fixtures/code-gen/synthetic-v0/`.
5. Author AC.V040C1.{1,2,3,4,S} tests. Run pytest after each.
6. Wire CLI flag in `cli.py`.
7. Run pytest on `plugins/dev-sdlc/odd-extractor/tests/` (full odd-extractor scope; not full repo per amendment-dispatch-speedups).
8. Generate pos-amend manifest via `loam amend new-plan` or equivalent.
9. Pre-amendment-commit: descriptive feat commit naming the new module + CLI flag + tests.
10. `loam amend apply --dry-run` green gate.
11. `loam amend apply` → BASELINE bump.
12. `loam amend seal` → seal commit + sidecar bump + narrative.
13. Post-seal: cross-component seal-diff verification (per amendment-dispatch-speedups: verify pos-amend `apply --dry-run` green, NOT full-repo rerun).
14. Build report at `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-4-0-cycle-1-build-report.md`.
15. NO `--amend`, NO `git push`, NO `git tag`, NO GitHub Release.

## Halt conditions (per parent §8)

Halt + surface-and-RF if any of:
1. Cross-component scope expansion beyond `plugins/dev-sdlc/odd-extractor/` + universal-paths.
2. AC count grows beyond 5 + .S.
3. Multi-commit case structurally infeasible.
4. `--amend`, `git push`, `git tag` reach.
5. `import anthropic` or `ANTHROPIC_API_KEY` reach.
6. Wall-clock exceeds 360 min (240 + 50% buffer).
7. ODD §2.5 violation discovered in surrounding code.

## Out-of-scope discoveries to surface

If during build I find:
- A multi-commit per-commit-`lifted_from` shape that needs methodology amendment → surface for C2/v0.4.1.
- A fixture-shape divergence from real `claude -p` output that would obviously fail at C2 → surface for C1 redesign.
- An ODD §2.5 violation in adjacent code (e.g., build-next.py) → surface; do NOT silently extend or fix outside fence.
