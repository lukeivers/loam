# loam-amend

`loam amend` — amendment-dispatch tooling subcommand for the unified
`loam` CLI. The package implements the `validate / apply / seal /
template / new-plan` surface; the canonical-side `loam` console-script
discovers this subcommand via the `loam.cli.subcommands` entry-point
group (M6a-authored).

## History

- Pre-M1g: `pos-amend` console-script at `framework/tools/pos-amend/`.
- M1g: renamed to `loam amend` subcommand under `framework/tools/loam/`
  (`loam_cli.amend` package).
- M6b.1: package MOVED to `plugins/dev-sdlc/tools/loam-amend/`
  (`loam_amend` package) per master plan AC.OSS-M6.15 + §10
  D-build.M6.15 (shadow-then-flip). The unified `loam` console-script
  + dispatcher (`loam_cli.cli.main`) STAY at canonical
  `framework/tools/loam/`; only the `amend` subcommand-package moves.

See `plugins/dev-sdlc/README.md` for the parent plugin overview and
`docs/rebuild/plans/oss-v0-1-0-publish-dev-sdlc-plugin-m6b1.md` for
the M6b.1 sub-plan.
