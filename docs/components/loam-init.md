# loam-init

## What it does

`loam-init` is the component that registers the `loam init`
subcommand of the unified `loam` CLI. It is the user-facing entry
point for bootstrapping a fresh loam workspace from a canonical
source — a local git working tree of loam, or a remote git URL.

It is a thin shim. The work of composing settings, scaffolding
per-host config, and discovering plugin contributions belongs to
[`workspace-bootstrap`](workspace-bootstrap.md). `loam-init` exists
so that `loam init <path>` is a stable verb on the unified CLI
even though the bootstrap engine evolves underneath it.

## How to invoke

```bash
loam init <new-ws-path> [--from <canonical-source>] [--init-existing] [--persona-handle <handle>]
```

- `<new-ws-path>` — target path for the new workspace.
- `--from <canonical-source>` — absolute POSIX path to a local git
  working tree, or an `http(s)`/`git@` URL. Optional; if omitted,
  defaults to the current working directory when it is a git tree
  (the typical pattern when `loam init` runs from inside a cloned
  loam tree).
- `--init-existing` — re-scaffold an already-bootstrapped workspace
  (skips clone). Idempotent.
- `--persona-handle <handle>` — workspace primary-persona handle
  (default: `primary`).

`loam init` is **idempotent** under `--init-existing` —
re-invocation re-composes the configuration from the current
framework + plugin set without disturbing your workspace data.

## Observable surface

What you can `tail` / `cat` / `grep` to see the component working:

- **`loam init --help`.** The subcommand surface; the help text is
  the contract.
- **`.claude/settings.json` after `loam init`.** Written by
  `workspace-bootstrap` during the init run; the composed settings
  view the workspace runs against.
- **Per-host state under `~/.loam/`.** First-run scaffolding writes
  per-host config here.
- **First-run inventory.** Bootstrap's first-run check writes a
  manifest of what exists vs what was created; visible at
  `~/.loam/<workspace>/first-run-inventory.yaml`.
- **OTel spans.** `loam.workspace_bootstrap.*` namespace (the work
  happens inside bootstrap; loam-init dispatches into it).

## Stable surfaces (for plugin authors)

Plugin authors do not extend `loam-init` directly. The extension
contract is published by [`workspace-bootstrap`](workspace-bootstrap.md):
plugins declare contributions via the `loam.bootstrap.contributions`
entry-point group; `loam init` discovers and composes them on every
run.

The CLI subcommand registration pattern itself is reusable —
plugins can register their own top-level `loam <verb>` subcommands
via the `loam.cli.subcommands` entry-point group; `loam-init`'s
own `init` subcommand is the reference example. Other registrants
include `dev-sdlc`'s `loam amend` family and the `odd-extract`
verb.

For internal implementation detail see
[`framework/loam-init/README.md`](../../framework/loam-init/README.md).
