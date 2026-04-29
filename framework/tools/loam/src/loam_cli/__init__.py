"""loam — unified top-level CLI for the loam framework.

The ``loam`` binary dispatches to subcommands via argparse subparsers.
At M1g sealing time the only registered subcommand is ``amend`` (the
amendment-dispatch tooling carried forward from the pre-rename
``pos-amend`` CLI per ``loam-rename-decisions.md`` Tier-1 #6); the
top-level dispatcher reserves namespace for future subcommands like
``loam scope new``, ``loam status``, ``loam plot create``.

See ``docs/rebuild/plans/oss-v0-1-0-publish-rename-1g.md`` for the
M1g rename plan, and ``docs/rebuild/plans/amendment-22-pos-amend-cli.md``
for the historical plan that authored the original pos-amend tool the
``loam amend`` subcommand surface descends from.
"""

__version__ = "0.1.0"
