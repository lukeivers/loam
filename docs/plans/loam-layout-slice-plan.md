# `.loam/` workspace-layout slice plan (loam v-next Phase-1, slice P1.2)

**Status:** slice plan-doc (plan-before-code per the v-next build workflow)
**Working dir:** `/Users/lukeivers/loam` (canonical loam)
**Date:** 2026-05-31
**Workflow:** `docs/plans/loam-vnext-build-workflow.md` (per-slice loop)
**Master plan / slice row:** `docs/plans/loam-vnext-build-plan.md` §6 row P1.2
**Predecessor slice:** P1.1 FBM-LIVE (`docs/plans/fbm-live-slice-plan.md`, disposition `leave`)
**Boundary def:** master plan §2 + §3 decision #1 (framework ↔ user-meaningful-state)

---

## Objective
Define + establish the COMPLETE, clean `.loam/` workspace layout that holds
the user's meaningful state behind the framework↔user-state boundary — so
every later mechanism (migration engine + cursor, onboarding seed, user-model,
config, session-model, per-user environment/perception model) has a declared
on-disk home. Largely STRUCTURE + a documented contract, not heavy code.
Additive over the live tree; the boundary holds; the migration is recorded.

---

## Step 1 — EXAMINE (ground truth from the live tree + git refs, NOT the plan's assumptions)

Inspected the two distinct `.loam/` trees empirically.

### A. The LIVE user-state `.loam/` — `/Users/lukeivers/pos3/workspace/.loam/`
```
.loam/
├── claude_p_policy.toml          # claude -p isolation policy (workspace-scoped user-state)
└── memory/                       # FBM episode store — LIVE, 1,283 episodes, active
    ├── .access-log.jsonl         # 477 KB, updated today 11:09
    ├── search-index.sqlite       # 7.1 MB, updated today 11:14
    └── episodes/pos3/            # 1,283 episode files
```
- **LIVE and active** — index + access-log mtimes are today; FBM writer hooks
  (P1.1) are firing into it. This tree is the 1,282+-episode store the dispatch
  says to LEAVE untouched. **Confirmed: do not redefine or move it.**
- Adjacent workspace user-state already lives in a *sibling* dir `.pos/`
  (NOT inside `.loam/`): `memory-write-queue/`, `memory-writes.log`,
  `last-turn-id`, `first-run.state`, `sync/`, `sync-config.yaml`,
  `trait-reflection/`. This is pre-existing user-state outside `.loam/`. **The
  layout contract must NOT claim to absorb or relocate `.pos/`** — that would be
  a destructive move (G★) and is explicitly out of scope. The contract DECLARES
  `.loam/` as the home for *new/future* state homes and documents that `.pos/`
  is legacy sibling user-state left in place.
- Global user-state lives at `~/.claude/` (CLAUDE.md, OBJECTIVES.md, projects/) —
  the other half of the boundary per §3 decision #1. Untouched by this slice.

### B. The BUILD-SIDE `.loam/` — `/Users/lukeivers/loam/.loam/`
```
.loam/
├── build-cursor.md                          # v-next build position cursor
└── migrations/
    └── fbm-live-slice.migration.yaml         # P1.1's declared migration (no-op)
```
- This is NOT a live user-state store — canonical loam's `.loam/` has no
  `memory/`. It holds the **v-next build's own bookkeeping** (the position
  cursor + the per-slice declared migrations).

### C. Scaffolding reality
- `framework/workspace-bootstrap/.../new_workspace.py` scaffolds `framework/`,
  `workspace/`, `.claude/` — it does **NOT** scaffold `.loam/` today. There is
  no existing declared `.loam/` layout contract. Disposition for the contract
  itself is therefore **build-new**; for the live `memory/` tree it is **leave**.

### D. F2 — a real defect carried in from P1.1 (named, evidenced, alternative)
- **Disagreement:** P1.1's record step is recorded as done, but its build-cursor
  and migration file are **not in git**. **Evidence:** `git check-ignore -v`
  shows both matched by `.gitignore:56` (`.loam/`); `git ls-files
  --error-unmatch` errors on both; commit `8ae3d7b` (`git show --stat`) contains
  ONLY `docs/plans/fbm-live-slice-plan.md` — the cursor + migration were silently
  dropped by the ignore. **Root cause:** `.loam/` is correctly gitignored as
  user-state (per the boundary), but the v-next BUILD-METHODOLOGY artefacts
  (position cursor + the declared-migrations *contract*) were placed inside that
  same ignored path, so they cannot be committed. The dispatch itself says "the
  `.loam/` user-state itself is gitignored" while also requiring the migration be
  committed — those two are in tension and P1.2 (the layout-contract slice) is
  exactly where it's resolved. **Alternative (the DEFINE decision below):** give
  the build-side migration *contract* a tracked home under `docs/`
  (`docs/state-migrations/`), keep the live user-state `.loam/` gitignored, and
  document the split in the layout contract. See DEFINE decision #2.

**Disposition:** `build-new` for the layout-contract + the build-side migration
home; `leave` for the live `memory/` tree (additive only, never disturbed).

---

## Step 2 — DEFINE (the clean target behind the boundary)

### The `.loam/` layout contract (per-workspace user-state)

`.loam/` is the **per-workspace user-meaningful-state** root (§3 decision #1:
`~/.claude/` = global user-state; `<workspace>/.loam/` = workspace-scoped).
Framework code never lives here. The declared layout:

```
<workspace>/.loam/
├── README.md                  # self-describing contract (this layout, the boundary rule)
├── memory/                    # [EXISTS — LEAVE] FBM episode store + index + access-log
│   ├── episodes/<ws>/         #   live; 1,283 episodes; never disturbed by this slice
│   ├── search-index.sqlite
│   └── .access-log.jsonl
├── migrations/                # applied-migration CURSOR home (runtime, user-state side)
│   └── .cursor                #   which declared state-migrations this workspace has applied
│                              #   (the migration ENGINE that reads/writes it is P1.3)
├── user-model/                # HOME for the per-user model + config (P1.5 fills it)
│   └── .gitkeep
├── session-model/             # HOME for the session-model (later slice fills it)
│   └── .gitkeep
└── environment-model/         # HOME for the per-user environment/perception model (later)
    └── .gitkeep
```

- `claude_p_policy.toml` (already present in the live tree) is workspace-scoped
  user-state and stays at `.loam/` root — documented in the README, left in place.
- `.pos/` is acknowledged in the README as **legacy sibling user-state** left in
  place; this slice does not absorb it (would be a destructive move → G★).
- The HOME dirs (`user-model/`, `session-model/`, `environment-model/`) are
  declared+created empty (`.gitkeep`) so later slices have a defined place to
  write. Declaring the home is the slice's job; filling it is the later slice's.

### Two migration locations — the build-side CONTRACT vs the user-side CURSOR (decision #2)

The boundary cleanly separates them and resolves the F2 defect:

| Artefact | What it is | Side of boundary | Home | Tracked? |
|---|---|---|---|---|
| **Declared migration files** (`<slug>.migration.yaml`) | The framework-shipped, author-declared "what a release changes in user-state" contract — release-gate input (P1.3/G4). Identical for every user. | **Framework** | `docs/state-migrations/` (tracked) | **yes** |
| **The applied-migration cursor** (`.cursor`) | Per-workspace runtime record of which declared migrations THIS workspace has applied. Unique per user. | **User-state** | `<workspace>/.loam/migrations/.cursor` | no (gitignored) |
| **The build position cursor** (`build-cursor.md`) | The v-next build's own "you are here" — build methodology, not a shipped user-state. | **Framework / build docs** | keep at `.loam/build-cursor.md` for continuity, BUT mirror/move under a tracked path so it is committable (see below) | needs tracked home |

**Resolution of the F2 ignore-trap:** the declared migration *files* are a
framework contract → they move to a tracked `docs/state-migrations/` dir (P1.1's
`fbm-live-slice.migration.yaml` migrates there as a corrective). The per-workspace
`.cursor` is genuine user-state → stays under the gitignored `.loam/migrations/`.
This is the §2 F2 "two migration systems / don't conflate" boundary made physical:
the *contract* (framework) is tracked; the *applied-state cursor* (user) is not.
The build position cursor is build-methodology and gets a tracked home too
(this slice moves it to `docs/plans/build-cursor.md` and leaves the live
`.loam/build-cursor.md` as the working copy if useful, OR makes the docs path
canonical — see BUILD; recommend canonical-under-docs, drop the ignored copy).

### Outcome-altitude acceptance criteria (cold-walk standard — invoke against a fresh tree, no pre-arranged state)

- **AC-LOAM-LAYOUT-1 (outcome-altitude:true)** — Establishing the layout against
  a *fresh* (empty) workspace root produces the complete declared `.loam/`
  structure: `README.md`, `migrations/`, `user-model/`, `session-model/`,
  `environment-model/` all present; verified by running the establish step on a
  brand-new temp dir with no pre-seeded `.loam/` and asserting every declared
  path exists. (No reliance on the live pos3 tree.)
- **AC-LOAM-LAYOUT-2 (outcome-altitude:true)** — The layout is **self-describing**:
  `.loam/README.md` exists, names every declared dir + its purpose, and states the
  boundary rule (user-state only; no framework code). Verified by reading the
  README out of a freshly-established tree and asserting each declared dir is
  documented.
- **AC-LOAM-LAYOUT-3** — **Boundary holds / additive on live state:** establishing
  the layout writes nothing under `framework/`, and the live pos3 `memory/` tree
  (episode count + index mtime) is byte-for-byte unchanged. Verified by a
  before/after check of the live `memory/` (episode count == 1283±live-drift,
  no file removed) and a `framework/`-write probe (zero writes).
- **AC-LOAM-LAYOUT-4** — **Idempotent + fail-safe:** running the establish step
  twice on the same tree is a no-op the second time (never overwrites an existing
  `memory/`, `README.md`, or `.cursor`); a pre-existing `memory/` is detected and
  left intact. Verified by establishing twice and asserting the live-shaped dirs
  are untouched on the second run.
- **AC-LOAM-LAYOUT-5** — **Migration recorded (release-gate input):** this slice
  declares a migration file under the tracked `docs/state-migrations/` home
  describing what a fresh `.loam/` init creates (structural-only is a valid
  declared migration). Verified by the file's presence + parse.

Method (the establish mechanism — a small idempotent scaffold helper) is the
builder's call (ODD); the ACs pin the outcome, not the implementation.

---

## Step 3 — BUILD (plan)

1. **Establish helper.** Add a small idempotent `.loam/`-layout establish function
   (compose on `workspace-bootstrap`'s scaffolding precedent; minimal code). It
   creates the declared dirs + `README.md` only if absent; it NEVER touches an
   existing `memory/`. This is the AC-1/AC-4 entry point.
2. **`.loam/README.md` contract** — written into the live pos3 `.loam/` AND
   produced by the establish helper for fresh trees. Self-describing (AC-2).
3. **Create the HOME dirs** in the live pos3 `.loam/` additively: `user-model/`,
   `session-model/`, `environment-model/` (`.gitkeep`), and `migrations/` for the
   runtime cursor. Leave `memory/` + `claude_p_policy.toml` exactly as-is.
4. **Tracked migration home.** Create `docs/state-migrations/`; move P1.1's
   `fbm-live-slice.migration.yaml` there as a corrective (NEW file + a note; do
   NOT `git rm` the ignored original since it was never tracked — just relocate
   the content into the tracked tree). Author THIS slice's migration there.
5. **Build cursor durable home.** Move `build-cursor.md` content to a tracked
   `docs/plans/build-cursor.md` (committable); the F2 defect is then closed.

**No framework code written under `framework/`.** All code is the small establish
helper — placed where the bootstrap scaffolds (framework-side *machinery* that
WRITES user-state is allowed; it's framework code that lives in `framework/` and
creates the user-state dirs, exactly like `new_workspace.py` does). The
USER-STATE itself (`.loam/` dirs) is on the user side. This respects the boundary:
the helper is framework, its output is user-state.

## Step 4 — PROVE (plan)
Run AC-1..5 as a real test against a fresh temp dir (cold-walk: no pre-arranged
state) + a before/after probe of the live pos3 `memory/` tree for AC-3.

## Step 5 — INTEGRATE + RECORD (plan)
- Author `docs/state-migrations/loam-layout-slice.migration.yaml` (structural).
- Commit in canonical loam: slice plan, establish helper + test, `.loam/README.md`
  template, tracked migration(s), the moved build-cursor. The live `.loam/` dirs
  themselves are gitignored user-state (correct) — only the framework-side
  contract + helper + docs are committed.
- Update the build cursor → P1.2 complete, NEXT P1.3.

## Halt triggers honoured
- Owner-gated: the **layout review** is owner-gated (master plan P1.2 "owner-gated
  layout review — it's the durable on-disk contract"). → DEFINE surfaces the
  contract + decisions for ratification; STAGE, do not flip anything in
  `~/.claude/settings.json`. No destructive move of `.pos/` or `memory/`.
- Cairn repo: not touched. Content-filter: HALT+report. No `--amend`; no push.
- Boundary: user-state only in `.loam/`; helper is framework code in `framework/`.

---

*Principles applied: EXAMINE-before-building (live tree + git refs, found the P1.1
ignore defect empirically — not assumed); plan-before-code; respect the boundary
(declared `.loam/` = user-state; helper = framework); additive/fail-safe on the
live 1,283-episode tree; record the migration (release-gate input); F2 (surfaced
the P1.1 cursor+migration-not-in-git defect with evidence + the tracked-home
alternative); outcome-altitude ACs (cold-walk against a fresh tree).*
