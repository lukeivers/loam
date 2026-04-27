# workspace-bootstrap

The composition framework for pOS v2. Reads the workspace's
`bootstrap.yaml`, orders contributions by phase, constructs the host,
runs each contribution, and coordinates shutdown.

This component additionally ships two operator-facing console scripts:

## Console scripts

### `pos-bootstrap`

Runs the full bootstrap against the manifest at
`$POS_BOOTSTRAP_MANIFEST` (or `~/.pos/bootstrap.yaml` by default).
Resolves contributions, runs each phase, and — when the orchestrator
contribution constructed an event loop — awaits it until SIGTERM /
SIGINT.

Used by the operator's launchd workflow + by the workspace's
session-start hook chain.

### `pos-new-workspace` (D-migration D.4, amendment #65)

Bootstraps a fresh pOS v2 workspace at the D-shape from a canonical
source.

```
pos-new-workspace <new-ws-path> --from <canonical-source>
```

- `<canonical-source>` is either an absolute POSIX path to a local
  git working tree, or an `http(s)://` / `git@` URL (cloned to a
  shared cache at `~/.pos/canonical-cache/<repo-id>/`).
- `<new-ws-path>` must be empty or non-existent. Pass
  `--init-existing` to re-scaffold an already-bootstrapped workspace
  (idempotent).

Post-bootstrap, the workspace has the D-shape:

```
<new-ws-path>/
  framework/        # git clone of canonical (the only tracked subtree
                    # by default; subsequent pos-sync invocations
                    # operate exclusively here)
  workspace/        # workspace-state (per D.2)
    .pos/
      sync-config.yaml          # canonical_source recorded
      legacy-user-config/       # user-config defaults (~/.pos/-shaped)
      ... (memory-worker, audit log, ...)
    personas/<handle>/          # primary persona scaffold
    .mcp.json                   # MCP server registration for Claude Code
    objective_tracker.sqlite    # workspace-rooted tracker DB
  .claude/          # Claude Code's expected location at workspace root
                    # (per D-Q.A4 lock)
  .gitignore        # framework/ + .claude/ are the only tracked
                    # subtrees by default
```

Subsequent `pos-sync` invocations from inside the workspace work
no-args (β.1 path): the workspace's `workspace/.pos/sync-config.yaml`
carries `canonical_source:` so the sync resolver short-circuits.

Examples:

```bash
# Local canonical (typical dev setup):
pos-new-workspace ~/my-ws --from /Users/lukeivers/ivers-corp-pos-v2

# URL canonical (typical user setup):
pos-new-workspace ~/my-ws --from https://github.com/lukeivers/pos-v2

# Re-scaffold an already-bootstrapped workspace (idempotent):
pos-new-workspace ~/my-ws --from /Users/lukeivers/ivers-corp-pos-v2 \
  --init-existing
```

## Component layout

- `src/workspace_bootstrap/main.py` — composition engine + `pos-bootstrap` entry.
- `src/workspace_bootstrap/new_workspace.py` — `pos-new-workspace` entry (D.4).
- `src/workspace_bootstrap/adapters/` — the foundational-adapter bundle (13 contributions).
- `src/workspace_bootstrap/workspace_paths.py` — single-source-of-truth path helpers (post-D.2).
- `docs/extension_protocol.md` — published Phase 4+ extension protocol; plugin authors register via `pos.bootstrap.contributions` entry points.

## Related components

- `framework/workspace-sync/` — `pos-sync` (D.3 git-merge flow); composed-with by `pos-new-workspace` for the URL-form cache-clone.
- `framework/hands-off-lifecycle/` — first-run hook chain that triggers the scaffold from the workspace's session-start.
- `framework/primary-persona/` — persona-loader; consumes `<workspace>/workspace/personas/<handle>/`.
