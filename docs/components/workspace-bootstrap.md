# workspace-bootstrap

## What it does

`workspace-bootstrap` is the composition engine that turns a fresh
directory into a running loam workspace. It reads the framework's
component metadata, the workspace's own configuration, any plugin
contributions, and merges them into the effective settings the
workspace runs against — `.claude/settings.json`, the per-host
`~/.loam/` state, the runtime adapters that wire components into
each other.

It also publishes the **plugin extension protocol** — the contract
plugins (like Dev/SDLC) extend to add hook handlers, settings
fragments, components, skills, or CLI subcommands to the
workspace. Without `workspace-bootstrap`, plugins would each have
to know how to wire themselves into Claude Code; with it, they
declare contributions and the bootstrap composes them.

## How to invoke

The user-facing entry point is `loam init`:

```bash
loam init <path>            # initialise <path> as a loam workspace
loam init .                 # initialise the current directory
```

`loam init` is **idempotent** — re-running it on an already-
initialised workspace re-composes the configuration from the
current framework + plugin set without disturbing your workspace
data. Plugin authors should expect their contributions to be
re-discovered on every `loam init` run.

Programmatic entry points (for plugin authors and contributors):

- **Adapter declarations** in `framework/<component>/` —
  the runtime wiring each component contributes.
- **Plugin entry-points** in plugin `pyproject.toml` files — the
  contract plugins register against; bootstrap discovers them via
  Python entry-points at init time.

## Observable surface

What you can `tail` / `cat` / `grep` to see bootstrap working:

- **`.claude/settings.json` after `loam init`.** The composed view
  the workspace runs Claude Code against. Plugin contributions
  show up as additional hook handlers, MCP servers, or
  permissions blocks in the merged file.
- **`~/.loam/` per-host config.** Bootstrap writes per-host state
  here on first run; subsequent workspaces share it.
- **OTel spans.** `loam.workspace_bootstrap.*` namespace. Init
  runs emit a `compose` span listing every contribution
  composed; first-run scaffolding emits a `scaffold` span.
- **First-run inventory.** Bootstrap's first-run check writes a
  manifest of what exists vs what was created; visible at
  `framework/first-run-inventory.yaml` (the framework-shipped
  baseline) and at `~/.loam/<workspace>/first-run-inventory.yaml`
  (the per-workspace evidence after init).

## Stable surfaces (for plugin authors)

The plugin extension protocol is the contract bootstrap publishes.
Plugins declare contributions via Python entry-points
(`pyproject.toml`); bootstrap discovers and composes them. The
contribution kinds (hook / settings / component-adapter / skill /
CLI) are stable from v0.1.0; new kinds may be added without
breaking existing plugins.

For internal implementation detail see
[`framework/workspace-bootstrap/README.md`](../../framework/workspace-bootstrap/README.md).
