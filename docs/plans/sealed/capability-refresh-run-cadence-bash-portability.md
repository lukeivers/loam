# Capability-refresh run-cadence.sh — bash portability fix

Slug: `capability-refresh-run-cadence-bash-portability`
Amendment: #194 (next sequential after #193
`capability-refresh-actions-cadence-migration`; confirmed at
`loam amend apply`).
Component: `framework/tools/capability-refresh` (sealed).

## §1 Objective

Make `framework/tools/capability-refresh/scripts/run-cadence.sh` execute
correctly on a POSIX environment where `zsh` is ABSENT (the Ubuntu Actions
runner), reaching its real `python3 -m capability_refresh` entry-point with
the repo-root working directory correctly resolved, while preserving
identical behaviour where it already works (macOS).

## §2 Predecessors / context

Composes against `capability-refresh-actions-cadence-migration` (#193),
which added `.github/workflows/capability-refresh.yml` and the
`LOAM_REFRESH_NO_COMMIT` opt-in to `run-cadence.sh`. That workflow runs the
script on `ubuntu-latest`, which has no `zsh`. The script's shebang
(`#!/bin/zsh`) and its line-16 `SCRIPT_DIR="${0:A:h}"` (zsh-only parameter
expansion) both fail there — the script dies with `cannot execute: required
file not found` (exit 127) before doing any work. The refresh logic itself
is correct; only the runner script's shell portability is broken.

Root cause (Tier-0, CI log): the interpreter `/bin/zsh` is absent on the
Ubuntu runner (the kernel cannot exec the shebang), and `${0:A:h}` (`:A`
absolute-with-symlinks-resolved, `:h` head/dirname) is a zsh-only
expansion with no bash equivalent.

## §3 Scope

In scope:
- `framework/tools/capability-refresh/scripts/run-cadence.sh` — change the
  shebang to a portable bash interpreter; replace the zsh-only `${0:A:h}`
  with a POSIX/bash script-dir resolution.
- New AC tests under `framework/tools/capability-refresh/tests/`.

Out of scope (halt-and-surface if it appears necessary):
- Any change to the refresh logic (`src/capability_refresh/**`).
- Any change to `.github/workflows/capability-refresh.yml` (the workflow is
  already correct; it invokes the script — the script is what must be
  fixed).
- Installing `zsh` in CI (explicitly rejected — the fix is script
  portability, not runner mutation).
- Any zsh-only construct BEYOND the shebang + line 16 (if a third is found,
  HALT per §6).

## §4 Acceptance criteria

AC family `CRSP` = Capability-Refresh Shell Portability.

| AC | Outcome | Verification |
|----|---------|-------------|
| **AC.CRSP.1 ★** (outcome-altitude) | The script, executed via its own shebang under a PATH from which `zsh` is genuinely absent, reaches `python3 -m capability_refresh --cadence-class <CLASS>` with the working directory correctly resolved to the repo root and `PYTHONPATH` including the component `src`. | Execute the REAL fixed script through its shebang with a controlled zsh-free PATH (real `bash`+`dirname` symlinked in; `python3`/`git` stubbed to capture argv/cwd/PYTHONPATH and do no I/O). Assert exit 0, cwd captured == repo root, PYTHONPATH contains the component `src`, argv == `-m capability_refresh --cadence-class all`. The test asserts `zsh` is unresolvable on the constructed PATH as a precondition, so the "zsh absent" condition is real, not assumed. |
| **AC.CRSP.2** (regression) | The zsh-only script-dir form (`${0:A:h}`) fails to resolve the repo root under bash while the fixed form resolves it — a shell-portability break cannot silently return. | Run the fixed form and a zsh-only-form variant (both under `bash`, zsh-free PATH). Fixed form reaches the entry-point (capture written, repo-root correct); the zsh-only form does NOT reach the entry-point (errors at the `${0:A:h}` expansion before `python3`). Plus a shebang tripwire: the fixed shebang resolves to bash via `env`, never a hardcoded `#!/bin/zsh`. |
| **AC.CRSP.3** (behaviour-preservation) | `set -euo pipefail` semantics and `LOAM_REFRESH_NO_COMMIT=1` behaviour are preserved by the fix; no macOS behaviour change. | (a) With corpus changes present (git stub: `diff --quiet` exit 1) and `LOAM_REFRESH_NO_COMMIT=1`, the script exits 0 via the no-commit branch and NEVER invokes `git add`/`git commit` (git stub logs calls). (b) With the required `$1` argument absent, `${1:?…}` under `set -e` exits non-zero and `python3` is NOT reached (the strict-mode guard is intact). |

Ladder-up: AC.CRSP.1-3 keep the capability-refresh RUN binding (the
deterministic corpus refresh) actually executable in its production runner,
which serves the corpus-currency protection floor (AC.CLP-CUR.*) that
ladders up to VALUE_PROPOSITION AC.PO.1/PO.2 (loam protecting the user from
stale/invented capability facts by keeping the corpus current).

## Primitive check

No new mechanism introduced. This is a shell-portability fix to an existing
script; the cadence binding (GitHub Actions `schedule`, the native Claude/CI
primitive) was already selected and built in #193 and is unchanged.

## §5 Sealed-component fence

Single component: `framework/tools/capability-refresh`.
- `seal_test`: `framework/tools/capability-refresh/tests/test_no_sealed_amendments.py`
- `sidecar`: `framework/tools/capability-refresh/tests/SEAL_COMMIT`
- The seal test already admits `framework/tools/capability-refresh/`,
  `docs/plans/`, `docs/STATE.md`, `docs/release-roadmap.md` — every path
  this amendment touches. No new prefix admission required.
- BASELINE advances to `a1166b8d` (HEAD at plan authoring) at apply.

## §6 Halt triggers

- More than the shebang + the one zsh-only line (`${0:A:h}`) requires
  change (a third zsh-only construct surfaces).
- The seal test fails for a reason unrelated to this edit (a pre-existing
  fence breach surfaced by the sweep).
- A surrounding-code ODD violation surfaces while editing.
- The seal mechanics differ from the standard apply→seal cycle.

## §7 Ship shape

Single amendment, single seal cycle. Commit ladder:
1. `docs(plans):` — this plan + manifest (before code).
2. `fix(capability-refresh):` — the script portability edit + the three AC
   tests.
3. `chore(amend): … apply` — `loam amend apply`.
4. `chore(seals): …` — `loam amend seal`.
5. `docs(plans):` — §14 SHA backfill.

DO NOT PUSH. Seal locally on the worktree branch; the owner holds the push
(public repo).

## §14 Method-decision register

- **D-CRSP.1 — shebang → `#!/usr/bin/env bash`.** `env`-resolved bash is
  present on both Ubuntu and macOS; more portable than a hardcoded
  `/bin/bash` and correct for the bash-3.2 feature set the script uses
  (`set -euo pipefail`, `[[ ]]`, `${var:?}`, `${var:+}`, `${var:-}` — all
  bash-3.2-safe).
- **D-CRSP.2 — `${0:A:h}` → `$(cd "$(dirname "$0")" && pwd)`.** The standard
  portable script-dir idiom; matches the adjacent line-17 `cd … && pwd`
  convention already in the script. In the real invocation (CI checkout /
  macOS repo path, symlink-free) it yields the identical directory `:A:h`
  produced, so REPO_ROOT is unchanged and macOS behaviour is preserved.
- **D-CRSP.3 — no other change.** Every other construct in the script
  (`set -euo pipefail`, `[[ ]]`, `${1:?}`, `${PYTHONPATH:+…}`,
  `${LOAM_REFRESH_NO_COMMIT:-0}`) is bash-compatible and left byte-identical.
- **D-CRSP.4 — line-24 `status=$?` incidentally corrected by the shebang
  change; no extra edit.** A THIRD zsh-incompatibility exists at line 24:
  `status` is a read-only special parameter in zsh, so `status=$?` errors
  (`read-only variable: status`) under the old `#!/bin/zsh`. Under bash
  `status` is an ordinary variable, so the D-CRSP.1 shebang change resolves
  it with no change to line 24. Because the fix needs no MORE than the
  two named lines, this does NOT trip the §6 halt trigger. See §16 for the
  F2 correction on the "works on macOS" framing.

Commit SHAs backfilled at seal via `loam amend seal --plan-doc`.

## §15 Backwards-compat verification

- The existing capability-refresh suite
  (`test_AC_CLP_CUR_*`, `test_AC_CLP_MDL_*`, `test_AC_CRAC_*`,
  `test_no_sealed_amendments.py`) must still pass (no source touched beyond
  the two script lines; these tests do not read the script).
- The seal guard-sweep floor (`docs/plans/guard-floor.yaml`) must pass.

## §16 Halt-and-surface findings

- Observed at authoring (surfaced, not blocking): the component's
  `tests/SEAL_COMMIT` (`f197050a…`) is not an ancestor of current `main`
  (`a1166b8d`) — a pre-existing artifact of the pos3→canonical history
  sync. The current seal test still passes (its BASELINE `d6d65c2b` IS an
  ancestor and the diff window resolves). This amendment's apply/seal
  rewrites both BASELINE and SEAL_COMMIT to commits in this branch, so the
  condition does not affect the cycle. Noted for the dispatcher.
- **F2 correction on the dispatch framing (surfaced, not blocking):** the
  brief states the fix should preserve "identical behavior where it already
  works (macOS)." Evidence (`zsh -c 'status=0'` → `read-only variable:
  status`; the same error reproduced by executing the pre-fix script under
  `/bin/zsh` on this macOS at line 24 after the entry-point was reached)
  shows the pre-fix script would ALSO die under zsh at line 24 whenever the
  refresh actually ran — so it did not fully "work" on macOS either. This
  never surfaced operationally because the launchd fallback died earlier at
  `python3 -m capability_refresh` (`ModuleNotFoundError: yaml` under the
  Xcode Python 3.9, per #193), before line 24. Net operational effect
  (the refresh never landed) is unchanged, so the fix objective stands; the
  bash port makes the whole script correct (verified: the fixed script runs
  past line 24 to completion under bash in AC.CRSP.1/3a). Surfaced for the
  dispatcher's record.

# Capability-refresh run-cadence.sh bash-portability fix — apply ladder

Extension of the capability-refresh component (plan
`docs/plans/claude-leverage-program-s1-currency.md`; RUN migration
`capability-refresh-actions-cadence-migration` #193). Fixes the shell
portability of the cadence runner so the #193 GitHub Actions binding
actually executes on ubuntu-latest.

Root cause (Tier-0, CI log): `run-cadence.sh` shipped with a
`#!/bin/zsh` shebang and a zsh-only line-16 `SCRIPT_DIR="${0:A:h}"`.
The Ubuntu runner has no zsh, so the kernel cannot exec the shebang
(`cannot execute: required file not found`, exit 127) and the refresh
never runs. macOS (which ships /bin/zsh) was unaffected — which is why
the defect only surfaced in CI.

This amendment (portability only; refresh logic byte-unchanged):
  1. shebang → `#!/usr/bin/env bash` — present on both Ubuntu and
     macOS, correct for the script's bash-3.2-safe feature set
     (`set -euo pipefail`, `[[ ]]`, `${var:?}`, `${var:+}`,
     `${var:-}`).
  2. `${0:A:h}` → `$(cd "$(dirname "$0")" && pwd)` — the standard
     portable script-dir idiom, matching the script's own adjacent
     line-17 `cd … && pwd`. Symlink-free real invocation yields the
     same directory, so REPO_ROOT and all downstream behaviour are
     unchanged on macOS.

AC.CRSP.1 ★ (outcome-altitude): the fixed script is EXECUTED through
its own shebang under a genuinely zsh-free PATH and proven to reach
`python3 -m capability_refresh` with the repo root correctly resolved —
not verified by source inspection.

`set -euo pipefail` and the `LOAM_REFRESH_NO_COMMIT=1` opt-in from #193
are preserved. NO Anthropic API key involved. NO public-action steps —
the fix is a repo file; it is sealed LOCALLY on the worktree branch and
the owner holds the push. BASELINE `a1166b8d`; counter 194 confirmed at
apply.
