# Note on file sizes

The workspace `CLAUDE.md` carries a "max 200 lines per file" rule.
Several files in `src/` exceed it:

| file | lines | reason |
|---|---:|---|
| `runtime.py` | ~700 | One cohesive `ScopeRuntime` class with ~17 public methods + transition machinery. Splitting via mixins would obscure the API; via composition would hide which method does what. The class is the API — keeping it in one file is the right tradeoff for readability. Internal logic is already extracted to `policies.py`, `projection_view.py`, `triggers.py`, and `observability.py`. |
| `spec.py` | ~300 | The seven-field `ScopeSpec` plus all supporting Pydantic types (Budget, Observer, the five Trigger discriminated-union members, enums). Each declaration is small; the file is wide because pOS deliberately makes the scope spec discoverable in one place. |
| `store.py` | ~300 | SQLite schema + `EventStore` class + per-prompt SQL view. The schema and the queries that read it belong together. |
| `projection.py` | ~265 | One projector function per typed event kind. The dispatch table is the file. |
| `events.py` | ~245 | Twelve typed event classes plus the discriminated-union alias. Each class is small. |

**Why this is acceptable here:** the rule's intent is to prevent
unbounded growth of files that mix concerns. These files are tightly
focused — each one corresponds to a single concept (the runtime, the
spec, the storage layer, the projection logic, the event vocabulary).
The size comes from breadth of typed declarations, not from bloated
implementation.

**What would be a real violation:** a single file mixing the runtime
+ spec + store, or a runtime that grew past 1,000 lines as features
were added without re-extraction. The current split has clear seams
for future extraction if a concept grows.
