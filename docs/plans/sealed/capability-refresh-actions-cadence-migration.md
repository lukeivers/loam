# Capability-refresh RUN migration to GitHub Actions — apply ladder

Extension of the capability-refresh component (sealed `c41f9473`, plan
`docs/plans/claude-leverage-program-s1-currency.md`; last SEAL_COMMIT tip
`2a7f62c5` from `capability-refresh-model-lineup`). Executes the RUN-side
migration ratified in
`workspace/strategy/capability-refresh-delivery-architecture-2026-07-02.md`
— the NEW authority reversing the 2026-06-14 cloud-routine activation.

Root cause fixed: both prior cadence bindings separated the runner from
the commit target. The cloud routine had compute-but-no-write (403s;
zero commits landed in ~18 days). The laptop launchd job had
write-but-no-guaranteed-runtime and a fragile Xcode Python 3.9 (dead for
weeks; `ModuleNotFoundError: yaml`). GitHub Actions has native
`GITHUB_TOKEN` write, guaranteed uptime, pinned deps, and visible failure.

This amendment:
  1. Adds `.github/workflows/capability-refresh.yml` (the repo's FIRST
     workflow): daily + weekly `schedule` crons matching the
     high-velocity / long-form cadence classes, plus `workflow_dispatch`.
     The run step invokes the existing deterministic
     `run-cadence.sh`; per ratified decision (2) the post-refresh step
     OPENS A PULL REQUEST against main (native git + `gh`, GITHUB_TOKEN;
     no third-party action) and NEVER auto-lands to main (AC.CRAC.1/2).
  2. Adds a backward-compatible `LOAM_REFRESH_NO_COMMIT` opt-in to
     `run-cadence.sh` so the CI/PR runner runs the refresh without
     committing (the PR step owns the commit). Default behavior — the
     local launchd fallback's local commit — is unchanged (D-CRAC.2).
  3. Re-authors the `http.client.IncompleteRead` catch in `fetch.py`
     (stranded in the unreachable cloud commit): a truncated HTTP body
     read now raises `FetchError` -> the entry is marked stale, never
     silently current (AC.CRAC.3 ★ outcome-altitude; the existing
     AC.CLP-CUR.5 protection floor). Unit test drives the production
     `fetch_source` with a patched `urlopen` whose `read()` raises
     `IncompleteRead`.
  4. Retires the old bindings in `cadence/routine-spec.md` +
     `cadence/ACTIVATION.md`: Actions-cron is the primary binding; the
     cloud routines are RETIRED (18-day zero-commit failure record);
     launchd is a documented-INACTIVE fallback that MUST use the
     component venv (not bare `python3`) + a failure signal if ever
     re-activated (AC.CRAC.4).
  5. Lands this morning's manual refresh output under
     `docs/capability-corpus/` (AC.CRAC.5).

★ AC.CRAC.3 (outcome-altitude): the fetch fix is verified through the
real `fetch_source()` entry-point with no pre-arranged state.

NO public-action steps in this amendment — the workflow exists only as a
repo file (it cannot fire until it is on main). The actual cloud-routine
deletion (interactive `/schedule` / web console) and the `launchctl
bootout` of the two launchd jobs are named owner/system actions carried
in the plan §7 + the cycle report, not repo commits.

NO Anthropic API key (all fetches are plain HTTP via urllib; the workflow
runs the deterministic no-LLM refresh). BASELINE `d6d65c2b` (HEAD at plan
authoring); counter 193 confirmed at apply.
