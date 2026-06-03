# FBM multi-repo work-visibility snapshot (Slice E)

**Slice:** E (P4-3) of the FBM quality-and-accuracy overhaul.
**Owner mandate:** Luke 13582 (greenlit). Unified plan:
`workspace/.scratch/claude-output/loam-fbm-quality-and-accuracy-unified-plan.md` (Slice E).
Diagnosis: `workspace/.scratch/claude-output/loam-fbm-project-status-accuracy-diagnosis-and-fix.md`
(flagged `work_visibility.py` as loam-centric / single `workspace_root`).
**Component:** `primary-persona` (single-component amendment; follow-on).
**WD:** `/Users/lukeivers/loam`. Read-only git probes against `/Users/lukeivers/cairn`.

---

## §1 — Objective (ODD)

> The work-visibility snapshot reflects EVERY registered project's
> ground-truth STATE (loam + Cairn), not just loam — so the owner's
> live "what's happening" view carries each active repo's real
> build/sealed/merged state, derived fresh, never stale prose.

The snapshot keeps its existing loam work-state (running-now / queued /
owner-pending / position / health) AND gains a per-project ground-truth
STATE bucket for each registered project, each sourced from ITS own
ground-truth spec via Slice C's `derive_project_state`.

---

## §2 — The genuine design fork (named + resolved per the constraint)

`work_visibility.build_snapshot` today reads THREE loam-operational
signals through a single `workspace_root`:

1. the **objective tracker DB** (running-now / queued / owner-pending),
2. the **position cursor** (which flow step),
3. the **stall watchdog** (health).

**These three are loam's operational runtime signal. Cairn has NO
equivalent surface** — no loam objective-tracker DB, no flow cursor, no
watchdog. Running the loam tracker against `/Users/lukeivers/cairn`
would read a non-existent DB and fabricate or blank state. So the
honest generalization is NOT "aggregate the tracker over N repos".

**Fork resolution (conservative, per the constraint's explicit
allowance):** the **work-state** part (tracker/cursor/watchdog) stays
**loam-only** — it is a per-workspace operational signal with no
cross-repo analogue. The **multi-repo addition** is a separate
**per-project ground-truth BUILD-STATE bucket**: for EVERY registered
project (loam + Cairn) the snapshot carries that project's
freshly-derived `StateOfLoam` summary (built/sealed/merged module
counts + head ref), reusing Slice C's `derive_project_state`. This is
the part the diagnosis actually flagged ("the work-visibility window …
has no concept of a second repo") and the part that is genuinely
additive. The constraint explicitly blesses this split:
*"acceptable for the project-STATE part to be the multi-repo addition
while a single-repo tracker DB stays loam-only."*

**Ruthless Feedback — is this redundant with Slice D?** No. Slice D's
`project_state.py` injects the per-module build-status block into the
**keep-pace turn-start LENS** (a retrieval contributor the persona reads
each turn). Work-visibility is a **different surface** — the on-demand
"what's happening / what's next / is anything stuck" plain-language
status the owner pulls (or that the generated-file presenter renders).
The two answer different questions (turn-start retrieval context vs.
on-demand work-status surface) and ride different entry points
(`register_project_state_contributor` vs. `render_work_visibility`).
Slice E does NOT build a second copy of Slice D's renderer — it REUSES
`derive_project_state` (the Slice C derivation, also Slice D's source)
and folds a COUNT-level per-project summary into the work-visibility
snapshot + renderer, preserving work-visibility's zero-internal-vocab,
counts-only invariant (the snapshot must not echo module names/SHAs into
the rendered surface, unlike the lens block which is internal-context).

---

## §3 — Composition (reuse, not re-implement)

- `loam_cli.audit.registry.derive_project_state(name)` /
  `registered_project_names()` — Slice C, reused verbatim. Lazy-imported
  inside the read (mirroring `work_visibility.py`'s existing `loam_cli`
  lazy-import discipline) so an absent `loam_cli` degrades to no
  project-state buckets, never an import-time crash.
- `StateOfLoam.components[*].liveness` + the `BUILT_CLASSES` /
  `Liveness` vocabulary — read to COUNT built vs not-built per project.
- The existing `build_snapshot` / `render_surface` / `WorkSnapshot`
  surface — EXTENDED (new field + new render line), not replaced. The
  existing four-source fail-soft discipline (AC.WVS-AGG.2) is the
  template the new project-state read follows.

---

## §4 — Added / changed surface

- `work_visibility.py`:
  - `ProjectStateSummary` — a frozen dataclass: `name`, `built` (count
    of MERGED/SEALED/WIRED/BUILT modules), `total`, `unknown` flag. COUNTS
    + a plain display name only — NO module names, NO SHAs (the
    zero-internal-vocab + counts-only invariant the snapshot already
    holds).
  - `WorkSnapshot.project_states: tuple[ProjectStateSummary, ...]` — new
    field, default empty (back-compat: existing loam-only callers are
    unchanged; the field is empty unless the multi-repo read populates
    it).
  - `_read_project_states(...)` — fail-soft reader: lazy-import the
    registry, derive each registered project, summarize to counts. A
    per-project derivation error OMITS that project (survivors still
    populate). A registry-absent / all-fail path yields an empty tuple +
    a `project_states_unknown` flag. Never raises, never hangs.
  - `WorkSnapshot.project_states_unknown: bool` — the per-source unknown
    marker (the AC.WVS-AGG.2 pattern).
  - `build_snapshot(..., include_project_states: bool = True,
    project_state_reader=None)` — populates `project_states`; the reader
    seam mirrors the existing `tracker_factory` test seam. Default-on so
    the production surface is multi-repo by default; a caller can opt out.
  - `render_surface` gains a per-project STATE line block: one short
    plain-language line per project
    (`Project loam: 18 of 18 pieces built.` / `Project cairn: 5 of 5
    pieces built.`). Counts only — survives the existing
    `contains_internal_vocabulary` HARD invariant by construction (no
    module names / SHAs in the rendered text).
  - `render_work_visibility(...)` threads the new params through.

No new component, no new tracking system — an aggregation + wiring
extension over the sealed Slice C derivation, exactly as
work_visibility's own docstring discipline requires.

---

## §5 — Acceptance criteria (each → a named test; ≥1 outcome-altitude)

- **E1 — AC.WVS-MR-1 (multi-repo buckets).** A snapshot built with a
  project-state reader covering loam + cairn carries a
  `ProjectStateSummary` for BOTH projects, each with its own
  built/total counts derived from ITS spec; the rendered surface names
  both projects' build state.
  (`test_AC_WVS_MR_1_multi_repo_buckets.py`.)

- **E2 — AC.WVS-MR-2 (no fabricated row).** A registry exposing a name
  whose derivation returns `None` (unregistered / no spec) produces NO
  bucket for that name — the snapshot omits it, never a fabricated row;
  the surviving registered projects still render. A registry-absent
  path yields zero project buckets + `project_states_unknown=True`, and
  the snapshot + surface still return (the existing fail-soft contract).
  (`test_AC_WVS_MR_2_no_fabricated_row_failsoft.py`.)

- **E3 — AC.WVS-MR-3 ★ (outcome-altitude).** Invoke the PRODUCTION
  snapshot builder (`build_snapshot` via `render_work_visibility`) with
  NO pre-arranged state against the LIVE registry (loam +
  `/Users/lukeivers/cairn`): BOTH repos appear with build state derived
  from their real refs/modules — Cairn's engine modules
  (verify/ledger/execute/pilot/cause) counted as BUILT — and the
  rendered surface carries zero internal vocabulary. A
  STUB-class test (hand-fed summaries / mocked derivation) does NOT
  satisfy this; the test drives the real `derive_project_state` against
  the live Cairn repo.
  (`test_AC_WVS_MR_3_outcome_altitude.py`.)

The pre-existing AC.WVS-AGG / AC.WVS-RENDER / AC.WVS-S suite stays green
(the work-state half is untouched; the project-state read is additive +
default-on but fail-soft, so the existing fail-soft + zero-vocab ACs
still hold).

---

## §6 — Constraints honored

- SCOPE = Slice E only. NOT Slice F (BrainBench P@5), NOT the junk purge.
- Conciseness: one short count-line per project; no per-module dump.
- Perf: `derive_project_state` runs git probes (~0.1 s for both repos,
  measured in Slice D); the work-visibility surface is an on-demand pull,
  not a per-turn hot path, so no new cache is needed here (Slice D's lens
  contributor — the per-turn surface — already carries the TTL cache).
  If the same process renders work-visibility repeatedly, Slice D's
  module-level cache is shared via the same `derive_project_state`.
- Fail-soft: every new branch degrades a project to omitted /
  `project_states_unknown`, never a hang, never a wrong/partial row.
- Zero-internal-vocab HARD invariant preserved: the project-state lines
  are counts + plain display names only.
- Read-only against `/Users/lukeivers/cairn`.
- Suite run under python3.13 (host default 3.9 < the >=3.11 floor; the
  latent 3.9 entry-point failures are pre-existing, not this slice's).

## §7 — ODD note

Every new branch traces to a named AC (E1/E2/E3). The fail-soft branches
are AC.WVS-MR-2; the zero-vocab path is the pre-existing
AC.WVS-RENDER.2 invariant. No defensive code for unnamed cases; the
Slice C derivation + the work-state half are consumed/left unchanged.

## §14 — Method-decision record

- **Design fork — work-state stays loam-only, build-state goes multi-repo.**
  The tracker DB / cursor / watchdog are per-workspace OPERATIONAL signals with
  no cross-repo analogue (Cairn has no loam tracker DB / cursor / watchdog), so
  running them against Cairn would read a non-existent DB and fabricate state.
  The multi-repo ADDITION is therefore the per-project ground-truth BUILD-STATE
  bucket (counts of built modules), reusing Slice C's `derive_project_state`.
  This is the part the diagnosis flagged ("the work-visibility window … has no
  concept of a second repo") and the part the brief explicitly blessed as the
  acceptable split.
- **NOT a second Slice-D surface (Ruthless Feedback).** Slice D injects per-module
  status into the keep-pace turn-START LENS; work-visibility is the on-demand
  counts-only status surface. Slice E REUSES the same `derive_project_state`
  derivation, folding a COUNT-level summary into `build_snapshot` + `render_surface`
  — no cloned renderer, no second derivation.
- **Counts-only, zero-internal-vocab by construction.** `ProjectStateSummary`
  carries `built` / `total` + a plain display name only (no module names / SHAs),
  so the rendered project lines pass the pre-existing AC.WVS-RENDER.2 HARD
  invariant without special handling.
- **Default-on, opt-out + test seam.** `include_project_states=True` makes
  production multi-repo by default; `project_state_reader` mirrors the existing
  `tracker_factory` seam for tests. The `loam_cli` import is lazy inside the read
  (the existing `work_visibility.py` discipline) so an absent `loam_cli` degrades
  to no project buckets, never an import-time crash.
- **Fail-soft throughout.** A per-project derivation raise OMITS that project; a
  `None` derivation yields NO row (never fabricated); a registry-absent / all-fail
  read yields zero buckets + `project_states_unknown=True`; the snapshot + surface
  always return. Verified at build time: the live surface renders
  `Project Cairn: 5 of 5 pieces built.` + `Project Loam: 4 of 4 pieces built.`

### Commit SHAs

- feat (source + tests + plan + manifest): `d47269f4`
- manifest+apply (sidecar bump to apply commit): `f1e0188a`
- seal: `14142c67`
