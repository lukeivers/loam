# protection-matrix — add the FM.DROPPED-OPEN-LOOPS floor row

**Slug:** `protection-matrix-dropped-open-loops-row`
**Component:** `framework/protection-matrix/` (EXISTING; follow-on amendment — advances the sidecar)
**Owner-prompted:** Luke, Telegram 13573.

---

## 1. Objective

Add ONE new floor-class row to the protection / failure-mode-guard matrix
for a genuine, currently-uncatalogued AI failure mode:

> **The assistant DROPS ITS OWN OPEN LOOPS** — deferred work, follow-ups,
> and rechecks it intended to revisit are never revisited; no proactive
> self-follow-up. An AI assistant that only acts when prompted and silently
> forgets its own outstanding obligations.

The row records an **HONEST PARTIAL coverage** state: an instance-level
guard exists (task #79 — launchd self-recheck jobs that wake an agent,
re-run the analysis, and message the owner on material change), but the
loam-canonical, reusable, default-on "self-recheck" SKILL + pending-rechecks
register is **scoped, not yet built**. The row must use the matrix's
legitimate unbuilt-guard shape — NOT a faked full-coverage claim.

## 2. The right schema shape — and why (Ruthless-Feedback / information-trust)

Two precedent rows model the two honest "not-fully-bound-guard" shapes:

- **FM.COMMS-PATH-DEAD** (`guard_kind: hook`, a **resolvable** `guard_ref`,
  `default_on: NO-PROGRAMMATIC`) — the guard is REAL and sealed **in the
  loam tree**, just not wired default-on. Requires a resolvable symbol.
- **FM.SILENT-EGRESS** (`guard_kind: none`, **empty** `guard_ref`,
  `default_on: NONE`) — the guard is named but has **no symbol in the loam
  tree** to resolve (designed-not-yet-built). Empty ref on a non-obligating
  kind is legitimate, NOT a divergence.

**This row takes the FM.SILENT-EGRESS shape**, and the reason is load-bearing:
the task-#79 self-recheck instance is LIVE, but it is live **in the operator's
personal pos3 environment (launchd jobs), NOT in canonical public loam.**
A grep of the canonical loam tree (`framework/`, `plugins/`) for any
`self_recheck` / `pending_recheck` / Iran-recheck symbol returns **nothing**
(verified at build time). The matrix is the **canonical-loam** catalogue, and
its guard_ref resolver resolves against the **real loam tree** — so there is
no symbol to bind. Claiming a resolvable `guard_ref` (the COMMS-PATH-DEAD
shape) would be a hallucinated binding the resolver would flag as a
divergence; the honest shape is `guard_kind: none` / empty `guard_ref` /
`default_on: NONE`, with the verification text naming the live-instance vs
not-yet-productized reality explicitly.

This is the FM.SILENT-EGRESS precedent applied faithfully: a documented
floor gap whose guard is NAMED (the future self-recheck SKILL + register,
first-instance-proven by the launchd jobs) but **not yet bound** in the
canonical tree.

## 3. The row (added to `data/failure-mode-guard-matrix.yaml`, after FM.SILENT-EGRESS)

```yaml
  - id: FM.DROPPED-OPEN-LOOPS
    name: "Forgets its own open loops"
    description: >-
      Drops its OWN deferred work — the follow-ups, rechecks, and revisits it
      intended to come back to are never revisited; it acts only when prompted
      and silently forgets its outstanding obligations (an assistant that
      cannot keep pace with the user because it loses its own future work).
    source: >-
      feedback_apply_claude_leverage_to_own_tooling.md (self-scheduled
      follow-up is CORE to keep-pace); CLAUDE.md §keep-pace; task #79
      (the persona self-scheduled-recheck mechanism)
    guard: >-
      the persona self-scheduled-recheck mechanism (task #79) — first instance
      LIVE in the operator environment (launchd self-recheck jobs that wake an
      agent, re-run the analysis, and message the owner on a material change);
      the loam-canonical reusable "self-recheck" SKILL + pending-rechecks
      register (a durable register of the persona's own outstanding
      obligations, default-on, built on a Claude-native scheduling primitive
      per Lens 1) is SCOPED, not yet built — until that capability is built +
      sealed in the canonical tree the floor is held only by persona discipline
    guard_kind: none
    guard_ref: ""
    default_on: NONE
    class: floor
    proportionality_note: ""
    verification: >-
      UNVERIFIABLE by a deterministic check in the canonical tree today —
      the named guard's first instance is LIVE but lives in the operator's
      personal environment (launchd jobs), NOT in canonical loam, and the
      reusable, productized, default-on self-recheck SKILL + pending-rechecks
      register is SCOPED, not yet built, so there is no symbol in the loam tree
      to resolve. This is the honest "named-but-not-yet-bound" status the
      FM.SILENT-EGRESS row holds (an instance-level guard exists; the general
      default-on capability does not) — the row carries the unbuilt-guard shape
      (guard_kind none, empty guard_ref, default_on NONE) rather than a
      hallucinated binding (the protection pillar must not invent coverage it
      does not have). A floor-class GAP: until the self-recheck capability is
      built + default-on in the canonical tree, the keep-your-own-open-loops
      floor is held only by persona discipline.
```

## 4. Acceptance criteria

`AC.PMROW.*` test pattern (modelled on `test_AC_PMROW_3_silent_egress_row.py`).
New test file: `test_AC_PMROW_4_dropped_open_loops_row.py`.

- **AC.PMROW.6** — FM.DROPPED-OPEN-LOOPS exists + is schema-conformant:
  floor-class, `guard_kind: none`, `guard_ref` empty (NOT a hallucinated
  binding), `default_on: NONE`, every required §5 field present + meaningful.
- **AC.PMROW.7** — the row is NOT a divergence: its non-obligating kind with
  an empty ref must not appear in `report.divergences` (no over-claim).
- **AC.PMROW.8** — the row surfaces as a visible floor GAP: it appears in
  `report.gaps` and in the rendered `GAPS —` section (named, not silently
  omitted).
- **★ AC.PMROW.9 (outcome-altitude: true)** — a real `load_catalogue()` +
  `run_coverage_check()` over the shipped catalogue + the live tree, no
  pre-arranged state: the row parses, adds zero new divergence, appears among
  the live coverage gaps, AND the coverage is honest-partial (guard text names
  both the live instance and the not-yet-built productized capability;
  `default_on != "YES"`).

## 5. Companion regeneration

`docs/design/protection-matrix.md` is GENERATED — regenerate via
`loam guards --refresh` after the YAML edit. The AC.PMGEN.1 md↔yaml sync test
stays green (the companion is a faithful projection; never hand-edited).

## 6. Non-regression

- AC.FMG-CAT.1 (schema) — the new row is enum-valid.
- AC.FMG-GAP.1 — `EXPECTED_FLOOR_GAPS` is a SUBSET assertion (`EXPECTED -
  gap_ids`), so a new additive floor gap does not break it.
- AC.FMG-CHECK.2 — no new divergence (empty ref on non-obligating kind).
- AC.PMROW.2 / .3 (COMMS-PATH-DEAD, SILENT-EGRESS) stay green.
- AC.PMTRACK.1 — catalogue still git-tracked + parses.
- AC.PMGEN.1 — companion sync.

## 7. The SECOND candidate row (Lens-1 own-tooling) — DISPOSITION: DO NOT ADD

Owner asked to ALSO assess a second row for "persona hand-rolls bespoke infra
instead of reaching for the Claude-native primitive (Lens-1 not applied to its
OWN tooling)." **Recommendation: do NOT add it; leave it as the standing
discipline rule** (`feedback_apply_claude_leverage_to_own_tooling.md`).

Reasoning (surface, do not force — per the objective):
1. **Schema/intent mismatch.** Every matrix row is a **runtime** way an AI
   betrays **the user** by default, bound to a **runtime guard** (hook / gate
   / comparator / persona-discipline that fires during operation). "Persona
   reaches for bespoke infra instead of the Claude-native primitive" is a
   **build-time / design-discipline lapse**, not a runtime user-facing
   betrayal — there is no runtime moment at which a guard fires.
2. **No guard_kind fits.** The "guard" would be a design-review habit, which
   none of the schema's `guard_kind` values model. Forcing `persona-discipline`
   would technically parse but would dilute the matrix's meaning (failure-mode
   × runtime-guard) and set a precedent that any authoring discipline belongs
   in the protection ledger.
3. **Already captured at the right altitude.** It is a Lens-1 *authoring*
   concern, durably held as a discipline rule + tracked under task #79; the
   matrix is the wrong home.

It does NOT cleanly fit the schema/intent, so it stays the discipline rule.

## 8. Mismatch surfaced (#71) — out of scope, owner-gated

The existing **FM.SILENT-EGRESS** row is now **STALE**: it states the
egress-consent gate is "DESIGNED, not yet built" (`guard_kind: none`, empty
ref, `default_on: NONE`), but the `framework/egress-consent/` component is now
**built + sealed** (`framework/egress-consent/src/loam/egress_consent/gate.py
:EgressReleaseGate` / `release`, sealed at `2304dea`). Per Ruthless-Feedback
T1 resolution this is SURFACED but NOT fixed in this amendment (out of scope —
this cycle adds the dropped-open-loops row only). It is a candidate follow-on
to re-bind FM.SILENT-EGRESS to the now-real egress-consent symbol (the
COMMS-PATH-DEAD shape). Owner-gated.

## 9. Baseline / fence

Single-component follow-on. BASELINE re-baselined to the pre-amendment main
tip (the documented HEAD~1 advance pattern) so the BASELINE..SEAL window shows
only this amendment's protection-matrix + docs/plans/ + generated-companion
surfaces (the prior sidecar BASELINE 949fced9 now predates the egress-consent
release and would span unrelated components).

No state-schema change → no migration (declared no-op consistent with prior
protection-matrix amendments).
