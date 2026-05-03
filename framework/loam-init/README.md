# loam-init

The `loam init` subcommand of the unified `loam` CLI. Bootstrap a fresh loam workspace from a canonical source.

## Usage

```
loam init <new-ws-path> --from <canonical-source> [--init-existing] [--persona-handle <handle>]
```

- `<new-ws-path>` — target path for the new workspace.
- `--from <canonical-source>` — absolute POSIX path to a local git working tree, or an `http(s)`/`git@` URL.
- `--init-existing` — re-scaffold an already-bootstrapped workspace (skips clone).
- `--persona-handle <handle>` — workspace primary-persona handle (default: `primary`).

## Composition

`loam-init` is a thin argparse shim over `loam.workspace_bootstrap.new_workspace.bootstrap_new_workspace`. The subcommand surface registers via the `loam.cli.subcommands` entry-point group; the unified `loam` dispatcher (`loam-cli`) discovers + invokes the builder at startup.

## Install

```
pip install -e framework/loam-init
```

Requires `loam-cli` and `loam-workspace-bootstrap` to be installed in the same environment.
