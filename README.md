# loam

**Cultivate a Claude agent in a substrate that remembers, schedules,
governs, and gets out of your way.**

loam is a Claude-attached harness: a long-running primary persona that
translates your natural-language intent into AI-effective execution,
backed by persistent memory, structural safety gates, cost governance,
and autonomous background work. You open a Claude Code session; the
primary persona greets you with what needs attention; you describe
what you want; the persona picks the execution path. You never pick
the mechanism.

> **One-line pitch:** loam is the substrate you cultivate a Claude
> agent in — single trusted persona, persistent memory, structural
> safety, autonomous continuity. Raw Claude plus the toolkit it
> deserves.

## Why

Raw Claude is powerful and frustrating in equal measure. Every useful
action requires the user to translate intent into the right prompt,
remember the right tool, manage the context window, and re-explain
themselves every session. loam absorbs that translation burden into
the primary persona; the user expresses intent, the persona handles
execution.

The full positioning lives at [`docs/positioning.md`](docs/positioning.md);
the design choice to scaffold (rather than ship a thin agent) is
articulated at [`docs/design/why-loam-scaffolds.md`](docs/design/why-loam-scaffolds.md).

## Quickstart

```bash
# 1. Clone loam.
git clone https://github.com/lukeivers/loam
cd loam

# 2. Install loam from the cloned tree.
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r install-from-source.txt

# 3. Bootstrap a fresh workspace from this clone.
loam init ~/loam-workspace

# 4. Open Claude Code in the new workspace.
cd ~/loam-workspace
claude
```

The install step walks `install-from-source.txt` so every loam
component is installed in the right order. See
[`docs/install-from-source.md`](docs/install-from-source.md) for the
prose guide and troubleshooting.

Your first run scaffolds `~/.loam/`, starts the orchestrator, primes
the file-based memory at `<workspace>/.loam/memory/`, and drops you
into a primary-persona greeting. Normal
runs surface what needs attention without you opening a terminal.

> **Note: you'll have two copies of loam source on disk.** The clone
> from step 1 (at `./loam/`) is what the loam CLI was installed from
> and what `loam init` reads as its canonical source. The new
> workspace from step 3 has its own copy of the framework under
> `<workspace>/framework/` **and its own `<workspace>/framework/.venv`,
> which `loam init` builds for you** (no manual venv or hook step
> inside the workspace — the scaffolded SessionStart hooks resolve to
> that venv, so the persona + orchestrator session-start context runs
> on your first `claude` turn). The workspace is genuinely
> self-contained from that point. The install clone is *disposable*
> once the workspace is bootstrapped: keep it if you want to reinstall
> or pull updates; delete it if you don't. A future minor will ship
> the CLI from PyPI directly, eliminating the install clone — for the
> v0.x series, the source-only install path is intentional + the two
> copies are the price of being self-contained.

## What ships

Eighteen runtime components plus the Dev/SDLC plugin. Highlights:

| Component | Role |
|-----------|------|
| `primary-persona` | The single voice you talk to; loader, monitor, autonomous-authoring contract. |
| `memory` | File-based session-bridging memory the persona reads at SessionStart and writes at Stop. |
| `workspace-bootstrap` | Composition engine; first-run scaffolding; plugin extension protocol. |
| `hands-off-lifecycle` | SessionStart hook, supervisor, drain/recovery. |
| `safety-layer` | Three-gate refusal chain + structural floor. |
| `reversibility-primitive` | Compensation-ledger + irreversibility classification. |
| `cost-governance` | Token / time / money ceilings + drift detection. |
| `observability-aggregator` | OTel-shaped span + log routing. |
| `dormancy` | Pause / resume / fail-loud policy under outage. |
| `dev-sdlc` plugin | ODD-by-default for new projects under loam. |

The full architecture map lives at
[`docs/architecture.md`](docs/architecture.md); per-component
references for all eighteen live under
[`docs/components/`](docs/components/).

## Design lenses

Three principles every feature passes:

1. **Claude-leverage-first.** Every feature actively considers what
   Claude Code / Claude SDK / Claude capabilities (slash commands,
   hooks, skills, MCP, plugins, background tasks) can be leveraged.
   If a Claude-native primitive already covers part of the surface,
   loam composes on top rather than re-implementing.
2. **Harness + primary-persona value.** Every feature must reduce
   translation burden for the user (primary-persona test) and add to
   the toolkit the primary persona can invoke (harness test). A
   feature that fails the harness test is almost always wrong.
3. **Objective-Driven Design.** Work is defined by its observable
   outcome, not by a sequence of steps. Method is the builder's call
   inside the constraint envelope. See
   [`docs/design/odd.md`](docs/design/odd.md).

## Workflow chain

After `loam init` (or any time the extractor opt-in fires), loam's
ODD extractor produces a banded contract draft from your codebase.
That draft is the first stage of a four-step workflow chain — each
stage refines the prior stage's output:

| Stage | Command                                       | What it produces                                                            |
|-------|-----------------------------------------------|-----------------------------------------------------------------------------|
| 1     | `loam odd-extract <repo>` (default)           | Banded contract draft + sidecar; objective inventory.                       |
| 2     | `loam odd-extract <repo> --interview`         | Augmented objective set; resolves flagged-missing items via Q&A.            |
| 3     | `loam odd-extract <repo> --gaps`              | Gap inventory: objectives without verified evidence backing.                |
| 4     | `loam odd-extract <repo> --build-next`        | Ranked candidate work to close the highest-value gaps.                      |

Each command's success-path stdout points at the next step. Run
the chain through once on a fresh codebase to see what loam
extracted; re-run periodically as the codebase evolves to refresh
the contract.

For a reverse-engineered ODD reference, the same chain produces
machine-readable artefacts under
`<workspace>/.loam/extractions/<repo-id>/`.

## Status

loam shipped v0.1.0 as the first public release on 2026-04-29; the
current public release is v0.12.11. The project remains intentionally
narrow: infrastructure components, one demonstration plugin (Dev/SDLC),
and enough scaffolding for a stranger to clone, run, and reach a useful
session without reading source. See `docs/STATE.md` and
`docs/release-roadmap.md` for the per-version detail.

The maintainer is one person on a personal GitHub account
(`lukeivers/loam`). Bus factor is honestly one. If loam helps you,
the most useful contribution is a small, well-scoped issue or PR;
review-circle expansion is the project's biggest non-technical need.

## Documentation

- [`docs/positioning.md`](docs/positioning.md) — the full pitch:
  what loam is, who it's for, what it explicitly is not.
- [`docs/architecture.md`](docs/architecture.md) — component map +
  how the pieces compose. *(authored alongside this README in the
  v0.1.0 docs lane.)*
- [`docs/getting-started.md`](docs/getting-started.md) — clone to
  first session, step by step. *(authored alongside this README in
  the v0.1.0 docs lane.)*
- [`docs/design/odd.md`](docs/design/odd.md) — Objective-Driven
  Design: the methodology loam practices natively and the Dev/SDLC
  plugin defaults new projects to.
- [`docs/papers/odd-methodology.md`](docs/papers/odd-methodology.md) —
  case-study report on Objective-Driven Design: what the methodology
  proposes, empirical observations from a ProgramBench-derivative
  investigation, and what the case data does and does not support.
- [`docs/components/`](docs/components/) — one short reference per
  shipping component.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for workflow, acceptance-
criterion expectations, ODD principle reference, and sign-off model.

## Security

See [`SECURITY.md`](SECURITY.md) for vulnerability-reporting workflow
and disclosure timeline.

## License

loam is licensed under the Apache License, Version 2.0. See
[`LICENSE`](LICENSE) for the full text. Copyright 2026 Luke Ivers and
contributors.
