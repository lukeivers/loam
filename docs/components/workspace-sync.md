# workspace-sync

## What it does

`workspace-sync` is the component that keeps a workspace's
framework directory in sync with the canonical loam repository
without overwriting the workspace's own data. The shape is
git-flavoured — the canonical tree advances; the workspace's
framework copy fast-forwards or three-way-merges; user data in
the workspace stays untouched.

Three classes of workspace state matter and are handled
differently:

- **Framework-owned files** (`framework/<component>/src/`,
  `framework/first-run-inventory.yaml`, etc.) — fast-forwarded
  from canonical with no semantic merge.
- **Generated files** (per-workspace settings written by
  `workspace-bootstrap`) — re-generated from the new framework
  state.
- **User data** (memory store, scope event logs, audit
  ledgers) — never touched by sync.

When a sync would conflict — the canonical tree changed
something the workspace has overlay-edited — workspace-sync
calls into a semantic-merge gate that asks for an LLM-mediated
resolution rather than a blind merge.

## How to invoke

The user-facing CLI:

```bash
loam-sync                        # advance the workspace to canonical HEAD
loam-sync --dry-run              # show what would change
loam-sync --resolve <conflict>   # interactive conflict resolution
```

`loam-sync` is also runnable from inside a Claude Code session;
the persona surfaces sync status in the SessionStart greeting if
the workspace is behind canonical.

## Observable surface

What you can `tail` / `cat` / `grep` to see the component working:

- **OTel spans.** `loam.workspace_sync.*` namespace. Each sync
  run emits a `sync.run` span with a list of changed paths; each
  semantic-merge gate invocation emits `merge.gate`; conflicts
  emit `conflict` spans with the conflicting paths.
- **Sync log.** Per-workspace log under
  `~/.loam/<workspace>/sync.log`; tails what was advanced and
  what was held back.
- **Canonical-cache.** workspace-sync caches a local clone of
  canonical for fast diffing; the cache lives under
  `~/.loam/canonical-cache/`.
- **Greeting integration.** If the workspace is behind canonical
  by more than a configurable threshold, the SessionStart
  greeting surfaces it.

## Stable surfaces (for plugin authors)

Plugins ship as their own Python packages and version
independently of the framework; workspace-sync only manages the
framework tree. Plugin authors need not touch sync to keep their
plugin updated — `pip install -U` (or the user's preferred
upgrade flow) handles plugin packages.

For internal implementation detail see
[`framework/workspace-sync/README.md`](../../framework/workspace-sync/README.md).
