# FBM inject derived per-project STATE record into the keep-pace lens (Slice D)

**Author:** build agent · **Date:** 2026-06-02 · **Owner:** Luke (greenlit 13582)
**Parent plan:** `workspace/.scratch/claude-output/loam-fbm-quality-and-accuracy-unified-plan.md` (Slice D, P4-2).
**Diagnosis:** `workspace/.scratch/claude-output/loam-fbm-project-status-accuracy-diagnosis-and-fix.md`.
**Mode:** plan-before-code; single-component amendment on the EXISTING `primary-persona` component.
Read-only against `/Users/lukeivers/cairn` and `/Users/lukeivers/loam` (git probes only; never modified).

---

## Objective

When the persona's session-start / turn-start context is composed, inject a CONCISE, accurate,
ground-truth-derived STATE summary for the registered projects (loam + cairn) — so the persona's
context carries the REAL per-module build/sealed/merged status instead of stale written prose. This
is the load-bearing accuracy fix: with Cairn's `verify`/`ledger`/`execute` shown as **built** in the
turn-start context, the persona literally cannot, from that context, claim they "remain to be built".

## Scope (Slice D ONLY)

IN: a keep-pace TURN contributor that derives the registered projects' STATE (via Slice C's
`derive_project_state` / `PROJECT_REGISTRY`), renders a SHORT per-project summary, caches the derived
record with a short TTL, fails soft on any probe error, and registers into the live composer's
production branch. OUT (NOT this build): Slice E (multi-repo work-visibility snapshot), Slice F
(BrainBench metric), the junk purge.

## Composition — reuse, do NOT re-implement (Lens 1/2)

- The STATE derivation is **already built and sealed** (Slice C): `loam_cli.audit.registry`
  (`derive_project_state`, `registered_project_names`, `PROJECT_REGISTRY`) + `cairn_state` +
  `record.py`'s `StateOfLoam` / `ComponentState` / `Liveness`. Slice D does NOT re-derive anything —
  it CONSUMES `derive_project_state(name)` and renders the result. The only new logic is (a) a concise
  renderer, (b) a short-TTL cache, (c) the contributor + its registration.
- The injection SEAM is the one the diagnosis named: the keep-pace turn-contributor surface in
  `session_start_emitter.build_session_composer`'s production (client-None) branch — the same place
  the gated `memory-retrieval` contributor registers (`register_keep_pace_turn_contributor`). The new
  `project-state` contributor registers ALONGSIDE it at `TriggerKind.turn`, independently fail-soft.
- `loam_cli` is already an import target of `primary-persona` (`work_visibility.py` imports
  `loam_cli.flows.cursor` lazily). Slice D follows the SAME lazy-import + fail-soft pattern: the import
  lives inside the derivation call, and any `ImportError` degrades to no injection.

## Design forks (picked + documented, per the "sensible conservative approach" clause)

1. **Where it registers.** A SEPARATE turn contributor named `project-state`, registered in the
   production (client-None) branch of `build_session_composer`, NOT folded into the `memory-retrieval`
   contributor. Rationale: independent fail-soft (a STATE-probe failure must not suppress the
   memory-retrieval block, and vice versa); a distinct named block keeps the surfaces auditable; no
   downstream consumer keys on a `project-state` name today (new block). Registered fail-soft (a
   registration-time exception simply omits the block — the AC46.2 graceful-empty pattern the
   surrounding registrations already use).

2. **How the TTL cache lives.** A module-level `dict[name -> (monotonic_ts, StateOfLoam)]` guarded by a
   short TTL (`_STATE_TTL_SECONDS = 60.0`). A turn re-deriving within the TTL reuses the cached record
   (no git probe); a stale/absent entry re-derives. Rationale: the git probes are ~0.1 s for both
   projects measured at build time, but a turn fires every prompt — caching makes the steady-state cost
   zero without persisting anything to disk (no drift surface; the cache is in-process and expires).
   Conservative over a per-call derive (avoids re-probing git on every keystroke-turn) and over a
   long/persistent cache (60 s bounds staleness to within a single working burst; a fresh session
   re-derives cold).

3. **Conciseness shape.** ONE line per project, modules grouped by liveness class:
   `Cairn: verify, ledger, execute, pilot, cause = built (merged)`. At most a few liveness groups per
   project, comma-joined module names, hard-capped (`_STATE_BLOCK_CHAR_CAP = 600`). NOT a per-module
   evidence dump (the evidence stays available via `loam audit` / the record itself; the LENS surface
   is glanceable status only). This is the explicit "do not trade removed junk for a new wall of text"
   guard.

## Fail-soft + perf guards (load-bearing)

- Any exception deriving a project's state → that project is OMITTED from the block (never a hang,
  never a partial/wrong status). If ALL projects fail / the registry is empty → the contributor returns
  `""` (no block). The lazy `loam_cli` import is inside the try; an `ImportError` degrades to no block.
- The TTL cache makes the steady-state per-turn cost a dict lookup (zero git I/O within the TTL window).
- The contributor is a `TriggerKind.turn` `fn(context: dict) -> str` per the composer contract; it
  returns `""` on no content so `_serialise_turn`'s `text.strip()` is safe.

## Method (builder's call, recorded for the seal)

New file `framework/primary-persona/src/loam/primary_persona/keep_pace/project_state.py`:

- `_STATE_TTL_SECONDS = 60.0`, `_STATE_BLOCK_CHAR_CAP = 600`, module-level cache dict.
- `_derive_cached(name)` — TTL-guarded wrapper around `loam_cli.audit.registry.derive_project_state`;
  returns the `StateOfLoam` or `None` (unregistered / probe error). Fail-soft.
- `_render_state_block(records)` — renders the concise per-project summary: one line per project,
  liveness-grouped module lists, the project's short head-SHA, capped. Returns `""` when empty.
- `render_project_state_block(*, names=None, now=...)` — the production derivation+render entry point:
  derives each registered project's state (cached), renders the concise block. No pre-arranged state.
- `build_project_state_contributor()` — returns the `fn(context: dict) -> str` turn contributor (calls
  `render_project_state_block`, fail-soft to `""`).
- `register_project_state_contributor(composer, *, name="project-state")` — registers the contributor
  at `TriggerKind.turn`.

Wire `register_project_state_contributor(composer)` into `build_session_composer`'s production
(client-None) branch, fail-soft, alongside the `register_keep_pace_turn_contributor` call.

## ODD ACs (each maps to a named test; ≥1 outcome-altitude)

- **AC-FBM-STATE-LENS-1** (D1): the production composer's production branch registers a `project-state`
  turn contributor; `on_user_prompt_submit` surfaces a STATE block whose text names a registered
  project + its derived status. Test: `test_AC_FBM_STATE_LENS_1_composer_registers_project_state.py`.
- **AC-FBM-STATE-CONCISE-2** (conciseness guard): the rendered block for both registered projects is
  SHORT — one line per project, under `_STATE_BLOCK_CHAR_CAP`, module names liveness-grouped, NOT a
  per-module evidence dump. Test: `test_AC_FBM_STATE_CONCISE_2_block_is_short.py`.
- **AC-FBM-STATE-FAILSOFT-3** (fail-soft guard): a project whose derivation raises is OMITTED from the
  block (the block still renders the surviving projects); an all-fail / registry-error path returns
  `""` — never a hang, never a partial/wrong status. Test:
  `test_AC_FBM_STATE_FAILSOFT_3_probe_error_omits_no_hang.py`.
- **AC-FBM-STATE-LIVE-4 (OUTCOME-ALTITUDE)** (D3): the REAL `render_project_state_block()` entry point,
  run with NO pre-arranged state against the LIVE loam + cairn repos, produces an ACCURATE block —
  loam AND cairn both present, and the Cairn line shows `verify`, `ledger`, `execute` as BUILT (so the
  persona cannot, from this context, claim they "remain to be built"). Invokes the production entry
  point, no fixtures. Test: `test_AC_FBM_STATE_LIVE_4_outcome_altitude.py`.

## Outcome match (verify on completion)

`render_project_state_block()` (production entry, no fixtures) returns a concise block containing a
Cairn line that shows verify/ledger/execute as built — verified at build time (Slice C derivation
already returns MERGED for all five Cairn modules). AC-FBM-STATE-LIVE-4 green proves the accurate live
status reaches the lens-injection surface, which is the whole point of Slice D.

## Pre-existing host fragility (flagged per Ruthless Feedback, NOT introduced here)

The host default `python3` is 3.9 (below the >=3.11 floor); some pre-existing entry-point-discovery
tests fail on 3.9 (`importlib.metadata.entry_points(group=...)`). The suite for this cycle is run under
python3.13. Those 3.9-only failures are a latent host issue, not a Slice D regression.
</content>
</invoke>
