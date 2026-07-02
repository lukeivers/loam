# Capability-refresh — RUN migration to GitHub Actions + fetch fix + binding retirement

> **Status:** sub-plan-doc (amendment cycle). Plan-before-code gate for the
> RUN-side migration ratified in
> `workspace/strategy/capability-refresh-delivery-architecture-2026-07-02.md`
> (the NEW authority; it reverses the 2026-06-14 cloud-routine activation).
> **WD:** `/Users/lukeivers/loam` (canonical loam).
> **Component fence (sealed):** `framework/tools/capability-refresh/`.
> **Design authority:** the architecture doc above, §3 (RUN) + §6 (migration).
> **Predecessors:** Slice-1 sealed `c41f9473` (the refresh engine + cadence
> machinery); `capability-refresh-model-lineup` (2a7f62c5, the current
> SEAL_COMMIT sidecar tip).
> **BASELINE candidate:** `d6d65c2b` (HEAD of main at plan authoring; builder
> confirms at apply time).

---

## §1 Objective

Move the deterministic capability-corpus refresh RUN off the two failed
bindings (Anthropic cloud routine + local launchd) onto a **GitHub Actions
scheduled workflow** in `lukeivers/loam`, where the runner has native write
access to the commit target. Per the ratified decision (2), a scheduled
refresh **opens a pull request** for owner review — it never auto-lands to
`main`. Re-author the `http.client.IncompleteRead` fetch fix that was
stranded in the unreachable cloud commit. Retire the old bindings and record
the new reality in the component's cadence docs. Land this morning's manual
refresh output.

Every change traces to a ratified migration step; no scope creep beyond §3.

## §2 Ratified decisions carried in (recorded before build)

1. **RUN moves to a GitHub Actions cron in `lukeivers/loam`** — reverses the
   2026-06-14 cloud-routine activation (the architecture doc is the new
   authority). Owner-ratified.
2. **Scheduled refreshes OPEN A PR, never auto-land to main.** `workflow_dispatch`
   is the manual verification path.
3. **Cloud routines retired; launchd demoted to documented-INACTIVE fallback**
   (must use the component venv, not bare `python3`, if ever re-activated).

## §3 Scope / fence

**In-fence (this amendment):**

- `framework/tools/capability-refresh/src/capability_refresh/fetch.py` — the
  `IncompleteRead` catch (re-authored) + its unit test.
- `framework/tools/capability-refresh/scripts/run-cadence.sh` — a
  backward-compatible `LOAM_REFRESH_NO_COMMIT` opt-in so the CI/PR runner can
  run the refresh without committing (the PR step owns the commit).
- `framework/tools/capability-refresh/cadence/ACTIVATION.md` +
  `cadence/routine-spec.md` — record Actions-cron as primary; cloud routines
  RETIRED; launchd documented-INACTIVE fallback + the venv-not-bare-python3
  hardening note.
- `.github/workflows/capability-refresh.yml` — NEW (repo has no workflows
  today). Admitted as a universal prefix `.github/workflows/` for this
  amendment (repo-level infra, not component source).
- `docs/capability-corpus/**` — this morning's refresh output (already in the
  working tree from a manual re-run) + any regenerated corpus state.

**System actions (not repo commits; reported, not sealed):**

- `launchctl bootout` the `com.loam.capability-refresh-daily` +
  `-weekly` jobs.

**Out of fence (surfaced, NOT done here):**

- Deleting the two Anthropic cloud routines (`trig_018DZTYo…`, `trig_01R27t…`)
  — that needs the interactive `/schedule` surface / web console, which a
  repo builder cannot reach. Named in §7 as a remaining owner/primary-session
  action; the repo-side binding (the docs) IS retired here.
- The weekly `knowledge-pack render` step inside the workflow (architecture
  doc §5). Deferred: it is not in the dispatch's enumerated Part A, and
  keeping the first workflow to run-cadence.sh only keeps the PR reviewable.
  Named follow-on (§7).

## §4 Named decisions (recommendation IS the decision)

- **D-CRAC.1 — PR mechanism = native `git` + `gh` (GITHUB_TOKEN), not a
  third-party action.** Avoids a supply-chain dependency; the dispatch says
  "committing via the native GITHUB_TOKEN." The workflow branches, commits the
  corpus diff, pushes, and `gh pr create`s against `main`.
- **D-CRAC.2 — run-cadence.sh reuse via `LOAM_REFRESH_NO_COMMIT` opt-in.** The
  dispatch says "run the existing deterministic run-cadence.sh." The script
  commits by default (unchanged for the launchd fallback); the CI sets the env
  var so the PR step owns the commit. Backward-compatible.
- **D-CRAC.3 — cron in UTC with a DST note.** GitHub cron has no TZ. Daily
  `37 12 * * *` (≈06:37/07:37 America/Chicago across DST); weekly
  `37 13 * * 0`. Off-peak minute per the architecture doc §3.3 mitigation.
- **D-CRAC.4 — fetch fix catches `http.client.IncompleteRead` specifically**
  (the stranded fix), routed to `FetchError` so the entry is marked stale,
  never silently current (the existing AC.CLP-CUR.5 protection floor).

## §5 Acceptance criteria (`AC.CRAC.*`; outcome-shape, method is builder's call)

- **AC.CRAC.1** — A workflow at `.github/workflows/capability-refresh.yml` has
  (a) a daily cron, (b) a weekly cron, (c) `workflow_dispatch`, and its run
  step invokes `run-cadence.sh` with the class matching the trigger.
  *Verify:* parse the YAML; assert the three triggers + the run-cadence.sh
  invocation.
- **AC.CRAC.2** — A scheduled/dispatched run opens a PR against `main` via the
  native `GITHUB_TOKEN` and NEVER pushes corpus changes to `main` directly.
  *Verify:* the workflow's post-refresh step creates a branch + `gh pr create`;
  no step pushes to `main`; the refresh runs in `LOAM_REFRESH_NO_COMMIT` mode.
- **AC.CRAC.3 ★ (outcome-altitude)** — A real call to the production
  `fetch_source()` entry-point against a source whose body read raises
  `http.client.IncompleteRead` yields a `FetchError` (stale-mark path), not a
  propagated raw exception. *Verify:* a unit test drives `fetch_source` with a
  patched `urlopen` whose `read()` raises `IncompleteRead`; asserts
  `FetchError`.
- **AC.CRAC.4** — `routine-spec.md` + `ACTIVATION.md` state Actions-cron as the
  primary binding, cloud routines as RETIRED, and launchd as
  documented-INACTIVE fallback that must use the component venv (not bare
  `python3`) if re-activated. *Verify:* both docs carry the new reality; the
  launchd daily+weekly jobs are booted out (system action, reported).
- **AC.CRAC.5** — This morning's refresh output is committed on the branch
  (lands in the PR). *Verify:* `docs/capability-corpus/` diff is committed.
- **AC.CRAC.S** — seal-diff fence invariant (in-fence only).

## §6 Build steps (method-level; builder's call per ODD §1.1)

1. Plan-doc + manifest commit (this doc + `.manifest.yaml`) — plan-before-code.
2. `fix(capability-refresh):` — re-author the `IncompleteRead` catch in
   `fetch.py` + add the unit test; run the touched tests.
3. `feat(capability-refresh):` — the Actions workflow + `run-cadence.sh`
   `NO_COMMIT` opt-in + the two cadence docs (retirement + hardening note).
4. `chore(corpus):` — commit this morning's refresh output.
5. `loam amend apply` (against committed HEAD) → `loam amend seal`.
6. `launchctl bootout` the two launchd jobs (system action).
7. `docs(plans):` §14 SHA backfill + STATE.md + roadmap §8.
8. Open the PR against `main`; STOP (owner reviews + merges).

## §7 Out of scope / remaining owner actions

1. **Delete the two cloud routines** (`trig_*`) — interactive `/schedule` /
   web console; a repo builder cannot reach the routines API. The repo-side
   binding is retired here; the actual routine deletion is an
   owner/primary-session action.
2. **Weekly `knowledge-pack render` step in the workflow** (architecture §5) —
   named follow-on; not in Part A's enumerated scope.
3. **60-day-inactivity keepalive** (architecture §3.3 risk 1) — loam's commit
   rate makes it near-impossible to hit; residual risk named, not built.
4. **The real `workflow_dispatch` verification run** — a post-merge owner step
   (the workflow file cannot fire until it is on `main`).

## §8 Halt triggers (in-flight)

1. A step about to perform a public action without a recorded owner approval →
   HARD STOP. (Part A performs none; the workflow only exists as a file.)
2. The fetch fix cannot be verified by a real-run unit test → halt.
3. An AC would ship partial → name the gap, do not ship a weaker variant.
4. Out-of-fence drift discovered mid-edit → halt + surface the fence widening.

## §9 Bookkeeping

- `docs/STATE.md` change-log entry; `docs/release-roadmap.md` §8 register row.
- §14 SHA backfill after seal.
