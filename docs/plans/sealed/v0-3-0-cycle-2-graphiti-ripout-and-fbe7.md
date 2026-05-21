# v0.3.0 Cycle 2 — Graphiti rip-out + FBE.7 memory pivot

**Status:** sub-plan-doc; expanded from stub at cycle-dispatch time per `plan-docs-author` SKILL master-vs-sub-plan trim discipline.
**Slug:** `v0-3-0-cycle-2-graphiti-ripout-and-fbe7`
**Date authored:** 2026-05-08 (stub); expanded 2026-05-08 at dispatch.
**Parent master plan:** `docs/plans/v0-3-0-master-plan.md` §3 Cycle 2.
**Predecessor cycles:** Cycle 1 (sealed at `459c7fc`).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.

---

## §1 — Outcome shape (the "why")

Graphiti-the-component is removed from the canonical pos-v2 tree. The FBE.7 file-backed memory substrate (Stop hook persists; UserPromptSubmit retrieves) is the v0.3.0 floor. Re-implementation as an M-GMP plugin is backlog per Luke 2026-05-08. A stranger cloning loam at v0.3.0 sees no `framework/memory-system/` directory; no `kuzu_db.wal` / `graphiti-service.log` residue; the persona's memory contributor surfaces episodic entries from `<workspace>/workspace/.loam/memory/episodes/` at next session-start.

## §2 — Prime objective ladder

VALUE_PROPOSITION.md prime objective → v0.3.0 release-roadmap §3 outcome ("documented features work as advertised AND terminology is consistent across forward-looking surface") → AC.V030.2 (graphiti rip-out) + AC.V030.3 (memory FBE.7 stranger-clone verification, impl portion at C2) → C2 ACs below.

## §3 — Component fence

PRIMARY: `framework/memory-system/` (entire directory subtree — DELETE).

Secondary: cross-reference scrub in non-sealed surfaces only (root files, docs, scripts that survived FBE.7).

Excluded from this cycle (FBE.7's prior conflict-resolution call holds):
- `framework/workspace-bootstrap/` — sealed component; `adapters/memory_system.py` + `adapters/mcp_json_writer.py` already neutered at FBE.7 (`memory-graphiti` not in `_SERVICE_KINDS`; `_run_mcp_json_writer` not invoked from scaffold). Per FBE.7 plan §2 Surface #4: kept dormant for M-GMP re-admission. Preserving that decision avoids re-opening a sealed component for graphiti-only edits.
- `framework/primary-persona/` — sealed component; FBE.7 verified production paths route through `FileBackedMemoryClient`. Negative AC at FBE.7 (AC.FBE.7.7). No edits in this cycle.
- `framework/self-upgrade/` — sealed component; only graphiti reference is a docstring comment in `probes.py`. Below the threshold for re-opening a seal.
- Sealed test files (`test_no_sealed_amendments.py`) — historical narratives; preserved per cycle-1 precedent.
- `docs/archive/*` — historical artefacts; refs preserved.
- `framework/*/seals/SEAL_COMMIT.*` — sealed historical narratives.

Read-only (verify, don't edit): `install-from-source.txt` (already has zero graphiti mentions per FBE.7), `framework/first-run-inventory.yaml` (memory-system already removed from `dedicated_venvs`).

## §4 — AC family `AC.GRX.*`

- **AC.GRX.1** — Directory removal: `framework/memory-system/` no longer exists post-cycle. `find framework/memory-system -type f 2>/dev/null` returns empty.

- **AC.GRX.2** — Launchd plist removal: `framework/memory-system/launchd/com.loam.memory-graphiti.plist` no longer exists (covered by AC.GRX.1; named separately because it's the user-visible artefact that previously installed the service).

- **AC.GRX.3** — Memory-system venv removal: `framework/memory-system/.venv/` no longer exists (covered by AC.GRX.1; named separately because it's the segregated-venv FBE.7 documented as v0.1.0-floor-removed).

- **AC.GRX.4** — Workspace state cleanup verification: a fresh `loam init` workspace does NOT produce `kuzu_db.wal` / `graphiti-service.log` / `graphiti-service.err.log` files. (Verified by absence of memory-system code + FBE.7's prior workspace-bootstrap neuter.)

- **AC.GRX.5** — FBE.7 operational: the FBE.7 file-backed memory path is exercised by the existing test suite. Specifically: (a) `test_AC_J_2_stop_hook_enqueues_for_async_drain.py` + `test_AC_M_5_stop_hook_recovers_turn_content.py` + `test_AC_M_4_stop_hook_exits_zero_every_path.py` exercise Stop-hook persistence path; (b) `test_D7_1_turn_start_retrieval.py` + `test_AC_FGF_3_render_retrieval_falls_through_to_episodes.py` exercise UserPromptSubmit retrieval path. Verification: all 5 named tests green post-cycle.

- **AC.GRX.6** — `pyproject.toml` graphiti-dep verification: `git grep "graphiti_core\|graphiti-core" -- '*.toml'` returns zero (verified pre-cycle: no pyproject.toml referenced graphiti; deletion of memory-system removes its `requirements.txt` graphiti-core line).

- **AC.GRX.7** — Cycle bookkeeping ladder: `loam amend apply` + `loam amend seal` ladder lands; manifest schema v3; new commits only (no `--amend`).

Negative ACs (deliberately out-of-scope work that this cycle does NOT do):

- **AC.GRX.N1** — Negative: zero edits to `framework/workspace-bootstrap/`. (FBE.7 dormancy preserved.)
- **AC.GRX.N2** — Negative: zero edits to `framework/primary-persona/`. (FBE.7 production-runtime contract preserved.)
- **AC.GRX.N3** — Negative: zero edits to sealed-component source under `framework/*/src/`.
- **AC.GRX.N4** — Negative: zero re-implementation of graphiti against the FBE.7 substrate. (M-GMP backlog per Luke 2026-05-08.)

## §5 — Removal mechanism

Single-step: `git rm -r framework/memory-system/`.

The directory is self-contained: no other component imports `from memory_system` or `import memory_system` at runtime (verified pre-cycle by `grep -rn "^from memory_system\|^import memory_system" framework/ plugins/` returning zero outside `memory-system/` itself). Two surface mentions remain in non-sealed surfaces post-deletion:
- `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/memory_system.py:25,87` — argv string `"python3 -m memory_system.service"`. This is a launcher subprocess argv; the launcher itself is FBE.7-neutered (not in `_SERVICE_KINDS`). The string is dormant — it never runs because the kind isn't auto-launched.
- `framework/self-upgrade/src/loam/self_upgrade/probes.py:27` — comment in a docstring listing "memory-system: ``memory_system.upgrade.snapshot``". Stale docstring inside a sealed component; surfaces under cycle-3 / cycle-4 doc scrub if/when self-upgrade re-opens.

Both are inside sealed components AND below threshold for re-opening a seal for graphiti-only edits. Per FBE.7's prior multi-signal call, dormancy is preserved.

## §6 — FBE.7 operational verification mechanism

Pre-cycle baseline (recorded at dispatch — 2026-05-08 13:35 CDT):
- `pytest framework/primary-persona/tests/` → 544 passed.
- The 5 named FBE.7-path tests at AC.GRX.5 → 7 passed (subset).

Post-cycle verification (run after `git rm -r framework/memory-system/`):
- `pytest framework/primary-persona/tests/` → expected 544 passed (no change; primary-persona has zero runtime dep on memory-system).
- The 5 named FBE.7-path tests → all 5 green.
- `find framework/memory-system -type f 2>/dev/null` → empty.
- `git grep -E "graphiti_core|graphiti-core" -- '*.toml' '*.txt'` → empty (excluding `framework/*/seals/` historical files).

D5 cross-session verification (stranger-clone fresh-install → session → /clear → next session retrieves prior) is **deferred to Cycle 6** per master plan §3 Cycle 2 dependencies.

## §7 — Smoke (REALISTIC CONDITION)

D2 steady-state — `find framework/memory-system -type f` returns 0; `pytest framework/primary-persona/tests/` returns 544 passed.

D4 reboot — n/a directly; verified-by-construction (launchd plist no longer on disk → no service to relaunch).

D5 cross-session — deferred to Cycle 6.

D6 telemetry-floor — n/a (memory-system audit log paths removed with the directory; FBE.7 `<workspace>/workspace/.loam/memory/.errors` log path is the new audit floor; verified by Cycle 6).

## §8 — Halt-and-surface (in-flight)

- WD mismatch (cd literal first; halt if pwd ≠ `/Users/lukeivers/ivers-corp-pos-v2`).
- A non-sealed runtime import of `memory_system` discovered at deletion time — halt; the rip-out is wider than scoped.
- FBE.7 verification fails post-deletion (any of the 5 named tests goes red) — halt; memory pivot has a defect; surface for owner ruling.
- `pytest framework/primary-persona/tests/` count drops below 544 — halt; an unanticipated coupling exists.
- Push or tag attempt — halt.
- Any commit touches non-`framework/memory-system/` files unrelated to the rip-out + cycle-bookkeeping (this plan-doc, the manifest, the seal sidecar) — halt.

## §9 — Out of scope

- Workspace-bootstrap adapter / mcp_json_writer edits — preserved dormant per FBE.7.
- Primary-persona edits — FBE.7 verified production.
- Self-upgrade probes.py docstring scrub — below threshold for re-opening seal.
- M-GMP graphiti plugin re-implementation — backlog (Luke 2026-05-08).
- Stranger-clone D5 cross-session verification — Cycle 6.
- `claude -p --strict-mcp-config` regression scan — Cycle 6.
- ODD-conformance sweep — Cycle 6.
- Glossary publication — Cycle 5.
- Lint-pass green — Cycle 4.
- Foundation-docs gap-fill — Cycle 3.

## §10 — F2 RF gaps surfaced at dispatch

1. **memory-system has its own seal-test.** `framework/memory-system/tests/test_no_sealed_amendments.py` is a 241-line seal-diff invariant. Deleting the directory deletes the test. The seal invariant goes away with the component — no orphan-test risk.

2. **The `loam amend` cycle pattern needs an owning sealed component for bookkeeping.** memory-system itself is being deleted — it can't own its own seal. Per cycle-1 precedent (`dev-sdlc` with `frozen_baseline: true` for the doc-only rebuild collapse): use `dev-sdlc` as the bookkeeping owner with `frozen_baseline: true` + universal_paths admission for `framework/memory-system/` deletion.

3. **`framework/memory-system/tests/SEAL_COMMIT` sidecar.** Deleted with the directory. No other file in the repo references this SEAL_COMMIT sidecar's content — verified by `git grep "memory-system/tests/SEAL_COMMIT"` returning only matches inside `framework/memory-system/`.

4. **Workspace-state cleanup.** AC.GRX.4 says "a fresh `loam init` workspace does NOT produce kuzu_db.wal / graphiti-service.log". This is verified-by-construction (no service to launch → no service log). Not a runtime test in this cycle. Cycle 6 stranger-clone covers explicit verification.

5. **Pre-existing untracked plan docs** under `docs/plans/` (e.g. `auto-create-explain-lint.md`, `pos3-forward-staging-promotion-classification-plan.md`). These predate this cycle and are not part of the rip-out — they remain untracked at cycle close. Surfaced at report.

6. **Hands-off-lifecycle byte-content test pre-existing fail.** `test_d1_byte_content_match.py::test_AC_D_1_5_byte_content_match_post_move` fails on `framework/workspace-bootstrap/src/loam/workspace_bootstrap/__init__.py` hash — unrelated to graphiti, predates this cycle. Surfaced at report; not in scope.

7. **Cycle 4 future-graphiti residue.** Some surface text in non-sealed docs may still reference graphiti (status / historical context). Cycle 5 terminology-consistency + Cycle 6 feature-honesty audit are the catchers; this cycle does not sweep prose-level mentions.

## §11 — Provenance trail

Master plan §3 Cycle 2; release-roadmap §3 v0.3.0 AC.V030.2 + AC.V030.3; FBE.7 plan-doc `docs/plans/v0-1-0-foldback-scope-expansion-fbe7.md` (predecessor — verified production runtime path at primary-persona); M-FBM build plan `docs/plans/oss-v0-1-0-publish-memory-pivot.md` (built `FileMemoryStore` at `framework/primary-persona/src/loam/primary_persona/file_memory.py`).

## §12 — Acceptance gate (pre-cycle conditions)

- [x] Master plan + Cycle 1 sealed (459c7fc).
- [x] WD confirmed at start (`pwd` returned `/Users/lukeivers/ivers-corp-pos-v2`).
- [x] No external runtime import of `memory_system` outside the directory itself (verified pre-cycle).
- [x] FBE.7 baseline tests green (7 of 7 named tests pass).
- [x] Full primary-persona suite green (544 of 544 pass).
- [x] No `graphiti_core` in any pyproject.toml (verified pre-cycle).
- [x] memory-system not in `install-from-source.txt` (verified pre-cycle).
- [x] memory-system removed from `framework/first-run-inventory.yaml::dedicated_venvs` (FBE.7 prior).

## §14 — Method-decision record

| Decision | Choice | Rationale |
|---|---|---|
| Owning component for cycle bookkeeping | `dev-sdlc` (`frozen_baseline: true`) | memory-system is being deleted; can't own its own seal. Cycle-1 precedent: dev-sdlc as bookkeeping owner with broad universal_paths admission. |
| Scope of rip-out | Delete `framework/memory-system/` entirely | Self-contained directory; no external `from memory_system` imports; the directory IS the graphiti integration. |
| Workspace-bootstrap edits | NOT in scope | Sealed component; FBE.7 already neutered (`memory-graphiti` not in `_SERVICE_KINDS`; mcp_json_writer not called). Re-opening a seal for dormant code below threshold. |
| Primary-persona edits | NOT in scope | Sealed component; FBE.7 verified production runtime path; AC.FBE.7.7 negative AC. |
| Self-upgrade probes.py docstring | NOT in scope | Sealed component; comment-only stale reference; below threshold for re-opening seal. |
| FBE.7 verification mechanism | Run named existing tests post-deletion | The 5 tests at AC.GRX.5 + the full primary-persona suite already exercise the FBE.7 path; running them after deletion is the verification. |
| D5 cross-session verification | Defer to Cycle 6 | Per master plan §3 Cycle 2 dependencies; Cycle 6 stranger-clone verification AC. |
| Cross-reference scrub of graphiti prose | Out of scope | Cycle 5 terminology-consistency + Cycle 6 feature-honesty audit catch surface-level prose. |
| `--amend` policy | NEW commits only | Per master plan §9 + `feedback_no_amend_in_agent_dispatches.md`. |
| Tag-push policy | NO tag push, NO remote push | Per dispatch + master plan §9. |

### Commit SHAs

| Commit | SHA | Description |
|---|---|---|
| 1 — plan-doc expand | `08ac5a0` | `docs(plans): v0.3.0 Cycle 2 — expand stub to sub-plan-doc` |
| 2 — source-edit (BASELINE; rip-out) | `b92aaea` | `chore(v0.3.0): Cycle 2 — delete framework/memory-system/ (graphiti rip-out)` |
| 3 — manifest | `3ce13cc` | `docs(plans): v0.3.0 Cycle 2 — manifest YAML` |
| 4 — apply auto-commit | `39094ea` | `chore(amend): v0-3-0-cycle-2-graphiti-ripout-and-fbe7 manifest+apply — dev-sdlc BASELINE+sidecar bump to b92aaea` |
| 5 — seal | `013553e` | `chore(seals): v0-3-0-cycle-2-graphiti-ripout-and-fbe7 — dev-sdlc at 39094ea` |
