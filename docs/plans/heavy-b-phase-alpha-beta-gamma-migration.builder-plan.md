# Heavy-B Phase α / β / γ data migration — builder plan

Companion to `heavy-b-phase-alpha-beta-gamma-migration.md`. Names the
specific files, symbols, and method-decision selections used in this
build. Authored before code per CLAUDE.md plan-before-code rule.

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Scope fence:** `tools/heavy-b-migrate/` (new) + a single side-effect
hook in `tools/loam-mode/` (the lazy-projection trigger). No
sealed-component edits.

---

## 1. Method-decision selections (from §11 of the plan doc)

- **D-build.1 — Extractor home.** **(a) `tools/heavy-b-migrate/`**, sibling to
  `tools/pos-amend/` and `tools/loam-mode/`. Master-research recommendation.
  Clean separation: heavy-b-migrate is one-time data-migration tooling +
  verification harness; pos-amend's role is amendment-cycle bookkeeping.
- **D-build.2 — Phase β placeholder convention.** **(a) one placeholder
  ObjectiveSpec per failed-parse component-section.** Master-research
  recommendation. Visible in `query_projection_view` filtered by
  `lifted_from.source_doc`; placeholders carry `source_ac="placeholder"` so
  they don't collide with real ACs.
- **D-build.3 — Phase γ amendment authoring policy.** **(a) every amendment
  is `authored_by="user"`.** Per research §A.4 dominant case. §6 constraint 7
  + halt-trigger 6 enforce.
- **D-build.4 — Continuous-registration verification.** **(b) one-shot
  post-Phase-γ verification pass.** Method: a `verify-continuous` subcommand
  on the heavy-b-migrate CLI that crafts a manifest fixture, invokes
  `register_objectives` from pos-amend's surface, asserts the records land,
  invokes `update_source_commits`, asserts source_commit lands. Runs in a
  tmpfs-style isolated tracker DB to avoid polluting the canonical workspace.
- **D-build.5 — Per-phase test scope.** **One test file per AC** (AC.D-mig.1
  through AC.D-mig.6). Tests under `tools/heavy-b-migrate/tests/`.
- **D-build.6 — Lazy-projection trigger attach point.** **(a) loam-mode's
  session-start emitter.** Master-research recommendation. The
  `tools/loam-mode/src/loam_mode/session_start.py` `cli_session_start` path
  already runs every session, already reads `dev_intent`, is dev-discipline
  (no sealed-component fence to cross), and is the established lifecycle
  event the contract is loaded against. The trigger fires as a side-effect
  before `emit_session_start_context`'s payload return; the trigger is
  fail-soft (any exception is swallowed; the SessionStart payload is
  unaffected) and idempotent (re-runs after first projection are no-ops via
  `lifted_from` query).

## 2. New files (under scope fence)

```
tools/heavy-b-migrate/
├── pyproject.toml
├── README.md
├── src/heavy_b_migrate/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py                  # argparse: `phase-alpha`, `phase-beta`, `phase-gamma`, `project`, `verify-continuous`
│   ├── components.py           # Phase α — sealed-component objective list + seeder
│   ├── component_acs.py        # Phase β — proposal AC extractor
│   ├── amendment_acs.py        # Phase γ — amendment-plan AC extractor
│   ├── extraction.py           # shared regex/markdown helpers
│   ├── ids.py                  # stable objective-id derivation
│   ├── runner.py               # phase-runner with ordering enforcement
│   ├── trigger.py              # lazy-projection entry point (run_if_dev_intent)
│   └── verify.py               # AC.D-mig.4 continuous-registration verifier
└── tests/
    ├── conftest.py             # tmpfs tracker fixtures
    ├── test_ac_d_mig_1_phase_alpha.py
    ├── test_ac_d_mig_2_phase_beta.py
    ├── test_ac_d_mig_3_phase_gamma.py
    ├── test_ac_d_mig_4_continuous_registration.py
    ├── test_ac_d_mig_5_placeholder_extraction.py
    └── test_ac_d_mig_6_phase_ordering.py
```

## 3. Surface to be edited (under scope fence)

`tools/loam-mode/src/loam_mode/session_start.py` — add a single guarded
`_invoke_lazy_projection(workspace_root)` call inside `cli_session_start`
(or `emit_session_start_context`) that:

1. Imports `heavy_b_migrate.trigger.run_if_dev_intent` lazily (so loam-mode
   has no install-time dep on heavy-b-migrate).
2. Calls it with the workspace root.
3. Catches every exception (fail-soft per AC.B5).

The trigger itself reads `dev_intent` (via the local fail-soft reader, not
the sealed primary-persona import — convention parity with B's existing
shape) and dispatches the phase runner.

## 4. AC mapping

| AC | Test file | Implementation surface |
|---|---|---|
| AC.D-mig.1 | test_ac_d_mig_1_phase_alpha.py | `components.seed_phase_alpha` |
| AC.D-mig.2 | test_ac_d_mig_2_phase_beta.py | `component_acs.extract_and_seed` |
| AC.D-mig.3 | test_ac_d_mig_3_phase_gamma.py | `amendment_acs.extract_and_seed` |
| AC.D-mig.4 | test_ac_d_mig_4_continuous_registration.py | `verify.verify_continuous_registration` |
| AC.D-mig.5 | test_ac_d_mig_5_placeholder_extraction.py | `extraction.parse_with_placeholder` |
| AC.D-mig.6 | test_ac_d_mig_6_phase_ordering.py | `runner.run_phases` (ordering check) |

## 5. Stable objective IDs

- Root: `value-prop-root` (already seeded by #39).
- Spec phases: `spec-v1.0` / `spec-v1.1` / `spec-v1.2` (already seeded).
- Phase α (component objectives): `component-<slug>` (e.g.
  `component-memory-system`, `component-safety-layer`).
- Phase β (component ACs): `component-<slug>-ac-<ac_id>` (e.g.
  `component-memory-system-ac-D1`).
- Phase γ (amendment ACs): `amendment-<NN>-ac-<ac_id>` (e.g.
  `amendment-29-ac-29.1`).
- Phase β placeholders: `component-<slug>-placeholder`.
- Phase γ placeholders: `amendment-<NN>-placeholder`.

Every record carries a `lifted_from(source_doc=..., source_ac=...)` provenance
pointer; idempotency is by `(source_doc, source_ac)` per §6 constraint 6 +
14.

## 6. Sealed-component → spec-phase mapping (for AC.D-mig.1 parent_id)

Per STATE.md "Component state machine":

- Phase 1 → `spec-v1.0`: scope-of-work, primary-persona-loader,
  objective-tracker, memory-system.
- Phase 2 → `spec-v1.0`: session-resilient-orchestrator, graceful-degradation,
  observability-aggregator, self-upgrade-framework.
- Phase 3 → `spec-v1.0`: safety-layer, reversibility-primitive,
  cost-governance, self-correction-loop.
- Phase 4 → `spec-v1.0`: workspace-bootstrap, foundation-audit,
  hands-off-lifecycle.

(All 13 sealed components ladder to v1.0 per STATE.md; v1.1 / v1.2 phases are
the spec-version layer, not the component-rebuild-phase layer. The naming
collision is a known docs-v-spec quirk; the parent_id mapping uses spec-v1.0
for every Phase 1–4 component.)

The 13 components seeded in Phase α (per `docs/archive/component-research/`):
cost-governance, foundation-audit, graceful-degradation, hands-off-lifecycle,
memory-system, objective-tracker, observability-aggregator,
primary-persona-loader, reversibility-primitive, safety-layer, scope-of-work,
self-correction-loop, self-upgrade-framework, session-resilient-orchestrator,
workspace-bootstrap. (15, but the plan §1.1 says "13" — STATE.md table lists
foundation-audit + hands-off-lifecycle as additions; we seed the actual
component dirs with proposal.md present, dropping `domain-workspace-migration`
which is shelved + has no proposal.md.)

Component dir slugs lacking a `proposal.md`: `domain-workspace-migration`,
`memory-system-gliner2-expansion` — skipped (no proposal to lift from).

## 7. Trigger flow

```
loam-mode session-start (every session, fail-soft)
   ↓
read_dev_intent_safe(workspace_root)  # already exists in loam-mode
   ↓ "yes"
heavy_b_migrate.trigger.run_if_dev_intent(workspace_root)  [new]
   ↓
   query tracker for `lifted_from.source_doc=<spec_doc>` and `source_ac=v1.0` etc
   ↓ if not all 13 component objectives present:
   run phase α (seed missing)
   ↓
   run phase β (extract proposal ACs for each component objective just seeded
                or already-seeded but not-yet-projected)
   ↓
   run phase γ (extract amendment plan ACs for each amendment plan file under
                docs/plans/amendment-*.md)
   ↓
   return  # next session: idempotency-by-`lifted_from` no-ops the run
```

## 8. Phase ordering enforcement (AC.D-mig.6)

The runner exposes:

```python
def run_phases(
    workspace_root: Path,
    *,
    phases: tuple[str, ...] = ("alpha", "beta", "gamma"),
    extractors: ExtractorFns | None = None,
) -> RunReport:
    """Execute phases in order. Raises PhaseOrderingError if 'beta' is
    requested before 'alpha' has run, or 'gamma' before 'beta'."""
```

Ordering is enforced by structural pre-check: phase β requires every
component-objective `parent_id` to exist; phase γ requires the relevant
component-AC to exist (or skips with placeholder).

Direct CLI invocation `phase-beta` (skipping α) exits non-zero with a
structured diagnostic.

## 9. Out of scope (explicit)

- LLM-assisted extraction of ambiguous plans.
- `pos-amend project --check` subcommand.
- Drift detection.
- The actual realisation of the 700+ records on the canonical workspace —
  that happens automatically on the next dev-mode session via the trigger.
  The brief explicitly accepts "trigger wired; counts realised on first
  dev-mode session" as a valid completion shape. **However:** to keep the
  programme verifiable, we do run the projection in canonical at build time
  to confirm the chain works end-to-end. Resulting records are not committed
  (the tracker DB is workspace-local + gitignored).

## 10. Commit shape

Per plan §10:

1. `feat(tools): heavy-b-migrate scaffold + Phase α / β / γ extractors`
   (single feature commit; the package as a whole is the unit).
2. `feat(loam-mode): wire heavy-b lazy-projection trigger into session-start`
   (the cross-tool wire).
3. `docs(plans): record heavy-b migration build SHAs in §14 method-decision register`
   (the plan-doc backfill).

No SEAL_COMMIT bump, no manifest, no seal commit (dev-discipline).

## 11. Method-decision register heading (pre-authored, per dispatch brief)

Will append §14 heading to the plan doc before any commit; §14 lists D-build.1
through D-build.6 with the selections from §1 above + commit SHAs backfilled
post-build.
