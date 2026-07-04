# v1.10.0 HARD smoke writeup — on-demand adversarial review

**Date:** 2026-07-04. **Release:** v1.10.0 — MINOR increment over published
v1.9.1 (`next_MINOR(v1.9.1) = v1.10.0`). Objective: a loam user can get a
genuinely harsh, evidence-bound adversarial review of any artifact, on
demand. Promotes the pos3-local adversarial-review capability into canonical
as a NEW opt-in component + a discoverable SKILL.

**Staging topology:** built in an isolated worktree off `main`
(`/Users/lukeivers/loam-release-v1.10.0`, branch `release/v1.10.0`) so the
paused `feat/memory-redesign-s1a` tree in the canonical checkout was never
touched.

**Release content tip at smoke:** `33c56986` — the branch tip after the
component seal + lockstep bump + bookkeeping (this smoke-writeup commit lands
on top of it).
**Two-component seal window (Tier-0):** plan+manifest `639ca033`; feat
`f0b9301b`; apply `7b1da6c`; conformance fix `485fb4d8`; seal `99a1be9`
(reachable from HEAD). Lockstep bump `d4c24839`.
**Last published (Tier-0, git ref):** `v1.9.1` tag `8666c12` (ancestor of HEAD).
**Secret scan:** no secrets introduced. The promoted component is stdlib-only;
no `.env`, credential, or token file was added. The AR spawn leg uses the
sealed `loam_spawn_isolation` surface, which scrubs the environment.
**Subscription mode** — no `ANTHROPIC_API_KEY`; no `anthropic` SDK. The real
`claude -p` spawn (§4) used the subscription credential via the sealed surface.

**Aggregate verdict: GREEN.**

---

## §1 — Probe design

Full per-MINOR HARD smoke per `feedback_hard_smoke_per_minor_before_publish`:
a real cold-clone of the release content tip, a real editable install into a
fresh venv, the system binary exercised, the named capability's own real
spawn-isolated `claude -p` leg run end-to-end, and the touched-component +
ride-along regression suites — all against the cold-installed tree, not the
build worktree.

- Cold clone: `git clone -b release/v1.10.0 <worktree>` → fresh tree at
  `33c56986`.
- Fresh venv (pyenv Python 3.13.2) + `pip install -r install-from-source.txt`.
- Interpreter/keys: subscription mode, no API key.

## §2 — Cold-install evidence

`pip install -r install-from-source.txt` into the fresh venv: **exit 0**, no
errors. Every in-scope component installed at **1.10.0** (`loam-cli-1.10.0`,
`loam-primary-persona-1.10.0`, `loam-plugin-loam-skills-1.10.0`,
`loam-plugin-dev-sdlc-1.10.0`, `loam-amend-1.10.0`, … — the full in-scope
cohort). `pytest-9.1.1` present.

**System binary operational (release-process gate 7):**

- `loam --version` → `loam 1.10.0` (Tier-0, from the cold-install venv).
- `loam --help` → exit 0; lists every documented subcommand: `init`, `amend`,
  `release`, `odd-extract`, `onboard`, `pr-safety`, `project`, `migrate`,
  `guards`.

## §3 — Capability + regression suites (cold-install venv)

| Suite | Result |
|---|---|
| `framework/adversarial-review/tests/` (the named capability) | **56 passed, 1 skipped** |
| `plugins/loam-skills/tests/` (touched component — the SKILL + conformance) | **381 passed, 25 skipped** |
| `plugins/dev-sdlc/tests/` (ride-along — release + lockstep + amend machinery) | **396 passed, 7 skipped** |
| `framework/adversarial-review/tests/test_no_sealed_amendments.py` (seal fence) | **1 passed** |

The 1 skip in the AR suite is `test_AR_S_real_calibration_smoke` — env-gated
behind `AR_REAL_CALIBRATION` so the default suite is deterministic + offline
(the frame-judge test posture: the model leg is stubbed, everything else is
real). The real spawn leg is exercised directly at §4.

## §4 — Real spawn-isolated `claude -p` SMOKE (the named capability's own leg)

Ran the capability's real spawn path on the cold-installed tree:
`adversarial_review.spawn.run_isolated_critic(...)` → the sealed
`loam_spawn_isolation.spawn_isolated_claude` → a real isolated `claude -p`
subprocess (subscription mode, empty-strict-MCP isolation, env scrubbed).

```
SPAWN_AVAILABLE: True
in-tree spawn src resolved: True
  → <cold-clone>/framework/tools/loam-spawn-isolation/src
spawn returned: 'SMOKE_OK'
CONTAINS_SMOKE_OK: True
```

This is the load-bearing promotion-correctness proof: the pos3→canonical
path-surgery converted `spawn.py`'s out-of-tree absolute reach into an
in-tree relative sibling import, and it **resolves correctly on a fresh
clone** (`parents[4]/framework/tools/loam-spawn-isolation/src`), not only on
the maintainer's primary path. A real subscription-mode isolated review leg
returned its output — no hang, no `REVIEW INCONCLUSIVE`, no Telegram-kill
vector (isolation flags present).

## §5 — Seal evidence

- Seal commit: `99a1be9` (`chore(seals): adversarial-review-capability — adversarial-review+loam-skills at 485fb4d`).
- Sidecars (Tier-0): both `framework/adversarial-review/tests/SEAL_COMMIT` and
  `plugins/loam-skills/tests/SEAL_COMMIT` = `485fb4d8` (the content tip).
- Narrative: `framework/adversarial-review/seals/SEAL_COMMIT.adversarial-review`.
- Post-seal `loam amend apply --dry-run`: both components `ok` (clean).
- Two-component seal (adversarial-review NEW + loam-skills EXTEND); each
  seal-fence admits the other's partner prefix. The sealed
  `loam-spawn-isolation` surface is imported, never edited.

## §6 — Versioning + lockstep

- `test_AC_PCVR_pyproject_version_lockstep` GREEN (5 passed): `docs/ACTIVE_MINOR`
  1.10.0; the 31 in-scope pyprojects at 1.10.0; the new `adversarial-review`
  component at 0.1.0, out-of-lockstep per D-AR-LOCK (not in the in-scope set).
- `loam --version` reports `1.10.0` from the cold-install venv (the meta
  `--version` literal advanced in lockstep).

## §7 — Release-gate note (worktree staging)

`loam release v1.10.0 --dry-run` gate 5 (`branch-main`) is not satisfiable in
this worktree because the release is staged on `release/v1.10.0`, not `main`
(the merge-to-main + tag + push is the owner's publish run). Gates 1
(hard-smoke GREEN token — this writeup), 2 (ACs GREEN — plan §6 / §status),
3 (STATE marks v1.10.0 SHIPPED LOCAL), 6 (seal `99a1be9` reachable from HEAD),
and the migration-declared gate (`v1-10-0-adversarial-review.migration.yaml`,
`operation: no-op`) are all satisfied; gates 4/5 resolve at the owner's
publish run when the branch fast-forwards onto `main`.

## §8 — Verdict

**GREEN on all smoke dimensions.** Cold clone + real editable install at
1.10.0; system binary operational; the named capability's suite passes on the
cold-installed tree; a real subscription-mode spawn-isolated `claude -p`
review leg returned output with the in-tree isolation reach resolving on a
fresh clone; touched-component + ride-along regressions clean; seal clean.

The annotated LOCAL tag `v1.10.0` is cut on this evidence. The public tag push
+ `git push origin main` + the GitHub Release proceed ONLY under the owner's
explicit command — they were NOT run.
