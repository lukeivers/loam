# Objective Tracker

Phase 1 primitive for pOS v2. Event-sourced objective tracker with
sidecar scope-to-objective binding, ODD integration surface, and OTel
observability emission.

## Status

- **Deliverables D1–D9:** complete.
- **Tests:** 86 passing.
- **Integration invariant:** scope-of-work's 77 tests still pass — the
  scope-to-objective enforcement is a sidecar, not a scope-of-work
  amendment.

## Layout

```
objective-tracker/
├── pyproject.toml
├── pytest.ini
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── spec.py              # ObjectiveSpec, TimeBound, Criterion variants
│   ├── events.py            # typed event discriminated union
│   ├── store.py             # SQLite WAL event store + sidecar table
│   ├── projection.py        # internal projection fold
│   ├── projection_view.py   # public immutable ObjectiveProjection
│   ├── policies.py          # legal status transitions
│   ├── observability.py     # OTel emission helpers (no-op safe)
│   ├── runtime.py           # ObjectiveTracker — public async API
│   ├── errors.py            # typed exceptions
│   └── upgrade.py           # D8 upgrade-fidelity harness
├── tests/
│   ├── conftest.py
│   ├── test_d1_objective_primitive.py
│   ├── test_d2_hierarchy.py
│   ├── test_d2b_parent_close.py
│   ├── test_d3_criterion_union.py
│   ├── test_d4_scope_binding.py       # includes sealed-SOW integration
│   ├── test_d5_authored_by.py
│   ├── test_d6_odd_integration.py
│   ├── test_d7_otel_emission.py
│   └── test_d8_upgrade_fidelity.py
└── docs/
    ├── overview.md
    ├── architecture.md
    ├── data-flow.md
    ├── relationship-map.md
    └── api-reference.md
```

## Running tests

```bash
cd /Users/lukeivers/ivers-corp-pos-v2/objective-tracker
source .venv/bin/activate
python -m pytest -q
```

To also confirm scope-of-work remains green:

```bash
cd /Users/lukeivers/ivers-corp-pos-v2/scope-of-work
source .venv/bin/activate
python -m pytest -q    # 77 passed, 1 skipped
```
