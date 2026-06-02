# protection-matrix — add the FM.SILENT-EGRESS floor row

**Amendment slug:** `protection-matrix-silent-egress-row`
**Component:** `framework/protection-matrix/` (existing sealed component;
follow-on — first seal `68fb6f8`, last follow-on advanced the sidecar via the
catalogue-track-and-rows cycle).
**Class:** small, single-component, documentation/catalogue amendment.

---

## §1 — Problem (source-of-scope finding)

Source-of-scope:
`/Users/lukeivers/pos3/workspace/.scratch/claude-output/loam-privacy-safe-data-sharing-design.md`
§0 / §0.1 — the protection matrix has **no `FM.SILENT-EGRESS` row**. "loam
sends a user's data / files off their machine for troubleshooting or analytics
WITHOUT explicit, transparent, per-item user consent" is a floor-class privacy
betrayal that is not on loam's failure ledger at all (grep of `docs/` +
`framework/` for egress/telemetry/analytics/consent returns only unrelated
OTel-internal hits).

## §2 — Objective (ODD)

> Add one schema-conformant catalogue row `FM.SILENT-EGRESS` to
> `framework/protection-matrix/data/failure-mode-guard-matrix.yaml` documenting
> the silent off-machine data-egress failure mode as a floor-class gap whose
> named guard (the future egress-consent gate layer) is designed but not yet
> programmatically bound — and regenerate the human-readable companion. The
> row is a documented floor gap, exactly the precedent `FM.COMMS-PATH-DEAD`
> set for a failure mode whose guard is named but not default-on-bound.

## §3 — Key Tier-0 constraint that shapes the row (READ — Ruthless Feedback)

`FM.COMMS-PATH-DEAD` is the brief's named precedent. Its row is
`class: floor, default_on: NO-PROGRAMMATIC, guard_kind: hook` — BUT its
`guard_ref` **resolves to a real, already-sealed importable symbol**
(`self_correction/watchdog.py:ChannelVerdict`). The egress-consent gate for
FM.SILENT-EGRESS **does not exist as a symbol at all** (the design doc states
it is "designed but not yet built").

The catalogue's `check.py` `divergence` rule flags any row whose `guard_kind`
obligates a resolvable `guard_ref` (`hook`/`release-gate`/`comparator`/
`memory`) but whose ref does NOT resolve, as a hallucinated-coverage
over-claim (`test_AC_FMG_CHECK_2_ground_truth_reconcile.py`). Therefore a
`guard_kind: hook` row with a guard_ref pointing at the unbuilt gate would
SEAL-FAIL the divergence test.

**Resolution (the correct "mark the binding status the same way" reading):**
COMMS-PATH-DEAD marked its status as a *visible floor gap*
(`default_on != YES` → it shows up in the GAP section). FM.SILENT-EGRESS gets
the SAME visible-floor-gap status, but because its named guard is not yet a
symbol, it uses the schema's legitimate **unbuilt-guard** shape — the same
shape `FM.ENV-PERCEPTION-MVC` uses (a floor row, `guard_kind: none`/
`persona-discipline`, **empty `guard_ref`**, `default_on: NONE`, the future
guard named in the `guard`/`verification` prose). Empty guard_ref on a
non-`guard_ref_required` kind is NOT a divergence (per `catalogue.py`
`guard_ref_required` + `check.py` `divergence`), so the row seals cleanly while
honestly recording the gap. This is the "named but not yet programmatically
bound" status the brief asks for — modelled on the COMMS-PATH-DEAD
*gap-visibility* posture, adapted to the fact that the named guard has no
symbol yet.

## §4 — The row (the spec)

- `id: FM.SILENT-EGRESS`
- `name`: plain-language ("Sends your data off your machine without asking").
- `description`: one sentence — sends a user's data/files off-machine for
  troubleshooting or analytics without explicit, transparent, per-item consent.
- `source`: the privacy-safe data-sharing design doc §0.1 + the relevant
  feedback/doctrine pointer.
- `guard`: names the future **egress-consent gate** (the fail-closed,
  per-item-reviewed, nothing-leaves-by-default release gate from the design
  §1.4) as the intended guard, recording it is designed-not-yet-built.
- `guard_kind: none` (no programmatic guard exists yet — the symbol is unbuilt;
  empty guard_ref is legitimate for this kind, avoids a false divergence).
- `guard_ref: ""`.
- `default_on: NONE`.
- `class: floor`.
- `proportionality_note: ""`.
- `verification`: names WHY it is a gap (the guard is designed in the
  privacy-safe data-sharing layer but not yet built/sealed; until then the
  floor is held only by persona discipline) — the same honest-gap prose
  COMMS-PATH-DEAD / ENV-PERCEPTION-MVC carry.

## §5 — Acceptance criteria (every line maps to one)

- **AC.PMROW.3 — FM.SILENT-EGRESS row present + schema-conformant.** The
  catalogue loads (`load_catalogue`) with the new row; the row is floor-class,
  carries every required §5 field, every enum-valued field in its enum, and is
  NOT flagged as a divergence (its empty guard_ref is legitimate for its
  guard_kind). Modelled on
  `test_AC_PMROW_2_comms_path_dead_and_narration_fold.py`.
- **AC.PMROW.4 — surfaced as a visible floor gap.** The coverage check
  (`run_coverage_check` → `render_report`) lists `FM.SILENT-EGRESS` in the
  distinct GAP section (it is floor-class with `default_on != YES`), so the gap
  is named, not silently omitted (the recursive FM.HALLUCINATION discipline).
- **★ AC.PMROW.5 — outcome-altitude (`outcome-altitude: true`).** A real
  catalogue load + coverage check at the production entry-point, NO
  pre-arranged state: `load_catalogue()` over the shipped file parses the row;
  `run_coverage_check()` (shipped catalogue + live tree) yields zero new
  divergence and includes FM.SILENT-EGRESS among `report.gaps`. The real load
  + real schema-conformance + real row-exists + real no-divergence check.

## §6 — Non-regression

`test_AC_FMG_CAT_1` (schema-conformant), `test_AC_FMG_GAP_1`
(`EXPECTED_FLOOR_GAPS` is a subset assertion — a 6th gap is additive, stays
green), `test_AC_FMG_CHECK_2` (no new divergence), `test_AC_PMGEN_1` (companion
md↔yaml sync — regenerate the companion so the fresh-render compare passes) all
stay green.

## §7 — Cycle mechanics

Single-component amendment on the EXISTING `framework/protection-matrix/`.
`loam amend apply <manifest>` → touched tests green → `loam amend seal`. LOCAL
only. New corrective commit; never `--amend`. Universal admissions:
`docs/plans/` + the generated `docs/design/protection-matrix.md` companion (it
is GENERATED, regenerated via `loam guards --refresh` from the catalogue).
Sidecar `framework/protection-matrix/tests/SEAL_COMMIT` advances.

## §8 — Halt-surface check

The one genuine design tension (the unbuilt named guard) is resolved in §3 and
surfaced here, not papered over: the row records an HONEST floor gap rather
than a hallucinated guard binding. No ODD violation in surrounding code; the
row references no other component's code and adds no programmatic guard, so no
sealed-component edits are implied.
