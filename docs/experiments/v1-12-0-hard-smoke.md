# v1.12.0 HARD smoke writeup — per-session episodic resume + release-machinery hardening

**Date:** 2026-07-09. **Release:** v1.12.0 — MIXED MINOR increment over published v1.11.0 (`next_MINOR(v1.11.0) = v1.12.0`). Objective: make loam's episodic resume private to the channel-session that produced it (AC.PSR.1-8) and harden the machinery that ships loam itself (release-CLI tag-target/cut/preflight, shared-doc guard-floor coverage, brittle-guard intent conversion, FBM Tier-1 smoke supersession hard-exclude).

**Staging topology:** built DIRECTLY on `main` in the canonical tree (`/Users/lukeivers/loam`, single-writer this cycle). Because the release is on `main`, gate `branch-main` is satisfiable at dry-run.

**Release content tip at smoke:** `7faa5514` — HEAD after the five cycle seals + the lockstep bump (this smoke writeup + STATE/roadmap backfill land on top).
**Five-cycle seals (Tier-0, each window = own delta; all HEAD-reachable):**
- release-CLI tag-target/cut/preflight (AC.DOM/CUT/PRE): source `0f61d193` · apply `9e51a18e` · seal `c074dc18`.
- shared-doc guard-floor coverage (AC.SDG/SDC): source `c325e358` · apply `d5e7e63f` · seal `a8a34b47`.
- brittle exact-value guards → intent (AC.BVG): source `f610448d` + `0bcbe5b5` · apply `f4b3cf48` · seal `30a3aaef`.
- per-session episodic resume (AC.PSR.1-8): source `c290d211` · apply `c6de4247` · seal `0fa74f79`.
- FBM Tier-1 smoke supersession hard-exclude (AC.SMKSUP.1): source `ae461621` · apply `53c73f16` · seal `69a345ba`.

**Integration:** the five cycles landed LINEARLY on `main` in dependency-free order — NO reconciliation was needed (unlike v1.11.0). Each fence window contains only its own delta; each seal is reachable from HEAD.

**Last published (Tier-0, git ref):** `v1.11.0` tag `01001ba` (ancestor of HEAD).
**Secret scan:** no secrets introduced. All five cycles are stdlib-only source/test/doc edits; no `.env`, credential, or token file added.
**Subscription mode** — no `ANTHROPIC_API_KEY`; no `anthropic` SDK. The real `claude -p` spawn (§4) used the subscription credential via the sealed `loam_spawn_isolation` surface.

**Aggregate verdict: GREEN.**

---

## §1 — Probe design

Full per-MINOR HARD smoke per `feedback_hard_smoke_per_minor_before_publish`: a real cold-clone of the release content tip, a real editable install into a fresh venv, the system binary exercised, a real spawn-isolated `claude -p` leg end-to-end, an outcome-altitude fixture exercising the per-session-resume behavior at the production entry-point, and the touched-component + ride-along regression suites — all against the cold-installed tree.

- Cold clone: `git clone --no-local /Users/lukeivers/loam` → fresh tree, checked out to the release content tip `7faa5514`.
- Fresh venv (pyenv Python 3.13.2) + `pip install -r install-from-source.txt`.
- Interpreter/keys: subscription mode, no API key.

## §2 — Cold-install evidence

`pip install -r install-from-source.txt` into the fresh venv: **exit 0**, no errors. Every in-scope component installed at **1.12.0** — the cold-venv "any installed loam-* component NOT at 1.12.0" check returns empty (excluding the deliberate 0.0.0 out-of-scope measurement harnesses, which are not in the install-from-source graph).

**System binary operational (release-process gate 7):**

- `loam --version` → `loam 1.12.0` (Tier-0, from the cold-install venv `.smoke-venv/bin/loam` AND the maintainer system binary `which loam` → `/opt/homebrew/bin/loam`).
- `loam --help` → **exit 0**; lists the documented subcommands: `init`, `amend`, `release`, `odd-extract`, `onboard`, `pr-safety`, `project` (plus `migrate`, `guards`, `report`, `recover`, `audit`, `flow`, `init-intake`, `workspace`).

## §3 — Capability + regression suites (cold-install venv, release content tip `7faa5514`)

| Suite | Result |
|---|---|
| `framework/tools/loam/tests/` (touched — release-CLI dominance/cut/preflight) | **221 passed** |
| `plugins/dev-sdlc/tests/` (touched — guard-floor + smoke-supersession + ride-along release/lockstep/amend) | **399 passed, 7 skipped** |
| `framework/primary-persona/tests/` (touched — per-session resume) | **1432 passed, 1 skipped** |
| `framework/hands-off-lifecycle/tests/` (touched — brittle-guard intent conversion) | **743 passed, 5 skipped** |
| touched-component `test_no_sealed_amendments.py` / seal-diff-window fences | **pass** (each window = own delta only) |

**One environmental artifact, resolved (not a code defect, not a fence breach).** The first cold-tree hands-off-lifecycle run reported 12 failures, all in `test_AC_SE_4_corpus_load_sentinel_write.py` (and its siblings) with `FileNotFoundError: .../.venv/bin/python`. Root cause: those tests spawn a CLI subprocess at the hardcoded `REPO_ROOT/.venv/bin/python` path (the repo's expected venv location), but the cold clone's venv was named `.smoke-venv`. Providing `.venv` (a symlink to the smoke venv, the repo's own convention) cleared all 12 — the full suite then reports 743 passed / 5 skipped. The shipped code was never at fault; the assumption is a test-harness venv-location convention.

## §4 — Real spawn-isolated `claude -p` SMOKE

Ran a real subscription-mode isolated `claude -p` on the cold-installed tree via the mandated sealed surface `loam_spawn_isolation.spawn_isolated_claude` (empty-strict-MCP isolation injected, env token/API-key-scrubbed, isolation asserted before spawn):

```
import OK; spawn_isolated_claude present: True
returncode: 0
CONTAINS_SMOKE_OK_V1120: True
output: SMOKE_OK_V1120
```

A real isolated leg returned its exact token — no hang, no Telegram/Discord-kill vector (isolation flags present, `--strict-mcp-config`), subscription credential resolved on the cold tree.

## §5 — Outcome-altitude fixtures (production entry-points, no pre-set state)

Cold-tree, hitting production entry-points with no pre-arranged release state:

- **AC.PSR.6** `test_AC_PSR_6_OA_worker_stamps_session_key_from_record` (per-session resume — production worker stamps the session key from the record, no pre-set state): **passed** (within the cold-tree primary-persona suite, §3). The resume is scoped to its own channel-session key, not another simultaneous session's handoff.
- The release CLI itself (§6) is the second production entry-point exercised with no pre-set state: `loam release v1.12.0 --dry-run` runs the real 12-gate CLI end-to-end.

## §6 — Release-gate dogfood (this cut's own machinery)

The cut CONTAINS the release-CLI hardening (cycle 1), so the publish dogfoods its own new gates. `loam release v1.12.0 --dry-run` on the canonical tree runs all 12 `run_all` gates GREEN, including:

- **`seal-dominance`** — resolves `69a345ba` as the unique dominator of the five-seal §2 row (Tier-0: `c074dc18` / `a8a34b47` / `30a3aaef` / `0fa74f79` are all ancestors of `69a345ba`). This exercises the multi-seal `dominates` path, not the vacuous single-seal path — the meaningful dogfood of cycle 1's `check_seal_dominance`.
- **`deterministic-cut`** — recomputes the cut from origin's published `v1.11.0` + the unreleased conventional-commit prefixes: `class=MINOR expected=v1.12.0`, matching the target. `loam release preflight v1.12.0` corroborates (`class=MINOR expected=v1.12.0, breaking-markers=no`).

The public tag + `git push` + GitHub Release proceed ONLY under the owner's explicit command; they were NOT run.

## §7 — F-LEAK / F-TIMEOUT / F-VERIFY-ORPHAN ride-alongs

Window-scoped to the five cycles' feature source diffs (`0f61d193`, `c325e358`, `f610448d` + `0bcbe5b5`, `c290d211`, `ae461621`):

- **F-LEAK (MCP-config / settings.json write-surface):** **GREEN.** One added-line write hit — `tmp.write_text(content)` — resolves to `workspace/.loam/handoffs/<persona>.md` (an atomic write into a workspace user-state home, the per-session-resume secondary handoff). No added line writes `~/.claude` / `settings.json` / MCP config beyond the workspace boundary.
- **F-TIMEOUT (claude-print client / subprocess timeout):** **GREEN by construction.** No cycle touches `claude_print_client` / the synthesis client or its timeout config (zero matching added lines).
- **F-VERIFY-ORPHAN (un-isolated `claude` binary spawn):** **GREEN.** The four added `subprocess.run(...)` calls (release-CLI dominance/cut/preflight) all spawn `git` (`["git", *args]`, `["git", "merge-base", ...]`, `["git", "ls-files"]`) — none spawns the `claude` binary. The only real claude spawn path is the sealed `spawn_isolated_claude` surface (§4).

## §8 — Seal evidence (five fences)

- Five component seals, all HEAD-reachable: `c074dc18` (loam-cli), `a8a34b47` (dev-sdlc guard-floor), `30a3aaef` (dev-sdlc+hands-off-lifecycle brittle-guard), `0fa74f79` (primary-persona per-session resume), `69a345ba` (dev-sdlc smoke-supersession).
- Each fence seal-test passes with `BASELINE..SEAL_COMMIT` containing only that amendment's own delta.
- Post-lockstep-bump (canonical tree, HEAD `7faa5514`): loam-cli `test_no_sealed_amendments` 1 passed; dev-sdlc 2 passed; primary-persona 2 passed; hands-off-lifecycle seal-diff-window suite 15 passed — the plain lockstep bump trips NO fence (the pyproject version field is outside every guarded diff window).

## §9 — Versioning + lockstep

- `test_AC_PCVR_pyproject_version_lockstep` GREEN (5 passed): `docs/ACTIVE_MINOR` 1.12.0; the 31 in-scope pyprojects at 1.12.0; the two excluded 0.0.0 measurement harnesses unchanged; no out-of-graph component in the in-scope set.
- `loam --version` reports `1.12.0` from the cold-install venv AND the maintainer system binary (the meta `__version__` literal advanced in lockstep, commit `7faa5514`).
- Migration declared `no-op` (`docs/state-migrations/v1-12-0-per-session-resume-and-release-machinery-hardening.migration.yaml`): per-session resume adds only an optional workspace-home handoff file (read-back-safe, fail-soft to workspace-global); the four META-FRAMEWORK cycles touch build/release machinery only, no user-state.

## §10 — Verdict

**GREEN on all smoke dimensions.** Cold clone + real editable install at 1.12.0; system binary operational; the four touched-component suites pass on the cold-installed tree (the one hands-off-lifecycle env artifact was a test-harness venv-location convention, not a code defect); a real subscription-mode spawn-isolated `claude -p` leg returned its token; the outcome-altitude per-session-resume fixture passes at the production entry-point; the release-CLI dogfood runs its own dominance + deterministic-cut gates GREEN; F-LEAK / F-TIMEOUT / F-VERIFY-ORPHAN clean; five seals clean and HEAD-reachable; lockstep + migration honest.

The release is SEALED-LOCAL on this evidence. The public tag push + `git push origin main` + the GitHub Release proceed ONLY under the owner's explicit command — they were NOT run.
