# hands-off-lifecycle

Composite component: installs the four amendments that together produce
a running healthy pOS v2 on its own when a user opens a Claude Code
session in a fresh workspace.

This component contributes no new Python package of its own — its
content lives as amendments to four pre-existing sealed components:

| Amendment | Target | What landed |
|-----------|--------|-------------|
| 1 | `memory-system/` | Staging store, drain worker, Linux systemd unit |
| 2 | `orchestrator/` | `MemorySupervisor`, `pos_session_start` helper |
| 3 | `graceful-degradation/` | `memory_sidecar` mode + supervisor signals |
| 4 | `workspace-bootstrap/` | `first_run_scaffold` phase + adapter |

Plus one new surface: the Claude Code `SessionStart` hook config in
`hooks/settings.json.fragment` that wires the helper script in.

## Error-code range

`-32090..-32099` are reserved to this component. No overlap with the
five prior ranges (safety -32040s, reversibility -32050s, cost -32060s,
self-correction -32070s, workspace-bootstrap -32080s).

Currently claimed codes:

- `-32090` partial_scaffold_detected (workspace-bootstrap adapter)
- `-32091` platform_unsupported (workspace-bootstrap adapter; also
  reused by true-first-run for
  `platform-unsupported:no-compatible-python-found` and
  `platform-unsupported:python-venv-module-missing` — first-run's
  Python-version gate is mechanically a platform-unsupported case)
- `-32092` memory_unreachable (orchestrator supervisor)
- `-32093` memory_corrupt (orchestrator supervisor, reserved)
- `-32094` supervisor_lost_quorum (orchestrator supervisor, reserved)
- `-32095` staging_overflow_hard_cap (memory-system staging)
- `-32096` drain_poison_accumulation (memory-system drain)
- `-32097` pip_install_failed (true-first-run helper)
- `-32098` service_health_timeout (true-first-run helper)
- `-32099` hands_off_lifecycle_internal (catch-all — inventory-parse
  failures, self-retire verification failures, venv-creation failures,
  etc.)

## SessionStart hook (Claude Code v2.1.87+)

The hook invokes `orchestrator/scripts/pos_session_start.py` as a
type: command hook. The helper never spawns a long-lived child
process inheriting Claude Code's FDs — it delegates to
`launchctl bootstrap` / `systemctl --user start`, which are
FD-safe. This mitigates issue #43123.

`hooks/settings.json.fragment` describes the exact supervisor-path
hook stanza — its command string is what the ongoing-operation hook
looks like. In practice, a pos-v2 workspace ships `.claude/settings.json`
already authored at the repo root, pointing at
`hands-off-lifecycle/hooks/first-run.sh`. That shell script creates
the shared venv on a fresh clone, installs per-component dependencies,
substitutes plists, bootstraps services, then **self-retires** by
rewriting the `SessionStart` stanza to invoke
`orchestrator/scripts/pos_session_start.py` directly (matching the
fragment) and deleting itself from the filesystem. The fragment is
therefore the post-self-retire target shape, not a hand-merge
recipe for users.

See `../context/pos-rebuild/components/true-first-run/` for the
true-first-run build brief. See `../docs/rebuild/FUTURE_IDEAS.md` for
the "setup scripts self-retire on success" Core Development Convention
the lifecycle follows.

## Ownership

Eve owns the brief and the proposal; build agents land the
amendments. See `context/pos-rebuild/components/hands-off-lifecycle/`
for research, proposal, brief, and outputs.
