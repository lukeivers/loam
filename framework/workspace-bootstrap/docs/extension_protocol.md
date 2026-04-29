# Phase 4+ Extension Protocol

How to add a new contribution to a pOS workspace without modifying
`workspace-bootstrap` itself.

## The three steps

1. **One adapter file in your package.** Define a class that inherits
   from `workspace_bootstrap.BaseContribution` (or satisfies the
   `Contribution` protocol) and exposes a `metadata: ContributionMetadata`
   class attribute.

   ```python
   # my_package/bootstrap_adapter.py
   from workspace_bootstrap import BaseContribution, ContributionMetadata, Phase

   class MyContribution(BaseContribution):
       metadata = ContributionMetadata(
           name="my_component",
           phase=Phase.after_orchestrator_ready,
           after=("self_correction",),
       )

       def contribute(self, host) -> None:
           # Wire your component into the host.
           ...
   ```

2. **One entry-point declaration in your `pyproject.toml`.**

   ```toml
   [project.entry-points."pos.bootstrap.contributions"]
   my_component = "my_package.bootstrap_adapter:MyContribution"
   ```

3. **One line in the workspace's `bootstrap.yaml`.**

   ```yaml
   version: 1
   contributions:
     - observability_aggregator
     - scope_of_work
     # ... foundational bundle ...
     - my_component        # ← your new contribution.
   ```

Install your package (`pip install my-package`). Restart the
workspace. Your contribution fires during the named phase. **Bootstrap's
code does not change.**

## Phases

Three phases run in fixed order:

- **`before_orchestrator_start`** — runs before the orchestrator's
  `_startup()` completes. Use this for tracer-provider registration,
  sidecar launching, persona loading.
- **`wrap_activate_scope`** — runs after the orchestrator's
  `activate_scope` IPC handler is registered. Use this for gate
  wraps that compose on top of `activate_scope`. Registration order
  yields dispatch order (last-registered runs first at dispatch).
- **`after_orchestrator_ready`** — runs after all wraps are installed.
  Use this for event-subscription components, CLI probes, late-phase
  hooks.

Phase is declared on the contribution's `metadata.phase`. Within a
phase, `after` and `before` declarations yield a deterministic order
via topological sort with alphabetical tie-breaking. Cross-phase
`after` / `before` declarations are allowed — they must be consistent
with the fixed phase order (a `before_orchestrator_start` contribution
cannot declare `after=` a `wrap_activate_scope` contribution).

## Ordering declarations

```python
ContributionMetadata(
    name="my_component",
    phase=Phase.after_orchestrator_ready,
    after=("self_correction",),       # this runs after self_correction
    before=("another_component",),    # this runs before another_component
)
```

Both `after` and `before` accept tuples of contribution names. Names
must exist in the workspace's manifest or a `-32085` unknown-reference
error is raised at boot.

## Manifest entry forms

Three entry forms are accepted per `contributions:` list item:

```yaml
contributions:
  # Bare string — resolved via `pos.bootstrap.contributions` entry point.
  - observability_aggregator

  # Dict with `module` + `attr` — direct dotted import.
  - name: my_remote
    module: my_package.bootstrap_adapter
    attr: MyContribution

  # Dict with `path` + `attr` — workspace-local file.
  - name: my_local
    path: ./adapters/local.py
    attr: LocalContribution
```

## Host API

The `host` object passed to `contribute(host)` exposes:

- `host.config_dir` — where per-adapter config files live.
- `host.workspace_root` — the workspace directory.
- `host.tracer` — OpenTelemetry tracer for `loam.bootstrap.*` spans.
- `host.channel_registry` — shared notification-channel registry.
- `host.register_shutdown(name, fn)` — push a teardown hook.
- `host.register_channel(name, channel)` — store a channel by name.
- `host.require(attr)` — read an orchestrator-populated attribute;
  raises if the producing phase has not run yet.

After the before-phase, these attributes are populated:
`host.orchestrator`, `host.ipc_server`, `host.scope_runtime`,
`host.objective_tracker`, `host.monitor`,
`host.observability_provider`, `host.loaded_persona`.

After the wrap-phase: `host.safety_controller`,
`host.reversibility_controller`, `host.cost_controller`.

After the after-phase: `host.self_correction_controller`,
`host.memory_sidecar_url`.

## Failure posture

Every boot error fails closed with a named diagnostic in the
`-32080..-32089` error-code range:

| Code | Name | Trigger |
|------|------|---------|
| -32080 | BOOTSTRAP_MISSING_CONFIG | manifest missing or unparseable |
| -32081 | BOOTSTRAP_CONTRIBUTION_NOT_FOUND | named contribution cannot be imported |
| -32082 | BOOTSTRAP_METADATA_INVALID | contribution metadata fails validation |
| -32083 | BOOTSTRAP_NAME_COLLISION | two contributions declare the same `name` |
| -32084 | BOOTSTRAP_ORDERING_CYCLE | topological sort detected a cycle |
| -32085 | BOOTSTRAP_UNKNOWN_REFERENCE | `after`/`before` names a non-existent contribution |
| -32086 | BOOTSTRAP_ADAPTER_RAISED | `contribute(host)` raised |

## Shutdown

Shutdown hooks registered via `host.register_shutdown(name, fn)` run
in LIFO order. The framework calls them after the orchestrator's
event loop exits; exceptions are logged but do not short-circuit
teardown of earlier hooks.
