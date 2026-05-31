# scope-of-work

Foundational Python primitive for loam. Event-sourced finite state
machine over SQLite WAL with three-axis budgeting (time / tokens /
money), declarative escalation triggers, OpenTelemetry emission,
parent-child cascade, and an upgrade-fidelity test harness.

## Quick start

```python
import asyncio
from scope_of_work import (
    ScopeRuntime, ScopeSpec, Budget, BudgetAxis, ReversibilityClass,
    SuccessCriterion,
)

async def main():
    rt = ScopeRuntime(db_path="./scope.db")
    spec = ScopeSpec(
        goal="research the synthetic Aldermere world",
        constraints=("synthetic data only",),
        budget=Budget(tokens=10_000),
        reversibility_class=ReversibilityClass.fully_reversible,
        success_criteria=(SuccessCriterion(criterion_id="answers", description="answer found"),),
        observers=(),
        escalation_triggers=(),
    )
    proj = await rt.create(spec)
    await rt.start(proj.scope_id)
    await rt.debit(proj.scope_id, input_tokens=100, output_tokens=50,
                   model="claude-sonnet-4-5", prompt_name="ner")
    await rt.complete(proj.scope_id, evaluations=[("answers", "met", None)])
    rt.close()

asyncio.run(main())
```

## Documentation

`docs/` ships alongside the code per loam v1.1 R4. Start at
`docs/README.md` for the reading order.

## Tests

```sh
.venv/bin/python -m pytest          # 63 tests, ~1s
RUN_LIVE_MEMORY=1 .venv/bin/python -m pytest tests/test_d6_memory_adapter.py::test_live_memory_round_trip
```

## Dependencies

Stdlib + `pydantic`, `pyee`, `opentelemetry-api`, `opentelemetry-sdk`.
That is the entire runtime footprint. (Test infra adds `pytest` and
`pytest-asyncio`.)

## Memory-mock retirement

```python
from scope_of_work.adapter import RealScopeSourceAdapter
api = MemoryAPI(memory_store, scope_source=RealScopeSourceAdapter(rt))
```

Memory's `MockScopeSource` is preserved as a test-only fixture; new
code uses the adapter.
